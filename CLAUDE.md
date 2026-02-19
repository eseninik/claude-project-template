# Summary instructions

When compacting, ALWAYS preserve these rules (they are lost most often):
- **AGENT TEAMS**: 3+ independent tasks -> ALWAYS use TeamCreate, not sequential execution
- **PIPELINE**: Read work/PIPELINE.md after compaction, continue from <- CURRENT marker
- **MEMORY**: ALWAYS update .claude/memory/activeContext.md before commit/exit
- **VERIFICATION**: NEVER say "done" without running tests
- **QA GATE**: After IMPLEMENT phase -> `cat .claude/skills/qa-validation-loop/SKILL.md` before TEST
- **TYPED MEMORY**: Read .claude/memory/patterns.md + gotchas.md at session start
- **GRAPHITI**: Query Graphiti at session start and after compaction for semantic context
- **RECOVERY**: Check work/attempt-history.json before retrying
- **PIPELINE MANDATORY**: Multi-phase tasks MUST create work/PIPELINE.md BEFORE implementation
After compaction: re-read work/PIPELINE.md + work/STATE.md + .claude/memory/activeContext.md + query Graphiti immediately.

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
2. Quick insight extraction: what worked, what failed, new patterns/gotchas
3. Update typed memory: patterns.md, gotchas.md, codebase-map.json
4. Save to Graphiti: add_memory(name="phase_insight", episode_body=<phase learnings>)
5. Re-read PIPELINE.md + STATE.md + typed memory for fresh context
6. Advance <- CURRENT marker and start next phase

This protocol prevents knowledge loss between phases in interactive mode.
```

## After Compaction (ALWAYS — NO EXCEPTIONS)

```
1. Re-read work/PIPELINE.md — find <- CURRENT phase
2. Re-read .claude/memory/activeContext.md + patterns.md + gotchas.md — typed memory
3. Query Graphiti — recover semantic context:
   - search_memory_facts(query=<current task description>, max_facts=10)
   - search_nodes(query=<current task description>, max_nodes=10)
4. Re-read work/STATE.md — project state
5. Check phase Mode: if AGENT_TEAMS -> create team
6. Continue execution from <- CURRENT
7. DO NOT restart from beginning

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
2. Read .claude/memory/patterns.md + gotchas.md — typed memory
3. Query Graphiti — semantic context:
   - search_memory_facts(query="recent session insights", max_facts=5)
   - search_memory_facts(query="known gotchas and pitfalls", max_facts=5)
   - search_nodes(query=<current task description>, max_nodes=5)
4. Read work/STATE.md — current project state
5. IF work/PIPELINE.md exists with <- CURRENT -> resume pipeline (DO NOT start new work)
6. IF work/attempt-history.json exists -> load recovery context
7. IF unfinished work -> "Продолжаю: [task]"
8. ELSE -> "Готов к новой задаче"

Steps 1-3 are NOT optional. Skipping them = working blind.
```

## Before Code Changes (always)

```
1. Check .claude/adr/decisions.md for relevant decisions
2. Read .claude/memory/activeContext.md for recent context
```

## After Task Completion (MANDATORY — every task, no exceptions)

```
1. Update .claude/memory/activeContext.md (Did/Decided/Learned/Next)
2. Update typed memory (file-based — always works):
   - .claude/memory/patterns.md (new patterns, deduplicate)
   - .claude/memory/gotchas.md (new gotchas, deduplicate)
   - .claude/memory/codebase-map.json (new file discoveries)
3. Save session insights to .claude/memory/session-insights/
4. Save to Graphiti (enriches future sessions):
   - add_memory(name="session_insight", episode_body=<what was learned>)
   - add_memory(name="pattern", episode_body=<new patterns>) if any
   - add_memory(name="gotcha", episode_body=<new pitfalls>) if any
5. Update work/STATE.md
6. Update work/PIPELINE.md if pipeline active
7. Update work/attempt-history.json (record good commit)
8. IF architectural decision -> create ADR
9. Commit with meaningful message

Steps 1-4 are BLOCKING — do NOT commit without completing them.
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

**One-liner rules (replace deleted skills):** Use TDD for new code. Validate all inputs. Never commit secrets. Use pytest + AsyncMock for tests. Follow Clean Architecture. Use uv for packages. Use typed memory (.claude/memory/) for cross-session knowledge. Use complexity assessment before QA. Use recovery manager on retries. Always Opus 4.6.

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
| Не пропускать QA review после IMPLEMENT | Запусти qa-validation-loop перед TEST |
| Не начинать multi-phase задачу без PIPELINE.md | Создай work/PIPELINE.md из шаблона ПЕРВЫМ делом |
| Не восстанавливаться после compaction без памяти | Re-read PIPELINE.md + STATE.md + activeContext.md + Graphiti |
| Не пропускать Graphiti queries | Graphiti is ALWAYS available — no 'if available' checks |

