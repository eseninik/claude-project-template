#!/usr/bin/env python3
"""Unit tests for codex-cost-report.py (AC10).

Covers:
- single happy-path log -> expected row + JSON shape (test_happy_path)
- multiple runs sorted by start_ts asc, tie-break task_id asc (test_sort_order)
- malformed JSON line skipped, parse continues (test_malformed_skipped)
- since-hours filter drops old runs (test_since_hours)
- status counts: pass / fail (test_status_counts)
- JSON round-trip is valid + has all keys (test_json_roundtrip)
- empty log dir -> exit 0 + zero summary (test_empty_dir)
- duration_s computed from ts diff (test_duration_computed)
- task_id_from_argv pulls --task path stem (test_task_id_from_argv)

Stdlib only. Discovers tests itself (does not require pytest).
"""
from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "codex-cost-report.py"

# Import as module despite hyphenated filename.
_spec = importlib.util.spec_from_file_location("codex_cost_report", str(SCRIPT))
ccr = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
sys.modules['codex_cost_report'] = ccr
_spec.loader.exec_module(ccr)


def _entry(ts, msg, **fields):
    """Build a single JSON log line."""
    rec = {"ts": ts, "level": "INFO", "logger": "codex_implement", "msg": msg}
    rec.update(fields)
    return json.dumps(rec)


def _write_log(tmpdir: Path, name: str, lines):
    """Write list of strings as a log file."""
    p = tmpdir / name
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def _good_run(start, end, *, task_id="T1", status="pass", model="gpt-5.5", reasoning="medium",
              returncode=0, stdout_len=12, stderr_len=3):
    """Build the canonical 4-line entry/run_codex/exit_codex/exit_main sequence."""
    argv = ["--task", f"tasks/T{task_id[1:] if task_id.startswith('T') else task_id}.md",
            "--worktree", "."]
    return [
        _entry(start, "entry: main", argv=argv),
        _entry(start, "entry: run_codex", model=model, reasoning=reasoning),
        _entry(end, "exit: run_codex", returncode=returncode,
               stdout_len=stdout_len, stderr_len=stderr_len, self_report=0),
        _entry(end, "exit: main", status=status, exit_code=0 if status == "pass" else 1),
    ]


