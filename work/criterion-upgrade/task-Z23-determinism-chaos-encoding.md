---
task_id: Z23-determinism-chaos-encoding
title: Criterion 4 Determinism — chaos test harness + encoding standardization + CLI flag abstraction
executor: dual
risk_class: routine
speed_profile: balanced
---

# Task Z23

## Goal

Criterion 4 (Determinism) currently 5/10. Three pillars need landing:

1. **Chaos test harness** — without measurement no determinism claim. Run
   N identical task specs (mocked at the codex-ask level so no real Codex
   needed), measure variance in outputs. Flag if variance > 5%.

2. **Encoding standardization** — UTF-8 no-BOM, deliberate LF or CRLF.
   Z11 hit BOM pollution from PowerShell `-Encoding utf8`. Y26 codified
   `[System.Text.UTF8Encoding]::new($false)`. But codex-implement.py and
   spawn-agent.py have other write paths — audit + lock with tests.

3. **CLI flag abstraction audit** — Y26 extracted `_build_codex_argv()`
   helper. Verify it is the ONLY call site for Codex CLI argv construction.
   Add a guard test that fails if anywhere else in the codebase a literal
   `--dangerously-bypass-approvals-and-sandbox` or `codex.cmd exec ...`
   appears outside the helper.

## Three coordinated improvements

### Improvement 1 — Chaos test harness

New file `.claude/scripts/test_determinism_chaos.py` (test-only, exempt
from cover). Runs `_build_codex_argv` and `_build_codex_env` 30 times
with identical inputs, asserts:

- Same `argv[0:8]` for all 30 (deterministic argv prefix)
- Same `set(env.keys())` for all 30 (deterministic env keys)
- `CODEX_FS_READ_ALLOWLIST` value identical across all 30 (no random ordering)
- No timing-dependent values in argv (no PID, no timestamp)

```python
def test_argv_chaos_30_runs_identical():
    """30 invocations of _build_codex_argv produce identical argv."""
    results = [_build_codex_argv("codex", "gpt-5.5", Path("/wt"), "<provider>") for _ in range(30)]
    assert all(r == results[0] for r in results), "argv non-deterministic"

def test_env_chaos_30_runs_identical():
    """30 invocations of _build_codex_env produce identical env (after sorting)."""
    results = [_build_codex_env(Path("/wt"), Path("/proj")) for _ in range(30)]
    keys_sets = [frozenset(r.keys()) for r in results]
    assert all(k == keys_sets[0] for k in keys_sets), "env keys non-deterministic"
    allowlists = [r.get("CODEX_FS_READ_ALLOWLIST", "") for r in results]
    assert all(a == allowlists[0] for a in allowlists), "FS allowlist non-deterministic"
```

### Improvement 2 — Encoding standardization

Audit `.claude/scripts/codex-implement.py` and `.claude/scripts/spawn-agent.py`
for `.write_text()`, `open(..., 'w')`, `subprocess.run` writes. For each
text-write site, ensure `encoding='utf-8'` is explicit AND `newline=''` or
`newline='\n'` is specified deliberately.

Add tests that read random commit-output files and assert no BOM marker
(`﻿` prefix). Test the `Set-Content -Encoding utf8` pattern in
`spawn-agent.py` Y14 block also has UTF-8 no-BOM equivalent.

```python
def test_no_bom_in_codex_implement_outputs(tmp_path):
    """codex-implement.py result.md / diff outputs use UTF-8 no-BOM."""
    result_path = tmp_path / "task-test-result.md"
    write_result_file(result_path, ...)
    raw = result_path.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), "BOM in result.md output"

def test_spawn_agent_y14_block_uses_utf8_no_bom_template():
    """spawn-agent.py Y14 instruction block embeds UTF8Encoding(False) (no-BOM)."""
    block = build_y14_block()
    assert "UTF8Encoding" in block and "$false" in block, "no-BOM template missing"
```

### Improvement 3 — CLI flag abstraction audit

Add test that greps the codebase for direct Codex CLI invocations outside
`_build_codex_argv()`:

