---
executor: dual
risk_class: routine
reasoning: high
speed_profile: balanced
---

# Task E2E-1: `.claude/scripts/codex-cost-report.py` — duration / token report from codex-implement logs

## Your Task

Stand-alone CLI that scans `.claude/logs/codex-implement-*.log` and `.claude/logs/codex-fix-*.log` files (structured JSON-per-line emitted by codex-implement.py) and emits a duration / token summary report.

Each log line is a JSON object with keys like `ts`, `level`, `logger`, `msg`, plus event-specific keys. Of particular interest:
- `msg="entry: main"` -> start of a codex-implement run
- `msg="exit: run_codex"` -> has `returncode`, `stdout_len`, `stderr_len`, `self_report` count
- `msg="exit: main"` -> has `status` (pass/fail/scope-violation), `exit_code`

Aggregate per-task: start_ts, end_ts, duration_s, status, stdout_len, stderr_len, returncode, model, reasoning.

## Scope Fence

**Allowed:**
- `.claude/scripts/codex-cost-report.py` (new)
- `.claude/scripts/test_codex_cost_report.py` (new)

**Forbidden:** any other path.

## Test Commands

```bash
py -3 .claude/scripts/test_codex_cost_report.py
py -3 .claude/scripts/codex-cost-report.py --help
py -3 .claude/scripts/codex-cost-report.py
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: CLI: `codex-cost-report.py [--log-dir .claude/logs] [--json] [--since-hours N] [--verbose]`. Default scans `.claude/logs/codex-*.log`. `--since-hours N` filters runs whose start_ts is within last N hours.
- [ ] AC2: Parses each log file line-by-line as JSON. Malformed lines -> log WARNING, skip, continue. NEVER crash on a malformed log.
- [ ] AC3: For each log file, identifies one or more codex-implement runs. A "run" begins with `msg="entry: main"` and ends with `msg="exit: main"` (or end-of-file if main never exited).
- [ ] AC4: Per-run aggregate fields: `task_id` (from argv parsing), `start_ts`, `end_ts`, `duration_s` (from ts difference), `status` (from exit_main), `returncode`, `stdout_len`, `stderr_len`, `model`, `reasoning`.
- [ ] AC5: Default output (markdown to stdout): header with generated_at + log dir + run count + total duration + status counts; per-run table with columns Task / Status / Duration / Reasoning / Model / Stdout / Stderr.
- [ ] AC6: `--json` emits valid JSON: top keys `generated_at`, `log_dir`, `window_hours`, `summary` (with `runs`, `pass`, `fail`, `total_duration_s`), `runs` (list of per-run dicts). Each run dict has all AC4 fields plus `log_file`.
- [ ] AC7: Empty dir or no matching runs -> human output one-liner; JSON: empty `runs` list + zeroed summary. Exit 0 in both.
- [ ] AC8: Sorting: runs sorted by start_ts ascending; tie-breaker `task_id` ascending.
- [ ] AC9: Stdlib only. Windows-compatible (pathlib). Under 300 lines script + 300 lines tests.
- [ ] AC10: Unit tests (>=8): single happy-path log -> expected row, multiple runs sorted, malformed JSON line skipped, since-hours filter, status counts, JSON round-trip, no logs -> exit 0, duration computed correctly from ts diff.
- [ ] All Test Commands above exit 0.

## Constraints

- READ-ONLY: never modifies log files.
- `datetime.fromisoformat` for ts parsing; tolerate both naive and tz-aware ts.
- Cross-platform line endings.
- Stdlib `logging`. Entry/exit/error per function.
- If your file would exceed ~250 lines, use Bash heredoc instead of Write tool.

## Handoff Output

Standard `=== PHASE HANDOFF: E2E-1-codex-cost-report ===` with sample run on this repo's actual `.claude/logs/`.
