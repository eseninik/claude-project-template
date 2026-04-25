"""Unit tests for dual-history-archive.py."""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import logging
import os
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from datetime import date, timedelta
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("dual-history-archive.py")
SPEC = importlib.util.spec_from_file_location("dual_history_archive", SCRIPT_PATH)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def _set_mtime(path, days_ago, today_value):
    """Backdate file mtime so today_value - mtime_date == days_ago."""
    target = today_value - timedelta(days=days_ago)
    epoch = time.mktime(time.strptime(target.isoformat() + " 12:00:00", "%Y-%m-%d %H:%M:%S"))
    os.utime(path, (epoch, epoch))


def _make_pair(source, name, days_ago, today_value, with_diff=True):
    """Create task-<name>-result.md and optionally task-<name>.diff inside source."""
    source.mkdir(parents=True, exist_ok=True)
    result = source / ("task-" + name + "-result.md")
    result.write_text("# result for " + name + "\n", encoding="utf-8")
    _set_mtime(result, days_ago, today_value)
    diff = None
    if with_diff:
        diff = source / ("task-" + name + ".diff")
        diff.write_text("+++ diff for " + name + "\n", encoding="utf-8")
        _set_mtime(diff, days_ago, today_value)
    return result, diff


def _ns(**overrides):
    """Build an argparse.Namespace with sensible defaults for run()."""
    base = dict(
        source="work/codex-implementations",
        dest="work/codex-primary/dual-history",
        max_age_days=7,
        dry_run=False,
        apply=False,
        json=False,
        verbose=False,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


class DualHistoryArchiveTests(unittest.TestCase):
    TODAY = date(2026, 4, 25)

    def setUp(self):
        logging.getLogger().setLevel(logging.CRITICAL)

    def test_discovery_in_tmp_dir(self):
        """AC2: discover_results lists task-*-result.md files (non-recursive)."""
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            _make_pair(source, "A", days_ago=0, today_value=self.TODAY, with_diff=True)
            _make_pair(source, "B", days_ago=10, today_value=self.TODAY, with_diff=False)
            (source / "inline").mkdir()
            (source / "inline" / "task-N-result.md").write_text("nested\n", encoding="utf-8")
            (source / "other.md").write_text("ignored\n", encoding="utf-8")
            results = mod.discover_results(source)
            self.assertEqual({p.name for p in results}, {"task-A-result.md", "task-B-result.md"})

    def test_age_threshold_filtering(self):
        """AC3: stale iff age_days > max_age_days. 7 days = NOT stale, 8 = stale."""
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            _make_pair(source, "fresh", days_ago=3, today_value=self.TODAY, with_diff=False)
            _make_pair(source, "edge", days_ago=7, today_value=self.TODAY, with_diff=False)
            _make_pair(source, "old", days_ago=8, today_value=self.TODAY, with_diff=False)
            entries = mod.collect_entries(source, dest, 7, self.TODAY)
            stale = {Path(e["path"]).name: e["stale"] for e in entries}
            self.assertFalse(stale["task-fresh-result.md"])
            self.assertFalse(stale["task-edge-result.md"])
            self.assertTrue(stale["task-old-result.md"])

    def test_dry_run_does_not_move(self):
        """AC4 + Constraints: dry-run is read-only - no mkdir, no move."""
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            result, diff = _make_pair(source, "X", days_ago=30, today_value=self.TODAY)
            args = _ns(source=str(source), dest=str(dest), max_age_days=7, apply=False)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = mod.run(args, today_value=self.TODAY)
            self.assertEqual(rc, 0)
            self.assertTrue(result.exists())
            self.assertTrue(diff.exists())
            self.assertFalse(dest.exists())
            self.assertIn("Skipping (dry-run).", buf.getvalue())

    def test_apply_moves_result_and_diff(self):
        """AC6+AC7: --apply moves both result.md and matching .diff together."""
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            result, diff = _make_pair(source, "Y", days_ago=40, today_value=self.TODAY)
            args = _ns(source=str(source), dest=str(dest), max_age_days=7, apply=True)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = mod.run(args, today_value=self.TODAY)
            self.assertEqual(rc, 0)
            self.assertFalse(result.exists())
            self.assertFalse(diff.exists())
            moved_result = dest / "2026-03" / "task-Y-result.md"
            moved_diff = dest / "2026-03" / "task-Y.diff"
            self.assertTrue(moved_result.exists())
            self.assertTrue(moved_diff.exists())

    def test_apply_creates_yyyy_mm_subdir(self):
        """AC6: dest/<YYYY-MM>/ is created when missing."""
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            self.assertFalse(dest.exists())
            _make_pair(source, "Z", days_ago=15, today_value=self.TODAY, with_diff=False)
            args = _ns(source=str(source), dest=str(dest), max_age_days=7, apply=True)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = mod.run(args, today_value=self.TODAY)
            self.assertEqual(rc, 0)
            subdirs = [p for p in dest.iterdir() if p.is_dir()]
            self.assertEqual(len(subdirs), 1)
            self.assertRegex(subdirs[0].name, r"^\d{4}-\d{2}$")

    def test_per_entry_failure_does_not_abort(self):
        """AC6: continues on per-entry failure; exit 1 reported."""
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            ok_result, _ = _make_pair(source, "ok", days_ago=20, today_value=self.TODAY, with_diff=False)
            bad_result, _ = _make_pair(source, "bad", days_ago=20, today_value=self.TODAY, with_diff=False)

            real_move = mod.shutil.move

            def fake_move(src, dst, *a, **kw):
                if "task-bad-result.md" in str(src):
                    raise OSError("simulated permission denied")
                return real_move(src, dst, *a, **kw)

            mod.shutil.move = fake_move
            try:
                args = _ns(source=str(source), dest=str(dest), max_age_days=7, apply=True)
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = mod.run(args, today_value=self.TODAY)
            finally:
                mod.shutil.move = real_move
            self.assertEqual(rc, 1)
            self.assertFalse(ok_result.exists())
            self.assertTrue(bad_result.exists())

    def test_json_round_trip(self):
        """AC5: --json emits required fields and is JSON-parseable."""
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            _make_pair(source, "S1", days_ago=30, today_value=self.TODAY, with_diff=True)
            _make_pair(source, "S2", days_ago=2, today_value=self.TODAY, with_diff=False)
            args = _ns(source=str(source), dest=str(dest), max_age_days=7, json=True)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = mod.run(args, today_value=self.TODAY)
            self.assertEqual(rc, 0)
            payload = json.loads(buf.getvalue())
            self.assertEqual(payload["found"], 2)
            self.assertEqual(payload["stale"], 1)
            self.assertEqual(payload["kept"], 1)
            self.assertEqual(payload["window_days"], 7)
            self.assertEqual(set(payload), {"source", "dest", "window_days", "found", "stale", "kept", "entries"})
            self.assertEqual(set(payload["entries"][0]), {"path", "age_days", "dest_path", "apply_status"})

    def test_no_stale_entries_exit_zero(self):
        """AC4: no stale entries => exit 0, friendly message."""
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            _make_pair(source, "fresh1", days_ago=1, today_value=self.TODAY, with_diff=False)
            _make_pair(source, "fresh2", days_ago=3, today_value=self.TODAY, with_diff=True)
            args = _ns(source=str(source), dest=str(dest), max_age_days=7, apply=False)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = mod.run(args, today_value=self.TODAY)
            self.assertEqual(rc, 0)
            self.assertIn("No stale entries found.", buf.getvalue())

    def test_diff_missing_only_moves_result(self):
        """AC2/AC7: when no .diff sibling exists, only result.md moves and exit 0."""
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            result, _ = _make_pair(source, "alone", days_ago=20, today_value=self.TODAY, with_diff=False)
            args = _ns(source=str(source), dest=str(dest), max_age_days=7, apply=True)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = mod.run(args, today_value=self.TODAY)
            self.assertEqual(rc, 0)
            self.assertFalse(result.exists())
            moved = list(dest.rglob("task-alone-result.md"))
            self.assertEqual(len(moved), 1)
            self.assertEqual(list(dest.rglob("task-alone.diff")), [])

    def test_subdirs_not_recursed(self):
        """AC2: sub-dirs (e.g. inline/) NOT recursed by default."""
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "src"
            (source / "inline").mkdir(parents=True)
            nested = source / "inline" / "task-nested-result.md"
            nested.write_text("nested\n", encoding="utf-8")
            _set_mtime(nested, 30, self.TODAY)
            results = mod.discover_results(source)
            self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
