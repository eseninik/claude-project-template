"""Extended local validation matrix — NO API CALLS.

Runs loop-driver.py main() against multiple scenarios using a stubbed
run_claude_iteration. Closes remaining gaps from QUARANTINE.md without
spending subscription credits.

Scenarios:
  1. Revert path          — agent writes kept=no lines, plateau fires as expected
  2. Multi-iteration      — 5 kept=yes wins, best_metric progresses monotonically
  3. Guard violation      — stub writes experiments/STOP mid-iteration, driver halts
  4. --resume             — pre-populated journal, driver loads best from kept=yes lines
  5. direction=lower      — baseline has direction=lower, lower metric is "improvement"

Also includes a structure smoke check on one real downstream target
(Legal Bot) to verify the synced skill is loadable.

Run:
    py -3 work/autoresearch-integration/canary_stub_matrix.py
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
from typing import Callable
from unittest.mock import patch


REPO = Path(__file__).resolve().parent.parent.parent
DRIVER_PATH = REPO / ".claude/shared/templates/new-project/.claude/skills/experiment-loop/templates/loop-driver.py"
PROMPT_PATH = REPO / ".claude/shared/templates/new-project/.claude/skills/experiment-loop/templates/iteration-prompt.md"
LEGAL_BOT_SKILL = Path("C:/Bots/Migrator bots/Legal Bot/.claude/skills/experiment-loop")


def load_driver():
    logging.disable(logging.CRITICAL)
    spec = importlib.util.spec_from_file_location(f"loop_driver_{id(DRIVER_PATH)}", DRIVER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def setup_scenario(tmp: Path, baseline: dict, prefill_journal: list[str] | None = None) -> None:
    (tmp / "goal.md").write_text("# Goal: stub scenario\nMode: pure\n", encoding="utf-8")
    (tmp / "iteration-prompt.md").write_text(PROMPT_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    experiments = tmp / "experiments"
    experiments.mkdir()
    (experiments / "baseline.json").write_text(json.dumps(baseline), encoding="utf-8")
    if prefill_journal:
        (experiments / "journal.md").write_text("\n".join(prefill_journal) + "\n", encoding="utf-8")
    subprocess.run(["git", "init", "--quiet"], cwd=tmp, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp, check=True)
    subprocess.run(
        ["git", "-c", "user.name=canary", "-c", "user.email=canary@test", "commit", "-q", "-m", "init"],
        cwd=tmp, check=True,
    )


def run_driver(
    argv: list[str],
    stub: Callable[[str, str, float], int],
    baseline: dict,
    prefill_journal: list[str] | None = None,
) -> dict:
    driver = load_driver()
    tmp_parent = Path(tempfile.mkdtemp(prefix="autoresearch-matrix-"))
    original_cwd = Path.cwd()
    results: dict = {}
    try:
        try:
            setup_scenario(tmp_parent, baseline, prefill_journal)
            os.chdir(tmp_parent)
            sys.argv = argv
            with patch.object(driver, "run_claude_iteration", stub):
                try:
                    rc = driver.main()
                    results["rc"] = rc
                except SystemExit as e:
                    results["rc"] = e.code

            journal = tmp_parent / "experiments" / "journal.md"
            stop = tmp_parent / "experiments" / "STOP"
            results["journal_lines"] = [
                ln for ln in journal.read_text(encoding="utf-8").splitlines() if ln.strip()
            ] if journal.exists() else []
            results["stop_content"] = stop.read_text(encoding="utf-8").strip() if stop.exists() else None
        finally:
            os.chdir(original_cwd)
            logging.shutdown()
    finally:
        shutil.rmtree(tmp_parent, ignore_errors=True)
    return results


# ---- Scenarios ----

def scenario_revert_path() -> tuple[bool, str]:
    """All iterations kept=no. Plateau should fire at window=2."""
    call = {"n": 0}

    def stub(prompt, mode, budget):
        call["n"] += 1
        n = call["n"]
        with Path("experiments/journal.md").open("a", encoding="utf-8") as f:
            f.write(f"iteration={n} metric=0.4 delta=-0.1 kept=no change=revert_{n}\n")
        return 0

    r = run_driver(
        ["loop-driver.py", "--max-iter", "10", "--plateau-window", "2", "--max-budget-usd", "1"],
        stub,
        {"metric": 0.5, "direction": "higher", "significance_threshold": 0.01},
    )
    if r["rc"] != 0:
        return False, f"rc={r['rc']}"
    if len(r["journal_lines"]) != 2:
        return False, f"expected 2 iters (plateau_window=2), got {len(r['journal_lines'])}"
    if not r["stop_content"] or "plateau" not in r["stop_content"].lower():
        return False, f"expected plateau STOP, got {r['stop_content']}"
    return True, f"2 reverts -> plateau STOP fired correctly"


def scenario_multi_iter_wins() -> tuple[bool, str]:
    """5 kept=yes with ascending metrics. Driver should accept all 5, no plateau."""
    call = {"n": 0}

    def stub(prompt, mode, budget):
        call["n"] += 1
        n = call["n"]
        m = 0.6 + 0.05 * n  # 0.65, 0.70, 0.75, 0.80, 0.85
        with Path("experiments/journal.md").open("a", encoding="utf-8") as f:
            f.write(f"iteration={n} metric={m:.2f} delta=+0.05 kept=yes change=win_{n}\n")
        return 0

    r = run_driver(
        ["loop-driver.py", "--max-iter", "5", "--plateau-window", "3", "--max-budget-usd", "1"],
        stub,
        {"metric": 0.5, "direction": "higher", "significance_threshold": 0.01},
    )
    if r["rc"] != 0:
        return False, f"rc={r['rc']}"
    if len(r["journal_lines"]) != 5:
        return False, f"expected 5 wins, got {len(r['journal_lines'])}"
    if r["stop_content"]:
        return False, f"unexpected STOP in win streak: {r['stop_content']}"
    return True, "5 ascending wins accepted, no false plateau"


def scenario_guard_violation() -> tuple[bool, str]:
    """Stub writes STOP mid-iteration (simulates guard failure the agent detected)."""
    call = {"n": 0}

    def stub(prompt, mode, budget):
        call["n"] += 1
        n = call["n"]
        j = Path("experiments/journal.md")
        with j.open("a", encoding="utf-8") as f:
            f.write(f"iteration={n} metric=0.65 delta=+0.15 kept=no change=guard_broke\n")
        if n == 1:
            Path("experiments/STOP").write_text("guard violation: deal_rate dropped below 1.0", encoding="utf-8")
        return 0

    r = run_driver(
        ["loop-driver.py", "--max-iter", "10", "--plateau-window", "5", "--max-budget-usd", "1"],
        stub,
        {"metric": 0.5, "direction": "higher", "significance_threshold": 0.01},
    )
    if r["rc"] != 0:
        return False, f"rc={r['rc']}"
    if len(r["journal_lines"]) != 1:
        return False, f"expected driver to stop after 1 iter (STOP written), got {len(r['journal_lines'])}"
    if not r["stop_content"] or "guard" not in r["stop_content"].lower():
        return False, f"expected guard STOP preserved, got {r['stop_content']}"
    return True, "guard STOP from stub honored, driver halted"


def scenario_resume() -> tuple[bool, str]:
    """Pre-populated journal with one kept=yes. Driver should find best_metric=0.75
    and continue. Resume fix (find_best_kept_metric) validated."""
    call = {"n": 0}

    def stub(prompt, mode, budget):
        call["n"] += 1
        n = call["n"]
        # Append a non-improving iteration (0.7 < 0.75 existing best).
        # Plateau window=1 -> should fire immediately.
        with Path("experiments/journal.md").open("a", encoding="utf-8") as f:
            f.write(f"iteration={n} metric=0.7 delta=-0.05 kept=yes change=resume_iter\n")
        return 0

    prefill = [
        "iteration=1 metric=0.6 delta=+0.1 kept=yes change=early_win",
        "iteration=2 metric=0.75 delta=+0.15 kept=yes change=best_so_far",
        "iteration=3 metric=0.5 delta=-0.25 kept=no change=reverted",
    ]
    r = run_driver(
        ["loop-driver.py", "--max-iter", "3", "--plateau-window", "1", "--max-budget-usd", "1", "--resume"],
        stub,
        {"metric": 0.5, "direction": "higher", "significance_threshold": 0.01},
        prefill_journal=prefill,
    )
    if r["rc"] != 0:
        return False, f"rc={r['rc']}"
    # Journal should have prefill (3 lines) + 1 stub iter = 4 lines
    if len(r["journal_lines"]) != 4:
        return False, f"expected 3 prefill + 1 stub = 4 lines, got {len(r['journal_lines'])}"
    # Plateau should fire because 0.7 does NOT improve on resumed best=0.75
    if not r["stop_content"] or "plateau" not in r["stop_content"].lower():
        return False, f"expected plateau STOP (0.7 < resumed best 0.75), got {r['stop_content']}"
    return True, "resume loaded best=0.75 from journal, plateau fired on 0.7"


def scenario_direction_lower() -> tuple[bool, str]:
    """direction=lower: smaller metric is better. baseline=0.5, stub returns 0.3 (improvement)
    then 0.4 (not improvement vs 0.3)."""
    call = {"n": 0}

    def stub(prompt, mode, budget):
        call["n"] += 1
        n = call["n"]
        m = 0.3 if n == 1 else 0.4  # iter 1 is win vs 0.5; iter 2 is regression vs 0.3
        with Path("experiments/journal.md").open("a", encoding="utf-8") as f:
            f.write(f"iteration={n} metric={m} delta=? kept=yes change=lower_{n}\n")
        return 0

    r = run_driver(
        ["loop-driver.py", "--max-iter", "5", "--plateau-window", "1", "--max-budget-usd", "1"],
        stub,
        {"metric": 0.5, "direction": "lower", "significance_threshold": 0.01},
    )
    if r["rc"] != 0:
        return False, f"rc={r['rc']}"
    # 2 iters should run: iter 1 sets best=0.3, iter 2 at 0.4 is not improvement -> plateau window=1
    if len(r["journal_lines"]) != 2:
        return False, f"expected 2 iters, got {len(r['journal_lines'])}"
    if not r["stop_content"] or "plateau" not in r["stop_content"].lower():
        return False, f"expected plateau STOP (0.4 is not improvement over 0.3 when lower=better), got {r['stop_content']}"
    return True, "direction=lower: 0.3 accepted as best, 0.4 correctly classified as non-improvement"


def scenario_skill_structure_on_bot() -> tuple[bool, str]:
    """Smoke-check the experiment-loop skill synced into Legal Bot: YAML frontmatter valid,
    loop-driver.py py_compile clean, references/ has 5 files, templates/ has 3 files."""
    if not LEGAL_BOT_SKILL.exists():
        return False, f"{LEGAL_BOT_SKILL} not found — sync step did not land"

    skill_md = LEGAL_BOT_SKILL / "SKILL.md"
    refs = LEGAL_BOT_SKILL / "references"
    tpls = LEGAL_BOT_SKILL / "templates"

    if not skill_md.exists():
        return False, "SKILL.md missing in Legal Bot"
    head = skill_md.read_text(encoding="utf-8").splitlines()
    if not head or head[0].strip() != "---":
        return False, "SKILL.md frontmatter does not start with ---"
    # Find closing ---
    try:
        close = next(i for i, ln in enumerate(head[1:], start=1) if ln.strip() == "---")
    except StopIteration:
        return False, "SKILL.md frontmatter has no closing ---"
    fm_keys = [ln.split(":", 1)[0].strip() for ln in head[1:close] if ":" in ln and not ln.startswith(" ")]
    if "name" not in fm_keys:
        return False, f"SKILL.md frontmatter missing 'name' key, got keys: {fm_keys}"

    if not refs.is_dir():
        return False, "references/ missing"
    ref_files = sorted(p.name for p in refs.glob("*.md"))
    expected_refs = ["anti-patterns.md", "fitness-design.md", "modes.md", "plateau-ideation.md", "triage-checklist.md"]
    if ref_files != expected_refs:
        return False, f"references/ contents mismatch: expected {expected_refs}, got {ref_files}"

    if not tpls.is_dir():
        return False, "templates/ missing"
    tpl_files = sorted(p.name for p in tpls.iterdir() if p.is_file())
    expected_tpls = ["goal.md", "iteration-prompt.md", "loop-driver.py"]
    if tpl_files != expected_tpls:
        return False, f"templates/ contents mismatch: expected {expected_tpls}, got {tpl_files}"

    import py_compile
    try:
        py_compile.compile(str(tpls / "loop-driver.py"), doraise=True)
    except py_compile.PyCompileError as e:
        return False, f"loop-driver.py py_compile failed on Legal Bot copy: {e}"

    return True, f"Legal Bot skill structure valid: SKILL.md frontmatter OK, 5 refs + 3 templates, loop-driver.py compiles"


# ---- Runner ----

SCENARIOS = [
    ("revert path (plateau on kept=no streak)", scenario_revert_path),
    ("multi-iteration ascending wins", scenario_multi_iter_wins),
    ("guard violation (stub writes STOP)", scenario_guard_violation),
    ("--resume with trailing revert", scenario_resume),
    ("direction=lower metric comparison", scenario_direction_lower),
    ("Legal Bot skill structure smoke", scenario_skill_structure_on_bot),
]


def main():
    print("=== Autoresearch extended local validation matrix (NO API) ===\n")
    results = []
    for name, fn in SCENARIOS:
        try:
            ok, msg = fn()
        except Exception as e:
            ok, msg = False, f"EXCEPTION: {e}"
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {name}: {msg}")
        results.append((name, ok, msg))

    print()
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"Summary: {passed}/{total} scenarios passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
