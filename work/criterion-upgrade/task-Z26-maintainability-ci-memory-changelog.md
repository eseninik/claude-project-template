---
task_id: Z26-maintainability-ci-memory-changelog
title: Criterion 5 Maintainability — GitHub Actions CI + memory archive automation + CHANGELOG.md scaffold
executor: dual
risk_class: routine
speed_profile: balanced
---

# Task Z26

## Goal

Criterion 5 (Maintainability) currently 6/10. Three improvements:

1. **GitHub Actions CI workflow** — every PR runs full test suite +
   live attack matrix + selftest. Catches regressions before merge.
2. **Memory archive automation** — when activeContext.md exceeds 200
   lines, auto-archive oldest sections to `.claude/memory/archive/`.
3. **CHANGELOG.md scaffold** — structured release notes anchored to
   commit tags, generated from `pipeline-checkpoint-*` tags.

## Three coordinated additions

### Addition 1 — GitHub Actions CI workflow

NEW file `.github/workflows/dual-implement-ci.yml`:
- Triggers: `on: pull_request` AND `on: push to fix/* and main branches`
- Jobs:
  - `tests` — runs all pytest suites (`.claude/scripts/test_*.py`,
    `.claude/hooks/test_*.py`)
  - `selftest` — runs `python .claude/scripts/dual-teams-selftest.py`
  - `attack-matrix` — runs `pytest .claude/hooks/test_enforcer_live_attacks.py -v`
- Use `actions/checkout@v4` + `actions/setup-python@v5` (Python 3.12).
- Fail PR check if any job fails.

### Addition 2 — Memory archive automation

NEW file `.claude/scripts/archive-active-context.py`:
- Reads `.claude/memory/activeContext.md`
- If `len(lines) > 200`: extract OLDEST round section (e.g. `## Round X`)
  → write to `.claude/memory/archive/active-YYYY-MM-DD-roundX.md`
- Update `activeContext.md` to remove the archived section
- Idempotent — safe to run multiple times
- Add to PreCompact hook chain as auto-trigger when memory bloats

Add helper `_extract_oldest_round(content) -> tuple[str, str]` returning
`(archived_section_text, remaining_content)`.

Tests in NEW `.claude/scripts/test_archive_active_context.py`:
- `test_archive_when_under_200_lines_noop`
- `test_archive_when_over_200_lines_extracts_oldest_round`
- `test_archive_preserves_header`

### Addition 3 — CHANGELOG.md scaffold

NEW file `CHANGELOG.md` at repo root:
- Conventional Commits-style headers
- Sections per `pipeline-checkpoint-*` tag
- Auto-populated from `git log <prev-tag>..<tag> --format="- %s"`
- Initial entries based on existing tags:
  - `Round 7 (Z12)` — Y21 + Y25 close all initial Y18-Y25 follow-ups
  - `Round 8 (Z14)` — Functional Coverage 10/10
  - `Round 8 (Z17)` — Reliability 10/10
  - `Round 8 (Z20)` — Security 10/10
  - `Round 8 (Z23)` — Determinism 10/10

NEW helper `.claude/scripts/generate-changelog.py`:
- Reads git tags matching `pipeline-checkpoint-*`
- For each tag: outputs section with commit titles since previous tag
- Idempotent — overwrites CHANGELOG.md sections >= last tag

Test in NEW `.claude/scripts/test_generate_changelog.py`:
- `test_generate_changelog_format` — output has expected structure
- `test_generate_changelog_idempotent` — running twice produces same content

## Scope Fence

```
.github/workflows/dual-implement-ci.yml     (NEW)
.claude/scripts/archive-active-context.py   (NEW)
.claude/scripts/test_archive_active_context.py (NEW)
.claude/scripts/generate-changelog.py       (NEW)
.claude/scripts/test_generate_changelog.py  (NEW)
CHANGELOG.md                                (NEW)
```

DO NOT modify any existing file.

## Read-Only Files / Evaluation Firewall

- `work/criterion-upgrade/task-Z26-maintainability-ci-memory-changelog.md`
- `.claude/scripts/codex-implement.py`, `spawn-agent.py`, `judge*.py`
- `.claude/hooks/codex-delegate-enforcer.py`
- All test files

## Acceptance Criteria

### AC-1: GitHub Actions workflow file exists + valid YAML

`.github/workflows/dual-implement-ci.yml` exists. YAML parseable:
```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/dual-implement-ci.yml'))"
```

### AC-2: Memory archive script works

```bash
python .claude/scripts/archive-active-context.py --dry-run
```
Returns 0 + prints "would archive: X lines" or "no archive needed".

`test_archive_active_context.py` tests pass.

### AC-3: CHANGELOG.md exists and is structured

`CHANGELOG.md` exists. Has sections with `## ` heading per release tag.
`test_generate_changelog.py` tests pass.

### AC-4: 124 existing tests still pass (regression)

```bash
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/scripts/test_spawn_agent.py .claude/scripts/test_determinism_chaos.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line
```

### AC-5: New tests pass

```bash
python -m pytest .claude/scripts/test_archive_active_context.py .claude/scripts/test_generate_changelog.py -v --tb=line
```

### AC-6: Selftest 6/6
`python .claude/scripts/dual-teams-selftest.py`

## Test Commands

```bash
# 1. New tests
python -m pytest .claude/scripts/test_archive_active_context.py .claude/scripts/test_generate_changelog.py -v --tb=line

# 2. Existing test regression
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/scripts/test_spawn_agent.py .claude/scripts/test_determinism_chaos.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line

# 3. YAML lint
python -c "import yaml; yaml.safe_load(open('.github/workflows/dual-implement-ci.yml'))"

# 4. Archive script dry-run
python .claude/scripts/archive-active-context.py --dry-run

# 5. Selftest
python .claude/scripts/dual-teams-selftest.py
```

## Implementation hints

- For workflow YAML: keep simple, single-OS (ubuntu-latest), Python 3.12.
- archive-active-context.py: parse markdown headings, group sections,
  identify oldest round number, slice it out.
- generate-changelog.py: use `subprocess.run(["git", "tag", "-l", "pipeline-checkpoint-*"])`,
  for each tag pair use `git log <prev>..<tag> --format="- %s"`.
- All scripts pure Python stdlib + PyYAML if needed for YAML test.

## Self-report format

```
=== TASK Z26 SELF-REPORT ===
- status: pass | fail | blocker
- Addition 1 (CI workflow) approach: <1 line>
- Addition 2 (archive automation) approach: <1 line>
- Addition 3 (CHANGELOG) approach: <1 line>
- new tests: <count>
- existing 124 tests still pass: yes / no
- attack matrix 25/25: yes / no
- selftest 6/6: PASS / FAIL
- net lines: <approx>
- files modified: [list]
- NOTE: <surprising>
- BLOCKER: <only if>
- Final commit SHA: <SHA>
=== END SELF-REPORT ===
```
