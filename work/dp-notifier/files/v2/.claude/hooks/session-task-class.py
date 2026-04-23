"""Bridge stub — re-invokes the real hook from the repo root.

Uses subprocess.run instead of os.execv because os.execv on Windows does
not reliably quote paths containing spaces (e.g. 'C:\Bots\Migrator bots\...').
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _repo_root(start: Path) -> Path | None:
    for cand in [start, *start.parents]:
        if (cand / ".git").exists() and (cand / ".claude" / "hooks").is_dir():
            if cand.resolve() != Path(__file__).resolve().parents[2]:
                return cand
    return None


def main() -> int:
    root = _repo_root(Path(__file__).resolve())
    if root is None:
        return 0
    real = root / ".claude" / "hooks" / "session-task-class.py"
    if not real.is_file():
        return 0
    result = subprocess.run(
        [sys.executable, str(real), *sys.argv[1:]],
        stdin=sys.stdin,
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
