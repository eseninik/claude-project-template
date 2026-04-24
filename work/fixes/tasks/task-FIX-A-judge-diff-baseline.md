---
executor: dual
risk_class: routine
reasoning: high
speed_profile: balanced
---

# Task FIX-A: judge.py — fix empty-diff bug, score all 6 axes correctly

## Your Task

The judge scoring system silently skips 4 of 6 axes because `git diff HEAD` returns empty in two scenarios:
- **Claude side** (committed): after `git commit`, `HEAD` IS the new tree — `git diff HEAD` shows nothing.
- **Codex side** (untracked files): `git diff HEAD` never includes truly-untracked files regardless of commit state.

Result: `logging_coverage`, `lint_clean`, `complexity`, `type_check` all skip with `"empty diff"` or `"no modified .py files"` reasons. Only `tests_passed` and `diff_size` contribute to verdicts — 2 axes out of 6 carrying the whole weight budget.

Fix by making the diff-collection symmetric across both committed and untracked worktree states:
1. Add helper `_ensure_untracked_visible(worktree)` that runs `git add -N` on untracked `.py` files (registers intent-to-add — content not staged, but files now appear in `git diff`).
2. Change all diff subprocess calls to use `git diff <base>` (NOT `<base>..HEAD`). The `<base>` form compares working-tree-vs-base, capturing committed + staged + unstaged + intent-to-add.
3. Add `_resolve_base(worktree, cli_base)` helper in `judge.py` main: priority (1) explicit CLI arg other than `"HEAD"`/`"auto"`, (2) `.dual-base-ref` sidecar in worktree, (3) `git merge-base HEAD <main|master|dev>`, (4) fallback `"HEAD"`.
4. Compute base **per-side** in `judge.main` (claude and codex may differ). Pass resolved base to each `score_side` call.
5. Change `--base` CLI default from `"HEAD"` to `"auto"` to trigger new resolution logic; documented as auto-resolve.

## Scope Fence

**Allowed:**
- `.claude/scripts/judge_axes.py` (modify)
- `.claude/scripts/judge.py` (modify)
- `.claude/scripts/test_judge.py` (modify — add new tests; do NOT remove existing ones)

**Forbidden:**
- Every other path under `.claude/scripts/`
- `.claude/hooks/*`
- Any `work/*` or `worktrees/*` path

## Test Commands

```bash
py -3 .claude/scripts/test_judge.py
py -3 .claude/scripts/judge.py --help
py -3 -c "import subprocess, json, pathlib; r = subprocess.run(['python','.claude/scripts/judge.py','--help'], capture_output=True, text=True); assert r.returncode == 0 and '--base' in r.stdout"
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: `_ensure_untracked_visible(worktree: Path) -> int` added to `judge_axes.py`. Runs `git ls-files --others --exclude-standard`, filters `.py`, runs `git add -N` on the list. Returns count. All exceptions → log + return 0 (never raises).
- [ ] AC2: `_git_diff_numstat`, `_git_diff_text`, `_list_modified_py` call `_ensure_untracked_visible(worktree)` as their first operation.
- [ ] AC3: All three diff helpers run `git diff <base>` form (NOT `git diff <base>..HEAD`). Keep `base` parameter kwarg but update comment / docstring to reflect "working-tree-vs-base" semantic.
- [ ] AC4: `judge.py` adds `_resolve_base(worktree: Path, cli_base: str) -> str` helper with the 4-level priority described above. Logs which level hit at INFO.
- [ ] AC5: `judge.main` calls `_resolve_base` once per side, passes resolved string as `base=` kwarg to `score_side` (new per-side base parameter). Old `--base HEAD` still works (literal pass-through).
- [ ] AC6: `--base` CLI default changed from `"HEAD"` to `"auto"`. Help text mentions auto-resolve.
- [ ] AC7: Existing test suite still passes. New tests added: (a) committed-only worktree produces non-empty numstat, (b) untracked-only worktree produces non-empty numstat after `_ensure_untracked_visible`, (c) `_resolve_base` picks sidecar over CLI fallback, (d) `_resolve_base` picks merge-base when no sidecar and CLI=`"auto"`.
- [ ] AC8: Every new/modified function has structured logging (entry with params, exit with result, error in exception branches). No `print()` except the CLI's JSON summary at main's end.
- [ ] AC9: Stdlib only. Windows-compatible (no fcntl, no os.fork).
- [ ] AC10: Total LOC added ≤ 200 in judge_axes.py, ≤ 100 in judge.py, ≤ 150 in test_judge.py.
- [ ] All Test Commands above exit 0.

## Constraints

- DO NOT change axis weight values. DO NOT change `decide_winner` logic. DO NOT change the verdict JSON schema.
- `_ensure_untracked_visible` must be IDEMPOTENT — safe to call twice in same judge run (it will be: `git add -N` on already-registered files is a no-op).
- `git diff <base>` without `..HEAD` is the **only** correct form. Do not revert to `..HEAD`.
- For files > 250 lines, use Bash heredoc instead of Write tool — the harness auto-denies big Writes (see teammate-prompt-template.md "Platform Gotchas").

## Handoff Output

Standard `=== PHASE HANDOFF: FIX-A-judge-diff-baseline ===` with:
- commit sha
- test output (all test cases, pass counts)
- a demonstration: run judge.py on any two fake worktrees (committed vs untracked) and show that `logging_coverage` is now NOT skipped.
