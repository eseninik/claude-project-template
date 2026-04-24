#!/usr/bin/env python3
"""Judge axes — pure scoring for dual-implement judging.

Each axis returns AxisResult{score in [0,1], weight, skipped, raw}.
Skipped axes are excluded from the weighted aggregate.
"""
from __future__ import annotations

import importlib.util
import json
import logging
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if sys.platform == "win32":
    for _s in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")

logger = logging.getLogger("judge_axes")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {"ts": datetime.now(timezone.utc).isoformat(),
                   "level": record.levelname, "logger": record.name,
                   "msg": record.getMessage()}
        extra = getattr(record, "extra_fields", None)
        if extra:
            payload.update(extra)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _log(level: int, msg: str, **fields: object) -> None:
    logger.log(level, msg, extra={"extra_fields": fields})


@dataclass
class TestRun:
    command: str
    exit_code: int
    duration_s: float
    stdout_tail: str = ""
    stderr_tail: str = ""

    @property
    def passed(self) -> bool:
        return self.exit_code == 0


@dataclass
class AxisResult:
    name: str
    score: float = 0.0
    weight: int = 0
    skipped: bool = False
    skip_reason: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "score": round(self.score, 4),
                "weight": self.weight, "skipped": self.skipped,
                "skip_reason": self.skip_reason, "raw": self.raw}


def _module_available(name: str) -> bool:
    _log(logging.DEBUG, "entry: _module_available", name=name)
    try:
        found = importlib.util.find_spec(name) is not None
        _log(logging.DEBUG, "exit: _module_available", name=name, found=found)
        return found
    except (ValueError, ModuleNotFoundError):
        return False


def _skip(name: str, weight: int, reason: str) -> AxisResult:
    _log(logging.INFO, "axis_skipped", axis=name, reason=reason)
    return AxisResult(name=name, weight=weight, skipped=True, skip_reason=reason)


def score_tests_passed(runs: list[TestRun], weight: int = 10) -> AxisResult:
    """Fraction of Test Commands that exited 0. Empty => skipped."""
    _log(logging.DEBUG, "entry: score_tests_passed", n=len(runs))
    try:
        if not runs:
            return _skip("tests_passed", weight, "no test commands")
        passed = sum(1 for r in runs if r.passed)
        score = passed / len(runs)
        _log(logging.DEBUG, "exit: score_tests_passed", score=score,
             passed=passed, total=len(runs))
        return AxisResult(name="tests_passed", score=score, weight=weight,
                          raw={"passed": passed, "total": len(runs)})
    except Exception:
        logger.exception("score_tests_passed failed")
        raise


def _git_diff_numstat(worktree: Path, base: str = "HEAD") -> tuple[int, int]:
    _log(logging.DEBUG, "entry: _git_diff_numstat", worktree=str(worktree), base=base)
    try:
        proc = subprocess.run(["git", "diff", "--numstat", base],
                              cwd=str(worktree), check=False, capture_output=True,
                              text=True, timeout=30)
        added = removed = 0
        for line in proc.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                added += int(parts[0])
                removed += int(parts[1])
        _log(logging.DEBUG, "exit: _git_diff_numstat", added=added, removed=removed)
        return added, removed
    except subprocess.TimeoutExpired:
        _log(logging.WARNING, "_git_diff_numstat timeout", worktree=str(worktree))
        return 0, 0
    except Exception:
        logger.exception("_git_diff_numstat failed")
        return 0, 0


def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
                    cap_lines: int = 500) -> AxisResult:
    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
    try:
        added, removed = _git_diff_numstat(worktree, base)
        score = max(0.0, 1.0 - (added / cap_lines))
        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
        return AxisResult(name="diff_size", score=score, weight=weight,
                          raw={"added": added, "removed": removed,
                               "cap_lines": cap_lines, "base": base})
    except Exception:
        logger.exception("score_diff_size failed")
        raise


_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")


def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
    _log(logging.DEBUG, "entry: _git_diff_text", worktree=str(worktree), base=base)
    try:
        proc = subprocess.run(["git", "diff", base, "--", "*.py"],
                              cwd=str(worktree), check=False, capture_output=True,
                              text=True, timeout=30)
        _log(logging.DEBUG, "exit: _git_diff_text", chars=len(proc.stdout))
        return proc.stdout
    except subprocess.TimeoutExpired:
        _log(logging.WARNING, "_git_diff_text timeout", worktree=str(worktree))
        return ""
    except Exception:
        logger.exception("_git_diff_text failed")
        return ""


