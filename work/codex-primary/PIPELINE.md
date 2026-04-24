# Pipeline: Codex Primary Implementer

- Status: PIPELINE_COMPLETE 2026-04-24
- Phase: DOCUMENT (final)
- Mode: INTERACTIVE
- Scope: LOCAL (this project only; NOT synced to new-project template or other bots until PoC passes)
- Started: 2026-04-24
- Feature branch: TBD (create at IMPLEMENT start)

> **Goal:** Integrate GPT-5.5 via Codex CLI as primary code implementer while preserving Agent Teams, skills, memory, and all Claude-centric infrastructure. Opus 4.7 stays planner + reviewer. Codex becomes executor for well-defined tasks. Level 2 (delegate) + Level 3 (dual-implement skill) built together.
>
> **Non-goals:** (a) Replace Claude for planning / UX / ambiguous work. (b) Sync to new-project template. (c) Propagate to other bot projects via fleet-sync. Those happen after PoC validates this approach.

---

## Phases

### Phase: PLAN
- Status: DONE (committed pipeline-checkpoint-PLAN)
- Mode: SOLO (Opus writes tech-spec + tasks)
- Attempts: 0 of 1
- On PASS: -> IMPLEMENT_WAVE_1
- On FAIL: -> STOP
- On BLOCKED: -> STOP
- Gate: work/codex-primary/tech-spec.md + tasks/T1..T8.md exist; user approves architecture
- Gate Type: USER_APPROVAL
- Inputs: this conversation, existing .claude/ infrastructure
- Outputs: work/codex-primary/tech-spec.md, work/codex-primary/tasks/T*.md, work/codex-primary/waves.md
- Checkpoint: pipeline-checkpoint-PLAN

### Phase: IMPLEMENT_WAVE_1
- Status: DONE (committed pipeline-checkpoint-IMPLEMENT_WAVE_1, 89 unit tests passing)
- Mode: AGENT_TEAMS
- Attempts: 0 of 2
- On PASS: -> IMPLEMENT_WAVE_2
- On FAIL: -> FIX
- On REWORK: -> PLAN
- On BLOCKED: -> STOP
- Gate: T1..T5 all mark status PASS in handoff; unit tests for codex-implement.py pass; scope-check script rejects out-of-fence diffs in synthetic test
- Gate Type: AUTO
- Inputs: tech-spec.md, tasks/T1..T5.md
- Outputs: .claude/scripts/codex-implement.py, codex-wave.py, codex-scope-check.py + phase-mode docs + task-codex-template.md + updated codex-gate.py
- Checkpoint: pipeline-checkpoint-IMPLEMENT_WAVE_1

### Phase: IMPLEMENT_WAVE_2
- Status: DONE (committed pipeline-checkpoint-IMPLEMENT_WAVE_2, skill + ADR + CLAUDE.md section)
- Mode: AGENT_TEAMS
- Attempts: 0 of 2
- On PASS: -> QA_REVIEW
- On FAIL: -> FIX
- On BLOCKED: -> STOP
- Gate: T6..T8 all mark status PASS; dual-implement skill has valid frontmatter + examples; ADR-012 follows template; CLAUDE.md updated at project-level only
- Gate Type: AUTO
- Inputs: tech-spec.md, tasks/T6..T8.md, outputs of IMPLEMENT_WAVE_1
- Outputs: .claude/skills/dual-implement/SKILL.md, .claude/adr/adr-012-codex-primary-implementer.md, updated project CLAUDE.md
- Checkpoint: pipeline-checkpoint-IMPLEMENT_WAVE_2

### Phase: QA_REVIEW
- Status: PENDING
- Mode: AGENT_TEAMS
- Attempts: 0 of 3
- On PASS: -> PROOF_OF_CONCEPT
- On FAIL: -> STOP
- On REWORK: -> FIX_WAVE
- On BLOCKED: -> STOP
- Gate: no CRITICAL or IMPORTANT issues in work/codex-primary/qa-review-report.md
- Gate Type: AUTO
- Inputs: all source changes from Waves 1 + 2, tech-spec.md acceptance criteria
- Outputs: work/codex-primary/qa-review-report.md, work/codex-primary/qa-issues.md
- Checkpoint: pipeline-checkpoint-QA_REVIEW

### Phase: FIX_WAVE
- Status: PENDING
- Mode: AGENT_TEAMS
- Attempts: 0 of 3
- On PASS: -> QA_REVIEW
- On BLOCKED: -> STOP
- Gate: all CRITICAL + IMPORTANT findings from qa-issues.md resolved
- Gate Type: AUTO
- Inputs: qa-issues.md
- Outputs: fixed source
- Checkpoint: pipeline-checkpoint-FIX_WAVE

