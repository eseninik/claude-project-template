# Summary instructions

When compacting, ALWAYS preserve these rules (they are lost most often):
- **AGENT TEAMS**: 3+ independent tasks -> ALWAYS use TeamCreate, not sequential execution
- **PIPELINE**: Read work/PIPELINE.md after compaction, continue from <- CURRENT marker
- **MEMORY**: ALWAYS update activeContext.md + daily log before commit/exit
- **AGENT MEMORY**: NEVER write Agent prompts by hand. ALWAYS use spawn-agent.py → auto-injects agent memory + skills + type detection
- **SKILLS**: Before task matching skill trigger -> invoke Skill tool. Before spawning teammate -> `python .claude/scripts/spawn-agent.py --task "..." --team X --name Y`
- **ELEGANCE**: After IMPLEMENT, before QA: ask "Is there a simpler way?" If yes and non-trivial → reimplement first
- **VERIFICATION**: NEVER say "done" without running tests
- **QA GATE**: After IMPLEMENT -> `cat .claude/skills/qa-validation-loop/SKILL.md` before TEST
- **KNOWLEDGE**: Read .claude/memory/knowledge.md at session start (patterns + gotchas)
- **GRAPHITI**: Query Graphiti at session start and after compaction for semantic context
- **PIPELINE MANDATORY**: Multi-phase tasks MUST create work/PIPELINE.md BEFORE implementation
- **MEMORY DECAY**: knowledge.md entries have verified: dates. Use `knowledge-touch` to refresh used patterns. Details: `py -3 .claude/scripts/memory-engine.py --help`
- **NYQUIST**: Before IMPLEMENT, map requirements to planned tests. 0 MISSING → proceed. Gaps → fix plan first
- **GOAL-BACKWARD**: Before claiming "done", verify GOAL achievement. Check: Exists → Substantive → Wired
- **LOGGING**: Every new/modified function MUST have structured logging (cat .claude/guides/logging-standards.md)
- **FRESH VERIFY**: After IMPLEMENT in pipeline → spawn fresh AO session for verification
- **AUTO-RESEARCH**: Pipeline auto-spawns 3 research agents before PLAN (mandatory phase, cannot be deleted)
- **SKILL EVOLUTION**: After pipeline completes → propose skill improvements → Skill Conductor validates → apply
- **DISCUSS-PHASE**: Before PLAN, if requirements have gray areas → discuss-phase → CONTEXT.md
After compaction: THE COMPACTION SUMMARY IS A HINT, NOT TRUTH. Re-read work/PIPELINE.md + .claude/memory/activeContext.md + .claude/memory/knowledge.md IMMEDIATELY. If PIPELINE.md has <- CURRENT marker: resume from that phase. DO NOT proceed without re-reading these files.

---

# Project: Claude Project Template Update

> Template upgrade automation with AI-First methodology integration

**Memory:** `.claude/memory/activeContext.md` | **ADR:** `.claude/adr/` | **Branch:** `dev`

---

# AUTONOMOUS PIPELINE PROTOCOL

> The #1 priority: parallelize work via Agent Teams and survive compaction.

## Agent Teams (ALWAYS for 3+ parallel subtasks within a phase)

TRIGGER: 3+ independent parallel subtasks within a phase (different files/modules).
ACTION: TeamCreate → TaskCreate → build prompts via `.claude/guides/teammate-prompt-template.md`.
- EVERY prompt MUST have `## Required Skills` section
- EVERY implementer gets verification-before-completion
- Read work/results-board.md before starting — agents learn from peers
- DO NOT do sequentially what can be parallelized
- After compaction: check work/PIPELINE.md Mode field for AGENT_TEAMS

## AO Hybrid (full-context single-project agents)

TRIGGER: `execution_engine=ao_hybrid` or Phase Mode = AO_HYBRID. Skill: `cat .claude/skills/ao-hybrid-spawn/SKILL.md`

## AO Fleet (multi-project parallel execution)

TRIGGER: Phase Mode = AO_FLEET or cross-project task. Skill: `cat .claude/skills/ao-fleet-spawn/SKILL.md`

## Phase Transition Protocol (between pipeline phases)

