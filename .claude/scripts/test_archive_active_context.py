"""Tests for archive-active-context.py."""
from __future__ import annotations

import argparse
import importlib.util
import io
import logging
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("archive-active-context.py")
SPEC = importlib.util.spec_from_file_location("archive_active_context", SCRIPT_PATH)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def _args(active_context: Path, archive_dir: Path, line_limit: int = 200, dry_run: bool = False) -> argparse.Namespace:
    return argparse.Namespace(
        active_context=str(active_context),
        archive_dir=str(archive_dir),
        line_limit=line_limit,
        dry_run=dry_run,
        verbose=False,
    )


class ArchiveActiveContextTests(unittest.TestCase):
    TODAY = date(2026, 4, 26)

    def setUp(self) -> None:
        logging.getLogger().setLevel(logging.CRITICAL)

    def test_archive_when_under_200_lines_noop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            active = root / "activeContext.md"
            archive_dir = root / "archive"
            active.write_text("# Active Context\n\n## Round 1\nshort\n", encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = mod.run(_args(active, archive_dir, dry_run=True), today_value=self.TODAY)
            self.assertEqual(rc, 0)
            self.assertIn("no archive needed", buf.getvalue())
            self.assertEqual(active.read_text(encoding="utf-8"), "# Active Context\n\n## Round 1\nshort\n")
            self.assertFalse(archive_dir.exists())

    def test_archive_when_over_200_lines_extracts_oldest_round(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            active = root / "activeContext.md"
            archive_dir = root / "archive"
            round_two = "## Round 2\n" + "\n".join("new " + str(i) for i in range(120)) + "\n"
            round_one = "## Round 1\n" + "\n".join("old " + str(i) for i in range(120)) + "\n"
            active.write_text("# Active Context\n\n" + round_two + "\n" + round_one, encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = mod.run(_args(active, archive_dir), today_value=self.TODAY)
            self.assertEqual(rc, 0)
            self.assertIn("archived:", buf.getvalue())
            archived = archive_dir / "active-2026-04-26-round1.md"
            self.assertTrue(archived.exists())
            self.assertIn("## Round 1", archived.read_text(encoding="utf-8"))
            remaining = active.read_text(encoding="utf-8")
            self.assertIn("## Round 2", remaining)
            self.assertNotIn("## Round 1", remaining)

    def test_archive_preserves_header(self) -> None:
        content = "# Active Context\n\n> Keep this header.\n\n## Round 3\nnew\n\n## Round 1\nold\n"
        archived, remaining = mod._extract_oldest_round(content)
        self.assertIn("## Round 1", archived)
        self.assertTrue(remaining.startswith("# Active Context\n\n> Keep this header.\n"))
        self.assertIn("## Round 3", remaining)
        self.assertNotIn("## Round 1", remaining)

    def test_archive_supports_current_focus_round_headings(self) -> None:
        content = "# Active Context\n\n## Current Focus\n\n### Round 3\nnew\n\n### Round 1\nold\n\n## Session Log\nkeep\n"
        archived, remaining = mod._extract_oldest_round(content)
        self.assertIn("### Round 1", archived)
        self.assertNotIn("## Session Log", archived)
        self.assertIn("### Round 3", remaining)
        self.assertIn("## Session Log", remaining)
        self.assertNotIn("### Round 1", remaining)


if __name__ == "__main__":
    unittest.main()
