You are executing one phase of an autonomous pipeline. Follow these steps exactly.

## 1. Load Context

Read these files NOW (in parallel):
- work/PIPELINE.md — find the phase marked `<- CURRENT`
- work/STATE.md — last execution results
- .claude/memory/activeContext.md — cross-session context

## 2. Identify Current Phase

From PIPELINE.md, extract:
- Phase name and number
- Mode: SOLO or AGENT_TEAMS
- Tasks and acceptance criteria
- Gate conditions (On PASS / On FAIL / On REWORK)
- Attempts count vs Max Attempts

## 3. Execute Phase

**If Mode = AGENT_TEAMS → MUST use TeamCreate tool. Do NOT use Task tool for parallelism.**
- Build teammate prompts using .claude/guides/teammate-prompt-template.md
- Each prompt MUST have `## Required Skills` section
- Wait for all teammates to complete, verify their output

**If Mode = SOLO → execute tasks directly.**

## 4. Quality Gate

Run the gate checks defined in the phase (tests, lint, health check, etc.).
Apply 4-verdict model:
- PASS → advance to On PASS target phase
- CONCERNS → document concerns, advance anyway
- REWORK → increment Attempts, return to phase (or BLOCKED if max reached)
- FAIL → mark Status: BLOCKED, stop

## 5. Update State

1. Update work/PIPELINE.md: mark phase `[x]`, move `<- CURRENT` to next phase
2. Update work/STATE.md with results
3. Update .claude/memory/activeContext.md (Did/Decided/Learned/Next)
4. If pipeline is done: set `Status: PIPELINE_COMPLETE` in PIPELINE.md

## 6. Commit

Stage all changes and commit: `pipeline: {phase name} complete`
