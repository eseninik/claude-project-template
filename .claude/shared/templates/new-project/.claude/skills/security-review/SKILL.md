---
name: security-review
description: Security review checklist for code — secrets management, input validation, auth, OWASP top 10. Use when implementing auth, handling user input, working with secrets, creating API endpoints, or reviewing security-sensitive code. Do NOT use for infrastructure/network security.
roles: [qa-reviewer, coder, coder-complex]
---

# Security Review

## When to Activate

- Implementing authentication or authorization
- Handling user input or file uploads
- Creating new API endpoints
- Working with secrets or credentials
- Implementing payment features
- Storing or transmitting sensitive data

## Security Checklist

### 1. Secrets Management

```python
# NEVER: hardcoded secrets
api_key = "sk-proj-xxxxx"

# ALWAYS: environment variables
api_key = os.environ["API_KEY"]
if not api_key:
    raise RuntimeError("API_KEY not configured")
```

- [ ] No hardcoded API keys, tokens, or passwords
- [ ] All secrets in environment variables
- [ ] `.env` files in `.gitignore`
- [ ] No secrets in git history (`git log -p | grep -i "password\|secret\|key"`)

### 2. Input Validation

```python
# ALWAYS validate at boundaries
from pydantic import BaseModel, EmailStr, constr

class CreateUser(BaseModel):
    email: EmailStr
    name: constr(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)
```

- [ ] All user inputs validated (type, length, format)
- [ ] SQL injection prevented (parameterized queries only)
- [ ] XSS prevented (sanitize HTML output, CSP headers)
- [ ] Path traversal prevented (no user input in file paths)

### 3. Authentication & Authorization

- [ ] Passwords hashed with bcrypt/argon2 (NEVER MD5/SHA1)
- [ ] JWTs have short expiry + refresh tokens
- [ ] Rate limiting on login endpoints
- [ ] Authorization checked on EVERY endpoint (not just frontend)
- [ ] CORS configured (not `*` in production)

### 4. Data Protection

- [ ] Sensitive data encrypted at rest
- [ ] HTTPS enforced (HSTS headers)
- [ ] Logs don't contain PII, tokens, or passwords
- [ ] Error messages don't leak internal details
- [ ] File uploads validated (type, size, content)

### 5. Dependencies

- [ ] No known vulnerabilities (`npm audit`, `pip-audit`, `cargo audit`)
- [ ] Dependencies pinned to specific versions
- [ ] Minimal dependencies (fewer = smaller attack surface)

## Key Rules

1. **Never trust user input** — validate everything at boundaries
2. **Principle of least privilege** — minimal permissions everywhere
3. **Defense in depth** — multiple layers of security
4. **Log security events** — auth failures, permission denials, suspicious patterns
5. **Fail securely** — on error, deny access (don't default to allow)

## Related

- [api-design](./../api-design/SKILL.md) — REST API resource naming and error formats
- [backend-patterns](./../backend-patterns/SKILL.md) — repository/service layers and DB optimization
- [coding-standards](./../coding-standards/SKILL.md) — universal code quality and naming standards
- [verification-before-completion](~/.claude/skills/verification-before-completion/SKILL.md) — evidence-based completion gate
