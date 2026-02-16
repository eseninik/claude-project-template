---
name: verification-before-completion
description: |
  Enforces evidence-based completion claims: run verification commands and confirm output before claiming work is done, fixed, or passing.
  Use when about to claim work is complete, before committing, creating PRs, moving to next task, or when expressing satisfaction about results.
  Does NOT define what tests to write (use testing skill) or enforce TDD (use test-driven-development skill).
---

# Verification Before Completion

Claiming work is complete without verification is dishonesty, not efficiency.

**Evidence before claims, always.**

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If the verification command was not run in this message, you cannot claim it passes.

## The Gate Function

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim
```

## Verification Requirements

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing |
| Bug fixed | Original symptom: resolved | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing |

## Patterns

**Tests:**
```
Run test command -> See: 34/34 pass -> "All tests pass"
NOT: "Should pass now" / "Looks correct"
```

**Regression tests (TDD Red-Green):**
```
Write test -> Run (pass) -> Revert fix -> Run (MUST FAIL) -> Restore -> Run (pass)
NOT: "I've written a regression test" (without red-green cycle)
```

**Build:**
```
Run build -> See: exit 0 -> "Build passes"
NOT: "Linter passed" (linter does not check compilation)
```

**Requirements:**
```
Re-read plan -> Create checklist -> Verify each item -> Report gaps or completion
NOT: "Tests pass, phase complete"
```

**Agent delegation:**
```
Agent reports success -> Check VCS diff -> Verify changes -> Report actual state
NOT: Trust agent report at face value
```

## Red Flags - STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Done!")
- About to commit/push/PR without verification
- Trusting agent success reports without checking
- Relying on partial verification
- Any wording implying success without having run verification

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | Run the verification |
| "I'm confident" | Confidence is not evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter is not compiler |
| "Agent said success" | Verify independently |
| "Partial check is enough" | Partial proves nothing |

## When to Apply

**ALWAYS before:**
- Any completion or success claim
- Any expression of satisfaction about work state
- Committing, PR creation, task completion
- Moving to next task
- Accepting delegated agent work

No shortcuts for verification. Run the command. Read the output. THEN claim the result.
