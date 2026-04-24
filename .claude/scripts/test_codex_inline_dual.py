#!/usr/bin/env python3
"""Unit tests for codex-inline-dual.py.

Stdlib only; no pytest/yaml required.

Run:
    py -3 .claude/scripts/test_codex_inline_dual.py
"""

from __future__ import annotations

import argparse
import importlib.util
import logging
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


# --- Load scripts as modules (hyphens in filenames -> importlib) ----------- #

_THIS = Path(__file__).resolve()
_SCRIPT = _THIS.parent / "codex-inline-dual.py"

spec = importlib.util.spec_from_file_location("codex_inline_dual", _SCRIPT)
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load {_SCRIPT}")
cid = importlib.util.module_from_spec(spec)
sys.modules["codex_inline_dual"] = cid
spec.loader.exec_module(cid)
logging.getLogger("codex_inline_dual").setLevel(logging.CRITICAL)

# codex-implement is loaded as the authoritative T1-format parser
# so we can verify generated specs pass its section parsing.
_CI_PATH = _THIS.parent / "codex-implement.py"
_ci_spec = importlib.util.spec_from_file_location("codex_implement", _CI_PATH)
if _ci_spec is None or _ci_spec.loader is None:
    raise ImportError(f"Cannot load {_CI_PATH}")
codex_impl = importlib.util.module_from_spec(_ci_spec)
sys.modules["codex_implement"] = codex_impl
_ci_spec.loader.exec_module(codex_impl)
logging.getLogger("codex_implement").setLevel(logging.CRITICAL)


# --- Helpers --------------------------------------------------------------- #


def _make_args(tmpdir, **overrides):
    """Build argparse.Namespace for prep() with sensible tmpdir defaults."""
    ns = argparse.Namespace(
        describe="Add --quiet flag to foo.py",
        scope=".claude/scripts/foo.py",
        test=["py -3 tests/test_foo.py"],
        task_id=None,
        speed="balanced",
        dry_run=True,
        worktree_base=Path(tmpdir) / "worktrees" / "inline",
        spec_dir=Path(tmpdir) / "work" / "inline",
        codex_timeout=3600,
        log_dir=Path(tmpdir) / "logs",
    )
    for k, v in overrides.items():
        setattr(ns, k, v)
    return ns


# --- parse_scope / sanitize_task_id ---------------------------------------- #


class TestParseScope(unittest.TestCase):
    def test_single_entry(self):
        self.assertEqual(cid.parse_scope("foo/bar.py"), ["foo/bar.py"])

    def test_comma_split_multiple(self):
        self.assertEqual(
            cid.parse_scope("a.py,b.py,c/d.py"),
            ["a.py", "b.py", "c/d.py"],
        )

    def test_trims_whitespace_and_drops_empties(self):
        self.assertEqual(
            cid.parse_scope(" a.py , ,  b.py,,"),
            ["a.py", "b.py"],
        )

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            cid.parse_scope("")
        with self.assertRaises(ValueError):
            cid.parse_scope(",,, ,")


class TestSanitizeTaskId(unittest.TestCase):
    def test_accepts_alnum_dash_underscore(self):
        self.assertEqual(cid.sanitize_task_id("my-id_42"), "my-id_42")
        self.assertEqual(cid.sanitize_task_id("A1"), "A1")

    def test_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            cid.sanitize_task_id("../evil")
        with self.assertRaises(ValueError):
            cid.sanitize_task_id("a/b")
        with self.assertRaises(ValueError):
            cid.sanitize_task_id("a\\b")

    def test_rejects_leading_dash(self):
        with self.assertRaises(ValueError):
            cid.sanitize_task_id("-flag")

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            cid.sanitize_task_id("")
        with self.assertRaises(ValueError):
            cid.sanitize_task_id("   ")

# --- render_task_spec ------------------------------------------------------ #


