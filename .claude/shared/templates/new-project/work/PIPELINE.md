# Pipeline: {TASK_NAME}

## Status: NOT_STARTED
## Current Phase: 0 of 0

> Edit this file to define your pipeline phases.
> Each phase with 3+ independent tasks should use AGENT_TEAMS mode.
> After compaction, agent re-reads this file and continues from <- CURRENT.

## Phases

- [ ] Phase 1: {name} <- CURRENT
  - Mode: SOLO | AGENT_TEAMS
  - Tasks: {description or list}
  - Acceptance: {criteria}
- [ ] Phase 2: {name}
  - Mode: SOLO | AGENT_TEAMS
  - Tasks: {description or list}
  - Acceptance: {criteria}
- [ ] Phase 3: {name}
  - Mode: SOLO | AGENT_TEAMS
  - Tasks: {description or list}
  - Acceptance: {criteria}

## Decisions

(Append decisions made during execution)

## Execution Rules

- EVERY phase with 3+ independent tasks -> USE AGENT TEAMS (TeamCreate)
- After compaction -> re-read this file -> continue from <- CURRENT marker
- After each phase -> run verification -> update this file
- If verification fails -> fix -> retest (max 3 attempts, then mark BLOCKED)
