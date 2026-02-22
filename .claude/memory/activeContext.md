# Active Context

> Session bridge. Agent reads at start, updates at end. Max ~150 lines.
> Old sessions → `.claude/memory/archive/`

**Last updated:** 2026-02-22

---

## Current Focus

### OpenClaw Memory System Analysis & Integration
**Pipeline:** `work/PIPELINE.md` | **Phase:** IMPLEMENT | **Status:** IN_PROGRESS

**Completed phases:**
1. **RESEARCH** — 3 parallel agents analyzed OpenClaw source code (18+ files) + own doc research
2. **COMPARE** — Comparison report + final recommendations approved by user

**Current IMPLEMENT tasks:**
- [x] Create knowledge.md (merged patterns + gotchas)
- [x] Create daily/ log system
- [x] Archive old activeContext.md entries
- [x] Delete dead files (session-insights/, codebase-map.json, patterns.md, gotchas.md)
- [x] Rewrite CLAUDE.md (346→311 lines, 8→4 session start, 9→2+3 after task)
- [x] Fix stale refs in 11 main files (3 agents: guides, prompts/agents/cmds, templates)
- [x] Sync new-project template (memory dir + all guides/prompts/agents/phases)
- [x] Final verification grep — ZERO stale memory path refs in .claude/
- [ ] Phase transition: commit, knowledge.md, daily log, Graphiti, advance PIPELINE

---

## Recent Decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-22 | SIMPLIFY + STRENGTHEN + ENRICH strategy | OpenClaw analysis shows our compliance is ~30-40% despite 40 rules |
| 2026-02-22 | Merge patterns.md + gotchas.md → knowledge.md | One file = higher compliance than two |
| 2026-02-22 | Add daily/ logs (OpenClaw pattern) | Chronological memory has lowest friction |
| 2026-02-22 | Session Start 8→4 steps, After Task 9→2+3 | Fewer mandatory steps = higher compliance |
| 2026-02-22 | Keep Graphiti without deletion deadline | Powerful tool, needs better enforcement |
| 2026-02-19 | Ralph Loop removed, features extracted | User never uses Ralph Loop; 3 patterns preserved |

---

## Session Log

### 2026-02-22 (current)
**Did:** Deep OpenClaw analysis (3 agents), comparison report, recommendations approved, started IMPLEMENT
**Decided:** Full implementation of SIMPLIFY + STRENGTHEN + ENRICH plan
**Learned:** OpenClaw's #1 advantage = programmatic enforcement (memory flush, context pruning). We can't replicate that but can simplify rules to boost compliance.
**Next:** Finish IMPLEMENT (CLAUDE.md rewrite is the big task), sync template, verify

### 2026-02-19
**Did:** Ralph Loop extraction pipeline (6 phases). Phase Transition Protocol integrated. Graphiti connected and verified.
**Decided:** Graphiti is ALWAYS available (no "if available" checks)
**Learned:** Phase Context Loading + insight extraction are the most valuable Ralph patterns
**Next:** OpenClaw analysis (now in progress)

### 2026-02-18
**Did:** Auto-Claude integration — 17 new files, 7 modified, template synced. Agent registry, typed memory, focused prompts, complexity assessment, recovery manager.
**Decided:** Always Opus 4.6. Typed memory as primary, Graphiti as enrichment.
**Learned:** Auto-Claude is sequential (1 subtask), our system is parallel (Agent Teams) — keep our approach
