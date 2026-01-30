# Project: [PROJECT NAME]

> **[ONE SENTENCE - WHAT THIS PROJECT IS ABOUT]**

---

## How This Project Works

**Context:** `.claude/skills/project-knowledge/` — architecture, patterns, git workflow, database, deployment.

**Memory:** `.claude/memory/activeContext.md` — session bridge, decisions, learned patterns.

**ADR:** `.claude/adr/` — architecture decision records.

**Default branch:** `dev`

---

# AUTO-BEHAVIORS

> Агент выполняет автоматически, БЕЗ команд пользователя.

---

## SESSION START (always)

```
1. Read .claude/memory/activeContext.md
2. Read work/STATE.md
3. IF unfinished work exists:
   → Tell user: "Продолжаю: [task]. Контекст: [recent decisions]"
4. ELSE:
   → Tell user: "Готов к новой задаче"
```

---

## BEFORE CODE CHANGES (always)

```
TRIGGER: User asks to implement/change/fix something

1. Read .claude/skills/project-knowledge/guides/architecture.md
2. Read .claude/skills/project-knowledge/guides/patterns.md
3. IF database-related:
   → Read .claude/skills/project-knowledge/guides/database.md
4. IF API-related:
   → Read .claude/skills/project-knowledge/guides/features.md
5. Check .claude/adr/decisions.md for relevant decisions
```

---

## AFTER TASK COMPLETION (always)

```
TRIGGER: Task is done, tests pass, verified

1. Update .claude/memory/activeContext.md:
   - Add to Session Log: date, what did, what decided, what learned
   - Update Recent Decisions if any
   - Update Learned Patterns if discovered something
   - Set Next Steps

2. Update work/STATE.md:
   - Current Work section
   - Session Notes

3. IF architectural decision was made:
   → Create .claude/adr/NNN-name.md
   → Update .claude/adr/decisions.md INDEX

4. Commit with meaningful message
```

---

## AFTER SESSION END (always)

```
TRIGGER: User ends session OR context limit approaching

1. Update .claude/memory/activeContext.md:
   - Current Focus: what was being worked on
   - Next Steps: what to do next
   - Session Log: summary of session

2. Update work/STATE.md:
   - Where stopped
   - Why stopped

3. Tell user: "Сессия сохранена. Следующие шаги: [list]"
```

---

## ON ERROR/BUG (always)

```
TRIGGER: Something breaks, test fails, unexpected behavior

1. Check .claude/memory/activeContext.md → Learned Patterns → Gotchas
2. Check if similar issue was solved before
3. IF solved before:
   → Apply known solution
4. ELSE:
   → Debug, fix, then add to Gotchas
```

---

## ON ARCHITECTURE DECISION (always)

```
TRIGGER: Choosing technology, changing data structure, new integration pattern

1. Check .claude/adr/decisions.md for existing decisions
2. IF contradicts existing decision:
   → Explain why change is needed
   → Get user confirmation
3. Create new ADR using .claude/adr/_template.md
4. Update .claude/adr/decisions.md INDEX
5. Update .claude/memory/activeContext.md → Recent Decisions
```

---

# HARD CONSTRAINTS

| Constraint | Reason |
|------------|--------|
| No data deletion without confirmation | Irreversible |
| No committing secrets | Security |
| No push to main without permission | Production stability |
| No "done" without verification | Honesty |
| Always update memory after work | Context preservation |
| No commit without memory update | Context loss between sessions |

---

# BLOCKING RULES

## Plan Detected (BLOCKING)

ENFORCE VIA: `cat .claude/guides/plan-execution-enforcer.md`
BLOCK: Cannot start implementation without valid checkpoint output

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

---

# KNOWLEDGE LOCATIONS

| Need | Location |
|------|----------|
| Project architecture | `.claude/skills/project-knowledge/guides/architecture.md` |
| Code patterns | `.claude/skills/project-knowledge/guides/patterns.md` |
| Database schema | `.claude/skills/project-knowledge/guides/database.md` |
| Features list | `.claude/skills/project-knowledge/guides/features.md` |
| Git workflow | `.claude/skills/project-knowledge/guides/git-workflow.md` |
| Deployment | `.claude/skills/project-knowledge/guides/deployment.md` |
| Session context | `.claude/memory/activeContext.md` |
| Task state | `work/STATE.md` |
| Architecture decisions | `.claude/adr/decisions.md` |

---

# FORBIDDEN

- Starting work without reading memory/activeContext.md
- Finishing work without updating memory
- Making architecture decisions without checking ADR
- Saying "done" without running tests
- Ignoring Learned Patterns → Gotchas