class TestParse(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_happy_path(self):
        """Single happy-path log -> one run with expected fields."""
        lines = _good_run("2026-04-25T10:00:00+00:00", "2026-04-25T10:01:30+00:00")
        log = _write_log(self.tmp, "codex-implement-T1.log", lines)
        runs = ccr.parse_log_file(log)
        self.assertEqual(len(runs), 1)
        r = runs[0]
        self.assertEqual(r.task_id, "1")
        self.assertEqual(r.status, "pass")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout_len, 12)
        self.assertEqual(r.stderr_len, 3)
        self.assertEqual(r.model, "gpt-5.5")
        self.assertEqual(r.reasoning, "medium")
        self.assertAlmostEqual(r.duration_s, 90.0, places=2)

    def test_sort_order(self):
        """Multiple runs sorted by start_ts asc, tie-break task_id asc (AC8)."""
        log_a = _write_log(self.tmp, "codex-implement-TA.log",
                           _good_run("2026-04-25T10:00:00+00:00",
                                     "2026-04-25T10:00:30+00:00", task_id="T2"))
        log_b = _write_log(self.tmp, "codex-implement-TB.log",
                           _good_run("2026-04-25T09:00:00+00:00",
                                     "2026-04-25T09:01:00+00:00", task_id="T1"))
        runs = ccr.collect_runs(self.tmp, None)
        self.assertEqual([r.start_ts for r in runs],
                         ["2026-04-25T09:00:00+00:00", "2026-04-25T10:00:00+00:00"])
        self.assertEqual([r.task_id for r in runs], ["1", "2"])

    def test_malformed_skipped(self):
        """Malformed JSON line is skipped; surrounding good lines still parse."""
        good = _good_run("2026-04-25T10:00:00+00:00", "2026-04-25T10:00:05+00:00")
        # Inject garbage between entry: main and exit: main
        garbage = ["this is not valid json {{{ "]
        lines = good[:1] + garbage + good[1:]
        log = _write_log(self.tmp, "codex-implement-T7.log", lines)
        runs = ccr.parse_log_file(log)
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].status, "pass")

    def test_since_hours(self):
        """--since-hours window drops runs older than cutoff (AC1)."""
        old_start = (datetime.now(timezone.utc) - timedelta(hours=10)).isoformat()
        old_end = (datetime.now(timezone.utc) - timedelta(hours=10, seconds=-30)).isoformat()
        new_start = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        new_end = (datetime.now(timezone.utc) - timedelta(minutes=9)).isoformat()
        _write_log(self.tmp, "codex-implement-Told.log", _good_run(old_start, old_end, task_id="Told"))
        _write_log(self.tmp, "codex-implement-Tnew.log", _good_run(new_start, new_end, task_id="Tnew"))
        runs = ccr.collect_runs(self.tmp, since_hours=1.0)
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].task_id, "Tnew")

    def test_status_counts(self):
        """Status counts: pass + fail aggregate correctly (AC5/AC6)."""
        _write_log(self.tmp, "codex-implement-T1.log",
                   _good_run("2026-04-25T10:00:00+00:00", "2026-04-25T10:00:10+00:00",
                             task_id="T1", status="pass"))
        _write_log(self.tmp, "codex-implement-T2.log",
                   _good_run("2026-04-25T10:01:00+00:00", "2026-04-25T10:01:10+00:00",
                             task_id="T2", status="fail"))
        runs = ccr.collect_runs(self.tmp, None)
        s = ccr.summarise(runs)
        self.assertEqual(s["runs"], 2)
        self.assertEqual(s["pass"], 1)
        self.assertEqual(s["fail"], 1)
        self.assertAlmostEqual(s["total_duration_s"], 20.0, places=2)

    def test_json_roundtrip(self):
        """--json emits parseable JSON with all required top keys + per-run fields (AC6)."""
        _write_log(self.tmp, "codex-implement-T1.log",
                   _good_run("2026-04-25T10:00:00+00:00", "2026-04-25T10:00:30+00:00"))
        runs = ccr.collect_runs(self.tmp, None)
        s = ccr.summarise(runs)
        text = ccr.render_json(runs, s, self.tmp, None, "2026-04-25T11:00:00+00:00")
        data = json.loads(text)
        for k in ("generated_at", "log_dir", "window_hours", "summary", "runs"):
            self.assertIn(k, data)
        self.assertEqual(len(data["runs"]), 1)
        run = data["runs"][0]
        for k in ("task_id", "log_file", "start_ts", "end_ts", "duration_s", "status",
                  "returncode", "stdout_len", "stderr_len", "model", "reasoning"):
            self.assertIn(k, run)

    def test_empty_dir(self):
        """No matching logs -> empty runs list, zero summary, exit 0 (AC7)."""
        runs = ccr.collect_runs(self.tmp, None)
        self.assertEqual(runs, [])
        s = ccr.summarise(runs)
        self.assertEqual(s, {"runs": 0, "pass": 0, "fail": 0, "total_duration_s": 0})
        # main() also exits 0 against empty dir.
        with redirect_stdout(io.StringIO()):
            rc = ccr.main(["--log-dir", str(self.tmp)])
        self.assertEqual(rc, 0)

    def test_duration_computed(self):
        """duration_s derives from ts diff (AC4)."""
        lines = _good_run("2026-04-25T10:00:00+00:00", "2026-04-25T10:02:30+00:00")
        log = _write_log(self.tmp, "codex-implement-T9.log", lines)
        runs = ccr.parse_log_file(log)
        self.assertAlmostEqual(runs[0].duration_s, 150.0, places=2)

    def test_task_id_from_argv(self):
        """task_id_from_argv pulls --task path stem; falls back when absent."""
        # Numeric Tn form keeps the suffix (T2 -> '2')
        self.assertEqual(ccr.task_id_from_argv(["--task", "tasks/T2.md"], "fb"), "2")
        # task-foo form keeps the rest
        self.assertEqual(ccr.task_id_from_argv(["--task", "tasks/task-bar.md"], "fb"), "bar")
        # Missing argv -> fallback
        self.assertEqual(ccr.task_id_from_argv(None, "fb"), "fb")
        self.assertEqual(ccr.task_id_from_argv([], "fb"), "fb")

    def test_incomplete_run(self):
        """A run that never sees exit: main is still emitted (status=incomplete)."""
        # Drop the trailing exit: main
        lines = _good_run("2026-04-25T10:00:00+00:00", "2026-04-25T10:00:05+00:00")[:-1]
        log = _write_log(self.tmp, "codex-implement-Tinc.log", lines)
        runs = ccr.parse_log_file(log)
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].status, "incomplete")

    def test_naive_ts_tolerated(self):
        """Naive (no-tz) ts must still parse + compute duration."""
        lines = _good_run("2026-04-25T10:00:00", "2026-04-25T10:00:30")
        log = _write_log(self.tmp, "codex-implement-Tnaive.log", lines)
        runs = ccr.parse_log_file(log)
        self.assertAlmostEqual(runs[0].duration_s, 30.0, places=2)


if __name__ == "__main__":
    unittest.main(verbosity=2)