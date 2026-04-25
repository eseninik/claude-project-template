#!/usr/bin/env python3
"""Audit knowledge.md entries by verification age tier."""
import argparse
import json
import logging
import re
import sys
from datetime import date
from pathlib import Path


TIERS = ("active", "warm", "cold", "archive", "unparsed")
DEFAULT_THRESHOLDS = (14, 30, 90)
ENTRY_RE = re.compile(r"^###\s+(.+?)\s+\((\d{4}-\d{2}-\d{2}),\s*verified:\s*(\d{4}-\d{2}-\d{2})\)\s*$")
HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")


class JsonFormatter(logging.Formatter):
    def format(self, record):
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


logger = logging.getLogger("knowledge_decay_report")


def configure_logging(verbose):
    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if verbose else logging.WARNING)
    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})


def parse_args(argv):
    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
    parser = argparse.ArgumentParser(description="Audit .claude/memory/knowledge.md verification decay tiers.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--knowledge-path", default=".claude/memory/knowledge.md", help="Path to knowledge.md.")
    parser.add_argument("--today", help="Override today's date as YYYY-MM-DD.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--include-gotchas", action="store_true", help="Include Gotchas section entries (default).")
    group.add_argument("--patterns-only", action="store_true", help="Only include Patterns section entries.")
    parser.add_argument("--threshold-days", default="14,30,90", help="Comma-separated active,warm,cold day cutoffs.")
    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG structured logs on stderr.")
    args = parser.parse_args(argv)
    logger.debug("exit", extra={"context": {"function": "parse_args", "json": args.json}})
    return args


def parse_thresholds(value):
    logger.debug("entry", extra={"context": {"function": "parse_thresholds", "value": value}})
    try:
        parts = tuple(int(part.strip()) for part in value.split(","))
        if len(parts) != 3 or parts[0] < 0 or not (parts[0] < parts[1] < parts[2]):
            raise ValueError("thresholds must be three increasing non-negative integers")
        logger.debug("exit", extra={"context": {"function": "parse_thresholds", "thresholds": parts}})
        return parts
    except ValueError:
        logger.exception("invalid_thresholds", extra={"context": {"function": "parse_thresholds", "value": value}})
        raise


def parse_today(value):
    logger.debug("entry", extra={"context": {"function": "parse_today", "provided": bool(value)}})
    try:
        result = date.fromisoformat(value) if value else date.today()
        logger.debug("exit", extra={"context": {"function": "parse_today", "today": result.isoformat()}})
        return result
    except ValueError:
        logger.exception("invalid_today", extra={"context": {"function": "parse_today", "value": value}})
        raise


def classify_age(age_days, thresholds):
    logger.debug("entry", extra={"context": {"function": "classify_age", "age_days": age_days}})
    active, warm, cold = thresholds
    if age_days <= active:
        tier = "active"
    elif age_days <= warm:
        tier = "warm"
    elif age_days <= cold:
        tier = "cold"
    else:
        tier = "archive"
    logger.debug("exit", extra={"context": {"function": "classify_age", "tier": tier}})
    return tier


def blank_report(today_value):
    logger.debug("entry", extra={"context": {"function": "blank_report", "today": today_value.isoformat()}})
    result = {
        "generated_at": date.today().isoformat(),
        "today": today_value.isoformat(),
        "tiers": {tier: [] for tier in TIERS},
        "summary": {tier: 0 for tier in TIERS},
        "promotion_candidates": [],
    }
    result["summary"]["total"] = 0
    logger.debug("exit", extra={"context": {"function": "blank_report"}})
    return result


def extract_name(line):
    logger.debug("entry", extra={"context": {"function": "extract_name"}})
    text = line[4:].strip()
    name = text.split(" (", 1)[0].strip() or text[:80]
    logger.debug("exit", extra={"context": {"function": "extract_name", "name": name}})
    return name


