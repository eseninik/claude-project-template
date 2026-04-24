"""List Codex helper scripts and their line counts."""

from __future__ import annotations

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


def main() -> int:
    """Print matching script filenames, line counts, and totals."""
    script_dir = Path(__file__).resolve().parent
    LOGGER.info(
        "list_codex_scripts.start",
        extra={"script_dir": str(script_dir), "pattern": SCRIPT_PATTERN},
    )

    total_lines = 0
    scripts = get_codex_scripts(script_dir)
    for script_path in scripts:
        line_count = count_lines(script_path)
        total_lines += line_count
        LOGGER.info(
            "list_codex_scripts.file_counted",
            extra={"filename": script_path.name, "line_count": line_count},
        )
        print(f"{script_path.name}  {line_count}")

    print(f"total: {len(scripts)} files, {total_lines} lines")
    LOGGER.info(
        "list_codex_scripts.exit",
        extra={"file_count": len(scripts), "line_count": total_lines},
    )
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    raise SystemExit(main())
