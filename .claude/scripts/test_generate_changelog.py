"""Tests for generate-changelog.py."""
from __future__ import annotations

import importlib.util
import logging
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).with_name("generate-changelog.py")
SPEC = importlib.util.spec_from_file_location("generate_changelog", SCRIPT_PATH)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class GenerateChangelogTests(unittest.TestCase):
    def setUp(self) -> None:
        logging.getLogger().setLevel(logging.CRITICAL)

    def test_generate_changelog_format(self) -> None:
        with mock.patch.object(mod, "list_checkpoint_tags", return_value=["pipeline-checkpoint-ONE", "pipeline-checkpoint-TWO"]):
            with mock.patch.object(mod, "commit_titles_between", side_effect=[["- feat: first"], ["- fix: second"]]):
                sections = mod.generate_checkpoint_sections(Path("."))
        text = mod.build_changelog("", sections)
        self.assertTrue(text.startswith("# Changelog\n"))
        self.assertIn("## Round 7 (Z12)", text)
        self.assertIn(mod.BEGIN_MARKER, text)
        self.assertIn("## pipeline-checkpoint-TWO\n### Changes\n- fix: second", text)
        self.assertIn("## pipeline-checkpoint-ONE\n### Changes\n- feat: first", text)
        self.assertLess(text.index("## pipeline-checkpoint-TWO"), text.index("## pipeline-checkpoint-ONE"))
        self.assertTrue(text.endswith("\n"))

    def test_generate_changelog_idempotent(self) -> None:
        first = mod.build_changelog("", "## pipeline-checkpoint-ONE\n### Changes\n- feat: first")
        second = mod.build_changelog(first, "## pipeline-checkpoint-ONE\n### Changes\n- feat: first")
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
