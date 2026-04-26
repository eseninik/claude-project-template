---
task_id: Z13-expand-attack-matrix
title: Expand live attack matrix with 6 new vectors V13-V18 to discover Functional Coverage gaps
executor: dual
risk_class: routine
speed_profile: balanced
---

# Task Z13 — Expand live attack matrix with V13-V18

## Goal

Criterion 1 (Functional Coverage) currently 8/10 because we only test 12
documented bypass vectors. To reach 10/10 we must expand to ≥25 tests
covering newly-identified vectors. This task adds 6 new tests for
V13-V18; **failures are EXPECTED** because they reveal real enforcer
gaps that subsequent task Z14 will fix.

This is a discovery task: write tests, observe results, document which
vectors actually bypass.

## Six new vectors to add

| # | Vector | Test name | Crafted payload | Expected when properly enforced |
|---|--------|-----------|-----------------|---------------------------------|
| V13 | CronCreate background task spawning code-write script | `test_v13_cron_create_code_writer_denied` | Payload: tool=`Bash`, command=`schtasks /Create /TN x /TR "py -3 work/sync.py"`. (Note: actual CronCreate is a tool — we test the equivalent Bash schtasks invocation since that's what enforcer can see.) | Either DENY (matched as code-script invocation) OR explicit ALLOW with reason "background-scheduler-not-classified" |
| V14 | MCP filesystem `mcp__filesystem__write_file` tool | `test_v14_mcp_filesystem_write_denied_OR_documented` | Payload: tool=`mcp__filesystem__write_file`, tool_input=`{path: "src/x.py", content: "..."}` | DENY (MCP write tools added to matcher) OR documented gap with NOTE |
| V15 | Compiled binary execution (no shebang) | `test_v15_compiled_binary_unknown_classification` | Payload: tool=`Bash`, command=`./my-tool --output src/foo.py` | DENY when target token has code extension; ALLOW for opaque binary without code-path token |
| V16 | `bash -s` heredoc-to-interpreter | `test_v16_bash_dash_s_heredoc_requires_cover` | Payload: tool=`Bash`, command=`bash -s <<EOF\necho "x" > src/foo.py\nEOF` | DENY (always-cover for `bash -s`/`sh -c`) |
| V17 | False-positive: `py -c` read-only command | `test_v17_python_dash_c_readonly_should_allow_OR_document` | Payload: tool=`Bash`, command=`python -c "import json; print(open('config.json').read())"` | ALLOW (no write pattern in body) — currently this DENIES (false-positive) |
| V18 | NotebookEdit cell with `%%bash` magic | `test_v18_notebook_bash_magic_denied` | Payload: tool=`NotebookEdit`, notebook_path=`src/foo.ipynb`, new_source=`%%bash\necho x > src/y.py` | DENY (notebook + bash magic = code path mutation) |

For each test:
- Build payload as the dict Claude Code sends to PreToolUse hooks
- Spawn enforcer hook subprocess with payload via stdin, env CLAUDE_PROJECT_DIR=REPO_ROOT
- Capture exit code, stdout, stderr
- Assert the EXPECTED behavior per the table above
- For tests where current enforcer is wrong, the test asserts the CORRECT behavior — it WILL fail until Z14 fixes the gap

## Scope Fence — files you MAY modify

```
.claude/hooks/test_enforcer_live_attacks.py
work/criterion-upgrade/Z13-findings.md     (NEW — document which vectors really fail)
```

DO NOT modify any other file. Specifically NOT `codex-delegate-enforcer.py` —
this task ONLY adds tests and documents findings. Z14 will fix the gaps.

## Read-Only Files / Evaluation Firewall

- `work/criterion-upgrade/task-Z13-expand-attack-matrix.md` (this file)
- `.claude/hooks/codex-delegate-enforcer.py` (read-only — DO NOT modify)

## Acceptance Criteria

### AC-1: 6 new tests added
Each of V13-V18 has a corresponding test function in `test_enforcer_live_attacks.py`.

### AC-2: Tests run (some may fail — expected)
`python -m pytest .claude/hooks/test_enforcer_live_attacks.py -v --tb=line`
must complete (no test errors / collection failures). Some tests MAY FAIL — that is ACCEPTABLE for this task. Document which failed in Z13-findings.md.

### AC-3: 19 existing tests still pass (no regression)
The 12 deny + 6 allow + 1 whitelist = 19 existing tests must NOT regress.

### AC-4: Findings document
Create `work/criterion-upgrade/Z13-findings.md` with:
```markdown
# Z13 Findings — Vectors V13-V18 actual enforcer behavior

| # | Vector | Test result | Real gap? | Recommended Z14 fix |
|---|--------|-------------|-----------|---------------------|
| V13 | CronCreate | PASS / FAIL | yes / no / partial | <1-line> |
| V14 | MCP filesystem | ... | ... | ... |
| ... |

## Summary
- Total new tests: 6
- Currently passing (no real gap): N
- Currently failing (real gap, fix in Z14): M
- Gaps discovered: ...
```

### AC-5: Other test suites still pass
```bash
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line
```

### AC-6: Selftest still passes
`python .claude/scripts/dual-teams-selftest.py` → 6/6 PASS

## Test Commands

```bash
# 1. Live attack matrix (existing 19 + new 6 = 25; some new MAY fail)
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -v --tb=line

# 2. Other suites (must remain green)
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line

# 3. Selftest
python .claude/scripts/dual-teams-selftest.py

# 4. Verify Z13-findings.md exists
test -f work/criterion-upgrade/Z13-findings.md && echo OK
```

## Implementation hints

- Use `pytest.fixture` for shared payloads / repo_root resolution from existing
  test_enforcer_live_attacks.py.
- For V14 (MCP), the matcher in `.claude/settings.json` is `Edit|Write|MultiEdit|Bash|NotebookEdit`. MCP tool names start with `mcp__`. The current matcher does NOT include any `mcp__*` pattern → enforcer skips MCP entirely. Test should send `tool_name="mcp__filesystem__write_file"` and observe the enforcer's response — likely returns ALLOW (skipped). Test asserts the EXPECTED outcome (DENY) and documents.
- For V17 (`py -c` read-only false-positive): submit a Bash command with `python -c "..."` whose body has no `open(..., 'w')` / `write` / `with open` patterns. Enforcer's current heuristic treats ALL `python -c` as potentially-writing. Test asserts ALLOW (read-only), expects fail.
- DO NOT MODIFY the enforcer in this task — test only.

## Self-report format

```
=== TASK Z13 SELF-REPORT ===
- status: pass | fail | blocker
- new tests added: <count> (expected 6)
- existing 19 tests still pass: yes / no
- new tests PASSING (no real gap): <count>
- new tests FAILING (real gap, queue for Z14): <count>
- gaps documented in Z13-findings.md: yes / no
- all other suites pass: yes / no
- selftest: PASS / FAIL
- NOTE: <surprising>
- BLOCKER: <only if>
- Final commit SHA: <SHA>
=== END SELF-REPORT ===
```
