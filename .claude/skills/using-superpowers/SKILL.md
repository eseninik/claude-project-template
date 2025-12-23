---
name: using-superpowers
version: 1.0.0
description: Use when starting any conversation - establishes mandatory workflows for finding and using skills
---

# Using Skills

## When to Check for Skills

**Check for skills when:**
- Writing or changing code
- Fixing bugs
- Implementing features
- Any task that modifies files

**Skip skill check for:**
- Informational questions ("what is X?")
- Clarifications on current task
- Confirmations ("yes", "continue")
- Simple file reads without changes

## The Process

1. **Check CLAUDE.md** — it has the Task Classification Algorithm
2. **If task needs skills** → `cat .claude/skills/SKILLS_INDEX.md`
3. **Select 1-3 skills** from the index
4. **Load each skill** → `cat .claude/skills/<folder>/SKILL.md`
5. **Announce** which skill you're using
6. **Follow** the skill exactly

## Announcing Skill Usage

Before using a skill, announce it:
- "I'm using systematic-debugging to investigate this error."
- "I'm using test-driven-development to implement this feature."

## Skills with Checklists

If a skill has a checklist, create TodoWrite todos for EACH item.

**Don't:**
- Work through checklist mentally
- Skip creating todos "to save time"
- Batch multiple items into one todo

## Common Rationalizations

If you catch yourself thinking:
- "This is just a simple question" → Is it? Check CLAUDE.md
- "I can check quickly without skills" → Skills save time, not waste it
- "This doesn't need a formal skill" → If a skill exists for it, use it
- "The skill is overkill" → Skills exist because simple things become complex

## Rules

1. **Algorithm in CLAUDE.md** — that's the source of truth for when to use skills
2. **Catalog in SKILLS_INDEX.md** — that tells you which skill to load
3. **Maximum 3 skills** simultaneously
4. **Announce usage** before using a skill
5. **Follow exactly** — don't adapt away the discipline

## Summary

```
Task arrives
  ↓
Check CLAUDE.md (Task Classification)
  ↓
Need skills? → cat .claude/skills/SKILLS_INDEX.md
  ↓
Select skills → Load each one
  ↓
Announce → Follow
```
