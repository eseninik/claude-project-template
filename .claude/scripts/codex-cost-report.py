#!/usr/bin/env python3
"""codex-cost-report.py - duration / token report from codex-implement logs.

Scans .claude/logs/codex-implement-*.log and codex-fix-*.log (JSON-per-line)
and reports per-run durations / sizes. A run = entry: main .. exit: main.
Stdlib only. Windows-compatible (pathlib).
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("codex_cost_report")


def _log(level, msg, **fields):
    """Emit structured log record."""
    suffix = (" " + " ".join(f"{k}={v}" for k, v in fields.items())) if fields else ""
    logger.log(level, "%s%s", msg, suffix)


def setup_logging(verbose):
    """Configure stderr logging - DEBUG with --verbose, else INFO."""
    _log(logging.DEBUG, "entry: setup_logging", verbose=verbose)
    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)
    logger.handlers.clear()
    h = logging.StreamHandler(sys.stderr)
    h.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    h.setLevel(level)
    logger.addHandler(h)
    _log(logging.DEBUG, "exit: setup_logging")


@dataclass
class RunRecord:
    """Per-run aggregate (AC4)."""
    task_id: str = ""
    log_file: str = ""
    start_ts: Optional[str] = None
    end_ts: Optional[str] = None
    duration_s: float = 0.0
    status: str = "incomplete"
    returncode: Optional[int] = None
    stdout_len: int = 0
    stderr_len: int = 0
    model: Optional[str] = None
    reasoning: Optional[str] = None


def parse_ts(ts):
    """Parse ISO-8601 ts (naive or tz-aware). Returns None on failure."""
    _log(logging.DEBUG, "entry: parse_ts", ts=ts)
    if not ts:
        return None
    try:
        s = ts.rstrip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        _log(logging.DEBUG, "exit: parse_ts", parsed=dt.isoformat())
        return dt
    except Exception:
        logger.warning("parse_ts failed: ts=%r", ts)
        return None


_TASK_FROM_LOG_RE = re.compile(r"codex-(?:implement|fix)-T?([\w\-]+)\.log$", re.IGNORECASE)


def task_id_from_argv(argv, fallback):
    """Extract task id from logged argv (--task <path>); else fallback."""
    _log(logging.DEBUG, "entry: task_id_from_argv", fallback=fallback)
    try:
        if isinstance(argv, list):
            for i, tok in enumerate(argv):
                if tok in ("--task", "-t") and i + 1 < len(argv):
                    stem = Path(str(argv[i + 1])).stem
                    m = re.match(r"^T(\d+[\w\-]*)", stem, re.IGNORECASE)
                    if m:
                        return m.group(1)
                    m = re.match(r"^task-(.+)$", stem, re.IGNORECASE)
                    return m.group(1) if m else stem
        return fallback
    except Exception:
        logger.exception("task_id_from_argv failed")
        return fallback


def task_id_from_log_path(log_path):
    """Derive fallback task id from log filename pattern."""
    _log(logging.DEBUG, "entry: task_id_from_log_path", path=str(log_path))
    m = _TASK_FROM_LOG_RE.search(log_path.name)
    return m.group(1) if m else log_path.stem


def parse_log_file(log_path):
    """Parse one log file -> list of RunRecord (AC2/AC3/AC4). Never raises."""
    _log(logging.INFO, "entry: parse_log_file", path=str(log_path))
    runs = []
    current = None
    fallback_task = task_id_from_log_path(log_path)
    try:
        with log_path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
            for lineno, raw in enumerate(fh, start=1):
                line = raw.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    logger.warning("skipping malformed JSON: file=%s line=%d", log_path.name, lineno)
                    continue
                msg = rec.get("msg", "")
                ts = rec.get("ts", "")
                if msg == "entry: main":
                    if current is not None:
                        runs.append(current)
                    current = RunRecord(
                        task_id=task_id_from_argv(rec.get("argv"), fallback_task),
                        log_file=str(log_path),
                        start_ts=ts or None,
                    )
                    continue
                if current is None:
                    current = RunRecord(task_id=fallback_task, log_file=str(log_path))
                if msg == "entry: run_codex":
                    current.model = rec.get("model") or current.model
                    current.reasoning = rec.get("reasoning") or current.reasoning
                elif msg == "exit: run_codex":
                    rc = rec.get("returncode")
                    if isinstance(rc, int):
                        current.returncode = rc
                    sl = rec.get("stdout_len")
                    if isinstance(sl, int):
                        current.stdout_len = sl
                    el = rec.get("stderr_len")
                    if isinstance(el, int):
                        current.stderr_len = el
                elif msg == "exit: main" or msg.startswith("exit: main"):
                    current.end_ts = ts or current.end_ts
                    status = rec.get("status")
                    if isinstance(status, str) and status:
                        current.status = status
                    elif "(degraded)" in msg:
                        current.status = "degraded"
                    runs.append(current)
                    current = None
        if current is not None:
            runs.append(current)
        for run in runs:
            sd = parse_ts(run.start_ts)
            ed = parse_ts(run.end_ts)
            if sd and ed:
                run.duration_s = max(0.0, (ed - sd).total_seconds())
        _log(logging.INFO, "exit: parse_log_file", path=str(log_path), runs=len(runs))
        return runs
    except FileNotFoundError:
        logger.warning("log file disappeared: %s", log_path)
        return []
    except Exception:
        logger.exception("parse_log_file failed: %s", log_path)
        return []


def collect_runs(log_dir, since_hours):
    """Scan log_dir, parse logs, apply since_hours filter, sort (AC8)."""
    _log(logging.INFO, "entry: collect_runs", log_dir=str(log_dir), since_hours=since_hours)
    if not log_dir.exists():
        logger.warning("log dir does not exist: %s", log_dir)
        return []
    files = []
    for pat in ("codex-implement-*.log", "codex-fix-*.log"):
        files.extend(sorted(log_dir.glob(pat)))
    all_runs = []
    for f in files:
        all_runs.extend(parse_log_file(f))
    if since_hours is not None and since_hours > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        kept = []
        for run in all_runs:
            sd = parse_ts(run.start_ts)
            if sd is None:
                kept.append(run)
                continue
            if sd.tzinfo is None:
                sd = sd.replace(tzinfo=timezone.utc)
            if sd >= cutoff:
                kept.append(run)
        all_runs = kept
    all_runs.sort(key=lambda r: (r.start_ts or "", r.task_id or ""))
    _log(logging.INFO, "exit: collect_runs", count=len(all_runs))
    return all_runs


def summarise(runs):
    """Aggregate counts/totals across runs."""
    _log(logging.DEBUG, "entry: summarise", runs=len(runs))
    out = {
        "runs": len(runs),
        "pass": sum(1 for r in runs if r.status == "pass"),
        "fail": sum(1 for r in runs if r.status == "fail"),
        "total_duration_s": round(sum(r.duration_s for r in runs), 3),
    }
    _log(logging.DEBUG, "exit: summarise", **out)
    return out


def render_markdown(runs, summary, log_dir, window_hours, generated_at):
    """Markdown report (AC5/AC7)."""
    _log(logging.DEBUG, "entry: render_markdown", runs=len(runs))
    lines = ["# Codex Cost Report", ""]
    lines.append(f"- generated_at: {generated_at}")
    lines.append(f"- log_dir: {log_dir}")
    lines.append(f"- window: {'all' if window_hours is None else f'last {window_hours}h'}")
    lines.append(f"- runs: {summary['runs']} (pass={summary['pass']}, fail={summary['fail']})")
    lines.append(f"- total_duration_s: {summary['total_duration_s']}")
    lines.append("")
    if not runs:
        lines.append("_No codex-implement runs found in the requested window._")
        lines.append("")
        return "\n".join(lines)
    lines.append("| Task | Status | Duration (s) | Reasoning | Model | Stdout | Stderr |")
    lines.append("|------|--------|--------------|-----------|-------|--------|--------|")
    for r in runs:
        lines.append("| {0} | {1} | {2} | {3} | {4} | {5} | {6} |".format(
            r.task_id or "-", r.status, f"{r.duration_s:.2f}",
            r.reasoning or "-", r.model or "-", r.stdout_len, r.stderr_len,
        ))
    lines.append("")
    return "\n".join(lines)


def render_json(runs, summary, log_dir, window_hours, generated_at):
    """JSON report (AC6)."""
    _log(logging.DEBUG, "entry: render_json", runs=len(runs))
    payload = {
        "generated_at": generated_at,
        "log_dir": str(log_dir),
        "window_hours": window_hours,
        "summary": summary,
        "runs": [asdict(r) for r in runs],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_arg_parser():
    """Argparse parser (AC1)."""
    _log(logging.DEBUG, "entry: build_arg_parser")
    p = argparse.ArgumentParser(
        prog="codex-cost-report.py",
        description="Duration / token summary report from codex-implement logs.",
    )
    p.add_argument("--log-dir", type=Path, default=Path(".claude/logs"),
                   help="Directory with codex log files (default: .claude/logs).")
    p.add_argument("--json", dest="as_json", action="store_true",
                   help="Emit JSON instead of markdown.")
    p.add_argument("--since-hours", type=float, default=None,
                   help="Filter runs whose start_ts is within last N hours.")
    p.add_argument("--verbose", action="store_true", help="Enable DEBUG stderr logging.")
    _log(logging.DEBUG, "exit: build_arg_parser")
    return p


def main(argv=None):
    """Entry point - returns 0 on success (AC7)."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    setup_logging(args.verbose)
    _log(logging.INFO, "entry: main", argv=argv if argv is not None else sys.argv[1:])
    try:
        log_dir = args.log_dir
        runs = collect_runs(log_dir, args.since_hours)
        summary = summarise(runs)
        gen = datetime.now(timezone.utc).isoformat()
        out = (render_json(runs, summary, log_dir, args.since_hours, gen) if args.as_json
               else render_markdown(runs, summary, log_dir, args.since_hours, gen))
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
        print(out)
        _log(logging.INFO, "exit: main", runs=len(runs), exit_code=0)
        return 0
    except Exception:
        logger.exception("main failed")
        _log(logging.ERROR, "exit: main", exit_code=1)
        return 1


if __name__ == "__main__":
    sys.exit(main())