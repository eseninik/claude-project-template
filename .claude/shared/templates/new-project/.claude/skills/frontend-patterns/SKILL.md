---
name: frontend-patterns
description: Frontend patterns for React/Next.js — component composition, state management, data fetching, performance optimization. Use when building UI components or client-side logic. Do NOT use for backend/API code.
roles: [coder, coder-complex]
---

# Frontend Development Patterns

## When to Activate

- Building React/Next.js components
- Managing state (useState, Zustand, Context)
- Implementing data fetching (SWR, React Query, server components)
- Optimizing rendering performance
- Working with forms and validation

## Component Patterns

### Composition Over Inheritance

```tsx
function Card({ children, variant = 'default' }) {
  return <div className={`card card-${variant}`}>{children}</div>
}

function CardHeader({ children }) {
  return <div className="card-header">{children}</div>
}

// Usage
<Card>
  <CardHeader>Title</CardHeader>
  <p>Content</p>
</Card>
```

### Container/Presenter Split

```tsx
// Container: data + logic
function UserListContainer() {
  const { data, isLoading } = useSWR('/api/users')
  if (isLoading) return <Skeleton />
  return <UserList users={data} />
}

// Presenter: pure rendering
function UserList({ users }: { users: User[] }) {
  return <ul>{users.map(u => <li key={u.id}>{u.name}</li>)}</ul>
}
```

## State Management

| Scope | Solution | When |
|-------|----------|------|
| Component-local | `useState` | Simple toggle, input value |
| Cross-component | Context or Zustand | Theme, auth, cart |
| Server state | SWR / React Query | API data, pagination |
| URL state | `useSearchParams` | Filters, pagination, sort |
| Form state | React Hook Form + Zod | Complex forms with validation |

## Performance

- **`React.memo`** — only for expensive renders with stable props
- **`useMemo`/`useCallback`** — only when profiler shows re-render issue
- **Code splitting** — `lazy()` + `Suspense` for routes
- **Image optimization** — `next/image` with width/height
- **Virtualization** — `@tanstack/virtual` for long lists (1000+ items)

## Key Rules

1. **Server Components by default** (Next.js) — add `"use client"` only when needed
2. **Colocate state** — keep state as close to where it's used as possible
3. **Don't over-abstract** — 3 similar components is better than premature abstraction
4. **Accessible by default** — semantic HTML, aria labels, keyboard navigation

## Related

- [e2e-testing](./../e2e-testing/SKILL.md) — Playwright browser automation tests
- [coding-standards](./../coding-standards/SKILL.md) — universal code quality and naming standards
- [cost-aware-llm-pipeline](./../cost-aware-llm-pipeline/SKILL.md) — LLM API cost optimization patterns
