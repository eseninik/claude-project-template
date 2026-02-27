---
name: subagent-driven-development
description: |
  Executes plans by dispatching fresh subagent per task with review after each wave.
  Supports wave parallelization (5-10 concurrent) and Worktree Mode for file conflicts.
  Includes QA validation loops after each wave.
  Use when executing a plan with independent tasks.
  Does NOT apply when plan needs revision or tasks are strictly sequential.
---

## Philosophy
Independent tasks should run in parallel with review gates between waves. Fresh context per agent preserves reasoning quality.

## Critical Constraints
**never:**
- Skip wave review between execution batches
- Launch agents without verification-before-completion skill

**always:**
- Review all agent outputs before starting next wave
- Use worktree isolation when agents modify overlapping files

## Runtime Configuration (Step 0)
Before executing, check `.claude/ops/config.yaml`:
- `pipeline_mode` → if set to `solo`, disable parallelization
- `processing_depth` → affects wave size (quick=larger waves, deep=smaller waves with more review)
- `max_retry_attempts` → maximum wave retries before escalation

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

## AO Hybrid Mode (full-context agents)

When `execution_engine: ao_hybrid` in config.yaml, or pipeline phase has `Mode: AO_HYBRID`:

1. Use `ao-hybrid-spawn` skill instead of TeamCreate
2. Each agent = full Claude Code session (CLAUDE.md, skills, hooks, memory)
3. Agents work in isolated git worktrees created by AO
4. Results collected via file reads + worktree merging

Decision tree:
- Tasks need skills/memory/hooks -> AO Hybrid
- Simple context-light tasks -> TeamCreate (faster, lighter)
- 5+ concurrent agents -> AO Hybrid recommended (better isolation)

Reference: `cat .claude/skills/ao-hybrid-spawn/SKILL.md`

## Red Flags
- Skipping QA between waves
- Proceeding with unfixed CRITICAL issues
- Not using Worktree Mode when files overlap
- Claiming done without running full test suite

## References
- Worktree details: `references/worktree-mode.md`
- Agent chains for review: `.claude/guides/agent-chains.md`
