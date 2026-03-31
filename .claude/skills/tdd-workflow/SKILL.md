---
name: tdd-workflow
description: Test-driven development workflow enforcing RED-GREEN-REFACTOR cycle with 80%+ coverage. Use when writing new features, fixing bugs, or refactoring code. Do NOT use for documentation-only changes or config updates.
roles: [coder, coder-complex, qa-fixer]
---

# Test-Driven Development Workflow

## When to Activate

- Writing new features or API endpoints
- Fixing bugs (write failing test first, then fix)
- Refactoring existing code
- Adding new components or services

## Core Process: RED-GREEN-REFACTOR

### 1. RED — Write Failing Test First
```
- Write test that describes desired behavior
- Run test — MUST fail (proves test catches the issue)
- Git checkpoint: `git commit -m "test: RED - {what}"`
```

### 2. GREEN — Minimal Implementation
```
- Write MINIMUM code to make the test pass
- No extra features, no premature optimization
- Run test — MUST pass
- Git checkpoint: `git commit -m "feat: GREEN - {what}"`
```

### 3. REFACTOR — Clean Up (Optional)
```
- Improve code quality without changing behavior
- All tests MUST still pass after refactoring
- Git checkpoint: `git commit -m "refactor: {what}"`
```

## Coverage Requirements

- **Minimum 80%** combined (unit + integration + E2E)
- All edge cases and error scenarios tested
- Boundary conditions verified

## Test Types

| Type | Scope | Tools |
|------|-------|-------|
| Unit | Functions, utilities, pure logic | pytest, vitest, jest |
| Integration | API endpoints, DB operations, services | pytest + httpx, supertest |
| E2E | User flows, browser automation | Playwright |

## Key Rules

1. **NEVER write implementation before test** — test defines the contract
2. **One test at a time** — don't batch; RED-GREEN per behavior
3. **Tests are immutable after approval** — Evaluation Firewall: don't modify tests to make them pass
4. **Run full suite before commit** — no regressions allowed
5. **Include structured logging in all new code** — entry, exit, errors

## Related

- [coding-standards](./../coding-standards/SKILL.md) — universal code quality and naming standards
- [e2e-testing](./../e2e-testing/SKILL.md) — Playwright browser automation tests
- [qa-validation-loop](~/.claude/skills/qa-validation-loop/SKILL.md) — risk-proportional QA review cycle
- [verification-before-completion](~/.claude/skills/verification-before-completion/SKILL.md) — evidence-based completion gate
