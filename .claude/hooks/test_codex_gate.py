#!/usr/bin/env python3
"""Unit tests for codex-gate.py (T5 — tech-spec Section 9).

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
            self.assertIsNone(self.gate._parse_result_status(p))
        finally:
            p.unlink()

    def test_path_in_fence_exact_file(self):
        self.assertTrue(self.gate._path_in_fence("a/b/c.py", ["a/b/c.py"]))

    def test_path_in_fence_dir_prefix(self):
        self.assertTrue(self.gate._path_in_fence("a/b/c.py", ["a/b"]))
        self.assertTrue(self.gate._path_in_fence("a/b/c.py", ["a/b/"]))

    def test_path_in_fence_not_match(self):
        self.assertFalse(self.gate._path_in_fence("a/b/c.py", ["other/dir"]))

    def test_path_in_fence_no_partial_segment(self):
        """'a/bb/c.py' must NOT match fence 'a/b' (prefix must be boundary)."""
        self.assertFalse(self.gate._path_in_fence("a/bb/c.py", ["a/b"]))

    def test_parse_scope_fence_strips_backticks_and_annotations(self):
        import tempfile, pathlib
        text = """# Task

## Scope Fence
**Allowed paths (may be written):**
- `.claude/hooks/codex-gate.py` (MODIFY)
- `.claude/hooks/test_codex_gate.py` (new)

**Forbidden paths (must NOT be modified):**
- elsewhere/

## Next
"""
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
            fh.write(text)
            p = pathlib.Path(fh.name)
        try:
            fence = self.gate._parse_scope_fence(p)
            self.assertIn(".claude/hooks/codex-gate.py", fence)
            self.assertIn(".claude/hooks/test_codex_gate.py", fence)
        finally:
            p.unlink()

    def test_dual_teams_worktree_sentinel_in_project_dir(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir).resolve()
            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")
            self.assertTrue(self.gate.is_dual_teams_worktree(project_dir))

    def test_dual_teams_worktree_sentinel_in_parent_dir(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            nested = root / "a" / "b" / "c"
            nested.mkdir(parents=True)
            (root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
            self.assertTrue(self.gate.is_dual_teams_worktree(nested))

    def test_dual_teams_worktree_absent_sentinel(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir).resolve()
            self.assertFalse(self.gate.is_dual_teams_worktree(project_dir))


if __name__ == "__main__":
    unittest.main(verbosity=2)
