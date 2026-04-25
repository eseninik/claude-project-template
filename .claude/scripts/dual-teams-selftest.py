#!/usr/bin/env python3
"""End-to-end self-test for dual-implement infrastructure.

The self-test builds an isolated git repository, creates a fake Claude/Codex
worktree pair, and verifies the sentinel, preflight, enforcer, and judge-axis
surfaces without invoking the Codex CLI or any external service.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Iterator


if sys.platform == "win32":
    for _stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")


LOGGER_NAME = "dual_teams_selftest"
logger = logging.getLogger(LOGGER_NAME)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
SENTINEL_NAME = ".dual-base-ref"


class JsonFormatter(logging.Formatter):
    """Minimal JSON log formatter for CI ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        extra = getattr(record, "extra_fields", None)
        if extra:
            payload.update(extra)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _log(level: int, message: str, **fields: Any) -> None:
    logger.log(level, message, extra={"extra_fields": fields})


def setup_logging(verbose: bool = False) -> None:
    """Configure module logger to emit structured JSON to stderr."""
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.propagate = False
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.addHandler(handler)


def positive_ms(start: float | None = None) -> int:
    """Return a positive integer millisecond duration."""
    if start is None:
        return 1
    elapsed = int(round((time.perf_counter() - start) * 1000))
    return max(1, elapsed)


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str
    duration_ms: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "detail": self.detail,
            "duration_ms": self.duration_ms,
        }


@dataclass
class SelfTestReport:
    started_at: str
    duration_ms: int
    summary: dict[str, int]
    results: list[CheckResult]
    tmpdir: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at,
            "duration_ms": self.duration_ms,
            "summary": self.summary,
            "results": [result.to_dict() for result in self.results],
        }


@dataclass
class SelfTestConfig:
    keep_tmpdir: bool = False
    verbose: bool = False
    fault_missing_sentinel: str | None = None


@dataclass
class IntegrationHandles:
    preflight: Callable[[Path], Any] | None = None
    enforcer: Callable[[Path], bool] | None = None
    judge_collect: Callable[[Path, str], list[Path]] | None = None
    load_failures: list[CheckResult] = field(default_factory=list)


@dataclass
class RepoFixture:
    root: Path
    claude_worktree: Path
    codex_worktree: Path
    base_sha: str


