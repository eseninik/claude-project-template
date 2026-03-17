---
name: subagent-driven-development
description: |
  Dispatch fresh subagent per task with code review between tasks. Auto-parallelizes independent tasks into waves (Agent Teams). Handles file conflicts via Worktree Mode (isolated git worktrees with merge).
  Use when executing implementation plans with independent tasks, when you have 3+ tasks that can run in parallel, when tasks modify overlapping files and need isolation, or when user says "TeamCreate" or "Agent Teams".
  Do NOT use for sequential-only plans, single-task execution, when tasks need each other's output in the same file, or when no plan exists yet (use task-decomposition first).
roles: [pipeline-lead, wave-coordinator, ao-hybrid-coordinator]
---

# Subagent-Driven Development

Execute plan by dispatching fresh subagent per task, with code review after each.

## Overview

**Core principle:** Fresh subagent per task + review between tasks = high quality, fast iteration.

- Fresh 200K-token context per subagent (no pollution)
- Auto wave parallelization for 3+ independent tasks
- Worktree Mode for tasks modifying same files
- Code review gate after each task/wave
- Post-execution validation, wave rollback, smoke tests

## Wave Parallelization

### Decision Algorithm (MANDATORY)

```
START: Have 3+ tasks with depends_on: []?
  |
  +- NO -> Execute sequentially (standard flow)
  |
  +- YES -> Check files_modified overlap
           |
           +- Files DON'T overlap -> Standard parallel (same worktree)
           |
           +- Files DO overlap -> MUST use Worktree Mode
                                 |
                                 +- Platform check passes? -> Execute in worktrees
                                 |
                                 +- Platform check fails? -> Sequential (fallback ONLY)
```

**BLOCKING:** If files overlap AND platform check passes, Worktree Mode is MANDATORY.

### Build Waves

1. Read all task files. Extract: task number, depends_on, files_modified
2. Assign waves:
   - `depends_on: []` -> Wave 1
   - `depends_on: [001]` -> Wave after task-001
3. Check file conflicts within waves:
   - If platform check passes -> mark "worktree-isolated", keep in same wave
   - If platform check fails -> move one task to next wave (fallback)

### Execute Waves

```
FOR each wave:
  IF wave has 3+ tasks:
    Spawn ALL subagents in parallel (max 3 concurrent)
    Wait for ALL to complete
    Run code review for each
  ELSE:
    Execute sequentially (standard flow)
  THEN move to next wave
```

After each wave completes, save checkpoint: `work/{feature}/checkpoint.yml`. See `references/checkpoint-recovery.md`.

### Checkpoint Recovery

For long implementation phases, save wave-level checkpoints to survive compaction. See `references/checkpoint-recovery.md` for schema and resume protocol.

## Worktree Mode

Solve the "same file" problem, not avoid it. Tasks modifying overlapping files run in parallel using isolated git worktrees, then merge results.

**DO NOT skip Worktree Mode just because files overlap** -- that is exactly what it is for.

### Lifecycle

1. **Platform check** -- verify compatibility (Windows+Cyrillic, git 2.17+, disk space)
2. **Lock** -- acquire concurrent session lock
3. **Create** -- `git worktree add` per conflicting task
4. **Execute** -- spawn subagents in parallel, each in its own worktree
5. **Validate** -- compare actual vs declared modified files
6. **Merge** -- sequential merge of worktree branches
7. **Smoke test** -- run post-merge tests
8. **Cleanup** -- remove worktrees, branches, lock, state

See `references/worktree-mode.md` for full scripts, conflict classification, state file format, and Windows notes.

### Conflict Classification (Quick Reference)

| Pattern | Classification | Action |
|---------|---------------|--------|
| Different functions (different names) | independent_additions | Keep both |
| Same function modified by both | same_function | STOP -- ask human |
| Identical imports | duplicate_import | Keep one |
| Different imports | independent_additions | Keep both |
| Same config key, different values | same_config | STOP -- ask human |
| Complex/unclear | unknown | STOP -- ask human |

### Wave Rollback

Trigger when: merge requires human intervention, actual file conflict detected, or smoke test fails.

1. Abort current merge
2. Reset to WAVE_START
3. Keep worktrees for investigation
4. Offer user: manual resolution, sequential fallback, or abort

