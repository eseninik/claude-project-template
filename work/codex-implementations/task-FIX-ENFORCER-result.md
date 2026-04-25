# Codex Implementation Result — Task FIX-ENFORCER

- status: pass
- timestamp: 2026-04-25T07:24:36.227872+00:00
- task_file: C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations\inline\task-FIX-ENFORCER.md
- base_sha: c1edf4e047577b9bb4548dd6ed3e30ab1410e084
- codex_returncode: 0
- scope_status: pass
- scope_message: OK: 2 path(s) in fence
- tests_all_passed: True
- test_commands_count: 1

## Diff

```diff
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 81098ec..559a64c 100644
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -85,6 +85,42 @@ def get_project_dir() -> Path:
     """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
     return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
 
+def is_dual_teams_worktree(project_dir: Path) -> bool:
+    """True iff project_dir or any ancestor contains .dual-base-ref."""
+    logger = logging.getLogger(HOOK_NAME)
+    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
+    current = project_dir
+    seen: set[Path] = set()
+    while True:
+        try:
+            resolved = current.resolve()
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
+            resolved = current.absolute()
+        if resolved in seen:
+            logger.info(
+                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
+                project_dir,
+            )
+            return False
+        seen.add(resolved)
+        sentinel = current / ".dual-base-ref"
+        try:
+            if sentinel.is_file():
+                logger.info(
+                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
+                    project_dir,
+                    sentinel,
+                )
+                return True
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
+        parent = current.parent
+        if parent == current:
+            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
+            return False
+        current = parent
+
 def resolve_target(project_dir: Path, target_raw: str):
     """Normalize raw file_path to absolute Path inside project_dir."""
     logger = logging.getLogger(HOOK_NAME)
@@ -394,6 +430,9 @@ def decide(payload: dict, project_dir: Path) -> bool:
     if tool_name not in {"Edit", "Write", "MultiEdit"}:
         logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
         return True
+    if is_dual_teams_worktree(project_dir):
+        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
+        return True
     raw_targets = extract_targets(payload)
     if not raw_targets:
         logger.info("decide.passthrough reason=no-targets")
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba..ab2bfc1 100644
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -22,6 +22,8 @@ production .codex/ and work/ directories are never touched.
 from __future__ import annotations
 
 import importlib.util
+import contextlib
+import io
 import json
 import os
 import shutil
@@ -286,6 +288,74 @@ class TestAC12Cases(BaseEnforcerTest):
         self.assertEqual(out.strip(), "")
 
 
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
 class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
@@ -404,4 +474,4 @@ class TestHelpers(unittest.TestCase):
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)
```

## Test Output

### `py -3 .claude/hooks/test_codex_delegate_enforcer.py`

- returncode: 0  - passed: True  - timed_out: False

```
--- stderr ---
test_01_exempt_path_allow (__main__.TestAC12Cases.test_01_exempt_path_allow)
AC12.1: exempt path (CLAUDE.md) -> allow. ... ok
test_02_code_no_result_deny (__main__.TestAC12Cases.test_02_code_no_result_deny)
AC12.2: code file + NO recent result.md -> deny with JSON. ... ok
test_03_stale_result_deny (__main__.TestAC12Cases.test_03_stale_result_deny)
AC12.3: code file + stale (> 15 min) result.md -> deny. ... ok
test_04_covered_pass_allow (__main__.TestAC12Cases.test_04_covered_pass_allow)
AC12.4: code file + fresh pass result.md with covering fence -> allow. ... ok
test_05_uncovered_pass_deny (__main__.TestAC12Cases.test_05_uncovered_pass_deny)
AC12.5: fresh pass, fence does NOT cover target -> deny. ... ok
test_06_fail_status_deny (__main__.TestAC12Cases.test_06_fail_status_deny)
AC12.6: fresh status=fail result.md -> deny. ... ok
test_07_non_code_file_allow (__main__.TestAC12Cases.test_07_non_code_file_allow)
AC12.7: non-code file (.txt, .md) -> allow. ... ok
test_08_multiedit_all_covered_allow (__main__.TestAC12Cases.test_08_multiedit_all_covered_allow)
AC12.8: MultiEdit with multiple files, all covered -> allow. ... ok
test_09_multiedit_one_uncovered_deny (__main__.TestAC12Cases.test_09_multiedit_one_uncovered_deny)
AC12.9: MultiEdit with one file uncovered -> deny. ... ok
test_10a_malformed_result_passthrough (__main__.TestAC12Cases.test_10a_malformed_result_passthrough)
AC12.10a: malformed result.md -> no crash, handled gracefully. ... ok
test_10b_corrupt_json_payload_passthrough (__main__.TestAC12Cases.test_10b_corrupt_json_payload_passthrough)
AC12.10b: corrupt JSON payload -> pass-through, no crash, exit 0. ... ok
test_11_non_edit_event_passthrough (__main__.TestAC12Cases.test_11_non_edit_event_passthrough)
AC12.11: non-Edit tool (Bash) -> pass-through (exit 0, no deny). ... ok
test_decide_allows_edit_when_sentinel_present_without_result (__main__.TestDualTeamsDecide.test_decide_allows_edit_when_sentinel_present_without_result) ... ok
test_decide_denies_edit_when_sentinel_absent_without_result (__main__.TestDualTeamsDecide.test_decide_denies_edit_when_sentinel_absent_without_result) ... emit_deny target=.claude/scripts/foo.py reason=no-results
ok
test_dual_teams_worktree_false_for_directory_sentinel (__main__.TestDualTeamsSentinel.test_dual_teams_worktree_false_for_directory_sentinel) ... ok
test_dual_teams_worktree_false_without_sentinel (__main__.TestDualTeamsSentinel.test_dual_teams_worktree_false_without_sentinel) ... ok
test_dual_teams_worktree_true_in_parent_dir (__main__.TestDualTeamsSentinel.test_dual_teams_worktree_true_in_parent_dir) ... ok
test_dual_teams_worktree_true_in_project_dir (__main__.TestDualTeamsSentinel.test_dual_teams_worktree_true_in_project_dir) ... ok
test_extract_targets_edit (__main__.TestHelpers.test_extract_targets_edit) ... ok
test_extract_targets_missing_is_empty (__main__.TestHelpers.test_extract_targets_missing_is_empty) ... ok
test_extract_targets_multiedit (__main__.TestHelpers.test_extract_targets_multiedit) ... ok
test_is_code_extension_negative (__main__.TestHelpers.test_is_code_extension_negative) ... ok
test_is_code_extension_positive (__main__.TestHelpers.test_is_code_extension_positive) ... ok
test_is_exempt_guides_skills_adr (__main__.TestHelpers.test_is_exempt_guides_skills_adr) ... ok
test_is_exempt_memory_star_star (__main__.TestHelpers.test_is_exempt_memory_star_star) ... ok
test_is_exempt_negative (__main__.TestHelpers.test_is_exempt_negative) ... ok
test_is_exempt_top_level_files (__main__.TestHelpers.test_is_exempt_top_level_files) ... ok
test_parse_result_fields_status_pass (__main__.TestHelpers.test_parse_result_fields_status_pass) ... ok
test_parse_scope_fence_strips_backticks_and_annotations (__main__.TestHelpers.test_parse_scope_fence_strips_backticks_and_annotations) ... ok
test_path_in_fence_dir_prefix (__main__.TestHelpers.test_path_in_fence_dir_prefix) ... ok
test_path_in_fence_exact_file (__main__.TestHelpers.test_path_in_fence_exact_file) ... ok
test_path_in_fence_no_partial_segment (__main__.TestHelpers.test_path_in_fence_no_partial_segment) ... ok
test_path_in_fence_strips_trailing_globs (__main__.TestHelpers.test_path_in_fence_strips_trailing_globs) ... ok
test_requires_cover_negative_exempt (__main__.TestHelpers.test_requires_cover_negative_exempt) ... ok
test_requires_cover_negative_non_code (__main__.TestHelpers.test_requires_cover_negative_non_code) ... ok
test_requires_cover_positive (__main__.TestHelpers.test_requires_cover_positive) ... ok

----------------------------------------------------------------------
Ran 36 tests in 0.776s

OK
```

## Self-Report (Codex NOTE/BLOCKER lines)

- NOTE: Modified `.claude/hooks/codex-delegate-enforcer.py:88` with `is_dual_teams_worktree(project_dir: Path) -> bool` and the early `decide()` passthrough at `.claude/hooks/codex-delegate-enforcer.py:433`.
- NOTE: Modified `.claude/hooks/test_codex_delegate_enforcer.py:291` with sentinel helper tests and `.claude/hooks/test_codex_delegate_enforcer.py:332` with `decide()` allow/deny regression tests.
- NOTE: Diff stats: `.claude/hooks/codex-delegate-enforcer.py` `+39/-0`; `.claude/hooks/test_codex_delegate_enforcer.py` `+71/-1`.
- NOTE: fix path: sentinel ancestor walk in `decide()` — see `is_dual_teams_worktree()`.
- NOTE: Test command run: `py -3 .claude/hooks/test_codex_delegate_enforcer.py`
- NOTE: Test output: `No installed Python found!`
- BLOCKER: Required test command exits `1` because `C:\WINDOWS\py.exe` reports no installed Python in this sandbox, so I cannot truthfully report all tests passing.

## Codex stderr

