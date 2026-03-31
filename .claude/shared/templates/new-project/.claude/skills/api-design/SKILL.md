---
name: api-design
description: REST API design patterns — resource naming, status codes, pagination, filtering, error responses, versioning. Use when designing or reviewing API endpoints. Do NOT use for internal function interfaces or CLI tools.
roles: [coder, coder-complex, qa-reviewer]
---

# API Design Patterns

## When to Activate

- Designing new API endpoints
- Reviewing existing API contracts
- Adding pagination, filtering, or sorting
- Implementing error handling for APIs
- Planning API versioning strategy

## Resource URL Structure

```
GET    /api/v1/users           # List
GET    /api/v1/users/:id       # Get one
POST   /api/v1/users           # Create
PUT    /api/v1/users/:id       # Replace
PATCH  /api/v1/users/:id       # Update
DELETE /api/v1/users/:id       # Delete

# Sub-resources
GET    /api/v1/users/:id/orders

# Actions (use verbs sparingly)
POST   /api/v1/orders/:id/cancel
```

**Rules:** nouns, plural, lowercase, kebab-case. Query params for filtering.

## Status Codes

| Code | When |
|------|------|
| 200 | Success with body |
| 201 | Created (POST) |
| 204 | Success, no body (DELETE) |
| 400 | Bad request / validation error |
| 401 | Not authenticated |
| 403 | Forbidden (authenticated but no access) |
| 404 | Resource not found |
| 409 | Conflict (duplicate, version mismatch) |
| 422 | Unprocessable entity |
| 429 | Rate limited |
| 500 | Server error |

## Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": [
      { "field": "email", "message": "Invalid format" }
    ]
  }
}
```

## Pagination

```
GET /api/v1/users?limit=20&offset=0

Response:
{
  "data": [...],
  "pagination": {
    "total": 150,
    "limit": 20,
    "offset": 0,
    "hasMore": true
  }
}
```

## Key Rules

1. **Consistent error format** across all endpoints
2. **Always validate input** — use Zod/Pydantic at boundaries
3. **Version from day one** — /api/v1/
4. **Rate limit all public endpoints** — return 429 + Retry-After header
5. **Log every request** — method, path, status, duration, user_id

## Related

- [backend-patterns](./../backend-patterns/SKILL.md) — repository/service layers and DB optimization
- [security-review](./../security-review/SKILL.md) — auth, input validation, OWASP top 10
- [coding-standards](./../coding-standards/SKILL.md) — universal code quality and naming standards
