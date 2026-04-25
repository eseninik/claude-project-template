#!/usr/bin/env python3
"""Unit tests for verdict-summarizer.py."""
from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_SCRIPT = _THIS_DIR / "verdict-summarizer.py"
_SPEC = importlib.util.spec_from_file_location("verdict_summarizer", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
summarizer = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(summarizer)


def _write_verdict(root: Path, feature: str, name: str, data: dict) -> Path:
    path = root / feature / "verdicts" / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _verdict(
    task_id: str,
    timestamp: str,
    winner: str = "claude",
    delta: float = 0.1,
    claude: float = 0.6,
    codex: float = 0.5,
    axes: dict | None = None,
) -> dict:
    return {
        "task_id": task_id,
        "winner": winner,
        "delta": delta,
        "scores": {"claude": claude, "codex": codex},
        "axes": axes if axes is not None else {},
        "timestamp": timestamp,
    }


class TestVerdictSummarizer(unittest.TestCase):
    def test_single_happy_path_verdict_outputs_table_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "work"
            _write_verdict(root, "fixes", "one", _verdict("FIX-A", "2026-04-24T22:20:34", "tie", -0.0015, 0.504, 0.5055))
            output = summarizer.render_markdown(summarizer.build_report(root, None, None, 3))
            self.assertIn("| FIX-A | tie | -0.0015 | 0.5040 | 0.5055 | 2026-04-24 22:20 |", output)

    def test_multiple_verdicts_sorted_by_timestamp_then_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "work"
            _write_verdict(root, "fixes", "b", _verdict("B", "2026-04-24T22:21:00"))
            _write_verdict(root, "fixes", "a2", _verdict("A2", "2026-04-24T22:20:00"))
            _write_verdict(root, "fixes", "a1", _verdict("A1", "2026-04-24T22:20:00"))
            verdicts = summarizer.build_report(root, None, None, 3)["verdicts"]
            self.assertEqual([item["task_id"] for item in verdicts], ["A1", "A2", "B"])

    def test_malformed_json_skipped_and_continue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, self.assertLogs("verdict_summarizer", level="WARNING") as logs:
            root = Path(tmp) / "work"
            _write_verdict(root, "fixes", "good", _verdict("GOOD", "2026-04-24T22:20:00"))
            bad = root / "fixes" / "verdicts" / "bad.json"
            bad.write_text("{bad", encoding="utf-8")
            report = summarizer.build_report(root, None, None, 3)
            self.assertEqual(report["summary"]["verdicts"], 1)
            self.assertIn("malformed_json", "\n".join(logs.output))

    def test_feature_filter_restricts_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "work"
            _write_verdict(root, "fixes", "fix", _verdict("FIX", "2026-04-24T22:20:00"))
            _write_verdict(root, "validation", "val", _verdict("VAL", "2026-04-24T22:20:00"))
            verdicts = summarizer.build_report(root, "validation", None, 3)["verdicts"]
            self.assertEqual([item["task_id"] for item in verdicts], ["VAL"])

    def test_since_days_filter_respects_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "work"
            _write_verdict(root, "fixes", "old", _verdict("OLD", "2026-04-20T00:00:00+00:00"))
            _write_verdict(root, "fixes", "new", _verdict("NEW", "2026-04-24T12:00:00+00:00"))
            now = datetime(2026, 4, 25, 12, 0, tzinfo=timezone.utc)
            verdicts = summarizer.build_report(root, None, 1, 3, generated_at=now)["verdicts"]
            self.assertEqual([item["task_id"] for item in verdicts], ["NEW"])

    def test_winners_count_consistent_with_verdicts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "work"
            _write_verdict(root, "fixes", "c", _verdict("C", "2026-04-24T22:20:00", "claude"))
            _write_verdict(root, "fixes", "x", _verdict("X", "2026-04-24T22:21:00", "codex"))
            _write_verdict(root, "fixes", "t", _verdict("T", "2026-04-24T22:22:00", "tie"))
            summary = summarizer.build_report(root, None, None, 3)["summary"]
            self.assertEqual(summary, {"verdicts": 3, "claude": 1, "codex": 1, "tie": 1})

    def test_top_axes_returns_top_k_by_mean_abs_delta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "work"
            axes = {
                "small": {"claude": 0.1, "codex": 0.2},
                "large": {"claude": 1.0, "codex": 0.0},
                "same": {"claude": 0.5, "codex": 0.5},
            }
            _write_verdict(root, "fixes", "one", _verdict("A", "2026-04-24T22:20:00", axes=axes))
            axis_rows = summarizer.build_report(root, None, None, 1)["axes"]
            self.assertEqual(axis_rows, [{"name": "large", "contested_count": 1, "mean_abs_delta": 1.0}])

    def test_json_schema_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "work"
            _write_verdict(root, "fixes", "one", _verdict("FIX-A", "2026-04-24T22:20:00"))
            out = io.StringIO()
            with redirect_stdout(out):
                code = summarizer.main(["--root", str(root), "--json"])
            payload = json.loads(out.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(set(payload), {"generated_at", "root", "feature", "window_days", "summary", "verdicts", "axes"})
            self.assertEqual(payload["verdicts"][0]["task_id"], "FIX-A")

    def test_empty_input_exit_zero_with_empty_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "work"
            report = summarizer.build_report(root, None, None, 3)
            self.assertEqual(report["summary"], {"verdicts": 0, "claude": 0, "codex": 0, "tie": 0})
            self.assertEqual(report["verdicts"], [])
            self.assertIn("No verdicts found under", summarizer.render_markdown(report))

    def test_missing_axes_field_still_summarized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "work"
            data = _verdict("NOAXES", "2026-04-24T22:20:00")
            data.pop("axes")
            _write_verdict(root, "fixes", "one", data)
            report = summarizer.build_report(root, None, None, 3)
            self.assertEqual(report["summary"]["verdicts"], 1)
            self.assertEqual(report["axes"], [])


if __name__ == "__main__":
    unittest.main()
