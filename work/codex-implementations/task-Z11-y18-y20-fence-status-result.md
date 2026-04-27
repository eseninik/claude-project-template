# Codex Implementation Result — Task Z11-y18-y20-fence-status

- status: scope-violation
- timestamp: 2026-04-26T12:45:06.738805+00:00
- task_file: C:\Bots\Migrator bots\claude-project-template-update\work\codify-enforcement\task-Z11-y18-y20-fence-status.md
- base_sha: bb3a0bf70cdf880cde6f88f94127bb1e4b3b4505
- codex_returncode: 0
- scope_status: fail
- scope_message: 2026-04-26 15:56:48,339 INFO codex_scope_check main_started diff=C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations\task-Z11-y18-y20-fence-status.diff fence= root=.
2026-04-26 15:56:48,339 INFO codex_scope_check read_diff_started source=C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations\task-Z11-y18-y20-fence-status.diff
2026-04-26 15:56:48,348 INFO codex_scope_check read_diff_completed bytes=10957
2026-04-26 15:56:48,348 INFO codex_scope_check parse_diff_paths_started diff_bytes=10957
2026-04-26 15:56:48,348 INFO codex_scope_check parse_diff_paths_completed count=2
2026-04-26 15:56:48,348 INFO codex_scope_check parse_fence_started fence_spec='' root=C:\Bots\Migrator bots\claude-project-template-update
2026-04-26 15:56:48,348 INFO codex_scope_check parse_fence_completed allowed=0 forbidden=0
2026-04-26 15:56:48,348 INFO codex_scope_check check_paths_started allowed=0 forbidden=0
2026-04-26 15:56:48,348 WARNING codex_scope_check check_paths_no_allowed path=.claude/scripts/codex-implement.py
2026-04-26 15:56:48,348 WARNING codex_scope_check check_paths_no_allowed path=.claude/scripts/test_codex_implement.py
2026-04-26 15:56:48,348 INFO codex_scope_check check_paths_completed violations=2
2026-04-26 15:56:48,348 ERROR codex_scope_check main_completed status=violation count=2
- scope_violations:
  - VIOLATION: 2 path(s) outside fence
  - .claude/scripts/codex-implement.py	no allowed fence entries configured
  - .claude/scripts/test_codex_implement.py	no allowed fence entries configured
  - 2026-04-26 15:56:48,339 INFO codex_scope_check main_started diff=C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations\task-Z11-y18-y20-fence-status.diff fence= root=.
  - 2026-04-26 15:56:48,339 INFO codex_scope_check read_diff_started source=C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations\task-Z11-y18-y20-fence-status.diff
  - 2026-04-26 15:56:48,348 INFO codex_scope_check read_diff_completed bytes=10957
  - 2026-04-26 15:56:48,348 INFO codex_scope_check parse_diff_paths_started diff_bytes=10957
  - 2026-04-26 15:56:48,348 INFO codex_scope_check parse_diff_paths_completed count=2
  - 2026-04-26 15:56:48,348 INFO codex_scope_check parse_fence_started fence_spec='' root=C:\Bots\Migrator bots\claude-project-template-update
  - 2026-04-26 15:56:48,348 INFO codex_scope_check parse_fence_completed allowed=0 forbidden=0
  - 2026-04-26 15:56:48,348 INFO codex_scope_check check_paths_started allowed=0 forbidden=0
  - 2026-04-26 15:56:48,348 WARNING codex_scope_check check_paths_no_allowed path=.claude/scripts/codex-implement.py
  - 2026-04-26 15:56:48,348 WARNING codex_scope_check check_paths_no_allowed path=.claude/scripts/test_codex_implement.py
  - 2026-04-26 15:56:48,348 INFO codex_scope_check check_paths_completed violations=2
  - 2026-04-26 15:56:48,348 ERROR codex_scope_check main_completed status=violation count=2

## Diff

