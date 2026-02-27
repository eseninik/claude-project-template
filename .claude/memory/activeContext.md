# Active Context

> Session bridge. Agent reads at start, updates at end. Max ~150 lines.
> Old sessions → `.claude/memory/archive/`

**Last updated:** 2026-02-27

---

## Current Focus

### AO Hybrid E2E Test + Bot Fleet Sync — COMPLETE
**Task:** Fix AO runtime for Windows, E2E test AO Hybrid with real spawned agents, sync to 8 bots.

**What was done (session 5):**
- Fixed ao-hybrid.sh status parsing: bracketed `[spawning]` patterns instead of bare words matching "(no active sessions)"
- Fixed AO Windows runtime: 3 issues blocking spawned sessions:
  1. `process.exit(0)` in spawn.ts — CLI returns immediately after spawning
  2. `detached: true` + `windowsHide: true` — child process survives parent exit
  3. `shellEscape()` Windows fix — double quotes for cmd.exe instead of POSIX single quotes
  4. Prompt-to-file: writes long prompts to `.ao-task-prompt.md` in worktree, passes short reference via CLI
- Added `agentConfig.permissions: skip` to AO config for autonomous agent execution
- Fixed ao-hybrid.sh session ID parsing: uses `SESSION=<id>` line instead of greedy regex
- E2E test: spawned 2 agents via `ao spawn --prompt-file`, both completed tasks successfully
  - Task 1: Skills audit → found 34 skills, wrote report, committed
  - Task 2: Template diff → found 2 missing files + 1 diff, wrote report, committed
- Synced AO Hybrid changes to 8 bots via Agent Teams (8 parallel agents)
- Spot-check verification: 3 bots checked, all 8/8 files present, registry.md exact match

---

### AO Hybrid Integration (Stage 3) — COMPLETE
**Task:** Implement hybrid TeamCreate + AO model for single-project development. TeamCreate coordinates, AO-spawned sessions execute (full Claude Code with CLAUDE.md + skills + memory).

**What was done:**
- Added `--prompt` / `--prompt-file` flags to AO spawn CLI (spawn.ts)
- Created `ao-hybrid.sh` helper script (spawn/status/wait/collect/cleanup)
- Created `ao-hybrid-spawn` skill (186 lines, full protocol)
- Registered current project in `~/.agent-orchestrator.yaml` (9 projects total)
- Added `execution_engine` field to `config.yaml` (teamcreate/ao_hybrid)
- Updated 5 docs: subagent skill, autonomous-pipeline, PIPELINE-v3.md, CLAUDE.md, registry
- Added `ao-hybrid-coordinator` agent type to registry
- Synced all changes to new-project template (8 files)
- Rebuilt AO — `ao spawn --help` shows new flags, `ao status` shows 9 projects

**Critical discovery:** `ao send` bypasses runtime abstraction → calls tmux directly → broken on Windows. Solution: spawn-only model — pass complete task prompts via Claude Code's `-p` flag at launch time. No follow-up messages needed.

**Mode ecosystem (6 modes):**
| Mode | Scope | Handler |
|------|-------|---------|
| SOLO | Single agent | Direct execution |
| AGENT_TEAMS | Parallel, single project, lightweight | TeamCreate |
| AO_HYBRID | Parallel, single project, full context | ao spawn --prompt-file |
| AGENT_CHAINS | Sequential | Agent N → Agent N+1 |
| AO_FLEET | Parallel, multiple projects | ao spawn per project |
| SUB_PIPELINE | Nested | Referenced PIPELINE.md |

---

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

### 2026-02-27 (session 4 — AO Hybrid Stage 3)
**Did:** (1) Explored ao send architecture — discovered it bypasses runtime abstraction, calls tmux directly. (2) Discovered spawn-only model — ao spawn passes prompts via Claude Code `-p` flag, no tmux needed. (3) Added --prompt/--prompt-file flags to AO spawn CLI. (4) Created ao-hybrid.sh helper script (243 lines). (5) Created ao-hybrid-spawn skill (186 lines). (6) Updated 5 docs + registry + CLAUDE.md with AO_HYBRID mode. (7) Synced to template. (8) Rebuilt AO + verified.
**Decided:** Spawn-only model beats send-based architecture on Windows — no race conditions, no tmux dependency, no cross-process stdin issues. AO_HYBRID is a 6th pipeline mode alongside SOLO, AGENT_TEAMS, AGENT_CHAINS, AO_FLEET, SUB_PIPELINE.
**Learned:** (1) ao send CLI hardcodes tmux calls at lines 104/119/143/148 — bypasses runtime.sendMessage() entirely. (2) sessionManager.send() does route correctly through runtime plugin, but CLI doesn't use it. (3) Cross-process stdin is fundamentally impossible on Windows without a persistent broker (tmux is Unix's broker). (4) Claude Code's `-p` flag embeds prompt at launch time — no IPC needed.
**Next:** Sync AO_HYBRID changes to 8 bots. End-to-end test: spawn 2-3 agents via ao-hybrid.sh with real tasks. Fix ao-hybrid.sh status parsing (counts project headers as "active").


