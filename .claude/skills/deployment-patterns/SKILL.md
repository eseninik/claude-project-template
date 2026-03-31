---
name: deployment-patterns
description: Deployment strategies (rolling, blue-green, canary), CI/CD pipelines, health checks, rollback plans, production readiness checklists. Use when setting up deployments or CI/CD. Do NOT use for Docker internals (see docker-patterns).
roles: [coder, coder-complex]
---

# Deployment Patterns

## When to Activate

- Setting up CI/CD pipelines
- Planning deployment strategy
- Implementing health checks and readiness probes
- Preparing for production release

## Deployment Strategies

### Rolling (Default)
Replace instances gradually. Old + new run simultaneously.
- **Pros:** Zero downtime, gradual
- **Cons:** Two versions coexist — requires backward compatibility
- **Use when:** Standard deployments, backward-compatible changes

### Blue-Green
Two identical environments. Switch traffic atomically.
- **Pros:** Instant rollback, zero downtime
- **Cons:** 2x infrastructure cost during deploy
- **Use when:** High-risk releases, database-independent changes

### Canary
Route small % of traffic to new version. Gradually increase.
- **Pros:** Real-world testing with minimal blast radius
- **Cons:** Requires traffic splitting, monitoring
- **Use when:** Major changes needing gradual validation

## Health Check Pattern

```python
@app.get("/health")
async def health():
    checks = {
        "database": await check_db(),
        "redis": await check_redis(),
        "disk": check_disk_space(),
    }
    healthy = all(checks.values())
    return {"status": "healthy" if healthy else "degraded", "checks": checks}
```

## CI/CD Pipeline Template

```
1. Lint + Type check
2. Unit tests
3. Build artifact
4. Integration tests
5. Deploy to staging
6. E2E tests on staging
7. Deploy to production
8. Smoke tests on production
9. Monitor for 15min
```

## Production Readiness Checklist

- [ ] Health check endpoint returns 200
- [ ] Structured logging configured
- [ ] Error tracking (Sentry/equivalent) connected
- [ ] Environment variables documented
- [ ] Database migrations run before deploy
- [ ] Rollback plan documented
- [ ] Monitoring/alerts configured
- [ ] Secrets in env vars (not code)
- [ ] Rate limiting on public endpoints
- [ ] CORS configured properly

## Related

- [docker-patterns](./../docker-patterns/SKILL.md) — Docker and Compose for containerized services
- [infrastructure](~/.claude/skills/infrastructure/SKILL.md) — dev infrastructure setup and automation
- [e2e-testing](./../e2e-testing/SKILL.md) — Playwright browser automation tests
