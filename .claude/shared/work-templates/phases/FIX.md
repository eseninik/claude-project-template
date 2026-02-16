# Phase Template: FIX

> Analyze test failures, fix bugs, and verify fixes pass.

## Metadata
- Default Mode: SOLO (1-2 bugs) or AGENT_TEAMS (3+ independent bugs)
- Gate Type: AUTO
- Loop Target: TEST (after fix, re-run tests)
- Max Attempts: 3
- Checkpoint: pipeline-checkpoint-FIX

## Inputs
- `work/{feature}/test-results.md` (failure details from TEST phase)
- Source code and test files
- `work/{feature}/tech-spec.md` (intended behavior reference)

## Process
1. Read `work/{feature}/test-results.md` — list all failures
2. Classify failures: independent bugs vs related root cause
3. For each independent failure group:
   a. Trace root cause (read failing test, read tested code, check inputs)
   b. Fix the code (not the test, unless test itself is wrong)
   c. Run the specific failing test to verify fix:
      ```bash
      uv run pytest tests/path/test_file.py::test_name -v
      ```
4. After all fixes, run full suite: `uv run pytest --tb=short -q`
5. If still failing and attempts < max — loop back to TEST
6. If attempts >= max — mark BLOCKED, alert user

## Outputs
- Fixed source code
- Updated `work/{feature}/test-results.md` (with fix attempt log)

## Quality Gate
```bash
uv run pytest --tb=short -q
```
Specifically: the tests that were failing before this phase must now pass.

### Verdicts
- PASS: Previously failing tests now pass, no new failures
- CONCERNS: Original failures fixed but new unrelated warning appeared
- REWORK: Some failures remain -> increment attempt, loop to TEST
- FAIL: Max attempts reached, fundamental issue -> BLOCKED

## Agent Team Config
Only when 3+ independent bugs exist:
- Team size: 2-4 (one per independent bug group)
- Roles: Debugger (analyzes and fixes bugs)
- Skills per role: systematic-debugging, verification-before-completion
- Prompt template: use `.claude/guides/teammate-prompt-template.md`
- Each agent gets: specific failing test(s), related source files, test-results.md

## Context Recovery
After compaction, re-read:
- `work/PIPELINE.md` (find current phase + attempt count)
- `work/{feature}/test-results.md` (which tests are failing)
- Git diff of recent changes (see what was already attempted)
