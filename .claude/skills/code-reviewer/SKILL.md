---
name: code-reviewer
version: 1.0.0
description: BACKGROUND SKILL - Automatically activated when writing or modifying code - performs continuous code review checking for common issues, patterns violations, and improvement opportunities
---

# Code Reviewer (Background Skill)

## Overview

This is a **background skill** that runs automatically during code writing. It catches issues before they become problems.

**Core principle:** Review as you write, not after you're done.

## Automatic Activation

This skill activates **automatically** when:
- Writing new functions/methods
- Modifying existing code
- Completing a code block
- Before committing changes

**No manual loading required.**

## Review Checklist

### 1. Function Quality

```
FOR EACH FUNCTION, CHECK:

□ Name describes what it does (verb + noun)
□ Single responsibility (does ONE thing)
□ Length < 30 lines (consider splitting if longer)
□ Cyclomatic complexity < 10
□ No deeply nested conditionals (max 3 levels)
□ Return type annotated
□ Parameters have type hints
```

### 2. Error Handling

```
FOR EACH TRY/EXCEPT, CHECK:

□ Specific exceptions caught (not bare except)
□ Exceptions logged or re-raised
□ Error messages are helpful
□ Resources cleaned up (finally or context manager)
□ User gets appropriate feedback
```

```python
# ❌ BAD: Swallows all errors silently
try:
    result = do_something()
except:
    pass

# ✅ GOOD: Specific exception, logged, re-raised
try:
    result = await api.fetch_data(user_id)
except aiohttp.ClientError as e:
    logger.error(f"API request failed for user {user_id}: {e}")
    raise ServiceUnavailableError("Could not fetch data") from e
```

### 3. Async Code

```
FOR ASYNC FUNCTIONS, CHECK:

□ All coroutines awaited
□ No blocking calls (time.sleep, requests.get)
□ Concurrent operations use gather()
□ Timeouts on external calls
□ Resources cleaned up (async with)
```

### 4. Security

```
FOR USER INPUT, CHECK:

□ Input validated before use
□ SQL queries parameterized
□ File paths sanitized
□ Sensitive data not logged
□ Secrets from environment variables
```

### 5. Code Smells

| Smell | Detection | Fix |
|-------|-----------|-----|
| Long function | > 30 lines | Split into smaller functions |
| Deep nesting | > 3 levels | Early returns, extract method |
| Duplicate code | Copy-paste | Extract function |
| Magic numbers | Hardcoded values | Named constants |
| God object | Class does everything | Split by responsibility |
| Long parameter list | > 4 params | Parameter object |

## Auto-Comments

When this skill detects issues, it suggests inline comments:

```python
async def process_user(user_id, name, email, phone, address, status, role):
    # REVIEW: Long parameter list (7 params). Consider using dataclass.
    
    if user_id:
        if name:
            if email:
                if phone:
                    # REVIEW: Deep nesting (4 levels). Use early returns.
                    ...

def calculate(x):
    return x * 86400
    # REVIEW: Magic number 86400. Use named constant SECONDS_PER_DAY.
```

## Issue Categories

### 🔴 Critical (must fix)

- Security vulnerabilities
- Potential data loss
- Unhandled exceptions that crash app
- Race conditions

### 🟠 Warning (should fix)

- Missing type hints on public API
- Functions > 30 lines
- Bare except clauses
- Hardcoded credentials

### 🟡 Suggestion (consider fixing)

- Code can be simplified
- Missing docstring
- Inconsistent naming
- Minor duplication

## Review Output Format

```markdown
## Code Review: [file:function]

### 🔴 Critical
- Line 45: SQL injection vulnerability - use parameterized query

### 🟠 Warnings
- Line 23: Function `process_data` is 52 lines - consider splitting
- Line 67: Bare except catches SystemExit - use `except Exception`

### 🟡 Suggestions
- Line 12: Consider using f-string instead of .format()
- Line 34: `data` could be more descriptive (e.g., `user_data`)

### ✅ Good Practices Observed
- Proper async/await usage
- Comprehensive type hints
- Clear error messages
```

## Integration with Workflow

### During Development

```
Write code → Background review → Fix issues → Continue
```

### Before Commit

```bash
# Manual trigger if needed
/review src/handlers/
```

### In PR

Code reviewer findings can be added to PR description:
```markdown
## Self-Review Checklist
- [x] No critical issues
- [x] All warnings addressed
- [ ] Suggestions considered
```

## Customization

### Disable for Specific Code

```python
# code-review: ignore-next-line
result = x * 86400  # Intentionally using magic number

# code-review: ignore-function
def legacy_function():
    # This function is scheduled for rewrite
    pass
```

### Project-Specific Rules

Add to `CLAUDE.md`:

```markdown
## Code Review Rules

### Exceptions to Standard Rules
- Magic numbers OK in: tests/, migrations/
- Long functions OK in: generated/

### Additional Checks
- All handlers must have rate limiting
- All DB operations must be in repositories
```

## Quick Reference

| Issue | Action |
|-------|--------|
| Function too long | Split at logical boundaries |
| Deep nesting | Use early returns |
| Duplicate code | Extract to function |
| Missing types | Add type hints |
| Bare except | Catch specific exceptions |
| Hardcoded value | Create constant |
| Security issue | Fix immediately |

## This Skill Triggers

- **test-driven-development** — if new code lacks tests
- **security-checklist** — if security issues found
- **architecture-patterns** — if structural issues detected
