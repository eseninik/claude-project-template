# Task: Audit Skills Directory

## Objective
Audit all skills in `.claude/skills/` directory. For each skill, extract the name, description (first line of SKILL.md), and file size. Write a summary report.

## Required Skills
No specific skills required.

## Acceptance Criteria
1. List ALL skills found in `.claude/skills/` (each subdirectory with SKILL.md)
2. For each: name, one-line description, line count
3. Write report to `work/ao-results/task-1-skills-audit.md`

## Constraints
- READ the skills, do NOT modify them
- Output MUST be written to the exact path above
- Keep report concise (table format preferred)

## Result Output
Write your findings to: `work/ao-results/task-1-skills-audit.md`

Format:
```
# Skills Audit Report
| # | Skill Name | Description | Lines |
|---|-----------|-------------|-------|
| 1 | ... | ... | ... |

Total: N skills
```
