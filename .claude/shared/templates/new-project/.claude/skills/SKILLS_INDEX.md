# Skills Index — 11-Skill System

> Skills = description (auto-loaded for routing) + checklist body (quick reference, ~30 lines each).
> Critical rules are INLINED in CLAUDE.md blocking rules — not hidden in skill files.

---

## Entry Points

| Situation | Skill / Action |
|-----------|---------------|
| **New/unfamiliar codebase** | `codebase-mapping` |
| **Task without clear plan** | `task-decomposition` → detect streams + waves |
| **Bug / Error** | `systematic-debugging` (also inlined in CLAUDE.md) |
| **Parallel tasks** | `subagent-driven-development` + `using-git-worktrees` |
| **Before "done"** | CLAUDE.md "Before done" checklist (inlined) |
| **After IMPLEMENT** | CLAUDE.md "After IMPLEMENT (QA Gate)" (inlined) |
| **Finishing branch** | `finishing-a-development-branch` |
| **Tool error** | `error-recovery` |
| **Auto-continue** | `self-completion` |
| **Agent Teams Mode** | `expert-panel` |
| **Autonomous pipeline** | `cat .claude/guides/autonomous-pipeline.md` |
| **External service** | `cat .claude/skills/mcp-integration/SKILL.md` |
| **Complexity assessment** | `cat .claude/guides/complexity-assessment.md` |
| **Recovery/retry** | `cat .claude/guides/recovery-manager.md` |
| **Typed memory** | `cat .claude/guides/typed-memory.md` |
| **Agent type lookup** | `.claude/agents/registry.md` |
| **Graphiti memory** | `cat .claude/guides/graphiti-integration.md` |
| **Focused prompts** | `.claude/prompts/{type}.md` or `.claude/guides/focused-prompts.md` |

---

## All Skills (11)

| Skill | Lines | Purpose |
|-------|-------|---------|
| **verification-before-completion** | 30 | Evidence-based completion (inlined in CLAUDE.md) |
| **qa-validation-loop** | 39 | Reviewer→Fixer cycle (inlined in CLAUDE.md QA Gate) |
| **expert-panel** | 42 | Multi-agent analysis, 3-5 experts from pool of 10 |
| **subagent-driven-development** | 49 | Wave parallelization + worktree mode |
| **task-decomposition** | 37 | Work stream analysis + wave building |
| **systematic-debugging** | 38 | 4-phase: investigate→hypothesize→test→fix |
| **using-git-worktrees** | 44 | Worktree create/cleanup for parallel agents |
| **error-recovery** | 31 | Retry table + 3-strike protocol |
| **codebase-mapping** | 30 | Analyze unknown codebase → codebase-map.md |
| **finishing-a-development-branch** | 32 | Merge/PR/cleanup checklist |
| **self-completion** | 23 | Auto-continue through pending tasks |

**Total: ~395 lines** (was ~2,200+ across 15 skills — 82% reduction)

---

## How Skills Work Now

1. **Descriptions** are auto-loaded by Claude Code → influence routing decisions
2. **CLAUDE.md blocking rules** contain the critical procedures inline → always active
3. **Skill bodies** are quick-reference checklists → loaded on-demand if needed
4. **Teammate prompts** include rules inline → no "cat skill" that gets skipped
6. **Agent Registry** defines tools/skills/thinking per agent type → `.claude/agents/registry.md`
7. **Focused prompts** provide role-specific detailed instructions → `.claude/prompts/`
8. **Typed memory** persists knowledge between sessions → `.claude/memory/`

---

## AUTONOMOUS PIPELINE

| Resource | Purpose |
|----------|---------|
| **autonomous-pipeline guide** | `cat .claude/guides/autonomous-pipeline.md` |
| **agent-chains guide** | `cat .claude/guides/agent-chains.md` |
| **PIPELINE-v3 template** | `.claude/shared/work-templates/PIPELINE-v3.md` |
| **phase transition protocol** | Section 5 in autonomous-pipeline.md |
| **complexity assessment** | `.claude/guides/complexity-assessment.md` |
| **recovery manager** | `.claude/guides/recovery-manager.md` |
| **typed memory guide** | `.claude/guides/typed-memory.md` |
| **agent registry** | `.claude/agents/registry.md` |
| **graphiti integration** | `.claude/guides/graphiti-integration.md` |
| **focused prompts guide** | `.claude/guides/focused-prompts.md` |
| **focused prompt files** | `.claude/prompts/planner.md, coder.md, qa-reviewer.md, qa-fixer.md, insight-extractor.md` |

---

## What Was Removed

### This round (4 skills → deleted)
- `executing-plans` — duplicated by pipeline system
- `session-resumption` — duplicated by CLAUDE.md Session Start auto-behavior
- `project-knowledge` — just a file listing, no procedural value
- `context-monitor` — Phase Transition Protocol handles context between phases

### Previous round (30 skills → deleted)
- TDD, async, security, architecture → CLAUDE.md one-liners
- mcp-integration → guide (`.claude/guides/mcp-integration.md`)
- Meta-skills, code-review, testing → Opus knows these natively

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

## Related Guides

- `.claude/guides/autonomous-pipeline.md` — Pipeline v3 execution guide
- `.claude/guides/agent-chains.md` — Sequential agent pipelines
- `.claude/guides/teammate-prompt-template.md` — Teammate prompt format
