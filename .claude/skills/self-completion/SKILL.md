---
name: self-completion
description: |
  Auto-continues through pending tasks until all complete or iteration limit reached. Loops through todo items autonomously without requiring manual "continue" commands.
  Use when there are pending tasks to work through, when user says "keep going", "finish the rest", "don't stop", or "work through remaining items", or during autonomous pipeline execution.
  Do NOT use for creating todo lists, checking task status, exploratory research, or user-guided interactive step-by-step work.
roles: [pipeline-lead, wave-coordinator]
---

# Self-Completion

## Overview

Automatically continue working through pending todo items without requiring manual "continue" commands.
Core principle: after finishing one task, check for more pending work and keep going.

## Algorithm

```
iteration_count = 0
max_iterations = 5

LOOP:
  1. Check todo list
     pending = todos where status == "pending"
     in_progress = todos where status == "in_progress"

  2. Check completion
     IF no pending AND no in_progress:
       OUTPUT <done>
       RETURN success

  3. Check iteration limit
     IF max_iterations != unlimited AND iteration_count >= max_iterations:
       OUTPUT <max_iterations>
       RETURN limit_reached
     IF max_iterations == unlimited:
       // Safety valve checks (defense in depth)
       IF context_pressure() > context_threshold:
         save_state()
         OUTPUT <safety_stop reason="context_pressure">
         RETURN safety_stop
       IF wall_clock_elapsed() > wall_clock_timeout:
         save_state()
         OUTPUT <safety_stop reason="timeout">
         RETURN safety_stop
       IF consecutive_no_change_iterations >= idle_threshold:
         // Idle = no git-diff changes (not self-reported). Trivial edits count as no change.
         save_state()
         OUTPUT <safety_stop reason="idle">
         RETURN safety_stop
       IF same_error_count >= 3:
         save_state()
         OUTPUT <safety_stop reason="progress_stall">
         RETURN safety_stop
       IF iteration_count % checkpoint_interval == 0 AND iteration_count > 0:
         log_checkpoint()  // log progress, re-read task list, assess if continuing makes sense

  4. Get next task
     IF in_progress exists: current = in_progress[0]
     ELSE: current = pending[0], mark in_progress

  5. Execute task

  6. Handle result
     success -> mark completed, increment count, CONTINUE
     blocked -> OUTPUT <blocked>, RETURN blocked
     failed  -> mark failed, OUTPUT <error>, ask user
```

## Completion Markers

| Marker | Meaning | Action |
|--------|---------|--------|
| `<done>` | All items completed | Session complete |
| `<blocked>` | Needs user input | Wait for user |
| `<max_iterations>` | Hit limit (5) | Check with user |
| `<error>` | Unrecoverable error | Report and wait |
| `<context_warning>` | Context > 70% full | Suggest subagent |
| `<safety_stop>` | Safety valve triggered (unlimited mode) | Save state, report reason, stop |

### Marker Examples

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

## Integration with Subagent-Driven-Development

When used with wave-based execution:

```
FOR wave IN waves:
  Dispatch subagents for wave tasks
  Wait for wave completion
  IF remaining waves > 0: CONTINUE (self-completion)
  ELSE: OUTPUT <done>
```

Each subagent can also self-complete through sub-steps within its task.

## Integration with Autowork Pipeline

```
Autowork Phase 3 (Execution):
  result = INVOKE self-completion with subagent-driven-development context

  success       -> proceed to Phase 4 (Quality Gates)
  limit_reached -> ask user to continue with remaining
  blocked       -> handle blocker
```

## Configuration

**Max iterations:** 5 (default) or `unlimited` for long-running tasks.
- Default (5): Safe for most tasks. Prevents loops, manages context.
- Custom (10, 20): For known multi-step tasks with predictable scope.
- Unlimited: For optimization/experimentation. REQUIRES safety valves (see Unlimited Mode).

Override: `INVOKE skill: self-completion max_iterations: 10`
Unlimited: `INVOKE skill: self-completion max_iterations: unlimited`

## Unlimited Mode