class TestRenderTaskSpec(unittest.TestCase):
    def test_contains_required_sections(self):
        spec = cid.render_task_spec(
            task_id="abc",
            describe="Do a thing",
            scope=["a.py", "b.py"],
            tests=["py -3 -m pytest"],
            speed="balanced",
        )
        self.assertIn("executor: dual", spec)
        self.assertIn("speed_profile: balanced", spec)
        self.assertIn("risk_class: routine", spec)
        self.assertIn("## Your Task", spec)
        self.assertIn("Do a thing", spec)
        self.assertIn("## Scope Fence", spec)
        self.assertIn("**Allowed paths:**", spec)
        self.assertIn("- `a.py`", spec)
        self.assertIn("- `b.py`", spec)
        self.assertIn("## Test Commands", spec)
        self.assertIn("py -3 -m pytest", spec)
        self.assertIn("## Acceptance Criteria (IMMUTABLE)", spec)

    def test_multiple_tests_each_get_ac_in_one_bash_block(self):
        """AC8: multiple --test flags merge into one bash block."""
        spec = cid.render_task_spec(
            task_id="x",
            describe="x",
            scope=["a.py"],
            tests=["cmd-one", "cmd-two", "cmd-three"],
            speed="fast",
        )
        self.assertIn("speed_profile: fast", spec)
        # Exactly one ```bash fenced block, containing all three cmds
        bash_blocks = re.findall(r"```bash\n(.*?)\n```", spec, flags=re.DOTALL)
        self.assertEqual(len(bash_blocks), 1)
        self.assertIn("cmd-one", bash_blocks[0])
        self.assertIn("cmd-two", bash_blocks[0])
        self.assertIn("cmd-three", bash_blocks[0])
        # Each test also gets its own AC line
        self.assertIn("AC3: Test Command `cmd-one` exits 0", spec)
        self.assertIn("AC4: Test Command `cmd-two` exits 0", spec)
        self.assertIn("AC5: Test Command `cmd-three` exits 0", spec)

    def test_generated_spec_parses_via_codex_implement(self):
        """AC8: generated task file passes T1 (codex-implement.py) section parsing."""
        spec_text = cid.render_task_spec(
            task_id="roundtrip",
            describe="Round-trip through T1 parser",
            scope=["src/x.py", "tests/test_x.py"],
            tests=["py -3 tests/test_x.py -v", "py -3 -c \"print(1)\""],
            speed="thorough",
        )
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "task-roundtrip.md"
            p.write_text(spec_text, encoding="utf-8")
            task = codex_impl.parse_task_file(p)
            self.assertEqual(task.frontmatter["executor"], "dual")
            self.assertEqual(task.frontmatter["speed_profile"], "thorough")
            self.assertEqual(task.frontmatter["risk_class"], "routine")
            self.assertIn("src/x.py", task.scope_fence.allowed)
            self.assertIn("tests/test_x.py", task.scope_fence.allowed)
            self.assertEqual(len(task.test_commands), 2)
            self.assertIn("py -3 tests/test_x.py -v", task.test_commands)
            self.assertGreaterEqual(len(task.acceptance_criteria), 3)


# --- argparse / CLI -------------------------------------------------------- #


class TestArgParser(unittest.TestCase):
    def test_minimal_args_ok(self):
        p = cid.build_arg_parser()
        args = p.parse_args(["--describe", "x", "--scope", "a.py", "--test", "cmd"])
        self.assertEqual(args.describe, "x")
        self.assertEqual(args.scope, "a.py")
        self.assertEqual(args.test, ["cmd"])
        self.assertEqual(args.speed, "balanced")  # AC8: default speed
        self.assertFalse(args.dry_run)

    def test_multiple_test_flags_append(self):
        p = cid.build_arg_parser()
        args = p.parse_args([
            "--describe", "x",
            "--scope", "a.py",
            "--test", "one",
            "--test", "two",
            "--test", "three",
        ])
        self.assertEqual(args.test, ["one", "two", "three"])

    def test_missing_required_exits_nonzero(self):
        """AC8: missing required arg -> argparse exits non-zero."""
        p = cid.build_arg_parser()
        with self.assertRaises(SystemExit) as ctx:
            with mock.patch("sys.stderr"):
                p.parse_args(["--describe", "x"])  # no --scope, no --test
        self.assertNotEqual(ctx.exception.code, 0)

    def test_speed_choices_enforced(self):
        p = cid.build_arg_parser()
        with self.assertRaises(SystemExit):
            with mock.patch("sys.stderr"):
                p.parse_args([
                    "--describe", "x",
                    "--scope", "a.py",
                    "--test", "cmd",
                    "--speed", "ludicrous",
                ])

# --- render_claude_prompt -------------------------------------------------- #


class TestRenderClaudePrompt(unittest.TestCase):
    def test_prompt_contains_key_sections(self):
        out = cid.render_claude_prompt(
            task_id="demo",
            describe="Do a thing",
            scope=["a.py", "b.py"],
            tests=["t1", "t2"],
            spec_path=Path("work/codex-implementations/inline/task-demo.md"),
            worktree_claude=Path("worktrees/inline/demo/claude"),
        )
        self.assertIn("Claude side of a dual micro-task", out)
        self.assertIn("verification-before-completion", out)
        self.assertIn("logging-standards", out)
        self.assertIn("inline/demo/claude", out)
        self.assertIn("- `a.py`", out)
        self.assertIn("- `b.py`", out)
        self.assertIn("t1", out)
        self.assertIn("t2", out)
        self.assertIn("PHASE HANDOFF: inline-demo-claude", out)


# --- prep() dry-run (no git, no subprocess) -------------------------------- #


