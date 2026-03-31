---
name: database-migrations
description: Database migration patterns — safe schema changes, zero-downtime deployments, rollback strategies for PostgreSQL and common ORMs. Use when creating/altering tables or running data migrations. Do NOT use for query optimization (see backend-patterns).
roles: [coder, coder-complex]
---

# Database Migration Patterns

## When to Activate

- Creating or altering database tables
- Adding/removing columns or indexes
- Running data migrations (backfill, transform)
- Planning zero-downtime schema changes

## Core Principles

1. **Every change is a migration** — never alter prod databases manually
2. **Forward-only in production** — rollbacks use new forward migrations
3. **Schema and data migrations are separate** — never mix DDL and DML
4. **Test against production-sized data** — 100 rows ≠ 10M rows
5. **Immutable once deployed** — never edit a deployed migration

## Safety Checklist

- [ ] Has both UP and DOWN (or marked irreversible)
- [ ] No full table locks on large tables
- [ ] New columns are nullable or have defaults
- [ ] Indexes created concurrently
- [ ] Data backfill is separate migration
- [ ] Tested against prod-sized data copy
- [ ] Rollback plan documented

## PostgreSQL Safe Patterns

```sql
-- SAFE: Add nullable column (instant, no lock)
ALTER TABLE users ADD COLUMN avatar_url TEXT;

-- SAFE: Add column with default (PG 11+, instant)
ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true;

-- DANGEROUS: NOT NULL without default on existing table
-- ALTER TABLE users ADD COLUMN status TEXT NOT NULL;  -- FULL TABLE REWRITE!

-- SAFE: Create index concurrently (no lock)
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);

-- SAFE: Rename via new column + backfill + swap
ALTER TABLE users ADD COLUMN full_name TEXT;
UPDATE users SET full_name = name;  -- separate migration!
ALTER TABLE users DROP COLUMN name;  -- separate migration!
```

## Zero-Downtime Column Rename

```
Migration 1: ADD new_name column (nullable)
Migration 2: BACKFILL new_name FROM old_name
Migration 3: App code reads BOTH columns (dual-read)
Deploy: App uses new_name only
Migration 4: DROP old_name column
```

## Key Rules

1. **Never lock large tables** — use concurrent operations
2. **Separate schema from data migrations** — different risk profiles
3. **Always have rollback plan** — documented before applying
4. **Log migration execution** — start time, end time, rows affected
5. **Run in transaction** where possible (DDL in PG is transactional)

## Related

- [backend-patterns](./../backend-patterns/SKILL.md) — repository/service layers and DB optimization
- [deployment-patterns](./../deployment-patterns/SKILL.md) — CI/CD pipelines and zero-downtime deploys
- [security-review](./../security-review/SKILL.md) — auth, input validation, OWASP top 10