**[Pre-compaction save 16:38]** Completed a full hybrid agent spawning architecture implementation with 7 parallel tasks: added `--prompt` and `--prompt-file` flags to `ao spawn`, created the `ao-hybrid.sh` helper script, updated 16 documentation files across main project and template, synced template files, built and verified the system, and updated memory files. All verifications passed.

### 2026-02-27 (session 2 — bot fleet sync)
**Did:** (1) Committed 76 template files (10,721 lines). (2) Discovered 8 bots + 2 non-bots. (3) Agent Teams: 8 parallel agents synced all bots. (4) Fixed template CLAUDE.md (missing MEMORY DECAY + HOOKS AUTO-INJECT). (5) Final verification: ALL 8 bots pass — 0 diffs, all skills match, no old hooks.
**Decided:** Use main project CLAUDE.md as source of truth (not template) for bot sync. Each agent extracts project section and merges.
**Learned:** Agent Teams scale to 8 concurrent bots without issues. Legal Bot had wrong project name from copy-paste — agents can detect and fix. Template CLAUDE.md can drift behind main — always verify sync.
**Next:** Consider adding decay to PreCompact hook. Monitor bot sessions for decay tier changes in 2-3 weeks.



**[Pre-compaction save 15:55]** Completed Agent Orchestrator Stage 1 (AO CLI installed globally, Windows runtime plugin created, 8 bots configured) and Stage 2 (integrated AO_FLEET mode into pipeline system across 6 documentation files). Discovered that TeamCreate subagents don't automatically load skills, knowledge, or context despite having access to CLAUDE.md rules.

### 2026-02-27 (session 3 — AO install + Windows runtime)
**Did:** (1) Installed AO (pnpm monorepo) at C:\Bots\agent-orchestrator. (2) Created Windows runtime plugin (runtime-windows) — fork of runtime-process with taskkill /T /F instead of POSIX kill(-pid). (3) Fixed config: added required `repo` field (Zod schema). (4) Fixed cross-process liveness: isAlive()/destroy()/getAttachInfo() now fall back to `tasklist /FI "PID eq N"` when process isn't in in-memory map. (5) Full smoke test PASSED: ao status, spawn, session ls, session kill all work.
**Decided:** AO is complementary to our system (outer loop vs inner loop). Windows runtime needs PID-based cross-process detection because each `ao` CLI invocation is a separate Node.js process (unlike tmux server).
**Learned:** (1) Zod silent validation → "no config found" is a common UX trap. (2) AO's spawn.ts hardcodes "tmux attach" display regardless of runtime. (3) In-memory process maps don't survive across CLI invocations — need PID-based fallback on Windows.
**Next:** Sync AO_FLEET changes to all 8 bots. Consider end-to-end test: pipeline with AO_FLEET phase that actually spawns fleet across bots.

### 2026-02-27 (session 3 continued — Stage 2: AO_FLEET integration)
**Did:** (1) Created ao-fleet-spawn skill with full protocol (pre-flight, spawn, monitor, collect, cleanup). (2) Added AO_FLEET mode to PIPELINE-v3.md template (with example phase + execution rule). (3) Added AO_FLEET execution protocol to autonomous-pipeline.md (Section 4 + Quick Reference). (4) Added fleet-orchestrator agent type to registry.md (full tools, ao-fleet-spawn skill, deep thinking). (5) Updated CLAUDE.md: AO_FLEET section, trigger keywords (fleet, ao spawn, all bots, multi-repo), compaction recovery, role mapping, context loading, knowledge locations. (6) Synced all changes to new-project template (skill, registry, pipeline template, CLAUDE.md).
**Decided:** AO_FLEET is a pipeline mode (like AGENT_TEAMS), not a replacement for AGENT_TEAMS. They're complementary: AGENT_TEAMS for in-project parallelism, AO_FLEET for cross-project fleet operations.
**Learned:** Mode ecosystem now has 5 options: SOLO, AGENT_TEAMS, AGENT_CHAINS, AO_FLEET, SUB_PIPELINE. Each has clear trigger and execution protocol.
**Next:** Sync to 8 bots. Test end-to-end AO_FLEET pipeline.

### 2026-02-27 (session 1 — memory decay integration)
**Did:** Ported memory-engine.py (537 lines), added verified: dates to knowledge.md, updated session-orient.py with tier labels, extended config.yaml. All 8 verification checks PASS.
**Learned:** Ebbinghaus decay prevents junk drawer. Graduated touch = natural spaced repetition. memory-engine.py target can be file OR directory.
**Next:** Sync to all bots (done in session 2).

### 2026-02-23
**Did:** Deep analysis of Athena-Public repo using Agent Teams (10 parallel agents).
**Decided:** Hybrid approach — adopt Athena's token efficiency + our agent teams.
**Learned:** Athena CLAUDE.md is 80 lines vs our 300. Agent Teams gave ~10x speedup.
**Next:** Implement Tier 1 recommendations.
