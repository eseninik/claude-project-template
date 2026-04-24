# Dual-Implement Level 3 Live Run — Post-Mortem

**Date:** 2026-04-24
**Task:** `task-dual-1.md` — add `--json` flag to `.claude/scripts/list_codex_scripts.py`
**Executor:** dual (Claude teammate in worktree A + GPT-5.5 via codex-implement.py in worktree B)
**Outcome:** Claude wins (by default). Codex's code lost to false-positive scope violation + rollback.

## Timeline

1. **Spec committed** (`4502d9a`) — task-dual-1.md with `executor: dual`.
2. **Two worktrees created**: `worktrees/dual/claude` (branch `claude/task-dual-1`), `worktrees/dual/codex` (branch `codex/task-dual-1`).
3. **Parallel launch**:
   - Claude teammate spawned via Agent tool (background).
   - codex-implement.py spawned (background bash) with `--worktree worktrees/dual/codex`.
4. **Claude finished** (~2 min): commit `0d909cf`, all 3 tests PASS, handoff PASS.
5. **Codex finished** (~8 min): codex_returncode=0, 4 NOTEs of correct implementation, 4 BLOCKERs from broken test environment. scope-check then fired FALSE POSITIVE (42 bogus allowed entries parsed from the fence). Rollback wiped the worktree's tracked changes AND the untracked `work/codex-implementations/` directory. **Codex's diff was lost** (write_result_file deliberately voids `diff_text = ""` on scope-violation).
6. **Judge**: with Codex's code absent, winner declared by default: Claude.
7. **Merged** `claude/task-dual-1` → `fix/watchdog-dushnost`. `--json` flag works end-to-end.

## Claude side (winner)

- 98 lines total (under the 120-line cap from the spec)
- Commit message: "dual-1/claude: add --json flag to list_codex_scripts.py"
- All three Test Commands pass locally
- AC6 drift check passed structurally (single `scripts` collection, gated presentation)
- Handoff noted friction: Edit/Write tools were permission-denied inside the worktree, fell back to bash heredoc

## Codex side (lost)

Per self-report lines in the result.md, Codex DID implement correctly:
- Added stdlib argparse/json
- Updated module docstring
- Shared a single `scripts` collection between plain and JSON modes (same architectural pattern Claude independently chose)
- JSON used `json.dumps(..., indent=2)` with required key order
- Preserved structured logger calls in main()

Two layers blocked verification:
- **Test env blocker**: Codex's sandboxed shell could not resolve `py -3` (Windows Python launcher not in sandbox PATH). All four Test Commands exited 112 with `No installed Python found!`. This is a **sandbox interaction gap** — tests in task-N.md invoke tools the sandbox does not expose.
- **Scope check false positive**: scope-check parsed the fence spec `.claude/scripts/list_codex_scripts.py` as a **file path**, read the file's 58 lines as 42 "allowed entries" (plus forbidden=0). Path matching then failed ("outside all allowed entries"). Rollback fired.

## Findings — new bugs surfaced by this PoC

### CRITICAL — Bug #7 in `codex-scope-check.py`: fence-spec file-vs-inline ambiguity

`--fence <spec>` checks `Path(spec).is_file()`. If the spec is a single path AND that path exists on disk (e.g., the target file you want to allow), the parser reads the TARGET file as a "fence file" and treats every line as an allowed entry. Catastrophically wrong in exactly the common case "fence is one file".

**Fix**: require explicit mode flags: `--fence-inline <csv>` vs `--fence-file <path>`. Or: default to inline, only read as file when preceded by `@` (like curl convention). Whatever — the silent `is_file()` probe is unsafe.

### CRITICAL — Bug #8 in `codex-implement.py`: result.md voids diff on scope-violation

