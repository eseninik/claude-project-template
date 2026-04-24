"""Print active git worktrees as path, branch, and SHA."""

from __future__ import annotations

import logging
import subprocess
import sys


LOGGER = logging.getLogger(__name__)


def get_worktree_porcelain() -> str:
    """Return porcelain output from git worktree list."""
    command = ["git", "worktree", "list", "--porcelain"]
    LOGGER.info("git_worktree_list.git.start", extra={"command": command})
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.CalledProcessError as error:
        LOGGER.exception("git_worktree_list.git.failed", extra={"returncode": error.returncode})
        result = subprocess.run(
            ["git", "-c", "safe.directory=*", "worktree", "list", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    LOGGER.info("git_worktree_list.git.exit", extra={"stdout_lines": len(result.stdout.splitlines())})
    return result.stdout


def main() -> int:
    """Print one tab-separated line per active git worktree."""
    LOGGER.info("git_worktree_list.main.start")
    records: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in get_worktree_porcelain().splitlines():
        if not line:
            if current:
                records.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    if current:
        records.append(current)

    for record in records:
        sha = record.get("HEAD", "")
        branch = record.get("branch", "")
        if branch.startswith("refs/heads/"):
            branch = branch.removeprefix("refs/heads/")
        if not branch:
            branch = sha[:7] or "(detached)"
        sys.stdout.write(f"{record.get('worktree', '')}\t{branch}\t{sha}\n")

    LOGGER.info("git_worktree_list.main.exit", extra={"worktree_count": len(records)})
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    raise SystemExit(main())
