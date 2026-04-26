---
task_id: Z14-fix-v13-v14-v15
title: Close V13 (scheduler verbs) + V14 (MCP write tools) + V15 (unknown-verb argv scan) — Functional Coverage 10/10
executor: dual
risk_class: high-stakes
speed_profile: balanced
---

# Task Z14 — Close 3 enforcer gaps revealed by Z13

## Goal

Z13 expanded live attack matrix to 25 tests; 22 pass, 3 fail. Each
failure reveals a real bypass vector. Z14 closes all 3 to bring matrix
to 25/25 PASS — the empirical exit criterion for Functional Coverage 10/10.

Per Z13-findings.md the three gaps are:

**V13 — Scheduler verb pass-through (HIGH severity)**
`schtasks /Create /TR "py -3 work/sync.py"` is parsed as an unknown verb;
its `/TR` payload is treated as an opaque string. Background-persistence
+ invisible code mutation. Same applies to `at`, `crontab`,
`Register-ScheduledTask`, `cron`.

**V14 — MCP write tools (HIGH severity, clean bypass)**
Tool names like `mcp__filesystem__write_file`, `mcp__github__create_file`,
etc. are not in the PreToolUse matcher pattern (only `Edit|Write|MultiEdit|Bash|NotebookEdit`).
Any MCP server providing write capability bypasses the enforcer entirely.

**V15 — Unknown-verb argv scan (MEDIUM severity)**
`./my-tool --output src/foo.py` — when the verb is unknown (compiled
binary, custom script), the parser only inspects positional argv for
known mutating/inplace branches. Code-extension paths in the argv are
not flagged. Easy tightening.

## The three fixes

### Fix V13 — Scheduler verbs re-tokenize their payload

In `.claude/hooks/codex-delegate-enforcer.py`, add a new verb class
`_SCHEDULER_VERBS = {"schtasks", "at", "crontab", "Register-ScheduledTask"}`
(case-insensitive on Windows, case-sensitive on Linux for `at`/`crontab`).

When the first token matches a scheduler verb, locate the embedded command
payload:
- `schtasks /Create /TR "<command>"` — extract value of `/TR`
- `crontab` reads stdin OR loads file — flag as opaque (always require cover)
- `at <time>` reads stdin — flag as opaque (always require cover)
- `Register-ScheduledTask -Action ... -Argument "<command>"` — extract `-Argument`

Re-run `parse_bash_command(extracted)` recursively against the payload.
If recursive result is `decision: deny` OR `decision: cover-required`,
propagate that decision up. Default for opaque-payload schedulers: deny
with reason `scheduler-opaque-payload`.

### Fix V14 — MCP write tools matcher + dispatch

Two coordinated changes:

1. **`.claude/settings.json`** — change `"matcher": "Edit|Write|MultiEdit|Bash|NotebookEdit"`
   → `"matcher": "Edit|Write|MultiEdit|Bash|NotebookEdit|mcp__.*"`

2. **`.claude/hooks/codex-delegate-enforcer.py`** — in `decide()` dispatch,
   add branch for tool names matching `^mcp__.*` (regex):
   - If tool name matches `^mcp__.*?(write|edit|create|patch|put|append|delete|remove|update).*$`
     → treat `tool_input.path` (or `tool_input.file_path`) as the target
   - If the target has a code extension AND is not under exempt paths →
     require cover, deny if missing
   - Otherwise allow (read-only MCP tools)

The existing `_decide_edit` machinery handles the cover lookup once we
have the target path.

### Fix V15 — Unknown-verb argv code-extension scan

In `.claude/hooks/codex-delegate-enforcer.py` `_decide_bash`, after all
known verb classes (read-only / test-runner / package-manager / git-read /
git-mutate / pwsh / inplace / mutating / interpreter / scheduler) are
exhausted and the verb is unknown:

```python
# Unknown verb fallback — scan argv for code-extension paths
code_targets = [
    arg for arg in remaining_argv
    if _is_code_path_token(arg)
]
if code_targets:
    return {"decision": "deny",
            "reason": "unknown-verb-with-code-path-argv",
            "targets": code_targets}
# Otherwise: allow (unknown verb, no obvious code paths)
return {"decision": "allow", "reason": "unknown-verb-no-code-paths", ...}
```

