---
task_id: Z10-y19-y22-script-infra
title: Y19 (codex-inline-dual --result-dir forwarding) + Y22 (sync-template-to-target relocate + whitelist)
executor: dual
risk_class: routine
speed_profile: balanced
---

# Task Z10 — Script infrastructure cleanup (Y19 + Y22)

## Goal

Two related ergonomic fixes that remove manual workarounds:

**Y19** — `codex-inline-dual.py` lands `result.md` inside its OWN
worktree (`worktrees/inline/<task>/codex/work/codex-implementations/`),
not in the main project's `work/codex-implementations/`. Effect: the
enforcer can't find the result for path-exact cover lookup, and every
codex-inline-dual usage requires a manual `Copy-Item` after the run
finishes. Compare to `dual-teams-spawn.py` which forwards `--result-dir`
correctly (Y9 fix).

**Y22** — `sync-template-to-target.py` currently lives in `work/`. It is
a long-lived helper script (`.py`, code), not a one-shot. After Z1
invariants, every invocation needs a fresh Codex cover. The 5-step
dance (Z6/Z9) is overhead. The script belongs in `.claude/scripts/`
where it can be added to the project's own dual-tooling whitelist in
`codex-delegate-enforcer.py`. Then `py -3 .claude/scripts/sync-template-to-target.py`
runs without cover, like `codex-ask.py`, `codex-implement.py`, etc.

## The two fixes

### Fix Y19 — codex-inline-dual forwards --result-dir

In `.claude/scripts/codex-inline-dual.py`, add `--result-dir` flag with
default = main project's `work/codex-implementations/`. After Codex
finishes successfully, copy the produced result.md from the worktree
into the `--result-dir`. (Either by passing `--result-dir` to
`codex-implement.py` if it supports it, or by Copy after.) Net change
~10-25 LOC.

### Fix Y22 — Relocate sync-script + whitelist

1. `git mv work/sync-template-to-target.py .claude/scripts/sync-template-to-target.py`
2. Find references in CLAUDE.md / README and update (use `grep -rn "work/sync-template-to-target"`)
3. Add `.claude/scripts/sync-template-to-target.py` to the project's
   own dual-tooling whitelist in `codex-delegate-enforcer.py`
   (`grep -n "DUAL_TOOLING\|whitelist\|codex-ask" .claude/hooks/codex-delegate-enforcer.py`)
4. Verify: `Bash(command="py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/x --apply")`
   should ALLOW without a recent Codex cover (test_a07).

## Scope Fence — files you MAY modify

```
.claude/scripts/codex-inline-dual.py
.claude/scripts/test_codex_inline_dual.py        (add tests for Y19)
.claude/scripts/sync-template-to-target.py       (NEW location — moved from work/)
work/sync-template-to-target.py                  (DELETE — moved)
.claude/hooks/codex-delegate-enforcer.py         (whitelist 1 path)
.claude/hooks/test_enforcer_live_attacks.py      (1 NEW test for whitelist)
CLAUDE.md                                        (update path references if any)
```

DO NOT modify any other file.

## Read-Only Files / Evaluation Firewall

- `work/codify-enforcement/task-Z10-y19-y22-script-infra.md` (this file)
- `.claude/scripts/codex-implement.py`, `codex-wave.py`,
  `dual-teams-spawn.py` (downstream consumers)

## Acceptance Criteria

### AC-1 (Y19): result.md lands in main work/

Add `test_inline_dual_result_in_main_work_dir`:
- Use mocked subprocess.run on codex.cmd
- Call codex-inline-dual main with default settings
- Assert result.md path is under `<repo_root>/work/codex-implementations/`
  not under `<repo_root>/worktrees/inline/.../codex/work/codex-implementations/`

### AC-2 (Y19): --result-dir flag override works

`test_inline_dual_respects_result_dir_flag`:
- Same mock setup, pass `--result-dir <tmp_path>`
- Assert result lands at `tmp_path/task-<id>-result.md`

### AC-3 (Y22a): script in canonical location

After your changes: `pathlib.Path(".claude/scripts/sync-template-to-target.py").exists() == True` AND `pathlib.Path("work/sync-template-to-target.py").exists() == False`

### AC-4 (Y22b): script invocation allowed by enforcer (live test)

Add `test_a07_sync_script_invocation_allowed` to
`.claude/hooks/test_enforcer_live_attacks.py`:
- Build payload: `Bash(command="py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply")`
- Run hook subprocess
- Assert exit code 0 (allow) — whitelisted as own dual-tooling

The matrix grows from 18 to 19 tests, all PASS.

### AC-5: Existing 187 tests still pass

```bash
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_ask.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line
```

187 + 3 new = 190 expected.

### AC-6: Selftest still passes
`python .claude/scripts/dual-teams-selftest.py` → 6/6 PASS

## Test Commands

```bash
# 1. inline_dual tests (existing + Y19 additions)
python -m pytest .claude/scripts/test_codex_inline_dual.py -v --tb=line

# 2. Live attack matrix (19/19 with Y22 whitelist test)
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -v --tb=line

# 3. All other suites (187 must remain green minus old inline_dual count)
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_ask.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line

# 4. Selftest
python .claude/scripts/dual-teams-selftest.py

# 5. File location verification
python -c "import pathlib; assert pathlib.Path('.claude/scripts/sync-template-to-target.py').exists(); assert not pathlib.Path('work/sync-template-to-target.py').exists(); print('OK file moves')"
```

## Implementation hints

- For Y19: check codex-implement.py's `--result-dir` support first.
  If it's there, just pass-through. If not, do the copy in
  codex-inline-dual.py post-run.
- For Y22 relocation: `git mv` preserves history. Check imports — script
  uses only stdlib so should work from any location.
- For whitelist: `grep -n "codex-ask\|codex-implement" .claude/hooks/codex-delegate-enforcer.py`
  will find the whitelist constant. Add the new path.
- The Bash command parser already detects `py -3 <script.py>` —
  whitelist is the right kind of fix.
- For tests, refactor cmd construction into helper if needed.

## Self-report format

```
=== TASK Z10 SELF-REPORT ===
- status: pass | fail | blocker
- files modified: [list]
- new tests added: <count>
- net lines: <approx>
- Y19 approach: <1 line>
- Y22 approach: <1 line>
- live attack matrix: 19/19 PASS / <X>/19
- existing 187 tests still pass: yes / no
- selftest: PASS / FAIL
- file moves verified: yes / no
- NOTE: <surprising>
- BLOCKER: <only if>
- Final commit SHA: <SHA>
=== END SELF-REPORT ===
```
