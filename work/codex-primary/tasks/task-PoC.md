---
executor: codex
risk_class: routine
reasoning: high
---

# Task PoC: `.claude/scripts/list_codex_scripts.py`

## Your Task
Create a small, self-contained Python utility at `.claude/scripts/list_codex_scripts.py` that lists all files matching pattern `.claude/scripts/codex*.py` with their line counts, sorted alphabetically by filename.

This script is part of proof-of-concept for the codex-primary-implementer pipeline. It exercises end-to-end delegation of a real coding task to GPT-5.5 via codex-implement.py.

## Scope Fence

**Allowed paths (may be written):**
- `.claude/scripts/list_codex_scripts.py` (new)

**Forbidden paths (must NOT be modified):**
- Any other file in the repository

## Test Commands (run after implementation)

```bash
py -3 .claude/scripts/list_codex_scripts.py
```

The output must:
- Exit with code 0
- Print to stdout one line per `.claude/scripts/codex*.py` file in the format `<filename>  <line_count>` (filename without directory prefix, line count right after)
- Sort lines alphabetically by filename
- End with a summary line: `total: N files, M lines`

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: File `.claude/scripts/list_codex_scripts.py` exists and is valid Python (parses without SyntaxError)
- [ ] AC2: Running `py -3 .claude/scripts/list_codex_scripts.py` exits 0
- [ ] AC3: Output contains entries for all expected files: `codex-ask.py`, `codex-implement.py`, `codex-scope-check.py`, `codex-wave.py` (at minimum)
- [ ] AC4: Each file-entry line format: filename followed by whitespace then integer line count (e.g., `codex-ask.py  150`)
- [ ] AC5: Entries are sorted alphabetically by filename
- [ ] AC6: Last line starts with `total:` and contains both a file count and a line count
- [ ] AC7: Script uses only Python stdlib (no external imports)
- [ ] AC8: Script has basic structured logging (stdlib `logging`) — at minimum a logger call at entry and exit of the main function
- [ ] AC9: Script has a module docstring explaining what it does

## Skill Contracts

### verification-before-completion (contract extract)
- Run the Test Command above. Verify every AC with evidence. Quote the stdout output.

### logging-standards (contract extract)
- At least one structured `logger.info` call at function entry and exit
- No bare `print()` for log-like data — `print()` is only for the actual user-facing output (the file listing + summary)
- Do NOT log any file contents — only file names and line counts

### coding-standards (contract extract)
- Use `pathlib.Path`, type hints on functions
- Single-file script, no sub-modules
- Under 80 lines total

## Read-Only Files (Evaluation Firewall)
- All test files (`test_*.py`, `*_test.py`)
- This task-PoC.md file itself
- All other files in the repository

## Constraints

- Windows-compatible (use `pathlib`, forward-slash patterns are fine for Path glob)
- No external dependencies — stdlib only
- Under 80 lines of code total (including docstring + logging setup)
- Deterministic output: same input repo state → same output every time

## Handoff Output (MANDATORY)

codex-implement.py will write `work/codex-implementations/task-PoC-result.md` with:
- Status (pass / fail / scope-violation / timeout)
- Full diff
- Test output
- Self-report
- Timestamp

## Notes

This is a PoC task for the codex-primary-implementer pipeline. Goal: prove end-to-end task-N.md → codex exec (GPT-5.5 high reasoning) → diff in scope fence → tests pass → result.md written.
