---
task_id: Z32-judge-quality-final
title: Criterion 7 Judge Quality — codex-ask timeout Y27 + mypy.ini for type_check axis + tie threshold tuning + logging_coverage refinement
executor: dual
risk_class: routine
speed_profile: balanced
---

# Task Z32

## Goal

Criterion 7 (Judge Quality) currently 5/10 because:
- 2 of 6 axes always skip (radon now INSTALLED via pip, mypy already INSTALLED but no `mypy.ini` config → still skips)
- `codex-ask.py` has hardcoded 120s timeout → strategic deep consults silently fail (Y27)
- Tie threshold 0.02 may not match observed verdict variance
- `logging_coverage` heuristic (window=5) misses functions delegating to logged helpers

## Four coordinated improvements

### Improvement 1 (Y27) — codex-ask.py timeout extension

In `.claude/scripts/codex-ask.py` `ask_via_exec()`, current `timeout=120`
silently fails for deep analyses (production-readiness review timed out
in our last verification round). Two-mode fix:
- Default `timeout=180` (up from 120 — covers normal advisor consults)
- Add `--strategic` CLI flag → `timeout=900` (15 min, for deep reviews)

Add tests:
- `test_ask_via_exec_default_timeout_180`
- `test_ask_via_exec_strategic_timeout_900`

### Improvement 2 — mypy.ini for type_check axis

NEW file `mypy.ini` at repo root with reasonable defaults:
```ini
[mypy]
python_version = 3.12
ignore_missing_imports = True
warn_unused_ignores = True
strict_optional = False
```

Update `.claude/scripts/judge_axes.py:score_type_check` to look for
`mypy.ini` OR `pyproject.toml` `[tool.mypy]` section and activate the
axis when present.

Add test:
- `test_score_type_check_active_when_mypy_ini_present`

### Improvement 3 — Tie threshold tuning

Observed verdicts in this session:
- Z10: TIE 0.000
- Z11: TIE -0.0099
- Z12: Codex -0.0245
- Z17: Codex -0.1741
- Z23: Codex -0.0277
- Z26: Codex -0.0856
- Z29: Codex -0.0533

Mean |delta| ≈ 0.052, std ≈ 0.057. Current tie threshold 0.02 catches
2 of 7 verdicts as TIE — too tight. Recommend threshold 0.030 (2σ-ish
of the bottom cluster). Configurable via judge.py `--tie-delta` already.

Update default in `judge.py` `--tie-delta` from 0.02 to 0.03 with NOTE
in argparse help: "Threshold tuned from observed dual-implement deltas".

Add test:
- `test_tie_threshold_default_is_0_03` (assert default in argparse)

### Improvement 4 — logging_coverage delegated-call recognition

In `judge_axes.py:score_logging_coverage`, current heuristic counts
functions whose body has `logger.` within `window=5` lines. Functions
that delegate to a helper (e.g. `_log(level, msg)`) are missed.

Refine: also count functions where body contains call to local helpers
matching pattern `_log\(` OR `logger.` within window. Helper names
recognized: `_log`, `log_info`, `log_warn`, `log_error`, `log_debug`.

Add test:
- `test_logging_coverage_counts_delegated_log_calls`

## Scope Fence

```
.claude/scripts/codex-ask.py
.claude/scripts/test_codex_ask.py
.claude/scripts/judge.py
.claude/scripts/judge_axes.py
.claude/scripts/test_judge.py
mypy.ini   (NEW at repo root)
```

DO NOT modify any other file.

## Read-Only Files / Evaluation Firewall

- `work/criterion-upgrade/task-Z32-judge-quality-final.md`
- `.claude/hooks/codex-delegate-enforcer.py`
- `.claude/scripts/codex-implement.py`, `spawn-agent.py`, etc.

## Acceptance Criteria

### AC-1 (Y27): timeout tests pass
- `test_ask_via_exec_default_timeout_180` PASSES
- `test_ask_via_exec_strategic_timeout_900` PASSES

### AC-2: mypy.ini exists + type_check active
- `mypy.ini` at repo root, valid INI parseable
- `test_score_type_check_active_when_mypy_ini_present` PASSES (no longer skipped)

### AC-3: tie threshold default 0.03
- `test_tie_threshold_default_is_0_03` PASSES

### AC-4: logging_coverage counts delegated calls
- `test_logging_coverage_counts_delegated_log_calls` PASSES

### AC-5: Existing 138 tests still pass

```bash
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/scripts/test_spawn_agent.py .claude/scripts/test_determinism_chaos.py .claude/scripts/test_archive_active_context.py .claude/scripts/test_generate_changelog.py .claude/scripts/test_sync_template_to_target.py .claude/scripts/test_verify_codex_auth.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line
```

### AC-6: Selftest + matrix
`python .claude/scripts/dual-teams-selftest.py` 6/6
`pytest .claude/hooks/test_enforcer_live_attacks.py` 25/25

## Test Commands

```bash
# 1. New + existing test_judge / test_codex_ask
python -m pytest .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py -v --tb=line

# 2. mypy.ini parseable
python -c "import configparser; c=configparser.ConfigParser(); c.read('mypy.ini'); assert 'mypy' in c"

# 3. Existing 138 (regression)
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_spawn_agent.py .claude/scripts/test_determinism_chaos.py .claude/scripts/test_archive_active_context.py .claude/scripts/test_generate_changelog.py .claude/scripts/test_sync_template_to_target.py .claude/scripts/test_verify_codex_auth.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line

# 4. Selftest
python .claude/scripts/dual-teams-selftest.py
```

## Implementation hints

- For Y27: locate `subprocess.run(..., timeout=120)` in `ask_via_exec`. Replace with `timeout=180` default, accept `strategic: bool` kwarg → 900s.
- mypy.ini: simple INI format. See implementation hint in task spec body.
- judge_axes.score_type_check: check `Path("mypy.ini").exists() or "[tool.mypy]" in pyproject.toml`. If yes, run `mypy --no-error-summary <files>` capture rc, score = 1.0 if rc==0 else 0.5.
- Tie threshold: simple constant change in argparse. Keep `tie_delta` param signatures.
- logging_coverage: extend regex to recognize `_log\(` AND `logger\.` within window.

## Self-report format

```
=== TASK Z32 SELF-REPORT ===
- status: pass | fail | blocker
- Improvement 1 (Y27 timeout) approach: <1 line>
- Improvement 2 (mypy.ini + type_check) approach: <1 line>
- Improvement 3 (tie threshold) approach: <1 line>
- Improvement 4 (logging delegated) approach: <1 line>
- new tests: <count> (expected 4)
- existing 138 pass: yes / no
- attack matrix 25/25: yes / no
- selftest 6/6: PASS / FAIL
- mypy.ini valid INI: yes / no
- net lines: <approx>
- files modified: [list]
- NOTE: <surprising>
- BLOCKER: <only if>
- Final commit SHA: <SHA>
=== END SELF-REPORT ===
```
