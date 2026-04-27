# Codex Implementation Result — Task Z13-expand-attack-matrix

- status: scope-violation
- timestamp: 2026-04-26T14:46:38.364945+00:00
- task_file: C:\Bots\Migrator bots\claude-project-template-update\work\criterion-upgrade\task-Z13-expand-attack-matrix.md
- base_sha: 3cd7fa5afafc00f58f3bbcd565d1c8cb0e1f0583
- codex_returncode: 0
- scope_status: fail
- scope_message: 2026-04-26 17:50:55,405 INFO codex_scope_check main_started diff=C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations\task-Z13-expand-attack-matrix.diff fence= root=.
2026-04-26 17:50:55,405 INFO codex_scope_check read_diff_started source=C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations\task-Z13-expand-attack-matrix.diff
2026-04-26 17:50:55,417 INFO codex_scope_check read_diff_completed bytes=6392
2026-04-26 17:50:55,418 INFO codex_scope_check parse_diff_paths_started diff_bytes=6392
2026-04-26 17:50:55,418 INFO codex_scope_check parse_diff_paths_completed count=2
2026-04-26 17:50:55,418 INFO codex_scope_check parse_fence_started fence_spec='' root=C:\Bots\Migrator bots\claude-project-template-update
2026-04-26 17:50:55,418 INFO codex_scope_check parse_fence_completed allowed=0 forbidden=0
2026-04-26 17:50:55,418 INFO codex_scope_check check_paths_started allowed=0 forbidden=0
2026-04-26 17:50:55,419 WARNING codex_scope_check check_paths_no_allowed path=.claude/hooks/test_enforcer_live_attacks.py
2026-04-26 17:50:55,420 WARNING codex_scope_check check_paths_no_allowed path=work/criterion-upgrade/Z13-findings.md
2026-04-26 17:50:55,420 INFO codex_scope_check check_paths_completed violations=2
2026-04-26 17:50:55,420 ERROR codex_scope_check main_completed status=violation count=2
- scope_violations:
  - VIOLATION: 2 path(s) outside fence
  - .claude/hooks/test_enforcer_live_attacks.py	no allowed fence entries configured
  - work/criterion-upgrade/Z13-findings.md	no allowed fence entries configured
  - 2026-04-26 17:50:55,405 INFO codex_scope_check main_started diff=C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations\task-Z13-expand-attack-matrix.diff fence= root=.
  - 2026-04-26 17:50:55,405 INFO codex_scope_check read_diff_started source=C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations\task-Z13-expand-attack-matrix.diff
  - 2026-04-26 17:50:55,417 INFO codex_scope_check read_diff_completed bytes=6392
  - 2026-04-26 17:50:55,418 INFO codex_scope_check parse_diff_paths_started diff_bytes=6392
  - 2026-04-26 17:50:55,418 INFO codex_scope_check parse_diff_paths_completed count=2
  - 2026-04-26 17:50:55,418 INFO codex_scope_check parse_fence_started fence_spec='' root=C:\Bots\Migrator bots\claude-project-template-update
  - 2026-04-26 17:50:55,418 INFO codex_scope_check parse_fence_completed allowed=0 forbidden=0
  - 2026-04-26 17:50:55,418 INFO codex_scope_check check_paths_started allowed=0 forbidden=0
  - 2026-04-26 17:50:55,419 WARNING codex_scope_check check_paths_no_allowed path=.claude/hooks/test_enforcer_live_attacks.py
  - 2026-04-26 17:50:55,420 WARNING codex_scope_check check_paths_no_allowed path=work/criterion-upgrade/Z13-findings.md
  - 2026-04-26 17:50:55,420 INFO codex_scope_check check_paths_completed violations=2
  - 2026-04-26 17:50:55,420 ERROR codex_scope_check main_completed status=violation count=2

## Diff

```diff
diff --git a/.claude/hooks/test_enforcer_live_attacks.py b/.claude/hooks/test_enforcer_live_attacks.py
index 33edb22..c7746a8 100644
--- a/.claude/hooks/test_enforcer_live_attacks.py
+++ b/.claude/hooks/test_enforcer_live_attacks.py
@@ -114,6 +114,22 @@ def _assert_allow(result: subprocess.CompletedProcess) -> None:
     )
 
 
+def _latest_skip_ledger_entry(project_root: Path) -> dict:
+    """Return the last skip-ledger entry for assertions on allow reasons."""
+    ledger = project_root / "work" / "codex-implementations" / "skip-ledger.jsonl"
+    if not ledger.exists():
+        return {}
+    lines = [line.strip() for line in ledger.read_text(encoding="utf-8").splitlines()
+             if line.strip()]
+    if not lines:
+        return {}
+    try:
+        obj = json.loads(lines[-1])
+    except json.JSONDecodeError:
+        return {}
+    return obj if isinstance(obj, dict) else {}
+
+
 # ----------------------------------------------------------------------
 # Fixtures
 # ----------------------------------------------------------------------
@@ -414,3 +430,84 @@ def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
     cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
     r = _run_enforcer(_bash_payload(cmd), project_root)
     _assert_allow(r)
+
+
+# ======================================================================
+# DISCOVERY VECTORS (V13-V18) - Z13 expanded live attack matrix
+# ======================================================================
+
+def test_v13_cron_create_code_writer_denied(project_root: Path) -> None:
+    """V13 - schtasks/CronCreate-style background code writer must be covered.
+
+    A proper implementation may either DENY because the scheduled action
+    invokes a code-writing script, or explicitly ALLOW with a documented
+    background-scheduler-not-classified reason.
+    """
+    (project_root / "work" / "sync.py").write_text("# sync\n", encoding="utf-8")
+    cmd = 'schtasks /Create /TN x /TR "py -3 work/sync.py"'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    if _parse_deny(r.stdout) is not None:
+        return
+    entry = _latest_skip_ledger_entry(project_root)
+    assert entry.get("decision") == "allow", (
+        f"expected DENY or explicit ALLOW; returncode={r.returncode} "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+    assert entry.get("reason") == "background-scheduler-not-classified", (
+        "expected explicit scheduler gap reason; "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+
+
+def test_v14_mcp_filesystem_write_denied_OR_documented(project_root: Path) -> None:
+    """V14 - MCP filesystem write_file should be denied or treated as a gap."""
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "mcp__filesystem__write_file",
+        "tool_input": {"path": "src/x.py", "content": "print('x')\n"},
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r, must_contain_in_reason="src/x.py")
+
+
+def test_v15_compiled_binary_unknown_classification(project_root: Path) -> None:
+    """V15 - unknown binary mutating a code path must deny, opaque run allows."""
+    r = _run_enforcer(_bash_payload("./my-tool --output src/foo.py"), project_root)
+    _assert_deny(r, must_contain_in_reason="src/foo.py")
+
+    opaque = _run_enforcer(_bash_payload("./my-tool --version"), project_root)
+    _assert_allow(opaque)
+
+
+def test_v16_bash_dash_s_heredoc_requires_cover(project_root: Path) -> None:
+    """V16 - bash -s heredoc is opaque interpreter input and must DENY."""
+    cmd = 'bash -s <<EOF\necho "x" > src/foo.py\nEOF'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_deny(r)
+
+
+def test_v17_python_dash_c_readonly_should_allow_OR_document(
+    project_root: Path,
+) -> None:
+    """V17 - python -c with read-only open(...).read() should ALLOW."""
+    cmd = "python -c \"import json; print(open('config.json').read())\""
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+def test_v18_notebook_bash_magic_denied(project_root: Path) -> None:
+    """V18 - NotebookEdit containing %%bash code-path mutation must DENY."""
+    target = "src/foo.ipynb"
+    (project_root / target).write_text("{}\n", encoding="utf-8")
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "NotebookEdit",
+        "tool_input": {
+            "notebook_path": target,
+            "new_source": "%%bash\necho x > src/y.py",
+        },
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r)
diff --git a/work/criterion-upgrade/Z13-findings.md b/work/criterion-upgrade/Z13-findings.md
new file mode 100644
index 0000000..38b585b
--- /dev/null
+++ b/work/criterion-upgrade/Z13-findings.md
@@ -0,0 +1,17 @@
+# Z13 Findings — Vectors V13-V18 actual enforcer behavior
+
+| # | Vector | Test result | Real gap? | Recommended Z14 fix |
+|---|--------|-------------|-----------|---------------------|
+| V13 | CronCreate | FAIL | yes | Classify `schtasks /Create ... /TR` as scheduler input and recursively inspect the scheduled command, or emit explicit `background-scheduler-not-classified` allow reason. |
+| V14 | MCP filesystem | FAIL | yes | Add MCP write tools such as `mcp__filesystem__write_file` to hook dispatch and extract `path` as a code-write target. |
+| V15 | Compiled binary | FAIL | yes | For unknown executables, require cover when any argument token names a code-extension path, while allowing opaque runs without code-path tokens. |
+| V16 | `bash -s` heredoc | PASS | no | Keep always-cover handling for `bash -s`/stdin-opaque interpreter input. |
+| V17 | `py -c` read-only | PASS | no | Keep read/write-sensitive `python -c` parsing so read-only `open(...).read()` allows. |
+| V18 | Notebook `%%bash` magic | PASS | no | Current NotebookEdit denial covers the `.ipynb`; preserve denial for notebook cells that can mutate code paths. |
+
+## Summary
+
+- Total new tests: 6
+- Currently passing (no real gap): 3
+- Currently failing (real gap, fix in Z14): 3
+- Gaps discovered: V13 scheduler-created background code writers, V14 MCP filesystem writes, V15 unknown compiled binaries with code-path arguments
```

## Test Output

(no test commands executed)
## Self-Report (Codex NOTE/BLOCKER lines)

(no NOTE/BLOCKER lines)

## Codex stderr

