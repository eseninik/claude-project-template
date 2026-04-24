#!/usr/bin/env python3
"""Codex Implement — single-task Codex executor.

Reads a task-N.md file, runs `codex exec` in a workspace-write sandbox
scoped to the task's worktree, captures the diff, validates against the
Scope Fence, runs Test Commands, and writes a standardized
`work/codex-implementations/task-{N}-result.md`.

Exit codes:
    0 = tests pass (scope ok)
    1 = tests fail but scope ok
    2 = scope violation OR timeout OR fatal error

Usage:
    py -3 .claude/scripts/codex-implement.py \\
        --task work/codex-primary/tasks/T1.md \\
        --worktree . \\
        [--reasoning high] \\
        [--timeout 3600] \\
        [--result-dir work/codex-implementations]
"""

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

if sys.platform == "win32":
    for _s in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")


# --------------------------------------------------------------------------- #
# Logging                                                                     #
# --------------------------------------------------------------------------- #

logger = logging.getLogger("codex_implement")


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
    """Configure root logger with JSON formatter + optional file sink."""
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


# --------------------------------------------------------------------------- #
# Exit codes                                                                  #
# --------------------------------------------------------------------------- #

EXIT_OK = 0
EXIT_TEST_FAIL = 1
EXIT_SCOPE_OR_TIMEOUT = 2


# --------------------------------------------------------------------------- #
# Data structures                                                             #
# --------------------------------------------------------------------------- #


@dataclass
class ScopeFence:
    allowed: list[str] = field(default_factory=list)
    forbidden: list[str] = field(default_factory=list)


@dataclass
class Task:
    path: Path
    task_id: str
    frontmatter: dict[str, str]
    sections: dict[str, str]
    scope_fence: ScopeFence
    test_commands: list[str]
    acceptance_criteria: list[str]
    skill_contracts: str

    @property
    def body(self) -> str:
        return self.path.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Parsing                                                                     #
# --------------------------------------------------------------------------- #


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse YAML-ish frontmatter (key: value pairs). Return (frontmatter, body)."""
    _log(logging.DEBUG, "entry: parse_frontmatter", text_len=len(text))
    try:
        fm: dict[str, str] = {}
        if not text.startswith("---\n") and not text.startswith("---\r\n"):
            _log(logging.DEBUG, "exit: parse_frontmatter", has_frontmatter=False)
            return fm, text

        end = text.find("\n---", 4)
        if end == -1:
            _log(logging.WARNING, "frontmatter open without close")
            return fm, text

        block = text[4:end]
        body_start = end + len("\n---")
        if body_start < len(text) and text[body_start] == "\r":
            body_start += 1
        if body_start < len(text) and text[body_start] == "\n":
            body_start += 1
        body = text[body_start:]

        for line in block.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()

        _log(logging.DEBUG, "exit: parse_frontmatter", keys=list(fm.keys()))
        return fm, body
    except Exception:
        logger.exception("parse_frontmatter failed")
        raise


def split_sections(body: str) -> dict[str, str]:
    """Split markdown body into ## sections. Key = heading text (without ##)."""
    _log(logging.DEBUG, "entry: split_sections", body_len=len(body))
    try:
        sections: dict[str, str] = {}
        current_key: Optional[str] = None
        current_lines: list[str] = []

        for raw_line in body.splitlines():
            m = re.match(r"^##\s+(?!#)(.+?)\s*$", raw_line)
            if m:
                if current_key is not None:
                    sections[current_key] = "\n".join(current_lines).strip("\n")
                current_key = m.group(1).strip()
                current_lines = []
            else:
                current_lines.append(raw_line)

        if current_key is not None:
            sections[current_key] = "\n".join(current_lines).strip("\n")

        _log(logging.DEBUG, "exit: split_sections", section_count=len(sections))
        return sections
    except Exception:
        logger.exception("split_sections failed")
        raise


