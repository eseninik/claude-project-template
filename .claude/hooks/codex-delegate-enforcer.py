#!/usr/bin/env python3
"""Codex Delegate Enforcer - Always-Dual PreToolUse hook (CLAUDE.md).
Edit/Write/MultiEdit on a code file that is NOT exempt -> require a fresh
(<15 min) work/codex-implementations/task-*-result.md with status=pass
whose paired task-N.md Scope Fence covers the target. Missing cover ->
deny via PreToolUse JSON. Fail-open on any exception.
"""
from __future__ import annotations
import fnmatch
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Iterable
if sys.platform == "win32":
    for _stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")
HOOK_NAME = "codex-delegate-enforcer"
RESULT_MAX_AGE_SECONDS: int = 15 * 60
MAX_RESULT_FILES_TO_SCAN: int = 50
CODEX_IMPLEMENTATIONS_DIR = "work/codex-implementations"
CODEX_TASKS_DIR = "work/codex-primary/tasks"
# AC5 - delegated code extensions. Frozenset for O(1) lookup.
CODE_EXTENSIONS: frozenset = frozenset({
    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
    ".sql", ".lua", ".r",
})
# AC6 - exempt path globs. Matched against POSIX relative path.
EXEMPT_PATTERNS: tuple = (
    ".claude/memory/**", "work/**", "CLAUDE.md", "AGENTS.md",
    "README.md", "CHANGELOG.md", "LICENSE", ".gitignore",
    ".claude/settings.json", ".claude/ops/*.yaml", ".mcp.json",
    ".claude/adr/**/*.md", ".claude/guides/**/*.md",
    ".claude/skills/**/*.md",
    "worktrees/**",  # dual-implement worktrees — edits here are part of an outer DUAL operation
)
# AC14 - regex compiled at module scope.
_STATUS_RE = re.compile(r"(?i)status\s*[:=]\s*([A-Za-z0-9_-]+)")
_TASK_FILE_RE = re.compile(r"(?i)task[_\s-]*file\s*[:=]\s*(.+)")
_SCOPE_FENCE_HEADING_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
_NEXT_HEADING_RE = re.compile(r"(?m)^##\s+")
_ALLOWED_SECTION_RE = re.compile(
    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\Z)"
)
_TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
_GLOB_TAIL_RE = re.compile(r"/?\*+$")
_RESULT_NAME_RE = re.compile(r"task-(.+?)-result\.md$")
RECOVERY_HINT = (
    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" "
    "--scope <path> for micro-task, or write work/<feature>/tasks/task-N.md "
    "and run codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
)

def _build_logger(project_dir: Path) -> logging.Logger:
    """Create enforcer logger: file if writable else stderr-only."""
    logger = logging.getLogger(HOOK_NAME)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    log_dir = project_dir / ".claude" / "logs"
    file_ok = False
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_dir / (HOOK_NAME + ".log"), encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        file_ok = True
    except OSError:
        file_ok = False
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(fmt)
    sh.setLevel(logging.WARNING if file_ok else logging.INFO)
    logger.addHandler(sh)
    logger.propagate = False
    return logger

def get_project_dir() -> Path:
    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()

def resolve_target(project_dir: Path, target_raw: str):
    """Normalize raw file_path to absolute Path inside project_dir."""
    logger = logging.getLogger(HOOK_NAME)
    if not target_raw:
        return None
    try:
        p = Path(target_raw)
        if not p.is_absolute():
            p = project_dir / p
        resolved = p.resolve()
    except (OSError, ValueError) as exc:
        logger.info("resolve_target.err raw=%r exc=%s", target_raw, exc)
        return None
    try:
        resolved.relative_to(project_dir)
    except ValueError:
        logger.info("resolve_target.escape resolved=%s", resolved)
        return None
    return resolved

def rel_posix(project_dir: Path, absolute: Path):
    """POSIX-style project-relative path, or None if outside."""
    try:
        return absolute.relative_to(project_dir).as_posix()
    except ValueError:
        return None

