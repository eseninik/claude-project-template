---
name: docker-patterns
description: Docker and Docker Compose patterns for local development, multi-stage builds, security, networking, volumes. Use when containerizing apps or designing multi-service architectures. Do NOT use for Kubernetes/orchestration patterns.
roles: [coder, coder-complex]
---

# Docker Patterns

## When to Activate

- Setting up Docker Compose for local dev
- Writing or reviewing Dockerfiles
- Designing multi-container architectures
- Troubleshooting networking or volume issues

## Multi-Stage Dockerfile

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --production=false
COPY . .
RUN npm run build

# Stage 2: Production
FROM node:20-alpine AS production
WORKDIR /app
RUN addgroup -g 1001 app && adduser -u 1001 -G app -s /bin/sh -D app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY package*.json ./
USER app
EXPOSE 3000
HEALTHCHECK --interval=30s CMD wget -qO- http://localhost:3000/health || exit 1
CMD ["node", "dist/index.js"]
```

## Docker Compose for Dev

```yaml
services:
  app:
    build:
      context: .
      target: dev
    ports: ["3000:3000"]
    volumes:
      - .:/app
      - /app/node_modules    # anonymous volume preserves container deps
    depends_on:
      db: { condition: service_healthy }

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: app_dev
      POSTGRES_PASSWORD: dev_password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      retries: 5
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

## Security Checklist

- Run as non-root user (`USER app`)
- Use specific image tags (not `latest`)
- Multi-stage builds (no build tools in production)
- No secrets in Dockerfile (use build args or runtime env)
- Scan images: `docker scout cves`
- Read-only root filesystem where possible

## Networking Rules

- Services on same compose network communicate by service name
- Only expose ports you need externally
- Use `internal: true` for backend-only networks

## Key Rules

1. **Always use healthchecks** — `depends_on: condition: service_healthy`
2. **Anonymous volumes for node_modules** — prevents host overwriting container deps
3. **`.dockerignore`** — exclude node_modules, .git, .env, tests
4. **restart: unless-stopped** on all production services

## Related

- [deployment-patterns](./../deployment-patterns/SKILL.md) — CI/CD pipelines and deploy strategies
- [infrastructure](~/.claude/skills/infrastructure/SKILL.md) — dev infrastructure setup and automation
- [backend-patterns](./../backend-patterns/SKILL.md) — repository/service layers and DB optimization
