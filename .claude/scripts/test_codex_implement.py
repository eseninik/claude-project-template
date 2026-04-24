#!/usr/bin/env python3
"""Unit tests for codex-implement.py.

Uses stdlib unittest — no pytest/yaml/other deps required.
Covers: frontmatter parsing, section extraction, scope fence parsing,
test command parsing, acceptance criteria parsing, exit code mapping,
error handling for missing task file and timeout simulation.

Run:
    py -3 .claude/scripts/test_codex_implement.py
"""

from __future__ import annotations

import importlib.util
import logging
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


# --------------------------------------------------------------------------- #
# Load codex-implement.py as a module (filename has a hyphen, so importlib)   #
# --------------------------------------------------------------------------- #

_THIS = Path(__file__).resolve()
_SCRIPT = _THIS.parent / "codex-implement.py"

spec = importlib.util.spec_from_file_location("codex_implement", _SCRIPT)
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load {_SCRIPT}")
codex_impl = importlib.util.module_from_spec(spec)
sys.modules["codex_implement"] = codex_impl  # required for dataclass + __future__.annotations
spec.loader.exec_module(codex_impl)

# Silence log output from the module during tests
logging.getLogger("codex_implement").setLevel(logging.CRITICAL)


# --------------------------------------------------------------------------- #
# Fixtures                                                                    #
# --------------------------------------------------------------------------- #

TASK_SAMPLE = """---
executor: codex
risk_class: routine
reasoning: high
wave: 1
---

# Task T42: Sample task

## Your Task
Implement a sample feature end-to-end.

## Scope Fence
**Allowed paths (may be written):**
- `src/sample.py`
- `tests/test_sample.py`

**Forbidden paths (must NOT be modified):**
- `src/other/*` (out of scope)
- docs/

## Test Commands (run after implementation)
```bash
py -3 -m pytest tests/test_sample.py -v
py -3 -c "print('ok')"
# commented line should be ignored
```

## Acceptance Criteria (IMMUTABLE)
- [ ] AC1: feature works end-to-end
- [ ] AC2: tests pass
- [ ] All Test Commands above exit 0

## Skill Contracts

### logging-standards (contract extract)
- entry/exit/error logs everywhere

## Constraints
- Windows compatible
"""

TASK_NO_FRONTMATTER = """# Task Tzap: bare

## Scope Fence
**Allowed paths (may be written):**
- a.py

## Test Commands
```bash
echo hi
```

## Acceptance Criteria
- [ ] AC1: something
"""


# --------------------------------------------------------------------------- #
# Parsing tests                                                               #
# --------------------------------------------------------------------------- #


class TestFrontmatterParser(unittest.TestCase):
    def test_parses_valid_frontmatter(self):
        fm, body = codex_impl.parse_frontmatter(TASK_SAMPLE)
        self.assertEqual(fm["executor"], "codex")
        self.assertEqual(fm["risk_class"], "routine")
        self.assertEqual(fm["reasoning"], "high")
        self.assertEqual(fm["wave"], "1")
        self.assertTrue(body.startswith("\n# Task T42"))

    def test_no_frontmatter_returns_body_unchanged(self):
        fm, body = codex_impl.parse_frontmatter(TASK_NO_FRONTMATTER)
        self.assertEqual(fm, {})
        self.assertEqual(body, TASK_NO_FRONTMATTER)

    def test_unterminated_frontmatter_returns_empty(self):
        broken = "---\nexecutor: codex\n(never closed)\n"
        fm, body = codex_impl.parse_frontmatter(broken)
        self.assertEqual(fm, {})
        self.assertEqual(body, broken)

    def test_ignores_blank_and_comment_lines(self):
        text = "---\n# comment\n\nkey: value\n---\nbody\n"
        fm, _ = codex_impl.parse_frontmatter(text)
        self.assertEqual(fm, {"key": "value"})


class TestSectionSplitter(unittest.TestCase):
    def test_splits_top_level_sections(self):
        _, body = codex_impl.parse_frontmatter(TASK_SAMPLE)
        sections = codex_impl.split_sections(body)
        self.assertIn("Your Task", sections)
        self.assertIn("Scope Fence", sections)
        self.assertIn("Test Commands (run after implementation)", sections)
        self.assertIn("Acceptance Criteria (IMMUTABLE)", sections)
        self.assertIn("Skill Contracts", sections)
        self.assertIn("Constraints", sections)

    def test_preserves_subheadings_inside_section(self):
        _, body = codex_impl.parse_frontmatter(TASK_SAMPLE)
        sections = codex_impl.split_sections(body)
        self.assertIn("### logging-standards", sections["Skill Contracts"])

    def test_does_not_split_on_triple_hash(self):
        text = "## A\nhello\n### subsection\nmore\n## B\nend\n"
        sections = codex_impl.split_sections(text)
        self.assertIn("A", sections)
        self.assertIn("B", sections)
        self.assertIn("### subsection", sections["A"])


