# Pipeline: {PIPELINE_NAME}

- Status: NOT_STARTED
- Phase: SPEC
- Mode: INTERACTIVE

> Delete unused phases. Reorder by editing `On PASS/FAIL/REWORK` transitions.
> After compaction: find `<- CURRENT`, read that phase, continue.

---

## Phases

### Phase: SPEC  <- CURRENT
- Status: PENDING
- Mode: SOLO
- Attempts: 0 of 1
- On PASS: -> REVIEW
- On FAIL: -> STOP
- On BLOCKED: -> STOP
- Gate: user-spec.md exists with acceptance criteria
- Gate Type: USER_APPROVAL
- Inputs: user request (conversation)
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
- On PASS: -> IMPLEMENT
- On FAIL: -> STOP
- On REWORK: -> REVIEW
- On BLOCKED: -> STOP
- Gate: tech-spec.md + tasks/*.md exist, wave analysis done
- Gate Type: USER_APPROVAL
- Inputs: work/expert-analysis.md, work/{feature}/user-spec.md
- Outputs: work/{feature}/tech-spec.md, tasks/*.md, tasks/waves.md
- Checkpoint: pipeline-checkpoint-PLAN

### Phase: IMPLEMENT
- Status: PENDING
- Mode: AGENT_TEAMS
- Attempts: 0 of 2
- On PASS: -> TEST
- On FAIL: -> FIX
- On REWORK: -> PLAN
- On BLOCKED: -> STOP
- Gate: all task acceptance criteria met, code compiles, lint clean
- Gate Type: AUTO
- Inputs: tasks/*.md, work/{feature}/tech-spec.md
- Outputs: source code, test files
- Checkpoint: pipeline-checkpoint-IMPLEMENT

### Phase: TEST
- Status: PENDING
- Mode: SOLO
- Attempts: 0 of 1
- On PASS: -> DEPLOY
- On FAIL: -> FIX
- On BLOCKED: -> STOP
- Gate: all tests pass (`uv run pytest`), no type errors
- Gate Type: AUTO
- Inputs: source code, test files
- Outputs: work/test-results.md
- Checkpoint: pipeline-checkpoint-TEST

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
5. **Agent Teams:** If Mode = AGENT_TEAMS, use TeamCreate. Build prompts with Required Skills section.
6. **Sub-pipeline:** If Mode = SUB_PIPELINE, execute referenced Pipeline file to completion, then return.
7. **After each phase:** Update this file (move `<- CURRENT`, set Status: DONE). Update work/STATE.md. Update memory. Git commit with checkpoint tag.
8. **Pipeline complete:** When last phase passes, set top-level Status: PIPELINE_COMPLETE.
