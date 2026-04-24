---
executor: dual
risk_class: routine
speed_profile: balanced
---

# Task T3: `.claude/scripts/dual-teams-spawn.py` — DUAL_TEAMS orchestration helper

## Your Task

Create a CLI orchestrator that runs the DUAL_TEAMS phase mode end-to-end: take a list of `task-T{i}.md` specs, spawn N Claude teammates (one per task) via `spawn-agent.py` and N Codex sessions via `codex-wave.py` in parallel, wait for all `2N` agents to finish, write a paired-results report ready for `judge.py` consumption.

## Scope Fence

**Allowed paths:**
- `.claude/scripts/dual-teams-spawn.py` (new)
- `.claude/scripts/test_dual_teams_spawn.py` (new — unit tests)

**Forbidden:**
- `.claude/scripts/codex-wave.py`, `codex-implement.py`, `spawn-agent.py` — read-only references
- `.claude/settings.json`
- Any other path

## Test Commands

```bash
python .claude/scripts/test_dual_teams_spawn.py
python .claude/scripts/dual-teams-spawn.py --help
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: CLI `dual-teams-spawn.py --tasks T1.md,T2.md,...,TN.md [--parallel N] [--feature NAME] [--worktree-base PATH]`
- [ ] AC2: For each T{i}.md, creates two worktrees:
  - `<worktree-base>/claude/T{i}` on branch `claude/dual-teams/T{i}`
  - `<worktree-base>/codex/T{i}` on branch `codex/dual-teams/T{i}`
- [ ] AC3: Generates Claude teammate prompts via `spawn-agent.py` for each T{i} (output to `work/<feature>/prompts/T{i}-claude.md`). The caller (Opus) is responsible for spawning the Agent tool using those prompts; this script just WRITES prompt files and prints the launch-commands block for the caller to copy.
- [ ] AC4: Launches Codex side via `codex-wave.py --tasks T1,...,TN --parallel <N> --worktree-base <codex-worktrees>` as background process; captures its PID + output file.
- [ ] AC5: Writes an orchestration report `work/<feature>/dual-teams-plan.md` containing:
  - feature name + timestamp
  - per-task: task file, claude worktree, codex worktree, Claude prompt file, Codex wave command reference
  - instructions for Opus: how to spawn the N Claude agents (paste block), how to wait on Codex wave (bash monitor command), where to find paired results after
- [ ] AC6: Does NOT itself spawn the Agent tool (can't — that's Claude Code harness territory). Does NOT block waiting. It's a **prep + report** helper — it sets up parallel infrastructure and tells Opus what to do next.
- [ ] AC7: Structured logging per AGENTS.md (entry/exit/error for every function, log file in `.claude/logs/`)
- [ ] AC8: Unit tests (≥ 8):
  - happy path with 2 tasks → 4 worktrees created, 2 prompt files, 1 codex-wave PID
  - `--parallel` default = number of tasks
  - duplicate worktree path → graceful error, no partial state
  - missing task file → clean error, exit non-zero
  - prompt file paths written as specified
  - worktree branch names follow convention
  - report file schema validated
  - `--dry-run` flag prints plan without creating anything
- [ ] AC9: Under 350 lines (script) + 350 (tests)
- [ ] All Test Commands exit 0

## Constraints

- Windows-compatible (no POSIX-only calls)
- Stdlib only
- Caller is Opus running from main worktree; worktree-base is relative to main repo root
- Must clean up partial worktrees on error (atomic-ish — if one worktree creation fails, roll back the ones already created)

## Handoff Output

Standard `=== PHASE HANDOFF: T3-dual-teams-spawn ===` block.

## Iteration History
(First round.)
