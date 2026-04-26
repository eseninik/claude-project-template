---
task_id: Z29-scaling-sync-rollback-auth
title: Criterion 6 Scaling — sync conflict guard + rollback + per-project auth verification
executor: dual
risk_class: routine
speed_profile: balanced
---

# Task Z29

## Goal

Criterion 6 (Scaling) currently 6/10. Three improvements for safe
multi-project deployment:

1. **Sync conflict guard** — `sync-template-to-target.py` must refuse
   to overwrite target files with local uncommitted modifications.
   Require `--force` flag for conscious override.
2. **Rollback mechanism** — `--rollback` flag stores pre-sync target
   state and can restore it.
3. **Per-project auth verification** — `verify-codex-auth.py` script
   checks codex.cmd works in target project's environment before sync
   proceeds.

## Three coordinated improvements

### Improvement 1 — Sync conflict guard

In `.claude/scripts/sync-template-to-target.py`:

Before overwriting any target file, check if it has uncommitted local
modifications via `git diff --quiet <file>`. If file is dirty:
- Without `--force`: skip with WARNING and add to summary.skipped_files
- With `--force`: overwrite (current behavior).

Add:
- `--force` flag (default False)
- `_target_has_local_changes(tgt_repo, file) -> bool` helper
- `LocallyModifiedSkipped` to plan.skipped_files

Add tests in NEW `.claude/scripts/test_sync_template_to_target.py`:
- `test_sync_skips_locally_modified_without_force`
- `test_sync_overwrites_locally_modified_with_force`
- `test_sync_normal_overwrite_when_target_clean`

### Improvement 2 — Rollback

Add to `sync-template-to-target.py`:
- `--rollback` flag — restores last sync's pre-state
- Pre-sync: snapshot all to-be-overwritten target files into
  `<target>/.claude/sync-rollback-snapshot/<timestamp>/...`
- On `--rollback`: read latest snapshot dir, restore each file

Tests:
- `test_sync_creates_rollback_snapshot`
- `test_rollback_restores_pre_sync_state`

### Improvement 3 — Per-project auth verification

NEW `.claude/scripts/verify-codex-auth.py`:
- Runs `codex.cmd whoami` (or `codex.cmd exec ping say OK`) in target's environment
- Reports whether authentication works
- Returns exit 0 if auth OK, 1 if not
- Used as pre-sync check (manual or in script)

Tests:
- `test_verify_codex_auth_subprocess_called`
- `test_verify_codex_auth_returns_zero_on_success`
- `test_verify_codex_auth_returns_one_on_failure`

## Scope Fence

```
.claude/scripts/sync-template-to-target.py
.claude/scripts/test_sync_template_to_target.py        (NEW)
.claude/scripts/verify-codex-auth.py                   (NEW)
.claude/scripts/test_verify_codex_auth.py              (NEW)
```

DO NOT modify any other file.

## Read-Only Files / Evaluation Firewall

- `work/criterion-upgrade/task-Z29-scaling-sync-rollback-auth.md`
- `.claude/scripts/codex-implement.py`, `codex-ask.py`, `judge*.py`

## Acceptance Criteria

### AC-1: Sync conflict guard tests pass (3 tests)

`test_sync_skips_locally_modified_without_force`,
`test_sync_overwrites_locally_modified_with_force`,
`test_sync_normal_overwrite_when_target_clean`.

### AC-2: Rollback tests pass (2 tests)

`test_sync_creates_rollback_snapshot`,
`test_rollback_restores_pre_sync_state`.

### AC-3: Auth verification tests pass (3 tests)

`test_verify_codex_auth_subprocess_called`,
`test_verify_codex_auth_returns_zero_on_success`,
`test_verify_codex_auth_returns_one_on_failure`.

### AC-4: Existing 130 tests still pass

```bash
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/scripts/test_spawn_agent.py .claude/scripts/test_determinism_chaos.py .claude/scripts/test_archive_active_context.py .claude/scripts/test_generate_changelog.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line
```

### AC-5: Selftest 6/6
`python .claude/scripts/dual-teams-selftest.py`

### AC-6: Live attack matrix 25/25
`python -m pytest .claude/hooks/test_enforcer_live_attacks.py -q --tb=line`

## Test Commands

```bash
# 1. New + existing sync tests
python -m pytest .claude/scripts/test_sync_template_to_target.py .claude/scripts/test_verify_codex_auth.py -v --tb=line

# 2. Existing 130 (regression)
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/scripts/test_spawn_agent.py .claude/scripts/test_determinism_chaos.py .claude/scripts/test_archive_active_context.py .claude/scripts/test_generate_changelog.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line

# 3. Selftest
python .claude/scripts/dual-teams-selftest.py
```

## Implementation hints

- For dirty check: `subprocess.run(["git", "-C", str(tgt_repo), "diff", "--quiet", "--", str(rel_file)])` returns 0 if clean, 1 if dirty.
- Snapshot dir: `<target>/.claude/sync-rollback-snapshot/<timestamp_iso>/<rel_path>` — preserve directory tree.
- Auth verification: `subprocess.run(["codex.cmd", "whoami"], timeout=10)` — but `whoami` requires TTY; use `codex.cmd exec - ...` with stdin "ping" instead, parse stdout for "OK" or any response.
- All scripts pure stdlib + filecmp/shutil/subprocess.

## Self-report format

```
=== TASK Z29 SELF-REPORT ===
- status: pass | fail | blocker
- Improvement 1 (conflict guard) approach: <1 line>
- Improvement 2 (rollback) approach: <1 line>
- Improvement 3 (auth verify) approach: <1 line>
- new tests: <count> (expected 8)
- existing 130 tests pass: yes / no
- attack matrix 25/25: yes / no
- selftest 6/6: PASS / FAIL
- net lines: <approx>
- files modified: [list]
- NOTE: <surprising>
- BLOCKER: <only if>
- Final commit SHA: <SHA>
=== END SELF-REPORT ===
```
