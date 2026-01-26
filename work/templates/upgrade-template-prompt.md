# Промпт для обновления до v2.0

**Короткий вариант (рекомендуется):**

```
Обнови проект до template v2.0 (commit b0dbba0): скопируй из "c:/Bots/Migrator bots/claude-project-template-update/" файлы .claude/knowledge/parallelization-patterns.md, .claude/skills/task-decomposition/, обнови CLAUDE.md (AUTO-CHECK вариант C строки 79-92 + checkpoint строки 89-100), SKILLS_INDEX.md (добавь task-decomposition в Entry Points и новую категорию TASK ANALYSIS), закоммить как "feat: upgrade to v2.0 (b0dbba0)".
```

---

## Детальный вариант (если нужны пошаговые инструкции)

<details>
<summary>Развернуть подробную инструкцию</summary>

```
Обнови этот проект до claude-project-template v2.0 (commit b0dbba0).

# Backup
cp CLAUDE.md CLAUDE.md.backup

# Копирование файлов template
mkdir -p .claude/knowledge
cp "c:/Bots/Migrator bots/claude-project-template-update/.claude/knowledge/parallelization-patterns.md" .claude/knowledge/

mkdir -p .claude/skills/task-decomposition
cp "c:/Bots/Migrator bots/claude-project-template-update/.claude/skills/task-decomposition/SKILL.md" .claude/skills/task-decomposition/

# Обновление CLAUDE.md
cat "c:/Bots/Migrator bots/claude-project-template-update/CLAUDE.md"

Найди строки 79-92 (AUTO-CHECK вариант C) и замени в моём CLAUDE.md.
Найди строки 89-100 (checkpoint format) и замени в моём CLAUDE.md.

# Обновление SKILLS_INDEX.md
Добавь в Entry Points:
| **Задача без явного плана** | `task-decomposition` | AUTO-CHECK вариант C |

Добавь категорию TASK ANALYSIS & DECOMPOSITION из template SKILLS_INDEX.md (строки 86-110).

# Верификация
cat CLAUDE.md | grep "Контекстный анализ"
cat .claude/knowledge/parallelization-patterns.md | head -20

# Git
git diff CLAUDE.md
git add CLAUDE.md .claude/knowledge/ .claude/skills/task-decomposition/ .claude/skills/SKILLS_INDEX.md
git commit -m "feat: upgrade to v2.0 - universal parallelization detection (b0dbba0)"
```

</details>

---

## Что получите

- ✅ Универсальное определение параллелизации (tasks/*.md, plan.md, память агента)
- ✅ База знаний паттернов
- ✅ Контекстный анализ задач без явного плана
- ✅ Автоматическое создание tasks/*.md по запросу
