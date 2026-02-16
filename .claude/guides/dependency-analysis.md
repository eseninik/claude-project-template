# Dependency Analysis Guide

> **Loaded from:** plan-execution-protocol.md (STEP 2 of Gate Function)

**This guide provides the Decision Algorithm for plan analysis.**
**Do not use directly - always load via plan-execution-protocol.md**

---

## Purpose

Determine if tasks in a plan are independent (can run in parallel) or dependent (must run sequentially).

**IMPORTANT:** This guide is loaded automatically when analyzing plans in formats other than tasks/*.md.

---

## Decision Algorithm

### Step 1: Determine Independence for Each Pair

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

### Step 2: Build Wave Structure

```python
def build_waves(tasks, dependencies):
    """
    Построение волновой структуры для определения возможности параллелизации
    """
    waves = []
    remaining_tasks = set(tasks)
    completed_tasks = set()

    while remaining_tasks:
        # Wave: задачи, у которых все зависимости выполнены
        current_wave = []

        for task in remaining_tasks:
            task_deps = dependencies.get(task, [])
            if all(dep in completed_tasks for dep in task_deps):
                current_wave.append(task)

        if not current_wave:
            # Circular dependency detected
            raise Exception("Circular dependency detected")

        waves.append(current_wave)
        remaining_tasks -= set(current_wave)
        completed_tasks |= set(current_wave)

    return waves
```

### Step 3: Choose Execution Strategy

```python
def choose_strategy(waves, user_preference):
    """
    Выбор стратегии выполнения на основе волновой структуры
    """
    # Подсчет параллелизма
    parallel_potential = sum(len(wave) > 1 for wave in waves)
    total_parallel_tasks = sum(len(wave) for wave in waves if len(wave) > 1)

    # Волновая структура (есть параллелизм)?
    if parallel_potential > 0:
        # tasks/*.md - волновая параллелизация
        return {
            "strategy": "tasks_md",
            "reason": f"Wave structure with {parallel_potential} parallel waves, {total_parallel_tasks} tasks can run in parallel",
            "waves": waves
        }

    # Строгая последовательность (каждая волна = 1 задача)
    if all(len(wave) == 1 for wave in waves):
        # executing-plans - последовательное выполнение
        return {
            "strategy": "executing_plans",
            "reason": "Strict sequential chain, no parallelization possible",
            "waves": waves
        }
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

### Example 2: Wave Structure (90% confidence) - OPTIMAL

**Plan:**
```
1. Create Config (config.py) - no deps
2. Create Client extension (client.py) - no deps
3. DR Service (dr_notifications.py) - depends on 1 (uses settings.dr_enabled)
4. Webhook integration (webhook.py) - depends on 1, 2, 3 (uses config, calls client, uses _dr_service)
5. Main init (main.py) - depends on 3 (imports DRStatusNotificationService)
6. .env setup - can start anytime
```

**Analysis:**
- Tasks 1, 2: Different files → INDEPENDENT
- Task 3: Depends on 1
- Tasks 4, 5: Depend on earlier tasks
- Task 6: Independent (configuration)

**Wave Structure:**
```
Wave 1: [1, 2] - parallel (2 tasks)
Wave 2: [3] - after 1
Wave 3: [4, 5] - after 1, 2, 3 (2 tasks parallel)
Wave 4: [6] - configuration
```

**Parallelization potential:** 4 out of 6 tasks can run in parallel waves
**Decision:** tasks/*.md + subagent-driven-development (wave parallelization)
**Time savings:** ~50% (instead of 6 sequential steps, run in 4 waves with 2 parallel tasks in 2 waves)

---

### Example 3: Strict Sequential Chain (90% confidence)

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
- Task 2 depends on 1
- Task 3 depends on 2
- Task 4 depends on 3
- Task 5 depends on 4

**Wave Structure:**
```
Wave 1: [1]
Wave 2: [2]
Wave 3: [3]
Wave 4: [4]
Wave 5: [5]
```

**Parallelization potential:** 0 (each wave has 1 task)
**Decision:** executing-plans (sequential with checkpoints)
**Reason:** No benefit from tasks/*.md structure, better to use batch review approach

---

### Example 4: Mixed (needs clarification)

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

## Wave Parallelization vs Sequential Execution

### When to Choose tasks/*.md (Wave Parallelization)

✅ **ANY of these conditions:**
1. At least one wave has 2+ tasks (can run in parallel)
2. Total waves < total tasks (some parallelization exists)
3. User preference = "speed and parallelism"

**Benefits:**
- Tasks in same wave run simultaneously
- Significant time savings
- Automatic merge handling via Worktree Mode
- Review happens naturally between waves

**Example:**
```
6 tasks → 4 waves with parallel tasks in Wave 1 and Wave 3
Time: ~4 wave cycles instead of 6 sequential steps
Savings: ~33%
```

### When to Choose executing-plans (Sequential Batches)

✅ **ONLY when ALL these conditions:**
1. Every wave has exactly 1 task (no parallelization possible)
2. Strict sequential chain: Task N depends on Task N-1
3. No benefit from wave structure

**Example:**
```
5 tasks → 5 waves, each with 1 task
Time: Same as sequential (no parallelization)
Better: Batch review approach (executing-plans)
```

### Decision Matrix

```
Waves structure analysis:
├─ Has waves with 2+ tasks?
│  ├─ YES → tasks/*.md (wave parallelization)
│  └─ NO → Check if all waves = 1 task
│     ├─ YES → executing-plans (strict sequential)
│     └─ NO → tasks/*.md (safer choice)
```

**IMPORTANT:** When user preference = "speed and parallelism", ALWAYS prefer tasks/*.md unless strictly impossible (every wave = 1 task).

---

## Red Flags (Never Do This)

❌ **Don't decide based on plan format**
```
BAD: "Plan has detailed steps → executing-plans"
GOOD: "Tasks have dependencies → check wave structure"
```

❌ **Don't assume parallelism without analysis**
```
BAD: "6 tasks → must be parallel"
GOOD: "6 tasks, checked dependencies → 4 parallel in waves + 2 sequential"
```

❌ **Don't ignore explicit dependency keywords**
```
Task 2: "Using results from Task 1"
BAD: "Different files → parallel"
GOOD: "Explicit dependency → build waves, check for parallel opportunities"
```

❌ **Don't choose executing-plans when wave parallelization is possible**
```
BAD: "Has dependencies → executing-plans"
GOOD: "Wave 1: [1,2] parallel, Wave 2: [3] → tasks/*.md for wave parallelization"
```

❌ **Don't miss parallelization opportunities**
```
BAD: "Task 3 depends on 1, Task 4 depends on 2 → sequential"
GOOD: "Wave 1: [1,2] parallel, Wave 2: [3,4] parallel → tasks/*.md"
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
