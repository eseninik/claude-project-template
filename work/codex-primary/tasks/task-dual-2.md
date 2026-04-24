---
executor: dual
risk_class: routine
reasoning: high
---

# Task Dual-2: Add `--sort-by` flag to `.claude/scripts/list_codex_scripts.py`

## Your Task

Extend the existing utility with a `--sort-by {name,lines}` CLI flag.

- `--sort-by name` (default, and when flag is omitted): current behaviour — entries sorted alphabetically by filename, ascending.
- `--sort-by lines`: entries sorted by `line_count`, **descending** (biggest file first); ties broken alphabetically by `name`, ascending.

This must work in BOTH the plain-text output mode AND the `--json` output mode (from dual-1). The sort choice affects ordering in both, identically.

## Scope Fence

**Allowed paths (may be written):**
- `.claude/scripts/list_codex_scripts.py` (modify only — do not create new files)

**Forbidden paths:**
- Every other file in the repository

## Test Commands (run after implementation)

```bash
python .claude/scripts/list_codex_scripts.py
python .claude/scripts/list_codex_scripts.py --sort-by name
python .claude/scripts/list_codex_scripts.py --sort-by lines
python .claude/scripts/list_codex_scripts.py --json --sort-by lines
python -c "import json, subprocess, sys; out = subprocess.run([sys.executable, '.claude/scripts/list_codex_scripts.py', '--json', '--sort-by', 'lines'], capture_output=True, text=True, check=True).stdout; data = json.loads(out); counts = [s['line_count'] for s in data['scripts']]; assert counts == sorted(counts, reverse=True), f'lines not desc-sorted: {counts}'; print('lines-desc ok')"
python -c "import json, subprocess, sys; out = subprocess.run([sys.executable, '.claude/scripts/list_codex_scripts.py', '--json'], capture_output=True, text=True, check=True).stdout; data = json.loads(out); names = [s['name'] for s in data['scripts']]; assert names == sorted(names), f'names not alpha-sorted: {names}'; print('name-asc ok')"
```

All six commands must exit 0. `python` is used instead of `py -3` because
some Codex sandbox environments on Windows do not expose the `py` launcher
in PATH (Finding #10 from dual-1 post-mortem).

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: Default (no flag, or `--sort-by name`) output matches the pre-change output byte-for-byte — alphabetical by filename
- [ ] AC2: `--sort-by lines` orders entries by `line_count` descending; ties broken alphabetically ascending by `name`
- [ ] AC3: Sort is applied identically in BOTH `--json` and plain-text modes
- [ ] AC4: `--sort-by` accepts exactly two values: `name`, `lines` — any other value exits non-zero with a clear argparse error
- [ ] AC5: Combining `--json --sort-by lines` outputs valid JSON with entries in `line_count`-desc order
- [ ] AC6: JSON schema unchanged from dual-1: `{scripts, total_files, total_lines}`; each entry `{name, line_count}`
- [ ] AC7: `total_files` and `total_lines` are independent of sort order (same values regardless of `--sort-by`)
- [ ] AC8: Module docstring is updated to mention `--sort-by`
- [ ] AC9: Stdlib only (`argparse`, `json`, `pathlib`, `logging`)
- [ ] AC10: Under 140 lines total after change (was ~98 after dual-1)
- [ ] All six Test Commands exit 0

## Skill Contracts

### verification-before-completion (contract extract)
- Run every Test Command. Quote stdout when reporting. Do NOT claim done if any exits non-zero.
- Specifically verify AC2 by running `--sort-by lines` and visually confirming the order is desc by `line_count` — the last Test Command asserts this programmatically.

### logging-standards (contract extract)
- Preserve/extend existing structured logger calls. If you add a helper function, give it entry/exit logs.
- `print()` only for user-facing output. No bare prints for log data.

### coding-standards (contract extract)
- Minimal diff. Do not refactor unrelated code.
- Match existing style: type hints, pathlib, module-level constants, docstrings.
- Keep the dual-1 `--json` feature intact — this task extends, not replaces.

## Read-Only Files (Evaluation Firewall)

- This task-dual-2.md itself
- All test files (`test_*.py`, `*_test.py`)
- Every other file except `.claude/scripts/list_codex_scripts.py`

## Constraints

- Under 140 lines
- Windows-compatible
- Sort order must be stable (same inputs → same output every time)
- When `--sort-by lines`: ties within same `line_count` MUST be broken by name-ascending, documented in code

## Handoff Output (MANDATORY)

Two paths produce this:
- **Claude teammate (worktree A):** writes standard `=== PHASE HANDOFF: task-dual-2-claude ===` block.
- **codex-implement.py (worktree B):** writes `work/codex-implementations/task-dual-2-result.md` with diff + test output + self-report.

Opus reads both, judges, picks winner or merges hybrid.

## Iteration History

- **Dual-1** (2026-04-24) — same shape of task: added `--json` flag. Claude won by default because Codex's diff was destroyed by false-positive scope-check + aggressive rollback. Post-mortem: `work/codex-primary/dual-1-postmortem.md`. Four bugs fixed in commit `b407c3a` before starting this round.
- **Key correction vs dual-1:** Test Commands use `python` (not `py -3`) to avoid Finding #10 sandbox PATH issue.
