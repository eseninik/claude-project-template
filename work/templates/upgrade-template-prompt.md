# Универсальный промпт для обновления проекта до v2.0

```
Обнови этот проект до версии template из "c:/Bots/Migrator bots/claude-project-template-update/" (commit b0dbba0 - universal parallelization detection):

1. Проанализируй текущий CLAUDE.md и SKILLS_INDEX.md
2. Сравни с template версией из указанной папки
3. Скопируй недостающие файлы (.claude/knowledge/parallelization-patterns.md, .claude/skills/task-decomposition/)
4. Обнови CLAUDE.md и SKILLS_INDEX.md согласно изменениям в template (AUTO-CHECK вариант C, checkpoint format, task-decomposition skill)
5. Сохрани все project-specific настройки без изменений
6. Покажи diff для подтверждения
7. Закоммить как "feat: upgrade to v2.0 - universal parallelization (b0dbba0)"
```

---

## Что получите

- ✅ Универсальное определение параллелизации (tasks/*.md, plan.md, память агента)
- ✅ База знаний паттернов для автоматического анализа
- ✅ Контекстный анализ задач без явного плана
- ✅ Автоматическое создание tasks/*.md по запросу
