---
name: continuous-learning
description: Auto-extract reusable patterns from Claude Code sessions into skills and knowledge. Use when ending productive sessions or when user says "/learn-eval". Do NOT use for routine config or memory updates.
roles: [insight-extractor]
---

# Continuous Learning

## When to Activate

- End of a productive session with new patterns discovered
- User says "/learn-eval" or "extract learnings"
- After completing a major feature or debugging session
- When a novel approach worked well and should be reusable

## Process

### 1. Session Analysis
Scan the current session for:
- **Error resolutions** — what broke, what fixed it, why
- **User corrections** — where Claude was wrong and user redirected
- **Workarounds** — non-obvious solutions to specific problems
- **Debugging techniques** — steps that led to root cause
- **Architectural decisions** — choices made and rationale

### 2. Pattern Evaluation

For each candidate pattern, score:

| Criterion | Weight | Question |
|-----------|--------|----------|
| Novelty | 40% | Is this already in knowledge.md? |
| Reusability | 30% | Will this apply to future sessions? |
| Specificity | 20% | Is it concrete enough to be actionable? |
| Impact | 10% | How much time/effort does it save? |

**Threshold:** Score >= 60% → save. Below → skip.

### 3. Save Destination

| Pattern Type | Destination | Format |
|-------------|-------------|--------|
| Gotcha / Bug pattern | `.claude/memory/knowledge.md` | `### Name (date, verified: date)` |
| Reusable workflow | `.claude/skills/{name}/SKILL.md` | Full skill format |
| Project-specific | `.claude/memory/daily/{date}.md` | Session log entry |

### 4. Deduplication

Before saving, check:
1. Does knowledge.md already have a similar pattern? → Update instead of duplicate
2. Does an existing skill cover this? → Propose evolution instead of new skill
3. Is the daily log sufficient? → Don't promote to knowledge.md

## Output Format

```markdown
## Session Learnings — {date}

### Patterns Extracted: {N}

1. **{Pattern Name}** (score: {X}%)
   - Type: {gotcha|workflow|architectural}
   - Destination: {knowledge.md|new skill|daily log}
   - Summary: {one line}

### Skipped: {M} patterns below threshold
```

## Key Rules

1. **Never save trivial fixes** — typos, one-time config changes
2. **Always check for duplicates** before adding to knowledge.md
3. **User corrections are highest priority** — if Claude was wrong, that's always worth saving
4. **Include "Why"** — pattern without rationale is useless

## Related

- [learn-eval](./../learn-eval/SKILL.md) — extract and evaluate session patterns
- [skill-evolution](~/.claude/skills/skill-evolution/SKILL.md) — self-evolving skill improvement after execution
- [skill-conductor](~/.claude/skills/skill-conductor/SKILL.md) — create, edit, evaluate, and package skills
