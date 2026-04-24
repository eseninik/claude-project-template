# Active Context

> Session bridge. Agent reads at start, updates at end. Max ~150 lines.
> Old sessions → `.claude/memory/archive/`

**Last updated:** 2026-04-24

---

## Current Focus

### Codex Primary Implementer Pipeline — PIPELINE_COMPLETE 2026-04-24
**Goal:** GPT-5.5 via Codex CLI as primary code implementer; Opus as planner + reviewer + memory keeper. Level 2 + Level 3 together. Local-to-this-project only until PoC validates on other boats.

**Status:** End-to-end validated. Two live dual-implement rounds completed. 9 bugs found and fixed surgically. Speed layer added. All 98 unit tests green.

**Key artifacts (local scope, NOT synced to new-project template yet):**
- `.claude/scripts/codex-implement.py` (1120 lines) + 38 tests — single-task Codex executor
- `.claude/scripts/codex-wave.py` (582 lines) + 23 tests — parallel launcher (architectural-ready, not yet live-exercised)
- `.claude/scripts/codex-scope-check.py` (274 lines) + 23 tests — diff ↔ fence validator with `@path` file-mode prefix
- `.claude/hooks/codex-gate.py` extended + 14 tests — recognizes task-result.md as valid opinion
- `.claude/skills/dual-implement/SKILL.md` — Level 3 orchestration
- `.claude/adr/adr-012-codex-primary-implementer.md` — decision record
- `.claude/shared/work-templates/phases/{IMPLEMENT-CODEX,IMPLEMENT-HYBRID,DUAL-IMPLEMENT}.md` — phase-mode docs
- `.claude/shared/work-templates/task-codex-template.md` — extended task-N.md format
- `AGENTS.md` at repo root — shared Codex project_doc context (auto-loaded, ~40% prompt shrink)
- Project `CLAUDE.md` — new opt-in section "Codex Primary Implementer (Experimental, Local)"

**Live validations performed:**
- PoC on gpt-5.5: status=pass, all tests passing
- PoC on gpt-5.5 via chatgpt backend-api route: status=pass
- Dual-1 (task-dual-1, add --json): bugs #7/#8/#9/#11 surfaced, Claude won by default
- Dual-2 (task-dual-2, add --sort-by): both sides PASS with valid diffs, Claude won on merit (logging-standards + style consistency + docstring quality)

**Speed layer:**
- `speed_profile: fast | balanced | thorough` frontmatter + `--speed` CLI flag
- Default `balanced` (reasoning=medium) — halves runtime vs old `high` default
- Precedence: `--reasoning` > `--speed` > FM `reasoning` > FM `speed_profile` > default
- AGENTS.md shared context cuts prompt size ~40%

**Critical gotchas surfaced (see knowledge.md):**
- GPT-5.5 via CLI blocked for ChatGPT accounts on default `openai` provider → use `chatgpt` provider route
- Codex prompts via stdin not argv on Windows (cmd.exe quoting kills markdown)
- Codex sandbox lacks `py -3` → use `python` in Test Commands
- `codex-scope-check.py --fence` needs explicit `@` prefix for file mode
- `codex-implement.py` preflight refuses dirty tree (rollback would destroy user work)

**Git tags (checkpoint trail):**
pipeline-checkpoint-PLAN → IMPLEMENT_WAVE_1 → IMPLEMENT_WAVE_2 → POC_FAIL → POC_FIX_v1 → POC_SUCCESS_GPT55 → POST_DUAL1_FIXES → DUAL2_COMPLETE → PIPELINE_COMPLETE

**What's next (future sessions):**
- `codex-wave.py` smoke test with 2 parallel tasks (architectural-ready)
- Propagation to new-project template + other bot projects via fleet-sync
- Iteration memory mechanism (`## Iteration History` section) automated when Opus re-runs same task

---

### Watchdog Дnushnost Fix — COMPLETE (branch: `fix/watchdog-dushnost`)
**Problem:** Codex Watchdog давал 10+ итерационные циклы ложных пробуждений. Два live FP пойманы за одну сессию: (1) «Linear MCP works with caveat» триггернул по словам works+fails; (2) codex-gate заблокировал write на 5 edits (by-design, не часть проблемы).

