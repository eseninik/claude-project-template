---
executor: dual
risk_class: routine
reasoning: high
speed_profile: balanced
---

# Task FIX-SELFTEST: `.claude/scripts/dual-teams-selftest.py` — end-to-end self-test for the dual-implement infrastructure

## Your Task

Stand-alone, **stdlib-only**, **no live Codex required** self-test that exercises every fixed surface of the dual-implement infrastructure end-to-end. Goal: detect any future regression of Y6 (writer-half blocking), Y7 (preflight × sidecar collision), or sidecar-aware judging in **under 30 s**, without consuming Codex tokens or relying on external services.

The script SHALL:

1. Build a transient git repo in a `tempfile.TemporaryDirectory()`, with a base commit that contains a `.gitignore` that ignores `.dual-base-ref` (mirroring the project's real rule).
2. Create a fake "claude" and "codex" worktree pair (via `git worktree add`).
3. Write a `.dual-base-ref` into each worktree.
4. Verify Y7 fix: `git status --porcelain` returns empty in each worktree → simulating a successful `preflight_worktree` (call the real function from `codex-implement.py` if importable; otherwise compute the equivalent check directly).
5. Verify Y6 fix: import `is_dual_teams_worktree` from `codex-delegate-enforcer.py` (loaded via `importlib`) and assert `True` on each worktree path.
6. Verify "previously-broken" judge axes by:
   - Adding a tiny .py file to claude side via `git commit` (simulates committed work)
   - Adding a tiny .py file to codex side WITHOUT committing (simulates untracked work)
   - Calling `judge_axes._collect_modified_py_files` (or equivalent) and asserting both worktrees report the new file.
7. Print a single one-line summary: `selftest: <N> checks, <K> passed, <M> failed (<duration_ms> ms)`.
8. Exit 0 iff every check passes; exit 1 otherwise. Emits a structured-log JSON line per check (entry/exit/error) for CI ingestion.

## Scope Fence

**Allowed:**
- `.claude/scripts/dual-teams-selftest.py` (new)
- `.claude/scripts/test_dual_teams_selftest.py` (new)

**Forbidden:**
- Every other path under `.claude/scripts/` and `.claude/hooks/`
- Any `work/*` or `worktrees/*` path

## Test Commands

```bash
py -3 .claude/scripts/test_dual_teams_selftest.py
py -3 .claude/scripts/dual-teams-selftest.py --help
py -3 .claude/scripts/dual-teams-selftest.py
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: CLI: `dual-teams-selftest.py [--json] [--verbose] [--keep-tmpdir]`. `--json` emits machine-readable per-check report.
- [ ] AC2: Total wall time on Windows < 30 s on a quiet machine. No external network. No live `codex` invocation (assert `subprocess.run` is never invoked with the codex CLI; if it must invoke `git`, that is fine).
- [ ] AC3: Each check is a separately reportable item. Default human-readable output:
  ```
  [PASS] preflight-clean-with-sentinel-V1                 (12 ms)
  [PASS] preflight-clean-with-sentinel-V2                 (10 ms)
  [PASS] is_dual_teams_worktree-true-on-V1                ( 6 ms)
  [PASS] is_dual_teams_worktree-true-on-V2                ( 5 ms)
  [PASS] judge-axes-sees-claude-committed-py              (38 ms)
  [PASS] judge-axes-sees-codex-untracked-py               (40 ms)
  selftest: 6 checks, 6 passed, 0 failed (143 ms)
  ```
- [ ] AC4: `--json` output schema: `{"started_at","duration_ms","summary":{"checks":N,"passed":K,"failed":M},"results":[{"name","status","detail","duration_ms"}]}`. Strict — `failed` must be 0 to exit 0.
- [ ] AC5: Internal integration: imports `is_dual_teams_worktree` from `.claude/hooks/codex-delegate-enforcer.py` via `importlib.util.spec_from_file_location`. If that module cannot be imported (e.g. enforcer file deleted), reports `[FAIL] enforcer-load`.
- [ ] AC6: Internal integration: imports `preflight_worktree` (or `check_tree_clean`) from `.claude/scripts/codex-implement.py` similarly. If unavailable, reports `[FAIL] preflight-load`.
- [ ] AC7: Internal integration: imports the relevant judge helper from `.claude/scripts/judge_axes.py`. Same fallback pattern.
- [ ] AC8: `--keep-tmpdir` skips the cleanup so a developer can post-mortem. Default cleans up.
- [ ] AC9: Test commands above all exit 0.
- [ ] AC10: Unit tests in `test_dual_teams_selftest.py` (≥ 6): (a) every check passes when fixes are in place, (b) selftest reports FAIL when sentinel is missing, (c) selftest reports FAIL when preflight is monkey-patched to reject, (d) `--json` schema round-trip, (e) duration field is positive integer ms, (f) `--keep-tmpdir` actually keeps the dir.
- [ ] AC11: When run in CI/quiet test mode, exit code is the only non-zero failure signal; the table goes to stdout, structured logs to stderr, no other side effects.

## Constraints

- Stdlib only. Use `tempfile`, `subprocess`, `pathlib`, `importlib`, `dataclasses`, `time`, `json`, `argparse`, `logging`.
- Cross-platform. Use `Path` not `os.path`. Be explicit about `os.sep`.
- The script must be **idempotent** and **safe to run while other dual-implement runs are in flight** — its tempdir is fully isolated. Do NOT touch real `worktrees/` or real `work/codex-implementations/`.
- Logging: structured JSON via stdlib `logging.Logger`, one logger per module. Entry/exit/error logs every function. No bare prints except final summary.
- If your file will exceed ~250 lines including logging, USE Bash heredoc (`cat > <path> <<'END_MARK'`) instead of Write — harness silently denies large Writes.
- Set up the transient repo's git config: `user.email selftest@local`, `user.name selftest`, `init.defaultBranch main` — to match the project convention and avoid CI environment leaks.

## Handoff Output

Standard `=== PHASE HANDOFF: FIX-SELFTEST ===` with:
- `py -3 .claude/scripts/test_dual_teams_selftest.py` test count + OK
- `py -3 .claude/scripts/dual-teams-selftest.py` actual run output (the table)
- One-line note: "Y6/Y7 regression detector lands in `.claude/scripts/dual-teams-selftest.py`."
