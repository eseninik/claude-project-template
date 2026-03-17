# Verification Before Completion — Examples

> Real-world examples from actual usage. Grows organically via skill-evolution pattern.
> Each example: what was the input → what the skill did → what was the output.

## Example 1: Fresh Session Verification Catches Missed Project

**Context**: Global skills migration — FRESH_VERIFY mandatory phase after IMPLEMENT

**Input**: 11 projects were supposed to be updated (skills removed, CLAUDE.md compressed, guides synced)

**What happened**:
- Fresh verifier agent spawned with NO implementation history
- Checked 5 verification criteria across sample projects
- Found Knowledge Bot main was entirely unmigrated (skills not removed, CLAUDE.md 491 lines, guides missing)

**Output**: FAIL verdict with CRITICAL finding. Knowledge Bot main fixed manually, then pipeline continued.

**Learning**: Projects with nested subdirectories (Knowledge Bot/Knowledge Bot main/) are easy to miss. Fresh eyes caught what the implementation team overlooked — proof that FRESH_VERIFY works.

---
