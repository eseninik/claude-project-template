# Observability Live-Test Debrief (T14-proper)

**Run start:** 2026-04-24 21:16
**Run end:** _TBD_
**Tasks:** T-A dual-status.py | T-B codex-health.py | T-C pipeline-status.py
**Parallelism:** 3 Claude teammates + 3 Codex sessions = 6 concurrent agents

## Wall-Time per Pair

| Pair | Claude start | Claude end | Codex start | Codex end | Judge verdict |
|------|--------------|------------|-------------|-----------|---------------|
| T-A  | 21:16:XX     | _TBD_      | 21:16:32    | _TBD_     | _TBD_         |
| T-B  | 21:16:XX     | _TBD_      | 21:16:32    | _TBD_     | _TBD_         |
| T-C  | 21:16:XX     | _TBD_      | 21:16:32    | _TBD_     | _TBD_         |

## What Worked

- Enforcer worktree-bypass held: every Write to `worktrees/observability/claude/**` approved as `exempt-or-non-code`. Zero false-positive blocks.
- codex-wave.py launched 3 parallel Codex sessions on the chatgpt backend-api route without UNC errors (prior X3/X4 fixes holding).
- `dual-teams-spawn.py` worktree provisioning worked across 6 worktrees (3 claude + 3 codex). Stale-worktree warnings were self-recovered.
- 6-way parallelism on a single ChatGPT account: no circuit breaker trip (`.codex/circuit-state.json` never materialized).
- T-C teammate's **honest-blocked fallback** is itself a protocol win: it returned a clear reason ("wait for Codex result, then Write") instead of hallucinating completion or writing a stub as real output.

## What Broke

- **Harness-level Write auto-deny (X5 upgraded from "workaround only" → reproducible blocker).** All 3 Claude teammates hit it:
  - T-A: 3 enforcer-allowed Write attempts for `dual-status.py` over 6 min, 0 persisted.
  - T-B: Fell back to probe-file — wrote `# test\n` (8 bytes) instead of full ~400-line script.
  - T-C: Gave up after enforcer-allowed Write didn't persist; returned blocked status.
- **Silent-failure asymmetry between enforcer and harness**: `decide.allow-target allowed=True` in enforcer log coexists with zero bytes on disk. No signal reaches the teammate that harness denied; teammate sees only "file not there after Write" and has to guess why.
- **task-N.md spec had no split-file guidance**: spec allowed "under 350 lines script + 350 lines tests" as a single file. That implicitly pushes teammates into the harness-deny zone. Root cause of 3/3 teammate failure lies in spec, not teammate reasoning.

## New Bugs Found

| # | Component | Symptom | Root cause | Fix |
|---|-----------|---------|------------|-----|
|   |           |         |            |     |

## Judge Axis Scores (per pair)

### T-A: dual-status.py
- tests_passed (w10): _claude X / codex Y_
- diff_size (w2): _claude X / codex Y_
- logging_coverage (w3): _claude X / codex Y_
- lint_clean (w2): _claude X / codex Y_
- complexity (w1 opt): _claude X / codex Y_
- type_check (w2 opt): _claude X / codex Y_
- **Total:** _claude XX / codex YY → WINNER_

### T-B: codex-health.py
_(same table)_

### T-C: pipeline-status.py
_(same table)_

## Infrastructure Observations (honest)

### Always-Dual protocol behavior
- Did teammates produce meaningful work inside their worktrees?
- Did the enforcer behave correctly (no spurious blocks)?
- Did the gate's worktree bypass hold?

### Codex-wave + backoff + circuit breaker
- Did any Codex session trigger rate-limit backoff?
- Was `.codex/circuit-state.json` touched?
- Any UNC long-path errors?
- Any Codex session exit without producing result.md?

### judge.py on real input
- Did axes compute correctly?
- Were there ties?
- Any axis crash (e.g. complexity axis with no .py files)?

## Promote to Knowledge

- _pending_

## Next Actions

- _pending_
