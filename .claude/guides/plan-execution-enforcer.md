# Plan Execution Enforcer

**PURPOSE:** 100% enforcement of plan-execution-protocol with structured checkpoint.

**BLOCKING:** You CANNOT start implementation without outputting a valid checkpoint.

---

## Detection Triggers

This enforcer activates when ANY of these conditions are true:

1. Plan file mentioned (*.md in plans/ or work/)
2. Task with 3+ steps detected
3. User says "реализуй план" / "execute plan" / similar
4. Implementation task references multiple files

**IF triggered → MUST output checkpoint box BEFORE any Edit/Write/Bash commands**

---

## Mandatory Checkpoint Format

You MUST output this bordered box in the SAME message where you detect the plan:

```
═══════════════════════════════════════════════════════════════════════════════
PLAN EXECUTION CHECKPOINT (MANDATORY)
═══════════════════════════════════════════════════════════════════════════════

Guide loaded: [YES/NO]
Plan format: [tasks/*.md / plan.md / implicit / NONE]
Plan location: [path or "user message"]
Tasks count: [N]

Wave structure analysis:
  Wave 1: [task names] - [N] tasks
  Wave 2: [task names] - [N] tasks
  ...
  Total waves: [N]

Parallelization calculation:
  Tasks in parallel waves (waves with 2+ tasks): [N]
  Total tasks: [N]
  Formula: [N/N × 100]
  Parallelization potential: [X%]

Decision rule applied:
  Condition: PP > 0%? [YES/NO]
  IF YES → Decision: tasks/*.md + subagent-driven
  IF NO → Decision: sequential execution

Final decision: [tasks/*.md / sequential]
Skill to load: [subagent-driven-development / none]

Self-verification checklist:
  [x] Guide loaded (plan-execution-protocol.md)
  [x] Wave structure analyzed
  [x] Parallelization calculated
  [x] Decision rule applied mechanically
  [x] Checkpoint box output in THIS message

Checkpoint valid: [YES/NO]

═══════════════════════════════════════════════════════════════════════════════
```

---

## Validation Rules

**Checkpoint is INVALID if ANY of these are true:**

1. `Guide loaded: NO`
2. Wave structure missing or says "N/A" (for plan.md/implicit formats)
3. Parallelization calculation missing
4. Decision contradicts rule (PP > 0% but chose sequential execution)
5. Self-verification checklist has unchecked items
6. `Checkpoint valid: NO`
7. Checkpoint appears in DIFFERENT message than plan detection

**IF checkpoint is INVALID → DO NOT proceed with implementation**

---

## Enforcement Mechanisms

### Level 1: BLOCKING RULE in CLAUDE.md
- Psychological trigger from "BLOCKING" keyword
- Explicit prohibition: "Cannot start without..."

### Level 2: Mandatory Output Format
- Bordered YAML box is visually distinctive
- Missing box = obvious violation
- Easy to verify compliance by scanning output

