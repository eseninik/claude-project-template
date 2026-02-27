# Task: Template Diff Check

## Objective
Compare key files between the main project `.claude/` and the template `.claude/shared/templates/new-project/.claude/` to find any files that are out of sync.

## Required Skills
No specific skills required.

## Acceptance Criteria
1. Compare these file categories between main and template:
   - `.claude/scripts/` vs template `.claude/scripts/`
   - `.claude/ops/config.yaml` vs template `.claude/ops/config.yaml`
   - `.claude/agents/registry.md` vs template `.claude/agents/registry.md`
2. Report which files match, which differ, and which are missing from template
3. Write report to `work/ao-results/task-2-template-diff.md`

## Constraints
- READ and COMPARE only, do NOT modify any files
- Output MUST be written to the exact path above
- Use diff or file comparison, not just listing

## Result Output
Write your findings to: `work/ao-results/task-2-template-diff.md`

Format:
```
# Template Diff Report

## Summary
- Files checked: N
- In sync: N
- Out of sync: N
- Missing from template: N

## Details
| File | Status | Notes |
|------|--------|-------|
| ... | MATCH/DIFF/MISSING | ... |
```
