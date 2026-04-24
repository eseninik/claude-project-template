#!/usr/bin/env python3
"""Unit tests for judge.py / judge_axes.py (AC9 >=10 tests).

Run: python .claude/scripts/test_judge.py

Uses unittest + pytest-style direct invocation. Zero deps beyond stdlib
so it runs in the judge's own CI sandbox without tool installs.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import judge  # noqa: E402
import judge_axes  # noqa: E402
from judge_axes import (  # noqa: E402
    AxisResult, TestRun, biggest_delta_rationale, decide_winner,
    score_diff_size, score_lint_clean, score_logging_coverage,
    score_tests_passed, weighted_aggregate,
)


# ------------------------ helpers ------------------------ #


def _init_git_repo(repo: Path) -> None:
    """Bare-minimum git repo with one empty initial commit."""
    for args in (
        ["git", "init", "-q", "-b", "main"],
        ["git", "config", "user.email", "t@example.com"],
        ["git", "config", "user.name", "t"],
        ["git", "commit", "-q", "--allow-empty", "-m", "init"],
    ):
        subprocess.run(args, cwd=str(repo), check=True, capture_output=True)


def _add_file(repo: Path, rel: str, content: str, commit: bool = False) -> Path:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    if commit:
        subprocess.run(["git", "add", rel], cwd=str(repo), check=True,
                       capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", f"add {rel}"],
                       cwd=str(repo), check=True, capture_output=True)
    return p


# ------------------------ tests_passed ------------------------ #


class TestTestsPassed(unittest.TestCase):
    def test_all_pass(self) -> None:
        runs = [TestRun(command="t1", exit_code=0, duration_s=0.1),
                TestRun(command="t2", exit_code=0, duration_s=0.1)]
        res = score_tests_passed(runs)
        self.assertAlmostEqual(res.score, 1.0)
        self.assertFalse(res.skipped)

    def test_some_pass(self) -> None:
        runs = [TestRun(command="t1", exit_code=0, duration_s=0.1),
                TestRun(command="t2", exit_code=1, duration_s=0.1),
                TestRun(command="t3", exit_code=0, duration_s=0.1)]
        res = score_tests_passed(runs)
        self.assertAlmostEqual(res.score, 2 / 3)

    def test_none_pass(self) -> None:
        runs = [TestRun(command="t1", exit_code=1, duration_s=0.1)]
        res = score_tests_passed(runs)
        self.assertEqual(res.score, 0.0)

    def test_empty_skipped(self) -> None:
        res = score_tests_passed([])
        self.assertTrue(res.skipped)
        self.assertEqual(res.skip_reason, "no test commands")


# ------------------------ diff_size ------------------------ #


class TestDiffSize(unittest.TestCase):
    def test_inverse_normalization(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)
            _add_file(repo, "a.py", "# pre\n", commit=True)
            # Add 50 lines uncommitted
            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
            res = score_diff_size(repo, cap_lines=500)
            # ~50 added, cap 500 => 1 - 50/500 = 0.9
            self.assertGreater(res.score, 0.85)
            self.assertLess(res.score, 0.95)
            self.assertEqual(res.raw["added"], 50)

    def test_empty_diff_max_score(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)
            res = score_diff_size(repo, cap_lines=500)
            self.assertAlmostEqual(res.score, 1.0)
            self.assertEqual(res.raw["added"], 0)


# ------------------------ logging_coverage ------------------------ #


class TestLoggingCoverage(unittest.TestCase):
    def test_function_with_logger(self) -> None:
        diff = textwrap.dedent("""\
            diff --git a/x.py b/x.py
            @@ -0,0 +1,3 @@
            +def foo():
            +    logger.info("hi")
            +    return 1
            """)
        res = score_logging_coverage(Path("."), diff_text=diff)
        self.assertAlmostEqual(res.score, 1.0)
        self.assertEqual(res.raw["covered"], 1)

    def test_function_without_logger(self) -> None:
        diff = textwrap.dedent("""\
            diff --git a/x.py b/x.py
            @@ -0,0 +1,3 @@
            +def foo():
            +    x = 1
            +    return x
            """)
        res = score_logging_coverage(Path("."), diff_text=diff)
        self.assertAlmostEqual(res.score, 0.0)
        self.assertEqual(res.raw["covered"], 0)

    def test_edge_no_new_functions(self) -> None:
        diff = "diff --git a/x.py b/x.py\n+x = 1\n"
        res = score_logging_coverage(Path("."), diff_text=diff)
        self.assertTrue(res.skipped)
        self.assertEqual(res.skip_reason, "no new python functions")

    def test_mixed_functions(self) -> None:
        diff = textwrap.dedent("""\
            diff --git a/x.py b/x.py
            @@ -0,0 +1,6 @@
            +def foo():
            +    logger.info("ok")
            +    return 1
            +def bar():
            +    return 2
            +
            """)
        res = score_logging_coverage(Path("."), diff_text=diff)
        self.assertAlmostEqual(res.score, 0.5)
        self.assertEqual(res.raw["covered"], 1)
        self.assertEqual(res.raw["total"], 2)


# ------------------------ lint_clean ------------------------ #


class TestLintClean(unittest.TestCase):
    def test_clean_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            clean = _add_file(repo, "clean.py", "x = 1\n")
            res = score_lint_clean(repo, files_override=[clean])
            self.assertAlmostEqual(res.score, 1.0)
            self.assertEqual(res.raw["compile_errors"], 0)

    def test_syntax_error(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            bad = _add_file(repo, "bad.py", "def :\n")
            res = score_lint_clean(repo, files_override=[bad])
            self.assertLess(res.score, 1.0)
            self.assertEqual(res.raw["compile_errors"], 1)

    def test_no_files_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            res = score_lint_clean(repo, files_override=[])
            self.assertTrue(res.skipped)
            self.assertEqual(res.skip_reason, "no modified .py files")


# ------------------------ optional tool skip ------------------------ #


class TestOptionalToolSkip(unittest.TestCase):
    def test_complexity_skipped_when_radon_absent(self) -> None:
        with patch.object(judge_axes, "_module_available", return_value=False):
            res = judge_axes.score_complexity(Path("."))
            self.assertTrue(res.skipped)
            self.assertIn("radon", res.skip_reason or "")

    def test_type_check_skipped_when_mypy_absent(self) -> None:
        with patch.object(judge_axes, "_module_available", return_value=False):
            res = judge_axes.score_type_check(Path("."))
            self.assertTrue(res.skipped)
            self.assertIn("mypy", res.skip_reason or "")


# ------------------------ weighted aggregate + winner ------------------------ #


class TestWeightedAggregate(unittest.TestCase):
    def test_weighted_correctness(self) -> None:
        axes = [
            AxisResult(name="a", score=1.0, weight=10),
            AxisResult(name="b", score=0.5, weight=2),
            AxisResult(name="c", score=0.0, weight=2),
        ]
        # (10*1 + 2*0.5 + 2*0) / 14 = 11/14 ~ 0.786
        agg = weighted_aggregate(axes)
        self.assertAlmostEqual(agg, 11 / 14, places=4)

    def test_skipped_ignored(self) -> None:
        axes = [
            AxisResult(name="a", score=1.0, weight=10),
            AxisResult(name="b", score=0.0, weight=100, skipped=True),
        ]
        self.assertAlmostEqual(weighted_aggregate(axes), 1.0)

    def test_all_skipped_zero(self) -> None:
        axes = [AxisResult(name="a", score=1.0, weight=10, skipped=True)]
        self.assertEqual(weighted_aggregate(axes), 0.0)


class TestWinnerDecision(unittest.TestCase):
    def test_claude_wins(self) -> None:
        w, d = decide_winner(0.80, 0.70)
        self.assertEqual(w, "claude")
        self.assertAlmostEqual(d, 0.10)

    def test_codex_wins(self) -> None:
        w, d = decide_winner(0.70, 0.90)
        self.assertEqual(w, "codex")

    def test_tie_within_delta(self) -> None:
        w, d = decide_winner(0.81, 0.80)  # delta 0.01 < 0.02
        self.assertEqual(w, "tie")

    def test_tie_custom_delta(self) -> None:
        w, _ = decide_winner(0.90, 0.70, tie_delta=0.25)
        self.assertEqual(w, "tie")


# ------------------------ verdict JSON schema ------------------------ #


class TestVerdictSchema(unittest.TestCase):
    def test_verdict_is_valid_json(self) -> None:
        c_axes = [AxisResult(name="tests_passed", score=1.0, weight=10)]
        k_axes = [AxisResult(name="tests_passed", score=0.5, weight=10)]
        verdict = judge.build_verdict("demo", c_axes, k_axes, tie_delta=0.02)
        blob = json.dumps(verdict)
        parsed = json.loads(blob)
        self.assertEqual(parsed["task_id"], "demo")
        self.assertEqual(parsed["winner"], "claude")
        self.assertIn("scores", parsed)
        self.assertIn("claude", parsed["scores"])
        self.assertIn("codex", parsed["scores"])
        self.assertIn("aggregate", parsed["scores"]["claude"])
        self.assertIn("axes", parsed["scores"]["claude"])
        self.assertIn("rationale_auto", parsed)
        self.assertIsNone(parsed["rationale_manual"])

    def test_rationale_cites_biggest_delta(self) -> None:
        c_axes = [
            AxisResult(name="tests_passed", score=1.0, weight=10),
            AxisResult(name="diff_size", score=0.5, weight=2),
        ]
        k_axes = [
            AxisResult(name="tests_passed", score=0.9, weight=10),
            AxisResult(name="diff_size", score=0.9, weight=2),
        ]
        rat = biggest_delta_rationale(c_axes, k_axes, "tie")
        # diff_size delta = 0.4, tests_passed delta = 0.1 => diff_size cited
        self.assertIn("diff_size", rat)


# ------------------------ CLI behavior ------------------------ #


class TestCLI(unittest.TestCase):
    def test_help_exits_zero(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
            check=False, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Objective judge", proc.stdout)

    def test_malformed_task_exit_1(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "nope.md"
            wt = Path(td) / "wt"
            wt.mkdir()
            rc = judge.main([
                "--task", str(missing),
                "--claude-worktree", str(wt),
                "--codex-worktree", str(wt),
            ])
            self.assertEqual(rc, 1)

    def test_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            task = tdp / "T1.md"
            task.write_text(textwrap.dedent("""\
                ---
                executor: dual
                ---
                # T1
                ## Test Commands
                ```bash
                echo hi
                ```
                ## Acceptance Criteria
                - [ ] AC1: ok
                """), encoding="utf-8")
            c_wt = tdp / "c"
            c_wt.mkdir()
            k_wt = tdp / "k"
            k_wt.mkdir()
            rc = judge.main([
                "--task", str(task),
                "--claude-worktree", str(c_wt),
                "--codex-worktree", str(k_wt),
                "--dry-run",
            ])
            self.assertEqual(rc, 0)


# ------------------------ logging sanity ------------------------ #


class TestStructuredLogging(unittest.TestCase):
    """AC10: each module emits structured JSON logs on entry/exit."""

    def test_json_formatter_shape(self) -> None:
        fmt = judge_axes.JsonFormatter()
        rec = logging.LogRecord(
            name="t", level=logging.INFO, pathname="x", lineno=1,
            msg="hello", args=(), exc_info=None,
        )
        out = fmt.format(rec)
        parsed = json.loads(out)
        self.assertEqual(parsed["msg"], "hello")
        self.assertEqual(parsed["level"], "INFO")
        self.assertIn("ts", parsed)


if __name__ == "__main__":
    unittest.main(verbosity=2)