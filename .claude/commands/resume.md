---
allowed-tools:
  - Read
  - AskUserQuestion
---

# /resume - Resume Incomplete Work

Resume work from a previous session by checking STATE.md.

## What This Command Does

1. Reads `work/STATE.md` to find incomplete work
2. Displays a summary of where you left off
3. Asks whether to resume or start fresh
4. If resuming, loads context and continues

## Usage

```
/resume
```

## Process

### Step 1: Check for STATE.md

```bash
Read: work/STATE.md
```

If file doesn't exist:
```
"Нет незавершённой работы. STATE.md не найден.
Готов к новой задаче."
```

### Step 2: Parse STATE.md

Extract key sections (Russian headers):
- "Текущая работа" → task, phase, status
- "Следующие шаги" → next steps list
- "Блокеры" → active blockers
- "Session Notes" → last session date

### Step 3: Display Summary

Show user what was found:

```
📋 **Незавершённая работа**

**Фича:** {feature-name}
**Задача:** {current task}
**Фаза:** {phase}
**Статус:** {status}
**Последняя сессия:** {date}

**Следующие шаги:**
- {step 1}
- {step 2}

**Блокеры:**
- {blocker if any}
```

### Step 4: Ask User

Use AskUserQuestion:

```
"Продолжить с того места, где остановились?"

Options:
- Да, продолжить
- Нет, начать заново
- Показать детали
```

### Step 5: Handle Response

**If "Да, продолжить":**
1. Load context files for the feature
2. Read tech-spec.md and relevant tasks
3. Continue from current phase/status

**If "Нет, начать заново":**
1. Clear work/STATE.md (or archive it)
2. Ready for new task

**If "Показать детали":**
1. Display full STATE.md content
2. Ask again

## Example

```
User: /resume

Agent: Checking for incomplete work...

📋 **Незавершённая работа**

**Фича:** user-auth
**Задача:** Task 2: Create login endpoint
**Фаза:** implementation
**Статус:** in_progress
**Последняя сессия:** 2026-01-18

**Следующие шаги:**
- Finish JWT token generation
- Add password validation
- Write tests

Продолжить с того места, где остановились?

User: Да

Agent: Загружаю контекст...
[reads tech-spec.md, tasks/2.md]

Продолжаю работу над JWT token generation...
```

## Related

- `work/STATE.md` - Session state file
- CLAUDE.md "Session Start" section - Auto-resume behavior
- CLAUDE.md "State Management" section - Rules for STATE.md