def parse_scope_fence(section_text: str) -> ScopeFence:
    """Extract allowed/forbidden paths from a Scope Fence section."""
    _log(logging.DEBUG, "entry: parse_scope_fence", text_len=len(section_text))
    try:
        fence = ScopeFence()
        if not section_text:
            _log(logging.DEBUG, "exit: parse_scope_fence", allowed=0, forbidden=0)
            return fence

        mode: Optional[str] = None
        for line in section_text.splitlines():
            stripped = line.strip()
            low = stripped.lower()

            if low.startswith("**allowed"):
                mode = "allowed"
                continue
            if low.startswith("**forbidden"):
                mode = "forbidden"
                continue

            if stripped.startswith("- ") and mode is not None:
                entry = stripped[2:].strip()
                # Drop trailing parenthetical comments first (they sit outside backticks)
                entry = re.split(r"\s+\(", entry, maxsplit=1)[0].strip()
                # Then strip inline backticks (e.g., `path/to/file`)
                entry = entry.strip("`").strip()
                if not entry:
                    continue
                if mode == "allowed":
                    fence.allowed.append(entry)
                else:
                    fence.forbidden.append(entry)

        _log(
            logging.DEBUG,
            "exit: parse_scope_fence",
            allowed=len(fence.allowed),
            forbidden=len(fence.forbidden),
        )
        return fence
    except Exception:
        logger.exception("parse_scope_fence failed")
        raise


def parse_test_commands(section_text: str) -> list[str]:
    """Extract shell commands from ```bash fenced blocks."""
    _log(logging.DEBUG, "entry: parse_test_commands", text_len=len(section_text))
    try:
        commands: list[str] = []
        if not section_text:
            return commands

        in_block = False
        current: list[str] = []
        for line in section_text.splitlines():
            fence = line.strip()
            if fence.startswith("```"):
                if not in_block:
                    in_block = True
                    current = []
                else:
                    in_block = False
                    for cmd in current:
                        cmd = cmd.strip()
                        if not cmd or cmd.startswith("#"):
                            continue
                        commands.append(cmd)
                    current = []
                continue
            if in_block:
                current.append(line)

        _log(logging.DEBUG, "exit: parse_test_commands", count=len(commands))
        return commands
    except Exception:
        logger.exception("parse_test_commands failed")
        raise


def parse_acceptance_criteria(section_text: str) -> list[str]:
    """Extract `- [ ] ...` bullet lines."""
    _log(logging.DEBUG, "entry: parse_acceptance_criteria", text_len=len(section_text))
    try:
        out: list[str] = []
        if not section_text:
            return out
        for line in section_text.splitlines():
            m = re.match(r"^\s*-\s*\[.\]\s*(.+)$", line)
            if m:
                out.append(m.group(1).strip())
        _log(logging.DEBUG, "exit: parse_acceptance_criteria", count=len(out))
        return out
    except Exception:
        logger.exception("parse_acceptance_criteria failed")
        raise


def _derive_task_id(path: Path) -> str:
    """Extract numeric/string task id from filename like `T1-foo.md` or `task-2.md`."""
    _log(logging.DEBUG, "entry: _derive_task_id", path=str(path))
    try:
        stem = path.stem
        m = re.match(r"^T(\d+)", stem, re.IGNORECASE)
        if m:
            task_id = m.group(1)
        else:
            m = re.match(r"^task-(\w+)", stem, re.IGNORECASE)
            task_id = m.group(1) if m else stem
        _log(logging.DEBUG, "exit: _derive_task_id", task_id=task_id)
        return task_id
    except Exception:
        logger.exception("_derive_task_id failed")
        raise


