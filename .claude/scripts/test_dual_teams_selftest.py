#!/usr/bin/env python3
"""Unit tests for dual-teams-selftest.py."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import unittest
from pathlib import Path
from unittest import mock


_THIS = Path(__file__).resolve()
_SCRIPT = _THIS.parent / "dual-teams-selftest.py"

spec = importlib.util.spec_from_file_location("dual_teams_selftest", _SCRIPT)
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load {_SCRIPT}")
selftest = importlib.util.module_from_spec(spec)
sys.modules["dual_teams_selftest"] = selftest
spec.loader.exec_module(selftest)


class DualTeamsSelftestTests(unittest.TestCase):
    def test_every_check_passes_when_fixes_are_present(self) -> None:
        report = selftest.run_selftest(selftest.SelfTestConfig())

        self.assertEqual(report.summary["checks"], 6)
        self.assertEqual(report.summary["passed"], 6)
        self.assertEqual(report.summary["failed"], 0)
        self.assertTrue(all(result.status == "PASS" for result in report.results))

    def test_reports_fail_when_sentinel_is_missing(self) -> None:
        config = selftest.SelfTestConfig(fault_missing_sentinel="codex")

        report = selftest.run_selftest(config)

        self.assertGreater(report.summary["failed"], 0)
        failures = {result.name for result in report.results if result.status == "FAIL"}
        self.assertIn("is_dual_teams_worktree-true-on-V2", failures)

    def test_reports_fail_when_preflight_rejects(self) -> None:
        original_loader = selftest.load_integrations

        def fake_loader(project_root: Path):
            integrations = original_loader(project_root)

            def reject_preflight(worktree: Path) -> str:
                raise RuntimeError(f"rejected {worktree.name}")

            integrations.preflight = reject_preflight
            return integrations

        with mock.patch.object(selftest, "load_integrations", fake_loader):
            report = selftest.run_selftest(selftest.SelfTestConfig())

        failures = {result.name for result in report.results if result.status == "FAIL"}
        self.assertIn("preflight-clean-with-sentinel-V1", failures)
        self.assertIn("preflight-clean-with-sentinel-V2", failures)

    def test_json_schema_round_trip_is_strict(self) -> None:
        report = selftest.run_selftest(selftest.SelfTestConfig())

        payload = json.loads(selftest.render_json_report(report))

        self.assertEqual(set(payload), {"started_at", "duration_ms", "summary", "results"})
        self.assertEqual(set(payload["summary"]), {"checks", "passed", "failed"})
        for result in payload["results"]:
            self.assertEqual(set(result), {"name", "status", "detail", "duration_ms"})

    def test_duration_fields_are_positive_integer_ms(self) -> None:
        report = selftest.run_selftest(selftest.SelfTestConfig())

        self.assertIsInstance(report.duration_ms, int)
        self.assertGreater(report.duration_ms, 0)
        for result in report.results:
            self.assertIsInstance(result.duration_ms, int)
            self.assertGreater(result.duration_ms, 0)

    def test_keep_tmpdir_keeps_the_directory(self) -> None:
        report = selftest.run_selftest(selftest.SelfTestConfig(keep_tmpdir=True))

        self.assertIsNotNone(report.tmpdir)
        self.assertTrue(report.tmpdir.is_dir())
        shutil.rmtree(report.tmpdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
