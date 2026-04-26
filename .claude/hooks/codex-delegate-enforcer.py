#!/usr/bin/env python3
"""Codex Delegate Enforcer - Always-Dual PreToolUse hook (CLAUDE.md).

Z1 - Four Invariants closing 12 bypass vectors:

I1. Extension wins. is_code_extension() is checked BEFORE is_exempt().
    Path exemptions (work/**, worktrees/**, .claude/scripts/**) only
    protect non-code extensions. A .py file in work/ requires cover.

I2. Bash counts. PreToolUse(Bash) tokenizes the command; mutating verbs
    (cp/mv/sed -i/redirect/python script.py/PowerShell Set-Content/...)
    against code paths require cover. A whitelist exempts read-only verbs
    (ls/cat/git status/pytest/...) and the project's own dual tooling
    (codex-ask, codex-implement, dual-teams-spawn, ...).

I3. Path-exact coverage. find_cover(target) returns True only if some
    artifact's Scope Fence explicitly lists the target (with glob support
    via fnmatch). No temporal carryover from unrelated stages.

I4. Skip-token audit + actionable block messages. Every allow/deny
    decision is appended to work/codex-implementations/skip-ledger.jsonl
    (best-effort, never blocks). DENY messages include a ready-to-run
    codex-inline-dual.py command for the blocked path.

Edit/Write/MultiEdit on a code file that is NOT exempt -> require a fresh
(<15 min) work/codex-implementations/task-*-result.md with status=pass
whose Scope Fence covers the target. Missing cover -> deny via PreToolUse
JSON. Fail-open on any unexpected exception.
"""
from __future__ import annotations
import datetime
import fnmatch
import json
import logging
import os
import re
import shlex
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Optional

if sys.platform == "win32":
    for _stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")

HOOK_NAME = "codex-delegate-enforcer"
RESULT_MAX_AGE_SECONDS: int = 15 * 60
MAX_RESULT_FILES_TO_SCAN: int = 50
CODEX_IMPLEMENTATIONS_DIR = "work/codex-implementations"
CODEX_TASKS_DIR = "work/codex-primary/tasks"
SKIP_LEDGER_REL = "work/codex-implementations/skip-ledger.jsonl"

# I1 - delegated code extensions. Frozenset for O(1) lookup.
# Z7-V02: .ipynb added - Jupyter notebooks contain executable code cells.
CODE_EXTENSIONS: frozenset = frozenset({
    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
    ".sql", ".lua", ".r", ".ipynb",
})

# I1 - exempt path globs. ONLY apply to non-code extensions.
EXEMPT_PATTERNS: tuple = (
    ".claude/memory/**", "work/**", "CLAUDE.md", "AGENTS.md",
    "README.md", "CHANGELOG.md", "LICENSE", ".gitignore",
    ".claude/settings.json", ".claude/ops/*.yaml", ".mcp.json",
    ".claude/adr/**/*.md", ".claude/guides/**/*.md",
    ".claude/skills/**/*.md",
    "worktrees/**",
)

# Regexes - compiled at module scope.
_STATUS_RE = re.compile(r"(?i)status\s*[:=]\s*([A-Za-z0-9_-]+)")
_TASK_FILE_RE = re.compile(r"(?i)task[_\s-]*file\s*[:=]\s*(.+)")
_SCOPE_FENCE_HEADING_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
_NEXT_HEADING_RE = re.compile(r"(?m)^##\s+")
_ALLOWED_SECTION_RE = re.compile(
    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\Z)"
)
_TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
_RESULT_NAME_RE = re.compile(r"task-(.+?)-result\.md$")

# I2 - Bash classification tables.
_BASH_READONLY_VERBS: frozenset = frozenset({
    "ls", "cat", "head", "tail", "less", "more", "wc", "file", "stat",
    "find", "grep", "rg", "ag", "sort", "uniq", "cut", "tr", "diff",
    "cmp", "tree", "echo", "printf", "true", "false", "pwd", "which",
    "whoami", "date", "env", "type", "command", "id", "hostname",
})

