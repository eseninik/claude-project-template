#!/usr/bin/env python3
"""Lint task-N.md files before dispatch to implementation agents."""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Callable

if sys.platform == "win32":
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

logger = logging.getLogger("task_spec_validator")

VALID_EXECUTORS = {"claude", "codex", "dual"}
VALID_RISK_CLASSES = {"routine", "high-stakes"}
CHECKBOX_RE = re.compile(r"^\s*-\s*\[[ xX]\]\s*(.+)$", re.MULTILINE)
FRONTMATTER_RE = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)
HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
SCOPE_ALLOWED_RE = re.compile(r"\*\*Allowed[^*]*:\*\*", re.IGNORECASE)
SCOPE_FORBIDDEN_RE = re.compile(r"\*\*Forbidden[^*]*:\*\*", re.IGNORECASE)
TEST_BLOCK_RE = re.compile(r"```bash\s*\n(?P<body>.*?)\n```", re.DOTALL | re.IGNORECASE)


class JsonFormatter(logging.Formatter):
    """Format log records as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload.update(getattr(record, "extra_fields", {}))
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        result = json.dumps(payload, ensure_ascii=False)
        return result


class CheckResult:
    def __init__(self, name: str, status: str, detail: str = "") -> None:
        self.name = name
        self.status = status
        self.detail = detail

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status, "detail": self.detail}


class FileReport:
    def __init__(self, path: str, checks: list[CheckResult]) -> None:
        self.path = path
        self.checks = checks
        self.overall = overall_status(checks)

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "checks": [check.to_dict() for check in self.checks],
            "overall": self.overall,
        }


def _log(level: int, message: str, **fields: object) -> None:
    logger.log(level, message, extra={"extra_fields": fields})


def setup_logging(verbose: bool) -> None:
    _log(logging.DEBUG, "entry: setup_logging", verbose=verbose)
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False
    _log(logging.DEBUG, "exit: setup_logging", verbose=verbose)


def normalize_text(text: str) -> str:
    _log(logging.DEBUG, "entry: normalize_text", chars=len(text))
    result = text.replace("\r\n", "\n").replace("\r", "\n")
    _log(logging.DEBUG, "exit: normalize_text", chars=len(result))
    return result


def safe_check(name: str, func: Callable[[], CheckResult]) -> CheckResult:
    _log(logging.DEBUG, "entry: safe_check", name=name)
    try:
        result = func()
        _log(logging.DEBUG, "exit: safe_check", name=name, status=result.status)
        return result
    except Exception as exc:
        logger.exception("check failed", extra={"extra_fields": {"check": name}})
        result = CheckResult(name, "fail", str(exc))
        _log(logging.DEBUG, "exit: safe_check", name=name, status=result.status)
        return result


def parse_frontmatter(text: str) -> tuple[dict[str, str], bool]:
    _log(logging.DEBUG, "entry: parse_frontmatter", chars=len(text))
    match = FRONTMATTER_RE.search(text)
    if not match or not match.group("body").strip():
        _log(logging.DEBUG, "exit: parse_frontmatter", present=False)
        return {}, False
    values: dict[str, str] = {}
    for line in match.group("body").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        values[key.strip()] = value.split("#", 1)[0].strip().strip("\"'")
    _log(logging.DEBUG, "exit: parse_frontmatter", present=True, keys=sorted(values))
    return values, True


def section_body(text: str, heading_names: tuple[str, ...]) -> str | None:
    _log(logging.DEBUG, "entry: section_body", headings=heading_names)
    for match in HEADING_RE.finditer(text):
        title = match.group(1).strip().lower()
        if title in {heading.lower() for heading in heading_names}:
            next_match = HEADING_RE.search(text, match.end())
            end = next_match.start() if next_match else len(text)
            result = text[match.end():end].strip()
            _log(logging.DEBUG, "exit: section_body", found=True, chars=len(result))
            return result
    _log(logging.DEBUG, "exit: section_body", found=False)
    return None


def check_frontmatter_present(present: bool) -> CheckResult:
    result = CheckResult("frontmatter.present", "ok" if present else "fail")
    return result


def check_frontmatter_value(frontmatter: dict[str, str], key: str, allowed: set[str]) -> CheckResult:
    value = frontmatter.get(key, "")
    status = "ok" if value in allowed else "fail"
    detail = value if value else "missing"
    return CheckResult(f"frontmatter.{key}", status, detail)


def check_your_task(text: str) -> CheckResult:
    body = section_body(text, ("Your Task",))
    status = "ok" if body else "fail"
    detail = "present" if body else "missing or empty"
    return CheckResult("section.your_task", status, detail)


def check_scope_fence(text: str) -> CheckResult:
    body = section_body(text, ("Scope Fence",))
    ok = bool(body and SCOPE_ALLOWED_RE.search(body) and SCOPE_FORBIDDEN_RE.search(body))
    detail = "contains Allowed and Forbidden" if ok else "missing Scope Fence or markers"
    return CheckResult("section.scope_fence", "ok" if ok else "fail", detail)


def check_test_commands(text: str) -> CheckResult:
    _log(logging.DEBUG, "entry: check_test_commands")
    body = section_body(text, ("Test Commands",))
    command_count = 0
    if body:
        for match in TEST_BLOCK_RE.finditer(body):
            command_count += sum(
                1 for line in match.group("body").splitlines()
                if line.strip() and not line.strip().startswith("#")
            )
    status = "ok" if command_count else "fail"
    detail = f"{command_count} command(s)" if command_count else "missing non-empty bash block"
    result = CheckResult("section.test_commands", status, detail)
    _log(logging.DEBUG, "exit: check_test_commands", status=status, commands=command_count)
    return result


def acceptance_items(text: str) -> list[str]:
    _log(logging.DEBUG, "entry: acceptance_items")
    body = section_body(text, ("Acceptance Criteria (IMMUTABLE)", "Acceptance Criteria"))
    if body is None:
        _log(logging.DEBUG, "exit: acceptance_items", items=0)
        return []
    result = [match.group(1).strip() for match in CHECKBOX_RE.finditer(body)]
    _log(logging.DEBUG, "exit: acceptance_items", items=len(result))
    return result


def check_acceptance_criteria(text: str) -> CheckResult:
    _log(logging.DEBUG, "entry: check_acceptance_criteria")
    body = section_body(text, ("Acceptance Criteria (IMMUTABLE)", "Acceptance Criteria"))
    if body is None:
        result = CheckResult("section.acceptance_criteria", "fail", "missing")
    else:
        count = len(acceptance_items(text))
        if count < 5:
            result = CheckResult("section.acceptance_criteria", "warn", f"{count} items (require ≥ 5)")
        elif count < 10:
            result = CheckResult("section.acceptance_criteria", "warn", f"{count} items (recommend ≥ 10)")
        else:
            result = CheckResult("section.acceptance_criteria", "ok", f"{count} items")
    _log(logging.DEBUG, "exit: check_acceptance_criteria", status=result.status)
    return result


def check_handoff(text: str) -> CheckResult:
    body = section_body(text, ("Handoff Output",))
    return CheckResult("section.handoff", "ok" if body is not None else "fail", "present" if body is not None else "missing")


def check_all_tests_pass_ac(text: str) -> CheckResult:
    _log(logging.DEBUG, "entry: check_all_tests_pass_ac")
    pattern = re.compile(r"all\s+test\s+commands.*(?:exit|pass).*0", re.IGNORECASE)
    found = any(pattern.search(item) for item in acceptance_items(text))
    detail = "present" if found else "missing All Test Commands exit 0 item"
    result = CheckResult("acceptance.contains_all_tests_pass", "ok" if found else "fail", detail)
    _log(logging.DEBUG, "exit: check_all_tests_pass_ac", status=result.status)
    return result


def overall_status(checks: list[CheckResult]) -> str:
    statuses = [check.status for check in checks]
    return "fail" if "fail" in statuses else "warn" if "warn" in statuses else "ok"


def display_path(path: Path, project_root: Path) -> str:
    _log(logging.DEBUG, "entry: display_path", path=str(path), root=str(project_root))
    try:
        result = path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        result = str(path)
    _log(logging.DEBUG, "exit: display_path", result=result)
    return result


def validate_file(path: Path, project_root: Path) -> FileReport:
    _log(logging.DEBUG, "entry: validate_file", path=str(path), root=str(project_root))
    display = display_path(path, project_root)
    if not path.exists():
        report = FileReport(display, [CheckResult("missing-file", "fail", "file does not exist")])
        _log(logging.DEBUG, "exit: validate_file", path=display, overall=report.overall)
        return report
    try:
        text = normalize_text(path.read_text(encoding="utf-8"))
        frontmatter, present = parse_frontmatter(text)
    except Exception as exc:
        logger.exception("read failed", extra={"extra_fields": {"path": display}})
        report = FileReport(display, [CheckResult("read-file", "fail", str(exc))])
        _log(logging.DEBUG, "exit: validate_file", path=display, overall=report.overall)
        return report
    checks = [
        safe_check("frontmatter.present", lambda: check_frontmatter_present(present)),
        safe_check("frontmatter.executor", lambda: check_frontmatter_value(frontmatter, "executor", VALID_EXECUTORS)),
        safe_check("frontmatter.risk_class", lambda: check_frontmatter_value(frontmatter, "risk_class", VALID_RISK_CLASSES)),
        safe_check("section.your_task", lambda: check_your_task(text)),
        safe_check("section.scope_fence", lambda: check_scope_fence(text)),
        safe_check("section.test_commands", lambda: check_test_commands(text)),
        safe_check("section.acceptance_criteria", lambda: check_acceptance_criteria(text)),
        safe_check("section.handoff", lambda: check_handoff(text)),
        safe_check("acceptance.contains_all_tests_pass", lambda: check_all_tests_pass_ac(text)),
    ]
    report = FileReport(display, checks)
    _log(logging.DEBUG, "exit: validate_file", path=display, overall=report.overall)
    return report


def apply_strict(report: FileReport) -> FileReport:
    _log(logging.DEBUG, "entry: apply_strict", path=report.path)
    checks: list[CheckResult] = []
    for check in report.checks:
        if check.status == "warn":
            detail = f"strict: {check.detail}" if check.detail else "strict escalation"
            checks.append(CheckResult(check.name, "fail", detail))
        else:
            checks.append(CheckResult(check.name, check.status, check.detail))
    result = FileReport(report.path, checks)
    _log(logging.DEBUG, "exit: apply_strict", path=report.path, overall=result.overall)
    return result


def summarize(reports: list[FileReport]) -> dict[str, int]:
    _log(logging.DEBUG, "entry: summarize", files=len(reports))
    summary = {"fail": 0, "warn": 0, "ok": 0, "files": len(reports)}
    for report in reports:
        for check in report.checks:
            summary[check.status] += 1
    _log(logging.DEBUG, "exit: summarize", **summary)
    return summary


def to_json_payload(reports: list[FileReport]) -> dict[str, object]:
    _log(logging.DEBUG, "entry: to_json_payload", files=len(reports))
    result = {"files": [report.to_dict() for report in reports], "summary": summarize(reports)}
    _log(logging.DEBUG, "exit: to_json_payload", files=len(reports))
    return result


def print_text_report(reports: list[FileReport]) -> None:
    _log(logging.DEBUG, "entry: print_text_report", files=len(reports))
    for report in reports:
        print(f"{report.path}:")
        for check in report.checks:
            label = f"[{check.status.upper()}]".ljust(7)
            detail = f" ({check.detail})" if check.detail else ""
            print(f"  {label} {check.name}{detail}")
        print(f"  overall: {report.overall}")
    summary = summarize(reports)
    noun = "file" if summary["files"] == 1 else "files"
    print(
        f"SUMMARY: {summary['files']} {noun}, {summary['fail']} fail, "
        f"{summary['warn']} warn, {summary['ok']} ok"
    )
    _log(logging.DEBUG, "exit: print_text_report", files=len(reports))


def build_parser() -> argparse.ArgumentParser:
    _log(logging.DEBUG, "entry: build_parser")
    parser = argparse.ArgumentParser(description="Lint task-N.md specs before agent dispatch.")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="project root for relative paths")
    parser.add_argument("--verbose", action="store_true", help="emit DEBUG logs as JSON on stderr")
    parser.add_argument("spec_files", nargs="+", metavar="spec-file", type=Path, help="task spec file(s) to validate")
    _log(logging.DEBUG, "exit: build_parser")
    return parser


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    setup_logging(args.verbose)
    _log(logging.DEBUG, "entry: run", strict=args.strict, json=args.json, files=len(args.spec_files))
    project_root = args.project_root.resolve()
    paths = [path if path.is_absolute() else project_root / path for path in args.spec_files]
    reports = [validate_file(path, project_root) for path in paths]
    if args.strict:
        reports = [apply_strict(report) for report in reports]
    if args.json:
        print(json.dumps(to_json_payload(reports), ensure_ascii=False, indent=2))
    else:
        print_text_report(reports)
    exit_code = 1 if any(report.overall == "fail" for report in reports) else 0
    _log(logging.DEBUG, "exit: run", exit_code=exit_code)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(run())
