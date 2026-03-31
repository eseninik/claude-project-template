---
name: backend-patterns
description: Backend architecture patterns — repository/service layers, database optimization, caching, middleware, background jobs. Use when building server-side APIs or services. Do NOT use for frontend or CLI tools.
roles: [coder, coder-complex]
---

# Backend Development Patterns

## When to Activate

- Designing API endpoints (REST/GraphQL)
- Implementing repository, service, or controller layers
- Optimizing database queries (N+1, indexing, connection pooling)
- Adding caching (Redis, in-memory, HTTP headers)
- Setting up background jobs or async processing

## Layered Architecture

```
Controller/Router  →  Service  →  Repository  →  Database
      ↓                  ↓            ↓
   Validation        Business      Data Access
   Serialization     Logic         Queries
```

### Repository Pattern

```python
class UserRepository:
    async def find_by_id(self, user_id: int) -> User | None:
        return await db.execute(select(User).where(User.id == user_id))

    async def create(self, data: CreateUserDTO) -> User:
        user = User(**data.model_dump())
        db.add(user)
        await db.commit()
        return user
```

### Service Layer

```python
class UserService:
    def __init__(self, repo: UserRepository, cache: CacheService):
        self.repo = repo
        self.cache = cache

    async def get_user(self, user_id: int) -> User:
        cached = await self.cache.get(f"user:{user_id}")
        if cached:
            return cached
        user = await self.repo.find_by_id(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        await self.cache.set(f"user:{user_id}", user, ttl=300)
        return user
```

## Database Optimization

- **N+1 Problem:** Use eager loading / `joinedload()` / `selectinload()`
- **Indexing:** Index columns used in WHERE, JOIN, ORDER BY
- **Connection pooling:** Use pool (SQLAlchemy pool_size, pgBouncer)
- **Pagination:** Always paginate list endpoints (LIMIT + OFFSET or cursor)

## Caching Strategy

| Layer | TTL | Use For |
|-------|-----|---------|
| In-memory | 1-5 min | Config, feature flags |
| Redis | 5-60 min | User sessions, API responses |
| HTTP Cache-Control | varies | Static assets, rarely changing data |

## Key Rules

1. **Never put business logic in controllers** — controllers only: validate, call service, serialize
2. **Always use transactions** for multi-step writes
3. **Log every external call** — DB queries, API calls, cache hits/misses
4. **Rate limit all endpoints** — protect against abuse
5. **Validate at boundaries** — never trust user input

## Related

- [api-design](./../api-design/SKILL.md) — REST API resource naming and error formats
- [database-migrations](./../database-migrations/SKILL.md) — safe schema changes and rollback strategies
- [docker-patterns](./../docker-patterns/SKILL.md) — Docker and Compose for containerized services
- [security-review](./../security-review/SKILL.md) — auth, input validation, OWASP top 10
