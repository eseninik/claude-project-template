# Pipeline: Watchdog Дnushnost Fix

- Status: IN_PROGRESS
- Phase: SPEC
- Mode: INTERACTIVE

> Targeted bug-fix pipeline. Skip MRD/AUTO_RESEARCH/REVIEW — problem is well-scoped (watchdog over-blocks, user reported 10+ iteration loops, Codex itself flagged over-blocking in latest.json, live FP captured in session).
> Layers implemented: L1 severity triage, L2 state memory, L3 task-class detection, L5 slash commands. L4 (gate consolidation) deferred to follow-up.

---

## Phases

### Phase: SPEC  <- CURRENT
- Status: PENDING
- Mandatory: true
- Mode: SOLO
- Gate: `spec.md` complete with severity taxonomy, state schema, task-class rules, AC1..ACn
- Inputs: user request + session evidence (watchdog FP log)
- Outputs: `work/watchdog-fix/spec.md`
- Checkpoint: pipeline-checkpoint-SPEC

### Phase: IMPL_L1_L2
- Status: PENDING
- Mode: SOLO
- On PASS: -> IMPL_L3
- Gate: codex-watchdog.py refactored; severity enum returned by Codex; state file dedup; unit-level smoke from CLI works
- Inputs: spec.md
- Outputs: `.claude/hooks/codex-watchdog.py`, `.codex/watchdog-state.json` schema
- Checkpoint: pipeline-checkpoint-IMPL_L1_L2

### Phase: IMPL_L3
- Status: PENDING
- Mode: SOLO
- On PASS: -> IMPL_L5
- Gate: `session-task-class.py` hook classifies; env `CLAUDE_TASK_CLASS` set; watchdog/gate read it
- Inputs: spec.md (task-class rules table)
- Outputs: `.claude/hooks/session-task-class.py`, modified `codex-watchdog.py`, `codex-gate.py`, `settings.json`
- Checkpoint: pipeline-checkpoint-IMPL_L3

### Phase: IMPL_L5
- Status: PENDING
- Mode: SOLO
- On PASS: -> TESTS
- Gate: `/watchdog` slash-command present with strict|normal|off|status subcommands
- Outputs: `.claude/commands/watchdog.md`, state file support
- Checkpoint: pipeline-checkpoint-IMPL_L5

### Phase: TESTS
- Status: PENDING
- Mode: SOLO
- On PASS: -> SYNC
- Gate: all unit tests pass; FP replay suite passes (the 1 captured FP from today MUST not trigger HALT under `chat` task-class)
- Outputs: `.claude/hooks/test_watchdog_fix.py`, `work/watchdog-fix/fp-replay-log.md`
- Checkpoint: pipeline-checkpoint-TESTS

### Phase: SYNC
- Status: PENDING
- Mode: SOLO
- On PASS: -> VERIFY
- Gate: new-project template mirrors all changed/new files
- Outputs: `.claude/shared/templates/new-project/.claude/**` updated
- Checkpoint: pipeline-checkpoint-SYNC

### Phase: VERIFY
- Status: PENDING
- Mandatory: true
- Mode: SOLO
- On PASS: -> COMPLETE
- Gate: AC1..ACn all verified with evidence; activeContext + daily log updated
- Outputs: `work/watchdog-fix/verification.md`
- Checkpoint: pipeline-checkpoint-VERIFY

### Phase: COMPLETE
- Status: PENDING
- Gate: Status = PIPELINE_COMPLETE; branch ready for merge

---

## Acceptance Criteria (frozen in SPEC phase, immutable per Evaluation Firewall)

See `work/watchdog-fix/spec.md` section "Acceptance Criteria". 7 criteria (AC1-AC7).

---

## Execution Log

- 2026-04-23 09:30 — Pipeline created, SPEC phase started.
