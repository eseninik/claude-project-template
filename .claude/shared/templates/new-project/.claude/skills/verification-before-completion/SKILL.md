---
name: verification-before-completion
description: >
  Evidence-based completion gate with goal-backward verification and 3-level artifact
  checking. Requires running verification commands and reading output before claiming
  success. Use when about to say "done", "fixed", "all tests pass", before committing,
  creating PRs, deploying, or moving to the next task/phase. Use when trusting agent
  reports, expressing satisfaction without evidence, or validating phase completion.
  Do NOT use as a substitute for test writing, QA review, code review, or debugging.
roles: [coder, coder-complex, qa-reviewer, qa-fixer, fixer, verifier]
---

# Verification Before Completion

## Overview

Claiming work is complete without verification is dishonesty, not efficiency.

**Core principle:** Evidence before claims, always.

**Violating the letter of this rule is violating the spirit of this rule.**

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.

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

Skip any step = lying, not verifying
```

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing |
| Has logging | Logger calls in new/modified functions | Code compiles without logs, "will add later" |

## Red Flags - STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!", etc.)
- About to commit/push/PR without verification
- Trusting agent success reports
- Relying on partial verification
- Thinking "just this once"
- Tired and wanting work over
- **ANY wording implying success without having run verification**

## Fresh Session Verification

For pipeline work, verification is stronger when done by a FRESH session — one that hasn't seen the implementation decisions.

### When to Use
- After each IMPLEMENT phase in a pipeline
- Before final COMPLETE phase (comprehensive review)
- When implementation was complex (5+ files changed)

### How It Works
1. **Lead agent** commits implementation checkpoint
2. **Lead agent** spawns fresh AO Hybrid session with this prompt:
   ```
   You are a Fresh Verification Agent. Your job is to verify code changes
   with NO prior context about WHY they were made.

   Read ONLY:
   - Changed files (git diff from checkpoint)
   - Test files
   - Acceptance criteria from task files

   Do NOT read: PIPELINE.md, expert-analysis.md, or any planning docs.

   For each acceptance criterion:
   1. Find the code that implements it
   2. Run relevant tests
   3. Check: Exists → Substantive → Wired (3-level check)

   Report format:
   ## Verification Report
   - PASS / FAIL per criterion
   - CRITICAL findings (blocks release)
   - IMPORTANT findings (should fix)
   - MINOR findings (nice to have)
   ```
3. **Fresh session** runs verification independently
4. **Lead agent** reads findings, fixes CRITICALs, re-verifies

### Re-verification Loop

After fixing CRITICAL findings, ALWAYS re-verify before proceeding:

```
FRESH_VERIFY -> findings
  IF 0 CRITICAL -> PASS -> next phase
  IF CRITICAL found -> FRESH_FIX -> fix issues -> FRESH_VERIFY (again)
  Max 3 cycles. If still CRITICAL after 3 -> BLOCKED, escalate to human.
```

The re-verification MUST use a FRESH session (not the same one that fixed the bugs).
Why: The fixer has confirmation bias — they believe their fix works. Fresh eyes catch remaining issues.

### Final Comprehensive Verification
After ALL pipeline phases complete, before COMPLETE:
- Spawn fresh session with 2-3 sub-agents:
  - **Code Quality Agent**: style, patterns, duplication, logging
  - **Security Agent**: injection, secrets, auth bypass
  - **Integration Agent**: wiring, imports, configuration
- Each agent reviews ALL changed code (not just last phase)
- Merge findings → fix → re-verify → COMPLETE

### Why Fresh Sessions
- "Fresh eyes" catch what "zamylenny vzglyad" (blurred vision) misses
- No confirmation bias — fresh session doesn't know what you intended
- Catches integration issues between phases (phase 2 broke phase 1)

## Common Mistakes

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence ≠ evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter ≠ compiler |
| "Agent said success" | Verify independently |
| "I'm tired" | Exhaustion ≠ excuse |
| "Partial check is enough" | Partial proves nothing |
| "Different words so rule doesn't apply" | Spirit over letter |

## Deferred Criteria

Some acceptance criteria can only be verified after deployment (live API, real data, external services).

**When a criterion can't be tested pre-deploy:**
1. Mark it explicitly as deferred
2. Document: what criterion, why deferred, what conditions needed, verification steps
3. Create handoff entry in work/{feature}/deferred-criteria.md

| Field | Content |
|-------|---------|
| Criterion | The acceptance criterion text |
| Reason | Why it can't be tested now (needs live env, real data, etc.) |
| Condition | What must exist before testing (deploy complete, data loaded, etc.) |
| Steps | Concrete verification steps for post-deploy |

**Never silently skip untestable criteria.** If you can't verify it now, defer it explicitly.

## Goal-Backward Verification

Instead of asking "did tasks complete?" ask "did the phase achieve its GOAL?"

Forward checking (task-list) misses gaps between completed tasks and actual goals. Goal-backward verification starts from the desired outcome and works backward to evidence.

**Process:**
1. Extract the phase goal from PIPELINE.md or task description
2. Derive must-haves from the goal (not from the task list)
3. Verify each must-have with evidence
4. Check for anti-patterns that undermine the goal

**Must-have categories:**

| Category | Description | Example |
|----------|-------------|---------|
| Observable truths | What users can see or do after this phase | User can log in, API returns data |
| Required artifacts | Files that must exist with real content | schema.sql, routes.ts, Dockerfile |
| Key links | Critical connections between artifacts | Router imports handler, config references DB |

All tasks can be "done" while the goal remains unmet. Verify the goal, not the checklist.

## Three-Level Artifact Check

Every artifact must pass three levels of verification, not just existence.

| Level | Check | Question |
|-------|-------|----------|
| 1. Exists | File present at expected path | `ls -la path/to/file` |
| 2. Substantive | Content is real implementation, not stub | Not just `return null`, placeholder, TODO |
| 3. Wired | Connected to rest of system | Imported and used somewhere, not orphaned |

**Status matrix:**

| Exists | Substantive | Wired | Status |
|--------|-------------|-------|--------|
| Yes | Yes | Yes | VERIFIED |
| Yes | Yes | No | ORPHANED |
| Yes | No | - | STUB |
| No | - | - | MISSING |

ORPHANED is the most dangerous status -- it looks complete but does nothing. Always check Level 3.

## Stub Detection Patterns

Common AI-generated stubs to flag during Level 2 checks.

**JavaScript/TypeScript:**
```
return <div>Component</div>
return <div>Placeholder</div>
return null
return Response.json({ message: "Not implemented" })
export function useAuth() { return { user: null } }
```

**Python:**
```
pass
return None
raise NotImplementedError
return {"status": "not implemented"}
```

**General red flags:**
```
# TODO
// TODO
/* TODO */
console.log("not implemented")
print("placeholder")
print("...")               # bare print instead of logger
console.log("...")         # bare console.log instead of logger
System.out.println("...")  # bare stdout instead of logger
```

Any of these in new code means Level 2 fails. The artifact is a STUB, not an implementation.

## Goal-Backward Process

```
1. EXTRACT: Read phase goal from PIPELINE.md or task description
2. DERIVE must-haves:
   - What observable truths must be true? (users can see/do X)
   - What artifacts must exist? (files, configs, schemas)
   - What key links must work? (imports, API calls, DB connections)
