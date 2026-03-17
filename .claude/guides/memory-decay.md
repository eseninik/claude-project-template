# Memory Decay (Ebbinghaus Forgetting Curve)

> Patterns/gotchas in knowledge.md have temporal relevance. Old entries auto-decay, fresh ones rise.

## Tiers

| Tier | Days since verified | When to use |
|------|-------------------|-------------|
| **active** | 0-14 | Top priority, always shown at session start |
| **warm** | 15-30 | Still relevant, may need re-verification |
| **cold** | 31-90 | Possibly outdated, needs refresh |
| **archive** | 90+ | Likely stale, surface only in deep/creative search |

## Search Modes

| Mode | Tokens | Use for |
|------|--------|---------|
| heartbeat | ~2K | Simple bug fixes, single-file tasks |
| normal | ~5K | Most tasks, feature implementation |
| deep | ~15K | Architecture decisions, "find everything about X" |
| creative | ~3K | Brainstorming, design phases, serendipity |

## Commands

```bash
py -3 .claude/scripts/memory-engine.py knowledge .claude/memory/ --verbose  # tier analysis
py -3 .claude/scripts/memory-engine.py knowledge-touch "name" .claude/memory/ # refresh pattern
py -3 .claude/scripts/memory-engine.py creative 5 .claude/memory/            # serendipity
py -3 .claude/scripts/memory-engine.py stats .claude/memory/                  # health check
py -3 .claude/scripts/memory-engine.py decay .claude/memory/                  # recalculate all
```

## When You USE a Pattern

If you used a knowledge.md pattern during work, refresh it:
```bash
py -3 .claude/scripts/memory-engine.py knowledge-touch "Pattern Name" .claude/memory/
```
This promotes it one tier up (graduated recall, not straight to top). Skip if already verified within 7 days.