After completing any phase, BEFORE starting the next:
1. Git commit with checkpoint tag (`pipeline-checkpoint-{PHASE}`)
2. If IMPLEMENT phase: spawn fresh AO Hybrid verification. If CRITICAL findings -> fix -> re-verify (loop until 0 CRITICAL, max 3 cycles)
3. Update knowledge.md + daily log + Graphiti
4. Re-read PIPELINE.md + activeContext.md + knowledge.md
5. Agents output `=== PHASE HANDOFF ===` block, advance <- CURRENT marker

## After Compaction (ALWAYS — NO EXCEPTIONS)

THE COMPACTION SUMMARY IS A HINT, NOT TRUTH.
1. Re-read work/PIPELINE.md — find <- CURRENT phase
2. Re-read .claude/memory/activeContext.md + knowledge.md
3. Query Graphiti: search_memory_facts(query=<current task>, max_facts=10)
4. Check phase Mode: AGENT_TEAMS → create team; AO_HYBRID → cat skill; AO_FLEET → cat skill
5. Continue from <- CURRENT. DO NOT restart from beginning.

## Pipeline State Machine (BLOCKING — work/PIPELINE.md)

BLOCKING: Any task with 2+ phases MUST create work/PIPELINE.md BEFORE implementation.
TRIGGER: implement/build/refactor/migrate/fleet tasks, or 3+ steps, or 5+ files, or architectural changes.
ACTION:
1. Read `.claude/guides/autonomous-pipeline.md`
2. Create work/PIPELINE.md from `.claude/shared/work-templates/PIPELINE-v3.md`
3. Mark first phase <- CURRENT, execute phase by phase with gates
4. After each phase: verify → update PIPELINE.md → git commit
5. DO NOT do informal planning — use formal phases with gates

## Expert Panel (explicit trigger)

TRIGGER: "Agent Teams Mode" OR "экспертная панель"
GUIDE: `cat .claude/guides/expert-panel-workflow.md` | SKILL: expert-panel
BLOCKING: No implementation without work/expert-analysis.md

---

# AUTO-BEHAVIORS

## Session Start (MANDATORY)
1. IF work/tasks/lessons.md exists → read top 5 lessons
2. IF work/PIPELINE.md exists with <- CURRENT → resume pipeline
3. Query Graphiti: search_memory_facts(query=<current task>, max_facts=5)

## Before Code Changes
1. Check .claude/adr/decisions.md | 2. Read activeContext.md

## After Task Completion (MANDATORY)
1. Update activeContext.md (Did/Decided/Learned/Next) — BLOCKING
2. Update daily/{YYYY-MM-DD}.md — BLOCKING
3. If learned something new → update knowledge.md + Graphiti

## On Architecture Decision
Check .claude/adr/decisions.md → if contradicts, explain → create ADR from .claude/adr/_template.md

---

# TEAM ROLE SKILLS MAPPING

| Role | Agent Type | Skills |
|------|-----------|--------|
| Developer | coder | verification-before-completion |
| Complex Implementer | coder-complex | verification-before-completion |
| Planner | planner | task-decomposition |
| QA Reviewer | qa-reviewer | qa-validation-loop, verification-before-completion |
| Researcher | spec-researcher | codebase-mapping |
| Debugger | analyzer/fixer | systematic-debugging |
| Pipeline Lead | pipeline-lead | subagent-driven-development, skill-evolution |
| Experimenter | experimenter | experiment-loop, skill-evolution, verification-before-completion |

Full list (21 types): `cat .claude/agents/registry.md`

**One-liner rules:** TDD for new code. Validate inputs. Never commit secrets. pytest + AsyncMock. Clean Architecture. uv for packages. Always Opus 4.6. Structured logging in all new code.

---

# HARD CONSTRAINTS

