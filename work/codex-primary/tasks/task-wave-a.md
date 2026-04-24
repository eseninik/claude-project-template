---
executor: codex
risk_class: routine
speed_profile: fast
---

# Task Wave-A: `.claude/scripts/codex_env_check.py`

## Your Task

Create a tiny diagnostic utility at `.claude/scripts/codex_env_check.py` that prints a one-line-per-fact snapshot of the Codex runtime environment: Python version, current working directory, whether the `codex` CLI is on PATH, and the number of entries in PATH.

## Scope Fence

**Allowed paths (may be written):**
- `.claude/scripts/codex_env_check.py` (new)

**Forbidden paths:**
- Every other file in the repository

## Test Commands (run after implementation)

```bash
python .claude/scripts/codex_env_check.py
python -c "import subprocess, sys; r = subprocess.run([sys.executable, '.claude/scripts/codex_env_check.py'], capture_output=True, text=True, check=True); out = r.stdout; assert 'python_version:' in out; assert 'cwd:' in out; assert 'codex_on_path:' in out; assert 'path_entries:' in out; print('env-check ok')"
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: File `.claude/scripts/codex_env_check.py` exists and is valid Python
- [ ] AC2: Running the script exits 0
- [ ] AC3: Stdout contains at minimum these lines (format `key: value`):
  - `python_version: <version>`
  - `cwd: <absolute path>`
  - `codex_on_path: <true|false>`
  - `path_entries: <integer>`
- [ ] AC4: Script is under 50 lines (excluding blank lines and docstring)
- [ ] AC5: Stdlib only
- [ ] AC6: Module docstring explains what the utility is for
- [ ] AC7: `main()` function with logger entry/exit (stdlib `logging`)
- [ ] All Test Commands exit 0

## Constraints

- Windows-compatible
- No side effects — pure read-only reporting
- Use `shutil.which("codex")` for the CLI check

## Handoff Output (MANDATORY)

codex-implement.py writes `task-wave-a-result.md` with diff + test output + self-report.
