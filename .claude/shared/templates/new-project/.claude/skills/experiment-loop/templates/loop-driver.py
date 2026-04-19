#!/usr/bin/env python3
"""
loop-driver.py — autoresearch loop driver (cross-platform Python).

Runs `claude -p` (non-interactive) in a bounded loop until ANY of:
  - max iterations reached (hard cap)
  - dollar budget exhausted (claude -p --max-budget-usd)
  - plateau detected (N iterations without significance-threshold improvement)
  - guard violation (loop writes experiments/STOP)
  - manual interrupt (Ctrl+C)

Adapted from Bayram Annakov's MIT-licensed loop-driver.sh.
Key changes from source:
- Python instead of bash (cross-platform, structured logging, better error handling)
- Default permission mode: acceptEdits (not bypassPermissions) for auditability
- Direction-aware plateau tracking (higher/lower is better, from baseline.json)
- Structured logging to experiments/driver.log
- Graceful SIGINT handling
- Resume capability: --resume reads last best metric and continues

Usage (cross-platform):
    python loop-driver.py [--max-iter N] [--max-budget-usd X] [--plateau-window N]
                          [--goal goal.md] [--prompt iteration-prompt.md]
                          [--permission-mode acceptEdits|bypassPermissions] [--resume]

On Windows, invoke via the Python launcher: `py -3 loop-driver.py ...`

Reads:  goal.md, experiments/journal.md, experiments/baseline.json, iteration-prompt.md
Writes: experiments/journal.md (appends by the agent), experiments/STOP (on termination), experiments/driver.log
Commits: one git commit per iteration (from claude -p inside the iteration)
"""

import argparse
import json
import logging
import re
import shutil
import signal
import subprocess
import sys
from pathlib import Path
from typing import Optional


LOG = logging.getLogger("loop-driver")


def setup_logging(experiments_dir: Path) -> None:
    """Console + file logging. Called once at startup after dir is created."""
    experiments_dir.mkdir(parents=True, exist_ok=True)
    log_file = experiments_dir / "driver.log"

    fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ]
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers)


def check_preconditions(goal: Path, prompt: Path, baseline: Path, git_dir: Path) -> None:
    """Verify required files and environment. Exits with rc=1 on any missing."""
    LOG.info("check_preconditions goal=%s prompt=%s baseline=%s", goal, prompt, baseline)

    errors = []
    if not goal.exists():
        errors.append(f"{goal} not found. Complete Stages 1-4 first.")
    if not prompt.exists():
        errors.append(f"{prompt} not found. Copy templates/iteration-prompt.md here.")
    if not baseline.exists():
        errors.append(f"{baseline} not found. Record baseline in Stage 3.")
    if not git_dir.exists():
        errors.append("Not a git repo. Autoresearch uses git as experiment memory.")
    if shutil.which("claude") is None:
        errors.append("claude CLI not found in PATH.")

    if errors:
        for e in errors:
            LOG.error("precondition: %s", e)
        sys.exit(1)

    LOG.info("preconditions OK")


def load_baseline(baseline: Path) -> dict:
    """Parse baseline.json. Expects at minimum: metric, direction, significance_threshold."""
    data = json.loads(baseline.read_text(encoding="utf-8"))
    LOG.info(
        "baseline loaded metric=%s direction=%s threshold=%s",
        data.get("metric"),
        data.get("direction", "higher"),
        data.get("significance_threshold"),
    )
    return data


def read_journal_lines(journal: Path) -> int:
    """Return number of non-empty lines in journal; 0 if missing."""
    if not journal.exists():
        return 0
    with journal.open(encoding="utf-8", errors="ignore") as f:
        return sum(1 for line in f if line.strip())


