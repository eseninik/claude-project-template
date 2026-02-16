# Phase Template: PLAN

> Create technical specification, decompose into tasks, and analyze parallelization.

## Metadata
- Default Mode: SOLO (simple) or AGENT_TEAMS (complex, 5+ components)
- Gate Type: USER_APPROVAL
- Loop Target: none
- Max Attempts: 1
- Checkpoint: pipeline-checkpoint-PLAN

## Inputs
- `work/{feature}/user-spec.md` (from SPEC phase)
- `work/expert-analysis.md` (from REVIEW phase)
- `.claude/skills/project-knowledge/guides/architecture.md`
- `.claude/adr/decisions.md`

## Process
1. Read user spec and expert analysis
2. Design technical architecture (modules, APIs, data flow)
3. If expert analysis flagged concerns — address each in the design
4. Decompose into atomic tasks with acceptance criteria
5. Write each task to `work/{feature}/tasks/{N}-{name}.md`
6. Run wave analysis: identify independent tasks that can parallelize
7. Write wave plan to `work/{feature}/tasks/waves.md`
8. Compile full tech spec to `work/{feature}/tech-spec.md`
9. Present plan summary to user for approval

## Outputs
- `work/{feature}/tech-spec.md` (architecture, API design, data model)
- `work/{feature}/tasks/*.md` (atomic task files with acceptance criteria)
- `work/{feature}/tasks/waves.md` (parallelization analysis)

## Quality Gate
User reviews tech spec and task breakdown.

### Verdicts
- PASS: User approves plan
- CONCERNS: User approves with notes (document in tech-spec)
- REWORK: User wants different approach — redesign and resubmit
- FAIL: User cancels the feature

## Agent Team Config
Only for complex plans (5+ components requiring separate research):
- Team size: 2-3
- Roles: Architect (design), Researcher (codebase analysis)
- Skills per role: project-knowledge, codebase-mapping
- Prompt template: use `.claude/guides/teammate-prompt-template.md`

## Context Recovery
After compaction, re-read:
- `work/PIPELINE.md` (find current phase)
- `work/{feature}/user-spec.md` (requirements)
- `work/expert-analysis.md` (expert concerns to address)
- `work/{feature}/tech-spec.md` (if exists — resume from draft)