```diff
diff --git a/.claude/scripts/codex-implement.py b/.claude/scripts/codex-implement.py
index 77c68b9..2e0f9c0 100644
--- a/.claude/scripts/codex-implement.py
+++ b/.claude/scripts/codex-implement.py
@@ -355,6 +355,33 @@ def parse_scope_fence(section_text: str) -> ScopeFence:
                 else:
                     fence.forbidden.append(entry)
 
+        if not fence.allowed:
+            _log(logging.DEBUG, "parse_scope_fence code-block fallback")
+            in_block = False
+            fallback_allowed = 0
+            for line in section_text.splitlines():
+                stripped = line.strip()
+                if stripped.startswith("```"):
+                    in_block = not in_block
+                    continue
+                if not in_block:
+                    continue
+
+                entry = stripped
+                if not entry or entry.startswith("#") or entry.startswith("//"):
+                    continue
+                entry = re.split(r"\s+\(", entry, maxsplit=1)[0].strip()
+                entry = entry.strip("`").strip()
+                if not entry:
+                    continue
+                fence.allowed.append(entry)
+                fallback_allowed += 1
+            _log(
+                logging.DEBUG,
+                "parse_scope_fence code-block fallback complete",
+                allowed_added=fallback_allowed,
+            )
+
         _log(
             logging.DEBUG,
             "exit: parse_scope_fence",
@@ -455,7 +482,13 @@ def parse_task_file(task_path: Path) -> Task:
         frontmatter, body = parse_frontmatter(text)
         sections = split_sections(body)
 
-        scope_fence = parse_scope_fence(sections.get("Scope Fence", ""))
+        scope_section = sections.get("Scope Fence", "")
+        if not scope_section:
+            for section_name, section_text in sections.items():
+                if section_name.startswith("Scope Fence "):
+                    scope_section = section_text
+                    break
+        scope_fence = parse_scope_fence(scope_section)
         test_commands = parse_test_commands(
             sections.get("Test Commands (run after implementation)", "")
             or sections.get("Test Commands", "")
@@ -1041,6 +1074,37 @@ class TestRunResult:
     outputs: list[dict[str, object]]
 
 
+def determine_run_status(
+    scope: Optional[ScopeCheckResult],
+    test_run: Optional[TestRunResult],
+    codex_run: Optional[CodexRunResult],
+    timed_out: bool,
+) -> str:
+    """Return the run status from actual gates: timeout, scope, and tests."""
+    _log(
+        logging.DEBUG,
+        "entry: determine_run_status",
+        scope_status=scope.status if scope else "skipped",
+        tests_all_passed=test_run.all_passed if test_run else None,
+        codex_returncode=codex_run.returncode if codex_run else None,
+        timed_out=timed_out,
+    )
+    try:
+        if timed_out:
+            status = "timeout"
+        elif scope is not None and scope.status == "fail":
+            status = "scope-violation"
+        elif test_run is not None and not test_run.all_passed:
+            status = "fail"
+        else:
+            status = "pass"
+        _log(logging.DEBUG, "exit: determine_run_status", status=status)
+        return status
+    except Exception:
+        logger.exception("determine_run_status failed")
+        raise
+
+
 def run_test_commands(
     commands: list[str],
     worktree: Path,
@@ -1399,7 +1463,12 @@ def main(argv: Optional[list[str]] = None) -> int:
         )
 
         if codex_run.timed_out:
-            status = "timeout"
+            status = determine_run_status(
+                scope=scope,
+                test_run=test_run,
+                codex_run=codex_run,
+                timed_out=True,
+            )
             rollback_worktree(worktree, base_sha)
         else:
             diff_text = capture_diff(worktree, base_sha)
@@ -1410,7 +1479,12 @@ def main(argv: Optional[list[str]] = None) -> int:
 
             scope = run_scope_check(diff_file, task.scope_fence, project_root)
             if scope.status == "fail":
-                status = "scope-violation"
+                status = determine_run_status(
+                    scope=scope,
+                    test_run=test_run,
+                    codex_run=codex_run,
+                    timed_out=False,
+                )
                 rollback_worktree(worktree, base_sha)
                 # Do NOT void diff_text on scope-violation — the diff is the
                 # single most important diagnostic artifact for post-mortem
@@ -1418,14 +1492,12 @@ def main(argv: Optional[list[str]] = None) -> int:
                 # false positive). See dual-1-postmortem.md Bug #8.
             else:
                 test_run = run_test_commands(task.test_commands, worktree)
-                if codex_run.returncode != 0 and not test_run.all_passed:
-                    status = "fail"
-                elif not test_run.all_passed:
-                    status = "fail"
-                elif codex_run.returncode != 0:
-                    status = "fail"
-                else:
-                    status = "pass"
+                status = determine_run_status(
+                    scope=scope,
+                    test_run=test_run,
+                    codex_run=codex_run,
+                    timed_out=False,
+                )
 
         result_path = result_dir / f"task-{task.task_id}-result.md"
         write_result_file(
diff --git a/.claude/scripts/test_codex_implement.py b/.claude/scripts/test_codex_implement.py
index cb1b59b..5656e83 100644
--- a/.claude/scripts/test_codex_implement.py
+++ b/.claude/scripts/test_codex_implement.py
@@ -181,6 +181,52 @@ class TestScopeFenceParser(unittest.TestCase):
         fence = codex_impl.parse_scope_fence(txt)
         self.assertEqual(fence.allowed, ["foo/bar.py", "baz/qux.py"])
 
+    def test_parse_scope_fence_code_block_syntax(self):
+        txt = (
+            "## Scope Fence \u2014 files you MAY modify\n\n"
+            "```\n"
+            ".claude/hooks/foo.py\n"
+            "src/bar/baz.py\n"
+            "```\n"
+        )
+        fence = codex_impl.parse_scope_fence(txt)
+        self.assertEqual(fence.allowed, [".claude/hooks/foo.py", "src/bar/baz.py"])
+
+    def test_parse_scope_fence_code_block_strips_comments_and_blanks(self):
+        txt = (
+            "```\n"
+            "\n"
+            "# comment\n"
+            "  // comment\n"
+            ".claude/hooks/foo.py\n"
+            "\n"
+            "src/bar/baz.py\n"
+            "```\n"
+        )
+        fence = codex_impl.parse_scope_fence(txt)
+        self.assertEqual(fence.allowed, [".claude/hooks/foo.py", "src/bar/baz.py"])
+
+    def test_parse_scope_fence_code_block_strips_trailing_parens(self):
+        txt = (
+            "```\n"
+            "CLAUDE.md (only the X section)\n"
+            "```\n"
+        )
+        fence = codex_impl.parse_scope_fence(txt)
+        self.assertEqual(fence.allowed, ["CLAUDE.md"])
+
+    def test_parse_scope_fence_falls_back_to_legacy_when_bold_present(self):
+        txt = (
+            "**Allowed paths (may be written):**\n"
+            "- `legacy/path.py`\n"
+            "\n"
+            "```\n"
+            "code/block/path.py\n"
+            "```\n"
+        )
+        fence = codex_impl.parse_scope_fence(txt)
+        self.assertEqual(fence.allowed, ["legacy/path.py"])
+
 
 class TestTestCommandParser(unittest.TestCase):
     def test_extracts_commands_from_bash_block(self):
@@ -261,6 +307,30 @@ class TestParseTaskFile(unittest.TestCase):
             self.assertEqual(len(task.test_commands), 2)
             self.assertEqual(len(task.acceptance_criteria), 3)
 
+    def test_scope_fence_heading_suffix_uses_code_block(self):
+        text = (
+            "---\n"
+            "executor: codex\n"
+            "---\n"
+            "\n"
+            "# Task T7\n"
+            "\n"
+            "## Scope Fence \u2014 files you MAY modify\n"
+            "\n"
+            "```\n"
+            ".claude/hooks/foo.py\n"
+            "src/bar/baz.py\n"
+            "```\n"
+        )
+        with tempfile.TemporaryDirectory() as td:
+            p = Path(td) / "T7-scope.md"
+            p.write_text(text, encoding="utf-8")
+            task = codex_impl.parse_task_file(p)
+            self.assertEqual(
+                task.scope_fence.allowed,
+                [".claude/hooks/foo.py", "src/bar/baz.py"],
+            )
+
     def test_missing_file_raises(self):
         with self.assertRaises(FileNotFoundError):
             codex_impl.parse_task_file(Path("/definitely/not/there.md"))
@@ -495,6 +565,62 @@ class TestWriteResultFile(unittest.TestCase):
             self.assertIn("NOTE: all good", content)
 
 
+class TestDetermineRunStatus(unittest.TestCase):
+    def test_status_pass_when_tests_pass_despite_codex_returncode_nonzero(self):
+        scope = codex_impl.ScopeCheckResult(status="pass", message="in-scope")
+        test_run = codex_impl.TestRunResult(all_passed=True, outputs=[])
+        codex_run = codex_impl.CodexRunResult(
+            returncode=1,
+            stdout="",
+            stderr="failed to record rollout items",
+            timed_out=False,
+            self_report=[],
+        )
+        status = codex_impl.determine_run_status(
+            scope=scope,
+            test_run=test_run,
+            codex_run=codex_run,
+            timed_out=False,
+        )
+        self.assertEqual(status, "pass")
+
+    def test_status_fail_when_tests_fail(self):
+        scope = codex_impl.ScopeCheckResult(status="pass", message="in-scope")
+        test_run = codex_impl.TestRunResult(all_passed=False, outputs=[])
+        codex_run = codex_impl.CodexRunResult(
+            returncode=0,
+            stdout="",
+            stderr="",
+            timed_out=False,
+            self_report=[],
+        )
+        status = codex_impl.determine_run_status(
+            scope=scope,
+            test_run=test_run,
+            codex_run=codex_run,
+            timed_out=False,
+        )
+        self.assertEqual(status, "fail")
+
+    def test_status_scope_violation_overrides_test_pass(self):
+        scope = codex_impl.ScopeCheckResult(status="fail", message="out-of-scope")
+        test_run = codex_impl.TestRunResult(all_passed=True, outputs=[])
+        codex_run = codex_impl.CodexRunResult(
+            returncode=0,
+            stdout="",
+            stderr="",
+            timed_out=False,
+            self_report=[],
+        )
+        status = codex_impl.determine_run_status(
+            scope=scope,
+            test_run=test_run,
+            codex_run=codex_run,
+            timed_out=False,
+        )
+        self.assertEqual(status, "scope-violation")
+
+
 class TestPreflightCleanTreeGuard(unittest.TestCase):
     """Regression suite for the dirty-tree preflight check.
```

## Test Output

(no test commands executed)
## Self-Report (Codex NOTE/BLOCKER lines)

(no NOTE/BLOCKER lines)

## Codex stderr

```
OpenAI Codex v0.125.0 (research preview)
--------
workdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z11\codex\task-Z11-y18-y20-fence-status
model: gpt-5.5
provider: chatgpt
approval: never
sandbox: danger-full-access
reasoning effort: xhigh
reasoning summaries: none
session id: 019dc9db-42dc-7c40-8d71-e5a9c62d7337
--------
user
You are the single-task implementer. The task specification below is IMMUTABLE.
Write code to satisfy all Acceptance Criteria. Do NOT modify files listed in
Forbidden Paths or Read-Only Files. After writing code, run every Test Command
listed in the task and report the result in your self-report.
Any AGENTS.md or CLAUDE.md in the worktree is authoritative background context.

---- TASK SPECIFICATION ----

---
task_id: Z11-y18-y20-fence-status
title: Y18 (parse_scope_fence accepts code-block syntax) + Y20 (status:pass when tests pass + scope pass, regardless of codex returncode)
executor: dual
risk_class: routine
speed_profile: balanced
---

# Task Z11 — Y18 + Y20 fixes in codex-implement.py

## Goal

Two surgical bugs that produce false negatives in dual-implement runs:

**Y18 — parse_scope_fence too narrow.** Current `parse_scope_fence` in
`codex-implement.py:324` only recognizes the `**Allowed**:` /
`**Forbidden**:` markdown-bold-header style with bullet lines. Most of
our task specs use a more readable code-block syntax:
```
## Scope Fence — files you MAY modify

\`\`\`
.claude/hooks/codex-delegate-enforcer.py
.claude/scripts/test_codex_implement.py
\`\`\`
```
The parser sees no `**Allowed**` heading, returns empty fence, then
`run_scope_check` invokes `codex-scope-check.py --fence ""` which
treats every modified path as a violation → false-positive
`scope-violation` status. Bit Z1 in this exact way.

**Y20 — status:fail when tests pass.** In
`codex-implement.py:1421-1428`, the status logic includes:
```python
elif codex_run.returncode != 0:
    status = "fail"
```
Effect: even when scope check passed AND all test commands passed
(`tests_ok=True`), if Codex CLI returncode is non-zero (which it
often is from CLI noise — e.g., the v0.125 "failed to record rollout
items" telemetry warning), status becomes "fail". This corrupted
Z9's status (was status:fail despite tests_ok=True + exit_code=0;
I had to manually patch result.md to status:pass to unblock the
sync). It also confuses judge.py.

## The two fixes

### Fix Y18 — parse_scope_fence accepts code-block syntax

Extend `parse_scope_fence` (~ line 324) to ALSO parse the
code-block-of-paths style. Algorithm:
1. If existing `**Allowed**:` parsing yields ≥1 entry → use that.
2. Else look for ``` fenced ``` blocks in the section. For each
   non-empty non-comment line inside the fence, treat as allowed path.
3. Strip surrounding whitespace and any trailing parenthetical
   comments (e.g., `path/file.py (do NOT modify)` → `path/file.py`).
4. Skip lines starting with `#` or `//` (comments).

Net change ~20-30 LOC (new branch + helper).

### Fix Y20 — status:pass when tests + scope are good

At lines 1421-1428, simplify status determination. Keep "fail" only
when an actual gate fails:
```python
test_run = run_test_commands(task.test_commands, worktree)
if not test_run.all_passed:
    status = "fail"
else:
    status = "pass"
    # NOTE Y20: codex_run.returncode != 0 is COMMON noise from
    # CLI v0.125 (e.g. failed-to-record-rollout-items warnings).
    # If tests passed AND scope passed, the run IS a pass.
```

If we want to surface non-zero codex returncode, do it as a NOTE in
self-report (informational), not as a status:fail.

Net change ~5-10 LOC.

## Scope Fence — files you MAY modify

```
.claude/scripts/codex-implement.py
.claude/scripts/test_codex_implement.py     (add Y18 + Y20 regression tests)
```

DO NOT modify any other file.

## Read-Only Files / Evaluation Firewall

- `work/codify-enforcement/task-Z11-y18-y20-fence-status.md` (this file)
- `.claude/scripts/codex-scope-check.py`, `codex-wave.py`,
  `codex-inline-dual.py`, `dual-teams-spawn.py` (downstream consumers)

## Acceptance Criteria

### AC-1 (Y18): Code-block fence parsing

Add to `.claude/scripts/test_codex_implement.py`:

- `test_parse_scope_fence_code_block_syntax()` — Given section text
  ```
  ## Scope Fence — files you MAY modify

  ```
  .claude/hooks/foo.py
  src/bar/baz.py
  ```
  ```
  Assert `parse_scope_fence(section_text).allowed == [".claude/hooks/foo.py", "src/bar/baz.py"]`

- `test_parse_scope_fence_code_block_strips_comments_and_blanks()` —
  Code block with empty lines + `# comment` + `// comment` — assert
  comments + blanks not in allowed list.

- `test_parse_scope_fence_code_block_strips_trailing_parens()` —
  Path like `CLAUDE.md (only the X section)` → `CLAUDE.md`

- `test_parse_scope_fence_falls_back_to_legacy_when_bold_present()` —
  When `**Allowed**:` header present, prefer legacy parsing (don't
  break existing tests).

### AC-2 (Y20): status:pass with non-zero codex returncode

- `test_status_pass_when_tests_pass_despite_codex_returncode_nonzero()` —
  Mock CodexRunResult(returncode=1), TestRunResult(all_passed=True),
  ScopeCheckResult(status="pass"). Run the status determination logic.
  Assert status == "pass".

- `test_status_fail_when_tests_fail()` — TestRunResult(all_passed=False),
  scope=pass, codex_returncode=0. Assert status == "fail".

- `test_status_scope_violation_overrides_test_pass()` — scope=fail,
  tests pass. Assert status == "scope-violation".

You may need to refactor the status logic into a pure function
`determine_run_status(scope, test_run, codex_run, timed_out) -> str`
to make tests easy. Refactor is in scope.

### AC-3: Existing test_codex_implement tests still pass (regression)

```bash
python -m pytest .claude/scripts/test_codex_implement.py -q --tb=line
```

64 existing tests must still pass + N new = ~71 expected.

### AC-4: Other test suites still pass

```bash
python -m pytest .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py .claude/scripts/test_codex_ask.py .claude/scripts/test_codex_inline_dual.py -q --tb=line
```

19 + 35 + 36 + 18 + 16 + 24 = 148 expected (or close).

### AC-5: Selftest still passes
`python .claude/scripts/dual-teams-selftest.py` → 6/6 PASS

## Test Commands

```bash
# 1. test_codex_implement (existing + new)
python -m pytest .claude/scripts/test_codex_implement.py -q --tb=line

# 2. All other suites
python -m pytest .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py .claude/scripts/test_codex_ask.py .claude/scripts/test_codex_inline_dual.py -q --tb=line

# 3. Selftest
python .claude/scripts/dual-teams-selftest.py
```

## Implementation hints

- Y18: easiest implementation — after the existing loop, if
  `not fence.allowed and not fence.forbidden`, scan the section for
  ``` triple-backtick ``` markers, then iterate the lines between them.
- Y20: refactor `if/elif` chain (line 1421-1428) into `determine_run_status()`
  helper for testability. Keep the same return values (`"fail"`,
  `"pass"`, `"scope-violation"`, `"timeout"`).
- Logging: add `logger.debug` entries for Y18 fallback path so future
  parse failures are diagnosable.

## Self-report format

```
=== TASK Z11 SELF-REPORT ===
- status: pass | fail | blocker
- files modified: [list]
- new tests added: <count>
- net lines: <approx>
- Y18 approach: <1 line>
- Y20 approach: <1 line>
- existing test_codex_implement passes: <X>/<Y>
- live attack matrix 19/19: yes / no
- selftest: PASS / FAIL
- NOTE: <surprising>
- BLOCKER: <only if>
- Final commit SHA: <SHA>
=== END SELF-REPORT ===
```


---- END TASK SPECIFICATION ----
Return a short self-report at the end of your run using lines starting with
`NOTE:` for observations and `BLOCKER:` for unresolved problems.

codex
I’ll make the scoped changes in `codex-implement.py` and its test file, then run the three required commands and report the concrete results. First I’m reading the existing parser, status logic, and test patterns so the patch stays narrow.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "def parse_scope_fence|class ScopeFence|determine_run_status|status =|codex_run.returncode|run_test_commands|CodexRunResult|TestRunResult|ScopeCheckResult" .claude/scripts/codex-implement.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z11\codex\task-Z11-y18-y20-fence-status
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z11\codex\task-Z11-y18-y20-fence-status
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "parse_scope_fence|status|CodexRunResult|TestRunResult|ScopeCheckResult|run_test_commands" .claude/scripts/test_codex_implement.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z11\codex\task-Z11-y18-y20-fence-status
 succeeded in 131ms:
232:class ScopeFence:
324:def parse_scope_fence(section_text: str) -> ScopeFence:
704:        status = _extract("status")
705:        scope_status = _extract("scope_status")
814:class CodexRunResult:
873:) -> CodexRunResult:
938:            return CodexRunResult(
960:        return CodexRunResult(
973:                           timeout: int, model: str = "gpt-5.5") -> CodexRunResult:
977:    last: Optional[CodexRunResult] = None
998:    return last if last is not None else CodexRunResult(
1008:class ScopeCheckResult:
1018:) -> ScopeCheckResult:
1026:            return ScopeCheckResult(status="skipped", message=msg)
1048:            return ScopeCheckResult(status="pass", message=r.stdout.strip() or "in-scope")
1053:        return ScopeCheckResult(
1060:        return ScopeCheckResult(status="fail", message="scope-check timeout")
1063:        return ScopeCheckResult(status="fail", message="scope-check exception")
1072:class TestRunResult:
1077:def determine_run_status(
1078:    scope: Optional[ScopeCheckResult],
1079:    test_run: Optional[TestRunResult],
1080:    codex_run: Optional[CodexRunResult],
1086:        "entry: determine_run_status",
1089:        codex_returncode=codex_run.returncode if codex_run else None,
1094:            status = "timeout"
1095:        elif scope is not None and scope.status == "fail":
1096:            status = "scope-violation"
1098:            status = "fail"
1100:            status = "pass"
1101:        _log(logging.DEBUG, "exit: determine_run_status", status=status)
1104:        logger.exception("determine_run_status failed")
1108:def run_test_commands(
1112:) -> TestRunResult:
1114:    _log(logging.INFO, "entry: run_test_commands", count=len(commands))
1169:        _log(logging.INFO, "exit: run_test_commands", all_passed=all_passed)
1170:        return TestRunResult(all_passed=all_passed, outputs=outputs)
1172:        logger.exception("run_test_commands failed")
1197:        if scope_status == "fail":
1211:    test_run: Optional[TestRunResult],
1212:    codex_run: Optional[CodexRunResult],
1213:    scope: Optional[ScopeCheckResult],
1223:        codex_rc = codex_run.returncode if codex_run else "N/A"
1225:        scope_status = scope.status if scope else "skipped"
1428:    codex_run: Optional[CodexRunResult] = None
1429:    test_run: Optional[TestRunResult] = None
1430:    scope: Optional[ScopeCheckResult] = None
1431:    status = "pass"
1445:            codex_run=CodexRunResult(returncode=-1, stdout="", stderr=degraded_stderr,
1466:            status = determine_run_status(
1481:            if scope.status == "fail":
1482:                status = determine_run_status(
1494:                test_run = run_test_commands(task.test_commands, worktree)
1495:                status = determine_run_status(
1516:        scope_status = scope.status if scope else "skipped"

 succeeded in 135ms:
164:        fence = codex_impl.parse_scope_fence(sections["Scope Fence"])
171:        fence = codex_impl.parse_scope_fence("")
181:        fence = codex_impl.parse_scope_fence(txt)
184:    def test_parse_scope_fence_code_block_syntax(self):
192:        fence = codex_impl.parse_scope_fence(txt)
195:    def test_parse_scope_fence_code_block_strips_comments_and_blanks(self):
206:        fence = codex_impl.parse_scope_fence(txt)
209:    def test_parse_scope_fence_code_block_strips_trailing_parens(self):
215:        fence = codex_impl.parse_scope_fence(txt)
218:    def test_parse_scope_fence_falls_back_to_legacy_when_bold_present(self):
227:        fence = codex_impl.parse_scope_fence(txt)
347:            codex_impl.map_status_to_exit("pass", "pass", True), codex_impl.EXIT_OK
352:            codex_impl.map_status_to_exit("pass", "skipped", True), codex_impl.EXIT_OK
357:            codex_impl.map_status_to_exit("fail", "pass", False),
363:            codex_impl.map_status_to_exit("scope-violation", "fail", False),
369:            codex_impl.map_status_to_exit("timeout", "skipped", False),
375:            codex_impl.map_status_to_exit("pass", "fail", True),
488:            self.assertEqual(result.status, "skipped")
522:            codex_run = codex_impl.CodexRunResult(
529:            test_run = codex_impl.TestRunResult(
542:            scope = codex_impl.ScopeCheckResult(status="pass", message="in-scope")
548:                status="pass",
558:            self.assertIn("status: pass", content)
560:            self.assertIn("scope_status: pass", content)
569:    def test_status_pass_when_tests_pass_despite_codex_returncode_nonzero(self):
570:        scope = codex_impl.ScopeCheckResult(status="pass", message="in-scope")
571:        test_run = codex_impl.TestRunResult(all_passed=True, outputs=[])
572:        codex_run = codex_impl.CodexRunResult(
579:        status = codex_impl.determine_run_status(
585:        self.assertEqual(status, "pass")
587:    def test_status_fail_when_tests_fail(self):
588:        scope = codex_impl.ScopeCheckResult(status="pass", message="in-scope")
589:        test_run = codex_impl.TestRunResult(all_passed=False, outputs=[])
590:        codex_run = codex_impl.CodexRunResult(
597:        status = codex_impl.determine_run_status(
603:        self.assertEqual(status, "fail")
605:    def test_status_scope_violation_overrides_test_pass(self):
606:        scope = codex_impl.ScopeCheckResult(status="fail", message="out-of-scope")
607:        test_run = codex_impl.TestRunResult(all_passed=True, outputs=[])
608:        codex_run = codex_impl.CodexRunResult(
615:        status = codex_impl.determine_run_status(
621:        self.assertEqual(status, "scope-violation")
707:- status: scope-violation
712:- scope_status: fail
742:    def test_parses_status_and_blockers(self):
747:            self.assertIn("prior status: scope-violation", summary)
748:            self.assertIn("prior scope_status: fail", summary)
797:            prior = "## Previous Iteration (auto-injected)\n\n- prior status: fail"
815:    return codex_impl.CodexRunResult(
821:    return codex_impl.CodexRunResult(

 succeeded in 140ms:
codex
The working tree is clean, and this branch already contains symbols and test names that match the requested refactor. I’m checking the actual implementations now to see whether this is pre-applied work, partial work, or just stubs.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path .claude/scripts/codex-implement.py | Select-Object -Skip 210 -First 170' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z11\codex\task-Z11-y18-y20-fence-status
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path .claude/scripts/codex-implement.py | Select-Object -Skip 1050 -First 80' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z11\codex\task-Z11-y18-y20-fence-status
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path .claude/scripts/codex-implement.py | Select-Object -Skip 1410 -First 110' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z11\codex\task-Z11-y18-y20-fence-status
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path .claude/scripts/test_codex_implement.py | Select-Object -Skip 140 -First 100' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z11\codex\task-Z11-y18-y20-fence-status
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path .claude/scripts/test_codex_implement.py | Select-Object -Skip 550 -First 90' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z11\codex\task-Z11-y18-y20-fence-status
 succeeded in 198ms:
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


def determine_run_status(
    scope: Optional[ScopeCheckResult],
    test_run: Optional[TestRunResult],
    codex_run: Optional[CodexRunResult],
    timed_out: bool,
) -> str:
    """Return the run status from actual gates: timeout, scope, and tests."""
    _log(
        logging.DEBUG,
        "entry: determine_run_status",
        scope_status=scope.status if scope else "skipped",
        tests_all_passed=test_run.all_passed if test_run else None,
        codex_returncode=codex_run.returncode if codex_run else None,
        timed_out=timed_out,
    )
    try:
        if timed_out:
            status = "timeout"
        elif scope is not None and scope.status == "fail":
            status = "scope-violation"
        elif test_run is not None and not test_run.all_passed:
            status = "fail"
        else:
            status = "pass"
        _log(logging.DEBUG, "exit: determine_run_status", status=status)
        return status
    except Exception:
        logger.exception("determine_run_status failed")
        raise


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

 succeeded in 200ms:
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

        if not fence.allowed:
            _log(logging.DEBUG, "parse_scope_fence code-block fallback")
            in_block = False
            fallback_allowed = 0
            for line in section_text.splitlines():
                stripped = line.strip()
                if stripped.startswith("```"):
                    in_block = not in_block
                    continue
                if not in_block:
                    continue

                entry = stripped
                if not entry or entry.startswith("#") or entry.startswith("//"):
                    continue
                entry = re.split(r"\s+\(", entry, maxsplit=1)[0].strip()
                entry = entry.strip("`").strip()
                if not entry:
                    continue
                fence.allowed.append(entry)
                fallback_allowed += 1
            _log(
                logging.DEBUG,

 succeeded in 206ms:
        self.assertIn("Scope Fence", sections)
        self.assertIn("Test Commands (run after implementation)", sections)
        self.assertIn("Acceptance Criteria (IMMUTABLE)", sections)
        self.assertIn("Skill Contracts", sections)
        self.assertIn("Constraints", sections)

    def test_preserves_subheadings_inside_section(self):
        _, body = codex_impl.parse_frontmatter(TASK_SAMPLE)
        sections = codex_impl.split_sections(body)
        self.assertIn("### logging-standards", sections["Skill Contracts"])

    def test_does_not_split_on_triple_hash(self):
        text = "## A\nhello\n### subsection\nmore\n## B\nend\n"
        sections = codex_impl.split_sections(text)
        self.assertIn("A", sections)
        self.assertIn("B", sections)
        self.assertIn("### subsection", sections["A"])


class TestScopeFenceParser(unittest.TestCase):
    def test_parses_allowed_and_forbidden_bullets(self):
        _, body = codex_impl.parse_frontmatter(TASK_SAMPLE)
        sections = codex_impl.split_sections(body)
        fence = codex_impl.parse_scope_fence(sections["Scope Fence"])
        self.assertIn("src/sample.py", fence.allowed)
        self.assertIn("tests/test_sample.py", fence.allowed)
        self.assertIn("src/other/*", fence.forbidden)
        self.assertIn("docs/", fence.forbidden)

    def test_empty_section_returns_empty_fence(self):
        fence = codex_impl.parse_scope_fence("")
        self.assertEqual(fence.allowed, [])
        self.assertEqual(fence.forbidden, [])

    def test_strips_backticks_and_trailing_comments(self):
        txt = (
            "**Allowed paths (may be written):**\n"
            "- `foo/bar.py` (new file)\n"
            "- baz/qux.py\n"
        )
        fence = codex_impl.parse_scope_fence(txt)
        self.assertEqual(fence.allowed, ["foo/bar.py", "baz/qux.py"])

    def test_parse_scope_fence_code_block_syntax(self):
        txt = (
            "## Scope Fence \u2014 files you MAY modify\n\n"
            "```\n"
            ".claude/hooks/foo.py\n"
            "src/bar/baz.py\n"
            "```\n"
        )
        fence = codex_impl.parse_scope_fence(txt)
        self.assertEqual(fence.allowed, [".claude/hooks/foo.py", "src/bar/baz.py"])

    def test_parse_scope_fence_code_block_strips_comments_and_blanks(self):
        txt = (
            "```\n"
            "\n"
            "# comment\n"
            "  // comment\n"
            ".claude/hooks/foo.py\n"
            "\n"
            "src/bar/baz.py\n"
            "```\n"
        )
        fence = codex_impl.parse_scope_fence(txt)
        self.assertEqual(fence.allowed, [".claude/hooks/foo.py", "src/bar/baz.py"])

    def test_parse_scope_fence_code_block_strips_trailing_parens(self):
        txt = (
            "```\n"
            "CLAUDE.md (only the X section)\n"
            "```\n"
        )
        fence = codex_impl.parse_scope_fence(txt)
        self.assertEqual(fence.allowed, ["CLAUDE.md"])

    def test_parse_scope_fence_falls_back_to_legacy_when_bold_present(self):
        txt = (
            "**Allowed paths (may be written):**\n"
            "- `legacy/path.py`\n"
            "\n"
            "```\n"
            "code/block/path.py\n"
            "```\n"
        )
        fence = codex_impl.parse_scope_fence(txt)
        self.assertEqual(fence.allowed, ["legacy/path.py"])


class TestTestCommandParser(unittest.TestCase):
    def test_extracts_commands_from_bash_block(self):
        _, body = codex_impl.parse_frontmatter(TASK_SAMPLE)
        sections = codex_impl.split_sections(body)
        cmds = codex_impl.parse_test_commands(
            sections["Test Commands (run after implementation)"]
        )
        self.assertEqual(len(cmds), 2)
        self.assertIn("py -3 -m pytest tests/test_sample.py -v", cmds)
        self.assertIn('py -3 -c "print(\'ok\')"', cmds)

 succeeded in 211ms:
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
            status = determine_run_status(
                scope=scope,
                test_run=test_run,
                codex_run=codex_run,
                timed_out=True,
            )
            rollback_worktree(worktree, base_sha)
        else:
            diff_text = capture_diff(worktree, base_sha)

            diff_file = result_dir / f"task-{task.task_id}.diff"
            diff_file.parent.mkdir(parents=True, exist_ok=True)
            diff_file.write_text(diff_text, encoding="utf-8")

            scope = run_scope_check(diff_file, task.scope_fence, project_root)
            if scope.status == "fail":
                status = determine_run_status(
                    scope=scope,
                    test_run=test_run,
                    codex_run=codex_run,
                    timed_out=False,
                )
                rollback_worktree(worktree, base_sha)
                # Do NOT void diff_text on scope-violation вЂ” the diff is the
                # single most important diagnostic artifact for post-mortem
                # review (especially when the fence check itself fires a
                # false positive). See dual-1-postmortem.md Bug #8.
            else:
                test_run = run_test_commands(task.test_commands, worktree)
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

 succeeded in 219ms:
                codex_run=codex_run,
                scope=scope,
                base_sha="deadbeef",
                timestamp="2026-04-24T00:00:00+00:00",
            )

            content = result_path.read_text(encoding="utf-8")
            self.assertIn("status: pass", content)
            self.assertIn("base_sha: deadbeef", content)
            self.assertIn("scope_status: pass", content)
            self.assertIn("tests_all_passed: True", content)
            self.assertIn("## Diff", content)
            self.assertIn("## Test Output", content)
            self.assertIn("## Self-Report", content)
            self.assertIn("NOTE: all good", content)


class TestDetermineRunStatus(unittest.TestCase):
    def test_status_pass_when_tests_pass_despite_codex_returncode_nonzero(self):
        scope = codex_impl.ScopeCheckResult(status="pass", message="in-scope")
        test_run = codex_impl.TestRunResult(all_passed=True, outputs=[])
        codex_run = codex_impl.CodexRunResult(
            returncode=1,
            stdout="",
            stderr="failed to record rollout items",
            timed_out=False,
            self_report=[],
        )
        status = codex_impl.determine_run_status(
            scope=scope,
            test_run=test_run,
            codex_run=codex_run,
            timed_out=False,
        )
        self.assertEqual(status, "pass")

    def test_status_fail_when_tests_fail(self):
        scope = codex_impl.ScopeCheckResult(status="pass", message="in-scope")
        test_run = codex_impl.TestRunResult(all_passed=False, outputs=[])
        codex_run = codex_impl.CodexRunResult(
            returncode=0,
            stdout="",
            stderr="",
            timed_out=False,
            self_report=[],
        )
        status = codex_impl.determine_run_status(
            scope=scope,
            test_run=test_run,
            codex_run=codex_run,
            timed_out=False,
        )
        self.assertEqual(status, "fail")

    def test_status_scope_violation_overrides_test_pass(self):
        scope = codex_impl.ScopeCheckResult(status="fail", message="out-of-scope")
        test_run = codex_impl.TestRunResult(all_passed=True, outputs=[])
        codex_run = codex_impl.CodexRunResult(
            returncode=0,
            stdout="",
            stderr="",
            timed_out=False,
            self_report=[],
        )
        status = codex_impl.determine_run_status(
            scope=scope,
            test_run=test_run,
            codex_run=codex_run,
            timed_out=False,
        )
        self.assertEqual(status, "scope-violation")


class TestPreflightCleanTreeGuard(unittest.TestCase):
    """Regression suite for the dirty-tree preflight check.

    PoC 2026-04-24 surfaced that preflight used to return HEAD sha without
    verifying a clean tree, so subsequent `git reset --hard` + `git clean -fd`
    in rollback destroyed pre-existing uncommitted user work. Preflight now
    refuses to proceed on any dirty worktree.
    """

    def _run(self, argv: list[str], cwd: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *argv],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path .claude/scripts/codex-implement.py | Select-Object -Skip 320 -First 80' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z11\codex\task-Z11-y18-y20-fence-status
 succeeded in 172ms:
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

        if not fence.allowed:
            _log(logging.DEBUG, "parse_scope_fence code-block fallback")
            in_block = False
            fallback_allowed = 0
            for line in section_text.splitlines():
                stripped = line.strip()
                if stripped.startswith("```"):
                    in_block = not in_block
                    continue
                if not in_block:
                    continue

                entry = stripped
                if not entry or entry.startswith("#") or entry.startswith("//"):
                    continue
                entry = re.split(r"\s+\(", entry, maxsplit=1)[0].strip()
                entry = entry.strip("`").strip()
                if not entry:
                    continue
                fence.allowed.append(entry)
                fallback_allowed += 1
            _log(
                logging.DEBUG,
                "parse_scope_fence code-block fallback complete",
                allowed_added=fallback_allowed,
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

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git log -1 --oneline --stat' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z11\codex\task-Z11-y18-y20-fence-status
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git branch --show-current' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z11\codex\task-Z11-y18-y20-fence-status
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git rev-parse HEAD' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z11\codex\task-Z11-y18-y20-fence-status
 succeeded in 141ms:
8e7ebe3 Fix codex scope fence and status gates
 .claude/scripts/codex-implement.py      |  94 +++++++++++++++++++++---
 .claude/scripts/test_codex_implement.py | 126 ++++++++++++++++++++++++++++++++
 2 files changed, 209 insertions(+), 11 deletions(-)

 succeeded in 129ms:
8e7ebe3406dc31e111d5b9b9ce33cc2448e78e31

 succeeded in 137ms:
codex-wave/task-Z11-y18-y20-fence-status

codex
HEAD already has a committed patch touching only the two allowed files, so I’m treating it as the implementation state for this worktree and validating it rather than adding churn. I’m also checking the commit diff briefly for scope before running the required suites.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git show --stat --oneline --name-only HEAD' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z11\codex\task-Z11-y18-y20-fence-status
 succeeded in 122ms:
8e7ebe3 Fix codex scope fence and status gates
.claude/scripts/codex-implement.py
.claude/scripts/test_codex_implement.py

codex
The committed diff is inside the scope fence: only `.claude/scripts/codex-implement.py` and `.claude/scripts/test_codex_implement.py`. I’m starting the mandated test commands now, beginning with the targeted `test_codex_implement` suite.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/scripts/test_codex_implement.py -q --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z11\codex\task-Z11-y18-y20-fence-status
 succeeded in 1387ms:
........................................................................ [100%]
72 passed in 0.93s

codex
`test_codex_implement` passed: 72/72. I’m running the broader hook/script regression command next.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py .claude/scripts/test_codex_ask.py .claude/scripts/test_codex_inline_dual.py -q --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z11\codex\task-Z11-y18-y20-fence-status
 succeeded in 4763ms:
........................................................................ [ 48%]
........................................................................ [ 97%]
....                                                                     [100%]
148 passed in 4.27s

codex
The broader regression command passed: 148/148. I’m running the dual-teams selftest now.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python .claude/scripts/dual-teams-selftest.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z11\codex\task-Z11-y18-y20-fence-status
 succeeded in 734ms:
[PASS] preflight-clean-with-sentinel-V1                     (61 ms)
[PASS] preflight-clean-with-sentinel-V2                     (57 ms)
[PASS] is_dual_teams_worktree-true-on-V1                    ( 1 ms)
[PASS] is_dual_teams_worktree-true-on-V2                    ( 1 ms)
[PASS] judge-axes-sees-claude-committed-py                  (29 ms)
[PASS] judge-axes-sees-codex-untracked-py                   (54 ms)
selftest: 6 checks, 6 passed, 0 failed (558 ms)
{"json_output": false, "keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: main", "ts": "2026-04-26T12:56:13.763620+00:00"}
{"keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: run_selftest", "ts": "2026-04-26T12:56:13.763620+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: setup_transient_repo", "tmpdir": "C:\\Users\\Lenovo\\AppData\\Local\\Temp\\dual-teams-selftest-z9uhfkds", "ts": "2026-04-26T12:56:13.764612+00:00"}
{"base_sha": "1f117e0ff42d31e05bd6293bff9b1cc2ff3fd984", "duration_ms": 250, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: setup_transient_repo", "ts": "2026-04-26T12:56:14.014987+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: load_integrations", "project_root": "C:\\Bots\\Migrator bots\\claude-project-template-update\\worktrees\\codify-enforcement-z11\\codex\\task-Z11-y18-y20-fence-status", "ts": "2026-04-26T12:56:14.014987+00:00"}
{"duration_ms": 5, "failures": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: load_integrations", "ts": "2026-04-26T12:56:14.019989+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: build_results", "ts": "2026-04-26T12:56:14.020989+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T12:56:14.020989+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "detail": "git status --porcelain empty", "duration_ms": 61, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T12:56:14.081505+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T12:56:14.081505+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "detail": "git status --porcelain empty", "duration_ms": 57, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T12:56:14.137504+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T12:56:14.137504+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T12:56:14.138505+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T12:56:14.138505+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T12:56:14.138505+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T12:56:14.203229+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "detail": "saw claude_probe.py", "duration_ms": 29, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T12:56:14.232590+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T12:56:14.232590+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "detail": "saw codex_probe.py", "duration_ms": 54, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T12:56:14.286306+00:00"}
{"checks": 6, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: build_results", "ts": "2026-04-26T12:56:14.286306+00:00"}
{"checks": 6, "duration_ms": 558, "failed": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: run_selftest", "passed": 6, "ts": "2026-04-26T12:56:14.322195+00:00"}
{"exit_code": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: main", "ts": "2026-04-26T12:56:14.322195+00:00"}

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z11\codex\task-Z11-y18-y20-fence-status
 succeeded in 128ms:
codex
=== TASK Z11 SELF-REPORT ===
- status: pass
- files modified: [.claude/scripts/codex-implement.py, .claude/scripts/test_codex_implement.py]
- new tests added: 7
- net lines: +198 approx
- Y18 approach: legacy `**Allowed**` parsing wins first; otherwise fenced code blocks are parsed as allowed paths with blanks/comments/trailing parens stripped.
- Y20 approach: status logic refactored into `determine_run_status()` and ignores noisy non-zero Codex returncode when scope/tests pass.
- existing test_codex_implement passes: 72/72
- live attack matrix 19/19: yes
- selftest: PASS
- NOTE: `python -m pytest .claude/scripts/test_codex_implement.py -q --tb=line` -> `72 passed in 0.93s`
- NOTE: broader regression command -> `148 passed in 4.27s`
- NOTE: `python .claude/scripts/dual-teams-selftest.py` -> `selftest: 6 checks, 6 passed, 0 failed`
- NOTE: implementation commit was already present at HEAD; working tree remained clean after verification.
- Final commit SHA: 8e7ebe3406dc31e111d5b9b9ce33cc2448e78e31
=== END SELF-REPORT ===
2026-04-26T12:56:48.041771Z ERROR codex_core::session: failed to record rollout items: thread 019dc9db-42dc-7c40-8d71-e5a9c62d7337 not found
tokens used
24 048
```
