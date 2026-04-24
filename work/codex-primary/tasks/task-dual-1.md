---
executor: dual
risk_class: routine
reasoning: high
---

# Task Dual-1: Add `--json` flag to `.claude/scripts/list_codex_scripts.py`

## Your Task

Extend the existing utility `list_codex_scripts.py` with a `--json` CLI flag. When the flag is present, instead of the plain text output, the script must print a single JSON document to stdout with the shape:

```json
{
  "scripts": [
    {"name": "codex-ask.py", "line_count": 171},
    {"name": "codex-implement.py", "line_count": 1100}
  ],
  "total_files": 2,
  "total_lines": 1271
}
```

Default behaviour (no flag) remains exactly unchanged — existing plain-text output must pass the same tests as before. The `--json` output must be valid JSON parseable by `json.loads`.

## Scope Fence

**Allowed paths (may be written):**
- `.claude/scripts/list_codex_scripts.py` (modify only — do not create new files)

**Forbidden paths:**
- Every other file in the repository
- Especially: no new test files, no edits to existing tests, no edits to other scripts or hooks

## Test Commands (run after implementation)

```bash
py -3 .claude/scripts/list_codex_scripts.py
py -3 .claude/scripts/list_codex_scripts.py --json
py -3 -c "import json, subprocess; out = subprocess.run(['py','-3','.claude/scripts/list_codex_scripts.py','--json'], capture_output=True, text=True, check=True).stdout; data = json.loads(out); assert 'scripts' in data and 'total_files' in data and 'total_lines' in data; assert isinstance(data['scripts'], list) and len(data['scripts']) >= 4; assert all('name' in s and 'line_count' in s for s in data['scripts']); assert data['total_files'] == len(data['scripts']); assert data['total_lines'] == sum(s['line_count'] for s in data['scripts']); print('json ok')"
```

All three commands must exit 0. The last one is the strictest — it parses the JSON and validates the schema + invariants.

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: Default (no flag) output is unchanged — `codex-ask.py  171`-style lines plus the `total:` summary line
- [ ] AC2: `--json` flag prints exactly one valid JSON document to stdout
- [ ] AC3: JSON schema: top-level object with keys `scripts` (list), `total_files` (int), `total_lines` (int)
- [ ] AC4: Each entry in `scripts` list has exactly two keys: `name` (str) and `line_count` (int)
- [ ] AC5: `total_files` equals `len(scripts)`; `total_lines` equals the sum of `line_count` across all entries
- [ ] AC6: The set of script names in JSON mode equals the set printed in default mode (no drift between the two output paths)
- [ ] AC7: When `--json` is present, NO plain-text `name  count` or `total: ...` lines are emitted — JSON only
- [ ] AC8: Script still uses only Python stdlib (`argparse`, `json`, `pathlib`, `logging` are all fine — no third-party)
- [ ] AC9: Entry into main() and exit from main() still have structured logger calls
- [ ] AC10: Module docstring is updated to mention the new flag
- [ ] All three Test Commands exit 0

## Skill Contracts

### verification-before-completion (contract extract)
- Run every Test Command and quote stdout when reporting. Do NOT claim done if any exits non-zero.
- Validate AC6 specifically by running both default and `--json` modes and diffing the script names manually — this catches drift bugs silently introduced during refactoring.

### logging-standards (contract extract)
- New `--json` path: if you add any new helper function, give it structured entry/exit/error logs like the existing ones.
- No bare `print()` for log data — `print()` is reserved for the actual user-facing output (JSON or plain text).

### coding-standards (contract extract)
- Follow the existing style of the file (type hints, pathlib, docstrings, module-level constants).
- Minimal diff — do not refactor unrelated code. Every line added must serve the `--json` feature.

## Read-Only Files (Evaluation Firewall)

- This task-dual-1.md itself
- All test files (`test_*.py`, `*_test.py`)
- Every other file except `.claude/scripts/list_codex_scripts.py`

## Constraints

- Under 120 lines total after change (the original is ~58)
- Deterministic JSON output: keys in the order specified above; entries in the `scripts` list sorted alphabetically by name (matches default mode)
- Use `json.dumps(..., indent=2)` for readability
- Windows-compatible

## Handoff Output (MANDATORY)

Two paths produce this:
- **Claude teammate (worktree A):** writes the standard `=== PHASE HANDOFF: task-dual-1-claude ===` block.
- **codex-implement.py (worktree B):** produces `work/codex-implementations/task-dual-1-result.md` with diff + test output + self-report.

Opus (with cross-model-review skill) then reads both artifacts, runs the judge protocol from the `dual-implement` skill, and picks the winner or composes a hybrid merge.

## Iteration History

(First round — no prior attempts.)
