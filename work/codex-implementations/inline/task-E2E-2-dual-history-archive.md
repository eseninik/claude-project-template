---
executor: dual
risk_class: routine
reasoning: high
speed_profile: balanced
---

# Task E2E-2: `.claude/scripts/dual-history-archive.py` — archive old result.md files into dated history dir

## Your Task

Stand-alone CLI that moves stale `work/codex-implementations/task-*-result.md` files (and matching `.diff` siblings) older than N days into `work/codex-primary/dual-history/<YYYY-MM>/` for cold storage. Default mode is dry-run; `--apply` does the move.

Useful for keeping the active result.md directory uncluttered while preserving history for post-mortems.

## Scope Fence

**Allowed:**
- `.claude/scripts/dual-history-archive.py` (new)
- `.claude/scripts/test_dual_history_archive.py` (new)

**Forbidden:** any other path.

## Test Commands

```bash
py -3 .claude/scripts/test_dual_history_archive.py
py -3 .claude/scripts/dual-history-archive.py --help
py -3 .claude/scripts/dual-history-archive.py --dry-run
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: CLI: `dual-history-archive.py [--source work/codex-implementations] [--dest work/codex-primary/dual-history] [--max-age-days 7] [--dry-run] [--apply] [--json] [--verbose]`. Default = dry-run. `--apply` is the only mode that mutates.
- [ ] AC2: Discovery: glob `<source>/task-*-result.md` plus the matching `<source>/task-*.diff` sibling (if exists). Sub-dirs (e.g. `inline/`) NOT recursed by default.
- [ ] AC3: For each candidate, computes `age_days = today - mtime.date()`. Stale iff `age_days > --max-age-days` (default 7).
- [ ] AC4: Default output: lists each stale entry with age + would-be destination, ends with "Run with --apply to move. Skipping (dry-run)." line. Includes count summary.
- [ ] AC5: `--json` emits `{"source","dest","window_days","found":N,"stale":N,"kept":N,"entries":[{"path","age_days","dest_path","apply_status":"skipped|moved|error"}]}`.
- [ ] AC6: With `--apply`: each move uses `shutil.move`. Each operation logged at INFO. Dest sub-dir `<dest>/<YYYY-MM>/` is created if missing. Continues on per-entry failure (do NOT abort loop). Exit 0 if all OK; exit 1 on any failure.
- [ ] AC7: Diff sibling tracking: when both `task-X-result.md` and `task-X.diff` exist, BOTH are moved together (atomic per task).
- [ ] AC8: Stdlib only. Windows-compatible (pathlib). Under 250 lines script + 250 lines tests.
- [ ] AC9: Unit tests (>=8): discovery in tmp dir, age threshold filtering, dry-run does NOT move, --apply moves both result.md + .diff, --apply creates YYYY-MM subdir if missing, per-entry failure does not abort, --json round-trip, no stale entries -> exit 0.
- [ ] All Test Commands above exit 0.

## Constraints

- Use `shutil.move` (cross-device safe). NOT `os.rename`.
- Date format: dest subdir = `<YYYY-MM>` (zero-padded). Compute from file mtime, not "now".
- Dry-run path must be TRULY READ-ONLY (no mkdir, no touch).
- `datetime.fromtimestamp(mtime).date()` for age calc.
- Stdlib `logging`. Entry/exit/error per function.
- If your file would exceed ~250 lines, use Bash heredoc instead of Write tool.

## Handoff Output

Standard `=== PHASE HANDOFF: E2E-2-dual-history-archive ===` with sample dry-run on real repo state.
