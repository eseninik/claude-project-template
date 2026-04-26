#!/usr/bin/env python3
"""Unit tests for codex-delegate-enforcer.py (task T1).

Covers all 11 required cases from spec AC12:

  1. exempt path (e.g., CLAUDE.md) -> allow
  2. code file + NO recent result.md -> deny with JSON
  3. code file + stale (> 15 min) result.md -> deny
  4. code file + fresh status=pass result.md with covering fence -> allow
  5. code file + fresh pass result.md but fence does NOT cover target -> deny
  6. code file + fresh status=fail result.md -> deny
  7. non-code file (.txt, .md) -> allow
  8. MultiEdit with multiple files, all covered -> allow
  9. MultiEdit with one file uncovered -> deny
 10. malformed result.md / corrupt JSON payload -> pass-through (no crash)
 11. hook called on non-Edit event (e.g., Bash) -> pass-through

Each test isolates state under a temporary CLAUDE_PROJECT_DIR so
production .codex/ and work/ directories are never touched.
"""

from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENFORCER_PATH = HERE / "codex-delegate-enforcer.py"


def _load_module():
    """Import codex-delegate-enforcer.py as a module (hyphen in filename)."""
    spec = importlib.util.spec_from_file_location(
        "codex_delegate_enforcer", ENFORCER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BaseEnforcerTest(unittest.TestCase):
    """Shared fixture: isolated project root with results + tasks dirs."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp(prefix="codex-enforcer-test-")
        self.root = Path(self.tmpdir).resolve()
        (self.root / ".claude" / "hooks").mkdir(parents=True)
        (self.root / "work" / "codex-primary" / "tasks").mkdir(parents=True)
        (self.root / "work" / "codex-implementations").mkdir(parents=True)
        # Target file the tool call "would edit"
        self.target_rel = ".claude/hooks/my_hook.py"
        (self.root / ".claude" / "hooks" / "my_hook.py").write_text(
            "# placeholder\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ----- subprocess invocation helpers -----

    def _run_enforcer(self, payload):
        """Invoke enforcer as subprocess; return (exit_code, stdout, stderr)."""
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)}
        result = subprocess.run(
            [sys.executable, str(ENFORCER_PATH)],
            input=json.dumps(payload),
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            env=env, timeout=30,
        )
        return result.returncode, result.stdout, result.stderr

    # ----- fixture helpers -----

    def _write_task(self, task_id: str, fence_paths: list) -> Path:
        """Write a task-N.md with given Scope Fence allowed paths."""
        task_file = self.root / "work" / "codex-primary" / "tasks" / (
            "T" + task_id + "-test.md"
        )
        fence_block = "\n".join("- `" + p + "`" for p in fence_paths)
        task_file.write_text(
            "---\nexecutor: codex\n---\n\n"
            "# Task T" + task_id + "\n\n"
            "## Your Task\ntest\n\n"
            "## Scope Fence\n"
            "**Allowed paths (may be written):**\n"
            + fence_block + "\n\n"
            "**Forbidden paths:**\n- other/\n\n"
            "## Acceptance Criteria\n- [ ] AC1\n",
            encoding="utf-8",
        )
        return task_file

    def _write_result(self, task_id: str, status: str, age_seconds: float = 0) -> Path:
        """Write a task-N-result.md with given status and optional mtime offset."""
        result_file = self.root / "work" / "codex-implementations" / (
            "task-" + task_id + "-result.md"
        )
        task_file_rel = "work/codex-primary/tasks/T" + task_id + "-test.md"
        result_file.write_text(
            "# Result T" + task_id + "\n\n"
            "- status: " + status + "\n"
            "- task_file: " + task_file_rel + "\n\n"
            "## Diff\n(none)\n",
            encoding="utf-8",
        )
        if age_seconds > 0:
            old = time.time() - age_seconds
            os.utime(result_file, (old, old))
        return result_file

    def _edit_payload(self, file_path: str) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": file_path,
                "old_string": "a",
                "new_string": "b",
            },
        }

    def _write_payload(self, file_path: str) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": file_path, "content": "x"},
        }

    def _multiedit_payload(self, paths: list) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "MultiEdit",
            "tool_input": {
                "edits": [
                    {"file_path": p, "old_string": "a", "new_string": "b"}
                    for p in paths
                ],
            },
        }

    # ----- response assertions -----

    def _assert_allow(self, code: int, stdout: str, stderr: str) -> None:
        self.assertEqual(code, 0, msg="expected exit 0. stderr=" + stderr)
        # No deny JSON in stdout.
        if stdout.strip():
            try:
                parsed = json.loads(stdout)
                decision = (
                    parsed.get("hookSpecificOutput", {})
                    .get("permissionDecision")
                )
                self.assertNotEqual(
                    decision, "deny", msg="unexpected deny JSON: " + stdout
                )
            except json.JSONDecodeError:
                pass  # non-JSON stdout is fine

    def _assert_deny(self, code: int, stdout: str, stderr: str) -> None:
        self.assertEqual(code, 0, msg="expected exit 0 (deny via JSON). stderr=" + stderr)
        self.assertTrue(stdout.strip(), msg="expected deny JSON on stdout")
        parsed = json.loads(stdout)
        decision = parsed["hookSpecificOutput"]["permissionDecision"]
        self.assertEqual(decision, "deny")
        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("Code Delegation Protocol", reason)


class TestAC12Cases(BaseEnforcerTest):
    """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""

    def test_01_exempt_path_allow(self) -> None:
        """AC12.1: exempt path (CLAUDE.md) -> allow."""
        code, out, err = self._run_enforcer(self._write_payload("CLAUDE.md"))
        self._assert_allow(code, out, err)

    def test_02_code_no_result_deny(self) -> None:
        """AC12.2: code file + NO recent result.md -> deny with JSON."""
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_03_stale_result_deny(self) -> None:
        """AC12.3: code file + stale (> 15 min) result.md -> deny."""
        self._write_task("3", [self.target_rel])
        self._write_result("3", "pass", age_seconds=20 * 60)  # 20 min old
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_04_covered_pass_allow(self) -> None:
        """AC12.4: code file + fresh pass result.md with covering fence -> allow."""
        self._write_task("4", [self.target_rel])
        self._write_result("4", "pass")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_allow(code, out, err)

    def test_05_uncovered_pass_deny(self) -> None:
        """AC12.5: fresh pass, fence does NOT cover target -> deny."""
        self._write_task("5", ["other/unrelated.py"])
        self._write_result("5", "pass")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_06_fail_status_deny(self) -> None:
        """AC12.6: fresh status=fail result.md -> deny."""
        self._write_task("6", [self.target_rel])
        self._write_result("6", "fail")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_07_non_code_file_allow(self) -> None:
        """AC12.7: non-code file (.txt, .md) -> allow."""
        for suffix in (".txt", ".md"):
            notes = ".claude/hooks/notes" + suffix
            (self.root / notes).write_text("x", encoding="utf-8")
            code, out, err = self._run_enforcer(self._write_payload(notes))
            self._assert_allow(code, out, err)

    def test_08_multiedit_all_covered_allow(self) -> None:
        """AC12.8: MultiEdit with multiple files, all covered -> allow."""
        a = ".claude/hooks/a.py"
        b = ".claude/hooks/b.py"
        (self.root / a).write_text("# a\n", encoding="utf-8")
        (self.root / b).write_text("# b\n", encoding="utf-8")
        self._write_task("8", [".claude/hooks/"])
        self._write_result("8", "pass")
        code, out, err = self._run_enforcer(self._multiedit_payload([a, b]))
        self._assert_allow(code, out, err)

    def test_09_multiedit_one_uncovered_deny(self) -> None:
        """AC12.9: MultiEdit with one file uncovered -> deny."""
        a = ".claude/hooks/a.py"
        b = "src/uncovered.py"
        (self.root / a).write_text("# a\n", encoding="utf-8")
        (self.root / "src").mkdir(parents=True)
        (self.root / b).write_text("# b\n", encoding="utf-8")
        self._write_task("9", [".claude/hooks/"])
        self._write_result("9", "pass")
        code, out, err = self._run_enforcer(self._multiedit_payload([a, b]))
        self._assert_deny(code, out, err)

    def test_10a_malformed_result_passthrough(self) -> None:
        """AC12.10a: malformed result.md -> no crash, handled gracefully."""
        # Write a recent file but with completely corrupt body.
        result_file = self.root / "work" / "codex-implementations" / (
            "task-10-result.md"
        )
        result_file.write_bytes(b"\x00\x01\xff garbage no fields here")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        # No crash: exit 0. Since no fence covers target, it is denied -
        # the point is the script didn't blow up (no traceback in stderr).
        self.assertEqual(code, 0)
        self.assertNotIn("Traceback", err)

    def test_10b_corrupt_json_payload_passthrough(self) -> None:
        """AC12.10b: corrupt JSON payload -> pass-through, no crash, exit 0."""
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)}
        result = subprocess.run(
            [sys.executable, str(ENFORCER_PATH)],
            input="{this-is-not-json",
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            env=env, timeout=30,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")
        self.assertNotIn("Traceback", result.stderr)

    def test_11_non_edit_event_passthrough(self) -> None:
        """AC12.11: non-Edit tool (Bash) -> pass-through (exit 0, no deny)."""
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
        }
        code, out, err = self._run_enforcer(payload)
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "")


