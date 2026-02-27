# Active Context

> Session bridge. Agent reads at start, updates at end. Max ~150 lines.
> Old sessions → `.claude/memory/archive/`

**Last updated:** 2026-02-27

---

## Current Focus

### Memory Decay Integration — PIPELINE_COMPLETE
**Task:** Integrate Ebbinghaus forgetting curve from agent-memory-skill into our template.
**Source:** github.com/smixs/agent-memory-skill (1650 lines, 8 files)

**What was done:**
- 3 research agents analyzed: external repo, our memory system, comparative analysis
- Also analyzed Claude Code's built-in AutoMemory — determined it complements but doesn't replace our system
- 4 implementation agents in parallel: memory-engine.py, knowledge.md metadata, session-orient tiers, config.yaml
- Integration: CLAUDE.md updated with MEMORY DECAY section + search modes
- Sync: 3 files synced to new-project template
- All 8 verification checks PASS

**New components:**
- `.claude/scripts/memory-engine.py` (537 lines) — Ebbinghaus decay engine (10 commands)
- `knowledge.md` entries now have `verified:` dates driving tier assignment
- `session-orient.py` shows `[active]`/`[warm]`/`[cold]` tier labels per entry
- `ops/config.yaml` memory: section with decay_rate, tiers, search budgets
- CLAUDE.md search modes: heartbeat(2K) / normal(5K) / deep(15K) / creative(3K)

---

## Recent Decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-24 | Merge 3 upgrade phases into 1 parallel wave | All bots are in independent directories — no file conflicts |
| 2026-02-24 | Hook enforcement > instruction enforcement | Arscontexta analysis: hooks achieve ~100% compliance |
| 2026-02-24 | Warn-don't-block for write validation | Early detection without friction |
| 2026-02-24 | Observation Capture Protocol | Typed observations → batch review → knowledge promotion |
| 2026-02-27 | Integrate Ebbinghaus decay from agent-memory-skill | Prevents knowledge.md junk drawer; automatic tier assignment |
| 2026-02-27 | AutoMemory complements, doesn't replace hooks | AutoMemory = organic notes; hooks = compaction survival + compliance |
| 2026-02-27 | Decay rate 0.01 (research preset) | Slower than CRM (0.025); our projects run weekly, not daily |
| 2026-02-22 | SIMPLIFY + STRENGTHEN + ENRICH strategy | OpenClaw analysis shows compliance ~30-40% |

---

## Session Log

### 2026-02-27
**Did:** (1) Deep analysis of agent-memory-skill repo (3 parallel research agents). (2) Analyzed Claude Code AutoMemory docs — complements but doesn't replace our hooks. (3) Ported memory-engine.py (537 lines, 10 commands). (4) Added verified: dates to all 22 knowledge.md entries. (5) Updated session-orient.py with tier labels. (6) Extended config.yaml with memory decay params. (7) Added MEMORY DECAY section to CLAUDE.md with search modes. (8) Synced to template. All 8 verification checks PASS.
**Decided:** AutoMemory = organic notes (Layer 5), hooks = compliance (Layer 1-2), decay = forgetting (new). Three systems complement each other. Decay rate 0.01 (research preset, not CRM 0.025). Tiers: active(14d)/warm(30d)/cold(90d)/archive.
**Learned:** Ebbinghaus forgetting curve prevents knowledge.md junk drawer problem. Graduated touch (promote one tier, not reset to top) implements natural spaced repetition. Creative mode (random cold/archive) enables serendipity. memory-engine.py target arg can be file OR directory — need to handle both.
**Next:** 7 bots need memory-engine.py + updated hooks synced. Consider adding decay to PreCompact hook (auto-run after save).


**[Pre-compaction save 12:44]** Analyzed external memory architecture (agent-memory-skill, AutoMemory) and implemented a complete multi-layer memory system with decay mechanics. Built and tested a full pipeline using Agent Teams with 4 parallel agents, achieving 24/25 test passes. Integrated tiered search protocol, knowledge decay (Ebbinghaus), and session persistence into the project.

### 2026-02-23
**Did:** Deep analysis of Athena-Public repo using Agent Teams (10 parallel agents).
**Decided:** Hybrid approach — adopt Athena's token efficiency + our agent teams.
**Learned:** Athena CLAUDE.md is 80 lines vs our 300. Agent Teams gave ~10x speedup.
**Next:** Implement Tier 1 recommendations.