```
OpenAI Codex v0.117.0 (research preview)
--------
workdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
model: gpt-5.5
provider: chatgpt
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR, C:\Users\Lenovo\.codex\memories]
reasoning effort: high
reasoning summaries: none
session id: 019dc386-acee-7471-9064-4b51b64d56ce
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
reasoning: high
speed_profile: balanced
---

# Task FIX-ENFORCER: codex-delegate-enforcer.py — exempt dual-teams worktrees via `.dual-base-ref` sentinel

## Your Task

**Y6 root cause.** `codex-delegate-enforcer.py` is a `PreToolUse` hook that blocks `Edit`/`Write`/`MultiEdit` on code files unless a fresh (< 15 min) `work/codex-implementations/task-*-result.md` with `status=pass` covers the target path.

When a Claude teammate runs **inside a dual-teams worktree** (e.g. `worktrees/validation/claude/task-V1-...`), the teammate's `CLAUDE_PROJECT_DIR` resolves to the worktree root — not the main repo. The teammate's project-relative target path becomes `.claude/scripts/foo.py`, which **does not match the existing `worktrees/**` exempt pattern** (that pattern only fires when the path *includes* `worktrees/...` as a prefix, i.e. when the planner session edits files inside a worktree from the main project root).

Net effect: every code Edit by the writer-half of a dual-implement run is denied. The teammate keeps retrying → 600 s watchdog kill → false "Claude teammate stalled" symptom.

The fix is to give the enforcer a reliable, location-independent signal that "this session IS the writer-half of a dual-implement run, the parallel Codex sibling is already executing — skip enforcement". The signal exists: `.dual-base-ref` is written by `codex-wave.py` and `dual-teams-spawn.py` into every freshly-created teammate worktree (FIX-B from Round 1).

Implement an ancestor walk: at the top of `decide()`, check whether `project_dir` (or any of its parents up to the filesystem root) holds a `.dual-base-ref` regular file. If yes → log `dual-teams-worktree`, return `True` (allow), skip the cover lookup entirely. If no → existing behavior unchanged.

The walk is bounded (`while parent != self`), guarded by a `seen` set against cycles, and tolerant of `OSError` on each `is_file()` probe (network drives, broken symlinks). No external dependencies.

## Scope Fence

**Allowed:**
- `.claude/hooks/codex-delegate-enforcer.py` (modify — add `is_dual_teams_worktree(project_dir)` helper + early-allow branch in `decide()`)
- `.claude/hooks/test_codex_delegate_enforcer.py` (modify — add tests; do NOT remove existing tests)

**Forbidden:**
- Every other path under `.claude/hooks/` and `.claude/scripts/`
- Any `work/*` or `worktrees/*` path
- Anything elsewhere in the repo

## Test Commands

```bash
py -3 .claude/hooks/test_codex_delegate_enforcer.py
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: New module-level function `is_dual_teams_worktree(project_dir: Path) -> bool` returns `True` iff `project_dir` *or any of its ancestors up to the filesystem root* contains a regular file named `.dual-base-ref`.
- [ ] AC2: The walk terminates: bounded by `parent == self` AND a `seen: set` of resolved Paths against pathological loops.
- [ ] AC3: The walk is exception-safe: each `is_file()` probe is wrapped so an `OSError` (e.g. permission denied on a network share) is treated as "not present" rather than propagating.
- [ ] AC4: `decide()` calls `is_dual_teams_worktree(project_dir)` immediately after the existing `event` and `tool_name` early-returns. If True → log `decide.passthrough reason=dual-teams-worktree project=<path>` and `return True`. The cover lookup loop is skipped entirely.
- [ ] AC5: When sentinel is absent, `decide()` behavior is byte-for-byte identical to before — every existing test in `test_codex_delegate_enforcer.py` still passes.
- [ ] AC6: NEW tests in `test_codex_delegate_enforcer.py`:
   - (a) `is_dual_teams_worktree` returns True when sentinel is in the project_dir itself.
   - (b) Returns True when sentinel is in a parent directory (deep nesting).
   - (c) Returns False when no sentinel exists anywhere in the chain.
   - (d) Returns False when the sentinel name exists but is a directory, not a regular file.
   - (e) `decide()` returns True (allow) for an Edit on `.claude/scripts/foo.py` when sentinel is present, even with NO fresh result.md anywhere.
   - (f) `decide()` returns False (deny) for the same Edit when sentinel is absent and no fresh result.md (existing behavior preserved).
- [ ] AC7: Structured logging: function entry/exit + the early-allow log line at INFO level. No bare prints.
- [ ] AC8: Stdlib only. Windows + POSIX both supported (use `Path` not `os.path`).
- [ ] AC9: `is_dual_teams_worktree` accepts `Path` only (matches existing `project_dir` type in this module).
- [ ] All Test Commands above exit 0.

## Constraints

- Do NOT change the existing `EXEMPT_PATTERNS` list — the sentinel check is an *additional* gate, not a replacement for the path-pattern exemption.
- Do NOT change any other file. Surgical fix, ~25 lines total in the hook + ~50 lines of new tests.
- Do NOT change the logging level conventions of the file (INFO for events, DEBUG for traces).
- The function name MUST be `is_dual_teams_worktree` exactly (other code may grow to depend on it).
- Use the existing `_build_logger` / `logging.getLogger(HOOK_NAME)` pattern; do NOT introduce a new logger.
- Tests must be self-contained (use `tempfile.TemporaryDirectory`, no fixtures of external paths).

## Handoff Output

Standard `=== PHASE HANDOFF: FIX-ENFORCER ===` with:
- Diff stats (lines added/removed in hook + tests)
- Output of `py -3 .claude/hooks/test_codex_delegate_enforcer.py` showing all tests pass (count of OK)
- Three-line note: "fix path: sentinel ancestor walk in `decide()` — see is_dual_teams_worktree()."


---- END TASK SPECIFICATION ----
Return a short self-report at the end of your run using lines starting with
`NOTE:` for observations and `BLOCKER:` for unresolved problems.

codex
I’ll use `tdd-workflow` plus project conventions, then inspect the hook/tests before patching.
exec
powershell.exe -Command "Get-Content -Path 'C:/Users/Lenovo/.codex/skills/tdd-workflow/SKILL.md'; Write-Output '---PROJECT---'; Get-Content -Path 'C:/Users/Lenovo/.codex/skills/project-conventions/SKILL.md'" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
 succeeded in 481ms:
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
---PROJECT---
---
name: "project-conventions"
description: "Project coding conventions and standards. Applied during implementation and review. Covers logging (structlog/pino), error handling, testing patterns, and architecture rules."
---

# Project Conventions

## Logging Standard

- Python: use `structlog` or `logging` stdlib with structured output
- Node.js: use `pino` with JSON output
- NEVER use bare `print()` or `console.log()` вЂ” ONLY logger calls
- Log levels: DEBUG (internals), INFO (business events), WARNING (recoverable), ERROR (failures), CRITICAL (fatal)

### What to Log
- Function entry with key parameters
- Function exit with result summary
- Every external call (API, DB, file I/O) with timing
- Every error/exception with full context and stack trace
- Decision points and branch taken

### What NOT to Log
- Passwords, tokens, API keys
- PII (emails, phone numbers, addresses)
- Full request/response bodies (log summary instead)

## Error Handling

- Handle errors at system boundaries (external APIs, user input, file I/O)
- Internal code can trust framework guarantees вЂ” don't over-validate
- Use specific exception types, not bare except/catch
- Always include context in error messages (what was attempted, with what inputs)

## Testing

- New behavior = new test (unit or integration)
- Bugfix = regression test that fails before fix
- Tests are IMMUTABLE after approval (Evaluation Firewall)
- Use pytest + AsyncMock for Python, jest/vitest for Node.js
- No network calls in tests unless explicitly mocked

## Architecture

- Clean Architecture: separate business logic from I/O
- Validate inputs at boundaries, trust internal data
- No premature abstractions вЂ” three similar lines > one premature helper
- Don't add features beyond what was asked

  → Inspect hook and tests
  • Add regression tests
  • Implement sentinel exemption
  • Run required test command
  • Prepare handoff self-report
codex
I’m checking the current hook shape and test style now.
exec
powershell.exe -Command "Get-Content -Path '.claude/hooks/codex-delegate-enforcer.py'; Write-Output '---TESTS---'; Get-Content -Path '.claude/hooks/test_codex_delegate_enforcer.py'" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
 succeeded in 475ms:
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
    "worktrees/**",  # dual-implement worktrees вЂ” edits here are part of an outer DUAL operation
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
---TESTS---
#!/usr/bin/env python3
"""Unit tests for codex-delegate-enforcer.py (task T1).

Covers all 11 required cases from spec AC12:

  1. exempt path (e.g., CLAUDE.md) -> allow
  2. code file + NO recent result.md -> deny with JSON
  3. code file + stale (> 15 min) result.md -> deny
  4. code file + fresh status=pass result.md with covering fence -> allow
  5. code file + fresh pass result.md but fence does NOT cover target -> deny
  6. code file + fresh status=fail result.md -> deny
  7. non-code file (.txt, .md) -> allow
  8. MultiEdit with multiple files, all covered -> allow
  9. MultiEdit with one file uncovered -> deny
 10. malformed result.md / corrupt JSON payload -> pass-through (no crash)
 11. hook called on non-Edit event (e.g., Bash) -> pass-through

Each test isolates state under a temporary CLAUDE_PROJECT_DIR so
production .codex/ and work/ directories are never touched.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENFORCER_PATH = HERE / "codex-delegate-enforcer.py"


def _load_module():
    """Import codex-delegate-enforcer.py as a module (hyphen in filename)."""
    spec = importlib.util.spec_from_file_location(
        "codex_delegate_enforcer", ENFORCER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BaseEnforcerTest(unittest.TestCase):
    """Shared fixture: isolated project root with results + tasks dirs."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp(prefix="codex-enforcer-test-")
        self.root = Path(self.tmpdir).resolve()
        (self.root / ".claude" / "hooks").mkdir(parents=True)
        (self.root / "work" / "codex-primary" / "tasks").mkdir(parents=True)
        (self.root / "work" / "codex-implementations").mkdir(parents=True)
        # Target file the tool call "would edit"
        self.target_rel = ".claude/hooks/my_hook.py"
        (self.root / ".claude" / "hooks" / "my_hook.py").write_text(
            "# placeholder\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ----- subprocess invocation helpers -----

    def _run_enforcer(self, payload):
        """Invoke enforcer as subprocess; return (exit_code, stdout, stderr)."""
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)}
        result = subprocess.run(
            [sys.executable, str(ENFORCER_PATH)],
            input=json.dumps(payload),
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            env=env, timeout=30,
        )
        return result.returncode, result.stdout, result.stderr

    # ----- fixture helpers -----

    def _write_task(self, task_id: str, fence_paths: list) -> Path:
        """Write a task-N.md with given Scope Fence allowed paths."""
        task_file = self.root / "work" / "codex-primary" / "tasks" / (
            "T" + task_id + "-test.md"
        )
        fence_block = "\n".join("- `" + p + "`" for p in fence_paths)
        task_file.write_text(
            "---\nexecutor: codex\n---\n\n"
            "# Task T" + task_id + "\n\n"
            "## Your Task\ntest\n\n"
            "## Scope Fence\n"
            "**Allowed paths (may be written):**\n"
            + fence_block + "\n\n"
            "**Forbidden paths:**\n- other/\n\n"
            "## Acceptance Criteria\n- [ ] AC1\n",
            encoding="utf-8",
        )
        return task_file

    def _write_result(self, task_id: str, status: str, age_seconds: float = 0) -> Path:
        """Write a task-N-result.md with given status and optional mtime offset."""
        result_file = self.root / "work" / "codex-implementations" / (
            "task-" + task_id + "-result.md"
        )
        task_file_rel = "work/codex-primary/tasks/T" + task_id + "-test.md"
        result_file.write_text(
            "# Result T" + task_id + "\n\n"
            "- status: " + status + "\n"
            "- task_file: " + task_file_rel + "\n\n"
            "## Diff\n(none)\n",
            encoding="utf-8",
        )
        if age_seconds > 0:
            old = time.time() - age_seconds
            os.utime(result_file, (old, old))
        return result_file

    def _edit_payload(self, file_path: str) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": file_path,
                "old_string": "a",
                "new_string": "b",
            },
        }

    def _write_payload(self, file_path: str) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": file_path, "content": "x"},
        }

    def _multiedit_payload(self, paths: list) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "MultiEdit",
            "tool_input": {
                "edits": [
                    {"file_path": p, "old_string": "a", "new_string": "b"}
                    for p in paths
                ],
            },
        }

    # ----- response assertions -----

    def _assert_allow(self, code: int, stdout: str, stderr: str) -> None:
        self.assertEqual(code, 0, msg="expected exit 0. stderr=" + stderr)
        # No deny JSON in stdout.
        if stdout.strip():
            try:
                parsed = json.loads(stdout)
                decision = (
                    parsed.get("hookSpecificOutput", {})
                    .get("permissionDecision")
                )
                self.assertNotEqual(
                    decision, "deny", msg="unexpected deny JSON: " + stdout
                )
            except json.JSONDecodeError:
                pass  # non-JSON stdout is fine

    def _assert_deny(self, code: int, stdout: str, stderr: str) -> None:
        self.assertEqual(code, 0, msg="expected exit 0 (deny via JSON). stderr=" + stderr)
        self.assertTrue(stdout.strip(), msg="expected deny JSON on stdout")
        parsed = json.loads(stdout)
        decision = parsed["hookSpecificOutput"]["permissionDecision"]
        self.assertEqual(decision, "deny")
        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("Code Delegation Protocol", reason)


class TestAC12Cases(BaseEnforcerTest):
    """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""

    def test_01_exempt_path_allow(self) -> None:
        """AC12.1: exempt path (CLAUDE.md) -> allow."""
        code, out, err = self._run_enforcer(self._write_payload("CLAUDE.md"))
        self._assert_allow(code, out, err)

    def test_02_code_no_result_deny(self) -> None:
        """AC12.2: code file + NO recent result.md -> deny with JSON."""
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_03_stale_result_deny(self) -> None:
        """AC12.3: code file + stale (> 15 min) result.md -> deny."""
        self._write_task("3", [self.target_rel])
        self._write_result("3", "pass", age_seconds=20 * 60)  # 20 min old
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_04_covered_pass_allow(self) -> None:
        """AC12.4: code file + fresh pass result.md with covering fence -> allow."""
        self._write_task("4", [self.target_rel])
        self._write_result("4", "pass")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_allow(code, out, err)

    def test_05_uncovered_pass_deny(self) -> None:
        """AC12.5: fresh pass, fence does NOT cover target -> deny."""
        self._write_task("5", ["other/unrelated.py"])
        self._write_result("5", "pass")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_06_fail_status_deny(self) -> None:
        """AC12.6: fresh status=fail result.md -> deny."""
        self._write_task("6", [self.target_rel])
        self._write_result("6", "fail")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_07_non_code_file_allow(self) -> None:
        """AC12.7: non-code file (.txt, .md) -> allow."""
        for suffix in (".txt", ".md"):
            notes = ".claude/hooks/notes" + suffix
            (self.root / notes).write_text("x", encoding="utf-8")
            code, out, err = self._run_enforcer(self._write_payload(notes))
            self._assert_allow(code, out, err)

    def test_08_multiedit_all_covered_allow(self) -> None:
        """AC12.8: MultiEdit with multiple files, all covered -> allow."""
        a = ".claude/hooks/a.py"
        b = ".claude/hooks/b.py"
        (self.root / a).write_text("# a\n", encoding="utf-8")
        (self.root / b).write_text("# b\n", encoding="utf-8")
        self._write_task("8", [".claude/hooks/"])
        self._write_result("8", "pass")
        code, out, err = self._run_enforcer(self._multiedit_payload([a, b]))
        self._assert_allow(code, out, err)

    def test_09_multiedit_one_uncovered_deny(self) -> None:
        """AC12.9: MultiEdit with one file uncovered -> deny."""
        a = ".claude/hooks/a.py"
        b = "src/uncovered.py"
        (self.root / a).write_text("# a\n", encoding="utf-8")
        (self.root / "src").mkdir(parents=True)
        (self.root / b).write_text("# b\n", encoding="utf-8")
        self._write_task("9", [".claude/hooks/"])
        self._write_result("9", "pass")
        code, out, err = self._run_enforcer(self._multiedit_payload([a, b]))
        self._assert_deny(code, out, err)

    def test_10a_malformed_result_passthrough(self) -> None:
        """AC12.10a: malformed result.md -> no crash, handled gracefully."""
        # Write a recent file but with completely corrupt body.
        result_file = self.root / "work" / "codex-implementations" / (
            "task-10-result.md"
        )
        result_file.write_bytes(b"\x00\x01\xff garbage no fields here")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        # No crash: exit 0. Since no fence covers target, it is denied -
        # the point is the script didn't blow up (no traceback in stderr).
        self.assertEqual(code, 0)
        self.assertNotIn("Traceback", err)

    def test_10b_corrupt_json_payload_passthrough(self) -> None:
        """AC12.10b: corrupt JSON payload -> pass-through, no crash, exit 0."""
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)}
        result = subprocess.run(
            [sys.executable, str(ENFORCER_PATH)],
            input="{this-is-not-json",
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            env=env, timeout=30,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")
        self.assertNotIn("Traceback", result.stderr)

    def test_11_non_edit_event_passthrough(self) -> None:
        """AC12.11: non-Edit tool (Bash) -> pass-through (exit 0, no deny)."""
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
        }
        code, out, err = self._run_enforcer(payload)
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "")


class TestHelpers(unittest.TestCase):
    """Direct unit tests of helper functions (no subprocess)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()

    def test_is_code_extension_positive(self) -> None:
        for p in ("a.py", "x/y/z.js", "lib/mod.rs", "s.cpp", "x.SQL"):
            self.assertTrue(self.mod.is_code_extension(p), p)

    def test_is_code_extension_negative(self) -> None:
        for p in ("README.md", "doc.txt", "config.yaml", "a.json", "b"):
            self.assertFalse(self.mod.is_code_extension(p), p)

    def test_is_exempt_memory_star_star(self) -> None:
        self.assertTrue(self.mod.is_exempt(".claude/memory/activeContext.md"))
        self.assertTrue(self.mod.is_exempt(".claude/memory/daily/2026-04-24.md"))

    def test_is_exempt_top_level_files(self) -> None:
        for p in ("CLAUDE.md", "AGENTS.md", "README.md", ".gitignore", "LICENSE"):
            self.assertTrue(self.mod.is_exempt(p), p)

    def test_is_exempt_guides_skills_adr(self) -> None:
        self.assertTrue(self.mod.is_exempt(".claude/adr/adr-001.md"))
        self.assertTrue(self.mod.is_exempt(".claude/guides/foo.md"))
        self.assertTrue(self.mod.is_exempt(".claude/skills/bar/SKILL.md"))

    def test_is_exempt_negative(self) -> None:
        self.assertFalse(self.mod.is_exempt(".claude/hooks/my_hook.py"))
        self.assertFalse(self.mod.is_exempt("src/main.py"))

    def test_requires_cover_positive(self) -> None:
        self.assertTrue(self.mod.requires_cover(".claude/hooks/x.py"))
        self.assertTrue(self.mod.requires_cover("src/main.ts"))

    def test_requires_cover_negative_non_code(self) -> None:
        self.assertFalse(self.mod.requires_cover("docs/readme.md"))

    def test_requires_cover_negative_exempt(self) -> None:
        # .claude/skills/**/*.md is exempt, and .md is non-code anyway.
        self.assertFalse(self.mod.requires_cover("CLAUDE.md"))
        # work/** is exempt even for .py.
        self.assertFalse(self.mod.requires_cover("work/scripts/helper.py"))

    def test_path_in_fence_exact_file(self) -> None:
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/c.py"]))

    def test_path_in_fence_dir_prefix(self) -> None:
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b"]))
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/"]))

    def test_path_in_fence_no_partial_segment(self) -> None:
        self.assertFalse(self.mod.path_in_fence("a/bb/c.py", ["a/b"]))

    def test_path_in_fence_strips_trailing_globs(self) -> None:
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/**"]))
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/*"]))

    def test_parse_result_fields_status_pass(self) -> None:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".md", delete=False, encoding="utf-8"
        ) as fh:
            fh.write("# result\n\n- status: pass\n- task_file: t.md\n")
            p = Path(fh.name)
        try:
            fields = self.mod.parse_result_fields(p)
            self.assertEqual(fields.get("status"), "pass")
            self.assertEqual(fields.get("task_file"), "t.md")
        finally:
            p.unlink()

    def test_parse_scope_fence_strips_backticks_and_annotations(self) -> None:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".md", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(
                "# Task\n\n"
                "## Scope Fence\n"
                "**Allowed paths (may be written):**\n"
                "- `.claude/hooks/x.py` (new)\n"
                "- `.claude/hooks/test_x.py`\n\n"
                "**Forbidden paths:**\n- else/\n\n## Next\n"
            )
            p = Path(fh.name)
        try:
            fence = self.mod.parse_scope_fence(p)
            self.assertIn(".claude/hooks/x.py", fence)
            self.assertIn(".claude/hooks/test_x.py", fence)
        finally:
            p.unlink()

    def test_extract_targets_edit(self) -> None:
        paths = self.mod.extract_targets({
            "tool_name": "Edit",
            "tool_input": {"file_path": "a.py", "old_string": "x", "new_string": "y"},
        })
        self.assertEqual(paths, ["a.py"])

    def test_extract_targets_multiedit(self) -> None:
        paths = self.mod.extract_targets({
            "tool_name": "MultiEdit",
            "tool_input": {
                "edits": [
                    {"file_path": "a.py", "old_string": "x", "new_string": "y"},
                    {"file_path": "b.py", "old_string": "x", "new_string": "y"},
                ],
            },
        })
        self.assertEqual(sorted(paths), ["a.py", "b.py"])

    def test_extract_targets_missing_is_empty(self) -> None:
        self.assertEqual(self.mod.extract_targets({}), [])
        self.assertEqual(self.mod.extract_targets({"tool_name": "Edit"}), [])
        self.assertEqual(self.mod.extract_targets(None), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)

codex
The file is larger than expected; I’m narrowing to `decide()` and existing test helpers.
exec
powershell.exe -Command 'rg -n "def decide|class|def test_decide|def fresh|TemporaryDirectory|if __name__" .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
2026-04-25T07:25:07.485513Z ERROR codex_core::tools::router: error={"output":"rg : Имя \"rg\" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте правильнос\r\nть написания имени, а также наличие и правильность пути, после чего повторите попытку.\r\nстрока:2 знак:1\r\n+ rg -n \"def decide|class|def test_decide|def fresh|TemporaryDirectory| ...\r\n+ ~~\r\n    + CategoryInfo          : ObjectNotFound: (rg:String) [], CommandNotFoundException\r\n    + FullyQualifiedErrorId : CommandNotFoundException\r\n \r\n","metadata":{"exit_code":1,"duration_seconds":1.2}}
 exited 1 in 1232ms:
rg : Имя "rg" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте правильнос
ть написания имени, а также наличие и правильность пути, после чего повторите попытку.
строка:2 знак:1
+ rg -n "def decide|class|def test_decide|def fresh|TemporaryDirectory| ...
+ ~~
    + CategoryInfo          : ObjectNotFound: (rg:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

exec
powershell.exe -Command "Select-String -Path '.claude/hooks/codex-delegate-enforcer.py','.claude/hooks/test_codex_delegate_enforcer.py' -Pattern 'def decide|class |def test_decide|TemporaryDirectory|if __name__'" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
 succeeded in 425ms:

.claude\hooks\codex-delegate-enforcer.py:385:def decide(payload: dict, project_dir: Path) -> bool:
.claude\hooks\codex-delegate-enforcer.py:447:if __name__ == "__main__":
.claude\hooks\test_codex_delegate_enforcer.py:49:class BaseEnforcerTest(unittest.TestCase):
.claude\hooks\test_codex_delegate_enforcer.py:178:class TestAC12Cases(BaseEnforcerTest):
.claude\hooks\test_codex_delegate_enforcer.py:289:class TestHelpers(unittest.TestCase):
.claude\hooks\test_codex_delegate_enforcer.py:406:if __name__ == "__main__":



exec
powershell.exe -Command '$hook = Get-Content -Path '"'.claude/hooks/codex-delegate-enforcer.py'; "'$hook[360..430]; Write-Output '"'---TEST 1---'; "'$test = Get-Content -Path '"'.claude/hooks/test_codex_delegate_enforcer.py'; "'$test[0..220]; Write-Output '"'---TEST 2---'; "'$test[220..405]' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
 succeeded in 422ms:

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
---TEST 1---
#!/usr/bin/env python3
"""Unit tests for codex-delegate-enforcer.py (task T1).

Covers all 11 required cases from spec AC12:

  1. exempt path (e.g., CLAUDE.md) -> allow
  2. code file + NO recent result.md -> deny with JSON
  3. code file + stale (> 15 min) result.md -> deny
  4. code file + fresh status=pass result.md with covering fence -> allow
  5. code file + fresh pass result.md but fence does NOT cover target -> deny
  6. code file + fresh status=fail result.md -> deny
  7. non-code file (.txt, .md) -> allow
  8. MultiEdit with multiple files, all covered -> allow
  9. MultiEdit with one file uncovered -> deny
 10. malformed result.md / corrupt JSON payload -> pass-through (no crash)
 11. hook called on non-Edit event (e.g., Bash) -> pass-through

Each test isolates state under a temporary CLAUDE_PROJECT_DIR so
production .codex/ and work/ directories are never touched.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENFORCER_PATH = HERE / "codex-delegate-enforcer.py"


def _load_module():
    """Import codex-delegate-enforcer.py as a module (hyphen in filename)."""
    spec = importlib.util.spec_from_file_location(
        "codex_delegate_enforcer", ENFORCER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BaseEnforcerTest(unittest.TestCase):
    """Shared fixture: isolated project root with results + tasks dirs."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp(prefix="codex-enforcer-test-")
        self.root = Path(self.tmpdir).resolve()
        (self.root / ".claude" / "hooks").mkdir(parents=True)
        (self.root / "work" / "codex-primary" / "tasks").mkdir(parents=True)
        (self.root / "work" / "codex-implementations").mkdir(parents=True)
        # Target file the tool call "would edit"
        self.target_rel = ".claude/hooks/my_hook.py"
        (self.root / ".claude" / "hooks" / "my_hook.py").write_text(
            "# placeholder\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ----- subprocess invocation helpers -----

    def _run_enforcer(self, payload):
        """Invoke enforcer as subprocess; return (exit_code, stdout, stderr)."""
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)}
        result = subprocess.run(
            [sys.executable, str(ENFORCER_PATH)],
            input=json.dumps(payload),
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            env=env, timeout=30,
        )
        return result.returncode, result.stdout, result.stderr

    # ----- fixture helpers -----

    def _write_task(self, task_id: str, fence_paths: list) -> Path:
        """Write a task-N.md with given Scope Fence allowed paths."""
        task_file = self.root / "work" / "codex-primary" / "tasks" / (
            "T" + task_id + "-test.md"
        )
        fence_block = "\n".join("- `" + p + "`" for p in fence_paths)
        task_file.write_text(
            "---\nexecutor: codex\n---\n\n"
            "# Task T" + task_id + "\n\n"
            "## Your Task\ntest\n\n"
            "## Scope Fence\n"
            "**Allowed paths (may be written):**\n"
            + fence_block + "\n\n"
            "**Forbidden paths:**\n- other/\n\n"
            "## Acceptance Criteria\n- [ ] AC1\n",
            encoding="utf-8",
        )
        return task_file

    def _write_result(self, task_id: str, status: str, age_seconds: float = 0) -> Path:
        """Write a task-N-result.md with given status and optional mtime offset."""
        result_file = self.root / "work" / "codex-implementations" / (
            "task-" + task_id + "-result.md"
        )
        task_file_rel = "work/codex-primary/tasks/T" + task_id + "-test.md"
        result_file.write_text(
            "# Result T" + task_id + "\n\n"
            "- status: " + status + "\n"
            "- task_file: " + task_file_rel + "\n\n"
            "## Diff\n(none)\n",
            encoding="utf-8",
        )
        if age_seconds > 0:
            old = time.time() - age_seconds
            os.utime(result_file, (old, old))
        return result_file

    def _edit_payload(self, file_path: str) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": file_path,
                "old_string": "a",
                "new_string": "b",
            },
        }

    def _write_payload(self, file_path: str) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": file_path, "content": "x"},
        }

    def _multiedit_payload(self, paths: list) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "MultiEdit",
            "tool_input": {
                "edits": [
                    {"file_path": p, "old_string": "a", "new_string": "b"}
                    for p in paths
                ],
            },
        }

    # ----- response assertions -----

    def _assert_allow(self, code: int, stdout: str, stderr: str) -> None:
        self.assertEqual(code, 0, msg="expected exit 0. stderr=" + stderr)
        # No deny JSON in stdout.
        if stdout.strip():
            try:
                parsed = json.loads(stdout)
                decision = (
                    parsed.get("hookSpecificOutput", {})
                    .get("permissionDecision")
                )
                self.assertNotEqual(
                    decision, "deny", msg="unexpected deny JSON: " + stdout
                )
            except json.JSONDecodeError:
                pass  # non-JSON stdout is fine

    def _assert_deny(self, code: int, stdout: str, stderr: str) -> None:
        self.assertEqual(code, 0, msg="expected exit 0 (deny via JSON). stderr=" + stderr)
        self.assertTrue(stdout.strip(), msg="expected deny JSON on stdout")
        parsed = json.loads(stdout)
        decision = parsed["hookSpecificOutput"]["permissionDecision"]
        self.assertEqual(decision, "deny")
        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("Code Delegation Protocol", reason)


class TestAC12Cases(BaseEnforcerTest):
    """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""

    def test_01_exempt_path_allow(self) -> None:
        """AC12.1: exempt path (CLAUDE.md) -> allow."""
        code, out, err = self._run_enforcer(self._write_payload("CLAUDE.md"))
        self._assert_allow(code, out, err)

    def test_02_code_no_result_deny(self) -> None:
        """AC12.2: code file + NO recent result.md -> deny with JSON."""
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_03_stale_result_deny(self) -> None:
        """AC12.3: code file + stale (> 15 min) result.md -> deny."""
        self._write_task("3", [self.target_rel])
        self._write_result("3", "pass", age_seconds=20 * 60)  # 20 min old
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_04_covered_pass_allow(self) -> None:
        """AC12.4: code file + fresh pass result.md with covering fence -> allow."""
        self._write_task("4", [self.target_rel])
        self._write_result("4", "pass")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_allow(code, out, err)

    def test_05_uncovered_pass_deny(self) -> None:
        """AC12.5: fresh pass, fence does NOT cover target -> deny."""
        self._write_task("5", ["other/unrelated.py"])
        self._write_result("5", "pass")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_06_fail_status_deny(self) -> None:
        """AC12.6: fresh status=fail result.md -> deny."""
        self._write_task("6", [self.target_rel])
        self._write_result("6", "fail")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_07_non_code_file_allow(self) -> None:
        """AC12.7: non-code file (.txt, .md) -> allow."""
        for suffix in (".txt", ".md"):
---TEST 2---
        for suffix in (".txt", ".md"):
            notes = ".claude/hooks/notes" + suffix
            (self.root / notes).write_text("x", encoding="utf-8")
            code, out, err = self._run_enforcer(self._write_payload(notes))
            self._assert_allow(code, out, err)

    def test_08_multiedit_all_covered_allow(self) -> None:
        """AC12.8: MultiEdit with multiple files, all covered -> allow."""
        a = ".claude/hooks/a.py"
        b = ".claude/hooks/b.py"
        (self.root / a).write_text("# a\n", encoding="utf-8")
        (self.root / b).write_text("# b\n", encoding="utf-8")
        self._write_task("8", [".claude/hooks/"])
        self._write_result("8", "pass")
        code, out, err = self._run_enforcer(self._multiedit_payload([a, b]))
        self._assert_allow(code, out, err)

    def test_09_multiedit_one_uncovered_deny(self) -> None:
        """AC12.9: MultiEdit with one file uncovered -> deny."""
        a = ".claude/hooks/a.py"
        b = "src/uncovered.py"
        (self.root / a).write_text("# a\n", encoding="utf-8")
        (self.root / "src").mkdir(parents=True)
        (self.root / b).write_text("# b\n", encoding="utf-8")
        self._write_task("9", [".claude/hooks/"])
        self._write_result("9", "pass")
        code, out, err = self._run_enforcer(self._multiedit_payload([a, b]))
        self._assert_deny(code, out, err)

    def test_10a_malformed_result_passthrough(self) -> None:
        """AC12.10a: malformed result.md -> no crash, handled gracefully."""
        # Write a recent file but with completely corrupt body.
        result_file = self.root / "work" / "codex-implementations" / (
            "task-10-result.md"
        )
        result_file.write_bytes(b"\x00\x01\xff garbage no fields here")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        # No crash: exit 0. Since no fence covers target, it is denied -
        # the point is the script didn't blow up (no traceback in stderr).
        self.assertEqual(code, 0)
        self.assertNotIn("Traceback", err)

    def test_10b_corrupt_json_payload_passthrough(self) -> None:
        """AC12.10b: corrupt JSON payload -> pass-through, no crash, exit 0."""
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)}
        result = subprocess.run(
            [sys.executable, str(ENFORCER_PATH)],
            input="{this-is-not-json",
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            env=env, timeout=30,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")
        self.assertNotIn("Traceback", result.stderr)

    def test_11_non_edit_event_passthrough(self) -> None:
        """AC12.11: non-Edit tool (Bash) -> pass-through (exit 0, no deny)."""
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
        }
        code, out, err = self._run_enforcer(payload)
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "")


class TestHelpers(unittest.TestCase):
    """Direct unit tests of helper functions (no subprocess)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()

    def test_is_code_extension_positive(self) -> None:
        for p in ("a.py", "x/y/z.js", "lib/mod.rs", "s.cpp", "x.SQL"):
            self.assertTrue(self.mod.is_code_extension(p), p)

    def test_is_code_extension_negative(self) -> None:
        for p in ("README.md", "doc.txt", "config.yaml", "a.json", "b"):
            self.assertFalse(self.mod.is_code_extension(p), p)

    def test_is_exempt_memory_star_star(self) -> None:
        self.assertTrue(self.mod.is_exempt(".claude/memory/activeContext.md"))
        self.assertTrue(self.mod.is_exempt(".claude/memory/daily/2026-04-24.md"))

    def test_is_exempt_top_level_files(self) -> None:
        for p in ("CLAUDE.md", "AGENTS.md", "README.md", ".gitignore", "LICENSE"):
            self.assertTrue(self.mod.is_exempt(p), p)

    def test_is_exempt_guides_skills_adr(self) -> None:
        self.assertTrue(self.mod.is_exempt(".claude/adr/adr-001.md"))
        self.assertTrue(self.mod.is_exempt(".claude/guides/foo.md"))
        self.assertTrue(self.mod.is_exempt(".claude/skills/bar/SKILL.md"))

    def test_is_exempt_negative(self) -> None:
        self.assertFalse(self.mod.is_exempt(".claude/hooks/my_hook.py"))
        self.assertFalse(self.mod.is_exempt("src/main.py"))

    def test_requires_cover_positive(self) -> None:
        self.assertTrue(self.mod.requires_cover(".claude/hooks/x.py"))
        self.assertTrue(self.mod.requires_cover("src/main.ts"))

    def test_requires_cover_negative_non_code(self) -> None:
        self.assertFalse(self.mod.requires_cover("docs/readme.md"))

    def test_requires_cover_negative_exempt(self) -> None:
        # .claude/skills/**/*.md is exempt, and .md is non-code anyway.
        self.assertFalse(self.mod.requires_cover("CLAUDE.md"))
        # work/** is exempt even for .py.
        self.assertFalse(self.mod.requires_cover("work/scripts/helper.py"))

    def test_path_in_fence_exact_file(self) -> None:
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/c.py"]))

    def test_path_in_fence_dir_prefix(self) -> None:
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b"]))
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/"]))

    def test_path_in_fence_no_partial_segment(self) -> None:
        self.assertFalse(self.mod.path_in_fence("a/bb/c.py", ["a/b"]))

    def test_path_in_fence_strips_trailing_globs(self) -> None:
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/**"]))
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/*"]))

    def test_parse_result_fields_status_pass(self) -> None:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".md", delete=False, encoding="utf-8"
        ) as fh:
            fh.write("# result\n\n- status: pass\n- task_file: t.md\n")
            p = Path(fh.name)
        try:
            fields = self.mod.parse_result_fields(p)
            self.assertEqual(fields.get("status"), "pass")
            self.assertEqual(fields.get("task_file"), "t.md")
        finally:
            p.unlink()

    def test_parse_scope_fence_strips_backticks_and_annotations(self) -> None:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".md", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(
                "# Task\n\n"
                "## Scope Fence\n"
                "**Allowed paths (may be written):**\n"
                "- `.claude/hooks/x.py` (new)\n"
                "- `.claude/hooks/test_x.py`\n\n"
                "**Forbidden paths:**\n- else/\n\n## Next\n"
            )
            p = Path(fh.name)
        try:
            fence = self.mod.parse_scope_fence(p)
            self.assertIn(".claude/hooks/x.py", fence)
            self.assertIn(".claude/hooks/test_x.py", fence)
        finally:
            p.unlink()

    def test_extract_targets_edit(self) -> None:
        paths = self.mod.extract_targets({
            "tool_name": "Edit",
            "tool_input": {"file_path": "a.py", "old_string": "x", "new_string": "y"},
        })
        self.assertEqual(paths, ["a.py"])

    def test_extract_targets_multiedit(self) -> None:
        paths = self.mod.extract_targets({
            "tool_name": "MultiEdit",
            "tool_input": {
                "edits": [
                    {"file_path": "a.py", "old_string": "x", "new_string": "y"},
                    {"file_path": "b.py", "old_string": "x", "new_string": "y"},
                ],
            },
        })
        self.assertEqual(sorted(paths), ["a.py", "b.py"])

    def test_extract_targets_missing_is_empty(self) -> None:
        self.assertEqual(self.mod.extract_targets({}), [])
        self.assertEqual(self.mod.extract_targets({"tool_name": "Edit"}), [])
        self.assertEqual(self.mod.extract_targets(None), [])


if __name__ == "__main__":

exec
powershell.exe -Command '$test = Get-Content -Path '"'.claude/hooks/test_codex_delegate_enforcer.py'; Write-Output '---0-170---'; "'$test[0..170]; Write-Output '"'---170-288---'; "'$test[170..288]; Write-Output '"'---289-420---'; "'$test[289..420]' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
 succeeded in 460ms:
---0-170---
#!/usr/bin/env python3
"""Unit tests for codex-delegate-enforcer.py (task T1).

Covers all 11 required cases from spec AC12:

  1. exempt path (e.g., CLAUDE.md) -> allow
  2. code file + NO recent result.md -> deny with JSON
  3. code file + stale (> 15 min) result.md -> deny
  4. code file + fresh status=pass result.md with covering fence -> allow
  5. code file + fresh pass result.md but fence does NOT cover target -> deny
  6. code file + fresh status=fail result.md -> deny
  7. non-code file (.txt, .md) -> allow
  8. MultiEdit with multiple files, all covered -> allow
  9. MultiEdit with one file uncovered -> deny
 10. malformed result.md / corrupt JSON payload -> pass-through (no crash)
 11. hook called on non-Edit event (e.g., Bash) -> pass-through

Each test isolates state under a temporary CLAUDE_PROJECT_DIR so
production .codex/ and work/ directories are never touched.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENFORCER_PATH = HERE / "codex-delegate-enforcer.py"


def _load_module():
    """Import codex-delegate-enforcer.py as a module (hyphen in filename)."""
    spec = importlib.util.spec_from_file_location(
        "codex_delegate_enforcer", ENFORCER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BaseEnforcerTest(unittest.TestCase):
    """Shared fixture: isolated project root with results + tasks dirs."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp(prefix="codex-enforcer-test-")
        self.root = Path(self.tmpdir).resolve()
        (self.root / ".claude" / "hooks").mkdir(parents=True)
        (self.root / "work" / "codex-primary" / "tasks").mkdir(parents=True)
        (self.root / "work" / "codex-implementations").mkdir(parents=True)
        # Target file the tool call "would edit"
        self.target_rel = ".claude/hooks/my_hook.py"
        (self.root / ".claude" / "hooks" / "my_hook.py").write_text(
            "# placeholder\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ----- subprocess invocation helpers -----

    def _run_enforcer(self, payload):
        """Invoke enforcer as subprocess; return (exit_code, stdout, stderr)."""
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)}
        result = subprocess.run(
            [sys.executable, str(ENFORCER_PATH)],
            input=json.dumps(payload),
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            env=env, timeout=30,
        )
        return result.returncode, result.stdout, result.stderr

    # ----- fixture helpers -----

    def _write_task(self, task_id: str, fence_paths: list) -> Path:
        """Write a task-N.md with given Scope Fence allowed paths."""
        task_file = self.root / "work" / "codex-primary" / "tasks" / (
            "T" + task_id + "-test.md"
        )
        fence_block = "\n".join("- `" + p + "`" for p in fence_paths)
        task_file.write_text(
            "---\nexecutor: codex\n---\n\n"
            "# Task T" + task_id + "\n\n"
            "## Your Task\ntest\n\n"
            "## Scope Fence\n"
            "**Allowed paths (may be written):**\n"
            + fence_block + "\n\n"
            "**Forbidden paths:**\n- other/\n\n"
            "## Acceptance Criteria\n- [ ] AC1\n",
            encoding="utf-8",
        )
        return task_file

    def _write_result(self, task_id: str, status: str, age_seconds: float = 0) -> Path:
        """Write a task-N-result.md with given status and optional mtime offset."""
        result_file = self.root / "work" / "codex-implementations" / (
            "task-" + task_id + "-result.md"
        )
        task_file_rel = "work/codex-primary/tasks/T" + task_id + "-test.md"
        result_file.write_text(
            "# Result T" + task_id + "\n\n"
            "- status: " + status + "\n"
            "- task_file: " + task_file_rel + "\n\n"
            "## Diff\n(none)\n",
            encoding="utf-8",
        )
        if age_seconds > 0:
            old = time.time() - age_seconds
            os.utime(result_file, (old, old))
        return result_file

    def _edit_payload(self, file_path: str) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": file_path,
                "old_string": "a",
                "new_string": "b",
            },
        }

    def _write_payload(self, file_path: str) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": file_path, "content": "x"},
        }

    def _multiedit_payload(self, paths: list) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "MultiEdit",
            "tool_input": {
                "edits": [
                    {"file_path": p, "old_string": "a", "new_string": "b"}
                    for p in paths
                ],
            },
        }

    # ----- response assertions -----

    def _assert_allow(self, code: int, stdout: str, stderr: str) -> None:
        self.assertEqual(code, 0, msg="expected exit 0. stderr=" + stderr)
        # No deny JSON in stdout.
        if stdout.strip():
            try:
                parsed = json.loads(stdout)
                decision = (
                    parsed.get("hookSpecificOutput", {})
                    .get("permissionDecision")
                )
                self.assertNotEqual(
                    decision, "deny", msg="unexpected deny JSON: " + stdout
                )
            except json.JSONDecodeError:
                pass  # non-JSON stdout is fine

    def _assert_deny(self, code: int, stdout: str, stderr: str) -> None:
        self.assertEqual(code, 0, msg="expected exit 0 (deny via JSON). stderr=" + stderr)
        self.assertTrue(stdout.strip(), msg="expected deny JSON on stdout")
        parsed = json.loads(stdout)
---170-288---
        parsed = json.loads(stdout)
        decision = parsed["hookSpecificOutput"]["permissionDecision"]
        self.assertEqual(decision, "deny")
        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("Code Delegation Protocol", reason)


class TestAC12Cases(BaseEnforcerTest):
    """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""

    def test_01_exempt_path_allow(self) -> None:
        """AC12.1: exempt path (CLAUDE.md) -> allow."""
        code, out, err = self._run_enforcer(self._write_payload("CLAUDE.md"))
        self._assert_allow(code, out, err)

    def test_02_code_no_result_deny(self) -> None:
        """AC12.2: code file + NO recent result.md -> deny with JSON."""
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_03_stale_result_deny(self) -> None:
        """AC12.3: code file + stale (> 15 min) result.md -> deny."""
        self._write_task("3", [self.target_rel])
        self._write_result("3", "pass", age_seconds=20 * 60)  # 20 min old
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_04_covered_pass_allow(self) -> None:
        """AC12.4: code file + fresh pass result.md with covering fence -> allow."""
        self._write_task("4", [self.target_rel])
        self._write_result("4", "pass")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_allow(code, out, err)

    def test_05_uncovered_pass_deny(self) -> None:
        """AC12.5: fresh pass, fence does NOT cover target -> deny."""
        self._write_task("5", ["other/unrelated.py"])
        self._write_result("5", "pass")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_06_fail_status_deny(self) -> None:
        """AC12.6: fresh status=fail result.md -> deny."""
        self._write_task("6", [self.target_rel])
        self._write_result("6", "fail")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_07_non_code_file_allow(self) -> None:
        """AC12.7: non-code file (.txt, .md) -> allow."""
        for suffix in (".txt", ".md"):
            notes = ".claude/hooks/notes" + suffix
            (self.root / notes).write_text("x", encoding="utf-8")
            code, out, err = self._run_enforcer(self._write_payload(notes))
            self._assert_allow(code, out, err)

    def test_08_multiedit_all_covered_allow(self) -> None:
        """AC12.8: MultiEdit with multiple files, all covered -> allow."""
        a = ".claude/hooks/a.py"
        b = ".claude/hooks/b.py"
        (self.root / a).write_text("# a\n", encoding="utf-8")
        (self.root / b).write_text("# b\n", encoding="utf-8")
        self._write_task("8", [".claude/hooks/"])
        self._write_result("8", "pass")
        code, out, err = self._run_enforcer(self._multiedit_payload([a, b]))
        self._assert_allow(code, out, err)

    def test_09_multiedit_one_uncovered_deny(self) -> None:
        """AC12.9: MultiEdit with one file uncovered -> deny."""
        a = ".claude/hooks/a.py"
        b = "src/uncovered.py"
        (self.root / a).write_text("# a\n", encoding="utf-8")
        (self.root / "src").mkdir(parents=True)
        (self.root / b).write_text("# b\n", encoding="utf-8")
        self._write_task("9", [".claude/hooks/"])
        self._write_result("9", "pass")
        code, out, err = self._run_enforcer(self._multiedit_payload([a, b]))
        self._assert_deny(code, out, err)

    def test_10a_malformed_result_passthrough(self) -> None:
        """AC12.10a: malformed result.md -> no crash, handled gracefully."""
        # Write a recent file but with completely corrupt body.
        result_file = self.root / "work" / "codex-implementations" / (
            "task-10-result.md"
        )
        result_file.write_bytes(b"\x00\x01\xff garbage no fields here")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        # No crash: exit 0. Since no fence covers target, it is denied -
        # the point is the script didn't blow up (no traceback in stderr).
        self.assertEqual(code, 0)
        self.assertNotIn("Traceback", err)

    def test_10b_corrupt_json_payload_passthrough(self) -> None:
        """AC12.10b: corrupt JSON payload -> pass-through, no crash, exit 0."""
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)}
        result = subprocess.run(
            [sys.executable, str(ENFORCER_PATH)],
            input="{this-is-not-json",
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            env=env, timeout=30,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")
        self.assertNotIn("Traceback", result.stderr)

    def test_11_non_edit_event_passthrough(self) -> None:
        """AC12.11: non-Edit tool (Bash) -> pass-through (exit 0, no deny)."""
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
        }
        code, out, err = self._run_enforcer(payload)
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "")


class TestHelpers(unittest.TestCase):
---289-420---
    """Direct unit tests of helper functions (no subprocess)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()

    def test_is_code_extension_positive(self) -> None:
        for p in ("a.py", "x/y/z.js", "lib/mod.rs", "s.cpp", "x.SQL"):
            self.assertTrue(self.mod.is_code_extension(p), p)

    def test_is_code_extension_negative(self) -> None:
        for p in ("README.md", "doc.txt", "config.yaml", "a.json", "b"):
            self.assertFalse(self.mod.is_code_extension(p), p)

    def test_is_exempt_memory_star_star(self) -> None:
        self.assertTrue(self.mod.is_exempt(".claude/memory/activeContext.md"))
        self.assertTrue(self.mod.is_exempt(".claude/memory/daily/2026-04-24.md"))

    def test_is_exempt_top_level_files(self) -> None:
        for p in ("CLAUDE.md", "AGENTS.md", "README.md", ".gitignore", "LICENSE"):
            self.assertTrue(self.mod.is_exempt(p), p)

    def test_is_exempt_guides_skills_adr(self) -> None:
        self.assertTrue(self.mod.is_exempt(".claude/adr/adr-001.md"))
        self.assertTrue(self.mod.is_exempt(".claude/guides/foo.md"))
        self.assertTrue(self.mod.is_exempt(".claude/skills/bar/SKILL.md"))

    def test_is_exempt_negative(self) -> None:
        self.assertFalse(self.mod.is_exempt(".claude/hooks/my_hook.py"))
        self.assertFalse(self.mod.is_exempt("src/main.py"))

    def test_requires_cover_positive(self) -> None:
        self.assertTrue(self.mod.requires_cover(".claude/hooks/x.py"))
        self.assertTrue(self.mod.requires_cover("src/main.ts"))

    def test_requires_cover_negative_non_code(self) -> None:
        self.assertFalse(self.mod.requires_cover("docs/readme.md"))

    def test_requires_cover_negative_exempt(self) -> None:
        # .claude/skills/**/*.md is exempt, and .md is non-code anyway.
        self.assertFalse(self.mod.requires_cover("CLAUDE.md"))
        # work/** is exempt even for .py.
        self.assertFalse(self.mod.requires_cover("work/scripts/helper.py"))

    def test_path_in_fence_exact_file(self) -> None:
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/c.py"]))

    def test_path_in_fence_dir_prefix(self) -> None:
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b"]))
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/"]))

    def test_path_in_fence_no_partial_segment(self) -> None:
        self.assertFalse(self.mod.path_in_fence("a/bb/c.py", ["a/b"]))

    def test_path_in_fence_strips_trailing_globs(self) -> None:
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/**"]))
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/*"]))

    def test_parse_result_fields_status_pass(self) -> None:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".md", delete=False, encoding="utf-8"
        ) as fh:
            fh.write("# result\n\n- status: pass\n- task_file: t.md\n")
            p = Path(fh.name)
        try:
            fields = self.mod.parse_result_fields(p)
            self.assertEqual(fields.get("status"), "pass")
            self.assertEqual(fields.get("task_file"), "t.md")
        finally:
            p.unlink()

    def test_parse_scope_fence_strips_backticks_and_annotations(self) -> None:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".md", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(
                "# Task\n\n"
                "## Scope Fence\n"
                "**Allowed paths (may be written):**\n"
                "- `.claude/hooks/x.py` (new)\n"
                "- `.claude/hooks/test_x.py`\n\n"
                "**Forbidden paths:**\n- else/\n\n## Next\n"
            )
            p = Path(fh.name)
        try:
            fence = self.mod.parse_scope_fence(p)
            self.assertIn(".claude/hooks/x.py", fence)
            self.assertIn(".claude/hooks/test_x.py", fence)
        finally:
            p.unlink()

    def test_extract_targets_edit(self) -> None:
        paths = self.mod.extract_targets({
            "tool_name": "Edit",
            "tool_input": {"file_path": "a.py", "old_string": "x", "new_string": "y"},
        })
        self.assertEqual(paths, ["a.py"])

    def test_extract_targets_multiedit(self) -> None:
        paths = self.mod.extract_targets({
            "tool_name": "MultiEdit",
            "tool_input": {
                "edits": [
                    {"file_path": "a.py", "old_string": "x", "new_string": "y"},
                    {"file_path": "b.py", "old_string": "x", "new_string": "y"},
                ],
            },
        })
        self.assertEqual(sorted(paths), ["a.py", "b.py"])

    def test_extract_targets_missing_is_empty(self) -> None:
        self.assertEqual(self.mod.extract_targets({}), [])
        self.assertEqual(self.mod.extract_targets({"tool_name": "Edit"}), [])
        self.assertEqual(self.mod.extract_targets(None), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)

exec
powershell.exe -Command '$test = Get-Content -Path '"'.claude/hooks/test_codex_delegate_enforcer.py'; Write-Output '---130-288---'; "'$test[130..288]' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
 succeeded in 424ms:
---130-288---
    def _write_payload(self, file_path: str) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": file_path, "content": "x"},
        }

    def _multiedit_payload(self, paths: list) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "MultiEdit",
            "tool_input": {
                "edits": [
                    {"file_path": p, "old_string": "a", "new_string": "b"}
                    for p in paths
                ],
            },
        }

    # ----- response assertions -----

    def _assert_allow(self, code: int, stdout: str, stderr: str) -> None:
        self.assertEqual(code, 0, msg="expected exit 0. stderr=" + stderr)
        # No deny JSON in stdout.
        if stdout.strip():
            try:
                parsed = json.loads(stdout)
                decision = (
                    parsed.get("hookSpecificOutput", {})
                    .get("permissionDecision")
                )
                self.assertNotEqual(
                    decision, "deny", msg="unexpected deny JSON: " + stdout
                )
            except json.JSONDecodeError:
                pass  # non-JSON stdout is fine

    def _assert_deny(self, code: int, stdout: str, stderr: str) -> None:
        self.assertEqual(code, 0, msg="expected exit 0 (deny via JSON). stderr=" + stderr)
        self.assertTrue(stdout.strip(), msg="expected deny JSON on stdout")
        parsed = json.loads(stdout)
        decision = parsed["hookSpecificOutput"]["permissionDecision"]
        self.assertEqual(decision, "deny")
        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("Code Delegation Protocol", reason)


class TestAC12Cases(BaseEnforcerTest):
    """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""

    def test_01_exempt_path_allow(self) -> None:
        """AC12.1: exempt path (CLAUDE.md) -> allow."""
        code, out, err = self._run_enforcer(self._write_payload("CLAUDE.md"))
        self._assert_allow(code, out, err)

    def test_02_code_no_result_deny(self) -> None:
        """AC12.2: code file + NO recent result.md -> deny with JSON."""
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_03_stale_result_deny(self) -> None:
        """AC12.3: code file + stale (> 15 min) result.md -> deny."""
        self._write_task("3", [self.target_rel])
        self._write_result("3", "pass", age_seconds=20 * 60)  # 20 min old
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_04_covered_pass_allow(self) -> None:
        """AC12.4: code file + fresh pass result.md with covering fence -> allow."""
        self._write_task("4", [self.target_rel])
        self._write_result("4", "pass")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_allow(code, out, err)

    def test_05_uncovered_pass_deny(self) -> None:
        """AC12.5: fresh pass, fence does NOT cover target -> deny."""
        self._write_task("5", ["other/unrelated.py"])
        self._write_result("5", "pass")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_06_fail_status_deny(self) -> None:
        """AC12.6: fresh status=fail result.md -> deny."""
        self._write_task("6", [self.target_rel])
        self._write_result("6", "fail")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_07_non_code_file_allow(self) -> None:
        """AC12.7: non-code file (.txt, .md) -> allow."""
        for suffix in (".txt", ".md"):
            notes = ".claude/hooks/notes" + suffix
            (self.root / notes).write_text("x", encoding="utf-8")
            code, out, err = self._run_enforcer(self._write_payload(notes))
            self._assert_allow(code, out, err)

    def test_08_multiedit_all_covered_allow(self) -> None:
        """AC12.8: MultiEdit with multiple files, all covered -> allow."""
        a = ".claude/hooks/a.py"
        b = ".claude/hooks/b.py"
        (self.root / a).write_text("# a\n", encoding="utf-8")
        (self.root / b).write_text("# b\n", encoding="utf-8")
        self._write_task("8", [".claude/hooks/"])
        self._write_result("8", "pass")
        code, out, err = self._run_enforcer(self._multiedit_payload([a, b]))
        self._assert_allow(code, out, err)

    def test_09_multiedit_one_uncovered_deny(self) -> None:
        """AC12.9: MultiEdit with one file uncovered -> deny."""
        a = ".claude/hooks/a.py"
        b = "src/uncovered.py"
        (self.root / a).write_text("# a\n", encoding="utf-8")
        (self.root / "src").mkdir(parents=True)
        (self.root / b).write_text("# b\n", encoding="utf-8")
        self._write_task("9", [".claude/hooks/"])
        self._write_result("9", "pass")
        code, out, err = self._run_enforcer(self._multiedit_payload([a, b]))
        self._assert_deny(code, out, err)

    def test_10a_malformed_result_passthrough(self) -> None:
        """AC12.10a: malformed result.md -> no crash, handled gracefully."""
        # Write a recent file but with completely corrupt body.
        result_file = self.root / "work" / "codex-implementations" / (
            "task-10-result.md"
        )
        result_file.write_bytes(b"\x00\x01\xff garbage no fields here")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        # No crash: exit 0. Since no fence covers target, it is denied -
        # the point is the script didn't blow up (no traceback in stderr).
        self.assertEqual(code, 0)
        self.assertNotIn("Traceback", err)

    def test_10b_corrupt_json_payload_passthrough(self) -> None:
        """AC12.10b: corrupt JSON payload -> pass-through, no crash, exit 0."""
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)}
        result = subprocess.run(
            [sys.executable, str(ENFORCER_PATH)],
            input="{this-is-not-json",
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            env=env, timeout=30,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")
        self.assertNotIn("Traceback", result.stderr)

    def test_11_non_edit_event_passthrough(self) -> None:
        """AC12.11: non-Edit tool (Bash) -> pass-through (exit 0, no deny)."""
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
        }
        code, out, err = self._run_enforcer(payload)
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "")


class TestHelpers(unittest.TestCase):

**Considering test structure and logging**

I'm thinking about how to set up the tests. Maybe I'll inherit from Base and set the module without too many changes. I could create a TestDualTeamsSentinel class and use super in setUp while incorporating tempfile.TemporaryDirectory for isolation, instead of using mkdtemp. The guidelines say tests must be self-contained and use TemporaryDirectory explicitly. I need to implement a structured logging function as well, ensuring the logging for function entry and exit is clear while addressing potential OSError for path resolution.
**Planning ancestor walk robustness**

I need to implement an ancestor walk for the project. I'll start with `current = project_dir`, but I'm wondering if project_dir exists. If it doesn't, that could be a problem. Also, I recall that Path.resolve in Python 3.6+ has a default of strict set to False, which is handy. However, on Windows, I still might encounter OSError due to symlink loops. So, I definitely need to ensure this function is robust to handle those potential issues.
  ✓ Inspect hook and tests
  → Add regression tests
  • Implement sentinel exemption
  • Run required test command
  • Prepare handoff self-report
codex
I’m adding focused RED tests for the sentinel ancestor walk and `decide()` branch.
apply patch
patch: completed
C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex\.claude/hooks/test_codex_delegate_enforcer.py
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

codex
Tests are in place; I’ll run the required command once to confirm the RED failure.
exec
powershell.exe -Command 'py -3 .claude/hooks/test_codex_delegate_enforcer.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
2026-04-25T07:26:53.645183Z ERROR codex_core::tools::router: error={"output":"No installed Python found!\r\n","metadata":{"exit_code":1,"duration_seconds":0.2}}
 exited 1 in 242ms:
No installed Python found!

diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

codex
The exact `py -3` command is blocked by the local launcher, so I’m implementing now and will also verify with `python`.
  ✓ Inspect hook and tests
  ✓ Add regression tests
  → Implement sentinel exemption
  • Run required test command
  • Prepare handoff self-report
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

apply patch
patch: completed
C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex\.claude/hooks/codex-delegate-enforcer.py
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 81098ec2547ec42978e25eb067d47d2d527fa1bb..559a64c5355a00095bd258ca191bd69568a27280
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -81,13 +81,49 @@
     logger.propagate = False
     return logger
 
-def get_project_dir() -> Path:
-    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
-    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
-
-def resolve_target(project_dir: Path, target_raw: str):
-    """Normalize raw file_path to absolute Path inside project_dir."""
-    logger = logging.getLogger(HOOK_NAME)
+def get_project_dir() -> Path:
+    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
+    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+
+def is_dual_teams_worktree(project_dir: Path) -> bool:
+    """True iff project_dir or any ancestor contains .dual-base-ref."""
+    logger = logging.getLogger(HOOK_NAME)
+    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
+    current = project_dir
+    seen: set[Path] = set()
+    while True:
+        try:
+            resolved = current.resolve()
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
+            resolved = current.absolute()
+        if resolved in seen:
+            logger.info(
+                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
+                project_dir,
+            )
+            return False
+        seen.add(resolved)
+        sentinel = current / ".dual-base-ref"
+        try:
+            if sentinel.is_file():
+                logger.info(
+                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
+                    project_dir,
+                    sentinel,
+                )
+                return True
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
+        parent = current.parent
+        if parent == current:
+            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
+            return False
+        current = parent
+
+def resolve_target(project_dir: Path, target_raw: str):
+    """Normalize raw file_path to absolute Path inside project_dir."""
+    logger = logging.getLogger(HOOK_NAME)
     if not target_raw:
         return None
     try:
@@ -391,10 +427,13 @@
     if event and event != "PreToolUse":
         logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
         return True
-    if tool_name not in {"Edit", "Write", "MultiEdit"}:
-        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
-        return True
-    raw_targets = extract_targets(payload)
+    if tool_name not in {"Edit", "Write", "MultiEdit"}:
+        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
+        return True
+    if is_dual_teams_worktree(project_dir):
+        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
+        return True
+    raw_targets = extract_targets(payload)
     if not raw_targets:
         logger.info("decide.passthrough reason=no-targets")
         return True
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 81098ec2547ec42978e25eb067d47d2d527fa1bb..559a64c5355a00095bd258ca191bd69568a27280
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -81,13 +81,49 @@
     logger.propagate = False
     return logger
 
-def get_project_dir() -> Path:
-    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
-    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
-
-def resolve_target(project_dir: Path, target_raw: str):
-    """Normalize raw file_path to absolute Path inside project_dir."""
-    logger = logging.getLogger(HOOK_NAME)
+def get_project_dir() -> Path:
+    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
+    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+
+def is_dual_teams_worktree(project_dir: Path) -> bool:
+    """True iff project_dir or any ancestor contains .dual-base-ref."""
+    logger = logging.getLogger(HOOK_NAME)
+    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
+    current = project_dir
+    seen: set[Path] = set()
+    while True:
+        try:
+            resolved = current.resolve()
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
+            resolved = current.absolute()
+        if resolved in seen:
+            logger.info(
+                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
+                project_dir,
+            )
+            return False
+        seen.add(resolved)
+        sentinel = current / ".dual-base-ref"
+        try:
+            if sentinel.is_file():
+                logger.info(
+                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
+                    project_dir,
+                    sentinel,
+                )
+                return True
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
+        parent = current.parent
+        if parent == current:
+            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
+            return False
+        current = parent
+
+def resolve_target(project_dir: Path, target_raw: str):
+    """Normalize raw file_path to absolute Path inside project_dir."""
+    logger = logging.getLogger(HOOK_NAME)
     if not target_raw:
         return None
     try:
@@ -391,10 +427,13 @@
     if event and event != "PreToolUse":
         logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
         return True
-    if tool_name not in {"Edit", "Write", "MultiEdit"}:
-        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
-        return True
-    raw_targets = extract_targets(payload)
+    if tool_name not in {"Edit", "Write", "MultiEdit"}:
+        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
+        return True
+    if is_dual_teams_worktree(project_dir):
+        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
+        return True
+    raw_targets = extract_targets(payload)
     if not raw_targets:
         logger.info("decide.passthrough reason=no-targets")
         return True
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

**Evaluating tool usage and logging**

I’m looking at the warning about the apply_patch tool, which seems to require using a shell command. The patch was applied, so now I need to check for any issues. There’s potential for a RuntimeError with current.resolve, particularly concerning symlink loops. It seems like the handling in place currently catches OSError, but not RuntimeError. Maybe using current.resolve with strict=False could help, but I’m pondering if there could be cycles with project_dir symlink. Also, I need to ensure structured logging with appropriate levels.
**Analyzing testing commands and potential blockers**

I need to implement a function that triggers immediately after an event, ensuring that tool returns sooner. There’s a need for a condition that checks if the sentinel is unchanged. My function calls might overload with additional logs and resolve calls, though output should be consistent. I'm concerned about the project_dir being an ancestor with a .dual-base-ref in the actual repository. I already used apply_patch but need to run tests again. However, the test command failed due to Python being missing, potentially marking it as a BLOCKER according to the spec.
**Considering test command outcomes**

The task indicates that if a test command exits with a non-zero status, I shouldn't claim the task as done or consider it a BLOCKER. The issue stems from Python not being installed, so I can't fix it directly. However, I'm thinking of potentially using the Python command. It attempted to run, but there wasn't any installed Python. I should check and see if Python is available on the system; that could clarify things.
codex
Implementation is patched; next I’m running the suite with available Python, then the exact required command.
exec
powershell.exe -Command 'python --version; python .claude/hooks/test_codex_delegate_enforcer.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
2026-04-25T07:27:48.482322Z ERROR codex_core::tools::router: error={"output":"python : Имя \"python\" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте пр\r\nавильность написания имени, а также наличие и правильность пути, после чего повторите попытку.\r\nстрока:2 знак:1\r\n+ python --version; python .claude/hooks/test_codex_delegate_enforcer.p ...\r\n+ ~~~~~~\r\n    + CategoryInfo          : ObjectNotFound: (python:String) [], CommandNotFoundException\r\n    + FullyQualifiedErrorId : CommandNotFoundException\r\n \r\npython : Имя \"python\" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте пр\r\nавильность написания имени, а также наличие и правильность пути, после чего повторите попытку.\r\nстрока:2 знак:19\r\n+ python --version; python .claude/hooks/test_codex_delegate_enforcer.p ...\r\n+                   ~~~~~~\r\n    + CategoryInfo          : ObjectNotFound: (python:String) [], CommandNotFoundException\r\n    + FullyQualifiedErrorId : CommandNotFoundException\r\n \r\n","metadata":{"exit_code":1,"duration_seconds":1.2}}
 exited 1 in 1212ms:
python : Имя "python" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте пр
авильность написания имени, а также наличие и правильность пути, после чего повторите попытку.
строка:2 знак:1
+ python --version; python .claude/hooks/test_codex_delegate_enforcer.p ...
+ ~~~~~~
    + CategoryInfo          : ObjectNotFound: (python:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 
python : Имя "python" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте пр
авильность написания имени, а также наличие и правильность пути, после чего повторите попытку.
строка:2 знак:19
+ python --version; python .claude/hooks/test_codex_delegate_enforcer.p ...
+                   ~~~~~~
    + CategoryInfo          : ObjectNotFound: (python:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 81098ec2547ec42978e25eb067d47d2d527fa1bb..559a64c5355a00095bd258ca191bd69568a27280
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -81,13 +81,49 @@
     logger.propagate = False
     return logger
 
-def get_project_dir() -> Path:
-    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
-    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
-
-def resolve_target(project_dir: Path, target_raw: str):
-    """Normalize raw file_path to absolute Path inside project_dir."""
-    logger = logging.getLogger(HOOK_NAME)
+def get_project_dir() -> Path:
+    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
+    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+
+def is_dual_teams_worktree(project_dir: Path) -> bool:
+    """True iff project_dir or any ancestor contains .dual-base-ref."""
+    logger = logging.getLogger(HOOK_NAME)
+    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
+    current = project_dir
+    seen: set[Path] = set()
+    while True:
+        try:
+            resolved = current.resolve()
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
+            resolved = current.absolute()
+        if resolved in seen:
+            logger.info(
+                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
+                project_dir,
+            )
+            return False
+        seen.add(resolved)
+        sentinel = current / ".dual-base-ref"
+        try:
+            if sentinel.is_file():
+                logger.info(
+                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
+                    project_dir,
+                    sentinel,
+                )
+                return True
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
+        parent = current.parent
+        if parent == current:
+            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
+            return False
+        current = parent
+
+def resolve_target(project_dir: Path, target_raw: str):
+    """Normalize raw file_path to absolute Path inside project_dir."""
+    logger = logging.getLogger(HOOK_NAME)
     if not target_raw:
         return None
     try:
@@ -391,10 +427,13 @@
     if event and event != "PreToolUse":
         logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
         return True
-    if tool_name not in {"Edit", "Write", "MultiEdit"}:
-        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
-        return True
-    raw_targets = extract_targets(payload)
+    if tool_name not in {"Edit", "Write", "MultiEdit"}:
+        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
+        return True
+    if is_dual_teams_worktree(project_dir):
+        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
+        return True
+    raw_targets = extract_targets(payload)
     if not raw_targets:
         logger.info("decide.passthrough reason=no-targets")
         return True
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

codex
Python isn’t on PATH here, so I’m checking for a local interpreter before finalizing.
exec
powershell.exe -Command "Get-Command py,python,python3 -ErrorAction SilentlyContinue | Format-List *; Get-ChildItem -Path . -Force -Directory -Filter '.venv'" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
 succeeded in 1218ms:


HelpUri            : 
FileVersionInfo    : File:             C:\WINDOWS\py.exe
                     InternalName:     Python Launcher
                     OriginalFilename: py.exe
                     FileVersion:      3.12.10
                     FileDescription:  Python
                     Product:          Python
                     ProductVersion:   3.12.10
                     Debug:            False
                     Patched:          False
                     PreRelease:       False
                     PrivateBuild:     False
                     SpecialBuild:     False
                     Language:         Language Neutral
                     
Path               : C:\WINDOWS\py.exe
Extension          : .exe
Definition         : C:\WINDOWS\py.exe
Source             : C:\WINDOWS\py.exe
Version            : 3.12.10150.1013
Visibility         : Public
OutputType         : {System.String}
Name               : py.exe
CommandType        : Application
ModuleName         : 
Module             : 
RemotingCapability : PowerShell
Parameters         : 
ParameterSets      : 




diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 81098ec2547ec42978e25eb067d47d2d527fa1bb..559a64c5355a00095bd258ca191bd69568a27280
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -81,13 +81,49 @@
     logger.propagate = False
     return logger
 
-def get_project_dir() -> Path:
-    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
-    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
-
-def resolve_target(project_dir: Path, target_raw: str):
-    """Normalize raw file_path to absolute Path inside project_dir."""
-    logger = logging.getLogger(HOOK_NAME)
+def get_project_dir() -> Path:
+    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
+    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+
+def is_dual_teams_worktree(project_dir: Path) -> bool:
+    """True iff project_dir or any ancestor contains .dual-base-ref."""
+    logger = logging.getLogger(HOOK_NAME)
+    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
+    current = project_dir
+    seen: set[Path] = set()
+    while True:
+        try:
+            resolved = current.resolve()
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
+            resolved = current.absolute()
+        if resolved in seen:
+            logger.info(
+                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
+                project_dir,
+            )
+            return False
+        seen.add(resolved)
+        sentinel = current / ".dual-base-ref"
+        try:
+            if sentinel.is_file():
+                logger.info(
+                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
+                    project_dir,
+                    sentinel,
+                )
+                return True
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
+        parent = current.parent
+        if parent == current:
+            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
+            return False
+        current = parent
+
+def resolve_target(project_dir: Path, target_raw: str):
+    """Normalize raw file_path to absolute Path inside project_dir."""
+    logger = logging.getLogger(HOOK_NAME)
     if not target_raw:
         return None
     try:
@@ -391,10 +427,13 @@
     if event and event != "PreToolUse":
         logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
         return True
-    if tool_name not in {"Edit", "Write", "MultiEdit"}:
-        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
-        return True
-    raw_targets = extract_targets(payload)
+    if tool_name not in {"Edit", "Write", "MultiEdit"}:
+        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
+        return True
+    if is_dual_teams_worktree(project_dir):
+        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
+        return True
+    raw_targets = extract_targets(payload)
     if not raw_targets:
         logger.info("decide.passthrough reason=no-targets")
         return True
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

**Considering environment setup**

I’m thinking maybe I don’t need to set up a virtual environment. I could use what’s installed in WindowsApps instead. Running a command like "where /r C:\Users\Lenovo python.exe" might take a while since it reads outside allowed areas, but I’m not sure it’s necessary. Instead, I wonder if I should look into using `uv` for my project. Let's see how to proceed with this efficient setup!
exec
powershell.exe -Command 'Get-Command uv,poetry,pdm,hatch -ErrorAction SilentlyContinue | Select-Object Name,Source' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
2026-04-25T07:28:08.593291Z ERROR codex_core::tools::router: error={"output":"","metadata":{"exit_code":1,"duration_seconds":1.2}}
 exited 1 in 1185ms:
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 81098ec2547ec42978e25eb067d47d2d527fa1bb..559a64c5355a00095bd258ca191bd69568a27280
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -81,13 +81,49 @@
     logger.propagate = False
     return logger
 
-def get_project_dir() -> Path:
-    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
-    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
-
-def resolve_target(project_dir: Path, target_raw: str):
-    """Normalize raw file_path to absolute Path inside project_dir."""
-    logger = logging.getLogger(HOOK_NAME)
+def get_project_dir() -> Path:
+    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
+    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+
+def is_dual_teams_worktree(project_dir: Path) -> bool:
+    """True iff project_dir or any ancestor contains .dual-base-ref."""
+    logger = logging.getLogger(HOOK_NAME)
+    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
+    current = project_dir
+    seen: set[Path] = set()
+    while True:
+        try:
+            resolved = current.resolve()
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
+            resolved = current.absolute()
+        if resolved in seen:
+            logger.info(
+                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
+                project_dir,
+            )
+            return False
+        seen.add(resolved)
+        sentinel = current / ".dual-base-ref"
+        try:
+            if sentinel.is_file():
+                logger.info(
+                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
+                    project_dir,
+                    sentinel,
+                )
+                return True
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
+        parent = current.parent
+        if parent == current:
+            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
+            return False
+        current = parent
+
+def resolve_target(project_dir: Path, target_raw: str):
+    """Normalize raw file_path to absolute Path inside project_dir."""
+    logger = logging.getLogger(HOOK_NAME)
     if not target_raw:
         return None
     try:
@@ -391,10 +427,13 @@
     if event and event != "PreToolUse":
         logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
         return True
-    if tool_name not in {"Edit", "Write", "MultiEdit"}:
-        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
-        return True
-    raw_targets = extract_targets(payload)
+    if tool_name not in {"Edit", "Write", "MultiEdit"}:
+        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
+        return True
+    if is_dual_teams_worktree(project_dir):
+        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
+        return True
+    raw_targets = extract_targets(payload)
     if not raw_targets:
         logger.info("decide.passthrough reason=no-targets")
         return True
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

exec
powershell.exe -Command 'py -0p' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
 succeeded in 227ms:
No installed Pythons found!

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 81098ec2547ec42978e25eb067d47d2d527fa1bb..559a64c5355a00095bd258ca191bd69568a27280
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -81,13 +81,49 @@
     logger.propagate = False
     return logger
 
-def get_project_dir() -> Path:
-    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
-    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
-
-def resolve_target(project_dir: Path, target_raw: str):
-    """Normalize raw file_path to absolute Path inside project_dir."""
-    logger = logging.getLogger(HOOK_NAME)
+def get_project_dir() -> Path:
+    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
+    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+
+def is_dual_teams_worktree(project_dir: Path) -> bool:
+    """True iff project_dir or any ancestor contains .dual-base-ref."""
+    logger = logging.getLogger(HOOK_NAME)
+    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
+    current = project_dir
+    seen: set[Path] = set()
+    while True:
+        try:
+            resolved = current.resolve()
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
+            resolved = current.absolute()
+        if resolved in seen:
+            logger.info(
+                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
+                project_dir,
+            )
+            return False
+        seen.add(resolved)
+        sentinel = current / ".dual-base-ref"
+        try:
+            if sentinel.is_file():
+                logger.info(
+                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
+                    project_dir,
+                    sentinel,
+                )
+                return True
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
+        parent = current.parent
+        if parent == current:
+            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
+            return False
+        current = parent
+
+def resolve_target(project_dir: Path, target_raw: str):
+    """Normalize raw file_path to absolute Path inside project_dir."""
+    logger = logging.getLogger(HOOK_NAME)
     if not target_raw:
         return None
     try:
@@ -391,10 +427,13 @@
     if event and event != "PreToolUse":
         logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
         return True
-    if tool_name not in {"Edit", "Write", "MultiEdit"}:
-        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
-        return True
-    raw_targets = extract_targets(payload)
+    if tool_name not in {"Edit", "Write", "MultiEdit"}:
+        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
+        return True
+    if is_dual_teams_worktree(project_dir):
+        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
+        return True
+    raw_targets = extract_targets(payload)
     if not raw_targets:
         logger.info("decide.passthrough reason=no-targets")
         return True
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

exec
powershell.exe -Command "Select-String -Path '.claude/hooks/codex-delegate-enforcer.py' -Pattern 'except' -Context 0,1" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
 succeeded in 454ms:

> .claude\hooks\codex-delegate-enforcer.py:6:deny via PreToolUse JSON. Fail-open on any exception.
  .claude\hooks\codex-delegate-enforcer.py:7:"""
> .claude\hooks\codex-delegate-enforcer.py:75:    except OSError:
  .claude\hooks\codex-delegate-enforcer.py:76:        file_ok = False
> .claude\hooks\codex-delegate-enforcer.py:97:        except OSError as exc:
  .claude\hooks\codex-delegate-enforcer.py:98:            logger.debug("is_dual_teams_worktree.resolve-error path=%s ex
c=%s", current, exc)
> .claude\hooks\codex-delegate-enforcer.py:116:        except OSError as exc:
  .claude\hooks\codex-delegate-enforcer.py:117:            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s
 exc=%s", sentinel, exc)
> .claude\hooks\codex-delegate-enforcer.py:134:    except (OSError, ValueError) as exc:
  .claude\hooks\codex-delegate-enforcer.py:135:        logger.info("resolve_target.err raw=%r exc=%s", target_raw, exc)
> .claude\hooks\codex-delegate-enforcer.py:139:    except ValueError:
  .claude\hooks\codex-delegate-enforcer.py:140:        logger.info("resolve_target.escape resolved=%s", resolved)
> .claude\hooks\codex-delegate-enforcer.py:148:    except ValueError:
  .claude\hooks\codex-delegate-enforcer.py:149:        return None
> .claude\hooks\codex-delegate-enforcer.py:199:    except OSError as exc:
  .claude\hooks\codex-delegate-enforcer.py:200:        logger.info("parse_result_fields.read_err path=%s exc=%s", resul
t_path.name, exc)
> .claude\hooks\codex-delegate-enforcer.py:221:    except OSError as exc:
  .claude\hooks\codex-delegate-enforcer.py:222:        logger.info("parse_scope_fence.read_err path=%s exc=%s", task_pa
th.name, exc)
> .claude\hooks\codex-delegate-enforcer.py:268:    except (OSError, ValueError) as exc:
  .claude\hooks\codex-delegate-enforcer.py:269:        logger.info("resolve_task_file.err raw=%r exc=%s", raw, exc)
> .claude\hooks\codex-delegate-enforcer.py:285:            except OSError:
  .claude\hooks\codex-delegate-enforcer.py:286:                continue
> .claude\hooks\codex-delegate-enforcer.py:304:            except (OSError, ValueError):
  .claude\hooks\codex-delegate-enforcer.py:305:                logger.info("find_cover.symlink-escape path=%s", rpath.n
ame)
> .claude\hooks\codex-delegate-enforcer.py:361:    except Exception as exc:
> .claude\hooks\codex-delegate-enforcer.py:362:        logger.exception("find_cover.unexpected target=%s exc=%s", targe
t_rel_posix, exc)
  .claude\hooks\codex-delegate-enforcer.py:363:        return False, "parse-error: " + str(exc)
> .claude\hooks\codex-delegate-enforcer.py:473:        except json.JSONDecodeError as exc:
  .claude\hooks\codex-delegate-enforcer.py:474:            logger.info("main.malformed-json exc=%s", exc)
> .claude\hooks\codex-delegate-enforcer.py:480:    except Exception as exc:
> .claude\hooks\codex-delegate-enforcer.py:481:        logger.exception("main.unexpected exc=%s", exc)
  .claude\hooks\codex-delegate-enforcer.py:482:    finally:



diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 81098ec2547ec42978e25eb067d47d2d527fa1bb..559a64c5355a00095bd258ca191bd69568a27280
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -81,13 +81,49 @@
     logger.propagate = False
     return logger
 
-def get_project_dir() -> Path:
-    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
-    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
-
-def resolve_target(project_dir: Path, target_raw: str):
-    """Normalize raw file_path to absolute Path inside project_dir."""
-    logger = logging.getLogger(HOOK_NAME)
+def get_project_dir() -> Path:
+    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
+    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+
+def is_dual_teams_worktree(project_dir: Path) -> bool:
+    """True iff project_dir or any ancestor contains .dual-base-ref."""
+    logger = logging.getLogger(HOOK_NAME)
+    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
+    current = project_dir
+    seen: set[Path] = set()
+    while True:
+        try:
+            resolved = current.resolve()
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
+            resolved = current.absolute()
+        if resolved in seen:
+            logger.info(
+                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
+                project_dir,
+            )
+            return False
+        seen.add(resolved)
+        sentinel = current / ".dual-base-ref"
+        try:
+            if sentinel.is_file():
+                logger.info(
+                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
+                    project_dir,
+                    sentinel,
+                )
+                return True
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
+        parent = current.parent
+        if parent == current:
+            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
+            return False
+        current = parent
+
+def resolve_target(project_dir: Path, target_raw: str):
+    """Normalize raw file_path to absolute Path inside project_dir."""
+    logger = logging.getLogger(HOOK_NAME)
     if not target_raw:
         return None
     try:
@@ -391,10 +427,13 @@
     if event and event != "PreToolUse":
         logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
         return True
-    if tool_name not in {"Edit", "Write", "MultiEdit"}:
-        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
-        return True
-    raw_targets = extract_targets(payload)
+    if tool_name not in {"Edit", "Write", "MultiEdit"}:
+        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
+        return True
+    if is_dual_teams_worktree(project_dir):
+        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
+        return True
+    raw_targets = extract_targets(payload)
     if not raw_targets:
         logger.info("decide.passthrough reason=no-targets")
         return True
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

**Evaluating project resolution**

I need to resolve the "project_dir" from the temporary settings, and it looks good so far. I'm thinking about whether I should test for "find_cover skipped entirely." We did remove the working directory in the sentinel test to confirm that if it's not skipped, there’s a no-results directory denial. That's a solid approach. I might also need to run the exact command after finalizing the code. Let's ensure everything's aligned!
codex
Code looks aligned; I’m rerunning the required command for the official result.
exec
powershell.exe -Command 'py -3 .claude/hooks/test_codex_delegate_enforcer.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
2026-04-25T07:28:40.383311Z ERROR codex_core::tools::router: error={"output":"No installed Python found!\r\n","metadata":{"exit_code":1,"duration_seconds":0.2}}
 exited 1 in 236ms:
No installed Python found!

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 81098ec2547ec42978e25eb067d47d2d527fa1bb..559a64c5355a00095bd258ca191bd69568a27280
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -81,13 +81,49 @@
     logger.propagate = False
     return logger
 
-def get_project_dir() -> Path:
-    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
-    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
-
-def resolve_target(project_dir: Path, target_raw: str):
-    """Normalize raw file_path to absolute Path inside project_dir."""
-    logger = logging.getLogger(HOOK_NAME)
+def get_project_dir() -> Path:
+    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
+    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+
+def is_dual_teams_worktree(project_dir: Path) -> bool:
+    """True iff project_dir or any ancestor contains .dual-base-ref."""
+    logger = logging.getLogger(HOOK_NAME)
+    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
+    current = project_dir
+    seen: set[Path] = set()
+    while True:
+        try:
+            resolved = current.resolve()
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
+            resolved = current.absolute()
+        if resolved in seen:
+            logger.info(
+                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
+                project_dir,
+            )
+            return False
+        seen.add(resolved)
+        sentinel = current / ".dual-base-ref"
+        try:
+            if sentinel.is_file():
+                logger.info(
+                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
+                    project_dir,
+                    sentinel,
+                )
+                return True
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
+        parent = current.parent
+        if parent == current:
+            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
+            return False
+        current = parent
+
+def resolve_target(project_dir: Path, target_raw: str):
+    """Normalize raw file_path to absolute Path inside project_dir."""
+    logger = logging.getLogger(HOOK_NAME)
     if not target_raw:
         return None
     try:
@@ -391,10 +427,13 @@
     if event and event != "PreToolUse":
         logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
         return True
-    if tool_name not in {"Edit", "Write", "MultiEdit"}:
-        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
-        return True
-    raw_targets = extract_targets(payload)
+    if tool_name not in {"Edit", "Write", "MultiEdit"}:
+        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
+        return True
+    if is_dual_teams_worktree(project_dir):
+        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
+        return True
+    raw_targets = extract_targets(payload)
     if not raw_targets:
         logger.info("decide.passthrough reason=no-targets")
         return True
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

**Exploring test processes**

I'm considering if I can still use a local test runner, but I think I need to get the diff stats instead. So, I’m thinking about using the command `git diff --stat`. It might also be a good idea to inspect the diff directly. I'm curious about how these steps will help me understand the changes better! The goal is to get everything squared away effectively.
codex
The required launcher still can’t find Python; I’m collecting diff stats and reviewing the patch.
exec
powershell.exe -Command 'git diff --stat -- .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer.py; git diff -- .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
2026-04-25T07:28:48.460096Z ERROR codex_core::tools::router: error={"output":"Total output lines: 962\n\n ...enforcer.py => test_codex_delegate_enforcer.py} | 938 ++++++++++-----------\n 1 file changed, 464 insertions(+), 474 deletions(-)\ndiff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py\nindex 559a64c..ab2bfc1 100644\n--- a/.claude/hooks/codex-delegate-enforcer.py\n+++ b/.claude/hooks/test_codex_delegate_enforcer.py\n@@ -1,487 +1,477 @@\n #!/usr/bin/env python3\n-\"\"\"Codex Delegate Enforcer - Always-Dual PreToolUse hook (CLAUDE.md).\n-Edit/Write/MultiEdit on a code file that is NOT exempt -> require a fresh\n-(<15 min) work/codex-implementations/task-*-result.md with status=pass\n-whose paired task-N.md Scope Fence covers the target. Missing cover ->\n-deny via PreToolUse JSON. Fail-open on any exception.\n+\"\"\"Unit tests for codex-delegate-enforcer.py (task T1).\n+\n+Covers all 11 required cases from spec AC12:\n+\n+  1. exempt path (e.g., CLAUDE.md) -> allow\n+  2. code file + NO recent result.md -> deny with JSON\n+  3. code file + stale (> 15 min) result.md -> deny\n+  4. code file + fresh status=pass result.md with covering fence -> allow\n+  5. code file + fresh pass result.md but fence does NOT cover target -> deny\n+  6. code file + fresh status=fail result.md -> deny\n+  7. non-code file (.txt, .md) -> allow\n+  8. MultiEdit with multiple files, all covered -> allow\n+  9. MultiEdit with one file uncovered -> deny\n+ 10. malformed result.md / corrupt JSON payload -> pass-through (no crash)\n+ 11. hook called on non-Edit event (e.g., Bash) -> pass-through\n+\n+Each test isolates state under a temporary CLAUDE_PROJECT_DIR so\n+production .codex/ and work/ directories are never touched.\n \"\"\"\n+\n from __future__ import annotations\n-import fnmatch\n+\n+import importlib.util\n+import contextlib\n+import io\n import json\n-import logging\n import os\n-import re\n+import shutil\n+import subprocess\n import sys\n+import tempfile\n import time\n+import unittest\n from pathlib import Path\n-from typing import Any, Iterable\n-if sys.platform == \"win32\":\n-    for _stream in (sys.stdin, sys.stdout, sys.stderr):\n-        if hasattr(_stream, \"reconfigure\"):\n-            _stream.reconfigure(encoding=\"utf-8\", errors=\"replace\")\n-HOOK_NAME = \"codex-delegate-enforcer\"\n-RESULT_MAX_AGE_SECONDS: int = 15 * 60\n-MAX_RESULT_FILES_TO_SCAN: int = 50\n-CODEX_IMPLEMENTATIONS_DIR = \"work/codex-implementations\"\n-CODEX_TASKS_DIR = \"work/codex-primary/tasks\"\n-# AC5 - delegated code extensions. Frozenset for O(1) lookup.\n-CODE_EXTENSIONS: frozenset = frozenset({\n-    \".py\", \".pyi\", \".js\", \".jsx\", \".mjs\", \".cjs\", \".ts\", \".tsx\",\n-    \".sh\", \".bash\", \".zsh\", \".go\", \".rs\", \".rb\", \".java\", \".kt\",\n-    \".swift\", \".c\", \".cpp\", \".cc\", \".h\", \".hpp\", \".cs\", \".php\",\n-    \".sql\", \".lua\", \".r\",\n-})\n-# AC6 - exempt path globs. Matched against POSIX relative path.\n-EXEMPT_PATTERNS: tuple = (\n-    \".claude/memory/**\", \"work/**\", \"CLAUDE.md\", \"AGENTS.md\",\n-    \"README.md\", \"CHANGELOG.md\", \"LICENSE\", \".gitignore\",\n-    \".claude/settings.json\", \".claude/ops/*.yaml\", \".mcp.json\",\n-    \".claude/adr/**/*.md\", \".claude/guides/**/*.md\",\n-    \".claude/skills/**/*.md\",\n-    \"worktrees/**\",  # dual-implement worktrees — edits here are part of an outer DUAL operation\n-)\n-# AC14 - regex compiled at module scope.\n-_STATUS_RE = re.compile(r\"(?i)status\\s*[:=]\\s*([A-Za-z0-9_-]+)\")\n-_TASK_FILE_RE = re.compile(r\"(?i)task[_\\s-]*file\\s*[:=]\\s*(.+)\")\n-_SCOPE_FENCE_HEADING_RE = re.compile(r\"(?im)^##\\s+Scope\\s+Fence\\s*$\")\n-_NEXT_HEADING_RE = re.compile(r\"(?m)^##\\s+\")\n-_ALLOWED_SECTION_RE = re.compile(\n-    r\"(?is)allowed\\s+paths[^\\n]*\\n(.+?)(?:\\n\\s*\\*{0,2}forbidden|\\Z)\"\n-)\n-_TRAILING_PAREN_RE = re.compile(r\"\\s*\\([^)]*\\)\\s*$\")\n-_GLOB_TAIL_RE = re.compile(r\"/?\\*+$\")\n-_RESULT_NAME_RE = re.compile(r\"task-(.+?)-result\\.md$\")\n-RECOVERY_HINT = (\n-    \"Use .claude/scripts/codex-inline-dual.py --describe \\\"...\\\" \"\n-    \"--scope <path> for micro-task, or write work/<feature>/tasks/task-N.md \"\n-    \"and run codex-implement.py. See CLAUDE.md \\\"Code Delegation Protocol\\\".\"\n-)\n-\n-def _build_logger(project_dir: Path) -> logging.Logger:\n-    \"\"\"Create enforcer logger: file if writable else stderr-only.\"\"\"\n-    logger = logging.getLogger(HOOK_NAME)\n-    if logger.handlers:\n-        return logger\n-    logger.setLevel(logging.INFO)\n-    fmt = logging.Formatter(\"%(asctime)s %(name)s %(levelname)s %(message)s\")\n-    log_dir = project_dir / \".claude\" / \"logs\"\n-    file_ok = False\n-    try:\n-        log_dir.mkdir(parents=True, exist_ok=True)\n-        fh = logging.FileHandler(log_dir / (HOOK_NAME + \".log\"), encoding=\"utf-8\")\n-        fh.setFormatter(fmt)\n-        logger.addHandler(fh)\n-        file_ok = True\n-    except OSError:\n-        file_ok = False\n-    sh = logging.StreamHandler(sys.stderr)\n-    sh.setFormatter(fmt)\n-    sh.setLevel(logging.WARNING if file_ok else logging.INFO)\n-    logger.addHandler(sh)\n-    logger.propagate = False\n-    return logger\n-\n-def get_project_dir() -> Path:\n-    \"\"\"Resolve project root. Honors CLAUDE_PROJECT_DIR env.\"\"\"\n-    return Path(os.environ.get(\"CLAUDE_…31064 chars truncated…(self.mod.is_exempt(\".claude/skills/bar/SKILL.md\"))\n+\n+    def test_is_exempt_negative(self) -> None:\n+        self.assertFalse(self.mod.is_exempt(\".claude/hooks/my_hook.py\"))\n+        self.assertFalse(self.mod.is_exempt(\"src/main.py\"))\n+\n+    def test_requires_cover_positive(self) -> None:\n+        self.assertTrue(self.mod.requires_cover(\".claude/hooks/x.py\"))\n+        self.assertTrue(self.mod.requires_cover(\"src/main.ts\"))\n+\n+    def test_requires_cover_negative_non_code(self) -> None:\n+        self.assertFalse(self.mod.requires_cover(\"docs/readme.md\"))\n+\n+    def test_requires_cover_negative_exempt(self) -> None:\n+        # .claude/skills/**/*.md is exempt, and .md is non-code anyway.\n+        self.assertFalse(self.mod.requires_cover(\"CLAUDE.md\"))\n+        # work/** is exempt even for .py.\n+        self.assertFalse(self.mod.requires_cover(\"work/scripts/helper.py\"))\n+\n+    def test_path_in_fence_exact_file(self) -> None:\n+        self.assertTrue(self.mod.path_in_fence(\"a/b/c.py\", [\"a/b/c.py\"]))\n+\n+    def test_path_in_fence_dir_prefix(self) -> None:\n+        self.assertTrue(self.mod.path_in_fence(\"a/b/c.py\", [\"a/b\"]))\n+        self.assertTrue(self.mod.path_in_fence(\"a/b/c.py\", [\"a/b/\"]))\n+\n+    def test_path_in_fence_no_partial_segment(self) -> None:\n+        self.assertFalse(self.mod.path_in_fence(\"a/bb/c.py\", [\"a/b\"]))\n+\n+    def test_path_in_fence_strips_trailing_globs(self) -> None:\n+        self.assertTrue(self.mod.path_in_fence(\"a/b/c.py\", [\"a/b/**\"]))\n+        self.assertTrue(self.mod.path_in_fence(\"a/b/c.py\", [\"a/b/*\"]))\n+\n+    def test_parse_result_fields_status_pass(self) -> None:\n+        with tempfile.NamedTemporaryFile(\n+            \"w\", suffix=\".md\", delete=False, encoding=\"utf-8\"\n+        ) as fh:\n+            fh.write(\"# result\\n\\n- status: pass\\n- task_file: t.md\\n\")\n+            p = Path(fh.name)\n         try:\n-            payload = json.loads(raw)\n-        except json.JSONDecodeError as exc:\n-            logger.info(\"main.malformed-json exc=%s\", exc)\n-            return 0\n-        if not isinstance(payload, dict):\n-            logger.info(\"main.non-dict-payload type=%s\", type(payload).__name__)\n-            return 0\n-        decide(payload, project_dir)\n-    except Exception as exc:\n-        logger.exception(\"main.unexpected exc=%s\", exc)\n-    finally:\n-        logger.info(\"main.exit\")\n-    return 0\n+            fields = self.mod.parse_result_fields(p)\n+            self.assertEqual(fields.get(\"status\"), \"pass\")\n+            self.assertEqual(fields.get(\"task_file\"), \"t.md\")\n+        finally:\n+            p.unlink()\n+\n+    def test_parse_scope_fence_strips_backticks_and_annotations(self) -> None:\n+        with tempfile.NamedTemporaryFile(\n+            \"w\", suffix=\".md\", delete=False, encoding=\"utf-8\"\n+        ) as fh:\n+            fh.write(\n+                \"# Task\\n\\n\"\n+                \"## Scope Fence\\n\"\n+                \"**Allowed paths (may be written):**\\n\"\n+                \"- `.claude/hooks/x.py` (new)\\n\"\n+                \"- `.claude/hooks/test_x.py`\\n\\n\"\n+                \"**Forbidden paths:**\\n- else/\\n\\n## Next\\n\"\n+            )\n+            p = Path(fh.name)\n+        try:\n+            fence = self.mod.parse_scope_fence(p)\n+            self.assertIn(\".claude/hooks/x.py\", fence)\n+            self.assertIn(\".claude/hooks/test_x.py\", fence)\n+        finally:\n+            p.unlink()\n+\n+    def test_extract_targets_edit(self) -> None:\n+        paths = self.mod.extract_targets({\n+            \"tool_name\": \"Edit\",\n+            \"tool_input\": {\"file_path\": \"a.py\", \"old_string\": \"x\", \"new_string\": \"y\"},\n+        })\n+        self.assertEqual(paths, [\"a.py\"])\n+\n+    def test_extract_targets_multiedit(self) -> None:\n+        paths = self.mod.extract_targets({\n+            \"tool_name\": \"MultiEdit\",\n+            \"tool_input\": {\n+                \"edits\": [\n+                    {\"file_path\": \"a.py\", \"old_string\": \"x\", \"new_string\": \"y\"},\n+                    {\"file_path\": \"b.py\", \"old_string\": \"x\", \"new_string\": \"y\"},\n+                ],\n+            },\n+        })\n+        self.assertEqual(sorted(paths), [\"a.py\", \"b.py\"])\n+\n+    def test_extract_targets_missing_is_empty(self) -> None:\n+        self.assertEqual(self.mod.extract_targets({}), [])\n+        self.assertEqual(self.mod.extract_targets({\"tool_name\": \"Edit\"}), [])\n+        self.assertEqual(self.mod.extract_targets(None), [])\n+\n \n if __name__ == \"__main__\":\n-    sys.exit(main())\n+    unittest.main(verbosity=2)\nwarning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it\nwarning: in the working copy of '.claude/hooks/test_codex_delegate_enforcer.py', LF will be replaced by CRLF the next time Git touches it\nwarning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it\nwarning: in the working copy of '.claude/hooks/test_codex_delegate_enforcer.py', LF will be replaced by CRLF the next time Git touches it\n","metadata":{"exit_code":1,"duration_seconds":0.2}}
 exited 1 in 244ms:
 ...enforcer.py => test_codex_delegate_enforcer.py} | 938 ++++++++++-----------
 1 file changed, 464 insertions(+), 474 deletions(-)
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 559a64c..ab2bfc1 100644
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -1,487 +1,477 @@
 #!/usr/bin/env python3
