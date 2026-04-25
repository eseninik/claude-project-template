"""Unit tests for worktree-cleaner.py."""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).parent / "worktree-cleaner.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("worktree_cleaner", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["worktree_cleaner"] = mod
    spec.loader.exec_module(mod)
    return mod


cleaner = _load_module()


def completed(stdout: str = "", stderr: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["git"], returncode, stdout, stderr)


class ParsePorcelainTests(unittest.TestCase):
    def test_discovery_from_canned_porcelain(self):
        text = """worktree C:/repo
HEAD abc
branch refs/heads/main

worktree C:/repo/worktrees/fixes/codex/task-one
HEAD def
branch refs/heads/codex/task-one

"""
        records = cleaner.parse_porcelain(text)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[1].worktree, Path("C:/repo/worktrees/fixes/codex/task-one"))
        self.assertEqual(records[1].branch, "codex/task-one")


class CollectEntriesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.worktrees = self.root / "worktrees"
        self.worktrees.mkdir()
        self.main = cleaner.WorktreeRecord(self.root, "main", "aaa")
        self.now = 2_000_000_000.0

    def tearDown(self):
        self.tmp.cleanup()

    def _candidate(self, name: str, branch: str = "feature") -> cleaner.WorktreeRecord:
        path = self.worktrees / name
        path.mkdir(parents=True)
        (path / ".dual-base-ref").write_text("base\n", encoding="utf-8")
        return cleaner.WorktreeRecord(path, branch, "bbb")

    def _run_git(self, timestamps: list[int] | None = None):
        values = [int(self.now)] if timestamps is None else timestamps

        def fake(args, cwd=None):
            if args[:3] == ["symbolic-ref", "--short", "HEAD"]:
                return completed("main\n")
            if args[:2] == ["log", "--no-merges"]:
                return completed("".join(f"{stamp}\n" for stamp in values))
            if args and args[0] == "merge-base":
                return completed("base\n")
            self.fail(f"unexpected git call: {args}")

        return fake

    def test_sentinel_missing_flags_rule_a(self):
        record = self._candidate("missing-sentinel")
        (record.worktree / ".dual-base-ref").unlink()
        with mock.patch.object(cleaner, "run_git", side_effect=self._run_git()):
            entries, _ = cleaner.collect_entries([self.main, record], "worktrees/", 7, self.now)
        self.assertIn("a", entries[0].reasons)
        self.assertFalse(entries[0].has_sentinel)

    def test_age_threshold_flags_rule_b(self):
        old = int(self.now - 8 * cleaner.SECONDS_PER_DAY)
        record = self._candidate("old")
        with mock.patch.object(cleaner, "run_git", side_effect=self._run_git([old])):
            entries, _ = cleaner.collect_entries([self.main, record], "worktrees/", 7, self.now)
        self.assertEqual(entries[0].age_days, 8)
        self.assertIn("b", entries[0].reasons)

    def test_zero_commits_flags_rule_c(self):
        record = self._candidate("empty")
        with mock.patch.object(cleaner, "run_git", side_effect=self._run_git([])):
            entries, _ = cleaner.collect_entries([self.main, record], "worktrees/", 7, self.now)
        self.assertIsNone(entries[0].age_days)
        self.assertIn("c", entries[0].reasons)

    def test_main_worktree_excluded(self):
        with mock.patch.object(cleaner, "run_git", side_effect=self._run_git()):
            entries, _ = cleaner.collect_entries([self.main], "worktrees/", 7, self.now)
        self.assertEqual(entries, [])

    def test_current_branch_worktree_excluded(self):
        record = self._candidate("current", branch="main")
        with mock.patch.object(cleaner, "run_git", side_effect=self._run_git()):
            entries, _ = cleaner.collect_entries([self.main, record], "worktrees/", 7, self.now)
        self.assertEqual(entries, [])


class ApplyAndFormatTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.path = self.root / "worktrees" / "feature"
        self.path.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def entry(self) -> cleaner.CleanupEntry:
        return cleaner.CleanupEntry(self.path, "feature", ["a"], False, 8)

    def test_apply_invokes_both_git_commands_per_entry(self):
        entry = self.entry()
        with mock.patch.object(cleaner, "run_git", return_value=completed()) as run_git:
            ok = cleaner.apply_cleanup([entry])
        self.assertTrue(ok)
        run_git.assert_has_calls([
            mock.call(["worktree", "remove", "--force", str(self.path)]),
            mock.call(["branch", "-D", "feature"]),
        ])
        self.assertEqual(entry.apply_status, "removed")

    def test_json_schema_round_trip(self):
        output = cleaner.format_json([self.entry()], self.root)
        payload = json.loads(output)
        self.assertEqual(payload["found"], 1)
        self.assertEqual(payload["stale"], 1)
        self.assertEqual(payload["kept"], 0)
        self.assertEqual(payload["entries"][0]["reasons"], ["a"])
        self.assertEqual(payload["entries"][0]["apply_status"], "skipped")

    def test_failure_on_remove_reported_and_continues(self):
        first = self.entry()
        second = cleaner.CleanupEntry(self.root / "worktrees" / "second", "second", ["b"], True, 9)
        results = [completed(returncode=1), completed(), completed(), completed()]
        with mock.patch.object(cleaner, "run_git", side_effect=results) as run_git:
            ok = cleaner.apply_cleanup([first, second])
        self.assertFalse(ok)
        self.assertEqual(first.apply_status, "error")
        self.assertEqual(second.apply_status, "removed")
        self.assertEqual(run_git.call_count, 4)

    def test_empty_input_message_exit_zero(self):
        porcelain = "worktree C:/repo\nHEAD abc\nbranch refs/heads/main\n\n"

        def fake_run_git(args, cwd=None):
            if args[:3] == ["worktree", "list", "--porcelain"]:
                return completed(porcelain)
            if args[:3] == ["symbolic-ref", "--short", "HEAD"]:
                return completed("main\n")
            self.fail(f"unexpected git call: {args}")

        stdout = io.StringIO()
        with mock.patch.object(cleaner, "run_git", side_effect=fake_run_git), redirect_stdout(stdout):
            code = cleaner.main(["--dry-run"])
        self.assertEqual(code, 0)
        self.assertIn("No stale worktrees found", stdout.getvalue())

    def test_dry_run_never_invokes_destructive_git_commands(self):
        porcelain = f"""worktree {self.root}
HEAD abc
branch refs/heads/main

worktree {self.path}
HEAD def
branch refs/heads/feature

"""

        def fake_run_git(args, cwd=None):
            self.assertNotEqual(args[:3], ["worktree", "remove", "--force"])
            self.assertNotEqual(args[:2], ["branch", "-D"])
            if args[:3] == ["worktree", "list", "--porcelain"]:
                return completed(porcelain)
            if args[:3] == ["symbolic-ref", "--short", "HEAD"]:
                return completed("main\n")
            if args and args[0] == "merge-base":
                return completed("base\n")
            if args[:2] == ["log", "--no-merges"]:
                return completed("")
            self.fail(f"unexpected git call: {args}")

        stdout = io.StringIO()
        with mock.patch.object(cleaner, "run_git", side_effect=fake_run_git), redirect_stdout(stdout):
            code = cleaner.main([])
        self.assertEqual(code, 0)
        self.assertIn("Run with --apply to remove", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
