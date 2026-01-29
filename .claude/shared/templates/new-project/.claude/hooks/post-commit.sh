#!/bin/bash
# Post-commit hook: fallback запись если агент не обновил память
#
# Логика:
# 1. Если агент обновил память (activeContext.md в коммите) → exit
# 2. Если агент НЕ обновил → добавить Auto-Generated запись
#
# Установка:
# ln -sf ../../.claude/hooks/post-commit.sh .git/hooks/post-commit
# chmod +x .git/hooks/post-commit

MEMORY_FILE=".claude/memory/activeContext.md"
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)
COMMIT_MSG=$(git log -1 --pretty=%B | head -1)
COMMIT_HASH=$(git log -1 --pretty=%h)
FILES_CHANGED=$(git diff-tree --no-commit-id --name-only -r HEAD | wc -l | tr -d ' ')

# Проверяем существование файла памяти
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
