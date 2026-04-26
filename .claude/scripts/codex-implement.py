#!/usr/bin/env python3
"""Codex Implement — single-task Codex executor.

Reads a task-N.md file, runs `codex exec` with danger-full-access in a
disposable git worktree (Y26: Codex CLI v0.125 silently ignores the
`--sandbox workspace-write` flag for `exec` mode — sandbox is always
read-only unless `--dangerously-bypass-approvals-and-sandbox` is used),
captures the diff, validates against the Scope Fence, runs Test
Commands, and writes a standardized
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
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
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
EXIT_DEGRADED = 3  # T9: circuit open - Codex not invoked

# --- T8+T9 Stability: rate-limit backoff + circuit breaker ----------------- #

RATE_LIMIT_PATTERNS = (
    re.compile(r"rate[\s_-]*limit", re.IGNORECASE),
    re.compile(r"\b429\b"),
    re.compile(r"stream disconnected before completion", re.IGNORECASE),
)
BACKOFF_SEQUENCE_S = (1, 2, 4, 8)        # AC2
MAX_RETRIES = 4                          # AC2
CIRCUIT_FAILURE_WINDOW_S = 15 * 60       # AC4
CIRCUIT_FAILURE_THRESHOLD = 3            # AC5
CIRCUIT_OPEN_TTL_S = 5 * 60              # AC5


def is_rate_limit_error(stderr: str) -> bool:
    """AC1: True iff stderr matches rate-limit / 429 / stream-disconnect patterns."""
    _log(logging.DEBUG, "entry: is_rate_limit_error", stderr_len=len(stderr or ""))
    if not stderr:
        return False
    for pat in RATE_LIMIT_PATTERNS:
        if pat.search(stderr):
            _log(logging.DEBUG, "exit: is_rate_limit_error", matched=pat.pattern)
            return True
    return False


def _atomic_write_json(path: Path, payload: dict) -> None:
    """AC9: temp-file + os.replace (Windows-safe atomic)."""
    _log(logging.DEBUG, "entry: _atomic_write_json", path=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".circuit-", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception:
        try: os.unlink(tmp)
        except OSError: pass
        logger.exception("_atomic_write_json failed"); raise


def read_circuit_state(project_root: Path) -> dict:
    """AC4: {failures: [...], updated_at: iso}; empty on missing/corrupt."""
    state_path = project_root / ".codex" / "circuit-state.json"
    _log(logging.DEBUG, "entry: read_circuit_state", path=str(state_path))
    now_iso = datetime.now(timezone.utc).isoformat()
    if not state_path.exists():
        return {"failures": [], "updated_at": now_iso}
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("failures"), list):
            raise ValueError("bad schema")
        data.setdefault("updated_at", now_iso)
        return data
    except (OSError, ValueError, json.JSONDecodeError):
        _log(logging.WARNING, "circuit state corrupt, resetting", path=str(state_path))
        return {"failures": [], "updated_at": now_iso}


def record_codex_failure(project_root: Path, task_id: str, reason: str) -> int:
    """AC3+AC5: append failure; open circuit when recent count >= threshold."""
    _log(logging.INFO, "entry: record_codex_failure", task_id=task_id, reason=reason)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=CIRCUIT_FAILURE_WINDOW_S)
    state = read_circuit_state(project_root)
    kept = []
    for item in state.get("failures", []) or []:
        if not isinstance(item, dict): continue
        try: ts = datetime.fromisoformat(item.get("timestamp", ""))
        except ValueError: continue
        if ts >= cutoff: kept.append(item)
    kept.append({"timestamp": now.isoformat(), "task_id": task_id})
    state_path = project_root / ".codex" / "circuit-state.json"
    _atomic_write_json(state_path, {"failures": kept, "updated_at": now.isoformat()})
    count = len(kept)
    _log(logging.WARNING, "codex failure recorded", task_id=task_id,
         recent_failures=count, threshold=CIRCUIT_FAILURE_THRESHOLD)
    if count >= CIRCUIT_FAILURE_THRESHOLD:
        expires = now + timedelta(seconds=CIRCUIT_OPEN_TTL_S)
        _atomic_write_json(project_root / ".codex" / "circuit-open",
            {"opened_at": now.isoformat(), "expires_at": expires.isoformat(), "reason": reason})
        _log(logging.ERROR, "circuit opened", expires_at=expires.isoformat(), reason=reason)
    return count


def record_codex_success(project_root: Path) -> None:
    """AC8: reset failures list (circuit health restored)."""
    _log(logging.INFO, "entry: record_codex_success")
    _atomic_write_json(project_root / ".codex" / "circuit-state.json",
        {"failures": [], "updated_at": datetime.now(timezone.utc).isoformat()})


def check_circuit_open(project_root: Path) -> Optional[dict]:
    """AC6+AC7: return flag payload if active; delete if expired; None if absent."""
    flag = project_root / ".codex" / "circuit-open"
    _log(logging.DEBUG, "entry: check_circuit_open", path=str(flag))
    if not flag.exists():
        return None
    try:
        payload = json.loads(flag.read_text(encoding="utf-8"))
        expires = datetime.fromisoformat(payload["expires_at"])
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        _log(logging.WARNING, "circuit flag corrupt, removing", path=str(flag))
        try: flag.unlink()
        except OSError: pass
        return None
    if datetime.now(timezone.utc) >= expires:
        _log(logging.INFO, "circuit flag expired, clearing", expires_at=payload["expires_at"])
        try: flag.unlink()
        except OSError: pass
        return None
    _log(logging.WARNING, "circuit_open_skip", expires_at=payload["expires_at"])
    return payload



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
    """Split markdown body into ## sections. Key = heading text (without ##).

    Headings with descriptive suffixes like ``## Scope Fence - paths`` are
    also registered under the prefix key (``Scope Fence``) for stable lookups.
    """
    _log(logging.DEBUG, "entry: split_sections", body_len=len(body))
    try:
        sections: dict[str, str] = {}
        current_key: Optional[str] = None
        current_keys: list[str] = []
        current_lines: list[str] = []

        for raw_line in body.splitlines():
            m = re.match(r"^##\s+(?!#)(.+?)\s*$", raw_line)
            if m:
                if current_key is not None:
                    section_text = "\n".join(current_lines).strip("\n")
                    for key in current_keys:
                        sections[key] = section_text
                current_key = m.group(1).strip()
                current_keys = [current_key]
                alias = re.split(r"\s[-—]\s", current_key, maxsplit=1)[0].strip()
                if alias and alias != current_key:
                    current_keys.append(alias)
                current_lines = []
            else:
                current_lines.append(raw_line)

        if current_key is not None:
            section_text = "\n".join(current_lines).strip("\n")
            for key in current_keys:
                sections[key] = section_text

        _log(logging.DEBUG, "exit: split_sections", section_count=len(sections))
        return sections
    except Exception:
        logger.exception("split_sections failed")
        raise


def parse_scope_fence(section_text: str) -> ScopeFence:
    """Extract allowed/forbidden paths from a Scope Fence section.

    Supports two markdown styles:

    1. Legacy ``**Allowed**:`` / ``**Forbidden**:`` bold-header bullet lists.
    2. (Y18) Code-block style — paths listed inside a triple-backtick block.
       Used as a fallback when the legacy bold-header style produces no
       entries. Each non-empty non-comment line becomes an allowed entry;
       trailing parenthetical comments and inline backticks are stripped,
       and lines starting with ``#`` or ``//`` are skipped.
    """
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

        # Y18: fall back to code-block-of-paths syntax when the legacy
        # bold-header style produced no entries. Most current task specs
        # use the more readable code-block style; without this fallback,
        # parse_scope_fence returns an empty ScopeFence and downstream
        # run_scope_check fires a false-positive scope-violation.
        if not fence.allowed and not fence.forbidden:
            _log(
                logging.DEBUG,
                "parse_scope_fence: legacy parse empty; trying code-block fallback",
            )
            in_block = False
            for line in section_text.splitlines():
                if line.strip().startswith("```"):
                    in_block = not in_block
                    continue
                if not in_block:
                    continue
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("#") or stripped.startswith("//"):
                    continue
                # Drop trailing parenthetical comments, then inline backticks.
                entry = re.split(r"\s+\(", stripped, maxsplit=1)[0].strip()
                entry = entry.strip("`").strip()
                if entry:
                    fence.allowed.append(entry)
            _log(
                logging.DEBUG,
                "parse_scope_fence: code-block fallback collected entries",
                count=len(fence.allowed),
            )

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
    """Extract task id from filename like `T1-foo.md`, `task-2.md`, `task-dual-1.md`.

    Keeps the FULL stem tail after the ``T<num>`` or ``task-`` prefix. Previously
    the regex ``^task-(\\w+)`` stopped at the first dash, so ``task-dual-1.md``
    became task_id=``dual`` (losing the ``-1``). See dual-1-postmortem.md
    Finding #11.
    """
    _log(logging.DEBUG, "entry: _derive_task_id", path=str(path))
    try:
        stem = path.stem
        m = re.match(r"^T(\d+[\w\-]*)", stem, re.IGNORECASE)
        if m:
            task_id = m.group(1)
        else:
            m = re.match(r"^task-(.+)$", stem, re.IGNORECASE)
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
    """`git reset --hard <base_sha>` + scoped `git clean` to restore baseline.

    Cleans untracked files that Codex itself may have created, but EXCLUDES
    ``work/codex-implementations/`` — that directory holds our own
    diagnostic artifacts (task-N.diff, task-N-result.md) which must survive
    rollback for post-mortem. See dual-1-postmortem.md Bug #9.
    """
    _log(logging.WARNING, "entry: rollback_worktree", worktree=str(worktree), base_sha=base_sha)
    try:
        _run_git(["reset", "--hard", base_sha], cwd=worktree, timeout=120)
        # Preserve diagnostic artifacts generated by codex-implement.py itself.
        _run_git(
            ["clean", "-fd", "-e", "work/codex-implementations/"],
            cwd=worktree,
            timeout=60,
        )
        _log(logging.WARNING, "exit: rollback_worktree")
    except Exception:
        logger.exception("rollback_worktree failed")


# --------------------------------------------------------------------------- #
# Codex invocation                                                            #
# --------------------------------------------------------------------------- #


def load_prior_iteration(path: Path) -> str:
    """Parse a previous task-result.md and distill it into a prompt-ready summary.

    Extracts: ``status``, self-report lines (NOTE/BLOCKER), the list of files
    touched (from ``diff --git`` headers), and scope-check verdict. Returns a
    markdown block ready to inject as ``## Previous Iteration`` into the next
    Codex prompt. This lets Opus hand a failed/partial round's context to the
    next round without manually re-editing task-N.md — "automated iteration
    memory" per activeContext follow-up list.

    Missing file raises FileNotFoundError; malformed content still returns
    whatever was parseable with ``(unparsed)`` placeholders for the rest.
    """
    _log(logging.DEBUG, "entry: load_prior_iteration", path=str(path))
    try:
        if not path.exists():
            raise FileNotFoundError(f"prior iteration not found: {path}")
        text = path.read_text(encoding="utf-8")

        def _extract(key: str) -> str:
            m = re.search(rf"^\-\s*{re.escape(key)}\s*:\s*(.+)$", text, re.MULTILINE)
            return m.group(1).strip() if m else "(unparsed)"

        status = _extract("status")
        scope_status = _extract("scope_status")
        codex_rc = _extract("codex_returncode")
        base_sha = _extract("base_sha")
        tests_all = _extract("tests_all_passed")

        files_touched: list[str] = []
        for m in re.finditer(r"^diff --git a/(\S+) b/", text, re.MULTILINE):
            f = m.group(1)
            if f not in files_touched:
                files_touched.append(f)

        notes: list[str] = []
        blockers: list[str] = []
        in_self_report = False
        for ln in text.splitlines():
            s = ln.strip()
            if s.startswith("## Self-Report"):
                in_self_report = True
                continue
            if in_self_report and s.startswith("## "):
                in_self_report = False
            if in_self_report:
                m = re.match(r"-\s*(NOTE|BLOCKER):\s*(.+)$", s)
                if m:
                    (blockers if m.group(1) == "BLOCKER" else notes).append(m.group(2).strip())

        parts: list[str] = []
        parts.append("## Previous Iteration (auto-injected by --iterate-from)")
        parts.append("")
        parts.append(f"- prior status: {status}")
        parts.append(f"- prior scope_status: {scope_status}")
        parts.append(f"- prior codex_returncode: {codex_rc}")
        parts.append(f"- prior tests_all_passed: {tests_all}")
        parts.append(f"- prior base_sha: {base_sha}")
        if files_touched:
            parts.append(f"- files touched previously: {', '.join(files_touched)}")
        if notes:
            parts.append("- prior NOTEs:")
            for n in notes:
                parts.append(f"  - NOTE: {n}")
        if blockers:
            parts.append("- prior BLOCKERs (address these this round):")
            for b in blockers:
                parts.append(f"  - BLOCKER: {b}")
        parts.append("")
        parts.append(
            "Key directive: do NOT repeat the prior failure mode verbatim. "
            "Read the BLOCKERs above and make sure your implementation this round "
            "addresses them. The task spec below is the same or a refinement — "
            "Acceptance Criteria remain IMMUTABLE."
        )
        summary = "\n".join(parts)
        _log(
            logging.INFO,
            "prior iteration loaded",
            path=str(path),
            status=status,
            notes=len(notes),
            blockers=len(blockers),
            files_touched=len(files_touched),
        )
        return summary
    except Exception:
        logger.exception("load_prior_iteration failed")
        raise


def build_codex_prompt(task: Task, prior_iteration: Optional[str] = None) -> str:
    """Build prompt embedding full task-N.md content + execution instructions.

    If ``prior_iteration`` is provided (markdown block from load_prior_iteration),
    it is injected BEFORE the task spec so Codex sees the failure context first.
    """
    _log(
        logging.DEBUG,
        "entry: build_codex_prompt",
        task_id=task.task_id,
        has_prior=bool(prior_iteration),
    )
    try:
        header = (
            "You are the single-task implementer. The task specification below is IMMUTABLE.\n"
            "Write code to satisfy all Acceptance Criteria. Do NOT modify files listed in\n"
            "Forbidden Paths or Read-Only Files. After writing code, run every Test Command\n"
            "listed in the task and report the result in your self-report.\n"
            "Any AGENTS.md or CLAUDE.md in the worktree is authoritative background context.\n"
        )
        if prior_iteration:
            header += (
                "\n---- PREVIOUS ITERATION ----\n\n"
                + prior_iteration
                + "\n\n---- END PREVIOUS ITERATION ----\n"
            )
        header += "\n---- TASK SPECIFICATION ----\n\n"

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


def determine_run_status(
    scope: "Optional[ScopeCheckResult]",
    test_run: "Optional[TestRunResult]",
    codex_run: "Optional[CodexRunResult]",
    timed_out: bool,
) -> str:
    """Pure helper: decide overall run status from the four signals.

    Y20 (2026-04-26): Codex CLI v0.125 frequently returns a non-zero
    returncode from harmless telemetry warnings (e.g. "failed to record
    rollout items"). Treating that as a hard failure produced
    ``status=fail`` runs even when the scope check passed AND every test
    command exited 0 (this corrupted Z9 and confused the judge). The rule
    below ignores ``codex_run.returncode`` entirely once tests and scope
    have given the green light. If a downstream consumer wants to surface
    the non-zero returncode, do it as an informational NOTE in the result
    file — not as a status:fail.

    Precedence (first match wins):
      1. ``timed_out``                   -> ``"timeout"``
      2. ``scope.status == "fail"``      -> ``"scope-violation"``
      3. ``not test_run.all_passed``     -> ``"fail"``
      4. otherwise                       -> ``"pass"``
    """
    _log(
        logging.DEBUG,
        "entry: determine_run_status",
        timed_out=timed_out,
        scope_status=(scope.status if scope is not None else None),
        tests_ok=(test_run.all_passed if test_run is not None else None),
        codex_returncode=(codex_run.returncode if codex_run is not None else None),
    )
    try:
        if timed_out:
            status = "timeout"
        elif scope is not None and scope.status == "fail":
            status = "scope-violation"
        elif test_run is None or not test_run.all_passed:
            status = "fail"
        else:
            status = "pass"
        _log(logging.DEBUG, "exit: determine_run_status", status=status)
        return status
    except Exception:
        logger.exception("determine_run_status failed")
        raise


@dataclass
class CodexRunResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    self_report: list[str]


def _build_codex_argv(
    codex: str,
    model: str,
    worktree: Path,
    chatgpt_provider: str,
) -> list[str]:
    """Build the argv used to invoke `codex exec`.

    Y26: Codex CLI v0.125 silently ignores `--sandbox workspace-write`
    (and `-c sandbox_*` overrides) for `exec` mode — the sandbox
    always degrades to `read-only`, which means Codex literally cannot
    write any files. This was empirically confirmed across four argv
    shapes after dual runs Y23 / Z5 / Z7 produced empty diffs three
    times in a row and Claude won by walkover each time.

    Switching to `--dangerously-bypass-approvals-and-sandbox` IS a
    capability escalation, but it is acceptable inside our pipeline:

      * we always run `--cd <worktree>` against an isolated git
        worktree on its own branch (losing the tree only loses local
        branch state);
      * the worktree contains no production secrets;
      * `codex-scope-check.py` validates every write post-hoc against
        the task's Scope Fence;
      * the alternative (read-only sandbox) makes Codex completely
        useless in dual-implement runs.

    Z20 (Improvement 3, 2026-04-26): if `_detect_os_sandbox()` finds an
    OS-level sandbox (Sandboxie on Windows / firejail on Linux) the
    detected wrap argv is **prepended** so the entire `codex exec`
    invocation runs inside that additional sandbox. Silent fallback when
    nothing is installed (the helper returns ``None``).

    Extracted as a helper so unit tests can inspect the argv without
    invoking the real Codex CLI. Production code path stays identical:
    `run_codex` calls this exactly once.
    """
    cmd = [
        codex,
        "exec",
        "-c", chatgpt_provider,
        "-c", "model_provider=chatgpt",
        "--model",
        model,
        "--dangerously-bypass-approvals-and-sandbox",
        "--cd",
        str(worktree.resolve()),
        "-",
    ]
    sandbox = _detect_os_sandbox()
    if sandbox is not None:
        name, prefix_argv = sandbox
        _log(
            logging.INFO,
            "OS-level sandbox detected; wrapping codex argv",
            sandbox=name,
            prefix=prefix_argv,
        )
        cmd = list(prefix_argv) + cmd
    return cmd


# --------------------------------------------------------------------------- #
# Z20 - Criterion 3 security helpers (FS allowlist + audit + sandbox)
# --------------------------------------------------------------------------- #


# Sensitive paths that must NEVER appear in the Codex FS read allowlist
# and must be flagged when reachable from the worktree. Built lazily inside
# the helpers so monkeypatched HOME (in tests) is honored.
_SENSITIVE_HOME_PATHS = (
    (".codex", "auth.json"),
    (".ssh",),
    (".aws", "credentials"),
)
_SENSITIVE_PROJECT_FILES = (".env", "credentials.json", "secrets.json")


def _build_codex_env(worktree: Path, project_root: Path) -> dict[str, str]:
    """Build the env dict used to invoke `codex exec` (Z20 Improvement 1).

    Returns a copy of ``os.environ`` with ``CODEX_FS_READ_ALLOWLIST`` set to
    an OS-pathsep-joined list of paths Codex is permitted to read. The
    allowlist is intentionally **narrow**:

      * the worktree path (resolved) - the work area
      * the project root (resolved) - read-only references
      * the system temp dir - pip caches, scratch files

    Sensitive home-directory paths (``~/.codex/auth.json``, ``~/.ssh``,
    ``~/.aws/credentials``) are explicitly **excluded**. Neither the parent
    ``~/.codex`` nor ``~/.ssh`` is added, and any candidate that resolves
    under one of those roots is scrubbed before being included.

    Heuristic: this env var is only honored by Codex CLI versions that read
    it. Older versions silently ignore it; in that case Improvement 3
    (OS-level sandbox wrap) and the post-hoc scope-fence check remain the
    actual enforcement layers. Best-effort defense in depth.
    """
    _log(
        logging.DEBUG,
        "entry: _build_codex_env",
        worktree=str(worktree),
        project_root=str(project_root),
    )
    try:
        env = os.environ.copy()
        # Always start from a clean slate - never trust a pre-existing
        # CODEX_FS_READ_ALLOWLIST from the parent shell.
        env.pop("CODEX_FS_READ_ALLOWLIST", None)

        candidates: list[Path] = [
            worktree.resolve(),
            project_root.resolve(),
            Path(tempfile.gettempdir()).resolve(),
        ]

        # Compute forbidden roots so we can scrub anything that resolves
        # under them. Path.home() is queried fresh so test monkeypatching
        # of HOME / USERPROFILE is honored.
        home = Path.home().resolve()
        forbidden_roots: list[Path] = []
        for parts in _SENSITIVE_HOME_PATHS:
            forbidden_roots.append((home.joinpath(*parts)).resolve())

        def _is_forbidden(p: Path) -> bool:
            for root in forbidden_roots:
                try:
                    p.relative_to(root)
                    return True
                except ValueError:
                    continue
                except Exception:
                    continue
            return False

        kept: list[str] = []
        seen: set[str] = set()
        for cand in candidates:
            if _is_forbidden(cand):
                _log(
                    logging.WARNING,
                    "allowlist candidate scrubbed (resolves under sensitive root)",
                    candidate=str(cand),
                )
                continue
            key = str(cand)
            if key in seen:
                continue
            seen.add(key)
            kept.append(key)

        env["CODEX_FS_READ_ALLOWLIST"] = os.pathsep.join(kept)
        _log(
            logging.INFO,
            "exit: _build_codex_env",
            allowlist_count=len(kept),
            allowlist=kept,
        )
        return env
    except Exception:
        logger.exception("_build_codex_env failed")
        raise


def _audit_sensitive_paths(worktree: Path, project_root: Path) -> list[str]:
    """List sensitive paths reachable from the worktree (Z20 Improvement 2).

    Checks for the existence of well-known credential files at standard
    locations (``~/.codex/auth.json``, ``~/.ssh``, ``~/.aws/credentials``)
    plus project-local secret files (``.env`` etc.) under both the
    worktree and the project root. Each existing path triggers a
    ``logger.warning("sensitive path reachable", path=...)`` so the
    operator is alerted that the broad ``--cd <worktree>`` posture lets
    Codex potentially read these files.

    Returns the list of stringified paths found (may be empty). The
    caller does not use the return value to fail the run - the audit is
    advisory; mitigation lives in Improvements 1 and 3.
    """
    _log(
        logging.DEBUG,
        "entry: _audit_sensitive_paths",
        worktree=str(worktree),
        project_root=str(project_root),
    )
    try:
        found: list[str] = []
        seen: set[str] = set()
        home = Path.home()

        for parts in _SENSITIVE_HOME_PATHS:
            candidate = home.joinpath(*parts)
            try:
                if candidate.exists():
                    key = str(candidate)
                    if key not in seen:
                        seen.add(key)
                        found.append(key)
                        _log(
                            logging.WARNING,
                            "sensitive path reachable",
                            path=key,
                            kind="home",
                        )
            except OSError:
                continue

        for root_label, root in (("worktree", worktree), ("project_root", project_root)):
            try:
                root_resolved = root.resolve()
            except Exception:
                continue
            for name in _SENSITIVE_PROJECT_FILES:
                candidate = root_resolved / name
                try:
                    if candidate.exists():
                        key = str(candidate)
                        if key not in seen:
                            seen.add(key)
                            found.append(key)
                            _log(
                                logging.WARNING,
                                "sensitive path reachable",
                                path=key,
                                kind=root_label,
                            )
                except OSError:
                    continue

        _log(
            logging.INFO,
            "exit: _audit_sensitive_paths",
            count=len(found),
        )
        return found
    except Exception:
        logger.exception("_audit_sensitive_paths failed")
        raise


_SANDBOXIE_PATHS = (
    Path(r"C:\Program Files\Sandboxie-Plus\Start.exe"),
    Path(r"C:\Program Files\Sandboxie\Start.exe"),
)


def _detect_os_sandbox() -> Optional[tuple[str, list[str]]]:
    """Detect an OS-level sandbox to wrap `codex exec` with (Z20 Improvement 3).

    On Windows: returns ``("sandboxie", ["<Start.exe>", "/box:codex"])``
    if a Sandboxie-Plus or classic Sandboxie ``Start.exe`` exists at one
    of the standard install paths.

    On Linux: returns ``("firejail", ["firejail", "--noroot",
    "--private-tmp"])`` when ``shutil.which("firejail")`` finds the
    binary.

    Returns ``None`` and stays silent when neither is available - silent
    fallback is intentional so dev machines without these tools do not
    spam INFO logs. Logs at INFO only when a sandbox IS detected, since
    that affects argv shape and is worth the breadcrumb.

    Macs / other platforms: ``None``.
    """
    _log(
        logging.DEBUG,
        "entry: _detect_os_sandbox",
        platform=sys.platform,
    )
    try:
        if sys.platform == "win32":
            for path in _SANDBOXIE_PATHS:
                try:
                    if path.exists():
                        prefix = [str(path), "/box:codex"]
                        _log(
                            logging.INFO,
                            "Sandboxie detected",
                            path=str(path),
                        )
                        return ("sandboxie", prefix)
                except OSError:
                    continue
            return None

        if sys.platform.startswith("linux"):
            firejail = shutil.which("firejail")
            if firejail:
                prefix = [firejail, "--noroot", "--private-tmp"]
                _log(
                    logging.INFO,
                    "firejail detected",
                    path=firejail,
                )
                return ("firejail", prefix)
            return None

        return None
    except Exception:
        logger.exception("_detect_os_sandbox failed")
        return None


def run_codex(
    prompt: str,
    worktree: Path,
    reasoning: str,
    timeout: int,
    model: str = "gpt-5.5",
) -> CodexRunResult:
    """Invoke `codex exec` with danger-full-access. Returns structured result.

    Default model = "gpt-5.5". The default Codex CLI `openai` provider blocks
    gpt-5.5 for ChatGPT-account users ("not supported when using Codex with a
    ChatGPT account"). We route through the `chatgpt` provider which targets
    `https://chatgpt.com/backend-api/codex` — the same endpoint the Codex
    desktop/web app uses — where gpt-5.5 IS available to ChatGPT-account users.
    Overrides are passed inline via `-c` so no global ~/.codex/config.toml
    changes are required (preserves unmodified default behavior for existing
    advisor tools: codex-ask.py, codex-parallel.py, codex-watchdog.py, etc.).
    """
    _log(
        logging.INFO,
        "entry: run_codex",
        worktree=str(worktree),
        reasoning=reasoning,
        timeout=timeout,
        model=model,
        prompt_len=len(prompt),
    )
    try:
        codex = shutil.which("codex")
        if not codex:
            raise RuntimeError("codex CLI not found in PATH")

        # Pass prompt via stdin (not argv) — multi-KB prompts with markdown special
        # chars get mangled through Windows cmd.exe when invoking the codex.CMD
        # wrapper. `codex exec` reads stdin when prompt arg is absent or equals '-'.
        #
        # Route via the `chatgpt` provider (chatgpt.com/backend-api/codex endpoint)
        # so gpt-5.5 works for ChatGPT-account users. The default `openai` provider
        # blocks gpt-5.5 for ChatGPT-account auth. See run_codex docstring.
        chatgpt_provider = (
            'model_providers.chatgpt='
            '{name="chatgpt",'
            'base_url="https://chatgpt.com/backend-api/codex",'
            'wire_api="responses"}'
        )
        # Y26: --sandbox workspace-write + --full-auto are silently ignored
        # by Codex CLI v0.125 for `exec` mode (sandbox always becomes
        # read-only). Bypass instead — safe because we run inside an
        # isolated git worktree (`--cd <worktree>`) and scope-fence
        # checker validates writes post-hoc.
        cmd = _build_codex_argv(
            codex=codex,
            model=model,
            worktree=worktree,
            chatgpt_provider=chatgpt_provider,
        )
        _log(logging.INFO, "codex cmd", argv_head=cmd[:9], prompt_via="stdin")

        # Z20 Improvement 2: audit sensitive paths reachable from worktree.
        # Advisory only - logs warnings; never fails the run.
        try:
            project_root_for_audit = find_project_root(worktree)
            _audit_sensitive_paths(worktree, project_root_for_audit)
        except Exception:
            logger.exception("sensitive-path audit failed (non-fatal)")
            project_root_for_audit = worktree

        # Z20 Improvement 1: build env dict with restrictive
        # CODEX_FS_READ_ALLOWLIST. Honored by Codex CLI versions that read
        # the var; older versions silently ignore it (defense in depth).
        try:
            codex_env = _build_codex_env(worktree, project_root_for_audit)
        except Exception:
            logger.exception("_build_codex_env failed; falling back to current env")
            codex_env = None

        try:
            proc = subprocess.run(
                cmd,
                input=prompt,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                env=codex_env,
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


def run_codex_with_backoff(prompt: str, worktree: Path, reasoning: str,
                           timeout: int, model: str = "gpt-5.5") -> CodexRunResult:
    """T8: retry run_codex with 1/2/4/8s backoff on rate-limit; cumulative deadline=timeout (AC2+AC3)."""
    _log(logging.INFO, "entry: run_codex_with_backoff", timeout=timeout, max_retries=MAX_RETRIES)
    deadline = time.monotonic() + max(timeout, 1)
    last: Optional[CodexRunResult] = None
    for attempt in range(1, MAX_RETRIES + 1):
        remaining = int(deadline - time.monotonic())
        if remaining <= 0:
            _log(logging.ERROR, "codex backoff budget exhausted", attempt=attempt); break
        last = run_codex(prompt=prompt, worktree=worktree, reasoning=reasoning,
                         timeout=remaining, model=model)
        if last.timed_out or not is_rate_limit_error(last.stderr):
            _log(logging.INFO, "exit: run_codex_with_backoff",
                 attempt=attempt, returncode=last.returncode, timed_out=last.timed_out)
            return last
        if attempt >= MAX_RETRIES:
            _log(logging.ERROR, "codex rate-limit retries exhausted",
                 attempt=attempt, backoff_s=0, reason="max-retries"); break
        backoff_s = BACKOFF_SEQUENCE_S[attempt - 1]
        if deadline - time.monotonic() - backoff_s <= 0:
            _log(logging.WARNING, "backoff exceeds deadline; giving up",
                 attempt=attempt, backoff_s=backoff_s, reason="deadline"); break
        _log(logging.WARNING, "codex rate-limit, backing off",
             attempt=attempt, backoff_s=backoff_s, reason="rate-limit")
        time.sleep(backoff_s)
    return last if last is not None else CodexRunResult(
        returncode=-1, stdout="", stderr="no attempts made", timed_out=False, self_report=[])


# --------------------------------------------------------------------------- #
# Scope check                                                                 #
# --------------------------------------------------------------------------- #


@dataclass
class ScopeCheckResult:
    status: str  # "pass" | "fail" | "skipped"
    message: str
    violations: list[str] = field(default_factory=list)


def _find_main_repo_root(p: Path) -> Optional[Path]:
    """Return the nearest ancestor with a real ``.git`` directory."""
    _log(logging.DEBUG, "entry: _find_main_repo_root", path=str(p))
    try:
        start = p.resolve()
        for candidate in (start, *start.parents):
            if (candidate / ".git").is_dir():
                _log(logging.DEBUG, "exit: _find_main_repo_root", root=str(candidate))
                return candidate
        _log(logging.DEBUG, "exit: _find_main_repo_root", root=None)
        return None
    except Exception:
        logger.exception("_find_main_repo_root failed")
        raise


def _resolve_scope_check_script(project_root: Path) -> Path:
    """Resolve the repo-current codex-scope-check.py script path."""
    _log(logging.DEBUG, "entry: _resolve_scope_check_script", project_root=str(project_root))
    try:
        env_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
        if env_project_dir:
            script = (
                Path(env_project_dir).expanduser().resolve()
                / ".claude"
                / "scripts"
                / "codex-scope-check.py"
            )
            _log(logging.DEBUG, "exit: _resolve_scope_check_script", source="env", script=str(script))
            return script

        main_root = _find_main_repo_root(project_root)
        if main_root is not None:
            script = main_root / ".claude" / "scripts" / "codex-scope-check.py"
            _log(logging.DEBUG, "exit: _resolve_scope_check_script", source="main_repo", script=str(script))
            return script

        script = project_root / ".claude" / "scripts" / "codex-scope-check.py"
        _log(logging.DEBUG, "exit: _resolve_scope_check_script", source="worktree", script=str(script))
        return script
    except Exception:
        logger.exception("_resolve_scope_check_script failed")
        raise


def run_scope_check(
    diff_path: Path,
    fence_paths: ScopeFence,
    project_root: Path,
) -> ScopeCheckResult:
    """Invoke codex-scope-check.py if present; skip gracefully otherwise."""
    _log(logging.DEBUG, "entry: run_scope_check", diff_path=str(diff_path))
    try:
        script = _resolve_scope_check_script(project_root)
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
            description="Run Codex CLI against a task-N.md spec (Y26: --dangerously-bypass-approvals-and-sandbox; safe in disposable worktree).",
        )
        p.add_argument("--task", required=True, type=Path,
                       help="Path to task-N.md file")
        p.add_argument("--worktree", default=Path("."), type=Path,
                       help="Path to worktree dir (defaults to cwd)")
        p.add_argument("--reasoning", default=None, choices=["high", "medium", "low"],
                       help="Override frontmatter reasoning effort (wins over --speed and speed_profile)")
        p.add_argument("--speed", default=None,
                       choices=["fast", "balanced", "thorough"],
                       help="Speed profile override: fast=reasoning low, balanced=medium, thorough=high. "
                            "Wins over speed_profile frontmatter but loses to --reasoning.")
        p.add_argument("--model", default="gpt-5.5",
                       help="Codex model (default: gpt-5.5 via chatgpt provider; any model name accepted by that endpoint)")
        p.add_argument("--timeout", default=3600, type=int,
                       help="Timeout in seconds for codex exec (default 3600)")
        p.add_argument("--result-dir", default=Path("work/codex-implementations"), type=Path,
                       help="Directory for task-{N}-result.md output")
        p.add_argument("--log-dir", default=Path("work/codex-primary/logs"), type=Path,
                       help="Directory for structured logs")
        p.add_argument("--iterate-from", type=Path, default=None,
                       help="Path to a prior task-N-result.md; its summary is auto-injected "
                            "into the Codex prompt as 'PREVIOUS ITERATION' so multi-round "
                            "tasks don't have to re-edit task-N.md's Iteration History manually.")
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

    # Reasoning effort precedence (highest wins):
    #   1. --reasoning CLI flag (explicit override, always)
    #   2. --speed CLI flag (maps to reasoning: fast=low/balanced=medium/thorough=high)
    #   3. `reasoning:` field in task-N.md frontmatter (explicit in spec)
    #   4. `speed_profile:` field in task-N.md frontmatter (same mapping as --speed)
    #   5. default "medium" (balanced — one step below old "high" default, for speed)
    _SPEED_TO_REASONING = {"fast": "low", "balanced": "medium", "thorough": "high"}
    if args.reasoning:
        task.frontmatter["reasoning"] = args.reasoning
    elif args.speed:
        task.frontmatter["reasoning"] = _SPEED_TO_REASONING[args.speed]
    elif "reasoning" not in task.frontmatter:
        profile = task.frontmatter.get("speed_profile", "balanced")
        task.frontmatter["reasoning"] = _SPEED_TO_REASONING.get(profile, "medium")
    _log(
        logging.INFO,
        "effective reasoning resolved",
        reasoning=task.frontmatter["reasoning"],
        speed_cli=args.speed,
        speed_profile_fm=task.frontmatter.get("speed_profile"),
    )

    try:
        base_sha = preflight_worktree(worktree)
    except Exception as exc:
        print(f"fatal: preflight failed: {exc}", file=sys.stderr)
        return EXIT_SCOPE_OR_TIMEOUT

    timestamp = datetime.now(timezone.utc).isoformat()
    project_root = find_project_root(worktree)

    prior_iteration: Optional[str] = None
    if args.iterate_from is not None:
        try:
            prior_iteration = load_prior_iteration(args.iterate_from.resolve())
        except Exception as exc:
            print(f"fatal: could not load --iterate-from: {exc}", file=sys.stderr)
            return EXIT_SCOPE_OR_TIMEOUT

    prompt = build_codex_prompt(task, prior_iteration=prior_iteration)

    codex_run: Optional[CodexRunResult] = None
    test_run: Optional[TestRunResult] = None
    scope: Optional[ScopeCheckResult] = None
    status = "pass"
    diff_text = ""

    circuit = check_circuit_open(project_root)
    if circuit is not None:
        result_path = result_dir / f"task-{task.task_id}-result.md"
        result_dir.mkdir(parents=True, exist_ok=True)
        degraded_stderr = (f"circuit-open degraded_reason=circuit-open "
                           f"opened_at={circuit.get('opened_at','')} "
                           f"expires_at={circuit.get('expires_at','')} "
                           f"reason={circuit.get('reason','')}")
        write_result_file(
            result_path=result_path, task=task, status="degraded",
            diff="(codex skipped: circuit open)", test_run=None,
            codex_run=CodexRunResult(returncode=-1, stdout="", stderr=degraded_stderr,
                                     timed_out=False, self_report=[]),
            scope=None, base_sha=base_sha,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        print(f"codex-implement: task={task.task_id} status=degraded "
              f"reason=circuit-open exit={EXIT_DEGRADED}")
        print(f"result: {result_path}")
        _log(logging.WARNING, "exit: main (degraded)", exit_code=EXIT_DEGRADED)
        return EXIT_DEGRADED

    try:
        codex_run = run_codex_with_backoff(
            prompt=prompt,
            worktree=worktree,
            reasoning=task.frontmatter.get("reasoning", "high"),
            timeout=args.timeout,
            model=args.model,
        )

        if codex_run.timed_out:
            # Y20: route timeout through the same helper that the
            # tests+scope branch uses so status determination has
            # exactly one canonical implementation.
            status = determine_run_status(
                scope=None, test_run=None, codex_run=codex_run, timed_out=True,
            )
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
                # Do NOT void diff_text on scope-violation — the diff is the
                # single most important diagnostic artifact for post-mortem
                # review (especially when the fence check itself fires a
                # false positive). See dual-1-postmortem.md Bug #8.
            else:
                test_run = run_test_commands(task.test_commands, worktree)
                # Y20: status is derived by the pure helper so the rule
                # is unit-testable and so codex_run.returncode noise no
                # longer overrides a clean tests+scope pass.
                status = determine_run_status(
                    scope=scope,
                    test_run=test_run,
                    codex_run=codex_run,
                    timed_out=False,
                )

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

        try:
            if exit_code == EXIT_OK:
                record_codex_success(project_root)
            else:
                record_codex_failure(project_root, task.task_id,
                                     reason=f"status={status} exit={exit_code}")
        except Exception:
            logger.exception("circuit state update failed (non-fatal)")

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
