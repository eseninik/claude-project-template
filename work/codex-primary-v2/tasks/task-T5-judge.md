---
executor: dual
risk_class: routine
speed_profile: thorough
---

# Task T5: `.claude/scripts/judge.py` — test-driven objective judge

## Your Task

Create a CLI scorer that reads two diffs (claude + codex) against a task spec and a pair of worktrees, runs all Test Commands from the spec against EACH diff applied in its worktree, scores on objective axes, and emits a structured verdict JSON declaring a winner (or `tie`).

This is the **objectivization** of the judge step — replaces Opus's subjective compare on routine tasks. Opus can still override the verdict, but the default is test-driven.

## Scope Fence

**Allowed paths:**
- `.claude/scripts/judge.py` (new)
- `.claude/scripts/test_judge.py` (new — unit tests)

**Forbidden:**
- All other paths

## Test Commands

```bash
python .claude/scripts/test_judge.py
python .claude/scripts/judge.py --help
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: CLI `judge.py --task <task-N.md> --claude-worktree <path> --codex-worktree <path> [--output <result.json>]`
- [ ] AC2: Parses task-N.md for Test Commands + expected Acceptance Criteria (reuses parser from codex-implement.py if possible; else local parse)
- [ ] AC3: For EACH side (claude, codex), runs every Test Command in that side's worktree; records: exit code, stdout tail (last 20 lines), duration, pass/fail
- [ ] AC4: Objective scoring axes (each returns numeric score or binary):
  - **tests_passed** (weight 10): fraction of Test Commands that exited 0
  - **diff_size** (weight 2): prefer smaller diff — compute added-lines count from `git diff` of each worktree vs base; smaller = higher score (inverse normalized)
  - **logging_coverage** (weight 3): for every NEW function (`def ` at col 0 in added lines of Python files), check if next 5 lines contain a `logger.` call; fraction covered
  - **lint_clean** (weight 2): run `python -m py_compile` on each modified `.py` file; also `python -m pyflakes` if available; count errors (inverse)
  - **complexity** (weight 1, optional): if `radon` available, compute cyclomatic complexity of added code; lower is better
  - **type_check** (weight 2, optional): if `mypy` available AND project has mypy config, run type check on modified files; errors inverse
- [ ] AC4a: Missing optional tools (radon, pyflakes, mypy) → skip that axis, log the skip, don't fail
- [ ] AC5: Weighted aggregate score per side = sum(weight_i * score_i) / sum(weight_i)
- [ ] AC6: Verdict: winner = side with higher aggregate; tie if within `0.02` delta (documented as tunable)
- [ ] AC7: Writes JSON to `--output` (default: `work/codex-primary/dual-history/<task-id>/judge-verdict.json`):
  ```json
  {
    "task_id": "<id>",
    "timestamp": "<iso>",
    "winner": "claude" | "codex" | "tie",
    "delta": 0.xx,
    "scores": { "claude": {"aggregate": x, "axes": {...}}, "codex": {...} },
    "rationale_auto": "<short string citing biggest-delta axis>",
    "rationale_manual": null
  }
  ```
- [ ] AC8: Exit 0 regardless of winner (Opus reads JSON and acts); exit 1 only on infra failure
- [ ] AC9: Unit tests (≥ 10):
  - tests_passed axis scoring (all pass / some pass / none pass)
  - diff_size normalization
  - logging_coverage: function with logger / without / edge cases
  - lint_clean: clean / syntax error / pyflakes warnings
  - optional tool skip (pyflakes absent → logged, no axis)
  - weighted aggregation correctness
  - tie detection within delta
  - verdict JSON schema
  - --dry-run / --help behavior
  - malformed task file → clean error, exit 1
- [ ] AC10: Structured logging per AGENTS.md
- [ ] AC11: Under 500 lines + 500 tests
- [ ] All Test Commands exit 0

## Constraints

- Windows-compatible
- Stdlib preferred; optional third-party tools detected via `shutil.which` + `importlib.util.find_spec`
- JSON output must be valid json.loads-able
- Scoring algorithm must be deterministic (same inputs → same verdict)

## Handoff Output

Standard `=== PHASE HANDOFF: T5-judge ===` block. Include sample verdict JSON for a synthetic pair in the handoff.

## Iteration History
(First round.)
