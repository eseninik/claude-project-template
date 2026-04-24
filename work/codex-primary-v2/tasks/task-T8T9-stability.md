---
executor: dual
risk_class: high-stakes
speed_profile: balanced
---

# Task T8+T9: Stability layer in codex-implement.py (rate-limit backoff + circuit breaker)

## Your Task

Extend `.claude/scripts/codex-implement.py` with two resilience features, applied as a cohesive "stability layer" in a single pass:

**T8 — Rate-limit backoff.** If `codex exec` stderr matches HTTP 429 / "rate limit" / "stream disconnected before completion" patterns, retry the same invocation with exponential backoff `1s → 2s → 4s → 8s`, max 4 attempts. Log each retry attempt with reason.

**T9 — Circuit breaker.** Track consecutive Codex failures in `.codex/circuit-state.json` at project root. After **3 consecutive** failures (from ANY codex-implement.py / -inline / -wave invocation in the last 15 min), write a flag `.codex/circuit-open` with 5-min TTL (embedded timestamp). While the flag is active, `codex-implement.py` exits early with a `DEGRADED: circuit open` status — does NOT invoke Codex at all. Flag auto-expires via timestamp check on next invocation. Dual-helpers (`codex-inline-dual.py`, `dual-teams-spawn.py`) are expected to consult the flag and degrade gracefully to Claude-only fallback; that wiring is out of scope for THIS task — only implement the detection and flag emission here.

## Scope Fence

**Allowed:**
- `.claude/scripts/codex-implement.py` (modify existing)
- `.claude/scripts/test_codex_implement.py` (add tests for both features)

**Forbidden:**
- Any other file

## Test Commands

```bash
python .claude/scripts/test_codex_implement.py
python .claude/scripts/codex-implement.py --help
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: Rate-limit retry triggers on stderr containing any of: `"rate limit"` (case-insensitive), `"429"`, `"stream disconnected before completion"` (known gpt-5.5 pattern from chatgpt backend).
- [ ] AC2: Backoff sequence 1s, 2s, 4s, 8s; max 4 retries; logged with extra fields `attempt`, `backoff_s`, `reason`.
- [ ] AC3: If all 4 retries fail → final failure recorded in `CodexRunResult.stderr` (unchanged interface) and counted as a "consecutive failure" for circuit breaker.
- [ ] AC4: Circuit state file at `<project_root>/.codex/circuit-state.json` with schema `{"failures": [{"timestamp": "<iso>", "task_id": "<id>"}], "updated_at": "<iso>"}`. Only failures within last 15 min count.
- [ ] AC5: Circuit opens at exactly 3 consecutive recent failures. Flag file `<project_root>/.codex/circuit-open` written with payload `{"opened_at": "<iso>", "expires_at": "<iso + 5 min>", "reason": "<why>"}`.
- [ ] AC6: On new `codex-implement.py` invocation, check flag FIRST. If present AND not expired → log `circuit_open_skip`, emit result.md with `status: degraded`, `degraded_reason: "circuit-open"`, exit code 3 (new, dedicated for degraded). Add `EXIT_DEGRADED = 3` constant.
- [ ] AC7: Flag auto-clears (delete file) when expired — checked on every invocation.
- [ ] AC8: On any successful Codex run → reset failures list to `[]` (circuit health restored).
- [ ] AC9: No global mutable state; circuit state read/written via atomic temp-file-rename pattern to survive concurrent invocations.
- [ ] AC10: All existing tests still pass. New tests (≥8):
  - backoff on rate-limit stderr (mock)
  - backoff on stream-disconnected stderr
  - max 4 retries then fail
  - circuit state file schema round-trip
  - exactly 3 failures → flag written
  - 2 failures → no flag
  - expired flag auto-deleted
  - active flag → skip Codex, return DEGRADED
  - successful run resets counter
- [ ] AC11: Structured logging per AGENTS.md (entry/exit/error, extra fields for attempt counts, circuit state).
- [ ] AC12: Total addition under 150 lines of new code; keep diff surgical.
- [ ] All Test Commands exit 0.

## Constraints

- Windows-compatible (atomic rename pattern: `os.replace`, not `os.rename`)
- Stdlib only
- Must not break existing `codex-implement.py` CLI signature or exit-code contract (EXIT_DEGRADED=3 is new, documented)
- Retry wrapper must respect `--timeout` cumulative (not per-attempt) — total wall-time across retries ≤ `--timeout`

## Handoff Output

Standard `=== PHASE HANDOFF: T8T9-stability ===` block.

## Iteration History
(First round.)
