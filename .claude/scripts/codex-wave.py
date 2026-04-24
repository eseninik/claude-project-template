"""
codex-wave.py -- Parallel launcher for codex-implement.py processes.

Spawns up to --parallel concurrent codex-implement.py subprocesses, each in
its own git worktree at worktrees/codex-wave/T{N}/. Aggregates results into
work/codex-primary/codex-wave-report.md.

Does NOT auto-merge worktree branches -- that is Opus's job.

CLI Usage:
    py -3 .claude/scripts/codex-wave.py \\
        --tasks work/codex-primary/tasks/T1.md,T2.md,T3.md \\
        --parallel 3 \\
        --worktree-base worktrees/codex-wave \\
        [--timeout-per-task 3600] \\
        [--report work/codex-primary/codex-wave-report.md] \\
        [--implement-script .claude/scripts/codex-implement.py] \\
        [--base-branch HEAD]
"""

from __future__ import annotations

import argparse
import glob
import logging
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional


logger = logging.getLogger("codex_wave")


DEFAULT_WORKTREE_BASE = Path("worktrees/codex-wave")
DEFAULT_REPORT = Path("work/codex-primary/codex-wave-report.md")
DEFAULT_IMPLEMENT_SCRIPT = Path(".claude/scripts/codex-implement.py")
DEFAULT_TIMEOUT = 3600


# ---------- data ------------------------------------------------------------

@dataclass
class TaskResult:
    """Outcome of running codex-implement.py on a single task."""
    task_id: str
    task_file: str
    worktree_path: str
    branch: str
    status: str  # pass | fail | timeout | error | scope-violation
    exit_code: int
    duration_s: float
    stdout: str = ""
    stderr: str = ""
    result_md_path: Optional[str] = None
    result_md_excerpt: str = ""
    error: Optional[str] = None


# ---------- helpers ---------------------------------------------------------

def _configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


_TASK_ID_RE = re.compile(r"T(\d+)", re.IGNORECASE)


def derive_task_id(task_file: Path) -> str:
    """Derive T{N} id from a task filename; fall back to stem."""
    stem = task_file.stem
    m = _TASK_ID_RE.search(stem)
    if m:
        return f"T{m.group(1)}"
    return stem


def expand_tasks(tasks_arg: str) -> list[Path]:
    """Expand comma-separated tasks/globs into a list of Path objects.

    Accepts comma-separated entries. Each entry is either a literal path or a
    glob (`*`, `?`, `[`). Paths are resolved but not required to exist yet --
    caller validates.
    """
    logger.info("expand_tasks_started tasks_arg=%r", tasks_arg)
    entries = [p.strip() for p in tasks_arg.split(",") if p.strip()]
    result: list[Path] = []
    seen: set[str] = set()
    for entry in entries:
        if any(ch in entry for ch in "*?["):
            matches = sorted(glob.glob(entry))
            logger.debug("expand_tasks_glob pattern=%s matches=%d", entry, len(matches))
            for m in matches:
                abs_m = str(Path(m).resolve())
                if abs_m not in seen:
                    seen.add(abs_m)
                    result.append(Path(m))
        else:
            abs_e = str(Path(entry).resolve())
            if abs_e not in seen:
                seen.add(abs_e)
                result.append(Path(entry))
    logger.info("expand_tasks_completed count=%d", len(result))
    return result


def _run(cmd: list[str], cwd: Optional[Path] = None, timeout: Optional[int] = None) -> tuple[int, str, str]:
    """Run a subprocess; return (rc, stdout, stderr)."""
    logger.debug("run_cmd cmd=%r cwd=%s timeout=%s", cmd, cwd, timeout)
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )
    logger.debug(
        "run_cmd_done rc=%d stdout_bytes=%d stderr_bytes=%d",
        proc.returncode,
        len(proc.stdout or ""),
        len(proc.stderr or ""),
    )
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def create_worktree(project_root: Path, worktree_path: Path, branch: str, base: str = "HEAD") -> None:
    """Create a git worktree at ``worktree_path`` on a new branch ``branch``.

    Removes any stale worktree entry with the same path beforehand.
    Raises RuntimeError on failure.
    """
    logger.info(
        "create_worktree_started path=%s branch=%s base=%s",
        worktree_path, branch, base,
    )
    worktree_path.parent.mkdir(parents=True, exist_ok=True)

    # Best-effort cleanup of stale worktree registrations.
    if worktree_path.exists():
        logger.warning("create_worktree_stale_path exists=%s removing_registration", worktree_path)
        _run(["git", "worktree", "remove", "--force", str(worktree_path)], cwd=project_root)

    rc, out, err = _run(
        [
            "git", "worktree", "add",
            "-b", branch,
            str(worktree_path),
            base,
        ],
        cwd=project_root,
    )
    if rc != 0:
        logger.error(
            "create_worktree_failed rc=%d stderr=%s", rc, err.strip()
        )
        raise RuntimeError(
            f"git worktree add failed (rc={rc}): {err.strip() or out.strip()}"
        )
    logger.info("create_worktree_completed path=%s", worktree_path)


