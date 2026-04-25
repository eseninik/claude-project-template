---
executor: dual
risk_class: routine
reasoning: high
speed_profile: balanced
---

# Task Y11-LIVE: `.claude/scripts/python-tool-version.py` — Y11 fix live verification (minimal CLI)

## Your Task

Tiny stand-alone CLI that prints versions of common Python tools used in this project (`python`, `pytest`, `mypy`, `ruff`, `black`) — useful for debugging "wrong tool version" issues. **Primary purpose of this task is to live-verify the Y11 sentinel fix** — sub-agents should NOT hit harness Permission UI denials when using direct Edit/Write tools.

## Scope Fence

**Allowed:**
- `.claude/scripts/python-tool-version.py` (new)
- `.claude/scripts/test_python_tool_version.py` (new)

**Forbidden:** any other path.

## Test Commands

```bash
py -3 .claude/scripts/test_python_tool_version.py
py -3 .claude/scripts/python-tool-version.py --help
py -3 .claude/scripts/python-tool-version.py
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: CLI: `python-tool-version.py [--json] [--tool python|pytest|mypy|ruff|black|all] [--verbose]`. Default scans all five tools.
- [ ] AC2: For each tool, runs `<tool> --version` (use `subprocess.run` with `capture_output=True, text=True, timeout=10`). Catches `FileNotFoundError` → reports `not_found`. Catches `subprocess.TimeoutExpired` → reports `timeout`.
- [ ] AC3: Default human-readable output:
   ```
   python  : Python 3.12.0
   pytest  : not_found
   mypy    : 1.8.0
   ruff    : not_found
   black   : 24.1.1
   ```
- [ ] AC4: `--json` emits `{"generated_at","tools":[{"name","version","status":"ok|not_found|timeout"}]}`.
- [ ] AC5: Exit 0 always (no tool installed is normal). Use `logging` for warnings.
- [ ] AC6: Stdlib only. Windows-compatible (use `shutil.which` to resolve before subprocess).
- [ ] AC7: Under 150 lines script + 150 lines tests.
- [ ] AC8: Unit tests (>=5): (a) all tools resolved happy path (with mocked subprocess), (b) tool not found returns `not_found` status, (c) tool timeout returns `timeout` status, (d) `--json` schema round-trip, (e) `--tool python` returns only python.
- [ ] All Test Commands above exit 0.

## Constraints

- Stdlib only. Use `subprocess`, `argparse`, `logging`, `json`, `dataclasses`, `pathlib`.
- Don't pip install anything. The point is to REPORT what's installed.
- Cross-platform — `shutil.which` for tool resolution.

## Handoff Output

Standard `=== PHASE HANDOFF: Y11-LIVE-claude ===` with:
- Diff stats
- Test count
- **CRITICAL:** one-line note `permission UI denials encountered: NONE` or `permission UI denials encountered: <list>` — this is the live verification of the Y11 fix.