```
OpenAI Codex v0.125.0 (research preview)
--------
workdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
model: gpt-5.5
provider: chatgpt
approval: never
sandbox: danger-full-access
reasoning effort: xhigh
reasoning summaries: none
session id: 019dca41-bab1-7751-ae52-6494f4e5c25d
--------
user
You are the single-task implementer. The task specification below is IMMUTABLE.
Write code to satisfy all Acceptance Criteria. Do NOT modify files listed in
Forbidden Paths or Read-Only Files. After writing code, run every Test Command
listed in the task and report the result in your self-report.
Any AGENTS.md or CLAUDE.md in the worktree is authoritative background context.

---- TASK SPECIFICATION ----

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


---- END TASK SPECIFICATION ----
Return a short self-report at the end of your run using lines starting with
`NOTE:` for observations and `BLOCKER:` for unresolved problems.

codex
I’ll read the existing live attack tests and enforcer behavior first, then add only the scoped tests and findings document. After that I’ll run the required commands and report the observed failures separately from regressions.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path .claude/hooks/codex-delegate-enforcer.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-ChildItem -Path work/criterion-upgrade -Force' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path .claude/hooks/test_enforcer_live_attacks.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
 succeeded in 193ms:


    Каталог: C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand
    -attack-matrix\work\criterion-upgrade


Mode                 LastWriteTime         Length Name                                                                 
----                 -------------         ------ ----                                                                 
-a----        26.04.2026     17:46           6135 PIPELINE.md                                                          
-a----        26.04.2026     17:46           7208 task-Z13-expand-attack-matrix.md                                     



 succeeded in 216ms:
#!/usr/bin/env python3
"""Z5 - Live attack matrix for codex-delegate-enforcer.py.

Subprocess-level live integration harness exercising all 12 documented
bypass vectors (must DENY) plus 6 positive controls (must ALLOW). Each
test crafts a PreToolUse JSON payload, pipes it via stdin into a fresh
``python codex-delegate-enforcer.py`` subprocess and asserts on the
binary contract Claude Code's harness uses:

  - DENY  -> stdout contains valid JSON with
             hookSpecificOutput.permissionDecision == "deny"
             AND the offending path / reason substring is present
             (in stdout reason or stderr log).
  - ALLOW -> stdout has no ``"permissionDecision": "deny"`` JSON.

Note on exit codes: the task spec mentions "exit code (2=deny, 0=allow)".
The current enforcer ALWAYS exits 0 and signals deny via JSON on stdout
(the actual PreToolUse contract). This file therefore checks the JSON
contract rather than the exit code. If the harness later switches to
exit-code semantics, the deny-side checks below must be tightened.

Each test uses an isolated ``tmp_path``-based project root with NO
``.dual-base-ref`` sentinel, so the enforcer fully engages (the
dual-teams shortcut would otherwise allow everything). For tests that
legitimately need a sentinel (A5), we create one in a dedicated tmp tree.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------

HERE = Path(__file__).resolve().parent
HOOK_PATH = HERE / "codex-delegate-enforcer.py"
SUBPROC_TIMEOUT_SECONDS = 10


# ----------------------------------------------------------------------
# Subprocess invocation helpers
# ----------------------------------------------------------------------

def _run_enforcer(payload: dict, project_root: Path) -> subprocess.CompletedProcess:
    """Spawn codex-delegate-enforcer.py with payload JSON on stdin.

    Uses a hermetic CLAUDE_PROJECT_DIR so the enforcer never sees the
    real repo's .dual-base-ref sentinel (which would short-circuit it).
    """
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project_root)}
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=SUBPROC_TIMEOUT_SECONDS,
    )


def _parse_deny(stdout: str) -> Optional[dict]:
    """Return the parsed deny payload if stdout contains one, else None."""
    s = stdout.strip()
    if not s:
        return None
    try:
        obj = json.loads(s)
    except json.JSONDecodeError:
        return None
    hs = obj.get("hookSpecificOutput") if isinstance(obj, dict) else None
    if not isinstance(hs, dict):
        return None
    if hs.get("permissionDecision") == "deny":
        return obj
    return None


def _assert_deny(result: subprocess.CompletedProcess,
                 must_contain_in_reason: str = "") -> None:
    """Assert the subprocess produced a PreToolUse deny JSON on stdout."""
    deny = _parse_deny(result.stdout)
    assert deny is not None, (
        "expected DENY JSON on stdout. "
        f"returncode={result.returncode} stdout={result.stdout!r} "
        f"stderr={result.stderr[-500:]!r}"
    )
    if must_contain_in_reason:
        reason = deny["hookSpecificOutput"].get("permissionDecisionReason", "")
        assert (must_contain_in_reason in reason
                or must_contain_in_reason in result.stderr), (
            f"expected substring {must_contain_in_reason!r} in deny reason "
            f"or stderr log; reason={reason!r} stderr={result.stderr[-500:]!r}"
        )


def _assert_allow(result: subprocess.CompletedProcess) -> None:
    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
    assert result.returncode == 0, (
        f"unexpected non-zero exit on allow: {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
    )
    deny = _parse_deny(result.stdout)
    assert deny is None, (
        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
    )


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------

@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Hermetic project root with the dirs the enforcer expects.

    Critically does NOT include a .dual-base-ref sentinel anywhere up
    the tree, so the dual-teams short-circuit does NOT engage.
    """
    root = tmp_path / "repo"
    (root / ".claude" / "hooks").mkdir(parents=True)
    (root / ".claude" / "scripts").mkdir(parents=True)
    (root / "work" / "codex-primary" / "tasks").mkdir(parents=True)
    (root / "work" / "codex-implementations").mkdir(parents=True)
    (root / "src").mkdir(parents=True)
    return root.resolve()


@pytest.fixture
def tmp_cover_artifact(project_root: Path):
    """Write a fresh task + result.md whose Scope Fence covers given paths.

    Yields a callable: ``write_cover(task_id, fence_paths, status='pass')``.
    Returns the result.md path. All artifacts auto-cleanup with tmp_path.
    """

    def write_cover(task_id: str, fence_paths: list, status: str = "pass") -> Path:
        task_file = project_root / "work" / "codex-primary" / "tasks" / (
            "T" + task_id + "-fake.md"
        )
        fence_block = "\n".join("- `" + p + "`" for p in fence_paths)
        task_file.write_text(
            "---\nexecutor: codex\n---\n\n# Task T" + task_id + "\n\n"
            "## Your Task\nfake\n\n"
            "## Scope Fence\n"
            "**Allowed paths (may be written):**\n"
            + fence_block + "\n\n"
            "**Forbidden paths:**\n- other/\n\n"
            "## Acceptance Criteria\n- [ ] AC1\n",
            encoding="utf-8",
        )
        result_file = project_root / "work" / "codex-implementations" / (
            "task-" + task_id + "-result.md"
        )
        task_file_rel = "work/codex-primary/tasks/T" + task_id + "-fake.md"
        result_file.write_text(
            "# Result T" + task_id + "\n\n"
            "- status: " + status + "\n"
            "- task_file: " + task_file_rel + "\n\n"
            "## Diff\n(none)\n",
            encoding="utf-8",
        )
        return result_file

    yield write_cover
    # tmp_path cleanup handles file removal


@pytest.fixture
def tmp_worktree(tmp_path: Path) -> Path:
    """A separate tmp directory that DOES contain .dual-base-ref.

    For test A5 - proves a sentinel-bearing worktree allows code edits.
    """
    wt = tmp_path / "wt"
    (wt / ".claude").mkdir(parents=True)
    (wt / ".dual-base-ref").write_text("main\n", encoding="utf-8")
    return wt.resolve()


# ----------------------------------------------------------------------
# Payload builders
# ----------------------------------------------------------------------

def _edit_payload(file_path: str) -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": file_path,
                       "old_string": "a", "new_string": "b"},
        "session_id": "z5-test",
    }


def _notebook_payload(notebook_path: str) -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "NotebookEdit",
        "tool_input": {"notebook_path": notebook_path,
                       "new_source": "print('x')"},
        "session_id": "z5-test",
    }


def _bash_payload(command: str) -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "session_id": "z5-test",
    }


# ======================================================================
# DENY VECTORS (V01-V12) - each must produce a deny JSON on stdout
# ======================================================================

def test_v01_work_py_denied(project_root: Path) -> None:
    """V1 - work/**/*.py exemption bypass (Invariant 1: extension wins)."""
    target = "work/sync-template-to-target.py"
    (project_root / "work" / "sync-template-to-target.py").write_text(
        "# placeholder\n", encoding="utf-8"
    )
    r = _run_enforcer(_edit_payload(target), project_root)
    _assert_deny(r, must_contain_in_reason=target)


def test_v02_notebook_edit_denied(project_root: Path) -> None:
    """V2 - NotebookEdit on a code-bearing notebook must DENY (Invariant 2).

    NOTE: .ipynb is NOT in CODE_EXTENSIONS, so this test reveals whether
    the enforcer's tool-dispatch covers NotebookEdit at all. If the
    current enforcer treats .ipynb as non-code, this DENY assertion
    will fail and reveal a real gap (Z7+).
    """
    target = "src/foo.ipynb"
    (project_root / "src" / "foo.ipynb").write_text("{}\n", encoding="utf-8")
    r = _run_enforcer(_notebook_payload(target), project_root)
    _assert_deny(r)


def test_v03_bash_heredoc_git_apply_denied(project_root: Path) -> None:
    """V3 - Bash heredoc + git apply (opaque patch) must DENY."""
    cmd = (
        "cat > /tmp/p.diff <<'EOF'\n"
        "--- a/src/x.py\n+++ b/src/x.py\n@@\n-x\n+y\n"
        "EOF\n"
        "git apply /tmp/p.diff"
    )
    r = _run_enforcer(_bash_payload(cmd), project_root)
    _assert_deny(r)


def test_v04_bash_sed_inplace_on_code_denied(project_root: Path) -> None:
    """V4 - sed -i on a .py file must DENY (Invariant 2)."""
    cmd = "sed -i 's/x/y/g' src/main.py"
    r = _run_enforcer(_bash_payload(cmd), project_root)
    _assert_deny(r, must_contain_in_reason="src/main.py")


def test_v05_bash_cp_code_to_code_denied(project_root: Path) -> None:
    """V5 - Bash cp src/a.py src/b.py must DENY (Invariant 2)."""
    cmd = "cp src/a.py src/b.py"
    r = _run_enforcer(_bash_payload(cmd), project_root)
    _assert_deny(r)


def test_v06_powershell_set_content_on_code_denied(project_root: Path) -> None:
    """V6 - powershell Set-Content -Path src/foo.py must DENY (Invariant 2)."""
    cmd = (
        'powershell -NoProfile -Command '
        '"Set-Content -Path src/foo.py -Value test"'
    )
    r = _run_enforcer(_bash_payload(cmd), project_root)
    _assert_deny(r, must_contain_in_reason="src/foo.py")


def test_v07_python_dash_c_open_write_denied(project_root: Path) -> None:
    """V7 - python -c with open(...,'w') must DENY (Invariant 2)."""
    cmd = "python -c \"open('src/x.py','w').write('')\""
    r = _run_enforcer(_bash_payload(cmd), project_root)
    _assert_deny(r)


def test_v08_edit_claude_scripts_py_denied(project_root: Path) -> None:
    """V8 - Edit on .claude/scripts/rogue.py must DENY (Invariant 1)."""
    target = ".claude/scripts/rogue.py"
    (project_root / target).write_text("# rogue\n", encoding="utf-8")
    r = _run_enforcer(_edit_payload(target), project_root)
    _assert_deny(r, must_contain_in_reason=target)


def test_v09_bash_invokes_mass_mutating_script_denied(project_root: Path) -> None:
    """V9 - Bash launching a script in work/ that mass-mutates must DENY.

    ``py -3 work/sync-template-to-target.py --apply`` should be intercepted
    because the python interpreter classifier treats invocation of a .py
    script (not in dual-tooling whitelist) as require_cover.
    """
    cmd = "py -3 work/sync-template-to-target.py --apply"
    r = _run_enforcer(_bash_payload(cmd), project_root)
    _assert_deny(r)


def test_v10_git_checkout_code_file_denied(project_root: Path) -> None:
    """V10 - git checkout main src/auth.py must DENY (Invariant 2)."""
    cmd = "git checkout main src/auth.py"
    r = _run_enforcer(_bash_payload(cmd), project_root)
    _assert_deny(r, must_contain_in_reason="src/auth.py")


def test_v11_worktrees_random_no_sentinel_denied(project_root: Path) -> None:
    """V11 - worktrees/random/foo.py with NO .dual-base-ref must DENY.

    Builds worktrees/random/foo.py UNDER project_root (which has no
    sentinel anywhere up the tree). Walking up from the file finds
    no sentinel -> enforcer must engage and DENY (Invariant 1).
    """
    target_rel = "worktrees/random-not-dual-teams/foo.py"
    target_abs = project_root / target_rel
    target_abs.parent.mkdir(parents=True, exist_ok=True)
    target_abs.write_text("# foo\n", encoding="utf-8")
    # Sanity: ensure no sentinel exists anywhere in this tree.
    sentinels = list(project_root.rglob(".dual-base-ref"))
    assert not sentinels, "test setup leaked a sentinel: " + str(sentinels)
    r = _run_enforcer(_edit_payload(target_rel), project_root)
    _assert_deny(r, must_contain_in_reason="foo.py")


def test_v12_stale_artifact_wrong_path_denied(
    project_root: Path, tmp_cover_artifact
) -> None:
    """V12 - recent (<15 min) result.md covers src/old.py, not src/new.py.

    Edit on src/new.py must DENY because no fresh result covers it
    (Invariant 3: path-exact coverage, no carryover).
    """
    tmp_cover_artifact("v12old", ["src/old.py"], status="pass")
    (project_root / "src" / "new.py").write_text("# new\n", encoding="utf-8")
    r = _run_enforcer(_edit_payload("src/new.py"), project_root)
    _assert_deny(r, must_contain_in_reason="src/new.py")


# ======================================================================
# ALLOW VECTORS (A01-A06) - each must produce no deny JSON
# ======================================================================

def test_a01_work_md_allowed(project_root: Path) -> None:
    """A1 - Edit on a .md file inside work/ must ALLOW (non-code, exempt)."""
    target = "work/notes.md"
    (project_root / "work" / "notes.md").write_text("# notes\n", encoding="utf-8")
    r = _run_enforcer(_edit_payload(target), project_root)
    _assert_allow(r)


def test_a02_bash_pytest_allowed(project_root: Path) -> None:
    """A2 - Bash ``pytest tests/`` must ALLOW (test runner whitelist)."""
    r = _run_enforcer(_bash_payload("pytest tests/"), project_root)
    _assert_allow(r)


def test_a03_bash_git_status_allowed(project_root: Path) -> None:
    """A3 - Bash ``git status`` must ALLOW (git-readonly whitelist)."""
    r = _run_enforcer(_bash_payload("git status"), project_root)
    _assert_allow(r)


def test_a04_bash_cp_readme_to_tmp_allowed(project_root: Path) -> None:
    """A4 - Bash ``cp README.md /tmp/`` must ALLOW (no code target)."""
    r = _run_enforcer(_bash_payload("cp README.md /tmp/"), project_root)
    _assert_allow(r)


def test_a05_dual_teams_worktree_allowed(tmp_worktree: Path) -> None:
    """A5 - Edit inside a worktree containing .dual-base-ref must ALLOW.

    Uses a dedicated tmp_worktree fixture (not project_root) so the
    sentinel sits exactly where the enforcer expects.
    """
    target_abs = tmp_worktree / ".claude" / "foo.py"
    target_abs.parent.mkdir(parents=True, exist_ok=True)
    target_abs.write_text("# foo\n", encoding="utf-8")
    target_rel = target_abs.relative_to(tmp_worktree).as_posix()
    r = _run_enforcer(_edit_payload(target_rel), tmp_worktree)
    _assert_allow(r)


def test_a06_valid_cover_allowed(
    project_root: Path, tmp_cover_artifact
) -> None:
    """A6 - Edit with a fresh, path-exact, status=pass cover must ALLOW."""
    target = "src/auth.py"
    (project_root / "src" / "auth.py").write_text("# auth\n", encoding="utf-8")
    tmp_cover_artifact("a06", ["src/auth.py"], status="pass")
    r = _run_enforcer(_edit_payload(target), project_root)
    _assert_allow(r)

def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.

    .claude/scripts/sync-template-to-target.py is the project's own helper
    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
    next to codex-ask.py, codex-implement.py, etc. Calling it via py -3 with
    arbitrary CLI args must NOT require a Codex cover.
    """
    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
    r = _run_enforcer(_bash_payload(cmd), project_root)
    _assert_allow(r)

 succeeded in 220ms:
 succeeded in 251ms:
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
# Z7-V02: .ipynb added - Jupyter notebooks contain executable code cells.
CODE_EXTENSIONS: frozenset = frozenset({
    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
    ".sql", ".lua", ".r", ".ipynb",
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
    ".claude/scripts/sync-template-to-target.py",
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
            # Z7-V03: newline terminates a logical command (heredoc body
            # lines may be reclassified individually; false positives are
            # preferable to masking a trailing mutating verb).
            if c == ";" or c == "\n":
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


def _codex_appears_unavailable(
    auth_path: Optional[Path] = None,
    now: Optional[datetime.datetime] = None,
    max_auth_age_hours: int = 24,
) -> tuple:
    """Return (True, reason) if Codex appears unusable, else (False, '').

    Y25 (Z12): pure helper, all kwargs optional for hermetic testing.
    Defaults to ~/.codex/auth.json + datetime.datetime.now().

    Detects two failure modes:
      1. ~/.codex/auth.json missing entirely (never logged in)
      2. ~/.codex/auth.json mtime older than max_auth_age_hours (token stale)

    Result is advisory only - the enforcer NEVER fails-open based on this.
    Used solely to prepend a human-readable hint to the DENY message so
    the user knows that running the suggested codex-inline-dual.py command
    will also fail until they refresh auth.
    """
    logger = logging.getLogger(HOOK_NAME)
    logger.debug(
        "codex_unavailable.enter auth_path=%s max_age_h=%d",
        auth_path, max_auth_age_hours,
    )
    try:
        auth = auth_path or (Path.home() / ".codex" / "auth.json")
        if not auth.exists():
            reason = "~/.codex/auth.json missing"
            logger.debug("codex_unavailable.exit unavailable=True reason=%s", reason)
            return True, reason
        clock = now or datetime.datetime.now()
        age_seconds = clock.timestamp() - auth.stat().st_mtime
        age_hours = age_seconds / 3600.0
        if age_hours > max_auth_age_hours:
            reason = ("~/.codex/auth.json older than "
                      + str(max_auth_age_hours) + "h ("
                      + str(int(age_hours)) + "h)")
            logger.debug("codex_unavailable.exit unavailable=True reason=%s", reason)
            return True, reason
        logger.debug("codex_unavailable.exit unavailable=False age_h=%.2f", age_hours)
        return False, ""
    except OSError as exc:
        # Stat / filesystem error - treat as unavailable so user gets a hint.
        logger.exception("codex_unavailable.os_err exc=%s", exc)
        return True, "~/.codex/auth.json unreadable: " + str(exc)
    except Exception as exc:
        # Any other error - fail-quiet, return False so enforcer prints
        # only the regular DENY message (no spurious hint).
        logger.exception("codex_unavailable.unexpected exc=%s", exc)
        return False, ""


def _build_block_message(blocked_path: str, reason_code: str) -> str:
    """Build the actionable DENY message for emit_deny.

    Y25 (Z12): when Codex itself appears unavailable (~/.codex/auth.json
    missing or stale), prepend a human-readable hint BEFORE the existing
    "no cover" / "codex-inline-dual.py" suggestion. The rule is unchanged
    (still fail-closed); only the wording improves so the user is not
    sent on a fool's errand of running a suggestion that will also fail.
    """
    logger = logging.getLogger(HOOK_NAME)
    reason_text = {
        "no-results": "no codex-implement result found",
        "no-results-dir": "work/codex-implementations/ does not exist",
        "stale": "all codex-implement results older than 15 min",
        "fail-status": "most recent matching result has status != pass",
        "scope-miss": "no recent pass result covers this exact path",
        "parse-error": "could not parse codex-implement result",
        "bash-no-cover": "Bash command would mutate code without cover",
    }.get(reason_code, reason_code)
    base_msg = (
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
    try:
        unavailable, why = _codex_appears_unavailable()
    except Exception as exc:
        logger.exception("build_block_message.unavail_check_err exc=%s", exc)
        unavailable, why = False, ""
    if unavailable:
        prefix = (
            "*** Codex appears unavailable: " + why + ".\n"
            "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
        )
        logger.info("build_block_message.unavailable_hint reason=%s", why)
        return prefix + base_msg
    return base_msg


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

2026-04-26T14:47:00.191079Z ERROR rmcp::transport::worker: worker quit with fatal: Client error: HTTP request failed: http/request failed: error sending request for url (https://chatgpt.com/backend-api/wham/apps), when send initialized notification
codex
The current test harness already uses subprocess payloads and a hermetic project root, so I’m going to extend that file in-place rather than add a second harness. I also noticed there are 19 existing tests including the Y22 whitelist test, which matches the task’s baseline count.
  ✓ Inspect live attack harness and enforcer classification behavior
  → Add V13-V18 subprocess tests within scoped test file
  • Run live matrix, capture actual V13-V18 results, and write findings
  • Run required regression suites, selftest, and findings existence check
  • Prepare self-report with pass/fail details and commit SHA if available
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "def parse_bash_command|def _classify_one_command|def _normalize_path_token|def _looks_like_path|def _extract_code_path_args|def extract_targets|def decide" .claude/hooks/codex-delegate-enforcer.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path .claude/hooks/codex-delegate-enforcer.py | Select-Object -Skip 300 -First 280' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
 succeeded in 141ms:
575:def _looks_like_path(token: str) -> bool:
582:def _normalize_path_token(token: str) -> str:
634:def parse_bash_command(command: str) -> dict:
770:def _extract_code_path_args(tokens: list) -> list:
1026:def extract_targets(payload: dict) -> list:
1060:def decide(payload: dict, project_dir: Path) -> bool:

 succeeded in 209ms:
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
            # Z7-V03: newline terminates a logical command (heredoc body
            # lines may be reclassified individually; false positives are
            # preferable to masking a trailing mutating verb).
            if c == ";" or c == "\n":
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


exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path .claude/hooks/codex-delegate-enforcer.py | Select-Object -Skip 580 -First 210' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path .claude/hooks/codex-delegate-enforcer.py | Select-Object -Skip 780 -First 120' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
 succeeded in 240ms:
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


 succeeded in 241ms:

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

codex
I’m adding a small skip-ledger reader for the V13 “explicit allow reason” case, then six tests with the exact payload shapes from the spec. V15 will include the positive opaque-binary control inside the same test so the future matcher doesn’t block every compiled binary blindly.
apply patch
patch: completed
C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix\.claude\hooks\test_enforcer_live_attacks.py
diff --git a/.claude/hooks/test_enforcer_live_attacks.py b/.claude/hooks/test_enforcer_live_attacks.py
index 33edb22e07bda37eb0c7c86547ba55d2fb030828..c7746a818b893fa8525f5acacd96340cb78d9f81
--- a/.claude/hooks/test_enforcer_live_attacks.py
+++ b/.claude/hooks/test_enforcer_live_attacks.py
@@ -102,22 +102,38 @@
         )
 
 
-def _assert_allow(result: subprocess.CompletedProcess) -> None:
-    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
-    assert result.returncode == 0, (
-        f"unexpected non-zero exit on allow: {result.returncode}; "
-        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
+def _assert_allow(result: subprocess.CompletedProcess) -> None:
+    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
+    assert result.returncode == 0, (
+        f"unexpected non-zero exit on allow: {result.returncode}; "
+        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
     )
     deny = _parse_deny(result.stdout)
-    assert deny is None, (
-        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
-    )
-
+    assert deny is None, (
+        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
+    )
+
+
+def _latest_skip_ledger_entry(project_root: Path) -> dict:
+    """Return the last skip-ledger entry for assertions on allow reasons."""
+    ledger = project_root / "work" / "codex-implementations" / "skip-ledger.jsonl"
+    if not ledger.exists():
+        return {}
+    lines = [line.strip() for line in ledger.read_text(encoding="utf-8").splitlines()
+             if line.strip()]
+    if not lines:
+        return {}
+    try:
+        obj = json.loads(lines[-1])
+    except json.JSONDecodeError:
+        return {}
+    return obj if isinstance(obj, dict) else {}
+
+
+# ----------------------------------------------------------------------
+# Fixtures
+# ----------------------------------------------------------------------
 
-# ----------------------------------------------------------------------
-# Fixtures
-# ----------------------------------------------------------------------
-
 @pytest.fixture
 def project_root(tmp_path: Path) -> Path:
     """Hermetic project root with the dirs the enforcer expects.
@@ -403,14 +419,95 @@
     r = _run_enforcer(_edit_payload(target), project_root)
     _assert_allow(r)
 
-def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
-    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
-
-    .claude/scripts/sync-template-to-target.py is the project's own helper
-    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
+def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
+    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
+
+    .claude/scripts/sync-template-to-target.py is the project's own helper
+    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
     next to codex-ask.py, codex-implement.py, etc. Calling it via py -3 with
     arbitrary CLI args must NOT require a Codex cover.
     """
-    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
-    r = _run_enforcer(_bash_payload(cmd), project_root)
-    _assert_allow(r)
+    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+# ======================================================================
+# DISCOVERY VECTORS (V13-V18) - Z13 expanded live attack matrix
+# ======================================================================
+
+def test_v13_cron_create_code_writer_denied(project_root: Path) -> None:
+    """V13 - schtasks/CronCreate-style background code writer must be covered.
+
+    A proper implementation may either DENY because the scheduled action
+    invokes a code-writing script, or explicitly ALLOW with a documented
+    background-scheduler-not-classified reason.
+    """
+    (project_root / "work" / "sync.py").write_text("# sync\n", encoding="utf-8")
+    cmd = 'schtasks /Create /TN x /TR "py -3 work/sync.py"'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    if _parse_deny(r.stdout) is not None:
+        return
+    entry = _latest_skip_ledger_entry(project_root)
+    assert entry.get("decision") == "allow", (
+        f"expected DENY or explicit ALLOW; returncode={r.returncode} "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+    assert entry.get("reason") == "background-scheduler-not-classified", (
+        "expected explicit scheduler gap reason; "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+
+
+def test_v14_mcp_filesystem_write_denied_OR_documented(project_root: Path) -> None:
+    """V14 - MCP filesystem write_file should be denied or treated as a gap."""
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "mcp__filesystem__write_file",
+        "tool_input": {"path": "src/x.py", "content": "print('x')\n"},
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r, must_contain_in_reason="src/x.py")
+
+
+def test_v15_compiled_binary_unknown_classification(project_root: Path) -> None:
+    """V15 - unknown binary mutating a code path must deny, opaque run allows."""
+    r = _run_enforcer(_bash_payload("./my-tool --output src/foo.py"), project_root)
+    _assert_deny(r, must_contain_in_reason="src/foo.py")
+
+    opaque = _run_enforcer(_bash_payload("./my-tool --version"), project_root)
+    _assert_allow(opaque)
+
+
+def test_v16_bash_dash_s_heredoc_requires_cover(project_root: Path) -> None:
+    """V16 - bash -s heredoc is opaque interpreter input and must DENY."""
+    cmd = 'bash -s <<EOF\necho "x" > src/foo.py\nEOF'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_deny(r)
+
+
+def test_v17_python_dash_c_readonly_should_allow_OR_document(
+    project_root: Path,
+) -> None:
+    """V17 - python -c with read-only open(...).read() should ALLOW."""
+    cmd = "python -c \"import json; print(open('config.json').read())\""
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+def test_v18_notebook_bash_magic_denied(project_root: Path) -> None:
+    """V18 - NotebookEdit containing %%bash code-path mutation must DENY."""
+    target = "src/foo.ipynb"
+    (project_root / target).write_text("{}\n", encoding="utf-8")
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "NotebookEdit",
+        "tool_input": {
+            "notebook_path": target,
+            "new_source": "%%bash\necho x > src/y.py",
+        },
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r)

diff --git a/.claude/hooks/test_enforcer_live_attacks.py b/.claude/hooks/test_enforcer_live_attacks.py
index 33edb22e07bda37eb0c7c86547ba55d2fb030828..c7746a818b893fa8525f5acacd96340cb78d9f81
--- a/.claude/hooks/test_enforcer_live_attacks.py
+++ b/.claude/hooks/test_enforcer_live_attacks.py
@@ -102,22 +102,38 @@
         )
 
 
-def _assert_allow(result: subprocess.CompletedProcess) -> None:
-    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
-    assert result.returncode == 0, (
-        f"unexpected non-zero exit on allow: {result.returncode}; "
-        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
+def _assert_allow(result: subprocess.CompletedProcess) -> None:
+    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
+    assert result.returncode == 0, (
+        f"unexpected non-zero exit on allow: {result.returncode}; "
+        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
     )
     deny = _parse_deny(result.stdout)
-    assert deny is None, (
-        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
-    )
-
+    assert deny is None, (
+        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
+    )
+
+
+def _latest_skip_ledger_entry(project_root: Path) -> dict:
+    """Return the last skip-ledger entry for assertions on allow reasons."""
+    ledger = project_root / "work" / "codex-implementations" / "skip-ledger.jsonl"
+    if not ledger.exists():
+        return {}
+    lines = [line.strip() for line in ledger.read_text(encoding="utf-8").splitlines()
+             if line.strip()]
+    if not lines:
+        return {}
+    try:
+        obj = json.loads(lines[-1])
+    except json.JSONDecodeError:
+        return {}
+    return obj if isinstance(obj, dict) else {}
+
+
+# ----------------------------------------------------------------------
+# Fixtures
+# ----------------------------------------------------------------------
 
-# ----------------------------------------------------------------------
-# Fixtures
-# ----------------------------------------------------------------------
-
 @pytest.fixture
 def project_root(tmp_path: Path) -> Path:
     """Hermetic project root with the dirs the enforcer expects.
@@ -403,14 +419,95 @@
     r = _run_enforcer(_edit_payload(target), project_root)
     _assert_allow(r)
 
-def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
-    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
-
-    .claude/scripts/sync-template-to-target.py is the project's own helper
-    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
+def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
+    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
+
+    .claude/scripts/sync-template-to-target.py is the project's own helper
+    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
     next to codex-ask.py, codex-implement.py, etc. Calling it via py -3 with
     arbitrary CLI args must NOT require a Codex cover.
     """
-    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
-    r = _run_enforcer(_bash_payload(cmd), project_root)
-    _assert_allow(r)
+    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+# ======================================================================
+# DISCOVERY VECTORS (V13-V18) - Z13 expanded live attack matrix
+# ======================================================================
+
+def test_v13_cron_create_code_writer_denied(project_root: Path) -> None:
+    """V13 - schtasks/CronCreate-style background code writer must be covered.
+
+    A proper implementation may either DENY because the scheduled action
+    invokes a code-writing script, or explicitly ALLOW with a documented
+    background-scheduler-not-classified reason.
+    """
+    (project_root / "work" / "sync.py").write_text("# sync\n", encoding="utf-8")
+    cmd = 'schtasks /Create /TN x /TR "py -3 work/sync.py"'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    if _parse_deny(r.stdout) is not None:
+        return
+    entry = _latest_skip_ledger_entry(project_root)
+    assert entry.get("decision") == "allow", (
+        f"expected DENY or explicit ALLOW; returncode={r.returncode} "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+    assert entry.get("reason") == "background-scheduler-not-classified", (
+        "expected explicit scheduler gap reason; "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+
+
+def test_v14_mcp_filesystem_write_denied_OR_documented(project_root: Path) -> None:
+    """V14 - MCP filesystem write_file should be denied or treated as a gap."""
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "mcp__filesystem__write_file",
+        "tool_input": {"path": "src/x.py", "content": "print('x')\n"},
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r, must_contain_in_reason="src/x.py")
+
+
+def test_v15_compiled_binary_unknown_classification(project_root: Path) -> None:
+    """V15 - unknown binary mutating a code path must deny, opaque run allows."""
+    r = _run_enforcer(_bash_payload("./my-tool --output src/foo.py"), project_root)
+    _assert_deny(r, must_contain_in_reason="src/foo.py")
+
+    opaque = _run_enforcer(_bash_payload("./my-tool --version"), project_root)
+    _assert_allow(opaque)
+
+
+def test_v16_bash_dash_s_heredoc_requires_cover(project_root: Path) -> None:
+    """V16 - bash -s heredoc is opaque interpreter input and must DENY."""
+    cmd = 'bash -s <<EOF\necho "x" > src/foo.py\nEOF'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_deny(r)
+
+
+def test_v17_python_dash_c_readonly_should_allow_OR_document(
+    project_root: Path,
+) -> None:
+    """V17 - python -c with read-only open(...).read() should ALLOW."""
+    cmd = "python -c \"import json; print(open('config.json').read())\""
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+def test_v18_notebook_bash_magic_denied(project_root: Path) -> None:
+    """V18 - NotebookEdit containing %%bash code-path mutation must DENY."""
+    target = "src/foo.ipynb"
+    (project_root / target).write_text("{}\n", encoding="utf-8")
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "NotebookEdit",
+        "tool_input": {
+            "notebook_path": target,
+            "new_source": "%%bash\necho x > src/y.py",
+        },
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r)

codex
The six discovery tests are in place. I’m running the live matrix now to confirm collection is clean, preserve the 19 existing outcomes, and identify which of V13-V18 actually fail against the current enforcer.
  ✓ Inspect live attack harness and enforcer classification behavior
  ✓ Add V13-V18 subprocess tests within scoped test file
  → Run live matrix, capture actual V13-V18 results, and write findings
  • Run required regression suites, selftest, and findings existence check
  • Prepare self-report with pass/fail details and commit SHA if available
diff --git a/.claude/hooks/test_enforcer_live_attacks.py b/.claude/hooks/test_enforcer_live_attacks.py
index 33edb22e07bda37eb0c7c86547ba55d2fb030828..c7746a818b893fa8525f5acacd96340cb78d9f81
--- a/.claude/hooks/test_enforcer_live_attacks.py
+++ b/.claude/hooks/test_enforcer_live_attacks.py
@@ -102,22 +102,38 @@
         )
 
 
-def _assert_allow(result: subprocess.CompletedProcess) -> None:
-    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
-    assert result.returncode == 0, (
-        f"unexpected non-zero exit on allow: {result.returncode}; "
-        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
+def _assert_allow(result: subprocess.CompletedProcess) -> None:
+    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
+    assert result.returncode == 0, (
+        f"unexpected non-zero exit on allow: {result.returncode}; "
+        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
     )
     deny = _parse_deny(result.stdout)
-    assert deny is None, (
-        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
-    )
-
+    assert deny is None, (
+        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
+    )
+
+
+def _latest_skip_ledger_entry(project_root: Path) -> dict:
+    """Return the last skip-ledger entry for assertions on allow reasons."""
+    ledger = project_root / "work" / "codex-implementations" / "skip-ledger.jsonl"
+    if not ledger.exists():
+        return {}
+    lines = [line.strip() for line in ledger.read_text(encoding="utf-8").splitlines()
+             if line.strip()]
+    if not lines:
+        return {}
+    try:
+        obj = json.loads(lines[-1])
+    except json.JSONDecodeError:
+        return {}
+    return obj if isinstance(obj, dict) else {}
+
+
+# ----------------------------------------------------------------------
+# Fixtures
+# ----------------------------------------------------------------------
 
-# ----------------------------------------------------------------------
-# Fixtures
-# ----------------------------------------------------------------------
-
 @pytest.fixture
 def project_root(tmp_path: Path) -> Path:
     """Hermetic project root with the dirs the enforcer expects.
@@ -403,14 +419,95 @@
     r = _run_enforcer(_edit_payload(target), project_root)
     _assert_allow(r)
 
-def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
-    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
-
-    .claude/scripts/sync-template-to-target.py is the project's own helper
-    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
+def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
+    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
+
+    .claude/scripts/sync-template-to-target.py is the project's own helper
+    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
     next to codex-ask.py, codex-implement.py, etc. Calling it via py -3 with
     arbitrary CLI args must NOT require a Codex cover.
     """
-    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
-    r = _run_enforcer(_bash_payload(cmd), project_root)
-    _assert_allow(r)
+    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+# ======================================================================
+# DISCOVERY VECTORS (V13-V18) - Z13 expanded live attack matrix
+# ======================================================================
+
+def test_v13_cron_create_code_writer_denied(project_root: Path) -> None:
+    """V13 - schtasks/CronCreate-style background code writer must be covered.
+
+    A proper implementation may either DENY because the scheduled action
+    invokes a code-writing script, or explicitly ALLOW with a documented
+    background-scheduler-not-classified reason.
+    """
+    (project_root / "work" / "sync.py").write_text("# sync\n", encoding="utf-8")
+    cmd = 'schtasks /Create /TN x /TR "py -3 work/sync.py"'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    if _parse_deny(r.stdout) is not None:
+        return
+    entry = _latest_skip_ledger_entry(project_root)
+    assert entry.get("decision") == "allow", (
+        f"expected DENY or explicit ALLOW; returncode={r.returncode} "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+    assert entry.get("reason") == "background-scheduler-not-classified", (
+        "expected explicit scheduler gap reason; "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+
+
+def test_v14_mcp_filesystem_write_denied_OR_documented(project_root: Path) -> None:
+    """V14 - MCP filesystem write_file should be denied or treated as a gap."""
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "mcp__filesystem__write_file",
+        "tool_input": {"path": "src/x.py", "content": "print('x')\n"},
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r, must_contain_in_reason="src/x.py")
+
+
+def test_v15_compiled_binary_unknown_classification(project_root: Path) -> None:
+    """V15 - unknown binary mutating a code path must deny, opaque run allows."""
+    r = _run_enforcer(_bash_payload("./my-tool --output src/foo.py"), project_root)
+    _assert_deny(r, must_contain_in_reason="src/foo.py")
+
+    opaque = _run_enforcer(_bash_payload("./my-tool --version"), project_root)
+    _assert_allow(opaque)
+
+
+def test_v16_bash_dash_s_heredoc_requires_cover(project_root: Path) -> None:
+    """V16 - bash -s heredoc is opaque interpreter input and must DENY."""
+    cmd = 'bash -s <<EOF\necho "x" > src/foo.py\nEOF'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_deny(r)
+
+
+def test_v17_python_dash_c_readonly_should_allow_OR_document(
+    project_root: Path,
+) -> None:
+    """V17 - python -c with read-only open(...).read() should ALLOW."""
+    cmd = "python -c \"import json; print(open('config.json').read())\""
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+def test_v18_notebook_bash_magic_denied(project_root: Path) -> None:
+    """V18 - NotebookEdit containing %%bash code-path mutation must DENY."""
+    target = "src/foo.ipynb"
+    (project_root / target).write_text("{}\n", encoding="utf-8")
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "NotebookEdit",
+        "tool_input": {
+            "notebook_path": target,
+            "new_source": "%%bash\necho x > src/y.py",
+        },
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r)

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/hooks/test_enforcer_live_attacks.py -v --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
2026-04-26T14:48:36.752716Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 2.6 seconds
Output:
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.2, pluggy-1.6.0 -- C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
plugins: anyio-4.12.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 25 items

.claude/hooks/test_enforcer_live_attacks.py::test_v01_work_py_denied PASSED [  4%]
.claude/hooks/test_enforcer_live_attacks.py::test_v02_notebook_edit_denied PASSED [  8%]
.claude/hooks/test_enforcer_live_attacks.py::test_v03_bash_heredoc_git_apply_denied PASSED [ 12%]
.claude/hooks/test_enforcer_live_attacks.py::test_v04_bash_sed_inplace_on_code_denied PASSED [ 16%]
.claude/hooks/test_enforcer_live_attacks.py::test_v05_bash_cp_code_to_code_denied PASSED [ 20%]
.claude/hooks/test_enforcer_live_attacks.py::test_v06_powershell_set_content_on_code_denied PASSED [ 24%]
.claude/hooks/test_enforcer_live_attacks.py::test_v07_python_dash_c_open_write_denied PASSED [ 28%]
.claude/hooks/test_enforcer_live_attacks.py::test_v08_edit_claude_scripts_py_denied PASSED [ 32%]
.claude/hooks/test_enforcer_live_attacks.py::test_v09_bash_invokes_mass_mutating_script_denied PASSED [ 36%]
.claude/hooks/test_enforcer_live_attacks.py::test_v10_git_checkout_code_file_denied PASSED [ 40%]
.claude/hooks/test_enforcer_live_attacks.py::test_v11_worktrees_random_no_sentinel_denied PASSED [ 44%]
.claude/hooks/test_enforcer_live_attacks.py::test_v12_stale_artifact_wrong_path_denied PASSED [ 48%]
.claude/hooks/test_enforcer_live_attacks.py::test_a01_work_md_allowed PASSED [ 52%]
.claude/hooks/test_enforcer_live_attacks.py::test_a02_bash_pytest_allowed PASSED [ 56%]
.claude/hooks/test_enforcer_live_attacks.py::test_a03_bash_git_status_allowed PASSED [ 60%]
.claude/hooks/test_enforcer_live_attacks.py::test_a04_bash_cp_readme_to_tmp_allowed PASSED [ 64%]
.claude/hooks/test_enforcer_live_attacks.py::test_a05_dual_teams_worktree_allowed PASSED [ 68%]
.claude/hooks/test_enforcer_live_attacks.py::test_a06_valid_cover_allowed PASSED [ 72%]
.claude/hooks/test_enforcer_live_attacks.py::test_a07_sync_script_invocation_allowed PASSED [ 76%]
.claude/hooks/test_enforcer_live_attacks.py::test_v13_cron_create_code_writer_denied FAILED [ 80%]
.claude/hooks/test_enforcer_live_attacks.py::test_v14_mcp_filesystem_write_denied_OR_documented FAILED [ 84%]
.claude/hooks/test_enforcer_live_attacks.py::test_v15_compiled_binary_unknown_classification FAILED [ 88%]
.claude/hooks/test_enforcer_live_attacks.py::test_v16_bash_dash_s_heredoc_requires_cover PASSED [ 92%]
.claude/hooks/test_enforcer_live_attacks.py::test_v17_python_dash_c_readonly_should_allow_OR_document PASSED [ 96%]
.claude/hooks/test_enforcer_live_attacks.py::test_v18_notebook_bash_magic_denied PASSED [100%]

================================== FAILURES ===================================
E   AssertionError: expected explicit scheduler gap reason; stdout='' stderr='' ledger={'ts': '2026-04-26T14:48:36+00:00', 'tool': 'Bash', 'cmd': 'schtasks /Create /TN x /TR "py -3 work/sync.py"', 'decision': 'allow', 'reason': 'whitelist-or-no-mutation'}
    assert 'whitelist-or-no-mutation' == 'background-s...ot-classified'
      
      - background-scheduler-not-classified
      + whitelist-or-no-mutation
C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix\.claude\hooks\test_enforcer_live_attacks.py:456: AssertionError: expected explicit scheduler gap reason; stdout='' stderr='' ledger={'ts': '2026-04-26T14:48:36+00:00', 'tool': 'Bash', 'cmd': 'schtasks /Create /TN x /TR "py -3 work/sync.py"', 'decision': 'allow', 'reason': 'whitelist-or-no-mutation'}
E   AssertionError: expected DENY JSON on stdout. returncode=0 stdout='' stderr=''
    assert None is not None
C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix\.claude\hooks\test_enforcer_live_attacks.py:91: AssertionError: expected DENY JSON on stdout. returncode=0 stdout='' stderr=''
E   AssertionError: expected DENY JSON on stdout. returncode=0 stdout='' stderr=''
    assert None is not None
C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix\.claude\hooks\test_enforcer_live_attacks.py:91: AssertionError: expected DENY JSON on stdout. returncode=0 stdout='' stderr=''
=========================== short test summary info ===========================
FAILED .claude/hooks/test_enforcer_live_attacks.py::test_v13_cron_create_code_writer_denied
FAILED .claude/hooks/test_enforcer_live_attacks.py::test_v14_mcp_filesystem_write_denied_OR_documented
FAILED .claude/hooks/test_enforcer_live_attacks.py::test_v15_compiled_binary_unknown_classification
======================== 3 failed, 22 passed in 1.87s =========================

 exited 1 in 2559ms:
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.2, pluggy-1.6.0 -- C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
plugins: anyio-4.12.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 25 items

.claude/hooks/test_enforcer_live_attacks.py::test_v01_work_py_denied PASSED [  4%]
.claude/hooks/test_enforcer_live_attacks.py::test_v02_notebook_edit_denied PASSED [  8%]
.claude/hooks/test_enforcer_live_attacks.py::test_v03_bash_heredoc_git_apply_denied PASSED [ 12%]
.claude/hooks/test_enforcer_live_attacks.py::test_v04_bash_sed_inplace_on_code_denied PASSED [ 16%]
.claude/hooks/test_enforcer_live_attacks.py::test_v05_bash_cp_code_to_code_denied PASSED [ 20%]
.claude/hooks/test_enforcer_live_attacks.py::test_v06_powershell_set_content_on_code_denied PASSED [ 24%]
.claude/hooks/test_enforcer_live_attacks.py::test_v07_python_dash_c_open_write_denied PASSED [ 28%]
.claude/hooks/test_enforcer_live_attacks.py::test_v08_edit_claude_scripts_py_denied PASSED [ 32%]
.claude/hooks/test_enforcer_live_attacks.py::test_v09_bash_invokes_mass_mutating_script_denied PASSED [ 36%]
.claude/hooks/test_enforcer_live_attacks.py::test_v10_git_checkout_code_file_denied PASSED [ 40%]
.claude/hooks/test_enforcer_live_attacks.py::test_v11_worktrees_random_no_sentinel_denied PASSED [ 44%]
.claude/hooks/test_enforcer_live_attacks.py::test_v12_stale_artifact_wrong_path_denied PASSED [ 48%]
.claude/hooks/test_enforcer_live_attacks.py::test_a01_work_md_allowed PASSED [ 52%]
.claude/hooks/test_enforcer_live_attacks.py::test_a02_bash_pytest_allowed PASSED [ 56%]
.claude/hooks/test_enforcer_live_attacks.py::test_a03_bash_git_status_allowed PASSED [ 60%]
.claude/hooks/test_enforcer_live_attacks.py::test_a04_bash_cp_readme_to_tmp_allowed PASSED [ 64%]
.claude/hooks/test_enforcer_live_attacks.py::test_a05_dual_teams_worktree_allowed PASSED [ 68%]
.claude/hooks/test_enforcer_live_attacks.py::test_a06_valid_cover_allowed PASSED [ 72%]
.claude/hooks/test_enforcer_live_attacks.py::test_a07_sync_script_invocation_allowed PASSED [ 76%]
.claude/hooks/test_enforcer_live_attacks.py::test_v13_cron_create_code_writer_denied FAILED [ 80%]
.claude/hooks/test_enforcer_live_attacks.py::test_v14_mcp_filesystem_write_denied_OR_documented FAILED [ 84%]
.claude/hooks/test_enforcer_live_attacks.py::test_v15_compiled_binary_unknown_classification FAILED [ 88%]
.claude/hooks/test_enforcer_live_attacks.py::test_v16_bash_dash_s_heredoc_requires_cover PASSED [ 92%]
.claude/hooks/test_enforcer_live_attacks.py::test_v17_python_dash_c_readonly_should_allow_OR_document PASSED [ 96%]
.claude/hooks/test_enforcer_live_attacks.py::test_v18_notebook_bash_magic_denied PASSED [100%]

================================== FAILURES ===================================
E   AssertionError: expected explicit scheduler gap reason; stdout='' stderr='' ledger={'ts': '2026-04-26T14:48:36+00:00', 'tool': 'Bash', 'cmd': 'schtasks /Create /TN x /TR "py -3 work/sync.py"', 'decision': 'allow', 'reason': 'whitelist-or-no-mutation'}
    assert 'whitelist-or-no-mutation' == 'background-s...ot-classified'
      
      - background-scheduler-not-classified
      + whitelist-or-no-mutation
C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix\.claude\hooks\test_enforcer_live_attacks.py:456: AssertionError: expected explicit scheduler gap reason; stdout='' stderr='' ledger={'ts': '2026-04-26T14:48:36+00:00', 'tool': 'Bash', 'cmd': 'schtasks /Create /TN x /TR "py -3 work/sync.py"', 'decision': 'allow', 'reason': 'whitelist-or-no-mutation'}
E   AssertionError: expected DENY JSON on stdout. returncode=0 stdout='' stderr=''
    assert None is not None
C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix\.claude\hooks\test_enforcer_live_attacks.py:91: AssertionError: expected DENY JSON on stdout. returncode=0 stdout='' stderr=''
E   AssertionError: expected DENY JSON on stdout. returncode=0 stdout='' stderr=''
    assert None is not None
C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix\.claude\hooks\test_enforcer_live_attacks.py:91: AssertionError: expected DENY JSON on stdout. returncode=0 stdout='' stderr=''
=========================== short test summary info ===========================
FAILED .claude/hooks/test_enforcer_live_attacks.py::test_v13_cron_create_code_writer_denied
FAILED .claude/hooks/test_enforcer_live_attacks.py::test_v14_mcp_filesystem_write_denied_OR_documented
FAILED .claude/hooks/test_enforcer_live_attacks.py::test_v15_compiled_binary_unknown_classification
======================== 3 failed, 22 passed in 1.87s =========================

diff --git a/.claude/hooks/test_enforcer_live_attacks.py b/.claude/hooks/test_enforcer_live_attacks.py
index 33edb22e07bda37eb0c7c86547ba55d2fb030828..c7746a818b893fa8525f5acacd96340cb78d9f81
--- a/.claude/hooks/test_enforcer_live_attacks.py
+++ b/.claude/hooks/test_enforcer_live_attacks.py
@@ -102,22 +102,38 @@
         )
 
 
-def _assert_allow(result: subprocess.CompletedProcess) -> None:
-    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
-    assert result.returncode == 0, (
-        f"unexpected non-zero exit on allow: {result.returncode}; "
-        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
+def _assert_allow(result: subprocess.CompletedProcess) -> None:
+    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
+    assert result.returncode == 0, (
+        f"unexpected non-zero exit on allow: {result.returncode}; "
+        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
     )
     deny = _parse_deny(result.stdout)
-    assert deny is None, (
-        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
-    )
-
+    assert deny is None, (
+        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
+    )
+
+
+def _latest_skip_ledger_entry(project_root: Path) -> dict:
+    """Return the last skip-ledger entry for assertions on allow reasons."""
+    ledger = project_root / "work" / "codex-implementations" / "skip-ledger.jsonl"
+    if not ledger.exists():
+        return {}
+    lines = [line.strip() for line in ledger.read_text(encoding="utf-8").splitlines()
+             if line.strip()]
+    if not lines:
+        return {}
+    try:
+        obj = json.loads(lines[-1])
+    except json.JSONDecodeError:
+        return {}
+    return obj if isinstance(obj, dict) else {}
+
+
+# ----------------------------------------------------------------------
+# Fixtures
+# ----------------------------------------------------------------------
 
-# ----------------------------------------------------------------------
-# Fixtures
-# ----------------------------------------------------------------------
-
 @pytest.fixture
 def project_root(tmp_path: Path) -> Path:
     """Hermetic project root with the dirs the enforcer expects.
@@ -403,14 +419,95 @@
     r = _run_enforcer(_edit_payload(target), project_root)
     _assert_allow(r)
 
-def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
-    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
-
-    .claude/scripts/sync-template-to-target.py is the project's own helper
-    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
+def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
+    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
+
+    .claude/scripts/sync-template-to-target.py is the project's own helper
+    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
     next to codex-ask.py, codex-implement.py, etc. Calling it via py -3 with
     arbitrary CLI args must NOT require a Codex cover.
     """
-    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
-    r = _run_enforcer(_bash_payload(cmd), project_root)
-    _assert_allow(r)
+    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+# ======================================================================
+# DISCOVERY VECTORS (V13-V18) - Z13 expanded live attack matrix
+# ======================================================================
+
+def test_v13_cron_create_code_writer_denied(project_root: Path) -> None:
+    """V13 - schtasks/CronCreate-style background code writer must be covered.
+
+    A proper implementation may either DENY because the scheduled action
+    invokes a code-writing script, or explicitly ALLOW with a documented
+    background-scheduler-not-classified reason.
+    """
+    (project_root / "work" / "sync.py").write_text("# sync\n", encoding="utf-8")
+    cmd = 'schtasks /Create /TN x /TR "py -3 work/sync.py"'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    if _parse_deny(r.stdout) is not None:
+        return
+    entry = _latest_skip_ledger_entry(project_root)
+    assert entry.get("decision") == "allow", (
+        f"expected DENY or explicit ALLOW; returncode={r.returncode} "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+    assert entry.get("reason") == "background-scheduler-not-classified", (
+        "expected explicit scheduler gap reason; "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+
+
+def test_v14_mcp_filesystem_write_denied_OR_documented(project_root: Path) -> None:
+    """V14 - MCP filesystem write_file should be denied or treated as a gap."""
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "mcp__filesystem__write_file",
+        "tool_input": {"path": "src/x.py", "content": "print('x')\n"},
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r, must_contain_in_reason="src/x.py")
+
+
+def test_v15_compiled_binary_unknown_classification(project_root: Path) -> None:
+    """V15 - unknown binary mutating a code path must deny, opaque run allows."""
+    r = _run_enforcer(_bash_payload("./my-tool --output src/foo.py"), project_root)
+    _assert_deny(r, must_contain_in_reason="src/foo.py")
+
+    opaque = _run_enforcer(_bash_payload("./my-tool --version"), project_root)
+    _assert_allow(opaque)
+
+
+def test_v16_bash_dash_s_heredoc_requires_cover(project_root: Path) -> None:
+    """V16 - bash -s heredoc is opaque interpreter input and must DENY."""
+    cmd = 'bash -s <<EOF\necho "x" > src/foo.py\nEOF'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_deny(r)
+
+
+def test_v17_python_dash_c_readonly_should_allow_OR_document(
+    project_root: Path,
+) -> None:
+    """V17 - python -c with read-only open(...).read() should ALLOW."""
+    cmd = "python -c \"import json; print(open('config.json').read())\""
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+def test_v18_notebook_bash_magic_denied(project_root: Path) -> None:
+    """V18 - NotebookEdit containing %%bash code-path mutation must DENY."""
+    target = "src/foo.ipynb"
+    (project_root / target).write_text("{}\n", encoding="utf-8")
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "NotebookEdit",
+        "tool_input": {
+            "notebook_path": target,
+            "new_source": "%%bash\necho x > src/y.py",
+        },
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r)

codex
The live matrix collected all 25 tests cleanly: the original 19 all passed, and V13, V14, and V15 failed as discovery gaps. I’m writing those exact observations into the scoped findings document before running the remaining required suites.
apply patch
patch: completed
C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix\work\criterion-upgrade\Z13-findings.md
diff --git a/.claude/hooks/test_enforcer_live_attacks.py b/.claude/hooks/test_enforcer_live_attacks.py
index 33edb22e07bda37eb0c7c86547ba55d2fb030828..c7746a818b893fa8525f5acacd96340cb78d9f81
--- a/.claude/hooks/test_enforcer_live_attacks.py
+++ b/.claude/hooks/test_enforcer_live_attacks.py
@@ -102,22 +102,38 @@
         )
 
 
-def _assert_allow(result: subprocess.CompletedProcess) -> None:
-    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
-    assert result.returncode == 0, (
-        f"unexpected non-zero exit on allow: {result.returncode}; "
-        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
+def _assert_allow(result: subprocess.CompletedProcess) -> None:
+    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
+    assert result.returncode == 0, (
+        f"unexpected non-zero exit on allow: {result.returncode}; "
+        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
     )
     deny = _parse_deny(result.stdout)
-    assert deny is None, (
-        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
-    )
-
+    assert deny is None, (
+        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
+    )
+
+
+def _latest_skip_ledger_entry(project_root: Path) -> dict:
+    """Return the last skip-ledger entry for assertions on allow reasons."""
+    ledger = project_root / "work" / "codex-implementations" / "skip-ledger.jsonl"
+    if not ledger.exists():
+        return {}
+    lines = [line.strip() for line in ledger.read_text(encoding="utf-8").splitlines()
+             if line.strip()]
+    if not lines:
+        return {}
+    try:
+        obj = json.loads(lines[-1])
+    except json.JSONDecodeError:
+        return {}
+    return obj if isinstance(obj, dict) else {}
+
+
+# ----------------------------------------------------------------------
+# Fixtures
+# ----------------------------------------------------------------------
 
-# ----------------------------------------------------------------------
-# Fixtures
-# ----------------------------------------------------------------------
-
 @pytest.fixture
 def project_root(tmp_path: Path) -> Path:
     """Hermetic project root with the dirs the enforcer expects.
@@ -403,14 +419,95 @@
     r = _run_enforcer(_edit_payload(target), project_root)
     _assert_allow(r)
 
-def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
-    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
-
-    .claude/scripts/sync-template-to-target.py is the project's own helper
-    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
+def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
+    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
+
+    .claude/scripts/sync-template-to-target.py is the project's own helper
+    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
     next to codex-ask.py, codex-implement.py, etc. Calling it via py -3 with
     arbitrary CLI args must NOT require a Codex cover.
     """
-    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
-    r = _run_enforcer(_bash_payload(cmd), project_root)
-    _assert_allow(r)
+    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+# ======================================================================
+# DISCOVERY VECTORS (V13-V18) - Z13 expanded live attack matrix
+# ======================================================================
+
+def test_v13_cron_create_code_writer_denied(project_root: Path) -> None:
+    """V13 - schtasks/CronCreate-style background code writer must be covered.
+
+    A proper implementation may either DENY because the scheduled action
+    invokes a code-writing script, or explicitly ALLOW with a documented
+    background-scheduler-not-classified reason.
+    """
+    (project_root / "work" / "sync.py").write_text("# sync\n", encoding="utf-8")
+    cmd = 'schtasks /Create /TN x /TR "py -3 work/sync.py"'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    if _parse_deny(r.stdout) is not None:
+        return
+    entry = _latest_skip_ledger_entry(project_root)
+    assert entry.get("decision") == "allow", (
+        f"expected DENY or explicit ALLOW; returncode={r.returncode} "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+    assert entry.get("reason") == "background-scheduler-not-classified", (
+        "expected explicit scheduler gap reason; "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+
+
+def test_v14_mcp_filesystem_write_denied_OR_documented(project_root: Path) -> None:
+    """V14 - MCP filesystem write_file should be denied or treated as a gap."""
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "mcp__filesystem__write_file",
+        "tool_input": {"path": "src/x.py", "content": "print('x')\n"},
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r, must_contain_in_reason="src/x.py")
+
+
+def test_v15_compiled_binary_unknown_classification(project_root: Path) -> None:
+    """V15 - unknown binary mutating a code path must deny, opaque run allows."""
+    r = _run_enforcer(_bash_payload("./my-tool --output src/foo.py"), project_root)
+    _assert_deny(r, must_contain_in_reason="src/foo.py")
+
+    opaque = _run_enforcer(_bash_payload("./my-tool --version"), project_root)
+    _assert_allow(opaque)
+
+
+def test_v16_bash_dash_s_heredoc_requires_cover(project_root: Path) -> None:
+    """V16 - bash -s heredoc is opaque interpreter input and must DENY."""
+    cmd = 'bash -s <<EOF\necho "x" > src/foo.py\nEOF'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_deny(r)
+
+
+def test_v17_python_dash_c_readonly_should_allow_OR_document(
+    project_root: Path,
+) -> None:
+    """V17 - python -c with read-only open(...).read() should ALLOW."""
+    cmd = "python -c \"import json; print(open('config.json').read())\""
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+def test_v18_notebook_bash_magic_denied(project_root: Path) -> None:
+    """V18 - NotebookEdit containing %%bash code-path mutation must DENY."""
+    target = "src/foo.ipynb"
+    (project_root / target).write_text("{}\n", encoding="utf-8")
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "NotebookEdit",
+        "tool_input": {
+            "notebook_path": target,
+            "new_source": "%%bash\necho x > src/y.py",
+        },
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r)
diff --git a/work/criterion-upgrade/Z13-findings.md b/work/criterion-upgrade/Z13-findings.md
new file mode 100644
index 0000000000000000000000000000000000000000..38b585b618ee80901232f87f6ac44c540b74510e
--- /dev/null
+++ b/work/criterion-upgrade/Z13-findings.md
@@ -0,0 +1,17 @@
+# Z13 Findings — Vectors V13-V18 actual enforcer behavior
+
+| # | Vector | Test result | Real gap? | Recommended Z14 fix |
+|---|--------|-------------|-----------|---------------------|
+| V13 | CronCreate | FAIL | yes | Classify `schtasks /Create ... /TR` as scheduler input and recursively inspect the scheduled command, or emit explicit `background-scheduler-not-classified` allow reason. |
+| V14 | MCP filesystem | FAIL | yes | Add MCP write tools such as `mcp__filesystem__write_file` to hook dispatch and extract `path` as a code-write target. |
+| V15 | Compiled binary | FAIL | yes | For unknown executables, require cover when any argument token names a code-extension path, while allowing opaque runs without code-path tokens. |
+| V16 | `bash -s` heredoc | PASS | no | Keep always-cover handling for `bash -s`/stdin-opaque interpreter input. |
+| V17 | `py -c` read-only | PASS | no | Keep read/write-sensitive `python -c` parsing so read-only `open(...).read()` allows. |
+| V18 | Notebook `%%bash` magic | PASS | no | Current NotebookEdit denial covers the `.ipynb`; preserve denial for notebook cells that can mutate code paths. |
+
+## Summary
+
+- Total new tests: 6
+- Currently passing (no real gap): 3
+- Currently failing (real gap, fix in Z14): 3
+- Gaps discovered: V13 scheduler-created background code writers, V14 MCP filesystem writes, V15 unknown compiled binaries with code-path arguments

diff --git a/.claude/hooks/test_enforcer_live_attacks.py b/.claude/hooks/test_enforcer_live_attacks.py
index 33edb22e07bda37eb0c7c86547ba55d2fb030828..c7746a818b893fa8525f5acacd96340cb78d9f81
--- a/.claude/hooks/test_enforcer_live_attacks.py
+++ b/.claude/hooks/test_enforcer_live_attacks.py
@@ -102,22 +102,38 @@
         )
 
 
-def _assert_allow(result: subprocess.CompletedProcess) -> None:
-    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
-    assert result.returncode == 0, (
-        f"unexpected non-zero exit on allow: {result.returncode}; "
-        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
+def _assert_allow(result: subprocess.CompletedProcess) -> None:
+    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
+    assert result.returncode == 0, (
+        f"unexpected non-zero exit on allow: {result.returncode}; "
+        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
     )
     deny = _parse_deny(result.stdout)
-    assert deny is None, (
-        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
-    )
-
+    assert deny is None, (
+        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
+    )
+
+
+def _latest_skip_ledger_entry(project_root: Path) -> dict:
+    """Return the last skip-ledger entry for assertions on allow reasons."""
+    ledger = project_root / "work" / "codex-implementations" / "skip-ledger.jsonl"
+    if not ledger.exists():
+        return {}
+    lines = [line.strip() for line in ledger.read_text(encoding="utf-8").splitlines()
+             if line.strip()]
+    if not lines:
+        return {}
+    try:
+        obj = json.loads(lines[-1])
+    except json.JSONDecodeError:
+        return {}
+    return obj if isinstance(obj, dict) else {}
+
+
+# ----------------------------------------------------------------------
+# Fixtures
+# ----------------------------------------------------------------------
 
-# ----------------------------------------------------------------------
-# Fixtures
-# ----------------------------------------------------------------------
-
 @pytest.fixture
 def project_root(tmp_path: Path) -> Path:
     """Hermetic project root with the dirs the enforcer expects.
@@ -403,14 +419,95 @@
     r = _run_enforcer(_edit_payload(target), project_root)
     _assert_allow(r)
 
-def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
-    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
-
-    .claude/scripts/sync-template-to-target.py is the project's own helper
-    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
+def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
+    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
+
+    .claude/scripts/sync-template-to-target.py is the project's own helper
+    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
     next to codex-ask.py, codex-implement.py, etc. Calling it via py -3 with
     arbitrary CLI args must NOT require a Codex cover.
     """
-    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
-    r = _run_enforcer(_bash_payload(cmd), project_root)
-    _assert_allow(r)
+    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+# ======================================================================
+# DISCOVERY VECTORS (V13-V18) - Z13 expanded live attack matrix
+# ======================================================================
+
+def test_v13_cron_create_code_writer_denied(project_root: Path) -> None:
+    """V13 - schtasks/CronCreate-style background code writer must be covered.
+
+    A proper implementation may either DENY because the scheduled action
+    invokes a code-writing script, or explicitly ALLOW with a documented
+    background-scheduler-not-classified reason.
+    """
+    (project_root / "work" / "sync.py").write_text("# sync\n", encoding="utf-8")
+    cmd = 'schtasks /Create /TN x /TR "py -3 work/sync.py"'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    if _parse_deny(r.stdout) is not None:
+        return
+    entry = _latest_skip_ledger_entry(project_root)
+    assert entry.get("decision") == "allow", (
+        f"expected DENY or explicit ALLOW; returncode={r.returncode} "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+    assert entry.get("reason") == "background-scheduler-not-classified", (
+        "expected explicit scheduler gap reason; "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+
+
+def test_v14_mcp_filesystem_write_denied_OR_documented(project_root: Path) -> None:
+    """V14 - MCP filesystem write_file should be denied or treated as a gap."""
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "mcp__filesystem__write_file",
+        "tool_input": {"path": "src/x.py", "content": "print('x')\n"},
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r, must_contain_in_reason="src/x.py")
+
+
+def test_v15_compiled_binary_unknown_classification(project_root: Path) -> None:
+    """V15 - unknown binary mutating a code path must deny, opaque run allows."""
+    r = _run_enforcer(_bash_payload("./my-tool --output src/foo.py"), project_root)
+    _assert_deny(r, must_contain_in_reason="src/foo.py")
+
+    opaque = _run_enforcer(_bash_payload("./my-tool --version"), project_root)
+    _assert_allow(opaque)
+
+
+def test_v16_bash_dash_s_heredoc_requires_cover(project_root: Path) -> None:
+    """V16 - bash -s heredoc is opaque interpreter input and must DENY."""
+    cmd = 'bash -s <<EOF\necho "x" > src/foo.py\nEOF'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_deny(r)
+
+
+def test_v17_python_dash_c_readonly_should_allow_OR_document(
+    project_root: Path,
+) -> None:
+    """V17 - python -c with read-only open(...).read() should ALLOW."""
+    cmd = "python -c \"import json; print(open('config.json').read())\""
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+def test_v18_notebook_bash_magic_denied(project_root: Path) -> None:
+    """V18 - NotebookEdit containing %%bash code-path mutation must DENY."""
+    target = "src/foo.ipynb"
+    (project_root / target).write_text("{}\n", encoding="utf-8")
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "NotebookEdit",
+        "tool_input": {
+            "notebook_path": target,
+            "new_source": "%%bash\necho x > src/y.py",
+        },
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r)
diff --git a/work/criterion-upgrade/Z13-findings.md b/work/criterion-upgrade/Z13-findings.md
new file mode 100644
index 0000000000000000000000000000000000000000..38b585b618ee80901232f87f6ac44c540b74510e
--- /dev/null
+++ b/work/criterion-upgrade/Z13-findings.md
@@ -0,0 +1,17 @@
+# Z13 Findings — Vectors V13-V18 actual enforcer behavior
+
+| # | Vector | Test result | Real gap? | Recommended Z14 fix |
+|---|--------|-------------|-----------|---------------------|
+| V13 | CronCreate | FAIL | yes | Classify `schtasks /Create ... /TR` as scheduler input and recursively inspect the scheduled command, or emit explicit `background-scheduler-not-classified` allow reason. |
+| V14 | MCP filesystem | FAIL | yes | Add MCP write tools such as `mcp__filesystem__write_file` to hook dispatch and extract `path` as a code-write target. |
+| V15 | Compiled binary | FAIL | yes | For unknown executables, require cover when any argument token names a code-extension path, while allowing opaque runs without code-path tokens. |
+| V16 | `bash -s` heredoc | PASS | no | Keep always-cover handling for `bash -s`/stdin-opaque interpreter input. |
+| V17 | `py -c` read-only | PASS | no | Keep read/write-sensitive `python -c` parsing so read-only `open(...).read()` allows. |
+| V18 | Notebook `%%bash` magic | PASS | no | Current NotebookEdit denial covers the `.ipynb`; preserve denial for notebook cells that can mutate code paths. |
+
+## Summary
+
+- Total new tests: 6
+- Currently passing (no real gap): 3
+- Currently failing (real gap, fix in Z14): 3
+- Gaps discovered: V13 scheduler-created background code writers, V14 MCP filesystem writes, V15 unknown compiled binaries with code-path arguments

  ✓ Inspect live attack harness and enforcer classification behavior
  ✓ Add V13-V18 subprocess tests within scoped test file
  ✓ Run live matrix, capture actual V13-V18 results, and write findings
  → Run required regression suites, selftest, and findings existence check
  • Prepare self-report with pass/fail details and commit SHA if available
diff --git a/.claude/hooks/test_enforcer_live_attacks.py b/.claude/hooks/test_enforcer_live_attacks.py
index 33edb22e07bda37eb0c7c86547ba55d2fb030828..c7746a818b893fa8525f5acacd96340cb78d9f81
--- a/.claude/hooks/test_enforcer_live_attacks.py
+++ b/.claude/hooks/test_enforcer_live_attacks.py
@@ -102,22 +102,38 @@
         )
 
 
-def _assert_allow(result: subprocess.CompletedProcess) -> None:
-    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
-    assert result.returncode == 0, (
-        f"unexpected non-zero exit on allow: {result.returncode}; "
-        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
+def _assert_allow(result: subprocess.CompletedProcess) -> None:
+    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
+    assert result.returncode == 0, (
+        f"unexpected non-zero exit on allow: {result.returncode}; "
+        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
     )
     deny = _parse_deny(result.stdout)
-    assert deny is None, (
-        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
-    )
-
+    assert deny is None, (
+        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
+    )
+
+
+def _latest_skip_ledger_entry(project_root: Path) -> dict:
+    """Return the last skip-ledger entry for assertions on allow reasons."""
+    ledger = project_root / "work" / "codex-implementations" / "skip-ledger.jsonl"
+    if not ledger.exists():
+        return {}
+    lines = [line.strip() for line in ledger.read_text(encoding="utf-8").splitlines()
+             if line.strip()]
+    if not lines:
+        return {}
+    try:
+        obj = json.loads(lines[-1])
+    except json.JSONDecodeError:
+        return {}
+    return obj if isinstance(obj, dict) else {}
+
+
+# ----------------------------------------------------------------------
+# Fixtures
+# ----------------------------------------------------------------------
 
-# ----------------------------------------------------------------------
-# Fixtures
-# ----------------------------------------------------------------------
-
 @pytest.fixture
 def project_root(tmp_path: Path) -> Path:
     """Hermetic project root with the dirs the enforcer expects.
@@ -403,14 +419,95 @@
     r = _run_enforcer(_edit_payload(target), project_root)
     _assert_allow(r)
 
-def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
-    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
-
-    .claude/scripts/sync-template-to-target.py is the project's own helper
-    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
+def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
+    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
+
+    .claude/scripts/sync-template-to-target.py is the project's own helper
+    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
     next to codex-ask.py, codex-implement.py, etc. Calling it via py -3 with
     arbitrary CLI args must NOT require a Codex cover.
     """
-    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
-    r = _run_enforcer(_bash_payload(cmd), project_root)
-    _assert_allow(r)
+    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+# ======================================================================
+# DISCOVERY VECTORS (V13-V18) - Z13 expanded live attack matrix
+# ======================================================================
+
+def test_v13_cron_create_code_writer_denied(project_root: Path) -> None:
+    """V13 - schtasks/CronCreate-style background code writer must be covered.
+
+    A proper implementation may either DENY because the scheduled action
+    invokes a code-writing script, or explicitly ALLOW with a documented
+    background-scheduler-not-classified reason.
+    """
+    (project_root / "work" / "sync.py").write_text("# sync\n", encoding="utf-8")
+    cmd = 'schtasks /Create /TN x /TR "py -3 work/sync.py"'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    if _parse_deny(r.stdout) is not None:
+        return
+    entry = _latest_skip_ledger_entry(project_root)
+    assert entry.get("decision") == "allow", (
+        f"expected DENY or explicit ALLOW; returncode={r.returncode} "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+    assert entry.get("reason") == "background-scheduler-not-classified", (
+        "expected explicit scheduler gap reason; "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+
+
+def test_v14_mcp_filesystem_write_denied_OR_documented(project_root: Path) -> None:
+    """V14 - MCP filesystem write_file should be denied or treated as a gap."""
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "mcp__filesystem__write_file",
+        "tool_input": {"path": "src/x.py", "content": "print('x')\n"},
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r, must_contain_in_reason="src/x.py")
+
+
+def test_v15_compiled_binary_unknown_classification(project_root: Path) -> None:
+    """V15 - unknown binary mutating a code path must deny, opaque run allows."""
+    r = _run_enforcer(_bash_payload("./my-tool --output src/foo.py"), project_root)
+    _assert_deny(r, must_contain_in_reason="src/foo.py")
+
+    opaque = _run_enforcer(_bash_payload("./my-tool --version"), project_root)
+    _assert_allow(opaque)
+
+
+def test_v16_bash_dash_s_heredoc_requires_cover(project_root: Path) -> None:
+    """V16 - bash -s heredoc is opaque interpreter input and must DENY."""
+    cmd = 'bash -s <<EOF\necho "x" > src/foo.py\nEOF'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_deny(r)
+
+
+def test_v17_python_dash_c_readonly_should_allow_OR_document(
+    project_root: Path,
+) -> None:
+    """V17 - python -c with read-only open(...).read() should ALLOW."""
+    cmd = "python -c \"import json; print(open('config.json').read())\""
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+def test_v18_notebook_bash_magic_denied(project_root: Path) -> None:
+    """V18 - NotebookEdit containing %%bash code-path mutation must DENY."""
+    target = "src/foo.ipynb"
+    (project_root / target).write_text("{}\n", encoding="utf-8")
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "NotebookEdit",
+        "tool_input": {
+            "notebook_path": target,
+            "new_source": "%%bash\necho x > src/y.py",
+        },
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r)
diff --git a/work/criterion-upgrade/Z13-findings.md b/work/criterion-upgrade/Z13-findings.md
new file mode 100644
index 0000000000000000000000000000000000000000..38b585b618ee80901232f87f6ac44c540b74510e
--- /dev/null
+++ b/work/criterion-upgrade/Z13-findings.md
@@ -0,0 +1,17 @@
+# Z13 Findings — Vectors V13-V18 actual enforcer behavior
+
+| # | Vector | Test result | Real gap? | Recommended Z14 fix |
+|---|--------|-------------|-----------|---------------------|
+| V13 | CronCreate | FAIL | yes | Classify `schtasks /Create ... /TR` as scheduler input and recursively inspect the scheduled command, or emit explicit `background-scheduler-not-classified` allow reason. |
+| V14 | MCP filesystem | FAIL | yes | Add MCP write tools such as `mcp__filesystem__write_file` to hook dispatch and extract `path` as a code-write target. |
+| V15 | Compiled binary | FAIL | yes | For unknown executables, require cover when any argument token names a code-extension path, while allowing opaque runs without code-path tokens. |
+| V16 | `bash -s` heredoc | PASS | no | Keep always-cover handling for `bash -s`/stdin-opaque interpreter input. |
+| V17 | `py -c` read-only | PASS | no | Keep read/write-sensitive `python -c` parsing so read-only `open(...).read()` allows. |
+| V18 | Notebook `%%bash` magic | PASS | no | Current NotebookEdit denial covers the `.ipynb`; preserve denial for notebook cells that can mutate code paths. |
+
+## Summary
+
+- Total new tests: 6
+- Currently passing (no real gap): 3
+- Currently failing (real gap, fix in Z14): 3
+- Gaps discovered: V13 scheduler-created background code writers, V14 MCP filesystem writes, V15 unknown compiled binaries with code-path arguments

codex
The findings file is now created with the 3 passing and 3 failing new vectors. Next I’m running the unrelated regression suites; these must stay green because this task only expands tests and documentation.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
 succeeded in 8982ms:
........................................................................ [ 28%]
........................................................................ [ 57%]
........................................................................ [ 86%]
.................................                                        [100%]
============================== warnings summary ===============================
.claude\scripts\judge_axes.py:46
  C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix\.claude\scripts\judge_axes.py:46: PytestCollectionWarning: cannot collect test class 'TestRun' because it has a __init__ constructor (from: .claude/scripts/test_judge.py)
    @dataclass

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
249 passed, 1 warning in 8.30s

diff --git a/.claude/hooks/test_enforcer_live_attacks.py b/.claude/hooks/test_enforcer_live_attacks.py
index 33edb22e07bda37eb0c7c86547ba55d2fb030828..c7746a818b893fa8525f5acacd96340cb78d9f81
--- a/.claude/hooks/test_enforcer_live_attacks.py
+++ b/.claude/hooks/test_enforcer_live_attacks.py
@@ -102,22 +102,38 @@
         )
 
 
-def _assert_allow(result: subprocess.CompletedProcess) -> None:
-    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
-    assert result.returncode == 0, (
-        f"unexpected non-zero exit on allow: {result.returncode}; "
-        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
+def _assert_allow(result: subprocess.CompletedProcess) -> None:
+    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
+    assert result.returncode == 0, (
+        f"unexpected non-zero exit on allow: {result.returncode}; "
+        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
     )
     deny = _parse_deny(result.stdout)
-    assert deny is None, (
-        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
-    )
-
+    assert deny is None, (
+        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
+    )
+
+
+def _latest_skip_ledger_entry(project_root: Path) -> dict:
+    """Return the last skip-ledger entry for assertions on allow reasons."""
+    ledger = project_root / "work" / "codex-implementations" / "skip-ledger.jsonl"
+    if not ledger.exists():
+        return {}
+    lines = [line.strip() for line in ledger.read_text(encoding="utf-8").splitlines()
+             if line.strip()]
+    if not lines:
+        return {}
+    try:
+        obj = json.loads(lines[-1])
+    except json.JSONDecodeError:
+        return {}
+    return obj if isinstance(obj, dict) else {}
+
+
+# ----------------------------------------------------------------------
+# Fixtures
+# ----------------------------------------------------------------------
 
-# ----------------------------------------------------------------------
-# Fixtures
-# ----------------------------------------------------------------------
-
 @pytest.fixture
 def project_root(tmp_path: Path) -> Path:
     """Hermetic project root with the dirs the enforcer expects.
@@ -403,14 +419,95 @@
     r = _run_enforcer(_edit_payload(target), project_root)
     _assert_allow(r)
 
-def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
-    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
-
-    .claude/scripts/sync-template-to-target.py is the project's own helper
-    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
+def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
+    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
+
+    .claude/scripts/sync-template-to-target.py is the project's own helper
+    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
     next to codex-ask.py, codex-implement.py, etc. Calling it via py -3 with
     arbitrary CLI args must NOT require a Codex cover.
     """
-    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
-    r = _run_enforcer(_bash_payload(cmd), project_root)
-    _assert_allow(r)
+    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+# ======================================================================
+# DISCOVERY VECTORS (V13-V18) - Z13 expanded live attack matrix
+# ======================================================================
+
+def test_v13_cron_create_code_writer_denied(project_root: Path) -> None:
+    """V13 - schtasks/CronCreate-style background code writer must be covered.
+
+    A proper implementation may either DENY because the scheduled action
+    invokes a code-writing script, or explicitly ALLOW with a documented
+    background-scheduler-not-classified reason.
+    """
+    (project_root / "work" / "sync.py").write_text("# sync\n", encoding="utf-8")
+    cmd = 'schtasks /Create /TN x /TR "py -3 work/sync.py"'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    if _parse_deny(r.stdout) is not None:
+        return
+    entry = _latest_skip_ledger_entry(project_root)
+    assert entry.get("decision") == "allow", (
+        f"expected DENY or explicit ALLOW; returncode={r.returncode} "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+    assert entry.get("reason") == "background-scheduler-not-classified", (
+        "expected explicit scheduler gap reason; "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+
+
+def test_v14_mcp_filesystem_write_denied_OR_documented(project_root: Path) -> None:
+    """V14 - MCP filesystem write_file should be denied or treated as a gap."""
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "mcp__filesystem__write_file",
+        "tool_input": {"path": "src/x.py", "content": "print('x')\n"},
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r, must_contain_in_reason="src/x.py")
+
+
+def test_v15_compiled_binary_unknown_classification(project_root: Path) -> None:
+    """V15 - unknown binary mutating a code path must deny, opaque run allows."""
+    r = _run_enforcer(_bash_payload("./my-tool --output src/foo.py"), project_root)
+    _assert_deny(r, must_contain_in_reason="src/foo.py")
+
+    opaque = _run_enforcer(_bash_payload("./my-tool --version"), project_root)
+    _assert_allow(opaque)
+
+
+def test_v16_bash_dash_s_heredoc_requires_cover(project_root: Path) -> None:
+    """V16 - bash -s heredoc is opaque interpreter input and must DENY."""
+    cmd = 'bash -s <<EOF\necho "x" > src/foo.py\nEOF'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_deny(r)
+
+
+def test_v17_python_dash_c_readonly_should_allow_OR_document(
+    project_root: Path,
+) -> None:
+    """V17 - python -c with read-only open(...).read() should ALLOW."""
+    cmd = "python -c \"import json; print(open('config.json').read())\""
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+def test_v18_notebook_bash_magic_denied(project_root: Path) -> None:
+    """V18 - NotebookEdit containing %%bash code-path mutation must DENY."""
+    target = "src/foo.ipynb"
+    (project_root / target).write_text("{}\n", encoding="utf-8")
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "NotebookEdit",
+        "tool_input": {
+            "notebook_path": target,
+            "new_source": "%%bash\necho x > src/y.py",
+        },
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r)
diff --git a/work/criterion-upgrade/Z13-findings.md b/work/criterion-upgrade/Z13-findings.md
new file mode 100644
index 0000000000000000000000000000000000000000..38b585b618ee80901232f87f6ac44c540b74510e
--- /dev/null
+++ b/work/criterion-upgrade/Z13-findings.md
@@ -0,0 +1,17 @@
+# Z13 Findings — Vectors V13-V18 actual enforcer behavior
+
+| # | Vector | Test result | Real gap? | Recommended Z14 fix |
+|---|--------|-------------|-----------|---------------------|
+| V13 | CronCreate | FAIL | yes | Classify `schtasks /Create ... /TR` as scheduler input and recursively inspect the scheduled command, or emit explicit `background-scheduler-not-classified` allow reason. |
+| V14 | MCP filesystem | FAIL | yes | Add MCP write tools such as `mcp__filesystem__write_file` to hook dispatch and extract `path` as a code-write target. |
+| V15 | Compiled binary | FAIL | yes | For unknown executables, require cover when any argument token names a code-extension path, while allowing opaque runs without code-path tokens. |
+| V16 | `bash -s` heredoc | PASS | no | Keep always-cover handling for `bash -s`/stdin-opaque interpreter input. |
+| V17 | `py -c` read-only | PASS | no | Keep read/write-sensitive `python -c` parsing so read-only `open(...).read()` allows. |
+| V18 | Notebook `%%bash` magic | PASS | no | Current NotebookEdit denial covers the `.ipynb`; preserve denial for notebook cells that can mutate code paths. |
+
+## Summary
+
+- Total new tests: 6
+- Currently passing (no real gap): 3
+- Currently failing (real gap, fix in Z14): 3
+- Gaps discovered: V13 scheduler-created background code writers, V14 MCP filesystem writes, V15 unknown compiled binaries with code-path arguments

codex
The regression suite is green: 249 passed with one existing pytest collection warning. I’m running the dual-teams selftest next, then the explicit findings-file existence check.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python .claude/scripts/dual-teams-selftest.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
 succeeded in 883ms:
[PASS] preflight-clean-with-sentinel-V1                     (71 ms)
[PASS] preflight-clean-with-sentinel-V2                     (65 ms)
[PASS] is_dual_teams_worktree-true-on-V1                    ( 1 ms)
[PASS] is_dual_teams_worktree-true-on-V2                    ( 1 ms)
[PASS] judge-axes-sees-claude-committed-py                  (34 ms)
[PASS] judge-axes-sees-codex-untracked-py                   (54 ms)
selftest: 6 checks, 6 passed, 0 failed (660 ms)
{"json_output": false, "keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: main", "ts": "2026-04-26T14:49:25.082741+00:00"}
{"keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: run_selftest", "ts": "2026-04-26T14:49:25.082741+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: setup_transient_repo", "tmpdir": "C:\\Users\\Lenovo\\AppData\\Local\\Temp\\dual-teams-selftest-8xx1bav3", "ts": "2026-04-26T14:49:25.084737+00:00"}
{"base_sha": "b0b220eed5321914e158b8c221fb174529e7e47c", "duration_ms": 300, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: setup_transient_repo", "ts": "2026-04-26T14:49:25.383775+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: load_integrations", "project_root": "C:\\Bots\\Migrator bots\\claude-project-template-update\\worktrees\\criterion-upgrade-z13\\codex\\task-Z13-expand-attack-matrix", "ts": "2026-04-26T14:49:25.384776+00:00"}
{"duration_ms": 5, "failures": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: load_integrations", "ts": "2026-04-26T14:49:25.389770+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: build_results", "ts": "2026-04-26T14:49:25.389770+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T14:49:25.389770+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "detail": "git status --porcelain empty", "duration_ms": 71, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T14:49:25.461129+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T14:49:25.461129+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "detail": "git status --porcelain empty", "duration_ms": 65, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T14:49:25.526375+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T14:49:25.526896+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T14:49:25.526896+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T14:49:25.526896+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T14:49:25.526896+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T14:49:25.614074+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "detail": "saw claude_probe.py", "duration_ms": 34, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T14:49:25.648779+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T14:49:25.648779+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "detail": "saw codex_probe.py", "duration_ms": 54, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T14:49:25.702732+00:00"}
{"checks": 6, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: build_results", "ts": "2026-04-26T14:49:25.702732+00:00"}
{"checks": 6, "duration_ms": 660, "failed": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: run_selftest", "passed": 6, "ts": "2026-04-26T14:49:25.743474+00:00"}
{"exit_code": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: main", "ts": "2026-04-26T14:49:25.743474+00:00"}

diff --git a/.claude/hooks/test_enforcer_live_attacks.py b/.claude/hooks/test_enforcer_live_attacks.py
index 33edb22e07bda37eb0c7c86547ba55d2fb030828..c7746a818b893fa8525f5acacd96340cb78d9f81
--- a/.claude/hooks/test_enforcer_live_attacks.py
+++ b/.claude/hooks/test_enforcer_live_attacks.py
@@ -102,22 +102,38 @@
         )
 
 
-def _assert_allow(result: subprocess.CompletedProcess) -> None:
-    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
-    assert result.returncode == 0, (
-        f"unexpected non-zero exit on allow: {result.returncode}; "
-        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
+def _assert_allow(result: subprocess.CompletedProcess) -> None:
+    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
+    assert result.returncode == 0, (
+        f"unexpected non-zero exit on allow: {result.returncode}; "
+        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
     )
     deny = _parse_deny(result.stdout)
-    assert deny is None, (
-        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
-    )
-
+    assert deny is None, (
+        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
+    )
+
+
+def _latest_skip_ledger_entry(project_root: Path) -> dict:
+    """Return the last skip-ledger entry for assertions on allow reasons."""
+    ledger = project_root / "work" / "codex-implementations" / "skip-ledger.jsonl"
+    if not ledger.exists():
+        return {}
+    lines = [line.strip() for line in ledger.read_text(encoding="utf-8").splitlines()
+             if line.strip()]
+    if not lines:
+        return {}
+    try:
+        obj = json.loads(lines[-1])
+    except json.JSONDecodeError:
+        return {}
+    return obj if isinstance(obj, dict) else {}
+
+
+# ----------------------------------------------------------------------
+# Fixtures
+# ----------------------------------------------------------------------
 
-# ----------------------------------------------------------------------
-# Fixtures
-# ----------------------------------------------------------------------
-
 @pytest.fixture
 def project_root(tmp_path: Path) -> Path:
     """Hermetic project root with the dirs the enforcer expects.
@@ -403,14 +419,95 @@
     r = _run_enforcer(_edit_payload(target), project_root)
     _assert_allow(r)
 
-def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
-    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
-
-    .claude/scripts/sync-template-to-target.py is the project's own helper
-    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
+def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
+    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
+
+    .claude/scripts/sync-template-to-target.py is the project's own helper
+    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
     next to codex-ask.py, codex-implement.py, etc. Calling it via py -3 with
     arbitrary CLI args must NOT require a Codex cover.
     """
-    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
-    r = _run_enforcer(_bash_payload(cmd), project_root)
-    _assert_allow(r)
+    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+# ======================================================================
+# DISCOVERY VECTORS (V13-V18) - Z13 expanded live attack matrix
+# ======================================================================
+
+def test_v13_cron_create_code_writer_denied(project_root: Path) -> None:
+    """V13 - schtasks/CronCreate-style background code writer must be covered.
+
+    A proper implementation may either DENY because the scheduled action
+    invokes a code-writing script, or explicitly ALLOW with a documented
+    background-scheduler-not-classified reason.
+    """
+    (project_root / "work" / "sync.py").write_text("# sync\n", encoding="utf-8")
+    cmd = 'schtasks /Create /TN x /TR "py -3 work/sync.py"'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    if _parse_deny(r.stdout) is not None:
+        return
+    entry = _latest_skip_ledger_entry(project_root)
+    assert entry.get("decision") == "allow", (
+        f"expected DENY or explicit ALLOW; returncode={r.returncode} "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+    assert entry.get("reason") == "background-scheduler-not-classified", (
+        "expected explicit scheduler gap reason; "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+
+
+def test_v14_mcp_filesystem_write_denied_OR_documented(project_root: Path) -> None:
+    """V14 - MCP filesystem write_file should be denied or treated as a gap."""
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "mcp__filesystem__write_file",
+        "tool_input": {"path": "src/x.py", "content": "print('x')\n"},
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r, must_contain_in_reason="src/x.py")
+
+
+def test_v15_compiled_binary_unknown_classification(project_root: Path) -> None:
+    """V15 - unknown binary mutating a code path must deny, opaque run allows."""
+    r = _run_enforcer(_bash_payload("./my-tool --output src/foo.py"), project_root)
+    _assert_deny(r, must_contain_in_reason="src/foo.py")
+
+    opaque = _run_enforcer(_bash_payload("./my-tool --version"), project_root)
+    _assert_allow(opaque)
+
+
+def test_v16_bash_dash_s_heredoc_requires_cover(project_root: Path) -> None:
+    """V16 - bash -s heredoc is opaque interpreter input and must DENY."""
+    cmd = 'bash -s <<EOF\necho "x" > src/foo.py\nEOF'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_deny(r)
+
+
+def test_v17_python_dash_c_readonly_should_allow_OR_document(
+    project_root: Path,
+) -> None:
+    """V17 - python -c with read-only open(...).read() should ALLOW."""
+    cmd = "python -c \"import json; print(open('config.json').read())\""
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+def test_v18_notebook_bash_magic_denied(project_root: Path) -> None:
+    """V18 - NotebookEdit containing %%bash code-path mutation must DENY."""
+    target = "src/foo.ipynb"
+    (project_root / target).write_text("{}\n", encoding="utf-8")
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "NotebookEdit",
+        "tool_input": {
+            "notebook_path": target,
+            "new_source": "%%bash\necho x > src/y.py",
+        },
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r)
diff --git a/work/criterion-upgrade/Z13-findings.md b/work/criterion-upgrade/Z13-findings.md
new file mode 100644
index 0000000000000000000000000000000000000000..38b585b618ee80901232f87f6ac44c540b74510e
--- /dev/null
+++ b/work/criterion-upgrade/Z13-findings.md
@@ -0,0 +1,17 @@
+# Z13 Findings — Vectors V13-V18 actual enforcer behavior
+
+| # | Vector | Test result | Real gap? | Recommended Z14 fix |
+|---|--------|-------------|-----------|---------------------|
+| V13 | CronCreate | FAIL | yes | Classify `schtasks /Create ... /TR` as scheduler input and recursively inspect the scheduled command, or emit explicit `background-scheduler-not-classified` allow reason. |
+| V14 | MCP filesystem | FAIL | yes | Add MCP write tools such as `mcp__filesystem__write_file` to hook dispatch and extract `path` as a code-write target. |
+| V15 | Compiled binary | FAIL | yes | For unknown executables, require cover when any argument token names a code-extension path, while allowing opaque runs without code-path tokens. |
+| V16 | `bash -s` heredoc | PASS | no | Keep always-cover handling for `bash -s`/stdin-opaque interpreter input. |
+| V17 | `py -c` read-only | PASS | no | Keep read/write-sensitive `python -c` parsing so read-only `open(...).read()` allows. |
+| V18 | Notebook `%%bash` magic | PASS | no | Current NotebookEdit denial covers the `.ipynb`; preserve denial for notebook cells that can mutate code paths. |
+
+## Summary
+
+- Total new tests: 6
+- Currently passing (no real gap): 3
+- Currently failing (real gap, fix in Z14): 3
+- Gaps discovered: V13 scheduler-created background code writers, V14 MCP filesystem writes, V15 unknown compiled binaries with code-path arguments

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'bash -lc "test -f work/criterion-upgrade/Z13-findings.md && echo OK"' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
 succeeded in 589ms:
OK

diff --git a/.claude/hooks/test_enforcer_live_attacks.py b/.claude/hooks/test_enforcer_live_attacks.py
index 33edb22e07bda37eb0c7c86547ba55d2fb030828..c7746a818b893fa8525f5acacd96340cb78d9f81
--- a/.claude/hooks/test_enforcer_live_attacks.py
+++ b/.claude/hooks/test_enforcer_live_attacks.py
@@ -102,22 +102,38 @@
         )
 
 
-def _assert_allow(result: subprocess.CompletedProcess) -> None:
-    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
-    assert result.returncode == 0, (
-        f"unexpected non-zero exit on allow: {result.returncode}; "
-        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
+def _assert_allow(result: subprocess.CompletedProcess) -> None:
+    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
+    assert result.returncode == 0, (
+        f"unexpected non-zero exit on allow: {result.returncode}; "
+        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
     )
     deny = _parse_deny(result.stdout)
-    assert deny is None, (
-        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
-    )
-
+    assert deny is None, (
+        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
+    )
+
+
+def _latest_skip_ledger_entry(project_root: Path) -> dict:
+    """Return the last skip-ledger entry for assertions on allow reasons."""
+    ledger = project_root / "work" / "codex-implementations" / "skip-ledger.jsonl"
+    if not ledger.exists():
+        return {}
+    lines = [line.strip() for line in ledger.read_text(encoding="utf-8").splitlines()
+             if line.strip()]
+    if not lines:
+        return {}
+    try:
+        obj = json.loads(lines[-1])
+    except json.JSONDecodeError:
+        return {}
+    return obj if isinstance(obj, dict) else {}
+
+
+# ----------------------------------------------------------------------
+# Fixtures
+# ----------------------------------------------------------------------
 
-# ----------------------------------------------------------------------
-# Fixtures
-# ----------------------------------------------------------------------
-
 @pytest.fixture
 def project_root(tmp_path: Path) -> Path:
     """Hermetic project root with the dirs the enforcer expects.
@@ -403,14 +419,95 @@
     r = _run_enforcer(_edit_payload(target), project_root)
     _assert_allow(r)
 
-def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
-    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
-
-    .claude/scripts/sync-template-to-target.py is the project's own helper
-    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
+def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
+    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
+
+    .claude/scripts/sync-template-to-target.py is the project's own helper
+    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
     next to codex-ask.py, codex-implement.py, etc. Calling it via py -3 with
     arbitrary CLI args must NOT require a Codex cover.
     """
-    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
-    r = _run_enforcer(_bash_payload(cmd), project_root)
-    _assert_allow(r)
+    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+# ======================================================================
+# DISCOVERY VECTORS (V13-V18) - Z13 expanded live attack matrix
+# ======================================================================
+
+def test_v13_cron_create_code_writer_denied(project_root: Path) -> None:
+    """V13 - schtasks/CronCreate-style background code writer must be covered.
+
+    A proper implementation may either DENY because the scheduled action
+    invokes a code-writing script, or explicitly ALLOW with a documented
+    background-scheduler-not-classified reason.
+    """
+    (project_root / "work" / "sync.py").write_text("# sync\n", encoding="utf-8")
+    cmd = 'schtasks /Create /TN x /TR "py -3 work/sync.py"'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    if _parse_deny(r.stdout) is not None:
+        return
+    entry = _latest_skip_ledger_entry(project_root)
+    assert entry.get("decision") == "allow", (
+        f"expected DENY or explicit ALLOW; returncode={r.returncode} "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+    assert entry.get("reason") == "background-scheduler-not-classified", (
+        "expected explicit scheduler gap reason; "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+
+
+def test_v14_mcp_filesystem_write_denied_OR_documented(project_root: Path) -> None:
+    """V14 - MCP filesystem write_file should be denied or treated as a gap."""
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "mcp__filesystem__write_file",
+        "tool_input": {"path": "src/x.py", "content": "print('x')\n"},
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r, must_contain_in_reason="src/x.py")
+
+
+def test_v15_compiled_binary_unknown_classification(project_root: Path) -> None:
+    """V15 - unknown binary mutating a code path must deny, opaque run allows."""
+    r = _run_enforcer(_bash_payload("./my-tool --output src/foo.py"), project_root)
+    _assert_deny(r, must_contain_in_reason="src/foo.py")
+
+    opaque = _run_enforcer(_bash_payload("./my-tool --version"), project_root)
+    _assert_allow(opaque)
+
+
+def test_v16_bash_dash_s_heredoc_requires_cover(project_root: Path) -> None:
+    """V16 - bash -s heredoc is opaque interpreter input and must DENY."""
+    cmd = 'bash -s <<EOF\necho "x" > src/foo.py\nEOF'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_deny(r)
+
+
+def test_v17_python_dash_c_readonly_should_allow_OR_document(
+    project_root: Path,
+) -> None:
+    """V17 - python -c with read-only open(...).read() should ALLOW."""
+    cmd = "python -c \"import json; print(open('config.json').read())\""
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+def test_v18_notebook_bash_magic_denied(project_root: Path) -> None:
+    """V18 - NotebookEdit containing %%bash code-path mutation must DENY."""
+    target = "src/foo.ipynb"
+    (project_root / target).write_text("{}\n", encoding="utf-8")
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "NotebookEdit",
+        "tool_input": {
+            "notebook_path": target,
+            "new_source": "%%bash\necho x > src/y.py",
+        },
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r)
diff --git a/work/criterion-upgrade/Z13-findings.md b/work/criterion-upgrade/Z13-findings.md
new file mode 100644
index 0000000000000000000000000000000000000000..38b585b618ee80901232f87f6ac44c540b74510e
--- /dev/null
+++ b/work/criterion-upgrade/Z13-findings.md
@@ -0,0 +1,17 @@
+# Z13 Findings — Vectors V13-V18 actual enforcer behavior
+
+| # | Vector | Test result | Real gap? | Recommended Z14 fix |
+|---|--------|-------------|-----------|---------------------|
+| V13 | CronCreate | FAIL | yes | Classify `schtasks /Create ... /TR` as scheduler input and recursively inspect the scheduled command, or emit explicit `background-scheduler-not-classified` allow reason. |
+| V14 | MCP filesystem | FAIL | yes | Add MCP write tools such as `mcp__filesystem__write_file` to hook dispatch and extract `path` as a code-write target. |
+| V15 | Compiled binary | FAIL | yes | For unknown executables, require cover when any argument token names a code-extension path, while allowing opaque runs without code-path tokens. |
+| V16 | `bash -s` heredoc | PASS | no | Keep always-cover handling for `bash -s`/stdin-opaque interpreter input. |
+| V17 | `py -c` read-only | PASS | no | Keep read/write-sensitive `python -c` parsing so read-only `open(...).read()` allows. |
+| V18 | Notebook `%%bash` magic | PASS | no | Current NotebookEdit denial covers the `.ipynb`; preserve denial for notebook cells that can mutate code paths. |
+
+## Summary
+
+- Total new tests: 6
+- Currently passing (no real gap): 3
+- Currently failing (real gap, fix in Z14): 3
+- Gaps discovered: V13 scheduler-created background code writers, V14 MCP filesystem writes, V15 unknown compiled binaries with code-path arguments

codex
Selftest passed 6/6 and the findings existence check returned `OK`. I’m checking the diff now to verify only the two scoped paths changed before I prepare the final self-report and commit SHA.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff -- .claude/hooks/test_enforcer_live_attacks.py work/criterion-upgrade/Z13-findings.md' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git ls-files --others --exclude-standard' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
 succeeded in 165ms:
 M .claude/hooks/test_enforcer_live_attacks.py
?? work/criterion-upgrade/Z13-findings.md

 succeeded in 165ms:
diff --git a/.claude/hooks/test_enforcer_live_attacks.py b/.claude/hooks/test_enforcer_live_attacks.py
index 33edb22..c7746a8 100644
--- a/.claude/hooks/test_enforcer_live_attacks.py
+++ b/.claude/hooks/test_enforcer_live_attacks.py
@@ -114,6 +114,22 @@ def _assert_allow(result: subprocess.CompletedProcess) -> None:
     )
 
 
+def _latest_skip_ledger_entry(project_root: Path) -> dict:
+    """Return the last skip-ledger entry for assertions on allow reasons."""
+    ledger = project_root / "work" / "codex-implementations" / "skip-ledger.jsonl"
+    if not ledger.exists():
+        return {}
+    lines = [line.strip() for line in ledger.read_text(encoding="utf-8").splitlines()
+             if line.strip()]
+    if not lines:
+        return {}
+    try:
+        obj = json.loads(lines[-1])
+    except json.JSONDecodeError:
+        return {}
+    return obj if isinstance(obj, dict) else {}
+
+
 # ----------------------------------------------------------------------
 # Fixtures
 # ----------------------------------------------------------------------
@@ -414,3 +430,84 @@ def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
     cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
     r = _run_enforcer(_bash_payload(cmd), project_root)
     _assert_allow(r)
+
+
+# ======================================================================
+# DISCOVERY VECTORS (V13-V18) - Z13 expanded live attack matrix
+# ======================================================================
+
+def test_v13_cron_create_code_writer_denied(project_root: Path) -> None:
+    """V13 - schtasks/CronCreate-style background code writer must be covered.
+
+    A proper implementation may either DENY because the scheduled action
+    invokes a code-writing script, or explicitly ALLOW with a documented
+    background-scheduler-not-classified reason.
+    """
+    (project_root / "work" / "sync.py").write_text("# sync\n", encoding="utf-8")
+    cmd = 'schtasks /Create /TN x /TR "py -3 work/sync.py"'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    if _parse_deny(r.stdout) is not None:
+        return
+    entry = _latest_skip_ledger_entry(project_root)
+    assert entry.get("decision") == "allow", (
+        f"expected DENY or explicit ALLOW; returncode={r.returncode} "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+    assert entry.get("reason") == "background-scheduler-not-classified", (
+        "expected explicit scheduler gap reason; "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+
+
+def test_v14_mcp_filesystem_write_denied_OR_documented(project_root: Path) -> None:
+    """V14 - MCP filesystem write_file should be denied or treated as a gap."""
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "mcp__filesystem__write_file",
+        "tool_input": {"path": "src/x.py", "content": "print('x')\n"},
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r, must_contain_in_reason="src/x.py")
+
+
+def test_v15_compiled_binary_unknown_classification(project_root: Path) -> None:
+    """V15 - unknown binary mutating a code path must deny, opaque run allows."""
+    r = _run_enforcer(_bash_payload("./my-tool --output src/foo.py"), project_root)
+    _assert_deny(r, must_contain_in_reason="src/foo.py")
+
+    opaque = _run_enforcer(_bash_payload("./my-tool --version"), project_root)
+    _assert_allow(opaque)
+
+
+def test_v16_bash_dash_s_heredoc_requires_cover(project_root: Path) -> None:
+    """V16 - bash -s heredoc is opaque interpreter input and must DENY."""
+    cmd = 'bash -s <<EOF\necho "x" > src/foo.py\nEOF'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_deny(r)
+
+
+def test_v17_python_dash_c_readonly_should_allow_OR_document(
+    project_root: Path,
+) -> None:
+    """V17 - python -c with read-only open(...).read() should ALLOW."""
+    cmd = "python -c \"import json; print(open('config.json').read())\""
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+def test_v18_notebook_bash_magic_denied(project_root: Path) -> None:
+    """V18 - NotebookEdit containing %%bash code-path mutation must DENY."""
+    target = "src/foo.ipynb"
+    (project_root / target).write_text("{}\n", encoding="utf-8")
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "NotebookEdit",
+        "tool_input": {
+            "notebook_path": target,
+            "new_source": "%%bash\necho x > src/y.py",
+        },
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r)
warning: in the working copy of '.claude/hooks/test_enforcer_live_attacks.py', LF will be replaced by CRLF the next time Git touches it

 succeeded in 171ms:
work/criterion-upgrade/Z13-findings.md

diff --git a/.claude/hooks/test_enforcer_live_attacks.py b/.claude/hooks/test_enforcer_live_attacks.py
index 33edb22e07bda37eb0c7c86547ba55d2fb030828..c7746a818b893fa8525f5acacd96340cb78d9f81
--- a/.claude/hooks/test_enforcer_live_attacks.py
+++ b/.claude/hooks/test_enforcer_live_attacks.py
@@ -102,22 +102,38 @@
         )
 
 
-def _assert_allow(result: subprocess.CompletedProcess) -> None:
-    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
-    assert result.returncode == 0, (
-        f"unexpected non-zero exit on allow: {result.returncode}; "
-        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
+def _assert_allow(result: subprocess.CompletedProcess) -> None:
+    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
+    assert result.returncode == 0, (
+        f"unexpected non-zero exit on allow: {result.returncode}; "
+        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
     )
     deny = _parse_deny(result.stdout)
-    assert deny is None, (
-        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
-    )
-
+    assert deny is None, (
+        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
+    )
+
+
+def _latest_skip_ledger_entry(project_root: Path) -> dict:
+    """Return the last skip-ledger entry for assertions on allow reasons."""
+    ledger = project_root / "work" / "codex-implementations" / "skip-ledger.jsonl"
+    if not ledger.exists():
+        return {}
+    lines = [line.strip() for line in ledger.read_text(encoding="utf-8").splitlines()
+             if line.strip()]
+    if not lines:
+        return {}
+    try:
+        obj = json.loads(lines[-1])
+    except json.JSONDecodeError:
+        return {}
+    return obj if isinstance(obj, dict) else {}
+
+
+# ----------------------------------------------------------------------
+# Fixtures
+# ----------------------------------------------------------------------
 
-# ----------------------------------------------------------------------
-# Fixtures
-# ----------------------------------------------------------------------
-
 @pytest.fixture
 def project_root(tmp_path: Path) -> Path:
     """Hermetic project root with the dirs the enforcer expects.
@@ -403,14 +419,95 @@
     r = _run_enforcer(_edit_payload(target), project_root)
     _assert_allow(r)
 
-def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
-    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
-
-    .claude/scripts/sync-template-to-target.py is the project's own helper
-    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
+def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
+    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
+
+    .claude/scripts/sync-template-to-target.py is the project's own helper
+    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
     next to codex-ask.py, codex-implement.py, etc. Calling it via py -3 with
     arbitrary CLI args must NOT require a Codex cover.
     """
-    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
-    r = _run_enforcer(_bash_payload(cmd), project_root)
-    _assert_allow(r)
+    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+# ======================================================================
+# DISCOVERY VECTORS (V13-V18) - Z13 expanded live attack matrix
+# ======================================================================
+
+def test_v13_cron_create_code_writer_denied(project_root: Path) -> None:
+    """V13 - schtasks/CronCreate-style background code writer must be covered.
+
+    A proper implementation may either DENY because the scheduled action
+    invokes a code-writing script, or explicitly ALLOW with a documented
+    background-scheduler-not-classified reason.
+    """
+    (project_root / "work" / "sync.py").write_text("# sync\n", encoding="utf-8")
+    cmd = 'schtasks /Create /TN x /TR "py -3 work/sync.py"'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    if _parse_deny(r.stdout) is not None:
+        return
+    entry = _latest_skip_ledger_entry(project_root)
+    assert entry.get("decision") == "allow", (
+        f"expected DENY or explicit ALLOW; returncode={r.returncode} "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+    assert entry.get("reason") == "background-scheduler-not-classified", (
+        "expected explicit scheduler gap reason; "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+
+
+def test_v14_mcp_filesystem_write_denied_OR_documented(project_root: Path) -> None:
+    """V14 - MCP filesystem write_file should be denied or treated as a gap."""
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "mcp__filesystem__write_file",
+        "tool_input": {"path": "src/x.py", "content": "print('x')\n"},
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r, must_contain_in_reason="src/x.py")
+
+
+def test_v15_compiled_binary_unknown_classification(project_root: Path) -> None:
+    """V15 - unknown binary mutating a code path must deny, opaque run allows."""
+    r = _run_enforcer(_bash_payload("./my-tool --output src/foo.py"), project_root)
+    _assert_deny(r, must_contain_in_reason="src/foo.py")
+
+    opaque = _run_enforcer(_bash_payload("./my-tool --version"), project_root)
+    _assert_allow(opaque)
+
+
+def test_v16_bash_dash_s_heredoc_requires_cover(project_root: Path) -> None:
+    """V16 - bash -s heredoc is opaque interpreter input and must DENY."""
+    cmd = 'bash -s <<EOF\necho "x" > src/foo.py\nEOF'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_deny(r)
+
+
+def test_v17_python_dash_c_readonly_should_allow_OR_document(
+    project_root: Path,
+) -> None:
+    """V17 - python -c with read-only open(...).read() should ALLOW."""
+    cmd = "python -c \"import json; print(open('config.json').read())\""
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+def test_v18_notebook_bash_magic_denied(project_root: Path) -> None:
+    """V18 - NotebookEdit containing %%bash code-path mutation must DENY."""
+    target = "src/foo.ipynb"
+    (project_root / target).write_text("{}\n", encoding="utf-8")
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "NotebookEdit",
+        "tool_input": {
+            "notebook_path": target,
+            "new_source": "%%bash\necho x > src/y.py",
+        },
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r)
diff --git a/work/criterion-upgrade/Z13-findings.md b/work/criterion-upgrade/Z13-findings.md
new file mode 100644
index 0000000000000000000000000000000000000000..38b585b618ee80901232f87f6ac44c540b74510e
--- /dev/null
+++ b/work/criterion-upgrade/Z13-findings.md
@@ -0,0 +1,17 @@
+# Z13 Findings — Vectors V13-V18 actual enforcer behavior
+
+| # | Vector | Test result | Real gap? | Recommended Z14 fix |
+|---|--------|-------------|-----------|---------------------|
+| V13 | CronCreate | FAIL | yes | Classify `schtasks /Create ... /TR` as scheduler input and recursively inspect the scheduled command, or emit explicit `background-scheduler-not-classified` allow reason. |
+| V14 | MCP filesystem | FAIL | yes | Add MCP write tools such as `mcp__filesystem__write_file` to hook dispatch and extract `path` as a code-write target. |
+| V15 | Compiled binary | FAIL | yes | For unknown executables, require cover when any argument token names a code-extension path, while allowing opaque runs without code-path tokens. |
+| V16 | `bash -s` heredoc | PASS | no | Keep always-cover handling for `bash -s`/stdin-opaque interpreter input. |
+| V17 | `py -c` read-only | PASS | no | Keep read/write-sensitive `python -c` parsing so read-only `open(...).read()` allows. |
+| V18 | Notebook `%%bash` magic | PASS | no | Current NotebookEdit denial covers the `.ipynb`; preserve denial for notebook cells that can mutate code paths. |
+
+## Summary
+
+- Total new tests: 6
+- Currently passing (no real gap): 3
+- Currently failing (real gap, fix in Z14): 3
+- Gaps discovered: V13 scheduler-created background code writers, V14 MCP filesystem writes, V15 unknown compiled binaries with code-path arguments

codex
The diff is limited to the scoped test file plus the new findings markdown. I’m staging just those two files and creating the task commit so the self-report can include an actual SHA.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git add -- .claude/hooks/test_enforcer_live_attacks.py work/criterion-upgrade/Z13-findings.md; git commit -m "test: expand enforcer live attack matrix"' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
 succeeded in 908ms:
[codex-wave/task-Z13-expand-attack-matrix d29a7b6] test: expand enforcer live attack matrix
 2 files changed, 114 insertions(+)
 create mode 100644 work/criterion-upgrade/Z13-findings.md
warning: in the working copy of '.claude/hooks/test_enforcer_live_attacks.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'work/criterion-upgrade/Z13-findings.md', LF will be replaced by CRLF the next time Git touches it
Memory NOT updated. Adding auto-generated entry...
Auto-entry added to memory

diff --git a/.claude/hooks/test_enforcer_live_attacks.py b/.claude/hooks/test_enforcer_live_attacks.py
index 33edb22e07bda37eb0c7c86547ba55d2fb030828..c7746a818b893fa8525f5acacd96340cb78d9f81
--- a/.claude/hooks/test_enforcer_live_attacks.py
+++ b/.claude/hooks/test_enforcer_live_attacks.py
@@ -102,22 +102,38 @@
         )
 
 
-def _assert_allow(result: subprocess.CompletedProcess) -> None:
-    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
-    assert result.returncode == 0, (
-        f"unexpected non-zero exit on allow: {result.returncode}; "
-        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
+def _assert_allow(result: subprocess.CompletedProcess) -> None:
+    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
+    assert result.returncode == 0, (
+        f"unexpected non-zero exit on allow: {result.returncode}; "
+        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
     )
     deny = _parse_deny(result.stdout)
-    assert deny is None, (
-        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
-    )
-
+    assert deny is None, (
+        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
+    )
+
+
+def _latest_skip_ledger_entry(project_root: Path) -> dict:
+    """Return the last skip-ledger entry for assertions on allow reasons."""
+    ledger = project_root / "work" / "codex-implementations" / "skip-ledger.jsonl"
+    if not ledger.exists():
+        return {}
+    lines = [line.strip() for line in ledger.read_text(encoding="utf-8").splitlines()
+             if line.strip()]
+    if not lines:
+        return {}
+    try:
+        obj = json.loads(lines[-1])
+    except json.JSONDecodeError:
+        return {}
+    return obj if isinstance(obj, dict) else {}
+
+
+# ----------------------------------------------------------------------
+# Fixtures
+# ----------------------------------------------------------------------
 
-# ----------------------------------------------------------------------
-# Fixtures
-# ----------------------------------------------------------------------
-
 @pytest.fixture
 def project_root(tmp_path: Path) -> Path:
     """Hermetic project root with the dirs the enforcer expects.
@@ -403,14 +419,95 @@
     r = _run_enforcer(_edit_payload(target), project_root)
     _assert_allow(r)
 
-def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
-    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
-
-    .claude/scripts/sync-template-to-target.py is the project's own helper
-    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
+def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
+    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
+
+    .claude/scripts/sync-template-to-target.py is the project's own helper
+    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
     next to codex-ask.py, codex-implement.py, etc. Calling it via py -3 with
     arbitrary CLI args must NOT require a Codex cover.
     """
-    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
-    r = _run_enforcer(_bash_payload(cmd), project_root)
-    _assert_allow(r)
+    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+# ======================================================================
+# DISCOVERY VECTORS (V13-V18) - Z13 expanded live attack matrix
+# ======================================================================
+
+def test_v13_cron_create_code_writer_denied(project_root: Path) -> None:
+    """V13 - schtasks/CronCreate-style background code writer must be covered.
+
+    A proper implementation may either DENY because the scheduled action
+    invokes a code-writing script, or explicitly ALLOW with a documented
+    background-scheduler-not-classified reason.
+    """
+    (project_root / "work" / "sync.py").write_text("# sync\n", encoding="utf-8")
+    cmd = 'schtasks /Create /TN x /TR "py -3 work/sync.py"'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    if _parse_deny(r.stdout) is not None:
+        return
+    entry = _latest_skip_ledger_entry(project_root)
+    assert entry.get("decision") == "allow", (
+        f"expected DENY or explicit ALLOW; returncode={r.returncode} "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+    assert entry.get("reason") == "background-scheduler-not-classified", (
+        "expected explicit scheduler gap reason; "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+
+
+def test_v14_mcp_filesystem_write_denied_OR_documented(project_root: Path) -> None:
+    """V14 - MCP filesystem write_file should be denied or treated as a gap."""
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "mcp__filesystem__write_file",
+        "tool_input": {"path": "src/x.py", "content": "print('x')\n"},
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r, must_contain_in_reason="src/x.py")
+
+
+def test_v15_compiled_binary_unknown_classification(project_root: Path) -> None:
+    """V15 - unknown binary mutating a code path must deny, opaque run allows."""
+    r = _run_enforcer(_bash_payload("./my-tool --output src/foo.py"), project_root)
+    _assert_deny(r, must_contain_in_reason="src/foo.py")
+
+    opaque = _run_enforcer(_bash_payload("./my-tool --version"), project_root)
+    _assert_allow(opaque)
+
+
+def test_v16_bash_dash_s_heredoc_requires_cover(project_root: Path) -> None:
+    """V16 - bash -s heredoc is opaque interpreter input and must DENY."""
+    cmd = 'bash -s <<EOF\necho "x" > src/foo.py\nEOF'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_deny(r)
+
+
+def test_v17_python_dash_c_readonly_should_allow_OR_document(
+    project_root: Path,
+) -> None:
+    """V17 - python -c with read-only open(...).read() should ALLOW."""
+    cmd = "python -c \"import json; print(open('config.json').read())\""
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+def test_v18_notebook_bash_magic_denied(project_root: Path) -> None:
+    """V18 - NotebookEdit containing %%bash code-path mutation must DENY."""
+    target = "src/foo.ipynb"
+    (project_root / target).write_text("{}\n", encoding="utf-8")
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "NotebookEdit",
+        "tool_input": {
+            "notebook_path": target,
+            "new_source": "%%bash\necho x > src/y.py",
+        },
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r)
diff --git a/work/criterion-upgrade/Z13-findings.md b/work/criterion-upgrade/Z13-findings.md
new file mode 100644
index 0000000000000000000000000000000000000000..38b585b618ee80901232f87f6ac44c540b74510e
--- /dev/null
+++ b/work/criterion-upgrade/Z13-findings.md
@@ -0,0 +1,17 @@
+# Z13 Findings — Vectors V13-V18 actual enforcer behavior
+
+| # | Vector | Test result | Real gap? | Recommended Z14 fix |
+|---|--------|-------------|-----------|---------------------|
+| V13 | CronCreate | FAIL | yes | Classify `schtasks /Create ... /TR` as scheduler input and recursively inspect the scheduled command, or emit explicit `background-scheduler-not-classified` allow reason. |
+| V14 | MCP filesystem | FAIL | yes | Add MCP write tools such as `mcp__filesystem__write_file` to hook dispatch and extract `path` as a code-write target. |
+| V15 | Compiled binary | FAIL | yes | For unknown executables, require cover when any argument token names a code-extension path, while allowing opaque runs without code-path tokens. |
+| V16 | `bash -s` heredoc | PASS | no | Keep always-cover handling for `bash -s`/stdin-opaque interpreter input. |
+| V17 | `py -c` read-only | PASS | no | Keep read/write-sensitive `python -c` parsing so read-only `open(...).read()` allows. |
+| V18 | Notebook `%%bash` magic | PASS | no | Current NotebookEdit denial covers the `.ipynb`; preserve denial for notebook cells that can mutate code paths. |
+
+## Summary
+
+- Total new tests: 6
+- Currently passing (no real gap): 3
+- Currently failing (real gap, fix in Z14): 3
+- Gaps discovered: V13 scheduler-created background code writers, V14 MCP filesystem writes, V15 unknown compiled binaries with code-path arguments

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git rev-parse HEAD' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git show --stat --oneline --name-only HEAD' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
 succeeded in 165ms:
 M .claude/memory/activeContext.md

 succeeded in 165ms:
d29a7b608da825faba467924fd6f302ba7f62e25

 succeeded in 165ms:
d29a7b6 test: expand enforcer live attack matrix
.claude/hooks/test_enforcer_live_attacks.py
work/criterion-upgrade/Z13-findings.md

diff --git a/.claude/hooks/test_enforcer_live_attacks.py b/.claude/hooks/test_enforcer_live_attacks.py
index 33edb22e07bda37eb0c7c86547ba55d2fb030828..c7746a818b893fa8525f5acacd96340cb78d9f81
--- a/.claude/hooks/test_enforcer_live_attacks.py
+++ b/.claude/hooks/test_enforcer_live_attacks.py
@@ -102,22 +102,38 @@
         )
 
 
-def _assert_allow(result: subprocess.CompletedProcess) -> None:
-    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
-    assert result.returncode == 0, (
-        f"unexpected non-zero exit on allow: {result.returncode}; "
-        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
+def _assert_allow(result: subprocess.CompletedProcess) -> None:
+    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
+    assert result.returncode == 0, (
+        f"unexpected non-zero exit on allow: {result.returncode}; "
+        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
     )
     deny = _parse_deny(result.stdout)
-    assert deny is None, (
-        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
-    )
-
+    assert deny is None, (
+        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
+    )
+
+
+def _latest_skip_ledger_entry(project_root: Path) -> dict:
+    """Return the last skip-ledger entry for assertions on allow reasons."""
+    ledger = project_root / "work" / "codex-implementations" / "skip-ledger.jsonl"
+    if not ledger.exists():
+        return {}
+    lines = [line.strip() for line in ledger.read_text(encoding="utf-8").splitlines()
+             if line.strip()]
+    if not lines:
+        return {}
+    try:
+        obj = json.loads(lines[-1])
+    except json.JSONDecodeError:
+        return {}
+    return obj if isinstance(obj, dict) else {}
+
+
+# ----------------------------------------------------------------------
+# Fixtures
+# ----------------------------------------------------------------------
 
-# ----------------------------------------------------------------------
-# Fixtures
-# ----------------------------------------------------------------------
-
 @pytest.fixture
 def project_root(tmp_path: Path) -> Path:
     """Hermetic project root with the dirs the enforcer expects.
@@ -403,14 +419,95 @@
     r = _run_enforcer(_edit_payload(target), project_root)
     _assert_allow(r)
 
-def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
-    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
-
-    .claude/scripts/sync-template-to-target.py is the project's own helper
-    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
+def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
+    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
+
+    .claude/scripts/sync-template-to-target.py is the project's own helper
+    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
     next to codex-ask.py, codex-implement.py, etc. Calling it via py -3 with
     arbitrary CLI args must NOT require a Codex cover.
     """
-    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
-    r = _run_enforcer(_bash_payload(cmd), project_root)
-    _assert_allow(r)
+    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+# ======================================================================
+# DISCOVERY VECTORS (V13-V18) - Z13 expanded live attack matrix
+# ======================================================================
+
+def test_v13_cron_create_code_writer_denied(project_root: Path) -> None:
+    """V13 - schtasks/CronCreate-style background code writer must be covered.
+
+    A proper implementation may either DENY because the scheduled action
+    invokes a code-writing script, or explicitly ALLOW with a documented
+    background-scheduler-not-classified reason.
+    """
+    (project_root / "work" / "sync.py").write_text("# sync\n", encoding="utf-8")
+    cmd = 'schtasks /Create /TN x /TR "py -3 work/sync.py"'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    if _parse_deny(r.stdout) is not None:
+        return
+    entry = _latest_skip_ledger_entry(project_root)
+    assert entry.get("decision") == "allow", (
+        f"expected DENY or explicit ALLOW; returncode={r.returncode} "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+    assert entry.get("reason") == "background-scheduler-not-classified", (
+        "expected explicit scheduler gap reason; "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+
+
+def test_v14_mcp_filesystem_write_denied_OR_documented(project_root: Path) -> None:
+    """V14 - MCP filesystem write_file should be denied or treated as a gap."""
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "mcp__filesystem__write_file",
+        "tool_input": {"path": "src/x.py", "content": "print('x')\n"},
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r, must_contain_in_reason="src/x.py")
+
+
+def test_v15_compiled_binary_unknown_classification(project_root: Path) -> None:
+    """V15 - unknown binary mutating a code path must deny, opaque run allows."""
+    r = _run_enforcer(_bash_payload("./my-tool --output src/foo.py"), project_root)
+    _assert_deny(r, must_contain_in_reason="src/foo.py")
+
+    opaque = _run_enforcer(_bash_payload("./my-tool --version"), project_root)
+    _assert_allow(opaque)
+
+
+def test_v16_bash_dash_s_heredoc_requires_cover(project_root: Path) -> None:
+    """V16 - bash -s heredoc is opaque interpreter input and must DENY."""
+    cmd = 'bash -s <<EOF\necho "x" > src/foo.py\nEOF'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_deny(r)
+
+
+def test_v17_python_dash_c_readonly_should_allow_OR_document(
+    project_root: Path,
+) -> None:
+    """V17 - python -c with read-only open(...).read() should ALLOW."""
+    cmd = "python -c \"import json; print(open('config.json').read())\""
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+def test_v18_notebook_bash_magic_denied(project_root: Path) -> None:
+    """V18 - NotebookEdit containing %%bash code-path mutation must DENY."""
+    target = "src/foo.ipynb"
+    (project_root / target).write_text("{}\n", encoding="utf-8")
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "NotebookEdit",
+        "tool_input": {
+            "notebook_path": target,
+            "new_source": "%%bash\necho x > src/y.py",
+        },
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r)
diff --git a/work/criterion-upgrade/Z13-findings.md b/work/criterion-upgrade/Z13-findings.md
new file mode 100644
index 0000000000000000000000000000000000000000..38b585b618ee80901232f87f6ac44c540b74510e
--- /dev/null
+++ b/work/criterion-upgrade/Z13-findings.md
@@ -0,0 +1,17 @@
+# Z13 Findings — Vectors V13-V18 actual enforcer behavior
+
+| # | Vector | Test result | Real gap? | Recommended Z14 fix |
+|---|--------|-------------|-----------|---------------------|
+| V13 | CronCreate | FAIL | yes | Classify `schtasks /Create ... /TR` as scheduler input and recursively inspect the scheduled command, or emit explicit `background-scheduler-not-classified` allow reason. |
+| V14 | MCP filesystem | FAIL | yes | Add MCP write tools such as `mcp__filesystem__write_file` to hook dispatch and extract `path` as a code-write target. |
+| V15 | Compiled binary | FAIL | yes | For unknown executables, require cover when any argument token names a code-extension path, while allowing opaque runs without code-path tokens. |
+| V16 | `bash -s` heredoc | PASS | no | Keep always-cover handling for `bash -s`/stdin-opaque interpreter input. |
+| V17 | `py -c` read-only | PASS | no | Keep read/write-sensitive `python -c` parsing so read-only `open(...).read()` allows. |
+| V18 | Notebook `%%bash` magic | PASS | no | Current NotebookEdit denial covers the `.ipynb`; preserve denial for notebook cells that can mutate code paths. |
+
+## Summary
+
+- Total new tests: 6
+- Currently passing (no real gap): 3
+- Currently failing (real gap, fix in Z14): 3
+- Gaps discovered: V13 scheduler-created background code writers, V14 MCP filesystem writes, V15 unknown compiled binaries with code-path arguments

codex
The commit succeeded, but the repository hook auto-wrote `.claude/memory/activeContext.md` after the commit. That file is outside this task’s scope, so I’m inspecting that unintended post-commit change and will clean it up if it is only the hook’s generated entry.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff -- .claude/memory/activeContext.md' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
 succeeded in 179ms:
diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index df1de9d..92d8fe9 100644
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,6 +620,11 @@ pipeline-checkpoint-PLAN в†’ IMPLEMENT_WAVE_1 в†’ IMPLEMENT_WAVE_2 в
 
 ## Auto-Generated Summaries
 
+### 2026-04-26 17:49 (commit `d29a7b6`)
+**Message:** test: expand enforcer live attack matrix
+**Files:** 2
+
+
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
warning: in the working copy of '.claude/memory/activeContext.md', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/hooks/test_enforcer_live_attacks.py b/.claude/hooks/test_enforcer_live_attacks.py
index 33edb22e07bda37eb0c7c86547ba55d2fb030828..c7746a818b893fa8525f5acacd96340cb78d9f81
--- a/.claude/hooks/test_enforcer_live_attacks.py
+++ b/.claude/hooks/test_enforcer_live_attacks.py
@@ -102,22 +102,38 @@
         )
 
 
-def _assert_allow(result: subprocess.CompletedProcess) -> None:
-    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
-    assert result.returncode == 0, (
-        f"unexpected non-zero exit on allow: {result.returncode}; "
-        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
+def _assert_allow(result: subprocess.CompletedProcess) -> None:
+    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
+    assert result.returncode == 0, (
+        f"unexpected non-zero exit on allow: {result.returncode}; "
+        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
     )
     deny = _parse_deny(result.stdout)
-    assert deny is None, (
-        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
-    )
-
+    assert deny is None, (
+        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
+    )
+
+
+def _latest_skip_ledger_entry(project_root: Path) -> dict:
+    """Return the last skip-ledger entry for assertions on allow reasons."""
+    ledger = project_root / "work" / "codex-implementations" / "skip-ledger.jsonl"
+    if not ledger.exists():
+        return {}
+    lines = [line.strip() for line in ledger.read_text(encoding="utf-8").splitlines()
+             if line.strip()]
+    if not lines:
+        return {}
+    try:
+        obj = json.loads(lines[-1])
+    except json.JSONDecodeError:
+        return {}
+    return obj if isinstance(obj, dict) else {}
+
+
+# ----------------------------------------------------------------------
+# Fixtures
+# ----------------------------------------------------------------------
 
-# ----------------------------------------------------------------------
-# Fixtures
-# ----------------------------------------------------------------------
-
 @pytest.fixture
 def project_root(tmp_path: Path) -> Path:
     """Hermetic project root with the dirs the enforcer expects.
@@ -403,14 +419,95 @@
     r = _run_enforcer(_edit_payload(target), project_root)
     _assert_allow(r)
 
-def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
-    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
-
-    .claude/scripts/sync-template-to-target.py is the project's own helper
-    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
+def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
+    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
+
+    .claude/scripts/sync-template-to-target.py is the project's own helper
+    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
     next to codex-ask.py, codex-implement.py, etc. Calling it via py -3 with
     arbitrary CLI args must NOT require a Codex cover.
     """
-    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
-    r = _run_enforcer(_bash_payload(cmd), project_root)
-    _assert_allow(r)
+    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+# ======================================================================
+# DISCOVERY VECTORS (V13-V18) - Z13 expanded live attack matrix
+# ======================================================================
+
+def test_v13_cron_create_code_writer_denied(project_root: Path) -> None:
+    """V13 - schtasks/CronCreate-style background code writer must be covered.
+
+    A proper implementation may either DENY because the scheduled action
+    invokes a code-writing script, or explicitly ALLOW with a documented
+    background-scheduler-not-classified reason.
+    """
+    (project_root / "work" / "sync.py").write_text("# sync\n", encoding="utf-8")
+    cmd = 'schtasks /Create /TN x /TR "py -3 work/sync.py"'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    if _parse_deny(r.stdout) is not None:
+        return
+    entry = _latest_skip_ledger_entry(project_root)
+    assert entry.get("decision") == "allow", (
+        f"expected DENY or explicit ALLOW; returncode={r.returncode} "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+    assert entry.get("reason") == "background-scheduler-not-classified", (
+        "expected explicit scheduler gap reason; "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+
+
+def test_v14_mcp_filesystem_write_denied_OR_documented(project_root: Path) -> None:
+    """V14 - MCP filesystem write_file should be denied or treated as a gap."""
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "mcp__filesystem__write_file",
+        "tool_input": {"path": "src/x.py", "content": "print('x')\n"},
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r, must_contain_in_reason="src/x.py")
+
+
+def test_v15_compiled_binary_unknown_classification(project_root: Path) -> None:
+    """V15 - unknown binary mutating a code path must deny, opaque run allows."""
+    r = _run_enforcer(_bash_payload("./my-tool --output src/foo.py"), project_root)
+    _assert_deny(r, must_contain_in_reason="src/foo.py")
+
+    opaque = _run_enforcer(_bash_payload("./my-tool --version"), project_root)
+    _assert_allow(opaque)
+
+
+def test_v16_bash_dash_s_heredoc_requires_cover(project_root: Path) -> None:
+    """V16 - bash -s heredoc is opaque interpreter input and must DENY."""
+    cmd = 'bash -s <<EOF\necho "x" > src/foo.py\nEOF'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_deny(r)
+
+
+def test_v17_python_dash_c_readonly_should_allow_OR_document(
+    project_root: Path,
+) -> None:
+    """V17 - python -c with read-only open(...).read() should ALLOW."""
+    cmd = "python -c \"import json; print(open('config.json').read())\""
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+def test_v18_notebook_bash_magic_denied(project_root: Path) -> None:
+    """V18 - NotebookEdit containing %%bash code-path mutation must DENY."""
+    target = "src/foo.ipynb"
+    (project_root / target).write_text("{}\n", encoding="utf-8")
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "NotebookEdit",
+        "tool_input": {
+            "notebook_path": target,
+            "new_source": "%%bash\necho x > src/y.py",
+        },
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r)
diff --git a/work/criterion-upgrade/Z13-findings.md b/work/criterion-upgrade/Z13-findings.md
new file mode 100644
index 0000000000000000000000000000000000000000..38b585b618ee80901232f87f6ac44c540b74510e
--- /dev/null
+++ b/work/criterion-upgrade/Z13-findings.md
@@ -0,0 +1,17 @@
+# Z13 Findings — Vectors V13-V18 actual enforcer behavior
+
+| # | Vector | Test result | Real gap? | Recommended Z14 fix |
+|---|--------|-------------|-----------|---------------------|
+| V13 | CronCreate | FAIL | yes | Classify `schtasks /Create ... /TR` as scheduler input and recursively inspect the scheduled command, or emit explicit `background-scheduler-not-classified` allow reason. |
+| V14 | MCP filesystem | FAIL | yes | Add MCP write tools such as `mcp__filesystem__write_file` to hook dispatch and extract `path` as a code-write target. |
+| V15 | Compiled binary | FAIL | yes | For unknown executables, require cover when any argument token names a code-extension path, while allowing opaque runs without code-path tokens. |
+| V16 | `bash -s` heredoc | PASS | no | Keep always-cover handling for `bash -s`/stdin-opaque interpreter input. |
+| V17 | `py -c` read-only | PASS | no | Keep read/write-sensitive `python -c` parsing so read-only `open(...).read()` allows. |
+| V18 | Notebook `%%bash` magic | PASS | no | Current NotebookEdit denial covers the `.ipynb`; preserve denial for notebook cells that can mutate code paths. |
+
+## Summary
+
+- Total new tests: 6
+- Currently passing (no real gap): 3
+- Currently failing (real gap, fix in Z14): 3
+- Gaps discovered: V13 scheduler-created background code writers, V14 MCP filesystem writes, V15 unknown compiled binaries with code-path arguments

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git restore --worktree -- .claude/memory/activeContext.md' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
 succeeded in 186ms:
diff --git a/.claude/hooks/test_enforcer_live_attacks.py b/.claude/hooks/test_enforcer_live_attacks.py
index 33edb22e07bda37eb0c7c86547ba55d2fb030828..c7746a818b893fa8525f5acacd96340cb78d9f81
--- a/.claude/hooks/test_enforcer_live_attacks.py
+++ b/.claude/hooks/test_enforcer_live_attacks.py
@@ -102,22 +102,38 @@
         )
 
 
-def _assert_allow(result: subprocess.CompletedProcess) -> None:
-    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
-    assert result.returncode == 0, (
-        f"unexpected non-zero exit on allow: {result.returncode}; "
-        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
+def _assert_allow(result: subprocess.CompletedProcess) -> None:
+    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
+    assert result.returncode == 0, (
+        f"unexpected non-zero exit on allow: {result.returncode}; "
+        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
     )
     deny = _parse_deny(result.stdout)
-    assert deny is None, (
-        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
-    )
-
+    assert deny is None, (
+        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
+    )
+
+
+def _latest_skip_ledger_entry(project_root: Path) -> dict:
+    """Return the last skip-ledger entry for assertions on allow reasons."""
+    ledger = project_root / "work" / "codex-implementations" / "skip-ledger.jsonl"
+    if not ledger.exists():
+        return {}
+    lines = [line.strip() for line in ledger.read_text(encoding="utf-8").splitlines()
+             if line.strip()]
+    if not lines:
+        return {}
+    try:
+        obj = json.loads(lines[-1])
+    except json.JSONDecodeError:
+        return {}
+    return obj if isinstance(obj, dict) else {}
+
+
+# ----------------------------------------------------------------------
+# Fixtures
+# ----------------------------------------------------------------------
 
-# ----------------------------------------------------------------------
-# Fixtures
-# ----------------------------------------------------------------------
-
 @pytest.fixture
 def project_root(tmp_path: Path) -> Path:
     """Hermetic project root with the dirs the enforcer expects.
@@ -403,14 +419,95 @@
     r = _run_enforcer(_edit_payload(target), project_root)
     _assert_allow(r)
 
-def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
-    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
-
-    .claude/scripts/sync-template-to-target.py is the project's own helper
-    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
+def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
+    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
+
+    .claude/scripts/sync-template-to-target.py is the project's own helper
+    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
     next to codex-ask.py, codex-implement.py, etc. Calling it via py -3 with
     arbitrary CLI args must NOT require a Codex cover.
     """
-    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
-    r = _run_enforcer(_bash_payload(cmd), project_root)
-    _assert_allow(r)
+    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+# ======================================================================
+# DISCOVERY VECTORS (V13-V18) - Z13 expanded live attack matrix
+# ======================================================================
+
+def test_v13_cron_create_code_writer_denied(project_root: Path) -> None:
+    """V13 - schtasks/CronCreate-style background code writer must be covered.
+
+    A proper implementation may either DENY because the scheduled action
+    invokes a code-writing script, or explicitly ALLOW with a documented
+    background-scheduler-not-classified reason.
+    """
+    (project_root / "work" / "sync.py").write_text("# sync\n", encoding="utf-8")
+    cmd = 'schtasks /Create /TN x /TR "py -3 work/sync.py"'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    if _parse_deny(r.stdout) is not None:
+        return
+    entry = _latest_skip_ledger_entry(project_root)
+    assert entry.get("decision") == "allow", (
+        f"expected DENY or explicit ALLOW; returncode={r.returncode} "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+    assert entry.get("reason") == "background-scheduler-not-classified", (
+        "expected explicit scheduler gap reason; "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+
+
+def test_v14_mcp_filesystem_write_denied_OR_documented(project_root: Path) -> None:
+    """V14 - MCP filesystem write_file should be denied or treated as a gap."""
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "mcp__filesystem__write_file",
+        "tool_input": {"path": "src/x.py", "content": "print('x')\n"},
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r, must_contain_in_reason="src/x.py")
+
+
+def test_v15_compiled_binary_unknown_classification(project_root: Path) -> None:
+    """V15 - unknown binary mutating a code path must deny, opaque run allows."""
+    r = _run_enforcer(_bash_payload("./my-tool --output src/foo.py"), project_root)
+    _assert_deny(r, must_contain_in_reason="src/foo.py")
+
+    opaque = _run_enforcer(_bash_payload("./my-tool --version"), project_root)
+    _assert_allow(opaque)
+
+
+def test_v16_bash_dash_s_heredoc_requires_cover(project_root: Path) -> None:
+    """V16 - bash -s heredoc is opaque interpreter input and must DENY."""
+    cmd = 'bash -s <<EOF\necho "x" > src/foo.py\nEOF'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_deny(r)
+
+
+def test_v17_python_dash_c_readonly_should_allow_OR_document(
+    project_root: Path,
+) -> None:
+    """V17 - python -c with read-only open(...).read() should ALLOW."""
+    cmd = "python -c \"import json; print(open('config.json').read())\""
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+def test_v18_notebook_bash_magic_denied(project_root: Path) -> None:
+    """V18 - NotebookEdit containing %%bash code-path mutation must DENY."""
+    target = "src/foo.ipynb"
+    (project_root / target).write_text("{}\n", encoding="utf-8")
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "NotebookEdit",
+        "tool_input": {
+            "notebook_path": target,
+            "new_source": "%%bash\necho x > src/y.py",
+        },
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r)
diff --git a/work/criterion-upgrade/Z13-findings.md b/work/criterion-upgrade/Z13-findings.md
new file mode 100644
index 0000000000000000000000000000000000000000..38b585b618ee80901232f87f6ac44c540b74510e
--- /dev/null
+++ b/work/criterion-upgrade/Z13-findings.md
@@ -0,0 +1,17 @@
+# Z13 Findings — Vectors V13-V18 actual enforcer behavior
+
+| # | Vector | Test result | Real gap? | Recommended Z14 fix |
+|---|--------|-------------|-----------|---------------------|
+| V13 | CronCreate | FAIL | yes | Classify `schtasks /Create ... /TR` as scheduler input and recursively inspect the scheduled command, or emit explicit `background-scheduler-not-classified` allow reason. |
+| V14 | MCP filesystem | FAIL | yes | Add MCP write tools such as `mcp__filesystem__write_file` to hook dispatch and extract `path` as a code-write target. |
+| V15 | Compiled binary | FAIL | yes | For unknown executables, require cover when any argument token names a code-extension path, while allowing opaque runs without code-path tokens. |
+| V16 | `bash -s` heredoc | PASS | no | Keep always-cover handling for `bash -s`/stdin-opaque interpreter input. |
+| V17 | `py -c` read-only | PASS | no | Keep read/write-sensitive `python -c` parsing so read-only `open(...).read()` allows. |
+| V18 | Notebook `%%bash` magic | PASS | no | Current NotebookEdit denial covers the `.ipynb`; preserve denial for notebook cells that can mutate code paths. |
+
+## Summary
+
+- Total new tests: 6
+- Currently passing (no real gap): 3
+- Currently failing (real gap, fix in Z14): 3
+- Gaps discovered: V13 scheduler-created background code writers, V14 MCP filesystem writes, V15 unknown compiled binaries with code-path arguments

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git show --stat --oneline HEAD' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z13\codex\task-Z13-expand-attack-matrix
 succeeded in 152ms:
 succeeded in 159ms:
d29a7b6 test: expand enforcer live attack matrix
 .claude/hooks/test_enforcer_live_attacks.py | 97 +++++++++++++++++++++++++++++
 work/criterion-upgrade/Z13-findings.md      | 17 +++++
 2 files changed, 114 insertions(+)

diff --git a/.claude/hooks/test_enforcer_live_attacks.py b/.claude/hooks/test_enforcer_live_attacks.py
index 33edb22e07bda37eb0c7c86547ba55d2fb030828..c7746a818b893fa8525f5acacd96340cb78d9f81
--- a/.claude/hooks/test_enforcer_live_attacks.py
+++ b/.claude/hooks/test_enforcer_live_attacks.py
@@ -102,22 +102,38 @@
         )
 
 
-def _assert_allow(result: subprocess.CompletedProcess) -> None:
-    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
-    assert result.returncode == 0, (
-        f"unexpected non-zero exit on allow: {result.returncode}; "
-        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
+def _assert_allow(result: subprocess.CompletedProcess) -> None:
+    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
+    assert result.returncode == 0, (
+        f"unexpected non-zero exit on allow: {result.returncode}; "
+        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
     )
     deny = _parse_deny(result.stdout)
-    assert deny is None, (
-        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
-    )
-
+    assert deny is None, (
+        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
+    )
+
+
+def _latest_skip_ledger_entry(project_root: Path) -> dict:
+    """Return the last skip-ledger entry for assertions on allow reasons."""
+    ledger = project_root / "work" / "codex-implementations" / "skip-ledger.jsonl"
+    if not ledger.exists():
+        return {}
+    lines = [line.strip() for line in ledger.read_text(encoding="utf-8").splitlines()
+             if line.strip()]
+    if not lines:
+        return {}
+    try:
+        obj = json.loads(lines[-1])
+    except json.JSONDecodeError:
+        return {}
+    return obj if isinstance(obj, dict) else {}
+
+
+# ----------------------------------------------------------------------
+# Fixtures
+# ----------------------------------------------------------------------
 
-# ----------------------------------------------------------------------
-# Fixtures
-# ----------------------------------------------------------------------
-
 @pytest.fixture
 def project_root(tmp_path: Path) -> Path:
     """Hermetic project root with the dirs the enforcer expects.
@@ -403,14 +419,95 @@
     r = _run_enforcer(_edit_payload(target), project_root)
     _assert_allow(r)
 
-def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
-    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
-
-    .claude/scripts/sync-template-to-target.py is the project's own helper
-    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
+def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
+    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
+
+    .claude/scripts/sync-template-to-target.py is the project's own helper
+    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
     next to codex-ask.py, codex-implement.py, etc. Calling it via py -3 with
     arbitrary CLI args must NOT require a Codex cover.
     """
-    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
-    r = _run_enforcer(_bash_payload(cmd), project_root)
-    _assert_allow(r)
+    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+# ======================================================================
+# DISCOVERY VECTORS (V13-V18) - Z13 expanded live attack matrix
+# ======================================================================
+
+def test_v13_cron_create_code_writer_denied(project_root: Path) -> None:
+    """V13 - schtasks/CronCreate-style background code writer must be covered.
+
+    A proper implementation may either DENY because the scheduled action
+    invokes a code-writing script, or explicitly ALLOW with a documented
+    background-scheduler-not-classified reason.
+    """
+    (project_root / "work" / "sync.py").write_text("# sync\n", encoding="utf-8")
+    cmd = 'schtasks /Create /TN x /TR "py -3 work/sync.py"'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    if _parse_deny(r.stdout) is not None:
+        return
+    entry = _latest_skip_ledger_entry(project_root)
+    assert entry.get("decision") == "allow", (
+        f"expected DENY or explicit ALLOW; returncode={r.returncode} "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+    assert entry.get("reason") == "background-scheduler-not-classified", (
+        "expected explicit scheduler gap reason; "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+
+
+def test_v14_mcp_filesystem_write_denied_OR_documented(project_root: Path) -> None:
+    """V14 - MCP filesystem write_file should be denied or treated as a gap."""
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "mcp__filesystem__write_file",
+        "tool_input": {"path": "src/x.py", "content": "print('x')\n"},
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r, must_contain_in_reason="src/x.py")
+
+
+def test_v15_compiled_binary_unknown_classification(project_root: Path) -> None:
+    """V15 - unknown binary mutating a code path must deny, opaque run allows."""
+    r = _run_enforcer(_bash_payload("./my-tool --output src/foo.py"), project_root)
+    _assert_deny(r, must_contain_in_reason="src/foo.py")
+
+    opaque = _run_enforcer(_bash_payload("./my-tool --version"), project_root)
+    _assert_allow(opaque)
+
+
+def test_v16_bash_dash_s_heredoc_requires_cover(project_root: Path) -> None:
+    """V16 - bash -s heredoc is opaque interpreter input and must DENY."""
+    cmd = 'bash -s <<EOF\necho "x" > src/foo.py\nEOF'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_deny(r)
+
+
+def test_v17_python_dash_c_readonly_should_allow_OR_document(
+    project_root: Path,
+) -> None:
+    """V17 - python -c with read-only open(...).read() should ALLOW."""
+    cmd = "python -c \"import json; print(open('config.json').read())\""
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+def test_v18_notebook_bash_magic_denied(project_root: Path) -> None:
+    """V18 - NotebookEdit containing %%bash code-path mutation must DENY."""
+    target = "src/foo.ipynb"
+    (project_root / target).write_text("{}\n", encoding="utf-8")
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "NotebookEdit",
+        "tool_input": {
+            "notebook_path": target,
+            "new_source": "%%bash\necho x > src/y.py",
+        },
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r)
diff --git a/work/criterion-upgrade/Z13-findings.md b/work/criterion-upgrade/Z13-findings.md
new file mode 100644
index 0000000000000000000000000000000000000000..38b585b618ee80901232f87f6ac44c540b74510e
--- /dev/null
+++ b/work/criterion-upgrade/Z13-findings.md
@@ -0,0 +1,17 @@
+# Z13 Findings — Vectors V13-V18 actual enforcer behavior
+
+| # | Vector | Test result | Real gap? | Recommended Z14 fix |
+|---|--------|-------------|-----------|---------------------|
+| V13 | CronCreate | FAIL | yes | Classify `schtasks /Create ... /TR` as scheduler input and recursively inspect the scheduled command, or emit explicit `background-scheduler-not-classified` allow reason. |
+| V14 | MCP filesystem | FAIL | yes | Add MCP write tools such as `mcp__filesystem__write_file` to hook dispatch and extract `path` as a code-write target. |
+| V15 | Compiled binary | FAIL | yes | For unknown executables, require cover when any argument token names a code-extension path, while allowing opaque runs without code-path tokens. |
+| V16 | `bash -s` heredoc | PASS | no | Keep always-cover handling for `bash -s`/stdin-opaque interpreter input. |
+| V17 | `py -c` read-only | PASS | no | Keep read/write-sensitive `python -c` parsing so read-only `open(...).read()` allows. |
+| V18 | Notebook `%%bash` magic | PASS | no | Current NotebookEdit denial covers the `.ipynb`; preserve denial for notebook cells that can mutate code paths. |
+
+## Summary
+
+- Total new tests: 6
+- Currently passing (no real gap): 3
+- Currently failing (real gap, fix in Z14): 3
+- Gaps discovered: V13 scheduler-created background code writers, V14 MCP filesystem writes, V15 unknown compiled binaries with code-path arguments

  ✓ Inspect live attack harness and enforcer classification behavior
  ✓ Add V13-V18 subprocess tests within scoped test file
  ✓ Run live matrix, capture actual V13-V18 results, and write findings
  ✓ Run required regression suites, selftest, and findings existence check
  → Prepare self-report with pass/fail details and commit SHA if available
diff --git a/.claude/hooks/test_enforcer_live_attacks.py b/.claude/hooks/test_enforcer_live_attacks.py
index 33edb22e07bda37eb0c7c86547ba55d2fb030828..c7746a818b893fa8525f5acacd96340cb78d9f81
--- a/.claude/hooks/test_enforcer_live_attacks.py
+++ b/.claude/hooks/test_enforcer_live_attacks.py
@@ -102,22 +102,38 @@
         )
 
 
-def _assert_allow(result: subprocess.CompletedProcess) -> None:
-    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
-    assert result.returncode == 0, (
-        f"unexpected non-zero exit on allow: {result.returncode}; "
-        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
+def _assert_allow(result: subprocess.CompletedProcess) -> None:
+    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
+    assert result.returncode == 0, (
+        f"unexpected non-zero exit on allow: {result.returncode}; "
+        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
     )
     deny = _parse_deny(result.stdout)
-    assert deny is None, (
-        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
-    )
-
+    assert deny is None, (
+        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
+    )
+
+
+def _latest_skip_ledger_entry(project_root: Path) -> dict:
+    """Return the last skip-ledger entry for assertions on allow reasons."""
+    ledger = project_root / "work" / "codex-implementations" / "skip-ledger.jsonl"
+    if not ledger.exists():
+        return {}
+    lines = [line.strip() for line in ledger.read_text(encoding="utf-8").splitlines()
+             if line.strip()]
+    if not lines:
+        return {}
+    try:
+        obj = json.loads(lines[-1])
+    except json.JSONDecodeError:
+        return {}
+    return obj if isinstance(obj, dict) else {}
+
+
+# ----------------------------------------------------------------------
+# Fixtures
+# ----------------------------------------------------------------------
 
-# ----------------------------------------------------------------------
-# Fixtures
-# ----------------------------------------------------------------------
-
 @pytest.fixture
 def project_root(tmp_path: Path) -> Path:
     """Hermetic project root with the dirs the enforcer expects.
@@ -403,14 +419,95 @@
     r = _run_enforcer(_edit_payload(target), project_root)
     _assert_allow(r)
 
-def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
-    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
-
-    .claude/scripts/sync-template-to-target.py is the project's own helper
-    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
+def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
+    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
+
+    .claude/scripts/sync-template-to-target.py is the project's own helper
+    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
     next to codex-ask.py, codex-implement.py, etc. Calling it via py -3 with
     arbitrary CLI args must NOT require a Codex cover.
     """
-    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
-    r = _run_enforcer(_bash_payload(cmd), project_root)
-    _assert_allow(r)
+    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+# ======================================================================
+# DISCOVERY VECTORS (V13-V18) - Z13 expanded live attack matrix
+# ======================================================================
+
+def test_v13_cron_create_code_writer_denied(project_root: Path) -> None:
+    """V13 - schtasks/CronCreate-style background code writer must be covered.
+
+    A proper implementation may either DENY because the scheduled action
+    invokes a code-writing script, or explicitly ALLOW with a documented
+    background-scheduler-not-classified reason.
+    """
+    (project_root / "work" / "sync.py").write_text("# sync\n", encoding="utf-8")
+    cmd = 'schtasks /Create /TN x /TR "py -3 work/sync.py"'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    if _parse_deny(r.stdout) is not None:
+        return
+    entry = _latest_skip_ledger_entry(project_root)
+    assert entry.get("decision") == "allow", (
+        f"expected DENY or explicit ALLOW; returncode={r.returncode} "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+    assert entry.get("reason") == "background-scheduler-not-classified", (
+        "expected explicit scheduler gap reason; "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+
+
+def test_v14_mcp_filesystem_write_denied_OR_documented(project_root: Path) -> None:
+    """V14 - MCP filesystem write_file should be denied or treated as a gap."""
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "mcp__filesystem__write_file",
+        "tool_input": {"path": "src/x.py", "content": "print('x')\n"},
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r, must_contain_in_reason="src/x.py")
+
+
+def test_v15_compiled_binary_unknown_classification(project_root: Path) -> None:
+    """V15 - unknown binary mutating a code path must deny, opaque run allows."""
+    r = _run_enforcer(_bash_payload("./my-tool --output src/foo.py"), project_root)
+    _assert_deny(r, must_contain_in_reason="src/foo.py")
+
+    opaque = _run_enforcer(_bash_payload("./my-tool --version"), project_root)
+    _assert_allow(opaque)
+
+
+def test_v16_bash_dash_s_heredoc_requires_cover(project_root: Path) -> None:
+    """V16 - bash -s heredoc is opaque interpreter input and must DENY."""
+    cmd = 'bash -s <<EOF\necho "x" > src/foo.py\nEOF'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_deny(r)
+
+
+def test_v17_python_dash_c_readonly_should_allow_OR_document(
+    project_root: Path,
+) -> None:
+    """V17 - python -c with read-only open(...).read() should ALLOW."""
+    cmd = "python -c \"import json; print(open('config.json').read())\""
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+def test_v18_notebook_bash_magic_denied(project_root: Path) -> None:
+    """V18 - NotebookEdit containing %%bash code-path mutation must DENY."""
+    target = "src/foo.ipynb"
+    (project_root / target).write_text("{}\n", encoding="utf-8")
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "NotebookEdit",
+        "tool_input": {
+            "notebook_path": target,
+            "new_source": "%%bash\necho x > src/y.py",
+        },
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r)
diff --git a/work/criterion-upgrade/Z13-findings.md b/work/criterion-upgrade/Z13-findings.md
new file mode 100644
index 0000000000000000000000000000000000000000..38b585b618ee80901232f87f6ac44c540b74510e
--- /dev/null
+++ b/work/criterion-upgrade/Z13-findings.md
@@ -0,0 +1,17 @@
+# Z13 Findings — Vectors V13-V18 actual enforcer behavior
+
+| # | Vector | Test result | Real gap? | Recommended Z14 fix |
+|---|--------|-------------|-----------|---------------------|
+| V13 | CronCreate | FAIL | yes | Classify `schtasks /Create ... /TR` as scheduler input and recursively inspect the scheduled command, or emit explicit `background-scheduler-not-classified` allow reason. |
+| V14 | MCP filesystem | FAIL | yes | Add MCP write tools such as `mcp__filesystem__write_file` to hook dispatch and extract `path` as a code-write target. |
+| V15 | Compiled binary | FAIL | yes | For unknown executables, require cover when any argument token names a code-extension path, while allowing opaque runs without code-path tokens. |
+| V16 | `bash -s` heredoc | PASS | no | Keep always-cover handling for `bash -s`/stdin-opaque interpreter input. |
+| V17 | `py -c` read-only | PASS | no | Keep read/write-sensitive `python -c` parsing so read-only `open(...).read()` allows. |
+| V18 | Notebook `%%bash` magic | PASS | no | Current NotebookEdit denial covers the `.ipynb`; preserve denial for notebook cells that can mutate code paths. |
+
+## Summary
+
+- Total new tests: 6
+- Currently passing (no real gap): 3
+- Currently failing (real gap, fix in Z14): 3
+- Gaps discovered: V13 scheduler-created background code writers, V14 MCP filesystem writes, V15 unknown compiled binaries with code-path arguments

codex
=== TASK Z13 SELF-REPORT ===
- status: pass
- new tests added: 6 (expected 6)
- existing 19 tests still pass: yes
- new tests PASSING (no real gap): 3
- new tests FAILING (real gap, queue for Z14): 3
- gaps documented in Z13-findings.md: yes
- all other suites pass: yes
- selftest: PASS
- NOTE: live matrix collected 25 tests: 22 passed, 3 failed. Expected discovery failures: V13, V14, V15.
- NOTE: other suites: 249 passed, 1 warning.
- NOTE: selftest output: 6 checks, 6 passed, 0 failed.
- NOTE: findings existence check output: OK.
- Final commit SHA: d29a7b608da825faba467924fd6f302ba7f62e25
=== END SELF-REPORT ===
diff --git a/.claude/hooks/test_enforcer_live_attacks.py b/.claude/hooks/test_enforcer_live_attacks.py
index 33edb22e07bda37eb0c7c86547ba55d2fb030828..c7746a818b893fa8525f5acacd96340cb78d9f81
--- a/.claude/hooks/test_enforcer_live_attacks.py
+++ b/.claude/hooks/test_enforcer_live_attacks.py
@@ -102,22 +102,38 @@
         )
 
 
-def _assert_allow(result: subprocess.CompletedProcess) -> None:
-    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
-    assert result.returncode == 0, (
-        f"unexpected non-zero exit on allow: {result.returncode}; "
-        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
+def _assert_allow(result: subprocess.CompletedProcess) -> None:
+    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
+    assert result.returncode == 0, (
+        f"unexpected non-zero exit on allow: {result.returncode}; "
+        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
     )
     deny = _parse_deny(result.stdout)
-    assert deny is None, (
-        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
-    )
-
+    assert deny is None, (
+        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
+    )
+
+
+def _latest_skip_ledger_entry(project_root: Path) -> dict:
+    """Return the last skip-ledger entry for assertions on allow reasons."""
+    ledger = project_root / "work" / "codex-implementations" / "skip-ledger.jsonl"
+    if not ledger.exists():
+        return {}
+    lines = [line.strip() for line in ledger.read_text(encoding="utf-8").splitlines()
+             if line.strip()]
+    if not lines:
+        return {}
+    try:
+        obj = json.loads(lines[-1])
+    except json.JSONDecodeError:
+        return {}
+    return obj if isinstance(obj, dict) else {}
+
+
+# ----------------------------------------------------------------------
+# Fixtures
+# ----------------------------------------------------------------------
 
-# ----------------------------------------------------------------------
-# Fixtures
-# ----------------------------------------------------------------------
-
 @pytest.fixture
 def project_root(tmp_path: Path) -> Path:
     """Hermetic project root with the dirs the enforcer expects.
@@ -403,14 +419,95 @@
     r = _run_enforcer(_edit_payload(target), project_root)
     _assert_allow(r)
 
-def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
-    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
-
-    .claude/scripts/sync-template-to-target.py is the project's own helper
-    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
+def test_a07_sync_script_invocation_allowed(project_root: Path) -> None:
+    """A7 (Y22) - Bash invocation of the relocated sync script must ALLOW.
+
+    .claude/scripts/sync-template-to-target.py is the project's own helper
+    (not a one-shot mass-mutator), so it lives in the dual-tooling whitelist
     next to codex-ask.py, codex-implement.py, etc. Calling it via py -3 with
     arbitrary CLI args must NOT require a Codex cover.
     """
-    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
-    r = _run_enforcer(_bash_payload(cmd), project_root)
-    _assert_allow(r)
+    cmd = "py -3 .claude/scripts/sync-template-to-target.py --tgt /tmp/foo --apply"
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+# ======================================================================
+# DISCOVERY VECTORS (V13-V18) - Z13 expanded live attack matrix
+# ======================================================================
+
+def test_v13_cron_create_code_writer_denied(project_root: Path) -> None:
+    """V13 - schtasks/CronCreate-style background code writer must be covered.
+
+    A proper implementation may either DENY because the scheduled action
+    invokes a code-writing script, or explicitly ALLOW with a documented
+    background-scheduler-not-classified reason.
+    """
+    (project_root / "work" / "sync.py").write_text("# sync\n", encoding="utf-8")
+    cmd = 'schtasks /Create /TN x /TR "py -3 work/sync.py"'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    if _parse_deny(r.stdout) is not None:
+        return
+    entry = _latest_skip_ledger_entry(project_root)
+    assert entry.get("decision") == "allow", (
+        f"expected DENY or explicit ALLOW; returncode={r.returncode} "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+    assert entry.get("reason") == "background-scheduler-not-classified", (
+        "expected explicit scheduler gap reason; "
+        f"stdout={r.stdout!r} stderr={r.stderr[-500:]!r} ledger={entry!r}"
+    )
+
+
+def test_v14_mcp_filesystem_write_denied_OR_documented(project_root: Path) -> None:
+    """V14 - MCP filesystem write_file should be denied or treated as a gap."""
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "mcp__filesystem__write_file",
+        "tool_input": {"path": "src/x.py", "content": "print('x')\n"},
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r, must_contain_in_reason="src/x.py")
+
+
+def test_v15_compiled_binary_unknown_classification(project_root: Path) -> None:
+    """V15 - unknown binary mutating a code path must deny, opaque run allows."""
+    r = _run_enforcer(_bash_payload("./my-tool --output src/foo.py"), project_root)
+    _assert_deny(r, must_contain_in_reason="src/foo.py")
+
+    opaque = _run_enforcer(_bash_payload("./my-tool --version"), project_root)
+    _assert_allow(opaque)
+
+
+def test_v16_bash_dash_s_heredoc_requires_cover(project_root: Path) -> None:
+    """V16 - bash -s heredoc is opaque interpreter input and must DENY."""
+    cmd = 'bash -s <<EOF\necho "x" > src/foo.py\nEOF'
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_deny(r)
+
+
+def test_v17_python_dash_c_readonly_should_allow_OR_document(
+    project_root: Path,
+) -> None:
+    """V17 - python -c with read-only open(...).read() should ALLOW."""
+    cmd = "python -c \"import json; print(open('config.json').read())\""
+    r = _run_enforcer(_bash_payload(cmd), project_root)
+    _assert_allow(r)
+
+
+def test_v18_notebook_bash_magic_denied(project_root: Path) -> None:
+    """V18 - NotebookEdit containing %%bash code-path mutation must DENY."""
+    target = "src/foo.ipynb"
+    (project_root / target).write_text("{}\n", encoding="utf-8")
+    payload = {
+        "hook_event_name": "PreToolUse",
+        "tool_name": "NotebookEdit",
+        "tool_input": {
+            "notebook_path": target,
+            "new_source": "%%bash\necho x > src/y.py",
+        },
+        "session_id": "z13-test",
+    }
+    r = _run_enforcer(payload, project_root)
+    _assert_deny(r)
diff --git a/work/criterion-upgrade/Z13-findings.md b/work/criterion-upgrade/Z13-findings.md
new file mode 100644
index 0000000000000000000000000000000000000000..38b585b618ee80901232f87f6ac44c540b74510e
--- /dev/null
+++ b/work/criterion-upgrade/Z13-findings.md
@@ -0,0 +1,17 @@
+# Z13 Findings — Vectors V13-V18 actual enforcer behavior
+
+| # | Vector | Test result | Real gap? | Recommended Z14 fix |
+|---|--------|-------------|-----------|---------------------|
+| V13 | CronCreate | FAIL | yes | Classify `schtasks /Create ... /TR` as scheduler input and recursively inspect the scheduled command, or emit explicit `background-scheduler-not-classified` allow reason. |
+| V14 | MCP filesystem | FAIL | yes | Add MCP write tools such as `mcp__filesystem__write_file` to hook dispatch and extract `path` as a code-write target. |
+| V15 | Compiled binary | FAIL | yes | For unknown executables, require cover when any argument token names a code-extension path, while allowing opaque runs without code-path tokens. |
+| V16 | `bash -s` heredoc | PASS | no | Keep always-cover handling for `bash -s`/stdin-opaque interpreter input. |
+| V17 | `py -c` read-only | PASS | no | Keep read/write-sensitive `python -c` parsing so read-only `open(...).read()` allows. |
+| V18 | Notebook `%%bash` magic | PASS | no | Current NotebookEdit denial covers the `.ipynb`; preserve denial for notebook cells that can mutate code paths. |
+
+## Summary
+
+- Total new tests: 6
+- Currently passing (no real gap): 3
+- Currently failing (real gap, fix in Z14): 3
+- Gaps discovered: V13 scheduler-created background code writers, V14 MCP filesystem writes, V15 unknown compiled binaries with code-path arguments

2026-04-26T14:50:55.072694Z ERROR codex_core::session: failed to record rollout items: thread 019dca41-bab1-7751-ae52-6494f4e5c25d not found
tokens used
55 206
```
