---
description: Extract learnings from current session into knowledge.md or new skills
---

# /learn-eval — Session Learning Extraction

Analyze this session and extract reusable patterns.

## Instructions

1. Invoke the `learn-eval` skill (read `.claude/skills/learn-eval/SKILL.md`)
2. Scan the entire conversation for patterns (errors resolved, user corrections, novel approaches, failed approaches, architecture decisions)
3. Score each pattern on novelty, reusability, specificity, impact
4. Check for duplicates in `.claude/memory/knowledge.md`
5. Save qualifying patterns (score >= 60%) to appropriate destination
6. Present the Learn-Eval Report to the user

## Quality Gate

Before saving any pattern:
- Verify it's not already in knowledge.md
- Verify it's concrete (not vague advice)
- Include the "Why" — rationale for why this matters
- If updating existing pattern, use `py -3 .claude/scripts/memory-engine.py knowledge-touch "{name}" .claude/memory/`