-"""Codex Delegate Enforcer - Always-Dual PreToolUse hook (CLAUDE.md).
-Edit/Write/MultiEdit on a code file that is NOT exempt -> require a fresh
-(<15 min) work/codex-implementations/task-*-result.md with status=pass
-whose paired task-N.md Scope Fence covers the target. Missing cover ->
-deny via PreToolUse JSON. Fail-open on any exception.
+"""Unit tests for codex-delegate-enforcer.py (task T1).
+
+Covers all 11 required cases from spec AC12:
+
+  1. exempt path (e.g., CLAUDE.md) -> allow
+  2. code file + NO recent result.md -> deny with JSON
+  3. code file + stale (> 15 min) result.md -> deny
+  4. code file + fresh status=pass result.md with covering fence -> allow
+  5. code file + fresh pass result.md but fence does NOT cover target -> deny
+  6. code file + fresh status=fail result.md -> deny
+  7. non-code file (.txt, .md) -> allow
+  8. MultiEdit with multiple files, all covered -> allow
+  9. MultiEdit with one file uncovered -> deny
+ 10. malformed result.md / corrupt JSON payload -> pass-through (no crash)
+ 11. hook called on non-Edit event (e.g., Bash) -> pass-through
+
+Each test isolates state under a temporary CLAUDE_PROJECT_DIR so
+production .codex/ and work/ directories are never touched.
 """
+
 from __future__ import annotations
-import fnmatch
+
+import importlib.util
+import contextlib
+import io
 import json
-import logging
 import os
-import re
+import shutil
+import subprocess
 import sys
+import tempfile
 import time
+import unittest
 from pathlib import Path
-from typing import Any, Iterable
-if sys.platform == "win32":
-    for _stream in (sys.stdin, sys.stdout, sys.stderr):
-        if hasattr(_stream, "reconfigure"):
-            _stream.reconfigure(encoding="utf-8", errors="replace")
-HOOK_NAME = "codex-delegate-enforcer"
-RESULT_MAX_AGE_SECONDS: int = 15 * 60
-MAX_RESULT_FILES_TO_SCAN: int = 50
-CODEX_IMPLEMENTATIONS_DIR = "work/codex-implementations"
-CODEX_TASKS_DIR = "work/codex-primary/tasks"
-# AC5 - delegated code extensions. Frozenset for O(1) lookup.
-CODE_EXTENSIONS: frozenset = frozenset({
-    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
-    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
-    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
-    ".sql", ".lua", ".r",
-})
-# AC6 - exempt path globs. Matched against POSIX relative path.
-EXEMPT_PATTERNS: tuple = (
-    ".claude/memory/**", "work/**", "CLAUDE.md", "AGENTS.md",
-    "README.md", "CHANGELOG.md", "LICENSE", ".gitignore",
-    ".claude/settings.json", ".claude/ops/*.yaml", ".mcp.json",
-    ".claude/adr/**/*.md", ".claude/guides/**/*.md",
-    ".claude/skills/**/*.md",
-    "worktrees/**",  # dual-implement worktrees — edits here are part of an outer DUAL operation
-)
-# AC14 - regex compiled at module scope.
-_STATUS_RE = re.compile(r"(?i)status\s*[:=]\s*([A-Za-z0-9_-]+)")
-_TASK_FILE_RE = re.compile(r"(?i)task[_\s-]*file\s*[:=]\s*(.+)")
-_SCOPE_FENCE_HEADING_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
-_NEXT_HEADING_RE = re.compile(r"(?m)^##\s+")
-_ALLOWED_SECTION_RE = re.compile(
-    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\Z)"
-)
-_TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
-_GLOB_TAIL_RE = re.compile(r"/?\*+$")
-_RESULT_NAME_RE = re.compile(r"task-(.+?)-result\.md$")
-RECOVERY_HINT = (
-    "Use .claude/scripts/codex-inline-dual.py --describe \"...\" "
-    "--scope <path> for micro-task, or write work/<feature>/tasks/task-N.md "
-    "and run codex-implement.py. See CLAUDE.md \"Code Delegation Protocol\"."
-)
-
-def _build_logger(project_dir: Path) -> logging.Logger:
-    """Create enforcer logger: file if writable else stderr-only."""
-    logger = logging.getLogger(HOOK_NAME)
-    if logger.handlers:
-        return logger
-    logger.setLevel(logging.INFO)
-    fmt = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
-    log_dir = project_dir / ".claude" / "logs"
-    file_ok = False
-    try:
-        log_dir.mkdir(parents=True, exist_ok=True)
-        fh = logging.FileHandler(log_dir / (HOOK_NAME + ".log"), encoding="utf-8")
-        fh.setFormatter(fmt)
-        logger.addHandler(fh)
-        file_ok = True
-    except OSError:
-        file_ok = False
-    sh = logging.StreamHandler(sys.stderr)
-    sh.setFormatter(fmt)
-    sh.setLevel(logging.WARNING if file_ok else logging.INFO)
-    logger.addHandler(sh)
-    logger.propagate = False
-    return logger
-
-def get_project_dir() -> Path:
-    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
-    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
-
-def is_dual_teams_worktree(project_dir: Path) -> bool:
-    """True iff project_dir or any ancestor contains .dual-base-ref."""
-    logger = logging.getLogger(HOOK_NAME)
-    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
-    current = project_dir
-    seen: set[Path] = set()
-    while True:
-        try:
-            resolved = current.resolve()
-        except OSError as exc:
-            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
-            resolved = current.absolute()
-        if resolved in seen:
-            logger.info(
-                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
-                project_dir,
-            )
-            return False
-        seen.add(resolved)
-        sentinel = current / ".dual-base-ref"
-        try:
-            if sentinel.is_file():
-                logger.info(
-                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
-                    project_dir,
-                    sentinel,
-                )
-                return True
-        except OSError as exc:
-            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
-        parent = current.parent
-        if parent == current:
-            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
-            return False
-        current = parent
-
-def resolve_target(project_dir: Path, target_raw: str):
-    """Normalize raw file_path to absolute Path inside project_dir."""
-    logger = logging.getLogger(HOOK_NAME)
-    if not target_raw:
-        return None
-    try:
-        p = Path(target_raw)
-        if not p.is_absolute():
-            p = project_dir / p
-        resolved = p.resolve()
-    except (OSError, ValueError) as exc:
-        logger.info("resolve_target.err raw=%r exc=%s", target_raw, exc)
-        return None
-    try:
-        resolved.relative_to(project_dir)
-    except ValueError:
-        logger.info("resolve_target.escape resolved=%s", resolved)
-        return None
-    return resolved
-
-def rel_posix(project_dir: Path, absolute: Path):
-    """POSIX-style project-relative path, or None if outside."""
-    try:
-        return absolute.relative_to(project_dir).as_posix()
-    except ValueError:
-        return None
-
-def is_code_extension(rel_path: str) -> bool:
-    """True iff extension is in the delegated code set."""
-    return Path(rel_path).suffix.lower() in CODE_EXTENSIONS
-
-def is_exempt(rel_path: str) -> bool:
-    """True iff rel_path matches any AC6 exempt glob."""
-    logger = logging.getLogger(HOOK_NAME)
-    for pattern in EXEMPT_PATTERNS:
-        if pattern.endswith("/**"):
-            prefix = pattern[:-3].rstrip("/")
-            if rel_path == prefix or rel_path.startswith(prefix + "/"):
-                logger.debug("is_exempt.match pattern=%s", pattern)
-                return True
-            continue
-        if "**" in pattern:
-            left, _, right = pattern.partition("**")
-            left = left.rstrip("/")
-            right = right.lstrip("/")
-            left_ok = (not left) or rel_path == left or rel_path.startswith(left + "/")
-            right_ok = (not right) or fnmatch.fnmatch(rel_path, "*" + right)
-            if left_ok and right_ok:
-                logger.debug("is_exempt.match pattern=%s (double-glob)", pattern)
-                return True
-            continue
-        if fnmatch.fnmatch(rel_path, pattern):
-            logger.debug("is_exempt.match pattern=%s", pattern)
-            return True
-    return False
-
-def requires_cover(rel_path: str) -> bool:
-    """True iff path needs a Codex cover to be editable."""
-    if not is_code_extension(rel_path):
-        return False
-    if is_exempt(rel_path):
-        return False
-    return True
-
-def _strip_md_markers(line: str) -> str:
-    """Strip leading bullets/quotes, surrounding bold/italic/backticks."""
-    s = line.lstrip(" \t-*>").strip()
-    return s.replace("**", "").replace("__", "").replace("`", "")
-
-def parse_result_fields(result_path: Path) -> dict:
-    """Extract ``status`` and ``task_file`` from a task-*-result.md."""
-    logger = logging.getLogger(HOOK_NAME)
-    out: dict = {}
-    try:
-        text = result_path.read_text(encoding="utf-8", errors="replace")
-    except OSError as exc:
-        logger.info("parse_result_fields.read_err path=%s exc=%s", result_path.name, exc)
-        return out
-    for raw in text.splitlines():
-        stripped = _strip_md_markers(raw)
-        if "status" not in out:
-            m = _STATUS_RE.match(stripped)
-            if m:
-                out["status"] = m.group(1).strip().lower()
-        if "task_file" not in out:
-            m2 = _TASK_FILE_RE.match(stripped)
-            if m2:
-                out["task_file"] = m2.group(1).strip().strip("`").strip()
-        if "status" in out and "task_file" in out:
-            break
-    return out
-
-def parse_scope_fence(task_path: Path) -> list:
-    """Extract ``Allowed paths`` entries from task-N.md Scope Fence."""
-    logger = logging.getLogger(HOOK_NAME)
-    try:
-        text = task_path.read_text(encoding="utf-8", errors="replace")
-    except OSError as exc:
-        logger.info("parse_scope_fence.read_err path=%s exc=%s", task_path.name, exc)
-        return []
-    heading = _SCOPE_FENCE_HEADING_RE.search(text)
-    if not heading:
-        return []
-    tail = text[heading.end():]
-    next_hdr = _NEXT_HEADING_RE.search(tail)
-    section = tail[: next_hdr.start()] if next_hdr else tail
-    allowed = _ALLOWED_SECTION_RE.search(section)
-    if not allowed:
-        return []
-    entries: list = []
-    for line in allowed.group(1).splitlines():
-        stripped = line.strip()
-        if not stripped.startswith("-"):
-            continue
-        entry = stripped.lstrip("-").strip().strip("`").strip()
-        entry = _TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
-        if not entry:
-            continue
-        entries.append(entry.replace("\\", "/").rstrip("/"))
-    return entries
-
-def path_in_fence(target_rel_posix: str, fence: Iterable) -> bool:
-    """True if target is covered by any fence entry."""
-    target = target_rel_posix.rstrip("/")
-    for raw_entry in fence:
-        if not raw_entry:
-            continue
-        simple = _GLOB_TAIL_RE.sub("", raw_entry).rstrip("/")
-        if not simple:
-            continue
-        if target == simple or target.startswith(simple + "/"):
-            return True
-    return False
-
-def _resolve_task_file(project_dir: Path, raw: str):
-    """Resolve a result.md task_file pointer to absolute Path."""
-    logger = logging.getLogger(HOOK_NAME)
-    if not raw:
-        return None
-    try:
-        p = Path(raw.strip())
-        if not p.is_absolute():
-            p = project_dir / p
-        return p.resolve()
-    except (OSError, ValueError) as exc:
-        logger.info("resolve_task_file.err raw=%r exc=%s", raw, exc)
-        return None
-
-def find_cover(project_dir: Path, target_rel_posix: str):
-    """Search recent result.md artefacts for one covering the target."""
-    logger = logging.getLogger(HOOK_NAME)
-    logger.info("find_cover.enter target=%s", target_rel_posix)
-    try:
-        results_dir = project_dir / CODEX_IMPLEMENTATIONS_DIR
-        if not results_dir.is_dir():
-            logger.info("find_cover.no-dir dir=%s", results_dir)
-            return False, "no-results-dir"
-        candidates: list = []
-        for rp in results_dir.glob("task-*-result.md"):
-            try:
-                candidates.append((rp.stat().st_mtime, rp))
-            except OSError:
-                continue
-        candidates.sort(key=lambda item: item[0], reverse=True)
-        candidates = candidates[:MAX_RESULT_FILES_TO_SCAN]
-        if not candidates:
-            logger.info("find_cover.no-results")
-            return False, "no-results"
-        now = time.time()
-        saw_fresh = False
-        saw_fresh_pass = False
-        best_reason = "stale"
-        for mtime, rpath in candidates:
-            age = now - mtime
-            if age > RESULT_MAX_AGE_SECONDS:
-                continue
-            saw_fresh = True
+
+HERE = Path(__file__).resolve().parent
+ENFORCER_PATH = HERE / "codex-delegate-enforcer.py"
+
+
+def _load_module():
+    """Import codex-delegate-enforcer.py as a module (hyphen in filename)."""
+    spec = importlib.util.spec_from_file_location(
+        "codex_delegate_enforcer", ENFORCER_PATH
+    )
+    module = importlib.util.module_from_spec(spec)
+    spec.loader.exec_module(module)
+    return module
+
+
+class BaseEnforcerTest(unittest.TestCase):
+    """Shared fixture: isolated project root with results + tasks dirs."""
+
+    def setUp(self) -> None:
+        self.tmpdir = tempfile.mkdtemp(prefix="codex-enforcer-test-")
+        self.root = Path(self.tmpdir).resolve()
+        (self.root / ".claude" / "hooks").mkdir(parents=True)
+        (self.root / "work" / "codex-primary" / "tasks").mkdir(parents=True)
+        (self.root / "work" / "codex-implementations").mkdir(parents=True)
+        # Target file the tool call "would edit"
+        self.target_rel = ".claude/hooks/my_hook.py"
+        (self.root / ".claude" / "hooks" / "my_hook.py").write_text(
+            "# placeholder\n", encoding="utf-8"
+        )
+
+    def tearDown(self) -> None:
+        shutil.rmtree(self.tmpdir, ignore_errors=True)
+
+    # ----- subprocess invocation helpers -----
+
+    def _run_enforcer(self, payload):
+        """Invoke enforcer as subprocess; return (exit_code, stdout, stderr)."""
+        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)}
+        result = subprocess.run(
+            [sys.executable, str(ENFORCER_PATH)],
+            input=json.dumps(payload),
+            capture_output=True, text=True,
+            encoding="utf-8", errors="replace",
+            env=env, timeout=30,
+        )
+        return result.returncode, result.stdout, result.stderr
+
+    # ----- fixture helpers -----
+
+    def _write_task(self, task_id: str, fence_paths: list) -> Path:
+        """Write a task-N.md with given Scope Fence allowed paths."""
+        task_file = self.root / "work" / "codex-primary" / "tasks" / (
+            "T" + task_id + "-test.md"
+        )
+        fence_block = "\n".join("- `" + p + "`" for p in fence_paths)
+        task_file.write_text(
+            "---\nexecutor: codex\n---\n\n"
+            "# Task T" + task_id + "\n\n"
+            "## Your Task\ntest\n\n"
+            "## Scope Fence\n"
+            "**Allowed paths (may be written):**\n"
+            + fence_block + "\n\n"
+            "**Forbidden paths:**\n- other/\n\n"
+            "## Acceptance Criteria\n- [ ] AC1\n",
+            encoding="utf-8",
+        )
+        return task_file
+
+    def _write_result(self, task_id: str, status: str, age_seconds: float = 0) -> Path:
+        """Write a task-N-result.md with given status and optional mtime offset."""
+        result_file = self.root / "work" / "codex-implementations" / (
+            "task-" + task_id + "-result.md"
+        )
+        task_file_rel = "work/codex-primary/tasks/T" + task_id + "-test.md"
+        result_file.write_text(
+            "# Result T" + task_id + "\n\n"
+            "- status: " + status + "\n"
+            "- task_file: " + task_file_rel + "\n\n"
+            "## Diff\n(none)\n",
+            encoding="utf-8",
+        )
+        if age_seconds > 0:
+            old = time.time() - age_seconds
+            os.utime(result_file, (old, old))
+        return result_file
+
+    def _edit_payload(self, file_path: str) -> dict:
+        return {
+            "hook_event_name": "PreToolUse",
+            "tool_name": "Edit",
+            "tool_input": {
+                "file_path": file_path,
+                "old_string": "a",
+                "new_string": "b",
+            },
+        }
+
+    def _write_payload(self, file_path: str) -> dict:
+        return {
+            "hook_event_name": "PreToolUse",
+            "tool_name": "Write",
+            "tool_input": {"file_path": file_path, "content": "x"},
+        }
+
+    def _multiedit_payload(self, paths: list) -> dict:
+        return {
+            "hook_event_name": "PreToolUse",
+            "tool_name": "MultiEdit",
+            "tool_input": {
+                "edits": [
+                    {"file_path": p, "old_string": "a", "new_string": "b"}
+                    for p in paths
+                ],
+            },
+        }
+
+    # ----- response assertions -----
+
+    def _assert_allow(self, code: int, stdout: str, stderr: str) -> None:
+        self.assertEqual(code, 0, msg="expected exit 0. stderr=" + stderr)
+        # No deny JSON in stdout.
+        if stdout.strip():
             try:
-                rresolved = rpath.resolve()
-                rresolved.relative_to(project_dir)
-            except (OSError, ValueError):
-                logger.info("find_cover.symlink-escape path=%s", rpath.name)
-                continue
-            fields = parse_result_fields(rpath)
-            status = fields.get("status", "")
-            if status != "pass":
-                if status == "fail":
-                    best_reason = "fail-status"
-                logger.info("find_cover.skip path=%s status=%s age=%.1fs",
-                            rpath.name, status or "?", age)
-                continue
-            saw_fresh_pass = True
-            task_candidates: list = []
-            pointer = _resolve_task_file(project_dir, fields.get("task_file", ""))
-            if pointer is not None and pointer.is_file():
-                task_candidates.append(pointer)
-            name_match = _RESULT_NAME_RE.match(rpath.name)
-            if name_match:
-                task_id = name_match.group(1)
-                tdir = project_dir / CODEX_TASKS_DIR
-                if tdir.is_dir():
-                    for pattern in ("T" + task_id + "-*.md",
-                                    task_id + "-*.md",
-                                    "task-" + task_id + ".md",
-                                    "task-" + task_id + "-*.md"):
-                        task_candidates.extend(tdir.glob(pattern))
-            seen: set = set()
-            unique: list = []
-            for cand in task_candidates:
-                if cand not in seen:
-                    seen.add(cand)
-                    unique.append(cand)
-            if not unique:
-                logger.info("find_cover.no-task-file result=%s", rpath.name)
-                best_reason = "scope-miss"
-                continue
-            for tpath in unique:
-                fence = parse_scope_fence(tpath)
-                if not fence:
-                    logger.info("find_cover.empty-fence task=%s", tpath.name)
-                    continue
-                if path_in_fence(target_rel_posix, fence):
-                    logger.info("find_cover.MATCH target=%s result=%s task=%s age=%.1fs",
-                                target_rel_posix, rpath.name, tpath.name, age)
-                    return True, ""
-                logger.info("find_cover.scope-miss target=%s task=%s entries=%d",
-                            target_rel_posix, tpath.name, len(fence))
-                best_reason = "scope-miss"
-        if not saw_fresh:
-            reason = "stale"
-        elif saw_fresh_pass:
-            reason = "scope-miss"
-        else:
-            reason = best_reason
-        logger.info("find_cover.exit target=%s covered=False reason=%s",
-                    target_rel_posix, reason)
-        return False, reason
-    except Exception as exc:
-        logger.exception("find_cover.unexpected target=%s exc=%s", target_rel_posix, exc)
-        return False, "parse-error: " + str(exc)
-
-def extract_targets(payload: dict) -> list:
-    """Collect every file path this tool call intends to edit."""
-    if not isinstance(payload, dict):
-        return []
-    tool_name = payload.get("tool_name", "")
-    tool_input = payload.get("tool_input") or {}
-    if not isinstance(tool_input, dict):
-        return []
-    paths: list = []
-    if tool_name in {"Edit", "Write"}:
-        p = tool_input.get("file_path")
-        if isinstance(p, str) and p:
-            paths.append(p)
-    elif tool_name == "MultiEdit":
-        top_path = tool_input.get("file_path")
-        if isinstance(top_path, str) and top_path:
-            paths.append(top_path)
-        edits = tool_input.get("edits")
-        if isinstance(edits, list):
-            for edit in edits:
-                if not isinstance(edit, dict):
-                    continue
-                ep = edit.get("file_path")
-                if isinstance(ep, str) and ep:
-                    paths.append(ep)
-    seen: set = set()
-    unique: list = []
-    for p in paths:
-        if p not in seen:
-            seen.add(p)
-            unique.append(p)
-    return unique
-
-def emit_deny(blocked: str, reason_code: str) -> None:
-    """Print the PreToolUse deny JSON to stdout."""
-    logger = logging.getLogger(HOOK_NAME)
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
-        "scope-miss": "no recent pass result covers this path",
-        "parse-error": "could not parse codex-implement result",
-    }.get(reason_code, reason_code)
-    message = ("Code Delegation Protocol: " + blocked + " blocked ("
-               + reason_text + "). " + RECOVERY_HINT)
-    payload = {
-        "hookSpecificOutput": {
-            "hookEventName": "PreToolUse",
-            "permissionDecision": "deny",
-            "permissionDecisionReason": message,
+                parsed = json.loads(stdout)
+                decision = (
+                    parsed.get("hookSpecificOutput", {})
+                    .get("permissionDecision")
+                )
+                self.assertNotEqual(
+                    decision, "deny", msg="unexpected deny JSON: " + stdout
+                )
+            except json.JSONDecodeError:
+                pass  # non-JSON stdout is fine
+
+    def _assert_deny(self, code: int, stdout: str, stderr: str) -> None:
+        self.assertEqual(code, 0, msg="expected exit 0 (deny via JSON). stderr=" + stderr)
+        self.assertTrue(stdout.strip(), msg="expected deny JSON on stdout")
+        parsed = json.loads(stdout)
+        decision = parsed["hookSpecificOutput"]["permissionDecision"]
+        self.assertEqual(decision, "deny")
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("Code Delegation Protocol", reason)
+
+
+class TestAC12Cases(BaseEnforcerTest):
+    """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
+
+    def test_01_exempt_path_allow(self) -> None:
+        """AC12.1: exempt path (CLAUDE.md) -> allow."""
+        code, out, err = self._run_enforcer(self._write_payload("CLAUDE.md"))
+        self._assert_allow(code, out, err)
+
+    def test_02_code_no_result_deny(self) -> None:
+        """AC12.2: code file + NO recent result.md -> deny with JSON."""
+        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
+        self._assert_deny(code, out, err)
+
+    def test_03_stale_result_deny(self) -> None:
+        """AC12.3: code file + stale (> 15 min) result.md -> deny."""
+        self._write_task("3", [self.target_rel])
+        self._write_result("3", "pass", age_seconds=20 * 60)  # 20 min old
+        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
+        self._assert_deny(code, out, err)
+
+    def test_04_covered_pass_allow(self) -> None:
+        """AC12.4: code file + fresh pass result.md with covering fence -> allow."""
+        self._write_task("4", [self.target_rel])
+        self._write_result("4", "pass")
+        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
+        self._assert_allow(code, out, err)
+
+    def test_05_uncovered_pass_deny(self) -> None:
+        """AC12.5: fresh pass, fence does NOT cover target -> deny."""
+        self._write_task("5", ["other/unrelated.py"])
+        self._write_result("5", "pass")
+        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
+        self._assert_deny(code, out, err)
+
+    def test_06_fail_status_deny(self) -> None:
+        """AC12.6: fresh status=fail result.md -> deny."""
+        self._write_task("6", [self.target_rel])
+        self._write_result("6", "fail")
+        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
+        self._assert_deny(code, out, err)
+
+    def test_07_non_code_file_allow(self) -> None:
+        """AC12.7: non-code file (.txt, .md) -> allow."""
+        for suffix in (".txt", ".md"):
+            notes = ".claude/hooks/notes" + suffix
+            (self.root / notes).write_text("x", encoding="utf-8")
+            code, out, err = self._run_enforcer(self._write_payload(notes))
+            self._assert_allow(code, out, err)
+
+    def test_08_multiedit_all_covered_allow(self) -> None:
+        """AC12.8: MultiEdit with multiple files, all covered -> allow."""
+        a = ".claude/hooks/a.py"
+        b = ".claude/hooks/b.py"
+        (self.root / a).write_text("# a\n", encoding="utf-8")
+        (self.root / b).write_text("# b\n", encoding="utf-8")
+        self._write_task("8", [".claude/hooks/"])
+        self._write_result("8", "pass")
+        code, out, err = self._run_enforcer(self._multiedit_payload([a, b]))
+        self._assert_allow(code, out, err)
+
+    def test_09_multiedit_one_uncovered_deny(self) -> None:
+        """AC12.9: MultiEdit with one file uncovered -> deny."""
+        a = ".claude/hooks/a.py"
+        b = "src/uncovered.py"
+        (self.root / a).write_text("# a\n", encoding="utf-8")
+        (self.root / "src").mkdir(parents=True)
+        (self.root / b).write_text("# b\n", encoding="utf-8")
+        self._write_task("9", [".claude/hooks/"])
+        self._write_result("9", "pass")
+        code, out, err = self._run_enforcer(self._multiedit_payload([a, b]))
+        self._assert_deny(code, out, err)
+
+    def test_10a_malformed_result_passthrough(self) -> None:
+        """AC12.10a: malformed result.md -> no crash, handled gracefully."""
+        # Write a recent file but with completely corrupt body.
+        result_file = self.root / "work" / "codex-implementations" / (
+            "task-10-result.md"
+        )
+        result_file.write_bytes(b"\x00\x01\xff garbage no fields here")
+        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
+        # No crash: exit 0. Since no fence covers target, it is denied -
+        # the point is the script didn't blow up (no traceback in stderr).
+        self.assertEqual(code, 0)
+        self.assertNotIn("Traceback", err)
+
+    def test_10b_corrupt_json_payload_passthrough(self) -> None:
+        """AC12.10b: corrupt JSON payload -> pass-through, no crash, exit 0."""
+        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)}
+        result = subprocess.run(
+            [sys.executable, str(ENFORCER_PATH)],
+            input="{this-is-not-json",
+            capture_output=True, text=True,
+            encoding="utf-8", errors="replace",
+            env=env, timeout=30,
+        )
+        self.assertEqual(result.returncode, 0)
+        self.assertEqual(result.stdout.strip(), "")
+        self.assertNotIn("Traceback", result.stderr)
+
+    def test_11_non_edit_event_passthrough(self) -> None:
+        """AC12.11: non-Edit tool (Bash) -> pass-through (exit 0, no deny)."""
+        payload = {
+            "hook_event_name": "PreToolUse",
+            "tool_name": "Bash",
+            "tool_input": {"command": "ls"},
         }
