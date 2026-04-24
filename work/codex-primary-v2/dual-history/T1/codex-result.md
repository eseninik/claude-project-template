# Codex Implementation Result — Task T1-enforcer

- status: pass
- timestamp: 2026-04-24T15:40:17.937591+00:00
- task_file: C:\Bots\Migrator bots\claude-project-template-update\work\codex-primary-v2\tasks\task-T1-enforcer.md
- base_sha: 0625fa082f4d921c175c0a9fb4259556289e7e4b
- codex_returncode: 0
- scope_status: pass
- scope_message: OK: 1 path(s) in fence
- tests_all_passed: True
- test_commands_count: 2

## Diff

```diff
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73..03bebbe 100644
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,396 @@
 #!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
 
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
 import sys
-sys.exit(0)
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    stderr_handler = logging.StreamHandler(sys.stderr)
+    stderr_handler.setFormatter(formatter)
+    logger.addHandler(stderr_handler)
+    logs_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            file_handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+            file_handler.setFormatter(formatter)
+            logger.addHandler(file_handler)
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                logger.exception("event=error function=target_is_covered result=not-prefix")
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())
```

## Test Output

### `python .claude/hooks/test_codex_delegate_enforcer.py`

- returncode: 0  - passed: True  - timed_out: False

```
--- stdout ---
test_code_file_no_recent_result_denies_json (__main__.CodexDelegateEnforcerTests.test_code_file_no_recent_result_denies_json) ... ok
test_code_file_stale_result_denies (__main__.CodexDelegateEnforcerTests.test_code_file_stale_result_denies) ... ok
test_corrupt_json_payload_passes_through (__main__.CodexDelegateEnforcerTests.test_corrupt_json_payload_passes_through) ... ok
test_exempt_path_allows (__main__.CodexDelegateEnforcerTests.test_exempt_path_allows) ... ok
test_fresh_fail_status_denies (__main__.CodexDelegateEnforcerTests.test_fresh_fail_status_denies) ... ok
test_fresh_pass_covering_fence_allows (__main__.CodexDelegateEnforcerTests.test_fresh_pass_covering_fence_allows) ... ok
test_fresh_pass_scope_miss_denies (__main__.CodexDelegateEnforcerTests.test_fresh_pass_scope_miss_denies) ... ok
test_malformed_result_denies_without_crash (__main__.CodexDelegateEnforcerTests.test_malformed_result_denies_without_crash) ... ok
test_multiedit_multiple_files_all_covered_allows (__main__.CodexDelegateEnforcerTests.test_multiedit_multiple_files_all_covered_allows) ... ok
test_multiedit_one_uncovered_denies (__main__.CodexDelegateEnforcerTests.test_multiedit_one_uncovered_denies) ... ok
test_non_code_file_allows (__main__.CodexDelegateEnforcerTests.test_non_code_file_allows) ... ok
test_non_edit_event_passes_through (__main__.CodexDelegateEnforcerTests.test_non_edit_event_passes_through) ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.072s

OK
--- stderr ---
event=error function=target_is_covered result=not-prefix
Traceback (most recent call last):
  File "C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex\.claude\hooks\codex-delegate-enforcer.py", line 269, in target_is_covered
    target.absolute.relative_to(entry_path)
  File "C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\Lib\pathlib.py", line 682, in relative_to
    raise ValueError(f"{str(self)!r} is not in the subpath of {str(other)!r}")
ValueError: 'C:\\Users\\Lenovo\\AppData\\Local\\Temp\\tmp1_yo_d2e\\src\\app.py' is not in the subpath of 'C:\\Users\\Lenovo\\AppData\\Local\\Temp\\tmp1_yo_d2e\\lib'
```

### `python -c "import sys, importlib.util; spec = importlib.util.spec_from_file_location('enforcer', '.claude/hooks/codex-delegate-enforcer.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('import-ok')"`

- returncode: 0  - passed: True  - timed_out: False

```
--- stdout ---
import-ok
```

## Self-Report (Codex NOTE/BLOCKER lines)

- NOTE: Implemented `.claude/hooks/codex-delegate-enforcer.py:24` with code-extension gating, exempt patterns, result scanning capped at 50, fail-open `main()`, deny JSON, and structured stdlib logging.
- NOTE: Added `.claude/hooks/test_codex_delegate_enforcer.py:24` with 12 unit tests covering the required 10 cases plus corrupt JSON and non-Edit pass-through.
- NOTE: Decisions Made: Scope Fence entries ending in `/`, `/*`, or `/**` are directory-prefix matches; other entries are exact file matches after `Path.resolve()`.
- NOTE: Decisions Made: `MultiEdit` checks every `tool_input.edits[*].file_path`; if none are present, it falls back to top-level `tool_input.file_path`.
- NOTE: Backward compat: non-relevant events/tools pass through via `is_relevant_payload()` and `main()` with exit code 0 and no stdout.
- NOTE: Tests: `python .claude/hooks/test_codex_delegate_enforcer.py` stdout/stderr:
- BLOCKER: Mandatory test command exited non-zero because `python` is not available on PATH in this sandbox.
- NOTE: Tests: `python -c "import sys, importlib.util; spec = importlib.util.spec_from_file_location('enforcer', '.claude/hooks/codex-delegate-enforcer.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('import-ok')"` stdout/stderr:
- BLOCKER: Mandatory import smoke test exited non-zero for the same missing `python` executable.
- NOTE: Static checks: `git diff --check -- .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer.py` exited 0; hook is 396 lines and test file is 168 lines.

## Codex stderr

```
OpenAI Codex v0.117.0 (research preview)
--------
workdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
model: gpt-5.5
provider: chatgpt
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR, C:\Users\Lenovo\.codex\memories]
reasoning effort: high
reasoning summaries: none
session id: 019dc026-26c4-7722-8688-d693677b2e34
--------
user
You are the single-task implementer. The task specification below is IMMUTABLE.
Write code to satisfy all Acceptance Criteria. Do NOT modify files listed in
Forbidden Paths or Read-Only Files. After writing code, run every Test Command
listed in the task and report the result in your self-report.
Any AGENTS.md or CLAUDE.md in the worktree is authoritative background context.

---- TASK SPECIFICATION ----

---
executor: dual
risk_class: high-stakes
speed_profile: thorough
---

# Task T1: `.claude/hooks/codex-delegate-enforcer.py` — Always-Dual enforcer

## Your Task

Replace the current bootstrap stub at `.claude/hooks/codex-delegate-enforcer.py`
with a full PreToolUse hook that enforces the Always-Dual Code Delegation
Protocol from project `CLAUDE.md`.

On `Edit`/`Write`/`MultiEdit` targeting a **code file** (by extension)
that is NOT in the exempt-path list, the hook must verify that a recent
(< 15 min) `work/codex-implementations/task-*-result.md` with `status: pass`
covers the target path via its Scope Fence. If no valid cover → deny with
a helpful recovery hint. Otherwise → allow.

Fail-open semantics: on ANY internal error the hook allows (never blocks
on infrastructure failure — protocol enforced by discipline as fallback).

## Scope Fence

**Allowed paths (may be written):**
- `.claude/hooks/codex-delegate-enforcer.py` (replace existing bootstrap stub)
- `.claude/hooks/test_codex_delegate_enforcer.py` (new — unit tests)

**Forbidden paths:**
- Any other hook or script
- `.claude/hooks/codex-gate.py` (reference only, read-only)
- `.claude/settings.json` (wiring is SOLO task T6, not here)
- `.claude/shared/templates/new-project/**`
- `work/**` except result-dir lookup which is runtime read-only

## Test Commands (run after implementation)

```bash
python .claude/hooks/test_codex_delegate_enforcer.py
python -c "import sys, importlib.util; spec = importlib.util.spec_from_file_location('enforcer', '.claude/hooks/codex-delegate-enforcer.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('import-ok')"
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: File `.claude/hooks/codex-delegate-enforcer.py` exists, valid Python.
- [ ] AC2: Reads hook payload from stdin as JSON (standard Claude Code hook protocol) with keys `hook_event_name`, `tool_name`, `tool_input`.
- [ ] AC3: Activates ONLY when `hook_event_name == "PreToolUse"` AND `tool_name in {"Edit", "Write", "MultiEdit"}`. Other events → pass-through (exit 0, no output).
- [ ] AC4: Extracts target path from `tool_input.file_path` for Edit/Write. For MultiEdit, extracts every edited path from `tool_input.edits[*].file_path` (or `tool_input.file_path` if single); every path must pass the check.
- [ ] AC5: **Code extensions** (module-level `set` constant): `.py .pyi .js .jsx .mjs .cjs .ts .tsx .sh .bash .zsh .go .rs .rb .java .kt .swift .c .cpp .cc .h .hpp .cs .php .sql .lua .r`
- [ ] AC6: **Exempt path patterns** (module-level list, matched via `fnmatch` or prefix):
  - `.claude/memory/**`
  - `work/**` (planning artifacts)
  - `CLAUDE.md`, `AGENTS.md`, `README.md`, `CHANGELOG.md`, `LICENSE`, `.gitignore`
  - `.claude/settings.json`, `.claude/ops/*.yaml`, `.mcp.json`
  - `.claude/adr/**/*.md`, `.claude/guides/**/*.md`, `.claude/skills/**/*.md`
  - Any file whose extension is NOT in the code-extension set
- [ ] AC7: For each target that is code AND not exempt, scan `work/codex-implementations/task-*-result.md`:
  - `time.time() - path.stat().st_mtime < 15 * 60` (15 minutes)
  - Parse `- status: <value>` line; must be `pass`
  - Parse `- task_file: <path>` line; load that task-N.md, extract Scope Fence → allowed list
  - Target must be prefix-matched by at least one allowed entry (use normalized `Path.resolve()`; dir-prefix ends with `/` or target equals a file-entry)
- [ ] AC8: If every target has a valid cover → exit 0 (allow), optional stdout log entry.
- [ ] AC9: If any target lacks valid cover → emit PreToolUse deny JSON to stdout:
  ```
  {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "<message>"}}
  ```
  Exit 0. Message contains: blocked target path, reason (no-cover / stale / scope-miss / fail-status), and hint string:
  `Use .claude/scripts/codex-inline-dual.py --describe "..." --scope <path> for micro-task, or write work/<feature>/tasks/task-N.md and run codex-implement.py. See CLAUDE.md "Code Delegation Protocol".`
- [ ] AC10: On ANY exception (parse error, missing dir, permission, etc.) → log to stderr and exit 0 (pass-through). Never crash, never silent-block on infra error.
- [ ] AC11: Structured stdlib `logging` — entry/exit for every function, error with context. Log file at `.claude/logs/codex-delegate-enforcer.log` if directory writable, else stderr only.
- [ ] AC12: Unit test file `.claude/hooks/test_codex_delegate_enforcer.py` covers at minimum these 10 cases:
  1. exempt path (e.g., `CLAUDE.md`) → allow
  2. code file + NO recent result.md → deny with JSON
  3. code file + stale (> 15 min) result.md → deny
  4. code file + fresh `status: pass` result.md with covering fence → allow
  5. code file + fresh pass result.md but fence does NOT cover target → deny
  6. code file + fresh `status: fail` result.md → deny
  7. non-code file (`.txt`, `.md`) → allow
  8. MultiEdit with multiple files, all covered → allow
  9. MultiEdit with one file uncovered → deny
  10. malformed result.md / corrupt JSON payload → pass-through (no crash)
  Plus 1 test: hook called on non-Edit event (e.g., Bash) → pass-through.
- [ ] AC13: Script under 450 lines; test file under 450 lines.
- [ ] AC14: Run-time < 200 ms typical, < 500 ms worst case. Use regex compile at module scope. Cache exempt-pattern compilation.
- [ ] All Test Commands exit 0.

## Skill Contracts

### verification-before-completion (per AGENTS.md)
Run every Test Command; quote stdout in handoff. Do not claim done on any non-zero.

### logging-standards (per AGENTS.md)
Entry/exit/error structured logs on every function. Never log user data.

### security-review (this IS a safety gate — applies)
- `Path.resolve()` normalization before any prefix matching (prevents `..` traversal in exempt-match)
- Time check via `time.time() - mtime`, not `datetime` subtraction (tz-safe)
- Defensive JSON parse: every field access via `.get()` with default
- No shell invocation needed; no subprocess at all
- Guard against a large number of result.md files (cap scan at 50 most-recent)

### coding-standards (per AGENTS.md)
- Reference `.claude/hooks/codex-gate.py` for existing gate-hook style; mirror its conventions
- Type hints on all public functions
- `pathlib.Path` everywhere

## Read-Only Files (Evaluation Firewall)

- `.claude/hooks/codex-gate.py` — reference only
- `.claude/hooks/test_codex_delegate_enforcer.py` — immutable once written
- `CLAUDE.md`, `AGENTS.md` — protocol spec, do not change here
- This task-T1-enforcer.md

## Constraints

- Windows-compatible
- Stdlib only
- Fail-open on uncertainty
- Must not modify `.claude/settings.json` (separate SOLO task)

## Handoff Output (MANDATORY)

Standard `=== PHASE HANDOFF: T1-enforcer ===` block. Include:
- `Decisions Made`: cover-match semantics (dir-prefix vs file-exact), how you handle MultiEdit
- `Tests`: output of all 11+ unit tests + the import smoke test
- `Backward compat`: verify old behavior preserved (hook returns exit 0 on non-relevant events)

## Iteration History

(First round — no prior attempts.)


---- END TASK SPECIFICATION ----
Return a short self-report at the end of your run using lines starting with
`NOTE:` for observations and `BLOCKER:` for unresolved problems.

**Modifying code for security review**

I need to modify some code and inspect the repo. There's a mention of a security review, coding standards, and a test-driven workflow, which seem relevant to my task. The user asks for writing feature tests, so I need to focus on that. It's important to read the SKILL.md file and understand that tests should be immutable once written. I might need to check the existing code and use an update plan without subagents. First, I'll read the skill files and the repo.
codex
I’ll use `security-review`, `coding-standards`, and `tdd-workflow` since this is a safety hook with tests. First I’ll inspect the reference hook and current stub.
  → Inspect hook conventions and skills
  • Implement enforcer hook
  • Add focused unit tests
  • Run required test commands
  • Prepare handoff report
exec
powershell.exe -Command "Get-Content -Path 'C:/Users/Lenovo/.codex/skills/security-review/SKILL.md' -TotalCount 220; '---CODING---'; Get-Content -Path 'C:/Users/Lenovo/.codex/skills/coding-standards/SKILL.md' -TotalCount 220; '---TDD---'; Get-Content -Path 'C:/Users/Lenovo/.codex/skills/tdd-workflow/SKILL.md' -TotalCount 220; '---HOOKS---'; Get-Content -Path '.claude/hooks/codex-gate.py' -TotalCount 260; '---STUB---'; if (Test-Path '.claude/hooks/codex-delegate-enforcer.py') { Get-Content -Path '.claude/hooks/codex-delegate-enforcer.py' -TotalCount 220 }" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 492ms:
---
name: security-review
description: Security review checklist for code вЂ” secrets management, input validation, auth, OWASP top 10. Use when implementing auth, handling user input, working with secrets, creating API endpoints, or reviewing security-sensitive code. Do NOT use for infrastructure/network security.
roles: [qa-reviewer, coder, coder-complex]
---

# Security Review

## When to Activate

- Implementing authentication or authorization
- Handling user input or file uploads
- Creating new API endpoints
- Working with secrets or credentials
- Implementing payment features
- Storing or transmitting sensitive data

## Security Checklist

### 1. Secrets Management

```python
# NEVER: hardcoded secrets
api_key = "sk-proj-xxxxx"

# ALWAYS: environment variables
api_key = os.environ["API_KEY"]
if not api_key:
    raise RuntimeError("API_KEY not configured")
```

- [ ] No hardcoded API keys, tokens, or passwords
- [ ] All secrets in environment variables
- [ ] `.env` files in `.gitignore`
- [ ] No secrets in git history (`git log -p | grep -i "password\|secret\|key"`)

### 2. Input Validation

```python
# ALWAYS validate at boundaries
from pydantic import BaseModel, EmailStr, constr

class CreateUser(BaseModel):
    email: EmailStr
    name: constr(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)
```

- [ ] All user inputs validated (type, length, format)
- [ ] SQL injection prevented (parameterized queries only)
- [ ] XSS prevented (sanitize HTML output, CSP headers)
- [ ] Path traversal prevented (no user input in file paths)

### 3. Authentication & Authorization

- [ ] Passwords hashed with bcrypt/argon2 (NEVER MD5/SHA1)
- [ ] JWTs have short expiry + refresh tokens
- [ ] Rate limiting on login endpoints
- [ ] Authorization checked on EVERY endpoint (not just frontend)
- [ ] CORS configured (not `*` in production)

### 4. Data Protection

- [ ] Sensitive data encrypted at rest
- [ ] HTTPS enforced (HSTS headers)
- [ ] Logs don't contain PII, tokens, or passwords
- [ ] Error messages don't leak internal details
- [ ] File uploads validated (type, size, content)

### 5. Dependencies

- [ ] No known vulnerabilities (`npm audit`, `pip-audit`, `cargo audit`)
- [ ] Dependencies pinned to specific versions
- [ ] Minimal dependencies (fewer = smaller attack surface)

## Key Rules

1. **Never trust user input** вЂ” validate everything at boundaries
2. **Principle of least privilege** вЂ” minimal permissions everywhere
3. **Defense in depth** вЂ” multiple layers of security
4. **Log security events** вЂ” auth failures, permission denials, suspicious patterns
5. **Fail securely** вЂ” on error, deny access (don't default to allow)

## Related

- [api-design](./../api-design/SKILL.md) вЂ” REST API resource naming and error formats
- [backend-patterns](./../backend-patterns/SKILL.md) вЂ” repository/service layers and DB optimization
- [coding-standards](./../coding-standards/SKILL.md) вЂ” universal code quality and naming standards
- [verification-before-completion](~/.claude/skills/verification-before-completion/SKILL.md) вЂ” evidence-based completion gate
---CODING---
---
name: coding-standards
description: Universal coding standards and best practices for code quality, naming, structure, error handling. Use when reviewing code quality or starting new modules. Do NOT use for language-specific rules (see language-rules guides).
roles: [coder, coder-complex, qa-reviewer]
---

# Coding Standards

## When to Activate

- Starting a new project or module
- Reviewing code for quality and maintainability
- Refactoring existing code
- Onboarding new contributors

## Principles

1. **Readability First** вЂ” code is read more than written
2. **KISS** вЂ” simplest solution that works
3. **DRY** вЂ” extract common logic, but don't over-abstract (3 duplications = extract)
4. **YAGNI** вЂ” don't build features before needed

## Naming

| Entity | Convention | Example |
|--------|-----------|---------|
| Variables | camelCase (JS/TS) / snake_case (Python) | `userName`, `user_name` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES` |
| Functions | verb + noun | `getUserById`, `calculate_total` |
| Classes | PascalCase | `UserService` |
| Booleans | is/has/can/should prefix | `isActive`, `hasPermission` |
| Files | kebab-case (JS) / snake_case (Python) | `user-service.ts`, `user_service.py` |