```python
def test_no_direct_codex_cli_outside_helper():
    """Only _build_codex_argv() may construct Codex CLI argv. Any other
    call site is a maintainability risk (Y26 lesson)."""
    forbidden_patterns = [
        "--dangerously-bypass-approvals-and-sandbox",
        "--sandbox workspace-write",
        "--full-auto",
    ]
    repo_root = Path(__file__).resolve().parents[2]
    py_files = list(repo_root.glob(".claude/scripts/*.py")) + list(repo_root.glob(".claude/hooks/*.py"))
    py_files = [f for f in py_files if f.name not in {"codex-implement.py"}]  # the helper home
    for pyf in py_files:
        text = pyf.read_text(encoding="utf-8", errors="replace")
        for pat in forbidden_patterns:
            assert pat not in text, f"{pyf.name} hardcodes Codex CLI flag: {pat}"
```

Note: the test explicitly EXCLUDES `codex-implement.py` (the legitimate
home) AND task spec markdown files (which document the flags).

## Scope Fence

```
.claude/scripts/test_determinism_chaos.py
.claude/scripts/test_codex_implement.py
.claude/scripts/test_spawn_agent.py
```

DO NOT modify any other file. This is a TEST-ONLY task — no production
code changes. Tests assert current implementation IS deterministic +
encoding-correct + flag-abstracted. If any test fails, document as
follow-up but do not fix the production code in this task.

## Read-Only Files / Evaluation Firewall

- `work/criterion-upgrade/task-Z23-determinism-chaos-encoding.md`
- `.claude/scripts/codex-implement.py`
- `.claude/scripts/spawn-agent.py`
- `.claude/hooks/codex-delegate-enforcer.py`

## Acceptance Criteria

### AC-1: Chaos test file exists with 2 tests

`.claude/scripts/test_determinism_chaos.py` contains:
- `test_argv_chaos_30_runs_identical`
- `test_env_chaos_30_runs_identical`
Both PASS.

### AC-2: Encoding tests pass

In `test_codex_implement.py`:
- `test_no_bom_in_codex_implement_outputs` PASSES.

In `test_spawn_agent.py`:
- `test_spawn_agent_y14_block_uses_utf8_no_bom_template` PASSES.

### AC-3: CLI flag abstraction test passes

In `test_codex_implement.py`:
- `test_no_direct_codex_cli_outside_helper` PASSES.

### AC-4: Existing 88+5 tests still pass

```bash
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_spawn_agent.py -q --tb=line
```

### AC-5: Live attack matrix 25/25 still passes

```bash
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -q --tb=line
```

### AC-6: Selftest 6/6
`python .claude/scripts/dual-teams-selftest.py`

## Test Commands

```bash
# 1. Determinism chaos
python -m pytest .claude/scripts/test_determinism_chaos.py -v --tb=line

# 2. test_codex_implement (existing + new)
python -m pytest .claude/scripts/test_codex_implement.py -q --tb=line

# 3. test_spawn_agent (existing + new)
python -m pytest .claude/scripts/test_spawn_agent.py -q --tb=line

# 4. Live attack matrix (regression)
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -q --tb=line

# 5. Other suites
python -m pytest .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line

# 6. Selftest
python .claude/scripts/dual-teams-selftest.py
```

## Implementation hints

- `_build_codex_argv` and `_build_codex_env` are pure functions in codex-implement.py — easy to import and call in tests.
- For chaos test, use `for _ in range(30)`. If the helper has any non-deterministic side effect (random.seed unset, time-based env), test will catch it.
- Encoding test: `result_path.read_bytes()[:3]` — if equals `b"\xef\xbb\xbf"` that's BOM. Assert NOT startswith.
- Flag abstraction test: glob the .py files, read content, check substring. Exclude the helper itself.
- All tests are pure Python no real Codex needed. Fast.

## Self-report format

```
=== TASK Z23 SELF-REPORT ===
- status: pass | fail | blocker
- Improvement 1 (chaos) approach: <1 line>
- Improvement 2 (encoding) approach: <1 line>
- Improvement 3 (CLI abstraction) approach: <1 line>
- new tests: <count> (expected 5 — 2 chaos + 2 encoding + 1 abstraction)
- existing 88+5 tests pass: yes / no
- attack matrix 25/25: yes / no
- selftest 6/6: PASS / FAIL
- net lines: <approx>
- files modified: [list]
- chaos variance observed (none expected): <none / list>
- BOM detected anywhere: yes / no
- direct CLI flags outside helper: <none / list>
- NOTE: <surprising>
- BLOCKER: <only if>
- Final commit SHA: <SHA>
=== END SELF-REPORT ===
```