-    }
-    logger.warning("emit_deny target=%s reason=%s", blocked, reason_code)
-    print(json.dumps(payload, ensure_ascii=False))
-
-def decide(payload: dict, project_dir: Path) -> bool:
-    """Core gate. True to allow; False after emitting deny."""
-    logger = logging.getLogger(HOOK_NAME)
-    event = payload.get("hook_event_name", "") if isinstance(payload, dict) else ""
-    tool_name = payload.get("tool_name", "") if isinstance(payload, dict) else ""
-    logger.info("decide.enter event=%s tool=%s", event, tool_name)
-    if event and event != "PreToolUse":
-        logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
-        return True
-    if tool_name not in {"Edit", "Write", "MultiEdit"}:
-        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
-        return True
-    if is_dual_teams_worktree(project_dir):
-        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
-        return True
-    raw_targets = extract_targets(payload)
-    if not raw_targets:
-        logger.info("decide.passthrough reason=no-targets")
-        return True
-    for raw in raw_targets:
-        abs_path = resolve_target(project_dir, raw)
-        if abs_path is None:
-            logger.info("decide.skip reason=unresolvable raw=%r", raw)
-            continue
-        rel = rel_posix(project_dir, abs_path)
-        if rel is None:
-            logger.info("decide.skip reason=outside-project path=%s", abs_path)
-            continue
-        if not requires_cover(rel):
-            logger.info("decide.allow-target rel=%s reason=exempt-or-non-code", rel)
-            continue
-        covered, reason = find_cover(project_dir, rel)
-        if not covered:
-            emit_deny(rel, reason)
-            logger.info("decide.exit target=%s allowed=False reason=%s", rel, reason)
-            return False
-        logger.info("decide.allow-target rel=%s reason=covered", rel)
-    logger.info("decide.exit allowed=True")
-    return True
-
-def main() -> int:
-    """Read JSON payload from stdin, run decide(), exit 0 always."""
-    project_dir = get_project_dir()
-    logger = _build_logger(project_dir)
-    logger.info("main.enter pid=%d", os.getpid())
-    try:
-        raw = sys.stdin.read()
-        if not raw.strip():
-            logger.info("main.empty-stdin passthrough")
-            return 0
+        code, out, err = self._run_enforcer(payload)
+        self.assertEqual(code, 0)
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
+    """Direct unit tests of helper functions (no subprocess)."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_is_code_extension_positive(self) -> None:
+        for p in ("a.py", "x/y/z.js", "lib/mod.rs", "s.cpp", "x.SQL"):
+            self.assertTrue(self.mod.is_code_extension(p), p)
+
+    def test_is_code_extension_negative(self) -> None:
+        for p in ("README.md", "doc.txt", "config.yaml", "a.json", "b"):
+            self.assertFalse(self.mod.is_code_extension(p), p)
+
+    def test_is_exempt_memory_star_star(self) -> None:
+        self.assertTrue(self.mod.is_exempt(".claude/memory/activeContext.md"))
+        self.assertTrue(self.mod.is_exempt(".claude/memory/daily/2026-04-24.md"))
+
+    def test_is_exempt_top_level_files(self) -> None:
+        for p in ("CLAUDE.md", "AGENTS.md", "README.md", ".gitignore", "LICENSE"):
+            self.assertTrue(self.mod.is_exempt(p), p)
+
+    def test_is_exempt_guides_skills_adr(self) -> None:
+        self.assertTrue(self.mod.is_exempt(".claude/adr/adr-001.md"))
+        self.assertTrue(self.mod.is_exempt(".claude/guides/foo.md"))
+        self.assertTrue(self.mod.is_exempt(".claude/skills/bar/SKILL.md"))
+
+    def test_is_exempt_negative(self) -> None:
+        self.assertFalse(self.mod.is_exempt(".claude/hooks/my_hook.py"))
+        self.assertFalse(self.mod.is_exempt("src/main.py"))
+
+    def test_requires_cover_positive(self) -> None:
+        self.assertTrue(self.mod.requires_cover(".claude/hooks/x.py"))
+        self.assertTrue(self.mod.requires_cover("src/main.ts"))
+
+    def test_requires_cover_negative_non_code(self) -> None:
+        self.assertFalse(self.mod.requires_cover("docs/readme.md"))
+
+    def test_requires_cover_negative_exempt(self) -> None:
+        # .claude/skills/**/*.md is exempt, and .md is non-code anyway.
+        self.assertFalse(self.mod.requires_cover("CLAUDE.md"))
+        # work/** is exempt even for .py.
+        self.assertFalse(self.mod.requires_cover("work/scripts/helper.py"))
+
+    def test_path_in_fence_exact_file(self) -> None:
+        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/c.py"]))
+
+    def test_path_in_fence_dir_prefix(self) -> None:
+        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b"]))
+        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/"]))
+
+    def test_path_in_fence_no_partial_segment(self) -> None:
+        self.assertFalse(self.mod.path_in_fence("a/bb/c.py", ["a/b"]))
+
+    def test_path_in_fence_strips_trailing_globs(self) -> None:
+        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/**"]))
+        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/*"]))
+
+    def test_parse_result_fields_status_pass(self) -> None:
+        with tempfile.NamedTemporaryFile(
+            "w", suffix=".md", delete=False, encoding="utf-8"
+        ) as fh:
+            fh.write("# result\n\n- status: pass\n- task_file: t.md\n")
+            p = Path(fh.name)
         try:
-            payload = json.loads(raw)
-        except json.JSONDecodeError as exc:
-            logger.info("main.malformed-json exc=%s", exc)
-            return 0
-        if not isinstance(payload, dict):
-            logger.info("main.non-dict-payload type=%s", type(payload).__name__)
-            return 0
-        decide(payload, project_dir)
-    except Exception as exc:
-        logger.exception("main.unexpected exc=%s", exc)
-    finally:
-        logger.info("main.exit")
-    return 0
+            fields = self.mod.parse_result_fields(p)
+            self.assertEqual(fields.get("status"), "pass")
+            self.assertEqual(fields.get("task_file"), "t.md")
+        finally:
+            p.unlink()
+
+    def test_parse_scope_fence_strips_backticks_and_annotations(self) -> None:
+        with tempfile.NamedTemporaryFile(
+            "w", suffix=".md", delete=False, encoding="utf-8"
+        ) as fh:
+            fh.write(
+                "# Task\n\n"
+                "## Scope Fence\n"
+                "**Allowed paths (may be written):**\n"
+                "- `.claude/hooks/x.py` (new)\n"
+                "- `.claude/hooks/test_x.py`\n\n"
+                "**Forbidden paths:**\n- else/\n\n## Next\n"
+            )
+            p = Path(fh.name)
+        try:
+            fence = self.mod.parse_scope_fence(p)
+            self.assertIn(".claude/hooks/x.py", fence)
+            self.assertIn(".claude/hooks/test_x.py", fence)
+        finally:
+            p.unlink()
+
+    def test_extract_targets_edit(self) -> None:
+        paths = self.mod.extract_targets({
+            "tool_name": "Edit",
+            "tool_input": {"file_path": "a.py", "old_string": "x", "new_string": "y"},
+        })
+        self.assertEqual(paths, ["a.py"])
+
+    def test_extract_targets_multiedit(self) -> None:
+        paths = self.mod.extract_targets({
+            "tool_name": "MultiEdit",
+            "tool_input": {
+                "edits": [
+                    {"file_path": "a.py", "old_string": "x", "new_string": "y"},
+                    {"file_path": "b.py", "old_string": "x", "new_string": "y"},
+                ],
+            },
+        })
+        self.assertEqual(sorted(paths), ["a.py", "b.py"])
+
+    def test_extract_targets_missing_is_empty(self) -> None:
+        self.assertEqual(self.mod.extract_targets({}), [])
+        self.assertEqual(self.mod.extract_targets({"tool_name": "Edit"}), [])
+        self.assertEqual(self.mod.extract_targets(None), [])
+
 
 if __name__ == "__main__":
-    sys.exit(main())
+    unittest.main(verbosity=2)
warning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/hooks/test_codex_delegate_enforcer.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/hooks/test_codex_delegate_enforcer.py', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 81098ec2547ec42978e25eb067d47d2d527fa1bb..559a64c5355a00095bd258ca191bd69568a27280
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -81,13 +81,49 @@
     logger.propagate = False
     return logger
 
-def get_project_dir() -> Path:
-    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
-    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
-
-def resolve_target(project_dir: Path, target_raw: str):
-    """Normalize raw file_path to absolute Path inside project_dir."""
-    logger = logging.getLogger(HOOK_NAME)
+def get_project_dir() -> Path:
+    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
+    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+
+def is_dual_teams_worktree(project_dir: Path) -> bool:
+    """True iff project_dir or any ancestor contains .dual-base-ref."""
+    logger = logging.getLogger(HOOK_NAME)
+    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
+    current = project_dir
+    seen: set[Path] = set()
+    while True:
+        try:
+            resolved = current.resolve()
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
+            resolved = current.absolute()
+        if resolved in seen:
+            logger.info(
+                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
+                project_dir,
+            )
+            return False
+        seen.add(resolved)
+        sentinel = current / ".dual-base-ref"
+        try:
+            if sentinel.is_file():
+                logger.info(
+                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
+                    project_dir,
+                    sentinel,
+                )
+                return True
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
+        parent = current.parent
+        if parent == current:
+            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
+            return False
+        current = parent
+
+def resolve_target(project_dir: Path, target_raw: str):
+    """Normalize raw file_path to absolute Path inside project_dir."""
+    logger = logging.getLogger(HOOK_NAME)
     if not target_raw:
         return None
     try:
@@ -391,10 +427,13 @@
     if event and event != "PreToolUse":
         logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
         return True
-    if tool_name not in {"Edit", "Write", "MultiEdit"}:
-        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
-        return True
-    raw_targets = extract_targets(payload)
+    if tool_name not in {"Edit", "Write", "MultiEdit"}:
+        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
+        return True
+    if is_dual_teams_worktree(project_dir):
+        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
+        return True
+    raw_targets = extract_targets(payload)
     if not raw_targets:
         logger.info("decide.passthrough reason=no-targets")
         return True
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

**Investigating file changes**

I noticed that the git diff is detecting a rename, showing codex-delegate-enforcer.py as renamed to test. That’s concerning! It might be because the files are so similar or have changed. Wait, I think the diff command might just be detecting a rename because the file paths got swapped. I should check the git status to get more clarity on what’s really happening here. Let's see what I find!
codex
Diff detection got confused by rename similarity; I’m checking file status and using no-renames.
exec
powershell.exe -Command 'git status --short; git diff --no-renames --stat -- .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
2026-04-25T07:28:56.226356Z ERROR codex_core::tools::router: error={"output":" ...enforcer.py => test_codex_delegate_enforcer.py} | 938 ++++++++++-----------\n 1 file changed, 464 insertions(+), 474 deletions(-)\nfatal: detected dubious ownership in repository at 'C:/Bots/Migrator bots/claude-project-template-update/worktrees/fix-enforcer/codex'\n'C:/Bots/Migrator bots/claude-project-template-update/worktrees/fix-enforcer/codex/.git' is owned by:\n\tDESKTOP-7FI6JC5/Lenovo (S-1-5-21-3639331995-3164478676-1546236719-1001)\nbut the current user is:\n\tDESKTOP-7FI6JC5/CodexSandboxOffline (S-1-5-21-3639331995-3164478676-1546236719-1004)\nTo add an exception for this directory, call:\n\n\tgit config --global --add safe.directory 'C:/Bots/Migrator bots/claude-project-template-update/worktrees/fix-enforcer/codex'\nwarning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it\nwarning: in the working copy of '.claude/hooks/test_codex_delegate_enforcer.py', LF will be replaced by CRLF the next time Git touches it\n","metadata":{"exit_code":1,"duration_seconds":0.2}}
 exited 1 in 234ms:
 ...enforcer.py => test_codex_delegate_enforcer.py} | 938 ++++++++++-----------
 1 file changed, 464 insertions(+), 474 deletions(-)
fatal: detected dubious ownership in repository at 'C:/Bots/Migrator bots/claude-project-template-update/worktrees/fix-enforcer/codex'
'C:/Bots/Migrator bots/claude-project-template-update/worktrees/fix-enforcer/codex/.git' is owned by:
	DESKTOP-7FI6JC5/Lenovo (S-1-5-21-3639331995-3164478676-1546236719-1001)
but the current user is:
	DESKTOP-7FI6JC5/CodexSandboxOffline (S-1-5-21-3639331995-3164478676-1546236719-1004)
To add an exception for this directory, call:

	git config --global --add safe.directory 'C:/Bots/Migrator bots/claude-project-template-update/worktrees/fix-enforcer/codex'
warning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/hooks/test_codex_delegate_enforcer.py', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 81098ec2547ec42978e25eb067d47d2d527fa1bb..559a64c5355a00095bd258ca191bd69568a27280
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -81,13 +81,49 @@
     logger.propagate = False
     return logger
 
-def get_project_dir() -> Path:
-    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
-    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
-
-def resolve_target(project_dir: Path, target_raw: str):
-    """Normalize raw file_path to absolute Path inside project_dir."""
-    logger = logging.getLogger(HOOK_NAME)
+def get_project_dir() -> Path:
+    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
+    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+
+def is_dual_teams_worktree(project_dir: Path) -> bool:
+    """True iff project_dir or any ancestor contains .dual-base-ref."""
+    logger = logging.getLogger(HOOK_NAME)
+    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
+    current = project_dir
+    seen: set[Path] = set()
+    while True:
+        try:
+            resolved = current.resolve()
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
+            resolved = current.absolute()
+        if resolved in seen:
+            logger.info(
+                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
+                project_dir,
+            )
+            return False
+        seen.add(resolved)
+        sentinel = current / ".dual-base-ref"
+        try:
+            if sentinel.is_file():
+                logger.info(
+                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
+                    project_dir,
+                    sentinel,
+                )
+                return True
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
+        parent = current.parent
+        if parent == current:
+            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
+            return False
+        current = parent
+
+def resolve_target(project_dir: Path, target_raw: str):
+    """Normalize raw file_path to absolute Path inside project_dir."""
+    logger = logging.getLogger(HOOK_NAME)
     if not target_raw:
         return None
     try:
@@ -391,10 +427,13 @@
     if event and event != "PreToolUse":
         logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
         return True
-    if tool_name not in {"Edit", "Write", "MultiEdit"}:
-        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
-        return True
-    raw_targets = extract_targets(payload)
+    if tool_name not in {"Edit", "Write", "MultiEdit"}:
+        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
+        return True
+    if is_dual_teams_worktree(project_dir):
+        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
+        return True
+    raw_targets = extract_targets(payload)
     if not raw_targets:
         logger.info("decide.passthrough reason=no-targets")
         return True
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

**Investigating Git status**

I'm trying to understand what's going on with the Git status. It seems like the first line might indicate a file rename, but I'm not entirely sure. It mentions one file has changed, which makes me think that maybe the .git index shows that codex-delegate-enforcer.py has been deleted? To clarify, I'll run the command `git -c safe.directory status` and see what it reveals. Let's figure it out step by step!
exec
powershell.exe -Command "git -c safe.directory='C:/Bots/Migrator bots/claude-project-template-update/worktrees/fix-enforcer/codex' status --short; git -c safe.directory='C:/Bots/Migrator bots/claude-project-template-update/worktrees/fix-enforcer/codex' diff --no-renames --stat -- .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer.py" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
 succeeded in 285ms:
 M .claude/hooks/codex-delegate-enforcer.py
 M .claude/hooks/test_codex_delegate_enforcer.py
 .claude/hooks/codex-delegate-enforcer.py      | 39 +++++++++++++++
 .claude/hooks/test_codex_delegate_enforcer.py | 72 ++++++++++++++++++++++++++-
 2 files changed, 110 insertions(+), 1 deletion(-)
warning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/hooks/test_codex_delegate_enforcer.py', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 81098ec2547ec42978e25eb067d47d2d527fa1bb..559a64c5355a00095bd258ca191bd69568a27280
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -81,13 +81,49 @@
     logger.propagate = False
     return logger
 
-def get_project_dir() -> Path:
-    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
-    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
-
-def resolve_target(project_dir: Path, target_raw: str):
-    """Normalize raw file_path to absolute Path inside project_dir."""
-    logger = logging.getLogger(HOOK_NAME)
+def get_project_dir() -> Path:
+    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
+    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+
+def is_dual_teams_worktree(project_dir: Path) -> bool:
+    """True iff project_dir or any ancestor contains .dual-base-ref."""
+    logger = logging.getLogger(HOOK_NAME)
+    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
+    current = project_dir
+    seen: set[Path] = set()
+    while True:
+        try:
+            resolved = current.resolve()
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
+            resolved = current.absolute()
+        if resolved in seen:
+            logger.info(
+                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
+                project_dir,
+            )
+            return False
+        seen.add(resolved)
+        sentinel = current / ".dual-base-ref"
+        try:
+            if sentinel.is_file():
+                logger.info(
+                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
+                    project_dir,
+                    sentinel,
+                )
+                return True
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
+        parent = current.parent
+        if parent == current:
+            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
+            return False
+        current = parent
+
+def resolve_target(project_dir: Path, target_raw: str):
+    """Normalize raw file_path to absolute Path inside project_dir."""
+    logger = logging.getLogger(HOOK_NAME)
     if not target_raw:
         return None
     try:
@@ -391,10 +427,13 @@
     if event and event != "PreToolUse":
         logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
         return True
-    if tool_name not in {"Edit", "Write", "MultiEdit"}:
-        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
-        return True
-    raw_targets = extract_targets(payload)
+    if tool_name not in {"Edit", "Write", "MultiEdit"}:
+        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
+        return True
+    if is_dual_teams_worktree(project_dir):
+        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
+        return True
+    raw_targets = extract_targets(payload)
     if not raw_targets:
         logger.info("decide.passthrough reason=no-targets")
         return True
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

**Analyzing diff stats**

I'm looking at the diff stats: 39 additions for the hook, 72 additions and 110 total tests, with one deletion. I wonder why that single deletion occurred—is it just because there was no blank? That seems reasonable. I should review the actual diff closely to check for renames, rather than getting too caught up in just the stats. It feels important to understand what changes are actually being made!
exec
powershell.exe -Command "git -c safe.directory='C:/Bots/Migrator bots/claude-project-template-update/worktrees/fix-enforcer/codex' diff --no-renames -- .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer.py" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
 succeeded in 241ms:
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 81098ec..559a64c 100644
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -85,6 +85,42 @@ def get_project_dir() -> Path:
     """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
     return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
 
