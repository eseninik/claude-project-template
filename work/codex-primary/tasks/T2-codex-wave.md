---
executor: claude
risk_class: routine
reasoning: high
wave: 1
---

# Task T2: `.claude/scripts/codex-wave.py` + `.claude/scripts/codex-scope-check.py`

## Your Task
Build two scripts:

1. **codex-wave.py** — spawn N parallel `codex-implement.py` processes, each in its own git worktree, monitor them, aggregate results.
2. **codex-scope-check.py** — small utility that checks a git diff against a scope fence.

Both support tech-spec.md Sections 7 and 8.

## Scope Fence
**Allowed paths (may be written):**
- `.claude/scripts/codex-wave.py` (new)
- `.claude/scripts/codex-scope-check.py` (new)
- `.claude/scripts/test_codex_wave.py` (new)
- `.claude/scripts/test_codex_scope_check.py` (new)

**Forbidden paths:**
- `.claude/shared/templates/new-project/**`
- `.claude/scripts/codex-implement.py` (T1's scope; do not touch even if you think it has a bug — report instead)
- `work/codex-primary/tech-spec.md`

## Test Commands
```bash
py -3 .claude/scripts/test_codex_scope_check.py
py -3 .claude/scripts/test_codex_wave.py
py -3 .claude/scripts/codex-scope-check.py --help
py -3 .claude/scripts/codex-wave.py --help
```

## Acceptance Criteria (IMMUTABLE)

### codex-scope-check.py
- [ ] AC1: CLI accepts `--diff <file|->` and `--fence <file|inline>` per tech-spec 8
- [ ] AC2: Parses `diff --git a/... b/...` headers to extract modified paths
- [ ] AC3: Normalizes paths with `os.path.realpath` to prevent `..` traversal escape
- [ ] AC4: Path is OK iff it's under at least one allowed fence entry AND not under any forbidden entry
- [ ] AC5: Exit 0 = all OK, exit 2 = at least one violation; stdout lists violators
- [ ] AC6: Unit test covers: no violations, one violation, path traversal attempt, empty diff, malformed diff

### codex-wave.py
- [ ] AC7: CLI accepts `--tasks <csv|glob>`, `--parallel <N>`, `--worktree-base <path>`, `--timeout-per-task <sec>`
- [ ] AC8: For each task, creates `git worktree add worktrees/codex-wave/T{N}/ -b codex-wave/T{N}` from current branch
- [ ] AC9: Uses subprocess + semaphore (threading or asyncio) to run up to `--parallel` concurrent codex-implement.py
- [ ] AC10: As each subprocess finishes, captures its result.md and records entry in `work/codex-primary/codex-wave-report.md`
- [ ] AC11: Handles individual task failure without killing the wave (continues with remaining tasks)
- [ ] AC12: On exit (success or interrupt), does NOT auto-remove worktrees — leaves them for Opus to merge; but logs their paths prominently in the report
- [ ] AC13: Every function has structured logging per logging-standards
- [ ] AC14: Unit test covers: task-list parsing, parallel launcher (mock subprocess), timeout handling, failure isolation

### Both scripts
- [ ] AC15: Every new function has entry/exit/error logs (logging-standards)
- [ ] AC16: `--help` for both shows all flags with descriptions
- [ ] All Test Commands exit 0

## Skill Contracts

### verification-before-completion
- Run every Test Command. If any fails, DO NOT claim done.
- Verify each AC with evidence.

### logging-standards
- Same as T1: structured loggers for every function. `structlog` if project uses it, else stdlib `logging`.
- No bare print() for log-like output. CLI user output is OK via print().

### coding-standards
- Mirror the style of other scripts in `.claude/scripts/`
- Type hints everywhere
- Use `pathlib.Path`
- `subprocess.run(..., check=False, timeout=..., capture_output=True, text=True)`

## Read-Only Files (Evaluation Firewall)
- `work/codex-primary/tech-spec.md`
- `.claude/scripts/test_codex_wave.py` and `test_codex_scope_check.py` once written
- `.claude/scripts/codex-implement.py` (other task's output)

## Constraints
- Windows compatibility. Use `ProcessPoolExecutor` or manual `subprocess.Popen` with semaphore — not os.fork.
- Worktree creation must work on Windows (forward-slash paths are fine for git; but actual fs paths may be backslash)
- When unit-testing codex-wave.py, mock codex-implement.py subprocess (don't actually call Codex)

## Handoff Output (MANDATORY)
Standard `=== PHASE HANDOFF ===` block. Files Modified: 4 files.

## Notes
- You may reference `.claude/scripts/ao-hybrid.sh` for worktree management pattern — but that's bash; translate into Python
- codex-scope-check.py is called from codex-implement.py, but this circular dependency is OK because codex-scope-check.py has no runtime dep on codex-implement.py
