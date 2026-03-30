# Pipeline: Skill Graphs — Cross-References + INDEX.md

- Status: PIPELINE_COMPLETE
- Phase: COMPLETE
- Mode: AGENT_TEAMS

> Lightweight pipeline: research done, spec is clear (2 patterns), skip to IMPLEMENT.

---

## Phases

### Phase: AUTO_RESEARCH
- Status: DONE
- Mandatory: true
- Mode: AGENT_TEAMS
- Attempts: 1 of 1
- Gate: research complete
- Gate Type: AUTO
- Checkpoint: pipeline-checkpoint-AUTO_RESEARCH
- Skip-if: N/A — completed via 3 parallel research agents

### Phase: IMPLEMENT  <- CURRENT
- Status: IN_PROGRESS
- Mode: AGENT_TEAMS
- Attempts: 0 of 2
- On PASS: -> QA_REVIEW
- On FAIL: -> STOP
- Gate: all 22 skills have ## Related section, INDEX.md exists
- Gate Type: AUTO
- Inputs: research findings (cross-reference map from 22 skills)
- Outputs: 22 updated SKILL.md files + INDEX.md
- Checkpoint: pipeline-checkpoint-IMPLEMENT

### Phase: QA_REVIEW
- Status: PENDING
- Mode: SOLO
- Attempts: 0 of 1
- On PASS: -> SYNC
- On FAIL: -> STOP
- Gate: 0 broken references, all Related sections consistent
- Gate Type: AUTO
- Inputs: updated SKILL.md files, INDEX.md
- Outputs: work/skill-graphs/qa-report.md
- Checkpoint: pipeline-checkpoint-QA_REVIEW

### Phase: SYNC
- Status: PENDING
- Mode: AGENT_TEAMS
- Attempts: 0 of 1
- On PASS: -> SKILL_EVOLUTION
- On FAIL: -> STOP
- Gate: project skills + template skills match global
- Gate Type: AUTO
- Inputs: global skills with Related sections
- Outputs: synced project + template skills
- Checkpoint: pipeline-checkpoint-SYNC

### Phase: SKILL_EVOLUTION
- Status: PENDING
- Mandatory: true
- Mode: SOLO
- Attempts: 0 of 1
- On PASS: -> COMPLETE
- On FAIL: -> COMPLETE
- Gate: evolution proposed or "no learnings" logged
- Gate Type: AUTO

---

## Decisions

- [AUTO_RESEARCH] Decision: Only 2 patterns needed (Related sections + INDEX.md). Reason: full skill graph transition has overhead > benefit, we're already at 80%.
- [IMPLEMENT] Decision: Split into 5 agent waves (4-5 skills each) + 1 INDEX.md agent. Reason: 22 skills need parallel updates.