Line ~1010 of codex-implement.py: `diff_text = ""  # rollback voids diff`. Reasoning was "diff is poisoned after rollback". But on FALSE POSITIVE scope-check (like Bug #7), this destroys real, correct, reviewable work. The diff is **the single most important diagnostic** — it must survive.

**Fix**: always preserve the diff in the result file. Add a separate `- rollback_applied: true/false` field for clarity. Let the human decide whether to use the diff.

### IMPORTANT — Bug #9 in `codex-implement.py` rollback: `git clean -fd` still destroys untracked

The earlier Bug #3 fix added a preflight clean-tree check, making rollback safe for PRE-EXISTING untracked files. But rollback still `git clean -fd` the worktree after Codex runs, destroying files Codex created PLUS files `codex-implement.py` itself created (e.g., `work/codex-implementations/task-X.diff`). When the rollback decision is a false positive, valuable diagnostic artifacts are destroyed.

**Fix**: replace `git clean -fd` with `git clean -fd -x -e work/codex-implementations/` (preserve diagnostic directory), OR move diagnostics outside the worktree before cleaning.

### IMPORTANT — Finding #10: Codex sandbox missing `py -3`

Codex's sandbox on Windows does not expose the `py -3` Python launcher. Test Commands in task-N.md that invoke `py -3` fail with `No installed Python found!` exit 112.

**Fix options**:
- Use `python` in Test Commands (if it resolves in Codex sandbox)
- Provide a small sandbox-init script that adds the Python launcher to PATH
- Document in task-codex-template.md: "prefer `python`/`python3` over `py -3` for tests"

### IMPORTANT — Finding #11: task_id stem derivation drops trailing number

`task-dual-1.md` was derived as `task_id = "dual"` (not `"dual-1"`). Result file became `task-dual-result.md` not `task-dual-1-result.md`. Confusing when multiple dual-N tasks exist.

**Fix**: task_id derivation should keep the full stem after `task-` prefix (e.g., `dual-1`, not `dual`).

## What the Level 3 PoC DID validate

- Two worktrees can be created and held in parallel on branches derived from a single base commit.
- Claude teammate (via Agent tool with targeted cwd) and codex-implement.py (with `--worktree <path>`) run concurrently without interfering with each other.
- Both report via structured handoff/result artifacts.
- Opus (1M context) can read both plus the full spec plus relevant code + history and judge. When one side has code lost, fall-back is "declare the surviving side winner".
- Merging winner branch via `git merge --no-ff` works cleanly; the loser branch can be deleted and worktrees pruned.
- Parallelism is real — total wall time ≈ max(claude_time, codex_time), not their sum. In this run ~8 min (Codex was slower).

## What Level 3 DID NOT validate

- The judge comparing TWO valid diffs and picking a winner on merit. We only saw a default-winner scenario because Codex's diff was destroyed. That comparison step remains theoretical until next successful dual run.

## Implications for the architecture

1. **Bugs #7 + #8** must be fixed before dual-implement can be trusted in real work.
2. **Finding #10** means task-codex-template.md should specify `python` (with fallback) in Test Commands, or we need a sandbox PATH fix.
3. **Finding #11** is cosmetic but bite-y; easy fix.
4. Reinforces that **Opus-as-memory-keeper** pays off. If we had relied on Codex session state, all this would be even harder to reason about. As-is, everything Codex "thought" is captured in the one self-report file — small blast radius, auditable.

## Recommended next actions (in order)

1. Fix Bug #7 (fence ambiguity) — ~10 lines in codex-scope-check.py.
2. Fix Bug #8 (always preserve diff) — ~5 lines in codex-implement.py write_result_file path.
3. Fix Bug #9 (scoped clean) — ~3 lines in rollback_worktree.
4. Fix Finding #11 (task_id derivation) — ~2 lines.
5. Re-run task-dual-2 with the same spec — this time both sides should complete with captured diffs, and the judge step can execute for real.
6. Update knowledge.md with the "Dual-Implement with Windows sandbox" and "Codex stateless → Opus as memory keeper" patterns.

## Git state

```
Before dual-implement:       2c06968  POC_SUCCESS_GPT55
Spec committed:              4502d9a  task-dual-1.md spec
Claude's work (merged):      0d909cf  dual-1/claude on claude/task-dual-1 (now merged)
Codex's work (lost):         —       was on codex/task-dual-1 — branch deleted; diff not recoverable from result.md
Merge commit:                current HEAD via --no-ff
```
