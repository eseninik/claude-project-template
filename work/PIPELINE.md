# Pipeline: Agent Memory Fix + Global Skills Audit

- Status: IN_PROGRESS
- Phase: AUTO_RESEARCH
- Mode: AGENT_TEAMS

> Task 1: Make Agent Memory work (spawn-agent.py integration or alternative)
> Task 2: Audit 14 original global skills — needed or dead weight?

---

## Phases

### Phase: AUTO_RESEARCH
- Status: DONE
- Mandatory: true
- Mode: AGENT_TEAMS
- Attempts: 1 of 1
- On PASS: -> PLAN
- Gate: auto-research.md exists with findings for both tasks
- Gate Type: AUTO

### Phase: PLAN
- Status: PENDING
- Mode: SOLO
- On PASS: -> IMPLEMENT
- Gate: plan approved by user

### Phase: IMPLEMENT  <- CURRENT
- Status: IN_PROGRESS
- Mode: AGENT_TEAMS
- On PASS: -> FRESH_VERIFY

### Phase: FRESH_VERIFY
- Status: PENDING
- Mandatory: true
- Mode: AO_HYBRID
- On PASS: -> SKILL_EVOLUTION
- Gate: fresh-verify-report.md with 0 CRITICAL

### Phase: SKILL_EVOLUTION
- Status: PENDING
- Mandatory: true
- Mode: SOLO
- On PASS: -> COMPLETE
- Gate: evolution proposed or "no learnings" logged

### Phase: COMPLETE
- Status: PENDING
- On PASS: -> DONE

---

## Decisions
- [USER] Agent Memory must work without forcing spawn-agent.py
- [USER] 14 original global skills need audit — remove if dead weight
- [USER] Test in passive mode — don't force features, observe if they trigger

## Feature Tracking (passive observation)
- AUTO_RESEARCH: ⏳ testing now
- Agent Memory: ⏳ main goal of this pipeline
- FRESH_VERIFY: ⏳ after IMPLEMENT
- SKILL_EVOLUTION: ⏳ after FRESH_VERIFY
- Skill Examples: ⏳ via SKILL_EVOLUTION
