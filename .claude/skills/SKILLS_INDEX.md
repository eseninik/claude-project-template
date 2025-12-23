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

---

## Skill Categories

### MANDATORY (use when applicable)

These skills are REQUIRED when the situation matches.

| Skill | When | Path | Version |
|-------|------|------|---------|
| **systematic-debugging** | Any bug, error, unexpected behavior | `systematic-debugging/SKILL.md` | 1.0.0 |
| **test-driven-development** | Any new code | `test-driven-development/SKILL.md` | 1.0.0 |
| **verification-before-completion** | Before claiming "done" | `verification-before-completion/SKILL.md` | 1.0.0 |

### SITUATIONAL (use based on context)

Use these when the specific situation applies.

| Skill | When | Path | Version |
|-------|------|------|---------|
| **root-cause-tracing** | Error deep in call stack | `root-cause-tracing/SKILL.md` | 1.0.0 |
| **defense-in-depth** | Bug from invalid data | `defense-in-depth/SKILL.md` | 1.0.0 |
| **condition-based-waiting** | Flaky tests, race conditions | `condition-based-waiting/SKILL.md` | 1.0.0 |
| **testing-anti-patterns** | Writing/changing tests | `testing-anti-patterns/SKILL.md` | 1.0.0 |
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
cat .claude/skills/test-driven-development/SKILL.md
```

---

## Selection Rules

1. **Maximum 3 skills** simultaneously (mandatory + 1-2 situational)
2. **Mandatory first** — always load applicable mandatory skills
3. **Entry point skill** — start with the skill matching your situation
4. **SUB-SKILL references** — if skill requires another, load it

---

## Typical Combinations

| Task | Skills |
|------|--------|
| Simple bug | systematic-debugging |
| Bug with new test | systematic-debugging + TDD |
| Complex bug | systematic-debugging + TDD + code-review |
| New feature task | TDD + executing-plans |
| Flaky test fix | condition-based-waiting + TDD |
| Final check | verification-before-completion |

---

## FORBIDDEN

- Loading ALL skills (`@.claude/skills`)
- Loading skills "just in case"
- Skipping mandatory skills when they apply
- Using more than 3 skills simultaneously
