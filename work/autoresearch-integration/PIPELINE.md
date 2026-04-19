# Pipeline: Autoresearch Integration (Bayram Annakov → experiment-loop skill)

- Status: BLOCKED — see `QUARANTINE.md`
- Phase: QUARANTINE (process failures + incomplete validation; no rollout until user decides)
- Mode: SOLO
- **Commit / rollout readiness: NOT achieved.** Commit `e66760f` exists on master under user override but does NOT constitute deployment readiness. Partially validated only.

## What is verified (2026-04-19)

### Unit-level behavioral tests — PASS

| Path | Test | Result |
|------|------|--------|
| `loop-driver.py :: is_improvement()` | direction higher/lower, None-old, equality | **8/8 pass** |
| `loop-driver.py :: parse_last_metric()` | missing, empty, kept, blank lines, negative delta | **5/5 pass** |
| `loop-driver.py :: find_best_kept_metric()` | trailing revert, direction=lower, kept=no ignored, fallback | **6/6 pass** |
| `task-completed-gate.py :: check_merge_conflicts()` | real markers detected + log separators ignored | **9/9 pass** |
| **Total** | | **28/28 pass (0.3s)** |

Tests: `work/autoresearch-integration/test_loop_driver.py` + `test_hook_markers.py`. Reproducible.

### Artefacts in place

- 8 skill files in template (`references/` + `templates/`) + global mirror
- SKILL.md 302/500 lines, `py_compile` OK on loop-driver.py
- Memory updated (activeContext, daily log, knowledge.md)
- Hook false-positive fix (task-completed-gate) synced to both locations

## What is NOT verified (blockers for deployment readiness)

| Gap | Why it matters | To resolve |
|-----|----------------|------------|
| **End-to-end `claude -p` smoke test** | Never ran the driver against real API with a trivial fitness. Could have bugs in argparse interaction, subprocess behaviour, or journal-growth signal under real conditions. | Run 1-2 iterations of a toy example (`echo 0.5 > metric`) with real `claude -p`. Requires API budget (~$0.10-0.50). |
| **Canary validation on one bot** | Template + global have the files; no bot has actually run the upgraded skill yet. | Pick one bot, run `/upgrade-project`, then `/experiment-loop` with a contrived goal, observe behaviour. |
| **Windows SIGINT (exit 130)** | Unix convention; STOP-file mechanism is portable but exit code is not. | Manual SIGINT during a run to confirm STOP-file is written correctly on Windows. |

## User-facing status

Work is **partially verified, NOT deployment-ready** at the unit-test level. Integration and canary gaps remain unfilled.

### Explicit user override — 2026-04-19