### Post-Merge Smoke Test

Run after all merges complete. Any failure = STOP and ask user. Do not determine if failure is "related" or not.

## The Process

### 1. Load Plan and Analyze Waves

1. Read plan file (tech-spec.md or plan file)
2. Read all task files, extract dependencies and files_modified
3. Build wave assignment
4. Create TodoWrite with all tasks
5. Announce wave plan to user

### 2. Execute Wave

**Parallel (3+ tasks in wave):** Spawn all subagents simultaneously, wait for all, review each.

**Sequential (1-2 tasks):** Dispatch one subagent at a time.

Subagent prompt template:
```
You are implementing Task N from [plan-file].
Read that task carefully. Your job is to:
1. Implement exactly what the task specifies
2. Write tests (following TDD if task says to)
3. Verify implementation works
4. Commit your work
5. Report back

Work from: [directory]
Report: What you implemented, what you tested, test results, files changed, any issues
```

### 3. Review Subagent Work

Dispatch code-reviewer subagent using `requesting-code-review/code-reviewer.md` template.

Inputs: what was implemented, plan requirements, BASE_SHA, HEAD_SHA, task summary.

Returns: Strengths, Issues (Critical/Important/Minor), Assessment.

### 4. Apply Review Feedback

- Fix Critical issues immediately
- Fix Important issues before next task
- Note Minor issues
- Dispatch follow-up subagent if needed

### 5. Mark Complete, Next Task

Mark task completed in TodoWrite. Move to next task. Repeat steps 2-5.

### 6. Final Review

After all tasks complete, dispatch final code-reviewer:
- Review entire implementation
- Check all plan requirements met
- Validate overall architecture

### 7. User Acceptance Testing (MANDATORY)

1. Announce: "Phase change: implementation -> UAT"
2. Load UAT skill: `cat .claude/skills/user-acceptance-testing/SKILL.md`
3. Read user-spec.md from feature folder
4. Generate UAT scenarios, present checklist to user
5. WAIT for user response
6. If issues found: fix and re-run UAT
7. If passed: proceed to step 8

Without UAT confirmation, implementation is NOT complete.

### 8. Complete Development

After UAT passes:
1. Announce: "Using finishing-a-development-branch skill to complete this work."
2. Follow `finishing-a-development-branch` skill to verify tests, present options, execute.

## AO Hybrid Mode

When `execution_engine: ao_hybrid` in config.yaml or phase has `Mode: AO_HYBRID`, use `ao-hybrid-spawn` skill instead of TeamCreate. Each agent gets full Claude Code context.

See `references/ao-hybrid-mode.md` for decision tree and details.

## Background Task Tracking

Track parallel execution in `work/background-tasks.json`. Update entries when dispatching and on completion. Report wave status to user after each wave.

See `references/background-task-tracking.md` for JSON schema, dispatch/completion procedures, and status format.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skip code review between tasks | Review after EACH task or wave -- quality gate is mandatory |
| Proceed with unfixed Critical issues | Fix Critical issues before moving to next task |
| Run parallel tasks on same files WITHOUT Worktree Mode | Use Worktree Mode -- that is what it is for |
| Claim "files overlap so can't parallelize" | Wrong -- use Worktree Mode instead |
| Run more than 3 subagents in parallel | Quality degrades beyond 3 concurrent agents |
| Try to fix subagent failure manually | Dispatch fix subagent with specific instructions (avoids context pollution) |
| Auto-resolve same_function or same_config conflicts | Always ask human for these |
| Skip post-execution file validation | May miss undeclared file changes causing surprise conflicts |
| Skip post-merge smoke test | Merged code may be broken in non-obvious ways |
| Proceed after smoke test failure without user confirmation | Any failure = STOP and ask user |

## Integration

**Required workflow skills:**
- `requesting-code-review` -- review after each task (Step 3)
- `user-acceptance-testing` -- UAT after final review (Step 7)
- `finishing-a-development-branch` -- complete development after UAT (Step 8)

**Subagents use:**
- `test-driven-development` -- TDD for each task

**Alternative:**
- `executing-plans` -- for parallel session instead of same-session execution
