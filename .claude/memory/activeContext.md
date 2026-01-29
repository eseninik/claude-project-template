# Active Context

> Мост между сессиями. Агент читает в начале, обновляет в конце.

**Last updated:** 2026-01-29 14:30

---

## Current Focus

Реализована трёхуровневая система памяти (pre-commit warning + post-commit fallback).

---

## Recent Decisions

| Date | Decision | Rationale | Files Affected |
|------|----------|-----------|----------------|
| 2026-01-29 | Добавить memory/ и adr/ в шаблон | Deep research показал что это решает "project amnesia" | .claude/memory/, .claude/adr/ |
| 2026-01-29 | AUTO-BEHAVIORS вместо команд | Пользователь хочет автоматику без ручных действий | CLAUDE.md |
| 2026-01-29 | Git hooks для автообновления | Память должна обновляться без участия человека | .claude/hooks/post-commit.sh |
| 2026-01-29 | Трёхуровневая система памяти | Гарантировать что память всегда обновляется | pre-commit.sh, post-commit.sh |

---

## Active Questions

- [x] Нужно ли добавить pre-commit hook для проверки заполненности памяти? → Да, добавлен
- [ ] Как обрабатывать большие Session Log (архивация)? → archive/ директория создана

---

## Learned Patterns

### What Works
- Триггерные правила в CLAUDE.md заставляют агента следовать протоколу
- Разделение STATE.md (задачи) и activeContext.md (контекст) — разные цели
- Трёхуровневая защита: BLOCKING RULE → pre-commit warning → post-commit fallback

### What Doesn't Work
- Команды требуют ручного вызова — пользователи забывают

### Gotchas
- При upgrade-project не трогать memory/ и adr/ — это проектные данные

---

## Next Steps

1. Установить hooks: `./.claude/scripts/setup-hooks.sh`
2. Протестировать систему памяти (тесты из плана)
3. Обновить upgrade-project чтобы не трогал memory/ и adr/

---

## Auto-Generated Summaries

> Записи добавляются post-commit когда агент не обновил память.
> При следующей сессии: интегрировать в Session Log и очистить.

---

## Session Log

### 2026-01-29 (сессия 2)
**Did:** Реализовал трёхуровневую систему памяти:
- pre-commit.sh: warning если память не обновлена
- post-commit.sh: fallback auto-entry если агент забыл
- BLOCKING RULE в CLAUDE.md
- Auto-Generated Summaries секция в activeContext.md
- Синхронизировал шаблоны new-project
**Decided:** WARNING mode для pre-commit (не блокирует CI/CD)
**Learned:** Wave analysis показал 100% parallelization → все задачи Wave 1 независимы
**Next:** Установить hooks и протестировать

### 2026-01-29 (сессия 1)
**Did:** Создал структуру memory/ и adr/, обновил CLAUDE.md шаблона
**Decided:** AUTO-BEHAVIORS подход вместо команд
**Learned:** Система должна быть полностью автоматической
**Next:** Обновить upgrade-project, протестировать
