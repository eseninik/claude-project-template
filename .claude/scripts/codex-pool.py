#!/usr/bin/env python3
"""Codex Pool - warm pool of `codex app-server` instances.

Manages N `codex app-server` websocket servers on ports from 4510 so
callers can reuse them instead of cold-starting `codex exec` each call.
State: <root>/.codex/pool-state.json, atomic via os.replace.
T10 scope = lifecycle only.

Usage:
    py -3 .claude/scripts/codex-pool.py start [--size 2] [--base-port 4510]
    py -3 .claude/scripts/codex-pool.py stop
    py -3 .claude/scripts/codex-pool.py status
    py -3 .claude/scripts/codex-pool.py health [--timeout 2.0]
"""
from __future__ import annotations
import argparse, json, logging, os, shutil, signal, socket, subprocess, sys, time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional

if sys.platform == "win32":
    for _s in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            try: _s.reconfigure(encoding="utf-8", errors="replace")
            except OSError: pass

SCHEMA_VERSION = 1
DEFAULT_SIZE = 2
DEFAULT_BASE_PORT = 4510
POSIX_GRACE_SECONDS = 3.0
HEALTH_TIMEOUT_SECONDS = 2.0
STATE_REL = Path(".codex") / "pool-state.json"
LOG_REL = Path(".claude") / "logs" / "codex-pool.log"
logger = logging.getLogger("codex_pool")
def setup_logging(log_file: Optional[Path]) -> None:
    logger.setLevel(logging.DEBUG); logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] codex_pool %(message)s")
    sh = logging.StreamHandler(sys.stderr); sh.setLevel(logging.INFO); sh.setFormatter(fmt)
    logger.addHandler(sh)
    if log_file is not None:
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setLevel(logging.DEBUG); fh.setFormatter(fmt); logger.addHandler(fh)
        except OSError as exc:
            logger.warning("setup_logging log_file_error=%s path=%s", exc, log_file)
    logger.debug("setup_logging ok log_file=%s", log_file)
@dataclass
class Instance:
    pool_id: int; port: int; pid: int; start_time: float
    def to_dict(self) -> dict: return asdict(self)
    @classmethod
    def from_dict(cls, d: dict) -> "Instance":
        return cls(int(d["pool_id"]), int(d["port"]), int(d["pid"]), float(d["start_time"]))
@dataclass
class PoolState:
    schema_version: int = SCHEMA_VERSION
    created_at: float = 0.0
    instances: list = field(default_factory=list)
    def to_dict(self) -> dict:
        return {"schema_version": self.schema_version, "created_at": self.created_at,
                "instances": [i.to_dict() for i in self.instances]}
    @classmethod
    def from_dict(cls, d: dict) -> "PoolState":
        return cls(int(d.get("schema_version", SCHEMA_VERSION)),
                   float(d.get("created_at", 0.0)),
                   [Instance.from_dict(x) for x in d.get("instances", [])])
def load_state(path: Path) -> PoolState:
    """Load pool state; return empty on missing/corrupt."""
    logger.debug("load_state entry path=%s", path)
    if not path.exists():
        logger.info("load_state missing -> empty"); return PoolState()
    try:
        state = PoolState.from_dict(json.loads(path.read_text(encoding="utf-8")))
        logger.info("load_state ok instances=%d", len(state.instances))
        return state
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.warning("load_state error=%s -> empty", exc); return PoolState()
def save_state(path: Path, state: PoolState) -> None:
    """Atomic write: tempfile + os.replace (POSIX + Windows safe)."""
    logger.debug("save_state entry path=%s instances=%d", path, len(state.instances))
    tmp: Optional[Path] = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
        tmp.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)
        logger.info("save_state ok instances=%d", len(state.instances))
    except OSError as exc:
        logger.error("save_state error=%s path=%s", exc, path)
        if tmp is not None:
            try: tmp.unlink()
            except OSError: pass
        raise
