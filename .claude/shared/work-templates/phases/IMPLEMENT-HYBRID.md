# Phase Template: IMPLEMENT-HYBRID

> Per-task executor dispatch. Opus judges each task and routes it to a Claude teammate (via `TeamCreate`), a Codex session (via `codex-implement.py`), or the `dual-implement` skill. Most elegant mode; default recommendation for mixed workloads.

## Metadata
- Default Mode: HYBRID_TEAMS
- Gate Type: AUTO
- Loop Target: FIX (on test failure)
- Max Attempts: 1
- Checkpoint: pipeline-checkpoint-IMPLEMENT

## Phase Context Loading
Before starting this phase, load:
- `work/{feature}/tech-spec.md` — architecture to implement
- `work/{feature}/tasks/*.md` — task definitions (each declares `executor: claude | codex | dual` in frontmatter)
- `work/{feature}/tasks/waves.md` — parallelization plan
- `.claude/memory/knowledge.md` — patterns, pitfalls, and module structure
- `.claude/guides/codex-integration.md` — Codex CLI invocation rules
- `.claude/guides/teammate-prompt-template.md` — required for every Claude teammate prompt
- `.claude/adr/adr-012-codex-primary-implementer.md` — rationale for hybrid dispatch

## Inputs
- `work/{feature}/tech-spec.md` (architecture)
- `work/{feature}/tasks/*.md` with mixed `executor:` hints
- `work/{feature}/tasks/waves.md` (parallelization plan)

## Trigger
- Tasks have mixed `executor:` hints (some `claude`, some `codex`, possibly `dual`)
- Phase explicitly declares `Mode: HYBRID_TEAMS` in PIPELINE.md
- Opus wants flexibility to match each task to the best executor

## Dispatch
Pipeline iterates through tasks in the current wave and dispatches per-task by executor hint:

- `executor: claude` → `TeamCreate` with a Claude teammate prompt built from `teammate-prompt-template.md` (full skills + memory + codex-ask-second-opinion preamble). Existing Agent Teams flow, unchanged.
- `executor: codex` → background `codex-implement.py` in an isolated worktree:

  ```bash
  py -3 .claude/scripts/codex-implement.py \
      --task work/{feature}/tasks/T2.md \
      --worktree worktrees/hybrid-wave/T2 \
      --result-dir work/codex-implementations
  ```

- `executor: dual` → invoke the `dual-implement` skill for that single task (see `DUAL-IMPLEMENT.md` and `.claude/skills/dual-implement/SKILL.md`).

For Codex-bound tasks that can run together, Opus uses `codex-wave.py` to spawn them in parallel:

```bash
py -3 .claude/scripts/codex-wave.py \
    --tasks work/{feature}/tasks/T2.md,work/{feature}/tasks/T5.md \
    --parallel 3 \
    --worktree-base worktrees/hybrid-wave \
    --timeout-per-task 3600
```

## Parallelism
- Claude teammates parallelize via `TeamCreate` (one call with N teammates inside the same wave).
- Codex sessions parallelize via background processes spawned by `codex-wave.py` (each in its own worktree).
- Dual tasks parallelize internally (Claude + Codex run concurrently for the same task in separate worktrees).
- Within a single wave Claude teammates AND Codex sessions run concurrently — they touch disjoint scope fences by construction.

## Claude's Role
- **Before:** plan, decompose, and assign `executor:` per task during task-decomposition. Extract Skill Contracts into each task-N.md (Codex never loads skills itself).
- **During:** orchestrate. Spawn Claude teammates via `TeamCreate`. Spawn Codex sessions via `codex-wave.py` / `codex-implement.py`. For `executor: dual`, invoke the `dual-implement` skill.
- **After:** collect Claude teammate handoff blocks and Codex `task-{N}-result.md` files. Merge worktree branches sequentially. Route test failures to FIX.

## Process
1. Read tech spec, tasks, and waves.md. Validate every task has an explicit `executor:` hint and a Scope Fence section.
2. For each wave (sequential between waves, parallel within):
   a. Partition tasks by executor: `claude_tasks`, `codex_tasks`, `dual_tasks`.
   b. Spawn Claude teammates for `claude_tasks` via `TeamCreate` (one team per wave).
   c. Start `codex-wave.py` for `codex_tasks` in background.
   d. Invoke `dual-implement` skill for each task in `dual_tasks` (these self-parallelize Claude + Codex).
   e. Wait for all three tracks to finish.
   f. **Wave boundary context reminder:** before starting each new wave, provide agents with active acceptance criteria, known gotchas from knowledge.md, files already modified by previous waves, and current test status. This prevents context drift in long multi-wave implementations.
