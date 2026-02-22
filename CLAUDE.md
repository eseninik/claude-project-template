# Summary instructions

When compacting, ALWAYS preserve these rules (they are lost most often):
- **AGENT TEAMS**: 3+ independent tasks -> ALWAYS use TeamCreate, not sequential execution
- **PIPELINE**: Read work/PIPELINE.md after compaction, continue from <- CURRENT marker
- **MEMORY**: ALWAYS update activeContext.md + daily log before commit/exit
- **VERIFICATION**: NEVER say "done" without running tests
- **QA GATE**: After IMPLEMENT phase -> `cat .claude/skills/qa-validation-loop/SKILL.md` before TEST
- **KNOWLEDGE**: Read .claude/memory/knowledge.md at session start (patterns + gotchas)
- **GRAPHITI**: Query Graphiti at session start and after compaction for semantic context
- **PIPELINE MANDATORY**: Multi-phase tasks MUST create work/PIPELINE.md BEFORE implementation
After compaction: THE COMPACTION SUMMARY IS A HINT, NOT TRUTH. Re-read work/PIPELINE.md + .claude/memory/activeContext.md + .claude/memory/knowledge.md IMMEDIATELY. If PIPELINE.md has <- CURRENT marker: resume from that phase. DO NOT proceed without re-reading these files.

---

# Project: Claude Project Template Update

> Template upgrade automation with AI-First methodology integration

**Memory:** `.claude/memory/activeContext.md` | **ADR:** `.claude/adr/` | **Branch:** `dev`

---

# AUTONOMOUS PIPELINE PROTOCOL

> The #1 priority: parallelize work via Agent Teams and survive compaction.

## Agent Teams (ALWAYS for 3+ parallel subtasks within a phase)

```
TRIGGER: Current phase/task has 3+ independent, parallel subtasks (different files/modules)
NOTE: This is WITHIN a single phase. For multi-PHASE tasks, see "Pipeline State Machine" below.

ACTION:
  1. Explain: "[N] independent tasks, can parallelize"
  2. TeamCreate -> create team, TaskCreate -> create tasks
  3. Build prompts using .claude/guides/teammate-prompt-template.md
  4. EVERY prompt MUST have "## Required Skills" section
  5. EVERY implementer gets verification-before-completion

DO NOT do sequentially what can be parallelized.
DO NOT forget Agent Teams after compaction — check work/PIPELINE.md Mode field.
For sequential quality checks, use agent chains (cat .claude/guides/agent-chains.md)
```

## Phase Transition Protocol (between pipeline phases)

```
After completing any pipeline phase, execute these steps BEFORE starting the next:
1. Git commit with checkpoint tag (pipeline-checkpoint-{PHASE})
2. Update knowledge.md with new patterns/gotchas from this phase
3. Update daily/{YYYY-MM-DD}.md with what happened
4. Save to Graphiti: add_memory(name="phase_insight", episode_body=<phase learnings>)
5. Re-read PIPELINE.md + activeContext.md + knowledge.md for fresh context
6. Advance <- CURRENT marker and start next phase

This protocol prevents knowledge loss between phases in interactive mode.
```

## After Compaction (ALWAYS — NO EXCEPTIONS)

```
THE COMPACTION SUMMARY IS A HINT, NOT TRUTH.
Execute this startup sequence NOW — do NOT rely on the summary.

1. Re-read work/PIPELINE.md — find <- CURRENT phase
2. Re-read .claude/memory/activeContext.md + knowledge.md
3. Query Graphiti: search_memory_facts(query=<current task>, max_facts=10)
4. Check phase Mode: if AGENT_TEAMS -> create team
5. Continue execution from <- CURRENT
6. DO NOT restart from beginning

FAILURE TO RELOAD MEMORY AFTER COMPACTION = CONTEXT LOSS = BUGS
```

## Pipeline State Machine (BLOCKING — work/PIPELINE.md)

