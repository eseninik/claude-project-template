# Phase Template: REVIEW

> Run expert panel analysis to identify risks, trade-offs, and architectural concerns.

## Metadata
- Default Mode: AGENT_TEAMS
- Gate Type: AUTO
- Loop Target: none
- Max Attempts: 1
- Checkpoint: pipeline-checkpoint-REVIEW

## Inputs
- `work/{feature}/user-spec.md` (from SPEC phase)
- `.claude/skills/project-knowledge/` (project context)
- `.claude/adr/decisions.md` (existing architectural decisions)

## Process
1. Load expert panel workflow: `cat .claude/guides/expert-panel-workflow.md`
2. Detect relevant domains from the spec (security, performance, data, API, etc.)
3. Select 3-5 expert roles from EXPERT PANEL ROLE SKILLS MAPPING
4. Spawn expert agents — each analyzes spec from their domain perspective
5. Collect expert reports via SendMessage
6. Synthesize into `work/expert-analysis.md` with sections: risks, trade-offs, recommendations, open questions
7. Verify no unresolved open questions remain

## Outputs
- `work/expert-analysis.md` (synthesized expert analysis)

## Quality Gate
Parse `work/expert-analysis.md` for open questions section.

### Verdicts
- PASS: No unresolved open questions, clear recommendations
- CONCERNS: Minor open questions documented but non-blocking
- REWORK: Critical open questions remain — re-run affected experts
- FAIL: Fundamental feasibility concern raised by multiple experts

## Agent Team Config
- Team size: 3-5
- Roles: Selected from — Business Analyst, System Architect, Security Analyst, QA Strategist, Performance Engineer, API Designer, Data Architect, Async Specialist, Risk Assessor
- Skills per role: Per EXPERT PANEL ROLE SKILLS MAPPING in CLAUDE.md
- Prompt template: use `.claude/guides/teammate-prompt-template.md`
- Note: Expert agents are READ-ONLY — they analyze and report, do not modify code

## Context Recovery
After compaction, re-read:
- `work/PIPELINE.md` (find current phase)
- `work/{feature}/user-spec.md` (what experts are reviewing)
- `work/expert-analysis.md` (if exists — check which experts reported)
