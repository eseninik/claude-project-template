# Skills Index — Unified Catalog

> **This file is a CATALOG of skills.**
> The algorithm for when to use skills is in `CLAUDE.md`.
> This file tells you WHICH skill to load and WHERE to find it.
>
> **See also:** `methodology/guides/skill-composition.md` for input/output contracts.

---

## Entry Points

**Start here based on your task:**

| Situation | Start With | Then |
|-----------|------------|------|
| **Понять проект** | `project-knowledge` | читай нужные guides |
| **Новый/незнакомый проект** | `codebase-mapping` | затем project-knowledge |
| **Новый проект с нуля** | `methodology` | + project-planning |
| **Неясные требования** | `context-capture` | затем user-spec-planning |
| **Планирование фичи** | `user-spec-planning` | затем tech-spec-planning |
| Bug / Error | `systematic-debugging` | + TDD if fix needs new code |
| New code (any) | `test-driven-development` | + others as needed |
| Executing plan | `executing-plans` | or `subagent-driven-development` |
| Flaky test | `condition-based-waiting` | - |
| **Реализация завершена** | `user-acceptance-testing` | затем verification |
| Before "done" | `verification-before-completion` | - |
| Finishing branch | `finishing-a-development-branch` | - |
| **Infrastructure setup** | `infrastructure` | CI/CD, Docker, tests |
| **Testing strategy** | `testing` | smoke → unit → integration → E2E |
| **Python async code** | `async-python-patterns` | + `python-testing-patterns` |
| **Telegram bot** | `telegram-bot-architecture` | + `async-python-patterns` |
| **Personal data** | `security-checklist` | + `secret-scanner` |
| **New API endpoint** | `api-design-principles` | + security if needed |
| **Major refactoring** | `architecture-patterns` | + TDD |
| **New project setup** | `python-packaging` | + `uv-package-manager` |
| **Performance issues** | `python-performance-optimization` | after profiling |
| **Need tests scaffold** | `test-generator` | + python-testing-patterns |
| **Code review needed** | `code-reviewer` | - |
| **Session start** | `session-resumption` | check for incomplete work |
| **Context overflow** | `context-monitor` | warn at 50%, block at 70% |
| **Auto-continue** | `self-completion` | for incomplete todos |
| **Error occurred** | `error-recovery` | structured recovery patterns |

---

## Skill Categories

### METHODOLOGY & PLANNING (from AI-First framework)

Skills for project planning, spec creation, and workflow management.

