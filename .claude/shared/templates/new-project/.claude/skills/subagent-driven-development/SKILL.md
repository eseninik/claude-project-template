---
name: subagent-driven-development
description: |
  Executes plans by dispatching fresh subagent per task with review after each wave.
  Supports wave parallelization (5-10 concurrent) and Worktree Mode for file conflicts.
  Includes QA validation loops after each wave.
  Use when executing a plan with independent tasks.
  Does NOT apply when plan needs revision or tasks are strictly sequential.
---

# Subagent-Driven Development

## Wave Execution

### 1. Analyze
- Read plan (tech-spec.md or tasks/*.md)
- Build waves: Wave 1 = no dependencies, Wave 2 = depends on Wave 1, etc.
- Check file overlap: overlap → Worktree Mode (MANDATORY)
- 5+ agents → Worktree Mode RECOMMENDED even without overlap

### 2. Execute Wave
- 3+ tasks: spawn all subagents in parallel (max 5-10 concurrent)
- 1-2 tasks: execute sequentially
- Each subagent: implement task, write tests, commit, report results

### 3. QA After Wave
- Run qa-validation-loop: reviewer checks all wave output
- Fix CRITICAL/IMPORTANT before next wave

### 4. Next Wave
- Repeat steps 2-3 for each wave
- After all waves: final verification

## Worktree Mode (file overlap or 5+ agents)
1. Create `.worktrees/task-{N}` per task
2. Execute in parallel (isolated branches)
3. Merge back sequentially
4. Resolve conflicts (auto or manual)
5. Clean up worktrees

## Red Flags
- Skipping QA between waves
- Proceeding with unfixed CRITICAL issues
- Not using Worktree Mode when files overlap
- Claiming done without running full test suite

## References
- Worktree details: `references/worktree-mode.md`
- Agent chains for review: `.claude/guides/agent-chains.md`