def parse_task_file(task_path: Path) -> Task:
    """Read and parse a task-N.md file into a Task struct."""
    _log(logging.DEBUG, "entry: parse_task_file", task_path=str(task_path))
    try:
        if not task_path.exists():
            raise FileNotFoundError(f"Task file not found: {task_path}")

        text = task_path.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(text)
        sections = split_sections(body)

        scope_fence = parse_scope_fence(sections.get("Scope Fence", ""))
        test_commands = parse_test_commands(
            sections.get("Test Commands (run after implementation)", "")
            or sections.get("Test Commands", "")
        )
        acceptance = parse_acceptance_criteria(
            sections.get("Acceptance Criteria (IMMUTABLE)", "")
            or sections.get("Acceptance Criteria", "")
        )
        skill_contracts = sections.get("Skill Contracts", "") or sections.get(
            "Skill Contracts (Opus extracted these from skills)", ""
        )

        task = Task(
            path=task_path,
            task_id=_derive_task_id(task_path),
            frontmatter=frontmatter,
            sections=sections,
            scope_fence=scope_fence,
            test_commands=test_commands,
            acceptance_criteria=acceptance,
            skill_contracts=skill_contracts,
        )
        _log(
            logging.INFO,
            "parsed task",
            task_id=task.task_id,
            sections=list(sections.keys()),
            test_commands=len(test_commands),
        )
        _log(logging.DEBUG, "exit: parse_task_file", task_id=task.task_id)
        return task
    except Exception:
        logger.exception("parse_task_file failed")
        raise


# --------------------------------------------------------------------------- #
# Git helpers                                                                 #
# --------------------------------------------------------------------------- #


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
            stdout_len=len(result.stdout),
            stderr_len=len(result.stderr),
        )
        return result
    except subprocess.TimeoutExpired:
        logger.exception("_run_git timed out")
        raise
    except Exception:
        logger.exception("_run_git failed")
        raise


class DirtyWorktreeError(RuntimeError):
    """Raised when the worktree has uncommitted changes before Codex runs.

    Rationale: codex-implement.py's rollback path (git reset --hard + git clean -fd)
    is safe ONLY if the pre-run tree is clean. Otherwise rollback destroys user work
    unrelated to the Codex run. Refuse at the gate rather than risk data loss.
    """


def check_tree_clean(worktree: Path) -> tuple[bool, list[str]]:
    """Return (is_clean, list_of_dirty_lines). Dirty = any tracked mod OR untracked file.

    Uses `git status --porcelain` (not --porcelain=2 — we only need emptiness + names).
    Ignored files are excluded by default, which matches intent (untracked-ignored is OK).
    """
    _log(logging.DEBUG, "entry: check_tree_clean", worktree=str(worktree))
    try:
        r = _run_git(["status", "--porcelain"], cwd=worktree, timeout=30)
        if r.returncode != 0:
            raise RuntimeError(f"git status failed in {worktree}: {r.stderr.strip()}")
        lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
        is_clean = len(lines) == 0
        _log(
            logging.DEBUG,
            "exit: check_tree_clean",
            is_clean=is_clean,
            dirty_count=len(lines),
        )
        return is_clean, lines
    except Exception:
        logger.exception("check_tree_clean failed")
        raise


