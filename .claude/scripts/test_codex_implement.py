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

    def test_parse_section_handles_em_dash_suffix(self):
        text = "## Scope Fence — desc\nbody\n"
        sections = codex_impl.split_sections(text)
        self.assertEqual(sections["Scope Fence"], "body")
        self.assertEqual(sections["Scope Fence — desc"], "body")

    def test_parse_section_handles_hyphen_suffix(self):
        text = "## Test Commands - desc\n```bash\necho hi\n```\n"
        sections = codex_impl.split_sections(text)
        self.assertIn("echo hi", sections["Test Commands"])
        self.assertIn("echo hi", sections["Test Commands - desc"])

    def test_parse_section_no_suffix_unchanged(self):
        text = "## Scope Fence\nbody\n"
        sections = codex_impl.split_sections(text)
        self.assertEqual(sections["Scope Fence"], "body")
        self.assertEqual(list(sections.keys()), ["Scope Fence"])


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


class TestScopeFenceParserCodeBlock(unittest.TestCase):
    """Y18: parse_scope_fence accepts code-block-of-paths style.

    Fixture pattern: each test builds a Scope-Fence section text in the
    code-block style and asserts on the parsed ScopeFence.allowed list.
    """

    @staticmethod
    def _section(*paths: str) -> str:
        """Helper: build a fence section with the given paths in a code block."""
        body = "\n".join(paths)
        return "## Scope Fence — files you MAY modify\n\n```\n" + body + "\n```\n"

    def test_parse_scope_fence_code_block_syntax(self):
        """AC-1.a: bare code block of paths -> all parsed as allowed."""
        txt = self._section(".claude/hooks/foo.py", "src/bar/baz.py")
        fence = codex_impl.parse_scope_fence(txt)
        self.assertEqual(fence.allowed, [".claude/hooks/foo.py", "src/bar/baz.py"])
        self.assertEqual(fence.forbidden, [])

    def test_parse_scope_fence_code_block_strips_comments_and_blanks(self):
        """AC-1.b: blank lines + # / // comments must be skipped."""
        txt = (
            "## Scope Fence\n\n"
            "```\n"
            ".claude/hooks/foo.py\n"
            "\n"
            "# this is a comment, not a path\n"
            "// also a comment\n"
            "src/bar/baz.py\n"
            "\n"
            "```\n"
        )
        fence = codex_impl.parse_scope_fence(txt)
        self.assertEqual(fence.allowed, [".claude/hooks/foo.py", "src/bar/baz.py"])
        self.assertNotIn("# this is a comment, not a path", fence.allowed)
        self.assertNotIn("// also a comment", fence.allowed)

    def test_parse_scope_fence_code_block_strips_trailing_parens(self):
        """AC-1.c: trailing `(comment)` is stripped from each path."""
        txt = (
            "## Scope Fence\n\n"
            "```\n"
            "CLAUDE.md (only the X section)\n"
            "src/foo.py  (do NOT modify imports)\n"
            "```\n"
        )
        fence = codex_impl.parse_scope_fence(txt)
        self.assertEqual(fence.allowed, ["CLAUDE.md", "src/foo.py"])

    def test_parse_scope_fence_falls_back_to_legacy_when_bold_present(self):
        """AC-1.d: when **Allowed**: bold-header is present, legacy parsing
        wins and the code-block fallback is NOT triggered (regression
        guard for the existing pre-Y18 behavior)."""
        txt = (
            "**Allowed paths:**\n"
            "- `legacy/path.py`\n"
            "\n"
            "```\n"
            "should_NOT_appear.py\n"
            "```\n"
        )
        fence = codex_impl.parse_scope_fence(txt)
        self.assertEqual(fence.allowed, ["legacy/path.py"])
        self.assertNotIn("should_NOT_appear.py", fence.allowed)

    def test_parse_scope_fence_em_dash_heading_yields_paths(self):
        text = (
            "# Task Z17\n\n"
            "## Scope Fence — files you MAY modify\n\n"
            "```\n"
            ".claude/scripts/codex-implement.py\n"
            ".claude/scripts/test_codex_implement.py\n"
            "```\n"
        )
        with tempfile.TemporaryDirectory() as td:
            task_path = Path(td) / "task-Z17.md"
            task_path.write_text(text, encoding="utf-8")
            task = codex_impl.parse_task_file(task_path)
        self.assertEqual(
            task.scope_fence.allowed,
            [
                ".claude/scripts/codex-implement.py",
                ".claude/scripts/test_codex_implement.py",
            ],
        )