class TestScopeFenceParser(unittest.TestCase):
    def test_parses_allowed_and_forbidden_bullets(self):
        _, body = codex_impl.parse_frontmatter(TASK_SAMPLE)
        sections = codex_impl.split_sections(body)
        fence = codex_impl.parse_scope_fence(sections["Scope Fence"])
        self.assertIn("src/sample.py", fence.allowed)
        self.assertIn("tests/test_sample.py", fence.allowed)
        self.assertIn("src/other/*", fence.forbidden)
        self.assertIn("docs/", fence.forbidden)

    def test_empty_section_returns_empty_fence(self):
        fence = codex_impl.parse_scope_fence("")
        self.assertEqual(fence.allowed, [])
        self.assertEqual(fence.forbidden, [])

    def test_strips_backticks_and_trailing_comments(self):
        txt = (
            "**Allowed paths (may be written):**\n"
            "- `foo/bar.py` (new file)\n"
            "- baz/qux.py\n"
        )
        fence = codex_impl.parse_scope_fence(txt)
        self.assertEqual(fence.allowed, ["foo/bar.py", "baz/qux.py"])


class TestTestCommandParser(unittest.TestCase):
    def test_extracts_commands_from_bash_block(self):
        _, body = codex_impl.parse_frontmatter(TASK_SAMPLE)
        sections = codex_impl.split_sections(body)
        cmds = codex_impl.parse_test_commands(
            sections["Test Commands (run after implementation)"]
        )
        self.assertEqual(len(cmds), 2)
        self.assertIn("py -3 -m pytest tests/test_sample.py -v", cmds)
        self.assertIn('py -3 -c "print(\'ok\')"', cmds)

    def test_ignores_commented_lines(self):
        txt = "```bash\n# commented\nrun-me\n```\n"
        cmds = codex_impl.parse_test_commands(txt)
        self.assertEqual(cmds, ["run-me"])

    def test_no_code_block_returns_empty(self):
        self.assertEqual(codex_impl.parse_test_commands(""), [])
        self.assertEqual(codex_impl.parse_test_commands("No fenced block here"), [])


class TestAcceptanceCriteriaParser(unittest.TestCase):
    def test_extracts_checkbox_lines(self):
        _, body = codex_impl.parse_frontmatter(TASK_SAMPLE)
        sections = codex_impl.split_sections(body)
        acs = codex_impl.parse_acceptance_criteria(
            sections["Acceptance Criteria (IMMUTABLE)"]
        )
        self.assertEqual(len(acs), 3)
        self.assertIn("AC1: feature works end-to-end", acs)


class TestTaskIdDerivation(unittest.TestCase):
    def test_t_prefix_with_number(self):
        self.assertEqual(
            codex_impl._derive_task_id(Path("T7-impl.md")), "7"
        )

    def test_task_prefix_with_name(self):
        self.assertEqual(
            codex_impl._derive_task_id(Path("task-alpha.md")), "alpha"
        )

    def test_fallback_to_stem(self):
        self.assertEqual(
            codex_impl._derive_task_id(Path("random.md")), "random"
        )


# --------------------------------------------------------------------------- #
# End-to-end parse_task_file                                                  #
# --------------------------------------------------------------------------- #


