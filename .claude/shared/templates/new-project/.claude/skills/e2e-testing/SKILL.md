---
name: e2e-testing
description: Playwright E2E testing patterns — Page Object Model, selectors, CI/CD integration, flaky test strategies. Use when writing or reviewing browser automation tests. Do NOT use for unit or integration tests.
roles: [coder, coder-complex, qa-reviewer]
---

# E2E Testing with Playwright

## When to Activate

- Writing browser automation tests
- Setting up Playwright in a project
- Debugging flaky E2E tests
- Adding CI/CD test pipelines

## Project Structure

```
tests/
├── e2e/
│   ├── auth/login.spec.ts
│   ├── features/search.spec.ts
│   └── api/endpoints.spec.ts
├── fixtures/auth.ts
└── playwright.config.ts
```

## Page Object Model

```typescript
export class LoginPage {
  constructor(private page: Page) {}

  readonly email = this.page.locator('[data-testid="email"]')
  readonly password = this.page.locator('[data-testid="password"]')
  readonly submit = this.page.locator('[data-testid="login-btn"]')

  async login(email: string, password: string) {
    await this.email.fill(email)
    await this.password.fill(password)
    await this.submit.click()
    await this.page.waitForURL('/dashboard')
  }
}
```

## Selector Priority

1. `data-testid` (most stable)
2. `role` + accessible name
3. Text content (for static labels)
4. CSS class (last resort)

## Anti-Flakiness Patterns

- **Never use `page.waitForTimeout()`** — use `waitForSelector`, `waitForURL`, `waitForResponse`
- **Retry assertions** — `expect(locator).toHaveText('x', { timeout: 5000 })`
- **Isolate tests** — each test creates own data, no shared state
- **Parallel by file** — `fullyParallel: true` in config

## CI/CD Integration

```yaml
- name: E2E Tests
  run: npx playwright test
  env:
    CI: true
    BASE_URL: http://localhost:3000
- uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: playwright-report
    path: playwright-report/
```

## Key Rules

1. **data-testid everywhere** — never rely on CSS classes for testing
2. **Test user flows, not implementation** — click login, verify dashboard
3. **Max 30s per test** — if longer, break into smaller tests
4. **Screenshots on failure** — always configure artifact upload

## Related

- [tdd-workflow](./../tdd-workflow/SKILL.md) — test-driven development with RED-GREEN-REFACTOR
- [deployment-patterns](./../deployment-patterns/SKILL.md) — CI/CD pipelines and deploy strategies
- [frontend-patterns](./../frontend-patterns/SKILL.md) — React/Next.js component and state patterns
