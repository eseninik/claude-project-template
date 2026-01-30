# Project: Claude Project Template Update

> Template upgrade automation with AI-First methodology integration

---

## Как работает этот проект

**Контекст:** `.claude/skills/project-knowledge/` — архитектура, паттерны, git workflow.

**Memory:** `.claude/memory/activeContext.md` — мост между сессиями, решения, паттерны.

**ADR:** `.claude/adr/` — архитектурные решения проекта.

**Основная ветка:** `dev`

**User preference:** Приоритет на скорость и параллелизм.

---

# AUTO-BEHAVIORS

> Агент выполняет автоматически, БЕЗ команд пользователя.

---

## SESSION START (always)

```
1. Read .claude/memory/activeContext.md
2. Read work/STATE.md
3. IF unfinished work exists:
   → Tell user: "Продолжаю: [task]. Контекст: [recent decisions]"
4. ELSE:
   → Tell user: "Готов к новой задаче"
```

---

## BEFORE CODE CHANGES (always)

```
1. Read .claude/skills/project-knowledge/guides/architecture.md
2. Read .claude/skills/project-knowledge/guides/patterns.md
3. Check .claude/adr/decisions.md for relevant decisions
```

---

## AFTER TASK COMPLETION (always)

```
1. Update .claude/memory/activeContext.md:
   - Session Log: date, what did, what decided, what learned
   - Recent Decisions if any
   - Learned Patterns if discovered something
   - Next Steps

2. Update work/STATE.md

3. IF architectural decision → Create ADR

4. Commit with meaningful message
```

---

## ON ARCHITECTURE DECISION (always)

```
1. Check .claude/adr/decisions.md for existing decisions
2. IF contradicts existing → Explain why change is needed
3. Create new ADR using .claude/adr/_template.md
4. Update .claude/adr/decisions.md INDEX
```

---

# CONTEXT LOADING TRIGGERS

**Когда видишь ситуацию → ОБЯЗАТЕЛЬНО загрузи guide ПЕРЕД действием.**

| Ситуация | Загрузить | Команда |
|----------|-----------|---------|
| Сложное решение, конфликт правил | decision-making | `cat .claude/guides/decision-making.md` |
| Произошла ошибка, что-то сломалось | error-handling | `cat .claude/guides/error-handling.md` |
| Нужно дать честную оценку | honesty-principles | `cat .claude/guides/honesty-principles.md` |
| Проверить что можно/нельзя | constraints-reference | `cat .claude/guides/constraints-reference.md` |
| Начало новой фичи | work-items | `cat .claude/guides/work-items.md` |
| Детали верификации | verification-protocol | `cat .claude/guides/verification-protocol.md` |
| Анализ плана | dependency-analysis | `cat .claude/guides/dependency-analysis.md` |
| **План для реализации** | **plan-execution-protocol** | `cat .claude/guides/plan-execution-protocol.md` |

---

# HARD CONSTRAINTS

| Constraint | Причина |
|------------|---------|
| Не удалять данные без подтверждения | Необратимо |
| Не коммитить секреты | Безопасность |
| Не пушить в main | Стабильность прода |
| Не говорить "готово" без verification | Честность |
| Не выбирать executing-plans без wave analysis | Потеря скорости |
| **Всегда обновлять memory после работы** | **Сохранение контекста** |
| Не коммитить без обновления памяти | Потеря контекста между сессиями |

---

# BLOCKING RULES

## Plan Detected (BLOCKING)

ENFORCE VIA: `cat .claude/guides/plan-execution-enforcer.md`
BLOCK: Cannot start implementation without valid checkpoint output

## After Code Changes

```
1. Написать тест для изменения
2. Запустить → проверить результат
3. Не работает → исправить → повторить
```

## Before Commit (BLOCKING)

```
TRIGGER: About to run git commit

BLOCK: Do NOT commit until memory is updated

1. VERIFY activeContext.md is staged (git status)
2. IF not staged:
   a. Update .claude/memory/activeContext.md with:
      - Did: конкретные изменения
      - Decided: выбор и обоснование
      - Learned: gotchas, что работает/не работает
      - Next: что осталось
   b. Stage: git add .claude/memory/activeContext.md
3. THEN proceed with commit
```

## Before "готово"

```
1. Phase change: code -> verification
2. cat .claude/skills/verification-before-completion/SKILL.md
3. Выполнить верификацию
4. Только тогда заявлять о завершении
```

---

# KNOWLEDGE LOCATIONS

| Need | Location |
|------|----------|
| Session context | `.claude/memory/activeContext.md` |
| Task state | `work/STATE.md` |
| Architecture decisions | `.claude/adr/decisions.md` |
| Project architecture | `.claude/skills/project-knowledge/guides/` |

---

# FORBIDDEN

- Starting work without reading memory/activeContext.md
- Finishing work without updating memory
- Making architecture decisions without checking ADR
- Saying "done" without running tests
- `@.claude/skills` — забивает контекст
- Plan detected → starting without plan-execution-protocol.md
