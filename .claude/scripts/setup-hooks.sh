#!/bin/bash
# Установка git hooks для автоматического обновления памяти проекта
#
# Использование:
#   ./.claude/scripts/setup-hooks.sh
#
# Что делает:
#   - Создаёт симлинки на hooks в .git/hooks/
#   - Делает их исполняемыми

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HOOKS_SOURCE="$PROJECT_ROOT/.claude/hooks"
HOOKS_TARGET="$PROJECT_ROOT/.git/hooks"

echo "Setting up git hooks..."

# Проверяем что мы в git репозитории
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo "Error: Not a git repository"
    exit 1
fi

# Создаём директорию hooks если её нет
mkdir -p "$HOOKS_TARGET"

# Устанавливаем post-commit hook
if [ -f "$HOOKS_SOURCE/post-commit.sh" ]; then
    ln -sf "../../.claude/hooks/post-commit.sh" "$HOOKS_TARGET/post-commit"
    chmod +x "$HOOKS_TARGET/post-commit"
    echo "  post-commit hook installed"
fi

# Устанавливаем pre-commit hook если есть
if [ -f "$HOOKS_SOURCE/pre-commit.sh" ]; then
    ln -sf "../../.claude/hooks/pre-commit.sh" "$HOOKS_TARGET/pre-commit"
    chmod +x "$HOOKS_TARGET/pre-commit"
    echo "  pre-commit hook installed"
fi

# Устанавливаем prepare-commit-msg hook если есть
if [ -f "$HOOKS_SOURCE/prepare-commit-msg.sh" ]; then
    ln -sf "../../.claude/hooks/prepare-commit-msg.sh" "$HOOKS_TARGET/prepare-commit-msg"
    chmod +x "$HOOKS_TARGET/prepare-commit-msg"
    echo "  prepare-commit-msg hook installed"
fi

echo ""
echo "Git hooks installed successfully!"
echo ""
echo "Installed hooks will:"
echo "  - pre-commit: Warn if memory not updated (non-blocking)"
echo "  - post-commit: Fallback auto-entry if agent didn't update memory"
echo ""
echo "To uninstall, remove symlinks from .git/hooks/"