_BASH_TEST_RUNNERS: frozenset = frozenset({
    "pytest", "unittest", "mypy", "ruff", "tsc", "eslint", "prettier",
    "cargo", "go",
})

_BASH_PACKAGE_MANAGERS: frozenset = frozenset({
    "uv", "pip", "npm", "yarn", "pnpm",
})

_BASH_DUAL_TOOLING: frozenset = frozenset({
    ".claude/scripts/codex-implement.py",
    ".claude/scripts/codex-wave.py",
    ".claude/scripts/codex-inline-dual.py",
    ".claude/scripts/dual-teams-spawn.py",
    ".claude/scripts/dual-teams-selftest.py",
    ".claude/scripts/judge.py",
    ".claude/scripts/judge_axes.py",
    ".claude/scripts/codex-ask.py",
    ".claude/scripts/codex-scope-check.py",
    ".claude/scripts/codex-pool.py",
    ".claude/scripts/dual-history-archive.py",
    ".claude/scripts/verdict-summarizer.py",
    ".claude/scripts/worktree-cleaner.py",
    ".claude/scripts/codex-cost-report.py",
    ".claude/scripts/sync-template-to-target.py",
})

_BASH_MUTATING_VERBS: frozenset = frozenset({
    "cp", "mv", "install", "rsync", "rm", "tee", "touch", "ln", "chmod",
    "chown", "dd",
})

_BASH_INPLACE_VERBS: frozenset = frozenset({"sed", "awk", "perl"})

_BASH_INTERPRETERS: frozenset = frozenset({
    "python", "python3", "py", "bash", "sh", "zsh", "node", "deno",
    "ruby", "perl", "lua",
})

_PWSH_MUTATING_CMDLETS: tuple = (
    "set-content", "add-content", "out-file", "new-item",
    "copy-item", "move-item", "remove-item",
    "writealltext", "appendalltext",
)

_BASH_PWSH_LAUNCHERS: frozenset = frozenset({
    "powershell", "powershell.exe", "pwsh", "pwsh.exe",
})


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


def is_dual_teams_worktree(project_dir: Path) -> bool:
    """True iff project_dir or any ancestor contains .dual-base-ref."""
    logger = logging.getLogger(HOOK_NAME)
    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
    current = project_dir
    seen: set[Path] = set()
    while True:
        try:
            resolved = current.resolve()
        except OSError as exc:
            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
            resolved = current.absolute()
        if resolved in seen:
            logger.info(
                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
                project_dir,
            )
            return False
        seen.add(resolved)
        sentinel = current / ".dual-base-ref"
        try:
            if sentinel.is_file():
                logger.info(
                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
                    project_dir, sentinel,
                )
                return True
        except OSError as exc:
            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
        parent = current.parent
        if parent == current:
            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
            return False
        current = parent


def resolve_target(project_dir: Path, target_raw: str) -> Optional[Path]:
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


def rel_posix(project_dir: Path, absolute: Path) -> Optional[str]:
    """POSIX-style project-relative path, or None if outside."""
    try:
        return absolute.relative_to(project_dir).as_posix()
    except ValueError:
        return None


def is_code_extension(rel_path: str) -> bool:
    """True iff extension is in the delegated code set."""
    return Path(rel_path).suffix.lower() in CODE_EXTENSIONS


def is_exempt(rel_path: str) -> bool:
    """True iff rel_path matches any exempt glob (NON-CODE only)."""
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
    """True iff path needs a Codex cover.

    I1 (Extension wins): code extensions ALWAYS require cover, regardless
    of path. Exempt globs only apply to non-code files.
    """
    logger = logging.getLogger(HOOK_NAME)
    logger.info("requires_cover.enter rel=%s", rel_path)
    if is_code_extension(rel_path):
        logger.info("requires_cover.exit rel=%s result=True reason=code-ext-wins", rel_path)
        return True
    if is_exempt(rel_path):
        logger.info("requires_cover.exit rel=%s result=False reason=non-code-exempt", rel_path)
        return False
    logger.info("requires_cover.exit rel=%s result=False reason=non-code-default", rel_path)
    return False


