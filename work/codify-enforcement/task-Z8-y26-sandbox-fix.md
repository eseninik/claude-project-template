---
task_id: Z8-y26-sandbox-fix
title: Y26 fix — Codex CLI v0.125 silently ignores --sandbox workspace-write; switch to --dangerously-bypass-approvals-and-sandbox
executor: dual
risk_class: high-stakes
speed_profile: balanced
---

# Task Z8 — Y26 fix: Codex CLI v0.125 sandbox arg silently ignored

## Goal

Codex CLI v0.125 silently ignores both `--sandbox workspace-write` flag
AND `-c sandbox_*` config overrides for `exec` mode. Sandbox is ALWAYS
`read-only` unless `--dangerously-bypass-approvals-and-sandbox` is used.
Empirically confirmed via 4 different argv shapes.

Effect: every `codex-implement.py` invocation got `sandbox: read-only`,
Codex literally cannot write files. All 3 dual-implement runs since
relogin (Y23/Z5/Z7) produced empty diffs and Claude won by walkover.
Without this fix dual-implement is degraded to single-implement.

This is a v0.125 regression vs v0.117. Fix: replace
`--sandbox workspace-write --full-auto` with
`--dangerously-bypass-approvals-and-sandbox`.

Risk acknowledgment (per Codex review): this IS a capability escalation,
not just a bug fix. Acceptable in OUR pipeline because:
- Runs inside an isolated git worktree (`--cd <worktree>`)
- Worktree on its own branch — losing tree = local-branch-only loss
- Scope-fence checker validates ALL writes post-hoc against task fence
- Worktrees contain no production secrets
- Alternative (read-only) makes Codex completely useless

## The minimal fix

In `.claude/scripts/codex-implement.py` find the `cmd = [...]` block
(~lines 831-844). Currently:

```python
cmd = [
    codex,
    "exec",
    "-c", chatgpt_provider,
    "-c", "model_provider=chatgpt",
    "--model",
    model,
    "--sandbox",
    "workspace-write",
    "--full-auto",
    "--cd",
    str(worktree.resolve()),
    "-",
]
```

After:

```python
cmd = [
    codex,
    "exec",
    "-c", chatgpt_provider,
    "-c", "model_provider=chatgpt",
    "--model",
    model,
    # v0.125: --sandbox workspace-write + --full-auto are silently
    # ignored for `exec` mode (sandbox always becomes read-only).
    # Y26 fix: bypass — runs only inside disposable git worktree.
    "--dangerously-bypass-approvals-and-sandbox",
    "--cd",
    str(worktree.resolve()),
    "-",
]
```

Net change: 3 flag lines removed + 1 flag line added (plus 3-line comment).

Also update:
- Module docstring at line 4 ("workspace-write sandbox" -> "danger-full-access in disposable worktree (Y26: v0.125 sandbox flag broken)")
- `run_codex` docstring at line 793 (similar wording)
- argparse description at line 1206 (similar)

## Scope Fence — files you MAY modify

```
.claude/scripts/codex-implement.py
.claude/scripts/test_codex_implement.py     (add 2 regression tests)
```

DO NOT modify any other file.

## Read-Only Files / Evaluation Firewall

- `work/codify-enforcement/task-Z8-y26-sandbox-fix.md` (this file)
- `.claude/scripts/codex-wave.py`, `codex-inline-dual.py`, `dual-teams-spawn.py` (downstream consumers)
- `.claude/hooks/codex-delegate-enforcer.py`

## Acceptance Criteria

### AC-1: argv contains the bypass flag (mocked test)

Add 2 tests to `.claude/scripts/test_codex_implement.py`:

- `test_argv_uses_dangerously_bypass_flag()` — Use `monkeypatch` on
  `subprocess.run` to capture the argv passed to Codex. Assert the argv
  contains `"--dangerously-bypass-approvals-and-sandbox"`.

- `test_argv_does_not_contain_sandbox_workspace_write()` — Same capture.
  Assert `"--sandbox" not in cmd` AND `"workspace-write" not in cmd` AND
  `"--full-auto" not in cmd`.

These tests must NOT make a real Codex call — pure argv inspection.

If the cmd is built inline inside `run_codex` and is hard to inspect
without running it, refactor: extract a tiny helper
`_build_codex_argv(codex, model, worktree, chatgpt_provider) -> list[str]`
and have tests call it directly. Refactor is in scope.

### AC-2: Existing test_codex_implement.py tests still pass

Run `python -m pytest .claude/scripts/test_codex_implement.py -q` —
all existing tests must still pass. The change is internal flag swap;
no API change.

### AC-3: Selftest still passes

`python .claude/scripts/dual-teams-selftest.py` -> exit 0, 6/6 PASS.

### AC-4: All other test suites still pass (123 total)

`python -m pytest .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py .claude/scripts/test_codex_ask.py -q --tb=line`

## Test Commands

```bash
# 1. test_codex_implement.py (existing + new)
python -m pytest .claude/scripts/test_codex_implement.py -q --tb=line

# 2. Regression — all other suites (123 total)
python -m pytest .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py .claude/scripts/test_codex_ask.py -q --tb=line

# 3. Selftest
python .claude/scripts/dual-teams-selftest.py
```

## Implementation hints

- The `cmd = [...]` block is a list literal — straightforward identification.
- Refactoring to `_build_codex_argv()` helper makes tests trivial and
  keeps the production code path identical (`run_codex` calls it once).
- Do NOT add CLI flags to expose this choice — it's a hard internal
  decision (always bypass for our pipeline).
- Logging: existing `codex cmd` log already includes `argv_head=cmd[:9]`
  which will show the bypass flag automatically.

## Self-report format

```
=== TASK Z8 SELF-REPORT ===
- status: pass | fail | blocker
- net lines: <approx>
- files modified: [list]
- new tests added: <count>
- new tests PASSING: <count>
- existing test_codex_implement.py tests pass: <X> / <Y>
- live attack matrix 18/18: yes / no
- selftest 6/6: PASS / FAIL
- approach: <1 line>
- NOTE: <surprising>
- BLOCKER: <only if>
- Final commit SHA: <SHA>
=== END SELF-REPORT ===
```
