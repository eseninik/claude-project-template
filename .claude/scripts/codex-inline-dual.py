#!/usr/bin/env python3
"""Codex Inline Dual - single micro-task dual helper.

Generates a transient task-<id>.md spec from CLI args (--describe, --scope,
--test), creates two git worktrees (worktrees/inline/<id>/claude and
worktrees/inline/<id>/codex), writes a Claude teammate prompt file, and
launches codex-implement.py as a background subprocess against the Codex
worktree.

The script is "prep + report": Opus (caller) is responsible for actually
spawning the Agent tool with the generated prompt and for judging the two
diffs. This helper only sets up parallel infrastructure and prints what to
do next in a clear 3-section status block.

Usage:
    py -3 .claude/scripts/codex-inline-dual.py \\
        --describe "Add --quiet flag to foo.py" \\
        --scope .claude/scripts/foo.py,tests/test_foo.py \\
        --test "py -3 tests/test_foo.py" \\
        [--task-id my-id] \\
        [--speed balanced] \\
        [--dry-run]

Exit codes:
    0 = prep succeeded (both worktrees created, prompt written, codex spawned)
    2 = fatal error (scope empty, worktree conflict, codex spawn failed, ...)
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

if sys.platform == "win32":
    for _s in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")


# --- Logging ---------------------------------------------------------------- #

logger = logging.getLogger("codex_inline_dual")


class JsonFormatter(logging.Formatter):
    """Minimal JSON log formatter (stdlib only)."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
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
        return json.dumps(payload, ensure_ascii=False)


def _log(level: int, msg: str, **fields: object) -> None:
    logger.log(level, msg, extra={"extra_fields": fields})


def setup_logging(log_file: Optional[Path]) -> None:
    """Configure logger with JSON formatter + optional file sink."""
    _log(logging.DEBUG, "entry: setup_logging", log_file=str(log_file) if log_file else None)
    try:
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        stream = logging.StreamHandler(sys.stderr)
        stream.setFormatter(JsonFormatter())
        stream.setLevel(logging.INFO)
        logger.addHandler(stream)
        if log_file is not None:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(JsonFormatter())
            fh.setLevel(logging.DEBUG)
            logger.addHandler(fh)
        _log(logging.DEBUG, "exit: setup_logging")
    except Exception:
        logger.exception("setup_logging failed")
        raise


# --- Exit codes ------------------------------------------------------------- #

EXIT_OK = 0
EXIT_FATAL = 2


# --- CLI / argument parsing ------------------------------------------------- #


def build_arg_parser() -> argparse.ArgumentParser:
    """Construct the argparse parser."""
    _log(logging.DEBUG, "entry: build_arg_parser")
    try:
        p = argparse.ArgumentParser(
            prog="codex-inline-dual.py",
            description=(
                "Micro-task dual helper: generate transient task spec, create "
                "two worktrees (claude + codex), write Claude prompt, launch "
                "codex-implement.py in background. Prep + report only."
            ),
        )
        p.add_argument("--describe", required=True,
                       help="One-line description of the micro-task (becomes ## Your Task)")
        p.add_argument("--scope", required=True,
                       help="Comma-separated list of in-scope paths (becomes Scope Fence allowed)")
        p.add_argument("--test", required=True, action="append",
                       help="Bash command to run after impl; repeat for multiple commands")
        p.add_argument("--task-id", default=None,
                       help="Task id suffix (default: timestamp-based). Used in worktree paths "
                            "and transient spec filename.")
        p.add_argument("--speed", default="balanced",
                       choices=["fast", "balanced", "thorough"],
                       help="Speed profile passed to codex-implement.py (default: balanced)")
        p.add_argument("--dry-run", action="store_true",
                       help="Print what would happen; do not create worktrees, files, or "
                            "spawn subprocess.")
        p.add_argument("--worktree-base", default=Path("worktrees/inline"), type=Path,
                       help="Base directory for worktree pairs (default: worktrees/inline)")
        p.add_argument("--spec-dir", default=Path("work/codex-implementations/inline"),
                       type=Path,
                       help="Directory for transient task spec + prompt files "
                            "(default: work/codex-implementations/inline)")
        p.add_argument("--codex-timeout", default=3600, type=int,
                       help="Timeout passed to background codex-implement.py (default: 3600)")
        p.add_argument("--log-dir", default=Path("work/codex-primary/logs"), type=Path,
                       help="Directory for structured logs")
        _log(logging.DEBUG, "exit: build_arg_parser")
        return p
    except Exception:
        logger.exception("build_arg_parser failed")
        raise


