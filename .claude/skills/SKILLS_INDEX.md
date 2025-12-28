# Skills Index — Catalog & Categories

> **This file is a CATALOG of skills, not the algorithm.**
> The algorithm for when to use skills is in `CLAUDE.md`.
> This file tells you WHICH skill to load and WHERE to find it.

---

## Entry Points

**Start here based on your task:**

| Situation | Start With | Then |
|-----------|------------|------|
| Bug / Error | `systematic-debugging` | + TDD if fix needs new code |
| New code (any) | `test-driven-development` | + others as needed |
| Executing plan | `executing-plans` | or `subagent-driven-development` |
| Flaky test | `condition-based-waiting` | - |
| Before "done" | `verification-before-completion` | - |
| Finishing branch | `finishing-a-development-branch` | - |
| **Python async code** | `async-python-patterns` | + `python-testing-patterns` |
| **Telegram bot** | `telegram-bot-architecture` | + `async-python-patterns` |
| **Personal data** | `security-checklist` | + `secret-scanner` |
| **New API endpoint** | `api-design-principles` | + security if needed |
| **Major refactoring** | `architecture-patterns` | + TDD |
| **New project setup** | `python-packaging` | + `uv-package-manager` |
| **Performance issues** | `python-performance-optimization` | after profiling |
| **Need tests scaffold** | `test-generator` | + python-testing-patterns |
| **Code review needed** | `code-reviewer` | - |

---

## Skill Categories

### MANDATORY (use when applicable)

These skills are REQUIRED when the situation matches.

| Skill | When | Path | Version |
|-------|------|------|---------|
| **systematic-debugging** | Any bug, error, unexpected behavior | `systematic-debugging/SKILL.md` | 1.0.0 |
| **test-driven-development** | Any new code | `test-driven-development/SKILL.md` | 1.0.0 |
| **verification-before-completion** | Before claiming "done" | `verification-before-completion/SKILL.md` | 1.0.0 |
| **security-checklist** | Any personal data handling | `security-checklist/SKILL.md` | 1.0.0 |

### PYTHON-SPECIFIC (use for Python projects)

Use these for Python/aiogram/FastAPI development.

| Skill | When | Path | Version |
|-------|------|------|---------|
| **async-python-patterns** | Any async/await, aiogram, aiohttp | `async-python-patterns/SKILL.md` | 1.0.0 |
| **python-testing-patterns** | Writing tests, pytest, AsyncMock | `python-testing-patterns/SKILL.md` | 1.0.0 |
| **telegram-bot-architecture** | Structuring aiogram bot project | `telegram-bot-architecture/SKILL.md` | 1.0.0 |
| **python-packaging** | pyproject.toml, dependencies, setup | `python-packaging/SKILL.md` | 1.0.0 |
| **python-performance-optimization** | Profiling, bottlenecks, optimization | `python-performance-optimization/SKILL.md` | 1.0.0 |
| **uv-package-manager** | Fast dependency management with uv | `uv-package-manager/SKILL.md` | 1.0.0 |

### ARCHITECTURE & API

| Skill | When | Path | Version |
|-------|------|------|---------|
| **architecture-patterns** | Clean Architecture, SOLID, DI, repos | `architecture-patterns/SKILL.md` | 1.0.0 |
| **api-design-principles** | REST API, webhooks, FastAPI endpoints | `api-design-principles/SKILL.md` | 1.0.0 |

### SECURITY

| Skill | When | Path | Version |
|-------|------|------|---------|
| **security-checklist** | Personal data, input validation, encryption | `security-checklist/SKILL.md` | 1.0.0 |
| **secret-scanner** | Detect hardcoded secrets, API keys | `secret-scanner/SKILL.md` | 1.0.0 |

### TESTING & CODE QUALITY

| Skill | When | Path | Version |
|-------|------|------|---------|
| **test-generator** | Scaffold tests for existing code | `test-generator/SKILL.md` | 1.0.0 |
| **code-reviewer** | Automated code review | `code-reviewer/SKILL.md` | 1.0.0 |
| **testing-anti-patterns** | Avoid bad testing practices | `testing-anti-patterns/SKILL.md` | 1.0.0 |

### SITUATIONAL (use based on context)

Use these when the specific situation applies.

