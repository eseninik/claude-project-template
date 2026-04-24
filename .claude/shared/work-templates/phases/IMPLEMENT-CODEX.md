# Phase Template: IMPLEMENT-CODEX

> Delegate ALL tasks in this phase to Codex (GPT-5.5). Claude plans before and reviews the diff after. Good for logic-heavy, well-specified work.

## Metadata
- Default Mode: CODEX_IMPLEMENT
- Gate Type: AUTO
- Loop Target: FIX (on test failure)
- Max Attempts: 1
- Checkpoint: pipeline-checkpoint-IMPLEMENT

## Phase Context Loading
Before starting this phase, load:
- `work/{feature}/tech-spec.md` — architecture to implement
- `work/{feature}/tasks/*.md` — task definitions (every task must have `executor: codex` in frontmatter)
- `.claude/memory/knowledge.md` — patterns, pitfalls, and module structure
- `.claude/guides/codex-integration.md` — Codex CLI invocation rules
- `.claude/adr/adr-012-codex-primary-implementer.md` — rationale for this mode

## Inputs
- `work/{feature}/tech-spec.md` (architecture)
- `work/{feature}/tasks/*.md` (atomic task definitions with Scope Fence + Acceptance Criteria IMMUTABLE + Skill Contracts)
- `work/{feature}/tasks/waves.md` (parallelization plan, optional)

## Trigger
- All tasks in this phase have `executor: codex` frontmatter, OR
- Phase explicitly declares `Mode: CODEX_IMPLEMENT` in PIPELINE.md, OR
- Tasks are routine logic with clear tests and well-defined scope fences

## Dispatch
Pipeline runs a single parallel wave via `codex-wave.py`:

```bash
py -3 .claude/scripts/codex-wave.py \
    --tasks work/{feature}/tasks/T1.md,work/{feature}/tasks/T2.md,work/{feature}/tasks/T3.md \
    --parallel 3 \
    --worktree-base worktrees/codex-wave \
    --timeout-per-task 3600
```

Each task runs in its own git worktree via an isolated `codex-implement.py` process:

```bash
py -3 .claude/scripts/codex-implement.py \
    --task work/{feature}/tasks/T1.md \
    --worktree worktrees/codex-wave/T1 \
    --result-dir work/codex-implementations
```

Results land in `work/codex-implementations/task-{N}-result.md` (status, diff, test output, self-reported blockers).

## Claude's Role
- **Before:** write the spec. Decompose into task-N.md files with Scope Fence, Test Commands, Acceptance Criteria (IMMUTABLE), and Skill Contracts (extracted from skills: verification-before-completion, logging-standards, security-review, coding-standards).
- **During:** do not edit source files. Claude does not implement in this mode.
- **After:** review each `task-{N}-result.md` diff. Merge worktree branches sequentially. If any scope-violation or test failure, route to FIX phase.

## Process
1. Read tech spec and all task files. Verify every task has `executor: codex` and a Scope Fence section.
2. Verify each task's Skill Contracts section contains extracted invariants (Opus does extraction during task-decomposition — Codex never loads skills itself).
3. Run `codex-wave.py` for the whole task list (or per wave if `waves.md` exists).
4. Wait for all processes to complete; collect result files.
5. For each `task-{N}-result.md`:
   - If `status: scope-violation` → task auto-rolled back; mark REWORK.
   - If `status: fail` → diff preserved; route to FIX phase.
   - If `status: pass` → queue worktree branch for sequential merge.
6. Merge worktree branches one at a time; run full test suite between merges to catch cross-task regressions.
7. Run full test suite: `uv run pytest`
8. Run linter: `uv run ruff check .`
9. If all pass — phase complete.

## Outputs
- Source code files (new/modified, produced by Codex in worktrees, then merged)
- `work/codex-implementations/task-{N}-result.md` (one per task)
- `work/codex-primary/codex-wave-report.md` (aggregate from codex-wave.py)
- `work/{feature}/test-results.md` (full-suite test run after merges)

