# Pipeline: Skills Audit & Cleanup

## Status: PIPELINE_COMPLETE
## Current Phase: 4 of 4 (ALL DONE)

> Real-world test of autonomous pipeline system.
> Task: Analyze why 44 skills aren't used by Agent Teams, decide which to keep/remove/fix.

## Phases

- [x] Phase 1: Deep Analysis (DONE — 4 agents: prompt-analyzer, skills-auditor, mechanism-researcher, usage-analyzer)
  - Mode: AGENT_TEAMS
  - Result: Root cause identified — skills are generic docs Opus already knows, no auto-loading mechanism

- [x] Phase 2: Classification & Decision (DONE — work/skills-classification.md)
  - Mode: SOLO
  - Result: 6 ESSENTIAL + 8 USEFUL + 17 MARGINAL + 13 REMOVE = 68% reduction (44 → 14)

- [x] Phase 3: Implementation (DONE — 2 agents: skill-remover + skill-trimmer + lead for index/CLAUDE.md)
  - Mode: AGENT_TEAMS
  - Result: 30 skills deleted, 8 trimmed to checklists, SKILLS_INDEX rewritten (410→123 lines), CLAUDE.md updated

- [x] Phase 4: Verification & Review (DONE)
  - Mode: SOLO
  - Result: Fixed stale refs in 8+ files (teammate-prompt-template, expert-panel, systematic-debugging, skills-reference, work-items), template synced, pipeline review written (work/pipeline-review.md)

## Decisions

- 2026-02-16: Root cause = skills are generic docs, not executable logic. Opus knows TDD/async/security without loading 200-line files
- 2026-02-16: Keep only 14 skills (6 essential + 8 useful), remove 30. Reduce to checklists where possible
- 2026-02-16: Skills should be reserved for complex multi-step procedures, not general knowledge

## Execution Rules

- EVERY phase with 3+ independent tasks -> USE AGENT TEAMS (TeamCreate)
- After compaction -> re-read this file -> continue from <- CURRENT marker
- After each phase -> run verification -> update this file
- If verification fails -> fix -> retest (max 3 attempts, then mark BLOCKED)
