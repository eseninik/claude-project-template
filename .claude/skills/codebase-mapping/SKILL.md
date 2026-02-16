---
name: codebase-mapping
description: |
  Automatically analyzes and documents existing codebase structure into codebase-map.md.
  Discovers tech stack, entry points, module organization, dependencies, and integration points.
  Use when starting work on an existing project, project-knowledge guides are empty/outdated, or after major refactoring.
  Does NOT apply to new projects built from scratch (nothing to map).
---

# Codebase Mapping

Automatically discover and document codebase structure for existing projects.

**Output:** `.claude/skills/project-knowledge/guides/codebase-map.md`

## Process

- [ ] Step 1: Analyze directory structure
- [ ] Step 2: Identify entry points
- [ ] Step 3: Analyze dependencies
- [ ] Step 4: Map modules
- [ ] Step 5: Identify integrations
- [ ] Step 6: Generate codebase-map.md
- [ ] Step 7: Suggest guide updates

### Step 1: Analyze Directory Structure

Use Glob tool to find source files (exclude noise directories):

```
Glob: **/*.py, **/*.ts, **/*.js, **/*.go
Exclude: node_modules/, __pycache__/, .git/, venv/, dist/
```

### Step 2: Identify Entry Points

Look for:
- `main.py`, `app.py`, `__main__.py` - Python entry
- `index.ts`, `index.js`, `server.ts` - Node entry
- `Dockerfile`, `docker-compose.yml` - Container config
- `setup.py`, `pyproject.toml`, `package.json` - Project config

Read entry points to understand startup flow.

### Step 3: Analyze Dependencies

**Python:**
```bash
cat requirements.txt 2>/dev/null
```
Or read `pyproject.toml` dependencies section.

**Node:**
Read `package.json` dependencies and devDependencies.

Identify: main framework, key libraries, critical versions.

### Step 4: Map Modules

Identify code organization pattern:

| Directory Pattern | Typical Content |
|-------------------|-----------------|
| `handlers/`, `routers/`, `controllers/` | Entry points, API endpoints |
| `services/`, `usecases/` | Business logic |
| `models/`, `entities/` | Data structures, ORM models |
| `repositories/`, `dal/` | Database access |
| `utils/`, `helpers/` | Shared utilities |
| `config/`, `settings/` | Configuration |
| `tests/` | Test files |

### Step 5: Identify Integrations

Search for:
- HTTP clients (requests, aiohttp, axios)
- Database connections (SQLAlchemy, Prisma, mongoose)
- External services (Redis, S3, email)
- Third-party APIs

### Step 6: Generate codebase-map.md

Write to `.claude/skills/project-knowledge/guides/codebase-map.md`:

```markdown
# Codebase Map

*Generated: [date]*

## Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.11 |
| Framework | aiogram | 3.x |

## Directory Structure

[tree representation of source directories]

## Entry Points

| File | Purpose |
|------|---------|
| src/main.py | Application entry |

## Key Modules

| Module | Purpose | Depends On |
|--------|---------|------------|
| handlers/ | Bot endpoints | services/ |
| services/ | Business logic | models/ |

## External Integrations

| Service | Used In | Purpose |
|---------|---------|---------|
| PostgreSQL | repositories/ | Primary database |

## Code Patterns

- Dependency Injection: [how]
- Error Handling: [how]
- Logging: [how]

## Testing

| Type | Location | Command |
|------|----------|---------|
| Unit | tests/unit/ | pytest tests/unit |

## Notes

- [Technical debt observations]
- [Non-obvious decisions]
```

### Step 7: Suggest Guide Updates

After generating map, check existing guides and suggest updates:

```markdown
codebase-map.md created.

**Recommend updating:**
- architecture.md - [what is outdated or missing]
- patterns.md - [new patterns discovered]
- database.md - [schema changes found]

Update now or later?
```

## Example

**Input:** Existing Python Telegram bot project with aiogram, SQLAlchemy, Redis

**Output:** codebase-map.md showing:
- Tech stack: Python 3.11, aiogram 3.x, SQLAlchemy 2.x, Redis
- Entry: src/main.py -> bot startup, router registration
- Modules: handlers/ -> services/ -> models/ -> repositories/
- Integrations: PostgreSQL, Redis, Telegram API
- Patterns: middleware-based DI, repository pattern, structured logging

## When to Re-run

- After major refactoring
- When adding new modules or services
- When architecture changes significantly
- Monthly for actively developed projects

## Edge Cases

- Monorepo with multiple services: map each service separately, document relationships
- No clear entry point: check scripts section of package.json or Makefile
- Mixed languages: document all, note primary language
- Very large codebase (>1000 files): focus on top-level structure first, detail key modules only