def preflight_worktree(worktree: Path) -> str:
    """Verify worktree is a git dir AND clean; return HEAD sha.

    Refuses to proceed on a dirty tree — Codex rollback (git reset --hard + git clean -fd)
    would destroy pre-existing uncommitted work. Users must commit/stash/discard first.
    """
    _log(logging.DEBUG, "entry: preflight_worktree", worktree=str(worktree))
    try:
        if not worktree.exists():
            raise FileNotFoundError(f"Worktree path does not exist: {worktree}")

        inside = _run_git(["rev-parse", "--is-inside-work-tree"], cwd=worktree)
        if inside.returncode != 0 or inside.stdout.strip() != "true":
            raise RuntimeError(
                f"Worktree is not inside a git work tree: {worktree} (stderr={inside.stderr.strip()})"
            )

        head = _run_git(["rev-parse", "HEAD"], cwd=worktree)
        if head.returncode != 0:
            raise RuntimeError(
                f"Could not read HEAD in {worktree}: {head.stderr.strip()}"
            )

        is_clean, dirty_lines = check_tree_clean(worktree)
        if not is_clean:
            preview = "\n  ".join(dirty_lines[:15])
            more = f"\n  ... +{len(dirty_lines) - 15} more" if len(dirty_lines) > 15 else ""
            raise DirtyWorktreeError(
                "Refusing to run codex-implement.py on a dirty working tree. "
                "Rollback on scope violation would destroy unrelated uncommitted work.\n"
                "Please commit, stash (`git stash push -u`), or discard changes first.\n"
                f"Dirty entries ({len(dirty_lines)}):\n  {preview}{more}"
            )

        sha = head.stdout.strip()
        _log(logging.INFO, "preflight ok", head=sha, worktree=str(worktree), tree="clean")
        _log(logging.DEBUG, "exit: preflight_worktree", head=sha)
        return sha
    except Exception:
        logger.exception("preflight_worktree failed")
        raise


def capture_diff(worktree: Path, base_sha: str) -> str:
    """Return unified `git diff <base_sha>` output (includes uncommitted changes)."""
    _log(logging.DEBUG, "entry: capture_diff", worktree=str(worktree), base_sha=base_sha)
    try:
        r = _run_git(["diff", base_sha], cwd=worktree, timeout=120)
        if r.returncode not in (0, 1):
            _log(logging.WARNING, "git diff non-zero", returncode=r.returncode)
        _log(logging.DEBUG, "exit: capture_diff", diff_len=len(r.stdout))
        return r.stdout
    except Exception:
        logger.exception("capture_diff failed")
        raise


def rollback_worktree(worktree: Path, base_sha: str) -> None:
    """`git reset --hard <base_sha>` + `git clean -fd` to restore baseline."""
    _log(logging.WARNING, "entry: rollback_worktree", worktree=str(worktree), base_sha=base_sha)
    try:
        _run_git(["reset", "--hard", base_sha], cwd=worktree, timeout=120)
        _run_git(["clean", "-fd"], cwd=worktree, timeout=60)
        _log(logging.WARNING, "exit: rollback_worktree")
    except Exception:
        logger.exception("rollback_worktree failed")


# --------------------------------------------------------------------------- #
# Codex invocation                                                            #
# --------------------------------------------------------------------------- #


def build_codex_prompt(task: Task) -> str:
    """Build prompt embedding full task-N.md content + execution instructions."""
    _log(logging.DEBUG, "entry: build_codex_prompt", task_id=task.task_id)
    try:
        header = (
            "You are the single-task implementer. The task specification below is IMMUTABLE.\n"
            "Write code to satisfy all Acceptance Criteria. Do NOT modify files listed in\n"
            "Forbidden Paths or Read-Only Files. After writing code, run every Test Command\n"
            "listed in the task and report the result in your self-report.\n"
            "Any AGENTS.md or CLAUDE.md in the worktree is authoritative background context.\n"
            "\n---- TASK SPECIFICATION ----\n\n"
        )
        footer = (
            "\n\n---- END TASK SPECIFICATION ----\n"
            "Return a short self-report at the end of your run using lines starting with\n"
            "`NOTE:` for observations and `BLOCKER:` for unresolved problems.\n"
        )
        prompt = header + task.body + footer
        _log(logging.DEBUG, "exit: build_codex_prompt", prompt_len=len(prompt))
        return prompt
    except Exception:
        logger.exception("build_codex_prompt failed")
        raise


@dataclass
class CodexRunResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    self_report: list[str]


