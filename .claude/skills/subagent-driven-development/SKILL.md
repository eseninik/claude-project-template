---
name: subagent-driven-development
version: 2.0.0
description: Use when executing implementation plans with independent tasks in the current session - dispatches fresh subagent for each task with code review between tasks, enabling fast iteration with quality gates. Now with AUTO WAVE PARALLELIZATION for 3+ independent tasks.
---

# Subagent-Driven Development

Execute plan by dispatching fresh subagent per task, with code review after each.

**Core principle:** Fresh subagent per task + review between tasks = high quality, fast iteration

**NEW in v2.0:** Auto Wave Parallelization - automatically runs independent tasks in parallel when 3+ tasks have no dependencies.

## Overview

**vs. Executing Plans (parallel session):**
- Same session (no context switch)
- Fresh subagent per task (no context pollution)
- Code review after each task (catch issues early)
- Faster iteration (no human-in-loop between tasks)
- **NEW:** Auto parallelization for independent tasks

**When to use:**
- Staying in this session
- Tasks are mostly independent
- Want continuous progress with quality gates

**When NOT to use:**
- Need to review plan first (use executing-plans)
- Tasks are tightly coupled (manual execution better)
- Plan needs revision (brainstorm first)

## Wave Parallelization (AUTO)

### When it activates:
- 3+ tasks in plan
- Tasks have `depends_on` field (or empty = independent)
- Independent tasks don't modify same files

### How it works:

**Step 1: Analyze dependencies**
```
Read all task.md files
For each task:
  - depends_on: [] → Wave 1 (independent)
  - depends_on: [001] → Wave after task-001
  - files_modified: [...] → check for conflicts
```

**Step 2: Build waves**
```
Wave 1: All tasks with depends_on: [] (and no file conflicts)
Wave 2: Tasks depending on Wave 1
Wave 3: Tasks depending on Wave 2
...
```

**Step 3: Check file conflicts**
```
IF two tasks in same wave modify same file:
  → Move one to next wave (avoid merge conflicts)
```

**Step 4: Execute waves**
```
FOR each wave:
  IF wave has 3+ tasks:
    → Spawn ALL subagents in parallel (max 3 concurrent)
    → Wait for ALL to complete
    → Run code review for each
  ELSE:
    → Execute sequentially (standard flow)

  THEN move to next wave
```

### Example:

```
Tasks in plan:
  task-001: depends_on: []           → Wave 1
  task-002: depends_on: []           → Wave 1
  task-003: depends_on: []           → Wave 1
  task-004: depends_on: [001, 002]   → Wave 2
  task-005: depends_on: [004]        → Wave 3

Execution:
  Wave 1: [001, 002, 003] → 3 subagents IN PARALLEL
  (wait for all Wave 1 to complete)
  Wave 2: [004] → 1 subagent (sequential)
  Wave 3: [005] → 1 subagent (sequential)

Result: 3 tasks execute simultaneously instead of 5 sequential
```

### Why quality doesn't drop:
- Each subagent gets FRESH 200K tokens (no shared context)
- Tasks are INDEPENDENT (no conflicts)
- Code review after EACH wave (quality gate)
- File conflicts detected BEFORE execution

## The Process

### 1. Load Plan & Analyze Waves

**Step 1.1:** Read plan file (tech-spec.md or plan file)

**Step 1.2:** Read all task files and extract:
```
For each task.md:
  - task number
  - depends_on (default: [] if not specified)
  - files_modified (default: [] if not specified)
```

**Step 1.3:** Build wave assignment:
```
wave_map = {}
for task in tasks:
  if task.depends_on is empty:
    wave_map[task] = 1
  else:
    max_dependency_wave = max(wave_map[dep] for dep in task.depends_on)
    wave_map[task] = max_dependency_wave + 1

# Check file conflicts within waves
for wave in waves:
  files_in_wave = collect all files_modified from tasks in wave
  if any file appears twice:
    move later task to next wave
```

