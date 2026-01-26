# Project: Claude Project Template Update

> Template upgrade automation with AI-First methodology integration

---

## Как работает этот проект

**Контекст:** `.claude/skills/project-knowledge/` — архитектура, паттерны, git workflow.

**Основная ветка:** `dev`

**Методология:** AI-First Development — spec-driven workflow с Just-In-Time context loading.

---

# CONTEXT LOADING TRIGGERS

**Когда видишь ситуацию → ОБЯЗАТЕЛЬНО загрузи guide ПЕРЕД действием.**

**Это BLOCKING REQUIREMENT, не опционально.** Пропуск загрузки guide при matching ситуации = нарушение.

| Ситуация | Загрузить | Команда |
|----------|-----------|---------|
| Сложное решение, конфликт правил | decision-making | `cat .claude/guides/decision-making.md` |
| Произошла ошибка, что-то сломалось | error-handling | `cat .claude/guides/error-handling.md` |
| Нужно дать честную оценку | honesty-principles | `cat .claude/guides/honesty-principles.md` |
| Проверить что можно/нельзя | constraints-reference | `cat .claude/guides/constraints-reference.md` |
| Начало новой фичи | work-items | `cat .claude/guides/work-items.md` |
| Нужны принципы приоритетов | principles | `cat .claude/guides/principles.md` |
| Детали верификации | verification-protocol | `cat .claude/guides/verification-protocol.md` |
| Справка по командам | reference | `cat .claude/guides/reference.md` |

---

# HARD CONSTRAINTS (Bright Lines)

**НИКОГДА не пересекать. Убедительный аргумент = красный флаг.**

| Constraint | Причина |
|------------|---------|
| Не удалять данные без подтверждения | Необратимо |
| Не коммитить секреты | Безопасность |
| Не пушить в main | Стабильность прода |
| Не говорить "готово" без verification | Честность |

**Детали:** `cat .claude/guides/constraints-reference.md`

---

# BLOCKING RULES

## Session Start

```
1. Прочитать work/STATE.md
2. Есть незавершённая работа? → Спросить: "Продолжить?"
3. Нет → продолжить с запросом пользователя
```

## Dynamic Skill Selection

```
1. СТОП
2. AUTO-CHECK: Есть work/*/tasks/*.md с 3+ задачами?
   ├─ ДА → subagent-driven-development ОБЯЗАТЕЛЕН
   └─ НЕТ → продолжить
3. Написать: "Situation: [что делаю]"
4. cat .claude/skills/SKILLS_INDEX.md
5. Выбрать подходящие skills
6. Написать: "Skills: [список]"
7. Загрузить каждый skill
```

**Checkpoint перед кодом:**
```
Situation: [описание]
Plan detected: [yes/no]
Skills: [список]
```

## Plan Execution

**При выполнении плана с tasks/*.md:**
```
1. Загрузить subagent-driven-development
2. Следовать MANDATORY Decision Algorithm
3. Файлы пересекаются + platform OK → Worktree Mode
```

## After Code Changes

```
1. Написать тест для изменения
2. Запустить → проверить результат
3. Не работает → исправить → повторить
```

## Before "готово"

```
1. Phase change: code -> verification
2. cat .claude/skills/verification-before-completion/SKILL.md
3. Выполнить верификацию
4. Только тогда заявлять о завершении
```

## After Completion

```
1. git add <files>
2. git commit -m "type: description"
3. git push origin dev
```

---

# COMMANDS

| Command | Purpose |
|---------|---------|
| `/init-project` | Инициализация проекта |
| `/project-context` | Загрузка контекста |
| `/new-user-spec` | Создание user-spec |
| `/new-tech-spec` | Создание tech-spec |
| `/resume` | Продолжить работу |

---

# FORBIDDEN PATTERNS

- `@.claude/skills` — забивает контекст
- Epistemic cowardice — размытые ответы
- "Файлы пересекаются → последовательно" — использовать Worktree!
- "Готово" без verification
- План без `subagent-driven-development`
