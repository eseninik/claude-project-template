# Skills Index — Lazy Loading Router

> **КРИТИЧНО:** НЕ загружай все скиллы. Читай только нужные для текущей задачи.

---

## Интеграция с OpenSpec

OpenSpec управляет **ЧТО** делать (proposal → tasks → archive).  
Skills управляют **КАК** делать (TDD, debugging, verification).

```
┌─────────────────────────────────────────────────────────────┐
│                      ЗАПРОС                                 │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
   ┌─────────┐      ┌──────────┐      ┌─────────┐
   │ OpenSpec│      │  Skills  │      │  Both   │
   │  Only   │      │   Only   │      │         │
   └─────────┘      └──────────┘      └─────────┘
   
   • proposal       • bug/fix         • implement
   • spec           • refactor        • continue
   • plan change    • debug           • finish
   • new feature    • test
```

---

## Когда что использовать

| Запрос содержит | Действие |
|-----------------|----------|
| `proposal`, `spec`, `plan change`, `новая фича` | → `openspec/AGENTS.md` (Stage 1), Skills NOT needed |
| `implement`, `continue`, `выполни tasks.md` | → OpenSpec Stage 2 + Skills |
| `archive`, `завершить change` | → `openspec/AGENTS.md` (Stage 3) |
| `bug`, `fix`, `ошибка`, `не работает` | → Skills напрямую |
| `refactor`, `optimize` (малый scope) | → Skills напрямую |

---

## OpenSpec Stage 2: Implementation + Skills

Когда proposal approved и ты на стадии Implementation:

```
1. Прочитай proposal.md — что делаем
2. Прочитай design.md (если есть) — как делаем
3. Прочитай tasks.md — чеклист задач

4. ЗАГРУЗИ SKILLS INDEX:
   cat .claude/skills/SKILLS_INDEX.md

5. ДЛЯ КАЖДОЙ ЗАДАЧИ из tasks.md:
   → Выбери 1-2 скилла из индекса
   → Загрузи: cat .claude/skills/<папка>/SKILL.md
   → Выполни задачу по скиллу
   → Отметь [x] в tasks.md

6. После всех задач:
   → verification-before-completion
   → finishing-a-development-branch
   → openspec archive (Stage 3)
```

---

## Скиллы по фазам

### Phase: Implementation (выполнение tasks.md)

| Скилл | Когда | Путь |
|-------|-------|------|
| **executing-plans** | Выполнение плана батчами с ревью | `executing-plans/SKILL.md` |
| **subagent-driven-development** | Независимые задачи, параллельная работа | `subagent-driven-development/SKILL.md` |
| **test-driven-development** | ⚠️ ВСЕГДА при написании кода | `test-driven-development/SKILL.md` |
| **using-git-worktrees** | Нужна изоляция для фичи | `using-git-worktrees/SKILL.md` |

---

### Phase: Debugging (при ошибках)

| Скилл | Когда | Путь |
|-------|-------|------|
| **systematic-debugging** | ⚠️ ЛЮБОЙ баг — СНАЧАЛА этот | `systematic-debugging/SKILL.md` |
| **root-cause-tracing** | Ошибка глубоко в стеке | `root-cause-tracing/SKILL.md` |
| **defense-in-depth** | Баг от невалидных данных | `defense-in-depth/SKILL.md` |
| **dispatching-parallel-agents** | 3+ независимых фейла | `dispatching-parallel-agents/SKILL.md` |

---

### Phase: Testing (качество тестов)

| Скилл | Когда | Путь |
|-------|-------|------|
| **testing-anti-patterns** | Пишу/меняю тесты | `testing-anti-patterns/SKILL.md` |
| **condition-based-waiting** | Flaky тесты, race conditions | `condition-based-waiting/SKILL.md` |

---

### Phase: Review (проверка кода)

| Скилл | Когда | Путь |
|-------|-------|------|
| **requesting-code-review** | Закончил задачу, нужен ревью | `requesting-code-review/SKILL.md` |
| **receiving-code-review** | Получил фидбек | `receiving-code-review/SKILL.md` |

---

### Phase: Completion (перед archive)

| Скилл | Когда | Путь |
|-------|-------|------|
| **verification-before-completion** | ⚠️ ПЕРЕД любым "готово" | `verification-before-completion/SKILL.md` |
| **finishing-a-development-branch** | Мерж, PR, завершение ветки | `finishing-a-development-branch/SKILL.md` |

---

## ⚠️ Обязательные скиллы

| Ситуация | Скилл | Почему |
|----------|-------|--------|
| Любой баг | `systematic-debugging` | Без root cause — фикс бесполезен |
| Любой новый код | `test-driven-development` | Без теста — код не верифицирован |
| Заявление "готово" | `verification-before-completion` | Без проверки — не факт |
| Все задачи в tasks.md выполнены | `finishing-a-development-branch` | Правильное завершение |

---

## Типичные сценарии

### Новая фича (полный цикл)

```
STAGE 1 — OpenSpec (Skills NOT needed):
  openspec/AGENTS.md → создать proposal
  → дождаться approval

STAGE 2 — Skills:
  using-git-worktrees (изоляция)

  Для каждой задачи:
    test-driven-development
    executing-plans

  После всех задач:
    verification-before-completion
    finishing-a-development-branch

STAGE 3 — OpenSpec:
  openspec archive <change-id> --yes
```

### Баг-фикс (без OpenSpec)

```
systematic-debugging → найти root cause
test-driven-development → failing test  
verification-before-completion → проверить
```

### Продолжить implementation

```
1. openspec show <change-id> → понять контекст
2. Прочитать tasks.md → найти незавершённые задачи
3. cat .claude/skills/SKILLS_INDEX.md
4. Выбрать скиллы для текущей задачи
5. Продолжить работу
```

---

## Мета-скиллы

| Скилл | Когда | Путь |
|-------|-------|------|
| **using-superpowers** | Начало сессии, определение скиллов | `using-superpowers/SKILL.md` |
| **writing-skills** | Создание нового скилла | `writing-skills/SKILL.md` |
| **testing-skills-with-subagents** | Тестирование скилла | `testing-skills-with-subagents/SKILL.md` |
| **sharing-skills** | Контрибьют скилла в upstream | `sharing-skills/SKILL.md` |

---

## Правила

1. **Максимум 3 скилла** одновременно
2. **OpenSpec первый** для новых фич (Stage 1 → Stage 2)
3. **Skills для HOW** — OpenSpec для WHAT
4. **SUB-SKILL ссылки** — если скилл требует другой, загрузи его
5. **Не загружай заранее** — только по необходимости
