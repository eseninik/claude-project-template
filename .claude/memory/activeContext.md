# Active Context

> Session bridge. Agent reads at start, updates at end. Max ~150 lines.
> Old sessions → `.claude/memory/archive/`

**Last updated:** 2026-02-27

---

## Current Focus

### Bot Fleet Sync — COMPLETE
**Task:** Commit template changes + sync all updates to 8 bots via Agent Teams (8 parallel agents).

**What was done:**
- Committed 76 files (+10,721 lines) to template project
- Discovered 8 bots with `.claude/` dirs, 2 without (skipped)
- Spawned 8 parallel agents (one per bot) via TeamCreate
- Each agent: copied generic files, merged CLAUDE.md, cleaned old hooks, verified, git committed
- Fixed template CLAUDE.md (was missing MEMORY DECAY section, HOOKS AUTO-INJECT, etc.)
- Final verification: ALL 8 bots pass — 0 file diffs, all skills match, MEMORY DECAY present, no old .sh hooks

**Bots synced:**
| Bot | Commit | Status |
|-----|--------|--------|
| Call Rate bot | 729423f | OK |
| ClientsLegal Bot | 437c7fb | OK |
| Conference Bot | 8c4b108 | OK |
| DocCheck Bot | 63217b3 | OK |
| LeadQualifier Bot | 794babf | OK |
| Legal Bot | 63d878c | OK (fixed project name) |
| Quality Control Bot | 11e0439 | OK |
| Sales Check Bot | 4a7c099 | OK |

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

### 2026-02-27 (session 2 — bot fleet sync)
**Did:** (1) Committed 76 template files (10,721 lines). (2) Discovered 8 bots + 2 non-bots. (3) Agent Teams: 8 parallel agents synced all bots. (4) Fixed template CLAUDE.md (missing MEMORY DECAY + HOOKS AUTO-INJECT). (5) Final verification: ALL 8 bots pass — 0 diffs, all skills match, no old hooks.
**Decided:** Use main project CLAUDE.md as source of truth (not template) for bot sync. Each agent extracts project section and merges.
**Learned:** Agent Teams scale to 8 concurrent bots without issues. Legal Bot had wrong project name from copy-paste — agents can detect and fix. Template CLAUDE.md can drift behind main — always verify sync.
**Next:** Consider adding decay to PreCompact hook. Monitor bot sessions for decay tier changes in 2-3 weeks.

### 2026-02-27 (session 1 — memory decay integration)
**Did:** Ported memory-engine.py (537 lines), added verified: dates to knowledge.md, updated session-orient.py with tier labels, extended config.yaml. All 8 verification checks PASS.
**Learned:** Ebbinghaus decay prevents junk drawer. Graduated touch = natural spaced repetition. memory-engine.py target can be file OR directory.
**Next:** Sync to all bots (done in session 2).

### 2026-02-23
**Did:** Deep analysis of Athena-Public repo using Agent Teams (10 parallel agents).
**Decided:** Hybrid approach — adopt Athena's token efficiency + our agent teams.
**Learned:** Athena CLAUDE.md is 80 lines vs our 300. Agent Teams gave ~10x speedup.
**Next:** Implement Tier 1 recommendations.