def score_logging_coverage(worktree: Path, weight: int = 3, base: str = "HEAD",
                           window: int = 5, diff_text: str | None = None) -> AxisResult:
    """Fraction of NEW Python functions that log within `window` following lines."""
    _log(logging.DEBUG, "entry: score_logging_coverage", worktree=str(worktree),
         window=window)
    try:
        diff = diff_text if diff_text is not None else _git_diff_text(worktree, base)
        if not diff.strip():
            return _skip("logging_coverage", weight, "empty diff")
        lines = diff.splitlines()
        total = covered = 0
        for i, line in enumerate(lines):
            if not _FUNC_RE.match(line):
                continue
            total += 1
            found = False
            j = i + 1
            seen = 0
            while j < len(lines) and seen < window:
                nxt = lines[j]
                if nxt.startswith("@@"):
                    break
                if nxt.startswith("+") or (nxt and not nxt.startswith("-")):
                    seen += 1
                    if _LOGGER_RE.search(nxt):
                        found = True
                        break
                j += 1
            if found:
                covered += 1
        if total == 0:
            return _skip("logging_coverage", weight, "no new python functions")
        score = covered / total
        _log(logging.DEBUG, "exit: score_logging_coverage", score=score,
             covered=covered, total=total)
        return AxisResult(name="logging_coverage", score=score, weight=weight,
                          raw={"covered": covered, "total": total, "window": window})
    except Exception:
        logger.exception("score_logging_coverage failed")
        raise


def _list_modified_py(worktree: Path, base: str = "HEAD") -> list[Path]:
    _log(logging.DEBUG, "entry: _list_modified_py", worktree=str(worktree))
    try:
        proc = subprocess.run(["git", "diff", "--name-only", base],
                              cwd=str(worktree), check=False, capture_output=True,
                              text=True, timeout=30)
        files: list[Path] = []
        for line in proc.stdout.splitlines():
            s = line.strip()
            if s.endswith(".py"):
                p = worktree / s
                if p.exists():
                    files.append(p)
        _log(logging.DEBUG, "exit: _list_modified_py", count=len(files))
        return files
    except subprocess.TimeoutExpired:
        _log(logging.WARNING, "_list_modified_py timeout")
        return []
    except Exception:
        logger.exception("_list_modified_py failed")
        return []


def score_lint_clean(worktree: Path, weight: int = 2, base: str = "HEAD",
                     files_override: list[Path] | None = None) -> AxisResult:
    """py_compile + optional pyflakes. score = max(0, 1 - (errs+0.2*warns)/files)."""
    _log(logging.DEBUG, "entry: score_lint_clean", worktree=str(worktree))
    try:
        files = files_override if files_override is not None else _list_modified_py(worktree, base)
        if not files:
            return _skip("lint_clean", weight, "no modified .py files")
        compile_errors = 0
        for f in files:
            proc = subprocess.run([sys.executable, "-m", "py_compile", str(f)],
                                  check=False, capture_output=True, text=True, timeout=30)
            if proc.returncode != 0:
                compile_errors += 1
        pyflakes_warnings = 0
        pyflakes_used = _module_available("pyflakes")
        if pyflakes_used:
            proc = subprocess.run([sys.executable, "-m", "pyflakes",
                                   *[str(f) for f in files]],
                                  check=False, capture_output=True, text=True, timeout=60)
            pyflakes_warnings = sum(1 for ln in proc.stdout.splitlines() if ln.strip())
        else:
            _log(logging.INFO, "optional_tool_missing", tool="pyflakes")
        n = max(len(files), 1)
        score = max(0.0, 1.0 - (compile_errors + 0.2 * pyflakes_warnings) / n)
        _log(logging.DEBUG, "exit: score_lint_clean", score=score,
             compile_errors=compile_errors, pyflakes_warnings=pyflakes_warnings)
        return AxisResult(name="lint_clean", score=score, weight=weight,
                          raw={"files": len(files), "compile_errors": compile_errors,
                               "pyflakes_warnings": pyflakes_warnings,
                               "pyflakes_used": pyflakes_used})
    except Exception:
        logger.exception("score_lint_clean failed")
        raise


def score_complexity(worktree: Path, weight: int = 1, base: str = "HEAD",
                     files_override: list[Path] | None = None) -> AxisResult:
    """Radon CC (optional). score = max(0, 1 - avg_cc/20)."""
    _log(logging.DEBUG, "entry: score_complexity", worktree=str(worktree))
    try:
        if not _module_available("radon"):
            return _skip("complexity", weight, "radon not installed")
        files = files_override if files_override is not None else _list_modified_py(worktree, base)
        if not files:
            return _skip("complexity", weight, "no modified .py files")
        try:
            from radon.complexity import cc_visit  # type: ignore
        except ImportError:
            return _skip("complexity", weight, "radon import failed")
        cc_values: list[int] = []
        for f in files:
            try:
                src = f.read_text(encoding="utf-8", errors="replace")
                for block in cc_visit(src):
                    cc_values.append(int(block.complexity))
            except Exception:
                logger.exception("radon parse failed on %s", f)
                continue
        if not cc_values:
            return _skip("complexity", weight, "no functions in modified files")
        avg_cc = sum(cc_values) / len(cc_values)
        score = max(0.0, 1.0 - avg_cc / 20.0)
        _log(logging.DEBUG, "exit: score_complexity", score=score, avg_cc=avg_cc)
        return AxisResult(name="complexity", score=score, weight=weight,
                          raw={"avg_cc": round(avg_cc, 2), "max_cc": max(cc_values),
                               "n_functions": len(cc_values)})
    except Exception:
        logger.exception("score_complexity failed")
        raise


