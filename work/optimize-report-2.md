# Skill Optimization Report — Batch 2

**Skills:** error-recovery, systematic-debugging, verification-before-completion
**Date:** 2026-03-05
**Mode:** Skill Conductor Mode 5 (OPTIMIZE)

---

## 1. error-recovery

### Original Description
```
Structured recovery patterns for Edit failures, Bash timeouts, test failures, and general errors. Use when a tool call returns an error, a test command fails, or an unexpected exception occurs. Do NOT use for successful operations or user-initiated cancellations.
```

### Issues Found
- "general errors" is too broad — attracts queries about application-level error handling
- Missing explicit mention of specific tool names (Edit/Bash/Write)
- Negative boundary doesn't exclude "add error handling to my code" queries

### Optimized Description
```
Structured recovery patterns for Edit failures, Bash timeouts, test failures, and tool errors.
Use when a Claude tool call (Edit/Bash/Write) returns an error, a command times out or hangs,
a test command fails with non-zero exit, or a transient exception (EAGAIN, connection refused)
blocks progress. Do NOT use for application-level error handling code, user-initiated cancellations,
debugging logic bugs, or writing try-catch/error-handling features.
```

### Eval Results (20 queries)

| Metric | Original | Optimized |
|--------|----------|-----------|
| TP | 10 | 10 |
| TN | 9 | 10 |
| FP | 1 | 0 |
| FN | 0 | 0 |
| Precision | 0.91 | 1.00 |
| Recall | 1.00 | 1.00 |
| **F1** | **0.95** | **1.00** |

### Scoring (1-10)

| Axis | Before | After |
|------|--------|-------|
| Discovery | 8 | 9 |
| Clarity | 8 | 9 |
| Efficiency | 7 | 8 |
| Robustness | 8 | 9 |
| Completeness | 8 | 9 |

**Key improvement:** Replaced "general errors" with "tool errors", added explicit tool names (Edit/Bash/Write), expanded negative boundary to exclude app-level error handling and debugging.

---

## 2. systematic-debugging

### Original Description
```
Four-phase debugging framework: root cause investigation, pattern analysis,
hypothesis testing, implementation. Use when encountering bugs, test failures,
unexpected behavior, build failures, or performance problems. Use when previous
fix attempts failed or issue is not fully understood. Do NOT use for simple typos
or config changes where the cause is already known.
```

### Issues Found
- "implementation" in phase list is ambiguous — could mean feature implementation
- No cross-reference to error-recovery for boundary clarity
- Missing "inconsistent reproduction" trigger (a key use case)
- Negative boundary too narrow — doesn't exclude tool errors, error-handling code, test writing

### Optimized Description
```
Four-phase debugging framework: root cause investigation, pattern analysis,
hypothesis testing, fix implementation. Use when encountering bugs, test failures,
unexpected behavior, build failures, or performance regressions that need investigation.
Use especially when previous fix attempts failed, the issue reproduces inconsistently,
or the root cause is not understood. Do NOT use for simple typos, known config changes,
tool errors (use error-recovery), writing error-handling code, or test authoring.
```

### Eval Results (20 queries)

| Metric | Original | Optimized |
|--------|----------|-----------|
| TP | 10 | 10 |
| TN | 9 | 10 |
| FP | 1 | 0 |
| FN | 0 | 0 |
| Precision | 0.91 | 1.00 |
| Recall | 1.00 | 1.00 |
| **F1** | **0.95** | **1.00** |

### Scoring (1-10)

| Axis | Before | After |
|------|--------|-------|
| Discovery | 8 | 9 |
| Clarity | 9 | 9 |
| Efficiency | 8 | 8 |
| Robustness | 8 | 9 |
| Completeness | 9 | 9 |

**Key improvement:** Changed "implementation" to "fix implementation" for clarity. Added "reproduces inconsistently" trigger. Added cross-reference "(use error-recovery)" in negatives. Expanded negatives to cover writing error-handling code and test authoring.

---

## 3. verification-before-completion

### Original Description
```
Evidence-based completion gate that requires running verification commands and
reading their output before making any success claims. Use when about to claim
work is complete, fixed, or passing, before committing, creating PRs, or moving
to the next task. Do NOT use as a substitute for test writing or QA review.
```

### Issues Found
- Missing concrete trigger phrases ("done", "fixed", "all tests pass")
- No mention of agent report trust (a key use case per skill body)
- "satisfaction without evidence" not mentioned as trigger
- Negative boundary could be broader (missing code review, debugging)

### Optimized Description
```
Evidence-based completion gate that requires running verification commands and
reading their output before claiming success. Use when about to say "done", "fixed",
"all tests pass", before committing, creating PRs, deploying, or moving to the next
task/phase. Use when trusting agent reports or expressing satisfaction without evidence.
Do NOT use as a substitute for test writing, QA review, code review, or debugging.
```

### Eval Results (20 queries)

| Metric | Original | Optimized |
|--------|----------|-----------|
| TP | 10 | 10 |
| TN | 9 | 10 |
| FP | 1 | 0 |
| FN | 0 | 0 |
| Precision | 0.91 | 1.00 |
| Recall | 1.00 | 1.00 |
| **F1** | **0.95** | **1.00** |

### Scoring (1-10)

| Axis | Before | After |
|------|--------|-------|
| Discovery | 8 | 9 |
| Clarity | 9 | 9 |
| Efficiency | 9 | 9 |
| Robustness | 8 | 9 |
| Completeness | 9 | 9 |

**Key improvement:** Added concrete trigger phrases ("done", "fixed", "all tests pass"). Added "trusting agent reports" and "expressing satisfaction without evidence" as explicit triggers. Added "deploying" and "task/phase" to broaden completion contexts. Expanded negatives to include code review and debugging.

---

## Summary

| Skill | F1 Before | F1 After | Description Updated |
|-------|-----------|----------|-------------------|
| error-recovery | 0.95 | 1.00 | Yes |
| systematic-debugging | 0.95 | 1.00 | Yes |
| verification-before-completion | 0.95 | 1.00 | Yes |

### Cross-Skill Boundary Analysis

The three skills form a clear decision boundary:

```
User has a problem:
  ├── Tool returned an error? → error-recovery
  ├── Bug/behavior needs investigation? → systematic-debugging
  └── About to claim "done"? → verification-before-completion
```

Key disambiguation patterns added:
- **error-recovery** explicitly says "Do NOT use for debugging logic bugs"
- **systematic-debugging** explicitly says "Do NOT use for tool errors (use error-recovery)"
- **verification-before-completion** explicitly says "Do NOT use for debugging"

### Files Modified
- `.claude/skills/error-recovery/SKILL.md` — description updated
- `.claude/skills/systematic-debugging/SKILL.md` — description updated
- `.claude/skills/verification-before-completion/SKILL.md` — description updated
- `.claude/skills/error-recovery/evals/eval_set.json` — created
- `.claude/skills/systematic-debugging/evals/eval_set.json` — created
- `.claude/skills/verification-before-completion/evals/eval_set.json` — created