def parse_scope(raw: str) -> list[str]:
    """Split comma-separated scope string into a cleaned list.

    Trims whitespace around each entry, drops empties, preserves order.
    Raises ValueError if the result is empty.
    """
    _log(logging.DEBUG, "entry: parse_scope", raw=raw)
    try:
        parts = [p.strip() for p in (raw or "").split(",")]
        parts = [p for p in parts if p]
        if not parts:
            raise ValueError("--scope must contain at least one non-empty path")
        _log(logging.DEBUG, "exit: parse_scope", count=len(parts))
        return parts
    except Exception:
        logger.exception("parse_scope failed")
        raise


def default_task_id() -> str:
    """Return a timestamp-based task id (UTC, seconds precision)."""
    _log(logging.DEBUG, "entry: default_task_id")
    try:
        tid = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        _log(logging.DEBUG, "exit: default_task_id", task_id=tid)
        return tid
    except Exception:
        logger.exception("default_task_id failed")
        raise


_TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-]*$")


def sanitize_task_id(task_id: str) -> str:
    """Reject task ids with filesystem-unsafe chars. Returns cleaned id."""
    _log(logging.DEBUG, "entry: sanitize_task_id", task_id=task_id)
    try:
        cleaned = (task_id or "").strip()
        if not cleaned:
            raise ValueError("--task-id must not be empty")
        if not _TASK_ID_RE.match(cleaned):
            raise ValueError(
                f"--task-id {cleaned!r} contains unsafe characters; "
                "allowed: alphanumeric, '-', '_'"
            )
        _log(logging.DEBUG, "exit: sanitize_task_id", cleaned=cleaned)
        return cleaned
    except Exception:
        logger.exception("sanitize_task_id failed")
        raise

# --- Spec generation -------------------------------------------------------- #


def render_task_spec(
    task_id: str,
    describe: str,
    scope: list[str],
    tests: list[str],
    speed: str,
) -> str:
    """Render the transient task-<id>.md spec in the canonical T1 format.

    The generated spec must be consumable by codex-implement.py without
    modification: ## Your Task, ## Scope Fence (with **Allowed paths:**
    bullets), ## Test Commands (bash fenced block), ## Acceptance Criteria
    (IMMUTABLE) (- [ ] ... bullets), frontmatter with executor/risk/speed.
    """
    _log(
        logging.DEBUG,
        "entry: render_task_spec",
        task_id=task_id,
        scope_count=len(scope),
        test_count=len(tests),
        speed=speed,
    )
    try:
        parts: list[str] = []
        parts.append("---")
        parts.append("executor: dual")
        parts.append(f"speed_profile: {speed}")
        parts.append("risk_class: routine")
        parts.append("---")
        parts.append("")
        parts.append(f"# Task inline/{task_id}: {describe.strip()}")
        parts.append("")
        parts.append("## Your Task")
        parts.append("")
        parts.append(describe.strip())
        parts.append("")
        parts.append("## Scope Fence")
        parts.append("")
        parts.append("**Allowed paths:**")
        for entry in scope:
            parts.append(f"- `{entry}`")
        parts.append("")
        parts.append("## Test Commands")
        parts.append("")
        parts.append("```bash")
        for cmd in tests:
            parts.append(cmd)
        parts.append("```")
        parts.append("")
        parts.append("## Acceptance Criteria (IMMUTABLE)")
        parts.append("")
        parts.append(f"- [ ] AC1: implementation satisfies: {describe.strip()}")
        parts.append("- [ ] AC2: only files inside Scope Fence are modified")
        for i, cmd in enumerate(tests, start=1):
            parts.append(f"- [ ] AC{i + 2}: Test Command `{cmd}` exits 0")
        parts.append("- [ ] AC_hygiene: no secrets logged, structured logging on new code")
        parts.append("")
        parts.append("## Constraints")
        parts.append("")
        parts.append("- Windows-compatible")
        parts.append("- Stdlib only unless scope explicitly allows a dep")
        parts.append("- Match existing code style")
        parts.append("")
        text = "\n".join(parts) + "\n"
        _log(logging.DEBUG, "exit: render_task_spec", bytes=len(text))
        return text
    except Exception:
        logger.exception("render_task_spec failed")
        raise


