---
task_id: Z20-security-sandbox-allowlist
title: Criterion 3 Security — filesystem read allowlist + auth.json protection + OS sandbox detection
executor: dual
risk_class: high-stakes
speed_profile: balanced
---

# Task Z20

## Goal

Criterion 3 (Security) currently 7/10. `--dangerously-bypass-approvals-and-sandbox`
is capability escalation; `--cd <worktree>` only constrains working
directory, not actual filesystem access. Defense in depth needs:

1. Explicit filesystem-read allowlist (env-based restriction or post-hoc check)
2. Auth-json sensitive-path protection (Codex must not read `~/.codex/auth.json` etc.)
3. OS-level sandbox wrap (Sandboxie Windows / firejail Linux) when available

OS-level sandbox installation is system-dependent — implement detection
+ conditional wrap. If neither installed, document as Y28 follow-up and
count this AC as best-effort given environment.

## Three coordinated improvements

### Improvement 1 — Filesystem read allowlist via env

Add to `.claude/scripts/codex-implement.py` `run_codex()` argv:
- Set `CODEX_FS_READ_ALLOWLIST` env var listing allowed-to-read paths
  (default: `<worktree>;<TEMP>;<auth.json absent>`).
- New helper `_build_codex_env(worktree, project_root) -> dict[str, str]`
  returns environment dict with restricted reads.
- Document: this is heuristic (env-var read by Codex CLI may or may not
  honor it depending on version). Best-effort.

Add tests:
- `test_build_codex_env_excludes_codex_auth` — env dict does NOT include
  `~/.codex/auth.json` parent in allowlist
- `test_build_codex_env_includes_worktree` — env includes worktree path

### Improvement 2 — Audit sensitive paths reachable from worktree

Add `_audit_sensitive_paths(worktree, project_root) -> list[str]`:
- Returns list of sensitive paths (auth.json, ssh keys, .env files,
  credentials.json) currently reachable via filesystem walk from worktree.
- Logs warnings for each via `logger.warning("sensitive path reachable", path=...)`.
- Called once at start of `run_codex()`.

Add tests:
- `test_audit_finds_codex_auth_when_reachable_via_home` — synthetic case where
  worktree is under user home, auth.json reachable → logged warning
- `test_audit_clean_when_no_sensitive_paths` — empty list

### Improvement 3 — OS-level sandbox detection (conditional wrap)

Add `_detect_os_sandbox() -> Optional[tuple[str, list[str]]]`:
- On Windows: check if Sandboxie `Start.exe` exists at standard paths
  (`C:\Program Files\Sandboxie-Plus\Start.exe` etc.). If yes, return
  `("sandboxie", ["Start.exe", "/box:codex"])`.
- On Linux: check if `firejail` in PATH. If yes, return
  `("firejail", ["firejail", "--noroot", "--private-tmp"])`.
- If neither, return None.

Modify `_build_codex_argv()` to **prepend** sandbox wrap if detected:
```python
sandbox = _detect_os_sandbox()
if sandbox:
    name, prefix_argv = sandbox
    cmd = prefix_argv + cmd
```

Add tests (mocked):
- `test_detect_os_sandbox_windows_sandboxie_present` — patch Path.exists to True for Sandboxie path → return tuple
- `test_detect_os_sandbox_linux_firejail_present` — patch shutil.which to return path → return tuple
- `test_detect_os_sandbox_neither_returns_none` — patch both to absent → None
- `test_argv_prepends_sandbox_wrap_when_detected` — when detection returns tuple, argv starts with prefix

## Scope Fence

```
.claude/scripts/codex-implement.py
.claude/scripts/test_codex_implement.py
```

DO NOT modify any other file.

## Read-Only Files / Evaluation Firewall

- `work/criterion-upgrade/task-Z20-security-sandbox-allowlist.md` (this file)
- `.claude/hooks/codex-delegate-enforcer.py`
- `.claude/scripts/codex-scope-check.py`

## Acceptance Criteria

### AC-1: Filesystem allowlist tests pass
2 new tests for `_build_codex_env`.

### AC-2: Sensitive paths audit tests pass
2 new tests for `_audit_sensitive_paths`.

### AC-3: OS sandbox detection tests pass
4 new tests for `_detect_os_sandbox` + `_build_codex_argv` integration.

### AC-4: Existing 72+ test_codex_implement tests still pass

```bash
python -m pytest .claude/scripts/test_codex_implement.py -q --tb=line
```

### AC-5: Live attack matrix 25/25 still passes
```bash
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -q --tb=line
```

### AC-6: Selftest 6/6
`python .claude/scripts/dual-teams-selftest.py`

## Test Commands

```bash
python -m pytest .claude/scripts/test_codex_implement.py -q --tb=line
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -q --tb=line
python -m pytest .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py .claude/scripts/test_spawn_agent.py -q --tb=line
python .claude/scripts/dual-teams-selftest.py
```

## Implementation hints

- Use `os.environ.copy()` for env dict, then add/override `CODEX_FS_READ_ALLOWLIST`.
- Sensitive path list: `~/.codex/auth.json`, `~/.ssh/`, project root `.env`, `credentials.json`. Use `Path.home() / ".codex" / "auth.json"` etc.
- `_detect_os_sandbox` should NOT log if neither found — silent fallback.
  Log at INFO level if detected and used.
- Sandboxie detection: `[Path("C:/Program Files/Sandboxie-Plus/Start.exe"), Path("C:/Program Files/Sandboxie/Start.exe")]`.
- firejail: `shutil.which("firejail")` returns path or None.
- Mocking: use `unittest.mock.patch` for `pathlib.Path.exists` and `shutil.which`.

## Self-report format

```
=== TASK Z20 SELF-REPORT ===
- status: pass | fail | blocker
- Improvement 1 (FS allowlist) approach: <1 line>
- Improvement 2 (sensitive audit) approach: <1 line>
- Improvement 3 (OS sandbox detection) approach: <1 line>
- new tests: <count>
- existing 72+ test_codex_implement pass: yes / no
- live attack matrix 25/25: yes / no
- selftest 6/6: PASS / FAIL
- Sandboxie / firejail detected on this machine: yes / no
- net lines: <approx>
- files modified: [list]
- NOTE: <surprising>
- BLOCKER: <only if>
- Final commit SHA: <SHA>
=== END SELF-REPORT ===
```