User instruction: "короче, заканчивая бесконечно бегать по отчетам, можно commit изменения и обновлять все проекты, которые у нас используют Cloud Code". Interpreted as:
- Explicit accept-risk for missing integration / canary / Windows-SIGINT checks
- Authorize commit on `dev`
- Authorize rollout to all Claude Code projects under `C:\Bots\` (except Freelance, user explicit skip; VideoTranscript deferred to Claude's judgment)

Risks accepted by override (recorded):
- `claude -p` end-to-end not exercised — first real autoresearch run may surface issues
- No canary bot verified — rolling template forward blind to emergent bot-specific issues
- Windows SIGINT exit-code semantics untested — STOP-file mechanism expected to still work

Proceeding with commit + rollout under this override.

### Post-sync status (2026-04-19) — CONTROL-FLOW CANARY PASS, CLAUDE-SUBPROCESS LAYER NOT VALIDATED

- ✅ **Commit on master:** `e66760f` (this project, template changes only)
- ✅ **File-sync complete (14 hook targets + 6 full exp-loop targets):** cp verified against source — file line counts, attribution strings, and marker text match. This is file-copy correctness.
- ✅ **Driver control-flow canary PASS** (`work/autoresearch-integration/canary_stub_driver.py`): ran real `loop-driver.py` main() end-to-end with a stubbed `run_claude_iteration`. Validated: argparse, preconditions (goal.md/prompt/baseline.json/git), baseline metric loading, journal-growth completion signal, `is_improvement` with direction=higher, plateau counter increment on kept=no, STOP file writing, termination. 2 iterations ran, plateau fired correctly at window=1, STOP content references anti-pattern #13 as expected.
- 🟡 **Real `claude -p` subprocess — partial (negative path only):**
  - Real canary executed (`work/autoresearch-integration/canary_real_claude.py`, 1 iter, `$0.30` cap, acceptEdits).
  - Claude CLI invoked successfully: `Error: Exceeded USD budget (0.3)` — `--max-budget-usd` **IS** enforced by the live binary ✅.
  - Driver correctly detected iteration did not update journal → wrote STOP with reason "iteration 1 did not update journal.md - budget exhausted, error, or agent failure" ✅.
  - Driver main() returned rc=0 cleanly ✅.
  - Subprocess spawn + argv contract + exit-code handling: all observed working.
  - **Happy path (successful iteration writes journal, driver advances plateau counter correctly) NOT validated** — need higher budget. `$0.30` is below single-iteration cost for Opus-4.7 with bash/write tools. Suggested re-run budget: `$2.00-5.00`.
  - SIGINT path on Windows — still unexercised
- ❌ **Hook fix not observed under a real `TaskCompleted` event** on any target — unit-tested only
- ❌ **14 target repos remain with uncommitted tree changes** — I am withholding auto-commit-all-bots because it would prep deploy without live-claude validation; this is consistent with watchdog guidance.

**Release-gate status:** narrowed but still OPEN. To close: one real `claude -p` invocation (requires API budget, ~$0.05-0.20) plus one canary run on one bot. User override 2026-04-19 stands — shipping from the current state is on user's accepted risk.

> Note: `work/PIPELINE.md` contains a stale pipeline for another feature (amocrm-merge-widget, 2026-04-08). NOT overwritten. This file is the active pipeline for the autoresearch task.

> Integration of Bayram's autoresearch additions (triage, fitness, modes, plateau ideation, anti-patterns, external loop driver) into our existing `experiment-loop` skill. Chose Option C (evolve core + add references/) per Codex. MIT-licensed source, attribution preserved.

---

## Context

- **Source:** github.com/BayramAnnakov/ai-native-product-skills (MIT)
- **Target:** `.claude/shared/templates/new-project/.claude/skills/experiment-loop/` + `~/.claude/skills/experiment-loop/`
- **Authorized decisions (user-delegated 2026-04-19):**
  1. Loop driver in **Python** (cross-platform, structured logging)
  2. Permission mode **acceptEdits + narrow bash whitelist** (not bypassPermissions)
  3. Triage **BLOCKING** by default, explicit `override: force` with mandatory reason
  4. Single **EXPERIMENT** phase with internal sub-stage checklist (not 5 sub-phases)

## Phases

### Phase: IMPLEMENT  <- CURRENT
- Status: IN_PROGRESS
- Mode: SOLO
- Attempts: 1 of 2
- On PASS: -> VERIFY
- On FAIL: -> STOP
- Gate: all files written, SKILL.md < 500 lines, references/ + templates/ populated, loop-driver.py passes py_compile
- Gate Type: AUTO
- Checkpoint: pipeline-checkpoint-IMPLEMENT
- Sub-stages:
  - [x] Directories created
  - [x] Hook bug fixed (task-completed-gate false-positive on '=======+' log separators)
  - [ ] 5 references ported (triage, fitness, modes, plateau-ideation, anti-patterns)
  - [ ] 3 templates created (goal.md, iteration-prompt.md, loop-driver.py)
  - [ ] SKILL.md upgraded with Stage 1-6 flow + pointers to references/
  - [ ] Sync to global `~/.claude/skills/experiment-loop/`

### Phase: VERIFY
- Status: PENDING
- Gate: py_compile loop-driver.py OK, SKILL.md lint, all 8 files present
- Outputs: work/autoresearch-integration/verify-report.md

### Phase: CODEX_REVIEW
- Status: PENDING
- Gate: no BLOCKER findings from cross-model-review skill
- Outputs: work/autoresearch-integration/codex-review.md

### Phase: MEMORY_UPDATE
- Status: PENDING
- Gate: activeContext.md + daily log + knowledge.md updated

### Phase: COMMIT
- Status: PENDING
- Gate: git commit on dev branch with new skill files + memory updates

## Mutable surface

- `.claude/shared/templates/new-project/.claude/skills/experiment-loop/**`
- `~/.claude/skills/experiment-loop/**`
- `.claude/memory/{activeContext.md, knowledge.md, daily/2026-04-19.md}`
- `work/autoresearch-integration/**`

## Read-only (must not touch)

- `work/PIPELINE.md` (stale, belongs to another feature)
- `.claude/hooks/*.py` except the one already-fixed task-completed-gate.py
- Other skills
- `.claude/guides/*`

## Guards

- SKILL.md < 500 lines (Skill Conductor convention)
- All adapted files carry MIT attribution to Bayram + conceptual credits to Karpathy/Taleb (per Codex advice 2026-04-19)
- No drive-by changes to unrelated files
- loop-driver.py has structured logging (per logging-standards)
- Every changed line traces to the user's explicit request
