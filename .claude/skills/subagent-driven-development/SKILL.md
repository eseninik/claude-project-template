---
name: subagent-driven-development
description: |
  Executes implementation plans by dispatching a fresh subagent per task with code review after each.
  Supports wave parallelization (3+ independent tasks run simultaneously) and Worktree Mode
  for tasks modifying the same files. Includes post-execution validation and smoke tests.
  Activate when executing a plan with independent tasks in the current session.
  Does NOT apply when plan needs revision (brainstorm first) or tasks are strictly sequential.
---

# Subagent-Driven Development

Execute plans by dispatching fresh subagent per task, with code review after each.

**Core principle:** Fresh subagent per task + review between tasks = high quality, fast iteration.

## When to Use

- Staying in current session (vs executing-plans for parallel sessions)
- Tasks are mostly independent
- Want continuous progress with quality gates

## Wave Parallelization (auto)

Activates when 3+ tasks have `depends_on: []`.

### Decision algorithm (MANDATORY)

```
3+ tasks with depends_on: []?
  NO  -> sequential execution
  YES -> check files_modified overlap
    NO overlap  -> standard parallel (same worktree)
    OVERLAP     -> Worktree Mode (MANDATORY if platform check passes)
      Platform OK?  -> execute in worktrees
      Platform fail -> sequential fallback
```

**BLOCKING RULE:** If files overlap AND platform check passes, Worktree Mode is MANDATORY.

### Build waves

```
Wave 1: all tasks with depends_on: []
Wave 2: tasks depending on Wave 1
Wave 3: tasks depending on Wave 2
...
```

If two tasks in same wave modify same file: use Worktree Mode (or move one to next wave as fallback).

## Process

### Step 1: Load plan and analyze waves

1. Read plan file (tech-spec.md or tasks/*.md)
2. Extract: task number, depends_on, files_modified for each task
3. Build wave assignment
4. Create TodoWrite with all tasks
5. Announce wave plan to user

### Step 2: Execute wave

**If wave has 3+ tasks:** spawn all subagents in parallel (max 3 concurrent), wait for all, review each.

**If wave has 1-2 tasks:** execute sequentially.

Subagent prompt template:

```
You are implementing Task N from [plan-file].
Read that task carefully. Your job is to:
1. Implement exactly what the task specifies
2. Write tests (following TDD)
3. Verify implementation works
4. Commit your work
5. Report: what implemented, what tested, test results, files changed, issues
```

### Step 3: Review subagent work

Dispatch code-reviewer subagent after each task (or after each wave in parallel mode).

### Step 4: Apply review feedback

Fix Critical issues immediately. Fix Important issues before next task. Note Minor issues.

### Step 5: Mark complete, next task

Mark completed in TodoWrite. Move to next wave. Repeat steps 2-5.

### Step 6: Final review

After all tasks complete, dispatch final code-reviewer for overall implementation.

### Step 7: User acceptance testing (MANDATORY)

1. Load UAT skill
2. Generate scenarios from user-spec.md
3. Present checklist to user
4. Wait for user response
5. Fix issues if found, re-run UAT

### Step 8: Complete development

Use finishing-a-development-branch skill.

## Worktree Mode (files overlap)

Read `references/worktree-mode.md` when tasks in the same wave modify overlapping files.

Summary: create isolated worktrees per task, execute in parallel, merge sequentially with conflict classification, validate actual changed files, run smoke tests.

## Background Task Tracking

Read `references/background-task-tracking.md` for JSON-based progress tracking in `work/background-tasks.json`.

## Example: Sequential mode

```
Wave analysis: 2 tasks -> sequential

Task 1: Hook installation script
  [subagent] -> implemented, 5/5 tests passing
  [code review] -> ready

Task 2: Recovery modes
  [subagent] -> implemented, 8/8 tests passing
  [code review] -> issues found -> fix -> ready

[final review] -> done
```

## Example: Parallel mode

```
Wave analysis:
  Wave 1: [001, 002, 003] (parallel)
  Wave 2: [004] (depends on 001, 002)
  Wave 3: [005] (depends on 004)

Wave 1: 3 subagents simultaneously
  001: user model, 5/5 tests
  002: API endpoints, 8/8 tests
  003: validation, 6/6 tests
  [reviews] -> all ready

Wave 2: task 004 sequential
  [review] -> ready

Wave 3: task 005 sequential
  [review] -> ready

[final review] -> [UAT] -> done
```

## Red Flags

- Never skip code review between tasks or waves
- Never proceed with unfixed Critical issues
- Never run >3 subagents in parallel
- Never claim "files overlap so cannot parallelize" -- use Worktree Mode
- Never skip Worktree Mode when files overlap AND platform check passes
- Never implement without reading the plan task first
- If subagent fails: dispatch fix subagent, do not fix manually (context pollution)

## References

| File | When to Read |
|------|-------------|
| references/worktree-mode.md | Tasks in same wave modify overlapping files |
| references/background-task-tracking.md | Need to track parallel subagent execution progress |

## Required Workflow Skills

- **requesting-code-review**: review after each task
- **user-acceptance-testing**: UAT after final review
- **finishing-a-development-branch**: complete development after UAT
- **test-driven-development**: subagents follow TDD
