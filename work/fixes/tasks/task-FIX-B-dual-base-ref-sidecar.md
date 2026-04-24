---
executor: dual
risk_class: routine
reasoning: high
speed_profile: balanced
---

# Task FIX-B: dual-teams-spawn + codex-wave — write `.dual-base-ref` sidecar

## Your Task

The `judge.py` (being fixed in parallel task FIX-A) needs to know the true "base" commit that each worktree branched from so its diff axes can score correctly. Today there is NO signal written — judge has to guess via `merge-base` heuristics.

Fix: every time a worktree is created by orchestration code, write a `.dual-base-ref` sidecar file at the worktree root containing the exact commit SHA used as `base`. This gives `judge.py` an unambiguous, never-wrong-base signal.

Two call sites create worktrees in this repo:
- `.claude/scripts/dual-teams-spawn.py` — creates BOTH claude + codex worktrees (via `create_worktree()` helper).
- `.claude/scripts/codex-wave.py` — creates codex-only worktrees (via its own `_create_worktree` or equivalent).

Add identical sidecar-write logic to both: after a successful `git worktree add`, resolve the actual SHA of the `base` arg (`git rev-parse <base>` in the PARENT repo, not in the new worktree) and write it to `<worktree>/.dual-base-ref` as a single-line text file (SHA + newline).

## Scope Fence

**Allowed:**
- `.claude/scripts/dual-teams-spawn.py` (modify)
- `.claude/scripts/codex-wave.py` (modify)
- `.claude/scripts/test_dual_teams_spawn.py` (modify — add tests)
- `.claude/scripts/test_codex_wave.py` (modify — add tests)

**Forbidden:**
- Every other path under `.claude/scripts/`
- `.claude/hooks/*`
- Any `work/*` or `worktrees/*` path

## Test Commands

```bash
py -3 .claude/scripts/test_dual_teams_spawn.py
py -3 .claude/scripts/test_codex_wave.py
py -3 .claude/scripts/dual-teams-spawn.py --help
py -3 .claude/scripts/codex-wave.py --help
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: `dual-teams-spawn.py:create_worktree()` (or wherever the worktree is registered as "successfully created") resolves the effective base commit via `git rev-parse <base>` in the parent repo, then writes it to `<worktree_path>/.dual-base-ref` with a trailing newline. Log at INFO.
- [ ] AC2: `codex-wave.py` — its worktree-creation function does the same: resolve + write `.dual-base-ref`. Log at INFO.
- [ ] AC3: If `git rev-parse` fails (rc != 0 or empty stdout), log WARNING, skip sidecar write, DO NOT fail the worktree creation. Robustness: sidecar is best-effort.
- [ ] AC4: If the sidecar write itself fails (disk full, permission), log WARNING, continue. Same robustness.
- [ ] AC5: Sidecar content format: exactly one line — the resolved SHA, followed by `\n`. No JSON, no yaml, no comments.
- [ ] AC6: Existing tests still pass. New unit tests:
  - (a) `test_create_worktree_writes_sidecar` in `test_dual_teams_spawn.py` — verify `.dual-base-ref` exists after `create_worktree()` call, contains 40-char SHA + newline.
  - (b) `test_create_worktree_sidecar_failure_soft` — mock `subprocess.run` to make `git rev-parse` fail; verify worktree creation still succeeds, no sidecar file, WARNING logged.
  - (c) Mirror (a) and (b) for codex-wave.py's worktree creation.
- [ ] AC7: Every new/modified function has structured logging. No `print()` in library code.
- [ ] AC8: Stdlib only. Windows-compatible.
- [ ] AC9: LOC added ≤ 50 across both .py scripts combined; ≤ 100 across both test files combined.
- [ ] All Test Commands exit 0.

## Constraints

- DO NOT change the worktree creation contract (return type, exceptions, parameter names).
- DO NOT write the sidecar outside the worktree (no accidental repo-root pollution).
- Order matters: sidecar write happens AFTER the worktree is confirmed created, BEFORE any prompt generation / codex spawn.
- For files > 250 lines, use Bash heredoc instead of Write tool — the harness auto-denies big Writes (see teammate-prompt-template.md "Platform Gotchas").
- For any `subprocess.run(["codex", ...])` or similar: resolve via `shutil.which("codex")` first, then pass the resolved absolute path. Bare name fails on Windows (.CMD wrappers).

## Handoff Output

Standard `=== PHASE HANDOFF: FIX-B-dual-base-ref-sidecar ===` with:
- commit sha
- test output
- `ls -la <some_temp_worktree>/.dual-base-ref` + `cat` of its content to prove it lands correctly.
