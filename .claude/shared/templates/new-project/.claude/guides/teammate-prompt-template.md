# Teammate Prompt Template

> Mandatory template for teammate prompts when spawning agents in Agent Teams Mode.
> BLOCKING: Cannot spawn teammate without "## Required Skills" section.

---

## Template

When creating a prompt for a teammate via Task tool, ALWAYS use this structure:

```
You are a teammate on team "{team-name}". Your name is "{name}".

## Agent Type
{type} (from .claude/agents/registry.md)
- Tools: {read-only | full | full + web}
- Thinking: {quick | standard | deep}

## Required Skills
- {skill-1}: {one-line description}

## Memory Context
{Injected from typed memory — patterns, gotchas, relevant codebase map entries}

## Verification Rules (MANDATORY)
- Run tests before claiming done
- Verify each acceptance criterion with evidence (VERIFY/RESULT format)
- If any check fails → fix first, do NOT claim done
- Update work/attempt-history.json if retry

## Your Task
{detailed task description}

## Acceptance Criteria
{what "done" looks like — measurable, verifiable}

## Constraints
{technical constraints, compatibility requirements}
```

---

## Memory Injection Protocol

Before spawning a teammate, inject relevant context from typed memory:

### Step 1: Read Agent Registry
Look up the agent type in `.claude/agents/registry.md`. Use the Memory column:
- **none**: Skip memory injection (utility tasks)
- **patterns**: Include .claude/memory/patterns.md
- **gotchas**: Include .claude/memory/gotchas.md
- **patterns + gotchas**: Include both
- **full**: Include patterns.md + gotchas.md + relevant entries from codebase-map.json

### Step 2: Build Memory Context Block
```
## Memory Context

### Project Patterns
{content from .claude/memory/patterns.md — relevant sections only}

### Known Gotchas
{content from .claude/memory/gotchas.md — relevant sections only}

### Relevant Files (from codebase map)
{entries from .claude/memory/codebase-map.json matching task scope}
```

### Step 3: Inject into Prompt
Place the Memory Context block after ## Agent Type and before ## Verification Rules.