### Phase: PROOF_OF_CONCEPT
- Status: PASS — gpt-5.5 via chatgpt provider validated; dual-2 real judge on two valid diffs (see poc-results.md + dual-2-judgment.md)
- Mode: SOLO
- Attempts: 0 of 2
- On PASS: -> DOCUMENT
- On FAIL: -> FIX_WAVE
- On BLOCKED: -> STOP
- Gate: (a) one real small task successfully executed by codex-implement.py end-to-end with tests passing; (b) dual-implement variant run on same task produces two diffs, Opus judges correctly; (c) scope fence never violated; (d) codex-gate allows subsequent Claude Edits
- Gate Type: USER_APPROVAL (user sees the PoC output and confirms quality)
- Inputs: everything built in waves 1+2
- Outputs: work/codex-primary/poc-results.md, commits in a test branch
- Checkpoint: pipeline-checkpoint-PROOF_OF_CONCEPT

### Phase: DOCUMENT  <- CURRENT (complete)
- Status: DONE — codex-integration.md + knowledge.md + activeContext.md + AGENTS.md + dual-2-judgment.md + speed_profile field all updated 2026-04-24
- Mode: SOLO
- Attempts: 0 of 1
- On PASS: -> COMPLETE
- On BLOCKED: -> STOP
- Gate: codex-integration.md updated, knowledge.md has new pattern entry, activeContext.md reflects DONE state, PIPELINE.md Status = PIPELINE_COMPLETE
- Gate Type: AUTO
- Inputs: poc-results.md, lessons learned during pipeline
- Outputs: updated .claude/guides/codex-integration.md, knowledge.md entries, activeContext.md
- Checkpoint: pipeline-checkpoint-DOCUMENT

---

## Decisions

<!-- Append-only. Record what was decided and why. -->

- [PLAN] Decision: Single Codex executor script + optional parallel wrapper, not N specialized executors. Reason: one contract (task-N.md) works for both Level 2 (single) and Level 3 (dual/parallel) — elegance via reuse.
- [PLAN] Decision: Add three phase modes (CODEX_IMPLEMENT, HYBRID_TEAMS, DUAL_IMPLEMENT) alongside existing (AGENT_TEAMS, AO_HYBRID, AO_FLEET). Reason: different execution strategies for different task profiles without breaking existing modes.
- [PLAN] Decision: task-N.md stays the single contract between Opus and Codex. Extend the existing template with Executor Hint, Scope Fence, Skill Contracts, Acceptance Criteria (IMMUTABLE). Reason: Evaluation Firewall + reuses task-decomposition skill output.
- [PLAN] Decision: Scope isolation — all changes in project's .claude/ only. new-project template and other bots left alone until PoC validates. Reason: user explicitly requested safe local validation before fleet-wide propagation.
- [PLAN] Decision: Codex sandbox stays read-only by default globally. Only codex-implement.py switches to workspace-write via explicit CLI flag, and only for scope-fenced directories. Reason: minimal blast radius, preserves existing advisor-only safety for codex-ask.py / parallel / watchdog.
- [PLAN] Decision: Agent Teams (TeamCreate) infrastructure stays completely intact. New "Codex teammate" is orthogonal: spawned via codex-wave.py, not TeamCreate. Opus orchestrates both kinds in HYBRID_TEAMS mode. Reason: preserve Claude's Skills + memory injection which make Agent Teams so effective.
- [PLAN] Decision: Every Claude teammate still calls codex-ask.py and cross-model-review skill for second opinion. These hooks are untouched. Reason: user requirement — "каждый агент может сейчас вызывать кодекс как second opinion, watchdog, и это нельзя терять".

---

## Execution Rules

(Same as PIPELINE-v3.md template. Copied execution rules apply here.)

---

## Scope Fence (for this pipeline's own changes)

Files this pipeline is allowed to create/modify:
- `.claude/scripts/codex-implement.py` (new)
- `.claude/scripts/codex-wave.py` (new)
- `.claude/scripts/codex-scope-check.py` (new)
- `.claude/shared/work-templates/phases/IMPLEMENT-CODEX.md` (new)
- `.claude/shared/work-templates/phases/IMPLEMENT-HYBRID.md` (new)
- `.claude/shared/work-templates/phases/DUAL-IMPLEMENT.md` (new)
- `.claude/shared/work-templates/task-codex-template.md` (new)
- `.claude/skills/dual-implement/SKILL.md` (new)
- `.claude/adr/adr-012-codex-primary-implementer.md` (new)
- `.claude/hooks/codex-gate.py` (modify — recognize codex-implement result as valid opinion)
- `CLAUDE.md` (project-level, not global ~/.claude/CLAUDE.md — add new section)
- `.claude/guides/codex-integration.md` (modify — add "Codex as Primary Implementer" section)
- `.claude/memory/knowledge.md` (append)
- `.claude/memory/activeContext.md` (update)
- `work/codex-primary/**` (pipeline artifacts)

Files this pipeline MUST NOT modify:
- `.claude/shared/templates/new-project/**` (template for future projects — sync only after PoC)
- `~/.claude/CLAUDE.md` (global — don't propagate until validated)
- `~/.codex/config.toml` (already updated model + reasoning; no more global changes)
- Any other bot project
- Existing advisor hooks not listed above (codex-ask, codex-parallel, codex-watchdog, codex-broker, codex-review, codex-stop-opinion)

---

## Results Board

See `work/codex-primary/results-board.md` (created at IMPLEMENT_WAVE_1 start).