def _strip_md_markers(line: str) -> str:
    """Strip leading bullets/quotes, surrounding bold/italic/backticks."""
    s = line.lstrip(" \t-*>").strip()
    return s.replace("**", "").replace("__", "").replace("`", "")


def parse_result_fields(result_path: Path) -> dict:
    """Extract status and task_file from a task-*-result.md."""
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
    """Extract Allowed paths entries from task-N.md Scope Fence."""
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
    """True if target path is explicitly covered by a fence entry.

    I3 (Path-exact coverage) supports:
      - exact match: 'src/auth.py' covers 'src/auth.py'
      - directory prefix: 'src/auth' covers 'src/auth/login.py'
      - fnmatch glob: 'src/auth/*.py' covers 'src/auth/login.py'
      - recursive glob: 'src/**' covers nested paths
    """
    target = target_rel_posix.rstrip("/")
    for raw_entry in fence:
        if not raw_entry:
            continue
        entry = raw_entry.rstrip("/")
        if not entry:
            continue
        if target == entry:
            return True
        if not any(c in entry for c in "*?["):
            if target.startswith(entry + "/"):
                return True
            continue
        # Glob match.
        simple = re.sub(r"/(?:\*\*|\*)$", "", entry).rstrip("/")
        if simple and not any(c in simple for c in "*?["):
            if target == simple or target.startswith(simple + "/"):
                return True
        if fnmatch.fnmatch(target, entry):
            return True
        if "**" in entry:
            translated = entry.replace("**", "*")
            if fnmatch.fnmatch(target, translated):
                return True
    return False


def _resolve_task_file(project_dir: Path, raw: str) -> Optional[Path]:
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


def find_cover(project_dir: Path, target_rel_posix: str) -> tuple:
    """Search recent result.md artefacts for one whose Scope Fence
    EXPLICITLY lists target_rel_posix (I3 - path-exact coverage)."""
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
        inline_dir = results_dir / "inline"
        if inline_dir.is_dir():
            for rp in inline_dir.glob("task-*-result.md"):
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
                    return True, "covered-by:" + rpath.name
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


# ----------------------------------------------------------------------
# I2 - Bash command parsing
# ----------------------------------------------------------------------

def _split_logical_commands(command: str) -> list:
    """Split a Bash command on ; && || | into sub-commands (quote-aware)."""
    out: list = []
    buf: list = []
    i = 0
    n = len(command)
    in_squote = False
    in_dquote = False
    while i < n:
        c = command[i]
        if c == "'" and not in_dquote:
            in_squote = not in_squote
            buf.append(c)
            i += 1
            continue
        if c == '"' and not in_squote:
            in_dquote = not in_dquote
            buf.append(c)
            i += 1
            continue
        if not in_squote and not in_dquote:
            # Z7-V03: newline terminates a logical command (heredoc body
            # lines may be reclassified individually; false positives are
            # preferable to masking a trailing mutating verb).
            if c == ";" or c == "\n":
                out.append("".join(buf))
                buf = []
                i += 1
                continue
            if c == "|":
                out.append("".join(buf))
                buf = []
                i += 1
                if i < n and command[i] == "|":
                    i += 1
                continue
            if c == "&" and i + 1 < n and command[i + 1] == "&":
                out.append("".join(buf))
                buf = []
                i += 2
                continue
        buf.append(c)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        out.append(tail)
    return [c.strip() for c in out if c.strip()]


def _safe_shlex(command: str) -> list:
    """shlex.split the command; on failure, fall back to whitespace split."""
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def _command_basename(token: str) -> str:
    """Extract the program basename for whitelist/keyword matching."""
    if not token:
        return ""
    if "=" in token and not token.startswith("/") and not token.startswith("."):
        parts = token.split("=", 1)
        if "/" not in parts[0] and "\\" not in parts[0]:
            return ""
    name = Path(token).name.lower()
    if name.endswith(".exe"):
        name = name[:-4]
    return name


