---
name: project-knowledge
description: |
  Provides access to all project documentation: architecture, tech stack, code patterns, database schema,
  deployment, git workflow, and UX guidelines. Read specific guides on demand for current task context.
  Use when needing project architecture info, coding conventions, deployment details, or any project-specific reference.
  Does NOT contain implementation instructions - it is a knowledge base, not a procedural skill.
---

# Project Knowledge

Access project documentation and context files that define how the project works.

## Available Guides

All documentation in `guides/` directory. Read specific guides as needed for current task:

| Guide | Content | Read When |
|-------|---------|-----------|
| **project.md** | Project overview, audience, key features, scope | Starting any work on the project |
| **features.md** | Feature list with priorities, dependencies, statuses | Planning or implementing features |
| **roadmap.md** | Development phases, milestones, migration plan | Understanding project direction |
| **architecture.md** | Tech stack, project structure, dependencies, data flow | Before code changes |
| **patterns.md** | Code standards, naming, error handling, security, testing | Writing or reviewing code |
| **database.md** | DB type, tables, constraints, migrations, naming | Working with data layer |
| **deployment.md** | Platform, SSH, env vars, triggers, rollback, environments | Deploying or configuring infrastructure |
| **git-workflow.md** | Branch structure, testing strategy, PR process | Creating branches or PRs |
| **ux-guidelines.md** | UI language, tone, glossary, text patterns, accessibility | Building user-facing features |
| **monitoring.md** | Logging, error tracking, metrics, health checks, alerting | Adding observability |
| **business-rules.md** | Domain workflows, validation rules, state machines | Implementing business logic |

## Usage Pattern

```
Task: implement new API endpoint
  -> Read: architecture.md (understand structure)
  -> Read: patterns.md (follow conventions)
  -> Read: database.md (if touching data layer)
  -> Implement following project standards
```

## Example

**Task:** Add user authentication endpoint

**Read sequence:**
1. `guides/architecture.md` - understand existing auth patterns, middleware structure
2. `guides/patterns.md` - follow error handling and naming conventions
3. `guides/database.md` - check user model schema and constraints

## Edge Cases

- Guide file missing or empty: note the gap, proceed with general best practices, suggest filling it later
- Guide content contradicts another guide: follow architecture.md as primary authority, flag contradiction
- Guide outdated after major refactoring: use codebase-mapping skill to regenerate, then update guide
