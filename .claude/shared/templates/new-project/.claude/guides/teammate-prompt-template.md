# Teammate Prompt Template

> Обязательный шаблон для промптов при спавне агентов в Agent Teams Mode.
> BLOCKING: Нельзя спавнить teammate без секции "Required Skills".

---

## Template

При создании промпта для teammate через Task tool, ВСЕГДА используй эту структуру:

```
You are a teammate on team "{team-name}". Your name is "{name}".

## Required Skills
Before starting work, load and follow these skills:
- {skill-1}: `cat .claude/skills/{skill-1}/SKILL.md`
- {skill-2}: `cat .claude/skills/{skill-2}/SKILL.md`

## Your Task
{detailed task description}

## Acceptance Criteria
{what "done" looks like}

## Constraints
{technical constraints, compatibility requirements}
```

---

## Skill Assignment Rules

### Minimum Requirements
- ANY teammate that writes/modifies code → `verification-before-completion`

### Role-Based Skills (from TEAM ROLE SKILLS MAPPING in CLAUDE.md)

| Role | Skills (from 14 remaining) |
|------|---------------------------|
| Developer/Implementer | verification-before-completion |
| Researcher/Explorer | codebase-mapping, project-knowledge |
| Debugger | systematic-debugging |
| Pipeline Lead | subagent-driven-development, executing-plans |

### When No Skills Apply
If a task is purely non-code (file copy, git operations, documentation):
- Still include `## Required Skills` section
- Write: "No specific skills required for this task"
- This confirms skills were consciously evaluated, not forgotten

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
Before starting work, load and follow these skills:
- verification-before-completion: `cat .claude/skills/verification-before-completion/SKILL.md`

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
| Business Analyst | project-knowledge |
| System Architect | project-knowledge |
| Security Analyst | — (Opus knows OWASP) |
| QA Strategist | verification-before-completion |
| Data Architect | project-knowledge |
| Researcher | codebase-mapping |
| Risk Assessor | systematic-debugging |

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