def remove_state(path: Path) -> None:
    logger.debug("remove_state entry path=%s", path)
    try:
        if path.exists():
            path.unlink(); logger.info("remove_state ok")
    except OSError as exc:
        logger.warning("remove_state error=%s", exc)
def pid_alive(pid: int) -> bool:
    """True if PID currently alive (Windows: tasklist; POSIX: kill -0)."""
    if pid <= 0: return False
    if sys.platform == "win32":
        try:
            out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                                 capture_output=True, text=True, check=False, timeout=10)
            s = (out.stdout or "").strip()
            return bool(s) and f"{pid}" in s and "No tasks" not in s
        except (OSError, subprocess.SubprocessError) as exc:
            logger.warning("pid_alive windows_error=%s pid=%d", exc, pid); return False
    try:
        os.kill(pid, 0); return True
    except ProcessLookupError: return False
    except PermissionError: return True
    except OSError as exc:
        logger.warning("pid_alive posix_error=%s pid=%d", exc, pid); return False
def terminate_pid(pid: int, grace_seconds: float = POSIX_GRACE_SECONDS) -> bool:
    """Kill PID. Windows: taskkill /T /F; POSIX: SIGTERM then SIGKILL."""
    logger.info("terminate_pid entry pid=%d platform=%s", pid, sys.platform)
    if pid <= 0: return False
    if sys.platform == "win32":
        try:
            r = subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)],
                               capture_output=True, text=True, check=False, timeout=15)
            logger.info("terminate_pid win pid=%d rc=%d", pid, r.returncode)
            return r.returncode == 0
        except (OSError, subprocess.SubprocessError) as exc:
            logger.error("terminate_pid win error=%s pid=%d", exc, pid); return False
    try:
        os.kill(pid, signal.SIGTERM)
        logger.info("terminate_pid posix sigterm pid=%d", pid)
    except ProcessLookupError: return True
    except OSError as exc:
        logger.error("terminate_pid posix sigterm_error=%s pid=%d", exc, pid); return False
    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        if not pid_alive(pid):
            logger.info("terminate_pid posix exited pid=%d", pid); return True
        time.sleep(0.1)
    try:
        os.kill(pid, signal.SIGKILL)
        logger.warning("terminate_pid posix sigkill pid=%d", pid); return True
    except ProcessLookupError: return True
    except OSError as exc:
        logger.error("terminate_pid posix sigkill_error=%s pid=%d", exc, pid); return False
def port_free(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port)); return True
        except OSError:
            return False
def allocate_ports(count: int, base_port: int, used: Optional[set] = None) -> list:
    """Find `count` free ports starting at base_port (up to 100 candidates)."""
    logger.debug("allocate_ports entry count=%d base_port=%d", count, base_port)
    used = set(used or set()); result: list = []
    candidate = base_port; attempts = 0
    while len(result) < count and attempts < 100:
        if candidate not in used and port_free(candidate):
            result.append(candidate); used.add(candidate)
        candidate += 1; attempts += 1
    if len(result) < count:
        raise RuntimeError(f"allocate_ports: could not find {count} free ports from {base_port}")
    logger.info("allocate_ports ok ports=%s", result)
    return result
def resolve_codex_bin() -> Optional[str]:
    return shutil.which("codex")
def build_app_server_cmd(codex_bin: str, port: int) -> list:
    return [codex_bin, "app-server", "--listen", f"ws://127.0.0.1:{port}"]
