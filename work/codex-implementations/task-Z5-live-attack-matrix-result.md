# Codex Implementation Result — Task Z5-live-attack-matrix

- status: fail
- timestamp: 2026-04-26T08:58:35.990011+00:00
- task_file: C:\Bots\Migrator bots\claude-project-template-update\work\codify-enforcement\task-Z5-live-attack-matrix.md
- base_sha: cf871cf03469aceebf5e06e5457ec1e19c4a7a07
- codex_returncode: 0
- scope_status: pass
- scope_message: OK: no modified paths in diff
- tests_all_passed: False
- test_commands_count: 3

## Diff

```diff
(no changes)
```

## Test Output

### `python -m pytest .claude/hooks/test_enforcer_live_attacks.py -v --tb=short`

- returncode: 4  - passed: False  - timed_out: False

```
--- stdout ---
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.2, pluggy-1.6.0 -- C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
plugins: anyio-4.12.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 0 items

============================ no tests ran in 0.01s ============================
--- stderr ---
ERROR: file or directory not found: .claude/hooks/test_enforcer_live_attacks.py
```

### `python -m pytest .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/scripts/test_codex_ask.py -q --tb=line`

- returncode: 0  - passed: True  - timed_out: False

```
--- stdout ---
........................................................................ [ 68%]
.................................                                        [100%]
105 passed in 3.27s
```

### `python .claude/scripts/dual-teams-selftest.py`

- returncode: 0  - passed: True  - timed_out: False

```
--- stdout ---
[PASS] preflight-clean-with-sentinel-V1                     (60 ms)
[PASS] preflight-clean-with-sentinel-V2                     (55 ms)
[PASS] is_dual_teams_worktree-true-on-V1                    ( 1 ms)
[PASS] is_dual_teams_worktree-true-on-V2                    ( 1 ms)
[PASS] judge-axes-sees-claude-committed-py                  (27 ms)
[PASS] judge-axes-sees-codex-untracked-py                   (49 ms)
selftest: 6 checks, 6 passed, 0 failed (534 ms)
--- stderr ---
{"json_output": false, "keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: main", "ts": "2026-04-26T09:02:55.216781+00:00"}
{"keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: run_selftest", "ts": "2026-04-26T09:02:55.216781+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: setup_transient_repo", "tmpdir": "C:\\Users\\Lenovo\\AppData\\Local\\Temp\\dual-teams-selftest-lgi8lpxt", "ts": "2026-04-26T09:02:55.217776+00:00"}
{"base_sha": "96460b543e115c17ab628b5b311ad08851cdf883", "duration_ms": 242, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: setup_transient_repo", "ts": "2026-04-26T09:02:55.459406+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: load_integrations", "project_root": "C:\\Bots\\Migrator bots\\claude-project-template-update\\worktrees\\codify-enforcement-z5\\codex\\task-Z5-live-attack-matrix", "ts": "2026-04-26T09:02:55.459406+00:00"}
{"duration_ms": 5, "failures": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: load_integrations", "ts": "2026-04-26T09:02:55.464702+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: build_results", "ts": "2026-04-26T09:02:55.464702+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T09:02:55.464702+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "detail": "git status --porcelain empty", "duration_ms": 60, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T09:02:55.524385+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T09:02:55.524385+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "detail": "git status --porcelain empty", "duration_ms": 55, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T09:02:55.579442+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T09:02:55.579442+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T09:02:55.579442+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T09:02:55.579442+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T09:02:55.579442+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T09:02:55.640600+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "detail": "saw claude_probe.py", "duration_ms": 27, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T09:02:55.667606+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T09:02:55.667606+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "detail": "saw codex_probe.py", "duration_ms": 49, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T09:02:55.716527+00:00"}
{"checks": 6, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: build_results", "ts": "2026-04-26T09:02:55.716527+00:00"}
{"checks": 6, "duration_ms": 534, "failed": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: run_selftest", "passed": 6, "ts": "2026-04-26T09:02:55.750814+00:00"}
{"exit_code": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: main", "ts": "2026-04-26T09:02:55.750814+00:00"}
```

## Self-Report (Codex NOTE/BLOCKER lines)

- NOTE: I inspected the enforcer and reference tests, and prepared the new live matrix file, but `apply_patch` was rejected because this session is in read-only sandbox mode with approval disabled.
- NOTE: Static inspection found a likely contract mismatch: the current enforcer returns exit `0` and emits deny JSON to stdout, while this task asks tests to expect exit `2` plus stderr.
- NOTE: This worktree also contains `.dual-base-ref`, so tests using `CLAUDE_PROJECT_DIR=REPO_ROOT` may hit the current dual-worktree allow bypass before vector-specific denial logic.
- BLOCKER: Cannot create `.claude/hooks/test_enforcer_live_attacks.py` or run the required new test command because filesystem writes and the pytest command were blocked by policy in this environment.

## Codex stderr

