# Pipeline: Prompt Generator + Auto-Discovery

- Status: PIPELINE_COMPLETE
- Phase: SYNC
- Mode: INTERACTIVE

> Build generate-prompt.py with skill auto-discovery via YAML roles field.

---

## Phases

### Phase: IMPLEMENT
- Status: PASS
- Mode: AGENT_TEAMS
- Attempts: 0 of 1
- On PASS: -> TEST
- On FAIL: -> STOP
- Gate: Script works, all 13 skills have roles, CLAUDE.md updated
- Gate Type: AUTO
- Inputs: .claude/skills/*/SKILL.md, agents/registry.md, teammate-prompt-template.md
- Outputs: generate-prompt.py, updated YAML front matters, CLAUDE.md rule
- Checkpoint: pipeline-checkpoint-IMPLEMENT

### Phase: TEST
- Status: PASS
- Mode: AGENT_TEAMS
- Attempts: 0 of 1
- On PASS: -> SYNC
- On FAIL: -> IMPLEMENT (fix issues)
- Gate: 4 test scenarios pass with correct skill embedding
- Gate Type: AUTO
- Inputs: generate-prompt.py, skill files
- Outputs: work/e2e-results/prompt-generator-tests.md
- Checkpoint: pipeline-checkpoint-TEST

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

- [DESIGN] Auto-discovery via `roles:` YAML field — no CLAUDE.md edits when adding skills
- [DESIGN] Python stdlib only (like memory-engine.py) — zero dependencies
- [DESIGN] 3 parallel agents in IMPLEMENT (script, YAML roles, CLAUDE.md)
- [DESIGN] 4 test scenarios in TEST: coder, qa-reviewer, planner, edge cases

---

## Execution Rules

1. **Start of session / after compaction:** Re-read this file. Find `<- CURRENT`. Resume from that phase.
2. **Phase execution:** Read phase Inputs. Execute. Produce Outputs. Run Gate check.
3. **Gate verdicts:** PASS (advance), CONCERNS (log + advance), FAIL (go to On FAIL or STOP).
4. **Agent Teams:** If Mode = AGENT_TEAMS, use TeamCreate.
5. **After each phase:** Update this file (move `<- CURRENT`, set Status). Git commit with checkpoint tag.
