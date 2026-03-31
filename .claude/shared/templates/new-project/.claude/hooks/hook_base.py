#!/usr/bin/env python3
"""Shared utilities for Claude Code hooks on Windows.

Every hook duplicates: encoding setup, path resolution, git operations,
logging config.  This module extracts those into importable helpers.

Hook Profiles (runtime control via environment variables):
  CLAUDE_HOOK_PROFILE=minimal|standard|strict  (default: standard)
    minimal  — only essential hooks: session-orient, tool-failure-logger
    standard — all hooks enabled (current default behavior)
    strict   — all hooks + extra validation (future use)

  CLAUDE_DISABLED_HOOKS="hook1,hook2"  (comma-separated hook names to disable)
    Overrides profile — a hook listed here is always skipped.

Usage in any hook:
    from hook_base import should_run
    if not should_run("my-hook-name"):
        sys.exit(0)
"""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Windows encoding
# ---------------------------------------------------------------------------

def setup_windows():
    """Configure UTF-8 encoding on Windows (safe no-op elsewhere)."""
    if sys.platform == "win32":
        for stream in [sys.stdin, sys.stdout, sys.stderr]:
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def get_logger(name: str) -> logging.Logger:
    """Create a hook logger that writes to stderr with a standard format."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(name)s %(levelname)s %(message)s",
            stream=sys.stderr,
        )
    return logger

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def get_project_dir() -> Path:
    """Get project directory from CLAUDE_PROJECT_DIR env var or cwd."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()

# ---------------------------------------------------------------------------
# Payload
# ---------------------------------------------------------------------------

def read_payload():
    """Read JSON payload from stdin.  Returns None on empty input."""
    raw = sys.stdin.read()
    if not raw.strip():
        return None
    return json.loads(raw)

# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def get_changed_files(project_dir=None):
    """Get list of changed + untracked files via git.

    Tries ``git diff --name-only HEAD`` first, falls back to unstaged diff,
    then appends untracked files.
    """
    cwd = str(project_dir) if project_dir else None
    changed = []
    for cmd in [
        ["git", "diff", "--name-only", "HEAD"],
        ["git", "diff", "--name-only"],
    ]:
        try:
            r = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10, cwd=cwd,
            )
            if r.stdout.strip():
                changed = r.stdout.strip().splitlines()
                break
        except Exception:
            continue

    try:
        r = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True, text=True, timeout=10, cwd=cwd,
        )
        if r.stdout.strip():
            changed.extend(r.stdout.strip().splitlines())
    except Exception:
        pass

    return changed

# ---------------------------------------------------------------------------
# External tool discovery
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Hook Profiles
# ---------------------------------------------------------------------------

HOOK_PROFILES = {
    "minimal": {
        "session-orient",
        "tool-failure-logger",
    },
    "standard": {
        "session-orient",
        "tool-failure-logger",
        "write-validate",
        "pre-compact-save",
        "task-completed-gate",
        "codex-parallel",
        "codex-review",
        "truthguard",
        "config-protection",
    },
    "strict": {
        "session-orient",
        "tool-failure-logger",
        "write-validate",
        "pre-compact-save",
        "task-completed-gate",
        "codex-parallel",
        "codex-review",
        "truthguard",
        "config-protection",
    },
}


def get_hook_profile() -> str:
    """Return current hook profile from CLAUDE_HOOK_PROFILE env var."""
    return os.environ.get("CLAUDE_HOOK_PROFILE", "standard").lower()


def is_hook_disabled(hook_name: str) -> bool:
    """Check if hook is explicitly disabled via CLAUDE_DISABLED_HOOKS."""
    disabled = os.environ.get("CLAUDE_DISABLED_HOOKS", "")
    if not disabled:
        return False
    return hook_name in [h.strip() for h in disabled.split(",")]


def should_run(hook_name: str, profile_override: str = None) -> bool:
    """Single check: should this hook execute?

    Returns False if:
      - hook is in CLAUDE_DISABLED_HOOKS
      - hook is not in the active profile's allowed set
    Returns True otherwise (standard profile allows all).
    """
    logger = get_logger("hook-profiles")
    if is_hook_disabled(hook_name):
        logger.info("hook=%s action=skip reason=disabled_by_env", hook_name)
        return False

    profile = profile_override or get_hook_profile()
    allowed = HOOK_PROFILES.get(profile, HOOK_PROFILES["standard"])

    if hook_name not in allowed:
        logger.info(
            "hook=%s action=skip reason=not_in_profile profile=%s",
            hook_name, profile,
        )
        return False

    return True


# ---------------------------------------------------------------------------
# External tool discovery
# ---------------------------------------------------------------------------

def find_codex():
    """Find codex binary, including Windows npm global path.

    Returns the path string if found, None otherwise.
    """
    import shutil

    codex_bin = shutil.which("codex")
    if codex_bin:
        return codex_bin
    npm_codex = Path.home() / "AppData" / "Roaming" / "npm" / "codex.cmd"
    if npm_codex.exists():
        return str(npm_codex)
    return None