```
OpenAI Codex v0.125.0 (research preview)
--------
workdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
model: gpt-5.5
provider: chatgpt
approval: never
sandbox: read-only
reasoning effort: xhigh
reasoning summaries: none
session id: 019dc903-16c3-7e82-89f7-90ea8ce9d53f
--------
user
You are the single-task implementer. The task specification below is IMMUTABLE.
Write code to satisfy all Acceptance Criteria. Do NOT modify files listed in
Forbidden Paths or Read-Only Files. After writing code, run every Test Command
listed in the task and report the result in your self-report.
Any AGENTS.md or CLAUDE.md in the worktree is authoritative background context.

---- TASK SPECIFICATION ----

---
task_id: Z5-live-attack-matrix
title: End-to-end live attack matrix for codex-delegate-enforcer (12 bypass vectors via fake-codex shim)
executor: dual
risk_class: high-stakes
speed_profile: thorough
---

# Task Z5 — Live attack matrix for codex-delegate-enforcer

## Goal

Build a **subprocess-level live integration test harness** that proves
all 12 documented bypass vectors are blocked by the Z1 enforcer, AND
that the 6 positive controls are allowed. Each test crafts a `PreToolUse`
JSON payload, pipes it via stdin into `python .claude/hooks/codex-delegate-enforcer.py`
as a subprocess, asserts exit code (2=deny, 0=allow) + stderr substring.

Why beyond the existing 35 unit tests:
- Unit tests `import` the hook module — they may miss env-var, working
  directory, stdin parsing, or process-spawn bugs that only surface in
  the actual subprocess invocation Claude Code harness uses.
- Z1 documents 12 bypass vectors. Unit tests cover ~7-8. We need EVERY
  vector exercised live at the binary contract level.
- The harness becomes the regression suite for any future enforcer change.

**Codex review feedback baked into this design:** use a **fake codex
shim** for tests that depend on Codex availability (PATH-injected fake
`codex.cmd`). Do NOT rely on real installed Codex. This makes tests
deterministic regardless of developer's CLI state.

## The 18 test cases (12 deny + 6 allow)

### Deny cases (each must produce exit code 2 + reason in stderr)

| # | Vector | Crafted tool call |
|---|--------|-------------------|
| V1 | `work/**` blanket exemption (Invariant 1) | `Edit(file_path="work/sync-template-to-target.py")` |
| V2 | NotebookEdit not intercepted (Invariant 2) | `NotebookEdit(notebook_path="src/foo.ipynb", new_source="...")` |
| V3 | Bash heredoc + git apply | `Bash(command="cat > /tmp/p.diff <<EOF\\n...\\nEOF\\ngit apply /tmp/p.diff")` |
| V4 | Bash sed -i on code | `Bash(command="sed -i 's/x/y/g' src/main.py")` |
| V5 | Bash cp/mv between code paths | `Bash(command="cp src/a.py src/b.py")` |
| V6 | PowerShell Set-Content on code | `Bash(command='powershell -NoProfile -Command "Set-Content -Path src/foo.py -Value test"')` |
| V7 | python -c with file write | `Bash(command='python -c "open(\\'src/x.py\\',\\'w\\').write(\\'\\')"')` |
| V8 | Edit on `.claude/scripts/**/*.py` | `Edit(file_path=".claude/scripts/rogue.py")` |
| V9 | Bash invokes a script that mass-mutates | `Bash(command="py -3 work/sync-template-to-target.py --apply")` |
| V10 | git checkout file restore | `Bash(command="git checkout main src/auth.py")` |
| V11 | `worktrees/**` over-exemption (no sentinel) | `Edit(file_path="worktrees/random-not-dual-teams/foo.py")` (where that worktree has NO `.dual-base-ref`) |
| V12 | 15-min staleness with wrong path | `Edit(file_path="src/new.py")` while a recent (<15 min) result.md covers `src/old.py` only |

### Allow cases (each must produce exit code 0)

| # | Allow case | Sample |
|---|------------|--------|
| A1 | Edit on `.md` in `work/` | `Edit(file_path="work/notes.md")` |
| A2 | Bash `pytest` | `Bash(command="pytest tests/")` |
| A3 | Bash `git status` | `Bash(command="git status")` |
| A4 | Bash `cp README.md /tmp/` | `Bash(command="cp README.md /tmp/")` |
| A5 | Edit inside `.dual-base-ref` worktree (sentinel allows) | `Edit(file_path="<tmp_worktree>/.claude/foo.py")` where `<tmp_worktree>/.dual-base-ref` exists |
| A6 | Edit with valid recent path-exact cover | `Edit(file_path="src/auth.py")` after writing `task-fake-result.md` with `status:pass` and Scope Fence containing `src/auth.py` |

## Scope Fence — files you MAY modify

```
.claude/hooks/test_enforcer_live_attacks.py
```

DO NOT modify any other file. If you discover a real enforcer bug while
running tests, do NOT fix the enforcer in this run — record as `NOTE:`
in self-report so a follow-up can address it. This task only BUILDS the
test matrix.

## Read-Only Files / Evaluation Firewall

- `work/codify-enforcement/task-Z5-live-attack-matrix.md` (this file)
- `.claude/hooks/codex-delegate-enforcer.py` (DO NOT modify, only invoke as subprocess)
- `.claude/hooks/test_codex_delegate_enforcer.py`,
  `.claude/hooks/test_codex_delegate_enforcer_invariants.py` (reference only)

## Acceptance Criteria

A new test file `.claude/hooks/test_enforcer_live_attacks.py` must exist
and contain ALL 18 test functions. The file must run via:

```bash
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -v --tb=short
```

Test naming convention (lowercase, descriptive):
- `test_v01_work_py_denied`, `test_v02_notebook_edit_denied`, …,
  `test_v12_stale_artifact_wrong_path_denied`
- `test_a01_work_md_allowed`, `test_a02_bash_pytest_allowed`, …,
  `test_a06_valid_cover_allowed`

Each test must:
1. Build a `PreToolUse` JSON payload as the dict the harness sends
   (use existing unit tests as schema reference — typically
   `{"tool_name": "...", "tool_input": {...}, "session_id": "..."}`)
2. Spawn the hook: `subprocess.run([sys.executable, str(HOOK_PATH)],
   input=json.dumps(payload), capture_output=True, text=True, timeout=10,
   env={**os.environ, "CLAUDE_PROJECT_DIR": str(REPO_ROOT)})`
3. For DENY tests: assert `r.returncode == 2`, assert reason substring
   in `r.stderr` (substring identifying invariant or target path).
4. For ALLOW tests: assert `r.returncode == 0`.

For tests requiring a recent cover artifact (V12, A6): use a `tmp_path`
pytest fixture to write a fake `task-fake-Z5-result.md` into
`work/codex-implementations/` of the repo root with appropriate
`status:pass` and Scope Fence content; clean up after test (use a
`yield` fixture).

For tests requiring a worktree directory (V11, A5):
- A5: create `tmp_path/wt/.dual-base-ref` (any content), then run hook
  with `CLAUDE_PROJECT_DIR=tmp_path/wt`, target a `.py` file inside.
- V11: create `tmp_path/worktrees/random/foo.py` (NO sentinel anywhere),
  then run hook with `CLAUDE_PROJECT_DIR=<repo root>`, target the file.
  The hook should NOT find `.dual-base-ref` walking up → DENY.

## Test Commands

ALL must succeed:

```bash
# 1. The new live attack matrix
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -v --tb=short

# 2. Existing 89 enforcer/gate/invariants tests (regression)
python -m pytest .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/scripts/test_codex_ask.py -q --tb=line

# 3. Selftest must still pass
python .claude/scripts/dual-teams-selftest.py
```

The new file's expected count: 18 test functions. **Some MAY fail** —
that is acceptable for THIS task because failures reveal genuine
enforcer gaps (Z7+ will fix). The deliverable is the test FILE itself
plus the gap inventory in the self-report.

## Implementation hints

- Use `pathlib.Path(__file__).resolve().parents[2]` to locate repo root
  from inside the test file.
- Use `subprocess.run(..., timeout=10)` — enforcer should be fast (<1s).
- Use `pytest.fixture` for `tmp_cover_artifact` and `tmp_worktree` so
  each test is hermetic.
- Use `pytest.mark.parametrize` if it makes the 12 deny tests cleaner —
  keep test names descriptive (so failures are obvious).
- Read the existing unit tests to understand the JSON schema the hook
  expects on stdin and how it returns deny/allow signals (exit code +
  optional JSON `permissionDecision` in stdout).
- For tests that need fresh cover, write the artifact ATOMICALLY before
  the subprocess call (write+close, then run).
- Prefer relative paths in payloads where possible.

## Logging requirements

The test file is a test file — no production logging required. Each
test SHOULD have a docstring explaining which vector it covers and the
expected reason substring. Example:
```python
def test_v05_bash_cp_code_to_code_denied(repo_root):
    """V5 — Bash cp between two code paths must DENY (Invariant 2)."""
    ...
```

## Self-report format

```
=== TASK Z5 SELF-REPORT ===
- status: pass | fail | blocker
- new tests added: <count> (expected 18)
- new tests PASSING (no enforcer gap): <count>
- new tests FAILING (real enforcer gap to fix in Z7+): <count>
- existing 105 tests still passing: yes / no
- selftest 6/6: PASS / FAIL
- net lines added: <approx>
- files modified: [list]
- enforcer-stdin-schema: <one line — what the hook expects>
- vectors that REVEALED a real enforcer gap: [list V01..V12 with brief reason]
- NOTE: <surprising findings>
- BLOCKER: <only if you couldn't even build the harness>
- Final commit SHA: <git rev-parse HEAD>
=== END SELF-REPORT ===
```


---- END TASK SPECIFICATION ----
Return a short self-report at the end of your run using lines starting with
`NOTE:` for observations and `BLOCKER:` for unresolved problems.

codex
I’ll first inspect the hook and nearby tests to match the live subprocess contract exactly, then I’ll add only the allowed test file if the sandbox permits writes.
2026-04-26T08:58:50.923953Z ERROR codex_core::tools::router: error=`"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'if (Test-Path AGENTS.md) { Get-Content AGENTS.md -TotalCount 220 }'` rejected: blocked by policy
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-ChildItem -Force' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg --files .claude/hooks .claude/scripts work | Select-Object -First 200' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'if (Test-Path AGENTS.md) { Get-Content AGENTS.md -TotalCount 220 }' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
 declined in 0ms:
`"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'if (Test-Path AGENTS.md) { Get-Content AGENTS.md -TotalCount 220 }'` rejected: blocked by policy
2026-04-26T08:58:51.105437Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 0.2 seconds
Output:
.claude/hooks\write-validate.py
.claude/hooks\truthguard.py
.claude/hooks\tool-failure-logger.py
.claude/hooks\test_watchdog_fix.py
.claude/hooks\test_curation.py
.claude/hooks\test_codex_gate.py
.claude/hooks\test_codex_delegate_enforcer_invariants.py
.claude/hooks\test_codex_delegate_enforcer.py
.claude/hooks\task-completed-gate.py
.claude/hooks\session-task-class.py
.claude/hooks\session-orient.py
.claude/hooks\pre-compact-save.py
.claude/hooks\hook_base.py
.claude/hooks\config-protection.py
.claude/hooks\codex-watchdog.py
.claude/hooks\codex-stop-opinion.py
.claude/hooks\codex-review.sh
.claude/hooks\codex-review.py
.claude/hooks\codex-parallel.py
.claude/hooks\codex-gate.py
.claude/hooks\codex-delegate-enforcer.py
.claude/hooks\codex-broker.py
.claude/scripts\worktree-cleaner.py
.claude/scripts\verdict-summarizer.py
.claude/scripts\validate-configs.py
.claude/scripts\test_worktree_cleaner.py
.claude/scripts\test_verdict_summarizer.py
.claude/scripts\test_task_spec_validator.py
.claude/scripts\test_spawn_agent.py
.claude/scripts\test_knowledge_decay_report.py
.claude/scripts\test_judge.py
.claude/scripts\test_dual_teams_spawn.py
.claude/scripts\test_dual_teams_selftest.py
.claude/scripts\test_dual_history_archive.py
.claude/scripts\test_codex_wave.py
.claude/scripts\test_codex_scope_check.py
.claude/scripts\test_codex_pool.py
.claude/scripts\test_codex_inline_dual.py
.claude/scripts\test_codex_implement.py
.claude/scripts\test_codex_cost_report.py
.claude/scripts\test_codex_ask.py
.claude/scripts\task-spec-validator.py
.claude/scripts\sync-from-github.sh
.claude/scripts\sync-bridge-stubs.py
.claude/scripts\spawn-agent.py
.claude/scripts\semantic-search.py
.claude/scripts\memory-engine.py
.claude/scripts\list_codex_scripts.py
.claude/scripts\knowledge-graph.py
.claude/scripts\knowledge-decay-report.py
.claude/scripts\judge_axes.py
.claude/scripts\judge.py
.claude/scripts\git_worktree_list.py
.claude/scripts\generate-prompt.py
.claude/scripts\dual-teams-spawn.py
.claude/scripts\dual-teams-selftest.py
.claude/scripts\dual-history-archive.py
.claude/scripts\context-layers.py
.claude/scripts\codex_env_check.py
.claude/scripts\codex-wave.py
.claude/scripts\codex-scope-check.py
.claude/scripts\codex-pool.py
.claude/scripts\codex-inline-dual.py
.claude/scripts\codex-implement.py
.claude/scripts\codex-cost-report.py
.claude/scripts\codex-ask.py
.claude/scripts\bridge-stub-template.py
.claude/scripts\ao-hybrid.sh
work\check_leads.py
work\CAPABILITY_MAP.md
work\followups\verdicts\task-Y8-verdict.json
work\fleet-sync.sh
work\bot-analysis\SYNTHESIS.md
work\background-tasks.json
work\y14-codify\verdicts\task-Y16-verdict.json
work\y14-codify\verdicts\task-Y15-verdict.json
work\autoresearch-integration\test_loop_driver.py
work\autoresearch-integration\test_hook_markers.py
work\autoresearch-integration\QUARANTINE.md
work\autoresearch-integration\PIPELINE.md
work\autoresearch-integration\canary_stub_matrix.py
work\autoresearch-integration\canary_stub_driver.py
work\autoresearch-integration\canary_real_claude.py
work\attempt-history.json
work\fixes\verdicts\task-FIX-B-verdict.json
work\fixes\verdicts\task-FIX-A-verdict.json
work\watchdog-fix\verification.md
work\watchdog-fix\spec.md
work\watchdog-fix\PIPELINE.md
work\watchdog-fix\fp-replay.md
work\voice_transcripts.md
work\voice_part_3.md
work\voice_part_2.md
work\voice_part_1.md
work\voice_part_0.md
work\verify-results.md
work\fixes\tasks\task-FIX-B-dual-base-ref-sidecar.md
work\fixes\tasks\task-FIX-A-judge-diff-baseline.md
work\fetch_all_deals.py
work\expert-analysis.md
work\expert-analysis-ao.md
work\errors.md
work\athena-analysis\recommendations.md
work\athena-analysis\comparison-matrix.md
work\athena-analysis\a9-workflows-skills.md
work\athena-analysis\a8-mcp-tools.md
work\athena-analysis\a7-claude-agents-md.md
work\athena-analysis\a6-rag-search.md
work\athena-analysis\a5-agent-coordination.md
work\athena-analysis\a4-governance-security.md
work\athena-analysis\a3-protocol-system.md
work\athena-analysis\a2-boot-lifecycle.md
work\athena-analysis\a10-context-engineering.md
work\athena-analysis\a1-memory-persistence.md
work\validation\verdicts\task-V4-verdict.json
work\validation\verdicts\task-V3-verdict.json
work\validation\verdicts\task-V2-verdict.json
work\validation\verdicts\task-V1-verdict.json
work\scalable-pipeline-design-gates.md
work\scalable-pipeline-design-format.md
work\scalable-pipeline-design-deploy.md
work\safety-review-3.md
work\safety-review-2.md
work\safety-review-1.md
work\ao-prompts\task-2-template-diff.md
work\ao-prompts\task-1-audit-skills.md
work\ao-prompts\ao-task-2.md
work\ao-prompts\ao-task-1.md
work\risk-assessment-memory-and-skills.md
work\anketa_timing.py
work\risk-assessment-global-skills.md
work\analysis-implementation-workflows.md
work\amocrm_link_check_report.xlsx
work\qa-review-report.md
work\PIPELINE.md
work\e2e-results\summary.md
work\e2e-results\skill-loading.md
work\e2e-results\improvements-summary.md
work\e2e-results\ao-hybrid.md
work\e2e-results\ao-agent-2.md
work\e2e-results\ao-agent-1.md
work\e2e-results\agent-teams.md
work\e2e-results\agent-3-error-handler.md
work\e2e-results\agent-2-mapper.md
work\e2e-results\agent-1-verifier.md
work\validation\tasks\task-V4-verdict-summarizer.md
work\validation\tasks\task-V3-worktree-cleaner.md
work\validation\tasks\task-V2-task-spec-validator.md
work\validation\tasks\task-V1-knowledge-decay-report.md
work\amocrm-dedup\pipelines.txt
work\amocrm-dedup\phase2_mass_merge.py
work\amocrm-dedup\phase1_test_merge.py
work\amocrm-dedup\phase0_scout.py
work\amocrm-dedup\phase0_name_dupes.py
work\amocrm-dedup\nick_to_telegram_report.csv
work\amocrm-dedup\nick_to_telegram.py
work\validation\prompts\task-V2-task-spec-validator-claude.md
work\validation\prompts\task-V1-knowledge-decay-report-claude.md
work\validation\dual-teams-plan.md
work\update_sheet.py
work\transcribe_worker.py
work\transcribe_voices.py
work\tilda-main-server.py
work\tilda-main-fixed.py
work\text_messages.md
work\test-verification-done.md
work\test-stale-refs-routing.md
work\e2e\verdicts\task-E2E-2-verdict.json
work\e2e\verdicts\task-E2E-1-verdict.json
work\amocrm-dedup\nick-sync-service\requirements.txt
work\amocrm-dedup\nick-sync-service\main.py
work\amocrm-dedup\name_dupes_review.csv
work\amocrm-dedup\merged_deals_report.csv
work\amocrm-dedup\export_to_sheets.py
work\amocrm-dedup\dedup_report.csv
work\test-scenarios\test_calculator.py
work\test-scenarios\test4-report.md
work\test-scenarios\test3-report.md
work\test-scenarios\test2-report.md
work\test-scenarios\test1-report.md
work\test-scenarios\multi-task-plan.md
work\test-scenarios\calculator.py
work\test-qa-debugging-inline.md
work\pipeline-v2-draft\ralph.sh
work\pipeline-v2-draft\PROMPT.md
work\pipeline-v2-draft\PIPELINE.md
work\pipeline-review.md
work\photo_analysis.md
work\phone_in_wz_report.json
work\amocrm-dedup\dedup-service\requirements.txt
work\amocrm-dedup\dedup-service\main.py
work\amocrm-dedup\dedup-service\init_tokens.py
work\amocrm-dedup\dedup-service\Dockerfile
work\amocrm-dedup\dedup-service\docker-compose.yml
work\amocrm-dedup\dedup-service\dedup.py
work\amocrm-dedup\dedup-service\config.py
work\amocrm-dedup\dedup-service\amocrm.py
work\test-prompts\test-reviewer.md
work\test-prompts\test-planner.md
work\test-prompts\test-coder.md

 succeeded in 182ms:


    Каталог: C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-at
    tack-matrix


Mode                 LastWriteTime         Length Name                                                                 
----                 -------------         ------ ----                                                                 
d-----        26.04.2026     11:58                .claude                                                              
d-----        26.04.2026     11:58                .codex                                                               
d-----        26.04.2026     11:58                .github                                                              
d-----        26.04.2026     11:58                docs                                                                 
d-----        26.04.2026     11:58                scripts                                                              
d-----        26.04.2026     11:58                work                                                                 
-a----        26.04.2026     11:58             41 .dual-base-ref                                                       
-a-h--        26.04.2026     11:58            104 .git                                                                 
-a----        26.04.2026     11:58            946 .gitignore                                                           
-a----        26.04.2026     11:58            243 .mcp.json                                                            
-a----        26.04.2026     11:58           8625 AGENTS.md                                                            
-a----        26.04.2026     11:58          12134 CLAUDE.md                                                            
-a----        26.04.2026     11:58           3947 README.md                                                            
-a----        26.04.2026     11:58           2265 SSH_CONTABO_CONNECTION.md                                            



 exited 1 in 181ms:
.claude/hooks\write-validate.py
.claude/hooks\truthguard.py
.claude/hooks\tool-failure-logger.py
.claude/hooks\test_watchdog_fix.py
.claude/hooks\test_curation.py
.claude/hooks\test_codex_gate.py
.claude/hooks\test_codex_delegate_enforcer_invariants.py
.claude/hooks\test_codex_delegate_enforcer.py
.claude/hooks\task-completed-gate.py
.claude/hooks\session-task-class.py
.claude/hooks\session-orient.py
.claude/hooks\pre-compact-save.py
.claude/hooks\hook_base.py
.claude/hooks\config-protection.py
.claude/hooks\codex-watchdog.py
.claude/hooks\codex-stop-opinion.py
.claude/hooks\codex-review.sh
.claude/hooks\codex-review.py
.claude/hooks\codex-parallel.py
.claude/hooks\codex-gate.py
.claude/hooks\codex-delegate-enforcer.py
.claude/hooks\codex-broker.py
.claude/scripts\worktree-cleaner.py
.claude/scripts\verdict-summarizer.py
.claude/scripts\validate-configs.py
.claude/scripts\test_worktree_cleaner.py
.claude/scripts\test_verdict_summarizer.py
.claude/scripts\test_task_spec_validator.py
.claude/scripts\test_spawn_agent.py
.claude/scripts\test_knowledge_decay_report.py
.claude/scripts\test_judge.py
.claude/scripts\test_dual_teams_spawn.py
.claude/scripts\test_dual_teams_selftest.py
.claude/scripts\test_dual_history_archive.py
.claude/scripts\test_codex_wave.py
.claude/scripts\test_codex_scope_check.py
.claude/scripts\test_codex_pool.py
.claude/scripts\test_codex_inline_dual.py
.claude/scripts\test_codex_implement.py
.claude/scripts\test_codex_cost_report.py
.claude/scripts\test_codex_ask.py
.claude/scripts\task-spec-validator.py
.claude/scripts\sync-from-github.sh
.claude/scripts\sync-bridge-stubs.py
.claude/scripts\spawn-agent.py
.claude/scripts\semantic-search.py
.claude/scripts\memory-engine.py
.claude/scripts\list_codex_scripts.py
.claude/scripts\knowledge-graph.py
.claude/scripts\knowledge-decay-report.py
.claude/scripts\judge_axes.py
.claude/scripts\judge.py
.claude/scripts\git_worktree_list.py
.claude/scripts\generate-prompt.py
.claude/scripts\dual-teams-spawn.py
.claude/scripts\dual-teams-selftest.py
.claude/scripts\dual-history-archive.py
.claude/scripts\context-layers.py
.claude/scripts\codex_env_check.py
.claude/scripts\codex-wave.py
.claude/scripts\codex-scope-check.py
.claude/scripts\codex-pool.py
.claude/scripts\codex-inline-dual.py
.claude/scripts\codex-implement.py
.claude/scripts\codex-cost-report.py
.claude/scripts\codex-ask.py
.claude/scripts\bridge-stub-template.py
.claude/scripts\ao-hybrid.sh
work\check_leads.py
work\CAPABILITY_MAP.md
work\followups\verdicts\task-Y8-verdict.json
work\fleet-sync.sh
work\bot-analysis\SYNTHESIS.md
work\background-tasks.json
work\y14-codify\verdicts\task-Y16-verdict.json
work\y14-codify\verdicts\task-Y15-verdict.json
work\autoresearch-integration\test_loop_driver.py
work\autoresearch-integration\test_hook_markers.py
work\autoresearch-integration\QUARANTINE.md
work\autoresearch-integration\PIPELINE.md
work\autoresearch-integration\canary_stub_matrix.py
work\autoresearch-integration\canary_stub_driver.py
work\autoresearch-integration\canary_real_claude.py
work\attempt-history.json
work\fixes\verdicts\task-FIX-B-verdict.json
work\fixes\verdicts\task-FIX-A-verdict.json
work\watchdog-fix\verification.md
work\watchdog-fix\spec.md
work\watchdog-fix\PIPELINE.md
work\watchdog-fix\fp-replay.md
work\voice_transcripts.md
work\voice_part_3.md
work\voice_part_2.md
work\voice_part_1.md
work\voice_part_0.md
work\verify-results.md
work\fixes\tasks\task-FIX-B-dual-base-ref-sidecar.md
work\fixes\tasks\task-FIX-A-judge-diff-baseline.md
work\fetch_all_deals.py
work\expert-analysis.md
work\expert-analysis-ao.md
work\errors.md
work\athena-analysis\recommendations.md
work\athena-analysis\comparison-matrix.md
work\athena-analysis\a9-workflows-skills.md
work\athena-analysis\a8-mcp-tools.md
work\athena-analysis\a7-claude-agents-md.md
work\athena-analysis\a6-rag-search.md
work\athena-analysis\a5-agent-coordination.md
work\athena-analysis\a4-governance-security.md
work\athena-analysis\a3-protocol-system.md
work\athena-analysis\a2-boot-lifecycle.md
work\athena-analysis\a10-context-engineering.md
work\athena-analysis\a1-memory-persistence.md
work\validation\verdicts\task-V4-verdict.json
work\validation\verdicts\task-V3-verdict.json
work\validation\verdicts\task-V2-verdict.json
work\validation\verdicts\task-V1-verdict.json
work\scalable-pipeline-design-gates.md
work\scalable-pipeline-design-format.md
work\scalable-pipeline-design-deploy.md
work\safety-review-3.md
work\safety-review-2.md
work\safety-review-1.md
work\ao-prompts\task-2-template-diff.md
work\ao-prompts\task-1-audit-skills.md
work\ao-prompts\ao-task-2.md
work\ao-prompts\ao-task-1.md
work\risk-assessment-memory-and-skills.md
work\anketa_timing.py
work\risk-assessment-global-skills.md
work\analysis-implementation-workflows.md
work\amocrm_link_check_report.xlsx
work\qa-review-report.md
work\PIPELINE.md
work\e2e-results\summary.md
work\e2e-results\skill-loading.md
work\e2e-results\improvements-summary.md
work\e2e-results\ao-hybrid.md
work\e2e-results\ao-agent-2.md
work\e2e-results\ao-agent-1.md
work\e2e-results\agent-teams.md
work\e2e-results\agent-3-error-handler.md
work\e2e-results\agent-2-mapper.md
work\e2e-results\agent-1-verifier.md
work\validation\tasks\task-V4-verdict-summarizer.md
work\validation\tasks\task-V3-worktree-cleaner.md
work\validation\tasks\task-V2-task-spec-validator.md
work\validation\tasks\task-V1-knowledge-decay-report.md
work\amocrm-dedup\pipelines.txt
work\amocrm-dedup\phase2_mass_merge.py
work\amocrm-dedup\phase1_test_merge.py
work\amocrm-dedup\phase0_scout.py
work\amocrm-dedup\phase0_name_dupes.py
work\amocrm-dedup\nick_to_telegram_report.csv
work\amocrm-dedup\nick_to_telegram.py
work\validation\prompts\task-V2-task-spec-validator-claude.md
work\validation\prompts\task-V1-knowledge-decay-report-claude.md
work\validation\dual-teams-plan.md
work\update_sheet.py
work\transcribe_worker.py
work\transcribe_voices.py
work\tilda-main-server.py
work\tilda-main-fixed.py
work\text_messages.md
work\test-verification-done.md
work\test-stale-refs-routing.md
work\e2e\verdicts\task-E2E-2-verdict.json
work\e2e\verdicts\task-E2E-1-verdict.json
work\amocrm-dedup\nick-sync-service\requirements.txt
work\amocrm-dedup\nick-sync-service\main.py
work\amocrm-dedup\name_dupes_review.csv
work\amocrm-dedup\merged_deals_report.csv
work\amocrm-dedup\export_to_sheets.py
work\amocrm-dedup\dedup_report.csv
work\test-scenarios\test_calculator.py
work\test-scenarios\test4-report.md
work\test-scenarios\test3-report.md
work\test-scenarios\test2-report.md
work\test-scenarios\test1-report.md
work\test-scenarios\multi-task-plan.md
work\test-scenarios\calculator.py
work\test-qa-debugging-inline.md
work\pipeline-v2-draft\ralph.sh
work\pipeline-v2-draft\PROMPT.md
work\pipeline-v2-draft\PIPELINE.md
work\pipeline-review.md
work\photo_analysis.md
work\phone_in_wz_report.json
work\amocrm-dedup\dedup-service\requirements.txt
work\amocrm-dedup\dedup-service\main.py
work\amocrm-dedup\dedup-service\init_tokens.py
work\amocrm-dedup\dedup-service\Dockerfile
work\amocrm-dedup\dedup-service\docker-compose.yml
work\amocrm-dedup\dedup-service\dedup.py
work\amocrm-dedup\dedup-service\config.py
work\amocrm-dedup\dedup-service\amocrm.py
work\test-prompts\test-reviewer.md
work\test-prompts\test-planner.md
work\test-prompts\test-coder.md

codex
The repo has the expected hook/test layout. I’m reading the enforcer entrypoint and existing tests now so the new harness uses the same payload schema and asserts the real subprocess behavior, not a guessed interface.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/hooks/codex-delegate-enforcer.py -TotalCount 260' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/hooks/test_codex_delegate_enforcer.py -TotalCount 260' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/hooks/test_codex_delegate_enforcer_invariants.py -TotalCount 260' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/hooks/test_codex_gate.py -TotalCount 220' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
 succeeded in 171ms:
#!/usr/bin/env python3
"""Unit tests for codex-delegate-enforcer.py (task T1).

Covers all 11 required cases from spec AC12:

  1. exempt path (e.g., CLAUDE.md) -> allow
  2. code file + NO recent result.md -> deny with JSON
  3. code file + stale (> 15 min) result.md -> deny
  4. code file + fresh status=pass result.md with covering fence -> allow
  5. code file + fresh pass result.md but fence does NOT cover target -> deny
  6. code file + fresh status=fail result.md -> deny
  7. non-code file (.txt, .md) -> allow
  8. MultiEdit with multiple files, all covered -> allow
  9. MultiEdit with one file uncovered -> deny
 10. malformed result.md / corrupt JSON payload -> pass-through (no crash)
 11. hook called on non-Edit event (e.g., Bash) -> pass-through

Each test isolates state under a temporary CLAUDE_PROJECT_DIR so
production .codex/ and work/ directories are never touched.
"""

from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENFORCER_PATH = HERE / "codex-delegate-enforcer.py"


def _load_module():
    """Import codex-delegate-enforcer.py as a module (hyphen in filename)."""
    spec = importlib.util.spec_from_file_location(
        "codex_delegate_enforcer", ENFORCER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BaseEnforcerTest(unittest.TestCase):
    """Shared fixture: isolated project root with results + tasks dirs."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp(prefix="codex-enforcer-test-")
        self.root = Path(self.tmpdir).resolve()
        (self.root / ".claude" / "hooks").mkdir(parents=True)
        (self.root / "work" / "codex-primary" / "tasks").mkdir(parents=True)
        (self.root / "work" / "codex-implementations").mkdir(parents=True)
        # Target file the tool call "would edit"
        self.target_rel = ".claude/hooks/my_hook.py"
        (self.root / ".claude" / "hooks" / "my_hook.py").write_text(
            "# placeholder\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ----- subprocess invocation helpers -----

    def _run_enforcer(self, payload):
        """Invoke enforcer as subprocess; return (exit_code, stdout, stderr)."""
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)}
        result = subprocess.run(
            [sys.executable, str(ENFORCER_PATH)],
            input=json.dumps(payload),
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            env=env, timeout=30,
        )
        return result.returncode, result.stdout, result.stderr

    # ----- fixture helpers -----

    def _write_task(self, task_id: str, fence_paths: list) -> Path:
        """Write a task-N.md with given Scope Fence allowed paths."""
        task_file = self.root / "work" / "codex-primary" / "tasks" / (
            "T" + task_id + "-test.md"
        )
        fence_block = "\n".join("- `" + p + "`" for p in fence_paths)
        task_file.write_text(
            "---\nexecutor: codex\n---\n\n"
            "# Task T" + task_id + "\n\n"
            "## Your Task\ntest\n\n"
            "## Scope Fence\n"
            "**Allowed paths (may be written):**\n"
            + fence_block + "\n\n"
            "**Forbidden paths:**\n- other/\n\n"
            "## Acceptance Criteria\n- [ ] AC1\n",
            encoding="utf-8",
        )
        return task_file

    def _write_result(self, task_id: str, status: str, age_seconds: float = 0) -> Path:
        """Write a task-N-result.md with given status and optional mtime offset."""
        result_file = self.root / "work" / "codex-implementations" / (
            "task-" + task_id + "-result.md"
        )
        task_file_rel = "work/codex-primary/tasks/T" + task_id + "-test.md"
        result_file.write_text(
            "# Result T" + task_id + "\n\n"
            "- status: " + status + "\n"
            "- task_file: " + task_file_rel + "\n\n"
            "## Diff\n(none)\n",
            encoding="utf-8",
        )
        if age_seconds > 0:
            old = time.time() - age_seconds
            os.utime(result_file, (old, old))
        return result_file

    def _edit_payload(self, file_path: str) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": file_path,
                "old_string": "a",
                "new_string": "b",
            },
        }

    def _write_payload(self, file_path: str) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": file_path, "content": "x"},
        }

    def _multiedit_payload(self, paths: list) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "MultiEdit",
            "tool_input": {
                "edits": [
                    {"file_path": p, "old_string": "a", "new_string": "b"}
                    for p in paths
                ],
            },
        }

    # ----- response assertions -----

    def _assert_allow(self, code: int, stdout: str, stderr: str) -> None:
        self.assertEqual(code, 0, msg="expected exit 0. stderr=" + stderr)
        # No deny JSON in stdout.
        if stdout.strip():
            try:
                parsed = json.loads(stdout)
                decision = (
                    parsed.get("hookSpecificOutput", {})
                    .get("permissionDecision")
                )
                self.assertNotEqual(
                    decision, "deny", msg="unexpected deny JSON: " + stdout
                )
            except json.JSONDecodeError:
                pass  # non-JSON stdout is fine

    def _assert_deny(self, code: int, stdout: str, stderr: str) -> None:
        self.assertEqual(code, 0, msg="expected exit 0 (deny via JSON). stderr=" + stderr)
        self.assertTrue(stdout.strip(), msg="expected deny JSON on stdout")
        parsed = json.loads(stdout)
        decision = parsed["hookSpecificOutput"]["permissionDecision"]
        self.assertEqual(decision, "deny")
        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("Code Delegation Protocol", reason)


class TestAC12Cases(BaseEnforcerTest):
    """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""

    def test_01_exempt_path_allow(self) -> None:
        """AC12.1: exempt path (CLAUDE.md) -> allow."""
        code, out, err = self._run_enforcer(self._write_payload("CLAUDE.md"))
        self._assert_allow(code, out, err)

    def test_02_code_no_result_deny(self) -> None:
        """AC12.2: code file + NO recent result.md -> deny with JSON."""
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_03_stale_result_deny(self) -> None:
        """AC12.3: code file + stale (> 15 min) result.md -> deny."""
        self._write_task("3", [self.target_rel])
        self._write_result("3", "pass", age_seconds=20 * 60)  # 20 min old
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_04_covered_pass_allow(self) -> None:
        """AC12.4: code file + fresh pass result.md with covering fence -> allow."""
        self._write_task("4", [self.target_rel])
        self._write_result("4", "pass")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_allow(code, out, err)

    def test_05_uncovered_pass_deny(self) -> None:
        """AC12.5: fresh pass, fence does NOT cover target -> deny."""
        self._write_task("5", ["other/unrelated.py"])
        self._write_result("5", "pass")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_06_fail_status_deny(self) -> None:
        """AC12.6: fresh status=fail result.md -> deny."""
        self._write_task("6", [self.target_rel])
        self._write_result("6", "fail")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_07_non_code_file_allow(self) -> None:
        """AC12.7: non-code file (.txt, .md) -> allow."""
        for suffix in (".txt", ".md"):
            notes = ".claude/hooks/notes" + suffix
            (self.root / notes).write_text("x", encoding="utf-8")
            code, out, err = self._run_enforcer(self._write_payload(notes))
            self._assert_allow(code, out, err)

    def test_08_multiedit_all_covered_allow(self) -> None:
        """AC12.8: MultiEdit with multiple files, all covered -> allow."""
        a = ".claude/hooks/a.py"
        b = ".claude/hooks/b.py"
        (self.root / a).write_text("# a\n", encoding="utf-8")
        (self.root / b).write_text("# b\n", encoding="utf-8")
        self._write_task("8", [".claude/hooks/"])
        self._write_result("8", "pass")
        code, out, err = self._run_enforcer(self._multiedit_payload([a, b]))
        self._assert_allow(code, out, err)

    def test_09_multiedit_one_uncovered_deny(self) -> None:
        """AC12.9: MultiEdit with one file uncovered -> deny."""
        a = ".claude/hooks/a.py"
        b = "src/uncovered.py"
        (self.root / a).write_text("# a\n", encoding="utf-8")
        (self.root / "src").mkdir(parents=True)
        (self.root / b).write_text("# b\n", encoding="utf-8")
        self._write_task("9", [".claude/hooks/"])
        self._write_result("9", "pass")
        code, out, err = self._run_enforcer(self._multiedit_payload([a, b]))
        self._assert_deny(code, out, err)

    def test_10a_malformed_result_passthrough(self) -> None:
        """AC12.10a: malformed result.md -> no crash, handled gracefully."""
        # Write a recent file but with completely corrupt body.
        result_file = self.root / "work" / "codex-implementations" / (
            "task-10-result.md"
        )
        result_file.write_bytes(b"\x00\x01\xff garbage no fields here")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        # No crash: exit 0. Since no fence covers target, it is denied -

 succeeded in 174ms:
#!/usr/bin/env python3
"""Codex Delegate Enforcer - Always-Dual PreToolUse hook (CLAUDE.md).

Z1 - Four Invariants closing 12 bypass vectors:

I1. Extension wins. is_code_extension() is checked BEFORE is_exempt().
    Path exemptions (work/**, worktrees/**, .claude/scripts/**) only
    protect non-code extensions. A .py file in work/ requires cover.

I2. Bash counts. PreToolUse(Bash) tokenizes the command; mutating verbs
    (cp/mv/sed -i/redirect/python script.py/PowerShell Set-Content/...)
    against code paths require cover. A whitelist exempts read-only verbs
    (ls/cat/git status/pytest/...) and the project's own dual tooling
    (codex-ask, codex-implement, dual-teams-spawn, ...).

I3. Path-exact coverage. find_cover(target) returns True only if some
    artifact's Scope Fence explicitly lists the target (with glob support
    via fnmatch). No temporal carryover from unrelated stages.

I4. Skip-token audit + actionable block messages. Every allow/deny
    decision is appended to work/codex-implementations/skip-ledger.jsonl
    (best-effort, never blocks). DENY messages include a ready-to-run
    codex-inline-dual.py command for the blocked path.

Edit/Write/MultiEdit on a code file that is NOT exempt -> require a fresh
(<15 min) work/codex-implementations/task-*-result.md with status=pass
whose Scope Fence covers the target. Missing cover -> deny via PreToolUse
JSON. Fail-open on any unexpected exception.
"""
from __future__ import annotations
import datetime
import fnmatch
import json
import logging
import os
import re
import shlex
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Optional

if sys.platform == "win32":
    for _stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")

HOOK_NAME = "codex-delegate-enforcer"
RESULT_MAX_AGE_SECONDS: int = 15 * 60
MAX_RESULT_FILES_TO_SCAN: int = 50
CODEX_IMPLEMENTATIONS_DIR = "work/codex-implementations"
CODEX_TASKS_DIR = "work/codex-primary/tasks"
SKIP_LEDGER_REL = "work/codex-implementations/skip-ledger.jsonl"

# I1 - delegated code extensions. Frozenset for O(1) lookup.
CODE_EXTENSIONS: frozenset = frozenset({
    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
    ".sql", ".lua", ".r",
})

# I1 - exempt path globs. ONLY apply to non-code extensions.
EXEMPT_PATTERNS: tuple = (
    ".claude/memory/**", "work/**", "CLAUDE.md", "AGENTS.md",
    "README.md", "CHANGELOG.md", "LICENSE", ".gitignore",
    ".claude/settings.json", ".claude/ops/*.yaml", ".mcp.json",
    ".claude/adr/**/*.md", ".claude/guides/**/*.md",
    ".claude/skills/**/*.md",
    "worktrees/**",
)