| Skill | When | Path | Version |
|-------|------|------|---------|
| **root-cause-tracing** | Error deep in call stack | `root-cause-tracing/SKILL.md` | 1.0.0 |
| **defense-in-depth** | Bug from invalid data | `defense-in-depth/SKILL.md` | 1.0.0 |
| **condition-based-waiting** | Flaky tests, race conditions | `condition-based-waiting/SKILL.md` | 1.0.0 |
| **dispatching-parallel-agents** | 3+ independent failures | `dispatching-parallel-agents/SKILL.md` | 1.0.0 |

### WORKFLOW (choose one per task)

Choose the appropriate workflow skill.

| Skill | When | Path | Version |
|-------|------|------|---------|
| **executing-plans** | Execute plan with review checkpoints | `executing-plans/SKILL.md` | 1.0.0 |
| **subagent-driven-development** | Independent tasks, same session | `subagent-driven-development/SKILL.md` | 1.0.0 |
| **finishing-a-development-branch** | Merge, PR, complete branch | `finishing-a-development-branch/SKILL.md` | 1.0.0 |
| **using-git-worktrees** | Need isolated workspace | `using-git-worktrees/SKILL.md` | 1.0.0 |

### CODE REVIEW

| Skill | When | Path | Version |
|-------|------|------|---------|
| **requesting-code-review** | Need review of your work | `requesting-code-review/SKILL.md` | 1.0.0 |
| **receiving-code-review** | Got feedback, need to respond | `receiving-code-review/SKILL.md` | 1.0.0 |

### META (skills about skills)

| Skill | When | Path | Version |
|-------|------|------|---------|
| **using-superpowers** | Starting session, finding skills | `using-superpowers/SKILL.md` | 1.0.0 |
| **writing-skills** | Creating new skill | `writing-skills/SKILL.md` | 1.0.0 |
| **testing-skills-with-subagents** | Testing a skill | `testing-skills-with-subagents/SKILL.md` | 1.0.0 |
| **sharing-skills** | Contributing skill upstream | `sharing-skills/SKILL.md` | 1.0.0 |

---

## How to Load Skills

```bash
# Load specific skill
cat .claude/skills/<folder>/SKILL.md

# Examples
cat .claude/skills/systematic-debugging/SKILL.md
cat .claude/skills/async-python-patterns/SKILL.md
cat .claude/skills/security-checklist/SKILL.md
```

---

## Selection Rules

1. **Maximum 3 skills** simultaneously (mandatory + 1-2 situational)
2. **Mandatory first** — always load applicable mandatory skills
3. **Entry point skill** — start with the skill matching your situation
4. **SUB-SKILL references** — if skill requires another, load it

---

## Typical Combinations

### General Development

| Task | Skills |
|------|--------|
| Simple bug | systematic-debugging |
| Bug with new test | systematic-debugging + TDD |
| Complex bug | systematic-debugging + TDD + code-reviewer |
| New feature task | TDD + executing-plans |
| Flaky test fix | condition-based-waiting + TDD |
| Final check | verification-before-completion |

### Python/aiogram Development

| Task | Skills |
|------|--------|
| New bot handler | TDD + async-python-patterns + telegram-bot-architecture |
| Async bug | systematic-debugging + async-python-patterns |
| Writing pytest tests | python-testing-patterns + TDD |
| Refactor bot structure | telegram-bot-architecture + architecture-patterns |
| Personal data feature | security-checklist + secret-scanner + TDD |
| FSM flow | telegram-bot-architecture + python-testing-patterns |
| New API endpoint | api-design-principles + TDD |
| Performance issue | python-performance-optimization |
| New project setup | python-packaging + uv-package-manager |
| Add tests to existing code | test-generator + python-testing-patterns |
| Code review | code-reviewer |

---

## Skill Count Summary

**Total: 30 skills**

| Category | Count | Skills |
|----------|-------|--------|
| Mandatory | 4 | debugging, TDD, verification, security-checklist |
| Python-specific | 6 | async, testing, bot-arch, packaging, perf, uv |
| Architecture & API | 2 | architecture-patterns, api-design |
| Security | 2 | security-checklist, secret-scanner |
| Testing & Quality | 3 | test-generator, code-reviewer, testing-anti-patterns |
| Situational | 4 | root-cause, defense, waiting, parallel |
| Workflow | 4 | executing, subagent, finishing, worktrees |
| Code Review | 2 | requesting, receiving |
| Meta | 4 | superpowers, writing, testing-skills, sharing |

---

## FORBIDDEN

- Loading ALL skills (`@.claude/skills`)
- Loading skills "just in case"
- Skipping mandatory skills when they apply
- Using more than 3 skills simultaneously
- **Skipping `security-checklist` when handling personal data**
- **Skipping `secret-scanner` before commits**
