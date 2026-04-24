#!/usr/bin/env python3
"""Judge — objective judge for dual-implement runs.

Runs Test Commands in claude & codex worktrees, scores on 6 axes (see
judge_axes.py), emits verdict JSON. Exit 0 valid run, 1 infra failure.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if sys.platform == "win32":
    for _s in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import judge_axes  # noqa: E402
from judge_axes import (  # noqa: E402
    AxisResult, TestRun, biggest_delta_rationale, decide_winner,
    score_complexity, score_diff_size, score_lint_clean,
    score_logging_coverage, score_tests_passed, score_type_check,
    weighted_aggregate,
)

logger = logging.getLogger("judge")
EXIT_OK, EXIT_INFRA = 0, 1

_MAIN_BRANCHES = ("main", "master", "dev")


def _log(level: int, msg: str, **fields: object) -> None:
    logger.log(level, msg, extra={"extra_fields": fields})


def setup_logging() -> None:
    """Init JSON logger on stderr."""
    _log(logging.DEBUG, "entry: setup_logging")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    h = logging.StreamHandler(sys.stderr)
    h.setFormatter(judge_axes.JsonFormatter())
    h.setLevel(logging.INFO)
    logger.addHandler(h)
    _log(logging.DEBUG, "exit: setup_logging")


def _load_task_parser() -> Any:
    """Try reusing codex-implement.parse_task_file via importlib."""
    _log(logging.DEBUG, "entry: _load_task_parser")
    try:
        ci = _THIS_DIR / "codex-implement.py"
        if not ci.exists():
            return None
        spec = importlib.util.spec_from_file_location("codex_implement", ci)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _log(logging.DEBUG, "exit: _load_task_parser", reused=True)
        return mod
    except Exception:
        logger.exception("_load_task_parser failed")
        return None


@dataclass
class ParsedTask:
    task_id: str
    test_commands: list[str]
    acceptance_criteria: list[str]


def _local_parse(text: str, stem: str) -> ParsedTask:
    """Fallback parser for Test Commands + acceptance criteria."""
    _log(logging.DEBUG, "entry: _local_parse", stem=stem)
    tid_m = re.match(r"^T(\d+[\w\-]*)", stem, re.IGNORECASE)
    tid = tid_m.group(1) if tid_m else (
        re.match(r"^task-(.+)$", stem, re.IGNORECASE) or re.match(r"(.+)", stem)).group(1)
    try:
        m = re.search(r"^##\s+Test Commands.*?$(.*?)(?=^##\s+|\Z)",
                      text, flags=re.MULTILINE | re.DOTALL)
        cmds: list[str] = []
        if m:
            in_block = False
            for line in m.group(1).splitlines():
                s = line.strip()
                if s.startswith("```"):
                    in_block = not in_block
                    continue
                if in_block and s and not s.startswith("#"):
                    cmds.append(s)
        m2 = re.search(r"^##\s+Acceptance Criteria.*?$(.*?)(?=^##\s+|\Z)",
                       text, flags=re.MULTILINE | re.DOTALL)
        acs = [mm.group(1).strip()
               for line in (m2.group(1).splitlines() if m2 else [])
               for mm in [re.match(r"^\s*-\s*\[.\]\s*(.+)$", line)] if mm]
        pt = ParsedTask(task_id=tid, test_commands=cmds, acceptance_criteria=acs)
        _log(logging.DEBUG, "exit: _local_parse", task_id=pt.task_id, n_cmds=len(cmds))
        return pt
    except Exception:
        logger.exception("_local_parse failed")
        raise


def parse_task(task_path: Path) -> ParsedTask:
    """Parse task-N.md for Test Commands + acceptance criteria."""
    _log(logging.DEBUG, "entry: parse_task", task_path=str(task_path))
    try:
        if not task_path.exists():
            raise FileNotFoundError(f"Task file not found: {task_path}")
        mod = _load_task_parser()
        if mod is not None:
            try:
                t = mod.parse_task_file(task_path)
                pt = ParsedTask(task_id=t.task_id,
                                test_commands=list(t.test_commands),
                                acceptance_criteria=list(t.acceptance_criteria))
                _log(logging.INFO, "parsed_task_via_shared",
                     task_id=pt.task_id, n_cmds=len(pt.test_commands))
                return pt
            except Exception:
                logger.exception("shared parser failed; fallback local")
        pt = _local_parse(task_path.read_text(encoding="utf-8"), task_path.stem)
        _log(logging.INFO, "parsed_task_locally", task_id=pt.task_id,
             n_cmds=len(pt.test_commands))
        return pt
    except Exception:
        logger.exception("parse_task failed")
        raise


def _tail(text: str, n: int = 20) -> str:
    return "\n".join(text.splitlines()[-n:])


def run_test_commands(commands: list[str], worktree: Path,
                      per_timeout: int = 600) -> list[TestRun]:
    """Run each shell command in worktree; capture exit/tail/duration."""
    _log(logging.DEBUG, "entry: run_test_commands", n=len(commands),
         worktree=str(worktree))
    try:
        results: list[TestRun] = []
        for cmd in commands:
            _log(logging.INFO, "running_test", cmd=cmd, worktree=str(worktree))
            t0 = time.monotonic()
            try:
                proc = subprocess.run(cmd, shell=True, cwd=str(worktree),
                                      check=False, capture_output=True,
                                      text=True, timeout=per_timeout)
                run = TestRun(command=cmd, exit_code=proc.returncode,
                              duration_s=round(time.monotonic() - t0, 3),
                              stdout_tail=_tail(proc.stdout, 20),
                              stderr_tail=_tail(proc.stderr, 20))
            except subprocess.TimeoutExpired:
                _log(logging.WARNING, "test_timeout", cmd=cmd)
                run = TestRun(command=cmd, exit_code=124,
                              duration_s=round(time.monotonic() - t0, 3),
                              stdout_tail="", stderr_tail="TIMEOUT")
            results.append(run)
            _log(logging.INFO, "test_done", cmd=cmd, rc=run.exit_code,
                 dur=run.duration_s)
        _log(logging.DEBUG, "exit: run_test_commands", n=len(results))
        return results
    except Exception:
        logger.exception("run_test_commands failed")
        raise


def _resolve_base(worktree: Path, cli_base: str) -> str:
    """Resolve the diff base for one side's worktree.

    Priority (first match wins):
      1. Explicit CLI arg (not ``"HEAD"`` or ``"auto"``) - pass-through verbatim.
      2. Sidecar file ``<worktree>/.dual-base-ref`` (first non-empty line).
      3. ``git merge-base HEAD <branch>`` for branch in (main, master, dev).
      4. Literal ``"HEAD"`` fallback.

    Logs which level hit at INFO. Swallows per-step errors so a broken sidecar
    or missing git CLI cannot break scoring - always returns a usable string.
    """
    _log(logging.DEBUG, "entry: _resolve_base", worktree=str(worktree),
         cli_base=cli_base)
    try:
        if cli_base and cli_base not in ("HEAD", "auto"):
            _log(logging.INFO, "resolve_base hit=cli", base=cli_base,
                 worktree=str(worktree))
            return cli_base
        sidecar = worktree / ".dual-base-ref"
        if sidecar.exists():
            try:
                for ln in sidecar.read_text(encoding="utf-8").splitlines():
                    s = ln.strip()
                    if s and not s.startswith("#"):
                        _log(logging.INFO, "resolve_base hit=sidecar",
                             base=s, worktree=str(worktree))
                        return s
            except Exception:
                logger.exception("_resolve_base sidecar read failed")
        for branch in _MAIN_BRANCHES:
            try:
                proc = subprocess.run(
                    ["git", "merge-base", "HEAD", branch],
                    cwd=str(worktree), check=False, capture_output=True,
                    text=True, timeout=15,
                )
                if proc.returncode == 0:
                    sha = proc.stdout.strip()
                    if sha:
                        _log(logging.INFO, "resolve_base hit=merge-base",
                             branch=branch, base=sha[:12],
                             worktree=str(worktree))
                        return sha
            except subprocess.TimeoutExpired:
                _log(logging.WARNING, "_resolve_base merge-base timeout",
                     branch=branch)
                continue
            except Exception:
                logger.exception("_resolve_base merge-base error branch=%s", branch)
                continue
        _log(logging.INFO, "resolve_base hit=fallback", base="HEAD",
             worktree=str(worktree))
        return "HEAD"
    except Exception:
        logger.exception("_resolve_base unexpected error")
        return "HEAD"


def score_side(worktree: Path, test_runs: list[TestRun],
               base: str = "HEAD") -> list[AxisResult]:
    """Compute all six axes for one side."""
    _log(logging.DEBUG, "entry: score_side", worktree=str(worktree), base=base)
    try:
        axes = [score_tests_passed(test_runs, weight=10),
                score_diff_size(worktree, weight=2, base=base),
                score_logging_coverage(worktree, weight=3, base=base),
                score_lint_clean(worktree, weight=2, base=base),
                score_complexity(worktree, weight=1, base=base),
                score_type_check(worktree, weight=2, base=base)]
        _log(logging.DEBUG, "exit: score_side",
             active=sum(1 for a in axes if not a.skipped))
        return axes
    except Exception:
        logger.exception("score_side failed")
        raise


def build_verdict(task_id: str, claude_axes: list[AxisResult],
                  codex_axes: list[AxisResult],
                  tie_delta: float = 0.02) -> dict[str, Any]:
    """Assemble verdict JSON per AC7 schema."""
    _log(logging.DEBUG, "entry: build_verdict", task_id=task_id, tie_delta=tie_delta)
    try:
        c_agg = weighted_aggregate(claude_axes)
        k_agg = weighted_aggregate(codex_axes)
        winner, delta = decide_winner(c_agg, k_agg, tie_delta)
        verdict = {
            "task_id": task_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "winner": winner, "delta": round(delta, 4), "tie_delta": tie_delta,
            "scores": {
                "claude": {"aggregate": round(c_agg, 4),
                           "axes": {a.name: a.to_dict() for a in claude_axes}},
                "codex": {"aggregate": round(k_agg, 4),
                          "axes": {a.name: a.to_dict() for a in codex_axes}},
            },
            "rationale_auto": biggest_delta_rationale(claude_axes, codex_axes, winner),
            "rationale_manual": None,
        }
        _log(logging.INFO, "verdict_built", task_id=task_id, winner=winner,
             delta=round(delta, 4))
        return verdict
    except Exception:
        logger.exception("build_verdict failed")
        raise


def _default_output(task_id: str) -> Path:
    return Path("work/codex-primary/dual-history") / task_id / "judge-verdict.json"


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="judge.py",
        description="Objective judge for Claude vs Codex dual-implement runs.")
    p.add_argument("--task", required=True, type=Path, help="Path to task-N.md")
    p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
    p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
    p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
    p.add_argument("--base", default="auto",
                   help="Git diff base. 'auto' = auto-resolve per side via "
                        "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
                        "then HEAD fallback. 'HEAD' = literal HEAD pass-through. "
                        "Any other value = explicit base (commit sha / ref).")
    p.add_argument("--per-timeout", type=int, default=600, help="Per-cmd timeout (s)")
    p.add_argument("--dry-run", action="store_true", help="Print plan, skip tests")
    return p


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    args = build_arg_parser().parse_args(argv)
    _log(logging.INFO, "judge_start", task=str(args.task),
         claude=str(args.claude_worktree), codex=str(args.codex_worktree),
         tie_delta=args.tie_delta, dry_run=args.dry_run, base_arg=args.base)
    try:
        try:
            task = parse_task(args.task)
        except (FileNotFoundError, Exception) as e:  # noqa: B014
            _log(logging.ERROR, "task_parse_failed", err=str(e))
            print(f"ERROR: {e}", file=sys.stderr)
            return EXIT_INFRA
        for label, wt in (("claude", args.claude_worktree), ("codex", args.codex_worktree)):
            if not wt.exists():
                _log(logging.ERROR, "worktree_missing", side=label, path=str(wt))
                print(f"ERROR: {label} worktree not found: {wt}", file=sys.stderr)
                return EXIT_INFRA
        output = args.output or _default_output(task.task_id)
        if args.dry_run:
            plan = {"task_id": task.task_id, "test_commands": task.test_commands,
                    "claude_worktree": str(args.claude_worktree),
                    "codex_worktree": str(args.codex_worktree),
                    "output": str(output), "tie_delta": args.tie_delta,
                    "base_arg": args.base}
            print(json.dumps(plan, indent=2))
            _log(logging.INFO, "dry_run_complete", task_id=task.task_id)
            return EXIT_OK
        claude_base = _resolve_base(args.claude_worktree, args.base)
        codex_base = _resolve_base(args.codex_worktree, args.base)
        _log(logging.INFO, "running_claude_side", n_cmds=len(task.test_commands),
             base=claude_base)
        c_runs = run_test_commands(task.test_commands, args.claude_worktree, args.per_timeout)
        c_axes = score_side(args.claude_worktree, c_runs, base=claude_base)
        _log(logging.INFO, "running_codex_side", n_cmds=len(task.test_commands),
             base=codex_base)
        k_runs = run_test_commands(task.test_commands, args.codex_worktree, args.per_timeout)
        k_axes = score_side(args.codex_worktree, k_runs, base=codex_base)
        verdict = build_verdict(task.task_id, c_axes, k_axes, tie_delta=args.tie_delta)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(verdict, indent=2, ensure_ascii=False), encoding="utf-8")
        _log(logging.INFO, "verdict_written", path=str(output),
             winner=verdict["winner"], delta=verdict["delta"])
        print(json.dumps({"task_id": verdict["task_id"], "winner": verdict["winner"],
                          "delta": verdict["delta"], "output": str(output)}, indent=2))
        return EXIT_OK
    except Exception:
        logger.exception("judge main failed")
        return EXIT_INFRA


if __name__ == "__main__":
    sys.exit(main())
