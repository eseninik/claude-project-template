# План: Трёхуровневая система памяти проекта

## Цель

Гарантировать что после каждого изменения кода в памяти проекта сохраняется **полная информация**: что сделали, какие решения приняли, что узнали.

---

## Архитектура

```
┌────────────────────────────────────────────────────────┐
│  УРОВЕНЬ 1: Агент пишет детальное описание             │
│  (Did / Decided / Learned / Next)                      │
│  ↓                                                     │
│  УРОВЕНЬ 2: Pre-commit проверяет что память обновлена  │
│  → WARNING если нет (не блокирует)                     │
│  ↓                                                     │
│  УРОВЕНЬ 3: Post-commit записывает техническую инфо    │
│  → Fallback если агент забыл                           │
└────────────────────────────────────────────────────────┘
```

---

## Файлы для создания/изменения

### Создать

| Файл | Описание |
|------|----------|
| `.claude/hooks/pre-commit.sh` | Проверка обновления памяти (WARNING) |
| `.claude/memory/archive/.gitkeep` | Директория для архива |
| `.claude/shared/templates/new-project/.claude/hooks/pre-commit.sh` | Копия для шаблона |

### Изменить

| Файл | Что изменить |
|------|--------------|
| `CLAUDE.md` | Добавить BLOCKING RULE для памяти |
| `.claude/hooks/post-commit.sh` | Логика fallback (только если агент не обновил) |
| `.claude/memory/activeContext.md` | Добавить секцию Auto-Generated |
| `.claude/scripts/setup-hooks.sh` | Информация об установке |
| `.claude/shared/templates/new-project/...` | Синхронизировать шаблоны |

---

## Детали реализации

### 1. Pre-commit hook (`.claude/hooks/pre-commit.sh`)

**Логика:**
```
1. Проверить есть ли code changes (не только .md)
2. Проверить что activeContext.md в staged changes
3. Если нет → показать WARNING с чеклистом
4. Спросить продолжать? (y/N)
5. Non-interactive mode → только warning, не блок
```

**Код:**
```bash
#!/bin/bash
# Pre-commit hook: проверяет обновление памяти проекта
#
# WARNING mode: не блокирует, только предупреждает

set -e

MEMORY_FILE=".claude/memory/activeContext.md"
WARNING_COLOR="\033[33m"
RESET_COLOR="\033[0m"

# Проверяем что есть code changes (не только .md или .claude)
CODE_CHANGES=$(git diff --cached --name-only | grep -v '\.md$' | grep -v '\.claude/' | head -1 || true)

if [ -z "$CODE_CHANGES" ]; then
    exit 0
fi

# Проверяем что activeContext.md в staged
if ! git diff --cached --name-only | grep -q "$MEMORY_FILE"; then
    echo ""
    echo -e "${WARNING_COLOR}========================================"
    echo -e "  WARNING: Memory not updated!"
    echo -e "========================================${RESET_COLOR}"
    echo ""
    echo "You're committing code but activeContext.md is not staged."
    echo ""
    echo "Memory checklist:"
    echo "  [ ] Did: что конкретно сделал"
    echo "  [ ] Decided: какие решения принял"
    echo "  [ ] Learned: что узнал, gotchas"
    echo "  [ ] Next: что дальше"
    echo ""
    echo "To update: edit $MEMORY_FILE, then git add it"
    echo "To skip: git commit --no-verify"
    echo ""

    if [ -t 0 ]; then
        read -p "Continue without updating memory? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

exit 0
```

### 2. Изменения в CLAUDE.md

**Добавить в секцию BLOCKING RULES:**
```markdown
## Before Commit (BLOCKING)

```
TRIGGER: About to run git commit

BLOCK: Do NOT commit until memory is updated

1. VERIFY activeContext.md is staged (git status)
2. IF not staged:
   a. Update .claude/memory/activeContext.md with:
      - Did: конкретные изменения
      - Decided: выбор и обоснование
      - Learned: gotchas, что работает/не работает
      - Next: что осталось
   b. Stage: git add .claude/memory/activeContext.md
3. THEN proceed with commit
```
```

**Добавить в HARD CONSTRAINTS таблицу:**
```markdown
| Не коммитить без обновления памяти | Потеря контекста между сессиями |
```

### 3. Post-commit hook (обновить `.claude/hooks/post-commit.sh`)

