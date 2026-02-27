# v2.0 - Universal Parallelization Detection

**Статус:** ✅ РЕАЛИЗОВАНО (commit b0dbba0)

**Цель:** Агент определяет возможность параллелизации даже если план только в памяти.

---

## Что изменилось

### v1.0 (commit 7db9f10)
- ✅ План в tasks/*.md → параллелизация
- ✅ План в plan.md → предложить конвертацию
- ❌ Нет файла плана → работать последовательно

### v2.0 (commit b0dbba0)
- ✅ План в tasks/*.md → параллелизация
- ✅ План в plan.md → предложить конвертацию
- ✅ **План в памяти агента → контекстный анализ → параллелизация**

---

## Компоненты

### 1. База знаний паттернов

**Файл:** [.claude/knowledge/parallelization-patterns.md](../../.claude/knowledge/parallelization-patterns.md)

**Содержит:**
- Типовые паттерны задач (аутентификация, уведомления, CRUD, файлы, интеграции, миграции, рефакторинг, оптимизация, инфраструктура)
- Триггеры для распознавания (ключевые слова)
- Алгоритм определения независимости
- Примеры с wave analysis

**Паттерны:**
- Аутентификация → 5 задач (middleware, login, register, storage, tests)
- Уведомления → 6 задач (модель, API, email, push, webhook, tests)
- CRUD → 7 задач (модель, endpoints, валидация, tests)
- API Integration → 5 задач (client, mapper, webhook, sync, tests)
- Performance Optimization → 5 задач (profiling, db, cache, bg jobs, tests)
- CI/CD Setup → 5 задач (workflow, dockerfile, compose, env, deploy)

### 2. Skill для task-decomposition

**Файл:** [.claude/skills/task-decomposition/SKILL.md](../../.claude/skills/task-decomposition/SKILL.md)

**Процесс (7 шагов):**
1. Загрузка базы знаний
2. Парсинг описания задачи
3. Определение подзадач (из паттерна или извлечение)
4. Проверка независимости
5. Построение waves
6. Оценка уверенности
7. Формирование рекомендации

**Уровни уверенности:**
- **>90%** - Высокая: Предложить параллелизацию уверенно
- **60-90%** - Средняя: Предложить с вопросом о зависимостях
- **<60%** - Низкая: Спросить детали

### 3. AUTO-CHECK вариант C

**Файл:** [CLAUDE.md:79-92](../../CLAUDE.md#L79-L92)

**Новый вариант C:**
```
C. Контекстный анализ задачи (нет явного плана)
   1. cat .claude/skills/task-decomposition/SKILL.md
   2. Применить процесс анализа
   3. IF 3+ подзадачи AND уверенность > 60%:
      → ПРЕДЛОЖИТЬ параллелизацию
   4. ELSE:
      → продолжить обычным workflow
```

### 4. Обновлённый Checkpoint

**Был:**
```
Situation: [описание]
Plan format: [tasks/*.md / plan.md / none]
Plan tasks count: [N]
Skills: [список]
```

**Стал:**
```
Situation: [описание]
Plan format: [tasks/*.md / plan.md / implicit / none]
Plan tasks count: [N]
Parallelization analysis: [detected / not applicable / uncertain]
  If detected:
    - Subtasks: [список]
    - Waves: [Wave 1: [...], Wave 2: [...]]
    - Confidence: [high / medium / low]
Skills: [список]
```

### 5. Обновлённый SKILLS_INDEX

**Файл:** [.claude/skills/SKILLS_INDEX.md](../../.claude/skills/SKILLS_INDEX.md)

**Добавлено:**
- Entry Point: "Задача без явного плана" → task-decomposition
- Новая категория: TASK ANALYSIS & DECOMPOSITION

---

## Примеры работы

### Пример 1: "Добавь систему уведомлений"

**Что делает агент:**
1. Парсинг: "уведомлен*" → Паттерн Notifications
2. Подзадачи (из паттерна): 6 задач
3. Независимость: Все разные файлы → INDEPENDENT
4. Waves: Wave 1: [1,2,3,4,5], Wave 2: [6]
5. Уверенность: 90% (высокая)
6. **Предложение:**
   ```
   Вижу 6 независимых подзадач:
   1. Модель Notification
   2. API endpoints
   3. Email сервис
   4. Push notification
   5. Webhook integration
   6. Тесты

   Wave analysis:
   - Wave 1: [1,2,3,4,5] (5 задач параллельно)
   - Wave 2: [6] (тесты)

   Варианты:
   1. Создать tasks/*.md и выполнить параллельно (рекомендуется)
      → Сэкономит ~80% времени
   2. Работать последовательно

   Какой вариант?
   ```

**Если пользователь выберет вариант 1:**
- Агент создаёт work/notifications/tasks/task-001.md ... task-006.md
- AUTO-CHECK вариант A срабатывает
- subagent-driven-development загружается
- Параллельное выполнение

### Пример 2: "Нужно: логирование, README, тесты"

**Что делает агент:**
1. Парсинг: Список из 3 пунктов
2. Подзадачи (извлечённые): 3 задачи
3. Независимость: Разные файлы, НО неуверенность в зависимостях (тесты могут зависеть)
4. Уверенность: 60% (средняя)
5. **Предложение:**
   ```
   Похоже задачу можно разбить на 3 подзадачи, но есть вопрос:

   Smoke tests зависят от логирования, или это независимая задача?

   Варианты:
   1. Если независимые → все 3 параллельно
   2. Если тесты зависят → логирование + README параллельно, затем тесты
   3. Работать последовательно
   ```

### Пример 3: "Улучши производительность"

**Что делает агент:**
1. Парсинг: "производительност*" → Паттерн (частичный)
2. Проблема: Не ясно какие оптимизации
3. Уверенность: 20% (низкая)
4. **Предложение:**
   ```
   Задача про оптимизацию.

   Типовые подзадачи:
   - Profiling
   - Database optimization
   - Caching
   - Background jobs

   НО нужно больше информации:
   - Какие части медленные?
   - Известны bottlenecks?

   Варианты:
   1. Дать детали → создам точный план
   2. Начать с profiling → затем план
   3. Работать последовательно
   ```

Полные примеры: [work/templates/v2-testing-examples.md](../../work/templates/v2-testing-examples.md)

---

## Универсальный промпт для других проектов

**Файл:** [work/templates/upgrade-template-prompt.md](../../work/templates/upgrade-template-prompt.md)

**Для обновления проекта до v2.0:**

```
Обнови этот проект до новой версии claude-project-template (commit b0dbba0).

Изменения:
1. AUTO-CHECK вариант C (контекстный анализ)
2. База знаний: .claude/knowledge/parallelization-patterns.md
3. Skill: task-decomposition
4. Обновлённый checkpoint format

Инструкция:

ЭТАП 1: Backup
cp CLAUDE.md CLAUDE.md.backup

ЭТАП 2: Обновить AUTO-CHECK
cat c:/Bots/Migrator\ bots/claude-project-template-update/CLAUDE.md
Скопировать вариант C (строки 79-92)
Заменить в текущем CLAUDE.md

ЭТАП 3: Обновить Checkpoint
Заменить checkpoint format (строки 89-100)

ЭТАП 4: Копировать файлы
mkdir -p .claude/knowledge
cp -r c:/Bots/Migrator\ bots/claude-project-template-update/.claude/knowledge/parallelization-patterns.md .claude/knowledge/

mkdir -p .claude/skills/task-decomposition
cp -r c:/Bots/Migrator\ bots/claude-project-template-update/.claude/skills/task-decomposition/* .claude/skills/task-decomposition/

ЭТАП 5: Обновить SKILLS_INDEX.md
Добавить task-decomposition в Entry Points и категорию TASK ANALYSIS

ЭТАП 6: Верификация
cat CLAUDE.md | grep "Контекстный анализ"
cat .claude/knowledge/parallelization-patterns.md
cat .claude/skills/task-decomposition/SKILL.md

ЭТАП 7: Git
git diff CLAUDE.md
Показать изменения для подтверждения
После подтверждения:
git add CLAUDE.md .claude/knowledge/ .claude/skills/task-decomposition/ .claude/skills/SKILLS_INDEX.md
git commit -m "feat: upgrade to v2.0 - universal parallelization detection (b0dbba0)"
```

**Копировать эту команду в новую сессию проекта.**

---

## Что это решает

### Проблема из Quality Control Bot

**Было:**
- План в plan.md → агент НЕ обнаруживал параллелизацию
- Работал последовательно (6 задач)

**Стало:**
- План в plan.md → v1.0 предлагает конвертацию
- **Нет явного плана → v2.0 анализирует контекст и предлагает параллелизацию**

### Ваш сценарий

**Вы сказали:**
> "Иногда я просто прошу сделать автоматически, агент создаёт план"

**Решение:**
- Агент создаёт план в памяти
- v2.0 **ОБНАРУЖИВАЕТ** этот план через task-decomposition
- Предлагает параллелизацию
- Создаёт tasks/*.md по запросу
- Запускает subagent-driven-development

**Результат:**
- ✅ Универсальное определение параллелизации
- ✅ Не зависит от формата (tasks/*.md, plan.md, память)
- ✅ Не теряется производительность

---

## Технические детали

### Алгоритм определения независимости

```python
def check_independence(task_a, task_b):
    if task_a.files != task_b.files:
        return "INDEPENDENT" # Разные файлы

    if task_a.scope != task_b.scope:
        return "INDEPENDENT" # Один файл, разные функции

    if "используя результат" in description:
        return "DEPENDENT"

    if "на основе" in description:
        return "DEPENDENT"

    return "UNCERTAIN" # Спросить пользователя
```

### Построение waves

```python
wave_map = {}
for task in tasks:
    if not task.depends_on:
        wave_map[task] = 1
    else:
        max_dep_wave = max(wave_map[dep] for dep in task.depends_on)
        wave_map[task] = max_dep_wave + 1
```

### Оценка уверенности

```python
confidence = 0.5 # Базовая

if pattern_matched:
    confidence += 0.3 # Паттерн совпал

if explicit_list:
    confidence += 0.2 # Чёткий список

if different_files:
    confidence += 0.1 # Разные файлы

if uncertain_dependencies:
    confidence -= 0.2 # Неуверенность
```

---

## Метрики эффективности

**Для оценки работы v2.0:**

- **Precision:** Сколько предложенных параллелизаций были корректными
- **Recall:** Сколько возможностей параллелизации обнаружено
- **User satisfaction:** Пользователь принял рекомендацию?

**Собирать feedback:**
- Какие паттерны работают лучше
- Какие триггеры дают ложные срабатывания
- Какие задачи пропускаются

**Эволюция:**
- Добавлять новые паттерны в базу знаний
- Улучшать алгоритм определения зависимостей
- Domain-specific расширения (Telegram bots, ML pipelines, etc.)

---

## Сравнение версий

| Аспект | v1.0 | v2.0 |
|--------|------|------|
| Обнаружение tasks/*.md | ✅ | ✅ |
| Обнаружение plan.md | ✅ | ✅ |
| Обнаружение плана в памяти | ❌ | ✅ |
| База знаний паттернов | ❌ | ✅ |
| Оценка уверенности | ❌ | ✅ |
| Создание tasks/*.md по запросу | ❌ | ✅ |
| Контекстный анализ | ❌ | ✅ |

---

## Файлы v2.0

**Новые файлы:**
- `.claude/knowledge/parallelization-patterns.md` (база знаний)
- `.claude/skills/task-decomposition/SKILL.md` (skill)
- `work/templates/v2-testing-examples.md` (примеры)
- `work/templates/upgrade-template-prompt.md` (промпт для обновления)
- `work/templates/universal-parallelization-proposal.md` (предложение v2.0)

**Изменённые файлы:**
- `CLAUDE.md` (AUTO-CHECK вариант C, checkpoint)
- `.claude/skills/SKILLS_INDEX.md` (task-decomposition entry point)

---

## Резюме

**v2.0 реализован полностью.**

**Агент теперь:**
1. ✅ Обнаруживает планы в любом формате (tasks/*.md, plan.md, память)
2. ✅ Анализирует контекст задачи
3. ✅ Распознаёт типовые паттерны
4. ✅ Определяет независимость подзадач
5. ✅ Оценивает уверенность
6. ✅ Предлагает параллелизацию осмысленно
7. ✅ Создаёт tasks/*.md по запросу
8. ✅ Запускает subagent-driven-development автоматически

**Универсальность достигнута:**
- Работает ВНЕ ЗАВИСИМОСТИ от наличия файла плана
- Не теряет производительность из-за формальных ограничений
- Предлагает варианты вместо навязывания

**Готово к использованию в других проектах.**