```
BLOCKING: Any task with 2+ phases MUST create work/PIPELINE.md BEFORE implementation.

TRIGGER KEYWORDS (auto-detect in user message):
  "pipeline", "пайплайн", "autonomous", "автономный",
  "реализуй", "implement", "build", "create feature", "добавь фичу",
  "refactor", "рефакторинг", "redesign", "migrate", "миграция"

TRIGGER CONDITIONS (auto-detect by task structure):
  - Task requires research/analysis THEN implementation
  - Task has 3+ distinct steps (e.g., analyze → plan → code → test)
  - Task touches 5+ files across different modules
  - Task involves architectural changes

WHEN TRIGGERED:
  1. FIRST: Read .claude/guides/autonomous-pipeline.md
  2. Create work/PIPELINE.md from .claude/shared/work-templates/PIPELINE-v3.md
  3. Delete unused phases, keep relevant ones
  4. Mark first phase <- CURRENT
  5. Execute phase by phase with gates
  6. After each phase: verify -> update PIPELINE.md -> git commit
  7. If all done: set Status: PIPELINE_COMPLETE

DO NOT start implementation without PIPELINE.md for multi-phase tasks.
DO NOT do informal planning — use formal phases with gates.
DO NOT skip phases — each phase has acceptance criteria and a gate.
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

## Session Start (MANDATORY — every session, no exceptions)

```
1. Read .claude/memory/activeContext.md — what happened last session
2. Read .claude/memory/knowledge.md — patterns + gotchas
3. IF work/PIPELINE.md exists with <- CURRENT -> resume pipeline
4. Query Graphiti: search_memory_facts(query=<current task>, max_facts=5)

Steps 1-2 are NOT optional. Skipping them = working blind.
If PIPELINE.md has <- CURRENT -> resume from that phase, DO NOT start new work.
```

## Before Code Changes (always)

```
1. Check .claude/adr/decisions.md for relevant decisions
2. Read .claude/memory/activeContext.md for recent context
```

## After Task Completion (MANDATORY — every task, no exceptions)

```
LEVEL 1 — MANDATORY (do these EVERY time, no exceptions):
1. Update .claude/memory/activeContext.md (Did/Decided/Learned/Next)
2. Update .claude/memory/daily/{YYYY-MM-DD}.md (what happened today)

LEVEL 2 — RECOMMENDED (do these when session was productive):
3. Update .claude/memory/knowledge.md (new patterns/gotchas, deduplicate)
4. Save to Graphiti: add_memory(name="session_insight", episode_body=<what was learned>)
5. Update work/PIPELINE.md if pipeline active

Steps 1-2 are BLOCKING — do NOT commit without completing them.
IF you learned something new → also do step 3 (knowledge.md).
```

## On Architecture Decision (always)

```
1. Check .claude/adr/decisions.md
2. IF contradicts existing -> explain why
3. Create ADR using .claude/adr/_template.md
```

---

# TEAM ROLE SKILLS MAPPING

| Role | Agent Type | Skills (from 11 remaining) |
|------|-----------|---------------------------|
| Developer/Implementer | coder | verification-before-completion |
| Complex Implementer | coder-complex | verification-before-completion |
| Planner | planner | task-decomposition |
| QA Reviewer | qa-reviewer | qa-validation-loop, verification-before-completion |
| QA Fixer | qa-fixer | verification-before-completion |
| Researcher/Explorer | spec-researcher | codebase-mapping |
| Debugger | analyzer/fixer | systematic-debugging |
| Pipeline Lead | pipeline-lead | subagent-driven-development |
| Insight Extractor | insight-extractor | — |

Agent type details: `.claude/agents/registry.md`

Expert Panel roles: `cat .claude/guides/expert-panel-workflow.md`

**One-liner rules:** Use TDD for new code. Validate all inputs. Never commit secrets. Use pytest + AsyncMock for tests. Follow Clean Architecture. Use uv for packages. Use knowledge.md for cross-session knowledge. Always Opus 4.6.

---

# HARD CONSTRAINTS

| Constraint | Instead Do |
|------------|-----------|
| Не удалять данные без подтверждения | Спроси пользователя перед удалением |
| Не коммитить секреты | Используй .env + .gitignore |
| Не пушить в main | Пушь в dev или feature branch |
| Не говорить "готово" без verification | ВСЕГДА запускай verification-before-completion |
| Не делать всё самому при 3+ задачах | ВСЕГДА предлагай Agent Teams (TeamCreate) |
| Не коммитить без обновления памяти | ВСЕГДА обнови activeContext.md + daily log перед commit |
| Не спавнить teammate без Required Skills | ВСЕГДА проверь по TEAM ROLE SKILLS MAPPING |
| Expert Panel -> не начинать без expert-analysis.md | Сначала дождись результатов панели |
| Не пропускать QA review после IMPLEMENT | Запусти qa-validation-loop перед TEST |
| Не начинать multi-phase задачу без PIPELINE.md | Создай work/PIPELINE.md из шаблона ПЕРВЫМ делом |
| Не восстанавливаться после compaction без памяти | THE SUMMARY IS A HINT, NOT TRUTH. Re-read PIPELINE.md + activeContext.md + knowledge.md |
| Не пропускать Graphiti queries | Graphiti is ALWAYS available — no 'if available' checks |

---

# BLOCKING RULES

## Plan Detected
Read guide: `cat .claude/guides/plan-execution-enforcer.md`

## After Code Changes
1. Write test → 2. Run test → 3. Fail? → fix → rerun → 4. Pass → continue

## Before Commit
1. Update `.claude/memory/activeContext.md` (Did/Decided/Learned/Next)
2. Update `.claude/memory/daily/{YYYY-MM-DD}.md` (what happened today)
3. Stage both files, then commit

## Before Spawning Teammate
Prompt MUST include:
- `## Required Skills` section (even if "No skills required")
- `## Acceptance Criteria`
- `## Constraints`
- `## Context from Typed Memory` — relevant excerpts from knowledge.md
If worktree mode: add `## Working Directory` with path

