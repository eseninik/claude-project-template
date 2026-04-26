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