### Level 3: Structured Decision Rule
- Mechanical, not intuitive
- Formula-based: PP = (tasks in waves with 2+ tasks) / total × 100%
- Binary decision: PP > 0% → tasks/*.md, PP = 0% → sequential execution

### Level 4: Self-Verification Checklist
- Agent checks own work before proceeding
- Unchecked items = invalid checkpoint

---

## Decision Rule (MECHANICAL - NO EXCEPTIONS)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DECISION RULE                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   1. Calculate Parallelization Potential (PP)                                │
│      PP = (tasks in waves with 2+ tasks) / total tasks × 100%               │
│                                                                              │
│   2. Apply Rule:                                                             │
│                                                                              │
│      IF PP > 0%  →  tasks/*.md + subagent-driven-development                │
│      IF PP = 0%  →  sequential execution                                    │
│                                                                              │
│   3. NO EXCEPTIONS. NO INTUITION. JUST MATH.                                │
│                                                                              │
│   User preference is "speed" → always take parallel opportunity              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Red Flags - Violation Indicators

### How to detect violations:

1. **Checkpoint box absent** - Most obvious violation
2. **Incomplete checkpoint** - TBD, N/A, or blank fields without justification
3. **Intuitive reasoning** - "seems sequential", "looks like a chain"
4. **Checkpoint in wrong message** - Must be in SAME message as plan detection
5. **Calculation skipped** - "obvious" or "clearly" without numbers

### The Anti-Pattern to Avoid:

```
❌ WRONG: "I see some tasks can be parallel, but there's a main chain,
          so I'll use sequential execution"

✅ RIGHT: "I calculated parallelization potential = X%.
          Since X% > 0%, I MUST use tasks/*.md"
```

---

## Examples

### Example 1: Valid Checkpoint (PP = 83%)

```
═══════════════════════════════════════════════════════════════════════════════
PLAN EXECUTION CHECKPOINT (MANDATORY)
═══════════════════════════════════════════════════════════════════════════════

Guide loaded: YES
Plan format: plan.md
Plan location: work/race-condition-fix/plan.md
Tasks count: 6

Wave structure analysis:
  Wave 1: [constructor, import] - 2 tasks
  Wave 2: [success, failure, pending handlers] - 3 tasks
  Wave 3: [main.py integration] - 1 task
  Total waves: 3

Parallelization calculation:
  Tasks in parallel waves (waves with 2+ tasks): 5 (Wave 1: 2, Wave 2: 3)
  Total tasks: 6
  Formula: 5/6 × 100
  Parallelization potential: 83%

Decision rule applied:
  Condition: PP > 0%? YES (83% > 0%)
  IF YES → Decision: tasks/*.md + subagent-driven

Final decision: tasks/*.md
Skill to load: subagent-driven-development

Self-verification checklist:
  [x] Guide loaded (plan-execution-protocol.md)
  [x] Wave structure analyzed
  [x] Parallelization calculated
  [x] Decision rule applied mechanically
  [x] Checkpoint box output in THIS message

Checkpoint valid: YES

═══════════════════════════════════════════════════════════════════════════════
```

### Example 2: Valid Checkpoint (PP = 0%)

```
═══════════════════════════════════════════════════════════════════════════════
PLAN EXECUTION CHECKPOINT (MANDATORY)
═══════════════════════════════════════════════════════════════════════════════

Guide loaded: YES
Plan format: plan.md
Plan location: work/migration/plan.md
Tasks count: 5

Wave structure analysis:
  Wave 1: [design-schema] - 1 task
  Wave 2: [create-migration] - 1 task
  Wave 3: [implement-models] - 1 task
  Wave 4: [build-api] - 1 task
  Wave 5: [add-frontend] - 1 task
  Total waves: 5

Parallelization calculation:
  Tasks in parallel waves (waves with 2+ tasks): 0
  Total tasks: 5
  Formula: 0/5 × 100
  Parallelization potential: 0%

Decision rule applied:
  Condition: PP > 0%? NO (0% = 0%)
  IF NO → Decision: sequential execution

Final decision: sequential execution
Skill to load: sequential execution

Self-verification checklist:
  [x] Guide loaded (plan-execution-protocol.md)
  [x] Wave structure analyzed
  [x] Parallelization calculated
  [x] Decision rule applied mechanically
  [x] Checkpoint box output in THIS message

Checkpoint valid: YES

═══════════════════════════════════════════════════════════════════════════════
```

### Example 3: INVALID Checkpoint (missing calculation)

```
═══════════════════════════════════════════════════════════════════════════════
PLAN EXECUTION CHECKPOINT (MANDATORY)
═══════════════════════════════════════════════════════════════════════════════

Guide loaded: YES
Plan format: plan.md
Plan location: ~/.claude/plans/example.md
Tasks count: 8

Wave structure analysis:
  N/A - will analyze during implementation    ← INVALID

Parallelization calculation:
  Skipped - obvious sequential chain          ← INVALID

Decision rule applied:
  Sequential plan → sequential execution           ← INVALID (no calculation)

Final decision: sequential execution
Skill to load: sequential execution

Self-verification checklist:
  [x] Guide loaded (plan-execution-protocol.md)
  [ ] Wave structure analyzed                 ← UNCHECKED
  [ ] Parallelization calculated              ← UNCHECKED
  [ ] Decision rule applied mechanically      ← UNCHECKED
  [x] Checkpoint box output in THIS message

Checkpoint valid: NO                          ← MUST NOT PROCEED

═══════════════════════════════════════════════════════════════════════════════
```

**Why this is invalid:** Missing wave structure, missing calculation, intuitive reasoning instead of formula.

---

## Why This Works

1. **Structured format** - Can't skip steps without visible gaps
2. **Bordered box** - Visually distinctive, easy to verify presence
3. **Self-verification** - Agent checks own work systematically
4. **Mechanical calculation** - No room for intuition to override
5. **Evidence-based** - Must show waves and numbers, not just claims
6. **Same-message requirement** - Prevents "I'll do it later" pattern

---

## Escalation Path

If enforcement still fails after implementing this guide:

1. **Verify checkpoint presence** - Is bordered box in output?
2. **Verify completion** - All checklist items checked?
3. **Add pre-edit hook** - Automated detection before Edit/Write tools
4. **If all fail** - System design problem, not enforcement problem
