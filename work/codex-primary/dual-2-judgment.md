# Dual-2 Judgment — Level 3 Real Compare

**Date:** 2026-04-24
**Task:** `task-dual-2.md` — add `--sort-by {name,lines}` flag to `.claude/scripts/list_codex_scripts.py`
**Both sides finished with valid diffs.** Unlike dual-1 (where Codex's diff was destroyed), this run exercised the full judge step against two passing implementations.

## Inputs compared

### Claude side (branch `claude/task-dual-2`, commit `f692384`)
- Diff: +36 / -2, 132 lines total (cap 140)
- All 6 Test Commands PASS, including strict programmatic asserts (lines-desc ok, name-asc ok)
- AC4 extra-checked: `--sort-by bogus` → argparse exit 2

### Codex-GPT-5.5 side (branch `codex/task-dual-2`, commit base — uncommitted in worktree)
- Diff: +~25 / -2, ~124 lines total
- codex-implement.py reports: status=pass, scope_status=pass, tests_all_passed=True, codex_returncode=0
- result.md has full diff + test output preserved (Bug #8 fix working)

## Axis-by-axis comparison

| Axis | Claude | Codex-5.5 | Winner |
|------|--------|-----------|--------|
| Correctness | Tests pass, sort key `(-line_count, name)` | Tests pass, same sort key | TIE |
| Preserves dual-1 `--json` | Yes | Yes | TIE |
| Scope Fence adherence | Exactly `list_codex_scripts.py` | Exactly `list_codex_scripts.py` | TIE |
| Docstring update (AC8) | 4-line paragraph explaining modes + AC7 invariant | 1-line mention | **Claude** (richer) |
| Module constants consistency | `SORT_CHOICES` mirrors `SCRIPT_PATTERN` | Inlined | **Claude** (style match) |
| Helper function for sort | `sort_entries()` with entry/exit logs | Inlined in main() | **Claude** (logging-standards compliance) |
| Diff footprint | +36 lines | +~25 lines | **Codex** (more compact) |
| Sort method | `sorted()` functional | `.sort()` in-place | TIE (both idiomatic) |
| Extensibility (future sort modes) | Drop in new case in helper | Inline `if/else` needs edit | **Claude** (marginally) |
| Risk surface | Slightly larger diff | Smaller diff | **Codex** |

## Verdict: **Claude** (by narrow margin)

**Why Claude:**
1. **Logging-standards fully satisfied.** `sort_entries()` is a new function, so per the standard it needs structured entry/exit logs — Claude provided them. Codex inlined the sort, which sidesteps the "every new function" rule technically but leaves no trace in the operational log when sort mode switches.
2. **Style consistency.** Existing file has `SCRIPT_PATTERN` as a module constant. Claude added `SORT_CHOICES` the same way. Codex inlined it — diverges from local convention.
3. **Docstring quality.** AC8 required "updated to mention the new flag". Claude went beyond mention, explaining the tie-break contract and the AC7 invariant. Codex met the letter of AC8 with one line. Richer contract documentation pays dividends at read-time.

**Why not Codex:**
- Equivalent correctness, so correctness is NOT the deciding factor.
- Smaller diff is genuinely virtuous, but not enough to overcome the three points above.

**Hybrid considered, rejected:**
We could cherry-pick Claude's `SORT_CHOICES` + `sort_entries()` and combine with Codex's compact docstring. Marginal net benefit, not worth the merge complexity. Claude's version is coherent as-is.

## What this Level 3 run proved

Unlike dual-1 (where we had only Claude's code to judge), this round delivered:

1. **Parallel execution is reliable** — both finished within ~3 min of each other on shared hardware.
2. **Safety mechanisms work correctly now** — scope-check pass (Fix #7), diff preserved (Fix #8), result.md survived (Fix #9), task_id correct (Fix #11), sandbox runs `python` (Finding #10 mitigation).
3. **Judge step is tractable with Opus 1M context** — I read both diffs, the original file, the spec, and the judgment criteria in one coherent mental pass. No chunking, no forgetting, no prompt re-engineering.
4. **Two independent implementations converged on the same core architecture** ("sort once → render per-mode"). The variations are in polish layer, not in design. This is a positive signal — the spec was well-formed, both agents read it similarly, and the disagreement area is stylistic preference, not semantic ambiguity.
5. **The judge verdict is meaningful now** — Claude wins on specific, articulable merits, not by default.

## Post-merge plan

1. Merge `claude/task-dual-2` → `fix/watchdog-dushnost` via `git merge --no-ff`.
2. Archive loser diff (save Codex's diff as reference artifact) — preserves the alternative approach for future review.
3. Cleanup worktrees + branches.
4. Tag checkpoint `pipeline-checkpoint-DUAL2_COMPLETE`.

## Score card

- Dual-implement mechanism: **production-ready** after Fixes #7/#8/#9/#11 + Finding #10 mitigation.
- Level 3 is **validated end-to-end** with real judge on real merit.
- Remaining: DOCUMENT phase (codex-integration.md, knowledge.md patterns), then optional propagation to other bot projects.
