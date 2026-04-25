---
executor: dual
risk_class: routine
reasoning: high
speed_profile: balanced
---

# Task V-3: `.claude/scripts/worktree-cleaner.py` — list / delete stale dual-teams worktrees + branches

## Your Task

Stand-alone diagnostic + cleanup CLI that finds stale dual-implement worktrees (from `dual-teams-spawn.py`, `codex-wave.py`, `codex-inline-dual.py`) and optionally removes them along with their now-orphan local branches. Default mode is **list-only** (--dry-run). Destructive removal requires explicit `--apply`.

A worktree is considered **stale** if ANY of:
- (a) The worktree directory does not contain a tracked `.dual-base-ref` sentinel — meaning either FIX-B never wrote it (old run) or someone removed it manually. The mere directory existence under `worktrees/**/` without a sidecar is suspicious.
- (b) The branch its HEAD is on has not seen a commit in N+ days (default N=7, configurable via `--max-age-days`).
- (c) The branch contains zero non-merge commits beyond its base (i.e. nothing was actually built before abandonment).

The script lists every found worktree with the reasons it was flagged, exits 0. With `--apply`, it runs `git worktree remove --force <path>` followed by `git branch -D <branch>` per stale entry, with structured logging of each step.

## Scope Fence

**Allowed:**
- `.claude/scripts/worktree-cleaner.py` (new)
- `.claude/scripts/test_worktree_cleaner.py` (new)

**Forbidden:** any other path.

## Test Commands

```bash
py -3 .claude/scripts/test_worktree_cleaner.py
py -3 .claude/scripts/worktree-cleaner.py --help
py -3 .claude/scripts/worktree-cleaner.py --dry-run
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: CLI: `worktree-cleaner.py [--dry-run] [--apply] [--max-age-days N] [--worktree-prefix worktrees/] [--json] [--verbose]`. `--dry-run` is implicit when `--apply` is absent. `--apply` is the only mode that mutates anything.
- [ ] AC2: Discovery uses `git worktree list --porcelain` parsed via stdlib (no third-party libs). Filters to entries whose `worktree` path is inside the configured `--worktree-prefix` (default `worktrees/`).
- [ ] AC3: For each candidate, computes:
   - `has_sentinel` — `True` iff `<worktree>/.dual-base-ref` is a regular file
   - `last_commit_age_days` — `time() - max(commit timestamps on the worktree's branch since its base)`; if branch has no commits beyond base, age = `None` and stale via rule (c)
   - `branch_name` — from porcelain output
   - `reasons` — list of which rules ((a), (b), (c)) flagged it
- [ ] AC4: Default human-readable output:
  ```
  Found 3 stale worktree(s):
    [a,b] worktrees/fixes/codex/task-FIX-A-judge-diff-baseline (age=8d, no sentinel)
    [c]   worktrees/observability/claude/task-T-A-dual-status (no commits beyond base)
    ...
  Run with --apply to remove. Skipping (dry-run).
  ```
- [ ] AC5: `--json` emits `{"found":N, "stale":N, "kept":N, "entries":[{"worktree","branch","reasons":["a","b"],"has_sentinel","age_days","apply_status":"skipped|removed|error"}]}`.
- [ ] AC6: With `--apply`: for each stale entry, runs `git worktree remove --force <path>` then `git branch -D <branch>`. Each operation logged at INFO with success/failure. Continues on per-entry failure (do NOT abort the loop). Exit 0 if every step OK; exit 1 if any failure.
- [ ] AC7: Excludes the **main project worktree** from cleanup candidates regardless of age (it is not under `worktrees/`).
- [ ] AC8: Excludes worktrees whose branch matches the current `git symbolic-ref HEAD` of the main worktree (you cannot delete the branch you're on).
- [ ] AC9: Stdlib only. Windows-compatible. Under 300 lines script + 300 lines tests.
- [ ] AC10: Unit tests (≥10): (a) discovery from canned `git worktree list --porcelain` text, (b) sentinel-missing flags rule (a), (c) age threshold flags rule (b), (d) zero-commits flags rule (c), (e) main worktree excluded, (f) current-branch worktree excluded, (g) `--apply` invokes both git commands per entry, (h) `--json` schema round-trip, (i) failure on remove still reported and continues, (j) empty input → "No stale worktrees found", exit 0.
- [ ] All Test Commands above exit 0.

## Constraints

- Use `subprocess.run` not `os.system`. Quote path args properly for Windows spaces.
- Structured JSON logging via stdlib `logging`. Entry/exit/error logs every function. `--verbose` toggles DEBUG.
- The list-only default path must be **truly read-only** — assert `subprocess.run` for the destructive commands is never invoked when `--apply` is absent.
- Do NOT call `git gc` or any global maintenance commands. Per-worktree only.
- Cross-platform path quoting: prefer `Path` operations over string concat for paths.
- If your file will exceed ~250 lines including logging, USE Bash heredoc (`cat > <path> <<'END_MARK'`) instead of Write — harness silently denies large Writes.

## Handoff Output

Standard `=== PHASE HANDOFF: V-3-worktree-cleaner ===` with sample dry-run output on this repo's actual stale worktrees and a trailing summary count.