def is_code_extension(rel_path: str) -> bool:
    """True iff extension is in the delegated code set."""
    return Path(rel_path).suffix.lower() in CODE_EXTENSIONS

def is_exempt(rel_path: str) -> bool:
    """True iff rel_path matches any AC6 exempt glob."""
    logger = logging.getLogger(HOOK_NAME)
    for pattern in EXEMPT_PATTERNS:
        if pattern.endswith("/**"):
            prefix = pattern[:-3].rstrip("/")
            if rel_path == prefix or rel_path.startswith(prefix + "/"):
                logger.debug("is_exempt.match pattern=%s", pattern)
                return True
            continue
        if "**" in pattern:
            left, _, right = pattern.partition("**")
            left = left.rstrip("/")
            right = right.lstrip("/")
            left_ok = (not left) or rel_path == left or rel_path.startswith(left + "/")
            right_ok = (not right) or fnmatch.fnmatch(rel_path, "*" + right)
            if left_ok and right_ok:
                logger.debug("is_exempt.match pattern=%s (double-glob)", pattern)
                return True
            continue
        if fnmatch.fnmatch(rel_path, pattern):
            logger.debug("is_exempt.match pattern=%s", pattern)
            return True
    return False

def requires_cover(rel_path: str) -> bool:
    """True iff path needs a Codex cover to be editable."""
    if not is_code_extension(rel_path):
        return False
    if is_exempt(rel_path):
        return False
    return True

def _strip_md_markers(line: str) -> str:
    """Strip leading bullets/quotes, surrounding bold/italic/backticks."""
    s = line.lstrip(" \t-*>").strip()
    return s.replace("**", "").replace("__", "").replace("`", "")

def parse_result_fields(result_path: Path) -> dict:
    """Extract ``status`` and ``task_file`` from a task-*-result.md."""
    logger = logging.getLogger(HOOK_NAME)
    out: dict = {}
    try:
        text = result_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        logger.info("parse_result_fields.read_err path=%s exc=%s", result_path.name, exc)
        return out
    for raw in text.splitlines():
        stripped = _strip_md_markers(raw)
        if "status" not in out:
            m = _STATUS_RE.match(stripped)
            if m:
                out["status"] = m.group(1).strip().lower()
        if "task_file" not in out:
            m2 = _TASK_FILE_RE.match(stripped)
            if m2:
                out["task_file"] = m2.group(1).strip().strip("`").strip()
        if "status" in out and "task_file" in out:
            break
    return out

def parse_scope_fence(task_path: Path) -> list:
    """Extract ``Allowed paths`` entries from task-N.md Scope Fence."""
    logger = logging.getLogger(HOOK_NAME)
    try:
        text = task_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        logger.info("parse_scope_fence.read_err path=%s exc=%s", task_path.name, exc)
        return []
    heading = _SCOPE_FENCE_HEADING_RE.search(text)
    if not heading:
        return []
    tail = text[heading.end():]
    next_hdr = _NEXT_HEADING_RE.search(tail)
    section = tail[: next_hdr.start()] if next_hdr else tail
    allowed = _ALLOWED_SECTION_RE.search(section)
    if not allowed:
        return []
    entries: list = []
    for line in allowed.group(1).splitlines():
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        entry = stripped.lstrip("-").strip().strip("`").strip()
        entry = _TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
        if not entry:
            continue
        entries.append(entry.replace("\\", "/").rstrip("/"))
    return entries

def path_in_fence(target_rel_posix: str, fence: Iterable) -> bool:
    """True if target is covered by any fence entry."""
    target = target_rel_posix.rstrip("/")
    for raw_entry in fence:
        if not raw_entry:
            continue
        simple = _GLOB_TAIL_RE.sub("", raw_entry).rstrip("/")
        if not simple:
            continue
        if target == simple or target.startswith(simple + "/"):
            return True
    return False