def _looks_like_path(token: str) -> bool:
    """True iff token looks like a file path (has '/' or '\' or '.')."""
    if not token or token.startswith("-"):
        return False
    return ("/" in token or "\\" in token or "." in token)


def _normalize_path_token(token: str) -> str:
    """Normalize a path token (POSIX, no quotes)."""
    return token.strip().strip("'\"").replace("\\", "/")


def _is_dual_tooling_invocation(tokens: list) -> bool:
    """True iff tokens reference a project-owned dual-implement script."""
    for tok in tokens[1:6]:
        if not tok or tok.startswith("-"):
            continue
        norm = _normalize_path_token(tok)
        if norm in _BASH_DUAL_TOOLING:
            return True
        for known in _BASH_DUAL_TOOLING:
            if norm.endswith(known) or norm == known:
                return True
    return False


def _scan_pwsh_for_paths(command: str) -> list:
    """Scan a PowerShell command body for code-file paths near mutating cmdlets."""
    body = command
    targets: list = []
    lower = body.lower()
    has_mut = any(c in lower for c in _PWSH_MUTATING_CMDLETS)
    if not has_mut:
        return targets
    for m in re.finditer(r"-Path\s+['\"]([^'\"]+)['\"]", body, re.IGNORECASE):
        targets.append(_normalize_path_token(m.group(1)))
    for m in re.finditer(r"-Path\s+(\S+)", body, re.IGNORECASE):
        cand = _normalize_path_token(m.group(1))
        if cand and cand not in targets:
            targets.append(cand)
    for m in re.finditer(r"['\"]([^'\"\n]+)['\"]", body):
        cand = _normalize_path_token(m.group(1))
        if cand and is_code_extension(cand) and cand not in targets:
            targets.append(cand)
    return [t for t in targets if t]


def _extract_redirect_targets(command: str) -> list:
    """Extract files appearing on the RHS of > or >> redirects."""
    out: list = []
    scan = re.sub(r"'[^']*'", "", command)
    scan = re.sub(r'"[^"]*"', "", scan)
    for m in re.finditer(r">{1,2}\s*([^\s|;&<>]+)", scan):
        cand = _normalize_path_token(m.group(1))
        if cand and not cand.startswith("&"):
            out.append(cand)
    return out


def parse_bash_command(command: str) -> dict:
    """Classify a Bash command. Returns dict with decision/reason/targets."""
    logger = logging.getLogger(HOOK_NAME)
    logger.info("parse_bash_command.enter cmd=%r", command[:200])
    if not command or not command.strip():
        return {"decision": "allow", "reason": "empty-command", "targets": []}
    sub_commands = _split_logical_commands(command)
    all_targets: list = []
    block_reasons: list = []
    for sub in sub_commands:
        result = _classify_single_command(sub)
        if result["decision"] == "require_cover":
            all_targets.extend(result["targets"])
            block_reasons.append(result["reason"])
    seen: set = set()
    unique_targets: list = []
    for t in all_targets:
        if t not in seen:
            seen.add(t)
            unique_targets.append(t)
    if unique_targets or block_reasons:
        out = {
            "decision": "require_cover",
            "reason": "; ".join(block_reasons) if block_reasons else "code-mutation",
            "targets": unique_targets,
        }
        logger.info("parse_bash_command.exit decision=require_cover targets=%s", unique_targets)
        return out
    logger.info("parse_bash_command.exit decision=allow")
    return {"decision": "allow", "reason": "whitelist-or-no-mutation", "targets": []}