def parse_last_metric(journal: Path) -> tuple[Optional[float], Optional[str]]:
    """Extract metric and kept flag from the last non-empty line of journal."""
    if not journal.exists():
        return None, None
    with journal.open(encoding="utf-8", errors="ignore") as f:
        lines = [line for line in f.readlines() if line.strip()]
    if not lines:
        return None, None
    last = lines[-1]
    metric_m = re.search(r"metric=([0-9.+\-eE]+)", last)
    kept_m = re.search(r"kept=(\w+)", last)
    metric = float(metric_m.group(1)) if metric_m else None
    kept = kept_m.group(1) if kept_m else None
    LOG.debug("parsed last journal line: metric=%s kept=%s", metric, kept)
    return metric, kept


def find_best_kept_metric(journal: Path, direction: str) -> Optional[float]:
    """Scan journal for the best metric among kept=yes lines (direction-aware).
    Used for --resume so that a trailing reverted iteration does not erase the incumbent."""
    if not journal.exists():
        return None
    best: Optional[float] = None
    with journal.open(encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "kept=yes" not in line:
                continue
            m = re.search(r"metric=([0-9.+\-eE]+)", line)
            if not m:
                continue
            value = float(m.group(1))
            if best is None or (direction == "lower" and value < best) or (direction != "lower" and value > best):
                best = value
    LOG.info("find_best_kept_metric scanned journal direction=%s best=%s", direction, best)
    return best


def is_improvement(new: float, old: Optional[float], direction: str) -> bool:
    """Direction-aware comparison. None old means always an improvement."""
    if old is None:
        return True
    if direction == "lower":
        return new < old
    return new > old


def substitute_prompt(template: str, iteration: int, max_iter: int) -> str:
    """Replace {{ITER}} and {{MAX_ITER}} placeholders."""
    return template.replace("{{ITER}}", str(iteration)).replace("{{MAX_ITER}}", str(max_iter))


def run_claude_iteration(
    prompt_text: str,
    permission_mode: str,
    max_budget_usd: float,
) -> int:
    """Invoke `claude -p` for one iteration. Returns its exit code (advisory only —
    journal growth is the authoritative completion signal because `claude -p` exits 0
    on budget exhaustion too)."""
    cmd = [
        "claude", "-p",
        "--permission-mode", permission_mode,
        "--max-budget-usd", str(max_budget_usd),
        "--output-format", "text",
        prompt_text,
    ]
    LOG.info("run_claude_iteration permission_mode=%s budget=%s", permission_mode, max_budget_usd)
    try:
        result = subprocess.run(cmd, check=False)
        LOG.info("claude returned rc=%s (advisory — journal growth is the real signal)", result.returncode)
        return result.returncode
    except (subprocess.SubprocessError, OSError) as e:
        LOG.exception("claude invocation failed: %s", e)
        return -1


def write_stop(stop_file: Path, reason: str) -> None:
    """Write STOP file with reason. Idempotent: overwrites prior content."""
    stop_file.write_text(reason + "\n", encoding="utf-8")
    LOG.warning("STOP written: %s", reason)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Autoresearch loop driver (Python, cross-platform)",
    )
    parser.add_argument("--max-iter", type=int, default=50,
                        help="Hard iteration cap (default 50)")
    parser.add_argument("--max-budget-usd", type=float, default=10.0,
                        help="Dollar cap passed to claude -p (default 10.0)")
    parser.add_argument("--plateau-window", type=int, default=10,
                        help="Iterations without kept improvement before stopping (default 10)")
    parser.add_argument("--goal", type=Path, default=Path("goal.md"))
    parser.add_argument("--prompt", type=Path, default=Path("iteration-prompt.md"))
    parser.add_argument(
        "--permission-mode",
        choices=["acceptEdits", "bypassPermissions"],
        default="acceptEdits",
        help="claude -p permission mode. acceptEdits (default) is safer and auditable; "
             "bypassPermissions is for truly unattended overnight runs — expects narrow Bash whitelist in project settings.json.",
    )
    parser.add_argument("--resume", action="store_true",
                        help="Continue from existing journal state; do not clear STOP file")
    return parser.parse_args()


