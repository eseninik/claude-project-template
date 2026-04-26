# Changelog

All notable changes are tracked here. Release sections are anchored to `pipeline-checkpoint-*` tags and commit subjects use Conventional Commits-style titles where available.

## Round 8 (Z23)
### Changes
- Determinism 10/10.

## Round 8 (Z20)
### Changes
- Security 10/10.

## Round 8 (Z17)
### Changes
- Reliability 10/10.

## Round 8 (Z14)
### Changes
- Functional Coverage 10/10.

## Round 7 (Z12)
### Changes
- Y21 + Y25 close all initial Y18-Y25 follow-ups.

<!-- pipeline-checkpoint-changelog:start -->
## pipeline-checkpoint-SESSION-PAUSE-2026-04-25
### Changes
- session-pause: full resume context (Y6-Y17 chain + architecture + open follow-ups + relogin protocol)
- y17-live: Y15+Y16+Y17 codification + LIVE verified — PowerShell-first 8x faster than fighting harness

## pipeline-checkpoint-Y15Y16Y17_DONE
### Changes
- No commits recorded.

## pipeline-checkpoint-Y15Y16_DONE
### Changes
- fix-Y16/claude: embed Y14 PowerShell-first section in spawn-agent.py generated prompts (claude won 0.84 vs 0.43)
- fix-Y15/claude: codify Y14 PowerShell-first pattern in template + CLAUDE.md (TIE, claude won)
- y15+y16 specs: codify Y14 PowerShell-first pattern in template + spawn-agent.py

## pipeline-checkpoint-Y14_ARCHITECTURAL_FINDING
### Changes
- y14-finding: sub-agent Write structurally blocked by harness; codified PowerShell workaround as canonical pattern; reverted misleading Edit/Write wildcards
- y11-live spec: live verification of target-path sentinel fix

## pipeline-checkpoint-FOLLOWUPS_FINAL
### Changes
- knowledge: Y11 entry + 5-reader meta-pattern (chain Y6/Y7/Y8/Y9/Y10/Y11 closed)

## pipeline-checkpoint-Y11_FIX
### Changes
- fix-Y11: target-path sentinel detection (catches sub-agent CLAUDE_PROJECT_DIR=main)

