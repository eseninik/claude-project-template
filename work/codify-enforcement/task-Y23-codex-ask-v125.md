---
task_id: Y23-codex-ask-v125
title: Fix codex-ask.py parser for Codex CLI v0.125 stdout format
executor: dual
risk_class: routine
speed_profile: balanced
---

# Task Y23 — Fix codex-ask.py for Codex CLI v0.125 stdout format

## Goal

`codex-ask.py` returns "Codex unavailable" with the new Codex CLI v0.125,
even though direct `codex.cmd exec` returns valid responses. Root cause:
v0.117 wrote header+response both to stdout with a sentinel line `codex`;
v0.125 puts header in stderr and only the response (plus `tokens used`
trailer) in stdout. The old parser scans stdout for the `codex` sentinel,
never finds it, returns None.

This blocks every session that relies on codex-ask (advisor consults,
gate refresh, parallel sessions). Fix is one defensive parser that
handles both formats.

## Scope Fence — files you MAY modify

```
.claude/scripts/codex-ask.py
.claude/scripts/test_codex_ask.py        (NEW)
```

DO NOT modify any other file.

## Read-Only Files / Evaluation Firewall

- `work/codify-enforcement/task-Y23-codex-ask-v125.md` (this file)
- `.claude/hooks/codex-delegate-enforcer.py`
- `.claude/hooks/codex-gate.py`

## Acceptance Criteria

A new test file `.claude/scripts/test_codex_ask.py` must contain ALL the
following test cases and ALL must pass via:

```bash
python -m pytest .claude/scripts/test_codex_ask.py -v --tb=short
```

### AC-1: Parser handles v0.125 format (header in stderr, response in stdout)
- `test_parse_v125_simple_ok()` — `parse_codex_exec_stdout("OK\n")` → `"OK"` (NOT None)
- `test_parse_v125_with_tokens_trailer()` — input `"OK\ntokens used\n3 901\nOK\n"` → returns either `"OK"` or `"OK\nOK"`. NOT None.
- `test_parse_v125_multiline_response()` — input `"line 1\nline 2\nline 3\ntokens used\n100\n"` → returns `"line 1\nline 2\nline 3"`
- `test_parse_v125_empty_returns_none()` — input `""` → returns None
- `test_parse_v125_only_whitespace_returns_none()` — input `"   \n\n"` → returns None

### AC-2: Parser still handles v0.117 legacy format (sentinel-based)
- `test_parse_v117_legacy_with_sentinel()` — full v0.117 envelope (header lines, then `codex` sentinel, then response, then `tokens used N`) → returns just the response between sentinel and `tokens used`
- `test_parse_v117_with_repeated_response()` — when v0.117 prints the response twice (once after `codex` sentinel, once after `tokens used`) → returns the canonical response, not None

### AC-3: ask_via_exec integration (mocked subprocess)
- `test_ask_via_exec_v125_returns_response()` — mock `subprocess.run` to return v0.125-shape (returncode 0, stdout="OK", stderr=header) → `ask_via_exec()` returns `"OK"`
- `test_ask_via_exec_v117_returns_response()` — mock to return v0.117-shape → returns the response
- `test_ask_via_exec_returncode_nonzero_returns_none()` — mock returncode=1 → returns None
- `test_ask_via_exec_codex_not_in_path_returns_none()` — patch `shutil.which` to return None → returns None
- `test_ask_via_exec_timeout_returns_none()` — mock to raise `subprocess.TimeoutExpired` → returns None (does not crash)

### AC-4: Refactor for testability
- Extract parsing into a named function `parse_codex_exec_stdout(stdout: str) -> str | None`
- The function MUST have a docstring explaining both v0.117 and v0.125 contracts
- Existing `ask_via_exec()` must call this new function instead of inlining the logic

### AC-5: Existing behavior preserved (regression)
- `test_main_flow_unchanged()` — when `ask_via_exec` returns a valid response, the rest of `main()` (last-consulted touch, edit-count reset to "0") still works correctly. Patch `subprocess.run` and verify file writes via `tmp_path` fixture.

## Test Commands

ALL must succeed:

```bash
# 1. New parser tests (your additions)
python -m pytest .claude/scripts/test_codex_ask.py -v --tb=short

# 2. Existing 89 enforcer/gate/invariants tests (regression)
python -m pytest .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py .claude/hooks/test_codex_delegate_enforcer_invariants.py -q --tb=line

# 3. Selftest must still pass
python .claude/scripts/dual-teams-selftest.py

# 4. Module import sanity
python -c "import importlib.util; spec = importlib.util.spec_from_file_location('codex_ask', '.claude/scripts/codex-ask.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('OK; has parse_codex_exec_stdout:', hasattr(m, 'parse_codex_exec_stdout'))"
```

## Implementation hints

Current `ask_via_exec()` in `.claude/scripts/codex-ask.py` lines ~104-130
contains the parsing block to extract.

Suggested function shape:

```python
def parse_codex_exec_stdout(stdout: str) -> str | None:
    """Parse Codex CLI exec stdout. Handles both:
      - v0.117 (header + sentinel 'codex' line + response + 'tokens used' in stdout)
      - v0.125 (header in stderr, response only in stdout, optional 'tokens used' trailer)
    Returns response text or None if no parseable response."""
    lines = stdout.strip().splitlines()
    if not lines:
        return None
    # Try v0.117 sentinel-based extraction first (more specific)
    if any(line.strip() == "codex" for line in lines):
        in_resp = False
        out: list[str] = []
        for line in lines:
            if line.strip() == "codex" and not in_resp:
                in_resp = True
                continue
            if in_resp and "tokens used" in line:
                break
            if in_resp:
                out.append(line)
        result = "\n".join(out).strip()
        if result:
            return result
    # v0.125 fallback: take everything until 'tokens used'
    out2: list[str] = []
    for line in lines:
        if line.strip() == "tokens used":
            break
        out2.append(line)
    result2 = "\n".join(out2).strip()
    return result2 or None
```

Use `from unittest.mock import patch` and `pytest.fixture(tmp_path)` for
mocked subprocess and file fixture tests.

## Logging requirements

Apply standard logging to modified or new functions:
- Entry log with `len(stdout)` (don't log full content)
- Exit log with `result_truthy: bool`
- `logger.exception` in any except block

## Self-report format

```
=== TASK Y23 SELF-REPORT ===
- status: pass | fail | blocker
- new tests added: <count>
- new tests PASSING: <count>
- existing 89 tests still passing: yes / no
- selftest: PASS / FAIL
- net lines added: <approx>
- files modified: [list]
- parser approach: <1-2 sentences>
- manual verification (real codex CLI): <"py -3 .claude/scripts/codex-ask.py 'ping say OK'" stdout, first 5 lines>
- NOTE: <surprising findings>
- BLOCKER: <only if status=blocker>
- Final commit SHA: <git -C "<worktree>" rev-parse HEAD>
=== END SELF-REPORT ===
```
