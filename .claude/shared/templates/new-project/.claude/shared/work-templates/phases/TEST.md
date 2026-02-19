# Phase Template: TEST

> Run full integration and E2E test suite, collect and report failures.

## Metadata
- Default Mode: SOLO
- Gate Type: AUTO
- Loop Target: FIX (on failure)
- Max Attempts: 1
- Checkpoint: pipeline-checkpoint-TEST

## Phase Context Loading
Before starting this phase, load:
- `work/{feature}/test-results.md` (if retry — see what failed last time)
- `.claude/memory/gotchas.md` — known testing pitfalls
- Query Graphiti: `search_memory_facts(query="test failures and debugging insights", max_facts=10)`

## Inputs
- Source code and tests (from IMPLEMENT or FIX phase)
- `work/{feature}/tech-spec.md` (expected behavior reference)

## Process
1. Run full test suite with verbose output:
   ```bash
   uv run pytest -v --tb=long 2>&1 | tee work/{feature}/test-results.md
   ```
2. Run linter: `uv run ruff check .`
3. Run type checker (if configured): `uv run pyright`
4. If failures exist:
   a. Parse failure output — list each failing test with error message
   b. Categorize: unit test failures, integration failures, type errors, lint errors
   c. Write failure summary to `work/{feature}/test-results.md`
   d. Transition to FIX phase
5. If all pass — phase complete

## Outputs
- `work/{feature}/test-results.md` (full test output + failure summary if any)

## Quality Gate
```bash
uv run pytest --tb=short -q && uv run ruff check .
```

### Verdicts
- PASS: All tests pass, lint clean
- CONCERNS: All tests pass but non-critical warnings exist
- REWORK: Test failures detected -> transition to FIX
- FAIL: Test infrastructure broken (cannot run tests at all)

## Context Recovery
After compaction, re-read:
- `work/PIPELINE.md` (find current phase)
- `work/{feature}/test-results.md` (see current test state)