def _classify_single_command(command: str) -> dict:
    """Classify one logical command (no ;, &&, ||, |)."""
    logger = logging.getLogger(HOOK_NAME)
    if not command or not command.strip():
        return {"decision": "allow", "reason": "empty", "targets": []}
    raw_lower = command.lower()
    is_pwsh = any(launcher in raw_lower for launcher in _BASH_PWSH_LAUNCHERS)
    tokens = _safe_shlex(command)
    if not tokens:
        return {"decision": "allow", "reason": "empty-tokens", "targets": []}
    if _is_dual_tooling_invocation(tokens):
        logger.info("classify.dual-tooling cmd=%r", command[:120])
        return {"decision": "allow", "reason": "dual-tooling", "targets": []}
    verb = _command_basename(tokens[0])

    # I2: redirect to a code path is a write regardless of leading verb
    # (echo > foo.py, cat > foo.py, printf > foo.py, etc.). Check first.
    early_redirects = [t for t in _extract_redirect_targets(command)
                       if is_code_extension(t)]
    if early_redirects:
        return {"decision": "require_cover",
                "reason": verb + "-redirect-to-code",
                "targets": early_redirects}

    if verb in _BASH_READONLY_VERBS:
        return {"decision": "allow", "reason": "readonly-verb", "targets": []}

    if verb in _BASH_TEST_RUNNERS:
        return {"decision": "allow", "reason": "test-runner", "targets": []}

    if verb in _BASH_PACKAGE_MANAGERS:
        return {"decision": "allow", "reason": "package-manager", "targets": []}

    if verb == "git" and len(tokens) >= 2:
        sub = _command_basename(tokens[1])
        if sub in {"status", "log", "diff", "show", "blame", "ls-files",
                   "rev-parse", "branch", "remote", "fetch", "worktree",
                   "config", "stash", "tag", "describe", "shortlog",
                   "ls-remote", "rev-list"}:
            return {"decision": "allow", "reason": "git-readonly", "targets": []}
        if sub in {"apply", "am"}:
            return {"decision": "require_cover",
                    "reason": "git-apply-opaque",
                    "targets": ["<git-apply-patch>"]}
        if sub in {"checkout", "restore", "mv", "rm"}:
            targets = _git_mutating_targets(tokens[1:], sub)
            if targets:
                return {"decision": "require_cover",
                        "reason": "git-" + sub,
                        "targets": targets}
            return {"decision": "allow", "reason": "git-" + sub + "-no-code-target",
                    "targets": []}
        if sub == "reset" and "--hard" in tokens:
            return {"decision": "require_cover",
                    "reason": "git-reset-hard",
                    "targets": ["<git-reset-hard>"]}
        return {"decision": "allow", "reason": "git-other", "targets": []}

    if is_pwsh or verb in _BASH_PWSH_LAUNCHERS:
        targets = _scan_pwsh_for_paths(command)
        code_targets = [t for t in targets if is_code_extension(t)]
        if code_targets:
            return {"decision": "require_cover",
                    "reason": "pwsh-mutating-cmdlet",
                    "targets": code_targets}
        return {"decision": "allow", "reason": "pwsh-no-code-target", "targets": []}

    if verb in _BASH_INPLACE_VERBS:
        if _has_inplace_flag(tokens):
            code_targets = _extract_code_path_args(tokens)
            if code_targets:
                return {"decision": "require_cover",
                        "reason": verb + "-inplace-on-code",
                        "targets": code_targets}
            return {"decision": "allow", "reason": verb + "-inplace-no-code",
                    "targets": []}
        return {"decision": "allow", "reason": verb + "-readonly", "targets": []}

    if verb in _BASH_MUTATING_VERBS:
        code_targets = _extract_code_path_args(tokens)
        if code_targets:
            return {"decision": "require_cover",
                    "reason": verb + "-on-code",
                    "targets": code_targets}
        return {"decision": "allow", "reason": verb + "-no-code-target", "targets": []}

    if verb in _BASH_INTERPRETERS:
        result = _classify_interpreter(tokens, command)
        if result is not None:
            return result

    return {"decision": "allow", "reason": "unknown-verb-allowed", "targets": []}