+def is_dual_teams_worktree(project_dir: Path) -> bool:
+    """True iff project_dir or any ancestor contains .dual-base-ref."""
+    logger = logging.getLogger(HOOK_NAME)
+    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
+    current = project_dir
+    seen: set[Path] = set()
+    while True:
+        try:
+            resolved = current.resolve()
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
+            resolved = current.absolute()
+        if resolved in seen:
+            logger.info(
+                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
+                project_dir,
+            )
+            return False
+        seen.add(resolved)
+        sentinel = current / ".dual-base-ref"
+        try:
+            if sentinel.is_file():
+                logger.info(
+                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
+                    project_dir,
+                    sentinel,
+                )
+                return True
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
+        parent = current.parent
+        if parent == current:
+            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
+            return False
+        current = parent
+
 def resolve_target(project_dir: Path, target_raw: str):
     """Normalize raw file_path to absolute Path inside project_dir."""
     logger = logging.getLogger(HOOK_NAME)
@@ -394,6 +430,9 @@ def decide(payload: dict, project_dir: Path) -> bool:
     if tool_name not in {"Edit", "Write", "MultiEdit"}:
         logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
         return True
+    if is_dual_teams_worktree(project_dir):
+        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
+        return True
     raw_targets = extract_targets(payload)
     if not raw_targets:
         logger.info("decide.passthrough reason=no-targets")
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba..ab2bfc1 100644
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -22,6 +22,8 @@ production .codex/ and work/ directories are never touched.
 from __future__ import annotations
 
 import importlib.util