def launch_instance(codex_bin: str, port: int) -> subprocess.Popen:
    """Spawn a single codex app-server bound to `port`."""
    argv = build_app_server_cmd(codex_bin, port)
    logger.info("launch_instance entry port=%d", port)
    kw = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if sys.platform == "win32":
        kw["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        kw["start_new_session"] = True
    proc = subprocess.Popen(argv, **kw)
    logger.info("launch_instance ok port=%d pid=%d", port, proc.pid)
    return proc
def cmd_start(args: argparse.Namespace, project_root: Path) -> int:
    """Launch N instances; refuse if any live; cleans stale first."""
    logger.info("cmd_start entry size=%d base_port=%d", args.size, args.base_port)
    state_path = project_root / STATE_REL
    state = load_state(state_path)
    alive: list = []; stale = 0
    for inst in state.instances:
        if pid_alive(inst.pid): alive.append(inst)
        else:
            stale += 1
            logger.warning("cmd_start stale pool_id=%d pid=%d port=%d", inst.pool_id, inst.pid, inst.port)
    if stale: logger.info("cmd_start cleaned_stale=%d", stale)
    if alive:
        print(f"pool already has {len(alive)} live instance(s); run stop first", file=sys.stderr)
        state.instances = alive; save_state(state_path, state); return 1
    codex_bin = resolve_codex_bin()
    if not codex_bin:
        print("codex CLI not found in PATH", file=sys.stderr)
        logger.error("cmd_start codex_missing"); return 2
    try:
        ports = allocate_ports(args.size, args.base_port)
    except RuntimeError as exc:
        print(f"port allocation failed: {exc}", file=sys.stderr)
        logger.error("cmd_start port_alloc_failed error=%s", exc); return 2
    new_instances: list = []; now = time.time()
    for pool_id, port in enumerate(ports):
        try:
            proc = launch_instance(codex_bin, port)
        except OSError as exc:
            logger.error("cmd_start spawn_error port=%d error=%s", port, exc)
            for inst in new_instances: terminate_pid(inst.pid)
            print(f"spawn failed for port {port}: {exc}", file=sys.stderr); return 2
        new_instances.append(Instance(pool_id, port, proc.pid, now))
    state = PoolState(SCHEMA_VERSION, now, new_instances)
    save_state(state_path, state)
    for inst in new_instances:
        print(f"pool_id={inst.pool_id} port={inst.port} pid={inst.pid} OK")
    print(f"started {len(new_instances)} instance(s); state -> {state_path}")
    logger.info("cmd_start ok count=%d", len(new_instances))
    return 0
def cmd_stop(args: argparse.Namespace, project_root: Path) -> int:
    """Terminate every recorded instance; remove state file."""
    logger.info("cmd_stop entry")
    state_path = project_root / STATE_REL
    state = load_state(state_path)
    if not state.instances:
        print("no pool to stop"); remove_state(state_path)
        logger.info("cmd_stop noop"); return 0
    failures = 0
    for inst in state.instances:
        ok = terminate_pid(inst.pid)
        print(f"pool_id={inst.pool_id} pid={inst.pid} port={inst.port} {'OK' if ok else 'FAIL'}")
        if not ok: failures += 1
    remove_state(state_path)
    logger.info("cmd_stop done count=%d failures=%d", len(state.instances), failures)
    if failures:
        print(f"{failures} termination(s) failed", file=sys.stderr); return 1
    return 0
def _format_age(seconds: float) -> str:
    if seconds < 60: return f"{seconds:.0f}s"
    if seconds < 3600: return f"{seconds / 60:.1f}m"
    return f"{seconds / 3600:.2f}h"
def render_status_table(state: PoolState, now: float, alive_map: dict) -> str:
    if not state.instances: return "pool: empty (no state)"
    header = f"{'pool_id':<8} {'port':<6} {'pid':<8} {'alive':<6} {'age':<8}"
    lines = [header, "-" * len(header)]
    for inst in state.instances:
        age = _format_age(max(0.0, now - inst.start_time))
        alive = "yes" if alive_map.get(inst.pid, False) else "no"
        lines.append(f"{inst.pool_id:<8} {inst.port:<6} {inst.pid:<8} {alive:<6} {age:<8}")
    live = sum(1 for v in alive_map.values() if v)
    lines.append("")
    lines.append(f"summary: {live}/{len(state.instances)} alive, schema_version={state.schema_version}")
    return "\n".join(lines)
def cmd_status(args: argparse.Namespace, project_root: Path) -> int:
    logger.info("cmd_status entry")
    state = load_state(project_root / STATE_REL)
    alive_map = {inst.pid: pid_alive(inst.pid) for inst in state.instances}
    print(render_status_table(state, time.time(), alive_map))
    logger.info("cmd_status ok instances=%d alive=%d", len(state.instances),
                sum(1 for v in alive_map.values() if v))
    return 0
def health_check_port(port: int, timeout: float = HEALTH_TIMEOUT_SECONDS):
    """TCP liveness + optional ws handshake. Returns (ok, message)."""
    logger.debug("health_check_port entry port=%d", port)
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout): pass
    except OSError as exc:
        logger.info("health_check_port tcp_fail port=%d error=%s", port, exc)
        return False, f"tcp: {exc}"
    try:
        import websocket  # type: ignore
    except ImportError:
        logger.warning("health_check_port ws_client_missing port=%d", port)
        return True, "tcp-ok (ws client not installed)"
    try:
        ws = websocket.create_connection(f"ws://127.0.0.1:{port}", timeout=timeout)
        try: ws.close()
        except Exception: pass
        logger.info("health_check_port ok port=%d", port)
        return True, "ws-ok"
    except Exception as exc:  # noqa: BLE001
        logger.info("health_check_port ws_fail port=%d error=%s", port, exc)
        return False, f"ws: {exc}"
