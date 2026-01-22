# Project: [PROJECT NAME]

> **[ОДНО ПРЕДЛОЖЕНИЕ - О ЧЕМ ЭТОТ ПРОЕКТ]**

---

## Как работает этот проект

**Контекст:** Все знания о проекте в `.claude/skills/project-knowledge/` - guides по архитектуре, паттернам, git workflow, UX, базе данных и деплою.

**Основная ветка:** `dev`

**Методология:** AI-First Development — spec-driven workflow с Just-In-Time context loading.

---

# STOP! BLOCKING RULES

**Эти правила НЕЛЬЗЯ обойти. Нарушение = провал задачи.**

## Session Start (BLOCKING)

**При КАЖДОМ начале сессии (первое сообщение):**

1. Прочитать `work/STATE.md`
2. Если есть незавершённая работа (status != completed):
   ```
   Незавершённая работа:
   - Task: [название из Current Work]
   - Status: [статус]
   - Last session: [дата из Session Notes]

   Продолжить? (да/нет/показать детали)
   ```
3. Если нет незавершённой работы → продолжить с запросом пользователя

**Это правило для агента, НЕ hooks.**

---

## State Management (BLOCKING)

### Before starting work:
1. Check if `work/STATE.md` exists
2. If exists: Read it
3. Write: `"Resuming: [task] from [date]"` (или `"Starting fresh"` если пусто)
4. Check blockers and previous decisions

### After finishing work (or session end):
1. Update `work/STATE.md`:
   - Current Work section (phase, task, status)
   - Session Notes with today's date
   - Next Steps
2. If made decisions → add to Key Decisions table
3. If found blockers → add to Blockers section

**Без обновления STATE.md сессия НЕ ЗАВЕРШЕНА.**

---

## Dynamic Skill Selection

### Когда переоценивать skills:
- В НАЧАЛЕ работы над задачей
- При СМЕНЕ фаз (research -> code -> tests -> completion)
- Когда СИТУАЦИЯ ИЗМЕНИЛАСЬ (нашел другую проблему, подход изменился)

### Алгоритм (ОБЯЗАТЕЛЬНЫЙ):

```
1. СТОП
2. Написать пользователю: "Situation: [что я делаю сейчас]"
3. cat .claude/skills/SKILLS_INDEX.md
4. Проанализировать ВСЕ skills - какие подходят для текущей ситуации?
5. Написать пользователю: "Skills: [список с кратким обоснованием]"
6. Загрузить КАЖДЫЙ: cat .claude/skills/<name>/SKILL.md
7. Следовать загруженным skills
```

### Checkpoint (БЛОКИРУЮЩИЙ):

**Я НЕ МОГУ писать/менять код без этого сообщения:**
```
Situation: [описание текущей фазы]
Skills: [skill1] (причина), [skill2] (причина)
```

Это сообщение = доказательство что я проанализировал и выбрал.
**Без этого сообщения писать код ЗАПРЕЩЕНО.**

### Переключение между skills:

Когда ситуация меняется:
```
1. Написать: "Phase change: [было] -> [стало]"
2. Повторить алгоритм выбора
3. Старые skills "выгружаются", работаю с новыми
```

---

## Plan Execution (BLOCKING)

