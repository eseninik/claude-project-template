# Промпт для обновления проекта до новой версии template

**Для использования в других проектах, построенных на этом шаблоне.**

---

## Команда для агента

```
Обнови этот проект до новой версии claude-project-template (commit 7db9f10).

Изменения в template:
1. Обновлён AUTO-CHECK rule в CLAUDE.md (гибкое определение плана)
2. Создан guide: .claude/guides/plan-format-conversion.md
3. Обновлены FORBIDDEN PATTERNS

Инструкция:

ЭТАП 1: Анализ текущего CLAUDE.md
1. cat CLAUDE.md
2. Найти секцию "## Dynamic Skill Selection"
3. Проверить есть ли там AUTO-CHECK правило

ЭТАП 2: Backup
1. Создать backup: cp CLAUDE.md CLAUDE.md.backup

ЭТАП 3: Обновление AUTO-CHECK
1. cat c:/Bots/Migrator\ bots/claude-project-template-update/CLAUDE.md
2. Найти строки 61-95 (секция Dynamic Skill Selection)
3. Скопировать НОВОЕ правило AUTO-CHECK (с вариантами A, B, C)
4. Заменить СТАРОЕ правило в текущем CLAUDE.md
5. ВАЖНО: Сохранить все остальные секции без изменений

ЭТАП 4: Обновление Checkpoint
1. Найти "**Checkpoint перед кодом:**"
2. Заменить на новый формат:
   ```
   Situation: [описание]
   Plan format: [tasks/*.md / plan.md / none]
   Plan tasks count: [N]
   Skills: [список]
   ```

ЭТАП 5: Обновление FORBIDDEN PATTERNS
1. Найти секцию "# FORBIDDEN PATTERNS"
2. Заменить строку "План без subagent-driven-development" на:
   - "План с tasks/*.md без subagent-driven-development"
   - "Игнорирование плана в другом формате — предложить варианты"

ЭТАП 6: Копирование guide
1. Создать папку .claude/guides/ если нет
2. Скопировать файл:
   cp c:/Bots/Migrator\ bots/claude-project-template-update/.claude/guides/plan-format-conversion.md .claude/guides/

ЭТАП 7: Верификация
1. cat CLAUDE.md | grep "AUTO-CHECK"
2. Проверить что видно новое правило с вариантами A, B, C
3. cat .claude/guides/plan-format-conversion.md
4. Проверить что guide скопирован

ЭТАП 8: Git
1. git diff CLAUDE.md
2. Показать мне изменения для подтверждения
3. СТОП - дождаться моего подтверждения
4. После подтверждения:
   git add CLAUDE.md .claude/guides/plan-format-conversion.md
   git commit -m "refactor: update AUTO-CHECK rule from template (7db9f10)"

ВАЖНО:
- НЕ удалять другие секции CLAUDE.md
- НЕ менять project-specific настройки
- Только обновить AUTO-CHECK, Checkpoint, FORBIDDEN PATTERNS
- Спросить перед коммитом
```

---

## После обновления

Проект получит:
- ✅ Гибкое определение плана (tasks/*.md, plan.md)
- ✅ Предложение вариантов для конвертации
- ✅ Guide для ручной конвертации планов

**НО:**
- ⚠️ Всё ещё требует явный файл плана
- ⚠️ Неявные планы (в памяти агента) не обнаруживаются

Для полностью универсального решения см.: [work/templates/universal-parallelization-proposal.md](universal-parallelization-proposal.md)