def run_codex(
    prompt: str,
    worktree: Path,
    reasoning: str,
    timeout: int,
) -> CodexRunResult:
    """Invoke `codex exec` in workspace-write mode. Returns structured result."""
    _log(
        logging.INFO,
        "entry: run_codex",
        worktree=str(worktree),
        reasoning=reasoning,
        timeout=timeout,
        prompt_len=len(prompt),
    )
    try:
        codex = shutil.which("codex")
        if not codex:
            raise RuntimeError("codex CLI not found in PATH")

        cmd = [
            codex,
            "exec",
            "--model",
            "gpt-5.5",
            "--sandbox",
            "workspace-write",
            "--full-auto",
            "--cd",
            str(worktree.resolve()),
            prompt,
        ]
        _log(logging.INFO, "codex cmd", argv_head=cmd[:9])

        try:
            proc = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as te:
            _log(logging.ERROR, "codex timeout", seconds=timeout)
            return CodexRunResult(
                returncode=-1,
                stdout=(te.stdout or "") if isinstance(te.stdout, str) else "",
                stderr=(te.stderr or "") if isinstance(te.stderr, str) else "",
                timed_out=True,
                self_report=[],
            )

        self_report = [
            line
            for line in proc.stdout.splitlines()
            if line.strip().startswith(("NOTE:", "BLOCKER:"))
        ]

        _log(
            logging.INFO,
            "exit: run_codex",
            returncode=proc.returncode,
            stdout_len=len(proc.stdout),
            stderr_len=len(proc.stderr),
            self_report=len(self_report),
        )
        return CodexRunResult(
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            timed_out=False,
            self_report=self_report,
        )
    except Exception:
        logger.exception("run_codex failed")
        raise


# --------------------------------------------------------------------------- #
# Scope check                                                                 #
# --------------------------------------------------------------------------- #


@dataclass
class ScopeCheckResult:
    status: str  # "pass" | "fail" | "skipped"
    message: str
    violations: list[str] = field(default_factory=list)


def run_scope_check(
    diff_path: Path,
    fence_paths: ScopeFence,
    project_root: Path,
) -> ScopeCheckResult:
    """Invoke codex-scope-check.py if present; skip gracefully otherwise."""
    _log(logging.DEBUG, "entry: run_scope_check", diff_path=str(diff_path))
    try:
        script = project_root / ".claude" / "scripts" / "codex-scope-check.py"
        if not script.exists():
            msg = f"codex-scope-check.py not found at {script}; scope check SKIPPED"
            _log(logging.WARNING, msg)
            return ScopeCheckResult(status="skipped", message=msg)

        allowed = ",".join(fence_paths.allowed)
        cmd = [
            sys.executable,
            str(script),
            "--diff",
            str(diff_path),
            "--fence",
            allowed,
        ]
        r = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        if r.returncode == 0:
            _log(logging.INFO, "scope check pass")
            return ScopeCheckResult(status="pass", message=r.stdout.strip() or "in-scope")
        violations = [
            ln.strip() for ln in (r.stdout + "\n" + r.stderr).splitlines() if ln.strip()
        ]
        _log(logging.ERROR, "scope check fail", violations=violations)
        return ScopeCheckResult(
            status="fail",
            message=r.stderr.strip() or r.stdout.strip() or "scope violation",
            violations=violations,
        )
    except subprocess.TimeoutExpired:
        logger.exception("scope check timed out")
        return ScopeCheckResult(status="fail", message="scope-check timeout")
    except Exception:
        logger.exception("run_scope_check failed")
        return ScopeCheckResult(status="fail", message="scope-check exception")


# --------------------------------------------------------------------------- #
# Test runner                                                                 #
# --------------------------------------------------------------------------- #


@dataclass
class TestRunResult:
    all_passed: bool
    outputs: list[dict[str, object]]


