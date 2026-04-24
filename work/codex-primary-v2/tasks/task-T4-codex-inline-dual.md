---
executor: dual
risk_class: routine
speed_profile: balanced
---

# Task T4: `.claude/scripts/codex-inline-dual.py` — micro-task dual helper

## Your Task

Create a CLI helper that generates a **transient task-N.md spec** from command-line args (`--describe`, `--scope`, `--test`), then runs BOTH Claude-side and Codex-side in parallel on a tiny scoped change, producing paired results for judging.

Unlike `dual-teams-spawn.py` (for big N-subtask phases), this one is for SINGLE micro-task dual execution (1 spec → 2 parallel diffs) without requiring the caller to write a full task-N.md manually.

## Scope Fence

**Allowed paths:**
- `.claude/scripts/codex-inline-dual.py` (new)
- `.claude/scripts/test_codex_inline_dual.py` (new — unit tests)

**Forbidden:**
- `.claude/scripts/codex-implement.py`, `codex-wave.py`, `spawn-agent.py` — read-only references
- All other paths

## Test Commands

```bash
python .claude/scripts/test_codex_inline_dual.py
python .claude/scripts/codex-inline-dual.py --help
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: CLI `codex-inline-dual.py --describe "<what>" --scope <path>[,<path>...] --test "<bash cmd>" [--test "<cmd2>"...] [--task-id <name>] [--speed <fast|balanced|thorough>]`
- [ ] AC2: Generates a transient `task-N.md` spec at `work/codex-implementations/inline/task-<id>.md` with:
  - frontmatter: `executor: dual`, `speed_profile: <--speed>`, `risk_class: routine`
  - `## Your Task` ← from `--describe`
  - `## Scope Fence` ← `--scope` entries as Allowed paths
  - `## Test Commands` ← each `--test` as a shell line
  - `## Acceptance Criteria (IMMUTABLE)` ← auto-generated from scope + tests (each Test Command exits 0; scope files modified; basic hygiene)
- [ ] AC3: Creates two worktrees: `worktrees/inline/<id>/claude` and `worktrees/inline/<id>/codex`
- [ ] AC4: Writes Claude teammate prompt file to `work/codex-implementations/inline/<id>-claude-prompt.md` (from `spawn-agent.py` template; caller spawns it via Agent tool)
- [ ] AC5: Invokes `codex-implement.py --task <path> --worktree worktrees/inline/<id>/codex --speed <--speed>` as **background** subprocess; records PID + log path
- [ ] AC6: Prints to stdout a clear 3-section block:
  - "CLAUDE TEAMMATE PROMPT" (path to spawn)
  - "CODEX BACKGROUND JOB" (PID + tail log command)
  - "NEXT STEPS" (judge command, merge command, cleanup)
- [ ] AC7: Does NOT block (same as T3: prep + report, Opus drives spawn + judge)
- [ ] AC8: Unit tests (≥ 8):
  - happy path: describe+scope+test → transient spec + 2 worktrees + prompt + codex PID
  - multiple `--test` flags merge into one bash block
  - default `--speed balanced`
  - multiple `--scope` entries comma-separated → all in Scope Fence
  - `--dry-run` prints what would happen, creates nothing
  - missing required arg → argparse exits non-zero
  - generated task file passes T1 (codex-implement.py) section parsing
  - worktree branch names follow `inline/<id>` convention
- [ ] AC9: Structured logging
- [ ] AC10: Under 350 lines + 350 tests
- [ ] All Test Commands exit 0

## Constraints

- Windows-compatible
- Stdlib only
- Transient spec files are committed-tracked (not ignored) to preserve audit trail
- Generated spec must be consumable by existing `codex-implement.py` without modification

## Handoff Output

Standard `=== PHASE HANDOFF: T4-codex-inline-dual ===` block.

## Iteration History
(First round.)
