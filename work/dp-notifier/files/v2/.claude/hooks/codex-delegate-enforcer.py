"""Bridge stub template — re-invokes the real hook from the repo root.

This is the CANONICAL stub implementation. Deployed copies are identical
except for filename. The hook name is derived from __file__.name at runtime,
so the same code works for any hook without per-file customization.

Why this exists: Claude Code sessions running from a staging subdirectory
(e.g. work/something/files/v2/) invoke hooks relative to the CWD, which
resolves to `<cwd>/.claude/hooks/<hook>.py` and fails if not present.
A stub at that path re-execs the real hook from the repo root.

Why subprocess.run (not os.execv): os.execv on Windows does not reliably
quote paths containing spaces like 'C:\Bots\Migrator bots\'. subprocess.run
with a list argument is the portable correct pattern.

Regenerate all stubs in staging dirs with:
  py -3 .claude/scripts/sync-bridge-stubs.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _repo_root(start: Path) -> Path | None:
    """Walk up until we find a parent with .git and .claude/hooks — but not
    the staging dir itself (which also has .claude/hooks)."""
    stub_root = Path(__file__).resolve().parents[2]
    for cand in [start, *start.parents]:
        if (cand / ".git").exists() and (cand / ".claude" / "hooks").is_dir():
            if cand.resolve() != stub_root:
                return cand
    return None


def main() -> int:
    hook_name = Path(__file__).name
    root = _repo_root(Path(__file__).resolve())
    if root is None:
        return 0  # No repo root found — fail silent, don't block session
    real = root / ".claude" / "hooks" / hook_name
    if not real.is_file():
        return 0  # Real hook not deployed — fail silent
    result = subprocess.run(
        [sys.executable, str(real), *sys.argv[1:]],
        stdin=sys.stdin,
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
