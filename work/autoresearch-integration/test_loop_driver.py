"""Behavioral tests for loop-driver.py in experiment-loop skill.

Covers the Codex-flagged bug fix (find_best_kept_metric scans entire journal with
direction awareness, ignoring trailing reverts) plus the two helpers it relies on:
is_improvement and parse_last_metric.

Run:
    py -3 work/autoresearch-integration/test_loop_driver.py
"""

import importlib.util
import logging
import sys
import tempfile
import unittest
from pathlib import Path


DRIVER_PATH = Path(".claude/shared/templates/new-project/.claude/skills/experiment-loop/templates/loop-driver.py")


def load_loop_driver():
    """Import loop-driver.py as a module without running its main()."""
    spec = importlib.util.spec_from_file_location("loop_driver", DRIVER_PATH)
    module = importlib.util.module_from_spec(spec)
    # Silence logging to avoid polluting test output
    logging.disable(logging.CRITICAL)
    spec.loader.exec_module(module)
    return module


class TestIsImprovement(unittest.TestCase):
    def setUp(self):
        self.driver = load_loop_driver()

    def test_higher_direction_better_wins(self):
        self.assertTrue(self.driver.is_improvement(0.8, 0.5, "higher"))

    def test_higher_direction_worse_loses(self):
        self.assertFalse(self.driver.is_improvement(0.3, 0.5, "higher"))

    def test_higher_direction_equal_is_not_improvement(self):
        self.assertFalse(self.driver.is_improvement(0.5, 0.5, "higher"))

    def test_lower_direction_better_wins(self):
        self.assertTrue(self.driver.is_improvement(0.3, 0.5, "lower"))

    def test_lower_direction_worse_loses(self):
        self.assertFalse(self.driver.is_improvement(0.8, 0.5, "lower"))

    def test_lower_direction_equal_is_not_improvement(self):
        self.assertFalse(self.driver.is_improvement(0.5, 0.5, "lower"))

    def test_none_old_always_improves_higher(self):
        self.assertTrue(self.driver.is_improvement(0.0, None, "higher"))

    def test_none_old_always_improves_lower(self):
        self.assertTrue(self.driver.is_improvement(1.0, None, "lower"))


class TestParseLastMetric(unittest.TestCase):
    def setUp(self):
        self.driver = load_loop_driver()

    def test_missing_file_returns_none(self):
        self.assertEqual(self.driver.parse_last_metric(Path("/nonexistent-journal.md")), (None, None))

    def test_empty_file_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            j = Path(tmp) / "journal.md"
            j.touch()
            self.assertEqual(self.driver.parse_last_metric(j), (None, None))

    def test_last_line_kept_yes(self):
        with tempfile.TemporaryDirectory() as tmp:
            j = Path(tmp) / "journal.md"
            j.write_text(
                "iteration=1 metric=0.5 kept=no change=bad\n"
                "iteration=2 metric=0.7 kept=yes change=good\n",
                encoding="utf-8",
            )
            metric, kept = self.driver.parse_last_metric(j)
            self.assertEqual(metric, 0.7)
            self.assertEqual(kept, "yes")

    def test_skips_trailing_blank_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            j = Path(tmp) / "journal.md"
            j.write_text(
                "iteration=1 metric=0.5 kept=yes change=good\n\n\n",
                encoding="utf-8",
            )
            metric, kept = self.driver.parse_last_metric(j)
            self.assertEqual(metric, 0.5)
            self.assertEqual(kept, "yes")

    def test_negative_metric_parses(self):
        with tempfile.TemporaryDirectory() as tmp:
            j = Path(tmp) / "journal.md"
            j.write_text("iteration=1 metric=-0.042 kept=no change=regression\n", encoding="utf-8")
            metric, kept = self.driver.parse_last_metric(j)
            self.assertEqual(metric, -0.042)
            self.assertEqual(kept, "no")


class TestFindBestKeptMetric(unittest.TestCase):
    """Covers the Codex-flagged bug fix: on --resume, trailing revert must not erase
    the incumbent best_metric."""

    def setUp(self):
        self.driver = load_loop_driver()

    def test_missing_file_returns_none(self):
        self.assertIsNone(self.driver.find_best_kept_metric(Path("/nonexistent"), "higher"))

    def test_empty_journal_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            j = Path(tmp) / "journal.md"
            j.touch()
            self.assertIsNone(self.driver.find_best_kept_metric(j, "higher"))

    def test_no_kept_lines_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            j = Path(tmp) / "journal.md"
            j.write_text(
                "iteration=1 metric=0.5 kept=no change=bad\n"
                "iteration=2 metric=0.7 kept=no change=worse\n",
                encoding="utf-8",
            )
            self.assertIsNone(self.driver.find_best_kept_metric(j, "higher"))

    def test_ignores_trailing_revert_higher_direction(self):
        """Key scenario: iter 2 was the best kept win; iter 3 reverted with higher fitness
        (hypothetically — in practice reverts are losses, but plateau counter logic must
        still treat reverted iterations as non-incumbents)."""
        with tempfile.TemporaryDirectory() as tmp:
            j = Path(tmp) / "journal.md"
            j.write_text(
                "iteration=1 metric=0.5 kept=yes change=baseline_kept\n"
                "iteration=2 metric=0.9 kept=yes change=big_win\n"
                "iteration=3 metric=0.7 kept=no change=reverted\n",
                encoding="utf-8",
            )
            self.assertEqual(self.driver.find_best_kept_metric(j, "higher"), 0.9)

    def test_direction_lower_finds_smallest_kept(self):
        with tempfile.TemporaryDirectory() as tmp:
            j = Path(tmp) / "journal.md"
            j.write_text(
                "iteration=1 metric=0.8 kept=yes change=start\n"
                "iteration=2 metric=0.3 kept=yes change=better_lower\n"
                "iteration=3 metric=0.5 kept=no change=reverted\n",
                encoding="utf-8",
            )
            self.assertEqual(self.driver.find_best_kept_metric(j, "lower"), 0.3)

    def test_only_kept_yes_lines_considered(self):
        with tempfile.TemporaryDirectory() as tmp:
            j = Path(tmp) / "journal.md"
            j.write_text(
                "iteration=1 metric=0.1 kept=yes change=kept_low\n"
                "iteration=2 metric=0.9 kept=no change=rejected_high\n"
                "iteration=3 metric=0.4 kept=yes change=kept_mid\n",
                encoding="utf-8",
            )
            # direction=higher, best kept should be 0.4, NOT 0.9 (which was rejected)
            self.assertEqual(self.driver.find_best_kept_metric(j, "higher"), 0.4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