| Constraint | Instead Do |
|------------|-----------|
| Не удалять данные без подтверждения | Спроси пользователя |
| Не коммитить секреты | .env + .gitignore |
| Не пушить в main | dev или feature branch |
| Не говорить "готово" без verification | verification-before-completion |
| Не переходить к QA без элегантности | После IMPLEMENT: "Есть ли способ проще?" |
| Не делать всё самому при 3+ задачах | Agent Teams (TeamCreate) |
| Не коммитить без памяти | activeContext.md + daily log перед commit |
| Не спавнить без Required Skills | Проверь TEAM ROLE SKILLS MAPPING |
| Expert Panel без expert-analysis.md | Дождись результатов панели |
| Не пропускать QA после IMPLEMENT | qa-validation-loop перед TEST |
| Без PIPELINE.md для multi-phase | Создай из шаблона ПЕРВЫМ делом |
| Compaction без памяти | Re-read PIPELINE.md + activeContext.md + knowledge.md |
| Без Graphiti | Graphiti ALWAYS available — no 'if available' |
| Без Nyquist (если фаза есть) | Map requirements → tests в nyquist-map.md |
| Без обсуждения серых зон | discuss-phase → CONTEXT.md |
| Quick Mode для 5+ файлов | Полный pipeline |
| Менять тесты чтобы прошли | Evaluation Firewall: тесты иммутабельны после утверждения |
| Код без логирования | structured logging (cat .claude/guides/logging-standards.md) |

---

# BLOCKING RULES

## Plan Detected
Read guide: `cat .claude/guides/plan-execution-enforcer.md`

## After Code Changes
Write test → Run test → Fail? → fix → rerun → Pass → continue

## Before Commit
1. Update activeContext.md (Did/Decided/Learned/Next) | 2. Update daily log | 3. Stage both, commit

## Before Spawning Teammate (MANDATORY — no exceptions)
NEVER write Agent tool prompts by hand. ALWAYS use spawn-agent.py:
1. Run: `python .claude/scripts/spawn-agent.py --task "<desc>" --team <team> --name <name> -o work/prompts/<name>.md`
2. Read the generated prompt: `cat work/prompts/<name>.md`
3. Pass the generated prompt to Agent tool
spawn-agent.py auto-injects: agent type detection → matching skills → agent memory → handoff template.
Hand-written prompts skip agent memory injection = broken feature.

## Before "done" (Verification Gate)
1. Run tests (`uv run pytest` / `npm test`) | 2. Type check (`mypy` / `tsc`)
3. Verify EACH acceptance criterion with evidence | 4. Update activeContext.md
5. If ANY fails → fix → re-run → NOT done | 6. Skipped verification = REWORK

## Nyquist Gate (before IMPLEMENT, if phase exists)
Map requirements → tests → gap analysis. MISSING > 0 → fix plan. Output: `work/{feature}/nyquist-map.md`

## Discuss-Phase (before PLAN, if gray areas)
Analyze ambiguity → discuss-phase workflow → capture in `work/{feature}/CONTEXT.md`

## QA Gate (after IMPLEMENT)
Spawn Reviewer → if CRITICAL issues → Fixer → re-review (max 3 cycles). Same issue 3+ times → BLOCKED, ask human.

## Recovery
Same approach 3+ times → STOP. 5+ retries → STUCK, escalate. Always try fundamentally different approach.

## Debugging
Read error → 2-3 hypotheses → test most likely → fix root cause → verify + regressions. 3+ failures → change approach.

---

# REFERENCES

| What | Where |
|------|-------|
| Context loading triggers (guides + skills) | `cat .claude/guides/context-triggers.md` |
| Knowledge locations (all file paths) | `cat .claude/guides/knowledge-map.md` |
| Memory decay tiers + engine commands | `py -3 .claude/scripts/memory-engine.py --help` |
| Memory search modes | heartbeat(2K)/normal(5K)/deep(15K)/creative(3K) — see memory-engine.py |
| Refresh used pattern | `py -3 .claude/scripts/memory-engine.py knowledge-touch "Name" .claude/memory/` |

---

# FORBIDDEN

- Starting work without reading activeContext.md + knowledge.md
- Finishing work without updating activeContext.md + daily log
- Saying "done" without running tests
- Doing 3+ tasks sequentially when they can be parallelized
- `@.claude/skills` (loads everything, wastes context)
- Plan detected → starting without plan-execution-protocol.md
- Ignoring <- CURRENT marker in PIPELINE.md after compaction
- Multi-phase task without creating work/PIPELINE.md first
- Compaction recovery without re-reading files (THE SUMMARY IS A HINT, NOT TRUTH)
- Skipping Phase Transition Protocol between pipeline phases
- Informal planning for complex tasks — use formal PIPELINE.md with phases and gates
- Writing new code without structured logging (entry/exit/error logs)