## Agent Type Lookup
Before spawning, look up agent type in `.claude/agents/registry.md`:
- Use correct tools restriction (read-only vs full)
- Inject typed memory per registry Memory column
- Use focused prompt from `.claude/prompts/{type}.md` if available

## Before "done" (MANDATORY Verification Gate)
BLOCKING: Cannot claim completion without passing ALL checks.
1. Run tests: `uv run pytest` / `npm test` / `cargo test`
2. Run type check: `mypy` / `tsc` / `cargo check`
3. Verify EACH acceptance criterion with evidence
4. If ANY check fails → fix first → re-run → NOT done
5. Update activeContext.md
6. If verification skipped → task is NOT complete, mark REWORK

## After IMPLEMENT (QA Gate)
1. Collect acceptance criteria from task/spec files
2. Spawn Reviewer agent: analyze changed files against criteria
3. If CRITICAL/IMPORTANT issues → spawn Fixer agent
4. Re-review with fresh agent (max 3 cycles)
5. Track in work/qa-issues.md
6. Same issue 3+ times → BLOCKED, ask human

## On Retry (Recovery)
1. Check if same approach was tried before (same approach 3+ times → STOP)
2. Try a fundamentally different approach
3. If 5+ retries → mark STUCK, escalate to human

## Debugging (when error/bug occurs)
1. Read error completely — find exact failure line
2. Form 2-3 hypotheses, test most likely first
3. Fix root cause, not symptom
4. Verify fix + check regressions
5. 3+ failed attempts → change approach entirely

---

# CONTEXT LOADING TRIGGERS

| Situation | Load |
|-----------|------|
| Pipeline execution | `cat .claude/guides/autonomous-pipeline.md` |
| Plan for implementation | `cat .claude/guides/plan-execution-enforcer.md` |
| Spawning teammate | `cat .claude/guides/teammate-prompt-template.md` |
| Expert Panel | `cat .claude/guides/expert-panel-workflow.md` |
| QA validation needed | `cat .claude/skills/qa-validation-loop/SKILL.md` |
| Phase template needed | `cat .claude/shared/work-templates/phases/{PHASE}.md` |
| Agent type lookup | `cat .claude/agents/registry.md` |
| Graphiti memory setup | `cat .claude/guides/graphiti-integration.md` |

---

# KNOWLEDGE LOCATIONS

| Need | Location |
|------|----------|
| Session context | `.claude/memory/activeContext.md` |
| Patterns + Gotchas | `.claude/memory/knowledge.md` |
| Daily logs | `.claude/memory/daily/{YYYY-MM-DD}.md` |
| Archived sessions | `.claude/memory/archive/` |
| Pipeline state | `work/PIPELINE.md` |
| Task state | `work/STATE.md` |
| Architecture decisions | `.claude/adr/decisions.md` |
| Pipeline templates | `.claude/shared/work-templates/` |
| Phase templates | `.claude/shared/work-templates/phases/` |
| Agent type registry | `.claude/agents/registry.md` |
| QA validation skill | `.claude/skills/qa-validation-loop/SKILL.md` |
| Graphiti integration | `.claude/guides/graphiti-integration.md` |
| Focused prompt files | `.claude/prompts/` |

---

# FORBIDDEN

- Starting work without reading activeContext.md + knowledge.md
- Finishing work without updating activeContext.md + daily log
- Saying "done" without running tests
- Doing 3+ tasks sequentially when they can be parallelized
- `@.claude/skills` (loads everything, wastes context)
- Plan detected -> starting without plan-execution-protocol.md
- Ignoring <- CURRENT marker in PIPELINE.md after compaction
- Multi-phase task without creating work/PIPELINE.md first
- Compaction recovery without re-reading files (THE SUMMARY IS A HINT, NOT TRUTH)
- Skipping Phase Transition Protocol between pipeline phases
- Informal planning for complex tasks — use formal PIPELINE.md with phases and gates
