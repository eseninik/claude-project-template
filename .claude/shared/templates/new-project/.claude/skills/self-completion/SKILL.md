---
name: self-completion
description: |
  Auto-continues through pending tasks until all complete or limit reached.
  Prevents stopping mid-task when more work remains.
  Activate when todo list has pending items after completing a task.
  Does NOT apply to exploratory work or user-guided tasks.
---

## Philosophy
Work should continue until all pending tasks are complete. Stopping mid-flow when more work remains wastes the context already built up.

## Critical Constraints
**never:**
- Stop when pending tasks remain in the task list without explicit user instruction
- Mark tasks complete without verification

**always:**
- Check TaskList after completing each task for newly unblocked work
- Prefer tasks in ID order

# Self-Completion

## Rules
1. After completing a task, check TaskList for remaining pending tasks
2. If pending tasks exist with no blockers -> claim next task, continue
3. If blocked -> report status, wait for unblock
4. Max 10 consecutive tasks without user check-in
5. After 10 tasks: report progress, ask user to continue or stop

## When to Stop
- All tasks completed
- Blocked by dependency
- 10 tasks done without user input
- Error that requires user decision
