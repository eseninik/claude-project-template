---
name: error-recovery
description: |
  Retry patterns for tool failures: Edit conflicts, Bash timeouts, test failures.
  Provides diagnosis and backoff. Escalates after 3 retries.
  Use when a tool call fails or returns unexpected errors.
---

# Error Recovery

## Quick Reference

| Error Type | Action |
|-----------|--------|
| Edit "old_string not found" | Re-read file, check exact content, retry with correct string |
| Bash timeout | Increase timeout or break into smaller commands |
| Test failure | Read full output, apply systematic-debugging |
| Permission denied | Ask user, do NOT force/sudo |
| Git conflict | Read conflict markers, resolve manually, do NOT --force |
| Rate limit | Wait 60s, retry (max 3) |
| ENOENT / file not found | Check path with Glob, fix path |

## Retry Protocol
1. First failure: diagnose, fix cause, retry immediately
2. Second failure: different approach, retry
3. Third failure: STOP, ask user for guidance

## Never
- Retry the exact same command that failed
- Use --force/--no-verify to bypass errors
- Silently swallow errors and continue
