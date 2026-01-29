# Task 02: Update CLAUDE.md with Memory Blocking Rule

**depends_on:** none
**files_modified:** `CLAUDE.md`
**wave:** 1

## Objective

Add BLOCKING RULE for memory update before commits.

## Specification

### Add to BLOCKING RULES section:

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

### Add to HARD CONSTRAINTS table:

```markdown
| Не коммитить без обновления памяти | Потеря контекста между сессиями |
```

## Acceptance Criteria

- [ ] BLOCKING RULES section has "Before Commit" rule
- [ ] HARD CONSTRAINTS table has memory constraint
