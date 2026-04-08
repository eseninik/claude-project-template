---
name: memory-consolidation
description: >
  Background memory consolidation — scan daily logs, deduplicate knowledge.md entries,
  resolve conflicts, refresh decay tiers, clean stale observations. Use at end of
  productive sessions, when user says "/consolidate", or via scheduled task.
  Do NOT use for mid-session memory updates or active context changes.
roles: [insight-extractor]
---

# Memory Consolidation

## Overview

Like human sleep consolidating daily experiences into long-term memory, this skill processes accumulated session data into clean, deduplicated, conflict-free knowledge. Inspired by Claude Code's AutoDream feature.

**Core principle:** Memory that isn't maintained becomes noise. Regular consolidation keeps the knowledge base sharp.

## When to Run

- End of a productive session (3+ tasks completed)
- User says "/consolidate" or "clean up memory"
- Via scheduled task (recommended: daily or weekly)
- After major refactoring or architecture changes
- When knowledge.md exceeds 100 entries

## Process

### Phase 1: Scan Recent Activity

1. Read daily logs from last 7 days: `.claude/memory/daily/*.md`
2. Read current knowledge.md: `.claude/memory/knowledge.md`
3. Read observations: `.claude/memory/observations/*.md`
4. Read activeContext.md for current session state
5. Collect all patterns, gotchas, and learnings mentioned

### Phase 2: Deduplicate Knowledge

Scan knowledge.md for near-duplicate entries:
- Same concept described differently (e.g., "Windows hooks need Python" and "Hooks on Windows must use py -3")
- Entries that evolved over time but old version wasn't removed
- Patterns that are subsets of other patterns

For each duplicate group:
1. Keep the most complete/recent entry
2. Merge unique details from duplicates into the keeper
3. Update the verified date to today
4. Remove the duplicates

### Phase 3: Resolve Conflicts

Find contradicting entries:
- "Always use X" vs. "Never use X" (direct contradiction)
- "Use approach A for task T" vs. "Use approach B for task T" (competing advice)
- Stale entries contradicted by recent daily logs

For each conflict:
1. Check which entry has more recent verification
2. Check daily logs for evidence of which approach actually worked
3. If clear winner: update to winning approach, remove loser
4. If ambiguous: flag for human review in consolidation report

### Phase 4: Refresh Decay Tiers

Run memory engine to recalculate all tiers:
```bash
py -3 .claude/scripts/memory-engine.py decay .claude/memory/
```

Review results:
- Entries decayed to archive tier → consider if still relevant
- Entries in cold tier → check if recently used but not touched
- Touch any pattern that was used in the last 7 days of daily logs

### Phase 5: Clean Observations

Review `.claude/memory/observations/*.md`:
- Observations older than 30 days that haven't been promoted to knowledge → archive
- Observations that duplicate existing knowledge.md entries → delete
- High-value observations not yet in knowledge.md → promote

### Phase 6: Generate Report

Output a consolidation summary:

```
## Memory Consolidation Report — {date}

### Statistics
- Knowledge entries before: {N}
- Knowledge entries after: {M}
- Duplicates merged: {X}
- Conflicts resolved: {Y}
- Conflicts flagged for human review: {Z}
- Observations archived: {A}
- Observations promoted to knowledge: {B}
- Patterns refreshed (decay touch): {C}

### Changes Made
{List of specific merges, removals, promotions}

### Flagged for Human Review
{List of unresolved conflicts, if any}

### Health Score
- Dedup ratio: {percentage of entries that were unique}
- Freshness: {percentage of entries verified within 30 days}
- Coverage: {ratio of observations promoted vs total observations}
```

## Integration

### With /schedule
```
/schedule daily 6am "Run memory consolidation"
```

### With /learn-eval
Run consolidation AFTER learn-eval extracts new patterns, to immediately deduplicate.

### With Pipeline
Add as optional step in Phase Transition Protocol:
"After 3+ phases complete, run memory-consolidation to prevent knowledge drift."

## Common Mistakes

- Running consolidation mid-session (can remove context you're actively using)
- Deleting entries without checking daily logs (the entry might be actively needed)
- Merging entries that look similar but apply to different contexts
- Skipping the conflict resolution phase (contradictions accumulate silently)
