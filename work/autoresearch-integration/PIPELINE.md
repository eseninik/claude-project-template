# Pipeline: Autoresearch Integration (Bayram Annakov → experiment-loop skill)

- Status: PARTIALLY_VERIFIED — unit-level only
- Phase: VERIFICATION (integration/canary NOT performed)
- Mode: SOLO
- **Commit / rollout readiness: NOT achieved** (watchdog-enforced honesty: unit-test coverage ≠ deployment readiness)

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