def run_test_commands(
    commands: list[str],
    worktree: Path,
    per_cmd_timeout: int = 600,
) -> TestRunResult:
    """Run each Test Command in sequence; capture output and aggregate pass/fail."""
    _log(logging.INFO, "entry: run_test_commands", count=len(commands))
    try:
        outputs: list[dict[str, object]] = []
        all_passed = True

        if not commands:
            _log(logging.WARNING, "no test commands declared")

        for cmd in commands:
            _log(logging.INFO, "running test command", cmd=cmd)
            try:
                r = subprocess.run(
                    cmd,
                    cwd=str(worktree),
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=per_cmd_timeout,
                    shell=True,
                )
                passed = r.returncode == 0
                outputs.append(
                    {
                        "cmd": cmd,
                        "returncode": r.returncode,
                        "stdout": r.stdout,
                        "stderr": r.stderr,
                        "passed": passed,
                        "timed_out": False,
                    }
                )
                if not passed:
                    all_passed = False
                    _log(
                        logging.WARNING,
                        "test command failed",
                        cmd=cmd,
                        returncode=r.returncode,
                    )
            except subprocess.TimeoutExpired as te:
                all_passed = False
                outputs.append(
                    {
                        "cmd": cmd,
                        "returncode": -1,
                        "stdout": (te.stdout or "") if isinstance(te.stdout, str) else "",
                        "stderr": (te.stderr or "") if isinstance(te.stderr, str) else "",
                        "passed": False,
                        "timed_out": True,
                    }
                )
                _log(logging.ERROR, "test command timed out", cmd=cmd, seconds=per_cmd_timeout)

        _log(logging.INFO, "exit: run_test_commands", all_passed=all_passed)
        return TestRunResult(all_passed=all_passed, outputs=outputs)
    except Exception:
        logger.exception("run_test_commands failed")
        raise


# --------------------------------------------------------------------------- #
# Result writing                                                              #
# --------------------------------------------------------------------------- #


def map_status_to_exit(
    status: str,
    scope_status: str,
    tests_ok: bool,
) -> int:
    """Map high-level status to process exit code."""
    _log(
        logging.DEBUG,
        "entry: map_status_to_exit",
        status=status,
        scope_status=scope_status,
        tests_ok=tests_ok,
    )
    try:
        if status in {"scope-violation", "timeout"}:
            return EXIT_SCOPE_OR_TIMEOUT
        if scope_status == "fail":
            return EXIT_SCOPE_OR_TIMEOUT
        if not tests_ok:
            return EXIT_TEST_FAIL
        return EXIT_OK
    finally:
        _log(logging.DEBUG, "exit: map_status_to_exit")