def score_type_check(worktree: Path, weight: int = 2, base: str = "HEAD",
                     files_override: list[Path] | None = None) -> AxisResult:
    """Mypy (optional, needs config). score = max(0, 1 - errors/files)."""
    _log(logging.DEBUG, "entry: score_type_check", worktree=str(worktree))
    try:
        if not _module_available("mypy"):
            return _skip("type_check", weight, "mypy not installed")
        has_config = any((worktree / p).exists()
                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
        if not has_config:
            return _skip("type_check", weight, "no mypy config")
        files = files_override if files_override is not None else _list_modified_py(worktree, base)
        if not files:
            return _skip("type_check", weight, "no modified .py files")
        proc = subprocess.run([sys.executable, "-m", "mypy", "--no-error-summary",
                               *[str(f) for f in files]],
                              cwd=str(worktree), check=False, capture_output=True,
                              text=True, timeout=180)
        errors = sum(1 for ln in proc.stdout.splitlines() if ": error:" in ln)
        n = max(len(files), 1)
        score = max(0.0, 1.0 - errors / n)
        _log(logging.DEBUG, "exit: score_type_check", score=score, errors=errors)
        return AxisResult(name="type_check", score=score, weight=weight,
                          raw={"errors": errors, "files": len(files)})
    except subprocess.TimeoutExpired:
        _log(logging.WARNING, "score_type_check timeout")
        return _skip("type_check", weight, "mypy timeout")
    except Exception:
        logger.exception("score_type_check failed")
        raise


def weighted_aggregate(axes: list[AxisResult]) -> float:
    """sum(weight*score) / sum(weight_used), ignoring skipped axes."""
    _log(logging.DEBUG, "entry: weighted_aggregate", n=len(axes))
    try:
        used = [a for a in axes if not a.skipped]
        if not used:
            _log(logging.WARNING, "weighted_aggregate: no active axes")
            return 0.0
        total_w = sum(a.weight for a in used)
        if total_w <= 0:
            _log(logging.WARNING, "weighted_aggregate: zero total weight")
            return 0.0
        agg = sum(a.weight * a.score for a in used) / total_w
        _log(logging.DEBUG, "exit: weighted_aggregate", agg=agg, total_w=total_w)
        return agg
    except Exception:
        logger.exception("weighted_aggregate failed")
        raise


def decide_winner(claude_agg: float, codex_agg: float,
                  tie_delta: float = 0.02) -> tuple[str, float]:
    """Return (winner, delta). winner in {'claude','codex','tie'}."""
    _log(logging.DEBUG, "entry: decide_winner", claude=claude_agg,
         codex=codex_agg, tie_delta=tie_delta)
    try:
        delta = claude_agg - codex_agg
        if delta >= tie_delta:
            winner = "claude"
        elif -delta >= tie_delta:
            winner = "codex"
        else:
            winner = "tie"
        _log(logging.DEBUG, "exit: decide_winner", winner=winner, delta=delta)
        return winner, delta
    except Exception:
        logger.exception("decide_winner failed")
        raise


def biggest_delta_rationale(claude_axes: list[AxisResult],
                            codex_axes: list[AxisResult], winner: str) -> str:
    """Cite the axis with the largest |claude - codex| delta."""
    _log(logging.DEBUG, "entry: biggest_delta_rationale", winner=winner)
    try:
        c = {a.name: a for a in claude_axes if not a.skipped}
        k = {a.name: a for a in codex_axes if not a.skipped}
        common = set(c) & set(k)
        if not common:
            return f"winner={winner}: no common active axes"
        best = max(common, key=lambda n: abs(c[n].score - k[n].score))
        out = (f"winner={winner} — biggest axis delta on '{best}' "
               f"(claude={c[best].score:.3f}, codex={k[best].score:.3f})")
        _log(logging.DEBUG, "exit: biggest_delta_rationale", rationale=out)
        return out
    except Exception:
        logger.exception("biggest_delta_rationale failed")
        raise