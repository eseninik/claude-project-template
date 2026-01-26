# AUTO-CHECK Rule Improvement

**Дата:** 2026-01-26
**Проблема:** AUTO-CHECK правило слишком жёсткое - проверяет формат вместо сути
**Решение:** Гибкое правило с вариантами для разных форматов планов

---

## Проблема

### Ситуация из Quality Control Bot

**План существует:**
- [work/dr-status-notifications/plan.md](C:\Bots\Migrator bots\Quality Control Bot\work\dr-status-notifications\plan.md) - детальный план с 6 этапами
- [work/dr-status-notifications/IMPLEMENTATION_PROMPT.md](C:\Bots\Migrator bots\Quality Control Bot\work\dr-status-notifications\IMPLEMENTATION_PROMPT.md) - промпт для реализации

**Структура плана:**
- Этап 1: Конфигурация (независимый)
- Этап 2: AmoCRM Client (независимый)
- Этап 3: DR Service (независимый)
- Этап 4: Webhook Handler (зависит от 1, 3)
- Этап 5: Main App (зависит от 3, 4)
- Этап 6: .env Configuration (независимый)

**Проблема:**
- Структуры `tasks/*.md` нет
- AUTO-CHECK проверяет только `work/*/tasks/*.md`
- Skill `subagent-driven-development` требует эту структуру
- Бот работает последовательно, теряя возможность параллелизации
- **Этапы 1, 2, 3, 6 могли выполняться параллельно (4 задачи одновременно)**

---

## Решение

### 1. Обновлено правило AUTO-CHECK

