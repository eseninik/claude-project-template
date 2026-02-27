# Pipeline: spawn-agent.py + Full Flow Automation

- Status: PIPELINE_COMPLETE
- Phase: SYNC
- Mode: INTERACTIVE

> Build spawn-agent.py with auto-type detection. Iterate until full flow is automatic.

---

## Phases

### Phase: IMPLEMENT
- Status: PASS
- Mode: AGENT_TEAMS
- Attempts: 0 of 1
- On PASS: -> TEST
- On FAIL: -> STOP
- Gate: spawn-agent.py works, CLAUDE.md updated, template synced
- Gate Type: AUTO
- Inputs: generate-prompt.py, registry.md, teammate-prompt-template.md
- Outputs: spawn-agent.py, updated CLAUDE.md, updated template
- Checkpoint: pipeline-checkpoint-IMPLEMENT

### Phase: TEST
- Status: PASS
- Mode: AGENT_TEAMS
- Attempts: 0 of 2
- On PASS: -> EVALUATE
- On FAIL: -> IMPLEMENT (fix issues)
- Gate: 4+ test scenarios pass with correct type detection and skill embedding
- Gate Type: AUTO
- Inputs: spawn-agent.py, skill files
- Outputs: work/test-results/spawn-agent-tests.md
- Checkpoint: pipeline-checkpoint-TEST

### Phase: EVALUATE
- Status: PASS
- Mode: SOLO
- Attempts: 0 of 3
- On PASS: -> SYNC
- On FAIL: -> ITERATE
- Gate: Answer to "does everything work automatically?" is YES
- Gate Type: AUTO
- Inputs: Test results, full flow analysis
- Outputs: work/automation-evaluation.md
- Checkpoint: pipeline-checkpoint-EVALUATE

### Phase: ITERATE
- Status: PENDING
- Mode: AGENT_TEAMS
- Attempts: 0 of 3
- On PASS: -> EVALUATE
- On FAIL: -> STOP
- Gate: All identified gaps fixed
- Gate Type: AUTO
- Inputs: work/automation-evaluation.md
- Outputs: Fixed scripts/docs
- Checkpoint: pipeline-checkpoint-ITERATE

### Phase: SYNC
- Status: PASS
- Mode: AGENT_TEAMS
- Attempts: 0 of 1
- On PASS: -> COMPLETE
- On FAIL: -> STOP
- Gate: Template + 8 bots synced
- Gate Type: AUTO
- Inputs: All modified files
- Outputs: Synced projects
- Checkpoint: pipeline-checkpoint-SYNC

---

## Decisions

- [DESIGN] spawn-agent.py imports generate-prompt.py as module — no code duplication
- [DESIGN] Keyword-based type detection with confidence scoring (0-100%)
- [DESIGN] Supports both English and Russian keywords
- [DESIGN] --type override available when auto-detection is insufficient
- [DESIGN] EVALUATE phase uses checklist: "is everything automatic?" — loops back to ITERATE if NO

---

## Execution Rules

1. **Start of session / after compaction:** Re-read this file. Find `<- CURRENT`. Resume from that phase.
2. **Phase execution:** Read phase Inputs. Execute. Produce Outputs. Run Gate check.
3. **Gate verdicts:** PASS (advance), CONCERNS (log + advance), FAIL (go to On FAIL or STOP).
4. **Agent Teams:** If Mode = AGENT_TEAMS, use TeamCreate.
5. **After each phase:** Update this file (move `<- CURRENT`, set Status). Git commit with checkpoint tag.