def _has_inplace_flag(tokens: list) -> bool:
    """True if any token is '-i', '-i.bak', '--in-place', or 'inplace' arg."""
    for i, tok in enumerate(tokens[1:], start=1):
        if tok == "-i" or tok.startswith("-i.") or tok == "--in-place":
            return True
        if tok == "inplace" and i >= 2 and tokens[i - 1] in ("-i", "--in-place"):
            return True
    return False


def _extract_code_path_args(tokens: list) -> list:
    """Extract path-like positional args whose extension is in CODE_EXTENSIONS."""
    out: list = []
    for tok in tokens[1:]:
        if not tok or tok.startswith("-"):
            continue
        norm = _normalize_path_token(tok)
        if not _looks_like_path(norm):
            continue
        if is_code_extension(norm):
            out.append(norm)
    return out


def _git_mutating_targets(args: list, sub: str) -> list:
    """Extract code-extension targets from git checkout|restore|mv|rm args."""
    out: list = []
    for tok in args[1:]:
        if not tok or tok.startswith("-"):
            continue
        norm = _normalize_path_token(tok)
        if not _looks_like_path(norm):
            continue
        if is_code_extension(norm):
            out.append(norm)
    return out


def _classify_interpreter(tokens: list, raw_command: str) -> Optional[dict]:
    """Classify python/bash/sh/node/... invocations."""
    logger = logging.getLogger(HOOK_NAME)
    verb = _command_basename(tokens[0])
    has_dash_alone = any(t == "-" for t in tokens[1:])
    has_dash_s = any(t == "-s" for t in tokens[1:])
    has_dash_c = False
    dash_c_index = -1
    for i, t in enumerate(tokens[1:], start=1):
        if t == "-c":
            has_dash_c = True
            dash_c_index = i
            break

    if has_dash_alone or has_dash_s:
        return {"decision": "require_cover",
                "reason": verb + "-stdin-opaque",
                "targets": ["<" + verb + "-stdin-opaque>"]}

    if has_dash_c and dash_c_index + 1 < len(tokens):
        snippet = tokens[dash_c_index + 1]
        write_patterns = [
            r"open\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]w",
            r"open\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]a",
            r"shutil\.copy[^\(]*\([^,]*,\s*['\"]([^'\"]+)['\"]",
            r"Path\s*\(\s*['\"]([^'\"]+)['\"]\s*\)\s*\.write",
        ]
        targets: list = []
        for pattern in write_patterns:
            for m in re.finditer(pattern, snippet):
                if m.groups():
                    cand = _normalize_path_token(m.group(1))
                    if cand and is_code_extension(cand):
                        targets.append(cand)
        if targets:
            return {"decision": "require_cover",
                    "reason": verb + "-c-write-to-code",
                    "targets": targets}
        if re.search(r"open\s*\([^)]*['\"][wa]", snippet):
            return {"decision": "require_cover",
                    "reason": verb + "-c-opaque-write",
                    "targets": ["<" + verb + "-c-opaque>"]}
        return {"decision": "allow", "reason": verb + "-c-no-write",
                "targets": []}

    skip_next = False
    script: Optional[str] = None
    for i, tok in enumerate(tokens[1:], start=1):
        if skip_next:
            skip_next = False
            continue
        if tok in ("-3", "-2", "-3.11", "-3.12", "-3.13", "-3.10"):
            continue
        if tok in ("-m", "-W", "-X"):
            return {"decision": "allow", "reason": verb + "-m-module",
                    "targets": []}
        if tok.startswith("-"):
            continue
        script = tok
        break

    if script is None:
        return {"decision": "allow", "reason": verb + "-repl", "targets": []}

    norm_script = _normalize_path_token(script)
    if not is_code_extension(norm_script):
        return {"decision": "allow", "reason": verb + "-non-code-script",
                "targets": []}

    for tool in _BASH_DUAL_TOOLING:
        if norm_script.endswith(tool) or norm_script == tool:
            return {"decision": "allow", "reason": "dual-tooling-script",
                    "targets": []}

    return {"decision": "require_cover",
            "reason": verb + "-script-execution",
            "targets": [norm_script]}