Where `_is_code_path_token(token)` checks: token is path-like
(contains `/`, `\`, or `.`) AND has a `CODE_EXTENSIONS` extension AND
is NOT `--flag=path/to/value` for a known --flag (best-effort —
strip leading `--name=` if present).

## Scope Fence — files you MAY modify

```
.claude/hooks/codex-delegate-enforcer.py
.claude/settings.json
```

DO NOT modify any other file. Specifically NOT
`.claude/hooks/test_enforcer_live_attacks.py` (it contains the IMMUTABLE
acceptance tests for V13-V18).

## Read-Only Files / Evaluation Firewall

- `work/criterion-upgrade/task-Z14-fix-v13-v14-v15.md` (this file)
- `.claude/hooks/test_enforcer_live_attacks.py` (the 25 ACs)
- `work/criterion-upgrade/Z13-findings.md` (root-cause analysis)

## Acceptance Criteria

### AC-1: All 25 live attack matrix tests pass
```bash
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -v --tb=line
```
Must show **25 passed, 0 failed**.

### AC-2: Existing 268-tests-minus-19 suite still passes (no regression)
```bash
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line
```

### AC-3: Selftest still passes
`python .claude/scripts/dual-teams-selftest.py` → 6/6 PASS

### AC-4: settings.json json-valid
```bash
python -c "import json; json.load(open('.claude/settings.json'))"
```

### AC-5: Matcher includes mcp__.*
```bash
python -c "import json; s=json.load(open('.claude/settings.json')); m=s['hooks']['PreToolUse'][0]['matcher']; assert 'mcp__' in m, f'mcp__ not in matcher: {m}'; print('OK matcher includes mcp__:', m)"
```

## Test Commands

ALL must succeed:

```bash
# 1. Live attack matrix — must be 25/25 PASS
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -v --tb=line

# 2. Regression
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line

# 3. Selftest
python .claude/scripts/dual-teams-selftest.py

# 4. JSON validity
python -c "import json; json.load(open('.claude/settings.json'))"

# 5. Matcher sanity
python -c "import json; s=json.load(open('.claude/settings.json')); m=s['hooks']['PreToolUse'][0]['matcher']; assert 'mcp__' in m"
```

## Implementation hints

- For V13 scheduler payload extraction: `shlex.split` then look for `/TR` index, take next token. For `Register-ScheduledTask` look for `-Argument` (case-insensitive). For `crontab`/`at` — opaque, deny outright.
- For V14 MCP: regex `re.match(r"^mcp__(?P<server>\w+)__(?P<action>\w+)$", tool_name)`. Action keywords for write: `["write", "edit", "create", "patch", "put", "append", "delete", "remove", "update"]`. Read-only actions allow.
- For V15: existing parser already has `parse_bash_command` returning `{decision, reason, targets}`. Add the unknown-verb fallback at the very end after all known classifiers have been tried.
- For settings.json: `mcp__.*` is regex syntax — verify Claude Code matcher accepts dot/star syntax. If not, list common ones: `mcp__filesystem.*|mcp__github.*|mcp__.*` etc. Or use `.*` or omit prefix entirely.
- Logging: each new branch (`scheduler-opaque-payload`, `mcp-write-tool-detected`, `unknown-verb-with-code-path-argv`) gets a `logger.info` entry/exit so future debugging is easy.

## Self-report format

```
=== TASK Z14 SELF-REPORT ===
- status: pass | fail | blocker
- live attack matrix: <X>/25 PASS
- V13 fix approach: <1 line>
- V14 fix approach: <1 line>
- V15 fix approach: <1 line>
- existing 249 tests still pass (other suites): yes / no
- selftest: PASS / FAIL
- settings.json matcher includes mcp__: yes / no
- net lines: <approx>
- files modified: [list]
- NOTE: <surprising>
- BLOCKER: <only if>
- Final commit SHA: <SHA>
=== END SELF-REPORT ===
```
