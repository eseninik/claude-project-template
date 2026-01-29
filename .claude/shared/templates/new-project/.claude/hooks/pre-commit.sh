#!/bin/bash
# Pre-commit hook: проверяет обновление памяти проекта
#
# WARNING mode: не блокирует, только предупреждает
#
# Установка:
# ln -sf ../../.claude/hooks/pre-commit.sh .git/hooks/pre-commit
# chmod +x .git/hooks/pre-commit

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
