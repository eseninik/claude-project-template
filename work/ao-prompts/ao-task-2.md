# AO Task 2: Analyze CLAUDE.md Skill Trigger Coverage

## Task

Read the project's CLAUDE.md file and analyze the "Skills (invoke via Skill tool)" trigger table. For each of the 13 skills listed, verify that the skill actually exists in `.claude/skills/` and that its YAML description matches the trigger situation.

## Steps

1. Read CLAUDE.md and extract the Skills trigger table
2. For each skill in the table, read its SKILL.md and check the YAML `description:` field
3. Verify the trigger situation in CLAUDE.md aligns with the skill's description
4. Check if any skills in `.claude/skills/` are NOT covered by the trigger table

## Output

Write your complete analysis to `work/e2e-results/ao-agent-2.md` with:
1. A coverage table (skill, trigger in CLAUDE.md, description match, verdict)
2. Any gaps or mismatches found
3. Overall coverage assessment

## Important

- Follow the project's CLAUDE.md instructions for skill invocation
- Before claiming your analysis is complete, verify each finding with evidence
- This is an E2E test — your skill usage will be analyzed
