# Pipeline: Global Skills Migration

- Status: PIPELINE_COMPLETE
- Phase: COMPLETE
- Mode: AGENT_TEAMS

> Move shared skills to ~/.claude/ (global), keep project-specific in project .claude/skills/.
> Test all 5 new features: AUTO_RESEARCH, FRESH_VERIFY, SKILL_EVOLUTION, Agent Memory, Examples.

---

## Phases

### Phase: AUTO_RESEARCH
- Status: DONE
- Mandatory: true
- Mode: AGENT_TEAMS
- Attempts: 1 of 1
- On PASS: -> PLAN
- On FAIL: -> STOP
- Gate: auto-research.md exists with GO decision
- Gate Type: AUTO
- Inputs: user request, current project structure, Claude Code docs on global skills
- Outputs: work/global-skills/auto-research.md
- Checkpoint: pipeline-checkpoint-AUTO_RESEARCH

### Phase: PLAN
- Status: DONE
- Mode: SOLO
- Attempts: 0 of 1
- On PASS: -> IMPLEMENT
- On FAIL: -> STOP
- Gate: migration plan exists with file list
- Gate Type: USER_APPROVAL
- Inputs: auto-research.md
- Outputs: work/global-skills/migration-plan.md

### Phase: IMPLEMENT
- Status: DONE
- Mode: AGENT_TEAMS
- Attempts: 0 of 2
- On PASS: -> FRESH_VERIFY
- On FAIL: -> STOP
- Gate: skills moved, projects updated
- Gate Type: AUTO

### Phase: FRESH_VERIFY
- Status: DONE
- Mandatory: true
- Mode: AO_HYBRID
- Attempts: 0 of 2
- On PASS: -> QA_REVIEW
- On FAIL: -> FIX
- Gate: fresh-verify-report.md exists with 0 CRITICAL
- Gate Type: AUTO

### Phase: QA_REVIEW
- Status: PENDING
- Mode: SOLO
- Attempts: 0 of 2
- On PASS: -> SKILL_EVOLUTION
- On REWORK: -> FIX
- Gate: no CRITICAL issues
- Gate Type: AUTO

### Phase: FIX
- Status: PENDING
- Mode: SOLO
- Attempts: 0 of 3
- On PASS: -> QA_REVIEW
- On BLOCKED: -> STOP

### Phase: SKILL_EVOLUTION
- Status: DONE
- Mandatory: true
- Mode: SOLO
- Attempts: 0 of 1
- On PASS: -> COMPLETE
- Gate: evolution proposed for used skills OR "no learnings" logged
- Gate Type: AUTO

### Phase: COMPLETE
- Status: PENDING
- Mode: SOLO
- On PASS: -> DONE
- Gate: memory updated, committed

---

## Decisions

- [USER] Skills should be global (~/.claude/) so self-evolution applies across all projects
- [USER] Project-specific skills stay in project .claude/skills/ (e.g. Freelance bot unique skill)
- [USER] This pipeline tests all 5 new features (AUTO_RESEARCH, FRESH_VERIFY, SKILL_EVOLUTION, Agent Memory, Examples)

---

## Execution Rules

1. Start of session / after compaction: find <- CURRENT, resume.
2. Mandatory phases cannot be skipped.
3. Agent Teams for 3+ parallel tasks.
