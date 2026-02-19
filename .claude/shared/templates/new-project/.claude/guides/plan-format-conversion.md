# Plan Format Conversion Guide

**Загружай когда:** Есть план (plan.md, IMPLEMENTATION_PROMPT.md), но нужен формат tasks/*.md для параллелизации.

---

## Зачем нужен формат tasks/*.md?

**Skill `subagent-driven-development` требует структуру tasks/*.md для:**
- Автоматического анализа зависимостей (depends_on)
- Определения файловых конфликтов (files_modified)
- Параллельного запуска независимых задач

**Если у вас уже есть plan.md, его можно конвертировать.**

---

## Структура tasks/*.md

Каждый файл задачи:

```markdown
---
depends_on: []  # Список задач, от которых зависит (пример: [001, 002])
files_modified:  # Список файлов, которые будет менять задача
  - src/bot/config.py
  - src/bot/services/dr_notifications/service.py
---

# Task 001: [Название задачи]

## Описание
[Что нужно сделать]

## Детали реализации
[Конкретные шаги]

## Критерии готовности
- [ ] Код написан
- [ ] Тесты проходят
- [ ] Committed
```

---

## Пример конвертации

### Было (plan.md):

```markdown
## Этапы реализации

### Этап 1: Конфигурация
**Файл:** src/bot/config.py
Добавить поля dr_pipeline_ids, dr_status_notifications

### Этап 2: AmoCRM Client
**Файл:** src/bot/services/amocrm/client.py
Расширить get_deal параметром with_contacts

### Этап 3: DR Service
**Создать:** src/bot/services/dr_notifications/service.py
Реализовать DRStatusNotificationService
```

### Стало (work/dr-status-notifications/tasks/):

**task-001.md:**
```markdown
---
depends_on: []
files_modified:
  - src/bot/config.py
---

# Task 001: Конфигурация

## Описание
Добавить DR конфигурацию в config.py

## Детали
- Поля: dr_pipeline_ids_str, dr_status_notifications
- Property: dr_pipeline_ids, dr_status_map, dr_enabled
- Импортировать json

## Критерии готовности
- [ ] Поля добавлены
- [ ] Properties работают
- [ ] Committed
```

**task-002.md:**
```markdown
---
depends_on: []
files_modified:
  - src/bot/services/amocrm/client.py
---

# Task 002: AmoCRM Client

## Описание
Расширить get_deal параметром with_contacts

## Детали
- Параметр: with_contacts: bool = False
- Логика: params = {"with": "contacts"} if with_contacts

## Критерии готовности
- [ ] Параметр добавлен
- [ ] API запрос работает
- [ ] Committed
```

**task-003.md:**
```markdown
---
depends_on: []
files_modified:
  - src/bot/services/dr_notifications/__init__.py
  - src/bot/services/dr_notifications/service.py
---

# Task 003: DR Service

## Описание
Создать DRStatusNotificationService

## Детали
- Файл service.py с классом
- Метод send_notification
- Метод _get_client_name
- Шаблоны уведомлений

## Критерии готовности
- [ ] Сервис создан
- [ ] Методы работают
- [ ] Committed
```

---

## Определение зависимостей

**depends_on: []** означает задачи независимые, можно выполнять параллельно.

**depends_on: [001]** означает задача зависит от task-001.

**Примеры:**
- Этап 1, 2, 3 не зависят друг от друга → `depends_on: []`
- Этап 4 требует завершения этапа 1 → `depends_on: [001]`
- Этап 5 требует 1 и 2 → `depends_on: [001, 002]`

---

## Определение files_modified

**Зачем:** Skill определяет конфликты файлов для Worktree Mode.

**Правило:** Указывай ВСЕ файлы, которые будут изменены.

**Примеры:**
- Добавление конфигурации → `[src/bot/config.py]`
- Создание нового сервиса → `[src/bot/services/new/service.py, src/bot/services/new/__init__.py]`
- Изменение существующего + тесты → `[src/models/user.py, tests/test_user.py]`

---

## Автоматическая конвертация

**Команда для бота:**

```
Создай tasks/*.md из plan.md следуя структуре из .claude/guides/plan-format-conversion.md

План: work/dr-status-notifications/plan.md
Целевая папка: work/dr-status-notifications/tasks/
```

**Что сделает бот:**
1. Прочитает plan.md
2. Определит этапы/задачи
3. Создаст task-001.md, task-002.md, ...
4. Заполнит frontmatter (depends_on, files_modified)
5. Скопирует детали реализации

---

## Проверка готовности

**После конвертации проверь:**
- [ ] Каждый этап = отдельный task-*.md файл
- [ ] Frontmatter заполнен (depends_on, files_modified)
- [ ] Независимые задачи имеют `depends_on: []`
- [ ] files_modified перечисляет ВСЕ изменяемые файлы

**Затем запускай:**
```
AUTO-CHECK пройдёт → subagent-driven-development активируется
→ Wave анализ → Параллельное выполнение
```

---

## Когда НЕ нужна конвертация

**НЕ конвертируй если:**
- Меньше 3 задач (параллелизация не нужна)
- Задачи строго последовательные (каждая зависит от предыдущей)
- План уже в формате tasks/*.md

**Вместо этого:**
- Используй sequential execution для последовательной сессии
- Работай последовательно в текущей сессии