def run_codex_implement(
    implement_script: Path,
    task_file: Path,
    worktree_path: Path,
    timeout: int,
    result_dir: Optional[Path] = None,
) -> tuple[int, str, str]:
    """Invoke codex-implement.py on ``task_file`` inside ``worktree_path``.

    Returns (rc, stdout, stderr). Raises subprocess.TimeoutExpired on timeout.
    """
    logger.info(
        "run_codex_implement_started task=%s worktree=%s timeout=%d",
        task_file, worktree_path, timeout,
    )
    cmd = [
        sys.executable,
        str(implement_script),
        "--task", str(task_file),
        "--worktree", str(worktree_path),
    ]
    if result_dir is not None:
        cmd += ["--result-dir", str(result_dir)]
    if timeout is not None:
        cmd += ["--timeout", str(timeout)]

    # Pad the wall-clock timeout slightly so codex-implement.py's own timeout
    # fires first and produces a structured result. Use None if no timeout.
    wall_timeout = timeout + 60 if timeout else None
    rc, out, err = _run(cmd, timeout=wall_timeout)
    logger.info("run_codex_implement_completed rc=%d", rc)
    return rc, out, err


def _status_from_exit(rc: int) -> str:
    """Map codex-implement.py exit codes to status tokens."""
    if rc == 0:
        return "pass"
    if rc == 1:
        return "fail"
    if rc == 2:
        return "scope-violation"
    return "error"


def _find_result_md(result_dir: Path, task_id: str) -> Optional[Path]:
    """Find a recent task-{id}-result.md matching ``task_id``."""
    if not result_dir.is_dir():
        return None
    candidates = sorted(
        result_dir.glob(f"task-{task_id}-result.md"),
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
        reverse=True,
    )
    if candidates:
        return candidates[0]
    # Permissive fallback — any *result.md containing the id.
    for p in result_dir.glob("*result*.md"):
        if task_id.lower() in p.name.lower():
            return p
    return None


def _excerpt(text: str, limit: int = 2000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated {len(text) - limit} chars]"


def process_task(
    task_file: Path,
    project_root: Path,
    worktree_base: Path,
    implement_script: Path,
    timeout: int,
    result_dir: Path,
    base_branch: str,
) -> TaskResult:
    """Full pipeline for one task: worktree + codex-implement + capture."""
    task_id = derive_task_id(task_file)
    worktree_path = (project_root / worktree_base / task_id).resolve()
    branch = f"codex-wave/{task_id}"
    logger.info(
        "process_task_started id=%s file=%s worktree=%s",
        task_id, task_file, worktree_path,
    )
    started = time.time()

    result = TaskResult(
        task_id=task_id,
        task_file=str(task_file),
        worktree_path=str(worktree_path),
        branch=branch,
        status="error",
        exit_code=-1,
        duration_s=0.0,
    )

    # 1. Worktree
    try:
        create_worktree(project_root, worktree_path, branch, base=base_branch)
    except Exception as exc:
        logger.exception("process_task_worktree_failed id=%s", task_id)
        result.status = "error"
        result.error = f"worktree creation failed: {exc}"
        result.duration_s = time.time() - started
        return result

    # 2. Run codex-implement
    try:
        rc, out, err = run_codex_implement(
            implement_script=implement_script,
            task_file=task_file,
            worktree_path=worktree_path,
            timeout=timeout,
            result_dir=result_dir,
        )
        result.exit_code = rc
        result.stdout = _excerpt(out)
        result.stderr = _excerpt(err)
        result.status = _status_from_exit(rc)
    except subprocess.TimeoutExpired as exc:
        logger.error(
            "process_task_timeout id=%s timeout_s=%s", task_id, exc.timeout
        )
        result.status = "timeout"
        result.error = f"codex-implement.py timed out after {exc.timeout}s"
    except FileNotFoundError as exc:
        logger.exception("process_task_implement_missing id=%s", task_id)
        result.status = "error"
        result.error = f"implement script not found: {exc}"
    except Exception as exc:
        logger.exception("process_task_implement_crashed id=%s", task_id)
        result.status = "error"
        result.error = f"codex-implement.py crashed: {exc}"

    # 3. Capture result.md
    try:
        result_md = _find_result_md(result_dir, task_id)
        if result_md is not None:
            result.result_md_path = str(result_md)
            result.result_md_excerpt = _excerpt(
                result_md.read_text(encoding="utf-8", errors="replace")
            )
    except Exception as exc:
        logger.warning("process_task_result_md_read_failed id=%s err=%s", task_id, exc)

    result.duration_s = round(time.time() - started, 2)
    logger.info(
        "process_task_completed id=%s status=%s duration_s=%.2f",
        task_id, result.status, result.duration_s,
    )
    return result