def cmd_health(args: argparse.Namespace, project_root: Path) -> int:
    logger.info("cmd_health entry timeout=%.2f", args.timeout)
    state = load_state(project_root / STATE_REL)
    if not state.instances:
        print("pool: empty (no state)"); return 0
    healthy = 0
    for inst in state.instances:
        ok, msg = health_check_port(inst.port, timeout=args.timeout)
        print(f"pool_id={inst.pool_id} port={inst.port} pid={inst.pid} {'OK' if ok else 'FAIL'} ({msg})")
        if ok: healthy += 1
    total = len(state.instances)
    print(f"summary: {healthy}/{total} healthy")
    logger.info("cmd_health ok healthy=%d total=%d", healthy, total)
    return 0 if healthy == total else 1
def find_project_root(start: Optional[Path] = None) -> Path:
    start = (start or Path.cwd()).resolve()
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists() or (candidate / "CLAUDE.md").exists():
            return candidate
    return start
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-pool",
                                     description="Manage warm codex app-server instances.")
    parser.add_argument("--project-root", type=Path, default=None, help="Project root (auto-detect).")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_start = sub.add_parser("start", help="launch N warm instances")
    p_start.add_argument("--size", type=int, default=DEFAULT_SIZE)
    p_start.add_argument("--base-port", type=int, default=DEFAULT_BASE_PORT)
    sub.add_parser("stop", help="terminate pool + remove state")
    sub.add_parser("status", help="print per-instance status table")
    p_health = sub.add_parser("health", help="websocket ping each instance")
    p_health.add_argument("--timeout", type=float, default=HEALTH_TIMEOUT_SECONDS)
    return parser
def main(argv: Optional[list] = None) -> int:
    parser = build_parser(); args = parser.parse_args(argv)
    project_root = (args.project_root or find_project_root()).resolve()
    setup_logging(project_root / LOG_REL)
    logger.info("main entry cmd=%s project_root=%s platform=%s", args.cmd, project_root, sys.platform)
    try:
        if args.cmd == "start": return cmd_start(args, project_root)
        if args.cmd == "stop": return cmd_stop(args, project_root)
        if args.cmd == "status": return cmd_status(args, project_root)
        if args.cmd == "health": return cmd_health(args, project_root)
        parser.print_help(); return 2
    except KeyboardInterrupt:
        logger.warning("main interrupted"); return 130
    except Exception as exc:  # noqa: BLE001
        logger.exception("main fatal error=%s", exc)
        print(f"fatal: {exc}", file=sys.stderr); return 2

if __name__ == "__main__":
    raise SystemExit(main())
