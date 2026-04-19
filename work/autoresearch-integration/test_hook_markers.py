"""Behavioral tests for task-completed-gate.py merge-conflict detection fix.

Verifies the hook:
- STILL flags real git conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
- NO LONGER false-positives on log separators like `=====================`

Run:
    py -3 work/autoresearch-integration/test_hook_markers.py
"""

import importlib.util
import logging
import tempfile
import unittest
from pathlib import Path


HOOK_PATH = Path(".claude/hooks/task-completed-gate.py")


def load_hook():
    """Import task-completed-gate.py as a module. Only call check_merge_conflicts — do not trigger main()."""
    spec = importlib.util.spec_from_file_location("task_completed_gate", HOOK_PATH)
    module = importlib.util.module_from_spec(spec)
    logging.disable(logging.CRITICAL)
    spec.loader.exec_module(module)
    return module


class TestMergeConflictDetection(unittest.TestCase):
    def setUp(self):
        self.hook = load_hook()

    def _check(self, content: str):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "test.txt"
            p.write_text(content, encoding="utf-8")
            return self.hook.check_merge_conflicts(Path(tmp), ["test.txt"])

    # --- MUST FLAG (real git conflict markers) ---
    def test_detects_head_marker(self):
        conflicts = self._check("<<<<<<< HEAD\nfoo\n=======\nbar\n>>>>>>> main\n")
        self.assertTrue(conflicts, "real HEAD/EQ/BRANCH conflict should be detected")

    def test_detects_exact_7_equals_alone(self):
        conflicts = self._check("line1\n=======\nline2\n")
        self.assertTrue(conflicts, "bare '=======' on its own line is a real marker")

    def test_detects_branch_marker_with_space(self):
        conflicts = self._check("<<<<<<< feature-branch\ncontent\n")
        self.assertTrue(conflicts, "'<<<<<<< branch-name' is a real marker")

    def test_detects_closing_marker_with_space(self):
        conflicts = self._check("content\n>>>>>>> main\n")
        self.assertTrue(conflicts, "'>>>>>>> branch-name' is a real marker")

    # --- MUST NOT FLAG (false-positive cases the fix addresses) ---
    def test_ignores_log_separator_long_equals(self):
        conflicts = self._check(
            "### 2026-04-08 Bash error\n"
            "Context: heredoc\n"
            "=====================\n"
            "Error: unexpected EOF\n"
        )
        self.assertEqual(conflicts, [], "long '====='... log separator must NOT be flagged")

    def test_ignores_21_equals(self):
        conflicts = self._check("a\n=====================\nb\n")
        self.assertEqual(conflicts, [])

    def test_ignores_8_equals(self):
        conflicts = self._check("a\n========\nb\n")
        self.assertEqual(conflicts, [], "8 equals is not a git marker (should be exactly 7)")

    def test_ignores_plain_text(self):
        conflicts = self._check("normal\nwith multiple\nlines\n")
        self.assertEqual(conflicts, [])

    def test_ignores_equals_in_middle_of_line(self):
        conflicts = self._check("foo ======= bar\n")
        self.assertEqual(conflicts, [], "marker NOT at line start should be ignored")


if __name__ == "__main__":
    unittest.main(verbosity=2)