# ----------------------------------------------------------------------
# I4 - Skip ledger + actionable block messages
# ----------------------------------------------------------------------

def _append_skip_ledger(project_dir: Path, entry: dict) -> None:
    """Append one JSON line to skip-ledger.jsonl. Best-effort."""
    logger = logging.getLogger(HOOK_NAME)
    try:
        ledger = project_dir / SKIP_LEDGER_REL
        ledger.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(entry, ensure_ascii=False)
        with ledger.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError as exc:
        logger.exception("skip_ledger.write_err exc=%s", exc)
    except Exception as exc:
        logger.exception("skip_ledger.unexpected exc=%s", exc)


def _now_iso() -> str:
    """Return UTC timestamp in ISO-8601 format."""
    return datetime.datetime.now(datetime.timezone.utc).replace(
        microsecond=0).isoformat()


def _build_block_message(blocked_path: str, reason_code: str) -> str:
    """Build the actionable DENY message for emit_deny."""
    reason_text = {
        "no-results": "no codex-implement result found",
        "no-results-dir": "work/codex-implementations/ does not exist",
        "stale": "all codex-implement results older than 15 min",
        "fail-status": "most recent matching result has status != pass",
        "scope-miss": "no recent pass result covers this exact path",
        "parse-error": "could not parse codex-implement result",
        "bash-no-cover": "Bash command would mutate code without cover",
    }.get(reason_code, reason_code)
    msg = (
        "Code Delegation Protocol: " + blocked_path + " blocked ("
        + reason_text + ").\n\n"
        "To start the dual-implement track for this path, run:\n\n"
        "  py -3 .claude/scripts/codex-inline-dual.py \\n"
        "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
        "    --scope " + blocked_path + " \\n"
        "    --test \"py -3 -m pytest -q\"\n\n"
        "Then retry your edit. For multi-file tasks, use:\n"
        "  py -3 .claude/scripts/dual-teams-spawn.py --tasks <task.md> ...\n"
    )
    return msg


def emit_deny(blocked: str, reason_code: str, project_dir: Path,
              tool_name: str = "Edit") -> None:
    """Print the PreToolUse deny JSON to stdout and append ledger entry."""
    logger = logging.getLogger(HOOK_NAME)
    message = _build_block_message(blocked, reason_code)
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }
    logger.warning("emit_deny target=%s reason=%s", blocked, reason_code)
    _append_skip_ledger(project_dir, {
        "ts": _now_iso(),
        "tool": tool_name,
        "path": blocked,
        "decision": "deny",
        "reason": reason_code,
    })
    print(json.dumps(payload, ensure_ascii=False))


# ----------------------------------------------------------------------
# Tool dispatch
# ----------------------------------------------------------------------

def extract_targets(payload: dict) -> list:
    """Collect every file path this Edit/Write/MultiEdit/NotebookEdit call edits."""
    if not isinstance(payload, dict):
        return []
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return []
    paths: list = []
    if tool_name in {"Edit", "Write", "NotebookEdit"}:
        p = tool_input.get("file_path") or tool_input.get("notebook_path")
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


def decide(payload: dict, project_dir: Path) -> bool:
    """Core gate. True to allow; False after emitting deny."""
    logger = logging.getLogger(HOOK_NAME)
    event = payload.get("hook_event_name", "") if isinstance(payload, dict) else ""
    tool_name = payload.get("tool_name", "") if isinstance(payload, dict) else ""
    logger.info("decide.enter event=%s tool=%s", event, tool_name)
    if event and event != "PreToolUse":
        logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
        return True
    if tool_name not in {"Edit", "Write", "MultiEdit", "Bash", "NotebookEdit"}:
        logger.info("decide.passthrough reason=unknown-tool tool=%s", tool_name)
        return True
    if is_dual_teams_worktree(project_dir):
        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
        return True

    if tool_name == "Bash":
        return _decide_bash(payload, project_dir)
    return _decide_edit(payload, project_dir, tool_name)


