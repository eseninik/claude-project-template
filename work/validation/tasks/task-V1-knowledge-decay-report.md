---
executor: dual
risk_class: routine
reasoning: high
speed_profile: balanced
---

# Task V-1: `.claude/scripts/knowledge-decay-report.py` — memory tier audit CLI

## Your Task

Stand-alone diagnostic CLI that scans `.claude/memory/knowledge.md`, classifies each Pattern (`### Name (YYYY-MM-DD, verified: YYYY-MM-DD)`) and Gotcha into one of four tiers based on `verified:` date age, and prints a report. Complements `.claude/scripts/memory-engine.py` but outputs a human-readable decay audit table rather than operating on entries.

Tier rules (match existing `.claude/ops/config.yaml` memory section):
- `active`: 0-14 days since verified
- `warm`: 15-30 days
- `cold`: 31-90 days
- `archive`: 91+ days

Default output: grouped table per tier + age histogram + "candidates for promotion" list (entries referenced in today's activeContext.md but currently in `warm`/`cold`).

## Scope Fence

**Allowed:**
- `.claude/scripts/knowledge-decay-report.py` (new)
- `.claude/scripts/test_knowledge_decay_report.py` (new)

**Forbidden:** any other path.

## Test Commands

```bash
py -3 .claude/scripts/test_knowledge_decay_report.py
py -3 .claude/scripts/knowledge-decay-report.py --help
py -3 .claude/scripts/knowledge-decay-report.py
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: CLI flags `knowledge-decay-report.py [--json] [--knowledge-path PATH] [--today YYYY-MM-DD] [--include-gotchas | --patterns-only] [--threshold-days N]`. Default reads `.claude/memory/knowledge.md`; default today=today; `--threshold-days` overrides tier boundaries (passing e.g. `7,21,60` sets active/warm/cold cutoffs).
- [ ] AC2: Parses entries of form `### <Name> (YYYY-MM-DD, verified: YYYY-MM-DD)` at the start of a line. Both dates required; missing/malformed → record `tier="unparsed"`, log WARNING, keep going (do NOT crash).
- [ ] AC3: For every parsed entry, compute `age_days = today - verified`, assign tier via the active/warm/cold/archive boundaries.
- [ ] AC4: Default output is grouped table:
  ```
  Tier    | Count | Entries (truncated to first 80 chars)
  --------+-------+-----------------------------------------
  active  |   3   | * Pattern Name A (2026-04-18, age=6d)
                    ...
  warm    |   1   | ...
  cold    |  12   | ...
  archive |   4   | ...
  unparsed|   0   |
  Total   |  20   |
  ```
- [ ] AC5: `--json` emits `{"generated_at": iso, "today": iso, "tiers": {"active": [...], "warm": [...], "cold": [...], "archive": [...], "unparsed": [...]}, "summary": {"active":N, "warm":N, "cold":N, "archive":N, "unparsed":N, "total":N}}` where each entry = `{"name","verified","created","age_days","tier","line_no"}`.
- [ ] AC6: Parse Patterns section AND Gotchas section by default. `--patterns-only` filters to Patterns only.
- [ ] AC7: "Promotion candidates" — if `.claude/memory/activeContext.md` exists, extract substring matches (case-insensitive) of entry `Name` within it. Any entry currently `warm`/`cold`/`archive` whose name is referenced → mark as candidate. Render below main table (`## Promotion candidates (N): ...`). Empty section when none.
- [ ] AC8: Structured logging (JSON, stdlib `logging`, `--verbose` toggles DEBUG). Entry/exit/error logs every function.
- [ ] AC9: Stdlib only (no radon, no external). Windows-compatible. Under 300 lines script + 300 lines tests.
- [ ] AC10: Unit tests (≥10): (a) fresh entry → `active`; (b) 20d → `warm`; (c) 60d → `cold`; (d) 120d → `archive`; (e) missing `verified:` → `unparsed`; (f) `--today` override applied correctly; (g) `--patterns-only` excludes gotchas; (h) JSON schema round-trip; (i) promotion candidate detection via activeContext.md; (j) empty knowledge.md → `total=0`, exit 0.
- [ ] All Test Commands exit 0.

## Constraints

- `datetime.date.fromisoformat` and `datetime.date.today()` — NOT `datetime.datetime`.
- Windows pathlib, no fcntl.
- Do NOT mutate `knowledge.md` — read-only operation.
- If your file will exceed ~250 lines including logging, USE Bash heredoc (`cat > <path> <<'END_MARK'`) instead of Write — harness silently denies large Writes.
- For any subprocess to npm/codex CLI: `shutil.which("codex")` first, pass resolved absolute path.

## Handoff Output

Standard `=== PHASE HANDOFF: V-1-knowledge-decay-report ===` with sample rendered table (on this repo's actual knowledge.md) and JSON snippet.
