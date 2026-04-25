---
executor: dual
risk_class: routine
reasoning: high
speed_profile: balanced
---

# Task Y9: dual-teams-spawn.py — propagate `--result-dir` to codex-wave so result.md lands at project root

## Your Task

**Y9 root cause.** `codex-wave.py` already supports `--result-dir <path>` and propagates it to its child `codex-implement.py` invocations (see `.claude/scripts/codex-wave.py` lines 221, 237–238). However, `dual-teams-spawn.py` launches `codex-wave.py` WITHOUT passing `--result-dir`, so each child's `task-N-result.md` lands in `<worktree>/work/codex-implementations/` (the codex-implement default, relative to the worktree).

The orchestrator session's `codex-delegate-enforcer.py` scans `<project_root>/work/codex-implementations/` for fresh result.md files. With result.md in worktree-local dirs, the enforcer never sees them — the orchestrator can't edit code paths that codex just covered, even though Codex DID produce a clean implementation. Workaround used twice this session: invoke `codex-implement.py` directly with `--result-dir <abs project root>/work/codex-implementations` (bypassing both `codex-wave.py` and `dual-teams-spawn.py`).

**Fix:** add an opt-in `--result-dir <path>` flag to `dual-teams-spawn.py`. When set, propagate it as `--result-dir <abs path>` to the spawned `codex-wave.py`. Default = unset (matches today's behavior — backward compatible, no regression). Most callers (the orchestrator session) should pass `--result-dir <project_root>/work/codex-implementations` so result.md is visible to the enforcer.

The propagation is a literal CLI argument forwarding — no semantic complexity, no new abstraction.

## Scope Fence

**Allowed:**
- `.claude/scripts/dual-teams-spawn.py` (modify — add CLI flag + propagation logic)
- `.claude/scripts/test_dual_teams_spawn.py` (modify — add tests; do NOT remove existing tests)

**Forbidden:**
- `.claude/scripts/codex-wave.py` (already correct — do NOT modify)
- Every other path under `.claude/scripts/` and `.claude/hooks/`
- Any `work/*` or `worktrees/*` path

## Test Commands

```bash
py -3 .claude/scripts/test_dual_teams_spawn.py
py -3 .claude/scripts/dual-teams-spawn.py --help
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: New CLI flag in `dual-teams-spawn.py`: `--result-dir PATH` (optional, default `None`). Type `pathlib.Path`. Help text: "If set, passed through as `--result-dir` to the spawned codex-wave.py so result.md files land at this absolute path. Recommended: `<project_root>/work/codex-implementations` so the orchestrator's codex-delegate-enforcer can find them."
- [ ] AC2: When `--result-dir` is provided, the constructed `codex-wave.py` invocation includes `["--result-dir", str(args.result_dir.resolve())]` in its argv (resolved to absolute). When NOT provided, the codex-wave argv is unchanged from today's behavior (no `--result-dir` flag).
- [ ] AC3: The path passed forward is **always absolute** (use `Path.resolve()` before injecting into argv). This is required because codex-wave's child codex-implement.py runs with `cwd=worktree`, and any relative path would resolve against the worktree, not the project root.
- [ ] AC4: When `--result-dir` is provided, the dual-teams-plan.md report (output of `dual-teams-spawn.py`) includes a line `- result_dir: <absolute path>` in the Codex wave section, near the existing `- pid:` and `- log:` lines, so the operator can see where to look for results.
- [ ] AC5: NEW tests in `test_dual_teams_spawn.py` (≥ 4):
   - (a) Without `--result-dir`, the codex-wave argv constructed by orchestrate() does NOT contain `--result-dir`
   - (b) With `--result-dir <some path>`, codex-wave argv contains `--result-dir <absolute resolved path>`
   - (c) Relative path passed to `--result-dir` is resolved to absolute before being injected
   - (d) The plan report contains the `- result_dir:` line when the flag is set, omitted otherwise
- [ ] AC6: All existing tests in `test_dual_teams_spawn.py` continue to pass (today's tests = 21).
- [ ] AC7: Stdlib only. Windows + POSIX both supported (`pathlib.Path`).
- [ ] AC8: Backward compatible: scripts that already invoke `dual-teams-spawn.py` without `--result-dir` see no behavior change.
- [ ] All Test Commands above exit 0.

## Constraints

- Do NOT modify `codex-wave.py` — it already supports `--result-dir`. Change is purely in `dual-teams-spawn.py` and its tests.
- Do NOT change the default of `dual-teams-spawn.py` to require `--result-dir` — that would break callers and CI.
- Use `args.result_dir.resolve()` not `os.path.abspath()` — `pathlib` is the project convention.
- The `if/else` to add the optional CLI argv pair is the simplest possible idiom; do NOT introduce config classes / enums for a single flag.
- Tests must be self-contained and not depend on a real codex-wave run — test the argv-construction path only, verify the constructed list contains the right tokens (use `unittest.mock.patch` on `subprocess.Popen` if your tests already use that pattern; otherwise factor the argv builder into a helper that tests can call directly).

## Handoff Output

Standard `=== PHASE HANDOFF: Y9-spawn-resultdir ===` with:
- Diff stats (lines added in spawn script + tests)
- Output of `py -3 .claude/scripts/test_dual_teams_spawn.py` showing all tests pass (count of OK)
- A one-line example invocation: `py -3 .claude/scripts/dual-teams-spawn.py --tasks ... --feature ... --result-dir "$PWD/work/codex-implementations"`
