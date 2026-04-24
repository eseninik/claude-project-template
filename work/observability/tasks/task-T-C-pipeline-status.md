---
executor: dual
risk_class: routine
speed_profile: balanced
---

# Task T-C: `.claude/scripts/pipeline-status.py` — PIPELINE.md parser + timeline

## Your Task

CLI that reads `work/**/PIPELINE.md` files, parses phase blocks, prints timeline: phase order, each phase's Status, `<- CURRENT` marker location, checkpoint tags via `git tag`, next-phase hint from `On PASS` of current phase.

## Scope Fence
**Allowed:** `.claude/scripts/pipeline-status.py` (new), `.claude/scripts/test_pipeline_status.py` (new).
**Forbidden:** any other path.

## Test Commands
```bash
python .claude/scripts/test_pipeline_status.py
python .claude/scripts/pipeline-status.py --help
python .claude/scripts/pipeline-status.py
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: CLI `pipeline-status.py [--feature <name>] [--json] [--project-root <path>] [--no-git]`.
- [ ] AC2: Discovers every `work/**/PIPELINE.md`; each = a pipeline grouped by containing-dir feature name.
- [ ] AC3: For each pipeline parses top-level `- Status:` and `- Phase:`, every `### Phase: <name>` block with its `- Status:`, plus `<- CURRENT` marker.
- [ ] AC4: Matches checkpoint tags via `git tag --list "pipeline-checkpoint-*"`; maps each tag to its short sha (`git rev-parse --short <tag>`).
- [ ] AC5: Text output per pipeline:
  ```
  Pipeline: <feature> (path: <rel-path>)
    Overall Status: <status>
    Current Phase : <phase> (<- CURRENT)
    Phases:
      1. PHASE_A     DONE
      2. PHASE_B     IN_PROGRESS  <- CURRENT
      3. PHASE_C     PENDING
    Checkpoints: <tag>@<sha>, ...
    Next hint   : <On PASS target of current phase | "complete">
  ```
- [ ] AC6: `--json`:
  ```json
  [{"feature": "...", "path": "...", "overall_status": "...", "current_phase": "...",
    "phases": [{"name": "...", "status": "...", "is_current": false}, ...],
    "checkpoints": [{"tag": "...", "sha": "..."}],
    "next_hint": "..."}]
  ```
- [ ] AC7: `--feature <name>` limits to `work/<name>/PIPELINE.md`.
- [ ] AC8: Malformed phase block without Status → record `status="unparsed"`; no crash.
- [ ] AC9: If `git` unavailable (or `--no-git`) → warn, skip checkpoints, exit 0.
- [ ] AC10: Structured logging, stdlib only.
- [ ] AC11: Under 350 lines script + 350 lines tests.
- [ ] AC12: Unit tests (≥10): multi-pipeline discovery, single pipeline phase order + current, whitespace-tolerant `<- CURRENT` match, malformed block → `unparsed`, `--feature` filter, `--json` schema, missing git → warn+exit0, no PIPELINE.md → exit 0 empty list, next-hint from `On PASS`, `PIPELINE_COMPLETE` → next="complete".
- [ ] All Test Commands exit 0.

## Constraints
- Windows-compatible (pathlib)
- Heuristic regex parse (`^### Phase:`, `^- Status:`, `<- CURRENT`), NOT a full markdown AST
- `subprocess.run(..., timeout=10, capture_output=True, text=True, check=False)` for git

## Handoff Output
Standard `=== PHASE HANDOFF: T-C-pipeline-status ===` with sample rendered timeline.
