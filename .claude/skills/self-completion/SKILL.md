---
name: self-completion
version: 1.0.0
description: |
  Auto-continue through pending todo items until complete.
  Prevents stopping mid-task when there's more work to do.

  AUTOMATIC TRIGGER:
  - TodoWrite has pending items after completing a task
  - Autowork pipeline running

  Do NOT use for: exploratory work, user-guided tasks
---

# Self-Completion Skill

Automatically continue working through pending todo items until all are complete or a limit is reached.

## Overview

When executing a plan with multiple tasks:
1. Complete current task
2. Check for more pending tasks
3. If pending exist → continue automatically
4. Stop when: all done, max iterations, or blocked

This prevents the agent from stopping mid-plan and requiring manual "continue" commands.

## Algorithm

```
SELF_COMPLETION:
  iteration_count = 0
  max_iterations = 5

  LOOP:
    # Step 1: Check todo list
    todos = GET_TODOS()
    pending = [t for t in todos if t.status == "pending"]
    in_progress = [t for t in todos if t.status == "in_progress"]

    # Step 2: Check completion
    IF len(pending) == 0 AND len(in_progress) == 0:
      OUTPUT("<done>")
      RETURN { status: "success", completed: iteration_count }

    # Step 3: Check iteration limit
    IF iteration_count >= max_iterations:
      OUTPUT("<max_iterations>")
      RETURN { status: "limit_reached", completed: iteration_count, remaining: len(pending) }

    # Step 4: Get next task
    IF len(in_progress) > 0:
      current = in_progress[0]  # Continue in-progress first
    ELSE:
      current = pending[0]
      MARK_IN_PROGRESS(current)

    # Step 5: Execute task
    result = EXECUTE_TASK(current)

    # Step 6: Handle result
    IF result.success:
      MARK_COMPLETED(current)
      iteration_count += 1
      CONTINUE LOOP  # Go to next task

    IF result.blocked:
      OUTPUT("<blocked>")
      RETURN { status: "blocked", reason: result.reason, task: current }

    IF result.failed:
      MARK_FAILED(current)
      OUTPUT("<error>")
      ASK_USER("Task failed: " + result.error + ". How to proceed?")
      RETURN { status: "error", error: result.error, task: current }
```

## Completion Markers

The skill outputs these markers for orchestrator integration:

| Marker | Meaning | Action |
|--------|---------|--------|
| `<done>` | All items completed | Session complete |
| `<blocked>` | Needs user input | Wait for user |
| `<max_iterations>` | Hit limit (5) | Check with user |
| `<error>` | Unrecoverable error | Report and wait |

### Marker Output Format

```
<done>
All 5 tasks completed successfully.
```

```
<blocked>
Blocked on: "Waiting for API credentials"
Task: "Configure external service"
```

```
<max_iterations>
Completed 5 tasks. 3 remaining.
Continuing would risk context overflow.
Continue? (yes/no)
```

```
<error>
Task "Deploy to production" failed.
Error: Permission denied
Awaiting guidance.
```

## Integration with Subagent-Driven-Development

When used with subagent-driven-development:

```
SUBAGENT_LOOP:
  # Main orchestrator tracks overall progress
  # Each subagent handles one task with fresh context

  FOR wave IN waves:
    # Dispatch subagents for wave
    FOR task IN wave.tasks:
      DISPATCH_SUBAGENT(task)

    # Wait for wave completion
    WAIT_FOR_WAVE()

    # Check if should continue
    IF remaining_waves > 0:
      # Self-completion: continue automatically
      CONTINUE
    ELSE:
      # Done
      OUTPUT("<done>")
```

### Subagent Self-Completion

Each subagent can also use self-completion:

```
SUBAGENT_TASK:
  # Subagent receives single task
  # But task may have sub-steps

  WHILE has_sub_steps():
    step = next_sub_step()
    execute(step)
    mark_complete(step)

  # Task done
  RETURN result
```

## Integration with Autowork Pipeline

Autowork uses self-completion for the execution phase:

```
AUTOWORK_PIPELINE:
  # Phase 1: Intent Classification
  # Phase 2: Spec Generation

  # Phase 3: Execution (uses self-completion)
  execution_result = INVOKE skill: self-completion
    context: subagent-driven-development
    tasks: tech-spec.tasks

  IF execution_result.status == "success":
    # Phase 4: Quality Gates
    INVOKE skill: user-acceptance-testing
    INVOKE skill: verification-before-completion

  ELIF execution_result.status == "limit_reached":
    ASK_USER("Completed {N} tasks. Continue with remaining?")

  ELIF execution_result.status == "blocked":
    HANDLE_BLOCKER(execution_result.reason)
```

## Configuration

### Max Iterations

Default: 5 tasks per self-completion cycle

Rationale:
- Prevents infinite loops
- Manages context usage
- Provides natural checkpoints

Can be overridden:
```
INVOKE skill: self-completion
  max_iterations: 10
```

### Blocking Conditions

Stop self-completion when:

1. **User input required**
   - Question needs answering
   - Decision point reached
   - Ambiguous requirement

2. **External dependency**
   - Waiting for API
   - Waiting for build
   - Waiting for deployment

3. **Error occurred**
   - Test failure (needs investigation)
   - Permission denied
   - Resource unavailable

4. **Quality gate**
   - Code review rejected
   - UAT failed
   - Verification failed

## Error Handling

### Task Execution Fails

```
IF task.execute() fails:
  # Don't automatically retry
  # Mark as failed and report
  MARK_FAILED(task)

  # Ask user how to proceed
  options = [
    "Retry this task",
    "Skip and continue",
    "Stop and investigate"
  ]

  ASK_USER(options)
```

### Context Getting Full

```
IF estimated_context > 50%:
  # Warn but continue if under limit
  LOG("Context at 50%, continuing cautiously")

IF estimated_context > 70%:
  # Stop self-completion
  OUTPUT("<context_warning>")
  SUGGEST("Use subagent for remaining tasks")
```

## Example Flow

```
[Starting with 5 todos]

Agent: Starting self-completion cycle.

[Iteration 1]
Agent: Task 1: Create user model
*executes task*
Agent: Task 1 complete. ✓

[Iteration 2]
Agent: Task 2: Create API endpoints
*executes task*
Agent: Task 2 complete. ✓

[Iteration 3]
Agent: Task 3: Add validation
*executes task*
Agent: Task 3 complete. ✓

[Iteration 4]
Agent: Task 4: Integration tests
*executes task*
Agent: Task 4 complete. ✓

[Iteration 5]
Agent: Task 5: E2E tests
*executes task*
Agent: Task 5 complete. ✓

Agent: <done>
All 5 tasks completed successfully.
```

### With Blocking

```
[Iteration 3]
Agent: Task 3: Configure Stripe
*attempts task*
Agent: Need Stripe API key to proceed.

Agent: <blocked>
Blocked on: "Stripe API key required"

Provide API key or skip this task?
```

## Output Format

```json
{
  "skill": "self-completion",
  "status": "success",
  "iterations_completed": 5,
  "iterations_max": 5,
  "tasks_completed": [
    "Create user model",
    "Create API endpoints",
    "Add validation",
    "Integration tests",
    "E2E tests"
  ],
  "tasks_remaining": [],
  "blocked_on": null,
  "errors": []
}
```

## Best Practices

1. **Clear todo items** - Each todo should be atomic and completable
2. **Set realistic limits** - 5 iterations is good default
3. **Handle blockers gracefully** - Don't spin on blocked tasks
4. **Monitor context** - Stop if context getting full
5. **Report progress** - User should see what's happening
