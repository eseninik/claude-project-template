#!/usr/bin/env python3
"""Sync bridge-stub files across all staging directories in this repo.

Scans .claude/settings.json for every `py -3 .claude/hooks/X.py` hook
command, then walks the repo finding every `.claude/hooks/` directory
under work/ (or similar staging areas). For each (hook, staging_dir)
combination, ensures a bridge-stub exists — the canonical stub from
.claude/scripts/bridge-stub-template.py copied with the hook's filename.

Run this:
  - After adding a new hook to settings.json
  - After creating a new staging directory with .claude/hooks/
  - When staging-session hooks are failing with [Errno 2]

Usage:
  py -3 .claude/scripts/sync-bridge-stubs.py [--dry-run] [--verbose]

Exit 0 on success, 1 if any stub could not be written.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger("sync-bridge-stubs")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    stream=sys.stderr,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = REPO_ROOT / ".claude" / "scripts" / "bridge-stub-template.py"
HOOK_CMD_RE = re.compile(r"\.claude/hooks/([a-zA-Z0-9_\-]+\.py)")


def extract_hook_filenames(settings_path: Path) -> set[str]:
    """Parse settings.json and collect every hook filename mentioned."""
    logger.info("extract_hook_filenames from=%s", settings_path)
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        logger.error("settings.json read/parse failed: %s", e)
        return set()

    text = json.dumps(data)
    hooks = set(HOOK_CMD_RE.findall(text))
    logger.info("extract_hook_filenames found=%d hooks", len(hooks))
    return hooks


def find_staging_hook_dirs(root: Path) -> list[Path]:
    """Find every `.claude/hooks/` inside staging areas (work/, etc.)
    except the repo root's own .claude/hooks.
    """
    repo_hooks = (root / ".claude" / "hooks").resolve()
    results = []
    # Search under work/, deploy/, staging/ — configurable if needed.
    for top in ["work", "deploy", "staging"]:
        top_dir = root / top
        if not top_dir.is_dir():
            continue
        for hooks_dir in top_dir.rglob(".claude/hooks"):
            if hooks_dir.resolve() == repo_hooks:
                continue
            if hooks_dir.is_dir():
                results.append(hooks_dir)
    logger.info("find_staging_hook_dirs count=%d dirs=%s",
                len(results), [str(d.relative_to(root)) for d in results])
    return results


def write_stub(staging_dir: Path, hook_name: str, template: str,
               dry_run: bool) -> tuple[bool, str]:
    """Ensure a stub at staging_dir/hook_name exists with canonical content.

    Returns (was_changed, action) where action is "create", "update", or
    "noop".
    """
    target = staging_dir / hook_name
    existing = target.read_text(encoding="utf-8") if target.exists() else ""

    if existing == template:
        return (False, "noop")

    action = "update" if existing else "create"
    if dry_run:
        return (True, f"{action}-dry")

    try:
        target.write_text(template, encoding="utf-8")
        return (True, action)
    except OSError as e:
        logger.error("write_stub fail=%s target=%s", e, target)
        return (False, "error")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Report changes without writing")
    ap.add_argument("--verbose", action="store_true",
                    help="Log each stub action")
    args = ap.parse_args()

    settings = REPO_ROOT / ".claude" / "settings.json"
    if not settings.is_file():
        logger.error("settings.json not found at %s", settings)
        return 1

    if not TEMPLATE_PATH.is_file():
        logger.error("template not found at %s", TEMPLATE_PATH)
        return 1

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    hooks = extract_hook_filenames(settings)
    staging_dirs = find_staging_hook_dirs(REPO_ROOT)

    if not hooks:
        logger.warning("no hook commands found in settings.json")
        return 0
    if not staging_dirs:
        logger.info("no staging .claude/hooks/ directories found — nothing to sync")
        return 0

    created = updated = noop = errors = 0
    for sd in staging_dirs:
        for hook in sorted(hooks):
            changed, action = write_stub(sd, hook, template, args.dry_run)
            if args.verbose or changed:
                logger.info("stub dir=%s hook=%s action=%s",
                            sd.relative_to(REPO_ROOT), hook, action)
            if action.startswith("create"):
                created += 1
            elif action.startswith("update"):
                updated += 1
            elif action == "noop":
                noop += 1
            elif action == "error":
                errors += 1

    logger.info("DONE created=%d updated=%d noop=%d errors=%d total_hooks=%d total_dirs=%d",
                created, updated, noop, errors, len(hooks), len(staging_dirs))
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