def parse_entry_line(line, line_no, today_value, thresholds):
    logger.debug("entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
    match = ENTRY_RE.match(line)
    if not match:
        entry = {
            "name": extract_name(line),
            "verified": None,
            "created": None,
            "age_days": None,
            "tier": "unparsed",
            "line_no": line_no,
        }
        logger.warning("unparsed_entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
        return entry
    try:
        name, created_text, verified_text = match.groups()
        created = date.fromisoformat(created_text)
        verified = date.fromisoformat(verified_text)
        age_days = (today_value - verified).days
        tier = classify_age(age_days, thresholds)
        entry = {
            "name": name,
            "verified": verified.isoformat(),
            "created": created.isoformat(),
            "age_days": age_days,
            "tier": tier,
            "line_no": line_no,
        }
        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": tier}})
        return entry
    except ValueError:
        logger.exception("malformed_entry_dates", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
        entry = {
            "name": extract_name(line),
            "verified": None,
            "created": None,
            "age_days": None,
            "tier": "unparsed",
            "line_no": line_no,
        }
        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
        return entry


def iter_relevant_lines(text, include_gotchas):
    logger.debug("entry", extra={"context": {"function": "iter_relevant_lines", "include_gotchas": include_gotchas}})
    section = None
    for line_no, line in enumerate(text.splitlines(), start=1):
        heading = HEADING_RE.match(line)
        if heading:
            title = heading.group(1).strip().lower()
            section = title if title in {"patterns", "gotchas"} else None
            continue
        if line.startswith("### ") and section == "patterns":
            yield line_no, line
        elif line.startswith("### ") and section == "gotchas" and include_gotchas:
            yield line_no, line
    logger.debug("exit", extra={"context": {"function": "iter_relevant_lines"}})


def detect_promotion_candidates(report, knowledge_path):
    logger.debug("entry", extra={"context": {"function": "detect_promotion_candidates", "path": str(knowledge_path)}})
    try:
        active_path = knowledge_path.parent / "activeContext.md"
        if not active_path.exists():
            logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": 0}})
            return []
        active_text = active_path.read_text(encoding="utf-8", errors="replace").lower()
        candidates = []
        for tier in ("warm", "cold", "archive"):
            for entry in report["tiers"][tier]:
                if entry["name"].lower() in active_text:
                    candidates.append(entry)
        logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": len(candidates)}})
        return candidates
    except OSError:
        logger.exception("active_context_read_failed", extra={"context": {"function": "detect_promotion_candidates"}})
        return []


def make_report(knowledge_path, today_value, include_gotchas, thresholds):
    logger.debug("entry", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
    report = blank_report(today_value)
    try:
        text = Path(knowledge_path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        logger.exception("knowledge_read_failed", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
        raise
    for line_no, line in iter_relevant_lines(text, include_gotchas):
        entry = parse_entry_line(line, line_no, today_value, thresholds)
        report["tiers"][entry["tier"]].append(entry)
    for tier in TIERS:
        report["summary"][tier] = len(report["tiers"][tier])
    report["summary"]["total"] = sum(report["summary"][tier] for tier in TIERS)
    report["promotion_candidates"] = detect_promotion_candidates(report, Path(knowledge_path))
    logger.debug("exit", extra={"context": {"function": "make_report", "total": report["summary"]["total"]}})
    return report


def format_entry(entry):
    logger.debug("entry", extra={"context": {"function": "format_entry", "tier": entry["tier"]}})
    if entry["tier"] == "unparsed":
        text = f"* {entry['name']} (line={entry['line_no']})"
    else:
        text = f"* {entry['name']} ({entry['verified']}, age={entry['age_days']}d)"
    result = text[:80]
    logger.debug("exit", extra={"context": {"function": "format_entry", "length": len(result)}})
    return result


def format_text_report(report):
    logger.debug("entry", extra={"context": {"function": "format_text_report", "total": report["summary"]["total"]}})
    lines = [
        "Tier    | Count | Entries (truncated to first 80 chars)",
        "--------+-------+-----------------------------------------",
    ]
    for tier in TIERS:
        entries = report["tiers"][tier]
        first = format_entry(entries[0]) if entries else ""
        lines.append(f"{tier:<8}| {len(entries):^5} | {first}")
        for entry in entries[1:]:
            lines.append(f"{'':8}  {'':5}   {format_entry(entry)}")
    lines.append(f"Total   | {report['summary']['total']:^5} |")
    lines.extend(["", "## Age histogram"])
    for tier in TIERS:
        lines.append(f"{tier}: {report['summary'][tier]}")
    candidates = report["promotion_candidates"]
    lines.extend(["", f"## Promotion candidates ({len(candidates)}):"])
    for entry in candidates:
        lines.append(format_entry(entry))
    result = "\n".join(lines)
    logger.debug("exit", extra={"context": {"function": "format_text_report", "length": len(result)}})
    return result


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)
    configure_logging(args.verbose)
    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
    try:
        today_value = parse_today(args.today)
        thresholds = parse_thresholds(args.threshold_days)
        data = make_report(Path(args.knowledge_path), today_value, not args.patterns_only, thresholds)
        if args.json:
            json_data = {key: data[key] for key in ("generated_at", "today", "tiers", "summary")}
            print(json.dumps(json_data, indent=2, sort_keys=True))
        else:
            print(format_text_report(data))
        logger.debug("exit", extra={"context": {"function": "main", "returncode": 0}})
        return 0
    except (OSError, ValueError) as exc:
        logger.exception("fatal_error", extra={"context": {"function": "main"}})
        print(f"error: {exc}", file=sys.stderr)
        logger.debug("exit", extra={"context": {"function": "main", "returncode": 2}})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
