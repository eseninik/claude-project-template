# Codex Implementation Result — Task Z20-security-sandbox-allowlist

- status: pass
- timestamp: 2026-04-26T15:42:01.314068+00:00
- task_file: C:\Bots\Migrator bots\claude-project-template-update\work\criterion-upgrade\task-Z20-security-sandbox-allowlist.md
- base_sha: 17b627db398caeafb31aa0d48d09d4c8970bfba0
- codex_returncode: 1
- scope_status: pass
- scope_message: OK: no modified paths in diff
- tests_all_passed: True
- test_commands_count: 4

## Diff

```diff
(no changes)
```

## Test Output

### `python -m pytest .claude/scripts/test_codex_implement.py -q --tb=line`

- returncode: 0  - passed: True  - timed_out: False

```
--- stdout ---
........................................................................ [ 90%]
........                                                                 [100%]
80 passed in 1.26s
```

### `python -m pytest .claude/hooks/test_enforcer_live_attacks.py -q --tb=line`

- returncode: 0  - passed: True  - timed_out: False

```
--- stdout ---
.........................                                                [100%]
25 passed in 1.88s
```

### `python -m pytest .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py .claude/scripts/test_spawn_agent.py -q --tb=line`

- returncode: 0  - passed: True  - timed_out: False

```
--- stdout ---
........................................................................ [ 39%]
........................................................................ [ 78%]
.......................................                                  [100%]
============================== warnings summary ===============================
.claude\scripts\judge_axes.py:46
  C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z20\codex\task-Z20-security-sandbox-allowlist\.claude\scripts\judge_axes.py:46: PytestCollectionWarning: cannot collect test class 'TestRun' because it has a __init__ constructor (from: .claude/scripts/test_judge.py)
    @dataclass

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
183 passed, 1 warning in 7.88s
```

### `python .claude/scripts/dual-teams-selftest.py`

- returncode: 0  - passed: True  - timed_out: False

```
--- stdout ---
[PASS] preflight-clean-with-sentinel-V1                     (70 ms)
[PASS] preflight-clean-with-sentinel-V2                     (66 ms)
[PASS] is_dual_teams_worktree-true-on-V1                    ( 1 ms)
[PASS] is_dual_teams_worktree-true-on-V2                    ( 1 ms)
[PASS] judge-axes-sees-claude-committed-py                  (33 ms)
[PASS] judge-axes-sees-codex-untracked-py                   (60 ms)
selftest: 6 checks, 6 passed, 0 failed (730 ms)
--- stderr ---
{"json_output": false, "keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: main", "ts": "2026-04-26T15:42:16.431474+00:00"}
{"keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: run_selftest", "ts": "2026-04-26T15:42:16.431474+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: setup_transient_repo", "tmpdir": "C:\\Users\\Lenovo\\AppData\\Local\\Temp\\dual-teams-selftest-8qbqafpy", "ts": "2026-04-26T15:42:16.433479+00:00"}
{"base_sha": "e03538b44db649be6cd283880aab63787c6cef1c", "duration_ms": 334, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: setup_transient_repo", "ts": "2026-04-26T15:42:16.767377+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: load_integrations", "project_root": "C:\\Bots\\Migrator bots\\claude-project-template-update\\worktrees\\criterion-upgrade-z20\\codex\\task-Z20-security-sandbox-allowlist", "ts": "2026-04-26T15:42:16.767377+00:00"}
{"duration_ms": 6, "failures": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: load_integrations", "ts": "2026-04-26T15:42:16.772910+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: build_results", "ts": "2026-04-26T15:42:16.773438+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T15:42:16.773438+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "detail": "git status --porcelain empty", "duration_ms": 70, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T15:42:16.843244+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T15:42:16.843244+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "detail": "git status --porcelain empty", "duration_ms": 66, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T15:42:16.909783+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T15:42:16.909783+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T15:42:16.909783+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T15:42:16.909783+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T15:42:16.909783+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T15:42:17.024837+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "detail": "saw claude_probe.py", "duration_ms": 33, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T15:42:17.057840+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T15:42:17.057840+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "detail": "saw codex_probe.py", "duration_ms": 60, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T15:42:17.117173+00:00"}
{"checks": 6, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: build_results", "ts": "2026-04-26T15:42:17.117173+00:00"}
{"checks": 6, "duration_ms": 730, "failed": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: run_selftest", "passed": 6, "ts": "2026-04-26T15:42:17.162174+00:00"}
{"exit_code": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: main", "ts": "2026-04-26T15:42:17.162174+00:00"}
```

## Self-Report (Codex NOTE/BLOCKER lines)

(no NOTE/BLOCKER lines)

## Codex stderr

```
OpenAI Codex v0.125.0 (research preview)
--------
workdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z20\codex\task-Z20-security-sandbox-allowlist
model: gpt-5.5
provider: chatgpt
approval: never
sandbox: danger-full-access
reasoning effort: xhigh
reasoning summaries: none
session id: 019dca74-6ef1-74c2-b21f-bd0738b9ba27
--------
user
You are the single-task implementer. The task specification below is IMMUTABLE.
Write code to satisfy all Acceptance Criteria. Do NOT modify files listed in
Forbidden Paths or Read-Only Files. After writing code, run every Test Command
listed in the task and report the result in your self-report.
Any AGENTS.md or CLAUDE.md in the worktree is authoritative background context.

---- TASK SPECIFICATION ----

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


---- END TASK SPECIFICATION ----
Return a short self-report at the end of your run using lines starting with
`NOTE:` for observations and `BLOCKER:` for unresolved problems.

ERROR: You've hit your usage limit. Upgrade to Pro (https://chatgpt.com/explore/pro), visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at Apr 29th, 2026 5:54 PM.
ERROR: You've hit your usage limit. Upgrade to Pro (https://chatgpt.com/explore/pro), visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at Apr 29th, 2026 5:54 PM.
2026-04-26T15:42:03.819259Z ERROR codex_core::session: failed to record rollout items: thread 019dca74-6ef1-74c2-b21f-bd0738b9ba27 not found
```
