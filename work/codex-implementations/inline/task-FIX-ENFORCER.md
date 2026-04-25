---
executor: dual
risk_class: high-stakes
reasoning: high
speed_profile: balanced
---

# Task FIX-ENFORCER: codex-delegate-enforcer.py — exempt dual-teams worktrees via `.dual-base-ref` sentinel

## Your Task

**Y6 root cause.** `codex-delegate-enforcer.py` is a `PreToolUse` hook that blocks `Edit`/`Write`/`MultiEdit` on code files unless a fresh (< 15 min) `work/codex-implementations/task-*-result.md` with `status=pass` covers the target path.

When a Claude teammate runs **inside a dual-teams worktree** (e.g. `worktrees/validation/claude/task-V1-...`), the teammate's `CLAUDE_PROJECT_DIR` resolves to the worktree root — not the main repo. The teammate's project-relative target path becomes `.claude/scripts/foo.py`, which **does not match the existing `worktrees/**` exempt pattern** (that pattern only fires when the path *includes* `worktrees/...` as a prefix, i.e. when the planner session edits files inside a worktree from the main project root).

Net effect: every code Edit by the writer-half of a dual-implement run is denied. The teammate keeps retrying → 600 s watchdog kill → false "Claude teammate stalled" symptom.

The fix is to give the enforcer a reliable, location-independent signal that "this session IS the writer-half of a dual-implement run, the parallel Codex sibling is already executing — skip enforcement". The signal exists: `.dual-base-ref` is written by `codex-wave.py` and `dual-teams-spawn.py` into every freshly-created teammate worktree (FIX-B from Round 1).

Implement an ancestor walk: at the top of `decide()`, check whether `project_dir` (or any of its parents up to the filesystem root) holds a `.dual-base-ref` regular file. If yes → log `dual-teams-worktree`, return `True` (allow), skip the cover lookup entirely. If no → existing behavior unchanged.

The walk is bounded (`while parent != self`), guarded by a `seen` set against cycles, and tolerant of `OSError` on each `is_file()` probe (network drives, broken symlinks). No external dependencies.

## Scope Fence

**Allowed:**
- `.claude/hooks/codex-delegate-enforcer.py` (modify — add `is_dual_teams_worktree(project_dir)` helper + early-allow branch in `decide()`)
- `.claude/hooks/test_codex_delegate_enforcer.py` (modify — add tests; do NOT remove existing tests)

**Forbidden:**
- Every other path under `.claude/hooks/` and `.claude/scripts/`
- Any `work/*` or `worktrees/*` path
- Anything elsewhere in the repo

## Test Commands

```bash
py -3 .claude/hooks/test_codex_delegate_enforcer.py
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: New module-level function `is_dual_teams_worktree(project_dir: Path) -> bool` returns `True` iff `project_dir` *or any of its ancestors up to the filesystem root* contains a regular file named `.dual-base-ref`.
- [ ] AC2: The walk terminates: bounded by `parent == self` AND a `seen: set` of resolved Paths against pathological loops.
- [ ] AC3: The walk is exception-safe: each `is_file()` probe is wrapped so an `OSError` (e.g. permission denied on a network share) is treated as "not present" rather than propagating.
- [ ] AC4: `decide()` calls `is_dual_teams_worktree(project_dir)` immediately after the existing `event` and `tool_name` early-returns. If True → log `decide.passthrough reason=dual-teams-worktree project=<path>` and `return True`. The cover lookup loop is skipped entirely.
- [ ] AC5: When sentinel is absent, `decide()` behavior is byte-for-byte identical to before — every existing test in `test_codex_delegate_enforcer.py` still passes.
- [ ] AC6: NEW tests in `test_codex_delegate_enforcer.py`:
   - (a) `is_dual_teams_worktree` returns True when sentinel is in the project_dir itself.
   - (b) Returns True when sentinel is in a parent directory (deep nesting).
   - (c) Returns False when no sentinel exists anywhere in the chain.
   - (d) Returns False when the sentinel name exists but is a directory, not a regular file.
   - (e) `decide()` returns True (allow) for an Edit on `.claude/scripts/foo.py` when sentinel is present, even with NO fresh result.md anywhere.
   - (f) `decide()` returns False (deny) for the same Edit when sentinel is absent and no fresh result.md (existing behavior preserved).
- [ ] AC7: Structured logging: function entry/exit + the early-allow log line at INFO level. No bare prints.
- [ ] AC8: Stdlib only. Windows + POSIX both supported (use `Path` not `os.path`).
- [ ] AC9: `is_dual_teams_worktree` accepts `Path` only (matches existing `project_dir` type in this module).
- [ ] All Test Commands above exit 0.

## Constraints

- Do NOT change the existing `EXEMPT_PATTERNS` list — the sentinel check is an *additional* gate, not a replacement for the path-pattern exemption.
- Do NOT change any other file. Surgical fix, ~25 lines total in the hook + ~50 lines of new tests.
- Do NOT change the logging level conventions of the file (INFO for events, DEBUG for traces).
- The function name MUST be `is_dual_teams_worktree` exactly (other code may grow to depend on it).
- Use the existing `_build_logger` / `logging.getLogger(HOOK_NAME)` pattern; do NOT introduce a new logger.
- Tests must be self-contained (use `tempfile.TemporaryDirectory`, no fixtures of external paths).

## Handoff Output

Standard `=== PHASE HANDOFF: FIX-ENFORCER ===` with:
- Diff stats (lines added/removed in hook + tests)
- Output of `py -3 .claude/hooks/test_codex_delegate_enforcer.py` showing all tests pass (count of OK)
- Three-line note: "fix path: sentinel ancestor walk in `decide()` — see is_dual_teams_worktree()."
