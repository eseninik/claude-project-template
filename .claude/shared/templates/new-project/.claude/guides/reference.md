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

## Commit Message Format

```
type: short description

Longer explanation if needed.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**Types:** feat, fix, refactor, test, docs, chore

---

## Когда использовать

Справочная информация. Загружай если забыл синтаксис команд.