---

# BLOCKING RULES

## Plan Detected
Read guide: `cat .claude/guides/plan-execution-enforcer.md`

## After Code Changes
1. Write test → 2. Run test → 3. Fail? → fix → rerun → 4. Pass → continue

## Before Commit
1. Update `.claude/memory/activeContext.md` (Did/Decided/Learned/Next)
2. Stage activeContext.md
3. Then commit

## Before Spawning Teammate
Prompt MUST include:
- `## Required Skills` section (even if "No skills required")
- `## Acceptance Criteria`
- `## Constraints`
- `## Context from Typed Memory` — relevant excerpts from patterns.md, gotchas.md, codebase-map.json
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

## On Retry (Recovery Manager)
1. Read work/attempt-history.json for this subtask
2. Check circular fix detection (same approach 3+ times → STOP)
3. Inject previous attempt context into prompt
4. If 5+ retries → mark STUCK, escalate to human
5. Reference: `.claude/guides/recovery-manager.md`

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
| Error occurred | `cat .claude/guides/error-handling.md` |
| Complex decision | `cat .claude/guides/decision-making.md` |
| Plan for implementation | `cat .claude/guides/plan-execution-enforcer.md` |
| Spawning teammate | `cat .claude/guides/teammate-prompt-template.md` |
| Expert Panel | `cat .claude/guides/expert-panel-workflow.md` |
| External service needed | `cat .claude/skills/mcp-integration/SKILL.md` |
| Phase template needed | `cat .claude/shared/work-templates/phases/{PHASE}.md` |
| Quality gate check | `cat work/scalable-pipeline-design-gates.md` |
| Dependency analysis | `cat .claude/guides/dependency-analysis.md` |
| QA validation needed | `cat .claude/skills/qa-validation-loop/SKILL.md` + follow BLOCKING RULES "After IMPLEMENT" |
| Agent chain execution | `cat .claude/guides/agent-chains.md` |
| Typed memory needed | `cat .claude/guides/typed-memory.md` |
| Complexity assessment | `cat .claude/guides/complexity-assessment.md` |
| Recovery/retry needed | `cat .claude/guides/recovery-manager.md` |
| Graphiti memory setup | `cat .claude/guides/graphiti-integration.md` |
| Focused prompt needed | `cat .claude/guides/focused-prompts.md` |
| Agent type lookup | `cat .claude/agents/registry.md` |

---

# KNOWLEDGE LOCATIONS

| Need | Location |
|------|----------|
| Session context | `.claude/memory/activeContext.md` |
| Pipeline state | `work/PIPELINE.md` |
| Task state | `work/STATE.md` |
| Architecture decisions | `.claude/adr/decisions.md` |
| Pipeline templates | `.claude/shared/work-templates/` |
| Phase templates | `.claude/shared/work-templates/phases/` |

| Agent chains guide | `.claude/guides/agent-chains.md` |
| QA validation skill | `.claude/skills/qa-validation-loop/SKILL.md` |
| Pipeline v3 template | `.claude/shared/work-templates/PIPELINE-v3.md` |
| Agent type registry | `.claude/agents/registry.md` |
| Typed memory guide | `.claude/guides/typed-memory.md` |
| Complexity assessment | `.claude/guides/complexity-assessment.md` |
| Recovery manager | `.claude/guides/recovery-manager.md` |
| Graphiti integration | `.claude/guides/graphiti-integration.md` |
| Focused prompts | `.claude/guides/focused-prompts.md` |
| Codebase map | `.claude/memory/codebase-map.json` |
| Project patterns | `.claude/memory/patterns.md` |
| Project gotchas | `.claude/memory/gotchas.md` |
| Session insights | `.claude/memory/session-insights/` |
| Attempt history | `work/attempt-history.json` |
| Focused prompt files | `.claude/prompts/` |

---

# FORBIDDEN

- Starting work without reading memory/activeContext.md
- Finishing work without updating memory (activeContext.md + typed memory + Graphiti)
- Saying "done" without running tests
- Doing 3+ tasks sequentially when they can be parallelized
- `@.claude/skills` (loads everything, wastes context)
- Plan detected -> starting without plan-execution-protocol.md
- Ignoring <- CURRENT marker in PIPELINE.md after compaction
- Multi-phase task without creating work/PIPELINE.md first
- Compaction recovery without re-reading ALL state files (PIPELINE.md + STATE.md + activeContext.md)
- Skipping Graphiti queries at session start / after compaction / after task completion
- Skipping Phase Transition Protocol between pipeline phases
- Informal planning for complex tasks — use formal PIPELINE.md with phases and gates
