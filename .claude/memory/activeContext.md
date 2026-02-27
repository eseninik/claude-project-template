# Active Context

> Session bridge. Agent reads at start, updates at end. Max ~150 lines.
> Old sessions → `.claude/memory/archive/`

**Last updated:** 2026-02-27

---

## Current Focus

### Full Skills Restoration + Auto-Loading Mechanism — COMPLETE
**Task:** Restore full skill versions from git history, fix skill loading for all agent types, sync to 8 bots.

**What was done (session 6):**
- Restored 8 skills from git commit `51f6d45` to full size (43→425, 44→201, 35→338, 83→1440, 50→296, 83→601, 54→448, 46→140 lines)
- Merged AO Hybrid Mode section into restored `subagent-driven-development` (1424+16=1440 lines)
- Fixed `task-decomposition` YAML description: Russian → English (invisible to skill routing)
- Updated teammate-prompt-template.md: require full skill CONTENT embedding, not just names
- Updated CLAUDE.md: added SKILLS rule to Summary Instructions (survives compaction), split CONTEXT LOADING TRIGGERS into Guides (cat) vs Skills (Skill tool) with 13-skill trigger mapping
- Synced all 13 skills + template + CLAUDE.md to new-project template
- Synced to 8 bots via 8 parallel agents — all verified (1440 lines, SKILLS rule, trigger table)

**Decisions:**
- Only `task-decomposition` had Russian description (the other 12 skills already had English)
- `using-git-worktrees` (v2.1) and `verification-before-completion` (140 lines) needed no post-reduction merges
- Template CLAUDE.md and main CLAUDE.md get identical structural changes

**Learned:**
- Skills were reduced from ~5,000 to ~500 total lines in commit `f9e2556` (40 min after `51f6d45`)
- ~30-40% skill compliance was caused by: terse descriptions, no content in teammate prompts, skills listed as `cat` commands instead of Skill tool invocations
- TeamCreate subagents CAN'T use Skill tool — they need full content embedded in their prompt

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


**[Pre-compaction save 18:14]** Completed full 4-phase AO Hybrid E2E pipeline: synced all 8 bots (6/8 → 7/8 → 8/8), verified files match templates, confirmed fixed bracket-based status parsing works on Windows, committed template changes (commit `855636e`, +1715 lines).


**[Pre-compaction save 18:40]** Completed full E2E infrastructure validation: synced 13 skills to all 8 bots (100% success), then executed 3-phase test pipeline verifying skill loading (3/3 PASS with full content), Agent Teams execution (3 agents with embedded skills following protocols), and quality gate checks. Discovered and fixed false-positive merge conflict markers in documentation examples.



**[Pre-compaction save 19:15]** Executed a complete 5-agent parallel implementation phase (IMPLEMENT) to fix AO Hybrid E2E issues, then synced all changes to template + 8 bots (SYNC phase), and began E2E integration testing (VERIFY phase) to validate the fixes.

### 2026-02-27 (session 8 — E2E Infrastructure Validation COMPLETE)
**Did:** (1) Completed Phase 2 TEST_AGENT_TEAMS — all 3 agents PASS (verifier 13/13, mapper 7-step map, error-handler 2 recoveries). (2) Fixed conflict marker false positives in template copy of subagent-driven-development. (3) Synced conflict marker fix to 8 bots. (4) Completed Phase 3 TEST_AO_HYBRID — 2 AO agents spawned, both produced outputs and git commits. (5) Wrote Phase 4 VERIFY summary. (6) Pipeline COMPLETE.
**Decided:** AO Hybrid spawns work but have 3 concerns: stale branch reuse, no skill invocation audit trail, global/project skill confusion. Future prompts should include "Report which skills you invoked."
**Learned:** (1) Quality gate hook matches exactly 7-char conflict markers (`"<" * 7`), so 4-char shortened examples pass. (2) AO worktrees can reuse existing branch names from previous sessions → stale code. (3) AO agents see both project and global skills. (4) Agent 2 found 13 phantom skills in SKILLS_INDEX.md and 15 orphaned skills without triggers.
**Next:** All E2E issues addressed and verified. System is stable. Consider future: AO Hybrid production use, skill compliance monitoring.

### 2026-02-27 (session 9 — E2E v2 Verification COMPLETE)
**Did:** (1) Resumed VERIFY phase of Post-E2E Improvements pipeline. (2) Spawned 3 parallel agents: index-verifier (SKILLS_INDEX accuracy), ao-verifier (ao-hybrid.sh fixes), skills-verifier (global cleanup). (3) All 3 PASS — every criterion verified with evidence. (4) Wrote improvements-summary.md. (5) Pipeline PIPELINE_COMPLETE.
**Decided:** All 5 E2E v1 issues are resolved. Infrastructure is clean and verified.
**Learned:** Agent Teams with embedded verification-before-completion + "Skills Invoked:" handoff format produces reliable structured evidence. The 3-phase improvement pipeline (IMPLEMENT→SYNC→VERIFY) is a proven pattern for infrastructure fixes.
**Next:** System stable. Future work: AO Hybrid in production pipelines, skill compliance monitoring over time.

> [6 older session(s) archived — see daily/ logs]