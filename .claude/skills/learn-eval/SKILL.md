---
name: learn-eval
description: Extract and evaluate reusable patterns from the current session, saving high-quality learnings to knowledge.md or as new skills. Use when ending a productive session, when user says "/learn-eval", or after major debugging/feature work. Do NOT use for routine session cleanup.
roles: [insight-extractor]
---

# Learn-Eval — Session Learning Extraction

## When to Activate

- User says "/learn-eval"
- End of productive session with new patterns
- After resolving complex bugs
- After completing major features

## Process

### Step 1: Scan Session
Review the conversation for:
1. **Errors resolved** — what broke, root cause, fix
2. **User corrections** — where agent was wrong (HIGHEST priority)
3. **Novel approaches** — non-obvious solutions that worked
4. **Failed approaches** — what was tried and why it failed
5. **Architecture decisions** — choices and rationale

### Step 2: Evaluate Each Pattern

Score each candidate (threshold: 60%):
- **Novelty (40%)** — not already in knowledge.md?
- **Reusability (30%)** — applies to future sessions?
- **Specificity (20%)** — concrete and actionable?
- **Impact (10%)** — saves significant time/effort?

### Step 3: Deduplicate

Before saving, check:
- `grep -i "{pattern keyword}" .claude/memory/knowledge.md`
- If similar exists → UPDATE with new details, refresh verified date
- If truly new → ADD to appropriate section

### Step 4: Save

| Score | Type | Destination |
|-------|------|-------------|
| 80%+ | Reusable workflow | New skill in `.claude/skills/` |
| 60-79% | Pattern/Gotcha | `.claude/memory/knowledge.md` |
| < 60% | Session note | `.claude/memory/daily/{date}.md` |

### Step 5: Output Report

```markdown
## Learn-Eval Report — {date}

### Saved ({N} patterns)
1. **{Name}** → {destination} (score: {X}%)
   - Summary: {one line}

### Skipped ({M} below threshold)
- {name}: {reason}

### Knowledge.md Updates
- Updated: {list}
- Added: {list}
```

## Key Rules

1. **User corrections are ALWAYS saved** — score override to 100%
2. **Never duplicate** — update existing patterns, don't create copies
3. **Include "Why"** — pattern without rationale is useless for future recall
4. **Refresh verified dates** — use `knowledge-touch` for patterns that were validated

## Related

- [continuous-learning](./../continuous-learning/SKILL.md) — auto-extract patterns from sessions
- [skill-evolution](~/.claude/skills/skill-evolution/SKILL.md) — self-evolving skill improvement after execution
