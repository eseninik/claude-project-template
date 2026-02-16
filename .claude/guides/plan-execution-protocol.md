# Plan Execution Protocol

**TRIGGER:** Plan detected / задача с 3+ шагами

**BLOCKING REQUIREMENT:** Этот guide ОБЯЗАТЕЛЕН перед началом реализации.

---

## The Gate Function

You CANNOT start implementation until you complete these steps IN THIS MESSAGE:

STEP 1: IDENTIFY PLAN FORMAT
Output: "Plan format: [tasks/*.md / plan.md / implicit / NONE]"

STEP 2: LOAD DECISION ALGORITHM
- IF format = tasks/*.md → Load subagent-driven-development
- IF format = plan.md OR implicit → Load dependency-analysis.md
- IF format = NONE → Continue normally

STEP 3: BUILD WAVE STRUCTURE (MANDATORY for plan.md/implicit)
For EACH task:
  a) List what it depends on
  b) Assign to earliest possible wave
Output wave structure explicitly.

STEP 4: CALCULATE PARALLELIZATION POTENTIAL (MANDATORY)
Formula: (tasks in waves with 2+ tasks) / (total tasks) × 100%
Output: "Parallelization potential: X%"

STEP 5: APPLY DECISION RULE (NO EXCEPTIONS)
```
IF Parallelization potential > 0%:
    → Decision: tasks/*.md + subagent-driven-development

IF Parallelization potential = 0% (every wave = 1 task):
    → Decision: executing-plans
```

STEP 6: OUTPUT PRE-EXECUTION CHECKPOINT
[Use mandatory format below]

If you haven't completed ALL 6 steps in this message, you CANNOT start coding.

**CRITICAL:** Steps 3-5 are COMPUTATIONAL, not intuitive. You must CALCULATE, not guess.

---

## Mandatory Checkpoint Format

```yaml
PRE-EXECUTION CHECKPOINT:

Plan format: [tasks/*.md / plan.md / implicit / none]
Plan location: [file path or "user message"]
Tasks count: [N]

Wave structure (MANDATORY - list ALL waves):
  Wave 1: [task IDs/names] - [N] tasks
  Wave 2: [task IDs/names] - [N] tasks
  Wave 3: [task IDs/names] - [N] tasks
  ...
  Total waves: [N]

Parallelization calculation (MANDATORY):
  Tasks in parallel waves (waves with 2+ tasks): [N]
  Total tasks: [N]
  Parallelization potential: [N/N × 100 = X%]

Decision rule applied:
  Parallelization potential > 0%? [YES/NO]
  IF YES → tasks/*.md (MANDATORY)
  IF NO → executing-plans (allowed)

Final decision: [tasks/*.md + subagent-driven / executing-plans]
Reasoning: [Must reference the calculation above]
```

**VALIDATION:** Checkpoint is INVALID if:
- Wave structure is missing or says "N/A"
- Parallelization calculation is missing
- Decision contradicts the rule (potential > 0% but chose executing-plans)

---

## Decision Rule (MECHANICAL - NO EXCEPTIONS)

```
┌─────────────────────────────────────────────────────────────┐
│                    DECISION RULE                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   1. Calculate Parallelization Potential (PP)               │
│      PP = (tasks in waves with 2+ tasks) / total × 100%    │
│                                                             │
│   2. Apply Rule:                                            │
│                                                             │
│      IF PP > 0%  →  tasks/*.md + subagent-driven           │
│      IF PP = 0%  →  executing-plans                        │
│                                                             │
│   3. NO EXCEPTIONS. NO INTUITION. JUST MATH.               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Why this rule works:**
- PP > 0% means SOME tasks can run in parallel
- Even 25% parallelization saves time
- User preference is "speed" → always take parallel opportunity
- Rule removes subjective judgment → no more "I think sequential is better"

**Examples of rule application:**
| PP | Decision | Reasoning |
|----|----------|-----------|
| 83% | tasks/*.md | PP > 0% |
| 75% | tasks/*.md | PP > 0% |
| 25% | tasks/*.md | PP > 0% |
| 10% | tasks/*.md | PP > 0% |
| 0% | executing-plans | PP = 0% |

---

## Examples

### Example 1: Race Condition Fix - 6 tasks (CORRECT)

```yaml
PRE-EXECUTION CHECKPOINT:

Plan format: plan.md
Plan location: work/race-condition-fix/plan.md
Tasks count: 6

Wave structure (MANDATORY - list ALL waves):
  Wave 1: [1-constructor, 6-import] - 2 tasks
  Wave 2: [2-success, 3-failure, 4-pending] - 3 tasks
  Wave 3: [5-main.py] - 1 task
  Total waves: 3

Parallelization calculation (MANDATORY):
  Tasks in parallel waves (waves with 2+ tasks): 5 (Wave 1: 2, Wave 2: 3)
  Total tasks: 6
  Parallelization potential: 5/6 × 100 = 83%

Decision rule applied:
  Parallelization potential > 0%? YES (83%)
  IF YES → tasks/*.md (MANDATORY)

Final decision: tasks/*.md + subagent-driven-development
Reasoning: 83% parallelization potential requires tasks/*.md per decision rule.
```

### Example 2: Meeting Reminders - 8 tasks (CORRECT)

```yaml
PRE-EXECUTION CHECKPOINT:

Plan format: plan.md
Plan location: ~/.claude/plans/tender-prancing-cocoa.md
Tasks count: 8

Wave structure (MANDATORY - list ALL waves):
  Wave 1: [models.py, config.py, sheets.py] - 3 tasks
  Wave 2: [storage.py] - 1 task
  Wave 3: [service.py] - 1 task
  Wave 4: [webhook.py, poll_handler.py, main.py] - 3 tasks
  Total waves: 4

Parallelization calculation (MANDATORY):
  Tasks in parallel waves (waves with 2+ tasks): 6 (Wave 1: 3, Wave 4: 3)
  Total tasks: 8
  Parallelization potential: 6/8 × 100 = 75%

Decision rule applied:
  Parallelization potential > 0%? YES (75%)
  IF YES → tasks/*.md (MANDATORY)

Final decision: tasks/*.md + subagent-driven-development
Reasoning: 75% parallelization potential requires tasks/*.md per decision rule.
```

### Example 3: Strict Sequential - 5 tasks (CORRECT)

```yaml
PRE-EXECUTION CHECKPOINT:

Plan format: plan.md
Plan location: work/migration/plan.md
Tasks count: 5

Wave structure (MANDATORY - list ALL waves):
  Wave 1: [design-schema] - 1 task
  Wave 2: [create-migration] - 1 task
  Wave 3: [implement-models] - 1 task
  Wave 4: [build-api] - 1 task
  Wave 5: [add-frontend] - 1 task
  Total waves: 5

Parallelization calculation (MANDATORY):
  Tasks in parallel waves (waves with 2+ tasks): 0
  Total tasks: 5
  Parallelization potential: 0/5 × 100 = 0%

Decision rule applied:
  Parallelization potential > 0%? NO (0%)
  IF NO → executing-plans (allowed)

Final decision: executing-plans
Reasoning: 0% parallelization potential - strict sequential chain, executing-plans is appropriate.
```

### Example 4: FAILURE CASE (What model did WRONG)

**Case: Meeting Reminders**
```
Model drew graph showing:
  config.py ─┐
  sheets.py ─┼─► "могут параллельно"  ← WROTE THIS!
  models.py ─┘

Model concluded: "Есть явная цепочка зависимостей"
Model chose: executing-plans  ← WRONG!
```

**Why wrong:**
- Model SAW parallel tasks but didn't CALCULATE potential
- Model focused on the sequential chain, ignored parallel branches
- No numeric calculation → wrong intuitive conclusion

**Correct calculation would show:**
- Wave 1: 3 tasks parallel
- Wave 4: 3 tasks parallel
- Parallelization potential: 75%
- Decision rule: 75% > 0% → tasks/*.md MANDATORY

---

## Red Flags - STOP AND RECALCULATE

**HARD VIOLATIONS (protocol violation):**
- Checkpoint missing wave structure
- Checkpoint missing parallelization calculation
- Parallelization potential > 0% but chose executing-plans
- Said "могут параллельно" anywhere but chose executing-plans

**SOFT WARNINGS (reconsider):**
- Wave structure says "N/A" for plan.md format
- Calculation skipped with excuse "obvious sequential"
- Focused on sequential chain, ignored parallel branches

**THE ANTI-PATTERN TO AVOID:**
```
❌ WRONG: "I see some tasks can be parallel, but there's a main chain,
          so I'll use executing-plans"

✅ RIGHT: "I calculated parallelization potential = X%.
          Since X% > 0%, I MUST use tasks/*.md"
```

**Rule is MECHANICAL, not intuitive:** If potential > 0%, decision is tasks/*.md. Period.

---

## Why This Works

1. **Output gate**: Checkpoint format is required, model must produce it
2. **Self-verification**: "Guide loaded: YES/NO" makes skipping visible
3. **Structured format**: YAML forces systematic thinking
4. **Evidence-based**: Must show waves, not just claim analysis
5. **User preference visibility**: Explicit field in checkpoint