class TestDetermineRunStatus(unittest.TestCase):
    """Y20: determine_run_status() pure helper.

    Status precedence:
      1. timed_out                  -> "timeout"
      2. scope.status == "fail"     -> "scope-violation"
      3. not test_run.all_passed    -> "fail"
      4. otherwise                  -> "pass"

    Crucially, codex_run.returncode != 0 is IGNORED when both scope and
    tests pass — that was the Y20 bug.
    """

    @staticmethod
    def _scope(status: str) -> object:
        return codex_impl.ScopeCheckResult(status=status, message="(test fixture)")

    @staticmethod
    def _tests(passed: bool) -> object:
        return codex_impl.TestRunResult(all_passed=passed, outputs=[])

    @staticmethod
    def _codex(returncode: int) -> object:
        return codex_impl.CodexRunResult(
            returncode=returncode, stdout="", stderr="", timed_out=False, self_report=[]
        )

    def test_status_pass_when_tests_pass_despite_codex_returncode_nonzero(self):
        """AC-2.a: tests pass + scope pass + codex_returncode=1 -> 'pass'.

        This is the bug Y20 fixes: CLI v0.125 telemetry warnings produce
        a non-zero returncode but the run is genuinely a pass.
        """
        status = codex_impl.determine_run_status(
            scope=self._scope("pass"),
            test_run=self._tests(True),
            codex_run=self._codex(1),
            timed_out=False,
        )
        self.assertEqual(status, "pass")

    def test_status_pass_when_only_codex_returncode_nonzero_and_no_modifications(self):
        """Verification-only run: tests/scope pass even when Codex rc is non-zero."""
        status = codex_impl.determine_run_status(
            scope=self._scope("pass"),
            test_run=self._tests(True),
            codex_run=self._codex(7),
            timed_out=False,
        )
        self.assertEqual(status, "pass")

    def test_status_fail_when_tests_fail(self):
        """AC-2.b: scope=pass, tests fail, codex_returncode=0 -> 'fail'."""
        status = codex_impl.determine_run_status(
            scope=self._scope("pass"),
            test_run=self._tests(False),
            codex_run=self._codex(0),
            timed_out=False,
        )
        self.assertEqual(status, "fail")

    def test_status_scope_violation_overrides_test_pass(self):
        """AC-2.c: scope=fail must take precedence over passing tests."""
        status = codex_impl.determine_run_status(
            scope=self._scope("fail"),
            test_run=self._tests(True),
            codex_run=self._codex(0),
            timed_out=False,
        )
        self.assertEqual(status, "scope-violation")

    def test_status_timeout_takes_top_precedence(self):
        """timed_out=True must beat every other signal (sanity guard)."""
        status = codex_impl.determine_run_status(
            scope=self._scope("fail"),
            test_run=self._tests(False),
            codex_run=self._codex(1),
            timed_out=True,
        )
        self.assertEqual(status, "timeout")


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
        """`T7-impl.md` must yield `7-impl` (Finding #11 — preserve trailing segment)."""
        self.assertEqual(
            codex_impl._derive_task_id(Path("T7-impl.md")), "7-impl"
        )

    def test_t_prefix_bare_number(self):
        """Bare `T7.md` without trailing segment still yields `7`."""
        self.assertEqual(codex_impl._derive_task_id(Path("T7.md")), "7")

    def test_task_prefix_compound_id(self):
        """`task-dual-1.md` must yield `dual-1`, not `dual` (Finding #11)."""
        self.assertEqual(
            codex_impl._derive_task_id(Path("task-dual-1.md")), "dual-1"
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
            # Task id preserves the trailing segment after T<num>- (Finding #11).
            self.assertEqual(task.task_id, "42-sample")
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
# Y26 — argv shape regression (--dangerously-bypass-approvals-and-sandbox)    #
# --------------------------------------------------------------------------- #


class TestBuildCodexArgvY26(unittest.TestCase):
    """Codex CLI v0.125 silently ignored `--sandbox workspace-write` for the
    `exec` mode, leaving every Codex run effectively read-only and producing
    empty diffs (Y23 / Z5 / Z7). The fix swaps the two flags
    (`--sandbox workspace-write` + `--full-auto`) for the single
    `--dangerously-bypass-approvals-and-sandbox` flag, which the worktree
    sandboxing already makes safe. These tests pin that argv shape so a future
    revert is caught immediately by the test suite.
    """

    def _argv(self) -> list[str]:
        return codex_impl._build_codex_argv(
            codex="/fake/codex",
            model="gpt-5.5",
            worktree=Path("."),
            chatgpt_provider="model_providers.chatgpt={name=\"chatgpt\"}",
        )

    def test_argv_uses_dangerously_bypass_flag(self):
        """AC-1a: bypass flag must be present (otherwise sandbox stays read-only)."""
        argv = self._argv()
        self.assertIn(
            "--dangerously-bypass-approvals-and-sandbox",
            argv,
            "Y26 regression: argv missing bypass flag — Codex would run read-only",
        )

    def test_argv_does_not_contain_sandbox_workspace_write(self):
        """AC-1b: legacy flags must be absent (they get silently dropped by v0.125 anyway)."""
        argv = self._argv()
        self.assertNotIn("--sandbox", argv, "Y26 regression: legacy --sandbox flag still present")
        self.assertNotIn("workspace-write", argv, "Y26 regression: legacy workspace-write value still present")
        self.assertNotIn("--full-auto", argv, "Y26 regression: legacy --full-auto flag still present")

    def test_argv_uses_stdin_marker(self):
        """Sanity: prompt is still passed via stdin (trailing `-` argument)."""
        argv = self._argv()
        self.assertEqual(argv[-1], "-", "argv must end with '-' (stdin prompt marker)")

    def test_run_codex_invokes_subprocess_with_bypass_flag(self):
        """End-to-end: monkeypatched run_codex actually passes the new flag to subprocess."""
        captured: dict[str, list[str]] = {}

        def _fake_run(cmd, *_args, **_kwargs):
            captured["cmd"] = list(cmd)
            class _R:
                returncode = 0
                stdout = ""
                stderr = ""
            return _R()

        with mock.patch("subprocess.run", side_effect=_fake_run), \
             mock.patch("shutil.which", return_value="/fake/codex"):
            codex_impl.run_codex(
                prompt="x", worktree=Path("."), reasoning="high", timeout=1
            )
        self.assertIn("--dangerously-bypass-approvals-and-sandbox", captured["cmd"])
        self.assertNotIn("--sandbox", captured["cmd"])
        self.assertNotIn("workspace-write", captured["cmd"])
        self.assertNotIn("--full-auto", captured["cmd"])

# --------------------------------------------------------------------------- #
# Scope check graceful fallback                                               #
# --------------------------------------------------------------------------- #


class TestScopeCheckFallback(unittest.TestCase):
    def test_resolve_scope_check_uses_env_var(self):
        with tempfile.TemporaryDirectory() as td:
            env_root = Path(td) / "repo-current"
            expected = env_root / ".claude" / "scripts" / "codex-scope-check.py"
            with mock.patch.dict(
                codex_impl.os.environ,
                {"CLAUDE_PROJECT_DIR": str(env_root)},
                clear=True,
            ):
                script = codex_impl._resolve_scope_check_script(Path(td) / "worktree")
        self.assertEqual(script, expected.resolve())

    def test_resolve_scope_check_walks_up_from_worktree(self):
        with tempfile.TemporaryDirectory() as td:
            repo_root = Path(td) / "repo"
            worktree = repo_root / "worktrees" / "feature"
            (repo_root / ".git").mkdir(parents=True)
            worktree.mkdir(parents=True)
            (worktree / ".git").write_text(
                "gitdir: ../../.git/worktrees/feature",
                encoding="utf-8",
            )
            expected = repo_root / ".claude" / "scripts" / "codex-scope-check.py"
            with mock.patch.dict(codex_impl.os.environ, {}, clear=True):
                script = codex_impl._resolve_scope_check_script(worktree)
        self.assertEqual(script, expected)

    def test_resolve_scope_check_falls_back_to_worktree(self):
        with tempfile.TemporaryDirectory() as td:
            worktree = Path(td) / "worktree"
            worktree.mkdir()
            expected = worktree / ".claude" / "scripts" / "codex-scope-check.py"
            with mock.patch.dict(codex_impl.os.environ, {}, clear=True):
                script = codex_impl._resolve_scope_check_script(worktree)
        self.assertEqual(script, expected)

    def test_missing_scope_check_script_returns_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # No .claude/scripts/codex-scope-check.py under this root
            (root / ".claude" / "scripts").mkdir(parents=True)
            diff_file = root / "some.diff"
            diff_file.write_text("", encoding="utf-8")
            fence = codex_impl.ScopeFence(allowed=["a.py"])
            with mock.patch.dict(codex_impl.os.environ, {}, clear=True):
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


class TestPreflightCleanTreeGuard(unittest.TestCase):
    """Regression suite for the dirty-tree preflight check.

    PoC 2026-04-24 surfaced that preflight used to return HEAD sha without
    verifying a clean tree, so subsequent `git reset --hard` + `git clean -fd`
    in rollback destroyed pre-existing uncommitted user work. Preflight now
    refuses to proceed on any dirty worktree.
    """

    def _run(self, argv: list[str], cwd: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *argv],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )

    def _init_repo(self, path: Path) -> None:
        self._run(["init", "--initial-branch=main"], path)
        self._run(["config", "user.email", "t@t"], path)
        self._run(["config", "user.name", "t"], path)
        self._run(["config", "commit.gpgsign", "false"], path)
        (path / "a.txt").write_text("a", encoding="utf-8")
        self._run(["add", "."], path)
        self._run(["commit", "-m", "init"], path)

    def test_clean_tree_passes_preflight(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._init_repo(repo)
            sha = codex_impl.preflight_worktree(repo)
            self.assertEqual(len(sha), 40)

    def test_dirty_tracked_file_rejects(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._init_repo(repo)
            (repo / "a.txt").write_text("modified", encoding="utf-8")
            with self.assertRaises(codex_impl.DirtyWorktreeError) as cm:
                codex_impl.preflight_worktree(repo)
            self.assertIn("dirty working tree", str(cm.exception).lower())
            self.assertIn("a.txt", str(cm.exception))

    def test_untracked_file_rejects(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._init_repo(repo)
            (repo / "new.py").write_text("print('hi')", encoding="utf-8")
            with self.assertRaises(codex_impl.DirtyWorktreeError) as cm:
                codex_impl.preflight_worktree(repo)
            self.assertIn("new.py", str(cm.exception))

    def test_staged_file_rejects(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._init_repo(repo)
            (repo / "b.txt").write_text("b", encoding="utf-8")
            self._run(["add", "b.txt"], repo)
            with self.assertRaises(codex_impl.DirtyWorktreeError) as cm:
                codex_impl.preflight_worktree(repo)
            self.assertIn("b.txt", str(cm.exception))

    def test_check_tree_clean_returns_tuple(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._init_repo(repo)
            is_clean, lines = codex_impl.check_tree_clean(repo)
            self.assertTrue(is_clean)
            self.assertEqual(lines, [])

            (repo / "dirty.txt").write_text("x", encoding="utf-8")
            is_clean, lines = codex_impl.check_tree_clean(repo)
            self.assertFalse(is_clean)
            self.assertEqual(len(lines), 1)
            self.assertIn("dirty.txt", lines[0])


class TestLoadPriorIteration(unittest.TestCase):
    """load_prior_iteration — auto-injected iteration memory (--iterate-from)."""

    _SAMPLE = """# Codex Implementation Result — Task dual-1

- status: scope-violation
- timestamp: 2026-04-24T11:00:00+00:00
- task_file: /x/task-dual-1.md
- base_sha: deadbeef0000000000000000000000000000dead
- codex_returncode: 0
- scope_status: fail
- scope_message: bogus 42 entries parsed from fence file
- tests_all_passed: False
- test_commands_count: 3

## Diff

```diff
diff --git a/.claude/scripts/foo.py b/.claude/scripts/foo.py
index 0000..1111 100644
--- a/.claude/scripts/foo.py
+++ b/.claude/scripts/foo.py
@@ -1 +1,2 @@
 original
+new line
diff --git a/.claude/scripts/bar.py b/.claude/scripts/bar.py
--- /dev/null
+++ b/.claude/scripts/bar.py
@@ -0,0 +1 @@
+hello
```

## Self-Report (Codex NOTE/BLOCKER lines)

- NOTE: Added feature X
- NOTE: Kept existing style
- BLOCKER: Tests failed because py -3 not in sandbox PATH
- BLOCKER: Scope fence parser flagged correct file wrongly
"""

    def test_parses_status_and_blockers(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "prior.md"
            p.write_text(self._SAMPLE, encoding="utf-8")
            summary = codex_impl.load_prior_iteration(p)
            self.assertIn("prior status: scope-violation", summary)
            self.assertIn("prior scope_status: fail", summary)
            self.assertIn("prior tests_all_passed: False", summary)
            self.assertIn("BLOCKER: Tests failed because py -3", summary)
            self.assertIn("BLOCKER: Scope fence parser flagged", summary)

    def test_extracts_files_touched(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "prior.md"
            p.write_text(self._SAMPLE, encoding="utf-8")
            summary = codex_impl.load_prior_iteration(p)
            self.assertIn(".claude/scripts/foo.py", summary)
            self.assertIn(".claude/scripts/bar.py", summary)
            # No duplicates — each file once.
            self.assertEqual(summary.count(".claude/scripts/foo.py"), 1)

    def test_preserves_notes(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "prior.md"
            p.write_text(self._SAMPLE, encoding="utf-8")
            summary = codex_impl.load_prior_iteration(p)
            self.assertIn("NOTE: Added feature X", summary)
            self.assertIn("NOTE: Kept existing style", summary)

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            codex_impl.load_prior_iteration(Path("/nope/does/not/exist.md"))

    def test_directive_suffix_always_appended(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "prior.md"
            p.write_text(self._SAMPLE, encoding="utf-8")
            summary = codex_impl.load_prior_iteration(p)
            self.assertIn("do NOT repeat the prior failure mode", summary)
            self.assertIn("Acceptance Criteria remain IMMUTABLE", summary)

    def test_build_prompt_injects_prior_section(self):
        # Minimal Task: body is read lazily from path, so write a real file.
        with tempfile.TemporaryDirectory() as td:
            task_path = Path(td) / "x.md"
            task_path.write_text("# Task body here\n", encoding="utf-8")
            task = codex_impl.Task(
                path=task_path, task_id="x",
                frontmatter={}, sections={},
                scope_fence=codex_impl.ScopeFence(),
                test_commands=[], acceptance_criteria=[],
                skill_contracts="",
            )
            prompt_no_prior = codex_impl.build_codex_prompt(task)
            self.assertNotIn("PREVIOUS ITERATION", prompt_no_prior)
            prior = "## Previous Iteration (auto-injected)\n\n- prior status: fail"
            prompt_with = codex_impl.build_codex_prompt(task, prior_iteration=prior)
            self.assertIn("---- PREVIOUS ITERATION ----", prompt_with)
            self.assertIn("---- END PREVIOUS ITERATION ----", prompt_with)
            # Prior block must come BEFORE the task spec.
            self.assertLess(
                prompt_with.index("PREVIOUS ITERATION"),
                prompt_with.index("TASK SPECIFICATION"),
            )



# --------------------------------------------------------------------------- #
# T8+T9 Stability layer tests                                                 #
# --------------------------------------------------------------------------- #


def _ok_result():
    return codex_impl.CodexRunResult(
        returncode=0, stdout="", stderr="", timed_out=False, self_report=[]
    )


def _rl_result(stderr="HTTP 429: rate limit exceeded"):
    return codex_impl.CodexRunResult(
        returncode=1, stdout="", stderr=stderr, timed_out=False, self_report=[]
    )


class TestIsRateLimitError(unittest.TestCase):
    def test_matches_rate_limit_phrase(self):
        self.assertTrue(codex_impl.is_rate_limit_error("Error: RATE LIMIT exceeded"))
        self.assertTrue(codex_impl.is_rate_limit_error("api returned rate_limit_error"))

    def test_matches_429(self):
        self.assertTrue(codex_impl.is_rate_limit_error("HTTP 429 Too Many Requests"))

    def test_matches_stream_disconnect(self):
        self.assertTrue(codex_impl.is_rate_limit_error(
            "stream disconnected before completion"))

    def test_empty_or_no_match_returns_false(self):
        self.assertFalse(codex_impl.is_rate_limit_error(""))
        self.assertFalse(codex_impl.is_rate_limit_error("some unrelated error"))
        self.assertFalse(codex_impl.is_rate_limit_error("42 is the answer"))  # bare "42" must not match "\b429\b"


class TestRunCodexWithBackoff(unittest.TestCase):
    """AC2/AC3 — rate-limit backoff sequence + final failure preserved."""

    def test_backoff_on_rate_limit_stderr(self):
        """First call rate-limits, second succeeds -> one sleep of 1s."""
        seq = [_rl_result("429 Too Many Requests"), _ok_result()]
        with mock.patch.object(codex_impl, "run_codex", side_effect=seq) as m_run, \
             mock.patch.object(codex_impl.time, "sleep") as m_sleep:
            result = codex_impl.run_codex_with_backoff(
                prompt="x", worktree=Path("."), reasoning="high", timeout=3600)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(m_run.call_count, 2)
            # Backoff of 1s between attempt 1 and 2
            m_sleep.assert_called_once_with(1)

    def test_backoff_on_stream_disconnect(self):
        """Stream-disconnect stderr triggers same retry path (AC1 coverage)."""
        seq = [_rl_result("stream disconnected before completion"), _ok_result()]
        with mock.patch.object(codex_impl, "run_codex", side_effect=seq) as m_run, \
             mock.patch.object(codex_impl.time, "sleep") as m_sleep:
            result = codex_impl.run_codex_with_backoff(
                prompt="x", worktree=Path("."), reasoning="high", timeout=3600)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(m_run.call_count, 2)
            m_sleep.assert_called_once_with(1)

    def test_max_4_retries_then_final_failure_preserved(self):
        """AC2: max 4 attempts. AC3: final stderr kept in returned result."""
        rl = _rl_result("429 persistent")
        with mock.patch.object(codex_impl, "run_codex", return_value=rl) as m_run, \
             mock.patch.object(codex_impl.time, "sleep") as m_sleep:
            result = codex_impl.run_codex_with_backoff(
                prompt="x", worktree=Path("."), reasoning="high", timeout=3600)
            self.assertEqual(m_run.call_count, codex_impl.MAX_RETRIES)
            # 3 sleeps between 4 attempts: 1, 2, 4 (8 would only happen after a 5th)
            self.assertEqual([c.args[0] for c in m_sleep.mock_calls], [1, 2, 4])
            # Final rate-limit stderr preserved (AC3).
            self.assertIn("429", result.stderr)


class TestCircuitStateIO(unittest.TestCase):
    """AC4 — schema round-trip for circuit-state.json."""

    def test_read_missing_returns_empty(self):
        with tempfile.TemporaryDirectory() as td:
            state = codex_impl.read_circuit_state(Path(td))
            self.assertEqual(state["failures"], [])
            self.assertIn("updated_at", state)

    def test_schema_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            codex_impl.record_codex_failure(root, task_id="T1", reason="boom")
            path = root / ".codex" / "circuit-state.json"
            self.assertTrue(path.exists())
            data = codex_impl.read_circuit_state(root)
            self.assertEqual(len(data["failures"]), 1)
            self.assertEqual(data["failures"][0]["task_id"], "T1")
            self.assertIn("timestamp", data["failures"][0])
            self.assertIn("updated_at", data)

    def test_corrupt_state_file_falls_back_to_empty(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".codex").mkdir(parents=True)
            (root / ".codex" / "circuit-state.json").write_text("{{not-json", encoding="utf-8")
            state = codex_impl.read_circuit_state(root)
            self.assertEqual(state["failures"], [])


class TestCircuitBreakerFlag(unittest.TestCase):
    """AC5/AC6/AC7/AC8 — flag lifecycle."""

    def test_exactly_3_failures_opens_circuit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            flag = root / ".codex" / "circuit-open"
            codex_impl.record_codex_failure(root, task_id="T1", reason="r1")
            self.assertFalse(flag.exists())
            codex_impl.record_codex_failure(root, task_id="T2", reason="r2")
            self.assertFalse(flag.exists())
            codex_impl.record_codex_failure(root, task_id="T3", reason="r3")
            self.assertTrue(flag.exists())
            payload = json.loads(flag.read_text(encoding="utf-8"))
            for key in ("opened_at", "expires_at", "reason"):
                self.assertIn(key, payload)

    def test_two_failures_no_flag(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            codex_impl.record_codex_failure(root, task_id="T1", reason="r1")
            codex_impl.record_codex_failure(root, task_id="T2", reason="r2")
            self.assertFalse((root / ".codex" / "circuit-open").exists())

    def test_expired_flag_is_auto_deleted(self):
        """AC7 — check_circuit_open clears expired flag on next invocation."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".codex").mkdir(parents=True)
            flag = root / ".codex" / "circuit-open"
            past = datetime.now(timezone.utc) - timedelta(seconds=10)
            flag.write_text(json.dumps({
                "opened_at": past.isoformat(),
                "expires_at": past.isoformat(),
                "reason": "old",
            }), encoding="utf-8")
            result = codex_impl.check_circuit_open(root)
            self.assertIsNone(result)
            self.assertFalse(flag.exists())

    def test_active_flag_returns_payload(self):
        """AC6 — check_circuit_open returns payload when active."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".codex").mkdir(parents=True)
            flag = root / ".codex" / "circuit-open"
            future = datetime.now(timezone.utc) + timedelta(seconds=60)
            flag.write_text(json.dumps({
                "opened_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": future.isoformat(),
                "reason": "testing",
            }), encoding="utf-8")
            result = codex_impl.check_circuit_open(root)
            self.assertIsNotNone(result)
            self.assertEqual(result["reason"], "testing")
            self.assertTrue(flag.exists())  # not deleted while active

    def test_successful_run_resets_counter(self):
        """AC8 — record_codex_success wipes failures list."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            codex_impl.record_codex_failure(root, task_id="T1", reason="r1")
            codex_impl.record_codex_failure(root, task_id="T2", reason="r2")
            codex_impl.record_codex_success(root)
            state = codex_impl.read_circuit_state(root)
            self.assertEqual(state["failures"], [])
            # Third failure alone must not open the circuit
            codex_impl.record_codex_failure(root, task_id="T3", reason="r3")
            self.assertFalse((root / ".codex" / "circuit-open").exists())


class TestExitDegradedConstant(unittest.TestCase):
    def test_constant_value(self):
        self.assertEqual(codex_impl.EXIT_DEGRADED, 3)
        # Must not collide with existing exit codes.
        self.assertNotIn(3, (codex_impl.EXIT_OK, codex_impl.EXIT_TEST_FAIL,
                             codex_impl.EXIT_SCOPE_OR_TIMEOUT))


# Imports used by T8+T9 tests (lifted after class defs so top-of-file stays
# minimal; unittest discovers cases regardless of import location).
import json  # noqa: E402
from datetime import datetime, timedelta, timezone  # noqa: E402

if __name__ == "__main__":
    unittest.main(verbosity=2)