| Skill | When | Path | Version |
|-------|------|------|---------|
| **methodology** | Изучить AI-First методологию, workflows, структуру | `methodology/SKILL.md` | 1.0.0 |
| **project-planning** | Планирование нового проекта (project.md, features.md, roadmap.md) | `project-planning/SKILL.md` | 1.0.0 |
| **user-spec-planning** | Создание user-spec.md через интервью | `user-spec-planning/SKILL.md` | 1.0.0 |
| **tech-spec-planning** | Создание tech-spec.md + tasks/*.md | `tech-spec-planning/SKILL.md` | 1.0.0 |

### INFRASTRUCTURE & TESTING STRATEGY

Skills for CI/CD setup and testing approach.

| Skill | When | Path | Version |
|-------|------|------|---------|
| **infrastructure** | CI/CD, Docker, pre-commit hooks, GitHub Actions | `infrastructure/SKILL.md` | 1.0.0 |
| **testing** | Стратегия тестов: smoke, unit, integration, E2E | `testing/SKILL.md` | 1.0.0 |

### PROJECT KNOWLEDGE

| Skill | When | Path | Version |
|-------|------|------|---------|
| **project-knowledge** | Понять архитектуру, tech stack, паттерны, БД, деплой | `project-knowledge/SKILL.md` | 1.0.0 |

### CONTEXT & MAPPING

Skills for understanding and capturing context.

| Skill | When | Path | Version |
|-------|------|------|---------|
| **context-capture** | Размытые требования, исследование проблемы | `context-capture/SKILL.md` | 1.0.0 |
| **codebase-mapping** | Новый/незнакомый проект, устаревшие guides | `codebase-mapping/SKILL.md` | 1.0.0 |

### MANDATORY (use when applicable)

These skills are REQUIRED when the situation matches.

| Skill | When | Path | Version |
|-------|------|------|---------|
| **systematic-debugging** | Any bug, error, unexpected behavior | `systematic-debugging/SKILL.md` | 1.0.0 |
| **test-driven-development** | Any new code | `test-driven-development/SKILL.md` | 1.0.0 |
| **user-acceptance-testing** | After implementation, BEFORE verification | `user-acceptance-testing/SKILL.md` | 1.0.0 |
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

### META (skills about skills & commands)

| Skill | When | Path | Version |
|-------|------|------|---------|
| **using-superpowers** | Starting session, finding skills | `using-superpowers/SKILL.md` | 1.0.0 |
| **writing-skills** | Creating new skill | `writing-skills/SKILL.md` | 1.0.0 |
| **testing-skills-with-subagents** | Testing a skill | `testing-skills-with-subagents/SKILL.md` | 1.0.0 |
| **sharing-skills** | Contributing skill upstream | `sharing-skills/SKILL.md` | 1.0.0 |
| **skill-creator** | Guide for creating skills | `skill-creator/SKILL.md` | 1.0.0 |
| **command-manager** | Manage slash commands | `command-manager/SKILL.md` | 1.0.0 |
| **documentation** | Manage project documentation | `documentation/SKILL.md` | 1.0.0 |

### AUTOMATION & ORCHESTRATION

Skills for automated execution, session management, and error handling.

| Skill | When | Path | Version |
|-------|------|------|---------|
| **session-resumption** | Session start with incomplete work, /resume command | `session-resumption/SKILL.md` | 1.0.0 |
| **context-monitor** | Monitor context usage, warn at 50%, block at 70% | `context-monitor/SKILL.md` | 1.0.0 |
| **error-recovery** | Tool errors, test failures, timeouts (triggers systematic-debugging for tests) | `error-recovery/SKILL.md` | 1.0.0 |
| **self-completion** | Auto-continue through pending todos until complete | `self-completion/SKILL.md` | 1.0.0 |

---

## How to Load Skills

```bash
# Load specific skill
cat .claude/skills/<folder>/SKILL.md

# Examples
cat .claude/skills/systematic-debugging/SKILL.md
cat .claude/skills/methodology/SKILL.md
cat .claude/skills/user-spec-planning/SKILL.md
```

---

## Selection Rules

1. **Maximum 3 skills** simultaneously (mandatory + 1-2 situational)
2. **Mandatory first** — always load applicable mandatory skills
3. **Entry point skill** — start with the skill matching your situation
4. **SUB-SKILL references** — if skill requires another, load it

---

## Typical Combinations

### Project Setup & Planning

| Task | Skills |
|------|--------|
| Новый проект с нуля | methodology + project-planning + infrastructure |
| Понять существующий проект | codebase-mapping → project-knowledge |
| Неясные требования | context-capture → user-spec-planning |
| Планирование фичи | user-spec-planning → tech-spec-planning |
| Настройка CI/CD | infrastructure |
| Стратегия тестов | testing |

### General Development

| Task | Skills |
|------|--------|
| Simple bug | systematic-debugging |
| Bug with new test | systematic-debugging + TDD |
| Complex bug | systematic-debugging + TDD + code-reviewer |
| New feature task | TDD + executing-plans |
| Flaky test fix | condition-based-waiting + TDD |
| После реализации фичи | user-acceptance-testing → verification |
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

**Total: 47 skills**

| Category | Count | Skills |
|----------|-------|--------|
| Methodology & Planning | 4 | methodology, project-planning, user-spec-planning, tech-spec-planning |
| Infrastructure & Testing Strategy | 2 | infrastructure, testing |
| Project | 1 | project-knowledge |
| Context & Mapping | 2 | context-capture, codebase-mapping |
| Mandatory | 5 | debugging, TDD, UAT, verification, security-checklist |
| Python-specific | 6 | async, testing, bot-arch, packaging, perf, uv |
| Architecture & API | 2 | architecture-patterns, api-design |
| Security | 2 | security-checklist, secret-scanner |
| Testing & Quality | 3 | test-generator, code-reviewer, testing-anti-patterns |
| Situational | 4 | root-cause, defense, waiting, parallel |
| Workflow | 4 | executing, subagent, finishing, worktrees |
| Code Review | 2 | requesting, receiving |
| Meta | 7 | superpowers, writing, testing-skills, sharing, skill-creator, command-manager, documentation |
| Automation & Orchestration | 4 | session-resumption, context-monitor, error-recovery, self-completion |

---

## Available Commands

Slash commands in `.claude/commands/`:

| Command | Purpose |
|---------|---------|
| `/init-project` | Initialize new project with template |
| `/init-context` | Fill project context files |
| `/project-context` | Load project context |
| `/meta-context` | Load meta-project context |
| `/new-user-spec` | Create user-spec for feature |
| `/new-tech-spec` | Create tech-spec for feature |
| `/resume` | Resume incomplete work from STATE.md |

---

## Available Agents

Subagents in `.claude/agents/`:

| Agent | Purpose |
|-------|---------|
| `code-developer` | Implements tasks, writes code and tests |
| `code-reviewer` | Reviews code quality, finds issues |
| `secret-scanner` | Scans for hardcoded secrets |
| `security-auditor` | Audits against OWASP Top 10 |
| `orchestrator` | Intent classification and automatic skill selection | opus |

---

## FORBIDDEN

- Loading ALL skills (`@.claude/skills`)
- Loading skills "just in case"
- Skipping mandatory skills when they apply
- Using more than 3 skills simultaneously
- **Skipping `security-checklist` when handling personal data**
- **Skipping `secret-scanner` before commits**
