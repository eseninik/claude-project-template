# Phase Template: SPEC

> Gather user requirements through adaptive interview and produce a structured spec.

## Metadata
- Default Mode: SOLO
- Gate Type: USER_APPROVAL
- Loop Target: none
- Max Attempts: 1
- Checkpoint: pipeline-checkpoint-SPEC

## Inputs
- User's initial task description (conversation or issue)
- `.claude/skills/project-knowledge/` (project context)

## Process
1. Read project context: `cat .claude/skills/project-knowledge/guides/architecture.md`
2. Analyze user request — identify ambiguities and missing details
3. Run adaptive interview (3-7 questions, stop when acceptance criteria are clear)
4. Extract functional requirements, non-functional requirements, constraints
5. Define acceptance criteria (testable, specific)
6. Write spec to `work/{feature}/user-spec.md`
7. Present spec summary to user for approval

## Outputs
- `work/{feature}/user-spec.md` (structured requirements with acceptance criteria)

## Quality Gate
User reviews the spec document.

### Verdicts
- PASS: User approves spec without changes
- CONCERNS: User approves with minor notes (document them in spec)
- REWORK: User requests significant changes — re-interview, rewrite spec
- FAIL: User abandons the feature request

## Context Recovery
After compaction, re-read:
- `work/PIPELINE.md` (find current phase)
- `work/{feature}/user-spec.md` (if exists — resume from last draft)
- Conversation history for interview answers