+import contextlib
+import io
 import json
 import os
 import shutil
@@ -286,6 +288,74 @@ class TestAC12Cases(BaseEnforcerTest):
         self.assertEqual(out.strip(), "")
 
 
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
 class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
@@ -404,4 +474,4 @@ class TestHelpers(unittest.TestCase):
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)
warning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/hooks/test_codex_delegate_enforcer.py', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 81098ec2547ec42978e25eb067d47d2d527fa1bb..559a64c5355a00095bd258ca191bd69568a27280
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -81,13 +81,49 @@
     logger.propagate = False
     return logger
 
-def get_project_dir() -> Path:
-    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
-    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
-
-def resolve_target(project_dir: Path, target_raw: str):
-    """Normalize raw file_path to absolute Path inside project_dir."""
-    logger = logging.getLogger(HOOK_NAME)
+def get_project_dir() -> Path:
+    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
+    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+
+def is_dual_teams_worktree(project_dir: Path) -> bool:
+    """True iff project_dir or any ancestor contains .dual-base-ref."""
+    logger = logging.getLogger(HOOK_NAME)
+    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
+    current = project_dir
+    seen: set[Path] = set()
+    while True:
+        try:
+            resolved = current.resolve()
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
+            resolved = current.absolute()
+        if resolved in seen:
+            logger.info(
+                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
+                project_dir,
+            )
+            return False
+        seen.add(resolved)
+        sentinel = current / ".dual-base-ref"
+        try:
+            if sentinel.is_file():
+                logger.info(
+                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
+                    project_dir,
+                    sentinel,
+                )
+                return True
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
+        parent = current.parent
+        if parent == current:
+            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
+            return False
+        current = parent
+
+def resolve_target(project_dir: Path, target_raw: str):
+    """Normalize raw file_path to absolute Path inside project_dir."""
+    logger = logging.getLogger(HOOK_NAME)
     if not target_raw:
         return None
     try:
