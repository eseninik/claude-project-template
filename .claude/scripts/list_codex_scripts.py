#!/usr/bin/env python3
"""List `.claude/scripts/codex*.py` files with alphabetical line counts."""

from __future__ import annotations

import logging
from pathlib import Path


logger = logging.getLogger("list_codex_scripts")


def count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def collect_entries(scripts_dir: Path) -> list[tuple[str, int]]:
    return sorted(
        (path.name, count_lines(path))
        for path in scripts_dir.glob("codex*.py")
        if path.is_file()
    )


def main() -> int:
    scripts_dir = Path(__file__).resolve().parent
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    logger.info("event=main_start scripts_dir=%s", scripts_dir)
    entries = collect_entries(scripts_dir)
    total_lines = sum(line_count for _, line_count in entries)
    for name, line_count in entries:
        print(f"{name}  {line_count}")
    print(f"total: {len(entries)} files, {total_lines} lines")
    logger.info("event=main_end file_count=%d line_count=%d", len(entries), total_lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