Removes the hard iteration cap for long-running optimization and experimentation tasks.
Triggered by: `max_iterations: unlimited` or user says "don't stop", "work until done", "no limit", "keep going indefinitely".

### Safety Architecture (Defense in Depth)

Unlimited mode has 5 INDEPENDENT safety valves. If ANY ONE triggers, the loop MUST stop immediately. No single point of failure.

| Safety Valve | Trigger | Action | Configurable? |
|-------------|---------|--------|---------------|
| **Context pressure** | >75% context used | Save state → STOP | Threshold: yes (60-85%) |
| **Wall-clock timeout** | >4 hours elapsed | Save state → STOP | Duration: yes (1-12h) |
| **Idle detection** | 3 consecutive iterations with 0 file changes | Save state → STOP | Count: yes (2-5) |
| **Progress stall** | Same error repeated 3+ times | Save state → STOP | Count: yes (2-5) |
| **Iteration checkpoint** | Every 10 iterations | Log progress, check all valves | Interval: yes (5-20) |

### Why Each Valve Exists

1. **Context pressure (75%)** — Primary defense. Claude Code's context window is finite. At 75%, quality degrades and risk of losing work increases. This is the MOST IMPORTANT valve.
2. **Wall-clock timeout (4h)** — Prevents runaway sessions overnight. Even if context is fine, a 12-hour session suggests something is wrong.
3. **Idle detection (3 iterations)** — If the agent runs 3 loops without changing any files, it's spinning without progress. Likely stuck in a reasoning loop.
4. **Progress stall (3 same errors)** — Existing behavior from base algorithm. Same error 3x = not making progress.
5. **Iteration checkpoint (every 10)** — Forces periodic self-assessment. Agent must re-evaluate whether continuing makes sense.

### State Preservation on Stop

When ANY safety valve triggers, BEFORE stopping:

1. Write `work/self-completion-state.md`:

```markdown
# Self-Completion State

- Status: PAUSED
- Reason: {context_pressure|timeout|idle|stall|manual}
- Completed: {N} tasks
- Remaining: {M} tasks
- Total iterations: {count}
- Time elapsed: {duration}
- Context usage: {percentage}%

## Completed Tasks
1. [task description] — DONE
2. [task description] — DONE

## Remaining Tasks
3. [task description] — PENDING
4. [task description] — PENDING

## Resume Instructions
To continue: read this file, pick up from task #{next_task_number}
```

2. Update activeContext.md with progress summary
3. Output `<safety_stop>` marker with reason

### Configuration

```
INVOKE skill: self-completion
  max_iterations: unlimited
  context_threshold: 75      # percent (default 75, range 60-85)
  wall_clock_timeout: 4h     # duration (default 4h, range 1-12h)
  idle_threshold: 3           # consecutive no-change iterations (default 3)
  checkpoint_interval: 10     # iterations between checkpoints (default 10)
```

## Blocking Conditions

Stop self-completion when:

1. **User input required** — question, decision point, ambiguous requirement
2. **External dependency** — waiting for API, build, deployment
3. **Error occurred** — test failure, permission denied, resource unavailable
4. **Quality gate** — code review rejected, UAT failed, verification failed
5. **Context pressure** — estimated context > 70% full

## Error Handling

**Task fails:**
- Do NOT automatically retry
- Mark as failed, report to user
- Offer: retry / skip and continue / stop and investigate

**Context getting full:**
- At 50%: warn but continue
- At 70%: stop self-completion, suggest using subagent for remaining tasks

**Unlimited mode safety stop:**
- Save state to work/self-completion-state.md
- Report which safety valve triggered and why
- Provide resume instructions
- Do NOT automatically restart — wait for human decision

## Common Mistakes

1. **Spinning on blocked tasks** — stop immediately, report the blocker
2. **Retrying failed tasks automatically** — always ask user first
3. **Ignoring context limits** — monitor and stop before overflow
4. **Not reporting progress** — user should see each task start/complete
5. **Running without clear todo items** — each todo must be atomic and completable