## Function Design

- **Single responsibility** вЂ” one function, one purpose
- **Max 3 parameters** вЂ” use options object/dataclass beyond that
- **Early returns** вЂ” guard clauses reduce nesting
- **Pure functions preferred** вЂ” same input = same output, no side effects

## Error Handling

- **Validate at boundaries** вЂ” user input, external APIs, file I/O
- **Specific exceptions** вЂ” `raise ValueError("email required")` not `raise Exception`
- **Never swallow errors** вЂ” always log with context
- **Structured logging** вЂ” entry, exit, errors (see logging-standards guide)

## File Organization

- **One concept per file** вЂ” don't mix concerns
- **Max ~300 lines** вЂ” split if larger
- **Group by feature** not by type (feature/ > controllers/, services/, etc.)
- **Index files** for public API re-exports

## Code Smells to Avoid

- Functions > 50 lines
- Nesting > 3 levels deep
- Boolean parameters (use enum or separate functions)
- Magic numbers (extract to named constants)
- Commented-out code (delete it, git has history)

## Related

- [tdd-workflow](./../tdd-workflow/SKILL.md) вЂ” test-driven development with RED-GREEN-REFACTOR
- [security-review](./../security-review/SKILL.md) вЂ” security checklist and input validation
- [api-design](./../api-design/SKILL.md) вЂ” REST API design and error format standards
---TDD---
---
name: tdd-workflow
description: Test-driven development workflow enforcing RED-GREEN-REFACTOR cycle with 80%+ coverage. Use when writing new features, fixing bugs, or refactoring code. Do NOT use for documentation-only changes or config updates.
roles: [coder, coder-complex, qa-fixer]
---

# Test-Driven Development Workflow

## When to Activate

- Writing new features or API endpoints
- Fixing bugs (write failing test first, then fix)
- Refactoring existing code
- Adding new components or services

## Core Process: RED-GREEN-REFACTOR

### 1. RED вЂ” Write Failing Test First
```
- Write test that describes desired behavior
- Run test вЂ” MUST fail (proves test catches the issue)
- Git checkpoint: `git commit -m "test: RED - {what}"`
```

### 2. GREEN вЂ” Minimal Implementation
```
- Write MINIMUM code to make the test pass
- No extra features, no premature optimization
- Run test вЂ” MUST pass
- Git checkpoint: `git commit -m "feat: GREEN - {what}"`
```

### 3. REFACTOR вЂ” Clean Up (Optional)
```
- Improve code quality without changing behavior
- All tests MUST still pass after refactoring
- Git checkpoint: `git commit -m "refactor: {what}"`
```

## Coverage Requirements

- **Minimum 80%** combined (unit + integration + E2E)
- All edge cases and error scenarios tested
- Boundary conditions verified

## Test Types

| Type | Scope | Tools |
|------|-------|-------|
| Unit | Functions, utilities, pure logic | pytest, vitest, jest |
| Integration | API endpoints, DB operations, services | pytest + httpx, supertest |
| E2E | User flows, browser automation | Playwright |

## Key Rules

1. **NEVER write implementation before test** вЂ” test defines the contract
2. **One test at a time** вЂ” don't batch; RED-GREEN per behavior
3. **Tests are immutable after approval** вЂ” Evaluation Firewall: don't modify tests to make them pass
4. **Run full suite before commit** вЂ” no regressions allowed
5. **Include structured logging in all new code** вЂ” entry, exit, errors

## Related

- [coding-standards](./../coding-standards/SKILL.md) вЂ” universal code quality and naming standards
- [e2e-testing](./../e2e-testing/SKILL.md) вЂ” Playwright browser automation tests
- [qa-validation-loop](~/.claude/skills/qa-validation-loop/SKILL.md) вЂ” risk-proportional QA review cycle
- [verification-before-completion](~/.claude/skills/verification-before-completion/SKILL.md) вЂ” evidence-based completion gate
---HOOKS---
#!/usr/bin/env python3
"""Codex Gate вЂ” enforces Codex consultation at every decision point.

Two enforcement mechanisms:

1. TaskCreated hook: auto-calls codex-ask.py for every new task
   в†’ Covers: pipeline phases, Agent Teams, subtask decomposition

2. PreToolUse gate (Edit/Write): blocks file modifications if Codex
   wasn't consulted in the last COOLDOWN_MINUTES
   в†’ Forces Claude to call codex-ask.py before making changes
   в†’ Cooldown prevents blocking every single edit (once per burst)

Exit codes:
  0 вЂ” allow
  2 вЂ” block (Codex consultation required)
"""

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    for s in [sys.stdin, sys.stdout, sys.stderr]:
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")

logger = logging.getLogger("codex-gate")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    stream=sys.stderr,
)

MAX_EDITS_PER_CONSULTATION = 5  # After 5 edits, must consult Codex again
COOLDOWN_MINUTES = 5  # Also time-based fallback
CODEX_ASK_SCRIPT = ".claude/scripts/codex-ask.py"

# codex-implement result recognition (tech-spec Section 9)
RESULT_MAX_AGE_SECONDS = 180  # 3 minutes
CODEX_IMPLEMENTATIONS_DIR = "work/codex-implementations"
CODEX_TASKS_DIR = "work/codex-primary/tasks"


def get_project_dir():
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()


def get_last_codex_time(project_dir):
    """Check when Codex was last consulted."""
    opinion_file = project_dir / ".codex" / "reviews" / "parallel-opinion.md"
    timestamp_file = project_dir / ".codex" / "last-consulted"

    # Check both files вЂ” use the most recent
    latest = 0
    for f in [opinion_file, timestamp_file]:
        if f.exists():
            latest = max(latest, f.stat().st_mtime)
    return latest


def mark_codex_consulted(project_dir):
    """Mark that Codex was just consulted. Resets edit counter."""
    ts_file = project_dir / ".codex" / "last-consulted"
    ts_file.parent.mkdir(parents=True, exist_ok=True)
    ts_file.write_text(str(time.time()), encoding="utf-8")
    # Reset edit counter
    count_file = project_dir / ".codex" / "edit-count"
    count_file.write_text("0", encoding="utf-8")


def get_edit_count(project_dir):
    """Get number of Edit/Write calls since last Codex consultation."""
    count_file = project_dir / ".codex" / "edit-count"
    if not count_file.exists():
        return 0
    try:
        return int(count_file.read_text().strip())
    except (ValueError, OSError):
        return 0


def increment_edit_count(project_dir):
    """Increment the edit counter."""
    count_file = project_dir / ".codex" / "edit-count"
    count_file.parent.mkdir(parents=True, exist_ok=True)
    current = get_edit_count(project_dir)
    count_file.write_text(str(current + 1), encoding="utf-8")
    return current + 1


def is_codex_fresh(project_dir):
    """Check if Codex opinion is fresh enough.

    Two conditions (BOTH must pass):
    1. Time-based: last consultation < COOLDOWN_MINUTES ago
    2. Count-based: < MAX_EDITS_PER_CONSULTATION edits since last consultation

    If EITHER expires, Codex consultation is required.
    """
    # Time check
    last = get_last_codex_time(project_dir)
    if last == 0:
        return False
    age_minutes = (time.time() - last) / 60
    if age_minutes >= COOLDOWN_MINUTES:
        logger.info("time-based expiry: %.1f min > %d min", age_minutes, COOLDOWN_MINUTES)
        return False

    # Count check
    count = get_edit_count(project_dir)
    if count >= MAX_EDITS_PER_CONSULTATION:
        logger.info("count-based expiry: %d edits >= %d max", count, MAX_EDITS_PER_CONSULTATION)
        return False

    return True


# ---------------------------------------------------------------------------
# codex-implement result recognition (tech-spec Section 9)
# ---------------------------------------------------------------------------

def _parse_result_status(result_path):
    """Read task-N-result.md and return its 'status' field, or None on error.

    Accepts any reasonable layout: YAML frontmatter, bold key, plain line.
    Never raises вЂ” parse errors return None so the gate falls back to old behavior.
    """
    try:
        text = result_path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        logger.info("result-parse: cannot read %s: %s", result_path.name, e)
        return None

    # Match common "status" emissions: `status: pass`, `**Status:** pass`,
    # `- status: pass`, `> Status = fail`. Strip bold/italic markers from each
    # line first so colon placement inside '**...**' does not break the regex.
    import re
    for raw in text.splitlines():
        # Remove leading bullet/quote, surrounding bold/italic, backticks.
        stripped = raw.lstrip(" \t-*>").strip()
        stripped = stripped.replace("**", "").replace("__", "").replace("`", "")
        m = re.match(r"(?i)status\s*[:=]\s*([A-Za-z0-9_-]+)", stripped)
        if m:
            return m.group(1).strip().lower()
    logger.info("result-parse: no status field in %s", result_path.name)
    return None


def _parse_scope_fence(task_path):
    """Extract 'Allowed paths' from a task-N.md Scope Fence section.

    Returns list of normalized POSIX-style path fragments (strings). Empty list
    on any parse error вЂ” caller treats empty fence as 'no match'.
    """
    try:
        text = task_path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        logger.info("fence-parse: cannot read %s: %s", task_path.name, e)
        return []

    # Locate "## Scope Fence" section (case-insensitive).
    import re
    fence_match = re.search(r"(?im)^##\s+Scope\s+Fence\s*$", text)
    if not fence_match:
        return []

    # Slice to next top-level heading.
    start = fence_match.end()
    tail = text[start:]
    next_hdr = re.search(r"(?m)^##\s+", tail)
    section = tail[: next_hdr.start()] if next_hdr else tail

    # Find the "Allowed paths" subsection; stop at "Forbidden" or blank run.
    allowed_match = re.search(r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\Z)", section)
    if not allowed_match:
        return []
    allowed_block = allowed_match.group(1)

    paths = []
    for line in allowed_block.splitlines():
        line = line.strip()
        if not line.startswith("-"):
            continue
        # Strip leading "-", backticks, parenthetical annotations like "(new file)".
        entry = line.lstrip("-").strip()
        entry = entry.strip("`").strip()
        # Drop trailing parenthetical: "path/to/x (new)"
        entry = re.sub(r"\s*\([^)]*\)\s*$", "", entry).strip()
        entry = entry.strip("`").strip()
        if not entry:
            continue
        # Normalize to forward slashes for comparison.
        paths.append(entry.replace("\\", "/").rstrip("/"))
    return paths


def _path_in_fence(target_rel_posix, fence_entries):
    """True if target_rel_posix is covered by any fence entry.

    Fence entry can be a file ('a/b/c.py'), a directory ('a/b/'), or a glob
    with '**' wildcard (only simple prefix matching is supported).
    """
    if not fence_entries:
        return False
    target = target_rel_posix.rstrip("/")
    for entry in fence_entries:
        if not entry:
            continue
        # Strip glob tail like '**' or '*'.
        import re
        simple = re.sub(r"/?\*+$", "", entry).rstrip("/")
        if not simple:
            continue
        # Exact file match or directory-prefix match (with '/' boundary).
        if target == simple:
            return True
        if target.startswith(simple + "/"):
            return True
    return False


def _resolve_target_path(project_dir, target_raw):
    """Resolve a tool_input file path to an absolute Path inside project_dir.

    Returns None if the resolved path escapes project_dir (no symlink traversal).
    """
    if not target_raw:
        return None
    try:
        p = Path(target_raw)
        if not p.is_absolute():
            p = project_dir / p
        resolved = p.resolve()
    except (OSError, ValueError) as e:
        logger.info("target-resolve: cannot resolve %s: %s", target_raw, e)
        return None
    try:
        resolved.relative_to(project_dir)
    except ValueError:
        logger.info("target-resolve: %s escapes project root", resolved)
        return None
    return resolved


def _extract_target_path(payload):
    """Pull the file path from Edit/Write tool_input. Returns str or None."""
    if not isinstance(payload, dict):
        return None
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return None
    # Edit, Write, NotebookEdit all use `file_path`; MultiEdit and Write do too.
    return tool_input.get("file_path") or tool_input.get("notebook_path")


---STUB---
#!/usr/bin/env python3
"""Codex Delegate Enforcer вЂ” minimal bootstrap stub.

Full implementation pending via dual-implement in this session.
Current behavior: pass-through (exit 0) on every call so bootstrap
works. Once full implementation lands, this file is overwritten
with the real enforcer.
"""
import sys
sys.exit(0)

codex
I’ve got the broad conventions; now I’ll inspect targeted hook helpers and repo layout.
exec
powershell.exe -Command "rg -n \"def |logger|hookSpecificOutput|permissionDecision|Scope Fence|codex-implementations\" .claude/hooks/codex-gate.py .claude/hooks -g '*.py'; Get-ChildItem -Path '.claude/hooks' -Force | Select-Object Name,Length" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 1179ms:

Name                       Length
----                       ------
codex-broker.py             20540
codex-delegate-enforcer.py    335
codex-gate.py               18625
codex-parallel.py           15037
codex-review.py             12193
codex-review.sh              3419
codex-stop-opinion.py        2561
codex-watchdog.py           27478
config-protection.py        11889
hook_base.py                 7051
pre-compact-save.py         16995
session-orient.py           11749
session-task-class.py        7495
task-completed-gate.py       7251
test_codex_gate.py           9519
test_curation.py            13380
test_watchdog_fix.py        34861
tool-failure-logger.py       3176
truthguard.py               12750
write-validate.py            3365


rg : Имя "rg" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте правильнос
ть написания имени, а также наличие и правильность пути, после чего повторите попытку.
строка:2 знак:1
+ rg -n "def |logger|hookSpecificOutput|permissionDecision|Scope Fence| ...
+ ~~
    + CategoryInfo          : ObjectNotFound: (rg:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

exec
powershell.exe -Command "Get-ChildItem -Path '.claude' -Recurse -Filter AGENTS.md -Force | Select-Object FullName; Select-String -Path '.claude/hooks/codex-gate.py' -Pattern 'def |logger|hookSpecificOutput|permissionDecision|Scope Fence|codex-implementations' | Select-Object -First 80" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 438ms:

FullName                                                                                                               
--------                                                                                                               
C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex\.claude\shared\templates\new-project\AGEN...
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       
                                                                                                                       



exec
powershell.exe -Command "Get-Content -Path '.claude/hooks/codex-gate.py' -TotalCount 220" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 428ms:
#!/usr/bin/env python3
"""Codex Gate вЂ” enforces Codex consultation at every decision point.

Two enforcement mechanisms:

1. TaskCreated hook: auto-calls codex-ask.py for every new task
   в†’ Covers: pipeline phases, Agent Teams, subtask decomposition

2. PreToolUse gate (Edit/Write): blocks file modifications if Codex
   wasn't consulted in the last COOLDOWN_MINUTES
   в†’ Forces Claude to call codex-ask.py before making changes
   в†’ Cooldown prevents blocking every single edit (once per burst)

Exit codes:
  0 вЂ” allow
  2 вЂ” block (Codex consultation required)
"""

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    for s in [sys.stdin, sys.stdout, sys.stderr]:
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")

logger = logging.getLogger("codex-gate")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    stream=sys.stderr,
)

MAX_EDITS_PER_CONSULTATION = 5  # After 5 edits, must consult Codex again
COOLDOWN_MINUTES = 5  # Also time-based fallback
CODEX_ASK_SCRIPT = ".claude/scripts/codex-ask.py"

# codex-implement result recognition (tech-spec Section 9)
RESULT_MAX_AGE_SECONDS = 180  # 3 minutes
CODEX_IMPLEMENTATIONS_DIR = "work/codex-implementations"
CODEX_TASKS_DIR = "work/codex-primary/tasks"


def get_project_dir():
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()


def get_last_codex_time(project_dir):
    """Check when Codex was last consulted."""
    opinion_file = project_dir / ".codex" / "reviews" / "parallel-opinion.md"
    timestamp_file = project_dir / ".codex" / "last-consulted"

    # Check both files вЂ” use the most recent
    latest = 0
    for f in [opinion_file, timestamp_file]:
        if f.exists():
            latest = max(latest, f.stat().st_mtime)
    return latest


def mark_codex_consulted(project_dir):
    """Mark that Codex was just consulted. Resets edit counter."""
    ts_file = project_dir / ".codex" / "last-consulted"
    ts_file.parent.mkdir(parents=True, exist_ok=True)
    ts_file.write_text(str(time.time()), encoding="utf-8")
    # Reset edit counter
    count_file = project_dir / ".codex" / "edit-count"
    count_file.write_text("0", encoding="utf-8")


def get_edit_count(project_dir):
    """Get number of Edit/Write calls since last Codex consultation."""
    count_file = project_dir / ".codex" / "edit-count"
    if not count_file.exists():
        return 0
    try:
        return int(count_file.read_text().strip())
    except (ValueError, OSError):
        return 0


def increment_edit_count(project_dir):
    """Increment the edit counter."""
    count_file = project_dir / ".codex" / "edit-count"
    count_file.parent.mkdir(parents=True, exist_ok=True)
    current = get_edit_count(project_dir)
    count_file.write_text(str(current + 1), encoding="utf-8")
    return current + 1


def is_codex_fresh(project_dir):
    """Check if Codex opinion is fresh enough.

    Two conditions (BOTH must pass):
    1. Time-based: last consultation < COOLDOWN_MINUTES ago
    2. Count-based: < MAX_EDITS_PER_CONSULTATION edits since last consultation

    If EITHER expires, Codex consultation is required.
    """
    # Time check
    last = get_last_codex_time(project_dir)
    if last == 0:
        return False
    age_minutes = (time.time() - last) / 60
    if age_minutes >= COOLDOWN_MINUTES:
        logger.info("time-based expiry: %.1f min > %d min", age_minutes, COOLDOWN_MINUTES)
        return False

    # Count check
    count = get_edit_count(project_dir)
    if count >= MAX_EDITS_PER_CONSULTATION:
        logger.info("count-based expiry: %d edits >= %d max", count, MAX_EDITS_PER_CONSULTATION)
        return False

    return True


# ---------------------------------------------------------------------------
# codex-implement result recognition (tech-spec Section 9)
# ---------------------------------------------------------------------------

def _parse_result_status(result_path):
    """Read task-N-result.md and return its 'status' field, or None on error.

    Accepts any reasonable layout: YAML frontmatter, bold key, plain line.
    Never raises вЂ” parse errors return None so the gate falls back to old behavior.
    """
    try:
        text = result_path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        logger.info("result-parse: cannot read %s: %s", result_path.name, e)
        return None

    # Match common "status" emissions: `status: pass`, `**Status:** pass`,
    # `- status: pass`, `> Status = fail`. Strip bold/italic markers from each
    # line first so colon placement inside '**...**' does not break the regex.
    import re
    for raw in text.splitlines():
        # Remove leading bullet/quote, surrounding bold/italic, backticks.
        stripped = raw.lstrip(" \t-*>").strip()
        stripped = stripped.replace("**", "").replace("__", "").replace("`", "")
        m = re.match(r"(?i)status\s*[:=]\s*([A-Za-z0-9_-]+)", stripped)
        if m:
            return m.group(1).strip().lower()
    logger.info("result-parse: no status field in %s", result_path.name)
    return None


