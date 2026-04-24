"""Unit tests for codex-scope-check.py.

Run: py -3 .claude/scripts/test_codex_scope_check.py
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).parent / "codex-scope-check.py"


def _load_module():
    """Load codex-scope-check.py as a module (hyphen in filename => importlib.util)."""
    spec = importlib.util.spec_from_file_location("codex_scope_check", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["codex_scope_check"] = mod
    spec.loader.exec_module(mod)
    return mod


scope = _load_module()


# Silence log output during tests.
logging.getLogger("codex_scope_check").setLevel(logging.CRITICAL)


DIFF_ONE_FILE = """diff --git a/src/main.py b/src/main.py
index 1234..5678 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1 +1,2 @@
 print("hi")
+print("bye")
"""

DIFF_TWO_FILES = """diff --git a/src/main.py b/src/main.py
index 1..2 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1 +1 @@
-old
+new
diff --git a/tests/test_main.py b/tests/test_main.py
index 3..4 100644
--- a/tests/test_main.py
+++ b/tests/test_main.py
@@ -1 +1 @@
-a
+b
"""

DIFF_TRAVERSAL = """diff --git a/src/../outside.py b/src/../outside.py
index 1..2 100644
--- a/src/../outside.py
+++ b/src/../outside.py
@@ -1 +1 @@
-x
+y
"""

DIFF_NEW_FILE = """diff --git a/src/new.py b/src/new.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/src/new.py
@@ -0,0 +1 @@
+hello
"""

DIFF_MALFORMED = """this is not a diff
just garbage
diff --gitmalformed
"""


class ParseDiffPathsTests(unittest.TestCase):
    def test_single_file(self):
        paths = scope.parse_diff_paths(DIFF_ONE_FILE)
        self.assertEqual(paths, ["src/main.py"])

    def test_two_files(self):
        paths = scope.parse_diff_paths(DIFF_TWO_FILES)
        self.assertEqual(paths, ["src/main.py", "tests/test_main.py"])

    def test_new_file_uses_b_side(self):
        # "--- /dev/null" but b-side is real → we take b-side
        paths = scope.parse_diff_paths(DIFF_NEW_FILE)
        self.assertEqual(paths, ["src/new.py"])

    def test_empty_diff(self):
        self.assertEqual(scope.parse_diff_paths(""), [])

    def test_malformed_diff_ignored(self):
        self.assertEqual(scope.parse_diff_paths(DIFF_MALFORMED), [])


class CheckPathsTests(unittest.TestCase):
    def setUp(self):
        # Use a real temp dir so realpath resolution is meaningful.
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        (self.root / "src").mkdir()
        (self.root / "tests").mkdir()
        (self.root / "src" / "secrets.py").write_text("x", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def _resolve(self, rel: str) -> str:
        return os.path.realpath(str(self.root / rel))

    def test_no_violations_when_inside_allowed(self):
        allowed = [self._resolve("src")]
        forbidden: list[str] = []
        violations = scope.check_paths(["src/main.py"], allowed, forbidden, self.root)
        self.assertEqual(violations, [])

    def test_one_violation_outside_allowed(self):
        allowed = [self._resolve("src")]
        forbidden: list[str] = []
        violations = scope.check_paths(
            ["docs/README.md"], allowed, forbidden, self.root
        )
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0][0], "docs/README.md")
        self.assertIn("outside", violations[0][1])

    def test_forbidden_path_rejected_even_if_allowed(self):
        allowed = [self._resolve("src")]
        forbidden = [self._resolve("src/secrets.py")]
        violations = scope.check_paths(
            ["src/secrets.py"], allowed, forbidden, self.root
        )
        self.assertEqual(len(violations), 1)
        self.assertIn("forbidden", violations[0][1])

    def test_path_traversal_escape_caught(self):
        # "src/../outside.py" resolves to <root>/outside.py, NOT under src/.
        allowed = [self._resolve("src")]
        forbidden: list[str] = []
        violations = scope.check_paths(
            ["src/../outside.py"], allowed, forbidden, self.root
        )
        self.assertEqual(len(violations), 1, f"Expected escape caught, got {violations}")

    def test_empty_allowed_rejects_everything(self):
        violations = scope.check_paths(
            ["src/main.py"], [], [], self.root
        )
        self.assertEqual(len(violations), 1)
        self.assertIn("no allowed", violations[0][1])

    def test_nested_path_allowed(self):
        allowed = [self._resolve("src")]
        violations = scope.check_paths(
            ["src/deep/nested/file.py"], allowed, [], self.root
        )
        self.assertEqual(violations, [])

    def test_exact_path_match_allowed(self):
        allowed = [self._resolve("src/main.py")]
        violations = scope.check_paths(
            ["src/main.py"], allowed, [], self.root
        )
        self.assertEqual(violations, [])


class ParseFenceTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self):
        self._tmp.cleanup()

    def test_inline_default_allow(self):
        allowed, forbidden = scope.parse_fence("src/,tests/", self.root)
        self.assertEqual(len(allowed), 2)
        self.assertEqual(forbidden, [])

    def test_inline_with_prefixes(self):
        allowed, forbidden = scope.parse_fence(
            "allow:src/,forbid:src/secrets.py", self.root
        )
        self.assertEqual(len(allowed), 1)
        self.assertEqual(len(forbidden), 1)

    def test_fence_from_file_requires_at_prefix(self):
        """File mode is opt-in via ``@`` prefix (post Bug #7 fix)."""
        fence_file = self.root / "fence.txt"
        fence_file.write_text(
            "# comment\n"
            "allow:src/\n"
            "\n"
            "forbid:src/secrets.py\n"
            "tests/\n",
            encoding="utf-8",
        )
        allowed, forbidden = scope.parse_fence(f"@{fence_file}", self.root)
        self.assertEqual(len(allowed), 2)
        self.assertEqual(len(forbidden), 1)

    def test_fence_path_without_at_prefix_is_inline(self):
        """A plain path that happens to exist is treated as inline, NOT read.

        Regression for Bug #7 from dual-1 post-mortem: previously a single
        allowed path like ``.claude/scripts/list_codex_scripts.py`` was
        silently read as a fence file (58 lines -> 42 allowed entries).
        """
        real_file = self.root / "src" / "main.py"
        real_file.parent.mkdir(exist_ok=True)
        real_file.write_text("# pretend code\n", encoding="utf-8")
        allowed, forbidden = scope.parse_fence(str(real_file), self.root)
        # Exactly one allowed entry — the path itself, taken literally.
        self.assertEqual(len(allowed), 1)
        self.assertEqual(len(forbidden), 0)
        self.assertTrue(allowed[0].endswith("main.py"))

    def test_fence_at_prefix_missing_file_raises(self):
        """``@missing.txt`` must raise, not fall through to inline."""
        with self.assertRaises(RuntimeError):
            scope.parse_fence("@/definitely/does/not/exist.txt", self.root)


class CliIntegrationTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        (self.root / "src").mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, diff_text: str, fence: str) -> int:
        diff_file = self.root / "test.diff"
        diff_file.write_text(diff_text, encoding="utf-8")
        return scope.main(
            [
                "--diff", str(diff_file),
                "--fence", fence,
                "--root", str(self.root),
            ]
        )

    def test_clean_diff_exit_0(self):
        rc = self._run(DIFF_ONE_FILE, "allow:src/")
        self.assertEqual(rc, 0)

    def test_violation_exit_2(self):
        rc = self._run(DIFF_TWO_FILES, "allow:src/")  # tests/ not allowed
        self.assertEqual(rc, 2)

    def test_empty_diff_exit_0(self):
        rc = self._run("", "allow:src/")
        self.assertEqual(rc, 0)

    def test_traversal_exit_2(self):
        rc = self._run(DIFF_TRAVERSAL, "allow:src/")
        self.assertEqual(rc, 2)

    def test_missing_diff_exit_2(self):
        rc = scope.main(
            ["--diff", str(self.root / "nope.diff"), "--fence", "allow:src/"]
        )
        self.assertEqual(rc, 2)

    def test_help_works(self):
        # argparse exits via SystemExit; verify exit code 0
        with self.assertRaises(SystemExit) as cm:
            scope.main(["--help"])
        self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