class TestPrepDryRun(unittest.TestCase):
    def test_dry_run_creates_nothing_but_returns_plan(self):
        """AC8: --dry-run prints what would happen, creates nothing."""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            args = _make_args(td, task_id="dry1", dry_run=True)
            result = cid.prep(args, project_root=tmp)

            self.assertEqual(result.task_id, "dry1")
            # Planned paths are computed but not created on disk
            self.assertFalse(result.pair.claude_path.exists())
            self.assertFalse(result.pair.codex_path.exists())
            self.assertFalse(result.spec_path.exists())
            self.assertFalse(result.prompt_path.exists())
            # AC8: branch names follow inline/<id> convention
            self.assertEqual(result.pair.claude_branch, "inline/dry1/claude")
            self.assertEqual(result.pair.codex_branch, "inline/dry1/codex")
            # No PID in dry-run
            self.assertIsNone(result.codex_job.pid)

    def test_dry_run_comma_scope_multiple_paths(self):
        """AC8: multiple --scope entries comma-separated -> all in Scope Fence."""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            args = _make_args(
                td,
                task_id="multi",
                scope="a.py, b.py, c/d.py",
                dry_run=True,
            )
            result = cid.prep(args, project_root=tmp)
            # render via same helpers prep would use
            spec_text = cid.render_task_spec(
                task_id=result.task_id,
                describe=args.describe,
                scope=cid.parse_scope(args.scope),
                tests=args.test,
                speed=args.speed,
            )
            self.assertIn("- `a.py`", spec_text)
            self.assertIn("- `b.py`", spec_text)
            self.assertIn("- `c/d.py`", spec_text)

    def test_dry_run_default_task_id_is_timestamp(self):
        """Default task-id has timestamp format YYYYMMDD-HHMMSS."""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            args = _make_args(td, task_id=None, dry_run=True)
            result = cid.prep(args, project_root=tmp)
            self.assertRegex(result.task_id, r"^\d{8}-\d{6}$")


# --- prep() live with mocked git + subprocess ------------------------------ #


class TestPrepLive(unittest.TestCase):
    def test_happy_path_creates_spec_prompt_and_spawns_codex(self):
        """AC8 happy path: describe+scope+test -> transient spec + 2 worktrees +
        prompt + codex PID.
        """
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            args = _make_args(td, task_id="happy", dry_run=False)

            fake_git = mock.MagicMock(return_value=subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            ))
            fake_proc = mock.MagicMock()
            fake_proc.pid = 12345

            # Pretend codex-implement.py exists at project_root/.claude/scripts
            scripts_dir = tmp / ".claude" / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            (scripts_dir / "codex-implement.py").write_text(
                "# fake\n", encoding="utf-8"
            )

            with mock.patch.object(cid, "_run_git", fake_git), \
                 mock.patch.object(cid.subprocess, "Popen", return_value=fake_proc):
                result = cid.prep(args, project_root=tmp)

            # Spec file written
            self.assertTrue(result.spec_path.exists(),
                            f"spec missing: {result.spec_path}")
            spec_text = result.spec_path.read_text(encoding="utf-8")
            self.assertIn("## Your Task", spec_text)
            self.assertIn("## Scope Fence", spec_text)
            # Prompt file written
            self.assertTrue(result.prompt_path.exists())
            # Codex PID captured
            self.assertEqual(result.codex_job.pid, 12345)
            # git worktree add was called twice (claude + codex)
            worktree_calls = [
                c for c in fake_git.call_args_list
                if c.args and c.args[0][:2] == ["worktree", "add"]
            ]
            self.assertEqual(len(worktree_calls), 2)
            # AC8: branch names follow inline/<id>/... convention
            branches = [c.args[0][3] for c in worktree_calls]
            self.assertIn("inline/happy/claude", branches)
            self.assertIn("inline/happy/codex", branches)

    def test_worktree_conflict_raises_without_partial_state(self):
        """Pre-existing worktree dir -> FileExistsError before any git call."""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            args = _make_args(td, task_id="conflict", dry_run=False)
            # Pre-create one of the target paths
            (args.worktree_base / "conflict" / "claude").mkdir(parents=True)

            fake_git = mock.MagicMock()
            with mock.patch.object(cid, "_run_git", fake_git):
                with self.assertRaises(FileExistsError):
                    cid.prep(args, project_root=tmp)
            self.assertEqual(fake_git.call_count, 0)


# --- render_status_block --------------------------------------------------- #


class TestRenderStatusBlock(unittest.TestCase):
    def test_block_has_three_sections(self):
        """AC6: clear 3-section block (CLAUDE / CODEX / NEXT STEPS)."""
        pair = cid.WorktreePair(
            claude_path=Path("worktrees/inline/x/claude"),
            codex_path=Path("worktrees/inline/x/codex"),
            claude_branch="inline/x/claude",
            codex_branch="inline/x/codex",
        )
        job = cid.CodexJob(pid=999, log_path=Path("work/logs/codex-inline-x.log"),
                           command=["py", "-3", "x"])
        out = cid.render_status_block(
            task_id="x",
            spec_path=Path("work/codex-implementations/inline/task-x.md"),
            prompt_path=Path("work/codex-implementations/inline/x-claude-prompt.md"),
            pair=pair,
            codex_job=job,
            dry_run=False,
        )
        self.assertIn("CLAUDE TEAMMATE PROMPT", out)
        self.assertIn("CODEX BACKGROUND JOB", out)
        self.assertIn("NEXT STEPS", out)
        self.assertIn("PID: 999", out)
        self.assertIn("inline/x/claude", out)
        self.assertIn("inline/x/codex", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)