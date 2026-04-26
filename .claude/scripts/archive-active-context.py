#!/usr/bin/env python3
"""Archive the oldest Round section from activeContext.md when it grows too large."""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from datetime import date
from pathlib import Path
from typing import Sequence


DEFAULT_ACTIVE_CONTEXT = ".claude/memory/activeContext.md"
DEFAULT_ARCHIVE_DIR = ".claude/memory/archive"
DEFAULT_LINE_LIMIT = 200
ROUND_HEADING_RE = re.compile(r"^(#{2,3})\s+Round\s+(\d+)\b", re.IGNORECASE)
HEADING_RE = re.compile(r"^(#{1,6})\s+")

logger = logging.getLogger("archive_active_context")


class JsonFormatter(logging.Formatter):
    """Small JSON formatter consistent with other local maintenance scripts."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        context = getattr(record, "context", None)
        if context:
            payload.update(context)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, sort_keys=True)


def configure_logging(verbose: bool) -> None:
    """Configure stderr logging."""
    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse CLI options."""
    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
    parser = argparse.ArgumentParser(description="Archive the oldest activeContext.md Round section if over the line limit.")
    parser.add_argument("--active-context", default=DEFAULT_ACTIVE_CONTEXT, help="Path to activeContext.md.")
    parser.add_argument("--archive-dir", default=DEFAULT_ARCHIVE_DIR, help="Directory for archived Round sections.")
    parser.add_argument("--line-limit", type=int, default=DEFAULT_LINE_LIMIT, help="Maximum active context lines before archiving.")
    parser.add_argument("--dry-run", action="store_true", help="Preview the archive action without writing files.")
    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG JSON logs on stderr.")
    args = parser.parse_args(list(argv))
    if args.line_limit < 1:
        parser.error("--line-limit must be positive")
    logger.debug("exit", extra={"context": {"function": "parse_args", "dry_run": args.dry_run}})
    return args


def _line_count(content: str) -> int:
    """Count lines in a way that matches activeContext.md curation checks."""
    logger.debug("entry", extra={"context": {"function": "_line_count", "chars": len(content)}})
    count = len(content.splitlines())
    logger.debug("exit", extra={"context": {"function": "_line_count", "lines": count}})
    return count


def _extract_oldest_round(content: str) -> tuple[str, str]:
    """Return the lowest-numbered Round section and the content with that section removed."""
    logger.debug("entry", extra={"context": {"function": "_extract_oldest_round", "chars": len(content)}})
    lines = content.splitlines(keepends=True)
    candidates: list[tuple[int, int, int]] = []
    for index, line in enumerate(lines):
        match = ROUND_HEADING_RE.match(line)
        if match:
            candidates.append((int(match.group(2)), len(match.group(1)), index))

    if not candidates:
        logger.debug("exit", extra={"context": {"function": "_extract_oldest_round", "found": False}})
        return "", content

    round_number, heading_level, start = min(candidates, key=lambda item: (item[0], item[2]))
    end = len(lines)
    for index in range(start + 1, len(lines)):
        heading_match = HEADING_RE.match(lines[index])
        round_match = ROUND_HEADING_RE.match(lines[index])
        if heading_match and len(heading_match.group(1)) < heading_level:
            end = index
            break
        if heading_level == 2 and heading_match and len(heading_match.group(1)) == 2:
            end = index
            break
        if heading_level == 3 and round_match and len(round_match.group(1)) == 3:
            end = index
            break

    archived = "".join(lines[start:end]).strip("\n") + "\n"
    remaining = "".join(lines[:start] + lines[end:])
    logger.debug(
        "exit",
        extra={
            "context": {
                "function": "_extract_oldest_round",
                "found": True,
                "round": round_number,
                "archived_lines": _line_count(archived),
            }
        },
    )
    return archived, remaining


def _round_slug(section: str) -> str:
    """Return the roundX slug for an archived section."""
    logger.debug("entry", extra={"context": {"function": "_round_slug"}})
    first_line = section.splitlines()[0] if section.splitlines() else ""
    match = ROUND_HEADING_RE.match(first_line)
    if not match:
        logger.debug("exit", extra={"context": {"function": "_round_slug", "slug": "round-unknown"}})
        return "round-unknown"
    slug = "round" + match.group(2)
    logger.debug("exit", extra={"context": {"function": "_round_slug", "slug": slug}})
    return slug


def _archive_path(archive_dir: Path, section: str, today_value: date) -> Path:
    """Compute an archive path for the section."""
    logger.debug("entry", extra={"context": {"function": "_archive_path", "archive_dir": str(archive_dir)}})
    path = archive_dir / ("active-" + today_value.isoformat() + "-" + _round_slug(section) + ".md")
    logger.debug("exit", extra={"context": {"function": "_archive_path", "path": str(path)}})
    return path


