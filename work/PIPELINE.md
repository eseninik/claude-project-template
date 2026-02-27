# Pipeline: AO Hybrid E2E Test + Bot Fleet Sync

- Status: PIPELINE_COMPLETE
- Phase: VERIFY
- Mode: INTERACTIVE

> Goal: (1) Fix prep issues, (2) E2E test AO Hybrid with real tasks, (3) Sync to 8 bots.
> After compaction: find `<- CURRENT`, read that phase, continue.

---

## Phases

### Phase: PREP
- Status: PASS
- Mode: SOLO
- Attempts: 0 of 1
- On PASS: -> AO_HYBRID_TEST
- On FAIL: -> STOP
- Gate: ao-hybrid.sh status parsing fixed, AO config has agentConfig.permissions
- Gate Type: AUTO
- Inputs: ao-hybrid.sh, ~/.agent-orchestrator.yaml
- Outputs: fixed script, updated config
- Checkpoint: pipeline-checkpoint-PREP

### Phase: AO_HYBRID_TEST
- Status: PASS
- Mode: AO_HYBRID
- Attempts: 0 of 2
- On PASS: -> BOT_SYNC
- On FAIL: -> STOP
- On REWORK: -> PREP
- Gate: 2+ sessions spawned, all produced handoff files, results verified
- Gate Type: USER_APPROVAL
- Inputs: ao-hybrid.sh, ao spawn CLI with --prompt-file
- Outputs: work/ao-results/*.md (handoff files from spawned agents)
- Checkpoint: pipeline-checkpoint-AO_HYBRID_TEST

### Phase: BOT_SYNC
- Status: PASS
- Mode: AGENT_TEAMS
- Attempts: 0 of 1
- On PASS: -> VERIFY
- On FAIL: -> STOP
- Gate: all 8 bots have updated files, CLAUDE.md includes AO_HYBRID section
- Gate Type: AUTO
- Inputs: template files from .claude/shared/templates/new-project/
- Outputs: 8 git commits (one per bot)
- Checkpoint: pipeline-checkpoint-BOT_SYNC

### Phase: VERIFY
- Status: PASS
- Mode: SOLO
- Attempts: 0 of 1
- On PASS: -> COMPLETE
- On FAIL: -> BOT_SYNC
- Gate: spot-check 2-3 bots, verify key files match template
- Gate Type: AUTO
- Inputs: 8 bot directories
- Outputs: verification report
- Checkpoint: pipeline-checkpoint-VERIFY

---

## Decisions

<!-- Append-only -->

---

## Execution Rules

1. **Start of session / after compaction:** Re-read this file. Find `<- CURRENT`. Resume from that phase.
2. **Phase execution:** Read phase Inputs. Execute. Produce Outputs. Run Gate check.
3. **Gate verdicts:** PASS (advance), CONCERNS (log + advance), REWORK (retry), FAIL (block).
4. **After each phase:** Update this file, update memory, git commit with checkpoint.
5. **Agent Teams:** If Mode = AGENT_TEAMS, use TeamCreate with Required Skills.
6. **AO Hybrid:** If Mode = AO_HYBRID, use ao spawn --prompt-file per task. Monitor via ao-hybrid.sh. Skill: `cat .claude/skills/ao-hybrid-spawn/SKILL.md`.