def install_sigint_handler(stop_file: Path) -> None:
    """Graceful Ctrl+C: write STOP and exit at next loop boundary."""
    def _sigint(_signum, _frame):
        LOG.warning("SIGINT received — writing STOP and exiting at next boundary")
        write_stop(stop_file, "manual interrupt via SIGINT")
        sys.exit(130)
    signal.signal(signal.SIGINT, _sigint)


def main() -> int:
    args = parse_args()

    experiments = Path("experiments")
    setup_logging(experiments)

    LOG.info(
        "startup max_iter=%s budget=%s window=%s permission_mode=%s resume=%s",
        args.max_iter, args.max_budget_usd, args.plateau_window,
        args.permission_mode, args.resume,
    )

    baseline = experiments / "baseline.json"
    journal = experiments / "journal.md"
    stop_file = experiments / "STOP"
    git_dir = Path(".git")

    check_preconditions(args.goal, args.prompt, baseline, git_dir)
    baseline_data = load_baseline(baseline)
    direction = baseline_data.get("direction", "higher")

    if not args.resume and stop_file.exists():
        stop_file.unlink()
        LOG.info("cleared stale STOP file")
    journal.touch()

    prompt_template = args.prompt.read_text(encoding="utf-8")

    best_metric: Optional[float] = None
    plateau_count = 0

    if args.resume:
        # Scan entire journal for best kept metric (trailing revert must not erase the incumbent).
        # Fallback to baseline if no kept line has ever been written.
        best_metric = find_best_kept_metric(journal, direction)
        if best_metric is None and "metric" in baseline_data:
            best_metric = float(baseline_data["metric"])
            LOG.info("resume: no kept iterations in journal, using baseline as best_metric=%s", best_metric)
        else:
            LOG.info("resume: best_metric from journal=%s", best_metric)
    elif "metric" in baseline_data:
        best_metric = float(baseline_data["metric"])
        LOG.info("baseline metric as starting best: %s", best_metric)

    install_sigint_handler(stop_file)

    iteration = 0
    while iteration < args.max_iter:
        iteration += 1
        LOG.info("=== iteration %s/%s ===", iteration, args.max_iter)

        prompt_text = substitute_prompt(prompt_template, iteration, args.max_iter)
        before_lines = read_journal_lines(journal)

        run_claude_iteration(prompt_text, args.permission_mode, args.max_budget_usd)

        if stop_file.exists():
            reason = stop_file.read_text(encoding="utf-8").strip()
            LOG.info("STOP signal detected: %s", reason)
            break

        after_lines = read_journal_lines(journal)
        if after_lines <= before_lines:
            write_stop(
                stop_file,
                f"iteration {iteration} did not update journal.md - budget exhausted, error, or agent failure",
            )
            break

        last_metric, last_kept = parse_last_metric(journal)
        if last_metric is None:
            LOG.warning("could not parse metric from last journal line; counting toward plateau")
            plateau_count += 1
        elif last_kept == "yes" and is_improvement(last_metric, best_metric, direction):
            LOG.info("new best metric: %s (was %s, direction=%s)", last_metric, best_metric, direction)
            best_metric = last_metric
            plateau_count = 0
        else:
            plateau_count += 1

        LOG.info("plateau_count=%s/%s best=%s", plateau_count, args.plateau_window, best_metric)

        if plateau_count >= args.plateau_window:
            write_stop(
                stop_file,
                f"plateau: {args.plateau_window} iterations without a kept improvement - "
                "change the search space (see anti-pattern #13 and plateau-ideation.md)",
            )
            break

    LOG.info("=== loop terminated after %s iterations ===", iteration)
    LOG.info(
        "best metric: %s (direction=%s)",
        best_metric if best_metric is not None else "unknown",
        direction,
    )
    LOG.info(
        "next: run Stage 6 post-mortem - review experiments/journal.md, read experiments/STOP, "
        "produce plateau diagnosis per SKILL.md Stage 6"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