def _resolve_archive_path(path: Path, section: str) -> Path:
    """Avoid clobbering a different archive with the same date and round."""
    logger.debug("entry", extra={"context": {"function": "_resolve_archive_path", "path": str(path)}})
    if not path.exists():
        logger.debug("exit", extra={"context": {"function": "_resolve_archive_path", "path": str(path)}})
        return path
    try:
        if path.read_text(encoding="utf-8") == section:
            logger.debug("exit", extra={"context": {"function": "_resolve_archive_path", "path": str(path), "identical": True}})
            return path
    except OSError:
        logger.exception("archive_read_failed", extra={"context": {"function": "_resolve_archive_path", "path": str(path)}})
        raise

    for suffix in range(2, 1000):
        candidate = path.with_name(path.stem + "-" + str(suffix) + path.suffix)
        if not candidate.exists():
            logger.debug("exit", extra={"context": {"function": "_resolve_archive_path", "path": str(candidate)}})
            return candidate
    raise RuntimeError("could not allocate unique archive path for " + str(path))


def archive_active_context(active_context: Path, archive_dir: Path, line_limit: int, dry_run: bool, today_value: date | None = None) -> tuple[int, str]:
    """Archive one oldest Round section if activeContext.md exceeds line_limit."""
    logger.debug(
        "entry",
        extra={
            "context": {
                "function": "archive_active_context",
                "active_context": str(active_context),
                "archive_dir": str(archive_dir),
                "line_limit": line_limit,
                "dry_run": dry_run,
            }
        },
    )
    today_value = today_value or date.today()
    if not active_context.exists():
        message = "no archive needed: activeContext.md missing"
        logger.info("missing_active_context", extra={"context": {"function": "archive_active_context", "path": str(active_context)}})
        logger.debug("exit", extra={"context": {"function": "archive_active_context", "returncode": 0}})
        return 0, message

    content = active_context.read_text(encoding="utf-8")
    if _line_count(content) <= line_limit:
        message = "no archive needed"
        logger.debug("exit", extra={"context": {"function": "archive_active_context", "returncode": 0, "action": "noop"}})
        return 0, message

    archived_section, remaining_content = _extract_oldest_round(content)
    if not archived_section:
        message = "no archive needed: no Round section found"
        logger.warning("no_round_section", extra={"context": {"function": "archive_active_context", "path": str(active_context)}})
        logger.debug("exit", extra={"context": {"function": "archive_active_context", "returncode": 0, "action": "noop"}})
        return 0, message

    archived_lines = _line_count(archived_section)
    archive_path = _archive_path(archive_dir, archived_section, today_value)
    if dry_run:
        message = "would archive: " + str(archived_lines) + " lines -> " + str(archive_path)
        logger.debug("exit", extra={"context": {"function": "archive_active_context", "returncode": 0, "action": "dry_run"}})
        return 0, message

    archive_dir.mkdir(parents=True, exist_ok=True)
    final_path = _resolve_archive_path(archive_path, archived_section)
    final_path.write_text(archived_section, encoding="utf-8")
    active_context.write_text(remaining_content, encoding="utf-8")
    message = "archived: " + str(archived_lines) + " lines -> " + str(final_path)
    logger.info(
        "archived_active_context",
        extra={"context": {"function": "archive_active_context", "lines": archived_lines, "path": str(final_path)}},
    )
    logger.debug("exit", extra={"context": {"function": "archive_active_context", "returncode": 0, "action": "archived"}})
    return 0, message


def run(args: argparse.Namespace, today_value: date | None = None) -> int:
    """Run the archive command and print the user-facing result."""
    logger.debug("entry", extra={"context": {"function": "run", "dry_run": args.dry_run}})
    try:
        code, message = archive_active_context(
            Path(args.active_context),
            Path(args.archive_dir),
            args.line_limit,
            args.dry_run,
            today_value=today_value,
        )
        print(message)
        logger.debug("exit", extra={"context": {"function": "run", "returncode": code}})
        return code
    except (OSError, RuntimeError) as exc:
        logger.exception("archive_active_context_failed", extra={"context": {"function": "run"}})
        print("error: " + str(exc), file=sys.stderr)
        logger.debug("exit", extra={"context": {"function": "run", "returncode": 2}})
        return 2


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)
    configure_logging(args.verbose)
    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
    code = run(args)
    logger.debug("exit", extra={"context": {"function": "main", "returncode": code}})
    return code


if __name__ == "__main__":
    raise SystemExit(main())