**При выполнении плана с tasks/*.md ОБЯЗАТЕЛЬНО:**

```
1. Загрузить subagent-driven-development skill
2. Следовать MANDATORY Decision Algorithm из skill
3. Если файлы пересекаются + platform check passes → Worktree Mode
```

**Это НЕ опционально.** Пропуск subagent-driven-development при выполнении плана = нарушение.

---

## Autowork Mode (Автоматический режим)

**Trigger:** Сообщение начинается с "autowork:" или "ulw:"

**Пример:** "autowork: добавить авторизацию пользователей"

### Автоматический Pipeline

1. **Intent Classification** (orchestrator)
   - Определить тип задачи (feature/bug/refactoring)
   - Выбрать подходящие skills автоматически
   - Проверить наличие prerequisite артефактов

2. **Spec Generation** (если нужно)
   - user-spec-planning → tech-spec-planning
   - Ждать approval пользователя на каждом этапе

3. **Execution** (subagent-driven-development)
   - Wave parallelization для независимых задач
   - Code review после каждой задачи
   - Progress tracking в background-tasks.json

4. **Quality Gates** (BLOCKING!)
   - user-acceptance-testing → получить подтверждение пользователя
   - verification-before-completion → собрать evidence

5. **Completion** (auto-commit если всё прошло)
   - Коммит изменений
   - Обновление STATE.md

### Intervention Points

Пользователь может вмешаться на любом checkpoint:
- После intent classification
- После spec generation
- После каждой wave выполнения
- На UAT
- Перед commit

### Fallback

Если autowork не справляется → переключается на manual skill selection.

---

## После КАЖДОГО изменения кода

```
1. Написать тест/скрипт для ЭТОГО изменения
2. Запустить -> собрать логи
3. Сравнить результат с требованиями (запрос пользователя / tasks.md / user-spec.md)
4. Не совпадает? -> Исправить -> Повторить
```

**Без теста изменение НЕ ЗАВЕРШЕНО.**

## После реализации фичи - UAT (BLOCKING)

**Я НЕ МОГУ сказать "готово" без UAT подтверждения от пользователя.**

**Scope:**
- **Фичи (features)** — UAT ОБЯЗАТЕЛЕН, проверка с пользователем
- **Bug fixes** — UAT НЕ требуется, достаточно verification-before-completion
- **Refactoring** — UAT НЕ требуется, достаточно verification + tests pass

```
1. Написать: "Phase change: implementation -> UAT"
2. cat .claude/skills/user-acceptance-testing/SKILL.md
3. Сгенерировать UAT сценарии из user-spec.md:
   - Секция "Как должно работать"
   - Секция "Критерии готовности"
   - Секция "Сценарии использования"
4. Представить пользователю чеклист для проверки
5. Получить ответ: "UAT прошёл" или список проблем
6. Есть проблемы? → Исправить → Повторить UAT
7. Прошёл? → Переходить к verification-before-completion
```

**Без UAT подтверждения фича НЕ ЗАВЕРШЕНА.**

## Управление размером контекста (BLOCKING)

**Качество деградирует при заполнении контекста:**
- 0-30%: Пиковое качество
- 30-50%: Хорошее качество
- 50-70%: Деградация
- 70%+: Низкое качество

**Правила:**
1. Один план: максимум 3 задачи
2. Контекст > 50%: запустить субагента или разбить задачу
3. Свежий контекст для сложных задач
4. Не накапливать контекст - использовать STATE.md для persistence

## Проверка от цели - Goal-backward Verification (BLOCKING)

**Проверяй от цели, а не от задач. Завершение задачи ≠ Достижение цели.**

```
1. Что должно быть ИСТИНОЙ для достижения цели?
   → Список наблюдаемых поведений (user can X, system does Y)

2. Что должно СУЩЕСТВОВАТЬ для этих истин?
   → Конкретные файлы, функции, endpoints

3. Что должно быть СВЯЗАНО для работы артефактов?
   → Импорты, вызовы, подключения к БД

4. Проверь КАЖДЫЙ уровень:
   - Артефакт СУЩЕСТВУЕТ? (файл есть)
   - Артефакт СОДЕРЖАТЕЛЬНЫЙ? (не заглушка, >15 строк для компонента)
   - Артефакт ПОДКЛЮЧЁН? (импортирован И используется)
```

**Если артефакт существует но не подключён = цель НЕ достигнута.**

## Перед словами "готово" / "исправлено" / "завершено"

```
1. Написать: "Phase change: code -> verification"
2. cat .claude/skills/verification-before-completion/SKILL.md
3. Выполнить верификацию по skill
4. Только тогда заявлять о завершении
```

## После завершения задачи - AUTO-COMMIT

**Я НЕ МОГУ сказать "готово" без коммита.**

```
1. Верификация пройдена
2. git add <измененные файлы>
3. git commit -m "type: описание"
4. git push origin dev
5. Только тогда заявлять о завершении
```

**Без коммита задача НЕ ЗАВЕРШЕНА.**

## Cleanup - удаление временных файлов

**После каждой сессии или перед коммитом:**

```bash
rm -f tmpclaude*
```

Эти файлы создаются Claude Code автоматически и не нужны.

## Исключения из правил

Правило можно нарушить ТОЛЬКО если:
1. Задокументировано: какое правило, почему, какие риски
2. Пользователь явно подтвердил исключение

---

# Work Items Workflow

## Spec-Driven Development Flow

```
Context → Discuss (optional) → User Spec → Tech Spec → Tasks → Code → UAT → Verification → Commit
```

**Каждый уровень уточняет предыдущий:**
1. `project.md` - что строим
2. `user-spec.md` - что хочет пользователь (Russian)
3. `tech-spec.md` - как реализуем (English)
4. `tasks/*.md` - атомарные задачи

## Для новой фичи/бага:

```
1. Создать work/<feature-name>/
2. /new-user-spec → заполнить user-spec.md (интервью с пользователем)
3. /new-tech-spec → заполнить tech-spec.md (технические решения)
4. Разбить на tasks/*.md
5. Реализовать задачи (с использованием skills - Dynamic Skill Selection)
6. После деплоя: переместить в work/completed/
```

## Для хранения архитектуры:

```
Вся проектная информация в:
.claude/skills/project-knowledge/guides/

Обновлять guides после значительных изменений в архитектуре.
```

---

# AI-First Methodology Concepts

## Just-In-Time Context
Агент читает только необходимую информацию для текущей задачи, не весь контекст.

- Task development → read task.md, tech-spec.md, relevant guides
- Feature development → read all tasks, tech-spec, user-spec
- Context update → read only modified files

## Single Source of Truth
Каждая информация хранится в одном месте, остальные ссылаются на неё.

- Project description → `project-knowledge/guides/project.md`
- Tech stack → `project-knowledge/guides/architecture.md`
- Database schema → `project-knowledge/guides/database.md`
- Deployment config → `project-knowledge/guides/deployment.md`

## Agent Orchestration
Главный агент координирует специализированных субагентов.

**Orchestrator (`.claude/agents/orchestrator.md`):**
- Intent classification (autowork trigger)
- Автоматический выбор skills
- Validation prerequisite артефактов
- Model selection (opus/sonnet/haiku)
- Coordination субагентов

**Субагенты (`.claude/agents/`):**
- `code-developer` - реализует код и тесты (sonnet)
- `code-reviewer` - ревьюит качество кода (sonnet)
- `secret-scanner` - сканирует на секреты
- `security-auditor` - аудит OWASP Top 10

---

# Available Commands

| Command | Purpose |
|---------|---------|
| `/init-project` | Инициализация нового проекта с шаблоном и CI/CD |
| `/init-context` | Заполнение контекстных файлов проекта |
| `/project-context` | Загрузка контекста проекта |
| `/new-user-spec` | Создание user-spec через интервью |
| `/new-tech-spec` | Создание tech-spec и tasks |
| `/resume` | Продолжить незавершённую работу из STATE.md |

---

# Reference Information

## Windows: Python Commands

**Проблема:** `python` возвращает exit code 49 из-за кириллицы в пути.

**Решение:** Использовать `py -3.12`:

```bash
py -3.12 -m pytest tests/
py -3.12 -m ruff check src tests
py -3.12 script.py
```

## Git Workflow

- `dev` - рабочая ветка, коммитим сюда
- `main` - продакшен, авто-деплой

**Правила:**
1. Коммитить СРАЗУ после каждого завершенного изменения
2. НЕ трогать `main` напрямую
3. `deploy` -> merge dev в main

```bash
git add <files> && git commit -m "fix: description" && git push origin dev
```

## Commands

```bash
py -3.12 -m pytest tests/ -v              # тесты
py -3.12 -m ruff check src tests          # линтинг
py -3.12 -m pytest tests/ --cov=bot       # coverage
```

## Code Style

- Длина строки: 100
- Type hints на public функциях
- snake_case (функции), PascalCase (классы)
- Async: `async def`, `await` для I/O

## aiogram Best Practices

1. Handlers тонкие - логика в services
2. Dependency injection через middleware
3. FSM states в отдельных файлы
4. AsyncMock для тестов handlers
5. Не блокировать event loop

---

# Key Skills Reference

## Planning Skills
- `methodology` - AI-First методология, workflows
- `project-planning` - планирование проекта (project.md, features.md, roadmap.md)
- `user-spec-planning` - создание user-spec через интервью
- `tech-spec-planning` - создание tech-spec и tasks

## Infrastructure Skills
- `infrastructure` - CI/CD, Docker, GitHub Actions, pre-commit hooks
- `testing` - стратегия тестирования (smoke → unit → integration → E2E)

## Mandatory Skills
- `systematic-debugging` - при любом баге
- `test-driven-development` - при любом новом коде
- `user-acceptance-testing` - после реализации, перед verification
- `verification-before-completion` - перед "готово"
- `security-checklist` - при работе с персональными данными

## Context & Mapping Skills
- `context-capture` - для размытых требований, перед user-spec
- `codebase-mapping` - для нового/незнакомого проекта

## Python Skills
- `async-python-patterns` - async/await, aiogram, aiohttp
- `telegram-bot-architecture` - структура aiogram проекта
- `python-testing-patterns` - pytest, AsyncMock

---

# FORBIDDEN

- `@.claude/skills` - загружает ВСЁ, забивает контекст
- Код без checkpoint сообщения "Situation: ... Skills: ..."
- Смена фазы без сообщения "Phase change: X -> Y"
- "Готово" без загрузки `verification-before-completion`
- Изменение без теста
- Нарушение правил без задокументированного исключения
- **Пропуск `security-checklist` при работе с персональными данными**
- **Пропуск `secret-scanner` перед коммитами**
- **Пропуск UAT после реализации фичи**
- **Заявление "готово" без UAT подтверждения от пользователя**
- **Игнорирование Goal-backward Verification (проверять artifacts без проверки wiring)**
- **Выполнение плана (tasks/*.md) без загрузки `subagent-driven-development`**
- **Пропуск Worktree Mode когда файлы пересекаются И platform check проходит**
- **Утверждение "файлы пересекаются, поэтому последовательно" — использовать Worktree Mode!**