**Step 1.4:** Create TodoWrite with all tasks

**Step 1.5:** Announce wave plan to user:
```
"Wave analysis complete:
  Wave 1: [task-001, task-002, task-003] (parallel)
  Wave 2: [task-004] (depends on Wave 1)
  Wave 3: [task-005] (depends on Wave 2)

Starting execution..."
```

### 2. Execute Wave (or Task)

**IF current wave has 3+ tasks:**

Spawn ALL subagents in parallel:
```
Task tool (general-purpose) x3:
  description: "Implement Task N: [task name]"
  prompt: |
    You are implementing Task N from [plan-file].
    ... (same as before)
```

Wait for ALL subagents to complete.
Run code review for each completed task.
Move to next wave.

**ELSE (wave has 1-2 tasks):**

Execute sequentially (standard flow below).

### 2-alt. Execute Single Task with Subagent (sequential mode)

For each task in wave (when wave has <3 tasks):

**Dispatch fresh subagent:**
```
Task tool (general-purpose):
  description: "Implement Task N: [task name]"
  prompt: |
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

**Subagent reports back** with summary of work.

### 3. Review Subagent's Work

**Dispatch code-reviewer subagent:**
```
Task tool (superpowers:code-reviewer):
  Use template at requesting-code-review/code-reviewer.md

  WHAT_WAS_IMPLEMENTED: [from subagent's report]
  PLAN_OR_REQUIREMENTS: Task N from [plan-file]
  BASE_SHA: [commit before task]
  HEAD_SHA: [current commit]
  DESCRIPTION: [task summary]
```

**Code reviewer returns:** Strengths, Issues (Critical/Important/Minor), Assessment

### 4. Apply Review Feedback

**If issues found:**
- Fix Critical issues immediately
- Fix Important issues before next task
- Note Minor issues

**Dispatch follow-up subagent if needed:**
```
"Fix issues from code review: [list issues]"
```

### 5. Mark Complete, Next Task

- Mark task as completed in TodoWrite
- Move to next task
- Repeat steps 2-5

### 6. Final Review

After all tasks complete, dispatch final code-reviewer:
- Reviews entire implementation
- Checks all plan requirements met
- Validates overall architecture

### 7. User Acceptance Testing (MANDATORY)

**After final code review passes, BEFORE completion:**

```
1. Announce: "Phase change: implementation -> UAT"
2. Load UAT skill: cat .claude/skills/user-acceptance-testing/SKILL.md
3. Read user-spec.md from feature folder
4. Generate UAT scenarios from user-spec
5. Present checklist to user for testing
6. WAIT for user response
7. If issues found:
   - Fix issues (dispatch subagent if needed)
   - Re-run UAT for fixed items
8. If passed: Proceed to Step 8
```

**Without UAT confirmation from user, implementation is NOT complete.**

### 8. Complete Development

After UAT passes:
- Announce: "I'm using the finishing-a-development-branch skill to complete this work."
- **REQUIRED SUB-SKILL:** Use superpowers:finishing-a-development-branch
- Follow that skill to verify tests, present options, execute choice

## Example Workflow

### Sequential Mode (< 3 independent tasks)

```
You: I'm using Subagent-Driven Development to execute this plan.

[Load plan, analyze waves]
Wave analysis: Wave 1 has 2 tasks → sequential mode

Task 1: Hook installation script
[Dispatch implementation subagent]
Subagent: Implemented install-hook with tests, 5/5 passing
[Code review] → Ready

Task 2: Recovery modes
[Dispatch implementation subagent]
Subagent: Added verify/repair, 8/8 tests passing
[Code review] → Issues found → Fix → Ready

[Final review]
Done!
```

### Parallel Mode (3+ independent tasks)

```
You: I'm using Subagent-Driven Development to execute this plan.

[Load plan, analyze waves]
Wave analysis complete:
  Wave 1: [task-001, task-002, task-003] (parallel - 3 independent)
  Wave 2: [task-004] (depends on 001, 002)
  Wave 3: [task-005] (depends on 004)

Starting Wave 1 (PARALLEL)...

[Spawn 3 subagents simultaneously]
  Subagent 1: Implementing task-001...
  Subagent 2: Implementing task-002...
  Subagent 3: Implementing task-003...

[All complete]
  Subagent 1: Done - user model created, 5/5 tests
  Subagent 2: Done - API endpoints, 8/8 tests
  Subagent 3: Done - validation layer, 6/6 tests

[Code review for each]
  Review 001: Ready
  Review 002: Ready
  Review 003: Minor issue → Fix → Ready

Wave 1 complete. Starting Wave 2...

[Task 004 - sequential]
Subagent: Integration layer complete
[Review] → Ready

Wave 2 complete. Starting Wave 3...

[Task 005 - sequential]
Subagent: E2E tests complete
[Review] → Ready

[Final review]
All 5 tasks complete.

Phase change: implementation -> UAT
[Load UAT skill]
[Generate scenarios from user-spec.md]

UAT Checklist:
1. [ ] Create new user with valid data → user appears in DB
2. [ ] API returns user list → correct format
3. [ ] Invalid email rejected → validation error shown

User: "All scenarios passed!"

UAT passed. Ready to complete.
```

## Advantages

**vs. Manual execution:**
- Subagents follow TDD naturally
- Fresh context per task (no confusion)
- Parallel-safe (subagents don't interfere)

**vs. Executing Plans:**
- Same session (no handoff)
- Continuous progress (no waiting)
- Review checkpoints automatic

**Cost:**
- More subagent invocations
- But catches issues early (cheaper than debugging later)

## Red Flags

**Never:**
- Skip code review between tasks (or after each wave)
- Proceed with unfixed Critical issues
- Run parallel tasks that modify SAME files (check files_modified!)
- Implement without reading plan task
- Run more than 3 subagents in parallel (quality degrades)

**If subagent fails task:**
- Dispatch fix subagent with specific instructions
- Don't try to fix manually (context pollution)

**If parallel execution has conflicts:**
- Stop all subagents
- Rebuild wave map with stricter file conflict detection
- Restart from last successful wave

## Integration

**Required workflow skills:**
- **requesting-code-review** - REQUIRED: Review after each task (see Step 3)
- **user-acceptance-testing** - REQUIRED: UAT after final review (see Step 7)
- **finishing-a-development-branch** - REQUIRED: Complete development after UAT (see Step 8)

**Subagents must use:**
- **test-driven-development** - Subagents follow TDD for each task

**Alternative workflow:**
- **executing-plans** - Use for parallel session instead of same-session execution

See code-reviewer template: requesting-code-review/code-reviewer.md

## Background Task Tracking

Track parallel subagent execution in `work/background-tasks.json` for visibility and debugging.

### JSON Structure

```json
{
  "version": "1.0",
  "tasks": [
    {
      "id": "task-001-wave1",
      "taskFile": "work/feature/tasks/task-001.md",
      "taskTitle": "Create user model",
      "agent": "code-developer",
      "model": "claude-opus-4-5-20251101",
      "wave": 1,
      "status": "completed",
      "startedAt": "2026-01-19T10:00:00Z",
      "completedAt": "2026-01-19T10:05:30Z",
      "duration": 330,
      "result": "User model created with 5/5 tests passing",
      "error": null
    }
  ],
  "activeWave": 1,
  "lastUpdated": "2026-01-19T10:05:30Z"
}
```

### Task Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (e.g., `task-001-wave1`) |
| `taskFile` | string | Path to task.md file |
| `taskTitle` | string | Human-readable task title |
| `agent` | string | Agent type (`code-developer`, `code-reviewer`) |
| `model` | string | Model used for execution |
| `wave` | number | Wave number (1, 2, 3...) |
| `status` | string | `pending` / `running` / `completed` / `failed` / `cancelled` |
| `startedAt` | string | ISO 8601 timestamp when started |
| `completedAt` | string | ISO 8601 timestamp when completed (null if running) |
| `duration` | number | Duration in seconds (null if not completed) |
| `result` | string | Summary of accomplishment (null if not completed) |
| `error` | string | Error message if failed (null if no error) |

### When Dispatching Tasks

**Before spawning subagent:**

```python
# 1. Read current state
tasks_json = read("work/background-tasks.json")

# 2. Add new task entry
new_task = {
    "id": f"task-{task_num}-wave{wave_num}",
    "taskFile": "work/feature/tasks/task-001.md",
    "taskTitle": "Task title from task.md",
    "agent": "code-developer",
    "model": "claude-opus-4-5-20251101",
    "wave": wave_num,
    "status": "running",
    "startedAt": now_iso8601(),
    "completedAt": null,
    "duration": null,
    "result": null,
    "error": null
}

# 3. Update JSON
tasks_json["tasks"].append(new_task)
tasks_json["activeWave"] = wave_num
tasks_json["lastUpdated"] = now_iso8601()

# 4. Write back
write("work/background-tasks.json", tasks_json)

# 5. THEN spawn subagent
```

### On Task Completion

**When subagent returns:**

```python
# 1. Read current state
tasks_json = read("work/background-tasks.json")

# 2. Find and update task
for task in tasks_json["tasks"]:
    if task["id"] == completed_task_id:
        task["status"] = "completed"  # or "failed"
        task["completedAt"] = now_iso8601()
        task["duration"] = calculate_duration(task["startedAt"], task["completedAt"])
        task["result"] = subagent_summary  # what was accomplished
        task["error"] = error_message if failed else null
        break

# 3. Check if wave complete
wave_tasks = [t for t in tasks_json["tasks"] if t["wave"] == current_wave]
if all(t["status"] in ["completed", "failed"] for t in wave_tasks):
    tasks_json["activeWave"] = current_wave + 1  # or null if done

# 4. Update timestamp
tasks_json["lastUpdated"] = now_iso8601()

# 5. Write back
write("work/background-tasks.json", tasks_json)
```

### Checking Wave Status

**Before proceeding to next wave:**

```python
# Read and check wave status
tasks_json = read("work/background-tasks.json")

current_wave = tasks_json["activeWave"]
wave_tasks = [t for t in tasks_json["tasks"] if t["wave"] == current_wave]

# Check all completed
all_done = all(t["status"] in ["completed", "failed"] for t in wave_tasks)
any_failed = any(t["status"] == "failed" for t in wave_tasks)

if not all_done:
    # Still waiting for subagents
    running = [t["taskTitle"] for t in wave_tasks if t["status"] == "running"]
    print(f"Wave {current_wave} still running: {running}")
    return

if any_failed:
    # Handle failures before proceeding
    failed = [t for t in wave_tasks if t["status"] == "failed"]
    for task in failed:
        print(f"FAILED: {task['taskTitle']}")
        print(f"Error: {task['error']}")
    # Decide: fix and retry, or abort
    return

# All passed - proceed to next wave
print(f"Wave {current_wave} complete. Proceeding to Wave {current_wave + 1}")
```

### Status Messages

**Report to user after each wave:**

```
Wave 1 Status (3 tasks):
  [x] task-001: Create user model (330s) - 5/5 tests
  [x] task-002: API endpoints (420s) - 8/8 tests
  [x] task-003: Validation layer (280s) - 6/6 tests

All Wave 1 tasks complete. Proceeding to Wave 2...
```

### Cleanup

**After plan execution completes:**

```python
# Option 1: Archive
mv work/background-tasks.json work/completed/background-tasks-{feature}.json

# Option 2: Reset for next run
reset_json = {
    "version": "1.0",
    "description": "Tracks parallel subagent task execution",
    "tasks": [],
    "activeWave": null,
    "lastUpdated": null
}
write("work/background-tasks.json", reset_json)
```