def write_result_file(
    result_path: Path,
    task: Task,
    status: str,
    diff: str,
    test_run: Optional[TestRunResult],
    codex_run: Optional[CodexRunResult],
    scope: Optional[ScopeCheckResult],
    base_sha: str,
    timestamp: str,
) -> None:
    """Write `work/codex-implementations/task-{N}-result.md` with standard schema."""
    _log(logging.INFO, "entry: write_result_file", result_path=str(result_path), status=status)
    try:
        result_path.parent.mkdir(parents=True, exist_ok=True)

        self_report_lines = codex_run.self_report if codex_run else []
        codex_rc = codex_run.returncode if codex_run else "N/A"
        codex_stderr = codex_run.stderr if codex_run else ""
        scope_status = scope.status if scope else "skipped"
        scope_message = scope.message if scope else "scope check not run"

        parts: list[str] = []
        parts.append(f"# Codex Implementation Result — Task {task.task_id}")
        parts.append("")
        parts.append(f"- status: {status}")
        parts.append(f"- timestamp: {timestamp}")
        parts.append(f"- task_file: {task.path}")
        parts.append(f"- base_sha: {base_sha}")
        parts.append(f"- codex_returncode: {codex_rc}")
        parts.append(f"- scope_status: {scope_status}")
        if scope_message:
            parts.append(f"- scope_message: {scope_message}")
        if scope and scope.violations:
            parts.append("- scope_violations:")
            for v in scope.violations:
                parts.append(f"  - {v}")
        if test_run is not None:
            parts.append(f"- tests_all_passed: {test_run.all_passed}")
            parts.append(f"- test_commands_count: {len(test_run.outputs)}")

        parts.append("")
        parts.append("## Diff")
        parts.append("")
        parts.append("```diff")
        parts.append(diff.rstrip() if diff else "(no changes)")
        parts.append("```")

        parts.append("")
        parts.append("## Test Output")
        parts.append("")
        if test_run is None or not test_run.outputs:
            parts.append("(no test commands executed)")
        else:
            for out in test_run.outputs:
                parts.append(f"### `{out['cmd']}`")
                parts.append("")
                parts.append(
                    f"- returncode: {out['returncode']}  "
                    f"- passed: {out['passed']}  "
                    f"- timed_out: {out['timed_out']}"
                )
                parts.append("")
                parts.append("```")
                stdout = str(out.get("stdout", ""))
                stderr = str(out.get("stderr", ""))
                if stdout.strip():
                    parts.append("--- stdout ---")
                    parts.append(stdout.rstrip())
                if stderr.strip():
                    parts.append("--- stderr ---")
                    parts.append(stderr.rstrip())
                parts.append("```")
                parts.append("")

        parts.append("## Self-Report (Codex NOTE/BLOCKER lines)")
        parts.append("")
        if self_report_lines:
            for line in self_report_lines:
                parts.append(f"- {line.strip()}")
        else:
            parts.append("(no NOTE/BLOCKER lines)")

        if codex_stderr.strip():
            parts.append("")
            parts.append("## Codex stderr")
            parts.append("")
            parts.append("```")
            parts.append(codex_stderr.rstrip())
            parts.append("```")

        result_path.write_text("\n".join(parts) + "\n", encoding="utf-8")
        _log(logging.INFO, "exit: write_result_file", bytes=result_path.stat().st_size)
    except Exception:
        logger.exception("write_result_file failed")
        raise


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #


def build_arg_parser() -> argparse.ArgumentParser:
    """CLI spec matches tech-spec 6.1."""
    _log(logging.DEBUG, "entry: build_arg_parser")
    try:
        p = argparse.ArgumentParser(
            prog="codex-implement.py",
            description="Run Codex CLI against a task-N.md spec (workspace-write sandbox).",
        )
        p.add_argument("--task", required=True, type=Path,
                       help="Path to task-N.md file")
        p.add_argument("--worktree", default=Path("."), type=Path,
                       help="Path to worktree dir (defaults to cwd)")
        p.add_argument("--reasoning", default=None, choices=["high", "medium", "low"],
                       help="Override frontmatter reasoning effort")
        p.add_argument("--timeout", default=3600, type=int,
                       help="Timeout in seconds for codex exec (default 3600)")
        p.add_argument("--result-dir", default=Path("work/codex-implementations"), type=Path,
                       help="Directory for task-{N}-result.md output")
        p.add_argument("--log-dir", default=Path("work/codex-primary/logs"), type=Path,
                       help="Directory for structured logs")
        _log(logging.DEBUG, "exit: build_arg_parser")
        return p
    except Exception:
        logger.exception("build_arg_parser failed")
        raise


