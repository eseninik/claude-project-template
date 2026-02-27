---
name: error-recovery
version: 1.0.0
description: |
  Structured recovery patterns for common errors.
  Handles Edit failures, Bash timeouts, test failures, and general errors.

  AUTOMATIC TRIGGER:
  - Tool call returns error
  - Test command fails
  - Unexpected exception

  Do NOT use for: successful operations, user-initiated cancellations
---

# Error Recovery Skill

Structured patterns for recovering from common errors during development.

## Overview

When errors occur, don't guess - follow systematic recovery patterns:

1. **Diagnose** - Identify error type and root cause
2. **Select Pattern** - Choose appropriate recovery strategy
3. **Execute Recovery** - Follow pattern steps with retry limits
4. **Escalate** - If recovery fails, escalate appropriately

## Pattern 1: Edit Error Recovery

**Triggers:**
- Edit tool returns error
- "old_string not found"
- "old_string not unique"
- File permission errors

### Diagnosis

```
DIAGNOSE_EDIT_ERROR(error):
  IF "not found" IN error:
    cause = "content_mismatch"
    # File content doesn't match expected
  ELIF "not unique" IN error:
    cause = "multiple_matches"
    # old_string appears multiple times
  ELIF "permission" IN error:
    cause = "permission_denied"
  ELIF "does not exist" IN error:
    cause = "file_missing"
  ELSE:
    cause = "unknown"

  RETURN cause
```

### Recovery Actions

```
RECOVER_EDIT(cause, original_edit):
  max_retries = 3
  retry_count = 0

  WHILE retry_count < max_retries:
    IF cause == "content_mismatch":
      # Step 1: Re-read the file
      current_content = Read(file_path)

      # Step 2: Find actual content to replace
      actual_old_string = find_similar(current_content, original_edit.old_string)

      IF actual_old_string:
        # Step 3: Retry with correct content
        Edit(file_path, actual_old_string, original_edit.new_string)
        RETURN success
      ELSE:
        # Content structure changed significantly
        ESCALATE("File structure changed, manual review needed")

    IF cause == "multiple_matches":
      # Step 1: Re-read to see context
      current_content = Read(file_path)

      # Step 2: Expand old_string to be unique
      expanded_old = expand_context(original_edit.old_string, current_content)

      # Step 3: Retry with expanded context
      Edit(file_path, expanded_old, expanded_new)
      RETURN success

    IF cause == "file_missing":
      # Use Write instead of Edit
      Write(file_path, original_edit.new_string)
      RETURN success

    IF cause == "permission_denied":
      ESCALATE("Permission denied - user action required")

    retry_count += 1

  # Max retries exceeded
  ESCALATE("Edit failed after 3 attempts")
```

### Fallback: Use Write

If Edit keeps failing:

```
FALLBACK_TO_WRITE(file_path, intended_content):
  # Read current file
  current = Read(file_path)

  # Apply change manually
  new_content = apply_change(current, intended_change)

  # Write entire file
  Write(file_path, new_content)

  # Verify
  verify = Read(file_path)
  RETURN verify == new_content
```

## Pattern 2: Bash Timeout Recovery

**Triggers:**
- Command execution timeout
- Command hangs (no output)
- Process killed

### Diagnosis

```
DIAGNOSE_TIMEOUT(command, timeout):
  IF is_test_command(command):
    cause = "slow_tests"
  ELIF is_build_command(command):
    cause = "slow_build"
  ELIF is_network_command(command):
    cause = "network_issue"
  ELIF involves_large_files(command):
    cause = "io_bound"
  ELSE:
    cause = "unknown_hang"

  RETURN cause
```

### Recovery Actions

```
RECOVER_TIMEOUT(cause, command):
  max_retries = 2
  retry_count = 0

  WHILE retry_count < max_retries:
    IF cause == "slow_tests":
      # Option 1: Increase timeout
      result = Bash(command, timeout=300000)  # 5 minutes

      # Option 2: Run subset
      IF still_timeout:
        result = Bash(command + " -k specific_test")

    IF cause == "slow_build":
      # Try with more verbose output to see progress
      result = Bash(command + " --verbose", timeout=600000)

    IF cause == "network_issue":
      # Wait and retry
      sleep(5)
      result = Bash(command, timeout=60000)

    IF cause == "io_bound":
      # Run in background, check later
      Bash(command, run_in_background=true)
      RETURN { status: "background", check_later: true }

    IF result.success:
      RETURN success

    retry_count += 1

  ESCALATE("Command timed out after retries: " + command)
```

### Background Execution

For long-running commands:

```
RUN_BACKGROUND(command):
  result = Bash(command, run_in_background=true)
  task_id = result.task_id

  # Check periodically
  WHILE true:
    status = TaskOutput(task_id, block=false)
    IF status.completed:
      RETURN status.output
    sleep(10)
```

## Pattern 3: Test Failure Recovery

**Triggers:**
- Test command exits with non-zero code
- Test assertions fail
- Test infrastructure errors