def _resolve_task_file(project_dir: Path, raw: str):
    """Resolve a result.md task_file pointer to absolute Path."""
    logger = logging.getLogger(HOOK_NAME)
    if not raw:
        return None
    try:
        p = Path(raw.strip())
        if not p.is_absolute():
            p = project_dir / p
        return p.resolve()
    except (OSError, ValueError) as exc:
        logger.info("resolve_task_file.err raw=%r exc=%s", raw, exc)
        return None

def find_cover(project_dir: Path, target_rel_posix: str):
    """Search recent result.md artefacts for one covering the target."""
    logger = logging.getLogger(HOOK_NAME)
    logger.info("find_cover.enter target=%s", target_rel_posix)
    try:
        results_dir = project_dir / CODEX_IMPLEMENTATIONS_DIR
        if not results_dir.is_dir():
            logger.info("find_cover.no-dir dir=%s", results_dir)
            return False, "no-results-dir"
        candidates: list = []
        for rp in results_dir.glob("task-*-result.md"):
            try:
                candidates.append((rp.stat().st_mtime, rp))
            except OSError:
                continue
        candidates.sort(key=lambda item: item[0], reverse=True)
        candidates = candidates[:MAX_RESULT_FILES_TO_SCAN]
        if not candidates:
            logger.info("find_cover.no-results")
            return False, "no-results"
        now = time.time()
        saw_fresh = False
        saw_fresh_pass = False
        best_reason = "stale"
        for mtime, rpath in candidates:
            age = now - mtime
            if age > RESULT_MAX_AGE_SECONDS:
                continue
            saw_fresh = True
            try:
                rresolved = rpath.resolve()
                rresolved.relative_to(project_dir)
            except (OSError, ValueError):
                logger.info("find_cover.symlink-escape path=%s", rpath.name)
                continue
            fields = parse_result_fields(rpath)
            status = fields.get("status", "")
            if status != "pass":
                if status == "fail":
                    best_reason = "fail-status"
                logger.info("find_cover.skip path=%s status=%s age=%.1fs",
                            rpath.name, status or "?", age)
                continue
            saw_fresh_pass = True
            task_candidates: list = []
            pointer = _resolve_task_file(project_dir, fields.get("task_file", ""))
            if pointer is not None and pointer.is_file():
                task_candidates.append(pointer)
            name_match = _RESULT_NAME_RE.match(rpath.name)
            if name_match:
                task_id = name_match.group(1)
                tdir = project_dir / CODEX_TASKS_DIR
                if tdir.is_dir():
                    for pattern in ("T" + task_id + "-*.md",
                                    task_id + "-*.md",
                                    "task-" + task_id + ".md",
                                    "task-" + task_id + "-*.md"):
                        task_candidates.extend(tdir.glob(pattern))
            seen: set = set()
            unique: list = []
            for cand in task_candidates:
                if cand not in seen:
                    seen.add(cand)
                    unique.append(cand)
            if not unique:
                logger.info("find_cover.no-task-file result=%s", rpath.name)
                best_reason = "scope-miss"
                continue
            for tpath in unique:
                fence = parse_scope_fence(tpath)
                if not fence:
                    logger.info("find_cover.empty-fence task=%s", tpath.name)
                    continue
                if path_in_fence(target_rel_posix, fence):
                    logger.info("find_cover.MATCH target=%s result=%s task=%s age=%.1fs",
                                target_rel_posix, rpath.name, tpath.name, age)
                    return True, ""
                logger.info("find_cover.scope-miss target=%s task=%s entries=%d",
                            target_rel_posix, tpath.name, len(fence))
                best_reason = "scope-miss"
        if not saw_fresh:
            reason = "stale"
        elif saw_fresh_pass:
            reason = "scope-miss"
        else:
            reason = best_reason
        logger.info("find_cover.exit target=%s covered=False reason=%s",
                    target_rel_posix, reason)
        return False, reason
    except Exception as exc:
        logger.exception("find_cover.unexpected target=%s exc=%s", target_rel_posix, exc)
        return False, "parse-error: " + str(exc)

