"""Canary test: run loop-driver.py end-to-end with a stubbed run_claude_iteration.

Validates the driver's full control flow (argparse -> preconditions -> loop ->
plateau detection -> STOP writing -> termination) WITHOUT burning claude API budget.

What this tests that the unit tests did NOT:
- main() flow start-to-finish
- argparse + Path defaults
- check_preconditions() against a real temp scenario (goal/prompt/baseline/git)
- plateau counter incrementing correctly across iterations
- STOP file content after plateau
- best_metric initialization from baseline
- journal-growth detection

What this does NOT test:
- Real `claude -p` subprocess behavior (would require API budget)
- Guard violation path (no guard metric in scenario)
- --resume branch (separate scenario needed)

Run:
    py -3 work/autoresearch-integration/canary_stub_driver.py
"""

import importlib.util
import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


DRIVER_PATH = Path(".claude/shared/templates/new-project/.claude/skills/experiment-loop/templates/loop-driver.py").resolve()
SKILL_DIR = DRIVER_PATH.parent.parent  # experiment-loop/
PROMPT_SRC = SKILL_DIR / "templates" / "iteration-prompt.md"
GOAL_SRC = SKILL_DIR / "templates" / "goal.md"


def load_driver():
    logging.disable(logging.CRITICAL)
    spec = importlib.util.spec_from_file_location("loop_driver", DRIVER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def setup_scenario(tmp: Path) -> None:
    """Write goal.md, iteration-prompt.md, experiments/baseline.json; init git."""
    (tmp / "goal.md").write_text(
        "# Goal: stub canary\nMode: pure\nFitness: stub returns fixed value\n",
        encoding="utf-8",
    )
    (tmp / "iteration-prompt.md").write_text(
        PROMPT_SRC.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    experiments = tmp / "experiments"
    experiments.mkdir()
    (experiments / "baseline.json").write_text(
        json.dumps({
            "metric": 0.5,
            "direction": "higher",
            "significance_threshold": 0.01,
            "date": "2026-04-19",
            "corpus": "stub",
            "corpus_size": 0,
            "seed": 42,
            "command": "stub",
        }),
        encoding="utf-8",
    )
    # Real git init — check_preconditions requires .git/
    subprocess.run(["git", "init", "--quiet"], cwd=tmp, check=True)


def run_canary() -> dict:
    """Run loop-driver main() with stubbed run_claude_iteration. Return assertions."""
    driver = load_driver()
    results = {}

    tmp_parent = Path(tempfile.mkdtemp(prefix="autoresearch-canary-"))
    tmp = tmp_parent
    original_cwd = Path.cwd()
    try:
        try:
            setup_scenario(tmp)
            os.chdir(tmp)

            # Stub: first iteration is a clear win (0.7 > 0.5 baseline), rest are noise.
            # With plateau_window=1, plateau should fire on iteration 2.
            iteration_counter = {"n": 0}

            def fake_claude(prompt_text: str, mode: str, budget: float) -> int:
                iteration_counter["n"] += 1
                n = iteration_counter["n"]
                metric, kept = (0.7, "yes") if n == 1 else (0.5, "no")
                journal = Path("experiments") / "journal.md"
                with journal.open("a", encoding="utf-8") as f:
                    f.write(f"iteration={n} metric={metric} delta=0.0 kept={kept} change=stub_iter_{n}\n")
                return 0

            # Simulate CLI invocation
            sys.argv = [
                "loop-driver.py",
                "--max-iter", "10",
                "--plateau-window", "1",
                "--max-budget-usd", "1.0",
                "--permission-mode", "acceptEdits",
            ]

            with patch.object(driver, "run_claude_iteration", fake_claude):
                try:
                    driver.main()
                except SystemExit as e:
                    results["main_exit_code"] = e.code

            results["iterations_run"] = iteration_counter["n"]
            results["journal_lines"] = (tmp / "experiments" / "journal.md").read_text(encoding="utf-8").splitlines()
            stop_path = tmp / "experiments" / "STOP"
            results["stop_written"] = stop_path.exists()
            results["stop_content"] = stop_path.read_text(encoding="utf-8").strip() if stop_path.exists() else None
            results["driver_log_tail"] = (tmp / "experiments" / "driver.log").read_text(encoding="utf-8").splitlines()[-5:]

        finally:
            os.chdir(original_cwd)
            # Release Windows file lock on driver.log before tempdir cleanup.
            logging.shutdown()
    finally:
        import shutil
        shutil.rmtree(tmp_parent, ignore_errors=True)

    return results


def assert_canary_pass(r: dict) -> list[str]:
    """Return list of assertion failures. Empty list = all pass."""
    failures = []

    # Expected: 2 iterations (first keep, second reverted triggers plateau window=1)
    if r["iterations_run"] != 2:
        failures.append(f"expected 2 iterations, got {r['iterations_run']}")

    # Journal should have 2 lines
    if len(r["journal_lines"]) != 2:
        failures.append(f"expected 2 journal lines, got {len(r['journal_lines'])}: {r['journal_lines']}")

    # Line 1: kept=yes, metric=0.7
    if len(r["journal_lines"]) >= 1:
        l1 = r["journal_lines"][0]
        if "kept=yes" not in l1 or "metric=0.7" not in l1:
            failures.append(f"iteration 1 expected kept=yes metric=0.7, got: {l1}")

    # Line 2: kept=no (reverted)
    if len(r["journal_lines"]) >= 2:
        l2 = r["journal_lines"][1]
        if "kept=no" not in l2:
            failures.append(f"iteration 2 expected kept=no, got: {l2}")

    # STOP file must exist with plateau content
    if not r["stop_written"]:
        failures.append("STOP file was not written")
    elif "plateau" not in (r["stop_content"] or "").lower():
        failures.append(f"STOP content expected 'plateau...', got: {r['stop_content']}")

    return failures


def main():
    print("=== Autoresearch canary: stub-claude driver test ===\n")
    results = run_canary()
    failures = assert_canary_pass(results)

    print(f"Iterations run:   {results['iterations_run']}")
    print(f"Journal lines:    {len(results['journal_lines'])}")
    for ln in results["journal_lines"]:
        print(f"  {ln}")
    print(f"STOP written:     {results['stop_written']}")
    print(f"STOP content:     {results['stop_content']}")
    print(f"Driver log tail:")
    for ln in results["driver_log_tail"]:
        print(f"  {ln}")
    print()

    if failures:
        print("FAIL:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("PASS — driver control flow validated end-to-end (stub claude)")
        sys.exit(0)


if __name__ == "__main__":
    main()