class TestParseTaskFile(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "T42-sample.md"
            p.write_text(TASK_SAMPLE, encoding="utf-8")
            task = codex_impl.parse_task_file(p)
            self.assertEqual(task.task_id, "42")
            self.assertEqual(task.frontmatter["executor"], "codex")
            self.assertIn("src/sample.py", task.scope_fence.allowed)
            self.assertIn("docs/", task.scope_fence.forbidden)
            self.assertEqual(len(task.test_commands), 2)
            self.assertEqual(len(task.acceptance_criteria), 3)

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            codex_impl.parse_task_file(Path("/definitely/not/there.md"))


# --------------------------------------------------------------------------- #
# Exit code mapping                                                           #
# --------------------------------------------------------------------------- #


class TestExitCodeMapping(unittest.TestCase):
    def test_pass_returns_zero(self):
        self.assertEqual(
            codex_impl.map_status_to_exit("pass", "pass", True), codex_impl.EXIT_OK
        )

    def test_scope_skipped_with_tests_pass_returns_zero(self):
        self.assertEqual(
            codex_impl.map_status_to_exit("pass", "skipped", True), codex_impl.EXIT_OK
        )

    def test_test_fail_returns_one(self):
        self.assertEqual(
            codex_impl.map_status_to_exit("fail", "pass", False),
            codex_impl.EXIT_TEST_FAIL,
        )

    def test_scope_violation_returns_two(self):
        self.assertEqual(
            codex_impl.map_status_to_exit("scope-violation", "fail", False),
            codex_impl.EXIT_SCOPE_OR_TIMEOUT,
        )

    def test_timeout_returns_two(self):
        self.assertEqual(
            codex_impl.map_status_to_exit("timeout", "skipped", False),
            codex_impl.EXIT_SCOPE_OR_TIMEOUT,
        )

    def test_scope_fail_outranks_tests(self):
        self.assertEqual(
            codex_impl.map_status_to_exit("pass", "fail", True),
            codex_impl.EXIT_SCOPE_OR_TIMEOUT,
        )


# --------------------------------------------------------------------------- #
# Codex timeout simulation                                                    #
# --------------------------------------------------------------------------- #


class TestRunCodexTimeout(unittest.TestCase):
    def test_timeout_returns_timed_out_result(self):
        with mock.patch("subprocess.run") as mock_run, \
             mock.patch("shutil.which", return_value="/fake/codex"):
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="codex", timeout=1)
            result = codex_impl.run_codex(
                prompt="x",
                worktree=Path("."),
                reasoning="high",
                timeout=1,
            )
            self.assertTrue(result.timed_out)
            self.assertEqual(result.returncode, -1)

    def test_missing_codex_raises(self):
        with mock.patch("shutil.which", return_value=None):
            with self.assertRaises(RuntimeError):
                codex_impl.run_codex(
                    prompt="x", worktree=Path("."), reasoning="high", timeout=1
                )


# --------------------------------------------------------------------------- #
# Scope check graceful fallback                                               #
# --------------------------------------------------------------------------- #


class TestScopeCheckFallback(unittest.TestCase):
    def test_missing_scope_check_script_returns_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # No .claude/scripts/codex-scope-check.py under this root
            (root / ".claude" / "scripts").mkdir(parents=True)
            diff_file = root / "some.diff"
            diff_file.write_text("", encoding="utf-8")
            fence = codex_impl.ScopeFence(allowed=["a.py"])
            result = codex_impl.run_scope_check(diff_file, fence, root)
            self.assertEqual(result.status, "skipped")


# --------------------------------------------------------------------------- #
# CLI build                                                                   #
# --------------------------------------------------------------------------- #


class TestArgParser(unittest.TestCase):
    def test_has_all_spec_flags(self):
        parser = codex_impl.build_arg_parser()
        actions = {a.dest for a in parser._actions}
        for flag in ("task", "worktree", "reasoning", "timeout", "result_dir"):
            self.assertIn(flag, actions, f"missing --{flag.replace('_', '-')}")

    def test_task_is_required(self):
        parser = codex_impl.build_arg_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args([])


# --------------------------------------------------------------------------- #
# Result file writing smoke test                                              #
# --------------------------------------------------------------------------- #


class TestWriteResultFile(unittest.TestCase):
    def test_writes_all_schema_sections(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            task_path = td_path / "T1-x.md"
            task_path.write_text(TASK_SAMPLE, encoding="utf-8")
            task = codex_impl.parse_task_file(task_path)

            codex_run = codex_impl.CodexRunResult(
                returncode=0,
                stdout="NOTE: all good\nregular line\n",
                stderr="",
                timed_out=False,
                self_report=["NOTE: all good"],
            )
            test_run = codex_impl.TestRunResult(
                all_passed=True,
                outputs=[
                    {
                        "cmd": "echo ok",
                        "returncode": 0,
                        "stdout": "ok\n",
                        "stderr": "",
                        "passed": True,
                        "timed_out": False,
                    }
                ],
            )
            scope = codex_impl.ScopeCheckResult(status="pass", message="in-scope")

            result_path = td_path / "task-42-result.md"
            codex_impl.write_result_file(
                result_path=result_path,
                task=task,
                status="pass",
                diff="diff --git a/a b/a\n",
                test_run=test_run,
                codex_run=codex_run,
                scope=scope,
                base_sha="deadbeef",
                timestamp="2026-04-24T00:00:00+00:00",
            )

            content = result_path.read_text(encoding="utf-8")
            self.assertIn("status: pass", content)
            self.assertIn("base_sha: deadbeef", content)
            self.assertIn("scope_status: pass", content)
            self.assertIn("tests_all_passed: True", content)
            self.assertIn("## Diff", content)
            self.assertIn("## Test Output", content)
            self.assertIn("## Self-Report", content)
            self.assertIn("NOTE: all good", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