3. Collect results:
   - Claude teammates → standard `=== PHASE HANDOFF ===` block (per teammate-prompt-template.md).
   - Codex sessions → `work/codex-implementations/task-{N}-result.md` (status, diff, test output).
   - Dual tasks → winner diff selected by Opus-as-judge (see DUAL-IMPLEMENT.md).
4. Merge worktree branches one at a time; run test suite between merges to catch cross-task regressions.
5. Run full test suite: `uv run pytest`
6. Run linter: `uv run ruff check .`
7. If all pass — phase complete.

## Outputs
- Source code files (new/modified from all three executor tracks, merged)
- Claude teammate handoff blocks (in-transcript)
- `work/codex-implementations/task-{N}-result.md` (one per Codex task)
- Dual-task winner archives (`worktrees/dual-task-N/winner.diff`)
- `work/{feature}/test-results.md`

## Quality Gate
```bash
uv run pytest --tb=short -q
uv run ruff check .
py -3 .claude/scripts/codex-scope-check.py --diff <(git diff main...HEAD) --fence work/{feature}/tasks/T*.md
```

### Verdicts
- PASS: All executor tracks produced passing results, all merges clean, full test suite green, no lint errors.
- CONCERNS: Tests pass but lint warnings exist (document and proceed).
- REWORK: One or more tasks scope-violated or produced merge conflicts → re-dispatch (possibly with a different executor).
- FAIL: Unresolvable blocker from any track → escalate to human.

## When to Use
- Most projects with a mix of task types — lets Opus match each task to the best executor.
- Phases combining logic-heavy work (→ Codex) with UX polish or ambiguous glue code (→ Claude).
- When a phase contains 1-2 high-stakes tasks (→ dual) surrounded by routine ones.
- Default recommendation when in doubt.

## When NOT to Use
- Phase where every task is clearly Codex-shaped → use `CODEX_IMPLEMENT` (simpler).
- Phase where every task is high-stakes → use `DUAL_IMPLEMENT`.
- Phase where tasks need tight skill-injected judgment and shared memory → use `AGENT_TEAMS` (pure Claude).
- Cross-project work → use `AO_FLEET`.

## Relationship to existing modes
These modes are **orthogonal** — pick whichever fits this phase:
- `AGENT_TEAMS` (Claude-only parallel via `TeamCreate`) — unchanged, remains primary for tasks requiring skills + memory context
- `AO_HYBRID` — unchanged, remains for full-Claude-context parallel within one project
- `AO_FLEET` — unchanged, remains for cross-project work
- `CODEX_IMPLEMENT` — all tasks to Codex (see `IMPLEMENT-CODEX.md`)
- `HYBRID_TEAMS` (this mode) — per-task executor dispatch
- `DUAL_IMPLEMENT` — dual executors per task with Opus judging (see `DUAL-IMPLEMENT.md`)

Opus picks per phase based on task profile. Within `HYBRID_TEAMS`, Opus then picks per task.

## Agent Team Config
- Team size: variable. Claude teammates: 2-5 per wave via `TeamCreate`. Codex sessions: up to `codex-wave.py --parallel 3` (conservative default).
- Roles: Claude Developer (implements `executor: claude` tasks), Codex implementer (implements `executor: codex` tasks), Dual pair + Judge (for `executor: dual` tasks).
- Skills per role:
  - Claude teammate: `verification-before-completion` (mandatory) + task-specific (e.g., `security-review` for auth).
  - Codex: N/A (gets extracted Skill Contracts inline).
  - Dual judge: `cross-model-review`.
- Prompt template: Claude teammates use `.claude/guides/teammate-prompt-template.md`. Codex prompt baked into `codex-implement.py`.
- Each executor gets: task-N.md, tech-spec.md, isolated worktree.

## Context Recovery
After compaction, re-read:
- `work/PIPELINE.md` (find current phase)
- `work/{feature}/tasks/waves.md` (which wave is current)
- `work/{feature}/tasks/*.md` (find tasks with no completion evidence)
- `work/codex-implementations/task-*-result.md` (Codex completions)
- `work/{feature}/test-results.md` (if exists)

## Phase Output
Claude orchestrator MUST produce a structured handoff block listing per-task executor, status, merged commits, and any tasks that required re-dispatch.

## Cross-links
- Scripts: `.claude/scripts/codex-implement.py`, `.claude/scripts/codex-wave.py`, `.claude/scripts/codex-scope-check.py`
- Skill: `.claude/skills/dual-implement/SKILL.md`
- Guide: `.claude/guides/teammate-prompt-template.md`
- Tech spec: `work/codex-primary/tech-spec.md` (Section 5.2)
- ADR: `.claude/adr/adr-012-codex-primary-implementer.md`
