#!/usr/bin/env python3
"""Tests for Z1 four-invariant enforcer (codex-delegate-enforcer.py).

Covers all 4 invariants:
- AC-1: I1 — extension wins (path exemption is non-code only)
- AC-2: I2 — Bash counts (effect-based interception)
- AC-3: I3 — path-exact coverage (no temporal carryover)
- AC-4: I4 — skip-token ledger + actionable block messages
- AC-5: regression — existing 36 tests still pass + selftest
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
# AC-1 — Invariant 1: Extension wins
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
# AC-2 — Invariant 2: Bash counts
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
# AC-3 — Invariant 3: Path-exact coverage (no temporal carryover)
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
# AC-4 — Invariant 4: Skip-token ledger + actionable block messages
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
# AC-5 — Regression: existing tests + selftest still pass
# ======================================================================
class TestRegression(unittest.TestCase):
    """Regression suite — runs the existing 36-test suite and selftest."""

    def test_existing_tests_still_pass(self):
        """Run pytest on test_codex_delegate_enforcer.py — exit 0."""
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
        """Run dual-teams-selftest.py — exit 0."""
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


# ======================================================================
# Y25 (Z12) — _codex_appears_unavailable helper + block-message hint
# ======================================================================
class TestY25CodexUnavailableHelper(unittest.TestCase):
    """Helper detects missing / stale ~/.codex/auth.json."""

    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module()

    def test_codex_unavailable_when_auth_missing(self):
        """auth_path pointing at a non-existent file -> True + 'missing'."""
        with tempfile.TemporaryDirectory() as td:
            nx = Path(td) / "nonexistent.json"
            self.assertFalse(nx.exists())
            unavailable, reason = self.mod._codex_appears_unavailable(auth_path=nx)
            self.assertTrue(unavailable)
            self.assertIn("missing", reason)

    def test_codex_available_when_auth_recent(self):
        """fresh tmp file (mtime=now) -> False, ''."""
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "auth.json"
            p.write_text("{}", encoding="utf-8")
            unavailable, reason = self.mod._codex_appears_unavailable(auth_path=p)
            self.assertFalse(unavailable)
            self.assertEqual(reason, "")

    def test_codex_unavailable_when_auth_stale(self):
        """tmp file with mtime 48h ago -> True + 'older'."""
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "auth.json"
            p.write_text("{}", encoding="utf-8")
            old = time.time() - 48 * 3600
            os.utime(p, (old, old))
            unavailable, reason = self.mod._codex_appears_unavailable(auth_path=p)
            self.assertTrue(unavailable)
            self.assertIn("older", reason)


class TestY25BlockMessage(_Base):
    """DENY message gains an unavailability hint when Codex is down."""

    def test_block_message_mentions_unavailability_when_codex_down(self):
        """When _codex_appears_unavailable returns True, deny msg has hint
        AND keeps the existing codex-inline-dual command."""
        target = "src/auth.py"
        (self.root / "src" / "auth.py").write_text("# a\n", encoding="utf-8")
        original = self.mod._codex_appears_unavailable
        try:
            self.mod._codex_appears_unavailable = lambda *a, **kw: (True, "test reason")
            allowed, stdout = self._decide(self._edit_payload(target))
        finally:
            self.mod._codex_appears_unavailable = original
        self.assertFalse(allowed)
        parsed = json.loads(stdout)
        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("appears unavailable", reason)
        self.assertIn("test reason", reason)
        # Existing recovery hint must remain.
        self.assertIn("codex-inline-dual.py", reason)

    def test_block_message_unchanged_when_codex_available(self):
        """When _codex_appears_unavailable returns (False, ''), deny msg
        does NOT contain the unavailability hint."""
        target = "src/auth.py"
        (self.root / "src" / "auth.py").write_text("# a\n", encoding="utf-8")
        original = self.mod._codex_appears_unavailable
        try:
            self.mod._codex_appears_unavailable = lambda *a, **kw: (False, "")
            allowed, stdout = self._decide(self._edit_payload(target))
        finally:
            self.mod._codex_appears_unavailable = original
        self.assertFalse(allowed)
        parsed = json.loads(stdout)
        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertNotIn("appears unavailable", reason)
        # Existing recovery hint still present (rule unchanged).
        self.assertIn("codex-inline-dual.py", reason)


if __name__ == "__main__":
    unittest.main(verbosity=2)
