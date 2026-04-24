---
executor: dual
risk_class: routine
speed_profile: thorough
---

# Task T5: `.claude/scripts/judge.py` — test-driven objective judge

## Your Task

Retry from previous session (was blocked by background-agent Write permission).

Create a CLI scorer that reads two diffs (claude + codex) against a task spec and two worktrees, runs all Test Commands from the spec against each side, scores on objective axes, emits structured verdict JSON declaring `winner ∈ {"claude", "codex", "tie"}`.

**Strategy to avoid prior Write-denial**: split into TWO files up front.
- `judge_axes.py` — pure scoring functions per axis (~350 lines)
- `judge.py` — main CLI + orchestration + JSON emission (~250 lines)
- `test_judge.py` — unit tests (~400 lines)

Three smaller files each pass Write fine; one 750-line file does not.

## Scope Fence

**Allowed:**
- `.claude/scripts/judge_axes.py` (new, pure scoring logic)
- `.claude/scripts/judge.py` (new, CLI + orchestration, imports judge_axes)
- `.claude/scripts/test_judge.py` (new, tests)

**Forbidden:**
- Any other path

## Test Commands

```bash
python .claude/scripts/test_judge.py
python .claude/scripts/judge.py --help
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: CLI `judge.py --task <task-N.md> --claude-worktree <path> --codex-worktree <path> [--output <result.json>] [--dry-run]`
- [ ] AC2: Parses task-N.md for Test Commands + acceptance criteria (reuse parser from codex-implement.py if possible via importlib; else local parse)
- [ ] AC3: For EACH side, run every Test Command in that side's worktree; capture exit code, stdout tail (last 20 lines), duration, pass/fail.
- [ ] AC4: Axis scoring (in `judge_axes.py`):
  - `tests_passed` (weight 10): fraction of Test Commands that exited 0
  - `diff_size` (weight 2): inverse-normalized added-lines count from `git diff` vs base; smaller = higher score
  - `logging_coverage` (weight 3): for every NEW Python function (`def ` at col 0 in added lines of `.py`), check next 5 lines for a `logger.` call; fraction covered
  - `lint_clean` (weight 2): run `python -m py_compile` on each modified `.py`; also `python -m pyflakes` if available; error count inverse
  - `complexity` (weight 1, optional): if `radon` importable, compute cyclomatic complexity delta; lower is better
  - `type_check` (weight 2, optional): if `mypy` importable AND project has mypy config, run on modified files; errors inverse
- [ ] AC4a: Missing optional tools (radon/pyflakes/mypy) → skip that axis, log the skip with `axis_skipped` event. Don't fail.
- [ ] AC5: Weighted aggregate per side = `sum(weight_i * score_i) / sum(weight_i_used)`
- [ ] AC6: Verdict: `winner = "claude"` if aggregate delta ≥ 0.02, `"codex"` if reverse, else `"tie"`. Tie-delta tunable via `--tie-delta` flag (default 0.02).
- [ ] AC7: Output JSON (default path: `work/codex-primary/dual-history/<task-id>/judge-verdict.json`):
  ```json
  {
    "task_id": "<id>",
    "timestamp": "<iso>",
    "winner": "claude" | "codex" | "tie",
    "delta": 0.xx,
    "scores": {
      "claude": {"aggregate": x, "axes": {...}},
      "codex":  {"aggregate": x, "axes": {...}}
    },
    "rationale_auto": "<short string citing biggest-delta axis>",
    "rationale_manual": null
  }
  ```
- [ ] AC8: Exit 0 on valid run regardless of winner; exit 1 on infra failure (missing task / worktree / unparseable diff).
- [ ] AC9: Unit tests (≥10):
  - tests_passed all/some/none
  - diff_size inverse normalization
  - logging_coverage — function with logger / without / edge
  - lint_clean — clean / syntax-error / pyflakes warnings
  - optional tool skip (pyflakes absent → logged, no axis)
  - weighted aggregation correctness
  - tie detection within delta
  - verdict JSON schema valid json.loads
  - `--dry-run` / `--help` behavior
  - malformed task file → exit 1 clean
- [ ] AC10: Structured logging per AGENTS.md
- [ ] AC11: Sizes: `judge_axes.py` < 400 lines, `judge.py` < 300 lines, `test_judge.py` < 450 lines
- [ ] All Test Commands exit 0.

## Constraints

- Windows-compatible
- Stdlib preferred; detect optional tools via `shutil.which` + `importlib.util.find_spec`
- JSON output must be valid `json.loads`-able
- Scoring deterministic: same inputs → same verdict

## Handoff Output

Standard `=== PHASE HANDOFF: T5-judge ===` block. Include sample verdict JSON for a synthetic pair.

## Iteration History

**Round 1** (previous session, 2026-04-24):
- Blocked by background-agent Write permission on single 750-line judge.py.
- Design was complete (6-axis scoring, weighted aggregate, tie detection, JSON schema).
- THIS round: split into 3 smaller files (judge_axes / judge / test_judge) to stay under the Write-permission threshold.