### CRITICAL RULE

```
⚠️ DO NOT propose fixes until root cause is identified!

Test failures MUST trigger systematic-debugging skill.
```

### Recovery Process

```
RECOVER_TEST_FAILURE(test_output):
  # Step 1: DO NOT GUESS THE FIX

  # Step 2: Invoke systematic-debugging
  INVOKE skill: systematic-debugging
    input: test_output
    goal: find_root_cause

  # Step 3: Wait for root cause analysis
  root_cause = systematic-debugging.result

  # Step 4: Only then propose fix
  IF root_cause.identified:
    PROPOSE_FIX(root_cause)
  ELSE:
    ASK_USER("Root cause unclear. Need more information.")
```

### Test Infrastructure vs Test Logic

```
CATEGORIZE_TEST_FAILURE(output):
  IF "ModuleNotFoundError" OR "ImportError":
    type = "infrastructure"
    action = "fix imports/dependencies"

  ELIF "ConnectionRefused" OR "timeout":
    type = "infrastructure"
    action = "check test environment"

  ELIF "AssertionError" OR "Expected" OR "Actual":
    type = "logic"
    action = "investigate with systematic-debugging"

  ELIF "fixture" OR "setup" OR "teardown":
    type = "infrastructure"
    action = "fix test setup"

  RETURN type, action
```

## Pattern 4: General Error Recovery

**Triggers:**
- Any unexpected error
- Unknown error types
- Multiple errors at once

### Categorization

```
CATEGORIZE_ERROR(error):
  # Transient - likely to succeed on retry
  transient_patterns = [
    "timeout", "connection", "network",
    "temporary", "retry", "EAGAIN"
  ]

  # Permanent - won't succeed without changes
  permanent_patterns = [
    "not found", "does not exist", "permission denied",
    "invalid", "syntax error", "type error"
  ]

  FOR pattern IN transient_patterns:
    IF pattern IN error.lower():
      RETURN "transient"

  FOR pattern IN permanent_patterns:
    IF pattern IN error.lower():
      RETURN "permanent"

  RETURN "unknown"
```

### Recovery by Category

```
RECOVER_GENERAL(error, category):
  IF category == "transient":
    # Retry with backoff
    FOR attempt IN [1, 2, 3]:
      sleep(attempt * 2)  # 2s, 4s, 6s
      result = retry_operation()
      IF result.success:
        RETURN success

    ESCALATE("Transient error persists after 3 retries")

  IF category == "permanent":
    # Don't retry - investigate
    LOG("Permanent error: " + error)
    ANALYZE_CAUSE(error)
    PROPOSE_SOLUTION()

  IF category == "unknown":
    # Investigate before acting
    LOG("Unknown error type: " + error)
    ASK_USER("Unexpected error occurred. How to proceed?")
```

## State Tracking

Track recovery attempts in JSON:

```json
{
  "recovery_session": {
    "started_at": "2026-01-19T10:00:00Z",
    "error_type": "edit_failure",
    "pattern": "content_mismatch",
    "attempts": [
      {
        "attempt": 1,
        "action": "re-read and retry",
        "result": "failed",
        "reason": "content still mismatched"
      },
      {
        "attempt": 2,
        "action": "expand context",
        "result": "success"
      }
    ],
    "final_status": "recovered",
    "total_attempts": 2
  }
}
```

## Integration with Orchestrator

Orchestrator wraps tool calls with error recovery:

```
TRY_WITH_RECOVERY(tool, params):
  result = call_tool(tool, params)

  IF result.error:
    # Identify pattern
    pattern = IDENTIFY_PATTERN(tool, result.error)

    # Invoke recovery
    recovery_result = INVOKE skill: error-recovery
      pattern: pattern
      error: result.error
      original_params: params

    IF recovery_result.success:
      RETURN recovery_result.value
    ELSE:
      ESCALATE(recovery_result.escalation)

  RETURN result
```

## Escalation Rules

When to escalate to user:

| Condition | Escalation |
|-----------|------------|
| Max retries exceeded | "Не удалось восстановиться после {N} попыток" |
| Permission error | "Требуются права доступа" |
| Unknown error type | "Неизвестная ошибка - нужна помощь" |
| Infrastructure broken | "Проблема с окружением" |
| Root cause unclear | "Не могу определить причину" |

### Escalation Format

```
ESCALATE(reason):
  message = f"""
  ⚠️ **Требуется помощь**

  **Проблема:** {reason}

  **Что было попробовано:**
  {list_of_attempts}

  **Текущее состояние:**
  {current_state}

  Как поступить?
  """

  DISPLAY(message)
  WAIT_FOR_USER()
```

## Output Format

```json
{
  "skill": "error-recovery",
  "pattern": "edit_failure",
  "diagnosis": "content_mismatch",
  "attempts": 2,
  "result": "success",
  "action_taken": "re-read file, expanded context, retried edit",
  "escalated": false
}
```
