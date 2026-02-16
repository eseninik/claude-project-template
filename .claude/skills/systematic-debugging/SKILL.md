---
name: systematic-debugging
description: |
  Four-phase debugging framework: root cause investigation, pattern analysis, hypothesis testing, implementation.
  Enforces understanding before fixing. Escalates to architecture review after 3+ failed fix attempts.
  Use when encountering any bug, test failure, unexpected behavior, or performance problem.
  For deep call stacks, trace manually through component boundaries.
---

# Systematic Debugging

**NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.**

## Phase 1: Root Cause Investigation
1. Read error messages completely (stack traces, line numbers, codes)
2. Reproduce consistently -- exact steps, every time
3. Check recent changes (`git diff`, new deps, config, env)
4. Gather evidence at component boundaries:
   - Log data entering/exiting each boundary
   - Verify env/config propagation
   - Run once -> find where it breaks -> investigate that component
5. For deep call stacks -> trace through component boundaries manually

## Phase 2: Pattern Analysis
1. Find similar WORKING code in same codebase
2. Read reference implementation COMPLETELY (do not skim)
3. List every difference between working and broken
4. Map dependencies: components, settings, assumptions

## Phase 3: Hypothesis Testing
1. Form single hypothesis: "X is root cause because Y"
2. Test minimally: smallest change, one variable at a time
3. Worked -> Phase 4. Failed -> NEW hypothesis (don't stack fixes)

## Phase 4: Implementation
1. Create failing test case
2. Implement single fix (root cause only, no "while I'm here")
3. Verify: test passes, no regressions
4. Fix fails? Count attempts:
   - <3: return to Phase 1 with new info
   - 3+: STOP -- question architecture (see below)

## After 3+ Failed Fixes
Signs of architectural problem: shared state coupling, "massive refactoring" needed, each fix creates new symptoms.
STOP and discuss fundamentals with user before more attempts.

## Red Flags -- Return to Phase 1
- "Quick fix for now, investigate later"
- "Just try changing X and see"
- "I don't fully understand but this might work"
- "One more fix attempt" (when already tried 2+)

## Quick Reference

| Phase | Done When |
|-------|-----------|
| 1. Root Cause | Understand WHAT and WHY |
| 2. Pattern | Differences identified |
| 3. Hypothesis | Confirmed or new hypothesis |
| 4. Implementation | Bug resolved, tests pass |
