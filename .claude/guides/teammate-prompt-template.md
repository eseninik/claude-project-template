# Teammate Prompt Template

> **IMPORTANT**: Do NOT manually write teammate prompts. Use spawn-agent.py:
> `python .claude/scripts/spawn-agent.py --task "..." --team X --name Y -o work/prompts/name.md`
> This auto-injects: agent type → skills → agent memory → handoff template.

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

MANDATORY: Include full skill content below, not just skill names.
Subagents cannot load skills themselves — they need the content IN this prompt.
If total skill content exceeds ~1,500 lines, include only the Protocol/Steps sections, skip examples.

### {skill-1}
{Read and paste the FULL content of .claude/skills/{skill-1}/SKILL.md here}

### {skill-2} (if needed)
{Read and paste the FULL content of .claude/skills/{skill-2}/SKILL.md here}

## Codex Second Opinion (MANDATORY)

Before starting your work, get Codex opinion:
```bash
py -3 .claude/scripts/codex-ask.py "I'm about to: {TASK_DESCRIPTION}. What should I watch for?"
```
Read the output and adjust your approach if needed. After finishing, verify:
```bash
py -3 .claude/scripts/codex-ask.py "Review my changes in {files}. Check for bugs and edge cases."
```

## Agent Memory (if available)

Check if `.claude/agent-memory/{agent-type}/MEMORY.md` exists for this agent's type.
If yes, inject the first 200 lines into the prompt below Required Skills.

### Agent Memory
{Paste first 200 lines of .claude/agent-memory/{agent-type}/MEMORY.md}

Agent memory contains project-specific learnings accumulated across sessions.
The agent should READ this at start and UPDATE it in their handoff block if they learned something new.

## Memory Context
{Injected from typed memory — patterns, gotchas, relevant codebase map entries}

## Verification Rules (MANDATORY)
- Run tests before claiming done
- Verify each acceptance criterion with evidence (VERIFY/RESULT format)
- If any check fails → fix first, do NOT claim done
- Update work/attempt-history.json if retry
- Verify logging coverage: every new function has entry/exit logs, every catch block logs errors (ref: .claude/guides/logging-standards.md)
- For high-risk tasks (auth, payments, migrations, security): run Codex cross-model review before claiming done. Use `cross-model-review` skill or run `codex exec` directly (ref: .claude/guides/codex-integration.md)
- After writing a file, verify with compile/typecheck instead of re-reading it (mypy/tsc/cargo check). Trust your writes — re-reading wastes turns exponentially.
- When tool output exceeds ~200 lines, extract key findings into 10-20 lines and work from the summary. Large outputs drain context rapidly (microcompact principle).
- After completing a skill-based task, check the `## Related` section at the bottom of the SKILL.md for next steps or connected skills to invoke

## Results Board
Before starting your task, check if `work/results-board.md` exists. If yes:
- Read it for context on what other agents have tried
- Note any failed approaches related to your task — do NOT repeat them
- After completing your task, append your result entry to the board

## Handoff Output (MANDATORY when your task is done)

When completing your task, output this structured block:

=== PHASE HANDOFF: {your_task_name} ===
Status: PASS | REWORK | BLOCKED
Files Modified:
- [path/to/file1.ext]
- [path/to/file2.ext]
Tests: [passed/failed/skipped counts or N/A]
Skills Invoked:
- [skill-name via Skill tool / embedded in prompt / none]
Decisions Made:
- [key decision with brief rationale]
Learnings:
- Friction: [what was hard or slow] | NONE
- Surprise: [what was unexpected] | NONE
- Pattern: [reusable insight for knowledge.md] | NONE
Next Phase Input: [what the next agent/phase needs to know]
=== END HANDOFF ===

## Your Task
{detailed task description}

## Acceptance Criteria
{what "done" looks like — measurable, verifiable}

## Constraints
{technical constraints, compatibility requirements}

## Read-Only Files (Evaluation Firewall)
{List files the implementer CANNOT modify. Default list below — add project-specific files.}
- All test files (test_*, *.test.*, *.spec.*)
- Acceptance criteria files (user-spec.md, task descriptions)
- Evaluation/benchmark scripts
- Codex review results (.codex/reviews/*.json) — reviewer cannot modify review output
- CI/CD pipeline configurations

If you need to modify any read-only file, STOP and ask the team lead first.
```

---

## Memory Injection Protocol

Before spawning a teammate, inject relevant context from typed memory:

### Step 1: Read Agent Registry
Look up the agent type in `.claude/agents/registry.md`. Use the Memory column:
- **none**: Skip memory injection (utility tasks)
- **patterns**: Include `.claude/memory/knowledge.md` (Patterns section)
- **gotchas**: Include `.claude/memory/knowledge.md` (Gotchas section)
- **patterns + gotchas**: Include `.claude/memory/knowledge.md` (both sections)
- **full**: Include full `.claude/memory/knowledge.md`

### Step 2: Build Memory Context Block
```
## Memory Context

### Project Patterns
{content from .claude/memory/knowledge.md Patterns section — relevant sections only}

### Known Gotchas
{content from .claude/memory/knowledge.md Gotchas section — relevant sections only}
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
- ANY teammate that writes/modifies code → must add structured logging per `.claude/guides/logging-standards.md`

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

## AO Hybrid Agent Prompts

When spawning AO Hybrid agents (via `ao spawn --prompt-file`), add these to the prompt:

1. **Skill audit requirement:** "In your handoff output, list all skills you invoked via the Skill tool under 'Skills Invoked:'"
2. **Absolute paths:** Use absolute project path (e.g., `/c/Bots/Migrator bots/project-name/.claude/skills/`) instead of relative `.claude/skills/` to avoid confusion with global skills in `~/.claude/skills/`
3. **Unique task context:** AO agents are full Claude Code sessions — they read CLAUDE.md, have Skill tool access, and can discover skills autonomously. But we need the audit trail.

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
- Код без логирования в новых функциях — основная причина слепой отладки в продакшне

---

## Examples

### Good: Developer teammate
```
You are a teammate on team "feature-dev". Your name is "backend-dev".

## Required Skills

### verification-before-completion
{FULL content of .claude/skills/verification-before-completion/SKILL.md pasted here — 140 lines}

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
