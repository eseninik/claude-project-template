# Pipeline: {PIPELINE_NAME}

- Status: NOT_STARTED
- Phase: SPEC
- Mode: INTERACTIVE

> v3.2: Added NYQUIST_CHECK phase, formalized checkpoint types (human-verify/decision/human-action), decimal phase numbering.
> v3.1: Added SKEPTIC_CHECK phase and quality/adequacy validator split in QA_REVIEW.
> v3: Added QA_REVIEW phase (reviewer+fixer agent chain) between IMPLEMENT and TEST.
> Supports agent chains (sequential multi-agent loops) and higher parallelism (5-10 agents).
> Delete unused phases. Mandatory phases (Mandatory: true) cannot be deleted — skip them via Skip-if conditions instead. Reorder by editing `On PASS/FAIL/REWORK` transitions.
> After compaction: find `<- CURRENT`, read that phase, continue.
> Phase Transition Protocol between phases preserves knowledge via typed memory + Graphiti.

---

## Phases

### Phase: AUTO_RESEARCH  <- CURRENT
- Status: PENDING
- Mandatory: true
- Mode: AGENT_TEAMS
- Attempts: 0 of 1
- On PASS: -> SPEC
- On FAIL: -> STOP
- On BLOCKED: -> STOP
- Gate: auto-research.md exists with GO decision, no unresolved blockers
- Gate Type: AUTO
- Inputs: user request (conversation)
- Outputs: work/{feature}/auto-research.md
- Checkpoint: pipeline-checkpoint-AUTO_RESEARCH
- Skip-if: single-file change, bug fix, docs-only, config change

### Phase: SPEC
- Status: PENDING
- Mode: SOLO
- Attempts: 0 of 1
- On PASS: -> REVIEW
- On FAIL: -> STOP
- On BLOCKED: -> STOP
- Gate: user-spec.md exists with acceptance criteria
- Gate Type: USER_APPROVAL
- Inputs: user request (conversation), work/{feature}/auto-research.md
- Outputs: work/{feature}/user-spec.md
- Checkpoint: pipeline-checkpoint-SPEC

### Phase: REVIEW
- Status: PENDING
- Mode: AGENT_TEAMS
- Attempts: 0 of 1
- On PASS: -> PLAN
- On FAIL: -> SPEC
- On REWORK: -> SPEC
- On BLOCKED: -> STOP
- Gate: expert-analysis.md has no unresolved open questions
- Gate Type: HYBRID
- Inputs: work/{feature}/user-spec.md
- Outputs: work/expert-analysis.md
- Checkpoint: pipeline-checkpoint-REVIEW

