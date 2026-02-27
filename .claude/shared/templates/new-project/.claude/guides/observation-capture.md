# Observation Capture Protocol

> Capture friction, surprises, gaps, and insights during work sessions.
> When observations accumulate, review and promote to knowledge.md.

---

## When to Capture

Capture an observation when you notice:
- **Friction**: Something was harder/slower than expected
- **Surprise**: Something worked differently than anticipated
- **Gap**: A missing feature, guide, or pattern was needed
- **Insight**: A reusable pattern or principle emerged

## How to Capture

Create a file in `.claude/memory/observations/`:

**Filename:** `{YYYY-MM-DD}-{short-slug}.md`
**Example:** `2026-02-24-session-orient-windows-encoding.md`

**Format:**
```
---
type: friction | surprise | gap | insight
date: YYYY-MM-DD
context: "Brief description of what you were doing"
status: pending | promoted | archived
---

[Observation text — 2-5 sentences describing what happened and why it matters]
```

## Review Thresholds

| Pending Count | Signal |
|---------------|--------|
| 5+ | Consider reviewing observations |
| 10+ | Review needed — run /rethink or manual review |

The session-orient hook automatically counts pending observations and surfaces alerts.

## Promotion Process

During review:
1. **PROMOTE**: Observation crystallized into a reusable pattern → add to knowledge.md
2. **ARCHIVE**: Session-specific, no longer relevant → set status: archived
3. **KEEP PENDING**: Needs more evidence → leave as pending

## Examples

### Friction Example
```
---
type: friction
date: 2026-02-24
context: "Creating session-orient hook for Windows"
status: pending
---
Windows default encoding (charmap) chokes on Unicode in knowledge.md.
Fix: sys.stdout.reconfigure(encoding="utf-8"). This should be standard
in all hooks that output file content to stdout.
```

### Insight Example
```
---
type: insight
date: 2026-02-24
context: "Implementing arscontexta improvements"
status: pending
---
Hook enforcement achieves ~100% compliance vs ~30-40% for instruction enforcement.
The key difference: hooks fire automatically regardless of agent attention state.
Instructions require the agent to remember, which degrades under context load.
```