def _write_report(report_path: Path, results: list[TaskResult]) -> None:
    """Write the aggregate wave-report.md to ``report_path``."""
    logger.info("write_report_started path=%s count=%d", report_path, len(results))
    report_path.parent.mkdir(parents=True, exist_ok=True)

    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    total = len(results)
    by_status: dict[str, int] = {}
    for r in results:
        by_status[r.status] = by_status.get(r.status, 0) + 1

    lines: list[str] = []
    lines.append(f"# codex-wave report ({ts})")
    lines.append("")
    lines.append(f"Total tasks: **{total}**")
    for status in ("pass", "fail", "timeout", "scope-violation", "error"):
        if status in by_status:
            lines.append(f"- {status}: {by_status[status]}")
    lines.append("")

    lines.append("## Worktrees (NOT auto-merged -- Opus must merge manually)")
    for r in results:
        lines.append(f"- `{r.worktree_path}` on branch `{r.branch}` (task {r.task_id}, status {r.status})")
    lines.append("")

    lines.append("## Per-task results")
    for r in results:
        lines.append(f"### {r.task_id} -- {r.status}")
        lines.append(f"- task_file: `{r.task_file}`")
        lines.append(f"- worktree: `{r.worktree_path}`")
        lines.append(f"- branch: `{r.branch}`")
        lines.append(f"- exit_code: {r.exit_code}")
        lines.append(f"- duration_s: {r.duration_s}")
        if r.error:
            lines.append(f"- error: `{r.error}`")
        if r.result_md_path:
            lines.append(f"- result_md: `{r.result_md_path}`")
            lines.append("")
            lines.append("<details><summary>result.md excerpt</summary>")
            lines.append("")
            lines.append("```markdown")
            lines.append(r.result_md_excerpt.rstrip())
            lines.append("```")
            lines.append("</details>")
        if r.stdout.strip():
            lines.append("")
            lines.append("<details><summary>stdout</summary>")
            lines.append("")
            lines.append("```")
            lines.append(r.stdout.rstrip())
            lines.append("```")
            lines.append("</details>")
        if r.stderr.strip():
            lines.append("")
            lines.append("<details><summary>stderr</summary>")
            lines.append("")
            lines.append("```")
            lines.append(r.stderr.rstrip())
            lines.append("```")
            lines.append("</details>")
        lines.append("")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("write_report_completed bytes=%d", report_path.stat().st_size)


def run_wave(
    task_files: list[Path],
    project_root: Path,
    worktree_base: Path,
    implement_script: Path,
    parallel: int,
    timeout: int,
    result_dir: Path,
    base_branch: str,
) -> list[TaskResult]:
    """Run ``task_files`` concurrently (up to ``parallel``). Returns all results."""
    logger.info(
        "run_wave_started tasks=%d parallel=%d timeout=%d",
        len(task_files), parallel, timeout,
    )
    if not task_files:
        logger.warning("run_wave_empty no tasks to run")
        return []

    results: list[TaskResult] = []
    results_lock = threading.Lock()

    def _worker(tf: Path) -> TaskResult:
        try:
            r = process_task(
                task_file=tf,
                project_root=project_root,
                worktree_base=worktree_base,
                implement_script=implement_script,
                timeout=timeout,
                result_dir=result_dir,
                base_branch=base_branch,
            )
        except Exception as exc:
            logger.exception("run_wave_worker_crashed task=%s", tf)
            r = TaskResult(
                task_id=derive_task_id(tf),
                task_file=str(tf),
                worktree_path="",
                branch="",
                status="error",
                exit_code=-1,
                duration_s=0.0,
                error=f"worker crashed: {exc}",
            )
        with results_lock:
            results.append(r)
        return r

    with ThreadPoolExecutor(max_workers=max(1, parallel)) as pool:
        futures: list[Future] = [pool.submit(_worker, tf) for tf in task_files]
        for fut in futures:
            # Each worker swallows its own exception; .result() is safe but we
            # wrap defensively in case a BaseException slipped through.
            try:
                fut.result()
            except Exception:
                logger.exception("run_wave_future_crashed")

    logger.info("run_wave_completed total=%d", len(results))
    return results