### Phase: PLAN
- Status: PENDING
- Mode: SOLO
- Attempts: 0 of 1
- On PASS: -> SKEPTIC_CHECK
- On FAIL: -> STOP
- On REWORK: -> REVIEW
- On BLOCKED: -> STOP
- Gate: tech-spec.md + tasks/*.md exist, wave analysis done
- Gate Type: USER_APPROVAL
- Inputs: work/expert-analysis.md, work/{feature}/user-spec.md
- Outputs: work/{feature}/tech-spec.md, tasks/*.md, tasks/waves.md
- Checkpoint: pipeline-checkpoint-PLAN

### Phase: SKEPTIC_CHECK
- Status: PENDING
- Mode: SOLO
- Attempts: 0 of 1
- On PASS: -> NYQUIST_CHECK
- On FAIL: -> PLAN
- On BLOCKED: -> STOP
- Gate: skeptic report has zero critical findings
- Gate Type: AUTO
- Inputs: work/{feature}/tech-spec.md, work/{feature}/tasks/*.md
- Outputs: work/{feature}/logs/skeptic-report.json
- Checkpoint: pipeline-checkpoint-SKEPTIC_CHECK

### Phase: NYQUIST_CHECK
- Status: PENDING
- Mode: SOLO
- Attempts: 0 of 1
- On PASS: -> IMPLEMENT
- On FAIL: -> PLAN
- On BLOCKED: -> STOP
- Gate: all requirements mapped to planned tests, 0 MISSING in nyquist-map.md
- Gate Type: AUTO
- Inputs: work/{feature}/tasks/*.md, acceptance criteria
- Outputs: work/{feature}/nyquist-map.md
- Checkpoint: pipeline-checkpoint-NYQUIST_CHECK

### Phase: IMPLEMENT
- Status: PENDING
- Mode: AGENT_TEAMS
- Attempts: 0 of 2
- On PASS: -> FRESH_VERIFY
- On FAIL: -> FIX
- On REWORK: -> PLAN
- On BLOCKED: -> STOP
- Gate: all task acceptance criteria met, code compiles, lint clean
- Gate Type: AUTO
- Inputs: tasks/*.md, work/{feature}/tech-spec.md
- Outputs: source code, test files
- Checkpoint: pipeline-checkpoint-IMPLEMENT

### Phase: FRESH_VERIFY
- Status: PENDING
- Mandatory: true
- Mode: AO_HYBRID
- Attempts: 0 of 2
- On PASS: -> QA_REVIEW
- On FAIL: -> FIX
- On BLOCKED: -> STOP
- Gate: fresh-verify-report.md exists with 0 CRITICAL findings
- Gate Type: AUTO
- Inputs: code changes from IMPLEMENT, acceptance criteria
- Outputs: work/{feature}/fresh-verify-report.md
- Checkpoint: pipeline-checkpoint-FRESH_VERIFY

### Phase: QA_REVIEW
- Status: PENDING
- Mode: AGENT_TEAMS
- Attempts: 0 of 3
- On PASS: -> TEST
- On FAIL: -> STOP
- On REWORK: -> FIX
- On BLOCKED: -> STOP
- Gate: no CRITICAL or IMPORTANT issues remaining in qa-review-report.md
- Gate Type: AUTO
> QA_REVIEW uses two validator types in sequence:
> 1. quality-validator: checks document structure, completeness, criteria testability
> 2. adequacy-validator: checks feasibility, sizing, over/underengineering
> Both are read-only agents from the Validation Agents registry section.
> Chain: quality-validator -> fix issues -> adequacy-validator -> fix issues -> re-review
- Inputs: source code from IMPLEMENT, acceptance criteria, .claude/skills/qa-validation-loop/SKILL.md
- Outputs: work/qa-issues.md, work/qa-review-report.md
- Checkpoint: pipeline-checkpoint-QA_REVIEW

### Phase: TEST
- Status: PENDING
- Mode: SOLO
- Attempts: 0 of 1
- On PASS: -> SKILL_EVOLUTION
- On FAIL: -> FIX
- On BLOCKED: -> STOP
- Gate: all tests pass (`uv run pytest`), no type errors
- Gate Type: AUTO
- Inputs: source code, test files
- Outputs: work/test-results.md
- Checkpoint: pipeline-checkpoint-TEST

### Phase: SKILL_EVOLUTION
- Status: PENDING
- Mandatory: true
- Mode: SOLO
- Attempts: 0 of 1
- On PASS: -> DEPLOY
- On FAIL: -> DEPLOY
- On BLOCKED: -> DEPLOY
- Gate: evolution proposed for used skills OR "no learnings" logged in pipeline decisions
- Gate Type: AUTO
- Inputs: list of skills used during pipeline, execution outcomes
- Outputs: skill evolution deltas (if any), updated examples.md entries
- Checkpoint: pipeline-checkpoint-SKILL_EVOLUTION

### Phase: FIX
- Status: PENDING
- Mode: AGENT_TEAMS
- Attempts: 0 of 3
- On PASS: -> TEST
- On BLOCKED: -> STOP
- Gate: previously failing tests now pass
- Gate Type: AUTO
- Inputs: work/test-results.md, failing test output
- Outputs: fixed source code
- Checkpoint: pipeline-checkpoint-FIX

### Phase: DEPLOY
- Status: PENDING
- Mode: SOLO
- Attempts: 0 of 2
- On PASS: -> STRESS_TEST
- On FAIL: -> FIX
- On BLOCKED: -> STOP
- Gate: service running, health check returns 200
- Gate Type: AUTO
- Inputs: source code, deploy config
- Outputs: deployment log
- Checkpoint: pipeline-checkpoint-DEPLOY

### Phase: STRESS_TEST
- Status: PENDING
- Mode: SOLO
- Attempts: 0 of 1
- On PASS: -> COMPLETE
- On FAIL: -> FIX
- On BLOCKED: -> STOP
- Gate: p95 < 500ms, error rate < 1%
- Gate Type: AUTO
- Inputs: deployed service URL
- Outputs: work/performance-report.md
- Checkpoint: pipeline-checkpoint-STRESS_TEST

> To use a sub-pipeline, set Mode and add Pipeline field:
> ```
> ### Phase: DEVELOPMENT
> - Mode: SUB_PIPELINE
> - Pipeline: work/development/PIPELINE.md
> - On PASS: -> TEST
> - On BLOCKED: -> STOP
> ```

> To add an experiment phase for optimization tasks:
> ```
> ### Phase: EXPERIMENT
> - Status: PENDING
> - Mode: SOLO
> - Attempts: 0 of 1
> - On PASS: -> IMPLEMENT
> - On FAIL: -> PLAN
> - On BLOCKED: -> STOP
> - Gate: best metric meets threshold OR budget exhausted
> - Gate Type: AUTO
> - Inputs: baseline metric, experiment scope
> - Outputs: work/{feature}/experiment-log.md, experiment-state.md
> ```
> Use for tasks with quantifiable metrics that need iterative optimization.
> Skill: `.claude/skills/experiment-loop/SKILL.md`

> To use AO fleet mode (multi-project parallel execution via Agent Orchestrator):
> ```
> ### Phase: FLEET_SYNC
> - Mode: AO_FLEET
> - Projects: call-rate-bot, clients-legal-bot, conference-bot, ...
> - On PASS: -> VERIFY
> - On BLOCKED: -> STOP
> - Gate: all sessions completed, no errors
> - Gate Type: AUTO
> ```
> AO_FLEET spawns separate Claude Code sessions per project via `ao spawn`.
> Use for fleet-wide operations across multiple repos (sync, deploy, migrate).
> Skill: `cat .claude/skills/ao-fleet-spawn/SKILL.md`

> To use AO Hybrid mode (single-project, full-context parallel agents):
> ```
> ### Phase: IMPLEMENT
> - Mode: AO_HYBRID
> - On PASS: -> QA_REVIEW
> - On BLOCKED: -> STOP
> - Gate: all agents completed, handoffs report PASS
> - Gate Type: AUTO
> ```
> AO_HYBRID spawns full Claude Code sessions via `ao spawn` within the same project.
> Each agent gets its own worktree, CLAUDE.md, skills, and memory.
> Use for single-project parallelism that needs full agent context.
> Skill: `cat .claude/skills/ao-hybrid-spawn/SKILL.md`

> To add per-phase fresh verification (recommended for IMPLEMENT phases):
> ```
> ### Phase: PHASE_VERIFY_{N}
> - Status: PENDING
> - Mode: AO_HYBRID
> - Attempts: 0 of 2
> - On PASS: -> {NEXT_PHASE}
> - On FAIL: -> FIX
> - On BLOCKED: -> STOP
> - Gate: verification report has 0 CRITICAL findings
> - Gate Type: AUTO
> - Inputs: code changes from Phase {N}, acceptance criteria
> - Outputs: work/{feature}/phase-verify-{N}.md
> ```
> Fresh session verification spawns a NEW Claude Code session via AO Hybrid.
> The fresh session sees ONLY: changed files + tests + acceptance criteria.
> It does NOT see implementation history — providing "fresh eyes" review.
> Pattern: implement → fresh-verify → fix → re-verify → next phase.
> For final verification after ALL phases: spawn comprehensive fresh session
> with 2-3 sub-agents (code quality, security, integration).

> To insert urgent/gap-closure work between existing phases, use decimal numbering:
> ```
> ### Phase: 3.1 (Gap Closure)
> - Status: PENDING
> - Mode: AGENT_TEAMS
> - Inserted: after verification gaps in Phase 3
> - On PASS: -> Phase 4
> - On FAIL: -> STOP
> - Gate: all gaps from VERIFICATION.md closed
> ```
> Decimal phases (3.1, 3.2) insert between integer phases without renumbering.
> Execution order: 1 -> 2 -> 2.1 -> 3 -> 3.1 -> 3.2 -> 4
> Use when: verification found gaps, UAT failed, urgent work needed between phases.

---

## Decisions

<!-- Append-only. Record what was decided and why. -->
<!-- Format: - [PHASE] Decision: {what}. Reason: {why}. -->

---

## Execution Rules

1. **Start of session / after compaction:** Re-read this file. Find `<- CURRENT`. Resume from that phase.
2. **Phase execution:** Read phase Inputs. Execute. Produce Outputs. Run Gate check.
3. **Gate verdicts:** PASS (advance), CONCERNS (log + advance), REWORK (go to On REWORK, increment Attempts), FAIL (go to On FAIL or STOP).
4. **Attempts overflow:** When Attempts X >= max Y, set Status: BLOCKED, stop pipeline.
5. **Agent Teams:** If Mode = AGENT_TEAMS, use TeamCreate. Build prompts with Required Skills section. Scale to 5-10 agents for large wave groups.
6. **Agent Chains:** For sequential multi-agent workflows (e.g., QA_REVIEW: reviewer -> fixer -> re-reviewer), run agents in sequence within the phase, looping up to the Max Attempts limit.
6b. **Checkpoint Types:** Tasks can contain typed checkpoints:
    - `checkpoint:human-verify` (90%): Claude automated work, user visually confirms. Auto-approve in YOLO/auto mode.
    - `checkpoint:decision` (9%): User chooses between options with pros/cons. Auto-select first option in auto mode.
    - `checkpoint:human-action` (1%): Truly manual action (2FA, OAuth). ALWAYS pauses, even in auto mode.
    When checkpoint reached mid-phase: save state to work/{feature}/checkpoint-state.md, pause, wait for user input.
7. **Sub-pipeline:** If Mode = SUB_PIPELINE, execute referenced Pipeline file to completion, then return.
8. **AO Fleet:** If Mode = AO_FLEET, use `ao spawn` per project listed in Projects field. Monitor via `ao session ls`. Collect results from each project's work/ directory. Kill sessions after completion. Skill: `cat .claude/skills/ao-fleet-spawn/SKILL.md`.
8b. **AO Hybrid:** If Mode = AO_HYBRID, use `ao spawn --prompt-file` per task. Each spawned session is a full Claude Code process with own context. Monitor via `ao-hybrid.sh wait`. Collect results from worktree paths. Merge worktree branches sequentially. Skill: `cat .claude/skills/ao-hybrid-spawn/SKILL.md`.
9. **After each phase:** Update this file (move `<- CURRENT`, set Status: DONE). Update work/STATE.md. Update memory. Git commit with checkpoint tag.
9b. **Phase Transition Protocol:** Between phases, execute: (1) git commit + checkpoint tag, (1b) if phase was IMPLEMENT: spawn fresh AO Hybrid verification session — fresh session prompt: "You are a fresh verification agent. You have NOT seen the implementation. Read ONLY the changed files, tests, and acceptance criteria. Verify everything works. Report: CRITICAL / IMPORTANT / MINOR findings." If CRITICAL findings: fix before advancing, (2) quick insight extraction — what worked/failed/learned, (3) update typed memory (knowledge.md), (4) save to Graphiti (add_memory), (5) re-read PIPELINE.md + STATE.md + typed memory, (6) advance <- CURRENT.
10. **Nyquist validation:** If NYQUIST_CHECK phase exists, ALL requirements from task files must have planned test coverage before IMPLEMENT begins. Gap analysis produces nyquist-map.md.
11. **Pipeline complete:** When last phase passes, set top-level Status: PIPELINE_COMPLETE.
12. **Mandatory phases:** Phases with `Mandatory: true` CANNOT be deleted when creating a pipeline from this template. They can be set to Skip-if conditions, but the phase definition must remain. If skip conditions are met, set Status: SKIPPED and advance to next phase.