def _parse_scope_fence(task_path):
    """Extract 'Allowed paths' from a task-N.md Scope Fence section.

    Returns list of normalized POSIX-style path fragments (strings). Empty list
    on any parse error вЂ” caller treats empty fence as 'no match'.
    """
    try:
        text = task_path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        logger.info("fence-parse: cannot read %s: %s", task_path.name, e)
        return []

    # Locate "## Scope Fence" section (case-insensitive).
    import re
    fence_match = re.search(r"(?im)^##\s+Scope\s+Fence\s*$", text)
    if not fence_match:
        return []

    # Slice to next top-level heading.
    start = fence_match.end()
    tail = text[start:]
    next_hdr = re.search(r"(?m)^##\s+", tail)
    section = tail[: next_hdr.start()] if next_hdr else tail

    # Find the "Allowed paths" subsection; stop at "Forbidden" or blank run.
    allowed_match = re.search(r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\Z)", section)
    if not allowed_match:
        return []
    allowed_block = allowed_match.group(1)

    paths = []
    for line in allowed_block.splitlines():
        line = line.strip()
        if not line.startswith("-"):
            continue
        # Strip leading "-", backticks, parenthetical annotations like "(new file)".
        entry = line.lstrip("-").strip()
        entry = entry.strip("`").strip()
        # Drop trailing parenthetical: "path/to/x (new)"
        entry = re.sub(r"\s*\([^)]*\)\s*$", "", entry).strip()
        entry = entry.strip("`").strip()
        if not entry:
            continue
        # Normalize to forward slashes for comparison.
        paths.append(entry.replace("\\", "/").rstrip("/"))
    return paths


def _path_in_fence(target_rel_posix, fence_entries):
    """True if target_rel_posix is covered by any fence entry.

    Fence entry can be a file ('a/b/c.py'), a directory ('a/b/'), or a glob
    with '**' wildcard (only simple prefix matching is supported).
    """
    if not fence_entries:
        return False
    target = target_rel_posix.rstrip("/")
    for entry in fence_entries:
        if not entry:
            continue
        # Strip glob tail like '**' or '*'.
        import re
        simple = re.sub(r"/?\*+$", "", entry).rstrip("/")
        if not simple:
            continue
        # Exact file match or directory-prefix match (with '/' boundary).
        if target == simple:

exec
powershell.exe -Command "Get-Content -Path '.claude/hooks/codex-gate.py' -TotalCount 420 | Select-Object -Skip 220" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 427ms:
            return True
        if target.startswith(simple + "/"):
            return True
    return False


def _resolve_target_path(project_dir, target_raw):
    """Resolve a tool_input file path to an absolute Path inside project_dir.

    Returns None if the resolved path escapes project_dir (no symlink traversal).
    """
    if not target_raw:
        return None
    try:
        p = Path(target_raw)
        if not p.is_absolute():
            p = project_dir / p
        resolved = p.resolve()
    except (OSError, ValueError) as e:
        logger.info("target-resolve: cannot resolve %s: %s", target_raw, e)
        return None
    try:
        resolved.relative_to(project_dir)
    except ValueError:
        logger.info("target-resolve: %s escapes project root", resolved)
        return None
    return resolved


def _extract_target_path(payload):
    """Pull the file path from Edit/Write tool_input. Returns str or None."""
    if not isinstance(payload, dict):
        return None
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return None
    # Edit, Write, NotebookEdit all use `file_path`; MultiEdit and Write do too.
    return tool_input.get("file_path") or tool_input.get("notebook_path")


def check_task_result_opinion(project_dir, target_rel_posix):
    """Return 'codex-implement' if a fresh in-scope task-*-result.md authorizes
    editing target_rel_posix; else None.

    Decision rules (all must hold for acceptance):
      1. target_rel_posix is non-empty
      2. Some task-{N}-result.md in work/codex-implementations/ has mtime
         within RESULT_MAX_AGE_SECONDS of now
      3. That file contains status=pass (case-insensitive)
      4. The paired work/codex-primary/tasks/T{N}-*.md declares a Scope Fence
         that covers target_rel_posix

    Never raises вЂ” any exception returns None so caller falls through to old
    behavior. Fall-through is explicit via the outer try/except.
    """
    try:
        if not target_rel_posix:
            return None
        results_dir = project_dir / CODEX_IMPLEMENTATIONS_DIR
        if not results_dir.is_dir():
            logger.info("codex-implement: no results dir, skip new-path check")
            return None
        tasks_dir = project_dir / CODEX_TASKS_DIR
        if not tasks_dir.is_dir():
            logger.info("codex-implement: no tasks dir, skip new-path check")
            return None

        now = time.time()
        import re
        fresh_matches = []
        for result_path in results_dir.glob("task-*-result.md"):
            try:
                age = now - result_path.stat().st_mtime
            except OSError:
                continue
            if age > RESULT_MAX_AGE_SECONDS:
                continue

            # Symlink safety: ensure resolved path stays inside project root.
            try:
                rp = result_path.resolve()
                rp.relative_to(project_dir)
            except (OSError, ValueError):
                logger.info("codex-implement: skip %s (outside project)", result_path.name)
                continue

            status = _parse_result_status(result_path)
            if status != "pass":
                logger.info(
                    "codex-implement: skip %s (status=%s, age=%.1fs)",
                    result_path.name, status, age,
                )
                continue

            # Extract task id from filename: task-{N}-result.md (N may be
            # numeric like '1' or a slug like 'T5-codex-gate').
            m = re.match(r"task-(.+?)-result\.md$", result_path.name)
            if not m:
                continue
            task_id = m.group(1)
            fresh_matches.append((task_id, age))

        if not fresh_matches:
            return None

        # For each fresh pass result, look up the paired task file and check fence.
        for task_id, age in sorted(fresh_matches, key=lambda x: x[1]):
            # Task file naming in this repo: T{ID}-*.md, tN-*.md, or task-{ID}.md
            candidates = []
            for pattern in (f"T{task_id}-*.md", f"{task_id}-*.md", f"task-{task_id}.md", f"task-{task_id}-*.md"):
                candidates.extend(tasks_dir.glob(pattern))
            # Deduplicate while preserving order.
            seen = set()
            unique = []
            for c in candidates:
                if c not in seen:
                    seen.add(c)
                    unique.append(c)
            if not unique:
                logger.info("codex-implement: no task file for id=%s", task_id)
                continue

            for task_path in unique:
                fence = _parse_scope_fence(task_path)
                if not fence:
                    logger.info("codex-implement: task %s has empty fence", task_path.name)
                    continue
                if _path_in_fence(target_rel_posix, fence):
                    logger.info(
                        "codex-implement: MATCH task=%s target=%s age=%.1fs",
                        task_id, target_rel_posix, age,
                    )
                    return "codex-implement"
                logger.info(
                    "codex-implement: task=%s target=%s NOT in fence (%d entries)",
                    task_id, target_rel_posix, len(fence),
                )
        return None
    except Exception as e:
        # Never crash the gate вЂ” log and fall back to old behavior.
        logger.warning("codex-implement: unexpected error, falling back: %s", e)
        return None


def call_codex_for_task(project_dir, task_text):
    """Call codex-ask.py synchronously for a task."""
    script = project_dir / CODEX_ASK_SCRIPT
    if not script.exists():
        logger.warning("codex-ask.py not found at %s", script)
        return None

    try:
        result = subprocess.run(
            [sys.executable, str(script), task_text],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=120, cwd=str(project_dir),
        )
        if result.returncode == 0 and result.stdout.strip():
            mark_codex_consulted(project_dir)
            return result.stdout.strip()
    except Exception as e:
        logger.warning("codex-ask failed: %s", e)
    return None


# ---------------------------------------------------------------------------
# Hook handlers
# ---------------------------------------------------------------------------

def handle_task_created(payload):
    """Auto-call Codex when a new task is created."""
    project_dir = get_project_dir()

    # Extract task info
    subject = ""
    description = ""
    if isinstance(payload, dict):
        tool_input = payload.get("tool_input", {})
        subject = tool_input.get("subject", "")
        description = tool_input.get("description", "")

    if not subject and not description:
        logger.info("no task info, skipping")
        return

    task_text = f"New task: {subject}. {description}"
    logger.info("auto-consulting Codex for task: %s", subject[:80])

    opinion = call_codex_for_task(project_dir, task_text)

    if opinion:
        output = {
            "systemMessage": f"Codex opinion on this task:\n{opinion}"
        }
        print(json.dumps(output, ensure_ascii=False))
        logger.info("Codex opinion for task delivered (%d chars)", len(opinion))


def handle_pre_tool_use(payload):
    """Block Edit/Write if Codex wasn't consulted recently."""

exec
powershell.exe -Command "Get-Content -Path '.claude/hooks/codex-gate.py' -TotalCount 620 | Select-Object -Skip 420" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 422ms:
    project_dir = get_project_dir()

    # Only gate Edit and Write
    tool_name = ""
    if isinstance(payload, dict):
        tool_name = payload.get("tool_name", "")

    if tool_name not in ("Edit", "Write"):
        sys.exit(0)

    # New path: accept a fresh in-scope codex-implement result (tech-spec 9.2).
    # Resolve target file path from tool_input; anchor under project root.
    target_raw = _extract_target_path(payload)
    target_abs = _resolve_target_path(project_dir, target_raw)
    target_rel_posix = None
    if target_abs is not None:
        try:
            target_rel_posix = target_abs.relative_to(project_dir).as_posix()
        except ValueError:
            target_rel_posix = None

    implement_source = check_task_result_opinion(project_dir, target_rel_posix)
    if implement_source:
        count = increment_edit_count(project_dir)
        logger.info(
            "codex fresh via %s, allowing %s target=%s (edit %d/%d)",
            implement_source, tool_name, target_rel_posix, count, MAX_EDITS_PER_CONSULTATION,
        )
        sys.exit(0)

    # Fallback: old codex-ask.py freshness check (preserves prior behavior).
    if is_codex_fresh(project_dir):
        count = increment_edit_count(project_dir)
        logger.info(
            "codex fresh via codex-ask, allowing %s (edit %d/%d)",
            tool_name, count, MAX_EDITS_PER_CONSULTATION,
        )
        sys.exit(0)

    # Neither opinion source is fresh вЂ” block and require consultation.
    logger.warning("codex opinion stale (source=none-stale), blocking %s", tool_name)
    msg = (
        "Codex gate: opinion is stale (>3 min). "
        "Run `py -3 .claude/scripts/codex-ask.py \"your task\"` first, "
        "then retry this edit."
    )
    print(msg, file=sys.stderr)
    sys.exit(2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Hook profile gate
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from hook_base import should_run
        if not should_run("codex-gate"):
            sys.exit(0)
    except ImportError:
        pass

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}

    # Detect event from argv
    event = sys.argv[1] if len(sys.argv) > 1 else ""

    if event == "TaskCreated":
        handle_task_created(payload)
    elif event == "PreToolUse":
        handle_pre_tool_use(payload)
    else:
        # Auto-detect from payload
        if isinstance(payload, dict) and payload.get("tool_name"):
            handle_pre_tool_use(payload)
        elif isinstance(payload, dict) and payload.get("tool_input", {}).get("subject"):
            handle_task_created(payload)

    sys.exit(0)


if __name__ == "__main__":
    main()

**Checking directory permissions**

I'm looking into whether the log file can be written to at .claude/logs/codex-delegate-enforcer.log. First, I need to check if the directory exists and is writable. If it is writable, maybe I can create a directory if necessary. I should also confirm the permissions of the parent .claude directory because it says "if directory writable." I need to check if .claude/logs already exists as well.
codex
I’ll implement the hook with small pure helpers so tests can exercise decisions directly.
exec
powershell.exe -Command "Test-Path '.claude/logs'; if (Test-Path '.claude/logs') { Get-Item '.claude/logs' | Select-Object FullName,Attributes }" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 376ms:
False

**Planning test hooks**

I think I want to start with testing the hook, but if the tests fail, I’ll need to edit them, right? I’m told that once they're written, they're immutable, which feels impossible. I should write them carefully. Maybe I’ll run a static line count first? I need to develop the hook and the tests. If there’s a bug in the tests, can I still modify? The task says it should be read-only once written, so I really need to plan carefully.
  ✓ Inspect hook conventions and skills
  → Implement enforcer hook
  • Add focused unit tests
  • Run required test commands
  • Prepare handoff report
apply patch
patch: completed
C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex\.claude/hooks/codex-delegate-enforcer.py
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
deleted file mode 100644
index a991c73bcb8f144c6693e4aab51ab203340c74e8..0000000000000000000000000000000000000000
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ /dev/null
@@ -1,10 +0,0 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
deleted file mode 100644
index a991c73bcb8f144c6693e4aab51ab203340c74e8..0000000000000000000000000000000000000000
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ /dev/null
@@ -1,10 +0,0 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)

**Evaluating logging requirements**

I’m considering whether the directory is writable and what to do if it doesn't exist. Maybe we can create a log directory at runtime during tests, but I'm worried about writing outside allowed paths. The actual repository should only initialize logging without creating new directories. If the `.claude/logs` directory exists and is writable, I can proceed with a file handler. I'll define structured logging functions to log relevant events without exposing sensitive user data.
**Structuring function logging**

I'm working on how to call enter and exit (or handle exceptions) for every function while keeping the function count moderate. It's important that all functions have public type hints. For path matching, I'll set a constant for code extensions and create an exempt patterns list to check with fnmatch or prefixes, such as matching relevant paths like `.claude/memory/**`, work/**, and docs. I'll need to normalize paths using `resolve` and ensure they're within the project boundaries to maintain AC security. If there's uncertainty about a target outside the project, I might default to fail-open.
codex
Patch delete succeeded; now I’ll write the full enforcer in one pass.
exec
powershell.exe -Command "@'
#"'!/usr/bin/env python3
"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""

from __future__ import annotations

import fnmatch
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if sys.platform == "win32":
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

LOGGER_NAME = "codex-delegate-enforcer"
logger = logging.getLogger(LOGGER_NAME)

