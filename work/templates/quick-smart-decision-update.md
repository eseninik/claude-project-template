# Quick Update: Smart Decision Making

## Что делать

Применить обновления из template проекта `claude-project-template-update` для умной логики принятия решений.

## Коротко

В template добавлена логика **волновой параллелизации**:
- Агент сам анализирует зависимости в плане
- Различает волновую структуру (Wave 1: [1,2] параллельно) vs строгую последовательность
- Автоматически выбирает оптимальный подход (tasks/*.md или executing-plans)
- Не спрашивает пользователя без необходимости

## Файлы изменений

```bash
# В template проекте смотри:
git show 5b9e6e9  # feat: intelligent dependency analysis
git show 0d81bd3  # feat: add wave parallelization detection
```

## Быстрое применение

```bash
# Скопируй из template в этот проект:
cp /path/to/claude-project-template-update/CLAUDE.md ./CLAUDE.md
cp /path/to/claude-project-template-update/.claude/guides/dependency-analysis.md ./.claude/guides/

git add CLAUDE.md .claude/guides/dependency-analysis.md
git commit -m "feat: add smart decision making from template"
```

## Или прочитай детали

```bash
cat work/templates/smart-decision-update-prompt.md
```

Там полная документация с примерами и вариантами применения.

---

**TL;DR:** Агент теперь сам выбирает параллельное выполнение для планов с волновой структурой. Экономия времени ~50% для типичных планов.
