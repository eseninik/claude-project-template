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


# ======================================================================
# Z13: NEW VECTORS V13-V18 - discovery tests
#
# Some of these MAY FAIL - failures are expected and reveal real enforcer
# gaps that Z14 will fix. Each test asserts the EXPECTED CORRECT behavior
# per the task spec; pass/fail outcomes are documented in
# work/criterion-upgrade/Z13-findings.md.
# ======================================================================

def test_v13_cron_create_code_writer_denied(project_root: Path) -> None:
    """V13 - schtasks/CronCreate scheduling code-writer script.

    Payload:  Bash command  schtasks /Create /TN x /TR "py -3 work/sync.py"

    Expected (correct): DENY because the scheduled command is itself
    a code-writing invocation (`py -3 work/sync.py` -> Invariant 2,
    work/**/*.py is still code per Invariant 1).

    Likely current: ALLOW - the enforcer sees verb=`schtasks` (unknown,
    not in mutating/readonly/interpreter sets) and falls through to
    `unknown-verb-allowed`. The nested `py -3 work/sync.py` payload is
    invisible because schtasks's `/TR` argument is just a string token
    to the parser, never re-tokenized.
    """
    cmd = 'schtasks /Create /TN x /TR "py -3 work/sync.py"'
    r = _run_enforcer(_bash_payload(cmd), project_root)
    _assert_deny(r)


def test_v14_mcp_filesystem_write_denied_OR_documented(project_root: Path) -> None:
    """V14 - MCP filesystem `mcp__filesystem__write_file` tool.

    Payload:  tool_name=mcp__filesystem__write_file,
              tool_input={path: "src/x.py", content: "..."}

    Expected (correct): DENY - any MCP write tool that mutates a
    code-extension target should require a Codex cover.

    Likely current: ALLOW - the dispatch in decide() only handles
    {Edit, Write, MultiEdit, Bash, NotebookEdit}; tool_name starting
    with `mcp__` falls through to passthrough. The settings.json hook
    matcher also does not list any `mcp__*` pattern, so the enforcer
    is never even invoked for live MCP write calls in production.
    """
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "mcp__filesystem__write_file",
        "tool_input": {"path": "src/x.py", "content": "# pwn\n"},
        "session_id": "z13-test",
    }
    (project_root / "src" / "x.py").write_text("# original\n", encoding="utf-8")
    r = _run_enforcer(payload, project_root)
    _assert_deny(r)


def test_v15_compiled_binary_unknown_classification(project_root: Path) -> None:
    """V15 - Compiled binary execution writing to a code path.

    Payload:  Bash command  ./my-tool --output src/foo.py

    Expected (correct): DENY because the argument `src/foo.py` is a
    code-extension token that the binary will write to. A safer
    enforcer should treat any unknown verb whose argv contains a
    code-extension positional path as `require_cover`.

    Likely current: ALLOW - `verb=my-tool` is unknown, falls through
    to `unknown-verb-allowed`. The redirect scanner only catches `>`
    / `>>`, not `--output` style flags. The `_extract_code_path_args`
    helper IS only called inside the mutating/inplace branches, never
    for unknown verbs.
    """
    cmd = "./my-tool --output src/foo.py"
    r = _run_enforcer(_bash_payload(cmd), project_root)
    _assert_deny(r, must_contain_in_reason="src/foo.py")


def test_v16_bash_dash_s_heredoc_requires_cover(project_root: Path) -> None:
    """V16 - `bash -s` heredoc-to-interpreter.

    Payload:  bash -s <<EOF\\necho "x" > src/foo.py\\nEOF

    Expected (correct): DENY. Two independent reasons:
      1. `bash -s` matches has_dash_s -> require_cover
         (`bash-stdin-opaque`).
      2. The split-on-newline body sub-command
         `echo "x" > src/foo.py` has a redirect to a code path, which
         the early_redirects branch in _classify_single_command catches.

    Likely current: PASS (deny) on the strength of either signal - the
    `-s` shortcut almost certainly fires first.
    """
    cmd = 'bash -s <<EOF\necho "x" > src/foo.py\nEOF'
    r = _run_enforcer(_bash_payload(cmd), project_root)
    _assert_deny(r)


def test_v17_python_dash_c_readonly_should_allow_OR_document(
    project_root: Path,
) -> None:
    """V17 - False-positive: `py -c` legitimate read-only command.

    Payload:  python -c "import json; print(open('config.json').read())"

    Expected (correct): ALLOW. The body opens config.json for the
    default read mode and only prints; there is no `open(..., 'w')`,
    no `'a'`, no Path.write_*, no shutil.copy. A correct heuristic
    must NOT flag this as a write.

    Likely current: ALLOW - _classify_interpreter dash_c branch
    iterates write_patterns (none match because there's no `'w'`/`'a'`
    after the comma) and the fallback regex `open\\([^)]*['\"][wa]`
    also does not match `open('config.json')` (no w/a literal). So
    enforcer should already return `python-c-no-write`.

    If this test ever FAILS, it means the enforcer's open()-detection
    has become over-eager (a regression worth investigating).
    """
    cmd = (
        "python -c \"import json; print(open('config.json').read())\""
    )
    r = _run_enforcer(_bash_payload(cmd), project_root)
    _assert_allow(r)


def test_v18_notebook_bash_magic_denied(project_root: Path) -> None:
    """V18 - NotebookEdit cell whose source is `%%bash` magic that writes code.

    Payload:  tool=NotebookEdit, notebook_path=src/foo.ipynb,
              new_source="%%bash\\necho x > src/y.py"

    Expected (correct): DENY. The notebook itself is a code file
    (.ipynb is in CODE_EXTENSIONS, Z7-V02), so the edit always
    requires a cover. Separately, the cell body would shell-execute
    a redirect to src/y.py - but the .ipynb extension is sufficient
    to require cover regardless of cell content.

    Likely current: PASS (deny) on the strength of the .ipynb
    extension match alone. Z14 will need to add inspection of
    `new_source` for `%%bash` / `%%sh` / `!`-magic commands so that
    NotebookEdit on a NON-.ipynb path (theoretical, but possible if
    extensions list ever changes) would also deny when the cell body
    mutates code.
    """
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "NotebookEdit",
        "tool_input": {
            "notebook_path": "src/foo.ipynb",
            "new_source": '%%bash\necho x > src/y.py',
        },
        "session_id": "z13-test",
    }
    (project_root / "src" / "foo.ipynb").write_text("{}\n", encoding="utf-8")
    r = _run_enforcer(payload, project_root)
    _assert_deny(r)