class TestDualTeamsSentinel(unittest.TestCase):
    """Regression tests for dual-teams worktree sentinel detection."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()

    def test_dual_teams_worktree_true_in_project_dir(self) -> None:
        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
            project_dir = Path(tmpdir).resolve()
            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")

            self.assertTrue(self.mod.is_dual_teams_worktree(project_dir))

    def test_dual_teams_worktree_true_in_parent_dir(self) -> None:
        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
            project_dir = Path(tmpdir).resolve()
            nested = project_dir / "worktrees" / "validation" / "claude"
            nested.mkdir(parents=True)
            (project_dir / ".dual-base-ref").write_text("main\n", encoding="utf-8")

            self.assertTrue(self.mod.is_dual_teams_worktree(nested))

    def test_dual_teams_worktree_false_without_sentinel(self) -> None:
        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
            project_dir = Path(tmpdir).resolve()
            nested = project_dir / "a" / "b" / "c"
            nested.mkdir(parents=True)

            self.assertFalse(self.mod.is_dual_teams_worktree(nested))

    def test_dual_teams_worktree_false_for_directory_sentinel(self) -> None:
        with tempfile.TemporaryDirectory(prefix="codex-enforcer-sentinel-") as tmpdir:
            project_dir = Path(tmpdir).resolve()
            (project_dir / ".dual-base-ref").mkdir()

            self.assertFalse(self.mod.is_dual_teams_worktree(project_dir))


class TestDualTeamsDecide(BaseEnforcerTest):
    """Regression tests for the dual-teams passthrough in decide()."""

    def setUp(self) -> None:
        super().setUp()
        self.mod = _load_module()
        self.script_rel = ".claude/scripts/foo.py"
        (self.root / ".claude" / "scripts").mkdir(parents=True)
        (self.root / self.script_rel).write_text("# foo\n", encoding="utf-8")

    def test_decide_allows_edit_when_sentinel_present_without_result(self) -> None:
        (self.root / ".dual-base-ref").write_text("main\n", encoding="utf-8")
        shutil.rmtree(self.root / "work", ignore_errors=True)

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)

        self.assertTrue(allowed)
        self.assertEqual(stdout.getvalue().strip(), "")

    def test_decide_denies_edit_when_sentinel_absent_without_result(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            allowed = self.mod.decide(self._edit_payload(self.script_rel), self.root)

        self.assertFalse(allowed)
        parsed = json.loads(stdout.getvalue())
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")


class TestHelpers(unittest.TestCase):
    """Direct unit tests of helper functions (no subprocess)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()

    def test_is_code_extension_positive(self) -> None:
        for p in ("a.py", "x/y/z.js", "lib/mod.rs", "s.cpp", "x.SQL"):
            self.assertTrue(self.mod.is_code_extension(p), p)

    def test_is_code_extension_negative(self) -> None:
        for p in ("README.md", "doc.txt", "config.yaml", "a.json", "b"):
            self.assertFalse(self.mod.is_code_extension(p), p)

    def test_is_exempt_memory_star_star(self) -> None:
        self.assertTrue(self.mod.is_exempt(".claude/memory/activeContext.md"))
        self.assertTrue(self.mod.is_exempt(".claude/memory/daily/2026-04-24.md"))

    def test_is_exempt_top_level_files(self) -> None:
        for p in ("CLAUDE.md", "AGENTS.md", "README.md", ".gitignore", "LICENSE"):
            self.assertTrue(self.mod.is_exempt(p), p)

    def test_is_exempt_guides_skills_adr(self) -> None:
        self.assertTrue(self.mod.is_exempt(".claude/adr/adr-001.md"))
        self.assertTrue(self.mod.is_exempt(".claude/guides/foo.md"))
        self.assertTrue(self.mod.is_exempt(".claude/skills/bar/SKILL.md"))

    def test_is_exempt_negative(self) -> None:
        self.assertFalse(self.mod.is_exempt(".claude/hooks/my_hook.py"))
        self.assertFalse(self.mod.is_exempt("src/main.py"))

    def test_requires_cover_positive(self) -> None:
        self.assertTrue(self.mod.requires_cover(".claude/hooks/x.py"))
        self.assertTrue(self.mod.requires_cover("src/main.ts"))

    def test_requires_cover_negative_non_code(self) -> None:
        self.assertFalse(self.mod.requires_cover("docs/readme.md"))

    def test_requires_cover_negative_exempt(self) -> None:
        # .claude/skills/**/*.md is exempt, and .md is non-code anyway.
        self.assertFalse(self.mod.requires_cover("CLAUDE.md"))
        # Z1/I1 (Extension wins): non-code under work/** is exempt;
        # code under work/** STILL requires cover.
        self.assertFalse(self.mod.requires_cover("work/notes.md"))
        self.assertTrue(self.mod.requires_cover("work/scripts/helper.py"))

    def test_path_in_fence_exact_file(self) -> None:
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/c.py"]))

    def test_path_in_fence_dir_prefix(self) -> None:
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b"]))
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/"]))

    def test_path_in_fence_no_partial_segment(self) -> None:
        self.assertFalse(self.mod.path_in_fence("a/bb/c.py", ["a/b"]))

    def test_path_in_fence_strips_trailing_globs(self) -> None:
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/**"]))
        self.assertTrue(self.mod.path_in_fence("a/b/c.py", ["a/b/*"]))

    def test_parse_result_fields_status_pass(self) -> None:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".md", delete=False, encoding="utf-8"
        ) as fh:
            fh.write("# result\n\n- status: pass\n- task_file: t.md\n")
            p = Path(fh.name)
        try:
            fields = self.mod.parse_result_fields(p)
            self.assertEqual(fields.get("status"), "pass")
            self.assertEqual(fields.get("task_file"), "t.md")
        finally:
            p.unlink()

    def test_parse_scope_fence_strips_backticks_and_annotations(self) -> None:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".md", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(
                "# Task\n\n"
                "## Scope Fence\n"
                "**Allowed paths (may be written):**\n"
                "- `.claude/hooks/x.py` (new)\n"
                "- `.claude/hooks/test_x.py`\n\n"
                "**Forbidden paths:**\n- else/\n\n## Next\n"
            )
            p = Path(fh.name)
        try:
            fence = self.mod.parse_scope_fence(p)
            self.assertIn(".claude/hooks/x.py", fence)
            self.assertIn(".claude/hooks/test_x.py", fence)
        finally:
            p.unlink()

    def test_extract_targets_edit(self) -> None:
        paths = self.mod.extract_targets({
            "tool_name": "Edit",
            "tool_input": {"file_path": "a.py", "old_string": "x", "new_string": "y"},
        })
        self.assertEqual(paths, ["a.py"])

    def test_extract_targets_multiedit(self) -> None:
        paths = self.mod.extract_targets({
            "tool_name": "MultiEdit",
            "tool_input": {
                "edits": [
                    {"file_path": "a.py", "old_string": "x", "new_string": "y"},
                    {"file_path": "b.py", "old_string": "x", "new_string": "y"},
                ],
            },
        })
        self.assertEqual(sorted(paths), ["a.py", "b.py"])

    def test_extract_targets_missing_is_empty(self) -> None:
        self.assertEqual(self.mod.extract_targets({}), [])
        self.assertEqual(self.mod.extract_targets({"tool_name": "Edit"}), [])
        self.assertEqual(self.mod.extract_targets(None), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
