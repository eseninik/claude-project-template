# Project: [PROJECT NAME]

> **[ОДНО ПРЕДЛОЖЕНИЕ - О ЧЕМ ЭТОТ ПРОЕКТ]**

---

## Как работает этот проект

**Контекст:** `.claude/skills/project-knowledge/` — архитектура, паттерны, git workflow.

**Основная ветка:** `dev`

**Методология:** AI-First Development — spec-driven workflow с Just-In-Time context loading.

---

# CORE PRINCIPLES

## Hierarchy of Priorities

```
1. SAFETY      → Не навреди пользователю, проекту, данным
2. QUALITY     → Сделай правильно, не быстро
3. GUIDELINES  → Следуй методологии
4. HELPFULNESS → Будь максимально полезен
```

## Key Rules (запомни)

- **"Unhelpfulness is never trivially safe"** — отказ тоже имеет cost
- **"Diplomatically honest rather than dishonestly diplomatic"** — честность > вежливость
- **Epistemic cowardice = нарушение** — размытые ответы запрещены

---

# CONTEXT LOADING TRIGGERS

**Когда видишь ситуацию → загрузи guide. Это гарантирует что детали не потеряются.**

| Ситуация | Загрузить | Команда |
|----------|-----------|---------|
| Сложное решение, конфликт правил | decision-making | `cat .claude/guides/decision-making.md` |
| Произошла ошибка, что-то сломалось | error-handling | `cat .claude/guides/error-handling.md` |
| Нужно дать честную оценку | honesty-principles | `cat .claude/guides/honesty-principles.md` |
| Проверить что можно/нельзя | constraints-reference | `cat .claude/guides/constraints-reference.md` |

**Это ОБЯЗАТЕЛЬНО, не опционально.** Пропуск загрузки guide при matching ситуации = нарушение.

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

# GOAL-BACKWARD VERIFICATION

**Проверяй от цели, не от задач.**

```
1. Что должно быть ИСТИНОЙ? → Наблюдаемые поведения
2. Что должно СУЩЕСТВОВАТЬ? → Файлы, функции
3. Что должно быть СВЯЗАНО? → Импорты, вызовы
4. Проверь КАЖДЫЙ уровень
```

**Артефакт существует но не подключён = цель НЕ достигнута.**

---

# WORK ITEMS WORKFLOW

```
Context → User Spec → Tech Spec → Tasks → Code → UAT → Verification → Commit
```

**Для новой фичи:**
```
1. work/<feature-name>/
2. /new-user-spec → user-spec.md
3. /new-tech-spec → tech-spec.md + tasks/
4. Реализовать с skills
5. После деплоя → work/completed/
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

# REFERENCE

## Git Workflow

- `dev` — рабочая ветка
- `main` — продакшен, не трогать напрямую

```bash
git add <files> && git commit -m "type: desc" && git push origin dev
```

## Python (Windows)

```bash
py -3.12 -m pytest tests/ -v
py -3.12 -m ruff check src tests
```

---

# KEY SKILLS

| Категория | Skills |
|-----------|--------|
| Planning | `user-spec-planning`, `tech-spec-planning` |
| Execution | `subagent-driven-development`, `test-driven-development` |
| Quality | `verification-before-completion`, `systematic-debugging` |
| Security | `security-checklist`, `secret-scanner` |

---

# FORBIDDEN PATTERNS

- `@.claude/skills` — забивает контекст
- Epistemic cowardice — размытые ответы
- "Файлы пересекаются → последовательно" — использовать Worktree!
- "Готово" без verification
- План без `subagent-driven-development`