**Root cause (confirmed via evidence in session):**
1. `codex-watchdog.py` не имел state-файла между вызовами — каждое Stop заново видело те же триггеры.
2. Pre-filter keywords были слишком широкие (`bug/error/ошибк/fail` + любое action word = trigger).
3. Единственный канал реакции = блокировка Claude (exit 2 + asyncRewake). Нюансированные вердикты форсились в HALT.
4. Codex сам в `.codex/reviews/latest.json` пометил over-blocking как BLOCKER в старой реализации `codex-review.py` (уже не wired).

**Solution (4 слоя):**
- **L1 Severity triage**: HALT (exit 2, ~3-5%) / WARN (stdout systemMessage, ~15%) / OBSERVE (file log, ~80%). HALT требует confidence ≥ 0.85.
- **L2 State memory**: `.codex/watchdog-state.json` — sig dedup (3 last wakes), topic dedup (downgrade after 2 HALTs на ту же тему), post-HALT cooldown (следующие 3 Stops cap'ятся до WARN).
- **L3 Task-class detector**: новый `session-task-class.py` хук на UserPromptSubmit — regex-классифицирует prompt в chat/typo/bugfix/feature/refactor/deploy. `chat` → watchdog skip entirely. `bugfix` → только HALT.
- **L5 Slash command**: `/watchdog status|strict|normal|off|class X` через `.codex/task-class-override` JSON.

**NOT changed (scope discipline):** `codex-gate.py`, `codex-broker.py`, `task-completed-gate.py` — user подтвердил что это by-design parallel Codex review, не часть проблемы.

**Files:** `.claude/hooks/codex-watchdog.py` (rewrite 255→456), `.claude/hooks/session-task-class.py` (new 195), `.claude/hooks/test_watchdog_fix.py` (new 277, 30/30 pass), `.claude/commands/watchdog.md` (new), `.claude/hooks/hook_base.py` (+session-task-class в profile), `.claude/settings.json` (wire UserPromptSubmit). Всё синхронизировано в new-project template.

**Not done (follow-up):** fleet-sync на 13 bot проектов требует отдельного user approval. Layer 4 (gate consolidation через broker cache) отложен — это перф-оптимизация, не душнота.

---

### Autoresearch Integration (Bayram Annakov → experiment-loop) — PARTIALLY VERIFIED (not deployment-ready)
**Task:** Evaluate Bayram Annakov's MIT-licensed autoresearch skill (github.com/BayramAnnakov/ai-native-product-skills) and integrate useful pieces into our existing `experiment-loop` skill.

**Status clarification (per Codex watchdog 2026-04-19):** All 8 files written + unit-level behavioral tests pass (28/28). End-to-end `claude -p` smoke test, canary validation on a real bot, and Windows SIGINT verification are NOT done. Work is reproducible from tests but NOT certified for rollout.

**What was done (session 2026-04-19):**
- Cloned + security-audited Bayram's 8-file autoresearch skill (MIT)
- Codex 4-way consultation (Option C confirmed: evolve experiment-loop + add references/)
- Fixed false-positive merge-conflict detection in `task-completed-gate.py` hook (now requires exact 7-char marker or marker+space, not `=======+` prefix)
- Ported 5 reference files: `triage-checklist.md`, `fitness-design.md` (7 reqs incl. compliance audit), `modes.md` (5 modes), `plateau-ideation.md` (revert mining + taxonomy coverage), `anti-patterns.md` (16 failure modes)
- Wrote 3 templates: `goal.md`, `iteration-prompt.md`, `loop-driver.py` (Python cross-platform, 315 lines, structured logging, direction-aware plateau, SIGINT handler, resume mode)
- Upgraded `experiment-loop/SKILL.md` (219→302 lines) with 5-stage flow (intake/triage/fitness/mode/loop+postmortem)
- Synced global + new-project template (8 files, ~75KB)
- Auto-fixed Codex-found bug: `best_metric` initialization on `--resume` now scans entire journal for best kept metric + baseline fallback

**Decisions (user-delegated autonomy):**
- Loop driver **Python** (not bash) — cross-platform, structured logging
- Permission mode **acceptEdits** default (not bypassPermissions) — auditable
- Triage **BLOCKING** with explicit `override: force + mandatory reason`
- Single **EXPERIMENT** phase with internal checklist (not 5 sub-phases) — avoids bureaucracy

**Files:** `.claude/shared/templates/new-project/.claude/skills/experiment-loop/**` + `~/.claude/skills/experiment-loop/**` + hook fix in `.claude/hooks/task-completed-gate.py` + pipeline tracker in `work/autoresearch-integration/PIPELINE.md` + daily log `.claude/memory/daily/2026-04-19.md`

**Not done (follow-up for user approval):** fleet sync to 13 bot projects. Global + new-project template is primary source per "single source of truth" convention.

### Karpathy Behavioral Rules Integration — COMPLETE
**Task:** Evaluate andrej-karpathy-skills repo (40K stars) and selectively adopt useful principles.

**What was done (session 2026-04-16):**
- Cloned and analyzed forrestchang/andrej-karpathy-skills (4 principles, ~60 lines)
- Full comparison with our 597-line CLAUDE.md + 22 skills system
- Codex second opinion obtained (agrees: "adopt principles, not repo")
- Adopted 2 of 4 principles into global ~/.claude/CLAUDE.md:
  1. **Think Before Coding** (new ### 1) — surface assumptions, ask if unclear
  2. **Surgical Changes** (new ### 2) — every changed line traces to request
- Renumbered existing rules (Logging→3, Auto-Fix→4, Codex→5)
- Added to Summary instructions (THINK FIRST, SURGICAL)
- Added to FORBIDDEN list (silent interpretation, drive-by refactoring)
- NOT adopted: Simplicity First (already in system prompt), Goal-Driven (our gates are deeper)

**Decisions:**
- Principles as GLOBAL HARD RULES, not as separate skill (Codex recommendation)
- Placed BEFORE Logging/Auto-Fix — behavioral rules fire before implementation rules

### MemPalace Cherry-Pick Integration — COMPLETE
**Task:** Adapt 3 components from MemPalace (github.com/milla-jovovich/mempalace).

**What was done (session 2026-04-08, part 2):**
- Analyzed MemPalace repo (8,580 lines, 96.6% LongMemEval)
- Cherry-picked via 3 parallel agents:
  1. SQLite Knowledge Graph (559 lines) — temporal triples, CLI
  2. Semantic Search (17K) — ChromaDB, optional dependency
  3. 4-Layer Context Loading (370 lines) — 93% token savings (610 vs 8,739 tokens)
- Fleet synced to 13 projects + global + template

**Decisions:**
- ChromaDB optional, grep fallback. KG replaces Graphiti (SQLite, zero deps).
- AAAK dialect and Palace metaphor NOT adopted.

### Webinar Insights Integration — COMPLETE
**Task:** Analyze "Inside the Agent" webinar (Bayram Annakov) and implement improvements.

**What was done (session 2026-04-08):**
- Analyzed webinar transcript (Claude Code architecture patterns, 60+ min)
- Identified 6 actionable improvements, prioritized P0-P3
- Implemented ALL 6 via Agent Teams (4 parallel agents, ~3 min total):
  1. **QA Evaluator Fresh Context** — reviewer no longer receives prior feedback (prevents bias)
  2. **Tool Verification Harness** — coder uses compile/typecheck instead of re-reading files
  3. **Microcompact Instructions** — agents summarize large tool outputs (>200 lines)
  4. **Phase Transition Reminders** — wave boundary context injection in IMPLEMENT phase
  5. **Memory Consolidation Skill** — new skill for background knowledge dedup/cleanup
  6. **KAIROS Heartbeat Pattern** — proactive agent guide + knowledge entry
- Synced all changes to new-project template (7 files)
- Global qa-validation-loop SKILL.md updated with Fresh Context Rule

**Decisions:**
- Evaluator WITHOUT memory of prior feedback — prevents confirmation bias (from Generator-Evaluator pattern)
- Compile-verify instead of re-read — reduces agent turns by ~10x (from Akim Khalilov's case study)
- KAIROS is documented as pattern, not implemented as daemon — token cost too high for current usage
- Memory consolidation as skill (not hook) — user-triggered, not automatic

### ECC Cherry-Pick Integration + Quality Fixes — COMPLETE
**Task:** Import best components from everything-claude-code, fix all quality gaps, fleet deploy.

**What was done (session 2026-03-31):**
- Analyzed ECC repo (136 skills, 28 agents, 60 commands) — 4 parallel Explore agents
- Imported 13 skills: tdd-workflow, api-design, coding-standards, e2e-testing, docker-patterns, deployment-patterns, backend-patterns, frontend-patterns, continuous-learning, cost-aware-llm-pipeline, database-migrations, security-review, learn-eval
- Created 4 language rule packs: Python, TypeScript, Go, Rust
- Created agentic-security.md guide (417 lines, adapted from ECC's 28KB security guide)
- Created config-protection.py hook (PreToolUse, blocks linter weakening)
- Created hook profiles system (minimal/standard/strict + CLAUDE_DISABLED_HOOKS)
- Added should_run() gate to all 9 hooks
- Created 3 JSON schemas + validate-configs.py (16 PASS, 0 FAIL)
- Created /learn-eval command + skill (continuous learning loop)
- Added 5 build-error-resolver agent types to registry.md
- Added ## Related cross-references to all 13 new skills
- Fixed MCP connection (.mcp.json with type:url transport)
- Fixed Codex wrapper retry logic (2 attempts on model refresh timeout)
- Fixed codex-review.py: IMPORTANT→non-blocking, sensitive file detection, summary.has_blockers→findings-derived
- Fixed config-protection.py: deletion-based loosening (Edit old_string + Write on-disk comparison)
- Fixed 3 hooks missing os import (tool-failure-logger, task-completed-gate, truthguard)
- Fixed git pre-commit (single-line NOTE, grep -cF) + post-commit (|| true, ${:-0})
- Synced 8 skills to Codex ~/.codex/skills/ — verified Codex uses them in reviews
- Codex found 5 real BLOCKERs across 3 reviews — all fixed
- 16/16 runtime tests PASS
- Fleet synced to 10 projects (9 bots + Freelance) + template
- RTK verified: 85.4% token savings, 575K tokens saved

**Decisions:**
- ECC целиком не внедряем — cherry-pick лучших компонентов
- Codex skills: только reviewer-relevant (8 из 13), не все
- Hook profiles: standard by default, minimal для быстрых сессий
- codex-review.py: only BLOCKERs block, IMPORTANT→stderr info

### Previous: Codex CLI Full Integration — COMPLETE
**Task:** Integrate OpenAI Codex CLI as parallel advisor + post-review verifier for Claude Code.

**What was done (session 2026-03-30):**
- Installed `@openai/codex` CLI v0.117.0 globally (npm)
- Fixed `codex-review.py` hook — v0.117.0 flags, structured logging, untracked files detection
- Added Stop hook to `settings.json`
- Updated `codex-integration.md` guide — v0.117.0 flags, Parallel Advisor architecture
- Created `~/.codex/config.toml` (model=gpt-5.5)
- Created 2 Codex global skills: `code-review-standards`, `project-conventions`
- Deployed `cross-model-review` skill to main project + global (`~/.claude/skills/`)
- Updated `~/.claude/skills/INDEX.md` with cross-model-review entry
- Updated `~/.claude/CLAUDE.md` — Hard Rule #3, AUTO-BEHAVIORS, HARD CONSTRAINTS, triggers, knowledge
- Fixed CLI flags in qa-validation-loop and verification-before-completion skills
- E2E tested: structured JSON output from Codex gpt-5.5 works, schema validates
- Codex found real bug (untracked files invisible to hook) — fixed immediately
- Used Agent Teams (5 parallel agents Wave 1, then Wave 2 sequential)
- Fleet synced to 11 projects (6 parallel agents): 10 bots + Freelance — all verified OK
- Updated init-project command with Step 8.5: Codex Integration Setup
- Updated new-project template with all Codex files (hook, guide, schema, settings, skills)

**Decisions:**
- Model: always gpt-5.5 (user preference, Plus subscription)
- Codex = read-only verifier, NEVER modifies code
- Stop hook REMOVED — was blocking UI for 60-90 seconds waiting for Codex response
- Replaced with UserPromptSubmit hook (parallel, non-blocking) — `codex-parallel.py` runs in background on every user request, writes opinion to `.codex/reviews/parallel-opinion.md`
- `codex-parallel.py` = primary hook (always active, automatic)
- `codex-review.py` = available for explicit skill invocation only (cross-model-review skill)
- Dual-mode: Mode 1 (Parallel Advisor via UserPromptSubmit) + Mode 2 (Deep Code Review via explicit skill)
- `codex exec` (not `codex exec review`) for structured JSON output with `--output-schema`
- `--full-auto` replaces old `--ask-for-approval never` (v0.117.0 change)

### Logging Standards Integration — COMPLETE
**Task:** Add mandatory structured logging to all code produced by our development system.

**What was done (session 2026-03-12):**
- Created `.claude/guides/logging-standards.md` (290 lines) — comprehensive guide with Python + Node.js patterns
- Updated `coder.md` — added Step 3.5: Add Logging + Self-Critique row + Quality Checklist items
- Updated `verification-before-completion/SKILL.md` — logging in Common Failures, Stub Detection, Goal-Backward, new Logging Verification section
- Updated `qa-validation-loop/SKILL.md` — Logging Coverage Review section with checklist + severity table, updated depth behaviors
- Updated `CLAUDE.md` — LOGGING in Summary, one-liners, HARD CONSTRAINTS, TRIGGERS, KNOWLEDGE, FORBIDDEN
- Updated `teammate-prompt-template.md` — logging in Verification Rules, Minimum Requirements, Anti-Patterns
- Synced all 6 files + new guide to new-project template (7 files total)
- Used Agent Teams (5 parallel agents) for IMPLEMENT phase
- Fleet synced to 10 bot projects (5 parallel agents, 2 bots each) — all verified

**Decisions:**
- Logging is a HARD CONSTRAINT, not a recommendation — enforced at write, review, and verify stages
- Missing logging in new code = CRITICAL QA finding
- Guide covers Python (structlog/stdlib) + Node.js (pino) with concrete examples
- No sensitive data in logs (passwords, tokens, PII)

### Autoresearch Integration (4 Features) — COMPLETE
**Task:** Analyze Karpathy's autoresearch + agenthub, extract useful patterns, integrate into our development system.

**What was done (session 2026-03-11):**
- Analyzed autoresearch repo, agenthub branch, moltbook, Reddit post, agent harness concept via 4 parallel research agents
- Identified 4 integrable patterns (experiment loop, evaluation firewall, unlimited self-completion, results board)
- Implemented all 4 via Agent Teams (4 parallel implementation agents)
- Safety verified unlimited self-completion with 3 independent review agents (all SAFE)
- QA reviewed all changes (PASS, 0 CRITICAL, 1 MINOR fixed)
- Synced to new-project template + 10 bot projects (5 parallel sync agents)

**New files created:**
- `.claude/skills/experiment-loop/SKILL.md` (213 lines) — autonomous hypothesis→experiment→measure→keep/discard loop
- `.claude/guides/results-board.md` (133 lines) — shared agent coordination board

**Files modified:**
- `self-completion/SKILL.md` — added unlimited mode with 5 safety valves (context 75%, timeout 4h, idle 3, stall 3, checkpoint 10)
- `qa-validation-loop/SKILL.md` — added Evaluation Firewall section
- `teammate-prompt-template.md` — added Read-Only Files + Results Board sections
- `registry.md` — added `experimenter` agent type
- `CLAUDE.md` — added experimenter role, evaluation firewall constraint, results board trigger, experiment-loop trigger
- `PIPELINE-v3.md` — added optional EXPERIMENT phase template

**Decisions:**
- Evaluation Firewall is prose-based (like Karpathy), enforced via QA reviewer check
- Unlimited self-completion uses defense-in-depth: 5 independent valves, any one stops the loop
- Results Board is append-only shared file, not a server (simpler than AgentHub)
- Rejected: AgentHub server, moltbook pattern, prose-only guardrails (we keep enforcement)

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

## Auto-Generated Summaries

### 2026-04-24 18:41 (commit `7fa7e6c`)
**Message:** codex-primary-v2: DUAL_TEAMS phase doc + AGENTS.md dual contract notice
**Files:** 2


### 2026-04-24 18:39 (commit `0625fa0`)
**Message:** codex-primary-v2: bootstrap enforcer stub + T1 full spec
**Files:** 2


### 2026-04-24 18:35 (commit `523ee6c`)
**Message:** codex-primary-v2: CLAUDE.md — Always-Dual protocol (MANDATORY, blocking)
**Files:** 1


### 2026-04-24 17:24 (commit `b5e1bad`)
**Message:** wave-smoke: 2 tiny task specs for codex-wave.py parallel live test
**Files:** 2


### 2026-04-24 17:22 (commit `1dd89dd`)
**Message:** codex-primary: automated iteration memory via --iterate-from
**Files:** 2


### 2026-04-24 16:52 (commit `83d564f`)
**Message:** pipeline: mark PROOF_OF_CONCEPT status PASS (was stale PENDING)
**Files:** 1


### 2026-04-24 16:47 (commit `995c5ff`)
**Message:** codex-primary: speed layer + AGENTS.md shared context
**Files:** 2


### 2026-04-24 16:39 (commit `d55a8df`)
**Message:** dual-2: judgment + archive of loser diff
**Files:** 4


### 2026-04-24 16:31 (commit `f36334a`)
**Message:** dual-2: spec with python (not py -3) to avoid sandbox Finding #10
**Files:** 1


### 2026-04-24 16:30 (commit `b407c3a`)
**Message:** codex-primary: fix 4 bugs surfaced by dual-1 live run
**Files:** 4


### 2026-04-24 16:22 (commit `89229ef`)
**Message:** dual-1: post-mortem + 3 new bugs + 2 findings from Level 3 live run
**Files:** 1


### 2026-04-24 16:07 (commit `4502d9a`)
**Message:** codex-primary: spec for Level 3 dual-implement live task (add --json to list_codex_scripts.py)
**Files:** 1


### 2026-04-24 15:05 (commit `1dede16`)
**Message:** codex-primary: recreate task-PoC.md (previously wiped by rollback)
**Files:** 1


### 2026-04-23 09:44 (commit `762d52a`)
**Message:** pipeline-checkpoint-IMPL+TESTS: severity-graded watchdog + classifier + tests
**Files:** 6


### 2026-04-23 09:34 (commit `0135b5f`)
**Message:** pipeline-checkpoint-SPEC: freeze watchdog-fix spec + FP corpus
**Files:** 3


### 2026-04-19 23:49 (commit `684b43f`)
**Message:** docs(autoresearch): finalize quarantine state + expanded stub validation matrix
**Files:** 6


### 2026-04-08 19:36 (commit `6140173`)
**Message:** fix: dedup chunks in semantic-search indexer (ChromaDB DuplicateIDError)
**Files:** 1


### 2026-03-17 16:58 (commit `20a9f28`)
**Message:** feat: agent memory mandatory + re-verify loop + skill-development removed
**Files:** 8


### 2026-03-17 16:49 (commit `a108a85`)
**Message:** feat: global skills migration + mandatory phases tested + skill evolution examples
**Files:** 5


> Агент НЕ обновил память. Интегрировать при следующей сессии.

### 2026-03-17 16:31 (commit `597820a`)
**Message:** feat: compress CLAUDE.md 526→221 lines + mandatory pipeline phases + reference guides
**Files:** 5

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


**[Pre-compaction save 17:17]** Successfully deployed all 8 bots to Contabo (7 migrated + client-bot), verified commits match source, and updated CI/CD pipelines (GitHub secrets + deploy.yml) for all repos. Resolved d-brain commit mismatch (unpushed EC2 commits) and fixed SSH key formatting in GitHub secrets.


> [4 older session(s) archived — see daily/ logs]

**[Pre-compaction save 12:40]** Diagnosed and fixed chronic autocompact failure in DocCheck Bot project. Identified that PreCompact hook was failing silently, preventing context cleanup before 85% threshold. Replaced broken hook with working version from another bot.


**[Pre-compaction save 21:44]** Диагностировал и исправил баг в OpenClaw — проблема была в `execFileUtf8`, который переписывал пустой stderr сообщением Node.js вместо реального вывода systemctl. Применил патч в коде, установил daemon и запустил gateway. Теперь OpenClaw полностью работает на сервере (слушает 127.0.0.1:18789), Telegram бот подключён, включены группы и получен pairing code для привязки.


**[Pre-compaction save 19:23]** Successfully diagnosed and fixed OpenClaw node-gateway connectivity issue. Node was missing `OPENCLAW_GATEWAY_TOKEN` in environment variables, preventing authentication. Added token, restarted services, and confirmed node is now connected and paired with gateway (capabilities: browser, system). Telegram bot (@genrihclawbot/"Gosh") is operational and connected to gateway.


**[Pre-compaction save 20:35]** Completed full 5-phase Skill Conductor pipeline (INSTALL → UPGRADE → VALIDATE → OPTIMIZE → SYNC) with 13 skills upgraded to 55% smaller size and F1 trigger scores improved from 0.87→0.97. Conducted deep analysis of molyanov-ai-dev repository identifying 6 integration opportunities.

### GSD Framework Integration — COMPLETE
**Task:** Analyze GSD (Get Shit Done) framework, identify improvements, integrate 9 features into our system, sync to all bots.

**What was done (2026-03-05):**
- Cloned + analyzed GSD repo (38,600 lines, 32 slash commands, 12 agents)
- Compared architectures: GSD is fresh-context executor model, ours is persistent-context pipeline model
- Identified 9 adoptable features across 3 tiers

**Tier 1 (Core Skills):**
- Goal-Backward Verification + 3-Level Artifact Check → verification-before-completion (181→280 lines)
- Wave-Based DAG Enhancement → task-decomposition (182→316 lines, formal DAG + XML tasks + decimal phases)
- Nyquist Pre-Flight Validation → qa-validation-loop (113→221 lines, requirement-to-test mapping)

**Tier 2 (Workflow):**
- Formalized Checkpoints (human-verify/decision/human-action) → PIPELINE-v3.md
- Discuss-Phase Decision Capture → new guide (discuss-phase-decisions.md, 140 lines)
- Quick Mode → new guide (quick-mode.md, 105 lines)

**Tier 3 (Templates):**
- Decimal Phase Numbering → PIPELINE-v3.md + task-decomposition
- XML Task Structure → task-decomposition
- Health Command → new command (health.md, 76 lines) + guide (health-check.md, 80 lines)

**QA fixes:**
- Added `dag-analyzer` + `nyquist-auditor` agent types to registry
- Fixed health command `--repair` flag → "say repair"
- Fixed duplicate rule 9. → 9b. in PIPELINE-v3
- CLAUDE.md: 7 targeted edits (summary rules, guides, skills, knowledge locations, constraints, blocking rules, role mapping)

**Synced to:**
- New-project template (9 files)
- 9 bot projects × 9 files = 81 file copies (all verified)

**Pipeline:** IMPLEMENT_W1(5 agents) → IMPLEMENT_W2(3 agents) → INTEGRATE → QA_REVIEW(3 agents) → FIX → TEMPLATE_SYNC → FLEET_SYNC → COMPLETE