# Regexes - compiled at module scope.
_STATUS_RE = re.compile(r"(?i)status\s*[:=]\s*([A-Za-z0-9_-]+)")
_TASK_FILE_RE = re.compile(r"(?i)task[_\s-]*file\s*[:=]\s*(.+)")
_SCOPE_FENCE_HEADING_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
_NEXT_HEADING_RE = re.compile(r"(?m)^##\s+")
_ALLOWED_SECTION_RE = re.compile(
    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\Z)"
)
_TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
_RESULT_NAME_RE = re.compile(r"task-(.+?)-result\.md$")

# I2 - Bash classification tables.
_BASH_READONLY_VERBS: frozenset = frozenset({
    "ls", "cat", "head", "tail", "less", "more", "wc", "file", "stat",
    "find", "grep", "rg", "ag", "sort", "uniq", "cut", "tr", "diff",
    "cmp", "tree", "echo", "printf", "true", "false", "pwd", "which",
    "whoami", "date", "env", "type", "command", "id", "hostname",
})

_BASH_TEST_RUNNERS: frozenset = frozenset({
    "pytest", "unittest", "mypy", "ruff", "tsc", "eslint", "prettier",
    "cargo", "go",
})

_BASH_PACKAGE_MANAGERS: frozenset = frozenset({
    "uv", "pip", "npm", "yarn", "pnpm",
})

_BASH_DUAL_TOOLING: frozenset = frozenset({
    ".claude/scripts/codex-implement.py",
    ".claude/scripts/codex-wave.py",
    ".claude/scripts/codex-inline-dual.py",
    ".claude/scripts/dual-teams-spawn.py",
    ".claude/scripts/dual-teams-selftest.py",
    ".claude/scripts/judge.py",
    ".claude/scripts/judge_axes.py",
    ".claude/scripts/codex-ask.py",
    ".claude/scripts/codex-scope-check.py",
    ".claude/scripts/codex-pool.py",
    ".claude/scripts/dual-history-archive.py",
    ".claude/scripts/verdict-summarizer.py",
    ".claude/scripts/worktree-cleaner.py",
    ".claude/scripts/codex-cost-report.py",
})

_BASH_MUTATING_VERBS: frozenset = frozenset({
    "cp", "mv", "install", "rsync", "rm", "tee", "touch", "ln", "chmod",
    "chown", "dd",
})

_BASH_INPLACE_VERBS: frozenset = frozenset({"sed", "awk", "perl"})

_BASH_INTERPRETERS: frozenset = frozenset({
    "python", "python3", "py", "bash", "sh", "zsh", "node", "deno",
    "ruby", "perl", "lua",
})

_PWSH_MUTATING_CMDLETS: tuple = (
    "set-content", "add-content", "out-file", "new-item",
    "copy-item", "move-item", "remove-item",
    "writealltext", "appendalltext",
)

_BASH_PWSH_LAUNCHERS: frozenset = frozenset({
    "powershell", "powershell.exe", "pwsh", "pwsh.exe",
})


