#!/usr/bin/env python3
"""Aggregate dual-implement judge verdict JSON files into a report."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if sys.platform == "win32":
    for _stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")

logger = logging.getLogger("verdict_summarizer")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {"ts": datetime.now(timezone.utc).isoformat(), "level": record.levelname,
                   "logger": record.name, "msg": record.getMessage()}
        extra = getattr(record, "extra_fields", None)
        if extra:
            payload.update(extra)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _log(level: int, msg: str, **fields: object) -> None:
    logger.log(level, msg, extra={"extra_fields": fields})


def setup_logging(verbose: bool = False) -> None:
    _log(logging.DEBUG, "entry: setup_logging", verbose=verbose)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    handler.setLevel(logging.DEBUG if verbose else logging.WARNING)
    logger.addHandler(handler)
    logger.propagate = False
    _log(logging.DEBUG, "exit: setup_logging")


def build_arg_parser() -> argparse.ArgumentParser:
    _log(logging.DEBUG, "entry: build_arg_parser")
    parser = argparse.ArgumentParser(
        description="Aggregate work/**/verdicts/*.json judge outputs."
    )
    parser.add_argument("--root", default="work", help="root directory to scan")
    parser.add_argument("--feature", help="feature directory name to include")
    parser.add_argument("--since-days", type=int, help="include verdicts within N days")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    parser.add_argument("--top-axes", type=int, default=3, help="number of contested axes to show")
    parser.add_argument("--verbose", action="store_true", help="enable DEBUG JSON logs")
    _log(logging.DEBUG, "exit: build_arg_parser")
    return parser


def parse_timestamp(value: Any) -> datetime | None:
    _log(logging.DEBUG, "entry: parse_timestamp", has_value=value is not None)
    if not isinstance(value, str) or not value.strip():
        _log(logging.DEBUG, "exit: parse_timestamp", parsed=False)
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        _log(logging.DEBUG, "exit: parse_timestamp", parsed=True)
        return parsed
    except ValueError:
        logger.exception("parse_timestamp failed", extra={"extra_fields": {"timestamp": value}})
        return None


def _score_value(scores: Any, side: str) -> float | None:
    _log(logging.DEBUG, "entry: _score_value", side=side)
    value = scores.get(side) if isinstance(scores, dict) else None
    if isinstance(value, (int, float)):
        result = float(value)
    elif isinstance(value, dict) and isinstance(value.get("aggregate"), (int, float)):
        result = float(value["aggregate"])
    else:
        result = None
    _log(logging.DEBUG, "exit: _score_value", side=side, found=result is not None)
    return result


def _axis_side_value(axis: Any, side: str) -> float | None:
    _log(logging.DEBUG, "entry: _axis_side_value", side=side)
    if not isinstance(axis, dict):
        _log(logging.DEBUG, "exit: _axis_side_value", found=False)
        return None
    value = axis.get(side)
    if isinstance(value, (int, float)):
        result = float(value)
    elif isinstance(value, dict) and isinstance(value.get("score"), (int, float)):
        result = float(value["score"])
    else:
        result = None
    _log(logging.DEBUG, "exit: _axis_side_value", found=result is not None)
    return result


def normalize_axes(raw: dict[str, Any]) -> dict[str, dict[str, float]]:
    _log(logging.DEBUG, "entry: normalize_axes")
    axes: dict[str, dict[str, float]] = {}
    top_axes = raw.get("axes")
    if isinstance(top_axes, dict):
        for name, axis in top_axes.items():
            claude = _axis_side_value(axis, "claude")
            codex = _axis_side_value(axis, "codex")
            if claude is not None and codex is not None:
                axes[str(name)] = {"claude": claude, "codex": codex}
    scores = raw.get("scores")
    if isinstance(scores, dict):
        claude_axes = scores.get("claude", {}).get("axes", {}) if isinstance(scores.get("claude"), dict) else {}
        codex_axes = scores.get("codex", {}).get("axes", {}) if isinstance(scores.get("codex"), dict) else {}
        if isinstance(claude_axes, dict) and isinstance(codex_axes, dict):
            for name in sorted(set(claude_axes) & set(codex_axes)):
                claude = _axis_side_value(claude_axes[name], "score")
                codex = _axis_side_value(codex_axes[name], "score")
                if claude is not None and codex is not None:
                    axes[str(name)] = {"claude": claude, "codex": codex}
    _log(logging.DEBUG, "exit: normalize_axes", axes=len(axes))
    return axes


def load_verdict(path: Path) -> dict[str, Any] | None:
    _log(logging.DEBUG, "entry: load_verdict", path=path.as_posix())
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.exception("malformed_json", extra={"extra_fields": {"path": path.as_posix()}})
        return None
    except OSError:
        logger.exception("read_failed", extra={"extra_fields": {"path": path.as_posix()}})
        return None
    if not isinstance(raw, dict):
        _log(logging.WARNING, "invalid_schema", path=path.as_posix(), reason="not_object")
        return None
    missing = [key for key in ("task_id", "winner", "delta", "scores", "timestamp") if key not in raw]
    if missing:
        _log(logging.WARNING, "missing_fields", path=path.as_posix(), fields=missing)
    if "axes" not in raw:
        _log(logging.WARNING, "missing_fields", path=path.as_posix(), fields=["axes"])
    scores = raw.get("scores")
    verdict = {
        "task_id": str(raw.get("task_id") or path.stem),
        "winner": str(raw.get("winner") or "unknown"),
        "delta": float(raw.get("delta")) if isinstance(raw.get("delta"), (int, float)) else 0.0,
        "score_claude": _score_value(scores, "claude"),
        "score_codex": _score_value(scores, "codex"),
        "timestamp": str(raw.get("timestamp") or ""),
        "timestamp_dt": parse_timestamp(raw.get("timestamp")),
        "path": path.as_posix(),
        "axes_map": normalize_axes(raw),
    }
    _log(logging.DEBUG, "exit: load_verdict", path=path.as_posix(), loaded=True)
    return verdict


def iter_verdict_paths(root: Path, feature: str | None = None) -> list[Path]:
    _log(logging.DEBUG, "entry: iter_verdict_paths", root=root.as_posix(), feature=feature)
    scan_root = root / feature if feature else root
    paths = sorted(scan_root.rglob("verdicts/*.json")) if scan_root.exists() else []
    _log(logging.DEBUG, "exit: iter_verdict_paths", count=len(paths))
    return paths


def filter_by_window(verdicts: list[dict[str, Any]], since_days: int | None, generated_at: datetime) -> list[dict[str, Any]]:
    _log(logging.DEBUG, "entry: filter_by_window", verdicts=len(verdicts), since_days=since_days)
    if since_days is None:
        _log(logging.DEBUG, "exit: filter_by_window", verdicts=len(verdicts))
        return verdicts
    cutoff = generated_at.timestamp() - (since_days * 86400)
    filtered = [item for item in verdicts if item["timestamp_dt"] is not None and item["timestamp_dt"].timestamp() >= cutoff]
    _log(logging.DEBUG, "exit: filter_by_window", verdicts=len(filtered))
    return filtered


def summarize_axes(verdicts: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
    _log(logging.DEBUG, "entry: summarize_axes", verdicts=len(verdicts), top_k=top_k)
    totals: dict[str, list[float]] = {}
    for verdict in verdicts:
        for name, values in verdict.get("axes_map", {}).items():
            claude = values.get("claude")
            codex = values.get("codex")
            if claude is not None and codex is not None and claude != codex:
                totals.setdefault(name, []).append(abs(claude - codex))
    rows = [
        {"name": name, "contested_count": len(deltas), "mean_abs_delta": sum(deltas) / len(deltas)}
        for name, deltas in totals.items()
    ]
    rows.sort(key=lambda item: (-item["mean_abs_delta"], -item["contested_count"], item["name"]))
    result = rows[: max(top_k, 0)]
    _log(logging.DEBUG, "exit: summarize_axes", axes=len(result))
    return result


def build_report(root: Path, feature: str | None, since_days: int | None, top_axes: int, generated_at: datetime | None = None) -> dict[str, Any]:
    _log(logging.DEBUG, "entry: build_report", root=root.as_posix(), feature=feature, since_days=since_days, top_axes=top_axes)
    generated = generated_at or datetime.now(timezone.utc)
    resolved_root = root.expanduser().resolve()
    verdicts = [item for path in iter_verdict_paths(resolved_root, feature) if (item := load_verdict(path)) is not None]
    verdicts = filter_by_window(verdicts, since_days, generated)
    verdicts.sort(key=lambda item: ((item["timestamp_dt"].timestamp() if item["timestamp_dt"] else float("-inf")), item["task_id"]))
    summary = {"verdicts": len(verdicts), "claude": 0, "codex": 0, "tie": 0}
    for verdict in verdicts:
        if verdict["winner"] in summary:
            summary[verdict["winner"]] += 1
    hidden = {"timestamp_dt", "axes_map"}
    display_root = "work/" if not root.is_absolute() and root.as_posix() == "work" else root.as_posix()
    public_verdicts = [{key: value for key, value in verdict.items() if key not in hidden} for verdict in verdicts]
    report = {
        "generated_at": generated.isoformat(),
        "root": display_root,
        "feature": feature,
        "window_days": since_days,
        "summary": summary,
        "verdicts": public_verdicts,
        "axes": summarize_axes(verdicts, top_axes),
    }
    _log(logging.DEBUG, "exit: build_report", verdicts=len(public_verdicts), axes=len(report["axes"]))
    return report


def _format_score(value: float | None) -> str:
    _log(logging.DEBUG, "entry: _format_score", found=value is not None)
    result = "" if value is None else f"{value:.4f}"
    _log(logging.DEBUG, "exit: _format_score")
    return result


def _format_timestamp(value: str) -> str:
    _log(logging.DEBUG, "entry: _format_timestamp", has_value=bool(value))
    parsed = parse_timestamp(value)
    parsed = parsed.astimezone() if parsed and parsed.tzinfo is not None else parsed
    result = parsed.strftime("%Y-%m-%d %H:%M") if parsed else value
    _log(logging.DEBUG, "exit: _format_timestamp")
    return result


def render_markdown(report: dict[str, Any], top_axes: int | None = None) -> str:
    _log(logging.DEBUG, "entry: render_markdown", verdicts=report["summary"]["verdicts"])
    if not report["verdicts"]:
        result = f"No verdicts found under {report['root']} matching filters.\n"
        _log(logging.DEBUG, "exit: render_markdown", empty=True)
        return result
    summary = report["summary"]
    lines = [
        "# Dual-Implement Verdict Summary",
        f"- generated: {report['generated_at']}",
        f"- root: {report['root']}",
        f"- feature filter: {report['feature'] or '(none)'}",
        f"- verdicts found: {summary['verdicts']}",
        f"- winners: claude={summary['claude']} codex={summary['codex']} tie={summary['tie']}",
        "",
        "## Per-task table",
        "| Task | Winner | Delta | Score Claude | Score Codex | Timestamp |",
        "|------|--------|-------|--------------|-------------|-----------|",
    ]
    for verdict in report["verdicts"]:
        lines.append(
            f"| {verdict['task_id']} | {verdict['winner']} | {verdict['delta']:+.4f} | "
            f"{_format_score(verdict['score_claude'])} | {_format_score(verdict['score_codex'])} | "
            f"{_format_timestamp(verdict['timestamp'])} |"
        )
    lines.extend(["", f"## Top-{top_axes if top_axes is not None else len(report['axes'])} contested axes"])
    for axis in report["axes"]:
        lines.append(
            f"- {axis['name']}: {axis['contested_count']}/{summary['verdicts']} verdicts non-zero, "
            f"mean |\u0394|={axis['mean_abs_delta']:.3f}"
        )
    result = "\n".join(lines) + "\n"
    _log(logging.DEBUG, "exit: render_markdown", empty=False)
    return result


def main(argv: list[str] | None = None) -> int:
    setup_logging(False)
    args = build_arg_parser().parse_args(argv)
    setup_logging(args.verbose)
    _log(logging.INFO, "entry: main", root=args.root, feature=args.feature, since_days=args.since_days, json=args.json, top_axes=args.top_axes)
    report = build_report(Path(args.root), args.feature, args.since_days, args.top_axes)
    if args.json:
        sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    else:
        sys.stdout.write(render_markdown(report, args.top_axes))
    _log(logging.INFO, "exit: main", verdicts=report["summary"]["verdicts"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
