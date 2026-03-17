# Planner Agent Memory

> Persistent memory for planner agents. First 200 lines auto-injected at startup.

## Patterns That Work

- Wave-based decomposition for 3+ independent tasks
- Decimal phase numbering for inserted phases (3.1, 3.2)
- Always check file dependencies before declaring tasks independent

## Patterns That Fail

- Declaring tasks independent when they modify the same file
- Plans with > 10 tasks in a single wave (quality degrades)
- Missing acceptance criteria in task definitions

## Project-Specific Knowledge

- Max 5 parallel agents for quality (3 is optimal)
- Template changes must sync to .claude/shared/templates/new-project/
- AO Fleet for cross-project, Agent Teams for in-project parallelism

## Recent History

| Date | Task | Outcome | Learning |
|------|------|---------|----------|
