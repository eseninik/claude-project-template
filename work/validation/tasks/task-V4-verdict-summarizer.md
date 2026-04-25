---
executor: dual
risk_class: routine
reasoning: high
speed_profile: balanced
---

# Task V-4: `.claude/scripts/verdict-summarizer.py` — aggregate dual-implement verdicts into a unified report

## Your Task

Stand-alone CLI that scans `work/**/verdicts/*.json` (output of `judge.py`) and aggregates them into a markdown summary report. Useful for:
- Quick at-a-glance picture of recent dual-implement runs ("what won this week — Claude or Codex?")
- Pipeline checkpoints (what tasks succeeded, what tied, what failed)
- Post-mortem when an experiment series ends

Each verdict JSON looks like (see `judge.py` output schema):
```json
{
  "task_id": "...",
  "winner": "claude" | "codex" | "tie",
  "delta": 0.0123,
  "scores": { "claude": 0.5, "codex": 0.49 },
  "axes": { ... },
  "timestamp": "..."
}
```

## Scope Fence

**Allowed:**
- `.claude/scripts/verdict-summarizer.py` (new)
- `.claude/scripts/test_verdict_summarizer.py` (new)

**Forbidden:** any other path.

## Test Commands

```bash
py -3 .claude/scripts/test_verdict_summarizer.py
py -3 .claude/scripts/verdict-summarizer.py --help
py -3 .claude/scripts/verdict-summarizer.py
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: CLI: `verdict-summarizer.py [--root work/] [--feature <name>] [--since-days N] [--json] [--top-axes K] [--verbose]`. Default scans `work/**/verdicts/*.json`. `--feature` filters to a specific dir like `fixes` or `validation`. `--since-days N` filters to verdicts whose `timestamp` is within N days. `--top-axes K` shows the K most-contested axes (largest |delta| spread).
- [ ] AC2: Reads each verdict JSON safely — schema-tolerant. Missing fields → log WARNING, continue. Malformed JSON → log ERROR with file path, skip that file, continue.
- [ ] AC3: Default output (markdown to stdout):
   ```
   # Dual-Implement Verdict Summary
   - generated: <iso timestamp>
   - root: work/
   - feature filter: (none)
   - verdicts found: 7
   - winners: claude=3 codex=2 tie=2

   ## Per-task table
   | Task | Winner | Delta | Score Claude | Score Codex | Timestamp |
   |------|--------|-------|--------------|-------------|-----------|
   | FIX-A | tie | -0.0015 | 0.5040 | 0.5055 | 2026-04-24 22:20 |
   | FIX-B | tie | +0.0003 | 0.5012 | 0.5009 | 2026-04-24 22:21 |
   | ... |

   ## Top-3 contested axes
   - logging_coverage: 5/7 verdicts non-zero, mean |Δ|=0.123
   - lint_clean: 4/7 verdicts non-zero, mean |Δ|=0.087
   - tests_passed: 3/7 verdicts non-zero, mean |Δ|=0.020
   ```
- [ ] AC4: `--json` emits `{"generated_at","root","feature","window_days","summary":{"verdicts":N,"claude":N,"codex":N,"tie":N},"verdicts":[{...}], "axes":[{"name","contested_count","mean_abs_delta"}]}`.
- [ ] AC5: Empty input (no verdicts found) → human output: "No verdicts found under <root> matching filters." JSON output with `verdicts:[]` and zeroed summary. Exit 0 in both.
- [ ] AC6: Sorting: per-task table sorted by `timestamp` ascending; tie-breaker `task_id` ascending.
- [ ] AC7: Resolves verdict file paths via `pathlib.Path.rglob` not shell glob (cross-platform). `--root` accepts both relative and absolute.
- [ ] AC8: Structured JSON logging, stdlib `logging`. Entry/exit/error per function. `--verbose` toggles DEBUG.
- [ ] AC9: Stdlib only. Windows-compatible. Under 300 lines script + 300 lines tests.
- [ ] AC10: Unit tests (≥10): (a) single happy-path verdict produces expected table row, (b) multiple verdicts sorted correctly, (c) malformed JSON skipped with WARNING + continue, (d) `--feature` filter restricts results, (e) `--since-days` filter respects timestamp boundary, (f) winners count consistent with verdicts, (g) `--top-axes K` returns top K by |Δ| mean, (h) `--json` schema round-trip, (i) empty input → exit 0 with empty summary, (j) verdict missing `axes` field → still in summary but axes loop skips it gracefully.
- [ ] All Test Commands above exit 0.

## Constraints

- This summarizer is READ-ONLY — never writes to verdict files or any other state.
- `datetime.fromisoformat` for timestamp parsing; tolerate both `"2026-04-24T22:20:34"` and `"2026-04-24 22:20:34"`.
- For `--top-axes`, "contested" = `axes[name].claude != axes[name].codex` AND both present. Sum |Δ| across verdicts.
- Cross-platform path printing: use `Path.as_posix()` in markdown output for stable paths.
- If your file will exceed ~250 lines including logging, USE Bash heredoc (`cat > <path> <<'END_MARK'`) instead of Write.

## Handoff Output

Standard `=== PHASE HANDOFF: V-4-verdict-summarizer ===` with sample run on this repo's actual `work/fixes/verdicts/` (showing FIX-A and FIX-B from Round 1) and trailing `verdicts found: N` count.
