# Project: Claude Project Template Update

> Template upgrade automation with AI-First methodology integration

---

## Как работает этот проект

**Контекст:** `.claude/skills/project-knowledge/` — архитектура, паттерны, git workflow.

**Основная ветка:** `dev`

**Методология:** AI-First Development — spec-driven workflow с Just-In-Time context loading.

**User preference:** Приоритет на скорость и параллелизм — при выборе подхода всегда предпочитать параллельное выполнение, если задачи независимы.

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
| Анализ плана (вариант B AUTO-CHECK) | dependency-analysis | `cat .claude/guides/dependency-analysis.md` |

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
2. AUTO-CHECK: Есть чёткий план для реализации?

   A. План в формате work/*/tasks/*.md с 3+ задачами?
      └─ ДА → subagent-driven-development ОБЯЗАТЕЛЕН

   B. План в другом формате (plan.md, IMPLEMENTATION_PROMPT.md)?
      └─ ДА → АНАЛИЗ ЗАВИСИМОСТЕЙ:
         0. cat .claude/guides/dependency-analysis.md  # ОБЯЗАТЕЛЬНО загрузить алгоритм
         1. Прочитать план
         2. Определить задачи и их scope (какие файлы трогают)
         3. Для каждой пары задач проверить:
            - Трогают разные файлы? → скорее независимые
            - Одна использует результат другой? → зависимые
            - Есть явные слова зависимости ("на основе", "используя", "после того как")? → зависимые
            - Можно начать параллельно? → независимые

         4. Принять решение:

            a) ВСЕ задачи независимые (>80% уверенность):
               → РЕШЕНИЕ: Создать tasks/*.md + subagent-driven-development
               → СООБЩИТЬ: "Анализ: [N] задач независимые (разные файлы/компоненты).
                           Создаю tasks/*.md для параллельного выполнения."
               → ДЕЙСТВИЕ: Создать структуру tasks/*.md с метаданными depends_on/files_modified

            b) ЕСТЬ зависимости (chains, последовательность):
               → РЕШЕНИЕ: executing-plans
               → СООБЩИТЬ: "Анализ: задачи имеют зависимости [перечислить].
                           Использую executing-plans для контролируемого последовательного выполнения."
               → ДЕЙСТВИЕ: Загрузить executing-plans skill

            c) НЕЯСНО - недостаточно информации для уверенного решения:
               → СПРОСИТЬ пользователя:
                  "Анализ плана ([N] задач):

                   Вопрос: [конкретный вопрос о зависимости между задачами X и Y]

                   Варианты:
                   1. Задачи независимы → создам tasks/*.md (параллельно, быстрее)
                   2. Есть зависимости → executing-plans (последовательно с контрольными точками)

                   Уточните зависимости или выберите подход."

         **User preference учитывается:** Если пользователь предпочитает скорость и параллелизм,
         при уверенности >70% выбирать вариант (a).

   C. Контекстный анализ задачи (нет явного плана)
      1. cat .claude/skills/task-decomposition/SKILL.md
      2. Применить процесс анализа:
         - Парсинг описания задачи
         - Поиск паттернов в .claude/knowledge/parallelization-patterns.md
         - Определение подзадач и зависимостей
         - Построение waves
         - Оценка уверенности
      3. IF 3+ подзадачи AND уверенность > 60%:
         └─ ПРЕДЛОЖИТЬ пользователю:
            "Варианты:
             1. Создать tasks/*.md и выполнить параллельно
             2. Работать последовательно
             3. Уточнить детали для точного плана"
      4. ELSE:
         └─ продолжить обычным workflow

3. Написать: "Situation: [что делаю]"
4. cat .claude/skills/SKILLS_INDEX.md
5. Выбрать подходящие skills
6. Написать: "Skills: [список]"
7. Загрузить каждый skill
```

**Checkpoint перед кодом:**
```
Situation: [описание]
Plan format: [tasks/*.md / plan.md / implicit / none]
Plan tasks count: [N]
Parallelization analysis: [detected / not applicable / uncertain]
  If detected:
    - Subtasks: [список подзадач]
    - Waves: [Wave 1: [...], Wave 2: [...]]
    - Confidence: [high / medium / low]
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
- План с tasks/*.md без `subagent-driven-development`
- Игнорирование плана в другом формате — предложить варианты
