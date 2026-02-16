# Autonomous Pipeline Guide

> On-demand guide for executing autonomous development pipelines.
> Loaded via: `cat .claude/guides/autonomous-pipeline.md`

---

## Overview

The autonomous pipeline enables Claude Code to execute complex multi-phase tasks without losing context or focus after compaction. It uses:

1. **PIPELINE.md** -- state machine file with explicit phase markers
2. **Ralph Loop** -- optional fresh-context shell script for long sessions
3. **Agent Teams** -- parallel execution for phases with 3+ independent tasks
4. **Three-layer context** -- contract (CLAUDE.md), working set (PIPELINE.md + STATE.md), noise (historical logs)

---

## When to Use

- Task has 3+ phases or stages
- Task will likely trigger compaction (>60% context window)
- Task needs autonomous execution without user intervention
- User explicitly requests "pipeline" or "autonomous mode"

## When NOT to Use

- Simple bug fix (1-2 files)
- Single-phase task that fits in one context window
- Task requiring constant user feedback between steps

---

## Pipeline Creation

### Step 1: Analyze the Task

Break the task into phases (analysis, implementation, testing, verification).
For each phase: determine mode (SOLO vs AGENT_TEAMS).
Rule: 3+ independent tasks in a phase = AGENT_TEAMS.

### Step 2: Create work/PIPELINE.md

Use template: `.claude/shared/work-templates/PIPELINE.md`

- Fill in phase names, modes, tasks, acceptance criteria
- Set first phase as `<- CURRENT`
- Set Status: `IN_PROGRESS`

### Step 3: Create work/PROMPT.md (Ralph Loop only)

Use template: `.claude/shared/work-templates/PROMPT.md`

- Customize context-loading steps for your project
- Add project-specific verification commands
- Add any special constraints

### Step 4: Execute

**Interactive mode:** Agent reads PIPELINE.md, executes phases sequentially, updates state after each.

**Ralph Loop mode:** User runs `./scripts/ralph.sh` for fully autonomous execution with fresh context per phase.

---

## Phase Execution Protocol

### SOLO Phases

```
1. Read phase tasks and acceptance criteria from PIPELINE.md
2. Implement changes
3. Run tests
4. If tests fail -> fix -> retest (max 3 attempts)
5. If still failing -> mark phase BLOCKED, alert user
6. If passing -> mark phase [x], advance <- CURRENT to next phase
```

### AGENT_TEAMS Phases

```
1. Analyze phase tasks for parallelization potential
2. TeamCreate with appropriate team size (2-5 agents)
3. Build teammate prompts using .claude/guides/teammate-prompt-template.md
4. MANDATORY: each prompt has ## Required Skills section
5. Wait for all agents to complete
6. Verify combined results against acceptance criteria
7. Mark phase [x], advance <- CURRENT to next phase
```

---

## Compaction Recovery

When compaction occurs during interactive mode:

1. System automatically re-loads CLAUDE.md (always in context)
2. CLAUDE.md Summary Instructions remind: "re-read PIPELINE.md"
3. Agent reads `work/PIPELINE.md`, finds `<- CURRENT` marker
4. Agent reads `work/STATE.md` for latest results
5. Agent continues from exactly where it left off
6. Phase mode (SOLO/AGENT_TEAMS) is preserved in PIPELINE.md

**This is why PIPELINE.md is critical** -- it is the agent's external memory that survives compaction. Without it, the agent forgets the plan and drifts.

---

## Ralph Loop Details

The Ralph Loop (`scripts/ralph.sh`) provides compaction-immune execution:

- Each phase runs in a FRESH `claude -p` process (200K clean context)
- State persists through PIPELINE.md + STATE.md + git history
- No compaction possible (each phase completes within one context window)
- Automatic git checkpoints between phases

### Usage

```bash
./scripts/ralph.sh                           # Default: 20 iterations
./scripts/ralph.sh --max-iterations 10       # Custom iteration limit
./scripts/ralph.sh --prompt work/PROMPT.md   # Custom prompt file
```

### How It Works

```
for each iteration:
  1. Read work/PIPELINE.md
  2. If Status = PIPELINE_COMPLETE -> exit success
  3. If Status = BLOCKED -> exit with error
  4. Spawn: claude -p work/PROMPT.md
  5. Agent executes ONE phase (reads PIPELINE.md, finds <- CURRENT)
  6. Agent updates PIPELINE.md, STATE.md, memory
  7. Agent commits checkpoint
  8. Loop back to step 1 with fresh context
```

---

## Verification Protocol

After each phase (MANDATORY):

1. Run project test suite (`uv run pytest` or equivalent)
2. Check acceptance criteria from PIPELINE.md
3. Apply 4-verdict model:
   - **PASS**: All criteria met, proceed to next phase
   - **CONCERNS**: Minor issues documented, proceed
   - **REWORK**: Fix issues, re-verify (max 3 attempts)
   - **FAIL**: Mark phase BLOCKED, stop pipeline, alert user

---

## Memory Updates

After each phase (MANDATORY -- do NOT skip):

1. **PIPELINE.md**: Mark phase done `[x]`, advance `<- CURRENT` marker
2. **work/STATE.md**: Record phase results, current project state
3. **.claude/memory/activeContext.md**:
   - Did: phase results and key changes
   - Decided: architectural or design decisions
   - Learned: gotchas, what worked, what didn't
   - Next: remaining phases and known blockers
4. **Git commit**: Checkpoint with meaningful message

---

## Anti-Drift Patterns

### Todo-List Rewriting

PIPELINE.md serves as the persistent todo list. By reading and updating it each phase, the pipeline state stays in the agent's recent attention span. This prevents drift caused by compaction or context overflow.

### Controlled Variation

If agents loop on the same error 3+ times:
- Try a different debugging angle or test strategy
- Spawn a fresh agent with a different prompt framing
- Mark the phase BLOCKED rather than looping indefinitely

### Keep Wrong Turns

Do not strip errors from context. Failed attempts help the agent avoid repeating the same mistakes. PIPELINE.md Decisions section captures what was tried and why it failed.

---

## Common Pitfalls

| Pitfall | Prevention |
|---------|------------|
| Forgetting Agent Teams after compaction | PIPELINE.md Mode field preserves the decision |
| Phase too large for one context window | Split into sub-phases if >60% context estimate |
| No verification between phases | Always test before advancing `<- CURRENT` |
| Stale PIPELINE.md | Always update BEFORE exiting or committing |
| No git checkpoints | Always commit between phases |
| Agent drifts from plan | Re-read PIPELINE.md at start of every phase |
| Skipping memory update | BLOCKING RULE: no commit without memory update |

---

## Quick Reference

```
CREATE:   PIPELINE.md (from template) + PROMPT.md (Ralph Loop only)
EXECUTE:  Read <- CURRENT -> implement -> test -> update state -> advance marker
RECOVER:  Re-read PIPELINE.md -> find <- CURRENT -> continue
VERIFY:   Tests pass + acceptance criteria met -> 4-verdict model
UPDATE:   PIPELINE.md + STATE.md + activeContext.md + git commit
FINISH:   All phases [x] -> Status: PIPELINE_COMPLETE
```