## pipeline-checkpoint-E2E_COMPLETE
### Changes
- e2e: codex-cost-report + dual-history-archive (Claude won both)
- knowledge: Y10 harness UI denial — root cause + fix entry
- e2e specs: codex-cost-report + dual-history-archive (verify Y8/Y9/Y10 fixes)
- merge winners V-1 V-2 V-3 V-4 (Phase 2/3 dual-implement results)
- fix-Y10: explicit permissions.allow for sub-agent Edit/Write in worktrees/**
- phase-followups: Y8 + Y9 fixed, knowledge.md + activeContext updated

## pipeline-checkpoint-FOLLOWUPS_COMPLETE
### Changes
- fix-Y9/codex: dual-teams-spawn forwards --result-dir to codex-wave
- fix-Y8/codex: codex-gate exempts dual-teams worktrees via .dual-base-ref sentinel
- y8/y9 specs: codex-gate sentinel + dual-teams-spawn --result-dir

## pipeline-checkpoint-ROUND2_COMPLETE
### Changes
- phase7/round2: PIPELINE_COMPLETE — Y6+Y7 fixed, 2x clean dual + 2x selftest

## pipeline-checkpoint-PHASE3
### Changes
- No commits recorded.

## pipeline-checkpoint-PHASE456
### Changes
- fix-Y6/Y7-selftest/codex: dual-teams-selftest.py — end-to-end regression detector

## pipeline-checkpoint-PHASE2
### Changes
- No commits recorded.

## pipeline-checkpoint-PHASE1
### Changes
- fix-Y6/codex: enforcer recognizes dual-teams worktrees via .dual-base-ref sentinel
- fix-bootstrap: gitignore .dual-base-ref + Round 2 pipeline + enforcer task spec
- session-checkpoint: round 1 complete, round 2 failed, restart context saved
- merge FIX-B: .dual-base-ref sidecar (Y2 supporting; TIE→claude)
- merge FIX-A: judge diff-baseline (Y2 fix; TIE→claude)
- fix-A/claude: judge diff-baseline — score all 6 axes on committed+untracked worktrees
- fix-B/claude: write .dual-base-ref sidecar after every worktree creation
- fix-docs: heredoc + Windows .CMD gotchas in task template (Y1+Y3)
- observability: task specs T-A/T-B/T-C (dual-status + codex-health + pipeline-status)

## pipeline-checkpoint-V2-FINAL
### Changes
- codex-primary-v2: T14 integration smoke complete — 5/5 tools validated end-to-end
- codex-wave: strip UNC prefix at all forward paths (edge case #2)

## pipeline-checkpoint-V2-WAVE3-DONE
### Changes
- codex-primary-v2: Wave 3 COMPLETE — T5+T8+T9+T10+T11+T12+T13 all landed
- dual-T5: merge Claude-side winner (judge.py 3-file split, 28 tests)
- dual-T10: merge Claude-side winner (warm Codex pool, 20 tests)
- dual-T8T9: merge Claude-side winner (rate-limit backoff + circuit breaker, 60 tests)
- dual-T10/claude: warm Codex pool + tests
- dual-T5/claude: judge.py + judge_axes.py + tests (split for writability)
- dual-T8T9/claude: rate-limit backoff + circuit breaker + tests
- Wave 3 specs: T8T9-stability + T10-warm-pool + T5-judge (retry, split into 3 files)
- codex-wave: strip \?\ UNC prefix before git worktree add (Windows parallel fix)
- Phase A docs: T11 streaming judge + T13 cherry-pick hybrid + T12 codex-integration Always-Dual section

## pipeline-checkpoint-V2-WAVE2-PARTIAL
### Changes
- dual-T3/claude: implement dual-teams-spawn.py + tests
- dual-T4: integrate finalized version (+22 tests, log-handle bug auto-fixed)
- dual-T4/claude: implement codex-inline-dual.py + tests
- codex-primary-v2: Wave 2 intermediate — T3 Claude winner (merged), T4 partial, T5 deferred
- codex-gate: exempt worktrees/** — dual-operation bypass (same pattern as enforcer)
- enforcer: exempt worktrees/** — dual-operation paths
- codex-primary-v2: Wave 2 specs — T3 (dual-teams-spawn) + T4 (codex-inline-dual) + T5 (judge.py)
- codex-primary-v2: T6 — enforcer hook wired in settings.json

## pipeline-checkpoint-V2-T1-DONE
### Changes
- dual-T1: archive Codex loser + preserve claude/codex diff history
- dual-T1: merge Claude-side winner (codex-delegate-enforcer.py)
- dual-T1/claude: implement codex-delegate-enforcer.py + tests
- codex-primary-v2: DUAL_TEAMS phase doc + AGENTS.md dual contract notice
- codex-primary-v2: bootstrap enforcer stub + T1 full spec
- codex-primary-v2: CLAUDE.md — Always-Dual protocol (MANDATORY, blocking)
- codex-primary: migrate gpt-5.4 -> gpt-5.5 across all files (110 replacements, 24 files)

## pipeline-checkpoint-PIPELINE_COMPLETE
### Changes
- wave-smoke: codex-wave.py live-exercised 2-way parallel
- wave-smoke: merge 2 parallel GPT-5.5 tasks (wave-a + wave-b)
- wave-b: add git_worktree_list.py (GPT-5.5 via wave)
- wave-a: add codex_env_check.py (GPT-5.5 via wave)
- wave-smoke: 2 tiny task specs for codex-wave.py parallel live test
- codex-primary: automated iteration memory via --iterate-from
- pipeline: mark PROOF_OF_CONCEPT status PASS (was stale PENDING)
- codex-primary: PIPELINE_COMPLETE — DOCUMENT phase done
- codex-primary: speed layer + AGENTS.md shared context

## pipeline-checkpoint-DUAL2_COMPLETE
### Changes
- dual-2: judgment + archive of loser diff
- dual-2: merge Claude-side winner (--sort-by flag)
- dual-2/claude: add --sort-by flag to list_codex_scripts.py
- dual-2: spec with python (not py -3) to avoid sandbox Finding #10

## pipeline-checkpoint-POST_DUAL1_FIXES
### Changes
- codex-primary: fix 4 bugs surfaced by dual-1 live run
- dual-1: post-mortem + 3 new bugs + 2 findings from Level 3 live run
- dual-1: merge Claude-side winner (--json flag for list_codex_scripts.py)
- dual-1/claude: add --json flag to list_codex_scripts.py
- codex-primary: spec for Level 3 dual-implement live task (add --json to list_codex_scripts.py)

## pipeline-checkpoint-POC_SUCCESS_GPT55
### Changes
- codex-primary: PoC SUCCESS on gpt-5.5 via chatgpt backend-api
- codex-primary: route gpt-5.5 via chatgpt backend-api provider

## pipeline-checkpoint-POC_SUCCESS_v54
### Changes
- codex-primary: PoC SUCCESS on gpt-5.4 — architecture fully validated
- codex-primary: pass Codex prompt via stdin not argv
- codex-primary: add --model flag, default gpt-5.4
- gitignore .codex/ runtime state; sync activeContext
- codex-primary: recreate task-PoC.md (previously wiped by rollback)

## pipeline-checkpoint-POC_FIX_v1
### Changes
- codex-primary: fix PoC bugs #1-#3 — clean-tree preflight guard

## pipeline-checkpoint-POC_FAIL
### Changes
- codex-primary: PoC FAIL — 3 critical bugs found + collateral damage doc

## pipeline-checkpoint-IMPLEMENT_WAVE_2
### Changes
- codex-primary: Wave 2 complete — skill + ADR + CLAUDE.md section

## pipeline-checkpoint-IMPLEMENT_WAVE_1
### Changes
- codex-primary: Wave 1 complete — foundations (5 teammates, 89 tests)

## pipeline-checkpoint-PLAN
### Changes
- codex-primary: PLAN phase complete — tech-spec + 8 tasks + waves
- bridge-stubs: canonical template + auto-sync across all staging dirs
- bridge-stubs: session-task-class.py for dp-notifier staging dirs
- codex-round5 FINAL: PASS — zero findings
- codex-round4 fix: end-to-end fail-closed path test
- codex-round3 fix: fail closed on lock timeout + concurrency regression tests
- codex-round2 fix: hold lock across Codex call, eliminates cooldown-reload race
- codex-review fixes: BLOCKER /watchdog off + file lock + HALT integration test
- quality: atomic state writes + 19 stress/integration tests + 5 TP tests
- pipeline-checkpoint-SYNC+VERIFY: mirror to new-project template + evidence
- pipeline-checkpoint-IMPL+TESTS: severity-graded watchdog + classifier + tests
- pipeline-checkpoint-SPEC: freeze watchdog-fix spec + FP corpus
- docs(autoresearch): finalize quarantine state + expanded stub validation matrix
- feat: autoresearch integration — experiment-loop skill v2 (Bayram Annakov MIT)
- Revert "feat: autoresearch integration — experiment-loop skill v2 (Bayram Annakov MIT)"
- Revert "docs(autoresearch): finalize quarantine state + expanded stub validation matrix"
- docs(autoresearch): finalize quarantine state + expanded stub validation matrix
- feat: autoresearch integration — experiment-loop skill v2 (Bayram Annakov MIT)
- fix: dedup chunks in semantic-search indexer (ChromaDB DuplicateIDError)
- feat: MemPalace cherry-pick — knowledge graph, semantic search, 4-layer context
- feat: webinar insights integration — 6 harness improvements from Claude Code architecture analysis
- feat: ECC cherry-pick integration — 13 skills, security guide, hook profiles, fleet sync
- sync: server dev changes — codex integration, QA skills, settings fix
- sync: push all local changes for server dev migration
- feat: agent memory mandatory + re-verify loop + skill-development removed
- feat: global skills migration + mandatory phases tested + skill evolution examples
- feat: compress CLAUDE.md 526→221 lines + mandatory pipeline phases + reference guides
- feat: integrate best-practice patterns — agent memory, auto-research, fresh verification, skill evolution, examples
- feat: add spawn-agent.py — one-command teammate spawning with auto-type detection
- feat: add generate-prompt.py — skill auto-discovery via YAML roles field
- feat: post-E2E improvements — full skills restored, global cleanup, AO fixes verified
- feat: AO Hybrid E2E validated + synced to 8 bots
- chore: update memory after bot fleet sync (8 bots synced)
- fix: sync new-project template CLAUDE.md with main project
- feat: memory decay integration + hooks + skills + observations system
- feat: PreCompact memory save hook — auto-saves context before compaction

## pipeline-checkpoint-EVALUATE
### Changes
- feat: OpenClaw pipeline COMPLETE — POST_TEST passed, user approved KEEP

## pipeline-checkpoint-IMPLEMENT
### Changes
- feat: OpenClaw-inspired memory restructure — knowledge.md, daily logs, simplified rules
- feat: Auto-Claude integration — typed memory, agent registry, Graphiti, Ralph Loop removal
- feat: scalable pipeline v2 — full autonomous project development system
- feat: skills audit & cleanup — 44 to 14 skills (68% reduction)
- feat: implement autonomous pipeline system for compaction-resilient execution
- feat: plan execution enforcer with minimal CLAUDE.md footprint
- feat: implement three-level memory system
- docs: add prompts for applying smart decision making to other projects
- feat: add wave parallelization detection
- feat: intelligent dependency analysis for plan execution
- docs: make upgrade prompt universal and flexible
- docs: add short upgrade prompt for other projects
- docs: add v2.0 complete documentation and upgrade guide
- feat: v2.0 - universal parallelization detection without explicit plan files
- refactor: improve AUTO-CHECK rule for flexible plan detection
- refactor: CLAUDE.md variant B - progressive disclosure
- refactor: restructure CLAUDE.md with Context Loading Triggers
- feat: integrate Anthropic Constitution principles into CLAUDE.md
- feat: add AUTO-CHECK for plan detection in skill selection
- feat: add BLOCKING rule for plan execution with subagent-driven-development
- feat: add MANDATORY decision algorithm for Worktree Mode
- fix: clarify Worktree Mode is for file conflicts, not to avoid them
- feat: implement Worktree Mode v2.1 for parallel task execution
- feat: add orchestration and automation skills
- feat: improve skill selection workflow with checkpoints
- fix: remove Quick Skill Selection table
- refactor: restructure CLAUDE.md with blocking rules and compact format
- chore: remove INSTALLATION_GUIDE.md
- feat: add 12 new skills and installation guide
- feat: switch to dev/main branch workflow
- fix: update init-project based on testing
- fix: add SSH key paths to config for Windows compatibility
- feat: fully automatic /init-project without any questions
- fix: use master branch instead of main
- feat: add interactive /init-project command
- refactor: restructure skills system with hybrid architecture
- feat: improve workflow rules for skills, testing, and fixes
- fix: remove brainstorming and writing-plans skills from planning stage
- docs: add Execution Mode Decision rule to CLAUDE.md
- Add Project Initialization section for Claude
- docs: use --squash merge for cleaner main branch history
- feat: add optional skills support for proposal stage
- docs: add comprehensive CI/CD setup guide and server setup script
- Initial template setup
<!-- pipeline-checkpoint-changelog:end -->
