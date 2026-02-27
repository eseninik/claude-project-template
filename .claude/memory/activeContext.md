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


**[Pre-compaction save 20:39]** Completed IMPLEMENT and TEST phases of skill auto-discovery system. Built `generate-prompt.py` (280-line stdlib script) that auto-discovers skills via `roles:` YAML field, validated it across 3 test agents (coder, qa-reviewer, pipeline-lead), and synced the generator + 13 updated skills to all 8 production bots (56/56 checks pass).


**[Pre-compaction save 21:03]** Built and tested a complete autonomous agent spawning pipeline (`spawn-agent.py`) with auto-detection of agent types based on task keywords. Implemented 7 critical fixes (word boundary matching, null checks, Russian language support, role mappings, BOM handling, dry-run guards) after parallel testing revealed edge cases and false positives.

### 2026-02-27 (session 8 — E2E Infrastructure Validation COMPLETE)
**Did:** (1) Completed Phase 2 TEST_AGENT_TEAMS — all 3 agents PASS (verifier 13/13, mapper 7-step map, error-handler 2 recoveries). (2) Fixed conflict marker false positives in template copy of subagent-driven-development. (3) Synced conflict marker fix to 8 bots. (4) Completed Phase 3 TEST_AO_HYBRID — 2 AO agents spawned, both produced outputs and git commits. (5) Wrote Phase 4 VERIFY summary. (6) Pipeline COMPLETE.
**Decided:** AO Hybrid spawns work but have 3 concerns: stale branch reuse, no skill invocation audit trail, global/project skill confusion. Future prompts should include "Report which skills you invoked."
**Learned:** (1) Quality gate hook matches exactly 7-char conflict markers (`"<" * 7`), so 4-char shortened examples pass. (2) AO worktrees can reuse existing branch names from previous sessions → stale code. (3) AO agents see both project and global skills. (4) Agent 2 found 13 phantom skills in SKILLS_INDEX.md and 15 orphaned skills without triggers.
**Next:** All E2E issues addressed and verified. System is stable. Consider future: AO Hybrid production use, skill compliance monitoring.

### 2026-02-27 (session 9 — E2E v2 Verification COMPLETE)
**Did:** (1) Resumed VERIFY phase of Post-E2E Improvements pipeline. (2) Spawned 3 parallel agents: index-verifier, ao-verifier, skills-verifier. (3) All 3 PASS.
**Next:** Build prompt generator for skill auto-discovery.

### 2026-02-27 (session 10 — Prompt Generator COMPLETE)
**Did:** (1) Built `generate-prompt.py` (280 lines, stdlib only) — auto-discovers skills via `roles:` YAML field. (2) Added `roles:` to all 13 skill YAML front matters. (3) Updated CLAUDE.md with generator rule. (4) TEST phase: 3 agents (coder, qa-reviewer, pipeline-lead) each correctly received their skills and followed protocols. (5) Fixed BOM handling for Windows. (6) Synced to template + 8 bots (56/56 checks pass).
**Decided:** Auto-discovery via YAML `roles:` field — adding a new skill requires only creating SKILL.md with `roles:`, no other files to edit. Generator reduces teammate prompt creation from 5 steps to 1.
**Learned:** (1) Prompt generator eliminates the multi-step compliance problem — 1 command produces a complete prompt with correct skills, memory, and handoff template. (2) qa-reviewer agent correctly identified BOM handling and registry parsing fragility. (3) pipeline-lead agent created a realistic 3-agent plan showing the generator integrates naturally into workflows.
**Next:** Build spawn-agent.py — one-command spawning with auto-type detection.

### 2026-02-27 (session 11 — spawn-agent.py + Full Flow Automation COMPLETE)
**Did:** (1) Built `spawn-agent.py` (406 lines) — auto-detects agent type from task keywords, imports generate-prompt.py. (2) TYPE_RULES: 16 agent types with EN+RU keywords, confidence scoring, word-boundary matching. (3) TEST phase: 3 parallel agents (skill verifier, code reviewer, edge tester) — found 6 issues. (4) ITERATE: fixed all 6 (word boundaries, null checks, Russian "баг", qa-reviewer roles, BOM strip, dry-run guard). (5) EVALUATE: "does everything work automatically?" → YES. (6) SYNC: 8 parallel agents synced spawn-agent.py + generate-prompt.py + verification SKILL.md + CLAUDE.md to all 8 bots — 32/32 checks pass.
**Decided:** spawn-agent.py as MANDATORY (not PREFERRED) in CLAUDE.md Before Spawning Teammate. Word boundary regex (`\b`) prevents substring false positives. Fallback to `coder` when score ≤ 0.
**Learned:** (1) Substring matching causes false positives ("fix" in "fixture", "add" in "address"). (2) Generic keywords like "code" and "change" cause cross-type detection collisions. (3) qa-reviewer was missing from verification-before-completion roles — a gap that affects skill routing.
**Next:** System fully automatic. Pipeline COMPLETE.

> [7 older session(s) archived — see daily/ logs]