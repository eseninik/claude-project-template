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

## Research Agents

Lightweight analysis agents for auto-research phase. All read-only.

| Type | Tools | Skills | Thinking | Context | Memory | MCP |
|------|-------|--------|----------|---------|--------|-----|
| `requirement-analyst` | read-only | -- | standard | standard | patterns | none |
| `feasibility-analyst` | read-only | codebase-mapping | standard | full | full | none |
| `risk-assessor` | read-only | -- | deep | standard | patterns | none |
| `product-analyst` | read-only | -- | standard | standard | patterns | none |
| `ux-reviewer` | read-only | -- | standard | standard | none | none |

**Notes:**
- `requirement-analyst` parses task into structured acceptance criteria
- `feasibility-analyst` checks codebase for constraints and complexity
- `risk-assessor` identifies risks, breaking changes, security concerns
- `product-analyst` evaluates user value, market fit, acceptance criteria from user perspective
- `ux-reviewer` checks UX flows, accessibility, user-facing text (for UI tasks)
- Auto-Research uses first 3 types. Product-analyst and ux-reviewer are optional additions for user-facing features.

---

## Planning Agents

Break down specs into actionable implementation plans.

| Type | Tools | Skills | Thinking | Context | Memory | MCP |
|------|-------|--------|----------|---------|--------|-----|
| `planner` | full + web | task-decomposition | deep | full | full | context7 |
| `complexity-assessor` | read-only | task-decomposition | standard | standard | patterns | none |

| `dag-analyzer` | read-only | task-decomposition | deep | full | patterns | none |

**Notes:**
- `planner` creates phased implementation plans with dependency graphs
- `complexity-assessor` estimates task complexity and identifies risks
- `dag-analyzer` builds formal dependency graphs with topological sort, cycle detection, and wave assignment

---

## Implementation Agents

Write and modify code. Always get `verification-before-completion`.

| Type | Tools | Skills | Thinking | Context | Memory | MCP |
|------|-------|--------|----------|---------|--------|-----|
| `coder` | full | verification-before-completion | standard | standard | patterns | none |
| `coder-complex` | full + web | verification-before-completion | deep | full | full | context7 |
| `experimenter` | full | experiment-loop, skill-evolution, verification-before-completion | deep | full | full | none |

**Notes:**
- `coder` handles straightforward implementation tasks (single file/module changes)
- `coder-complex` handles tasks requiring research, multiple modules, or architectural decisions
- `experimenter` runs autonomous experiment loops with quantifiable metrics (hypothesis → measure → keep/discard)
- All three MUST run tests before claiming done

---

## QA Agents

Review code quality and fix issues found during review.

| Type | Tools | Skills | Thinking | Context | Memory | MCP |
|------|-------|--------|----------|---------|--------|-----|
| `qa-reviewer` | read-only | qa-validation-loop | deep | full | full | none |
| `qa-fixer` | full | verification-before-completion | standard | full | full | none |
| `nyquist-auditor` | read-only | qa-validation-loop | deep | full | full | none |

**Notes:**
- `qa-reviewer` is READ-ONLY -- analyzes code against acceptance criteria, reports issues
- `qa-fixer` receives issues from reviewer and fixes them, then verifies
- `nyquist-auditor` maps requirements to planned tests (Nyquist pre-flight) and audits post-implementation coverage
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

## Validation Agents

Verify documents and code against requirements and reality.

| Type | Tools | Skills | Thinking | Context | Memory | MCP |
|------|-------|--------|----------|---------|--------|-----|
| `skeptic` | read-only | -- | deep | full | full | none |
| `quality-validator` | read-only | qa-validation-loop | deep | full | full | none |
| `adequacy-validator` | read-only | qa-validation-loop | deep | full | full | none |

**Notes:**
- `skeptic` verifies factual claims (file paths, function names, dependencies) against actual codebase. Anti-hallucination gate.
- `quality-validator` checks document quality: structure, completeness, acceptance criteria testability, contradictions, template compliance
- `adequacy-validator` checks solution adequacy: feasibility, sizing, overengineering, underengineering, better alternatives
- Use in chain: skeptic -> quality-validator -> adequacy-validator (for tech-spec review)
- All are READ-ONLY — analyze and report, never modify files

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
| `pipeline-lead` | full | subagent-driven-development, skill-evolution | deep | full | full | none |
| `wave-coordinator` | full | subagent-driven-development, task-decomposition | standard | standard | patterns | none |
| `fleet-orchestrator` | full | ao-fleet-spawn | deep | full | full | none |
| `ao-hybrid-coordinator` | full | ao-hybrid-spawn, subagent-driven-development | deep | full | full | none |

**Notes:**
- `pipeline-lead` owns the full pipeline lifecycle (PIPELINE.md state machine)
- `wave-coordinator` manages a single wave of parallel agents within a pipeline phase
- `fleet-orchestrator` manages AO_FLEET phases: spawns sessions via `ao` CLI, monitors, collects results, kills sessions
- `ao-hybrid-coordinator` manages AO_HYBRID phases: spawns full Claude Code sessions via `ao spawn --prompt-file`, monitors progress, collects results, merges worktrees

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

## Build Error Resolvers

Language-specific agents for diagnosing and fixing build/compile/dependency errors.

| Type | Tools | Skills | Thinking | Context | Memory | MCP |
|------|-------|--------|----------|---------|--------|-----|
| `generic-build-resolver` | full | error-recovery, systematic-debugging | deep | full | full | none |
| `python-build-resolver` | full | error-recovery, systematic-debugging | standard | standard | patterns | none |
| `typescript-build-resolver` | full | error-recovery, systematic-debugging | standard | standard | patterns | none |
| `go-build-resolver` | full | error-recovery, systematic-debugging | standard | standard | patterns | none |
| `rust-build-resolver` | full | error-recovery, systematic-debugging | standard | standard | patterns | none |

**Notes:**
- `generic-build-resolver` auto-detects language from error output, then applies language-specific strategies
- `python-build-resolver` handles: pip/uv/poetry dependency errors, import errors, venv issues, wheel build failures
- `typescript-build-resolver` handles: tsc errors, webpack/esbuild/vite build failures, npm dependency conflicts, type errors
- `go-build-resolver` handles: go build errors, go mod tidy, CGO linking errors, missing packages
- `rust-build-resolver` handles: cargo build errors, borrow checker issues, linker errors, feature flag conflicts
- All resolvers follow: read error → form hypotheses → test most likely → fix root cause → verify
- Reference language rules: `cat .claude/guides/language-rules/{language}.md`

---

### Adding a New Agent Type

1. Add entry to the appropriate category table (all 6 properties required)
2. If the agent has a complex prompt, create `.claude/prompts/{type}.md`
3. Update this file and teammate-prompt-template.md if the role has special rules
4. Sync to `shared/templates/new-project/.claude/agents/registry.md`
