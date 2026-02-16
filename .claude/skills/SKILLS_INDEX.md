# Skills Index — 14-Skill System

> Skills exist ONLY for complex multi-step procedures that an agent can't derive from general knowledge.
> Generic best practices (TDD, async patterns, security) are handled by CLAUDE.md one-liners.

---

## Entry Points

| Situation | Skill | Then |
|-----------|-------|------|
| **Understand project** | `project-knowledge` | read relevant guides |
| **New/unfamiliar codebase** | `codebase-mapping` | then project-knowledge |
| **Task without clear plan** | `task-decomposition` | detect parallelization |
| **Bug / Error** | `systematic-debugging` | 4-phase framework |
| **Executing plan** | `executing-plans` | or `subagent-driven-development` |
| **Parallel tasks with conflicts** | `subagent-driven-development` | + `using-git-worktrees` |
| **Before "done"** | `verification-before-completion` | evidence-based check |
| **Finishing branch** | `finishing-a-development-branch` | merge/PR workflow |
| **Session start** | `session-resumption` | check for incomplete work |
| **Context overflow** | `context-monitor` | warn at thresholds |
| **Error occurred** | `error-recovery` | retry/backoff patterns |
| **Auto-continue** | `self-completion` | for incomplete todos |
| **Agent Teams Mode** | `expert-panel` | multi-agent analysis |
| **Autonomous pipeline** | guide | `cat .claude/guides/autonomous-pipeline.md` |
| **External service** | guide | `cat .claude/guides/mcp-integration.md` |

---

## All Skills (14)

### ESSENTIAL (6) — Complex procedures, unique value

| Skill | Purpose | Path |
|-------|---------|------|
| **verification-before-completion** | Evidence-based completion claims | `verification-before-completion/SKILL.md` |
| **expert-panel** | Multi-agent expert analysis (10 roles, 4 phases) | `expert-panel/SKILL.md` |
| **subagent-driven-development** | Wave parallelization + worktree mode | `subagent-driven-development/SKILL.md` |
| **session-resumption** | Git state checks + worktree recovery | `session-resumption/SKILL.md` |
| **project-knowledge** | Project-specific docs router | `project-knowledge/SKILL.md` |
| **codebase-mapping** | Discovery protocol for unknown codebases | `codebase-mapping/SKILL.md` |

### USEFUL (8) — Trimmed checklists (~50 lines each)

| Skill | Purpose | Path |
|-------|---------|------|
| **executing-plans** | Batch execution with review checkpoints | `executing-plans/SKILL.md` |
| **task-decomposition** | Parallelization detection | `task-decomposition/SKILL.md` |
| **systematic-debugging** | 4-phase debugging checklist | `systematic-debugging/SKILL.md` |
| **error-recovery** | Retry/backoff patterns for CC tools | `error-recovery/SKILL.md` |
| **context-monitor** | Threshold-based warnings | `context-monitor/SKILL.md` |
| **finishing-a-development-branch** | Merge/PR workflow | `finishing-a-development-branch/SKILL.md` |
| **using-git-worktrees** | Worktree management procedures | `using-git-worktrees/SKILL.md` |
| **self-completion** | Auto-continue protocol | `self-completion/SKILL.md` |

---

## AUTONOMOUS PIPELINE

| Resource | Purpose | Path |
|----------|---------|------|
| **autonomous-pipeline guide** | Full pipeline guide: creation, execution, recovery | `.claude/guides/autonomous-pipeline.md` |
| **PIPELINE.md template** | State machine with `<- CURRENT` markers | `.claude/shared/work-templates/PIPELINE.md` |
| **PROMPT.md template** | Ralph Loop prompt for fresh-context phases | `.claude/shared/work-templates/PROMPT.md` |
| **ralph.sh** | Fresh-context loop script | `scripts/ralph.sh` |

---

## Workflow Decision Tree

```
Need to execute tasks from plan?
├─ YES → Same files?
│        ├─ YES → subagent-driven-development (Worktree Mode)
│        └─ NO → executing-plans (batch) or subagent-driven-development (parallel)
└─ NO → finishing-a-development-branch
```

---

## What Was Removed (and Why)

30 skills removed — they duplicated knowledge Opus already has.

**Replaced by CLAUDE.md one-liners:**
- TDD, async patterns, pytest patterns, telegram architecture, security checklist
- Architecture patterns, API design, python packaging, uv, performance optimization

**Replaced by guides:**
- mcp-integration → `.claude/guides/mcp-integration.md`

**Removed entirely (meta/unused):**
- methodology, project-planning, user/tech-spec-planning (kept as /commands)
- skill-development, command-manager, documentation (meta-skills)
- code-reviewer, requesting/receiving-code-review (agent can review without skill)
- test-generator, testing-anti-patterns, condition-based-waiting, dispatching-parallel-agents
- defense-in-depth, root-cause-tracing, secret-scanner, context-capture
- infrastructure, testing, user-acceptance-testing

---

## Available Commands

| Command | Purpose |
|---------|---------|
| `/init-project` | Initialize new project with template |
| `/init-context` | Fill project context files |
| `/project-context` | Load project context |
| `/new-user-spec` | Create user-spec for feature |
| `/new-tech-spec` | Create tech-spec for feature |
| `/resume` | Resume incomplete work |
| `/expert-panel` | Run expert panel analysis |

---

## Loading

```bash
cat .claude/skills/<folder>/SKILL.md
```

**Rules:** Max 3 skills simultaneously. Load only when the situation matches.