def find_project_root(start: Path) -> Path:
    """Walk up from `start` until we hit a dir containing `.claude` or `.git`."""
    _log(logging.DEBUG, "entry: find_project_root", start=str(start))
    try:
        current = start.resolve()
        for candidate in [current, *current.parents]:
            if (candidate / ".claude").is_dir() or (candidate / ".git").exists():
                _log(logging.DEBUG, "exit: find_project_root", root=str(candidate))
                return candidate
        _log(logging.WARNING, "project root not found; using start", start=str(current))
        return current
    except Exception:
        logger.exception("find_project_root failed")
        raise


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        task_path = args.task.resolve()
        worktree = args.worktree.resolve()
        result_dir = args.result_dir if args.result_dir.is_absolute() else (worktree / args.result_dir)
        log_dir = args.log_dir if args.log_dir.is_absolute() else (worktree / args.log_dir)

        task_id_guess = _derive_task_id(task_path)
        log_file = log_dir / f"codex-implement-T{task_id_guess}.log"
        setup_logging(log_file)
    except Exception as exc:
        print(f"fatal: setup failed: {exc}", file=sys.stderr)
        return EXIT_SCOPE_OR_TIMEOUT

    _log(logging.INFO, "entry: main", argv=sys.argv[1:])

    try:
        task = parse_task_file(task_path)
    except Exception as exc:
        print(f"fatal: could not parse task file: {exc}", file=sys.stderr)
        return EXIT_SCOPE_OR_TIMEOUT

    if args.reasoning:
        task.frontmatter["reasoning"] = args.reasoning

    try:
        base_sha = preflight_worktree(worktree)
    except Exception as exc:
        print(f"fatal: preflight failed: {exc}", file=sys.stderr)
        return EXIT_SCOPE_OR_TIMEOUT

    timestamp = datetime.now(timezone.utc).isoformat()
    project_root = find_project_root(worktree)

    prompt = build_codex_prompt(task)

    codex_run: Optional[CodexRunResult] = None
    test_run: Optional[TestRunResult] = None
    scope: Optional[ScopeCheckResult] = None
    status = "pass"
    diff_text = ""

    try:
        codex_run = run_codex(
            prompt=prompt,
            worktree=worktree,
            reasoning=task.frontmatter.get("reasoning", "high"),
            timeout=args.timeout,
        )

        if codex_run.timed_out:
            status = "timeout"
            rollback_worktree(worktree, base_sha)
        else:
            diff_text = capture_diff(worktree, base_sha)

            diff_file = result_dir / f"task-{task.task_id}.diff"
            diff_file.parent.mkdir(parents=True, exist_ok=True)
            diff_file.write_text(diff_text, encoding="utf-8")

            scope = run_scope_check(diff_file, task.scope_fence, project_root)
            if scope.status == "fail":
                status = "scope-violation"
                rollback_worktree(worktree, base_sha)
                diff_text = ""  # rollback voids diff
            else:
                test_run = run_test_commands(task.test_commands, worktree)
                if codex_run.returncode != 0 and not test_run.all_passed:
                    status = "fail"
                elif not test_run.all_passed:
                    status = "fail"
                elif codex_run.returncode != 0:
                    status = "fail"
                else:
                    status = "pass"

        result_path = result_dir / f"task-{task.task_id}-result.md"
        write_result_file(
            result_path=result_path,
            task=task,
            status=status,
            diff=diff_text,
            test_run=test_run,
            codex_run=codex_run,
            scope=scope,
            base_sha=base_sha,
            timestamp=timestamp,
        )

        tests_ok = test_run.all_passed if test_run is not None else False
        scope_status = scope.status if scope else "skipped"
        exit_code = map_status_to_exit(status, scope_status, tests_ok)

        print(
            f"codex-implement: task={task.task_id} status={status} "
            f"scope={scope_status} tests_ok={tests_ok} exit={exit_code}"
        )
        print(f"result: {result_path}")
        _log(logging.INFO, "exit: main", status=status, exit_code=exit_code)
        return exit_code

    except Exception as exc:
        logger.exception("main failed")
        try:
            result_path = result_dir / f"task-{task.task_id}-result.md"
            write_result_file(
                result_path=result_path,
                task=task,
                status="fail",
                diff=diff_text,
                test_run=test_run,
                codex_run=codex_run,
                scope=scope,
                base_sha=base_sha,
                timestamp=timestamp,
            )
        except Exception:
            logger.exception("failed to write result after exception")
        print(f"fatal: {exc}", file=sys.stderr)
        return EXIT_SCOPE_OR_TIMEOUT


if __name__ == "__main__":
    sys.exit(main())