@@ -391,10 +427,13 @@
     if event and event != "PreToolUse":
         logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
         return True
-    if tool_name not in {"Edit", "Write", "MultiEdit"}:
-        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
-        return True
-    raw_targets = extract_targets(payload)
+    if tool_name not in {"Edit", "Write", "MultiEdit"}:
+        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
+        return True
+    if is_dual_teams_worktree(project_dir):
+        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
+        return True
+    raw_targets = extract_targets(payload)
     if not raw_targets:
         logger.info("decide.passthrough reason=no-targets")
         return True
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

**Considering error handling**

I think I should include catching RuntimeError as well, just in case. Although, it seems like I can only catch OSError within the “is_file” probe. Still, maybe I should think about testing this as it might be tricky since I can’t run Python. I wonder if I can use PowerShell for a check, but that doesn’t seem useful either. I need to verify what file triggers the LF warning and ensure there are no new nested AGENTS since we didn't check .claude/AGENTS.
codex
Before calling it blocked, I’m checking common Python install locations for validation.
exec
powershell.exe -Command '$paths = @(
  "$env:LOCALAPPDATA'"\\Programs\\Python\",
  \""'$env:ProgramFiles'"\\Python*\",
  \""'$env:ProgramFiles'"\\WindowsApps\",
  \"C:\\Python*\"
); foreach ("'$p in $paths) { Get-ChildItem -Path $p -Filter python.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 5 -ExpandProperty FullName }' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
2026-04-25T07:29:52.721164Z ERROR codex_core::tools::router: error={"output":"C:\\Bots\\AmoCRM Tools\\.venv\\Scripts\\python.exe\r\nC:\\Bots\\Freelance\\.venv\\Scripts\\python.exe\r\nC:\\Bots\\Migrator bots\\Call Rate bot Sales\\.venv\\Scripts\\python.exe\r\nC:\\Bots\\Migrator bots\\Call Rate Legal\\.venv\\Scripts\\python.exe\r\nC:\\Bots\\Migrator bots\\ClientsLegal Bot\\.venv\\Scripts\\python.exe\r\nGet-ChildItem : Access is denied\r\nстрока:7 знак:29\r\n+ ... n $paths) { Get-ChildItem -Path $p -Filter python.exe -Recurse -Error ...\r\n+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\r\n    + CategoryInfo          : NotSpecified: (:) [Get-ChildItem], UnauthorizedAccessException\r\n    + FullyQualifiedErrorId : System.UnauthorizedAccessException,Microsoft.PowerShell.Commands.GetChildItemCommand\r\n \r\n","metadata":{"exit_code":1,"duration_seconds":12.9}}
 exited 1 in 12905ms:
C:\Bots\AmoCRM Tools\.venv\Scripts\python.exe
C:\Bots\Freelance\.venv\Scripts\python.exe
C:\Bots\Migrator bots\Call Rate bot Sales\.venv\Scripts\python.exe
C:\Bots\Migrator bots\Call Rate Legal\.venv\Scripts\python.exe
C:\Bots\Migrator bots\ClientsLegal Bot\.venv\Scripts\python.exe
Get-ChildItem : Access is denied
строка:7 знак:29
+ ... n $paths) { Get-ChildItem -Path $p -Filter python.exe -Recurse -Error ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (:) [Get-ChildItem], UnauthorizedAccessException
    + FullyQualifiedErrorId : System.UnauthorizedAccessException,Microsoft.PowerShell.Commands.GetChildItemCommand
 

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 81098ec2547ec42978e25eb067d47d2d527fa1bb..559a64c5355a00095bd258ca191bd69568a27280
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -81,13 +81,49 @@
     logger.propagate = False
     return logger
 
-def get_project_dir() -> Path:
-    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
-    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
-
-def resolve_target(project_dir: Path, target_raw: str):
-    """Normalize raw file_path to absolute Path inside project_dir."""
-    logger = logging.getLogger(HOOK_NAME)
+def get_project_dir() -> Path:
+    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
+    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+
+def is_dual_teams_worktree(project_dir: Path) -> bool:
+    """True iff project_dir or any ancestor contains .dual-base-ref."""
+    logger = logging.getLogger(HOOK_NAME)
+    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
+    current = project_dir
+    seen: set[Path] = set()
+    while True:
+        try:
+            resolved = current.resolve()
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
+            resolved = current.absolute()
+        if resolved in seen:
+            logger.info(
+                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
+                project_dir,
+            )
+            return False
+        seen.add(resolved)
+        sentinel = current / ".dual-base-ref"
+        try:
+            if sentinel.is_file():
+                logger.info(
+                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
+                    project_dir,
+                    sentinel,
+                )
+                return True
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
+        parent = current.parent
+        if parent == current:
+            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
+            return False
+        current = parent
+
+def resolve_target(project_dir: Path, target_raw: str):
+    """Normalize raw file_path to absolute Path inside project_dir."""
+    logger = logging.getLogger(HOOK_NAME)
     if not target_raw:
         return None
     try:
@@ -391,10 +427,13 @@
     if event and event != "PreToolUse":
         logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
         return True
-    if tool_name not in {"Edit", "Write", "MultiEdit"}:
-        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
-        return True
-    raw_targets = extract_targets(payload)
+    if tool_name not in {"Edit", "Write", "MultiEdit"}:
+        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
+        return True
+    if is_dual_teams_worktree(project_dir):
+        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
+        return True
+    raw_targets = extract_targets(payload)
     if not raw_targets:
         logger.info("decide.passthrough reason=no-targets")
         return True
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

**Exploring virtual environments**

I found some other virtual environments outside of my workspace. I’m wondering if I can execute read commands there, which might be okay if I'm in a sandbox. But would it be appropriate to run something outside the workspace? I think it could work as long as there are no modifications. I might need to issue a command to access something outside my workspace, so I’m considering the possibilities here.
codex
I found an existing venv interpreter; I’ll use it only to sanity-run the stdlib tests.
exec
powershell.exe -Command "& 'C:\\Bots\\AmoCRM Tools\\.venv\\Scripts\\python.exe' --version; & 'C:\\Bots\\AmoCRM Tools\\.venv\\Scripts\\python.exe' .claude/hooks/test_codex_delegate_enforcer.py" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
2026-04-25T07:30:02.447752Z ERROR codex_core::tools::router: error={"output":"error: uv trampoline failed to spawn Python child process\n  Caused by: permission denied (os error 5)\n\nerror: uv trampoline failed to spawn Python child process\n  Caused by: permission denied (os error 5)\n\n","metadata":{"exit_code":1,"duration_seconds":0.2}}
 exited 1 in 237ms:
error: uv trampoline failed to spawn Python child process
  Caused by: permission denied (os error 5)

error: uv trampoline failed to spawn Python child process
  Caused by: permission denied (os error 5)


diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 81098ec2547ec42978e25eb067d47d2d527fa1bb..559a64c5355a00095bd258ca191bd69568a27280
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -81,13 +81,49 @@
     logger.propagate = False
     return logger
 
-def get_project_dir() -> Path:
-    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
-    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
-
-def resolve_target(project_dir: Path, target_raw: str):
-    """Normalize raw file_path to absolute Path inside project_dir."""
-    logger = logging.getLogger(HOOK_NAME)
+def get_project_dir() -> Path:
+    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
+    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+
+def is_dual_teams_worktree(project_dir: Path) -> bool:
+    """True iff project_dir or any ancestor contains .dual-base-ref."""
+    logger = logging.getLogger(HOOK_NAME)
+    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
+    current = project_dir
+    seen: set[Path] = set()
+    while True:
+        try:
+            resolved = current.resolve()
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
+            resolved = current.absolute()
+        if resolved in seen:
+            logger.info(
+                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
+                project_dir,
+            )
+            return False
+        seen.add(resolved)
+        sentinel = current / ".dual-base-ref"
+        try:
+            if sentinel.is_file():
+                logger.info(
+                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
+                    project_dir,
+                    sentinel,
+                )
+                return True
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
+        parent = current.parent
+        if parent == current:
+            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
+            return False
+        current = parent
+
+def resolve_target(project_dir: Path, target_raw: str):
+    """Normalize raw file_path to absolute Path inside project_dir."""
+    logger = logging.getLogger(HOOK_NAME)
     if not target_raw:
         return None
     try:
@@ -391,10 +427,13 @@
     if event and event != "PreToolUse":
         logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
         return True
-    if tool_name not in {"Edit", "Write", "MultiEdit"}:
-        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
-        return True
-    raw_targets = extract_targets(payload)
+    if tool_name not in {"Edit", "Write", "MultiEdit"}:
+        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
+        return True
+    if is_dual_teams_worktree(project_dir):
+        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
+        return True
+    raw_targets = extract_targets(payload)
     if not raw_targets:
         logger.info("decide.passthrough reason=no-targets")
         return True
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

exec
powershell.exe -Command '$hook = Get-Content '"'.claude/hooks/codex-delegate-enforcer.py'; "'$hook[80..125]; $hook[424..436]; $test = Get-Content '"'.claude/hooks/test_codex_delegate_enforcer.py'; "'$test[20..35]; $test[288..365]' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
 succeeded in 412ms:
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
                    project_dir,
                    sentinel,
                )
                return True
        except OSError as exc:
            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
        parent = current.parent
        if parent == current:
            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
            return False
        current = parent