### Why This Matters
- Agents start with project-specific knowledge, not from scratch
- Gotchas prevent repeating past mistakes
- Patterns ensure consistency across agents
- ~80% token reduction vs loading full CLAUDE.md (inspired by Auto-Claude's focused prompts)

---

## Focused Prompt Files

For complex agent roles, use dedicated prompt files from `.claude/prompts/`:

| Role | Prompt File | When to Use |
|------|-------------|-------------|
| Planner | .claude/prompts/planner.md | Planning phase, task decomposition |
| Coder | .claude/prompts/coder.md | Implementation subtasks |
| QA Reviewer | .claude/prompts/qa-reviewer.md | QA validation reviews |
| QA Fixer | .claude/prompts/qa-fixer.md | Fixing QA-identified issues |
| Insight Extractor | .claude/prompts/insight-extractor.md | Post-session insight extraction |

### Using Focused Prompts
1. Load the prompt file content
2. Inject task-specific variables (task description, files, criteria)
3. Inject memory context (per Memory Injection Protocol above)
4. The focused prompt REPLACES the generic template for that role

### When to Use Focused vs Generic
- **Focused prompt**: Agent has a dedicated .claude/prompts/{type}.md file → use it
- **Generic template**: No dedicated prompt file → use this template

---

## Skill Assignment Rules

### Minimum Requirements
- ANY teammate that writes/modifies code → `verification-before-completion`

### Role-Based Skills (from TEAM ROLE SKILLS MAPPING in CLAUDE.md)

| Role | Agent Type | Skills |
|------|-----------|--------|
| Developer/Implementer | coder | verification-before-completion |
| Complex Implementer | coder-complex | verification-before-completion |
| Researcher/Explorer | spec-researcher | codebase-mapping |
| Planner | planner | task-decomposition |
| QA Reviewer | qa-reviewer | qa-validation-loop |
| QA Fixer | qa-fixer | verification-before-completion |
| Debugger | analyzer/fixer | systematic-debugging |
| Pipeline Lead | pipeline-lead | subagent-driven-development |
| Insight Extractor | insight-extractor | — (quick pass) |

### When No Skills Apply
If a task is purely non-code (file copy, git operations, documentation):
- Still include `## Required Skills` section
- Write: "No specific skills required for this task"
- This confirms skills were consciously evaluated, not forgotten

---

## Worktree Instructions

When teammates work in isolated worktrees (manual setup or worktree-per-agent), add this to the prompt:

```
## Working Directory
Your working directory is {worktree_path}.
- All file operations MUST be relative to this directory
- Do NOT modify files outside your worktree
- Commit your changes with a descriptive message before finishing
```

This is REQUIRED when:
- Agent Teams Mode spawns parallel agents (automatic)
- Manual worktree-per-agent setup
- 5+ agents in same AGENT_TEAMS phase (recommended)

---

## Recovery Context Injection

When retrying a subtask (from recovery manager), inject attempt history:

```
## Previous Attempts
Attempt 1: {approach} → {outcome}: {error_message}
Attempt 2: {approach} → {outcome}: {error_message}

⚠️ {Circular fix warning if detected}

You MUST try a fundamentally different approach from the above.
Reference: .claude/guides/recovery-manager.md
```

Load from: work/attempt-history.json (if exists)

---

## Anti-Patterns

- Промпт без секции "Required Skills" — ЗАПРЕЩЕНО
- Generic "use best practices" вместо конкретных скиллов — бесполезно
- Назначение скиллов без проверки по TEAM ROLE SKILLS MAPPING — неправильный выбор
- Пропуск verification-before-completion для implementer роли — основная ошибка

---

## Examples

### Good: Developer teammate
```
You are a teammate on team "feature-dev". Your name is "backend-dev".

## Required Skills
- verification-before-completion: evidence-based completion with test runs

## Verification Rules (MANDATORY)
- Run tests before claiming done
- Verify each acceptance criterion with evidence
- If any check fails → fix first, do NOT claim done

## Your Task
Implement the new /status endpoint...

## Acceptance Criteria
- Endpoint returns 200 with JSON status
- Tests pass

## Constraints
- Use existing router pattern from routes/
```

### Good: Non-code task
```
You are a teammate on team "cleanup". Your name is "sync-agent".

## Required Skills
No specific skills required for this task (file sync only).

## Your Task
Copy modified files from .claude/hooks/ to .claude/shared/templates/new-project/.claude/hooks/

## Acceptance Criteria
- Files are identical after copy
```

---

## Expert Panel Roles

When spawning expert panel teammates, use the EXPERT PANEL ROLE SKILLS MAPPING from CLAUDE.md:

| Role | Skills to Load |
|------|---------------|
| Business Analyst | codebase-mapping |
| System Architect | codebase-mapping |
| Security Analyst | — (Opus knows OWASP) |
| QA Strategist | verification-before-completion |
| Data Architect | codebase-mapping |
| Researcher | codebase-mapping |
| Risk Assessor | systematic-debugging |

**Note:** Expert panel agents are READ-ONLY researchers. Most don't need skills — they analyze using general knowledge. Only load skills when the agent needs project-specific procedural knowledge.

### Key Differences from Implementation Teammates

- Expert panel agents are **READ-ONLY** — they analyze and report, they do NOT modify files
- Every expert MUST reference the Priority Ladder: `cat .claude/guides/priority-ladder.md`
- Expert output is sent via SendMessage to lead, not written to files
- Use the expert prompt template from `.claude/guides/expert-panel-workflow.md`

### Bad: Missing skills (BLOCKED)
```
You are a teammate on team "feature-dev". Your name is "dev-1".

## Your Task
Implement the login feature...
```
This prompt would be BLOCKED — no "## Required Skills" section.