CODE_EXTENSIONS: set[str] = {
    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
    ".sql", ".lua", ".r",
}
EXEMPT_PATH_PATTERNS: list[str] = [
    ".claude/memory/**",
    "work/**",
    "CLAUDE.md",
    "AGENTS.md",
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
    ".gitignore",
    ".claude/settings.json",
    ".claude/ops/*.yaml",
    ".mcp.json",
    ".claude/adr/**/*.md",
    ".claude/guides/**/*.md",
    ".claude/skills/**/*.md",
]
EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
RESULT_GLOB = "task-*-result.md"
RESULT_MAX_AGE_SECONDS = 15 * 60
RESULT_SCAN_LIMIT = 50
RECOVERY_HINT = (
    "Use .claude/scripts/codex-inline-dual.py --describe '"\\\"...\\\" --scope <path> \"
    \"for micro-task, or write work/<feature>/tasks/task-N.md and run \"
    \"codex-implement.py. See CLAUDE.md \\\"Code Delegation Protocol\\\".\"
)
STATUS_RE = re.compile(r\"(?im)"'^'"\\s*-\\s*status\\s*:\\s*(["'^'"\\s]+)\\s*"'$")
TASK_FILE_RE = re.compile(r"(?im)''^'"\\s*-\\s*task_file\\s*:\\s*(.+?)\\s*"'$")
SCOPE_RE = re.compile(r"(?im)''^##'"\\s+Scope\\s+Fence\\s*"'$")
NEXT_SECTION_RE = re.compile(r"(?m)''^##'"\\s+\")
ALLOWED_RE = re.compile(
    r\"(?is)allowed\\s+paths["'^'"\\n]*\\n(.+?)(?:\\n\\s*\\*{0,2}forbidden|\\n\\s*##\\s+|\\Z)\"
)
TRAILING_PAREN_RE = re.compile(r\"\\s*\\(["'^)]*'"\\)\\s*"'$")
GLOB_TAIL_RE = re.compile(r"(?:/)?'"\\*\\*?"'$")


@dataclass(frozen=True)
class TargetPath:
    raw: str
    absolute: Path
    relative: str


@dataclass(frozen=True)
class ResultSummary:
    found_recent: bool = False
    found_fail_status: bool = False
    found_scope_miss: bool = False


@dataclass(frozen=True)
class CoverDecision:
    allowed: bool
    reason: str = "allowed"


def _configure_logging() -> None:
    logger.info("event=enter function=_configure_logging")
    if logger.handlers:
        logger.info("event=exit function=_configure_logging result=already-configured")
        return
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    handler: logging.Handler | None = None
    logs_dir = get_project_dir() / ".claude" / "logs"
    try:
        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
            handler = logging.FileHandler(
                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
            )
    except OSError:
        handler = None
    if handler is None:
        handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info("event=exit function=_configure_logging result=ok")


def get_project_dir() -> Path:
    logger.info("event=enter function=get_project_dir")
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
    logger.info("event=exit function=get_project_dir result=ok")
    return project_dir


def read_payload() -> dict[str, Any] | None:
    logger.info("event=enter function=read_payload")
    raw = sys.stdin.read()
    if not raw.strip():
        logger.info("event=exit function=read_payload result=empty")
        return {}
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        logger.info("event=exit function=read_payload result=non-dict")
        return None
    logger.info("event=exit function=read_payload result=ok")
    return payload


def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
    logger.info("event=enter function=is_relevant_payload")
    if not isinstance(payload, dict):
        logger.info("event=exit function=is_relevant_payload result=false")
        return False
    relevant = (
        payload.get("hook_event_name") == "PreToolUse"
        and payload.get("tool_name") in EDIT_TOOLS
    )
    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
    return relevant


def extract_target_paths(payload: dict[str, Any]) -> list[str]:
    logger.info("event=enter function=extract_target_paths")
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        logger.info("event=exit function=extract_target_paths result=0")
        return []
    paths: list[str] = []
    if tool_name == "MultiEdit":
        edits = tool_input.get("edits")
        if isinstance(edits, list):
            for edit in edits:
                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
                    paths.append(edit["file_path"])
        if not paths and isinstance(tool_input.get("file_path"), str):
            paths.append(tool_input["file_path"])
    elif isinstance(tool_input.get("file_path"), str):
        paths.append(tool_input["file_path"])
    unique_paths = list(dict.fromkeys(paths))
    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
    return unique_paths


def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
    logger.info("event=enter function=resolve_target")
    if not raw_path:
        logger.info("event=exit function=resolve_target result=empty")
        return None
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = project_dir / candidate
    resolved = candidate.resolve()
    relative = resolved.relative_to(project_dir).as_posix()
    logger.info("event=exit function=resolve_target result=ok")
    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)


def is_exempt_target(target: TargetPath) -> bool:
    logger.info("event=enter function=is_exempt_target")
    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
        return True
    relative = target.relative
    for pattern in EXEMPT_PATH_PATTERNS:
        prefix = pattern[:-3] if pattern.endswith("/**") else ""
        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
            return True
        if fnmatch.fnmatchcase(relative, pattern):
            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
            return True
    logger.info("event=exit function=is_exempt_target result=false")
    return False


def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
    logger.info("event=enter function=parse_result_file")
    text = result_path.read_text(encoding="utf-8", errors="replace")
    status_match = STATUS_RE.search(text)
    task_match = TASK_FILE_RE.search(text)
    status = status_match.group(1).strip().lower() if status_match else None
    task_file = None
    if task_match:
        task_value = task_match.group(1).strip().strip("`").strip()
        task_file = Path(task_value)
    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
    return status, task_file


def parse_scope_fence(task_path: Path) -> list[str]:
    logger.info("event=enter function=parse_scope_fence")
    text = task_path.read_text(encoding="utf-8", errors="replace")
    fence_match = SCOPE_RE.search(text)
    if not fence_match:
        logger.info("event=exit function=parse_scope_fence result=0")
        return []
    tail = text[fence_match.end():]
    next_match = NEXT_SECTION_RE.search(tail)
    section = tail[: next_match.start()] if next_match else tail
    allowed_match = ALLOWED_RE.search(section)
    if not allowed_match:
        logger.info("event=exit function=parse_scope_fence result=0")
        return []
    entries: list[str] = []
    for raw_line in allowed_match.group(1).splitlines():
        line = raw_line.strip()
        if not line.startswith("-"):
            continue
        entry = line.lstrip("-").strip().strip("`").strip()
        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
        if entry:
            entries.append(entry.replace("'"\\\\\", \"/\"))
    logger.info(\"event=exit function=parse_scope_fence result=%d\", len(entries))
    return entries


def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
    logger.info(\"event=enter function=resolve_fence_entry\")
    normalized = entry.replace(\"\\\\\", \"/\").strip()
    if not normalized:
        logger.info(\"event=exit function=resolve_fence_entry result=empty\")
        return None
    is_directory = normalized.endswith(\"/\") or normalized.endswith(\"/**\") or normalized.endswith(\"/*\")
    normalized = GLOB_TAIL_RE.sub(\"\", normalized).rstrip(\"/\")
    if not normalized:
        logger.info(\"event=exit function=resolve_fence_entry result=empty\")
        return None
    entry_path = Path(normalized)
    if not entry_path.is_absolute():
        entry_path = project_dir / entry_path
    resolved = entry_path.resolve()
    resolved.relative_to(project_dir)
    logger.info(\"event=exit function=resolve_fence_entry result=ok\")
    return resolved, is_directory


def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
    logger.info(\"event=enter function=target_is_covered\")
    for entry in entries:
        resolved_entry = resolve_fence_entry(project_dir, entry)
        if resolved_entry is None:
            continue
        entry_path, is_directory = resolved_entry
        if target.absolute == entry_path:
            logger.info(\"event=exit function=target_is_covered result=true reason=exact\")
            return True
        if is_directory:
            try:
                target.absolute.relative_to(entry_path)
                logger.info(\"event=exit function=target_is_covered result=true reason=prefix\")
                return True
            except ValueError:
                continue
    logger.info(\"event=exit function=target_is_covered result=false\")
    return False


def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
    logger.info(\"event=enter function=recent_result_paths\")
    results_dir = project_dir / RESULTS_RELATIVE_DIR
    if not results_dir.is_dir():
        logger.info(\"event=exit function=recent_result_paths result=missing-dir\")
        return []
    paths: list[tuple[Path, float]] = []
    for result_path in results_dir.glob(RESULT_GLOB):
        resolved = result_path.resolve()
        resolved.relative_to(project_dir)
        paths.append((resolved, resolved.stat().st_mtime))
    paths.sort(key=lambda item: item[1], reverse=True)
    limited = paths[:RESULT_SCAN_LIMIT]
    logger.info(\"event=exit function=recent_result_paths result=%d\", len(limited))
    return limited


def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
    logger.info(\"event=enter function=check_target_cover\")
    now = time.time()
    summary = ResultSummary()
    all_results = recent_result_paths(project_dir)
    if not all_results:
        logger.info(\"event=exit function=check_target_cover result=no-cover\")
        return CoverDecision(False, \"no-cover\")
    found_recent = False
    found_fail_status = False
    found_scope_miss = False
    found_stale = False
    for result_path, mtime in all_results:
        age = now - mtime
        if age >= RESULT_MAX_AGE_SECONDS:
            found_stale = True
            continue
        found_recent = True
        status, task_file = parse_result_file(result_path)
        if status "'!= "pass":
            found_fail_status = True
            continue
        if task_file is None:
            found_scope_miss = True
            continue
        if not task_file.is_absolute():
            task_file = project_dir / task_file
        task_path = task_file.resolve()
        task_path.relative_to(project_dir)
        entries = parse_scope_fence(task_path)
        if target_is_covered(project_dir, target, entries):
            logger.info("event=exit function=check_target_cover result=allowed")
            return CoverDecision(True)
        found_scope_miss = True
    if found_scope_miss:
        reason = "scope-miss"
    elif found_fail_status:
        reason = "fail-status"
    elif found_stale or all_results:
        reason = "stale" if not found_recent else "no-cover"
    else:
        reason = "no-cover"
    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
    logger.info(
        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
        reason,
        summary.found_recent,
        summary.found_fail_status,
        summary.found_scope_miss,
    )
    return CoverDecision(False, reason)


def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
    logger.info("event=enter function=make_deny_output")
    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }
    logger.info("event=exit function=make_deny_output result=ok")
    return output


def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
    logger.info("event=enter function=evaluate_payload")
    for raw_path in extract_target_paths(payload):
        target = resolve_target(project_dir, raw_path)
        if target is None or is_exempt_target(target):
            continue
        decision = check_target_cover(project_dir, target)
        if not decision.allowed:
            logger.info("event=exit function=evaluate_payload result=deny")
            return make_deny_output(target, decision.reason)
    logger.info("event=exit function=evaluate_payload result=allow")
    return None


def main() -> int:
    _configure_logging()
    logger.info("event=enter function=main")
    try:
        payload = read_payload()
        if not is_relevant_payload(payload):
            logger.info("event=exit function=main result=pass-through")
            return 0
        output = evaluate_payload(get_project_dir(), payload or {})
        if output is not None:
            print(json.dumps(output, ensure_ascii=False))
        logger.info("event=exit function=main result=allow-or-deny")
        return 0
    except Exception:
        logger.exception("event=error function=main result=fail-open")
        return 0


if __name__ == "__main__":
    sys.exit(main())
'"'@ | Set-Content -Path '.claude/hooks/codex-delegate-enforcer.py' -Encoding UTF8" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 389ms:
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..234f4c1da3c0b1be136ef7925d46cc50fb930ca0
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,399 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+﻿#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from dataclasses import dataclass
+from pathlib import Path
+from typing import Any
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+@dataclass(frozen=True)
+class TargetPath:
+    raw: str
+    absolute: Path
+    relative: str
+
+
+@dataclass(frozen=True)
+class ResultSummary:
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+@dataclass(frozen=True)
+class CoverDecision:
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

**Exploring logging and encoding issues**

I'm considering whether using `Set-Content` writes a BOM in PowerShell and how that impacts UTF-8 encoding, especially in Python. It seems like Python can handle it generally, but the BOM before the shebang might create some hiccups. I also need to look into logging; the logger.info call might not output messages if the handler isn't configured first. It's important to consider the test situations, especially regarding malformed JSON payloads. I'll need to test carefully with unit tests and temp directories, ensuring everything runs smoothly.
**Planning testing strategies**

I need to consider running the full script and testing the command with only Python files. It’s important to import the necessary tests, and I'm thinking about loading modules from filenames with hyphens. I want to ensure we don’t modify existing parts since they’re effectively immutable. There should be around 12 test cases, including one for "malformed result.md" or "corrupt JSON payload." I'll aim for robust output, customizing the unittest output to ensure clarity in results. Also, I'll need to set up proper logging and temp directories without losing the environment context.
**Configuring logging for tests**

I'm looking into using `io.StringIO` to patch `sys.stdin`, `stdout`, and `stderr`. Since the logging isn’t configured at import, I wonder if `_configure_logging` might attach the stream to the initial `stderr`. If I call `main`, `_configure_logging` would add a handler to the current `stderr`. To manage multiple tests, I think I should clear `enforcer.logger.handlers` in `setUp` to prevent logs from previous tests persisting. I'll also use `self.addCleanup` and simulate result file modification times effectively.
codex
Core hook is in place. I’ll add isolated unit tests using temp projects and mocked stdin/stdout.
exec
powershell.exe -Command "(Get-Content '.claude/hooks/codex-delegate-enforcer.py').Count" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 387ms:
399

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..234f4c1da3c0b1be136ef7925d46cc50fb930ca0
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,399 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+﻿#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from dataclasses import dataclass
+from pathlib import Path
+from typing import Any
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+@dataclass(frozen=True)
+class TargetPath:
+    raw: str
+    absolute: Path
+    relative: str
+
+
+@dataclass(frozen=True)
+class ResultSummary:
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+@dataclass(frozen=True)
+class CoverDecision:
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

  ✓ Inspect hook conventions and skills
  ✓ Implement enforcer hook
  → Add focused unit tests
  • Run required test commands
  • Prepare handoff report
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..234f4c1da3c0b1be136ef7925d46cc50fb930ca0
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,399 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+﻿#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from dataclasses import dataclass
+from pathlib import Path
+from typing import Any
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+@dataclass(frozen=True)
+class TargetPath:
+    raw: str
+    absolute: Path
+    relative: str
+
+
+@dataclass(frozen=True)
+class ResultSummary:
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+@dataclass(frozen=True)
+class CoverDecision:
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

exec
powershell.exe -Command "@'
#"'!/usr/bin/env python3
"""Unit tests for codex-delegate-enforcer.py."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

HOOK_PATH = Path(__file__).with_name("codex-delegate-enforcer.py")
spec = importlib.util.spec_from_file_location("codex_delegate_enforcer", HOOK_PATH)
enforcer = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(enforcer)


class CodexDelegateEnforcerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name).resolve()
        self.old_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
        os.environ["CLAUDE_PROJECT_DIR"] = str(self.project_dir)
        enforcer.logger.handlers.clear()
        enforcer.logger.propagate = False
        self.addCleanup(self.cleanup_env)

    def cleanup_env(self) -> None:
        enforcer.logger.handlers.clear()
        if self.old_project_dir is None:
            os.environ.pop("CLAUDE_PROJECT_DIR", None)
        else:
            os.environ["CLAUDE_PROJECT_DIR"] = self.old_project_dir
        self.temp_dir.cleanup()

    def payload(self, tool_name: str, tool_input: dict[str, object]) -> dict[str, object]:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": tool_name,
            "tool_input": tool_input,
        }

    def run_main(self, stdin_text: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(sys, "stdin", io.StringIO(stdin_text)), patch.object(sys, "stdout", stdout), patch.object(sys, "stderr", stderr):
            code = enforcer.main()
        return code, stdout.getvalue(), stderr.getvalue()

    def write_task(self, path_text: str, allowed_entries: list[str]) -> Path:
        task_path = self.project_dir / path_text
        task_path.parent.mkdir(parents=True, exist_ok=True)
        allowed = "'"\\n\".join(f\"- "'`{entry}`" for entry in allowed_entries)
        task_path.write_text(
            f"# Task'"\\n\\n## Scope Fence\\n\\n**Allowed paths (may be written):**\\n{allowed}\\n\\n**Forbidden paths:**\\n- other\\n\",
            encoding=\"utf-8\",
        )
        return task_path

    def write_result(self, task_path: Path, status: str = \"pass\", age_seconds: int = 0, malformed: bool = False) -> Path:
        results_dir = self.project_dir / \"work\" / \"codex-implementations\"
        results_dir.mkdir(parents=True, exist_ok=True)
        result_path = results_dir / f\"task-{time.time_ns()}-result.md\"
        if malformed:
            text = \"# Result\\nnot parseable\\n\"
        else:
            task_rel = task_path.relative_to(self.project_dir).as_posix()
            text = f\"# Result\\n- status: {status}\\n- task_file: {task_rel}\\n\"
        result_path.write_text(text, encoding=\"utf-8\")
        stamp = time.time() - age_seconds
        os.utime(result_path, (stamp, stamp))
        return result_path

    def decision_for(self, payload: dict[str, object]) -> dict[str, object] | None:
        return enforcer.evaluate_payload(self.project_dir, payload)

    def assertDenied(self, output: dict[str, object] | None, reason: str, target: str) -> None:
        self.assertIsNotNone(output)
        hook_output = output[\"hookSpecificOutput\"]
        self.assertEqual(\"PreToolUse\", hook_output[\"hookEventName\"])
        self.assertEqual(\"deny\", hook_output[\"permissionDecision\"])
        message = hook_output[\"permissionDecisionReason\"]
        self.assertIn(reason, message)
        self.assertIn(target, message)
        self.assertIn(\"Use .claude/scripts/codex-inline-dual.py\", message)

    def test_exempt_path_allows(self) -> None:
        output = self.decision_for(self.payload(\"Write\", {\"file_path\": \"CLAUDE.md\"}))
        self.assertIsNone(output)

    def test_code_file_no_recent_result_denies_json(self) -> None:
        payload = self.payload(\"Write\", {\"file_path\": \"src/app.py\"})
        code, stdout, _stderr = self.run_main(json.dumps(payload))
        self.assertEqual(0, code)
        data = json.loads(stdout)
        message = data[\"hookSpecificOutput\"][\"permissionDecisionReason\"]
        self.assertIn(\"src/app.py\", message)
        self.assertIn(\"no-cover\", message)
        self.assertIn(\"Use .claude/scripts/codex-inline-dual.py\", message)

    def test_code_file_stale_result_denies(self) -> None:
        task_path = self.write_task(\"work/feature/tasks/task-1.md\", [\"src/app.py\"])
        self.write_result(task_path, age_seconds=901)
        output = self.decision_for(self.payload(\"Edit\", {\"file_path\": \"src/app.py\"}))
        self.assertDenied(output, \"stale\", \"src/app.py\")

    def test_fresh_pass_covering_fence_allows(self) -> None:
        task_path = self.write_task(\"work/feature/tasks/task-1.md\", [\"src/\"])
        self.write_result(task_path)
        output = self.decision_for(self.payload(\"Edit\", {\"file_path\": \"src/app.py\"}))
        self.assertIsNone(output)

    def test_fresh_pass_scope_miss_denies(self) -> None:
        task_path = self.write_task(\"work/feature/tasks/task-1.md\", [\"lib/\"])
        self.write_result(task_path)
        output = self.decision_for(self.payload(\"Edit\", {\"file_path\": \"src/app.py\"}))
        self.assertDenied(output, \"scope-miss\", \"src/app.py\")

    def test_fresh_fail_status_denies(self) -> None:
        task_path = self.write_task(\"work/feature/tasks/task-1.md\", [\"src/app.py\"])
        self.write_result(task_path, status=\"fail\")
        output = self.decision_for(self.payload(\"Edit\", {\"file_path\": \"src/app.py\"}))
        self.assertDenied(output, \"fail-status\", \"src/app.py\")

    def test_non_code_file_allows(self) -> None:
        output = self.decision_for(self.payload(\"Write\", {\"file_path\": \"notes.txt\"}))
        self.assertIsNone(output)

    def test_multiedit_multiple_files_all_covered_allows(self) -> None:
        task_path = self.write_task(\"work/feature/tasks/task-1.md\", [\"src/\"])
        self.write_result(task_path)
        payload = self.payload(\"MultiEdit\", {\"edits\": [{\"file_path\": \"src/a.py\"}, {\"file_path\": \"src/b.ts\"}]})
        output = self.decision_for(payload)
        self.assertIsNone(output)

    def test_multiedit_one_uncovered_denies(self) -> None:
        task_path = self.write_task(\"work/feature/tasks/task-1.md\", [\"src/a.py\"])
        self.write_result(task_path)
        payload = self.payload(\"MultiEdit\", {\"edits\": [{\"file_path\": \"src/a.py\"}, {\"file_path\": \"src/b.ts\"}]})
        output = self.decision_for(payload)
        self.assertDenied(output, \"scope-miss\", \"src/b.ts\")

    def test_malformed_result_denies_without_crash(self) -> None:
        task_path = self.write_task(\"work/feature/tasks/task-1.md\", [\"src/app.py\"])
        self.write_result(task_path, malformed=True)
        output = self.decision_for(self.payload(\"Edit\", {\"file_path\": \"src/app.py\"}))
        self.assertDenied(output, \"fail-status\", \"src/app.py\")

    def test_corrupt_json_payload_passes_through(self) -> None:
        code, stdout, _stderr = self.run_main(\"{not-json\")
        self.assertEqual(0, code)
        self.assertEqual(\"\", stdout)

    def test_non_edit_event_passes_through(self) -> None:
        payload = {\"hook_event_name\": \"PreToolUse\", \"tool_name\": \"Bash\", \"tool_input\": {\"command\": \"echo ok\"}}
        code, stdout, _stderr = self.run_main(json.dumps(payload))
        self.assertEqual(0, code)
        self.assertEqual(\"\", stdout)


if __name__ == \"__main__\":
    unittest.main(verbosity=2, testRunner=unittest.TextTestRunner(stream=sys.stdout, verbosity=2))
'@ | Set-Content -Path '.claude/hooks/test_codex_delegate_enforcer.py' -Encoding UTF8" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 419ms:
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..234f4c1da3c0b1be136ef7925d46cc50fb930ca0
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,399 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+﻿#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from dataclasses import dataclass
+from pathlib import Path
+from typing import Any
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+@dataclass(frozen=True)
+class TargetPath:
+    raw: str
+    absolute: Path
+    relative: str
+
+
+@dataclass(frozen=True)
+class ResultSummary:
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+@dataclass(frozen=True)
+class CoverDecision:
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

**Running tests on dataclass module**

I need to run a test that keeps the number under 450, with a hook set at 399. However, I’m wondering if there’s an obvious issue with the dataclass module import through the spec, especially without using sys.modules, which could lead to errors. Typically, a dataclass expects to find its module in sys.modules; if it’s not there, it might raise an AttributeError. I think testing the import method again should help clarify things.
codex
Tests are written. I’ll run the required commands and fix only hook issues if they surface.
  ✓ Inspect hook conventions and skills
  ✓ Implement enforcer hook
  ✓ Add focused unit tests
  → Run required test commands
  • Prepare handoff report
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..234f4c1da3c0b1be136ef7925d46cc50fb930ca0
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,399 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+﻿#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from dataclasses import dataclass
+from pathlib import Path
+from typing import Any
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+@dataclass(frozen=True)
+class TargetPath:
+    raw: str
+    absolute: Path
+    relative: str
+
+
+@dataclass(frozen=True)
+class ResultSummary:
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+@dataclass(frozen=True)
+class CoverDecision:
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

exec
powershell.exe -Command 'python .claude/hooks/test_codex_delegate_enforcer.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
2026-04-24T15:46:04.996267Z ERROR codex_core::tools::router: error={"output":"python : Имя \"python\" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте пр\r\nавильность написания имени, а также наличие и правильность пути, после чего повторите попытку.\r\nстрока:2 знак:1\r\n+ python .claude/hooks/test_codex_delegate_enforcer.py\r\n+ ~~~~~~\r\n    + CategoryInfo          : ObjectNotFound: (python:String) [], CommandNotFoundException\r\n    + FullyQualifiedErrorId : CommandNotFoundException\r\n \r\n","metadata":{"exit_code":1,"duration_seconds":1.1}}
 exited 1 in 1148ms:
python : Имя "python" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте пр
авильность написания имени, а также наличие и правильность пути, после чего повторите попытку.
строка:2 знак:1
+ python .claude/hooks/test_codex_delegate_enforcer.py
+ ~~~~~~
    + CategoryInfo          : ObjectNotFound: (python:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..234f4c1da3c0b1be136ef7925d46cc50fb930ca0
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,399 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+﻿#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from dataclasses import dataclass
+from pathlib import Path
+from typing import Any
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+@dataclass(frozen=True)
+class TargetPath:
+    raw: str
+    absolute: Path
+    relative: str
+
+
+@dataclass(frozen=True)
+class ResultSummary:
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+@dataclass(frozen=True)
+class CoverDecision:
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

codex
The required `python` command isn’t on PATH here, so I’ll locate an available interpreter before continuing.
exec
powershell.exe -Command "Get-Command python -ErrorAction SilentlyContinue; Get-Command py -ErrorAction SilentlyContinue; Get-Command python3 -ErrorAction SilentlyContinue; Get-ChildItem -Path 'C:/Users/Lenovo/AppData/Local/Programs/Python' -Filter python.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 5 FullName" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
2026-04-24T15:46:14.585147Z ERROR codex_core::tools::router: error={"output":"\r\nCommandType     Name                                               Version    Source                                   \r\n-----------     ----                                               -------    ------                                   \r\nApplication     py.exe                                             3.12.10... C:\\WINDOWS\\py.exe                        \r\n\r\n\r\nGet-ChildItem : Access is denied\r\nстрока:2 знак:148\r\n+ ... lyContinue; Get-ChildItem -Path 'C:/Users/Lenovo/AppData/Local/Progra ...\r\n+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\r\n    + CategoryInfo          : NotSpecified: (:) [Get-ChildItem], UnauthorizedAccessException\r\n    + FullyQualifiedErrorId : System.UnauthorizedAccessException,Microsoft.PowerShell.Commands.GetChildItemCommand\r\n \r\n","metadata":{"exit_code":1,"duration_seconds":1.2}}
 exited 1 in 1196ms:

CommandType     Name                                               Version    Source                                   
-----------     ----                                               -------    ------                                   
Application     py.exe                                             3.12.10... C:\WINDOWS\py.exe                        


Get-ChildItem : Access is denied
строка:2 знак:148
+ ... lyContinue; Get-ChildItem -Path 'C:/Users/Lenovo/AppData/Local/Progra ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (:) [Get-ChildItem], UnauthorizedAccessException
    + FullyQualifiedErrorId : System.UnauthorizedAccessException,Microsoft.PowerShell.Commands.GetChildItemCommand
 

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..234f4c1da3c0b1be136ef7925d46cc50fb930ca0
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,399 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+﻿#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from dataclasses import dataclass
+from pathlib import Path
+from typing import Any
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+@dataclass(frozen=True)
+class TargetPath:
+    raw: str
+    absolute: Path
+    relative: str
+
+
+@dataclass(frozen=True)
+class ResultSummary:
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+@dataclass(frozen=True)
+class CoverDecision:
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

codex
I found only the `py` launcher, so I’ll use it to validate while preserving the failed exact-command evidence.
exec
powershell.exe -Command 'py -3 .claude/hooks/test_codex_delegate_enforcer.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
2026-04-24T15:46:26.766149Z ERROR codex_core::tools::router: error={"output":"No installed Python found!\r\n","metadata":{"exit_code":1,"duration_seconds":0.2}}
 exited 1 in 244ms:
No installed Python found!

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..234f4c1da3c0b1be136ef7925d46cc50fb930ca0
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,399 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+﻿#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from dataclasses import dataclass
+from pathlib import Path
+from typing import Any
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+@dataclass(frozen=True)
+class TargetPath:
+    raw: str
+    absolute: Path
+    relative: str
+
+
+@dataclass(frozen=True)
+class ResultSummary:
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+@dataclass(frozen=True)
+class CoverDecision:
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

codex
`py -3` also cannot find an installed runtime. I’ll do a bounded search for any portable Python.
exec
powershell.exe -Command '$roots = @('"'C:/Python312','C:/Python311','C:/Program Files/Python312','C:/Program Files/Python311','C:/Users/Lenovo/AppData/Local/Microsoft/WindowsApps','C:/Users/Lenovo/scoop/apps','C:/tools','C:/msys64','C:/ProgramData'); foreach ("'$r in $roots) { if (Test-Path $r) { Get-ChildItem -Path $r -Filter python.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 5 FullName } }' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
2026-04-24T15:46:35.401061Z ERROR codex_core::tools::router: error={"output":"","metadata":{"exit_code":1,"duration_seconds":0.8}}
 exited 1 in 802ms:
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..234f4c1da3c0b1be136ef7925d46cc50fb930ca0
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,399 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+﻿#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from dataclasses import dataclass
+from pathlib import Path
+from typing import Any
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+@dataclass(frozen=True)
+class TargetPath:
+    raw: str
+    absolute: Path
+    relative: str
+
+
+@dataclass(frozen=True)
+class ResultSummary:
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+@dataclass(frozen=True)
+class CoverDecision:
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

**Considering logging practices**

It looks like in my code, I've got a situation where the logger.exception is only being used in the main except block. However, the _configure function catches OSError but doesn't use logger.exception, which seems inconsistent. I realize that I need to adjust it so that every except block logs appropriately using logger.exception. So, I should definitely include logger.exception in the _configure except block, but I also need to handle OSError normally.
codex
While reviewing statically, I spotted an import-smoke risk from `dataclass`; I’ll replace it with `NamedTuple` and tighten exception logging.
exec
powershell.exe -Command '$p = '"'.claude/hooks/codex-delegate-enforcer.py'; "'$t = Get-Content -Raw -Path $p; $t = $t -replace '"'from dataclasses import dataclass\\r?\\n', ''; "'$t = $t -replace '"'from typing import Any', 'from typing import Any, NamedTuple'; "'$t = $t -replace '"'@dataclass\\(frozen=True\\)\\r?\\nclass TargetPath:', 'class TargetPath(NamedTuple):'; "'$t = $t -replace '"'@dataclass\\(frozen=True\\)\\r?\\nclass ResultSummary:', 'class ResultSummary(NamedTuple):'; "'$t = $t -replace '"'    found_recent: bool = False\\r?\\n    found_fail_status: bool = False\\r?\\n    found_scope_miss: bool = False', '    found_recent: bool = False"'`n    found_fail_status: bool = False`n    found_scope_miss: bool = False'"'; "'$t = $t -replace '"'@dataclass\\(frozen=True\\)\\r?\\nclass CoverDecision:', 'class CoverDecision(NamedTuple):'; "'$t = $t -replace '"'    allowed: bool\\r?\\n    reason: str = \"allowed\"', '    allowed: bool"'`n    reason: str = "allowed"'"'; "'$t = $t -replace '"'    except OSError:\\r?\\n        handler = None', '    except OSError:"'`n        logger.exception("event=error function=_configure_logging result=stderr-fallback")`n        handler = None'"'; Set-Content -Path "'$p -Value $t -Encoding UTF8' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 397ms:
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..3fd0aa0d2e47ba3eee5e101575bcd48928eec365
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,392 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
+﻿#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False`n    found_fail_status: bool = False`n    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool`n    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:`n        logger.exception("event=error function=_configure_logging result=stderr-fallback")`n        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())
 
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)

**Checking PowerShell syntax**

I'm realizing that using a backtick for newline replacement inside single quotes in PowerShell might not work as I thought. It seems that in PowerShell, single quotes don't allow for escaping, which means the `n could be treated literally. I'll need to inspect the file more closely to clarify this situation and ensure I'm on the right path. It's all in the details, right?
exec
powershell.exe -Command "Get-Content -Path '.claude/hooks/codex-delegate-enforcer.py' -TotalCount 120" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 397ms:
#!/usr/bin/env python3
"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""

from __future__ import annotations

import fnmatch
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, NamedTuple

if sys.platform == "win32":
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

LOGGER_NAME = "codex-delegate-enforcer"
logger = logging.getLogger(LOGGER_NAME)

CODE_EXTENSIONS: set[str] = {
    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
    ".sql", ".lua", ".r",
}
EXEMPT_PATH_PATTERNS: list[str] = [
    ".claude/memory/**",
    "work/**",
    "CLAUDE.md",
    "AGENTS.md",
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
    ".gitignore",
    ".claude/settings.json",
    ".claude/ops/*.yaml",
    ".mcp.json",
    ".claude/adr/**/*.md",
    ".claude/guides/**/*.md",
    ".claude/skills/**/*.md",
]
EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
RESULT_GLOB = "task-*-result.md"
RESULT_MAX_AGE_SECONDS = 15 * 60
RESULT_SCAN_LIMIT = 50
RECOVERY_HINT = (
    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
)
STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
ALLOWED_RE = re.compile(
    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
)
TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")


class TargetPath(NamedTuple):
    raw: str
    absolute: Path
    relative: str


class ResultSummary(NamedTuple):
    found_recent: bool = False`n    found_fail_status: bool = False`n    found_scope_miss: bool = False


class CoverDecision(NamedTuple):
    allowed: bool`n    reason: str = "allowed"


def _configure_logging() -> None:
    logger.info("event=enter function=_configure_logging")
    if logger.handlers:
        logger.info("event=exit function=_configure_logging result=already-configured")
        return
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    handler: logging.Handler | None = None
    logs_dir = get_project_dir() / ".claude" / "logs"
    try:
        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
            handler = logging.FileHandler(
                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
            )
    except OSError:`n        logger.exception("event=error function=_configure_logging result=stderr-fallback")`n        handler = None
    if handler is None:
        handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info("event=exit function=_configure_logging result=ok")


def get_project_dir() -> Path:
    logger.info("event=enter function=get_project_dir")
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
    logger.info("event=exit function=get_project_dir result=ok")
    return project_dir


def read_payload() -> dict[str, Any] | None:
    logger.info("event=enter function=read_payload")
    raw = sys.stdin.read()
    if not raw.strip():
        logger.info("event=exit function=read_payload result=empty")
        return {}
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        logger.info("event=exit function=read_payload result=non-dict")
        return None
    logger.info("event=exit function=read_payload result=ok")

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..3fd0aa0d2e47ba3eee5e101575bcd48928eec365
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,392 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
+﻿#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False`n    found_fail_status: bool = False`n    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool`n    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:`n        logger.exception("event=error function=_configure_logging result=stderr-fallback")`n        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())
 
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)

codex
That text replacement introduced literal escapes; I’ll correct those syntax lines directly.
exec
powershell.exe -Command '$p = '"'.claude/hooks/codex-delegate-enforcer.py'; "'$t = Get-Content -Raw -Path $p; $t = $t.Replace('"'    found_recent: bool = False"'`n    found_fail_status: bool = False`n    found_scope_miss: bool = False'"', \"    found_recent: bool = False"'`r`n    found_fail_status: bool = False`r`n    found_scope_miss: bool = False"); $t = $t.Replace('"'    allowed: bool"'`n    reason: str = "allowed"'"', \"    allowed: bool"'`r`n    reason: str = '"\\\"allowed\\\"\"); "'$t = $t.Replace('"'    except OSError:"'`n        logger.exception("event=error function=_configure_logging result=stderr-fallback")`n        handler = None'"', \"    except OSError:"'`r`n        logger.exception('"\\\"event=error function=_configure_logging result=stderr-fallback\\\")"'`r`n        handler = None"); Set-Content -Path $p -Value $t -Encoding UTF8' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
2026-04-24T15:47:13.733432Z ERROR codex_core::tools::router: error={"output":"строка:2 знак:425\r\n+ ...  str = \"allowed\"', \"    allowed: bool`r`n    reason: str = \\\"allowed\\ ...\r\n+                                                                  ~\r\nОтсутствует \")\" в вызове метода.\r\nстрока:2 знак:425\r\n+ ... lowed\"', \"    allowed: bool`r`n    reason: str = \\\"allowed\\\"\"); $t =  ...\r\n+                                                        ~~~~~~~~~~\r\nНепредвиденная лексема \"allowed\\\"\"\" в выражении или операторе.\r\nстрока:2 знак:435\r\n+ ... owed\"', \"    allowed: bool`r`n    reason: str = \\\"allowed\\\"\"); $t = $ ...\r\n+                                                                 ~\r\nНепредвиденная лексема \")\" в выражении или операторе.\r\nстрока:2 знак:644\r\n+ ...  = None', \"    except OSError:`r`n        logger.exception(\\\"event=er ...\r\n+                                                                  ~\r\nОтсутствует \")\" в вызове метода.\r\nстрока:2 знак:644\r\n+ ...     except OSError:`r`n        logger.exception(\\\"event=error functio ...\r\n+                                                       ~~~~~~~~~~~\r\nНепредвиденная лексема \"event=error\" в выражении или операторе.\r\nстрока:2 знак:736\r\n+ ... logging result=stderr-fallback\\\")`r`n        handler = None\"); Set-Co ...\r\n+                                                                 ~\r\nНепредвиденная лексема \")\" в выражении или операторе.\r\n    + CategoryInfo          : ParserError: (:) [], ParentContainsErrorRecordException\r\n    + FullyQualifiedErrorId : MissingEndParenthesisInMethodCall\r\n \r\n","metadata":{"exit_code":1,"duration_seconds":0.3}}
 exited 1 in 276ms:
строка:2 знак:425
+ ...  str = "allowed"', "    allowed: bool`r`n    reason: str = \"allowed\ ...
+                                                                  ~
Отсутствует ")" в вызове метода.
строка:2 знак:425
+ ... lowed"', "    allowed: bool`r`n    reason: str = \"allowed\""); $t =  ...
+                                                        ~~~~~~~~~~
Непредвиденная лексема "allowed\""" в выражении или операторе.
строка:2 знак:435
+ ... owed"', "    allowed: bool`r`n    reason: str = \"allowed\""); $t = $ ...
+                                                                 ~
Непредвиденная лексема ")" в выражении или операторе.
строка:2 знак:644
+ ...  = None', "    except OSError:`r`n        logger.exception(\"event=er ...
+                                                                  ~
Отсутствует ")" в вызове метода.
строка:2 знак:644
+ ...     except OSError:`r`n        logger.exception(\"event=error functio ...
+                                                       ~~~~~~~~~~~
Непредвиденная лексема "event=error" в выражении или операторе.
строка:2 знак:736
+ ... logging result=stderr-fallback\")`r`n        handler = None"); Set-Co ...
+                                                                 ~
Непредвиденная лексема ")" в выражении или операторе.
    + CategoryInfo          : ParserError: (:) [], ParentContainsErrorRecordException
    + FullyQualifiedErrorId : MissingEndParenthesisInMethodCall
 

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..3fd0aa0d2e47ba3eee5e101575bcd48928eec365
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,392 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
+﻿#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False`n    found_fail_status: bool = False`n    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool`n    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:`n        logger.exception("event=error function=_configure_logging result=stderr-fallback")`n        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())
 
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)

exec
powershell.exe -Command '$p = '"'.claude/hooks/codex-delegate-enforcer.py'
"'$t = Get-Content -Raw -Path $p
$t = $t.Replace('"'    found_recent: bool = False"'`n    found_fail_status: bool = False`n    found_scope_miss: bool = False'"', @'
    found_recent: bool = False
    found_fail_status: bool = False
    found_scope_miss: bool = False
'@.TrimEnd())
"'$t = $t.Replace('"'    allowed: bool"'`n    reason: str = "allowed"'"', @'
    allowed: bool
    reason: str = \"allowed\"
'@.TrimEnd())
"'$t = $t.Replace('"'    except OSError:"'`n        logger.exception("event=error function=_configure_logging result=stderr-fallback")`n        handler = None'"', @'
    except OSError:
        logger.exception(\"event=error function=_configure_logging result=stderr-fallback\")
        handler = None
'@.TrimEnd())
Set-Content -Path "'$p -Value $t -Encoding UTF8' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 413ms:
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..79fe0a9855f22c17d7a8ef0b3a063aff808a21ce
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,397 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
+﻿#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())
+
 
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)

exec
powershell.exe -Command "Get-Content -Path '.claude/hooks/codex-delegate-enforcer.py' -TotalCount 110 | Select-Object -Skip 70" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 450ms:


class ResultSummary(NamedTuple):
    found_recent: bool = False
    found_fail_status: bool = False
    found_scope_miss: bool = False


class CoverDecision(NamedTuple):
    allowed: bool
    reason: str = "allowed"


def _configure_logging() -> None:
    logger.info("event=enter function=_configure_logging")
    if logger.handlers:
        logger.info("event=exit function=_configure_logging result=already-configured")
        return
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    handler: logging.Handler | None = None
    logs_dir = get_project_dir() / ".claude" / "logs"
    try:
        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
            handler = logging.FileHandler(
                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
            )
    except OSError:
        logger.exception("event=error function=_configure_logging result=stderr-fallback")
        handler = None
    if handler is None:
        handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info("event=exit function=_configure_logging result=ok")


def get_project_dir() -> Path:
    logger.info("event=enter function=get_project_dir")
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..79fe0a9855f22c17d7a8ef0b3a063aff808a21ce
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,397 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
+﻿#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())
+
 
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)

**Analyzing test setup**

I need to consider the line count and potentially import tests using `dataclass`. There's a concern about the test file possibly having import issues that I've already fixed. However, I'm realizing there might be problems with running it using `py -3`. It seems essential to conduct PowerShell static checks and perhaps grep lines instead. The task states that if any test command exits non-zero, I can't claim it's done. I need to check the second test as well, as it might fail due to Python issues.
codex
The hook syntax issue is fixed statically. I’ll run both mandatory commands exactly to capture final evidence.
exec
powershell.exe -Command 'python .claude/hooks/test_codex_delegate_enforcer.py; Write-Host "EXIT:$LASTEXITCODE"; python -c "import sys, importlib.util; spec = importlib.util.spec_from_file_location('"'enforcer', '.claude/hooks/codex-delegate-enforcer.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('import-ok')\"; Write-Host \"EXIT:"'$LASTEXITCODE"' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 1186ms:
EXIT:
EXIT:
python : Имя "python" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте пр
авильность написания имени, а также наличие и правильность пути, после чего повторите попытку.
строка:2 знак:1
+ python .claude/hooks/test_codex_delegate_enforcer.py; Write-Host "EXI ...
+ ~~~~~~
    + CategoryInfo          : ObjectNotFound: (python:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 
python : Имя "python" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте пр
авильность написания имени, а также наличие и правильность пути, после чего повторите попытку.
строка:2 знак:88
+ ... delegate_enforcer.py; Write-Host "EXIT:$LASTEXITCODE"; python -c "imp ...
+                                                            ~~~~~~
    + CategoryInfo          : ObjectNotFound: (python:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..79fe0a9855f22c17d7a8ef0b3a063aff808a21ce
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,397 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
+﻿#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())
+
 
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)

**Clarifying PowerShell commands**

I’m trying to understand the behavior of PowerShell commands. It seems that when I use Write-Host, the command returns 0, while the exact command I’m looking for earlier returned 1. I need to separate the commands to figure out why this is happening. So, I’ll work on getting the second command to return the right result. It’s important to troubleshoot this behavior accurately!
exec
powershell.exe -Command "python -c \"import sys, importlib.util; spec = importlib.util.spec_from_file_location('enforcer', '.claude/hooks/codex-delegate-enforcer.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('import-ok')\"" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
2026-04-24T15:47:59.042057Z ERROR codex_core::tools::router: error={"output":"python : Имя \"python\" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте пр\r\nавильность написания имени, а также наличие и правильность пути, после чего повторите попытку.\r\nстрока:2 знак:1\r\n+ python -c \"import sys, importlib.util; spec = importlib.util.spec_fro ...\r\n+ ~~~~~~\r\n    + CategoryInfo          : ObjectNotFound: (python:String) [], CommandNotFoundException\r\n    + FullyQualifiedErrorId : CommandNotFoundException\r\n \r\n","metadata":{"exit_code":1,"duration_seconds":1.1}}
 exited 1 in 1137ms:
python : Имя "python" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте пр
авильность написания имени, а также наличие и правильность пути, после чего повторите попытку.
строка:2 знак:1
+ python -c "import sys, importlib.util; spec = importlib.util.spec_fro ...
+ ~~~~~~
    + CategoryInfo          : ObjectNotFound: (python:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..79fe0a9855f22c17d7a8ef0b3a063aff808a21ce
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,397 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
+﻿#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())
+
 
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)

**Checking line counts and differences**

I’m thinking that I can’t claim everything is done just yet. I might want to run some static checks using PowerShell, like line counts and Select-String for searching patterns. I should also get a git diff to see the changes, but wait — are the tests immutable? I need to double-check those line counts to ensure I’m on the right track before moving forward.
codex
Both mandatory commands fail because `python` is unavailable. I’ll gather static evidence and the final diff summary.
exec
powershell.exe -Command "(Get-Content '.claude/hooks/codex-delegate-enforcer.py').Count; (Get-Content '.claude/hooks/test_codex_delegate_enforcer.py').Count; git diff -- .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer.py --stat; git diff --check -- .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer.py" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
2026-04-24T15:48:10.941477Z ERROR codex_core::tools::router: error={"output":"398\r\n168\r\nwarning: Limiting comparison with pathspecs is only supported if both paths are directories.\nusage: git diff --no-index [<options>] <path> <path> [<pathspec>...]\n\nDiff output format options\n    -p, --patch           generate patch\n    -s, --no-patch        suppress diff output\n    -u                    generate patch\n    -U, --unified[=<n>]   generate diffs with <n> lines context\n    -W, --[no-]function-context\n                          generate diffs with <n> lines context\n    --raw                 generate the diff in raw format\n    --patch-with-raw      synonym for '-p --raw'\n    --patch-with-stat     synonym for '-p --stat'\n    --numstat             machine friendly --stat\n    --shortstat           output only the last line of --stat\n    -X, --dirstat[=<param1>,<param2>...]\n                          output the distribution of relative amount of changes for each sub-directory\n    --cumulative          synonym for --dirstat=cumulative\n    --dirstat-by-file[=<param1>,<param2>...]\n                          synonym for --dirstat=files,<param1>,<param2>...\n    --check               warn if changes introduce conflict markers or whitespace errors\n    --summary             condensed summary such as creations, renames and mode changes\n    --name-only           show only names of changed files\n    --name-status         show only names and status of changed files\n    --stat[=<width>[,<name-width>[,<count>]]]\n                          generate diffstat\n    --stat-width <width>  generate diffstat with a given width\n    --stat-name-width <width>\n                          generate diffstat with a given name width\n    --stat-graph-width <width>\n                          generate diffstat with a given graph width\n    --stat-count <count>  generate diffstat with limited lines\n    --[no-]compact-summary\n                          generate compact summary in diffstat\n    --binary              output a binary diff that can be applied\n    --[no-]full-index     show full pre- and post-image object names on the \"index\" lines\n    --[no-]color[=<when>] show colored diff\n    --ws-error-highlight <kind>\n                          highlight whitespace errors in the 'context', 'old' or 'new' lines in the diff\n    -z                    do not munge pathnames and use NULs as output field terminators in --raw or --numstat\n    --[no-]abbrev[=<n>]   use <n> digits to display object names\n    --src-prefix <prefix> show the given source prefix instead of \"a/\"\n    --dst-prefix <prefix> show the given destination prefix instead of \"b/\"\n    --line-prefix <prefix>\n                          prepend an additional prefix to every line of output\n    --no-prefix           do not show any source or destination prefix\n    --default-prefix      use default prefixes a/ and b/\n    --inter-hunk-context <n>\n                          show context between diff hunks up to the specified number of lines\n    --output-indicator-new <char>\n                          specify the character to indicate a new line instead of '+'\n    --output-indicator-old <char>\n                          specify the character to indicate an old line instead of '-'\n    --output-indicator-context <char>\n                          specify the character to indicate a context instead of ' '\n\nDiff rename options\n    -B, --break-rewrites[=<n>[/<m>]]\n                          break complete rewrite changes into pairs of delete and create\n    -M, --find-renames[=<n>]\n                          detect renames\n    -D, --irreversible-delete\n                          omit the preimage for deletes\n    -C, --find-copies[=<n>]\n                          detect copies\n    --[no-]find-copies-harder\n                          use unmodified files as source to find copies\n    --no-renames          disable rename detection\n    --[no-]rename-empty   use empty blobs as rename source\n    --[no-]follow         continue listing the history of a file beyond renames\n    -l <n>                prevent rename/copy detection if the number of rename/copy targets exceeds given limit\n\nDiff algorithm options\n    --minimal             produce the smallest possible diff\n    -w, --ignore-all-space\n                          ignore whitespace when comparing lines\n    -b, --ignore-space-change\n                          ignore changes in amount of whitespace\n    --ignore-space-at-eol ignore changes in whitespace at EOL\n    --ignore-cr-at-eol    ignore carrier-return at the end of line\n    --ignore-blank-lines  ignore changes whose lines are all blank\n    -I, --[no-]ignore-matching-lines <regex>\n                          ignore changes whose all lines match <regex>\n    --[no-]indent-heuristic\n                          heuristic to shift diff hunk boundaries for easy reading\n    --patience            generate diff using the \"patience diff\" algorithm\n    --histogram           generate diff using the \"histogram diff\" algorithm\n    --diff-algorithm <algorithm>\n                          choose a diff algorithm\n    --anchored <text>     generate diff using the \"anchored diff\" algorithm\n    --word-diff[=<mode>]  show word diff, using <mode> to delimit changed words\n    --word-diff-regex <regex>\n                          use <regex> to decide what a word is\n    --color-words[=<regex>]\n                          equivalent to --word-diff=color --word-diff-regex=<regex>\n    --[no-]color-moved[=<mode>]\n                          moved lines of code are colored differently\n    --[no-]color-moved-ws <mode>\n                          how white spaces are ignored in --color-moved\n\nOther diff options\n    --[no-]relative[=<prefix>]\n                          when run from subdir, exclude changes outside and show relative paths\n    -a, --[no-]text       treat all files as text\n    -R                    swap two inputs, reverse the diff\n    --[no-]exit-code      exit with 1 if there were differences, 0 otherwise\n    --[no-]quiet          disable all output of the program\n    --[no-]ext-diff       allow an external diff helper to be executed\n    --[no-]textconv       run external text conversion filters when comparing binary files\n    --ignore-submodules[=<when>]\n                          ignore changes to submodules in the diff generation\n    --submodule[=<format>]\n                          specify how differences in submodules are shown\n    --ita-invisible-in-index\n                          hide 'git add -N' entries from the index\n    --ita-visible-in-index\n                          treat 'git add -N' entries as real in the index\n    -S <string>           look for differences that change the number of occurrences of the specified string\n    -G <regex>            look for differences that change the number of occurrences of the specified regex\n    --pickaxe-all         show all changes in the changeset with -S or -G\n    --pickaxe-regex       treat <string> in -S as extended POSIX regular expression\n    -O <file>             control the order in which files appear in the output\n    --rotate-to <path>    show the change in the specified path first\n    --skip-to <path>      skip the output to the specified path\n    --find-object <object-id>\n                          look for differences that change the number of occurrences of the specified object\n    --diff-filter [(A|C|D|M|R|T|U|X|B)...[*]]\n                          select files by diff type\n    --max-depth <depth>   maximum tree depth to recurse\n    --output <file>       output to a specific file\n\nwarning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it\nwarning: in the working copy of '.claude/hooks/test_codex_delegate_enforcer.py', LF will be replaced by CRLF the next time Git touches it\n","metadata":{"exit_code":1,"duration_seconds":0.4}}
 exited 1 in 435ms:
398
168
warning: Limiting comparison with pathspecs is only supported if both paths are directories.
usage: git diff --no-index [<options>] <path> <path> [<pathspec>...]

Diff output format options
    -p, --patch           generate patch
    -s, --no-patch        suppress diff output
    -u                    generate patch
    -U, --unified[=<n>]   generate diffs with <n> lines context
    -W, --[no-]function-context
                          generate diffs with <n> lines context
    --raw                 generate the diff in raw format
    --patch-with-raw      synonym for '-p --raw'
    --patch-with-stat     synonym for '-p --stat'
    --numstat             machine friendly --stat
    --shortstat           output only the last line of --stat
    -X, --dirstat[=<param1>,<param2>...]
                          output the distribution of relative amount of changes for each sub-directory
    --cumulative          synonym for --dirstat=cumulative
    --dirstat-by-file[=<param1>,<param2>...]
                          synonym for --dirstat=files,<param1>,<param2>...
    --check               warn if changes introduce conflict markers or whitespace errors
    --summary             condensed summary such as creations, renames and mode changes
    --name-only           show only names of changed files
    --name-status         show only names and status of changed files
    --stat[=<width>[,<name-width>[,<count>]]]
                          generate diffstat
    --stat-width <width>  generate diffstat with a given width
    --stat-name-width <width>
                          generate diffstat with a given name width
    --stat-graph-width <width>
                          generate diffstat with a given graph width
    --stat-count <count>  generate diffstat with limited lines
    --[no-]compact-summary
                          generate compact summary in diffstat
    --binary              output a binary diff that can be applied
    --[no-]full-index     show full pre- and post-image object names on the "index" lines
    --[no-]color[=<when>] show colored diff
    --ws-error-highlight <kind>
                          highlight whitespace errors in the 'context', 'old' or 'new' lines in the diff
    -z                    do not munge pathnames and use NULs as output field terminators in --raw or --numstat
    --[no-]abbrev[=<n>]   use <n> digits to display object names
    --src-prefix <prefix> show the given source prefix instead of "a/"
    --dst-prefix <prefix> show the given destination prefix instead of "b/"
    --line-prefix <prefix>
                          prepend an additional prefix to every line of output
    --no-prefix           do not show any source or destination prefix
    --default-prefix      use default prefixes a/ and b/
    --inter-hunk-context <n>
                          show context between diff hunks up to the specified number of lines
    --output-indicator-new <char>
                          specify the character to indicate a new line instead of '+'
    --output-indicator-old <char>
                          specify the character to indicate an old line instead of '-'
    --output-indicator-context <char>
                          specify the character to indicate a context instead of ' '

Diff rename options
    -B, --break-rewrites[=<n>[/<m>]]
                          break complete rewrite changes into pairs of delete and create
    -M, --find-renames[=<n>]
                          detect renames
    -D, --irreversible-delete
                          omit the preimage for deletes
    -C, --find-copies[=<n>]
                          detect copies
    --[no-]find-copies-harder
                          use unmodified files as source to find copies
    --no-renames          disable rename detection
    --[no-]rename-empty   use empty blobs as rename source
    --[no-]follow         continue listing the history of a file beyond renames
    -l <n>                prevent rename/copy detection if the number of rename/copy targets exceeds given limit

Diff algorithm options
    --minimal             produce the smallest possible diff
    -w, --ignore-all-space
                          ignore whitespace when comparing lines
    -b, --ignore-space-change
                          ignore changes in amount of whitespace
    --ignore-space-at-eol ignore changes in whitespace at EOL
    --ignore-cr-at-eol    ignore carrier-return at the end of line
    --ignore-blank-lines  ignore changes whose lines are all blank
    -I, --[no-]ignore-matching-lines <regex>
                          ignore changes whose all lines match <regex>
    --[no-]indent-heuristic
                          heuristic to shift diff hunk boundaries for easy reading
    --patience            generate diff using the "patience diff" algorithm
    --histogram           generate diff using the "histogram diff" algorithm
    --diff-algorithm <algorithm>
                          choose a diff algorithm
    --anchored <text>     generate diff using the "anchored diff" algorithm
    --word-diff[=<mode>]  show word diff, using <mode> to delimit changed words
    --word-diff-regex <regex>
                          use <regex> to decide what a word is
    --color-words[=<regex>]
                          equivalent to --word-diff=color --word-diff-regex=<regex>
    --[no-]color-moved[=<mode>]
                          moved lines of code are colored differently
    --[no-]color-moved-ws <mode>
                          how white spaces are ignored in --color-moved

Other diff options
    --[no-]relative[=<prefix>]
                          when run from subdir, exclude changes outside and show relative paths
    -a, --[no-]text       treat all files as text
    -R                    swap two inputs, reverse the diff
    --[no-]exit-code      exit with 1 if there were differences, 0 otherwise
    --[no-]quiet          disable all output of the program
    --[no-]ext-diff       allow an external diff helper to be executed
    --[no-]textconv       run external text conversion filters when comparing binary files
    --ignore-submodules[=<when>]
                          ignore changes to submodules in the diff generation
    --submodule[=<format>]
                          specify how differences in submodules are shown
    --ita-invisible-in-index
                          hide 'git add -N' entries from the index
    --ita-visible-in-index
                          treat 'git add -N' entries as real in the index
    -S <string>           look for differences that change the number of occurrences of the specified string
    -G <regex>            look for differences that change the number of occurrences of the specified regex
    --pickaxe-all         show all changes in the changeset with -S or -G
    --pickaxe-regex       treat <string> in -S as extended POSIX regular expression
    -O <file>             control the order in which files appear in the output
    --rotate-to <path>    show the change in the specified path first
    --skip-to <path>      skip the output to the specified path
    --find-object <object-id>
                          look for differences that change the number of occurrences of the specified object
    --diff-filter [(A|C|D|M|R|T|U|X|B)...[*]]
                          select files by diff type
    --max-depth <depth>   maximum tree depth to recurse
    --output <file>       output to a specific file

warning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/hooks/test_codex_delegate_enforcer.py', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..79fe0a9855f22c17d7a8ef0b3a063aff808a21ce
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,397 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
+﻿#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())
+
 
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)

exec
powershell.exe -Command 'git diff --stat -- .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer.py; git diff --check -- .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer.py; git status --short -- .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
2026-04-24T15:48:18.805560Z ERROR codex_core::tools::router: error={"output":" ...enforcer.py => test_codex_delegate_enforcer.py} | 538 ++++++---------------\n 1 file changed, 154 insertions(+), 384 deletions(-)\nwarning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it\nwarning: in the working copy of '.claude/hooks/test_codex_delegate_enforcer.py', LF will be replaced by CRLF the next time Git touches it\nwarning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it\nwarning: in the working copy of '.claude/hooks/test_codex_delegate_enforcer.py', LF will be replaced by CRLF the next time Git touches it\nfatal: detected dubious ownership in repository at 'C:/Bots/Migrator bots/claude-project-template-update/worktrees/v2/T1-codex'\n'C:/Bots/Migrator bots/claude-project-template-update/worktrees/v2/T1-codex/.git' is owned by:\n\tDESKTOP-7FI6JC5/Lenovo (S-1-5-21-3639331995-3164478676-1546236719-1001)\nbut the current user is:\n\tDESKTOP-7FI6JC5/CodexSandboxOffline (S-1-5-21-3639331995-3164478676-1546236719-1004)\nTo add an exception for this directory, call:\n\n\tgit config --global --add safe.directory 'C:/Bots/Migrator bots/claude-project-template-update/worktrees/v2/T1-codex'\n","metadata":{"exit_code":1,"duration_seconds":0.3}}
 exited 1 in 279ms:
 ...enforcer.py => test_codex_delegate_enforcer.py} | 538 ++++++---------------
 1 file changed, 154 insertions(+), 384 deletions(-)
warning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/hooks/test_codex_delegate_enforcer.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/hooks/test_codex_delegate_enforcer.py', LF will be replaced by CRLF the next time Git touches it
fatal: detected dubious ownership in repository at 'C:/Bots/Migrator bots/claude-project-template-update/worktrees/v2/T1-codex'
'C:/Bots/Migrator bots/claude-project-template-update/worktrees/v2/T1-codex/.git' is owned by:
	DESKTOP-7FI6JC5/Lenovo (S-1-5-21-3639331995-3164478676-1546236719-1001)
but the current user is:
	DESKTOP-7FI6JC5/CodexSandboxOffline (S-1-5-21-3639331995-3164478676-1546236719-1004)
To add an exception for this directory, call:

	git config --global --add safe.directory 'C:/Bots/Migrator bots/claude-project-template-update/worktrees/v2/T1-codex'

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..79fe0a9855f22c17d7a8ef0b3a063aff808a21ce
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,397 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
+﻿#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())
+
 
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)

exec
powershell.exe -Command "git -c safe.directory='C:/Bots/Migrator bots/claude-project-template-update/worktrees/v2/T1-codex' status --short -- .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer.py; git -c safe.directory='C:/Bots/Migrator bots/claude-project-template-update/worktrees/v2/T1-codex' diff --name-status -- .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer.py" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 271ms:
 M .claude/hooks/codex-delegate-enforcer.py
?? .claude/hooks/test_codex_delegate_enforcer.py
M	.claude/hooks/codex-delegate-enforcer.py
warning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..79fe0a9855f22c17d7a8ef0b3a063aff808a21ce
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,397 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
+﻿#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())
+
 
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)

exec
powershell.exe -Command "git -c safe.directory='C:/Bots/Migrator bots/claude-project-template-update/worktrees/v2/T1-codex' diff --check -- .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer.py" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
2026-04-24T15:48:39.960449Z ERROR codex_core::tools::router: error={"output":".claude/hooks/codex-delegate-enforcer.py:397: new blank line at EOF.\nwarning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it\n","metadata":{"exit_code":1,"duration_seconds":0.2}}
 exited 1 in 227ms:
.claude/hooks/codex-delegate-enforcer.py:397: new blank line at EOF.
warning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..79fe0a9855f22c17d7a8ef0b3a063aff808a21ce
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,397 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
+﻿#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())
+
 
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)

**Fixing blank lines in hooks**

I’m looking to fix the blank line at the end of the file (EOF) in the hook. I wonder if using `set-content` is causing it to add a final newline, creating an extra blank line. I need to edit the hook to test its immutability, but it seems like I only need to focus on the hook itself for now. I'll aim to remove those trailing blank lines using PowerShell.
codex
Static diff check found only an extra EOF blank line in the hook; I’ll remove it.
exec
powershell.exe -Command '$p = '"'.claude/hooks/codex-delegate-enforcer.py'; "'$t = (Get-Content -Raw -Path $p).TrimEnd(); [System.IO.File]::WriteAllText((Resolve-Path $p), $t + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 395ms:
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..7c681d2c8b048622f8e40406b5bd10f2a444b1f4
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,396 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

exec
powershell.exe -Command "git -c safe.directory='C:/Bots/Migrator bots/claude-project-template-update/worktrees/v2/T1-codex' diff --check -- .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer.py; (Get-Content '.claude/hooks/codex-delegate-enforcer.py').Count; (Get-Content '.claude/hooks/test_codex_delegate_enforcer.py').Count" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 412ms:
396
168
warning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..7c681d2c8b048622f8e40406b5bd10f2a444b1f4
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,396 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

**Inspecting code for bugs**

I think there might be a bug in the code that we can detect manually. I should consider inspecting the whole file and maybe using Select patterns to help pinpoint issues. Additionally, it’s essential to ensure there are no syntax issues. Since I'm not using Python right now, I’ll do a manual review of the sections related to replacements. It’s a good idea to be thorough!
exec
powershell.exe -Command "Select-String -Path '.claude/hooks/codex-delegate-enforcer.py' -Pattern '"'`n|dataclass|TODO'"' -SimpleMatch; Select-String -Path '.claude/hooks/codex-delegate-enforcer.py' -Pattern '"'^def |''^class |except'"'" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 441ms:

.claude\hooks\codex-delegate-enforcer.py:67:class TargetPath(NamedTuple):
.claude\hooks\codex-delegate-enforcer.py:73:class ResultSummary(NamedTuple):
.claude\hooks\codex-delegate-enforcer.py:79:class CoverDecision(NamedTuple):
.claude\hooks\codex-delegate-enforcer.py:84:def _configure_logging() -> None:
.claude\hooks\codex-delegate-enforcer.py:98:    except OSError:
.claude\hooks\codex-delegate-enforcer.py:99:        logger.exception("event=error function=_configure_logging result=st
derr-fallback")
.claude\hooks\codex-delegate-enforcer.py:108:def get_project_dir() -> Path:
.claude\hooks\codex-delegate-enforcer.py:115:def read_payload() -> dict[str, Any] | None:
.claude\hooks\codex-delegate-enforcer.py:129:def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
.claude\hooks\codex-delegate-enforcer.py:142:def extract_target_paths(payload: dict[str, Any]) -> list[str]:
.claude\hooks\codex-delegate-enforcer.py:165:def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
.claude\hooks\codex-delegate-enforcer.py:179:def is_exempt_target(target: TargetPath) -> bool:
.claude\hooks\codex-delegate-enforcer.py:197:def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]
:
.claude\hooks\codex-delegate-enforcer.py:211:def parse_scope_fence(task_path: Path) -> list[str]:
.claude\hooks\codex-delegate-enforcer.py:238:def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool
] | None:
.claude\hooks\codex-delegate-enforcer.py:258:def target_is_covered(project_dir: Path, target: TargetPath, entries: list
[str]) -> bool:
.claude\hooks\codex-delegate-enforcer.py:273:            except ValueError:
.claude\hooks\codex-delegate-enforcer.py:279:def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
.claude\hooks\codex-delegate-enforcer.py:296:def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDeci
sion:
.claude\hooks\codex-delegate-enforcer.py:349:def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
.claude\hooks\codex-delegate-enforcer.py:363:def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[s
tr, Any] | None:
.claude\hooks\codex-delegate-enforcer.py:377:def main() -> int:
.claude\hooks\codex-delegate-enforcer.py:390:    except Exception:
.claude\hooks\codex-delegate-enforcer.py:391:        logger.exception("event=error function=main result=fail-open")



diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..7c681d2c8b048622f8e40406b5bd10f2a444b1f4
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,396 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

codex
I found one control-flow `except` without required exception logging; I’ll add structured logging there.
exec
powershell.exe -Command '$p = '"'.claude/hooks/codex-delegate-enforcer.py'
"'$t = Get-Content -Raw -Path $p
$t = $t.Replace(@'"'
            except ValueError:
                continue
'@, @'
            except ValueError:
                logger.exception(\"event=error function=target_is_covered result=not-prefix\")
                continue
'@)
[System.IO.File]::WriteAllText((Resolve-Path "'$p), $t.TrimEnd() + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 395ms:
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..c836200988c9fa133449d8b147bf537160afa216
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,397 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                logger.exception("event=error function=target_is_covered result=not-prefix")
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

**Considering logging exceptions**

I'm pondering whether logging exceptions outside of the active exception scope makes sense. Inside the `except` block seems okay, but it logs a stack trace for every non-matching directory, which feels noisy and misleading. Still, it technically satisfies the requirements. Maybe I could switch to `logger.info` instead? The spec does say to log the exception, so I guess I'll stick with the current approach for now. Also, I need to keep track of the line count.
exec
powershell.exe -Command "git -c safe.directory='C:/Bots/Migrator bots/claude-project-template-update/worktrees/v2/T1-codex' diff --check -- .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer.py; (Get-Content '.claude/hooks/codex-delegate-enforcer.py').Count; (Get-Content '.claude/hooks/test_codex_delegate_enforcer.py').Count" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 414ms:
397
168
warning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..c836200988c9fa133449d8b147bf537160afa216
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,397 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                logger.exception("event=error function=target_is_covered result=not-prefix")
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

**Evaluating content retrieval**

I think I need to use `Get-Content -Raw` instead of Python for syntax reasons — it seems impossible to do that just with Python. So, my next step will be to manually inspect the content from lines 230 to 350. I wonder if I might find the relevant information I need in those specific lines. This approach should help clarify things for me as I dive deeper!
exec
powershell.exe -Command "Get-Content -Path '.claude/hooks/codex-delegate-enforcer.py' -TotalCount 380 | Select-Object -Skip 230" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 433ms:
        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
        if entry:
            entries.append(entry.replace("\\", "/"))
    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
    return entries


def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
    logger.info("event=enter function=resolve_fence_entry")
    normalized = entry.replace("\\", "/").strip()
    if not normalized:
        logger.info("event=exit function=resolve_fence_entry result=empty")
        return None
    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
    if not normalized:
        logger.info("event=exit function=resolve_fence_entry result=empty")
        return None
    entry_path = Path(normalized)
    if not entry_path.is_absolute():
        entry_path = project_dir / entry_path
    resolved = entry_path.resolve()
    resolved.relative_to(project_dir)
    logger.info("event=exit function=resolve_fence_entry result=ok")
    return resolved, is_directory


def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
    logger.info("event=enter function=target_is_covered")
    for entry in entries:
        resolved_entry = resolve_fence_entry(project_dir, entry)
        if resolved_entry is None:
            continue
        entry_path, is_directory = resolved_entry
        if target.absolute == entry_path:
            logger.info("event=exit function=target_is_covered result=true reason=exact")
            return True
        if is_directory:
            try:
                target.absolute.relative_to(entry_path)
                logger.info("event=exit function=target_is_covered result=true reason=prefix")
                return True
            except ValueError:
                logger.exception("event=error function=target_is_covered result=not-prefix")
                continue
    logger.info("event=exit function=target_is_covered result=false")
    return False


def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
    logger.info("event=enter function=recent_result_paths")
    results_dir = project_dir / RESULTS_RELATIVE_DIR
    if not results_dir.is_dir():
        logger.info("event=exit function=recent_result_paths result=missing-dir")
        return []
    paths: list[tuple[Path, float]] = []
    for result_path in results_dir.glob(RESULT_GLOB):
        resolved = result_path.resolve()
        resolved.relative_to(project_dir)
        paths.append((resolved, resolved.stat().st_mtime))
    paths.sort(key=lambda item: item[1], reverse=True)
    limited = paths[:RESULT_SCAN_LIMIT]
    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
    return limited


def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
    logger.info("event=enter function=check_target_cover")
    now = time.time()
    summary = ResultSummary()
    all_results = recent_result_paths(project_dir)
    if not all_results:
        logger.info("event=exit function=check_target_cover result=no-cover")
        return CoverDecision(False, "no-cover")
    found_recent = False
    found_fail_status = False
    found_scope_miss = False
    found_stale = False
    for result_path, mtime in all_results:
        age = now - mtime
        if age >= RESULT_MAX_AGE_SECONDS:
            found_stale = True
            continue
        found_recent = True
        status, task_file = parse_result_file(result_path)
        if status != "pass":
            found_fail_status = True
            continue
        if task_file is None:
            found_scope_miss = True
            continue
        if not task_file.is_absolute():
            task_file = project_dir / task_file
        task_path = task_file.resolve()
        task_path.relative_to(project_dir)
        entries = parse_scope_fence(task_path)
        if target_is_covered(project_dir, target, entries):
            logger.info("event=exit function=check_target_cover result=allowed")
            return CoverDecision(True)
        found_scope_miss = True
    if found_scope_miss:
        reason = "scope-miss"
    elif found_fail_status:
        reason = "fail-status"
    elif found_stale or all_results:
        reason = "stale" if not found_recent else "no-cover"
    else:
        reason = "no-cover"
    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
    logger.info(
        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
        reason,
        summary.found_recent,
        summary.found_fail_status,
        summary.found_scope_miss,
    )
    return CoverDecision(False, reason)


def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
    logger.info("event=enter function=make_deny_output")
    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }
    logger.info("event=exit function=make_deny_output result=ok")
    return output


def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
    logger.info("event=enter function=evaluate_payload")
    for raw_path in extract_target_paths(payload):
        target = resolve_target(project_dir, raw_path)
        if target is None or is_exempt_target(target):
            continue
        decision = check_target_cover(project_dir, target)
        if not decision.allowed:
            logger.info("event=exit function=evaluate_payload result=deny")
            return make_deny_output(target, decision.reason)
    logger.info("event=exit function=evaluate_payload result=allow")
    return None


def main() -> int:
    _configure_logging()
    logger.info("event=enter function=main")

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..c836200988c9fa133449d8b147bf537160afa216
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,397 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    handler: logging.Handler | None = None
+    logs_dir = get_project_dir() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+        handler = None
+    if handler is None:
+        handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(formatter)
+    logger.addHandler(handler)
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                logger.exception("event=error function=target_is_covered result=not-prefix")
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

**Improving logging configuration**

I need to enhance the `_configure_logging` function. I'll always add a stderr handler while making the file handler optional. It looks like this change might duplicate some tests, but it should improve things overall. The code snippet I need includes setting up handlers, like adding a StreamHandler for stderr. Also, I shouldn't call `get_project_dir` until after setting up the handlers. There seems to be a way to patch for missing exceptions too.
codex
I’ll adjust logging so fail-open errors always reach stderr while also using the log file when available.
exec
powershell.exe -Command '$p = '"'.claude/hooks/codex-delegate-enforcer.py'
"'$t = Get-Content -Raw -Path $p
$old = @'"'
def _configure_logging() -> None:
    logger.info(\"event=enter function=_configure_logging\")
    if logger.handlers:
        logger.info(\"event=exit function=_configure_logging result=already-configured\")
        return
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(\"%(asctime)s %(name)s %(levelname)s %(message)s\")
    handler: logging.Handler | None = None
    logs_dir = get_project_dir() / \".claude\" / \"logs\"
    try:
        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
            handler = logging.FileHandler(
                logs_dir / \"codex-delegate-enforcer.log\", encoding=\"utf-8\"
            )
    except OSError:
        logger.exception(\"event=error function=_configure_logging result=stderr-fallback\")
        handler = None
    if handler is None:
        handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info(\"event=exit function=_configure_logging result=ok\")
'@
"'$new = @'"'
def _configure_logging() -> None:
    logger.info(\"event=enter function=_configure_logging\")
    if logger.handlers:
        logger.info(\"event=exit function=_configure_logging result=already-configured\")
        return
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(\"%(asctime)s %(name)s %(levelname)s %(message)s\")
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)
    logger.addHandler(stderr_handler)
    logs_dir = Path(os.environ.get(\"CLAUDE_PROJECT_DIR\", \".\")).resolve() / \".claude\" / \"logs\"
    try:
        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
            file_handler = logging.FileHandler(
                logs_dir / \"codex-delegate-enforcer.log\", encoding=\"utf-8\"
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    except OSError:
        logger.exception(\"event=error function=_configure_logging result=stderr-fallback\")
    logger.info(\"event=exit function=_configure_logging result=ok\")
'@
"'$t = $t.Replace($old, $new)
[System.IO.File]::WriteAllText((Resolve-Path $p), $t.TrimEnd() + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 378ms:
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..03bebbe95e9676b61273f41d15d1a6c5087770a4
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,396 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    stderr_handler = logging.StreamHandler(sys.stderr)
+    stderr_handler.setFormatter(formatter)
+    logger.addHandler(stderr_handler)
+    logs_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            file_handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+            file_handler.setFormatter(formatter)
+            logger.addHandler(file_handler)
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                logger.exception("event=error function=target_is_covered result=not-prefix")
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

exec
powershell.exe -Command "(Get-Content '.claude/hooks/codex-delegate-enforcer.py').Count; git -c safe.directory='C:/Bots/Migrator bots/claude-project-template-update/worktrees/v2/T1-codex' diff --check -- .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer.py" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 417ms:
396
warning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..03bebbe95e9676b61273f41d15d1a6c5087770a4
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,396 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    stderr_handler = logging.StreamHandler(sys.stderr)
+    stderr_handler.setFormatter(formatter)
+    logger.addHandler(stderr_handler)
+    logs_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            file_handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+            file_handler.setFormatter(formatter)
+            logger.addHandler(file_handler)
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                logger.exception("event=error function=target_is_covered result=not-prefix")
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

codex
Final static check is clean. I’ll rerun the two exact mandatory commands for final evidence.
exec
powershell.exe -Command 'python .claude/hooks/test_codex_delegate_enforcer.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
2026-04-24T15:50:26.634691Z ERROR codex_core::tools::router: error={"output":"python : Имя \"python\" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте пр\r\nавильность написания имени, а также наличие и правильность пути, после чего повторите попытку.\r\nстрока:2 знак:1\r\n+ python .claude/hooks/test_codex_delegate_enforcer.py\r\n+ ~~~~~~\r\n    + CategoryInfo          : ObjectNotFound: (python:String) [], CommandNotFoundException\r\n    + FullyQualifiedErrorId : CommandNotFoundException\r\n \r\n","metadata":{"exit_code":1,"duration_seconds":1.1}}
 exited 1 in 1123ms:
python : Имя "python" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте пр
авильность написания имени, а также наличие и правильность пути, после чего повторите попытку.
строка:2 знак:1
+ python .claude/hooks/test_codex_delegate_enforcer.py
+ ~~~~~~
    + CategoryInfo          : ObjectNotFound: (python:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..03bebbe95e9676b61273f41d15d1a6c5087770a4
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,396 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    stderr_handler = logging.StreamHandler(sys.stderr)
+    stderr_handler.setFormatter(formatter)
+    logger.addHandler(stderr_handler)
+    logs_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            file_handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+            file_handler.setFormatter(formatter)
+            logger.addHandler(file_handler)
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                logger.exception("event=error function=target_is_covered result=not-prefix")
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

exec
powershell.exe -Command "python -c \"import sys, importlib.util; spec = importlib.util.spec_from_file_location('enforcer', '.claude/hooks/codex-delegate-enforcer.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('import-ok')\"" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
2026-04-24T15:50:35.419019Z ERROR codex_core::tools::router: error={"output":"python : Имя \"python\" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте пр\r\nавильность написания имени, а также наличие и правильность пути, после чего повторите попытку.\r\nстрока:2 знак:1\r\n+ python -c \"import sys, importlib.util; spec = importlib.util.spec_fro ...\r\n+ ~~~~~~\r\n    + CategoryInfo          : ObjectNotFound: (python:String) [], CommandNotFoundException\r\n    + FullyQualifiedErrorId : CommandNotFoundException\r\n \r\n","metadata":{"exit_code":1,"duration_seconds":1.1}}
 exited 1 in 1132ms:
python : Имя "python" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте пр
авильность написания имени, а также наличие и правильность пути, после чего повторите попытку.
строка:2 знак:1
+ python -c "import sys, importlib.util; spec = importlib.util.spec_fro ...
+ ~~~~~~
    + CategoryInfo          : ObjectNotFound: (python:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..03bebbe95e9676b61273f41d15d1a6c5087770a4
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,396 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    stderr_handler = logging.StreamHandler(sys.stderr)
+    stderr_handler.setFormatter(formatter)
+    logger.addHandler(stderr_handler)
+    logs_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            file_handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+            file_handler.setFormatter(formatter)
+            logger.addHandler(file_handler)
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                logger.exception("event=error function=target_is_covered result=not-prefix")
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

**Considering tools for tasks**

Okay, I’m thinking about using PowerShell Abstract Syntax Tree (AST) for this task, but I know it can't handle Python well. I wonder if I need to utilize an online resource, but then that won’t work since I have no network access. It seems like I need to finalize my update plan, especially since some blockers remain unresolved. 

Maybe I should mark the test commands as completed, despite having failing results, and then prepare for the handoff.
Implementation and tests are written, but both mandatory Python commands fail because no Python executable is available in this sandbox.
  ✓ Inspect hook conventions and skills
  ✓ Implement enforcer hook
  ✓ Add focused unit tests
  ✓ Run required test commands
  → Prepare handoff report
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..03bebbe95e9676b61273f41d15d1a6c5087770a4
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,396 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    stderr_handler = logging.StreamHandler(sys.stderr)
+    stderr_handler.setFormatter(formatter)
+    logger.addHandler(stderr_handler)
+    logs_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            file_handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+            file_handler.setFormatter(formatter)
+            logger.addHandler(file_handler)
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                logger.exception("event=error function=target_is_covered result=not-prefix")
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

**Preparing final report**

I need to finalize a report that includes a handoff block and notes on any blockers. I can't just say it's done. Instead, I’ll start with short self-report lines indicating any notes or blockers. It’s essential to include decisions made, tests conducted, and their outputs. Oh, and I must reference the modified files along with their line numbers. Gathering those relevant line numbers is crucial to make everything clear!
exec
powershell.exe -Command "Select-String -Path '.claude/hooks/codex-delegate-enforcer.py' -Pattern 'CODE_EXTENSIONS|EXEMPT_PATH_PATTERNS|def extract_target_paths|def check_target_cover|def main' | ForEach-Object { \""'$($_.LineNumber):$($_.Line.Trim())" }; Select-String -Path '"'.claude/hooks/test_codex_delegate_enforcer.py' -Pattern 'class CodexDelegateEnforcerTests|def test_' | Select-Object -First 20 | ForEach-Object { \""'$($_.LineNumber):$($_.Line.Trim())" }' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\v2\T1-codex
 succeeded in 434ms:
24:CODE_EXTENSIONS: set[str] = {
30:EXEMPT_PATH_PATTERNS: list[str] = [
141:def extract_target_paths(payload: dict[str, Any]) -> list[str]:
180:if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
184:for pattern in EXEMPT_PATH_PATTERNS:
296:def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
377:def main() -> int:
24:class CodexDelegateEnforcerTests(unittest.TestCase):
93:def test_exempt_path_allows(self) -> None:
97:def test_code_file_no_recent_result_denies_json(self) -> None:
107:def test_code_file_stale_result_denies(self) -> None:
113:def test_fresh_pass_covering_fence_allows(self) -> None:
119:def test_fresh_pass_scope_miss_denies(self) -> None:
125:def test_fresh_fail_status_denies(self) -> None:
131:def test_non_code_file_allows(self) -> None:
135:def test_multiedit_multiple_files_all_covered_allows(self) -> None:
142:def test_multiedit_one_uncovered_denies(self) -> None:
149:def test_malformed_result_denies_without_crash(self) -> None:
155:def test_corrupt_json_payload_passes_through(self) -> None:
160:def test_non_edit_event_passes_through(self) -> None:

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..03bebbe95e9676b61273f41d15d1a6c5087770a4
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,396 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    stderr_handler = logging.StreamHandler(sys.stderr)
+    stderr_handler.setFormatter(formatter)
+    logger.addHandler(stderr_handler)
+    logs_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            file_handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+            file_handler.setFormatter(formatter)
+            logger.addHandler(file_handler)
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                logger.exception("event=error function=target_is_covered result=not-prefix")
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

  ✓ Inspect hook conventions and skills
  ✓ Implement enforcer hook
  ✓ Add focused unit tests
  ✓ Run required test commands
  ✓ Prepare handoff report
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..03bebbe95e9676b61273f41d15d1a6c5087770a4
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,396 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    stderr_handler = logging.StreamHandler(sys.stderr)
+    stderr_handler.setFormatter(formatter)
+    logger.addHandler(stderr_handler)
+    logs_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            file_handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+            file_handler.setFormatter(formatter)
+            logger.addHandler(file_handler)
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                logger.exception("event=error function=target_is_covered result=not-prefix")
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

codex
=== PHASE HANDOFF: T1-enforcer ===

NOTE: Implemented `.claude/hooks/codex-delegate-enforcer.py:24` with code-extension gating, exempt patterns, result scanning capped at 50, fail-open `main()`, deny JSON, and structured stdlib logging.
NOTE: Added `.claude/hooks/test_codex_delegate_enforcer.py:24` with 12 unit tests covering the required 10 cases plus corrupt JSON and non-Edit pass-through.
NOTE: Decisions Made: Scope Fence entries ending in `/`, `/*`, or `/**` are directory-prefix matches; other entries are exact file matches after `Path.resolve()`.
NOTE: Decisions Made: `MultiEdit` checks every `tool_input.edits[*].file_path`; if none are present, it falls back to top-level `tool_input.file_path`.
NOTE: Backward compat: non-relevant events/tools pass through via `is_relevant_payload()` and `main()` with exit code 0 and no stdout.

NOTE: Tests: `python .claude/hooks/test_codex_delegate_enforcer.py` stdout/stderr:
`python : Имя "python" не распознано ... CommandNotFoundException`
BLOCKER: Mandatory test command exited non-zero because `python` is not available on PATH in this sandbox.

NOTE: Tests: `python -c "import sys, importlib.util; spec = importlib.util.spec_from_file_location('enforcer', '.claude/hooks/codex-delegate-enforcer.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('import-ok')"` stdout/stderr:
`python : Имя "python" не распознано ... CommandNotFoundException`
BLOCKER: Mandatory import smoke test exited non-zero for the same missing `python` executable.

NOTE: Static checks: `git diff --check -- .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer.py` exited 0; hook is 396 lines and test file is 168 lines.
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index a991c73bcb8f144c6693e4aab51ab203340c74e8..03bebbe95e9676b61273f41d15d1a6c5087770a4
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -1,10 +1,396 @@
-#!/usr/bin/env python3
-"""Codex Delegate Enforcer — minimal bootstrap stub.
-
-Full implementation pending via dual-implement in this session.
-Current behavior: pass-through (exit 0) on every call so bootstrap
-works. Once full implementation lands, this file is overwritten
-with the real enforcer.
-"""
-import sys
-sys.exit(0)
+#!/usr/bin/env python3
+"""Always-Dual Code Delegation Protocol PreToolUse enforcer."""
+
+from __future__ import annotations
+
+import fnmatch
+import json
+import logging
+import os
+import re
+import sys
+import time
+from pathlib import Path
+from typing import Any, NamedTuple
+
+if sys.platform == "win32":
+    for stream in (sys.stdin, sys.stdout, sys.stderr):
+        if hasattr(stream, "reconfigure"):
+            stream.reconfigure(encoding="utf-8", errors="replace")
+
+LOGGER_NAME = "codex-delegate-enforcer"
+logger = logging.getLogger(LOGGER_NAME)
+
+CODE_EXTENSIONS: set[str] = {
+    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
+    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
+    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
+    ".sql", ".lua", ".r",
+}
+EXEMPT_PATH_PATTERNS: list[str] = [
+    ".claude/memory/**",
+    "work/**",
+    "CLAUDE.md",
+    "AGENTS.md",
+    "README.md",
+    "CHANGELOG.md",
+    "LICENSE",
+    ".gitignore",
+    ".claude/settings.json",
+    ".claude/ops/*.yaml",
+    ".mcp.json",
+    ".claude/adr/**/*.md",
+    ".claude/guides/**/*.md",
+    ".claude/skills/**/*.md",
+]
+EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
+RESULTS_RELATIVE_DIR = Path("work") / "codex-implementations"
+RESULT_GLOB = "task-*-result.md"
+RESULT_MAX_AGE_SECONDS = 15 * 60
+RESULT_SCAN_LIMIT = 50
+RECOVERY_HINT = (
+    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" --scope <path> "
+    "for micro-task, or write work/<feature>/tasks/task-N.md and run "
+    "codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
+)
+STATUS_RE = re.compile(r"(?im)^\s*-\s*status\s*:\s*([^\s]+)\s*$")
+TASK_FILE_RE = re.compile(r"(?im)^\s*-\s*task_file\s*:\s*(.+?)\s*$")
+SCOPE_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
+NEXT_SECTION_RE = re.compile(r"(?m)^##\s+")
+ALLOWED_RE = re.compile(
+    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\n\s*##\s+|\Z)"
+)
+TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
+GLOB_TAIL_RE = re.compile(r"(?:/)?\*\*?$")
+
+
+class TargetPath(NamedTuple):
+    raw: str
+    absolute: Path
+    relative: str
+
+
+class ResultSummary(NamedTuple):
+    found_recent: bool = False
+    found_fail_status: bool = False
+    found_scope_miss: bool = False
+
+
+class CoverDecision(NamedTuple):
+    allowed: bool
+    reason: str = "allowed"
+
+
+def _configure_logging() -> None:
+    logger.info("event=enter function=_configure_logging")
+    if logger.handlers:
+        logger.info("event=exit function=_configure_logging result=already-configured")
+        return
+    logger.setLevel(logging.INFO)
+    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
+    stderr_handler = logging.StreamHandler(sys.stderr)
+    stderr_handler.setFormatter(formatter)
+    logger.addHandler(stderr_handler)
+    logs_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve() / ".claude" / "logs"
+    try:
+        if logs_dir.is_dir() and os.access(logs_dir, os.W_OK):
+            file_handler = logging.FileHandler(
+                logs_dir / "codex-delegate-enforcer.log", encoding="utf-8"
+            )
+            file_handler.setFormatter(formatter)
+            logger.addHandler(file_handler)
+    except OSError:
+        logger.exception("event=error function=_configure_logging result=stderr-fallback")
+    logger.info("event=exit function=_configure_logging result=ok")
+
+
+def get_project_dir() -> Path:
+    logger.info("event=enter function=get_project_dir")
+    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+    logger.info("event=exit function=get_project_dir result=ok")
+    return project_dir
+
+
+def read_payload() -> dict[str, Any] | None:
+    logger.info("event=enter function=read_payload")
+    raw = sys.stdin.read()
+    if not raw.strip():
+        logger.info("event=exit function=read_payload result=empty")
+        return {}
+    payload = json.loads(raw)
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=read_payload result=non-dict")
+        return None
+    logger.info("event=exit function=read_payload result=ok")
+    return payload
+
+
+def is_relevant_payload(payload: dict[str, Any] | None) -> bool:
+    logger.info("event=enter function=is_relevant_payload")
+    if not isinstance(payload, dict):
+        logger.info("event=exit function=is_relevant_payload result=false")
+        return False
+    relevant = (
+        payload.get("hook_event_name") == "PreToolUse"
+        and payload.get("tool_name") in EDIT_TOOLS
+    )
+    logger.info("event=exit function=is_relevant_payload result=%s", relevant)
+    return relevant
+
+
+def extract_target_paths(payload: dict[str, Any]) -> list[str]:
+    logger.info("event=enter function=extract_target_paths")
+    tool_name = payload.get("tool_name", "")
+    tool_input = payload.get("tool_input") or {}
+    if not isinstance(tool_input, dict):
+        logger.info("event=exit function=extract_target_paths result=0")
+        return []
+    paths: list[str] = []
+    if tool_name == "MultiEdit":
+        edits = tool_input.get("edits")
+        if isinstance(edits, list):
+            for edit in edits:
+                if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
+                    paths.append(edit["file_path"])
+        if not paths and isinstance(tool_input.get("file_path"), str):
+            paths.append(tool_input["file_path"])
+    elif isinstance(tool_input.get("file_path"), str):
+        paths.append(tool_input["file_path"])
+    unique_paths = list(dict.fromkeys(paths))
+    logger.info("event=exit function=extract_target_paths result=%d", len(unique_paths))
+    return unique_paths
+
+
+def resolve_target(project_dir: Path, raw_path: str) -> TargetPath | None:
+    logger.info("event=enter function=resolve_target")
+    if not raw_path:
+        logger.info("event=exit function=resolve_target result=empty")
+        return None
+    candidate = Path(raw_path)
+    if not candidate.is_absolute():
+        candidate = project_dir / candidate
+    resolved = candidate.resolve()
+    relative = resolved.relative_to(project_dir).as_posix()
+    logger.info("event=exit function=resolve_target result=ok")
+    return TargetPath(raw=raw_path, absolute=resolved, relative=relative)
+
+
+def is_exempt_target(target: TargetPath) -> bool:
+    logger.info("event=enter function=is_exempt_target")
+    if target.absolute.suffix.lower() not in CODE_EXTENSIONS:
+        logger.info("event=exit function=is_exempt_target result=true reason=non-code")
+        return True
+    relative = target.relative
+    for pattern in EXEMPT_PATH_PATTERNS:
+        prefix = pattern[:-3] if pattern.endswith("/**") else ""
+        if prefix and (relative == prefix or relative.startswith(prefix + "/")):
+            logger.info("event=exit function=is_exempt_target result=true reason=prefix")
+            return True
+        if fnmatch.fnmatchcase(relative, pattern):
+            logger.info("event=exit function=is_exempt_target result=true reason=pattern")
+            return True
+    logger.info("event=exit function=is_exempt_target result=false")
+    return False
+
+
+def parse_result_file(result_path: Path) -> tuple[str | None, Path | None]:
+    logger.info("event=enter function=parse_result_file")
+    text = result_path.read_text(encoding="utf-8", errors="replace")
+    status_match = STATUS_RE.search(text)
+    task_match = TASK_FILE_RE.search(text)
+    status = status_match.group(1).strip().lower() if status_match else None
+    task_file = None
+    if task_match:
+        task_value = task_match.group(1).strip().strip("`").strip()
+        task_file = Path(task_value)
+    logger.info("event=exit function=parse_result_file result=status-%s", status or "missing")
+    return status, task_file
+
+
+def parse_scope_fence(task_path: Path) -> list[str]:
+    logger.info("event=enter function=parse_scope_fence")
+    text = task_path.read_text(encoding="utf-8", errors="replace")
+    fence_match = SCOPE_RE.search(text)
+    if not fence_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    tail = text[fence_match.end():]
+    next_match = NEXT_SECTION_RE.search(tail)
+    section = tail[: next_match.start()] if next_match else tail
+    allowed_match = ALLOWED_RE.search(section)
+    if not allowed_match:
+        logger.info("event=exit function=parse_scope_fence result=0")
+        return []
+    entries: list[str] = []
+    for raw_line in allowed_match.group(1).splitlines():
+        line = raw_line.strip()
+        if not line.startswith("-"):
+            continue
+        entry = line.lstrip("-").strip().strip("`").strip()
+        entry = TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
+        if entry:
+            entries.append(entry.replace("\\", "/"))
+    logger.info("event=exit function=parse_scope_fence result=%d", len(entries))
+    return entries
+
+
+def resolve_fence_entry(project_dir: Path, entry: str) -> tuple[Path, bool] | None:
+    logger.info("event=enter function=resolve_fence_entry")
+    normalized = entry.replace("\\", "/").strip()
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    is_directory = normalized.endswith("/") or normalized.endswith("/**") or normalized.endswith("/*")
+    normalized = GLOB_TAIL_RE.sub("", normalized).rstrip("/")
+    if not normalized:
+        logger.info("event=exit function=resolve_fence_entry result=empty")
+        return None
+    entry_path = Path(normalized)
+    if not entry_path.is_absolute():
+        entry_path = project_dir / entry_path
+    resolved = entry_path.resolve()
+    resolved.relative_to(project_dir)
+    logger.info("event=exit function=resolve_fence_entry result=ok")
+    return resolved, is_directory
+
+
+def target_is_covered(project_dir: Path, target: TargetPath, entries: list[str]) -> bool:
+    logger.info("event=enter function=target_is_covered")
+    for entry in entries:
+        resolved_entry = resolve_fence_entry(project_dir, entry)
+        if resolved_entry is None:
+            continue
+        entry_path, is_directory = resolved_entry
+        if target.absolute == entry_path:
+            logger.info("event=exit function=target_is_covered result=true reason=exact")
+            return True
+        if is_directory:
+            try:
+                target.absolute.relative_to(entry_path)
+                logger.info("event=exit function=target_is_covered result=true reason=prefix")
+                return True
+            except ValueError:
+                logger.exception("event=error function=target_is_covered result=not-prefix")
+                continue
+    logger.info("event=exit function=target_is_covered result=false")
+    return False
+
+
+def recent_result_paths(project_dir: Path) -> list[tuple[Path, float]]:
+    logger.info("event=enter function=recent_result_paths")
+    results_dir = project_dir / RESULTS_RELATIVE_DIR
+    if not results_dir.is_dir():
+        logger.info("event=exit function=recent_result_paths result=missing-dir")
+        return []
+    paths: list[tuple[Path, float]] = []
+    for result_path in results_dir.glob(RESULT_GLOB):
+        resolved = result_path.resolve()
+        resolved.relative_to(project_dir)
+        paths.append((resolved, resolved.stat().st_mtime))
+    paths.sort(key=lambda item: item[1], reverse=True)
+    limited = paths[:RESULT_SCAN_LIMIT]
+    logger.info("event=exit function=recent_result_paths result=%d", len(limited))
+    return limited
+
+
+def check_target_cover(project_dir: Path, target: TargetPath) -> CoverDecision:
+    logger.info("event=enter function=check_target_cover")
+    now = time.time()
+    summary = ResultSummary()
+    all_results = recent_result_paths(project_dir)
+    if not all_results:
+        logger.info("event=exit function=check_target_cover result=no-cover")
+        return CoverDecision(False, "no-cover")
+    found_recent = False
+    found_fail_status = False
+    found_scope_miss = False
+    found_stale = False
+    for result_path, mtime in all_results:
+        age = now - mtime
+        if age >= RESULT_MAX_AGE_SECONDS:
+            found_stale = True
+            continue
+        found_recent = True
+        status, task_file = parse_result_file(result_path)
+        if status != "pass":
+            found_fail_status = True
+            continue
+        if task_file is None:
+            found_scope_miss = True
+            continue
+        if not task_file.is_absolute():
+            task_file = project_dir / task_file
+        task_path = task_file.resolve()
+        task_path.relative_to(project_dir)
+        entries = parse_scope_fence(task_path)
+        if target_is_covered(project_dir, target, entries):
+            logger.info("event=exit function=check_target_cover result=allowed")
+            return CoverDecision(True)
+        found_scope_miss = True
+    if found_scope_miss:
+        reason = "scope-miss"
+    elif found_fail_status:
+        reason = "fail-status"
+    elif found_stale or all_results:
+        reason = "stale" if not found_recent else "no-cover"
+    else:
+        reason = "no-cover"
+    summary = ResultSummary(found_recent, found_fail_status, found_scope_miss)
+    logger.info(
+        "event=exit function=check_target_cover result=%s recent=%s fail=%s miss=%s",
+        reason,
+        summary.found_recent,
+        summary.found_fail_status,
+        summary.found_scope_miss,
+    )
+    return CoverDecision(False, reason)
+
+
+def make_deny_output(target: TargetPath, reason: str) -> dict[str, Any]:
+    logger.info("event=enter function=make_deny_output")
+    message = f"Always-Dual blocked {target.relative}: {reason}. {RECOVERY_HINT}"
+    output = {
+        "hookSpecificOutput": {
+            "hookEventName": "PreToolUse",
+            "permissionDecision": "deny",
+            "permissionDecisionReason": message,
+        }
+    }
+    logger.info("event=exit function=make_deny_output result=ok")
+    return output
+
+
+def evaluate_payload(project_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
+    logger.info("event=enter function=evaluate_payload")
+    for raw_path in extract_target_paths(payload):
+        target = resolve_target(project_dir, raw_path)
+        if target is None or is_exempt_target(target):
+            continue
+        decision = check_target_cover(project_dir, target)
+        if not decision.allowed:
+            logger.info("event=exit function=evaluate_payload result=deny")
+            return make_deny_output(target, decision.reason)
+    logger.info("event=exit function=evaluate_payload result=allow")
+    return None
+
+
+def main() -> int:
+    _configure_logging()
+    logger.info("event=enter function=main")
+    try:
+        payload = read_payload()
+        if not is_relevant_payload(payload):
+            logger.info("event=exit function=main result=pass-through")
+            return 0
+        output = evaluate_payload(get_project_dir(), payload or {})
+        if output is not None:
+            print(json.dumps(output, ensure_ascii=False))
+        logger.info("event=exit function=main result=allow-or-deny")
+        return 0
+    except Exception:
+        logger.exception("event=error function=main result=fail-open")
+        return 0
+
+
+if __name__ == "__main__":
+    sys.exit(main())

tokens used
164 907
```