def import_module_from_path(module_name: str, path: Path) -> ModuleType:
    """Import a Python module from an arbitrary file path."""
    _log(logging.DEBUG, "entry: import_module_from_path", module_name=module_name, path=str(path))
    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load spec for {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        _log(logging.DEBUG, "exit: import_module_from_path", module_name=module_name)
        return module
    except Exception:
        logger.exception("import_module_from_path failed", extra={"extra_fields": {"path": str(path)}})
        raise


def make_failure(name: str, detail: str, start: float | None = None) -> CheckResult:
    """Create and log a failed check result."""
    duration_ms = positive_ms(start)
    result = CheckResult(name=name, status="FAIL", detail=detail, duration_ms=duration_ms)
    _log(logging.ERROR, "check error", check=name, status="FAIL", detail=detail, duration_ms=duration_ms)
    return result


def load_integrations(project_root: Path) -> IntegrationHandles:
    """Load real preflight, enforcer, and judge helpers via importlib."""
    _log(logging.INFO, "entry: load_integrations", project_root=str(project_root))
    start = time.perf_counter()
    handles = IntegrationHandles()
    try:
        codex_impl = import_module_from_path(
            "dual_teams_selftest_codex_implement",
            project_root / ".claude" / "scripts" / "codex-implement.py",
        )
        preflight = getattr(codex_impl, "preflight_worktree", None)
        check_clean = getattr(codex_impl, "check_tree_clean", None)
        if callable(preflight):
            handles.preflight = preflight
        elif callable(check_clean):
            handles.preflight = lambda worktree: check_clean(worktree)
        else:
            handles.load_failures.append(make_failure("preflight-load", "preflight helper unavailable"))
    except Exception as exc:
        handles.load_failures.append(make_failure("preflight-load", str(exc)))

    try:
        enforcer_module = import_module_from_path(
            "dual_teams_selftest_codex_delegate_enforcer",
            project_root / ".claude" / "hooks" / "codex-delegate-enforcer.py",
        )
        enforcer = getattr(enforcer_module, "is_dual_teams_worktree", None)
        if callable(enforcer):
            handles.enforcer = enforcer
        else:
            handles.enforcer = lambda worktree: (Path(worktree) / SENTINEL_NAME).is_file()
    except Exception as exc:
        handles.load_failures.append(make_failure("enforcer-load", str(exc)))

    try:
        judge_axes = import_module_from_path(
            "dual_teams_selftest_judge_axes",
            project_root / ".claude" / "scripts" / "judge_axes.py",
        )
        collect = getattr(judge_axes, "_collect_modified_py_files", None)
        if not callable(collect):
            collect = getattr(judge_axes, "_list_modified_py", None)
        if callable(collect):
            handles.judge_collect = collect
        else:
            handles.load_failures.append(make_failure("judge-load", "judge helper unavailable"))
    except Exception as exc:
        handles.load_failures.append(make_failure("judge-load", str(exc)))

    _log(
        logging.INFO,
        "exit: load_integrations",
        duration_ms=positive_ms(start),
        failures=len(handles.load_failures),
    )
    return handles


def is_codex_command(command: Any) -> bool:
    """Return True when a subprocess command targets a Codex CLI binary."""
    _log(logging.DEBUG, "entry: is_codex_command")
    try:
        if isinstance(command, (str, bytes)):
            first = str(command).strip().split()[0] if str(command).strip() else ""
        else:
            parts = list(command)
            first = str(parts[0]) if parts else ""
        name = Path(first).name.lower()
        found = name in {"codex", "codex.cmd", "codex.exe"}
        _log(logging.DEBUG, "exit: is_codex_command", found=found, name=name)
        return found
    except Exception:
        logger.exception("is_codex_command failed")
        raise


@contextlib.contextmanager
def guard_no_codex_subprocess() -> Iterator[None]:
    """Assert that no subprocess invocation calls a Codex CLI."""
    _log(logging.DEBUG, "entry: guard_no_codex_subprocess")
    original_run = subprocess.run

    def guarded_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess:
        command = args[0] if args else kwargs.get("args")
        if is_codex_command(command):
            raise AssertionError(f"selftest must not invoke Codex CLI: {command!r}")
        return original_run(*args, **kwargs)

    subprocess.run = guarded_run
    try:
        yield
    except Exception:
        logger.exception("guard_no_codex_subprocess failed")
        raise
    finally:
        subprocess.run = original_run
        _log(logging.DEBUG, "exit: guard_no_codex_subprocess")


def run_command(args: list[str], cwd: Path, timeout: int = 30) -> subprocess.CompletedProcess:
    """Run a non-shell subprocess with timeout and captured text output."""
    _log(logging.DEBUG, "entry: run_command", args=args, cwd=str(cwd))
    try:
        if is_codex_command(args):
            raise AssertionError(f"selftest must not invoke Codex CLI: {args!r}")
        proc = subprocess.run(
            args,
            cwd=str(cwd),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        _log(logging.DEBUG, "exit: run_command", args=args, returncode=proc.returncode)
        return proc
    except Exception:
        logger.exception("run_command failed", extra={"extra_fields": {"args": args, "cwd": str(cwd)}})
        raise


def require_success(proc: subprocess.CompletedProcess, action: str) -> None:
    """Raise when a subprocess result failed."""
    _log(logging.DEBUG, "entry: require_success", action=action, returncode=proc.returncode)
    try:
        if proc.returncode != 0:
            raise RuntimeError(f"{action} failed: {proc.stderr.strip() or proc.stdout.strip()}")
        _log(logging.DEBUG, "exit: require_success", action=action)
    except Exception:
        logger.exception("require_success failed", extra={"extra_fields": {"action": action}})
        raise


def setup_transient_repo(tmpdir: Path, config: SelfTestConfig) -> RepoFixture:
    """Create an isolated git repo with Claude and Codex worktrees."""
    _log(logging.INFO, "entry: setup_transient_repo", tmpdir=str(tmpdir))
    start = time.perf_counter()
    try:
        root = tmpdir / "repo"
        root.mkdir(parents=True)
        require_success(run_command(["git", "init", "--initial-branch", "main"], root), "git init")
        require_success(run_command(["git", "config", "user.email", "selftest@local"], root), "git config user.email")
        require_success(run_command(["git", "config", "user.name", "selftest"], root), "git config user.name")
        require_success(run_command(["git", "config", "init.defaultBranch", "main"], root), "git config init.defaultBranch")
        (root / ".gitignore").write_text(f"{SENTINEL_NAME}\n", encoding="utf-8")
        (root / "README.md").write_text("dual teams selftest\n", encoding="utf-8")
        require_success(run_command(["git", "add", ".gitignore", "README.md"], root), "git add base")
        require_success(run_command(["git", "commit", "-m", "base"], root), "git commit base")
        base_sha_proc = run_command(["git", "rev-parse", "HEAD"], root)
        require_success(base_sha_proc, "git rev-parse HEAD")
        base_sha = base_sha_proc.stdout.strip()

        claude_worktree = tmpdir / "claude"
        codex_worktree = tmpdir / "codex"
        require_success(
            run_command(["git", "worktree", "add", "-b", "claude/dual-teams/selftest", str(claude_worktree), "HEAD"], root),
            "git worktree add claude",
        )
        require_success(
            run_command(["git", "worktree", "add", "-b", "codex/dual-teams/selftest", str(codex_worktree), "HEAD"], root),
            "git worktree add codex",
        )
        if config.fault_missing_sentinel != "claude":
            (claude_worktree / SENTINEL_NAME).write_text(base_sha + "\n", encoding="utf-8")
        if config.fault_missing_sentinel != "codex":
            (codex_worktree / SENTINEL_NAME).write_text(base_sha + "\n", encoding="utf-8")

        _log(logging.INFO, "exit: setup_transient_repo", duration_ms=positive_ms(start), base_sha=base_sha)
        return RepoFixture(root=root, claude_worktree=claude_worktree, codex_worktree=codex_worktree, base_sha=base_sha)
    except Exception:
        logger.exception("setup_transient_repo failed")
        raise


def cleanup_fixture(fixture: RepoFixture) -> None:
    """Prune transient worktree metadata before tempdir cleanup."""
    _log(logging.DEBUG, "entry: cleanup_fixture", root=str(fixture.root))
    try:
        run_command(["git", "worktree", "prune"], fixture.root)
        _log(logging.DEBUG, "exit: cleanup_fixture")
    except Exception:
        logger.exception("cleanup_fixture failed")


def run_check(name: str, callback: Callable[[], str]) -> CheckResult:
    """Run one named self-test check and return a separately reportable result."""
    _log(logging.INFO, "check entry", check=name)
    start = time.perf_counter()
    try:
        detail = callback()
        duration_ms = positive_ms(start)
        _log(logging.INFO, "check exit", check=name, status="PASS", detail=detail, duration_ms=duration_ms)
        return CheckResult(name=name, status="PASS", detail=detail, duration_ms=duration_ms)
    except Exception as exc:
        duration_ms = positive_ms(start)
        logger.exception(
            "check error",
            extra={"extra_fields": {"check": name, "status": "FAIL", "duration_ms": duration_ms}},
        )
        return CheckResult(name=name, status="FAIL", detail=str(exc), duration_ms=duration_ms)


def check_preflight(worktree: Path, preflight: Callable[[Path], Any]) -> str:
    """Verify the real preflight helper accepts a sentinel-clean worktree."""
    _log(logging.DEBUG, "entry: check_preflight", worktree=str(worktree))
    try:
        preflight(worktree)
        proc = run_command(["git", "status", "--porcelain"], worktree)
        require_success(proc, "git status --porcelain")
        if proc.stdout.strip():
            raise AssertionError(f"worktree is dirty: {proc.stdout.strip()}")
        _log(logging.DEBUG, "exit: check_preflight", worktree=str(worktree))
        return "git status --porcelain empty"
    except Exception:
        logger.exception("check_preflight failed")
        raise


def check_enforcer(worktree: Path, enforcer: Callable[[Path], bool]) -> str:
    """Verify the enforcer identifies a sentinel worktree as dual-teams."""
    _log(logging.DEBUG, "entry: check_enforcer", worktree=str(worktree))
    try:
        if not enforcer(worktree):
            raise AssertionError(f"{worktree} was not recognized as a dual-teams worktree")
        _log(logging.DEBUG, "exit: check_enforcer", worktree=str(worktree))
        return f"{SENTINEL_NAME} recognized"
    except Exception:
        logger.exception("check_enforcer failed")
        raise


def add_claude_committed_py(fixture: RepoFixture) -> Path:
    """Add and commit a tiny Python file in the Claude worktree."""
    _log(logging.DEBUG, "entry: add_claude_committed_py", worktree=str(fixture.claude_worktree))
    try:
        target = fixture.claude_worktree / "claude_probe.py"
        target.write_text("def claude_probe():\n    return 'claude'\n", encoding="utf-8")
        require_success(run_command(["git", "add", "claude_probe.py"], fixture.claude_worktree), "git add claude_probe.py")
        require_success(run_command(["git", "commit", "-m", "claude probe"], fixture.claude_worktree), "git commit claude probe")
        _log(logging.DEBUG, "exit: add_claude_committed_py", path=str(target))
        return target
    except Exception:
        logger.exception("add_claude_committed_py failed")
        raise


def add_codex_untracked_py(fixture: RepoFixture) -> Path:
    """Add but do not commit a tiny Python file in the Codex worktree."""
    _log(logging.DEBUG, "entry: add_codex_untracked_py", worktree=str(fixture.codex_worktree))
    try:
        target = fixture.codex_worktree / "codex_probe.py"
        target.write_text("def codex_probe():\n    return 'codex'\n", encoding="utf-8")
        _log(logging.DEBUG, "exit: add_codex_untracked_py", path=str(target))
        return target
    except Exception:
        logger.exception("add_codex_untracked_py failed")
        raise


def normalize_paths(paths: list[Path]) -> set[str]:
    """Convert a list of paths to comparable POSIX-style names."""
    _log(logging.DEBUG, "entry: normalize_paths", count=len(paths))
    try:
        names = {Path(path).name for path in paths}
        _log(logging.DEBUG, "exit: normalize_paths", count=len(names))
        return names
    except Exception:
        logger.exception("normalize_paths failed")
        raise


def check_judge_sees_file(worktree: Path, base_sha: str, collect: Callable[[Path, str], list[Path]], filename: str) -> str:
    """Verify judge modified-file collection sees the expected Python file."""
    _log(logging.DEBUG, "entry: check_judge_sees_file", worktree=str(worktree), filename=filename)
    try:
        files = collect(worktree, base_sha)
        names = normalize_paths(files)
        if filename not in names:
            raise AssertionError(f"{filename} missing from judge files: {sorted(names)}")
        _log(logging.DEBUG, "exit: check_judge_sees_file", filename=filename)
        return f"saw {filename}"
    except Exception:
        logger.exception("check_judge_sees_file failed")
        raise


def build_results(fixture: RepoFixture, integrations: IntegrationHandles) -> list[CheckResult]:
    """Execute all available self-test checks in a stable order."""
    _log(logging.INFO, "entry: build_results")
    try:
        results = list(integrations.load_failures)
        if integrations.preflight is not None:
            results.append(run_check("preflight-clean-with-sentinel-V1", lambda: check_preflight(fixture.claude_worktree, integrations.preflight)))
            results.append(run_check("preflight-clean-with-sentinel-V2", lambda: check_preflight(fixture.codex_worktree, integrations.preflight)))
        if integrations.enforcer is not None:
            results.append(run_check("is_dual_teams_worktree-true-on-V1", lambda: check_enforcer(fixture.claude_worktree, integrations.enforcer)))
            results.append(run_check("is_dual_teams_worktree-true-on-V2", lambda: check_enforcer(fixture.codex_worktree, integrations.enforcer)))
        if integrations.judge_collect is not None:
            add_claude_committed_py(fixture)
            add_codex_untracked_py(fixture)
            results.append(
                run_check(
                    "judge-axes-sees-claude-committed-py",
                    lambda: check_judge_sees_file(fixture.claude_worktree, fixture.base_sha, integrations.judge_collect, "claude_probe.py"),
                )
            )
            results.append(
                run_check(
                    "judge-axes-sees-codex-untracked-py",
                    lambda: check_judge_sees_file(fixture.codex_worktree, fixture.base_sha, integrations.judge_collect, "codex_probe.py"),
                )
            )
        _log(logging.INFO, "exit: build_results", checks=len(results))
        return results
    except Exception:
        logger.exception("build_results failed")
        raise


def make_summary(results: list[CheckResult]) -> dict[str, int]:
    """Build strict summary counters from check results."""
    _log(logging.DEBUG, "entry: make_summary", checks=len(results))
    try:
        passed = sum(1 for result in results if result.status == "PASS")
        failed = sum(1 for result in results if result.status != "PASS")
        summary = {"checks": len(results), "passed": passed, "failed": failed}
        _log(logging.DEBUG, "exit: make_summary", **summary)
        return summary
    except Exception:
        logger.exception("make_summary failed")
        raise


def run_selftest(config: SelfTestConfig) -> SelfTestReport:
    """Run the isolated end-to-end self-test and return a report."""
    _log(logging.INFO, "entry: run_selftest", keep_tmpdir=config.keep_tmpdir)
    started_at = datetime.now(timezone.utc).isoformat()
    start = time.perf_counter()
    tmp_manager: tempfile.TemporaryDirectory[str] | None = None
    tmpdir: Path | None = None
    fixture: RepoFixture | None = None
    results: list[CheckResult] = []
    try:
        with guard_no_codex_subprocess():
            tmp_manager = tempfile.TemporaryDirectory(prefix="dual-teams-selftest-")
            tmpdir = Path(tmp_manager.name).resolve()
            fixture = setup_transient_repo(tmpdir, config)
            integrations = load_integrations(PROJECT_ROOT)
            results = build_results(fixture, integrations)
            cleanup_fixture(fixture)
            if config.keep_tmpdir and tmp_manager is not None:
                finalizer = getattr(tmp_manager, "_finalizer", None)
                if finalizer is not None:
                    finalizer.detach()
                tmp_manager = None
    except Exception as exc:
        results.append(make_failure("selftest-run", str(exc), start))
    finally:
        if fixture is not None and not config.keep_tmpdir:
            cleanup_fixture(fixture)
        if tmp_manager is not None:
            try:
                tmp_manager.cleanup()
            except PermissionError:
                shutil.rmtree(tmp_manager.name, ignore_errors=True)

    duration_ms = positive_ms(start)
    summary = make_summary(results)
    report = SelfTestReport(
        started_at=started_at,
        duration_ms=duration_ms,
        summary=summary,
        results=results,
        tmpdir=tmpdir if config.keep_tmpdir else None,
    )
    _log(logging.INFO, "exit: run_selftest", duration_ms=duration_ms, **summary)
    return report


def render_human_report(report: SelfTestReport) -> str:
    """Render the human-readable table and one-line summary."""
    _log(logging.DEBUG, "entry: render_human_report", checks=report.summary["checks"])
    try:
        lines = []
        for result in report.results:
            lines.append(f"[{result.status}] {result.name:<52} ({result.duration_ms:>2} ms)")
        lines.append(
            "selftest: {checks} checks, {passed} passed, {failed} failed ({duration_ms} ms)".format(
                checks=report.summary["checks"],
                passed=report.summary["passed"],
                failed=report.summary["failed"],
                duration_ms=report.duration_ms,
            )
        )
        text = "\n".join(lines)
        _log(logging.DEBUG, "exit: render_human_report")
        return text
    except Exception:
        logger.exception("render_human_report failed")
        raise


def render_json_report(report: SelfTestReport) -> str:
    """Render the strict JSON report schema."""
    _log(logging.DEBUG, "entry: render_json_report", checks=report.summary["checks"])
    try:
        text = json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True)
        _log(logging.DEBUG, "exit: render_json_report")
        return text
    except Exception:
        logger.exception("render_json_report failed")
        raise


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run the dual-teams infrastructure self-test.")
    parser.add_argument("--json", action="store_true", help="emit the machine-readable report to stdout")
    parser.add_argument("--verbose", action="store_true", help="emit debug structured logs to stderr")
    parser.add_argument("--keep-tmpdir", action="store_true", help="keep the transient repository for post-mortem")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = parse_args(argv)
    setup_logging(verbose=args.verbose)
    _log(logging.INFO, "entry: main", json_output=args.json, keep_tmpdir=args.keep_tmpdir)
    try:
        report = run_selftest(SelfTestConfig(keep_tmpdir=args.keep_tmpdir, verbose=args.verbose))
        if args.json:
            print(render_json_report(report))
        else:
            print(render_human_report(report))
        exit_code = 0 if report.summary["failed"] == 0 else 1
        _log(logging.INFO, "exit: main", exit_code=exit_code)
        return exit_code
    except Exception:
        logger.exception("main failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