def _decide_edit(payload: dict, project_dir: Path, tool_name: str) -> bool:
    """Edit/Write/MultiEdit/NotebookEdit branch."""
    logger = logging.getLogger(HOOK_NAME)
    raw_targets = extract_targets(payload)
    if not raw_targets:
        logger.info("decide.passthrough reason=no-targets tool=%s", tool_name)
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
            logger.info("decide.allow-target rel=%s reason=non-code-or-exempt", rel)
            _append_skip_ledger(project_dir, {
                "ts": _now_iso(), "tool": tool_name, "path": rel,
                "decision": "allow", "reason": "non-code-or-exempt",
            })
            continue
        if is_dual_teams_worktree(abs_path):
            logger.info("decide.allow-target rel=%s reason=dual-teams-target abs=%s",
                        rel, abs_path)
            _append_skip_ledger(project_dir, {
                "ts": _now_iso(), "tool": tool_name, "path": rel,
                "decision": "allow", "reason": "dual-teams-target",
            })
            continue
        covered, reason = find_cover(project_dir, rel)
        if not covered:
            emit_deny(rel, reason, project_dir, tool_name=tool_name)
            logger.info("decide.exit target=%s allowed=False reason=%s", rel, reason)
            return False
        logger.info("decide.allow-target rel=%s reason=covered", rel)
        _append_skip_ledger(project_dir, {
            "ts": _now_iso(), "tool": tool_name, "path": rel,
            "decision": "allow", "reason": reason,
        })
    logger.info("decide.exit allowed=True")
    return True


def _decide_bash(payload: dict, project_dir: Path) -> bool:
    """Bash branch (I2). Parse command, classify, check cover for each target."""
    logger = logging.getLogger(HOOK_NAME)
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        logger.info("decide_bash.no-input")
        return True
    command = tool_input.get("command", "")
    if not isinstance(command, str) or not command.strip():
        logger.info("decide_bash.empty-command")
        return True
    parsed = parse_bash_command(command)
    if parsed["decision"] == "allow":
        logger.info("decide_bash.allow reason=%s", parsed["reason"])
        _append_skip_ledger(project_dir, {
            "ts": _now_iso(), "tool": "Bash", "cmd": command[:200],
            "decision": "allow", "reason": parsed["reason"],
        })
        return True
    targets = parsed["targets"]
    if not targets:
        logger.info("decide_bash.require_cover-no-targets reason=%s", parsed["reason"])
        emit_deny("<bash-command>", "bash-no-cover", project_dir, tool_name="Bash")
        return False
    for target in targets:
        if target.startswith("<") and target.endswith(">"):
            emit_deny(target, "bash-no-cover", project_dir, tool_name="Bash")
            logger.info("decide_bash.exit allowed=False reason=opaque-target target=%s", target)
            return False
        norm = _normalize_path_token(target)
        abs_path = resolve_target(project_dir, norm)
        if abs_path is not None:
            rel = rel_posix(project_dir, abs_path) or norm
        else:
            rel = norm
        if abs_path is not None and is_dual_teams_worktree(abs_path):
            logger.info("decide_bash.allow-target rel=%s reason=dual-teams-target", rel)
            _append_skip_ledger(project_dir, {
                "ts": _now_iso(), "tool": "Bash", "path": rel,
                "decision": "allow", "reason": "dual-teams-target",
            })
            continue
        covered, reason = find_cover(project_dir, rel)
        if not covered:
            emit_deny(rel, reason, project_dir, tool_name="Bash")
            logger.info("decide_bash.exit target=%s allowed=False reason=%s", rel, reason)
            return False
        _append_skip_ledger(project_dir, {
            "ts": _now_iso(), "tool": "Bash", "path": rel,
            "decision": "allow", "reason": reason,
        })
    logger.info("decide_bash.exit allowed=True")
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
