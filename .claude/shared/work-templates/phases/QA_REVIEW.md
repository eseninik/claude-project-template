# Phase Template: QA_REVIEW

> Automated code review cycle: Reviewer agent checks against acceptance criteria, Fixer agent resolves issues. Loops max 3 times.

## Metadata
- Default Mode: AGENT_TEAMS (Reviewer + Fixer agents in sequential chain)
- Gate Type: AUTO
- Loop Target: self (reviewer-fixer cycle, max 3 iterations)
- Max Attempts: 3
- Checkpoint: pipeline-checkpoint-QA_REVIEW

## Phase Context Loading
Before starting this phase, load:
- Acceptance criteria from `work/{feature}/user-spec.md` or `work/{feature}/tech-spec.md`
- `.claude/memory/knowledge.md` — known pitfalls to check for
- `.claude/skills/qa-validation-loop/SKILL.md` — QA procedure
- Query Graphiti: `search_memory_facts(query="quality issues and common bugs", max_facts=10)`

## Inputs
- Source code from IMPLEMENT phase
- Acceptance criteria from task files or user-spec.md
- `.claude/skills/qa-validation-loop/SKILL.md` (the QA skill)

## Process
1. Load QA Validation Loop skill: `cat .claude/skills/qa-validation-loop/SKILL.md`
2. Collect acceptance criteria from Inputs
3. Run QA loop (reviewer -> fixer -> re-reviewer, max 3 iterations)
4. Track issues in `work/qa-issues.md`
5. If all CRITICAL/IMPORTANT resolved -> PASS
6. If recurring issues (3+ same issue) -> FAIL (escalate to human)

## Outputs
- `work/qa-issues.md` -- tracked issues with iteration history
- `work/qa-review-report.md` -- final QA summary (PASS/FAIL with details)

## Quality Gate
Review `work/qa-review-report.md` for final verdict.

### Verdicts
- PASS: No CRITICAL or IMPORTANT issues remaining
- CONCERNS: Only MINOR issues remaining (document and proceed)
- REWORK: CRITICAL issues found but fixable (retry within max 3 iterations)
- FAIL: Recurring unfixable issues (escalate to human)

## Acceptance Criteria
- All CRITICAL issues resolved
- All IMPORTANT issues resolved or documented with justification
- MINOR issues documented (not blocking)
- No recurring issues (same issue across 3+ iterations)

## Agent Team Config
- Team size: 2 (Reviewer + Fixer in sequential chain)
- Roles: Reviewer (checks code against acceptance criteria), Fixer (resolves found issues)
- Skills per role: verification-before-completion, qa-validation-loop
- Prompt template: use `.claude/guides/teammate-prompt-template.md`
- Each agent gets: source code, acceptance criteria, qa-issues.md (if exists from prior iteration)

## Context Recovery
After compaction, re-read:
- `work/PIPELINE.md` (find current phase)
- `work/qa-issues.md` (see current iteration and outstanding issues)
- `work/qa-review-report.md` (if exists -- see prior review results)
