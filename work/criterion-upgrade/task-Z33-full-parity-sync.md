---
task_id: Z33-full-parity-sync
title: Full QA-Legal parity sync — top-level CI/CHANGELOG/mypy.ini mirroring
executor: dual
risk_class: routine
speed_profile: balanced
---

# Task Z33

## Goal

User wants QA Legal byte-identical infrastructure to template (except
project-specific files). Current `sync-template-to-target.py` mirrors
`.claude/...` categories but SKIPS three top-level files created in
Round 8: `.github/workflows/dual-implement-ci.yml` (Z26),
`CHANGELOG.md` (Z26), `mypy.ini` (Z32). They must land in target for
full parity.

## The fix

In `.claude/scripts/sync-template-to-target.py` add new constant
`MIRROR_TOP_FILES` listing the three relative paths above. After the
per-category mirror loop, iterate this list and use the same per-file
helper (with `--force` and rollback semantics).

Add 4 tests in `test_sync_template_to_target.py`:
- `test_mirror_top_files_constant_lists_three_files`
- `test_sync_mirrors_top_level_dual_implement_ci_yml`
- `test_sync_mirrors_top_level_changelog_and_mypy_ini`
- `test_top_files_skipped_when_locally_modified_without_force`

## Scope Fence

```
.claude/scripts/sync-template-to-target.py
.claude/scripts/test_sync_template_to_target.py
```

DO NOT modify any other file.

## Read-Only Files / Evaluation Firewall

- `work/criterion-upgrade/task-Z33-full-parity-sync.md`
- `.github/workflows/dual-implement-ci.yml`, `CHANGELOG.md`, `mypy.ini`
  (source files; do not modify)

## Acceptance Criteria

### AC-1
`test_mirror_top_files_constant_lists_three_files` PASSES.

### AC-2
`test_sync_mirrors_top_level_dual_implement_ci_yml` PASSES.

### AC-3
`test_sync_mirrors_top_level_changelog_and_mypy_ini` PASSES.

### AC-4
`test_top_files_skipped_when_locally_modified_without_force` PASSES.

### AC-5: Existing tests still pass
```bash
python -m pytest .claude/scripts/test_sync_template_to_target.py -q --tb=line
```

### AC-6: Live attack matrix 25/25
```bash
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -q --tb=line
```

### AC-7: Selftest 6/6
`python .claude/scripts/dual-teams-selftest.py`

## Test Commands

```bash
python -m pytest .claude/scripts/test_sync_template_to_target.py -v --tb=line
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -q --tb=line
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/scripts/test_spawn_agent.py .claude/scripts/test_determinism_chaos.py .claude/scripts/test_archive_active_context.py .claude/scripts/test_generate_changelog.py .claude/scripts/test_verify_codex_auth.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line
python .claude/scripts/dual-teams-selftest.py
```

## Implementation hints

- `MIRROR_TOP_FILES` near `MIRROR_DIRS`.
- After category loop add `for top in MIRROR_TOP_FILES: <call same per-file helper>`.
- Honor `--force` (refuse overwrite of locally-modified target without it)
  AND `--rollback` (snapshot pre-state) — same as existing mirror behavior.
- Tests use `tmp_path` fixture for synthetic source/target trees.

## Self-report format

```
=== TASK Z33 SELF-REPORT ===
- status: pass | fail | blocker
- approach: <1 line>
- new tests: <count>
- existing tests pass: yes / no
- attack matrix 25/25: yes / no
- selftest 6/6: PASS / FAIL
- net lines: <approx>
- files modified: [list]
- conflict guard works for top files: yes / no
- NOTE: <surprising>
- BLOCKER: <only if>
- Final commit SHA: <SHA>
=== END SELF-REPORT ===
```
