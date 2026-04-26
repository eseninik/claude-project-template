---
task_id: Z12-y21-y25-judge-diagnostic
title: Y21 (judge diff_size logarithmic) + Y25 (enforcer unavailability diagnostic)
executor: dual
risk_class: routine
speed_profile: balanced
---

# Task Z12 — Y21 + Y25 final UX/quality polish

## Goal

Two final improvements that close all open follow-ups:

**Y21:** `score_diff_size` in `judge_axes.py:181-188` uses `score =
max(0, 1 - added/cap_lines)` with hardcoded `cap_lines=500`. Diffs > 500
LOC score 0.0 — Z1 was +1102 LOC → forced TIE artifact. Fix:
asymptotic `score = scale / (scale + added)` — large diffs still score
lower, but never 0; judge can differentiate.

**Y25:** When enforcer denies a code-extension write, message says
"no Codex cover for X / run codex-inline-dual". But if Codex itself is
DOWN (auth expired, network out), running the suggestion ALSO fails.
Y25 detects unavailability and prepends an explicit hint:
```
*** Codex appears unavailable (<reason>).
*** Run `codex login` or wait, then retry.
```
Rule unchanged (still fail-closed). Wording improves only.

## Scope Fence — files you MAY modify

```
.claude/scripts/judge_axes.py
.claude/scripts/test_judge.py
.claude/hooks/codex-delegate-enforcer.py
.claude/hooks/test_codex_delegate_enforcer_invariants.py
```

DO NOT modify any other file.

## Read-Only Files / Evaluation Firewall

- `work/codify-enforcement/task-Z12-y21-y25-judge-diagnostic.md`
- `.claude/scripts/judge.py`, `codex-implement.py`, `codex-wave.py`,
  `codex-inline-dual.py` (downstream consumers)

## Acceptance Criteria

### AC-1 (Y21): asymptotic scaling

Modify `score_diff_size(...)`:
```python
score = scale_factor / (scale_factor + max(0, added))
```
where `scale_factor` = parameter previously named `cap_lines`. Keep
the kwarg name backward-compatible (`cap_lines: int = 500`) — internally
treat it as the asymptotic scale.

Add tests in `test_judge.py` (create file if absent — hermetic, no
real codex needed):

- `test_diff_size_zero_added_scores_one()` — added=0, cap=500 → score == 1.0
- `test_diff_size_at_scale_scores_half()` — added=500, cap=500 → score in [0.49, 0.51]
- `test_diff_size_far_above_scale_still_nonzero()` — added=2000, cap=500 → 0.0 < score < 0.3
- `test_diff_size_huge_diff_asymptotic()` — added=10000, cap=500 → score in (0.0, 0.1]

If existing test_judge tests assert hard-zero at cap, RELAX them per
this design change. Document any updated tests in self-report.

### AC-2 (Y25): unavailability helper

Add to `codex-delegate-enforcer.py`:

```python
def _codex_appears_unavailable(
    auth_path: Optional[Path] = None,
    now: Optional[datetime] = None,
    max_auth_age_hours: int = 24,
) -> tuple[bool, str]:
    """Return (True, reason) if Codex appears unusable, else (False, '')."""
    auth = auth_path or (Path.home() / ".codex" / "auth.json")
    if not auth.exists():
        return True, f"~/.codex/auth.json missing"
    age_hours = ((now or datetime.now()).timestamp() - auth.stat().st_mtime) / 3600
    if age_hours > max_auth_age_hours:
        return True, f"~/.codex/auth.json older than {max_auth_age_hours}h ({int(age_hours)}h)"
    return False, ""
```

Tests:

- `test_codex_unavailable_when_auth_missing(tmp_path)` — pass
  `auth_path=tmp_path/nonexistent.json` → True + "missing" in reason
- `test_codex_available_when_auth_recent(tmp_path)` — write tmp file
  with mtime=now → False, ""
- `test_codex_unavailable_when_auth_stale(tmp_path)` — write tmp file
  + os.utime to set mtime 48h ago → True + "older" in reason

### AC-3 (Y25): block message includes unavailability hint

In the existing block-message construction (likely in `decide()` or
`_format_deny_message()`), when the unavailability helper returns True,
prepend lines:
```
*** Codex appears unavailable: {reason}.
*** Run `codex login` or check ~/.codex/auth.json, then retry.
```
Then continue with the existing "no cover" message.

Test:
- `test_block_message_mentions_unavailability_when_codex_down(monkeypatch)` —
  monkeypatch `_codex_appears_unavailable` to return `(True, "test reason")`,
  build a no-cover deny scenario, capture stderr → assert it contains
  "appears unavailable" AND "test reason" AND existing "codex-inline-dual"
- `test_block_message_unchanged_when_codex_available(monkeypatch)` —
  monkeypatch to return `(False, "")` → assert stderr does NOT contain
  "appears unavailable"

### AC-4: Existing 220 tests still pass

```bash
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line
```

Some judge tests may need adjusting (AC-1) — that's by design.

### AC-5: Selftest still passes
`python .claude/scripts/dual-teams-selftest.py` → 6/6 PASS

## Test Commands

```bash
# 1. Judge axis tests
python -m pytest .claude/scripts/test_judge.py -v --tb=line

# 2. Enforcer invariants (with Y25 helper)
python -m pytest .claude/hooks/test_codex_delegate_enforcer_invariants.py -v --tb=line

# 3. Other suites
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line

# 4. Selftest
python .claude/scripts/dual-teams-selftest.py
```

## Implementation hints

- For Y21: the formula `scale / (scale + x)` is a Hill function /
  Michaelis-Menten — smooth, monotonic, asymptotic to 0 as x → ∞.
  Score@x=0 = 1.0, score@x=scale = 0.5, score@x=2*scale = 0.333,
  score@x=10*scale ≈ 0.091.
- For Y25 helper: pure function with optional kwargs for `auth_path`
  and `now` makes testing trivial. Default to real `~/.codex/auth.json`
  and `datetime.now()`.
- For Y25 message: find the existing deny-message construction —
  `grep -n "codex-inline-dual\|no cover\|blocked" .claude/hooks/codex-delegate-enforcer.py`.
  Wrap the message string with conditional prefix.
- Logging: add `logger.debug` entry/exit for Y25 helper. Y21 — keep
  existing logs.

## Self-report format

```
=== TASK Z12 SELF-REPORT ===
- status: pass | fail | blocker
- files modified: [list]
- new tests added: <count>
- net lines: <approx>
- Y21 approach: <1 line>
- Y25 approach: <1 line>
- existing 220 tests still pass: yes / no
- selftest: PASS / FAIL
- diff_size new behavior verified (added=2000, cap=500, 0 < score < 0.3): yes / no
- block message unavailability hint added: yes / no
- NOTE: <surprising>
- BLOCKER: <only if>
- Final commit SHA: <SHA>
=== END SELF-REPORT ===
```
