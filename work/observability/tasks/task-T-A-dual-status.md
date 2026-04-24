---
executor: dual
risk_class: routine
speed_profile: balanced
---

# Task T-A: `.claude/scripts/dual-status.py` — dual-history summary CLI

## Your Task

Create a diagnostic CLI that scans the project's dual-implement audit trail and prints a summary table of every dual run the project has recorded.

Two input sources:
- `work/**/dual-history/<task-id>/` — canonical archive (claude-winner.diff, codex-loser.diff, codex-result.md, judge-verdict.json)
- `work/codex-implementations/task-*-result.md` — raw codex-implement output files

For each entry: task id, feature (parent dir), timestamp, winner (`claude`|`codex`|`tie`|`unknown`), claude-test-count if extractable, codex-status, claude-added-lines, codex-added-lines.

## Scope Fence
**Allowed:** `.claude/scripts/dual-status.py` (new), `.claude/scripts/test_dual_status.py` (new).
**Forbidden:** Any other path.

## Test Commands
```bash
python .claude/scripts/test_dual_status.py
python .claude/scripts/dual-status.py --help
python .claude/scripts/dual-status.py
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: CLI `dual-status.py [--json] [--since <duration>] [--feature <name>] [--project-root <path>]`. Text table default, `--json` emits list.
- [ ] AC2: `--since <duration>` formats `Nd`/`Nh`/`Nm`; filters older entries.
- [ ] AC3: `--feature <name>` filters to `work/<name>/...` subtree.
- [ ] AC4: Text table columns `task_id | feature | timestamp_iso | winner | claude_tests | codex_status | claude_lines | codex_lines`; aligned headers + summary line.
- [ ] AC5: JSON = valid json.loads-able array; each record has the column keys plus `path`.
- [ ] AC6: Corrupt result.md → record has `winner="unknown"`, `codex_status="parse-error"`; no crash; log.
- [ ] AC7: Exit 0 on empty project (empty table + `total: 0`).
- [ ] AC8: Sort by `timestamp` desc default; ties by task_id asc.
- [ ] AC9: Structured logging (stdlib), entry/exit/error.
- [ ] AC10: Stdlib only. Under 300 lines script + 300 lines tests.
- [ ] AC11: Unit tests (≥10): happy multi-entry, empty project, corrupt result, `--since 1d` filter, `--feature` filter, `--json` roundtrip, missing dual-history dir, missing codex-implementations dir, sort order, winner from judge-verdict.json.
- [ ] All Test Commands exit 0.

## Constraints
- Windows-compatible
- Winner priority: (1) judge-verdict.json, (2) commit-message heuristic via `git log` optional, (3) `unknown`.
- Robust to zero-dual-history project.

## Handoff Output
Standard `=== PHASE HANDOFF: T-A-dual-status ===` with sample rendered table.
