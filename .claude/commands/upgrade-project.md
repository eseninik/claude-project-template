---
description: Upgrade existing project to latest template version
allowed-tools:
  - Read
  - Edit
  - Write
  - Bash(*)
  - AskUserQuestion
---

# Instructions

## Overview

This command upgrades an existing project to the latest template version.
It compares current project config with the template and applies updates safely.

**PROTECTED DIRECTORIES (never overwrite):**
- `.claude/memory/` — project-specific session data
- `.claude/adr/` — project-specific architecture decisions
- `.claude/skills/project-knowledge/` — project-specific documentation
- `work/` — project work items and state

## 1. Check Current State

**Read current CLAUDE.md:**
```bash
Read: CLAUDE.md
```

**Check existing structures:**
```bash
ls -la .claude/memory/ 2>/dev/null || echo "MEMORY_NOT_FOUND"
ls -la .claude/adr/ 2>/dev/null || echo "ADR_NOT_FOUND"
ls work/STATE.md 2>/dev/null || echo "STATE_NOT_FOUND"
```

## 2. Analyze Differences

Compare current project with template and identify:

1. **Missing memory/** - needs to be created
2. **Missing adr/** - needs to be created
3. **Missing STATE.md** - needs to be created
4. **Outdated CLAUDE.md** - missing AUTO-BEHAVIORS section
5. **Missing git hooks** - post-commit not installed

## 3. Show Upgrade Plan

Tell user (Russian):

```
🔄 Анализ проекта завершён

Текущая версия: [detected or "unknown"]
Целевая версия: 3.0 (AUTO-BEHAVIORS + Memory System)

Что будет обновлено:

1. CLAUDE.md:
   [✓ уже есть / ⚠️ нужно добавить] AUTO-BEHAVIORS section

2. .claude/memory/:
   [✓ уже есть / ⚠️ нужно создать] activeContext.md

3. .claude/adr/:
   [✓ уже есть / ⚠️ нужно создать] decisions.md, _template.md

4. work/STATE.md:
   [✓ уже есть / ⚠️ нужно создать]

5. Git hooks:
   [✓ уже есть / ⚠️ нужно установить] post-commit

⚠️ НЕ будут затронуты (проектные данные):
- Существующий контент в memory/
- Существующие ADR
- project-knowledge guides
- work/ folders

Применить обновления?
```

**Wait for user confirmation.**

## 4. Apply Updates

### 4.1 Create memory/ (if missing)

```bash
mkdir -p .claude/memory
```

**If activeContext.md does NOT exist**, write it:
```markdown
# Active Context

> Мост между сессиями. Агент читает в начале, обновляет в конце.

**Last updated:** [DATE]

---

## Current Focus

<!-- Что делаем прямо сейчас (1-2 предложения) -->

---

## Recent Decisions

| Date | Decision | Rationale | Files Affected |
|------|----------|-----------|----------------|
| | | | |

---

## Active Questions

- [ ]

---

## Learned Patterns

### What Works
-

### What Doesn't Work
-

### Gotchas
-

---

## Next Steps

1.
2.
3.

---

## Session Log

<!-- Агент добавляет запись после каждой сессии -->
```

### 4.2 Create adr/ (if missing)

```bash
mkdir -p .claude/adr
```

**If decisions.md does NOT exist**, write it:
```markdown
# Architecture Decision Records

> INDEX всех архитектурных решений проекта. Агент консультируется перед изменением архитектуры.

---

## Active Decisions

| ID | Title | Date | Status | Impact |
|----|-------|------|--------|--------|
| | | | | |

---

## By Category

### Architecture
### Database
### API
### Infrastructure

---

## How to Use

**Агент автоматически:**
1. Читает этот INDEX перед архитектурными изменениями
2. Создаёт новый ADR при значимом решении
3. Обновляет INDEX при создании/изменении ADR
```

**If _template.md does NOT exist**, write it:
```markdown
# ADR-NNN: [Title]

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-XXX

---

## Context
## Decision
## Rationale
## Alternatives Considered
## Consequences
## For AI Agents
```

### 4.3 Create STATE.md (if missing)

```bash
mkdir -p work
```

Write `work/STATE.md` (only if not exists)

### 4.4 Update CLAUDE.md

**Check if AUTO-BEHAVIORS section exists.**

**If NOT found, REPLACE entire CLAUDE.md with new template:**

Read project name and description from current CLAUDE.md, then write new version:

```markdown
# Project: [PROJECT NAME]

> **[PROJECT DESCRIPTION]**

---

## How This Project Works

**Context:** `.claude/skills/project-knowledge/` — architecture, patterns, git workflow, database, deployment.

**Memory:** `.claude/memory/activeContext.md` — session bridge, decisions, learned patterns.

**ADR:** `.claude/adr/` — architecture decision records.

**Default branch:** `dev`

---

# AUTO-BEHAVIORS

> Агент выполняет автоматически, БЕЗ команд пользователя.

---

## SESSION START (always)

1. Read .claude/memory/activeContext.md
2. Read work/STATE.md
3. IF unfinished work exists → Tell user
4. ELSE → Ready for new task

---

## BEFORE CODE CHANGES (always)

1. Read .claude/skills/project-knowledge/guides/architecture.md
2. Read .claude/skills/project-knowledge/guides/patterns.md
3. Check .claude/adr/decisions.md for relevant decisions

---

## AFTER TASK COMPLETION (always)

1. Update .claude/memory/activeContext.md
2. Update work/STATE.md
3. IF architectural decision → Create ADR
4. Commit with meaningful message

---

## ON ERROR/BUG (always)

1. Check .claude/memory/activeContext.md → Gotchas
2. Apply known solution or add new one

---

# HARD CONSTRAINTS

| Constraint | Reason |
|------------|--------|
| No data deletion without confirmation | Irreversible |
| No committing secrets | Security |
| No push to main without permission | Production stability |
| No "done" without verification | Honesty |
| Always update memory after work | Context preservation |

---

# KNOWLEDGE LOCATIONS

| Need | Location |
|------|----------|
| Project architecture | `.claude/skills/project-knowledge/guides/architecture.md` |
| Code patterns | `.claude/skills/project-knowledge/guides/patterns.md` |
| Session context | `.claude/memory/activeContext.md` |
| Task state | `work/STATE.md` |
| Architecture decisions | `.claude/adr/decisions.md` |

---

# FORBIDDEN

- Starting work without reading memory/activeContext.md
- Finishing work without updating memory
- Making architecture decisions without checking ADR
- Saying "done" without running tests
```

### 4.5 Install Git Hooks

```bash
mkdir -p .claude/hooks
```

Write post-commit.sh if not exists, then:

```bash
mkdir -p .git/hooks
ln -sf ../../.claude/hooks/post-commit.sh .git/hooks/post-commit 2>/dev/null || echo "Hook symlink failed"
chmod +x .git/hooks/post-commit 2>/dev/null || echo "chmod failed"
```

## 5. Final Report

Tell user (Russian):

```
✅ Проект обновлён до версии 3.0!

Что добавлено:
- .claude/memory/activeContext.md — мост между сессиями
- .claude/adr/ — архитектурные решения
- AUTO-BEHAVIORS в CLAUDE.md — автоматическое поведение
- Git hooks — автообновление памяти после коммитов

Как это работает:
1. При старте сессии агент автоматически читает память
2. Перед изменениями — проверяет архитектуру и паттерны
3. После завершения — обновляет память
4. При коммите — добавляет запись в Session Log

Тебе ничего не нужно делать — всё работает автоматически.
```

## 6. Commit Changes

```bash
git add .claude/memory/ .claude/adr/ .claude/hooks/ CLAUDE.md work/STATE.md
git commit -m "chore: upgrade project to template v3.0 (AUTO-BEHAVIORS)

Added:
- .claude/memory/ for session context bridge
- .claude/adr/ for architecture decision records
- AUTO-BEHAVIORS in CLAUDE.md
- post-commit hook for automatic memory updates

Co-Authored-By: Claude <noreply@anthropic.com>"

git push
```

# Important Notes

- This command is SAFE - it only ADDS to protected directories, never removes
- Existing content in memory/, adr/, project-knowledge/ is NEVER overwritten
- User must confirm before any changes are applied
- Git hooks require manual setup on Windows (symlinks may not work)
