# Skills Index — 13-Skill System

> 13 project-level skills for agent infrastructure. Full content loaded via Skill tool or embedded in teammate prompts.
> Global skills (14) are in ~/.claude/skills/ and auto-loaded by Claude Code.

---

## Entry Points

| Situation | Skill |
|-----------|-------|
| New/unfamiliar codebase | `codebase-mapping` |
| Task without clear plan | `task-decomposition` |
| Bug / Error | `systematic-debugging` |
| Parallel tasks | `subagent-driven-development` + `using-git-worktrees` |
| Tool call failures | `error-recovery` |
| Before "done" | `verification-before-completion` |
| After IMPLEMENT (QA) | `qa-validation-loop` |
| Finishing branch | `finishing-a-development-branch` |
| Auto-continue todos | `self-completion` |
| Expert panel / Agent Teams Mode | `expert-panel` |
| AO Hybrid execution | `ao-hybrid-spawn` |
| Fleet cross-project ops | `ao-fleet-spawn` |

---

## All Skills (13)

| Skill | Lines | Purpose |
|-------|-------|---------|
| **ao-fleet-spawn** | 104 | Spawn and manage parallel agent sessions across multiple projects via Agent Orchestrator CLI |
| **ao-hybrid-spawn** | 186 | Spawn parallel worker agents as full Claude Code sessions via Agent Orchestrator |
| **codebase-mapping** | 42 | Analyze unknown codebase structure into codebase-map.md |
| **error-recovery** | 425 | Structured recovery patterns for tool call errors, test failures, and Bash timeouts |
| **expert-panel** | 54 | Multi-agent expert panel for task analysis, spawns 3-5 specialists from pool of 10 |
| **finishing-a-development-branch** | 201 | Guides completion of development work with structured options for merge, PR, or cleanup |
| **qa-validation-loop** | 98 | Risk-proportional QA cycle: Reviewer agent checks code, Fixer agent repairs issues |
| **self-completion** | 338 | Auto-continue through pending todo items until complete |
| **subagent-driven-development** | 1444 | Wave parallelization with worktree mode for tasks modifying same files |
| **systematic-debugging** | 296 | Four-phase framework: root cause investigation, pattern analysis, hypothesis testing, implementation |
| **task-decomposition** | 601 | Analyze tasks for parallel subtask splitting, detect work streams for smarter parallelization |
| **using-git-worktrees** | 448 | Isolated workspace creation and parallel task execution via git worktrees |
| **verification-before-completion** | 140 | Evidence-based completion gate — requires running verification commands before success claims |

**Total: 4377 lines**

---

## How Skills Work

1. **Lead agent**: Invokes via Skill tool (full content loaded)
2. **TeamCreate agents**: Full skill content embedded in prompt (can't use Skill tool)
3. **AO Hybrid agents**: Full Claude Code sessions with Skill tool access
4. **Descriptions**: YAML front matter auto-loaded for routing
5. **CLAUDE.md**: Skill trigger table maps situations → skills

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

- `.claude/guides/autonomous-pipeline.md` — Pipeline v3 execution
- `.claude/guides/agent-chains.md` — Sequential agent pipelines
- `.claude/guides/teammate-prompt-template.md` — Teammate prompt format