3. VERIFY each must-have:
   - Level 1: File/endpoint exists
   - Level 2: Content is substantive (not stub)
   - Level 3: Properly wired (imported, called, connected)
4. SCAN for anti-patterns:
   - TODO/FIXME in new code
   - console.log-only implementations
   - Placeholder text in UI
   - Empty catch blocks
   - Unused imports/exports
   - New/modified functions without structured logging
   - Catch/except blocks without error logging
5. REPORT:
   - VERIFIED: all must-haves pass 3 levels
   - GAPS_FOUND: list gaps with evidence
   - STUBS_FOUND: list stubs with file:line
```

## Key Patterns

**Tests:**
```
✅ [Run test command] [See: 34/34 pass] "All tests pass"
❌ "Should pass now" / "Looks correct"
```

**Regression tests (TDD Red-Green):**
```
✅ Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
❌ "I've written a regression test" (without red-green verification)
```

**Build:**
```
✅ [Run build] [See: exit 0] "Build passes"
❌ "Linter passed" (linter doesn't check compilation)
```

**Requirements:**
```
✅ Re-read plan → Create checklist → Verify each → Report gaps or completion
❌ "Tests pass, phase complete"
```

**Agent delegation:**
```
✅ Agent reports success → Check VCS diff → Verify changes → Report actual state
❌ Trust agent report
```

## Verification Commands by Type

Pick the RIGHT command for what you're verifying:

| Task Type | Verification Command |
|-----------|---------------------|
| API endpoint | `curl -s http://localhost:PORT/endpoint \| jq .` |
| Python module | `python -c "from module import func; print(func(test))"` |
| Docker service | `docker compose ps && docker compose logs --tail=5 svc` |
| Config change | `grep expected_value config_file` |
| DB migration | `python -c "from db import engine; ..."` |
| Bot command | Manual: send /command, verify response matches spec |
| File creation | `ls -la path/to/file && head -5 path/to/file` |
| Git operation | `git log --oneline -3 && git diff --stat` |
| Logging coverage | `grep -r "logger\." src/ --include="*.py" \| wc -l` | No logger imports in new files |

Don't just run the test suite when a targeted command proves the claim faster.

## Why This Matters

From 24 failure memories:
- your human partner said "I don't believe you" - trust broken
- Undefined functions shipped - would crash
- Missing requirements shipped - incomplete features
- Time wasted on false completion → redirect → rework
- Violates: "Honesty is a core value. If you lie, you'll be replaced."

## When To Apply

**ALWAYS before:**
- ANY variation of success/completion claims
- ANY expression of satisfaction
- ANY positive statement about work state
- Committing, PR creation, task completion
- Moving to next task
- Delegating to agents

**Rule applies to:**
- Exact phrases
- Paraphrases and synonyms
- Implications of success
- ANY communication suggesting completion/correctness

## The Bottom Line

**No shortcuts for verification.**

Run the command. Read the output. THEN claim the result.

This is non-negotiable.

## Logging Verification

**Before claiming "done", verify logging coverage:**
- Every new function has entry (INFO) and exit (INFO) logs
- Every catch/except block has ERROR log with context
- Every external API/DB call has timing log
- No bare print()/console.log() — use structured logger
- No sensitive data in logs (passwords, tokens, PII)

If new code lacks logging → it is NOT done. Add logging first.
