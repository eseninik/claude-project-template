#!/usr/bin/env python3
"""Archive stale dual-implement result.md and matching .diff files into dated history.

Stand-alone CLI: scans work/codex-implementations for task-prefix result.md
files older than the max-age-days flag and moves them into dual-history.

Default mode is dry-run (read-only). The apply flag is the only mutating mode.
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, List, Optional


DEFAULT_SOURCE = "work/codex-implementations"
DEFAULT_DEST = "work/codex-primary/dual-history"
DEFAULT_MAX_AGE_DAYS = 7


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        for key, value in getattr(record, "context", {}).items():
            payload[key] = value
        return json.dumps(payload, sort_keys=True)


logger = logging.getLogger("dual_history_archive")


def configure_logging(verbose: bool) -> None:
    """Wire stderr JSON logging at DEBUG (verbose) or INFO level."""
    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})


def parse_args(argv: List[str]) -> argparse.Namespace:
    """Parse CLI flags. Default mode is dry-run; apply flag toggles mutation."""
    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
    parser = argparse.ArgumentParser(
        description="Archive stale dual-implement result.md (and matching .diff) into dated history.",
    )
    parser.add_argument("--source", default=DEFAULT_SOURCE, help="Source directory to scan (default: %(default)s).")
    parser.add_argument("--dest", default=DEFAULT_DEST, help="Destination archive root (default: %(default)s).")
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=DEFAULT_MAX_AGE_DAYS,
        help="Files older than this many days are stale (default: %(default)s).",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Preview only (default behaviour).")
    mode.add_argument("--apply", action="store_true", help="Actually move stale files. The only mutating mode.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG structured logs on stderr.")
    args = parser.parse_args(argv)
    if args.max_age_days < 0:
        parser.error("--max-age-days must be non-negative")
    logger.debug("exit", extra={"context": {"function": "parse_args", "apply": args.apply, "json": args.json}})
    return args


def discover_results(source: Path) -> List[Path]:
    """Return sorted task-prefix result.md paths in source (non-recursive)."""
    logger.debug("entry", extra={"context": {"function": "discover_results", "source": str(source)}})
    if not source.exists():
        logger.warning("source_missing", extra={"context": {"function": "discover_results", "source": str(source)}})
        logger.debug("exit", extra={"context": {"function": "discover_results", "count": 0}})
        return []
    results = sorted(p for p in source.glob("task-*-result.md") if p.is_file())
    logger.debug("exit", extra={"context": {"function": "discover_results", "count": len(results)}})
    return results


def matching_diff(result_path: Path) -> Optional[Path]:
    """Return the task-X.diff sibling for task-X-result.md if it exists."""
    logger.debug("entry", extra={"context": {"function": "matching_diff", "path": str(result_path)}})
    name = result_path.name
    suffix = "-result.md"
    if not name.endswith(suffix):
        logger.debug("exit", extra={"context": {"function": "matching_diff", "found": False}})
        return None
    stem = name[: -len(suffix)]
    candidate = result_path.with_name(stem + ".diff")
    found = candidate if candidate.is_file() else None
    logger.debug("exit", extra={"context": {"function": "matching_diff", "found": found is not None}})
    return found


def compute_age_days(path: Path, today_value: date) -> int:
    """Return integer age in days from file mtime to today_value."""
    logger.debug("entry", extra={"context": {"function": "compute_age_days", "path": str(path)}})
    mtime = path.stat().st_mtime
    mtime_date = datetime.fromtimestamp(mtime).date()
    age = (today_value - mtime_date).days
    logger.debug("exit", extra={"context": {"function": "compute_age_days", "age_days": age}})
    return age


def dest_subdir_for(path: Path, dest_root: Path) -> Path:
    """Compute dest_root/YYYY-MM from path mtime."""
    logger.debug("entry", extra={"context": {"function": "dest_subdir_for", "path": str(path)}})
    mtime = path.stat().st_mtime
    mtime_dt = datetime.fromtimestamp(mtime)
    sub = "%04d-%02d" % (mtime_dt.year, mtime_dt.month)
    out = dest_root / sub
    logger.debug("exit", extra={"context": {"function": "dest_subdir_for", "subdir": str(out)}})
    return out


def build_entry(result_path: Path, dest_root: Path, today_value: date, max_age_days: int) -> dict:
    """Build a JSON-serialisable entry describing a candidate file pair."""
    logger.debug("entry", extra={"context": {"function": "build_entry", "path": str(result_path)}})
    age_days = compute_age_days(result_path, today_value)
    is_stale = age_days > max_age_days
    sub = dest_subdir_for(result_path, dest_root)
    diff = matching_diff(result_path)
    entry = {
        "path": str(result_path),
        "diff_path": str(diff) if diff is not None else None,
        "age_days": age_days,
        "stale": is_stale,
        "dest_path": str(sub / result_path.name),
        "dest_diff_path": str(sub / diff.name) if diff is not None else None,
        "apply_status": "skipped",
        "error": None,
    }
    logger.debug("exit", extra={"context": {"function": "build_entry", "stale": is_stale, "age_days": age_days}})
    return entry


def move_pair(entry: dict) -> None:
    """Move result.md (and optional .diff) atomically per task. Mutates entry."""
    logger.debug("entry", extra={"context": {"function": "move_pair", "path": entry["path"]}})
    try:
        dest_path = Path(entry["dest_path"])
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("move_result", extra={"context": {"function": "move_pair", "src": entry["path"], "dst": entry["dest_path"]}})
        shutil.move(entry["path"], str(dest_path))
        if entry.get("diff_path") and entry.get("dest_diff_path"):
            logger.info("move_diff", extra={"context": {"function": "move_pair", "src": entry["diff_path"], "dst": entry["dest_diff_path"]}})
            shutil.move(entry["diff_path"], entry["dest_diff_path"])
        entry["apply_status"] = "moved"
    except OSError as exc:
        entry["apply_status"] = "error"
        entry["error"] = str(exc)
        logger.exception("move_failed", extra={"context": {"function": "move_pair", "path": entry["path"]}})
    logger.debug("exit", extra={"context": {"function": "move_pair", "status": entry["apply_status"]}})


def collect_entries(source: Path, dest: Path, max_age_days: int, today_value: date) -> List[dict]:
    """Discover and classify every candidate result.md in source."""
    logger.debug("entry", extra={"context": {"function": "collect_entries", "source": str(source)}})
    entries = [build_entry(p, dest, today_value, max_age_days) for p in discover_results(source)]
    logger.debug("exit", extra={"context": {"function": "collect_entries", "count": len(entries)}})
    return entries


def summarise(entries: Iterable[dict], source: Path, dest: Path, max_age_days: int) -> dict:
    """Produce the JSON summary block (AC5)."""
    logger.debug("entry", extra={"context": {"function": "summarise"}})
    items = list(entries)
    stale_items = [e for e in items if e["stale"]]
    payload = {
        "source": str(source),
        "dest": str(dest),
        "window_days": max_age_days,
        "found": len(items),
        "stale": len(stale_items),
        "kept": len(items) - len(stale_items),
        "entries": [{"path": e["path"], "age_days": e["age_days"], "dest_path": e["dest_path"], "apply_status": e["apply_status"]} for e in stale_items],
    }
    logger.debug("exit", extra={"context": {"function": "summarise", "stale": payload["stale"]}})
    return payload


def format_text(entries: List[dict], source: Path, dest: Path, max_age_days: int, applied: bool) -> str:
    """Render the human-readable preview/result text (AC4)."""
    logger.debug("entry", extra={"context": {"function": "format_text", "applied": applied}})
    stale = [e for e in entries if e["stale"]]
    lines = [
        "Source : " + str(source),
        "Dest   : " + str(dest),
        "Window : > " + str(max_age_days) + " day(s) old",
        "Found  : " + str(len(entries)) + " result.md file(s)",
        "Stale  : " + str(len(stale)),
        "Kept   : " + str(len(entries) - len(stale)),
        "",
    ]
    if stale:
        lines.append("Stale entries:")
        for entry in stale:
            diff_marker = " (+diff)" if entry.get("diff_path") else ""
            status = entry["apply_status"]
            lines.append("  * " + entry["path"] + diff_marker + "  age=" + str(entry["age_days"]) + "d  -> " + entry["dest_path"] + "  [" + status + "]")
            if entry.get("error"):
                lines.append("      error: " + entry["error"])
    else:
        lines.append("No stale entries found.")
    lines.append("")
    if applied:
        moved = sum(1 for e in stale if e["apply_status"] == "moved")
        errors = sum(1 for e in stale if e["apply_status"] == "error")
        lines.append("Applied. Moved " + str(moved) + ", errors " + str(errors) + ".")
    else:
        lines.append("Run with --apply to move. Skipping (dry-run).")
    text = "\n".join(lines)
    logger.debug("exit", extra={"context": {"function": "format_text", "length": len(text)}})
    return text


def run(args: argparse.Namespace, today_value: Optional[date] = None) -> int:
    """Pure-logic entry point. Returns exit code."""
    logger.debug("entry", extra={"context": {"function": "run", "apply": args.apply}})
    today_value = today_value or date.today()
    source = Path(args.source)
    dest = Path(args.dest)
    entries = collect_entries(source, dest, args.max_age_days, today_value)
    stale = [e for e in entries if e["stale"]]
    failures = 0
    if args.apply:
        for entry in stale:
            move_pair(entry)
            if entry["apply_status"] == "error":
                failures += 1
    if args.json:
        print(json.dumps(summarise(entries, source, dest, args.max_age_days), indent=2, sort_keys=True))
    else:
        print(format_text(entries, source, dest, args.max_age_days, applied=args.apply))
    code = 1 if failures else 0
    logger.debug("exit", extra={"context": {"function": "run", "returncode": code, "failures": failures}})
    return code


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point."""
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)
    configure_logging(args.verbose)
    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
    try:
        code = run(args)
        logger.debug("exit", extra={"context": {"function": "main", "returncode": code}})
        return code
    except (OSError, ValueError) as exc:
        logger.exception("fatal_error", extra={"context": {"function": "main"}})
        print("error: " + str(exc), file=sys.stderr)
        logger.debug("exit", extra={"context": {"function": "main", "returncode": 2}})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
