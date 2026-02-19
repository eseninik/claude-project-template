# Agent Registry

> Single source of truth for all agent types. Look up before spawning any teammate.

**Model**: Always Opus 4.6 (`claude-opus-4-6`). Never Haiku or Sonnet.

---

## Properties

Each agent type defines 6 properties:

| Property | Values | Description |
|----------|--------|-------------|
| **Tools** | `read-only` / `full` / `full+web` | Read-only = Read, Glob, Grep. Full adds Write, Edit, Bash. +web adds WebSearch, WebFetch |
| **Skills** | from 11-skill system | Skills to include in `## Required Skills` |
| **Thinking** | `quick` / `standard` / `deep` | Prompt phrasing: quick = "brief pass", standard = default, deep = "think carefully and deeply" |
| **Context** | `minimal` / `standard` / `full` | ~50 / ~100 / ~200 lines of prompt |
| **Memory** | `none` / `patterns` / `full` | What to inject from activeContext.md and project patterns |
| **MCP** | `none` / list of servers | Which MCP servers to activate |

---

## Spec Creation Agents

Read-only researchers that gather requirements and write specifications.

| Type | Tools | Skills | Thinking | Context | Memory | MCP |
|------|-------|--------|----------|---------|--------|-----|
| `spec-gatherer` | read-only + web | -- | standard | standard | patterns | context7 |
| `spec-researcher` | read-only + web | codebase-mapping | deep | full | full | context7 |
| `spec-writer` | full | -- | deep | full | full | none |
| `spec-critic` | read-only | -- | deep | full | full | none |

**Notes:**
- `spec-gatherer` searches docs and codebase for relevant context
- `spec-researcher` does deep codebase analysis for technical constraints
- `spec-writer` produces the final spec document (needs Write access)
- `spec-critic` reviews specs for gaps, contradictions, missing edge cases

---

## Planning Agents

Break down specs into actionable implementation plans.

| Type | Tools | Skills | Thinking | Context | Memory | MCP |
|------|-------|--------|----------|---------|--------|-----|
| `planner` | full + web | task-decomposition | deep | full | full | context7 |
| `complexity-assessor` | read-only | task-decomposition | standard | standard | patterns | none |

**Notes:**
- `planner` creates phased implementation plans with dependency graphs
- `complexity-assessor` estimates task complexity and identifies risks

---

## Implementation Agents

Write and modify code. Always get `verification-before-completion`.

| Type | Tools | Skills | Thinking | Context | Memory | MCP |
|------|-------|--------|----------|---------|--------|-----|
| `coder` | full | verification-before-completion | standard | standard | patterns | none |
| `coder-complex` | full + web | verification-before-completion | deep | full | full | context7 |

**Notes:**
- `coder` handles straightforward implementation tasks (single file/module changes)
- `coder-complex` handles tasks requiring research, multiple modules, or architectural decisions
- Both MUST run tests before claiming done

---

## QA Agents

Review code quality and fix issues found during review.

| Type | Tools | Skills | Thinking | Context | Memory | MCP |
|------|-------|--------|----------|---------|--------|-----|
| `qa-reviewer` | read-only | qa-validation-loop | deep | full | full | none |
| `qa-fixer` | full | verification-before-completion | standard | full | full | none |

**Notes:**
- `qa-reviewer` is READ-ONLY -- analyzes code against acceptance criteria, reports issues
- `qa-fixer` receives issues from reviewer and fixes them, then verifies
- Use in chain: qa-reviewer -> qa-fixer -> qa-reviewer (max 3 cycles)

---

## Debug Agents

Systematic debugging pipeline: reproduce -> analyze -> fix -> verify.

| Type | Tools | Skills | Thinking | Context | Memory | MCP |
|------|-------|--------|----------|---------|--------|-----|
| `reproducer` | full | systematic-debugging | standard | standard | patterns | none |
| `analyzer` | read-only | systematic-debugging | deep | full | full | none |
| `fixer` | full | systematic-debugging, verification-before-completion | standard | full | full | none |
| `verifier` | full | verification-before-completion | standard | standard | patterns | none |

**Notes:**
- `reproducer` creates minimal reproduction of the bug
- `analyzer` is READ-ONLY -- traces root cause, forms hypotheses
- `fixer` applies the fix and runs initial tests
- `verifier` confirms fix works and checks for regressions
- Typical chain: reproducer -> analyzer -> fixer -> verifier

---

## Expert Panel Agents

Always READ-ONLY. Analyze and report via SendMessage, never modify files.

| Type | Tools | Skills | Thinking | Context | Memory | MCP |
|------|-------|--------|----------|---------|--------|-----|
| `business-analyst` | read-only | codebase-mapping | deep | full | full | none |
| `system-architect` | read-only | codebase-mapping | deep | full | full | none |
| `security-analyst` | read-only | -- | deep | full | full | none |
| `qa-strategist` | read-only | -- | deep | full | full | none |
| `risk-assessor` | read-only | -- | deep | full | full | none |

**Notes:**
- All expert panel agents are spawned via `.claude/guides/expert-panel-workflow.md`
- Output goes to lead via SendMessage, not to files
- Security-analyst uses general OWASP/security knowledge (no skill needed)
- See teammate-prompt-template.md "Expert Panel Roles" for skill mapping

---

## Utility Agents

Lightweight agents for mechanical tasks.

| Type | Tools | Skills | Thinking | Context | Memory | MCP |
|------|-------|--------|----------|---------|--------|-----|
| `insight-extractor` | read-only | -- | quick | minimal | none | none |
| `template-syncer` | full | -- | quick | minimal | none | none |
| `commit-helper` | full | finishing-a-development-branch | quick | minimal | none | none |

**Notes:**
- `insight-extractor` pulls key facts from long outputs (e.g., summarize test results)
- `template-syncer` copies files between main `.claude/` and `shared/templates/new-project/.claude/`
- `commit-helper` stages, commits, and optionally pushes with proper message format

---

## Pipeline Agents

Coordinate multi-phase autonomous pipelines.

| Type | Tools | Skills | Thinking | Context | Memory | MCP |
|------|-------|--------|----------|---------|--------|-----|
| `pipeline-lead` | full | subagent-driven-development | deep | full | full | none |
| `wave-coordinator` | full | subagent-driven-development, task-decomposition | standard | standard | patterns | none |

**Notes:**
- `pipeline-lead` owns the full pipeline lifecycle (PIPELINE.md state machine)
- `wave-coordinator` manages a single wave of parallel agents within a pipeline phase

---

## How to Use

### When Spawning a Teammate

1. Identify the agent type from the tables above
2. Build prompt using `.claude/guides/teammate-prompt-template.md`
3. Include tools restriction: `"You have READ-ONLY access (Read, Glob, Grep only)"` or full
4. Include `## Required Skills` listing skills from the registry
5. Set thinking level via prompt phrasing:
   - quick: "Do a quick pass on..."
   - standard: (default, no special phrasing)
   - deep: "Think carefully and deeply about..."
6. Inject memory based on Memory column:
   - `none`: no memory context
   - `patterns`: key patterns from activeContext.md
   - `full`: full activeContext.md + relevant ADRs

### Adding a New Agent Type

1. Add entry to the appropriate category table (all 6 properties required)
2. If the agent has a complex prompt, create `.claude/prompts/{type}.md`
3. Update this file and teammate-prompt-template.md if the role has special rules
4. Sync to `shared/templates/new-project/.claude/agents/registry.md`