## Quality Gate
```bash
uv run pytest --tb=short -q
uv run ruff check .
py -3 .claude/scripts/codex-scope-check.py --diff <(git diff main...HEAD) --fence work/{feature}/tasks/T*.md
```

### Verdicts
- PASS: All Codex tasks produced `status: pass`, all merges clean, full test suite green, no lint errors.
- CONCERNS: Tests pass but lint warnings exist (document and proceed).
- REWORK: One or more tasks produced `scope-violation` or merge conflicts → re-decompose or tighten scope fence.
- FAIL: Codex unable to satisfy spec after one attempt (ambiguous requirements, tooling gap) → route to FIX or escalate to human.

## When to Use
- Logic-heavy, well-specified tasks (parsers, algorithms, data transforms)
- Bug fixes with clear reproduction + regression test
- Isolated-module refactors with tight scope fences
- Routine CRUD endpoint implementation against an OpenAPI contract
- Anything where the spec can be expressed as IMMUTABLE acceptance criteria + Test Commands

## When NOT to Use
- UX / frontend polish (subjective, needs "reading between lines")
- Ambiguous requirements (Codex diverges without guidance)
- Cross-cutting refactors spanning many modules (scope fence impractical)
- Tasks requiring skill-injected judgment (Codex sees only the Skill Contracts extract, not the full skill)
- High-stakes code (auth, migrations, payments, crypto) — use `DUAL-IMPLEMENT.md` instead

## Relationship to existing modes
These modes are **orthogonal** — pick whichever fits this phase:
- `AGENT_TEAMS` (Claude-only parallel via `TeamCreate`) — unchanged, remains primary for tasks requiring skills + memory context
- `AO_HYBRID` — unchanged, remains for full-Claude-context parallel within one project
- `AO_FLEET` — unchanged, remains for cross-project work
- `CODEX_IMPLEMENT` (this mode) — all tasks to Codex; Claude plans + reviews
- `HYBRID_TEAMS` — per-task executor dispatch (see `IMPLEMENT-HYBRID.md`)
- `DUAL_IMPLEMENT` — dual executors per task with Opus judging (see `DUAL-IMPLEMENT.md`)

Opus picks per phase based on task profile.

## Agent Team Config
- Team size: N/A for implementers (no Claude teammates spawned; all implementation delegated to Codex subprocesses).
- Roles: Codex implementer per task (headless `codex exec` with `--sandbox workspace-write`, scoped to task worktree).
- Skills per role: N/A for Codex (it receives extracted Skill Contracts inline in task-N.md). For the post-merge Claude reviewer: `verification-before-completion`.
- Prompt template: Codex prompt is the task-N.md itself plus a fixed preamble baked into `codex-implement.py`.
- Each Codex session gets: full task-N.md content, `AGENTS.md`/`CLAUDE.md` hint (auto-loaded by Codex), and an isolated git worktree.

## Context Recovery
After compaction, re-read:
- `work/PIPELINE.md` (find current phase)
- `work/{feature}/tasks/*.md` (find tasks without a result file)
- `work/codex-implementations/task-*-result.md` (see which tasks finished and with what status)
- `work/codex-primary/codex-wave-report.md` (if exists — see aggregate run)

## Phase Output
Claude reviewer MUST produce a structured handoff block (see teammate-prompt-template.md) summarizing which tasks merged, which required FIX, and any scope-fence violations observed.

## Cross-links
- Scripts: `.claude/scripts/codex-implement.py`, `.claude/scripts/codex-wave.py`, `.claude/scripts/codex-scope-check.py`
- Skill: `.claude/skills/dual-implement/SKILL.md` (for per-task escalation to Level 3)
- Tech spec: `work/codex-primary/tech-spec.md` (Section 5.1)
- ADR: `.claude/adr/adr-012-codex-primary-implementer.md`
