---
name: coding-standards
description: Universal coding standards and best practices for code quality, naming, structure, error handling. Use when reviewing code quality or starting new modules. Do NOT use for language-specific rules (see language-rules guides).
roles: [coder, coder-complex, qa-reviewer]
---

# Coding Standards

## When to Activate

- Starting a new project or module
- Reviewing code for quality and maintainability
- Refactoring existing code
- Onboarding new contributors

## Principles

1. **Readability First** — code is read more than written
2. **KISS** — simplest solution that works
3. **DRY** — extract common logic, but don't over-abstract (3 duplications = extract)
4. **YAGNI** — don't build features before needed

## Naming

| Entity | Convention | Example |
|--------|-----------|---------|
| Variables | camelCase (JS/TS) / snake_case (Python) | `userName`, `user_name` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES` |
| Functions | verb + noun | `getUserById`, `calculate_total` |
| Classes | PascalCase | `UserService` |
| Booleans | is/has/can/should prefix | `isActive`, `hasPermission` |
| Files | kebab-case (JS) / snake_case (Python) | `user-service.ts`, `user_service.py` |

## Function Design

- **Single responsibility** — one function, one purpose
- **Max 3 parameters** — use options object/dataclass beyond that
- **Early returns** — guard clauses reduce nesting
- **Pure functions preferred** — same input = same output, no side effects

## Error Handling

- **Validate at boundaries** — user input, external APIs, file I/O
- **Specific exceptions** — `raise ValueError("email required")` not `raise Exception`
- **Never swallow errors** — always log with context
- **Structured logging** — entry, exit, errors (see logging-standards guide)

## File Organization

- **One concept per file** — don't mix concerns
- **Max ~300 lines** — split if larger
- **Group by feature** not by type (feature/ > controllers/, services/, etc.)
- **Index files** for public API re-exports

## Code Smells to Avoid

- Functions > 50 lines
- Nesting > 3 levels deep
- Boolean parameters (use enum or separate functions)
- Magic numbers (extract to named constants)
- Commented-out code (delete it, git has history)

## Related

- [tdd-workflow](./../tdd-workflow/SKILL.md) — test-driven development with RED-GREEN-REFACTOR
- [security-review](./../security-review/SKILL.md) — security checklist and input validation
- [api-design](./../api-design/SKILL.md) — REST API design and error format standards
