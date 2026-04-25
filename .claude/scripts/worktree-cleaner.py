"""List or remove stale dual-team git worktrees and branches."""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger("worktree_cleaner")
SECONDS_PER_DAY = 86_400
GIT_TIMEOUT_SECONDS = 30
LOG_ATTRS = set(logging.makeLogRecord({}).__dict__)


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in LOG_ATTRS and key not in {"message", "asctime"}:
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, sort_keys=True, default=str)


@dataclass
class WorktreeRecord:
    worktree: Path
    branch: str
    head: str


@dataclass
class CleanupEntry:
    worktree: Path
    branch: str
    reasons: list[str]
    has_sentinel: bool
    age_days: int | None
    apply_status: str = "skipped"


def configure_logging(verbose: bool) -> None:
    LOGGER.debug("configure_logging.entry", extra={"verbose": verbose})
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    LOGGER.debug("configure_logging.exit", extra={"root_level": root.level})


def run_git(git_args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    LOGGER.debug("run_git.entry", extra={"git_args": git_args, "cwd_path": str(cwd) if cwd else None})
    try:
        result = subprocess.run(
            ["git", "-c", "safe.directory=*", *git_args], cwd=str(cwd) if cwd else None, check=False,
            capture_output=True, text=True, timeout=GIT_TIMEOUT_SECONDS,
        )
    except Exception:
        LOGGER.exception("run_git.error", extra={"git_args": git_args, "cwd_path": str(cwd) if cwd else None})
        raise
    LOGGER.debug("run_git.exit", extra={"returncode": result.returncode, "git_args": git_args})
    return result


def _record_from_fields(fields: dict[str, str]) -> WorktreeRecord:
    LOGGER.debug("_record_from_fields.entry", extra={"keys": sorted(fields)})
    branch = fields.get("branch", "")
    if branch.startswith("refs/heads/"):
        branch = branch.removeprefix("refs/heads/")
    record = WorktreeRecord(Path(fields.get("worktree", "")), branch, fields.get("HEAD", ""))
    LOGGER.debug("_record_from_fields.exit", extra={"worktree": str(record.worktree), "branch_name": branch})
    return record


def parse_porcelain(text: str) -> list[WorktreeRecord]:
    LOGGER.debug("parse_porcelain.entry", extra={"line_count": len(text.splitlines())})
    records: list[WorktreeRecord] = []
    current: dict[str, str] = {}
    for line in text.splitlines():
        if not line:
            if current:
                records.append(_record_from_fields(current))
                current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    if current:
        records.append(_record_from_fields(current))
    LOGGER.debug("parse_porcelain.exit", extra={"record_count": len(records)})
    return records


def get_worktree_records() -> list[WorktreeRecord]:
    LOGGER.debug("get_worktree_records.entry")
    result = run_git(["worktree", "list", "--porcelain"])
    if result.returncode != 0:
        LOGGER.error("get_worktree_records.error", extra={"stderr": result.stderr.strip()})
        raise RuntimeError(f"git worktree list failed: {result.stderr.strip()}")
    records = parse_porcelain(result.stdout)
    LOGGER.debug("get_worktree_records.exit", extra={"record_count": len(records)})
    return records


def get_main_branch(main_root: Path) -> str:
    LOGGER.debug("get_main_branch.entry", extra={"main_root": str(main_root)})
    result = run_git(["symbolic-ref", "--short", "HEAD"], cwd=main_root)
    branch = result.stdout.strip() if result.returncode == 0 else ""
    LOGGER.debug("get_main_branch.exit", extra={"branch_name": branch})
    return branch


def resolve_prefix(main_root: Path, prefix: str) -> Path:
    LOGGER.debug("resolve_prefix.entry", extra={"main_root": str(main_root), "prefix": prefix})
    prefix_path = Path(prefix)
    resolved = (prefix_path if prefix_path.is_absolute() else main_root / prefix_path).resolve()
    LOGGER.debug("resolve_prefix.exit", extra={"resolved": str(resolved)})
    return resolved


def is_inside_prefix(path: Path, prefix_root: Path) -> bool:
    LOGGER.debug("is_inside_prefix.entry", extra={"path": str(path), "prefix_root": str(prefix_root)})
    try:
        path.resolve().relative_to(prefix_root)
        inside = True
    except ValueError:
        inside = False
    LOGGER.debug("is_inside_prefix.exit", extra={"inside": inside})
    return inside


def read_base_ref(worktree: Path) -> tuple[bool, str | None]:
    LOGGER.debug("read_base_ref.entry", extra={"worktree": str(worktree)})
    sentinel = worktree / ".dual-base-ref"
    has_sentinel = sentinel.is_file()
    base_ref: str | None = None
    if has_sentinel:
        try:
            base_ref = sentinel.read_text(encoding="utf-8").strip() or None
        except OSError:
            LOGGER.exception("read_base_ref.error", extra={"sentinel": str(sentinel)})
    LOGGER.debug("read_base_ref.exit", extra={"has_sentinel": has_sentinel, "base_ref": base_ref})
    return has_sentinel, base_ref


def get_commit_timestamps(branch: str, base_ref: str | None, main_branch: str) -> list[int]:
    LOGGER.debug("get_commit_timestamps.entry", extra={"branch_name": branch, "base_ref": base_ref})
    if not branch:
        LOGGER.debug("get_commit_timestamps.exit", extra={"timestamp_count": 0})
        return []
    effective_base = base_ref
    if not effective_base and main_branch:
        merge_base = run_git(["merge-base", branch, main_branch])
        effective_base = merge_base.stdout.strip() if merge_base.returncode == 0 else None
    if not effective_base:
        LOGGER.debug("get_commit_timestamps.exit", extra={"timestamp_count": 0})
        return []
    result = run_git(["log", "--no-merges", "--format=%ct", f"{effective_base}..{branch}"])
    if result.returncode != 0:
        LOGGER.error("get_commit_timestamps.error", extra={"branch_name": branch, "stderr": result.stderr.strip()})
        LOGGER.debug("get_commit_timestamps.exit", extra={"timestamp_count": 0})
        return []
    timestamps = [int(line) for line in result.stdout.splitlines() if line.strip().isdigit()]
    LOGGER.debug("get_commit_timestamps.exit", extra={"timestamp_count": len(timestamps)})
    return timestamps


def collect_entries(records: list[WorktreeRecord], prefix: str, max_age_days: int, now: float) -> tuple[list[CleanupEntry], Path]:
    LOGGER.debug("collect_entries.entry", extra={"record_count": len(records), "prefix": prefix})
    if not records:
        cwd = Path.cwd().resolve()
        LOGGER.debug("collect_entries.exit", extra={"entry_count": 0, "main_root": str(cwd)})
        return [], cwd
    main_root = records[0].worktree.resolve()
    prefix_root = resolve_prefix(main_root, prefix)
    main_branch = get_main_branch(main_root)
    entries: list[CleanupEntry] = []
    for record in records:
        worktree = record.worktree.resolve()
        if not is_inside_prefix(worktree, prefix_root) or (record.branch and record.branch == main_branch):
            continue
        has_sentinel, base_ref = read_base_ref(worktree)
        timestamps = get_commit_timestamps(record.branch, base_ref, main_branch)
        age_days = None if not timestamps else max(0, int((now - max(timestamps)) // SECONDS_PER_DAY))
        reasons = ([] if has_sentinel else ["a"]) + (["b"] if age_days is not None and age_days >= max_age_days else [])
        if age_days is None:
            reasons.append("c")
        entries.append(CleanupEntry(worktree, record.branch, reasons, has_sentinel, age_days))
    LOGGER.debug("collect_entries.exit", extra={"entry_count": len(entries), "main_root": str(main_root)})
    return entries, main_root


def display_path(path: Path, main_root: Path) -> str:
    LOGGER.debug("display_path.entry", extra={"path": str(path), "main_root": str(main_root)})
    try:
        value = path.resolve().relative_to(main_root).as_posix()
    except ValueError:
        value = str(path)
    LOGGER.debug("display_path.exit", extra={"value": value})
    return value


def format_human(entries: list[CleanupEntry], main_root: Path, apply_mode: bool) -> str:
    LOGGER.debug("format_human.entry", extra={"entry_count": len(entries), "apply_mode": apply_mode})
    stale = [entry for entry in entries if entry.reasons]
    if not stale:
        LOGGER.debug("format_human.exit", extra={"stale_count": 0})
        return "No stale worktrees found\n"
    lines = [f"Found {len(stale)} stale worktree(s):"]
    for entry in stale:
        details = ["no commits beyond base"] if entry.age_days is None and "c" in entry.reasons else []
        if entry.age_days is not None:
            details.append(f"age={entry.age_days}d")
        if not entry.has_sentinel:
            details.append("no sentinel")
        marker = ("[" + ",".join(entry.reasons) + "]").ljust(5)
        lines.append(f"  {marker} {display_path(entry.worktree, main_root)} ({', '.join(details)})")
    lines.append("Removal attempted. See logs for details." if apply_mode else "Run with --apply to remove. Skipping (dry-run).")
    output = "\n".join(lines) + "\n"
    LOGGER.debug("format_human.exit", extra={"stale_count": len(stale)})
    return output


def format_json(entries: list[CleanupEntry], main_root: Path) -> str:
    LOGGER.debug("format_json.entry", extra={"entry_count": len(entries)})
    stale_count = sum(1 for entry in entries if entry.reasons)
    payload = {"found": len(entries), "stale": stale_count, "kept": len(entries) - stale_count, "entries": [
        {"worktree": display_path(entry.worktree, main_root), "branch": entry.branch, "reasons": entry.reasons,
         "has_sentinel": entry.has_sentinel, "age_days": entry.age_days, "apply_status": entry.apply_status}
        for entry in entries]}
    output = json.dumps(payload, sort_keys=True) + "\n"
    LOGGER.debug("format_json.exit", extra={"stale_count": stale_count})
    return output


def apply_cleanup(entries: list[CleanupEntry]) -> bool:
    LOGGER.debug("apply_cleanup.entry", extra={"entry_count": len(entries)})
    ok = True
    for entry in entries:
        if not entry.reasons:
            continue
        remove = run_git(["worktree", "remove", "--force", str(entry.worktree)])
        LOGGER.info("apply.worktree_remove", extra={"worktree": str(entry.worktree), "returncode": remove.returncode})
        branch = run_git(["branch", "-D", entry.branch])
        LOGGER.info("apply.branch_delete", extra={"branch_name": entry.branch, "returncode": branch.returncode})
        entry.apply_status = "removed" if remove.returncode == 0 and branch.returncode == 0 else "error"
        ok = ok and entry.apply_status == "removed"
    LOGGER.debug("apply_cleanup.exit", extra={"ok": ok})
    return ok


def build_parser() -> argparse.ArgumentParser:
    LOGGER.debug("build_parser.entry")
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="list stale worktrees without removing them")
    mode.add_argument("--apply", action="store_true", help="remove stale worktrees and local branches")
    parser.add_argument("--max-age-days", type=int, default=7, help="stale age threshold in days")
    parser.add_argument("--worktree-prefix", default="worktrees/", help="worktree prefix to scan")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--verbose", action="store_true", help="enable DEBUG logs")
    LOGGER.debug("build_parser.exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.verbose)
    LOGGER.debug("main.entry", extra={"argv_value": argv})
    try:
        records = get_worktree_records()
        entries, main_root = collect_entries(records, args.worktree_prefix, args.max_age_days, time.time())
        ok = apply_cleanup(entries) if args.apply else True
        sys.stdout.write(format_json(entries, main_root) if args.json else format_human(entries, main_root, args.apply))
        exit_code = 0 if ok else 1
    except Exception:
        LOGGER.exception("main.error")
        exit_code = 1
    LOGGER.debug("main.exit", extra={"exit_code": exit_code})
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())


