# Phase Template: IMPLEMENT

> Code the solution with TDD, using parallel agents for independent tasks.

## Metadata
- Default Mode: AGENT_TEAMS (for 3+ tasks)
- Gate Type: AUTO
- Loop Target: FIX (on test failure)
- Max Attempts: 1
- Checkpoint: pipeline-checkpoint-IMPLEMENT

## Phase Context Loading
Before starting this phase, load:
- `work/{feature}/tech-spec.md` — architecture to implement
- `work/{feature}/tasks/*.md` — task definitions
- `.claude/memory/knowledge.md` — patterns, pitfalls, and module structure

## Inputs
- `work/{feature}/tech-spec.md` (architecture)
- `work/{feature}/tasks/*.md` (atomic task definitions)
- `work/{feature}/tasks/waves.md` (parallelization plan)

## Process
1. Read tech spec and all task files
2. Read wave analysis to determine parallel execution groups
3. For each wave (sequential between waves, parallel within):
   a. Create Agent Team for tasks in the wave
   b. Each agent: write test first, then implement, then verify test passes
   c. Collect results, verify no conflicts between agents
   d. **Wave boundary context reminder:** Before starting each new wave, provide agents with:
      - Active acceptance criteria for their tasks
      - Known gotchas from knowledge.md relevant to modified modules
      - Files already modified by previous waves (to avoid conflicts)
      - Current test status (which tests pass/fail after prior waves)
      This prevents context drift in long multi-wave implementations.
4. After all waves complete, run full test suite: `uv run pytest`
5. Run linter: `uv run ruff check .`
6. Run type checker: `uv run pyright` (if configured)
7. If all pass — phase complete

## Outputs
- Source code files (new/modified)
- Test files
- `work/{feature}/test-results.md` (test run output)

## Quality Gate
```bash
uv run pytest --tb=short -q
uv run ruff check .
```

### Verdicts
- PASS: All tests pass, no lint errors
- CONCERNS: Tests pass but lint warnings exist (document and proceed)
- REWORK: Tests fail -> transition to FIX phase
- FAIL: Fundamental implementation blocker (missing dependency, API unavailable)

## Agent Team Config
- Team size: 2-5 (one per wave group or one per task)
- Roles: Developer (implements tasks)
- Skills per role: verification-before-completion
- Prompt template: use `.claude/guides/teammate-prompt-template.md`
- Each agent gets: task file, tech-spec, relevant source files

## Context Recovery
After compaction, re-read:
- `work/PIPELINE.md` (find current phase)
- `work/{feature}/tasks/waves.md` (which wave is current)
- `work/{feature}/tasks/*.md` (find uncompleted tasks)
- `work/{feature}/test-results.md` (if exists — see what passed/failed)

## Phase Output
Agent MUST produce a structured handoff block (see teammate-prompt-template.md).
