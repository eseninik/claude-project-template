# Summary instructions

When compacting, ALWAYS preserve these rules (they are lost most often):
- **AGENT TEAMS**: 3+ independent tasks -> ALWAYS use TeamCreate, not sequential execution
- **PIPELINE**: Read work/PIPELINE.md after compaction, continue from <- CURRENT marker
- **MEMORY**: ALWAYS update .claude/memory/activeContext.md before commit/exit
- **VERIFICATION**: NEVER say "done" without running tests
After compaction: re-read work/PIPELINE.md and work/STATE.md immediately.

---

# Project: Claude Project Template Update

> Template upgrade automation with AI-First methodology integration

**Context:** `.claude/skills/project-knowledge/guides/` | **Memory:** `.claude/memory/activeContext.md` | **ADR:** `.claude/adr/` | **Branch:** `dev`

---

# AUTONOMOUS PIPELINE PROTOCOL

> The #1 priority: parallelize work via Agent Teams and survive compaction.

## Agent Teams (ALWAYS for 3+ tasks)

```
TRIGGER: Task has 3+ independent subtasks (different files/modules)

ACTION:
  1. Explain: "[N] independent tasks, can parallelize"
  2. TeamCreate -> create team, TaskCreate -> create tasks
  3. Build prompts using .claude/guides/teammate-prompt-template.md
  4. EVERY prompt MUST have "## Required Skills" section
  5. EVERY implementer gets verification-before-completion

DO NOT do sequentially what can be parallelized.
DO NOT forget Agent Teams after compaction — check work/PIPELINE.md Mode field.
```

## After Compaction (ALWAYS)

```
1. Re-read work/PIPELINE.md — find <- CURRENT phase
2. Re-read work/STATE.md — project state
3. Check phase Mode: if AGENT_TEAMS -> create team
4. Continue execution from <- CURRENT
5. DO NOT restart from beginning
```

## Pipeline State Machine (work/PIPELINE.md)

```
When task has multiple phases:
1. Create work/PIPELINE.md with phases, modes, acceptance criteria
2. Mark first phase <- CURRENT
3. Execute phase by phase
4. After each phase: verify -> update PIPELINE.md -> git commit
5. If all done: set Status: PIPELINE_COMPLETE

Template: .claude/shared/work-templates/PIPELINE.md
Full guide: cat .claude/guides/autonomous-pipeline.md
```

## Expert Panel (explicit trigger)

```
TRIGGER: "Agent Teams Mode" OR "экспертная панель"
GUIDE: cat .claude/guides/expert-panel-workflow.md
SKILL: cat .claude/skills/expert-panel/SKILL.md
BLOCKING: No implementation without work/expert-analysis.md
```

---

# AUTO-BEHAVIORS

## Session Start (always)

```
1. Read .claude/memory/activeContext.md
2. Read work/STATE.md
3. IF work/PIPELINE.md exists with <- CURRENT -> resume pipeline
4. IF unfinished work -> "Продолжаю: [task]"
5. ELSE -> "Готов к новой задаче"
```

## Before Code Changes (always)

```
1. Read .claude/skills/project-knowledge/guides/architecture.md
2. Read .claude/skills/project-knowledge/guides/patterns.md
3. Check .claude/adr/decisions.md for relevant decisions
```

## After Task Completion (always)

```
1. Update .claude/memory/activeContext.md (Did/Decided/Learned/Next)
2. Update work/STATE.md
3. Update work/PIPELINE.md if pipeline active
4. IF architectural decision -> create ADR
5. Commit with meaningful message
```

## On Architecture Decision (always)

```
1. Check .claude/adr/decisions.md
2. IF contradicts existing -> explain why
3. Create ADR using .claude/adr/_template.md
```

---

# TEAM ROLE SKILLS MAPPING

| Role | Required Skills | Additional Skills |
|------|----------------|-------------------|
| Developer/Implementer | verification-before-completion | TDD, async-python-patterns, telegram-bot-architecture |
| Reviewer | testing-anti-patterns | code-reviewer, security-checklist |
| Researcher/Explorer | — | codebase-mapping, project-knowledge |
| Debugger | — | systematic-debugging, root-cause-tracing |
| Security | security-checklist | secret-scanner |
| Architect/Planner | — | architecture-patterns, tech-spec-planning |

Expert Panel roles: `cat .claude/guides/expert-panel-workflow.md`

---

# HARD CONSTRAINTS

| Constraint | Instead Do |
|------------|-----------|
| Не удалять данные без подтверждения | Спроси пользователя перед удалением |
| Не коммитить секреты | Используй .env + .gitignore |
| Не пушить в main | Пушь в dev или feature branch |
| Не говорить "готово" без verification | ВСЕГДА запускай verification-before-completion |
| Не делать всё самому при 3+ задачах | ВСЕГДА предлагай Agent Teams (TeamCreate) |
| Не коммитить без обновления памяти | ВСЕГДА обнови activeContext.md перед commit |
| Не спавнить teammate без Required Skills | ВСЕГДА проверь по TEAM ROLE SKILLS MAPPING |
| Expert Panel -> не начинать без expert-analysis.md | Сначала дождись результатов панели |

---

# BLOCKING RULES

## Plan Detected
ENFORCE: `cat .claude/guides/plan-execution-enforcer.md`

## After Code Changes
```
1. Write test -> 2. Run -> 3. If fail -> fix -> repeat
```

## Before Commit
```
BLOCK until .claude/memory/activeContext.md is updated and staged.
```

## Before Spawning Teammate
```
BLOCK until prompt has "## Required Skills" section.
Template: .claude/guides/teammate-prompt-template.md
```

## Before "готово"
```
1. cat .claude/skills/verification-before-completion/SKILL.md
2. Execute verification
3. Only then claim completion
```

---

# CONTEXT LOADING TRIGGERS

| Situation | Load |
|-----------|------|
| Pipeline execution | `cat .claude/guides/autonomous-pipeline.md` |
| Error occurred | `cat .claude/guides/error-handling.md` |
| Complex decision | `cat .claude/guides/decision-making.md` |
| Plan for implementation | `cat .claude/guides/plan-execution-enforcer.md` |
| Spawning teammate | `cat .claude/guides/teammate-prompt-template.md` |
| Expert Panel | `cat .claude/guides/expert-panel-workflow.md` |
| External service needed | `cat .claude/skills/mcp-integration/SKILL.md` |
| Dependency analysis | `cat .claude/guides/dependency-analysis.md` |

---

# KNOWLEDGE LOCATIONS

| Need | Location |
|------|----------|
| Session context | `.claude/memory/activeContext.md` |
| Pipeline state | `work/PIPELINE.md` |
| Task state | `work/STATE.md` |
| Architecture decisions | `.claude/adr/decisions.md` |
| Project architecture | `.claude/skills/project-knowledge/guides/` |
| Pipeline templates | `.claude/shared/work-templates/` |
| Ralph Loop script | `scripts/ralph.sh` |

---

# FORBIDDEN

- Starting work without reading memory/activeContext.md
- Finishing work without updating memory
- Saying "done" without running tests
- Doing 3+ tasks sequentially when they can be parallelized
- `@.claude/skills` (loads everything, wastes context)
- Plan detected -> starting without plan-execution-protocol.md
- Ignoring <- CURRENT marker in PIPELINE.md after compaction
