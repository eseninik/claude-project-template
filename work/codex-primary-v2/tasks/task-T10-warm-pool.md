---
executor: dual
risk_class: routine
speed_profile: balanced
---

# Task T10: `.claude/scripts/codex-pool.py` — warm Codex app-server pool

## Your Task

Create a script that manages N warm `codex app-server` instances on distinct localhost ports, so `codex-implement.py` / `codex-inline-dual.py` / `codex-wave.py` can reuse them instead of cold-starting a new `codex exec` process each call. Saves ~5-10 s per invocation.

**Scope for this task:** only the pool management script (`codex-pool.py`) + its tests. Wiring into `codex-implement.py` to prefer pool is out of scope — separate follow-up. For now the script just manages the pool lifecycle.

## Scope Fence

**Allowed:**
- `.claude/scripts/codex-pool.py` (new)
- `.claude/scripts/test_codex_pool.py` (new — unit tests)

**Forbidden:**
- Any other file, especially `codex-implement.py` / `-inline-dual.py` / `-wave.py` (wiring is separate task)

## Test Commands

```bash
python .claude/scripts/test_codex_pool.py
python .claude/scripts/codex-pool.py --help
python .claude/scripts/codex-pool.py status
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: CLI with subcommands: `start --size <N>`, `stop`, `status`, `health`.
- [ ] AC2: `start --size 2` (default) launches N `codex app-server --listen ws://127.0.0.1:<port>` subprocesses. Ports auto-allocated starting at 4510, incrementing. Records each instance's PID + port + start_time in `<project_root>/.codex/pool-state.json`.
- [ ] AC3: `stop` terminates all instances (Windows: `taskkill /T /F /PID`; POSIX: SIGTERM then SIGKILL after 3s). Removes state file.
- [ ] AC4: `status` prints table: pool-id, port, PID, alive?, age_s, for each instance. Plus a summary line.
- [ ] AC5: `health` performs a quick websocket ping on each port; reports per-instance health + summary.
- [ ] AC6: If state file exists but pool is partly dead (PIDs gone) → `start` cleans stale entries before launching; `status` marks them.
- [ ] AC7: Logs go to `.claude/logs/codex-pool.log`.
- [ ] AC8: Unit tests (≥8) using mocks for subprocess.Popen / websocket:
  - start creates N instances, state file matches
  - stop terminates all + cleans state
  - status formats table correctly
  - health ping logic
  - stale-entry cleanup on restart
  - default --size is 2
  - windows-vs-posix branch for termination
  - state schema round-trip
- [ ] AC9: Stdlib only (except: may use `websocket-client` if importable, else skip health ping gracefully with log warning)
- [ ] AC10: Under 350 lines script + 350 lines tests.
- [ ] All Test Commands exit 0.

## Constraints

- Windows-compatible
- Atomic state-file updates via os.replace (same pattern as circuit-state.json in T8T9)
- Pool state file schema must be future-compatible — include `schema_version: 1`

## Handoff Output

Standard `=== PHASE HANDOFF: T10-warm-pool ===` block.

## Iteration History
(First round.)
