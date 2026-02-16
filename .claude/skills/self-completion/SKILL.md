---
name: self-completion
description: |
  Automatically continues through pending todo items until all are complete or a limit is reached.
  Prevents stopping mid-task when more work remains in the plan.
  Activate when TodoWrite has pending items after completing a task, or during autowork pipeline execution.
  Does NOT apply to exploratory work, user-guided interactive tasks, or single-step operations.
---

# Self-Completion

## Algorithm

```
iteration = 0, max = 5

LOOP:
  1. Get todos -> find pending/in_progress items
  2. None remain -> DONE, return
  3. iteration >= max -> LIMIT, return
  4. Pick next: in_progress first, then first pending
  5. Execute task
  6. Success -> mark completed, iteration++, continue
  7. Blocked (needs user input/external dep) -> BLOCKED, return
  8. Failure -> mark failed, ERROR, ask user
```

## Completion Markers

| Marker | Meaning | Next |
|--------|---------|------|
| DONE | All items completed | Session complete |
| BLOCKED | Needs user input or external dep | Wait for user |
| LIMIT | Hit 5-iteration limit | Ask user to continue or stop |
| ERROR | Unrecoverable failure | Report and wait |

## Stop Conditions
- User input required (question, decision, ambiguity)
- External dependency (API key, build, deployment)
- Error occurred (test failure, permission denied)
- Quality gate failed (review rejected, verification failed)
- Context >70% -- suggest subagent for remaining tasks

## Error Handling
1. Mark task as failed
2. Do NOT auto-retry
3. Present: retry / skip and continue / stop and investigate
4. Wait for user choice

## Hard Rules
- Default max_iterations: 5 (override via invocation context)
- Ambiguous/large todo -> break into sub-steps before executing
- Context >50%: log warning. >70%: stop, suggest subagent delegation.