def _build_logger(project_dir: Path) -> logging.Logger:
    """Create enforcer logger: file if writable else stderr-only."""
    logger = logging.getLogger(HOOK_NAME)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    log_dir = project_dir / ".claude" / "logs"
    file_ok = False
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_dir / (HOOK_NAME + ".log"), encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        file_ok = True
    except OSError:
        file_ok = False
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(fmt)
    sh.setLevel(logging.WARNING if file_ok else logging.INFO)
    logger.addHandler(sh)
    logger.propagate = False
    return logger


def get_project_dir() -> Path:
    """Resolve project root. Honors CLAUDE_PROJECT_DIR env."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()


def is_dual_teams_worktree(project_dir: Path) -> bool:
    """True iff project_dir or any ancestor contains .dual-base-ref."""
    logger = logging.getLogger(HOOK_NAME)
    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
    current = project_dir
    seen: set[Path] = set()
    while True:
        try:
            resolved = current.resolve()
        except OSError as exc:
            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
            resolved = current.absolute()
        if resolved in seen:
            logger.info(
                "is_dual_teams_worktree.exit project=%s result=False reason=cycle",
                project_dir,
            )
            return False
        seen.add(resolved)
        sentinel = current / ".dual-base-ref"
        try:
            if sentinel.is_file():
                logger.info(
                    "is_dual_teams_worktree.exit project=%s result=True sentinel=%s",
                    project_dir, sentinel,
                )
                return True
        except OSError as exc:
            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
        parent = current.parent
        if parent == current:
            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
            return False
        current = parent


def resolve_target(project_dir: Path, target_raw: str) -> Optional[Path]:
    """Normalize raw file_path to absolute Path inside project_dir."""
    logger = logging.getLogger(HOOK_NAME)
    if not target_raw:
        return None
    try:
        p = Path(target_raw)
        if not p.is_absolute():
            p = project_dir / p
        resolved = p.resolve()
    except (OSError, ValueError) as exc:
        logger.info("resolve_target.err raw=%r exc=%s", target_raw, exc)
        return None
    try:
        resolved.relative_to(project_dir)
    except ValueError:
        logger.info("resolve_target.escape resolved=%s", resolved)
        return None
    return resolved


def rel_posix(project_dir: Path, absolute: Path) -> Optional[str]:
    """POSIX-style project-relative path, or None if outside."""
    try:
        return absolute.relative_to(project_dir).as_posix()
    except ValueError:
        return None


def is_code_extension(rel_path: str) -> bool:
    """True iff extension is in the delegated code set."""
    return Path(rel_path).suffix.lower() in CODE_EXTENSIONS


def is_exempt(rel_path: str) -> bool:
    """True iff rel_path matches any exempt glob (NON-CODE only)."""
    logger = logging.getLogger(HOOK_NAME)
    for pattern in EXEMPT_PATTERNS:
        if pattern.endswith("/**"):
            prefix = pattern[:-3].rstrip("/")
            if rel_path == prefix or rel_path.startswith(prefix + "/"):
                logger.debug("is_exempt.match pattern=%s", pattern)
                return True
            continue
        if "**" in pattern:
            left, _, right = pattern.partition("**")
            left = left.rstrip("/")
            right = right.lstrip("/")
            left_ok = (not left) or rel_path == left or rel_path.startswith(left + "/")
            right_ok = (not right) or fnmatch.fnmatch(rel_path, "*" + right)
            if left_ok and right_ok:
                logger.debug("is_exempt.match pattern=%s (double-glob)", pattern)
                return True
            continue

 succeeded in 173ms:
#!/usr/bin/env python3
"""Unit tests for codex-gate.py (T5 вЂ” tech-spec Section 9).

Covers AC5 a-e:
  a) No opinions at all -> gate blocks
  b) Fresh codex-ask.py opinion -> gate passes (old behavior preserved)
  c) Stale codex-ask.py but fresh in-scope task-result.md -> gate passes (new behavior)
  d) Fresh task-result.md but target file NOT in scope fence -> gate blocks
  e) task-result.md with status=fail -> gate blocks

Each test isolates state under a temporary CLAUDE_PROJECT_DIR so production
.codex/ and work/ directories are never touched.
"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATE_PATH = HERE / "codex-gate.py"


def _load_gate():
    """Import codex-gate.py as a module (filename has a hyphen)."""
    spec = importlib.util.spec_from_file_location("codex_gate", GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BaseGateTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="codex-gate-test-")
        self.root = Path(self.tmpdir).resolve()
        # Scaffold project layout the gate expects.
        (self.root / ".claude" / "hooks").mkdir(parents=True)
        (self.root / ".codex" / "reviews").mkdir(parents=True)
        (self.root / "work" / "codex-primary" / "tasks").mkdir(parents=True)
        (self.root / "work" / "codex-implementations").mkdir(parents=True)
        # Target file that Claude is "about to edit".
        self.target_rel = ".claude/hooks/codex-gate.py"
        (self.root / ".claude" / "hooks" / "codex-gate.py").write_text("# placeholder\n", encoding="utf-8")

        os.environ["CLAUDE_PROJECT_DIR"] = str(self.root)
        # Disable hook profile filtering so gate always runs.
        os.environ["CLAUDE_HOOK_PROFILE"] = "standard"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run_gate(self, payload):
        """Invoke gate as subprocess; return (exit_code, stderr)."""
        result = subprocess.run(
            [sys.executable, str(GATE_PATH), "PreToolUse"],
            input=json.dumps(payload),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env={**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)},
            timeout=30,
        )
        return result.returncode, result.stderr

    def _write_fresh_codex_ask(self):
        ts = self.root / ".codex" / "last-consulted"
        ts.write_text(str(time.time()), encoding="utf-8")
        ec = self.root / ".codex" / "edit-count"
        ec.write_text("0", encoding="utf-8")

    def _write_task(self, task_id, fence_paths):
        task_file = self.root / "work" / "codex-primary" / "tasks" / f"T{task_id}-test.md"
        fence_block = "\n".join(f"- `{p}`" for p in fence_paths)
        task_file.write_text(
            f"""---
executor: claude
risk_class: routine
---

# Task T{task_id}: test

## Your Task
test

## Scope Fence
**Allowed paths (may be written):**
{fence_block}

**Forbidden paths (must NOT be modified):**
- everything-else/

## Acceptance Criteria
- [ ] AC1
""",
            encoding="utf-8",
        )
        return task_file

    def _write_result(self, task_id, status):
        result_file = (
            self.root / "work" / "codex-implementations" / f"task-{task_id}-result.md"
        )
        result_file.write_text(
            f"""# Task T{task_id} result

status: {status}

## Diff
(none)

## Test output
ok
""",
            encoding="utf-8",
        )
        return result_file

    def _payload(self, file_path):
        return {
            "tool_name": "Edit",
            "tool_input": {"file_path": file_path, "old_string": "a", "new_string": "b"},
        }


class TestGateDecisions(BaseGateTest):
    def test_a_no_opinions_blocks(self):
        """AC5a: no codex-ask, no task-result -> exit 2 (block)."""
        code, stderr = self._run_gate(self._payload(self.target_rel))
        self.assertEqual(code, 2, msg=f"expected block, got stderr:\n{stderr}")
        self.assertIn("stale", stderr.lower())

    def test_b_fresh_codex_ask_passes(self):
        """AC5b: fresh codex-ask opinion -> exit 0 (allow). Old path preserved."""
        self._write_fresh_codex_ask()
        code, stderr = self._run_gate(self._payload(self.target_rel))
        self.assertEqual(code, 0, msg=f"expected allow, got stderr:\n{stderr}")
        self.assertIn("codex-ask", stderr)

    def test_c_stale_ask_but_fresh_in_scope_result_passes(self):
        """AC5c: no codex-ask, fresh in-scope task-result.md with status=pass -> allow."""
        self._write_task("5", [".claude/hooks/codex-gate.py", ".claude/hooks/"])
        self._write_result("5", "pass")
        code, stderr = self._run_gate(self._payload(self.target_rel))
        self.assertEqual(code, 0, msg=f"expected allow, got stderr:\n{stderr}")
        self.assertIn("codex-implement", stderr)

    def test_d_fresh_result_but_out_of_scope_blocks(self):
        """AC5d: fresh pass result, but target file not in fence -> block."""
        self._write_task("5", ["some/other/dir/"])
        self._write_result("5", "pass")
        code, stderr = self._run_gate(self._payload(self.target_rel))
        self.assertEqual(code, 2, msg=f"expected block, got stderr:\n{stderr}")
        self.assertIn("NOT in fence", stderr)

    def test_e_fail_status_blocks(self):
        """AC5e: fresh task-result with status=fail -> block."""
        self._write_task("5", [".claude/hooks/codex-gate.py"])
        self._write_result("5", "fail")
        code, stderr = self._run_gate(self._payload(self.target_rel))
        self.assertEqual(code, 2, msg=f"expected block, got stderr:\n{stderr}")
        self.assertIn("status=fail", stderr)

    def test_stale_result_falls_through(self):
        """Stale task-result (older than 3 min) ignored; gate falls to old path."""
        task = self._write_task("5", [".claude/hooks/codex-gate.py"])
        result = self._write_result("5", "pass")
        # Backdate mtime to 10 min ago.
        old = time.time() - 600
        os.utime(result, (old, old))
        code, stderr = self._run_gate(self._payload(self.target_rel))
        # No fresh codex-ask either -> block (old behavior).
        self.assertEqual(code, 2, msg=f"expected block, got stderr:\n{stderr}")

    def test_dual_teams_worktree_allows_stale_codex_ask(self):
        """Dual-teams sentinel bypasses cooldown that would otherwise block."""
        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
        ts = self.root / ".codex" / "last-consulted"
        ts.write_text(str(time.time() - 600), encoding="utf-8")
        code, stderr = self._run_gate(self._payload(self.target_rel))
        self.assertEqual(code, 0, msg=f"expected allow, got stderr:\n{stderr}")
        self.assertIn("dual-teams-worktree", stderr)


class TestParsingHelpers(unittest.TestCase):
    """Unit-level tests for parse helpers (do not spawn subprocess)."""

    @classmethod
    def setUpClass(cls):
        cls.gate = _load_gate()

    def test_parse_status_yaml_style(self):
        import tempfile, pathlib
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
            fh.write("status: pass\nmore: stuff\n")
            p = pathlib.Path(fh.name)
        try:
            self.assertEqual(self.gate._parse_result_status(p), "pass")
        finally:
            p.unlink()

    def test_parse_status_bold_style(self):
        import tempfile, pathlib
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
            fh.write("# Heading\n\n**Status:** fail\n")
            p = pathlib.Path(fh.name)
        try:
            self.assertEqual(self.gate._parse_result_status(p), "fail")
        finally:
            p.unlink()

    def test_parse_status_missing(self):
        import tempfile, pathlib
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
            fh.write("no status here\n")
            p = pathlib.Path(fh.name)
        try:

 succeeded in 191ms:
#!/usr/bin/env python3
"""Tests for Z1 four-invariant enforcer (codex-delegate-enforcer.py).

Covers all 4 invariants:
- AC-1: I1 вЂ” extension wins (path exemption is non-code only)
- AC-2: I2 вЂ” Bash counts (effect-based interception)
- AC-3: I3 вЂ” path-exact coverage (no temporal carryover)
- AC-4: I4 вЂ” skip-token ledger + actionable block messages
- AC-5: regression вЂ” existing 36 tests still pass + selftest
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENFORCER_PATH = HERE / "codex-delegate-enforcer.py"


def _load_module():
    """Import codex-delegate-enforcer.py as a module (hyphen in filename)."""
    spec = importlib.util.spec_from_file_location(
        "codex_delegate_enforcer_z1", ENFORCER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Base(unittest.TestCase):
    """Shared fixture: isolated project root with results + tasks dirs."""

    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module()

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="z1-enforcer-")
        self.root = Path(self.tmpdir).resolve()
        (self.root / ".claude" / "hooks").mkdir(parents=True)
        (self.root / "work" / "codex-primary" / "tasks").mkdir(parents=True)
        (self.root / "work" / "codex-implementations").mkdir(parents=True)
        (self.root / ".claude" / "scripts").mkdir(parents=True)
        (self.root / "src").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ----- fixture helpers -----

    def _write_task(self, task_id: str, fence_paths: list) -> Path:
        """Write a task-N.md with given Scope Fence allowed paths."""
        tf = self.root / "work" / "codex-primary" / "tasks" / (
            "T" + task_id + "-test.md"
        )
        fence_block = "\n".join("- `" + p + "`" for p in fence_paths)
        tf.write_text(
            "---\nexecutor: codex\n---\n\n# Task T" + task_id + "\n\n"
            "## Your Task\ntest\n\n"
            "## Scope Fence\n"
            "**Allowed paths (may be written):**\n"
            + fence_block + "\n\n"
            "**Forbidden paths:**\n- other/\n\n"
            "## Acceptance Criteria\n- [ ] AC1\n",
            encoding="utf-8",
        )
        return tf

    def _write_result(self, task_id: str, status: str, age_seconds: float = 0) -> Path:
        rf = self.root / "work" / "codex-implementations" / (
            "task-" + task_id + "-result.md"
        )
        task_file_rel = "work/codex-primary/tasks/T" + task_id + "-test.md"
        rf.write_text(
            "# Result T" + task_id + "\n\n"
            "- status: " + status + "\n"
            "- task_file: " + task_file_rel + "\n\n"
            "## Diff\n(none)\n",
            encoding="utf-8",
        )
        if age_seconds > 0:
            old = time.time() - age_seconds
            os.utime(rf, (old, old))
        return rf

    def _edit_payload(self, file_path: str) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": file_path,
                           "old_string": "a", "new_string": "b"},
        }

    def _bash_payload(self, command: str) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command},
        }

    def _decide(self, payload: dict):
        """Run decide() in-process; return (allowed, stdout)."""
        with contextlib.redirect_stdout(io.StringIO()) as out:
            allowed = self.mod.decide(payload, self.root)
        return allowed, out.getvalue()

    def _assert_deny(self, allowed: bool, stdout: str):
        self.assertFalse(allowed, "expected DENY but got allow. stdout=" + stdout)
        self.assertTrue(stdout.strip(), "expected deny JSON on stdout")
        parsed = json.loads(stdout)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")

    def _assert_allow(self, allowed: bool, stdout: str):
        self.assertTrue(allowed, "expected ALLOW but got deny. stdout=" + stdout)



# ======================================================================
# AC-1 вЂ” Invariant 1: Extension wins
# ======================================================================
class TestI1ExtensionWins(_Base):
    """Code extensions ALWAYS require cover, regardless of path glob."""

    def test_work_py_requires_cover(self):
        """work/sync-template-to-target.py -> DENY (was previously ALLOW)."""
        target = "work/sync-template-to-target.py"
        (self.root / "work" / "sync-template-to-target.py").write_text("# x\n",
                                                                      encoding="utf-8")
        allowed, out = self._decide(self._edit_payload(target))
        self._assert_deny(allowed, out)

    def test_work_md_still_exempt(self):
        """work/notes.md -> ALLOW (non-code, exempt)."""
        target = "work/notes.md"
        (self.root / "work" / "notes.md").write_text("notes\n", encoding="utf-8")
        allowed, out = self._decide(self._edit_payload(target))
        self._assert_allow(allowed, out)

    def test_claude_scripts_py_requires_cover(self):
        """.claude/scripts/foo.py -> DENY."""
        target = ".claude/scripts/foo.py"
        (self.root / target).write_text("# foo\n", encoding="utf-8")
        allowed, out = self._decide(self._edit_payload(target))
        self._assert_deny(allowed, out)

    def test_worktrees_py_outside_dual_requires_cover(self):
        """worktrees/random/foo.py (no .dual-base-ref) -> DENY."""
        target = "worktrees/random/foo.py"
        (self.root / "worktrees" / "random").mkdir(parents=True)
        (self.root / target).write_text("# foo\n", encoding="utf-8")
        allowed, out = self._decide(self._edit_payload(target))
        self._assert_deny(allowed, out)

    def test_worktrees_dual_teams_py_allow(self):
        """worktrees/feature/.dual-base-ref present -> ALLOW (Y6/Y11 preserved)."""
        wt = self.root / "worktrees" / "feature" / "claude" / "task-A"
        wt.mkdir(parents=True)
        (wt / ".dual-base-ref").write_text("main\n", encoding="utf-8")
        target_abs = wt / "foo.py"
        target_abs.write_text("# foo\n", encoding="utf-8")
        target_rel = target_abs.relative_to(self.root).as_posix()
        allowed, out = self._decide(self._edit_payload(target_rel))
        self._assert_allow(allowed, out)



# ======================================================================
# AC-2 вЂ” Invariant 2: Bash counts
# ======================================================================
class TestI2BashCounts(_Base):
    """Bash command effects on code paths require cover."""

    def test_bash_python_script_in_work_requires_cover(self):
        cmd = "py -3 work/sync-template-to-target.py"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_pytest_allow(self):
        cmd = "pytest tests/"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_cp_code_to_code_requires_cover(self):
        cmd = "cp src/a.py src/b.py"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_cp_md_to_md_allow(self):
        cmd = "cp README.md /tmp/"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_sed_i_on_code_requires_cover(self):
        cmd = "sed -i 's/x/y/' src/auth.py"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_sed_i_on_md_allow(self):
        cmd = "sed -i 's/x/y/' work/notes.md"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_redirect_to_code_requires_cover(self):
        cmd = "echo \"x\" > src/foo.py"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_heredoc_to_code_requires_cover(self):
        cmd = "cat > src/foo.py << EOF\nbody\nEOF"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_powershell_set_content_code_requires_cover(self):
        cmd = "powershell -Command \"Set-Content -Path src/foo.py -Value '...'\""
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_powershell_set_content_md_allow(self):
        cmd = "powershell -Command \"Set-Content -Path notes.md -Value '...'\""
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_git_apply_requires_cover(self):
        cmd = "git apply patch.diff"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_git_checkout_code_file_requires_cover(self):
        cmd = "git checkout main src/auth.py"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_codex_ask_allow(self):
        cmd = "py -3 .claude/scripts/codex-ask.py \"hello\""
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_dual_teams_spawn_allow(self):
        cmd = "py -3 .claude/scripts/dual-teams-spawn.py --tasks T1.md"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_python_dash_c_open_write_requires_cover(self):
        cmd = "python -c \"open('src/x.py','w').write('...')\""
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_python_dash_c_print_allow(self):
        cmd = "python -c \"print(2+2)\""
        allowed, out = self._decide(self._bash_payload(cmd))

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "def (main|decide|deny|allow|handle|extract|find_cover|record)|permissionDecision|sys.exit|stderr|tool_name|Notebook|Bash|return False|return True" .claude/hooks/codex-delegate-enforcer.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/hooks/codex-delegate-enforcer.py | Select-Object -Skip 240 -First 320' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/hooks/test_codex_delegate_enforcer_invariants.py | Select-Object -Skip 190 -First 260' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/hooks/test_codex_delegate_enforcer.py | Select-Object -Skip 250 -First 260' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
 succeeded in 131ms:
10:I2. Bash counts. PreToolUse(Bash) tokenizes the command; mutating verbs
44:    for _stream in (sys.stdin, sys.stdout, sys.stderr):
84:# I2 - Bash classification tables.
142:    """Create enforcer logger: file if writable else stderr-only."""
158:    sh = logging.StreamHandler(sys.stderr)
188:            return False
197:                return True
203:            return False
249:                return True
259:                return True
263:            return True
264:    return False
277:        return True
280:        return False
282:    return False
362:            return True
365:                return True
371:                return True
373:            return True
377:                return True
378:    return False
396:def find_cover(project_dir: Path, target_rel_posix: str) -> tuple:
405:            return False, "no-results-dir"
423:            return False, "no-results"
480:                    return True, "covered-by:" + rpath.name
492:        return False, reason
495:        return False, "parse-error: " + str(exc)
499:# I2 - Bash command parsing
503:    """Split a Bash command on ; && || | into sub-commands (quote-aware)."""
573:        return False
589:            return True
592:                return True
593:    return False
630:    """Classify a Bash command. Returns dict with decision/reason/targets."""
759:            return True
761:            return True
762:    return False
906:        "bash-no-cover": "Bash command would mutate code without cover",
923:              tool_name: str = "Edit") -> None:
930:            "permissionDecision": "deny",
931:            "permissionDecisionReason": message,
937:        "tool": tool_name,
949:def extract_targets(payload: dict) -> list:
950:    """Collect every file path this Edit/Write/MultiEdit/NotebookEdit call edits."""
953:    tool_name = payload.get("tool_name", "")
958:    if tool_name in {"Edit", "Write", "NotebookEdit"}:
962:    elif tool_name == "MultiEdit":
983:def decide(payload: dict, project_dir: Path) -> bool:
987:    tool_name = payload.get("tool_name", "") if isinstance(payload, dict) else ""
988:    logger.info("decide.enter event=%s tool=%s", event, tool_name)
991:        return True
992:    if tool_name not in {"Edit", "Write", "MultiEdit", "Bash", "NotebookEdit"}:
993:        logger.info("decide.passthrough reason=unknown-tool tool=%s", tool_name)
994:        return True
997:        return True
999:    if tool_name == "Bash":
1001:    return _decide_edit(payload, project_dir, tool_name)
1004:def _decide_edit(payload: dict, project_dir: Path, tool_name: str) -> bool:
1005:    """Edit/Write/MultiEdit/NotebookEdit branch."""
1009:        logger.info("decide.passthrough reason=no-targets tool=%s", tool_name)
1010:        return True
1023:                "ts": _now_iso(), "tool": tool_name, "path": rel,
1031:                "ts": _now_iso(), "tool": tool_name, "path": rel,
1037:            emit_deny(rel, reason, project_dir, tool_name=tool_name)
1039:            return False
1042:            "ts": _now_iso(), "tool": tool_name, "path": rel,
1046:    return True
1050:    """Bash branch (I2). Parse command, classify, check cover for each target."""
1055:        return True
1059:        return True
1064:            "ts": _now_iso(), "tool": "Bash", "cmd": command[:200],
1067:        return True
1071:        emit_deny("<bash-command>", "bash-no-cover", project_dir, tool_name="Bash")
1072:        return False
1075:            emit_deny(target, "bash-no-cover", project_dir, tool_name="Bash")
1077:            return False
1087:                "ts": _now_iso(), "tool": "Bash", "path": rel,
1093:            emit_deny(rel, reason, project_dir, tool_name="Bash")
1095:            return False
1097:            "ts": _now_iso(), "tool": "Bash", "path": rel,
1101:    return True
1104:def main() -> int:
1131:    sys.exit(main())

 succeeded in 189ms:
def is_exempt(rel_path: str) -> bool:
    """True iff rel_path matches any exempt glob (NON-CODE only)."""
    logger = logging.getLogger(HOOK_NAME)
    for pattern in EXEMPT_PATTERNS:
        if pattern.endswith("/**"):
            prefix = pattern[:-3].rstrip("/")
            if rel_path == prefix or rel_path.startswith(prefix + "/"):
                logger.debug("is_exempt.match pattern=%s", pattern)
                return True
            continue
        if "**" in pattern:
            left, _, right = pattern.partition("**")
            left = left.rstrip("/")
            right = right.lstrip("/")
            left_ok = (not left) or rel_path == left or rel_path.startswith(left + "/")
            right_ok = (not right) or fnmatch.fnmatch(rel_path, "*" + right)
            if left_ok and right_ok:
                logger.debug("is_exempt.match pattern=%s (double-glob)", pattern)
                return True
            continue
        if fnmatch.fnmatch(rel_path, pattern):
            logger.debug("is_exempt.match pattern=%s", pattern)
            return True
    return False


def requires_cover(rel_path: str) -> bool:
    """True iff path needs a Codex cover.

    I1 (Extension wins): code extensions ALWAYS require cover, regardless
    of path. Exempt globs only apply to non-code files.
    """
    logger = logging.getLogger(HOOK_NAME)
    logger.info("requires_cover.enter rel=%s", rel_path)
    if is_code_extension(rel_path):
        logger.info("requires_cover.exit rel=%s result=True reason=code-ext-wins", rel_path)
        return True
    if is_exempt(rel_path):
        logger.info("requires_cover.exit rel=%s result=False reason=non-code-exempt", rel_path)
        return False
    logger.info("requires_cover.exit rel=%s result=False reason=non-code-default", rel_path)
    return False


def _strip_md_markers(line: str) -> str:
    """Strip leading bullets/quotes, surrounding bold/italic/backticks."""
    s = line.lstrip(" \t-*>").strip()
    return s.replace("**", "").replace("__", "").replace("`", "")


def parse_result_fields(result_path: Path) -> dict:
    """Extract status and task_file from a task-*-result.md."""
    logger = logging.getLogger(HOOK_NAME)
    out: dict = {}
    try:
        text = result_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        logger.info("parse_result_fields.read_err path=%s exc=%s", result_path.name, exc)
        return out
    for raw in text.splitlines():
        stripped = _strip_md_markers(raw)
        if "status" not in out:
            m = _STATUS_RE.match(stripped)
            if m:
                out["status"] = m.group(1).strip().lower()
        if "task_file" not in out:
            m2 = _TASK_FILE_RE.match(stripped)
            if m2:
                out["task_file"] = m2.group(1).strip().strip("`").strip()
        if "status" in out and "task_file" in out:
            break
    return out


def parse_scope_fence(task_path: Path) -> list:
    """Extract Allowed paths entries from task-N.md Scope Fence."""
    logger = logging.getLogger(HOOK_NAME)
    try:
        text = task_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        logger.info("parse_scope_fence.read_err path=%s exc=%s", task_path.name, exc)
        return []
    heading = _SCOPE_FENCE_HEADING_RE.search(text)
    if not heading:
        return []
    tail = text[heading.end():]
    next_hdr = _NEXT_HEADING_RE.search(tail)
    section = tail[: next_hdr.start()] if next_hdr else tail
    allowed = _ALLOWED_SECTION_RE.search(section)
    if not allowed:
        return []
    entries: list = []
    for line in allowed.group(1).splitlines():
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        entry = stripped.lstrip("-").strip().strip("`").strip()
        entry = _TRAILING_PAREN_RE.sub("", entry).strip().strip("`").strip()
        if not entry:
            continue
        entries.append(entry.replace("\\", "/").rstrip("/"))
    return entries


def path_in_fence(target_rel_posix: str, fence: Iterable) -> bool:
    """True if target path is explicitly covered by a fence entry.

    I3 (Path-exact coverage) supports:
      - exact match: 'src/auth.py' covers 'src/auth.py'
      - directory prefix: 'src/auth' covers 'src/auth/login.py'
      - fnmatch glob: 'src/auth/*.py' covers 'src/auth/login.py'
      - recursive glob: 'src/**' covers nested paths
    """
    target = target_rel_posix.rstrip("/")
    for raw_entry in fence:
        if not raw_entry:
            continue
        entry = raw_entry.rstrip("/")
        if not entry:
            continue
        if target == entry:
            return True
        if not any(c in entry for c in "*?["):
            if target.startswith(entry + "/"):
                return True
            continue
        # Glob match.
        simple = re.sub(r"/(?:\*\*|\*)$", "", entry).rstrip("/")
        if simple and not any(c in simple for c in "*?["):
            if target == simple or target.startswith(simple + "/"):
                return True
        if fnmatch.fnmatch(target, entry):
            return True
        if "**" in entry:
            translated = entry.replace("**", "*")
            if fnmatch.fnmatch(target, translated):
                return True
    return False


def _resolve_task_file(project_dir: Path, raw: str) -> Optional[Path]:
    """Resolve a result.md task_file pointer to absolute Path."""
    logger = logging.getLogger(HOOK_NAME)
    if not raw:
        return None
    try:
        p = Path(raw.strip())
        if not p.is_absolute():
            p = project_dir / p
        return p.resolve()
    except (OSError, ValueError) as exc:
        logger.info("resolve_task_file.err raw=%r exc=%s", raw, exc)
        return None


def find_cover(project_dir: Path, target_rel_posix: str) -> tuple:
    """Search recent result.md artefacts for one whose Scope Fence
    EXPLICITLY lists target_rel_posix (I3 - path-exact coverage)."""
    logger = logging.getLogger(HOOK_NAME)
    logger.info("find_cover.enter target=%s", target_rel_posix)
    try:
        results_dir = project_dir / CODEX_IMPLEMENTATIONS_DIR
        if not results_dir.is_dir():
            logger.info("find_cover.no-dir dir=%s", results_dir)
            return False, "no-results-dir"
        candidates: list = []
        for rp in results_dir.glob("task-*-result.md"):
            try:
                candidates.append((rp.stat().st_mtime, rp))
            except OSError:
                continue
        inline_dir = results_dir / "inline"
        if inline_dir.is_dir():
            for rp in inline_dir.glob("task-*-result.md"):
                try:
                    candidates.append((rp.stat().st_mtime, rp))
                except OSError:
                    continue
        candidates.sort(key=lambda item: item[0], reverse=True)
        candidates = candidates[:MAX_RESULT_FILES_TO_SCAN]
        if not candidates:
            logger.info("find_cover.no-results")
            return False, "no-results"
        now = time.time()
        saw_fresh = False
        saw_fresh_pass = False
        best_reason = "stale"
        for mtime, rpath in candidates:
            age = now - mtime
            if age > RESULT_MAX_AGE_SECONDS:
                continue
            saw_fresh = True
            try:
                rresolved = rpath.resolve()
                rresolved.relative_to(project_dir)
            except (OSError, ValueError):
                logger.info("find_cover.symlink-escape path=%s", rpath.name)
                continue
            fields = parse_result_fields(rpath)
            status = fields.get("status", "")
            if status != "pass":
                if status == "fail":
                    best_reason = "fail-status"
                logger.info("find_cover.skip path=%s status=%s age=%.1fs",
                            rpath.name, status or "?", age)
                continue
            saw_fresh_pass = True
            task_candidates: list = []
            pointer = _resolve_task_file(project_dir, fields.get("task_file", ""))
            if pointer is not None and pointer.is_file():
                task_candidates.append(pointer)
            name_match = _RESULT_NAME_RE.match(rpath.name)
            if name_match:
                task_id = name_match.group(1)
                tdir = project_dir / CODEX_TASKS_DIR
                if tdir.is_dir():
                    for pattern in ("T" + task_id + "-*.md",
                                    task_id + "-*.md",
                                    "task-" + task_id + ".md",
                                    "task-" + task_id + "-*.md"):
                        task_candidates.extend(tdir.glob(pattern))
            seen: set = set()
            unique: list = []
            for cand in task_candidates:
                if cand not in seen:
                    seen.add(cand)
                    unique.append(cand)
            if not unique:
                logger.info("find_cover.no-task-file result=%s", rpath.name)
                best_reason = "scope-miss"
                continue
            for tpath in unique:
                fence = parse_scope_fence(tpath)
                if not fence:
                    logger.info("find_cover.empty-fence task=%s", tpath.name)
                    continue
                if path_in_fence(target_rel_posix, fence):
                    logger.info("find_cover.MATCH target=%s result=%s task=%s age=%.1fs",
                                target_rel_posix, rpath.name, tpath.name, age)
                    return True, "covered-by:" + rpath.name
                logger.info("find_cover.scope-miss target=%s task=%s entries=%d",
                            target_rel_posix, tpath.name, len(fence))
                best_reason = "scope-miss"
        if not saw_fresh:
            reason = "stale"
        elif saw_fresh_pass:
            reason = "scope-miss"
        else:
            reason = best_reason
        logger.info("find_cover.exit target=%s covered=False reason=%s",
                    target_rel_posix, reason)
        return False, reason
    except Exception as exc:
        logger.exception("find_cover.unexpected target=%s exc=%s", target_rel_posix, exc)
        return False, "parse-error: " + str(exc)


# ----------------------------------------------------------------------
# I2 - Bash command parsing
# ----------------------------------------------------------------------

def _split_logical_commands(command: str) -> list:
    """Split a Bash command on ; && || | into sub-commands (quote-aware)."""
    out: list = []
    buf: list = []
    i = 0
    n = len(command)
    in_squote = False
    in_dquote = False
    while i < n:
        c = command[i]
        if c == "'" and not in_dquote:
            in_squote = not in_squote
            buf.append(c)
            i += 1
            continue
        if c == '"' and not in_squote:
            in_dquote = not in_dquote
            buf.append(c)
            i += 1
            continue
        if not in_squote and not in_dquote:
            if c == ";":
                out.append("".join(buf))
                buf = []
                i += 1
                continue
            if c == "|":
                out.append("".join(buf))
                buf = []
                i += 1
                if i < n and command[i] == "|":
                    i += 1
                continue
            if c == "&" and i + 1 < n and command[i + 1] == "&":
                out.append("".join(buf))
                buf = []
                i += 2
                continue
        buf.append(c)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        out.append(tail)
    return [c.strip() for c in out if c.strip()]


def _safe_shlex(command: str) -> list:
    """shlex.split the command; on failure, fall back to whitespace split."""
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def _command_basename(token: str) -> str:
    """Extract the program basename for whitelist/keyword matching."""
    if not token:
        return ""
    if "=" in token and not token.startswith("/") and not token.startswith("."):

 succeeded in 187ms:
        self._assert_allow(allowed, out)

    def test_bash_cp_code_to_code_requires_cover(self):
        cmd = "cp src/a.py src/b.py"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_cp_md_to_md_allow(self):
        cmd = "cp README.md /tmp/"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_sed_i_on_code_requires_cover(self):
        cmd = "sed -i 's/x/y/' src/auth.py"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_sed_i_on_md_allow(self):
        cmd = "sed -i 's/x/y/' work/notes.md"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_redirect_to_code_requires_cover(self):
        cmd = "echo \"x\" > src/foo.py"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_heredoc_to_code_requires_cover(self):
        cmd = "cat > src/foo.py << EOF\nbody\nEOF"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_powershell_set_content_code_requires_cover(self):
        cmd = "powershell -Command \"Set-Content -Path src/foo.py -Value '...'\""
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_powershell_set_content_md_allow(self):
        cmd = "powershell -Command \"Set-Content -Path notes.md -Value '...'\""
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_git_apply_requires_cover(self):
        cmd = "git apply patch.diff"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_git_checkout_code_file_requires_cover(self):
        cmd = "git checkout main src/auth.py"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_codex_ask_allow(self):
        cmd = "py -3 .claude/scripts/codex-ask.py \"hello\""
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_dual_teams_spawn_allow(self):
        cmd = "py -3 .claude/scripts/dual-teams-spawn.py --tasks T1.md"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_python_dash_c_open_write_requires_cover(self):
        cmd = "python -c \"open('src/x.py','w').write('...')\""
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_python_dash_c_print_allow(self):
        cmd = "python -c \"print(2+2)\""
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_ls_allow(self):
        cmd = "ls -la work/"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_git_status_allow(self):
        cmd = "git status"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_python_dash_alone_requires_cover(self):
        """python - (stdin) is opaque -> always require cover."""
        cmd = "python - < script.py"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)



# ======================================================================
# AC-3 вЂ” Invariant 3: Path-exact coverage (no temporal carryover)
# ======================================================================
class TestI3PathExactCoverage(_Base):
    """Codex artifact must EXPLICITLY list the target path."""

    def test_artifact_covers_path_a_blocks_path_b(self):
        """Artifact lists src/a.py; Edit on src/b.py -> DENY."""
        self._write_task("aa", ["src/a.py"])
        self._write_result("aa", "pass")
        (self.root / "src" / "b.py").write_text("# b\n", encoding="utf-8")
        allowed, out = self._decide(self._edit_payload("src/b.py"))
        self._assert_deny(allowed, out)

    def test_artifact_covers_path_a_allows_path_a(self):
        """Same artifact; Edit on src/a.py -> ALLOW."""
        self._write_task("ab", ["src/a.py"])
        self._write_result("ab", "pass")
        (self.root / "src" / "a.py").write_text("# a\n", encoding="utf-8")
        allowed, out = self._decide(self._edit_payload("src/a.py"))
        self._assert_allow(allowed, out)

    def test_glob_in_scope_fence_matches(self):
        """Artifact lists src/auth/*.py; Edit on src/auth/login.py -> ALLOW."""
        (self.root / "src" / "auth").mkdir(parents=True)
        (self.root / "src" / "auth" / "login.py").write_text("# login\n",
                                                             encoding="utf-8")
        self._write_task("gl", ["src/auth/*.py"])
        self._write_result("gl", "pass")
        allowed, out = self._decide(self._edit_payload("src/auth/login.py"))
        self._assert_allow(allowed, out)

    def test_stale_artifact_outside_15min_blocks(self):
        """Artifact older than 15 min covering exact path -> DENY."""
        self._write_task("st", ["src/a.py"])
        self._write_result("st", "pass", age_seconds=20 * 60)
        (self.root / "src" / "a.py").write_text("# a\n", encoding="utf-8")
        allowed, out = self._decide(self._edit_payload("src/a.py"))
        self._assert_deny(allowed, out)

    def test_failed_artifact_blocks_even_if_covers_path(self):
        """status: fail covering path -> DENY."""
        self._write_task("fa", ["src/a.py"])
        self._write_result("fa", "fail")
        (self.root / "src" / "a.py").write_text("# a\n", encoding="utf-8")
        allowed, out = self._decide(self._edit_payload("src/a.py"))
        self._assert_deny(allowed, out)



# ======================================================================
# AC-4 вЂ” Invariant 4: Skip-token ledger + actionable block messages
# ======================================================================
class TestI4Ledger(_Base):
    """Skip-ledger.jsonl audit + actionable DENY messages."""

    def _read_ledger(self):
        ledger = self.root / "work" / "codex-implementations" / "skip-ledger.jsonl"
        if not ledger.exists():
            return []
        text = ledger.read_text(encoding="utf-8").strip()
        return [json.loads(ln) for ln in text.splitlines() if ln.strip()]

    def test_skip_ledger_appends_on_allow(self):
        """Allowed Edit appends one JSONL line with decision=allow + reason."""
        self._write_task("la", ["src/a.py"])
        self._write_result("la", "pass")
        (self.root / "src" / "a.py").write_text("# a\n", encoding="utf-8")
        before = len(self._read_ledger())
        allowed, _ = self._decide(self._edit_payload("src/a.py"))
        self.assertTrue(allowed)
        after = self._read_ledger()
        self.assertEqual(len(after) - before, 1, "expected exactly 1 new ledger line")
        last = after[-1]
        self.assertEqual(last["decision"], "allow")
        self.assertIn("reason", last)
        self.assertEqual(last["path"], "src/a.py")

    def test_skip_ledger_appends_on_deny(self):
        """Denied Edit appends one JSONL line with decision=deny + reason."""
        (self.root / "src" / "a.py").write_text("# a\n", encoding="utf-8")
        before = len(self._read_ledger())
        allowed, _ = self._decide(self._edit_payload("src/a.py"))
        self.assertFalse(allowed)
        after = self._read_ledger()
        self.assertEqual(len(after) - before, 1)
        last = after[-1]
        self.assertEqual(last["decision"], "deny")
        self.assertIn("reason", last)

    def test_skip_ledger_jsonl_parseable(self):
        """All ledger lines parse as valid JSON with required keys."""
        # Trigger a few decisions.
        (self.root / "src" / "a.py").write_text("# a\n", encoding="utf-8")
        self._decide(self._edit_payload("src/a.py"))  # deny
        self._decide(self._edit_payload("CLAUDE.md"))  # allow
        ledger = self._read_ledger()
        self.assertGreaterEqual(len(ledger), 2)
        required = {"ts", "tool", "decision", "reason"}
        for entry in ledger:
            self.assertTrue(required.issubset(entry.keys()),
                            "missing keys in entry: " + str(entry))

    def test_block_message_includes_inline_dual_command(self):
        """DENY error message contains codex-inline-dual.py --describe + path."""
        target = "src/auth.py"
        (self.root / "src" / "auth.py").write_text("# a\n", encoding="utf-8")
        allowed, stdout = self._decide(self._edit_payload(target))
        self.assertFalse(allowed)
        parsed = json.loads(stdout)
        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("codex-inline-dual.py", reason)
        self.assertIn("--describe", reason)
        self.assertIn(target, reason)



# ======================================================================
# AC-5 вЂ” Regression: existing tests + selftest still pass
# ======================================================================
class TestRegression(unittest.TestCase):
    """Regression suite вЂ” runs the existing 36-test suite and selftest."""

    def test_existing_tests_still_pass(self):
        """Run pytest on test_codex_delegate_enforcer.py вЂ” exit 0."""
        existing = HERE / "test_codex_delegate_enforcer.py"
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(existing), "-q",
             "--tb=line", "--no-header"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=120,
        )
        self.assertEqual(
            result.returncode, 0,
            "existing tests failed: stdout=" + result.stdout
            + " stderr=" + result.stderr,
        )

    def test_dual_teams_selftest_still_passes(self):
        """Run dual-teams-selftest.py вЂ” exit 0."""
        # Walk up to project root (the worktree itself).
        project_root = HERE.parent.parent
        selftest = project_root / ".claude" / "scripts" / "dual-teams-selftest.py"
        if not selftest.is_file():
            self.skipTest("dual-teams-selftest.py not found at " + str(selftest))
        result = subprocess.run(
            [sys.executable, str(selftest)],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=180, cwd=str(project_root),
        )
        self.assertEqual(
            result.returncode, 0,
            "dual-teams-selftest failed: stdout=" + result.stdout[-1000:]
            + " stderr=" + result.stderr[-500:],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

 succeeded in 186ms:

    def test_10a_malformed_result_passthrough(self) -> None:
        """AC12.10a: malformed result.md -> no crash, handled gracefully."""
        # Write a recent file but with completely corrupt body.
        result_file = self.root / "work" / "codex-implementations" / (
            "task-10-result.md"
        )
        result_file.write_bytes(b"\x00\x01\xff garbage no fields here")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        # No crash: exit 0. Since no fence covers target, it is denied -
        # the point is the script didn't blow up (no traceback in stderr).
        self.assertEqual(code, 0)
        self.assertNotIn("Traceback", err)

    def test_10b_corrupt_json_payload_passthrough(self) -> None:
        """AC12.10b: corrupt JSON payload -> pass-through, no crash, exit 0."""
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)}
        result = subprocess.run(
            [sys.executable, str(ENFORCER_PATH)],
            input="{this-is-not-json",
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            env=env, timeout=30,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")
        self.assertNotIn("Traceback", result.stderr)

    def test_11_non_edit_event_passthrough(self) -> None:
        """AC12.11: non-Edit tool (Bash) -> pass-through (exit 0, no deny)."""
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
        }
        code, out, err = self._run_enforcer(payload)
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "")


class TestDualTeamsSentinel(unittest.TestCase):
    """Regression tests for dual-teams worktree sentinel detection."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()

    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
            project_dir = Path(tmpdir).resolve()
            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")

            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))

    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
            project_dir = Path(tmpdir).resolve()
            nested = project_dir / "worktrees" / "validation" / "claude"
            nested.mkdir(parents=True)
            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")

            self.assertTrue(self.mod.is_dual_teams_worktree(nested))

    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
            project_dir = Path(tmpdir).resolve()
            nested = project_dir / "a" / "b" / "c"
            nested.mkdir(parents=True)

            self.assertFalse(self.mod.is_dual_teams_worktree(nested))

    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
            project_dir = Path(tmpdir).resolve()
            (project_dir / ".dual-base-ref").mkdir()

            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))


class TestDualTeamsDecide(BaseEnforcerTest):
    """Regression tests for the dual-teams passthrough in decide()."""

    def setUp(self) -> None:
        super().setUp()
        self.mod = _load_module()
        self.script_rel = ".claude/scripts/foo.py"
        (self.root / ".claude" / "scripts").mkdir(parents=True)
        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")

    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
        shutil.rmtree(self.root / "work", ignore_errors=True)

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)

        self.assertTrue(allowed)
        self.assertEqual(stdout.getvalue().strip(), "")

    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)

        self.assertFalse(allowed)
        parsed = json.loads(stdout.getvalue())
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")


class TestHelpers(unittest.TestCase):
    """Direct unit tests of helper functions (no subprocess)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()

    def test_is_code_extension_positive(self) -> None:
        for p in ("a.py", "x/y/z.js", "lib/mod.rs", "s.cpp", "x.SQL"):
            self.assertTrue(self.mod.is_code_extension(p), p)

    def test_is_code_extension_negative(self) -> None:
        for p in ("README.md", "doc.txt", "config.yaml", "a.json", "b"):
            self.assertFalse(self.mod.is_code_extension(p), p)

    def test_is_exempt_memory_star_star(self) -> None:
        self.assertTrue(self.mod.is_exempt(".claude/memory/activeContext.md"))
        self.assertTrue(self.mod.is_exempt(".claude/memory/daily/2026-04-24.md"))

    def test_is_exempt_top_level_files(self) -> None:
        for p in ("CLAUDE.md", "AGENTS.md", "README.md", ".gitignore", "LICENSE"):
            self.assertTrue(self.mod.is_exempt(p), p)

    def test_is_exempt_guides_skills_adr(self) -> None:
        self.assertTrue(self.mod.is_exempt(".claude/adr/adr-001.md"))
        self.assertTrue(self.mod.is_exempt(".claude/guides/foo.md"))
        self.assertTrue(self.mod.is_exempt(".claude/skills/bar/SKILL.md"))

    def test_is_exempt_negative(self) -> None:
        self.assertFalse(self.mod.is_exempt(".claude/hooks/my_hook.py"))
        self.assertFalse(self.mod.is_exempt("src/main.py"))

    def test_requires_cover_positive(self) -> None:
        self.assertTrue(self.mod.requires_cover(".claude/hooks/x.py"))
        self.assertTrue(self.mod.requires_cover("src/main.ts"))

    def test_requires_cover_negative_non_code(self) -> None:
        self.assertFalse(self.mod.requires_cover("docs/readme.md"))

    def test_requires_cover_negative_exempt(self) -> None:
        # .claude/skills/**/*.md is exempt, and .md is non-code anyway.
        self.assertFalse(self.mod.requires_cover("CLAUDE.md"))
        # Z1/I1 (Extension wins): non-code under work/** is exempt;
        # code under work/** STILL requires cover.
        self.assertFalse(self.mod.requires_cover("work/notes.md"))
        self.assertTrue(self.mod.requires_cover("work/scripts/helper.py"))

    def test_path_in_fence_exact_file(self) -> None:
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/c.py"]))

    def test_path_in_fence_dir_prefix(self) -> None:
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b"]))
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/"]))

    def test_path_in_fence_no_partial_segment(self) -> None:
        self.assertFalse(self.mod.path_in_fence("a/bb/c.py", ["a/b"]))

    def test_path_in_fence_strips_trailing_globs(self) -> None:
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/**"]))
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/*"]))

    def test_parse_result_fields_status_pass(self) -> None:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".md", delete=False, encoding="utf-8"
        ) as fh:
            fh.write("# result\n\n- status: pass\n- task_file: t.md\n")
            p = Path(fh.name)
        try:
            fields = self.mod.parse_result_fields(p)
            self.assertEqual(fields.get("status"), "pass")
            self.assertEqual(fields.get("task_file"), "t.md")
        finally:
            p.unlink()

    def test_parse_scope_fence_strips_backticks_and_annotations(self) -> None:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".md", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(
                "# Task\n\n"
                "## Scope Fence\n"
                "**Allowed paths (may be written):**\n"
                "- `.claude/hooks/x.py` (new)\n"
                "- `.claude/hooks/test_x.py`\n\n"
                "**Forbidden paths:**\n- else/\n\n## Next\n"
            )
            p = Path(fh.name)
        try:
            fence = self.mod.parse_scope_fence(p)
            self.assertIn(".claude/hooks/x.py", fence)
            self.assertIn(".claude/hooks/test_x.py", fence)
        finally:
            p.unlink()

    def test_extract_targets_edit(self) -> None:
        paths = self.mod.extract_targets({
            "tool_name": "Edit",
            "tool_input": {"file_path": "a.py", "old_string": "x", "new_string": "y"},
        })
        self.assertEqual(paths, ["a.py"])

    def test_extract_targets_multiedit(self) -> None:
        paths = self.mod.extract_targets({
            "tool_name": "MultiEdit",
            "tool_input": {
                "edits": [
                    {"file_path": "a.py", "old_string": "x", "new_string": "y"},
                    {"file_path": "b.py", "old_string": "x", "new_string": "y"},
                ],
            },
        })
        self.assertEqual(sorted(paths), ["a.py", "b.py"])

    def test_extract_targets_missing_is_empty(self) -> None:
        self.assertEqual(self.mod.extract_targets({}), [])
        self.assertEqual(self.mod.extract_targets({"tool_name": "Edit"}), [])
        self.assertEqual(self.mod.extract_targets(None), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/hooks/codex-delegate-enforcer.py | Select-Object -Skip 620 -First 520' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/hooks/codex-delegate-enforcer.py | Select-Object -Skip 500 -First 160' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
 succeeded in 182ms:

def _split_logical_commands(command: str) -> list:
    """Split a Bash command on ; && || | into sub-commands (quote-aware)."""
    out: list = []
    buf: list = []
    i = 0
    n = len(command)
    in_squote = False
    in_dquote = False
    while i < n:
        c = command[i]
        if c == "'" and not in_dquote:
            in_squote = not in_squote
            buf.append(c)
            i += 1
            continue
        if c == '"' and not in_squote:
            in_dquote = not in_dquote
            buf.append(c)
            i += 1
            continue
        if not in_squote and not in_dquote:
            if c == ";":
                out.append("".join(buf))
                buf = []
                i += 1
                continue
            if c == "|":
                out.append("".join(buf))
                buf = []
                i += 1
                if i < n and command[i] == "|":
                    i += 1
                continue
            if c == "&" and i + 1 < n and command[i + 1] == "&":
                out.append("".join(buf))
                buf = []
                i += 2
                continue
        buf.append(c)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        out.append(tail)
    return [c.strip() for c in out if c.strip()]


def _safe_shlex(command: str) -> list:
    """shlex.split the command; on failure, fall back to whitespace split."""
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def _command_basename(token: str) -> str:
    """Extract the program basename for whitelist/keyword matching."""
    if not token:
        return ""
    if "=" in token and not token.startswith("/") and not token.startswith("."):
        parts = token.split("=", 1)
        if "/" not in parts[0] and "\\" not in parts[0]:
            return ""
    name = Path(token).name.lower()
    if name.endswith(".exe"):
        name = name[:-4]
    return name


def _looks_like_path(token: str) -> bool:
    """True iff token looks like a file path (has '/' or '\' or '.')."""
    if not token or token.startswith("-"):
        return False
    return ("/" in token or "\\" in token or "." in token)


def _normalize_path_token(token: str) -> str:
    """Normalize a path token (POSIX, no quotes)."""
    return token.strip().strip("'\"").replace("\\", "/")


def _is_dual_tooling_invocation(tokens: list) -> bool:
    """True iff tokens reference a project-owned dual-implement script."""
    for tok in tokens[1:6]:
        if not tok or tok.startswith("-"):
            continue
        norm = _normalize_path_token(tok)
        if norm in _BASH_DUAL_TOOLING:
            return True
        for known in _BASH_DUAL_TOOLING:
            if norm.endswith(known) or norm == known:
                return True
    return False


def _scan_pwsh_for_paths(command: str) -> list:
    """Scan a PowerShell command body for code-file paths near mutating cmdlets."""
    body = command
    targets: list = []
    lower = body.lower()
    has_mut = any(c in lower for c in _PWSH_MUTATING_CMDLETS)
    if not has_mut:
        return targets
    for m in re.finditer(r"-Path\s+['\"]([^'\"]+)['\"]", body, re.IGNORECASE):
        targets.append(_normalize_path_token(m.group(1)))
    for m in re.finditer(r"-Path\s+(\S+)", body, re.IGNORECASE):
        cand = _normalize_path_token(m.group(1))
        if cand and cand not in targets:
            targets.append(cand)
    for m in re.finditer(r"['\"]([^'\"\n]+)['\"]", body):
        cand = _normalize_path_token(m.group(1))
        if cand and is_code_extension(cand) and cand not in targets:
            targets.append(cand)
    return [t for t in targets if t]


def _extract_redirect_targets(command: str) -> list:
    """Extract files appearing on the RHS of > or >> redirects."""
    out: list = []
    scan = re.sub(r"'[^']*'", "", command)
    scan = re.sub(r'"[^"]*"', "", scan)
    for m in re.finditer(r">{1,2}\s*([^\s|;&<>]+)", scan):
        cand = _normalize_path_token(m.group(1))
        if cand and not cand.startswith("&"):
            out.append(cand)
    return out


def parse_bash_command(command: str) -> dict:
    """Classify a Bash command. Returns dict with decision/reason/targets."""
    logger = logging.getLogger(HOOK_NAME)
    logger.info("parse_bash_command.enter cmd=%r", command[:200])
    if not command or not command.strip():
        return {"decision": "allow", "reason": "empty-command", "targets": []}
    sub_commands = _split_logical_commands(command)
    all_targets: list = []
    block_reasons: list = []
    for sub in sub_commands:
        result = _classify_single_command(sub)
        if result["decision"] == "require_cover":
            all_targets.extend(result["targets"])
            block_reasons.append(result["reason"])
    seen: set = set()
    unique_targets: list = []
    for t in all_targets:
        if t not in seen:
            seen.add(t)
            unique_targets.append(t)
    if unique_targets or block_reasons:
        out = {
            "decision": "require_cover",
            "reason": "; ".join(block_reasons) if block_reasons else "code-mutation",
            "targets": unique_targets,
        }
        logger.info("parse_bash_command.exit decision=require_cover targets=%s", unique_targets)
        return out
    logger.info("parse_bash_command.exit decision=allow")
    return {"decision": "allow", "reason": "whitelist-or-no-mutation", "targets": []}



 succeeded in 200ms:
    scan = re.sub(r'"[^"]*"', "", scan)
    for m in re.finditer(r">{1,2}\s*([^\s|;&<>]+)", scan):
        cand = _normalize_path_token(m.group(1))
        if cand and not cand.startswith("&"):
            out.append(cand)
    return out


def parse_bash_command(command: str) -> dict:
    """Classify a Bash command. Returns dict with decision/reason/targets."""
    logger = logging.getLogger(HOOK_NAME)
    logger.info("parse_bash_command.enter cmd=%r", command[:200])
    if not command or not command.strip():
        return {"decision": "allow", "reason": "empty-command", "targets": []}
    sub_commands = _split_logical_commands(command)
    all_targets: list = []
    block_reasons: list = []
    for sub in sub_commands:
        result = _classify_single_command(sub)
        if result["decision"] == "require_cover":
            all_targets.extend(result["targets"])
            block_reasons.append(result["reason"])
    seen: set = set()
    unique_targets: list = []
    for t in all_targets:
        if t not in seen:
            seen.add(t)
            unique_targets.append(t)
    if unique_targets or block_reasons:
        out = {
            "decision": "require_cover",
            "reason": "; ".join(block_reasons) if block_reasons else "code-mutation",
            "targets": unique_targets,
        }
        logger.info("parse_bash_command.exit decision=require_cover targets=%s", unique_targets)
        return out
    logger.info("parse_bash_command.exit decision=allow")
    return {"decision": "allow", "reason": "whitelist-or-no-mutation", "targets": []}


def _classify_single_command(command: str) -> dict:
    """Classify one logical command (no ;, &&, ||, |)."""
    logger = logging.getLogger(HOOK_NAME)
    if not command or not command.strip():
        return {"decision": "allow", "reason": "empty", "targets": []}
    raw_lower = command.lower()
    is_pwsh = any(launcher in raw_lower for launcher in _BASH_PWSH_LAUNCHERS)
    tokens = _safe_shlex(command)
    if not tokens:
        return {"decision": "allow", "reason": "empty-tokens", "targets": []}
    if _is_dual_tooling_invocation(tokens):
        logger.info("classify.dual-tooling cmd=%r", command[:120])
        return {"decision": "allow", "reason": "dual-tooling", "targets": []}
    verb = _command_basename(tokens[0])

    # I2: redirect to a code path is a write regardless of leading verb
    # (echo > foo.py, cat > foo.py, printf > foo.py, etc.). Check first.
    early_redirects = [t for t in _extract_redirect_targets(command)
                       if is_code_extension(t)]
    if early_redirects:
        return {"decision": "require_cover",
                "reason": verb + "-redirect-to-code",
                "targets": early_redirects}

    if verb in _BASH_READONLY_VERBS:
        return {"decision": "allow", "reason": "readonly-verb", "targets": []}

    if verb in _BASH_TEST_RUNNERS:
        return {"decision": "allow", "reason": "test-runner", "targets": []}

    if verb in _BASH_PACKAGE_MANAGERS:
        return {"decision": "allow", "reason": "package-manager", "targets": []}

    if verb == "git" and len(tokens) >= 2:
        sub = _command_basename(tokens[1])
        if sub in {"status", "log", "diff", "show", "blame", "ls-files",
                   "rev-parse", "branch", "remote", "fetch", "worktree",
                   "config", "stash", "tag", "describe", "shortlog",
                   "ls-remote", "rev-list"}:
            return {"decision": "allow", "reason": "git-readonly", "targets": []}
        if sub in {"apply", "am"}:
            return {"decision": "require_cover",
                    "reason": "git-apply-opaque",
                    "targets": ["<git-apply-patch>"]}
        if sub in {"checkout", "restore", "mv", "rm"}:
            targets = _git_mutating_targets(tokens[1:], sub)
            if targets:
                return {"decision": "require_cover",
                        "reason": "git-" + sub,
                        "targets": targets}
            return {"decision": "allow", "reason": "git-" + sub + "-no-code-target",
                    "targets": []}
        if sub == "reset" and "--hard" in tokens:
            return {"decision": "require_cover",
                    "reason": "git-reset-hard",
                    "targets": ["<git-reset-hard>"]}
        return {"decision": "allow", "reason": "git-other", "targets": []}

    if is_pwsh or verb in _BASH_PWSH_LAUNCHERS:
        targets = _scan_pwsh_for_paths(command)
        code_targets = [t for t in targets if is_code_extension(t)]
        if code_targets:
            return {"decision": "require_cover",
                    "reason": "pwsh-mutating-cmdlet",
                    "targets": code_targets}
        return {"decision": "allow", "reason": "pwsh-no-code-target", "targets": []}

    if verb in _BASH_INPLACE_VERBS:
        if _has_inplace_flag(tokens):
            code_targets = _extract_code_path_args(tokens)
            if code_targets:
                return {"decision": "require_cover",
                        "reason": verb + "-inplace-on-code",
                        "targets": code_targets}
            return {"decision": "allow", "reason": verb + "-inplace-no-code",
                    "targets": []}
        return {"decision": "allow", "reason": verb + "-readonly", "targets": []}

    if verb in _BASH_MUTATING_VERBS:
        code_targets = _extract_code_path_args(tokens)
        if code_targets:
            return {"decision": "require_cover",
                    "reason": verb + "-on-code",
                    "targets": code_targets}
        return {"decision": "allow", "reason": verb + "-no-code-target", "targets": []}

    if verb in _BASH_INTERPRETERS:
        result = _classify_interpreter(tokens, command)
        if result is not None:
            return result

    return {"decision": "allow", "reason": "unknown-verb-allowed", "targets": []}


def _has_inplace_flag(tokens: list) -> bool:
    """True if any token is '-i', '-i.bak', '--in-place', or 'inplace' arg."""
    for i, tok in enumerate(tokens[1:], start=1):
        if tok == "-i" or tok.startswith("-i.") or tok == "--in-place":
            return True
        if tok == "inplace" and i >= 2 and tokens[i - 1] in ("-i", "--in-place"):
            return True
    return False


def _extract_code_path_args(tokens: list) -> list:
    """Extract path-like positional args whose extension is in CODE_EXTENSIONS."""
    out: list = []
    for tok in tokens[1:]:
        if not tok or tok.startswith("-"):
            continue
        norm = _normalize_path_token(tok)
        if not _looks_like_path(norm):
            continue
        if is_code_extension(norm):
            out.append(norm)
    return out


def _git_mutating_targets(args: list, sub: str) -> list:
    """Extract code-extension targets from git checkout|restore|mv|rm args."""
    out: list = []
    for tok in args[1:]:
        if not tok or tok.startswith("-"):
            continue
        norm = _normalize_path_token(tok)
        if not _looks_like_path(norm):
            continue
        if is_code_extension(norm):
            out.append(norm)
    return out


def _classify_interpreter(tokens: list, raw_command: str) -> Optional[dict]:
    """Classify python/bash/sh/node/... invocations."""
    logger = logging.getLogger(HOOK_NAME)
    verb = _command_basename(tokens[0])
    has_dash_alone = any(t == "-" for t in tokens[1:])
    has_dash_s = any(t == "-s" for t in tokens[1:])
    has_dash_c = False
    dash_c_index = -1
    for i, t in enumerate(tokens[1:], start=1):
        if t == "-c":
            has_dash_c = True
            dash_c_index = i
            break

    if has_dash_alone or has_dash_s:
        return {"decision": "require_cover",
                "reason": verb + "-stdin-opaque",
                "targets": ["<" + verb + "-stdin-opaque>"]}

    if has_dash_c and dash_c_index + 1 < len(tokens):
        snippet = tokens[dash_c_index + 1]
        write_patterns = [
            r"open\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]w",
            r"open\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]a",
            r"shutil\.copy[^\(]*\([^,]*,\s*['\"]([^'\"]+)['\"]",
            r"Path\s*\(\s*['\"]([^'\"]+)['\"]\s*\)\s*\.write",
        ]
        targets: list = []
        for pattern in write_patterns:
            for m in re.finditer(pattern, snippet):
                if m.groups():
                    cand = _normalize_path_token(m.group(1))
                    if cand and is_code_extension(cand):
                        targets.append(cand)
        if targets:
            return {"decision": "require_cover",
                    "reason": verb + "-c-write-to-code",
                    "targets": targets}
        if re.search(r"open\s*\([^)]*['\"][wa]", snippet):
            return {"decision": "require_cover",
                    "reason": verb + "-c-opaque-write",
                    "targets": ["<" + verb + "-c-opaque>"]}
        return {"decision": "allow", "reason": verb + "-c-no-write",
                "targets": []}

    skip_next = False
    script: Optional[str] = None
    for i, tok in enumerate(tokens[1:], start=1):
        if skip_next:
            skip_next = False
            continue
        if tok in ("-3", "-2", "-3.11", "-3.12", "-3.13", "-3.10"):
            continue
        if tok in ("-m", "-W", "-X"):
            return {"decision": "allow", "reason": verb + "-m-module",
                    "targets": []}
        if tok.startswith("-"):
            continue
        script = tok
        break

    if script is None:
        return {"decision": "allow", "reason": verb + "-repl", "targets": []}

    norm_script = _normalize_path_token(script)
    if not is_code_extension(norm_script):
        return {"decision": "allow", "reason": verb + "-non-code-script",
                "targets": []}

    for tool in _BASH_DUAL_TOOLING:
        if norm_script.endswith(tool) or norm_script == tool:
            return {"decision": "allow", "reason": "dual-tooling-script",
                    "targets": []}

    return {"decision": "require_cover",
            "reason": verb + "-script-execution",
            "targets": [norm_script]}


# ----------------------------------------------------------------------
# I4 - Skip ledger + actionable block messages
# ----------------------------------------------------------------------

def _append_skip_ledger(project_dir: Path, entry: dict) -> None:
    """Append one JSON line to skip-ledger.jsonl. Best-effort."""
    logger = logging.getLogger(HOOK_NAME)
    try:
        ledger = project_dir / SKIP_LEDGER_REL
        ledger.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(entry, ensure_ascii=False)
        with ledger.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError as exc:
        logger.exception("skip_ledger.write_err exc=%s", exc)
    except Exception as exc:
        logger.exception("skip_ledger.unexpected exc=%s", exc)


def _now_iso() -> str:
    """Return UTC timestamp in ISO-8601 format."""
    return datetime.datetime.now(datetime.timezone.utc).replace(
        microsecond=0).isoformat()


def _build_block_message(blocked_path: str, reason_code: str) -> str:
    """Build the actionable DENY message for emit_deny."""
    reason_text = {
        "no-results": "no codex-implement result found",
        "no-results-dir": "work/codex-implementations/ does not exist",
        "stale": "all codex-implement results older than 15 min",
        "fail-status": "most recent matching result has status != pass",
        "scope-miss": "no recent pass result covers this exact path",
        "parse-error": "could not parse codex-implement result",
        "bash-no-cover": "Bash command would mutate code without cover",
    }.get(reason_code, reason_code)
    msg = (
        "Code Delegation Protocol: " + blocked_path + " blocked ("
        + reason_text + ").\n\n"
        "To start the dual-implement track for this path, run:\n\n"
        "  py -3 .claude/scripts/codex-inline-dual.py \\n"
        "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
        "    --scope " + blocked_path + " \\n"
        "    --test \"py -3 -m pytest -q\"\n\n"
        "Then retry your edit. For multi-file tasks, use:\n"
        "  py -3 .claude/scripts/dual-teams-spawn.py --tasks <task.md> ...\n"
    )
    return msg


def emit_deny(blocked: str, reason_code: str, project_dir: Path,
              tool_name: str = "Edit") -> None:
    """Print the PreToolUse deny JSON to stdout and append ledger entry."""
    logger = logging.getLogger(HOOK_NAME)
    message = _build_block_message(blocked, reason_code)
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }
    logger.warning("emit_deny target=%s reason=%s", blocked, reason_code)
    _append_skip_ledger(project_dir, {
        "ts": _now_iso(),
        "tool": tool_name,
        "path": blocked,
        "decision": "deny",
        "reason": reason_code,
    })
    print(json.dumps(payload, ensure_ascii=False))


# ----------------------------------------------------------------------
# Tool dispatch
# ----------------------------------------------------------------------

def extract_targets(payload: dict) -> list:
    """Collect every file path this Edit/Write/MultiEdit/NotebookEdit call edits."""
    if not isinstance(payload, dict):
        return []
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return []
    paths: list = []
    if tool_name in {"Edit", "Write", "NotebookEdit"}:
        p = tool_input.get("file_path") or tool_input.get("notebook_path")
        if isinstance(p, str) and p:
            paths.append(p)
    elif tool_name == "MultiEdit":
        top_path = tool_input.get("file_path")
        if isinstance(top_path, str) and top_path:
            paths.append(top_path)
        edits = tool_input.get("edits")
        if isinstance(edits, list):
            for edit in edits:
                if not isinstance(edit, dict):
                    continue
                ep = edit.get("file_path")
                if isinstance(ep, str) and ep:
                    paths.append(ep)
    seen: set = set()
    unique: list = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def decide(payload: dict, project_dir: Path) -> bool:
    """Core gate. True to allow; False after emitting deny."""
    logger = logging.getLogger(HOOK_NAME)
    event = payload.get("hook_event_name", "") if isinstance(payload, dict) else ""
    tool_name = payload.get("tool_name", "") if isinstance(payload, dict) else ""
    logger.info("decide.enter event=%s tool=%s", event, tool_name)
    if event and event != "PreToolUse":
        logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
        return True
    if tool_name not in {"Edit", "Write", "MultiEdit", "Bash", "NotebookEdit"}:
        logger.info("decide.passthrough reason=unknown-tool tool=%s", tool_name)
        return True
    if is_dual_teams_worktree(project_dir):
        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
        return True

    if tool_name == "Bash":
        return _decide_bash(payload, project_dir)
    return _decide_edit(payload, project_dir, tool_name)


def _decide_edit(payload: dict, project_dir: Path, tool_name: str) -> bool:
    """Edit/Write/MultiEdit/NotebookEdit branch."""
    logger = logging.getLogger(HOOK_NAME)
    raw_targets = extract_targets(payload)
    if not raw_targets:
        logger.info("decide.passthrough reason=no-targets tool=%s", tool_name)
        return True
    for raw in raw_targets:
        abs_path = resolve_target(project_dir, raw)
        if abs_path is None:
            logger.info("decide.skip reason=unresolvable raw=%r", raw)
            continue
        rel = rel_posix(project_dir, abs_path)
        if rel is None:
            logger.info("decide.skip reason=outside-project path=%s", abs_path)
            continue
        if not requires_cover(rel):
            logger.info("decide.allow-target rel=%s reason=non-code-or-exempt", rel)
            _append_skip_ledger(project_dir, {
                "ts": _now_iso(), "tool": tool_name, "path": rel,
                "decision": "allow", "reason": "non-code-or-exempt",
            })
            continue
        if is_dual_teams_worktree(abs_path):
            logger.info("decide.allow-target rel=%s reason=dual-teams-target abs=%s",
                        rel, abs_path)
            _append_skip_ledger(project_dir, {
                "ts": _now_iso(), "tool": tool_name, "path": rel,
                "decision": "allow", "reason": "dual-teams-target",
            })
            continue
        covered, reason = find_cover(project_dir, rel)
        if not covered:
            emit_deny(rel, reason, project_dir, tool_name=tool_name)
            logger.info("decide.exit target=%s allowed=False reason=%s", rel, reason)
            return False
        logger.info("decide.allow-target rel=%s reason=covered", rel)
        _append_skip_ledger(project_dir, {
            "ts": _now_iso(), "tool": tool_name, "path": rel,
            "decision": "allow", "reason": reason,
        })
    logger.info("decide.exit allowed=True")
    return True


def _decide_bash(payload: dict, project_dir: Path) -> bool:
    """Bash branch (I2). Parse command, classify, check cover for each target."""
    logger = logging.getLogger(HOOK_NAME)
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        logger.info("decide_bash.no-input")
        return True
    command = tool_input.get("command", "")
    if not isinstance(command, str) or not command.strip():
        logger.info("decide_bash.empty-command")
        return True
    parsed = parse_bash_command(command)
    if parsed["decision"] == "allow":
        logger.info("decide_bash.allow reason=%s", parsed["reason"])
        _append_skip_ledger(project_dir, {
            "ts": _now_iso(), "tool": "Bash", "cmd": command[:200],
            "decision": "allow", "reason": parsed["reason"],
        })
        return True
    targets = parsed["targets"]
    if not targets:
        logger.info("decide_bash.require_cover-no-targets reason=%s", parsed["reason"])
        emit_deny("<bash-command>", "bash-no-cover", project_dir, tool_name="Bash")
        return False
    for target in targets:
        if target.startswith("<") and target.endswith(">"):
            emit_deny(target, "bash-no-cover", project_dir, tool_name="Bash")
            logger.info("decide_bash.exit allowed=False reason=opaque-target target=%s", target)
            return False
        norm = _normalize_path_token(target)
        abs_path = resolve_target(project_dir, norm)
        if abs_path is not None:
            rel = rel_posix(project_dir, abs_path) or norm
        else:
            rel = norm
        if abs_path is not None and is_dual_teams_worktree(abs_path):
            logger.info("decide_bash.allow-target rel=%s reason=dual-teams-target", rel)
            _append_skip_ledger(project_dir, {
                "ts": _now_iso(), "tool": "Bash", "path": rel,
                "decision": "allow", "reason": "dual-teams-target",
            })
            continue
        covered, reason = find_cover(project_dir, rel)
        if not covered:
            emit_deny(rel, reason, project_dir, tool_name="Bash")
            logger.info("decide_bash.exit target=%s allowed=False reason=%s", rel, reason)
            return False
        _append_skip_ledger(project_dir, {
            "ts": _now_iso(), "tool": "Bash", "path": rel,
            "decision": "allow", "reason": reason,
        })
    logger.info("decide_bash.exit allowed=True")
    return True


def main() -> int:
    """Read JSON payload from stdin, run decide(), exit 0 always."""
    project_dir = get_project_dir()
    logger = _build_logger(project_dir)
    logger.info("main.enter pid=%d", os.getpid())
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            logger.info("main.empty-stdin passthrough")
            return 0
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.info("main.malformed-json exc=%s", exc)
            return 0
        if not isinstance(payload, dict):
            logger.info("main.non-dict-payload type=%s", type(payload).__name__)
            return 0
        decide(payload, project_dir)
    except Exception as exc:
        logger.exception("main.unexpected exc=%s", exc)
    finally:
        logger.info("main.exit")
    return 0


if __name__ == "__main__":
    sys.exit(main())

 succeeded in 281ms:
codex
One important mismatch is already visible: the current enforcer exits `0` and writes deny decisions as JSON to stdout, while this task asks the live tests to require exit `2` plus stderr text. I’ll keep the new harness aligned to the immutable task spec and report any failures as discovered contract gaps, without touching the enforcer.
2026-04-26T09:00:23.249798Z ERROR codex_core::tools::router: error=`"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-ChildItem work/codex-implementations -Force -ErrorAction SilentlyContinue | Select-Object Name,Length,LastWriteTime | Format-Table -AutoSize'` rejected: blocked by policy
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-ChildItem work/codex-implementations -Force -ErrorAction SilentlyContinue | Select-Object Name,Length,LastWriteTime | Format-Table -AutoSize' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
 declined in 0ms:
`"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-ChildItem work/codex-implementations -Force -ErrorAction SilentlyContinue | Select-Object Name,Length,LastWriteTime | Format-Table -AutoSize'` rejected: blocked by policy
2026-04-26T09:00:23.276076Z ERROR codex_core::tools::router: error=`"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-ChildItem work/codex-primary/tasks -Force -ErrorAction SilentlyContinue | Select-Object Name,Length,LastWriteTime | Format-Table -AutoSize'` rejected: blocked by policy
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-ChildItem work/codex-primary/tasks -Force -ErrorAction SilentlyContinue | Select-Object Name,Length,LastWriteTime | Format-Table -AutoSize' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
 declined in 0ms:
`"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-ChildItem work/codex-primary/tasks -Force -ErrorAction SilentlyContinue | Select-Object Name,Length,LastWriteTime | Format-Table -AutoSize'` rejected: blocked by policy
2026-04-26T09:00:23.288061Z ERROR codex_core::tools::router: error=`"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Test-Path .claude/hooks/test_enforcer_live_attacks.py; if (Test-Path .claude/hooks/test_enforcer_live_attacks.py) { Get-Content .claude/hooks/test_enforcer_live_attacks.py -TotalCount 80 }'` rejected: blocked by policy
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Test-Path .claude/hooks/test_enforcer_live_attacks.py; if (Test-Path .claude/hooks/test_enforcer_live_attacks.py) { Get-Content .claude/hooks/test_enforcer_live_attacks.py -TotalCount 80 }' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
 declined in 0ms:
`"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Test-Path .claude/hooks/test_enforcer_live_attacks.py; if (Test-Path .claude/hooks/test_enforcer_live_attacks.py) { Get-Content .claude/hooks/test_enforcer_live_attacks.py -TotalCount 80 }'` rejected: blocked by policy
codex
The live hook also has an early dual-worktree bypass when `CLAUDE_PROJECT_DIR` contains `.dual-base-ref`; this checkout has that sentinel. I’m still building the tests against the requested contract, and I’ll call out the sentinel interaction separately in the report because it affects live deny expectations in this worktree.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg --files work/codex-implementations' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg --files work/codex-primary/tasks' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg --files .claude/hooks | rg "test_enforcer_live_attacks"' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
 succeeded in 136ms:
work/codex-primary/tasks\task-wave-b.md
work/codex-primary/tasks\task-wave-a.md
work/codex-primary/tasks\task-PoC.md
work/codex-primary/tasks\task-dual-2.md
work/codex-primary/tasks\task-dual-1.md
work/codex-primary/tasks\T8-claude-md-update.md
work/codex-primary/tasks\T7-adr.md
work/codex-primary/tasks\T6-dual-implement-skill.md
work/codex-primary/tasks\T5-codex-gate-update.md
work/codex-primary/tasks\T4-task-template.md
work/codex-primary/tasks\T3-phase-modes.md
work/codex-primary/tasks\T2-codex-wave.md
work/codex-primary/tasks\T1-codex-implement.md

 succeeded in 139ms:
work/codex-implementations\task-PoC-result.md
work/codex-implementations\task-V4-verdict-summarizer-result.md
work/codex-implementations\task-FIX-SELFTEST-result.md
work/codex-implementations\task-FIX-ENFORCER-result.md
work/codex-implementations\task-V2-task-spec-validator-result.md
work/codex-implementations\task-V1-knowledge-decay-report-result.md
work/codex-implementations\task-V3-worktree-cleaner-result.md
work/codex-implementations\task-wave-b.diff
work/codex-implementations\task-wave-a.diff
work/codex-implementations\task-PoC.diff
work/codex-implementations\task-wave-a-result.md
work/codex-implementations\task-Y16-update-spawn-agent-result.md
work/codex-implementations\task-Y15-update-prompt-template-result.md
work/codex-implementations\task-wave-b-result.md
work/codex-implementations\task-Y8-gate-sentinel-result.md
work/codex-implementations\task-Y8-gate-sentinel.diff
work/codex-implementations\task-Y9-spawn-resultdir-result.md
work/codex-implementations\task-Y9-spawn-resultdir.diff
work/codex-implementations\task-Z4-sync-script-recheck-result.md
work/codex-implementations\inline\Z4-sync-script-recheck-claude-prompt.md
work/codex-implementations\inline\Z3-sync-script-recheck-claude-prompt.md
work/codex-implementations\inline\Z2-sync-script-recheck-claude-prompt.md
work/codex-implementations\inline\task-Z4-sync-script-recheck.md
work/codex-implementations\inline\task-Z3-sync-script-recheck.md
work/codex-implementations\inline\task-Z2-sync-script-recheck.md
work/codex-implementations\inline\task-Y9-spawn-resultdir.md
work/codex-implementations\inline\task-Y8-gate-sentinel.md
work/codex-implementations\inline\task-Y16-update-spawn-agent.md
work/codex-implementations\inline\task-Y15-update-prompt-template.md
work/codex-implementations\inline\task-Y11-LIVE-pytool-version.md
work/codex-implementations\inline\task-FIX-SELFTEST.md
work/codex-implementations\inline\task-FIX-ENFORCER.md
work/codex-implementations\inline\task-E2E-2-dual-history-archive.md
work/codex-implementations\inline\task-E2E-1-codex-cost-report.md

2026-04-26T09:00:33.359578Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 0.2 seconds
Output:

 exited 1 in 172ms:
codex
I’m going to add the single allowed file now. The harness will include named tests for all 12 deny vectors and 6 positive controls, a fake `codex.cmd`/`codex` shim on `PATH`, and cleanup for temporary cover artifacts.
2026-04-26T09:02:08.781538Z ERROR codex_core::tools::router: error=patch rejected: writing is blocked by read-only sandbox; rejected by user approval settings
codex
The patch was rejected by the environment: filesystem writes are blocked by the read-only sandbox and approval is disabled, so I cannot create the required test file in this run. I’ll capture the current repository state and report this as a blocker rather than pretending the harness was added.
2026-04-26T09:02:23.532269Z ERROR codex_core::tools::router: error=`"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git rev-parse HEAD'` rejected: blocked by policy
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git rev-parse HEAD' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
 declined in 0ms:
`"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git rev-parse HEAD'` rejected: blocked by policy
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg --files .claude/hooks | rg "test_enforcer_live_attacks"' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
 succeeded in 129ms:
2026-04-26T09:02:23.699124Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 0.2 seconds
Output:

 exited 1 in 155ms:
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git log -1 --format=%H' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
2026-04-26T09:02:31.281858Z ERROR codex_core::tools::router: error=`"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/hooks/test_enforcer_live_attacks.py -v --tb=short'` rejected: blocked by policy
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/hooks/test_enforcer_live_attacks.py -v --tb=short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix
 declined in 0ms:
`"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/hooks/test_enforcer_live_attacks.py -v --tb=short'` rejected: blocked by policy
 succeeded in 120ms:
cf871cf03469aceebf5e06e5457ec1e19c4a7a07

codex
=== TASK Z5 SELF-REPORT ===
- status: blocker
- new tests added: 0 (expected 18)
- files modified: []
- existing tests still passing: not run
- selftest 6/6: not run
- enforcer-stdin-schema: JSON dict with `hook_event_name`, `tool_name`, `tool_input`, optional `session_id`
- Final commit SHA: `cf871cf03469aceebf5e06e5457ec1e19c4a7a07`

NOTE: I inspected the enforcer and reference tests, and prepared the new live matrix file, but `apply_patch` was rejected because this session is in read-only sandbox mode with approval disabled.
NOTE: Static inspection found a likely contract mismatch: the current enforcer returns exit `0` and emits deny JSON to stdout, while this task asks tests to expect exit `2` plus stderr.
NOTE: This worktree also contains `.dual-base-ref`, so tests using `CLAUDE_PROJECT_DIR=REPO_ROOT` may hit the current dual-worktree allow bypass before vector-specific denial logic.
BLOCKER: Cannot create `.claude/hooks/test_enforcer_live_attacks.py` or run the required new test command because filesystem writes and the pytest command were blocked by policy in this environment.
=== END SELF-REPORT ===
2026-04-26T09:02:50.871372Z ERROR codex_core::session: failed to record rollout items: thread 019dc903-16c3-7e82-89f7-90ea8ce9d53f not found
tokens used
60 183
```