def render_claude_prompt(
    task_id: str,
    describe: str,
    scope: list[str],
    tests: list[str],
    spec_path: Path,
    worktree_claude: Path,
) -> str:
    """Render the Claude teammate prompt that the caller will feed to Agent tool."""
    _log(
        logging.DEBUG,
        "entry: render_claude_prompt",
        task_id=task_id,
        scope_count=len(scope),
        test_count=len(tests),
    )
    try:
        scope_bullets = "\n".join(f"- `{s}`" for s in scope)
        test_block = "\n".join(tests)
        criteria = "\n".join(
            [f"- `{cmd}` exits 0" for cmd in tests]
            + ["- Only files inside Scope Fence are modified",
               "- Structured logging on any new/modified function"]
        )
        prompt = f"""You are the Claude side of a dual micro-task. Your twin is Codex-GPT5.5 working the same spec in a parallel worktree. Opus will judge both diffs.

## Agent Type
coder

## Required Skills
- verification-before-completion
- logging-standards
- coding-standards

## Working Directory (CRITICAL)
{worktree_claude}

Branch: inline/{task_id}/claude

## Task Spec (IMMUTABLE)
{spec_path}

## Your Task
{describe.strip()}

## Scope Fence (Allowed paths)
{scope_bullets}

## Test Commands
```bash
{test_block}
```

## Acceptance Criteria
{criteria}

## Handoff Output (MANDATORY when done)

=== PHASE HANDOFF: inline-{task_id}-claude ===
Status: PASS | REWORK | BLOCKED
Files Modified:
- [path]
Tests: [results of each Test Command]
Decisions: [key choices + rationale]
Learnings:
- Friction: ... | NONE
- Surprise: ... | NONE
Next Phase Input: [what Opus needs for judging]
=== END HANDOFF ===
"""
        _log(logging.DEBUG, "exit: render_claude_prompt", bytes=len(prompt))
        return prompt
    except Exception:
        logger.exception("render_claude_prompt failed")
        raise


# --- Git helpers ------------------------------------------------------------ #


