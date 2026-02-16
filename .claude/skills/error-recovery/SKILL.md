---
name: error-recovery
description: |
  Structured recovery patterns for Edit failures, Bash timeouts, test failures, and general errors.
  Provides diagnosis, retry with backoff, and escalation procedures.
  Activate when a tool call returns an error, a test command fails, or an unexpected exception occurs.
  Does NOT handle user-initiated cancellations or successful operations.
---

# Error Recovery

Diagnose first, then select recovery pattern. Max 3 retries, then escalate.

## Pattern 1: Edit Errors

| Error | Recovery |
|-------|----------|
| "old_string not found" | Re-read file, find actual content, retry |
| "old_string not unique" | Expand old_string with surrounding context |
| "permission denied" | Escalate to user |
| "does not exist" | Use Write instead of Edit |
| 3+ failures | Fall back to Write (read full file, apply change, write entire file) |

## Pattern 2: Bash Timeouts

| Cause | Recovery |
|-------|----------|
| Slow tests | Increase timeout to 300000ms, or `-k specific_test` |
| Slow build | Add `--verbose`, timeout 600000ms |
| Network issue | Wait 5s, retry with 60000ms timeout |
| I/O bound | `run_in_background=true`, check later |

## Pattern 3: Test Failures

Categorize first:

| Pattern | Category | Action |
|---------|----------|--------|
| ModuleNotFoundError, ImportError | Infrastructure | Fix imports/deps |
| ConnectionRefused, timeout | Infrastructure | Check test env |
| AssertionError, Expected vs Actual | Logic | Investigate root cause BEFORE fixing |
| fixture/setup/teardown errors | Infrastructure | Fix test setup |

## Pattern 4: General Errors

| Category | Patterns | Strategy |
|----------|----------|----------|
| Transient | timeout, connection, EAGAIN | Retry with backoff (2s, 4s, 6s), max 3 |
| Permanent | not found, permission, syntax, type error | Do NOT retry. Investigate cause |
| Unknown | Anything else | Ask user |

## Escalation (after 3 retries or permanent error)

```
Problem: {description}
Attempted: {recovery actions taken}
Current state: {what works/doesn't}
Options: {suggested next steps}
```
