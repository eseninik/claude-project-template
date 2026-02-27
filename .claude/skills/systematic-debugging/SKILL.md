---
name: systematic-debugging
description: |
  Four-phase debugging framework: investigate -> hypothesize -> test -> fix.
  Enforces understanding before fixing. Escalates after 3+ failed attempts.
  Use when encountering any bug, test failure, or unexpected behavior.
---

## Philosophy
Understanding the bug must come before fixing it. A fix without understanding is a coin flip that creates technical debt.

## Critical Constraints
**never:**
- Apply fixes without forming and testing a hypothesis first
- Skip regression verification after a fix

**always:**
- Form 2-3 hypotheses and test the most likely first
- Change approach entirely after 3 failed attempts

# Systematic Debugging

## 4 Phases (follow in order)

### 1. Investigate
- Read error message/stack trace completely
- Find the exact line that fails
- Check recent changes (`git diff`, `git log -5`)
- Reproduce consistently

### 2. Hypothesize
- Form 2-3 ranked hypotheses (most likely first)
- For each: what evidence would confirm/deny it?
- Check existing code for similar patterns

### 3. Test
- Test top hypothesis first
- Add diagnostic output (print/log) at failure point
- If hypothesis wrong -> next hypothesis, do NOT guess-fix

### 4. Fix
- Fix root cause, not symptom
- Run original failing test to verify
- Run full test suite to check regressions
- If fix fails 3+ times -> escalate (ask user or try different approach)

## Red Flags
- Changing code without understanding the bug -> STOP
- "Try this and see" without hypothesis -> STOP
- Same fix attempted 3+ times -> change approach entirely
