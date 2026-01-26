# Dependency Analysis Guide

## Purpose

Determine if tasks in a plan are independent (can run in parallel) or dependent (must run sequentially).

**IMPORTANT:** This guide is loaded automatically when analyzing plans in formats other than tasks/*.md.

---

## Decision Algorithm

```
FOR each pair of tasks (A, B):
    IF same_files(A, B):
        IF different_scope(A, B):  # Different functions/classes in same file
            RETURN "INDEPENDENT - Worktree Mode possible"
        ELSE:
            RETURN "DEPENDENT - Cannot modify same code simultaneously"

    IF explicit_dependency_keywords(A, B):
        # Keywords: "на основе", "используя результат", "после того как", "depends on"
        RETURN "DEPENDENT"

    IF different_files(A, B) AND no_data_flow(A, B):
        RETURN "INDEPENDENT"

    IF uncertain():
        RETURN "UNCERTAIN"
```

---

## Independence Indicators (Green Flags)

✅ **Different files**
```
Task A: models/notification.py
Task B: api/notifications.py
→ INDEPENDENT (even if B imports A later, they can be written in parallel)
```

✅ **Different components**
```
Task A: Email service
Task B: Push notification service
→ INDEPENDENT (separate subsystems)
```

✅ **Same category, different entities**
```
Task A: User model
Task B: Order model
→ INDEPENDENT
```

✅ **Can start without waiting**
```
If Task B can start coding before Task A finishes → INDEPENDENT
```

---

## Dependency Indicators (Red Flags)

🚫 **Explicit dependency keywords**
```
"используя результат Task 1"
"на основе Task 2"
"после выполнения Task 3"
"depends on Task 4"
→ DEPENDENT
```

🚫 **Sequential requirements**
```
Task A: Database migration
Task B: Use new table from migration
→ DEPENDENT (B needs A's schema changes)
```

🚫 **Data flow**
```
Task A: Generate API client
Task B: Use generated client
→ DEPENDENT (B needs A's output)
```

🚫 **Same code location**
```
Task A: Add function X to utils.py:50-70
Task B: Modify function Y in utils.py:80-100
→ Check if they're truly independent or will conflict
```

---

## Uncertainty Cases

⚠️ **Same file, unclear scope**
```
Task A: Update auth.py
Task B: Refactor auth.py
→ UNCERTAIN - Need clarification: Do they touch same functions?
```

⚠️ **Vague descriptions**
```
Task A: "Improve performance"
Task B: "Add caching"
→ UNCERTAIN - Are these separate or is B part of A?
```

⚠️ **Implicit dependencies**
```
Task A: User registration
Task B: Email verification
→ Seems dependent, but can be coded in parallel if interface is clear
```

---

## Confidence Levels

### >80% - High Confidence
- Different files explicitly stated
- Different components/modules
- No dependency keywords
- **ACTION:** Decide automatically → tasks/*.md (parallel)

### 60-80% - Medium Confidence
- Likely independent but some ambiguity
- Same broad area but different specifics
- **ACTION:** Decide with note → "Assuming independence based on [reason]"

### <60% - Low Confidence
- Same files without clear scope
- Vague task descriptions
- Possible implicit dependencies
- **ACTION:** Ask user for clarification

---

## Examples

### Example 1: Clear Independence (95% confidence)

**Plan:**
```
1. Create Notification model (models/notification.py)
2. Add API endpoints (api/notifications.py)
3. Implement email service (services/email.py)
4. Add push notification (services/push.py)
5. Create webhook handler (webhooks/notifications.py)
6. Write tests (tests/test_notifications.py)
```

**Analysis:**
- Tasks 1-5: Different files → INDEPENDENT
- Task 6: Needs 1-5 completed → DEPENDENT

**Waves:**
- Wave 1: [1, 2, 3, 4, 5] - parallel
- Wave 2: [6] - after all

**Decision:** tasks/*.md + subagent-driven-development

---

### Example 2: Clear Dependencies (90% confidence)

**Plan:**
```
1. Design database schema
2. Create migration using schema from step 1
3. Implement models based on migration
4. Build API using models
5. Add frontend using API
```

**Analysis:**
- Each step uses output of previous → DEPENDENT chain

**Decision:** executing-plans (sequential with checkpoints)

---

### Example 3: Mixed (needs clarification)

**Plan:**
```
1. Add logging to auth.py
2. Refactor error handling in auth.py
3. Update tests
```

**Analysis:**
- Tasks 1-2: Same file, unclear if they touch same functions → UNCERTAIN
- Task 3: Depends on 1-2 → DEPENDENT

**Question to user:**
```
"Анализ плана:
 - Задачи 1 и 2 обе работают с auth.py
 - Вопрос: Они модифицируют разные функции (можно параллельно)
   или пересекающийся код (нужно последовательно)?

 Варианты:
 1. Разные функции → tasks/*.md (параллельно с Worktree Mode)
 2. Пересекается → executing-plans (последовательно)

 Уточните?"
```

---

## User Preference Integration

**When user preference = "speed and parallelism":**

```
IF confidence >= 70% that tasks are independent:
    → Choose tasks/*.md (parallel execution)
    → Risk: Small chance of conflicts
    → Benefit: Significant speed gain

IF confidence < 70%:
    → Ask user (don't assume)
```

**Default (no preference):**

```
IF confidence >= 85%:
    → Decide automatically

IF confidence < 85%:
    → Ask user
```

---

## Integration with AUTO-CHECK

**When loaded (variant B):**

```bash
# 1. Load this guide
cat .claude/guides/dependency-analysis.md

# 2. Read plan
cat work/{feature}/plan.md

# 3. Apply algorithm
# 4. Make decision or ask question
# 5. Proceed with chosen approach
```

---

## Red Flags (Never Do This)

❌ **Don't decide based on plan format**
```
BAD: "Plan has detailed steps → executing-plans"
GOOD: "Tasks have dependencies → executing-plans"
```

❌ **Don't assume parallelism without analysis**
```
BAD: "6 tasks → must be parallel"
GOOD: "6 tasks, checked dependencies → 4 parallel + 2 sequential"
```

❌ **Don't ignore explicit dependency keywords**
```
Task 2: "Using results from Task 1"
BAD: "Different files → parallel"
GOOD: "Explicit dependency → sequential"
```

---

## Success Metrics

**After applying this guide, agent should:**

1. ✅ Make correct independence assessment >90% of time
2. ✅ Only ask user when genuinely uncertain (<70% confidence)
3. ✅ Prefer parallel execution when user wants speed
4. ✅ Never create conflicts by parallelizing dependent tasks

---

## Evolution

This guide will improve based on:
- Feedback from actual plan analyses
- New dependency patterns discovered
- Domain-specific rules (e.g., Telegram bots, migrations, etc.)
