---
executor: codex
risk_class: routine
speed_profile: fast
---

# Task Wave-B: `.claude/scripts/git_worktree_list.py`

## Your Task

Create a tiny diagnostic utility at `.claude/scripts/git_worktree_list.py` that prints one line per active git worktree in the current repository in the format `<worktree-path>\t<branch>\t<sha>`.

## Scope Fence

**Allowed paths (may be written):**
- `.claude/scripts/git_worktree_list.py` (new)

**Forbidden paths:**
- Every other file in the repository

## Test Commands (run after implementation)

```bash
python .claude/scripts/git_worktree_list.py
python -c "import subprocess, sys; r = subprocess.run([sys.executable, '.claude/scripts/git_worktree_list.py'], capture_output=True, text=True, check=True); out = r.stdout.strip(); assert out, 'empty output'; lines = out.splitlines(); assert lines, 'no lines'; first = lines[0].split('\t'); assert len(first) == 3, f'expected 3 tab-separated fields, got {len(first)}: {first}'; print('worktree-list ok')"
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: File `.claude/scripts/git_worktree_list.py` exists and is valid Python
- [ ] AC2: Running the script exits 0
- [ ] AC3: Each line of stdout is tab-separated with exactly three fields: path, branch, sha
- [ ] AC4: At least one line printed (the main worktree exists by definition)
- [ ] AC5: Script is under 60 lines
- [ ] AC6: Stdlib only (use `subprocess` to call `git worktree list --porcelain`)
- [ ] AC7: Module docstring + `main()` function with logger entry/exit
- [ ] All Test Commands exit 0

## Constraints

- Windows-compatible
- Handles worktrees in detached-HEAD state (branch field becomes short sha or `(detached)`)
- No side effects

## Handoff Output (MANDATORY)

codex-implement.py writes `task-wave-b-result.md` with diff + test output + self-report.
