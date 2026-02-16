# Autonomous Pipeline Execution

You are executing an autonomous development pipeline.

## Step 1: Load Context

1. Read CLAUDE.md for project rules and constraints
2. Read work/PIPELINE.md for current pipeline state
3. Read work/STATE.md for project state
4. Read .claude/memory/activeContext.md for session context

## Step 2: Execute Current Phase

1. Find the phase marked <- CURRENT in PIPELINE.md
2. Check the phase Mode:
   - SOLO: Execute the tasks yourself
   - AGENT_TEAMS: Create a team (TeamCreate) with appropriate roles
3. For AGENT_TEAMS mode:
   - Build teammate prompts using .claude/guides/teammate-prompt-template.md
   - Each teammate MUST have ## Required Skills section
   - Use verification-before-completion for all implementers

## Step 3: Verify

1. Run all relevant tests
2. If tests fail -> fix -> retest (max 3 attempts)
3. If still failing after 3 attempts -> mark phase as BLOCKED in PIPELINE.md

## Step 4: Update State

1. Mark completed phase as [x] in PIPELINE.md
2. Move <- CURRENT marker to next phase
3. Update work/STATE.md with results
4. Update .claude/memory/activeContext.md with:
   - Did: what was accomplished
   - Decided: key decisions made
   - Learned: gotchas discovered
   - Next: what remains

## Step 5: Check Completion

- If all phases [x] -> write "PIPELINE_COMPLETE" at top of PIPELINE.md Status
- If more phases remain -> exit (Ralph Loop will spawn fresh instance)

## Constraints

- NEVER skip tests
- NEVER mark phase done without verification
- ALWAYS use Agent Teams for phases with 3+ independent tasks
- ALWAYS update memory before exiting
