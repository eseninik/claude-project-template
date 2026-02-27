# AO Task 1: Verify Template-to-Project Skills Sync

## Task

Compare all 13 project skills in `.claude/skills/` against their copies in `.claude/shared/templates/new-project/.claude/skills/`. Verify they are in sync.

For each skill, compare the SKILL.md line count between the project and template directories. Report any differences.

## Output

Write your complete findings to `work/e2e-results/ao-agent-1.md` with:
1. A comparison table (skill name, project lines, template lines, match/mismatch)
2. Any discrepancies found
3. Overall sync status (PASS/FAIL)

## Important

- Follow the project's CLAUDE.md instructions for skill invocation
- Before claiming "done", verify your work following the project's verification protocols
- This is an E2E test — your skill usage will be analyzed