**Новая логика — fallback только если агент не обновил:**
```bash
#!/bin/bash
# Post-commit hook: fallback запись если агент не обновил память

MEMORY_FILE=".claude/memory/activeContext.md"
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)
COMMIT_MSG=$(git log -1 --pretty=%B | head -1)
COMMIT_HASH=$(git log -1 --pretty=%h)
FILES_CHANGED=$(git diff-tree --no-commit-id --name-only -r HEAD | wc -l | tr -d ' ')

if [ ! -f "$MEMORY_FILE" ]; then
    exit 0
fi

# Проверяем: агент обновил память в этом коммите?
MEMORY_IN_COMMIT=$(git diff-tree --no-commit-id --name-only -r HEAD | grep -c "$MEMORY_FILE" || echo "0")

if [ "$MEMORY_IN_COMMIT" -gt "0" ]; then
    echo "Memory updated by agent ✓"
    exit 0
fi

# FALLBACK: агент НЕ обновил — записываем техническую инфо
echo "Memory NOT updated. Adding auto-generated entry..."

TEMP_FILE=$(mktemp)

# Проверяем есть ли секция Auto-Generated
if grep -q "## Auto-Generated Summaries" "$MEMORY_FILE"; then
    awk -v date="$DATE" -v time="$TIME" -v msg="$COMMIT_MSG" -v hash="$COMMIT_HASH" -v files="$FILES_CHANGED" '
    /^## Auto-Generated Summaries/ {
        print
        print ""
        print "### " date " " time " (commit `" hash "`)"
        print "**Message:** " msg
        print "**Files:** " files
        print ""
        next
    }
    { print }
    ' "$MEMORY_FILE" > "$TEMP_FILE"
else
    # Создаём секцию перед Session Log
    awk -v date="$DATE" -v time="$TIME" -v msg="$COMMIT_MSG" -v hash="$COMMIT_HASH" -v files="$FILES_CHANGED" '
    /^## Session Log/ {
        print "## Auto-Generated Summaries"
        print ""
        print "> Агент НЕ обновил память. Интегрировать при следующей сессии."
        print ""
        print "### " date " " time " (commit `" hash "`)"
        print "**Message:** " msg
        print "**Files:** " files
        print ""
        print "---"
        print ""
    }
    { print }
    ' "$MEMORY_FILE" > "$TEMP_FILE"
fi

mv "$TEMP_FILE" "$MEMORY_FILE"
echo "Auto-entry added to memory"
```

### 4. Секция в activeContext.md

**Добавить между "Next Steps" и "Session Log":**
```markdown
---

## Auto-Generated Summaries

> Записи добавляются post-commit когда агент не обновил память.
> При следующей сессии: интегрировать в Session Log и очистить.

---

## Session Log
```

---

## Порядок выполнения

1. [ ] Создать `.claude/hooks/pre-commit.sh`
2. [ ] Обновить `CLAUDE.md` — BLOCKING RULE
3. [ ] Обновить `.claude/hooks/post-commit.sh` — fallback логика
4. [ ] Обновить `.claude/memory/activeContext.md` — новая секция
5. [ ] Создать `.claude/memory/archive/.gitkeep`
6. [ ] Синхронизировать `.claude/shared/templates/new-project/`
7. [ ] Обновить `.claude/scripts/setup-hooks.sh`

---

## Verification

### Test 1: Коммит БЕЗ обновления памяти
```bash
echo "test" > test.py
git add test.py
git commit -m "test"
# → Должен показать WARNING
# → Ответить "n" → коммит отменён
rm test.py
```

### Test 2: Коммит С обновлением памяти
```bash
# Обновить activeContext.md
echo "test" > test.py
git add test.py .claude/memory/activeContext.md
git commit -m "test"
# → Проходит без warning
git reset --hard HEAD~1
```

### Test 3: Fallback
```bash
echo "test" > test.py
git add test.py
git commit --no-verify -m "test without memory"
# → Post-commit должен добавить Auto-Generated запись
git log -1
cat .claude/memory/activeContext.md | head -50
git reset --hard HEAD~1
```

---

## Edge Cases

| Случай | Поведение |
|--------|-----------|
| Только .md файлы в коммите | Pre-commit пропускает |
| Только .claude/ файлы | Pre-commit пропускает |
| CI/CD (non-interactive) | Warning без блока |
| `git commit --no-verify` | Post-commit всё равно сработает |
| Агент прерван mid-task | Post-commit запишет fallback |