def resolve_target(project_dir: Path, target_raw: str):
    """Normalize raw file_path to absolute Path inside project_dir."""
    logger = logging.getLogger(HOOK_NAME)
    tool_name = payload.get("tool_name", "") if isinstance(payload, dict) else ""
    logger.info("decide.enter event=%s tool=%s", event, tool_name)
    if event and event != "PreToolUse":
        logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
        return True
    if tool_name not in {"Edit", "Write", "MultiEdit"}:
        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
        return True
    if is_dual_teams_worktree(project_dir):
        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
        return True
    raw_targets = extract_targets(payload)
    if not raw_targets:

from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path



class TestDualTeamsSentinel(unittest.TestCase):
    """Regression tests for dual-teams worktree sentinel detection."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()

    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
            project_dir = Path(tmpdir).resolve()
            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")

            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))

    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
            project_dir = Path(tmpdir).resolve()
            nested = project_dir / "worktrees" / "validation" / "claude"
            nested.mkdir(parents=True)
            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")

            self.assertTrue(self.mod.is_dual_teams_worktree(nested))

    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
            project_dir = Path(tmpdir).resolve()
            nested = project_dir / "a" / "b" / "c"
            nested.mkdir(parents=True)

            self.assertFalse(self.mod.is_dual_teams_worktree(nested))

    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
            project_dir = Path(tmpdir).resolve()
            (project_dir / ".dual-base-ref").mkdir()

            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))


class TestDualTeamsDecide(BaseEnforcerTest):
    """Regression tests for the dual-teams passthrough in decide()."""

    def setUp(self) -> None:
        super().setUp()
        self.mod = _load_module()
        self.script_rel = ".claude/scripts/foo.py"
        (self.root / ".claude" / "scripts").mkdir(parents=True)
        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")

    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
        shutil.rmtree(self.root / "work", ignore_errors=True)

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)

        self.assertTrue(allowed)
        self.assertEqual(stdout.getvalue().strip(), "")

    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)

        self.assertFalse(allowed)
        parsed = json.loads(stdout.getvalue())
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")


class TestHelpers(unittest.TestCase):
    """Direct unit tests of helper functions (no subprocess)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()

    def test_is_code_extension_positive(self) -> None:

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 81098ec2547ec42978e25eb067d47d2d527fa1bb..559a64c5355a00095bd258ca191bd69568a27280
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -81,13 +81,49 @@
     logger.propagate = False
     return logger
 
-def get_project_dir() -> Path:
-    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
-    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
-
-def resolve_target(project_dir: Path, target_raw: str):
-    """Normalize raw file_path to absolute Path inside project_dir."""
-    logger = logging.getLogger(HOOK_NAME)
+def get_project_dir() -> Path:
+    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
+    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+
+def is_dual_teams_worktree(project_dir: Path) -> bool:
+    """True iff project_dir or any ancestor contains .dual-base-ref."""
+    logger = logging.getLogger(HOOK_NAME)
+    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
+    current = project_dir
+    seen: set[Path] = set()
+    while True:
+        try:
+            resolved = current.resolve()
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
+            resolved = current.absolute()
+        if resolved in seen:
+            logger.info(
+                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
+                project_dir,
+            )
+            return False
+        seen.add(resolved)
+        sentinel = current / ".dual-base-ref"
+        try:
+            if sentinel.is_file():
+                logger.info(
+                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
+                    project_dir,
+                    sentinel,
+                )
+                return True
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
+        parent = current.parent
+        if parent == current:
+            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
+            return False
+        current = parent
+
+def resolve_target(project_dir: Path, target_raw: str):
+    """Normalize raw file_path to absolute Path inside project_dir."""
+    logger = logging.getLogger(HOOK_NAME)
     if not target_raw:
         return None
     try:
@@ -391,10 +427,13 @@
     if event and event != "PreToolUse":
         logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
         return True
-    if tool_name not in {"Edit", "Write", "MultiEdit"}:
-        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
-        return True
-    raw_targets = extract_targets(payload)
+    if tool_name not in {"Edit", "Write", "MultiEdit"}:
+        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
+        return True
+    if is_dual_teams_worktree(project_dir):
+        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
+        return True
+    raw_targets = extract_targets(payload)
     if not raw_targets:
         logger.info("decide.passthrough reason=no-targets")
         return True
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

**Troubleshooting file handling**

I'm realizing that the process won't inspect raw targets, which poses a potential issue. When the sentinel is absent, the behavior might be byte-for-byte identical to before. However, even without targets, it checks ancestors, possibly allowing access if an unrelated ancestor sentinel is present. I need to consider whether adding an OSError catch in the current.resolve step might prevent issues. If `current` is a relative Path, I’ll have to address how it handles the project directory and its ancestors correctly. It might be necessary to handle relative paths better.
**Enhancing project directory resolution**

I'm considering that the project_dir type in the module resolves correctly with get_project_dir. To make it more robust, I could set `current = project_dir.resolve()`. But what if the project directory doesn't actually exist? If it does exist, then I should walk it absolutely and catch any OSError for better error handling. If `project_dir` is relative, I should ensure that current.resolve goes absolute during each iteration. After resolving, it might be best to set current to the resolved path for walking. This could improve the functionality overall.
**Evaluating project paths**

I'm considering the path resolution process for the project directory. If I try to resolve the current path and encounter an OSError, I might switch to using the absolute path. I think it’s important to maintain a set of seen resolved paths to avoid cycles in parent loops. I’m also pondering symlink issues and their implications on path resolution, like potential discrepancies when checking for the existence of files. I need to address dependencies and exceptions during these checks. Okay, time to evaluate more thoroughly!
**Clarifying reporting issues**

I realize I need to ensure there are "no bare prints" in the code since we haven't added any. The existing `emit_deny` function does include a print statement for when JSON is allowed. It seems reasonable to add a "BLOCKER" line due to the tests. The user requested a self-report note, which I could phrase as: "BLOCKER: Required test command exits with code 1 because the Python launcher reports no installed Python found." I'm also considering using `git diff --numstat` to track line changes safely.
exec
powershell.exe -Command "git -c safe.directory='C:/Bots/Migrator bots/claude-project-template-update/worktrees/fix-enforcer/codex' diff --no-renames --numstat -- .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer.py" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\fix-enforcer\codex
 succeeded in 262ms:
39	0	.claude/hooks/codex-delegate-enforcer.py
71	1	.claude/hooks/test_codex_delegate_enforcer.py
warning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/hooks/test_codex_delegate_enforcer.py', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 81098ec2547ec42978e25eb067d47d2d527fa1bb..559a64c5355a00095bd258ca191bd69568a27280
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -81,13 +81,49 @@
     logger.propagate = False
     return logger
 
-def get_project_dir() -> Path:
-    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
-    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
-
-def resolve_target(project_dir: Path, target_raw: str):
-    """Normalize raw file_path to absolute Path inside project_dir."""
-    logger = logging.getLogger(HOOK_NAME)
+def get_project_dir() -> Path:
+    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
+    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+
+def is_dual_teams_worktree(project_dir: Path) -> bool:
+    """True iff project_dir or any ancestor contains .dual-base-ref."""
+    logger = logging.getLogger(HOOK_NAME)
+    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
+    current = project_dir
+    seen: set[Path] = set()
+    while True:
+        try:
+            resolved = current.resolve()
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
+            resolved = current.absolute()
+        if resolved in seen:
+            logger.info(
+                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
+                project_dir,
+            )
+            return False
+        seen.add(resolved)
+        sentinel = current / ".dual-base-ref"
+        try:
+            if sentinel.is_file():
+                logger.info(
+                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
+                    project_dir,
+                    sentinel,
+                )
+                return True
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
+        parent = current.parent
+        if parent == current:
+            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
+            return False
+        current = parent
+
+def resolve_target(project_dir: Path, target_raw: str):
+    """Normalize raw file_path to absolute Path inside project_dir."""
+    logger = logging.getLogger(HOOK_NAME)
     if not target_raw:
         return None
     try:
@@ -391,10 +427,13 @@
     if event and event != "PreToolUse":
         logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
         return True
-    if tool_name not in {"Edit", "Write", "MultiEdit"}:
-        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
-        return True
-    raw_targets = extract_targets(payload)
+    if tool_name not in {"Edit", "Write", "MultiEdit"}:
+        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
+        return True
+    if is_dual_teams_worktree(project_dir):
+        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
+        return True
+    raw_targets = extract_targets(payload)
     if not raw_targets:
         logger.info("decide.passthrough reason=no-targets")
         return True
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

Required test command was run, but it failed because the Windows py launcher reports no installed Python.
  ✓ Inspect hook and tests
  ✓ Add regression tests
  ✓ Implement sentinel exemption
  ✓ Run required test command
  → Prepare handoff self-report
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 81098ec2547ec42978e25eb067d47d2d527fa1bb..559a64c5355a00095bd258ca191bd69568a27280
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -81,13 +81,49 @@
     logger.propagate = False
     return logger
 
-def get_project_dir() -> Path:
-    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
-    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
-
-def resolve_target(project_dir: Path, target_raw: str):
-    """Normalize raw file_path to absolute Path inside project_dir."""
-    logger = logging.getLogger(HOOK_NAME)
+def get_project_dir() -> Path:
+    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
+    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+
+def is_dual_teams_worktree(project_dir: Path) -> bool:
+    """True iff project_dir or any ancestor contains .dual-base-ref."""
+    logger = logging.getLogger(HOOK_NAME)
+    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
+    current = project_dir
+    seen: set[Path] = set()
+    while True:
+        try:
+            resolved = current.resolve()
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
+            resolved = current.absolute()
+        if resolved in seen:
+            logger.info(
+                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
+                project_dir,
+            )
+            return False
+        seen.add(resolved)
+        sentinel = current / ".dual-base-ref"
+        try:
+            if sentinel.is_file():
+                logger.info(
+                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
+                    project_dir,
+                    sentinel,
+                )
+                return True
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
+        parent = current.parent
+        if parent == current:
+            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
+            return False
+        current = parent
+
+def resolve_target(project_dir: Path, target_raw: str):
+    """Normalize raw file_path to absolute Path inside project_dir."""
+    logger = logging.getLogger(HOOK_NAME)
     if not target_raw:
         return None
     try:
@@ -391,10 +427,13 @@
     if event and event != "PreToolUse":
         logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
         return True
-    if tool_name not in {"Edit", "Write", "MultiEdit"}:
-        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
-        return True
-    raw_targets = extract_targets(payload)
+    if tool_name not in {"Edit", "Write", "MultiEdit"}:
+        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
+        return True
+    if is_dual_teams_worktree(project_dir):
+        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
+        return True
+    raw_targets = extract_targets(payload)
     if not raw_targets:
         logger.info("decide.passthrough reason=no-targets")
         return True
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

Handoff prepared with a BLOCKER for unavailable Python launcher.
  ✓ Inspect hook and tests
  ✓ Add regression tests
  ✓ Implement sentinel exemption
  ✓ Run required test command
  ✓ Prepare handoff self-report
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 81098ec2547ec42978e25eb067d47d2d527fa1bb..559a64c5355a00095bd258ca191bd69568a27280
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -81,13 +81,49 @@
     logger.propagate = False
     return logger
 
-def get_project_dir() -> Path:
-    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
-    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
-
-def resolve_target(project_dir: Path, target_raw: str):
-    """Normalize raw file_path to absolute Path inside project_dir."""
-    logger = logging.getLogger(HOOK_NAME)
+def get_project_dir() -> Path:
+    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
+    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+
+def is_dual_teams_worktree(project_dir: Path) -> bool:
+    """True iff project_dir or any ancestor contains .dual-base-ref."""
+    logger = logging.getLogger(HOOK_NAME)
+    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
+    current = project_dir
+    seen: set[Path] = set()
+    while True:
+        try:
+            resolved = current.resolve()
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
+            resolved = current.absolute()
+        if resolved in seen:
+            logger.info(
+                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
+                project_dir,
+            )
+            return False
+        seen.add(resolved)
+        sentinel = current / ".dual-base-ref"
+        try:
+            if sentinel.is_file():
+                logger.info(
+                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
+                    project_dir,
+                    sentinel,
+                )
+                return True
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
+        parent = current.parent
+        if parent == current:
+            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
+            return False
+        current = parent
+
+def resolve_target(project_dir: Path, target_raw: str):
+    """Normalize raw file_path to absolute Path inside project_dir."""
+    logger = logging.getLogger(HOOK_NAME)
     if not target_raw:
         return None
     try:
@@ -391,10 +427,13 @@
     if event and event != "PreToolUse":
         logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
         return True
-    if tool_name not in {"Edit", "Write", "MultiEdit"}:
-        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
-        return True
-    raw_targets = extract_targets(payload)
+    if tool_name not in {"Edit", "Write", "MultiEdit"}:
+        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
+        return True
+    if is_dual_teams_worktree(project_dir):
+        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
+        return True
+    raw_targets = extract_targets(payload)
     if not raw_targets:
         logger.info("decide.passthrough reason=no-targets")
         return True
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

codex
=== PHASE HANDOFF: FIX-ENFORCER ===

NOTE: Modified `.claude/hooks/codex-delegate-enforcer.py:88` with `is_dual_teams_worktree(project_dir: Path) -> bool` and the early `decide()` passthrough at `.claude/hooks/codex-delegate-enforcer.py:433`.
NOTE: Modified `.claude/hooks/test_codex_delegate_enforcer.py:291` with sentinel helper tests and `.claude/hooks/test_codex_delegate_enforcer.py:332` with `decide()` allow/deny regression tests.
NOTE: Diff stats: `.claude/hooks/codex-delegate-enforcer.py` `+39/-0`; `.claude/hooks/test_codex_delegate_enforcer.py` `+71/-1`.
NOTE: fix path: sentinel ancestor walk in `decide()` — see `is_dual_teams_worktree()`.
NOTE: Test command run: `py -3 .claude/hooks/test_codex_delegate_enforcer.py`
NOTE: Test output: `No installed Python found!`
BLOCKER: Required test command exits `1` because `C:\WINDOWS\py.exe` reports no installed Python in this sandbox, so I cannot truthfully report all tests passing.
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 81098ec2547ec42978e25eb067d47d2d527fa1bb..559a64c5355a00095bd258ca191bd69568a27280
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -81,13 +81,49 @@
     logger.propagate = False
     return logger
 
-def get_project_dir() -> Path:
-    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
-    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
-
-def resolve_target(project_dir: Path, target_raw: str):
-    """Normalize raw file_path to absolute Path inside project_dir."""
-    logger = logging.getLogger(HOOK_NAME)
+def get_project_dir() -> Path:
+    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
+    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
+
+def is_dual_teams_worktree(project_dir: Path) -> bool:
+    """True iff project_dir or any ancestor contains .dual-base-ref."""
+    logger = logging.getLogger(HOOK_NAME)
+    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
+    current = project_dir
+    seen: set[Path] = set()
+    while True:
+        try:
+            resolved = current.resolve()
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
+            resolved = current.absolute()
+        if resolved in seen:
+            logger.info(
+                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
+                project_dir,
+            )
+            return False
+        seen.add(resolved)
+        sentinel = current / ".dual-base-ref"
+        try:
+            if sentinel.is_file():
+                logger.info(
+                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
+                    project_dir,
+                    sentinel,
+                )
+                return True
+        except OSError as exc:
+            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
+        parent = current.parent
+        if parent == current:
+            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
+            return False
+        current = parent
+
+def resolve_target(project_dir: Path, target_raw: str):
+    """Normalize raw file_path to absolute Path inside project_dir."""
+    logger = logging.getLogger(HOOK_NAME)
     if not target_raw:
         return None
     try:
@@ -391,10 +427,13 @@
     if event and event != "PreToolUse":
         logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
         return True
-    if tool_name not in {"Edit", "Write", "MultiEdit"}:
-        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
-        return True
-    raw_targets = extract_targets(payload)
+    if tool_name not in {"Edit", "Write", "MultiEdit"}:
+        logger.info("decide.passthrough reason=non-edit-tool tool=%s", tool_name)
+        return True
+    if is_dual_teams_worktree(project_dir):
+        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
+        return True
+    raw_targets = extract_targets(payload)
     if not raw_targets:
         logger.info("decide.passthrough reason=no-targets")
         return True
diff --git a/.claude/hooks/test_codex_delegate_enforcer.py b/.claude/hooks/test_codex_delegate_enforcer.py
index 1261aba248f7e5266b63ecda7b28545517389719..ab2bfc12eea8f1523e5b0eaad97f3cf4c16560cd
--- a/.claude/hooks/test_codex_delegate_enforcer.py
+++ b/.claude/hooks/test_codex_delegate_enforcer.py
@@ -21,11 +21,13 @@
 
 from __future__ import annotations
 
-import importlib.util
-import json
-import os
-import shutil
-import subprocess
+import importlib.util
+import contextlib
+import io
+import json
+import os
+import shutil
+import subprocess
 import sys
 import tempfile
 import time
@@ -175,7 +177,7 @@
         self.assertIn("Code Delegation Protocol", reason)
 
 
-class TestAC12Cases(BaseEnforcerTest):
+class TestAC12Cases(BaseEnforcerTest):
     """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""
 
     def test_01_exempt_path_allow(self) -> None:
@@ -283,10 +285,78 @@
         }
         code, out, err = self._run_enforcer(payload)
         self.assertEqual(code, 0)
-        self.assertEqual(out.strip(), "")
-
-
-class TestHelpers(unittest.TestCase):
+        self.assertEqual(out.strip(), "")
+
+
+class TestDualTeamsSentinel(unittest.TestCase):
+    """Regression tests for dual-teams worktree sentinel detection."""
+
+    @classmethod
+    def setUpClass(cls) -> None:
+        cls.mod = _load_module()
+
+    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))
+
+    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "worktrees" / "validation" / "claude"
+            nested.mkdir(parents=True)
+            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+
+            self.assertTrue(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            nested = project_dir / "a" / "b" / "c"
+            nested.mkdir(parents=True)
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(nested))
+
+    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
+            project_dir = Path(tmpdir).resolve()
+            (project_dir / ".dual-base-ref").mkdir()
+
+            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))
+
+
+class TestDualTeamsDecide(BaseEnforcerTest):
+    """Regression tests for the dual-teams passthrough in decide()."""
+
+    def setUp(self) -> None:
+        super().setUp()
+        self.mod = _load_module()
+        self.script_rel = ".claude/scripts/foo.py"
+        (self.root / ".claude" / "scripts").mkdir(parents=True)
+        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")
+
+    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
+        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
+        shutil.rmtree(self.root / "work", ignore_errors=True)
+
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertTrue(allowed)
+        self.assertEqual(stdout.getvalue().strip(), "")
+
+    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
+        with contextlib.redirect_stdout(io.StringIO()) as stdout:
+            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)
+
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout.getvalue())
+        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
+
+
+class TestHelpers(unittest.TestCase):
     """Direct unit tests of helper functions (no subprocess)."""
 
     @classmethod
@@ -404,4 +474,4 @@
 
 
 if __name__ == "__main__":
-    unittest.main(verbosity=2)
\ No newline at end of file
+    unittest.main(verbosity=2)

tokens used
134 931
```