# ---------- CLI -------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codex-wave.py",
        description=(
            "Launch N codex-implement.py processes in parallel, each in its "
            "own git worktree. Aggregates results into a wave report. "
            "Does NOT auto-merge worktrees -- Opus merges manually."
        ),
    )
    parser.add_argument(
        "--tasks", required=True,
        help="Comma-separated task files or globs (e.g. 'tasks/T*.md').",
    )
    parser.add_argument(
        "--parallel", type=int, default=3,
        help="Maximum concurrent codex-implement.py processes (default: 3).",
    )
    parser.add_argument(
        "--worktree-base", default=str(DEFAULT_WORKTREE_BASE),
        help=f"Directory to host per-task worktrees (default: {DEFAULT_WORKTREE_BASE}).",
    )
    parser.add_argument(
        "--timeout-per-task", type=int, default=DEFAULT_TIMEOUT,
        help=f"Per-task timeout in seconds (default: {DEFAULT_TIMEOUT}).",
    )
    parser.add_argument(
        "--report", default=str(DEFAULT_REPORT),
        help=f"Output aggregate report path (default: {DEFAULT_REPORT}).",
    )
    parser.add_argument(
        "--result-dir", default="work/codex-implementations",
        help="Directory where codex-implement.py writes task-N-result.md.",
    )
    parser.add_argument(
        "--implement-script", default=str(DEFAULT_IMPLEMENT_SCRIPT),
        help=f"Path to codex-implement.py (default: {DEFAULT_IMPLEMENT_SCRIPT}).",
    )
    parser.add_argument(
        "--base-branch", default="HEAD",
        help="Branch/commit to base each worktree on (default: HEAD).",
    )
    parser.add_argument(
        "--project-root", default=".",
        help="Project root (default: cwd).",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable DEBUG-level logging.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose)

    project_root = Path(args.project_root).resolve()
    worktree_base = Path(args.worktree_base)
    implement_script = Path(args.implement_script)
    report_path = Path(args.report)
    result_dir = Path(args.result_dir)

    logger.info(
        "main_started tasks=%s parallel=%d worktree_base=%s timeout=%d",
        args.tasks, args.parallel, worktree_base, args.timeout_per_task,
    )

    task_files = expand_tasks(args.tasks)
    if not task_files:
        logger.error("main_no_tasks tasks_arg=%r", args.tasks)
        print("ERROR: no task files matched", file=sys.stderr)
        return 2

    missing = [t for t in task_files if not Path(t).is_file()]
    if missing:
        logger.error("main_missing_task_files count=%d", len(missing))
        for m in missing:
            print(f"ERROR: task file not found: {m}", file=sys.stderr)
        return 2

    if not implement_script.is_file():
        logger.error("main_implement_script_missing path=%s", implement_script)
        print(
            f"ERROR: implement script not found: {implement_script}",
            file=sys.stderr,
        )
        return 2

    try:
        results = run_wave(
            task_files=task_files,
            project_root=project_root,
            worktree_base=worktree_base,
            implement_script=implement_script,
            parallel=args.parallel,
            timeout=args.timeout_per_task,
            result_dir=result_dir,
            base_branch=args.base_branch,
        )
    except KeyboardInterrupt:
        logger.warning("main_interrupted keyboard")
        print("Interrupted -- partial results may be written", file=sys.stderr)
        return 130

    _write_report(report_path, results)

    # Summary to stdout for human readers
    total = len(results)
    passes = sum(1 for r in results if r.status == "pass")
    print(
        f"Wave complete: {passes}/{total} passed. Report: {report_path}. "
        f"Worktrees kept for Opus under {worktree_base}/."
    )
    for r in results:
        print(f"  {r.task_id:6s} {r.status:16s} rc={r.exit_code} ({r.duration_s}s) {r.worktree_path}")

    logger.info("main_completed total=%d pass=%d", total, passes)
    # Wave exit: 0 only if every task passed
    return 0 if passes == total else 1


if __name__ == "__main__":
    sys.exit(main())
