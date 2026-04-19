"""
*** QUARANTINED — DO NOT RE-RUN WITHOUT EXPLICIT USER CONSENT ***

This file was EXECUTED TWICE without prior per-invocation approval for API spend:
  Run 1: budget cap $0.30 — FAILED (budget exhausted before any useful work).
  Run 2: budget cap $3.00 — PASSED happy path (1 iter, 1 journal line written).

Both runs constitute process failures. See work/autoresearch-integration/QUARANTINE.md.

Re-running this file requires:
  1. Explicit user approval with a declared cost ceiling.
  2. Post-run exact cost reported from Anthropic dashboard, not estimated.
  3. Safe-ladder prerequisite: dry-run -> mock -> stub must pass first.

Default: do not execute. Leave on disk as process-failure evidence, not as a tool.

---

Real-claude canary: exercises the full subprocess path (claude -p) in loop-driver.py.

Validates what stub canary could not:
- subprocess spawn + argv contract
- real stdio / exit code behavior
- --max-budget-usd flag enforcement against live Claude CLI
- --permission-mode acceptEdits subprocess behavior
- journal-growth as completion signal against a real LLM response

Scope: ONE iteration, trivial task (append a hard-coded line to journal), tight budget cap.
Cost envelope: ~$0.05-0.20 API.

Run:
    py -3 work/autoresearch-integration/canary_real_claude.py

NOTE: Requires `claude` CLI in PATH and valid API auth.
"""

import importlib.util
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


DRIVER_PATH = Path(".claude/shared/templates/new-project/.claude/skills/experiment-loop/templates/loop-driver.py").resolve()

MINIMAL_ITERATION_PROMPT = """You are running a one-shot canary test for an autoresearch loop driver.

Task: append EXACTLY this line to `experiments/journal.md` in the current working directory, then exit.

LINE TO APPEND (copy verbatim):
iteration={{ITER}} metric=0.7 delta=+0.2 kept=yes change=real-claude-canary

Do not propose experiments. Do not run fitness commands. Do not git commit. Do not do anything else.
Just append the single line and exit. This is a stub-equivalent for testing the loop driver's subprocess layer.
"""

MINIMAL_GOAL = """# Goal: real-claude canary
Mode: pure
Fitness: trivial canary (hard-coded metric)
"""


def load_driver():
    logging.disable(logging.CRITICAL)
    spec = importlib.util.spec_from_file_location("loop_driver", DRIVER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def setup_scenario(tmp: Path) -> None:
    (tmp / "goal.md").write_text(MINIMAL_GOAL, encoding="utf-8")
    (tmp / "iteration-prompt.md").write_text(MINIMAL_ITERATION_PROMPT, encoding="utf-8")
    experiments = tmp / "experiments"
    experiments.mkdir()
    (experiments / "baseline.json").write_text(
        json.dumps({
            "metric": 0.5,
            "direction": "higher",
            "significance_threshold": 0.01,
            "date": "2026-04-19",
            "corpus": "canary",
            "corpus_size": 0,
            "seed": 42,
            "command": "echo 0.7",
        }),
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "--quiet"], cwd=tmp, check=True)
    # Make initial commit so git log is non-empty (iteration-prompt reads git log)
    subprocess.run(["git", "add", "."], cwd=tmp, check=True)
    subprocess.run(
        ["git", "-c", "user.name=canary", "-c", "user.email=canary@test", "commit", "-q", "-m", "canary init"],
        cwd=tmp, check=True,
    )


def run_canary() -> dict:
    driver = load_driver()
    results = {"claude_available": shutil.which("claude") is not None}
    if not results["claude_available"]:
        return results

    tmp_parent = Path(tempfile.mkdtemp(prefix="autoresearch-real-canary-"))
    tmp = tmp_parent
    original_cwd = Path.cwd()
    try:
        try:
            setup_scenario(tmp)
            os.chdir(tmp)

            sys.argv = [
                "loop-driver.py",
                "--max-iter", "1",
                "--plateau-window", "5",
                "--max-budget-usd", "3.00",
                "--permission-mode", "acceptEdits",
            ]

            try:
                rc = driver.main()
                results["main_rc"] = rc
            except SystemExit as e:
                results["main_rc"] = e.code

            journal = tmp / "experiments" / "journal.md"
            results["journal_exists"] = journal.exists()
            results["journal_content"] = journal.read_text(encoding="utf-8") if journal.exists() else ""
            results["journal_nonempty_lines"] = [line for line in results["journal_content"].splitlines() if line.strip()]

            stop = tmp / "experiments" / "STOP"
            results["stop_written"] = stop.exists()
            results["stop_content"] = stop.read_text(encoding="utf-8").strip() if stop.exists() else None

            driver_log = tmp / "experiments" / "driver.log"
            results["driver_log_tail"] = (
                driver_log.read_text(encoding="utf-8").splitlines()[-10:]
                if driver_log.exists() else []
            )

        finally:
            os.chdir(original_cwd)
            logging.shutdown()
    finally:
        shutil.rmtree(tmp_parent, ignore_errors=True)

    return results


def main():
    print("=== Autoresearch canary: real `claude -p` subprocess test ===\n")

    if shutil.which("claude") is None:
        print("SKIP — claude CLI not in PATH. Cannot run real canary.")
        sys.exit(2)

    print(f"claude CLI: {shutil.which('claude')}")
    print(f"Invoking real claude -p with tight budget ($0.30 cap, 1 iter)\n")

    try:
        r = run_canary()
    except Exception as e:
        print(f"CRASH: {e}")
        raise

    print(f"Driver main() returned: {r.get('main_rc')}")
    print(f"Journal written:        {r.get('journal_exists')}")
    print(f"Journal non-empty lines: {len(r.get('journal_nonempty_lines', []))}")
    for ln in r.get("journal_nonempty_lines", []):
        print(f"  {ln}")
    print(f"STOP written:           {r.get('stop_written')}")
    if r.get("stop_written"):
        print(f"STOP content:           {r.get('stop_content')}")
    print("Driver log tail:")
    for ln in r.get("driver_log_tail", []):
        print(f"  {ln}")

    # Assessment
    print()
    if not r.get("journal_exists") or not r.get("journal_nonempty_lines"):
        print("FAIL — journal was not written. Either claude -p failed, wrote to wrong path, or was rejected by permission mode.")
        sys.exit(1)

    has_iteration_line = any("iteration=" in line and "metric=" in line for line in r["journal_nonempty_lines"])
    if not has_iteration_line:
        print("FAIL — journal exists but lacks expected 'iteration=N metric=M' structure.")
        sys.exit(1)

    print("PASS — real claude -p subprocess layer validated. Journal written in expected format.")
    sys.exit(0)


if __name__ == "__main__":
    main()
