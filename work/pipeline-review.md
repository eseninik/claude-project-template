# Pipeline Test Review: Skills Audit & Cleanup

**Date:** 2026-02-16
**Pipeline:** Skills Audit & Cleanup (4 phases)
**Duration:** Single session (with context compaction/continuation)

---

## What Worked

### State Machine (PIPELINE.md)
- `<- CURRENT` markers correctly guided resumption after compaction
- Phase-by-phase progression with clear acceptance criteria was effective
- Mode field (SOLO vs AGENT_TEAMS) determined execution strategy per phase

### Agent Teams (Phases 1 & 3)
- **Phase 1:** 4 research agents (prompt-analyzer, skills-auditor, mechanism-researcher, usage-analyzer) all completed successfully in parallel. Each produced focused, non-overlapping analysis.
- **Phase 3:** 2 implementation agents (skill-remover + skill-trimmer) worked on non-conflicting directories. Lead handled SKILLS_INDEX and CLAUDE.md updates to avoid merge conflicts.

### Results Quality
- Root cause identified clearly: skills are generic documentation that Opus already knows
- Classification was decisive: 44 → 14 skills (68% reduction)
- Cross-reference cleanup caught stale refs in 6+ files across main and template

### Compaction Resilience
- Session survived context compaction and continued from Phase 4
- PIPELINE.md provided enough state to resume correctly
- Summary instructions in CLAUDE.md preserved critical behavioral rules

---

## What Didn't Work

### Template Sync Gap
- Phase 3 agents updated main `.claude/` files but NOT the `shared/templates/new-project/.claude/` copies
- Required manual Phase 4 cleanup to sync template copies
- **Fix needed:** Template sync should be an explicit task in every implementation phase

### Stale Reference Cascade
- Deleting 30 skills left stale references in 8+ files: teammate-prompt-template.md, expert-panel/SKILL.md, systematic-debugging/SKILL.md, skills-reference.md, work-items.md
- Phase 3 agents didn't run a cross-reference check before reporting "done"
- **Fix needed:** verification-before-completion should include cross-reference grep for deleted items

### Agent Coordination
- No automated way for implementation agents to know about template copies
- Each agent only sees their assigned scope, doesn't know about the template mirror
- **Fix needed:** Task descriptions should explicitly list ALL locations to update (main + template)

### CLAUDE.md Stale Mappings
- CLAUDE.md TEAM ROLE SKILLS MAPPING and EXPERT PANEL ROLE SKILLS MAPPING were updated but still reference deleted skills in non-CLAUDE.md contexts
- Agent definitions (orchestrator.md, code-reviewer.md) still reference deleted skills in their configs
- **Decision:** Agent .md files are descriptive and tolerate stale skill references. Not critical but should be cleaned on next pass.

---

## Pipeline System Assessment

### Strengths
1. **Phase isolation** — each phase has clear scope and acceptance criteria
2. **Mode selection** — AGENT_TEAMS for 3+ parallel tasks, SOLO for sequential work
3. **State persistence** — PIPELINE.md survives compaction, enables resumption
4. **Decisions log** — captures key decisions with dates for traceability

### Gaps for Full-Project Pipelines
1. **No quality gates** — no automated check between phases (e.g., "did Phase 3 actually delete all skills?")
2. **No rollback** — if Phase 3 breaks something, no mechanism to undo
3. **No conditional branching** — every pipeline is linear (Phase 1 → 2 → 3 → 4)
4. **No sub-pipelines** — can't nest a "template sync" mini-pipeline inside Phase 3
5. **No deploy integration** — pipeline ends at code; no path to server deployment
6. **Template sync is manual** — should be automatic for dual-location projects

### Metrics

| Metric | Value |
|--------|-------|
| Total phases | 4 |
| Agent Teams phases | 2 (Phases 1, 3) |
| Total agents spawned | 6 (4 research + 2 implementation) |
| Skills before | 44 |
| Skills after | 14 (6 essential + 8 useful) |
| Files modified | 15+ |
| Stale references found | 8+ files |
| Compaction events | 1 (between Phase 3 and 4) |
| Recovery success | Yes (resumed from `<- CURRENT`) |

---

## Recommendations for Next Pipeline

1. **Add template sync as explicit phase task** — any implementation that touches `.claude/` must also touch `shared/templates/new-project/.claude/`
2. **Add cross-reference check to implementation agents** — grep for deleted/renamed items before reporting complete
3. **Consider quality gate between phases** — automated verification script that runs between phases
4. **For full-project pipelines** — need conditional branching (if tests fail → fix phase, not next phase) and sub-pipeline nesting
