"""List Codex helper scripts and their line counts.

Default output is plain text (``name  line_count`` per file plus a ``total:``
summary line). Pass ``--json`` to emit a single JSON document instead with the
shape ``{"scripts": [{"name", "line_count"}], "total_files", "total_lines"}``.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path


LOGGER = logging.getLogger(__name__)
SCRIPT_PATTERN = "codex*.py"


def count_lines(file_path: Path) -> int:
    """Return the number of lines in a text file."""
    with file_path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def get_codex_scripts(script_dir: Path) -> list[Path]:
    """Return matching script files sorted alphabetically by filename."""
    return sorted(
        (path for path in script_dir.glob(SCRIPT_PATTERN) if path.is_file()),
        key=lambda path: path.name,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for the list-codex-scripts utility."""
    parser = argparse.ArgumentParser(
        description="List Codex helper scripts and their line counts.",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Emit a single JSON document instead of plain text.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Print matching script filenames, line counts, and totals."""
    args = parse_args(argv)
    script_dir = Path(__file__).resolve().parent
    LOGGER.info(
        "list_codex_scripts.start",
        extra={
            "script_dir": str(script_dir),
            "pattern": SCRIPT_PATTERN,
            "as_json": args.as_json,
        },
    )

    total_lines = 0
    entries: list[dict[str, object]] = []
    scripts = get_codex_scripts(script_dir)
    for script_path in scripts:
        line_count = count_lines(script_path)
        total_lines += line_count
        LOGGER.info(
            "list_codex_scripts.file_counted",
            extra={"filename": script_path.name, "line_count": line_count},
        )
        entries.append({"name": script_path.name, "line_count": line_count})
        if not args.as_json:
            print(f"{script_path.name}  {line_count}")

    if args.as_json:
        payload = {
            "scripts": entries,
            "total_files": len(entries),
            "total_lines": total_lines,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"total: {len(scripts)} files, {total_lines} lines")

    LOGGER.info(
        "list_codex_scripts.exit",
        extra={
            "file_count": len(scripts),
            "line_count": total_lines,
            "as_json": args.as_json,
        },
    )
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    raise SystemExit(main())
