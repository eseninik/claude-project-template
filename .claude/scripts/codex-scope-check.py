"""
codex-scope-check.py -- Scope fence validator for codex-implement.py diffs.

Given a unified git diff and a scope fence (allowed + forbidden paths),
verify that every modified path is in-fence.

- Allowed paths: each modified file must be under at least one allowed entry
- Forbidden paths: any modified file under a forbidden entry fails
- Paths are normalized via os.path.realpath to prevent `..` traversal escape

Exit codes:
  0 = all modified paths in fence
  2 = at least one violation; stdout lists offending paths

CLI Usage:
    # Inline fence
    py -3 .claude/scripts/codex-scope-check.py \\
        --diff <(git diff HEAD) \\
        --fence "allow:src/,allow:tests/,forbid:src/secrets.py"

    # Fence from file (one entry per line, optional allow:/forbid: prefix)
    py -3 .claude/scripts/codex-scope-check.py --diff diff.patch --fence fence.txt

    # Read diff from stdin
    git diff HEAD | py -3 .claude/scripts/codex-scope-check.py --diff - --fence fence.txt
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import sys
from pathlib import Path
from typing import Iterable


logger = logging.getLogger("codex_scope_check")


_DIFF_HEADER_RE = re.compile(r'^diff --git a/(?P<a>\S+) b/(?P<b>\S+)\s*$')


def _configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def parse_diff_paths(diff_text: str) -> list[str]:
    """Extract modified paths from a unified ``git diff`` text.

    Returns the 'b/' side of each ``diff --git`` header.
    Ignores ``/dev/null`` (new/deleted file placeholder).
    """
    logger.info("parse_diff_paths_started diff_bytes=%d", len(diff_text))
    paths: list[str] = []
    for line in diff_text.splitlines():
        m = _DIFF_HEADER_RE.match(line)
        if not m:
            continue
        b = m.group("b")
        if b == "/dev/null":
            logger.debug("parse_diff_paths_skip_devnull a=%s", m.group("a"))
            continue
        paths.append(b)
    logger.info("parse_diff_paths_completed count=%d", len(paths))
    return paths


def _normalize(root: Path, p: str) -> str:
    """Resolve ``p`` relative to ``root`` into an absolute realpath."""
    abs_path = (root / p).resolve() if not Path(p).is_absolute() else Path(p).resolve()
    return os.path.realpath(str(abs_path))


def _is_under(child: str, parent: str) -> bool:
    """True if ``child`` (realpath) is ``parent`` or nested under ``parent``."""
    if child == parent:
        return True
    sep = os.sep
    prefix = parent if parent.endswith(sep) else parent + sep
    return child.startswith(prefix)


def parse_fence(fence_spec: str, root: Path) -> tuple[list[str], list[str]]:
    """Parse a fence specification into (allowed, forbidden) realpath lists.

    ``fence_spec`` is either:
      * path to a file (one entry per line), or
      * inline comma-separated entries.

    Each entry may be prefixed with ``allow:`` or ``forbid:``.
    Unprefixed entries default to ``allow:``.
    Blank lines and lines starting with ``#`` are skipped.
    """
    logger.info("parse_fence_started fence_spec=%r root=%s", fence_spec, root)
    fence_path = Path(fence_spec)
    raw_entries: list[str]
    if fence_path.is_file():
        raw_entries = fence_path.read_text(encoding="utf-8").splitlines()
        logger.debug("parse_fence_source file=%s lines=%d", fence_path, len(raw_entries))
    else:
        raw_entries = fence_spec.split(",")
        logger.debug("parse_fence_source inline entries=%d", len(raw_entries))

    allowed: list[str] = []
    forbidden: list[str] = []
    for raw in raw_entries:
        entry = raw.strip()
        if not entry or entry.startswith("#"):
            continue
        kind = "allow"
        value = entry
        if entry.startswith("allow:"):
            value = entry[len("allow:"):].strip()
        elif entry.startswith("forbid:"):
            kind = "forbid"
            value = entry[len("forbid:"):].strip()
        if not value:
            logger.warning("parse_fence_empty_entry raw=%r", raw)
            continue
        normalized = _normalize(root, value)
        if kind == "allow":
            allowed.append(normalized)
        else:
            forbidden.append(normalized)

    logger.info(
        "parse_fence_completed allowed=%d forbidden=%d",
        len(allowed),
        len(forbidden),
    )
    return allowed, forbidden


def check_paths(
    paths: Iterable[str],
    allowed: list[str],
    forbidden: list[str],
    root: Path,
) -> list[tuple[str, str]]:
    """Return list of (path, reason) for every violating path.

    A path is OK iff it is under at least one allowed entry AND
    not under any forbidden entry.
    """
    logger.info(
        "check_paths_started allowed=%d forbidden=%d",
        len(allowed),
        len(forbidden),
    )
    violations: list[tuple[str, str]] = []
    for raw_path in paths:
        abs_path = _normalize(root, raw_path)
        logger.debug("check_paths_item raw=%s resolved=%s", raw_path, abs_path)

        forbid_hit = next((f for f in forbidden if _is_under(abs_path, f)), None)
        if forbid_hit is not None:
            violations.append((raw_path, f"forbidden (matches {forbid_hit})"))
            logger.warning("check_paths_forbidden path=%s rule=%s", raw_path, forbid_hit)
            continue

        if not allowed:
            violations.append((raw_path, "no allowed fence entries configured"))
            logger.warning("check_paths_no_allowed path=%s", raw_path)
            continue

        allow_hit = any(_is_under(abs_path, a) for a in allowed)
        if not allow_hit:
            violations.append((raw_path, "outside all allowed entries"))
            logger.warning("check_paths_outside_allowed path=%s", raw_path)

    logger.info("check_paths_completed violations=%d", len(violations))
    return violations


def _read_diff(diff_arg: str) -> str:
    logger.info("read_diff_started source=%s", diff_arg)
    if diff_arg == "-":
        text = sys.stdin.read()
    else:
        p = Path(diff_arg)
        if not p.is_file():
            raise FileNotFoundError(f"Diff source not found: {diff_arg}")
        text = p.read_text(encoding="utf-8", errors="replace")
    logger.info("read_diff_completed bytes=%d", len(text))
    return text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codex-scope-check.py",
        description=(
            "Validate a git diff against a scope fence. "
            "Exit 0 = clean, exit 2 = violation."
        ),
    )
    parser.add_argument(
        "--diff",
        required=True,
        help="Path to unified diff file, or '-' for stdin.",
    )
    parser.add_argument(
        "--fence",
        required=True,
        help=(
            "Fence spec: path to file (one entry per line) or inline "
            "comma-separated entries. Each entry may be prefixed with "
            "'allow:' or 'forbid:'; default is 'allow:'."
        ),
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Project root for resolving relative paths (default: cwd).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose)
    logger.info("main_started diff=%s fence=%s root=%s", args.diff, args.fence, args.root)

    try:
        diff_text = _read_diff(args.diff)
    except FileNotFoundError as exc:
        logger.error("main_diff_missing err=%s", exc)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    root = Path(args.root).resolve()
    paths = parse_diff_paths(diff_text)
    if not paths:
        logger.info("main_empty_diff no_modified_paths")
        print("OK: no modified paths in diff")
        return 0

    allowed, forbidden = parse_fence(args.fence, root)
    violations = check_paths(paths, allowed, forbidden, root)

    if not violations:
        logger.info("main_completed status=pass paths=%d", len(paths))
        print(f"OK: {len(paths)} path(s) in fence")
        return 0

    logger.error("main_completed status=violation count=%d", len(violations))
    print(f"VIOLATION: {len(violations)} path(s) outside fence")
    for path, reason in violations:
        print(f"  {path}\t{reason}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
