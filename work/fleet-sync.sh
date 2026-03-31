#!/bin/bash
# Fleet sync: copy ECC integration files + git hook fixes to a target project
# Usage: bash work/fleet-sync.sh "/path/to/target/project"

set -e

TARGET="$1"
SRC="C:/Bots/Migrator bots/claude-project-template-update"

if [ -z "$TARGET" ] || [ ! -d "$TARGET/.claude" ]; then
  echo "ERROR: Target project not found or missing .claude/: $TARGET"
  exit 1
fi

echo "Syncing to: $TARGET"

# --- 1. Hooks (all 10 + __pycache__ exclusion) ---
for hook in hook_base.py codex-parallel.py codex-review.py config-protection.py write-validate.py session-orient.py pre-compact-save.py task-completed-gate.py tool-failure-logger.py truthguard.py; do
  cp "$SRC/.claude/hooks/$hook" "$TARGET/.claude/hooks/$hook" 2>/dev/null && echo "  Hook: $hook"
done

# --- 2. New skills (13 + learn-eval) ---
for skill in tdd-workflow api-design coding-standards e2e-testing docker-patterns deployment-patterns backend-patterns frontend-patterns continuous-learning cost-aware-llm-pipeline database-migrations security-review learn-eval; do
  mkdir -p "$TARGET/.claude/skills/$skill"
  cp "$SRC/.claude/skills/$skill/SKILL.md" "$TARGET/.claude/skills/$skill/SKILL.md"
done
echo "  Skills: 13 synced"

# --- 3. Language rules ---
mkdir -p "$TARGET/.claude/guides/language-rules"
cp "$SRC/.claude/guides/language-rules/"*.md "$TARGET/.claude/guides/language-rules/"
echo "  Language rules: synced"

# --- 4. Security guide ---
cp "$SRC/.claude/guides/agentic-security.md" "$TARGET/.claude/guides/agentic-security.md"
echo "  Security guide: synced"

# --- 5. Schemas ---
mkdir -p "$TARGET/.claude/schemas"
cp "$SRC/.claude/schemas/"*.json "$TARGET/.claude/schemas/"
echo "  Schemas: synced"

# --- 6. Validate script ---
cp "$SRC/.claude/scripts/validate-configs.py" "$TARGET/.claude/scripts/validate-configs.py" 2>/dev/null
echo "  Validate script: synced"

# --- 7. learn-eval command ---
mkdir -p "$TARGET/.claude/commands"
cp "$SRC/.claude/commands/learn-eval.md" "$TARGET/.claude/commands/learn-eval.md"
echo "  Command: learn-eval synced"

# --- 8. Settings.json (merge PreToolUse hook, don't overwrite) ---
# Each project has its own settings, so we only add config-protection if missing
if ! grep -q "config-protection" "$TARGET/.claude/settings.json" 2>/dev/null; then
  echo "  Settings: config-protection hook needs manual add (project has custom settings)"
else
  echo "  Settings: config-protection already present"
fi

# --- 9. Git hooks fix (pre-commit + post-commit) ---
if [ -f "$TARGET/.git/hooks/post-commit" ]; then
  # Fix post-commit: grep -c || echo "0" -> grep -cF || true
  sed -i 's/grep -c "$MEMORY_FILE" || echo "0"/grep -cF "$MEMORY_FILE" || true/g' "$TARGET/.git/hooks/post-commit"
  # Fix post-commit: [ "$VAR" -gt "0" ] -> [ "${VAR:-0}" -gt 0 ]
  sed -i 's/\[ "$MEMORY_IN_COMMIT" -gt "0" \]/[ "${MEMORY_IN_COMMIT:-0}" -gt 0 ]/g' "$TARGET/.git/hooks/post-commit"
  echo "  Git post-commit: fixed"
fi

if [ -f "$TARGET/.git/hooks/pre-commit" ]; then
  # Copy our fixed pre-commit
  cp "$SRC/.git/hooks/pre-commit" "$TARGET/.git/hooks/pre-commit"
  echo "  Git pre-commit: replaced with fixed version"
fi

echo "DONE: $TARGET"