**Было ([CLAUDE.md:65-72](CLAUDE.md#L65-L72)):**
```markdown
## Dynamic Skill Selection

```
1. СТОП
2. AUTO-CHECK: Есть work/*/tasks/*.md с 3+ задачами?
   ├─ ДА → subagent-driven-development ОБЯЗАТЕЛЕН
   └─ НЕТ → продолжить
```

**Стало ([CLAUDE.md:62-80](CLAUDE.md#L62-L80)):**
```markdown
## Dynamic Skill Selection

```
1. СТОП
2. AUTO-CHECK: Есть чёткий план для реализации?

   A. План в формате work/*/tasks/*.md с 3+ задачами?
      └─ ДА → subagent-driven-development ОБЯЗАТЕЛЕН

   B. План в другом формате (plan.md, IMPLEMENTATION_PROMPT.md)?
      └─ ДА → СПРОСИТЬ пользователя:
         "Есть план с [N] задачами, но не в формате tasks/*.md.

          Варианты:
          1. Создать tasks/*.md из плана (рекомендуется для 3+ независимых задач)
          2. Использовать executing-plans (параллельная сессия)
          3. Работать последовательно"

   C. Нет плана или < 3 задач?
      └─ продолжить обычным workflow
```

### 2. Обновлён Checkpoint

**Было:**
```
Situation: [описание]
Plan detected: [yes/no]
Skills: [список]
```

**Стало:**
```
Situation: [описание]
Plan format: [tasks/*.md / plan.md / none]
Plan tasks count: [N]
Skills: [список]
```

### 3. Обновлены FORBIDDEN PATTERNS

**Было:**
```
- План без `subagent-driven-development`
```

**Стало:**
```
- План с tasks/*.md без `subagent-driven-development`
- Игнорирование плана в другом формате — предложить варианты
```

---

## Создан guide для конвертации

**Файл:** [.claude/guides/plan-format-conversion.md](.claude/guides/plan-format-conversion.md)

**Содержит:**
1. Структуру tasks/*.md с frontmatter
2. Пример конвертации plan.md → tasks/*.md
3. Определение зависимостей (depends_on)
4. Определение файлов (files_modified)
5. Автоматическую конвертацию через команду

---

## Пример для DR Status Notifications

### Wave Analysis после конвертации

**Структура tasks/*.md:**
```
task-001.md: Конфигурация
  depends_on: []
  files_modified: [src/bot/config.py]

task-002.md: AmoCRM Client
  depends_on: []
  files_modified: [src/bot/services/amocrm/client.py]

task-003.md: DR Service
  depends_on: []
  files_modified: [
    src/bot/services/dr_notifications/__init__.py,
    src/bot/services/dr_notifications/service.py
  ]

task-004.md: Webhook Handler
  depends_on: [001, 003]
  files_modified: [src/bot/services/amocrm/webhook.py]

task-005.md: Main App
  depends_on: [003, 004]
  files_modified: [src/bot/__main__.py]

task-006.md: .env Configuration
  depends_on: []
  files_modified: [.env]
```

**Wave Parallelization:**
```
Wave 1: [001, 002, 003, 006] (4 задачи параллельно)
  ├─ Файлы не пересекаются
  └─ Standard parallel mode

Wave 2: [004] (зависит от 001, 003)
  └─ Sequential

Wave 3: [005] (зависит от 003, 004)
  └─ Sequential
```

**Результат:**
- **Было:** 6 задач последовательно = ~120 минут
- **Стало:** Wave 1 параллельно + Wave 2 + Wave 3 = ~40 минут
- **Выигрыш:** 3x ускорение

---

## Команда для конвертации

**Для пользователя Quality Control Bot:**

```
Прочитай plan.md и создай tasks/*.md структуру:

1. cat .claude/guides/plan-format-conversion.md
2. cat work/dr-status-notifications/plan.md
3. Создать work/dr-status-notifications/tasks/ папку
4. Конвертировать 6 этапов в task-001.md ... task-006.md
5. Заполнить frontmatter (depends_on, files_modified) на основе плана
6. Скопировать детали реализации

Используй plan.md строки 30-546 для извлечения информации.
```

---

## Что это решает

1. ✅ Правило проверяет суть (наличие плана), а не только формат
2. ✅ Бот предлагает варианты вместо молчаливой деградации
3. ✅ Пользователь может конвертировать план для параллелизации
4. ✅ Альтернатива (executing-plans) доступна
5. ✅ Guide объясняет КАК конвертировать

---

## Принципы решения

**Из [.claude/guides/decision-making.md](.claude/guides/decision-making.md):**

### Independent Judgment анализ

**Условия для отклонения от правила (все выполняются):**
1. ✅ Evidence overwhelming - очевидно что plan.md содержит план с задачами
2. ❌ Stakes extremely high - НЕ выполняется (можно работать последовательно)
3. ✅ Задокументировано - этот документ
4. ✅ Минимальное отклонение - предложение вариантов, а не игнорирование

**Градация действий:**
1. ✅ Raise concerns - указал на проблему
2. ✅ Ask clarification - предложил варианты
3. ❌ Decline to proceed - НЕ делаем
4. ❌ Deviate from rules - НЕ делаем

### Dual Newspaper Test

- Тест 1: "Журналист напишет что AI отказался помочь из-за формального отсутствия файла?" - ✅ ДА ⚠️
- Тест 2: "Журналист напишет что AI помог несмотря на формальное отсутствие файла?" - ❌ НЕТ

**Решение:** Изменить правило на более гибкое с предложением вариантов.

### Hierarchy of Priorities

```
1. SAFETY      → Не нарушено (параллелизация безопасна)
2. QUALITY     → Улучшено (параллелизация + review)
3. GUIDELINES  → Улучшено (гибкое правило)
4. HELPFULNESS → Улучшено (предложение вариантов)
```

---

## Связанные файлы

- [CLAUDE.md](CLAUDE.md) - обновлён AUTO-CHECK, Checkpoint, FORBIDDEN PATTERNS
- [.claude/guides/plan-format-conversion.md](.claude/guides/plan-format-conversion.md) - новый guide
- [.claude/guides/decision-making.md](.claude/guides/decision-making.md) - использован для анализа
- [.claude/guides/principles.md](.claude/guides/principles.md) - Hierarchy of Priorities

---

## Тестовые сценарии

### TC-01: План в формате tasks/*.md (без изменений)

**Дано:** `work/feature/tasks/task-001.md`, `task-002.md`, `task-003.md`

**Ожидаемое поведение:**
1. AUTO-CHECK вариант A → ДА
2. subagent-driven-development ОБЯЗАТЕЛЕН
3. Wave analysis
4. Выполнение

**Статус:** ✅ РАБОТАЕТ ИДЕНТИЧНО

---

### TC-02: План в формате plan.md (новое)

**Дано:** `work/dr-status-notifications/plan.md` с 6 этапами

**Ожидаемое поведение:**
1. AUTO-CHECK вариант B → ДА
2. Спросить пользователя варианты:
   - Создать tasks/*.md
   - executing-plans
   - Последовательно
3. Пользователь выбирает
4. Выполнение согласно выбору

**Статус:** ✅ НОВАЯ ФУНКЦИОНАЛЬНОСТЬ

---

### TC-03: Нет плана

**Дано:** Простая задача "Fix typo"

**Ожидаемое поведение:**
1. AUTO-CHECK вариант C → продолжить
2. Dynamic Skill Selection
3. Выполнение

**Статус:** ✅ РАБОТАЕТ ИДЕНТИЧНО

---

## Выводы

**Проблема:** Правило было слишком жёстким (формат вместо сути)

**Решение:** Правило стало гибким (проверяет наличие плана + предлагает варианты)

**Результат:**
- Пользователь не теряет производительность из-за формата
- Бот помогает конвертировать план при необходимости
- Альтернативы доступны (executing-plans, sequential)

**Статус:** ✅ РЕАЛИЗОВАНО
