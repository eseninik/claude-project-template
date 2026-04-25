#!/usr/bin/env python3
"""test_spawn_agent.py — Smoke tests for the Y14 reminder block injection.

Exercises ``.claude/scripts/spawn-agent.py`` end-to-end via ``subprocess``
because the script name contains a hyphen (not importable as a module).
Each test asserts an Acceptance Criterion from
``work/codex-implementations/inline/task-Y16-update-spawn-agent.md``:

* ``test_y14_section_present`` — AC1 + AC5(a)
* ``test_y14_section_appears_once`` — AC2 + AC5(b)
* ``test_y14_block_contains_powershell_keywords`` — AC5(c)
* ``test_dry_run_grep_count_one`` — AC3
* ``test_detect_only_unchanged`` — AC4

Run with:

    py -3 .claude/scripts/test_spawn_agent.py

Stdlib only; works on Windows + POSIX.
"""

from __future__ import annotations

import logging
import subprocess
import sys
import unittest
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging (per global hard rule: every module gets structured logging).
# ---------------------------------------------------------------------------

logger = logging.getLogger("test_spawn_agent")
if not logger.handlers:
    _h = logging.StreamHandler(sys.stderr)
    _h.setFormatter(
        logging.Formatter(
            "%(asctime)s level=%(levelname)s %(name)s %(message)s"
        )
    )
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
SPAWN_SCRIPT = REPO_ROOT / ".claude" / "scripts" / "spawn-agent.py"

Y14_HEADING = "## CRITICAL — sub-agent file write mechanism (Y14 finding)"


def run_spawn(*extra_args: str) -> subprocess.CompletedProcess:
    """Invoke ``spawn-agent.py`` with the given extra CLI flags.

    Captures stdout/stderr separately, decodes as UTF-8 with replacement
    so Windows cp1251 consoles never corrupt the result, and returns the
    raw ``CompletedProcess`` for the caller to inspect.

    Parameters
    ----------
    *extra_args : str
        CLI flags appended after ``py -3 spawn-agent.py``.

    Returns
    -------
    subprocess.CompletedProcess
        With ``.stdout`` and ``.stderr`` as ``str`` objects.
    """
    cmd = [sys.executable, str(SPAWN_SCRIPT), *extra_args]
    logger.info("event=run_spawn.enter cmd=%s", cmd)
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(REPO_ROOT),
        timeout=60,
        check=False,
    )
    logger.info(
        "event=run_spawn.exit returncode=%d stdout_chars=%d stderr_chars=%d",
        proc.returncode,
        len(proc.stdout or ""),
        len(proc.stderr or ""),
    )
    return proc


def dry_run_prompt(task: str = "Demo task for Y14 verification") -> str:
    """Return the stdout of a ``--dry-run`` invocation as one string.

    Parameters
    ----------
    task : str
        Task description fed to spawn-agent.py.

    Returns
    -------
    str
        Combined stdout text.
    """
    proc = run_spawn(
        "--task", task,
        "--team", "t",
        "--name", "n",
        "--dry-run",
    )
    if proc.returncode != 0:
        logger.error(
            "event=dry_run_prompt.fail returncode=%d stderr=%s",
            proc.returncode,
            proc.stderr,
        )
    return proc.stdout


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class Y14InjectionTests(unittest.TestCase):
    """Verify the Y14 block is embedded in every generated prompt."""

    def test_y14_section_present(self) -> None:
        """AC1 / AC5(a): generated prompt contains the Y14 heading."""
        logger.info("event=test.y14_section_present.enter")
        prompt = dry_run_prompt()
        self.assertIn(
            Y14_HEADING,
            prompt,
            msg="Y14 heading missing from generated prompt (AC1)",
        )
        logger.info("event=test.y14_section_present.exit pass=true")

    def test_y14_section_appears_once(self) -> None:
        """AC2 / AC5(b): the Y14 heading appears exactly once per prompt."""
        logger.info("event=test.y14_section_appears_once.enter")
        prompt = dry_run_prompt()
        count = prompt.count(Y14_HEADING)
        self.assertEqual(
            count, 1,
            msg=(
                f"Expected exactly 1 Y14 heading, found {count}. "
                "inject_y14_block() is not idempotent (AC2)."
            ),
        )
        logger.info("event=test.y14_section_appears_once.exit pass=true count=%d", count)

    def test_y14_block_contains_powershell_keywords(self) -> None:
        """AC5(c): block mentions ``Set-Content -Encoding utf8`` + ``PowerShell``."""
        logger.info("event=test.y14_block_keywords.enter")
        prompt = dry_run_prompt()
        for needle in ("Set-Content -Encoding utf8", "PowerShell"):
            self.assertIn(
                needle,
                prompt,
                msg=f"Y14 block missing required literal: {needle!r} (AC5c)",
            )
        logger.info("event=test.y14_block_keywords.exit pass=true")

    def test_dry_run_grep_count_one(self) -> None:
        """AC3: ``grep -c "Y14 finding"`` against --dry-run stdout returns 1."""
        logger.info("event=test.dry_run_grep_count.enter")
        prompt = dry_run_prompt()
        finding_count = sum(
            1 for line in prompt.splitlines() if "Y14 finding" in line
        )
        self.assertEqual(
            finding_count, 1,
            msg=(
                f"grep -c 'Y14 finding' should return 1 per AC3, got {finding_count}"
            ),
        )
        logger.info(
            "event=test.dry_run_grep_count.exit pass=true count=%d",
            finding_count,
        )

    def test_detect_only_unchanged(self) -> None:
        """AC4: ``--detect-only`` still works and does NOT emit the prompt."""
        logger.info("event=test.detect_only.enter")
        proc = run_spawn(
            "--task", "Implement a login flow",
            "--detect-only",
        )
        self.assertEqual(
            proc.returncode, 0,
            msg=f"--detect-only should exit 0, got {proc.returncode}",
        )
        # Detect-only stdout must NOT contain the Y14 block — it only prints
        # auto-detection metadata.
        self.assertNotIn(
            Y14_HEADING, proc.stdout,
            msg="--detect-only must not emit the prompt (AC4)",
        )
        self.assertIn(
            "Auto-detection result:", proc.stdout,
            msg="--detect-only output preamble missing (regression)",
        )
        logger.info("event=test.detect_only.exit pass=true")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """Run the test suite via ``unittest`` and return its exit code."""
    logger.info("event=main.enter spawn_script=%s", SPAWN_SCRIPT)
    if not SPAWN_SCRIPT.is_file():
        logger.error(
            "event=main.fail reason=spawn_script_missing path=%s",
            SPAWN_SCRIPT,
        )
        print(
            f"ERROR: spawn-agent.py not found at {SPAWN_SCRIPT}",
            file=sys.stderr,
        )
        return 2

    suite = unittest.TestLoader().loadTestsFromTestCase(Y14InjectionTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    rc = 0 if result.wasSuccessful() else 1
    logger.info("event=main.exit returncode=%d", rc)
    return rc


if __name__ == "__main__":
    sys.exit(main())