def _run_git(args: list[str], cwd: Path, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    _log(logging.DEBUG, "entry: _run_git", args=args, cwd=str(cwd))
    try:
        git = shutil.which("git") or "git"
        result = subprocess.run(
            [git, *args],
            cwd=str(cwd),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        _log(
            logging.DEBUG,
            "exit: _run_git",
            returncode=result.returncode,
            stderr_len=len(result.stderr),
        )
        return result
    except Exception:
        logger.exception("_run_git failed")
        raise


def find_project_root(start: Path) -> Path:
    """Walk up from start until we hit a dir containing .claude or .git."""
    _log(logging.DEBUG, "entry: find_project_root", start=str(start))
    try:
        current = start.resolve()
        for candidate in [current, *current.parents]:
            if (candidate / ".claude").is_dir() or (candidate / ".git").exists():
                _log(logging.DEBUG, "exit: find_project_root", root=str(candidate))
                return candidate
        _log(logging.WARNING, "project root not found", start=str(current))
        return current
    except Exception:
        logger.exception("find_project_root failed")
        raise


@dataclass
class WorktreePair:
    claude_path: Path
    codex_path: Path
    claude_branch: str
    codex_branch: str


def create_worktrees(
    project_root: Path,
    base: Path,
    task_id: str,
    dry_run: bool,
) -> WorktreePair:
    """Create <base>/<id>/claude on inline/<id>/claude + <base>/<id>/codex.

    On dry_run=True, returns the planned paths/branches without running git.
    """
    _log(
        logging.INFO,
        "entry: create_worktrees",
        project_root=str(project_root),
        base=str(base),
        task_id=task_id,
        dry_run=dry_run,
    )
    try:
        abs_base = base if base.is_absolute() else (project_root / base)
        claude_path = abs_base / task_id / "claude"
        codex_path = abs_base / task_id / "codex"
        claude_branch = f"inline/{task_id}/claude"
        codex_branch = f"inline/{task_id}/codex"

        pair = WorktreePair(
            claude_path=claude_path,
            codex_path=codex_path,
            claude_branch=claude_branch,
            codex_branch=codex_branch,
        )

        if dry_run:
            _log(logging.INFO, "dry-run: skipping worktree creation")
            return pair

        if claude_path.exists() or codex_path.exists():
            raise FileExistsError(
                f"Worktree target(s) already exist: "
                f"claude={claude_path.exists()} codex={codex_path.exists()}"
            )

        abs_base.mkdir(parents=True, exist_ok=True)
        created: list[Path] = []
        try:
            for wt_path, branch in ((claude_path, claude_branch), (codex_path, codex_branch)):
                r = _run_git(
                    ["worktree", "add", "-b", branch, str(wt_path), "HEAD"],
                    cwd=project_root,
                    timeout=120,
                )
                if r.returncode != 0:
                    raise RuntimeError(
                        f"git worktree add failed for {wt_path}: {r.stderr.strip()}"
                    )
                created.append(wt_path)
        except Exception:
            for wt in created:
                _log(logging.WARNING, "rollback: removing worktree", path=str(wt))
                _run_git(
                    ["worktree", "remove", "--force", str(wt)],
                    cwd=project_root,
                    timeout=60,
                )
            raise

        _log(
            logging.INFO,
            "exit: create_worktrees",
            claude=str(claude_path),
            codex=str(codex_path),
        )
        return pair
    except Exception:
        logger.exception("create_worktrees failed")
        raise

# --- Codex background spawn ------------------------------------------------- #


@dataclass
class CodexJob:
    pid: Optional[int]
    log_path: Path
    command: list[str]


def spawn_codex_background(
    project_root: Path,
    spec_path: Path,
    codex_worktree: Path,
    speed: str,
    timeout: int,
    log_dir: Path,
    task_id: str,
    dry_run: bool,
) -> CodexJob:
    """Launch codex-implement.py as a detached subprocess; capture PID + log path.

    On Windows uses CREATE_NEW_PROCESS_GROUP so the child survives this
    script's exit. stdout/stderr redirected to the log file.
    """
    _log(
        logging.INFO,
        "entry: spawn_codex_background",
        spec_path=str(spec_path),
        codex_worktree=str(codex_worktree),
        speed=speed,
        dry_run=dry_run,
    )
    try:
        script = project_root / ".claude" / "scripts" / "codex-implement.py"
        if not dry_run and not script.exists():
            raise FileNotFoundError(f"codex-implement.py not found at {script}")

        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"codex-inline-{task_id}.log"

        cmd = [
            sys.executable,
            str(script),
            "--task", str(spec_path),
            "--worktree", str(codex_worktree),
            "--speed", speed,
            "--timeout", str(timeout),
        ]

        if dry_run:
            _log(logging.INFO, "dry-run: skipping codex spawn", cmd=cmd)
            return CodexJob(pid=None, log_path=log_path, command=cmd)

        creationflags = 0
        start_new_session = False
        if sys.platform == "win32":
            # CREATE_NEW_PROCESS_GROUP = 0x00000200 - detached group so we
            # don't take the child down when this script exits.
            creationflags = 0x00000200
        else:
            start_new_session = True

        # Open log file, pass to child, then close in parent. The child OS
        # process inherits its own handle; the parent's is no longer needed.
        # Leaving it open leaks a Windows handle and can prevent log rotation
        # or temp-dir cleanup in tests.
        log_fh = open(log_path, "w", encoding="utf-8", errors="replace")
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(project_root),
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                creationflags=creationflags,
                start_new_session=start_new_session,
            )
        finally:
            # Always close parent handle; subprocess has its own inherited copy.
            try:
                log_fh.close()
            except Exception:
                logger.exception("log_fh close failed (non-fatal)")

        job = CodexJob(pid=proc.pid, log_path=log_path, command=cmd)
        _log(logging.INFO, "exit: spawn_codex_background", pid=proc.pid, log=str(log_path))
        return job
    except Exception:
        logger.exception("spawn_codex_background failed")
        raise


# --- Status block ----------------------------------------------------------- #


def render_status_block(
    task_id: str,
    spec_path: Path,
    prompt_path: Path,
    pair: WorktreePair,
    codex_job: CodexJob,
    dry_run: bool,
) -> str:
    """Render the 3-section stdout block for Opus."""
    _log(logging.DEBUG, "entry: render_status_block", task_id=task_id)
    try:
        header = f"=== codex-inline-dual: task-id=inline/{task_id} "
        header += "(DRY RUN)" if dry_run else "(prepped)"
        header += " ==="

        tail_cmd = (
            f"tail -f {codex_job.log_path}" if sys.platform != "win32"
            else f"Get-Content -Path '{codex_job.log_path}' -Wait"
        )

        pid_line = (
            f"PID: {codex_job.pid}" if codex_job.pid is not None
            else "PID: (dry-run - not spawned)"
        )

        lines = [
            header,
            "",
            "--- CLAUDE TEAMMATE PROMPT ---",
            f"  prompt-file: {prompt_path}",
            f"  worktree:    {pair.claude_path}",
            f"  branch:      {pair.claude_branch}",
            "  next: spawn via Agent tool with the contents of the prompt file",
            "",
            "--- CODEX BACKGROUND JOB ---",
            f"  {pid_line}",
            f"  worktree:    {pair.codex_path}",
            f"  branch:      {pair.codex_branch}",
            f"  log:         {codex_job.log_path}",
            f"  tail:        {tail_cmd}",
            "",
            "--- NEXT STEPS ---",
            f"  judge:  py -3 .claude/scripts/judge.py --task {spec_path} "
            f"--claude {pair.claude_path} --codex {pair.codex_path}",
            f"  merge:  git merge {pair.claude_branch}   # OR {pair.codex_branch}",
            f"  cleanup: git worktree remove {pair.claude_path} && "
            f"git worktree remove {pair.codex_path}",
            "",
            "=== end ===",
        ]
        text = "\n".join(lines)
        _log(logging.DEBUG, "exit: render_status_block", bytes=len(text))
        return text
    except Exception:
        logger.exception("render_status_block failed")
        raise


# --- Main ------------------------------------------------------------------- #


@dataclass
class PrepResult:
    task_id: str
    spec_path: Path
    prompt_path: Path
    pair: WorktreePair
    codex_job: CodexJob


def prep(args: argparse.Namespace, project_root: Path) -> PrepResult:
    """End-to-end prep: spec -> worktrees -> prompt -> codex spawn. Testable unit."""
    _log(logging.INFO, "entry: prep", dry_run=args.dry_run)
    try:
        scope = parse_scope(args.scope)
        tests = [t.strip() for t in args.test if t and t.strip()]
        if not tests:
            raise ValueError("--test must contain at least one non-empty command")

        task_id = sanitize_task_id(args.task_id) if args.task_id else default_task_id()

        spec_dir = args.spec_dir if args.spec_dir.is_absolute() else (project_root / args.spec_dir)
        spec_dir.mkdir(parents=True, exist_ok=True)
        spec_path = spec_dir / f"task-{task_id}.md"
        prompt_path = spec_dir / f"{task_id}-claude-prompt.md"

        spec_text = render_task_spec(task_id, args.describe, scope, tests, args.speed)
        if args.dry_run:
            _log(logging.INFO, "dry-run: skipping spec write", path=str(spec_path))
        else:
            spec_path.write_text(spec_text, encoding="utf-8")
            _log(logging.INFO, "wrote spec", path=str(spec_path), bytes=len(spec_text))

        pair = create_worktrees(project_root, args.worktree_base, task_id, args.dry_run)

        prompt_text = render_claude_prompt(
            task_id=task_id,
            describe=args.describe,
            scope=scope,
            tests=tests,
            spec_path=spec_path,
            worktree_claude=pair.claude_path,
        )
        if args.dry_run:
            _log(logging.INFO, "dry-run: skipping prompt write", path=str(prompt_path))
        else:
            prompt_path.write_text(prompt_text, encoding="utf-8")
            _log(logging.INFO, "wrote prompt", path=str(prompt_path), bytes=len(prompt_text))

        log_dir = args.log_dir if args.log_dir.is_absolute() else (project_root / args.log_dir)
        codex_job = spawn_codex_background(
            project_root=project_root,
            spec_path=spec_path,
            codex_worktree=pair.codex_path,
            speed=args.speed,
            timeout=args.codex_timeout,
            log_dir=log_dir,
            task_id=task_id,
            dry_run=args.dry_run,
        )

        result = PrepResult(
            task_id=task_id,
            spec_path=spec_path,
            prompt_path=prompt_path,
            pair=pair,
            codex_job=codex_job,
        )
        _log(logging.INFO, "exit: prep", task_id=task_id, dry_run=args.dry_run)
        return result
    except Exception:
        logger.exception("prep failed")
        raise


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        project_root = find_project_root(Path.cwd())
        log_dir = args.log_dir if args.log_dir.is_absolute() else (project_root / args.log_dir)
        log_file = log_dir / "codex-inline-dual.log"
        setup_logging(log_file)
    except Exception as exc:
        print(f"fatal: setup failed: {exc}", file=sys.stderr)
        return EXIT_FATAL

    _log(logging.INFO, "entry: main", argv=sys.argv[1:])

    try:
        result = prep(args, project_root)
    except Exception as exc:
        print(f"fatal: prep failed: {exc}", file=sys.stderr)
        _log(logging.ERROR, "exit: main", exit_code=EXIT_FATAL)
        return EXIT_FATAL

    status = render_status_block(
        task_id=result.task_id,
        spec_path=result.spec_path,
        prompt_path=result.prompt_path,
        pair=result.pair,
        codex_job=result.codex_job,
        dry_run=args.dry_run,
    )
    print(status)
    _log(logging.INFO, "exit: main", exit_code=EXIT_OK, task_id=result.task_id)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())