def extract_targets(payload: dict) -> list:
    """Collect every file path this tool call intends to edit."""
    if not isinstance(payload, dict):
        return []
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return []
    paths: list = []
    if tool_name in {"Edit", "Write"}:
        p = tool_input.get("file_path")
        if isinstance(p, str) and p:
            paths.append(p)
    elif tool_name == "MultiEdit":
        top_path = tool_input.get("file_path")
        if isinstance(top_path, str) and top_path:
            paths.append(top_path)
        edits = tool_input.get("edits")
        if isinstance(edits, list):
            for edit in edits:
                if not isinstance(edit, dict):
                    continue
                ep = edit.get("file_path")
                if isinstance(ep, str) and ep:
                    paths.append(ep)
    seen: set = set()
    unique: list = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique

def emit_deny(blocked: str, reason_code: str) -> None:
    """Print the PreToolUse deny JSON to stdout."""
    logger = logging.getLogger(HOOK_NAME)
    reason_text = {
        "no-results": "no codex-implement result found",
        "no-results-dir": "work/codex-implementations/ does not exist",
        "stale": "all codex-implement results older than 15 min",
        "fail-status": "most recent matching result has status != pass",
        "scope-miss": "no recent pass result covers this path",
        "parse-error": "could not parse codex-implement result",
    }.get(reason_code, reason_code)
    message = ("Code Delegation Protocol: " + blocked + " blocked ("
               + reason_text + "). " + RECOVERY_HINT)
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }
    logger.warning("emit_deny target=%s reason=%s", blocked, reason_code)
    print(json.dumps(payload, ensure_ascii=False))

def decide(payload: dict, project_dir: Path) -> bool:
    """Core gate. True to allow; False after emitting deny."""
    logger = logging.getLogger(HOOK_NAME)
    event = payload.get("hook_event_name", "") if isinstance(payload, dict) else ""
    tool_name = payload.get("tool_name", "") if isinstance(payload, dict) else ""
    logger.info("decide.enter event=%s tool=%s", event, tool_name)
    if event and event != "PreToolUse":
        logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
        return True
    if tool_name not in {"Edit", "Write", "MultiEdit"}:
        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
        return True
    raw_targets = extract_targets(payload)
    if not raw_targets:
        logger.info("decide.passthrough reason=no-targets")
        return True
    for raw in raw_targets:
        abs_path = resolve_target(project_dir, raw)
        if abs_path is None:
            logger.info("decide.skip reason=unresolvable raw=%r", raw)
            continue
        rel = rel_posix(project_dir, abs_path)
        if rel is None:
            logger.info("decide.skip reason=outside-project path=%s", abs_path)
            continue
        if not requires_cover(rel):
            logger.info("decide.allow-target rel=%s reason=exempt-or-non-code", rel)
            continue
        covered, reason = find_cover(project_dir, rel)
        if not covered:
            emit_deny(rel, reason)
            logger.info("decide.exit target=%s allowed=False reason=%s", rel, reason)
            return False
        logger.info("decide.allow-target rel=%s reason=covered", rel)
    logger.info("decide.exit allowed=True")
    return True

def main() -> int:
    """Read JSON payload from stdin, run decide(), exit 0 always."""
    project_dir = get_project_dir()
    logger = _build_logger(project_dir)
    logger.info("main.enter pid=%d", os.getpid())
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            logger.info("main.empty-stdin passthrough")
            return 0
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.info("main.malformed-json exc=%s", exc)
            return 0
        if not isinstance(payload, dict):
            logger.info("main.non-dict-payload type=%s", type(payload).__name__)
            return 0
        decide(payload, project_dir)
    except Exception as exc:
        logger.exception("main.unexpected exc=%s", exc)
    finally:
        logger.info("main.exit")
    return 0

if __name__ == "__main__":
    sys.exit(main())
