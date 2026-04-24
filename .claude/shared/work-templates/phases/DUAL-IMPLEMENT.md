# Phase Template: DUAL-IMPLEMENT

> Every task runs BOTH a Claude teammate and Codex (GPT-5.5) in parallel worktrees against the same spec. Opus (or a judge agent with `cross-model-review` skill) compares diffs and picks or merges the winner. For high-stakes code where correctness cost dominates token cost.

## Metadata
- Default Mode: DUAL_IMPLEMENT
- Gate Type: AUTO
- Loop Target: FIX (on both-fail or judge-rejected winner)
- Max Attempts: 1
- Checkpoint: pipeline-checkpoint-IMPLEMENT

## Phase Context Loading
Before starting this phase, load:
- `work/{feature}/tech-spec.md` — architecture to implement
- `work/{feature}/tasks/*.md` — task definitions (every task must have `executor: dual` or `risk_class: high-stakes`)
- `.claude/memory/knowledge.md` — patterns, pitfalls, and module structure
- `.claude/skills/dual-implement/SKILL.md` — the protocol this phase runs
- `.claude/skills/cross-model-review/SKILL.md` — used by the judge agent
- `.claude/guides/teammate-prompt-template.md` — required for the Claude half
- `.claude/adr/adr-012-codex-primary-implementer.md` — rationale for dual

## Inputs
- `work/{feature}/tech-spec.md` (architecture)
- `work/{feature}/tasks/*.md` (every task with `executor: dual` or `risk_class: high-stakes`)

## Trigger
- Entire phase is high-stakes — every task declares `executor: dual` or `risk_class: high-stakes`.
- Phase explicitly declares `Mode: DUAL_IMPLEMENT` in PIPELINE.md (explicit pipeline override).
- Task touches auth, migrations, payments, crypto, or complex algorithms where correctness dominates.

## Dispatch
Each task spawns TWO parallel executors against the same task-N.md spec, in separate worktrees:

1. **Worktree A — Claude:** `TeamCreate` with a Claude teammate prompt built from `teammate-prompt-template.md`. Works inside `worktrees/dual-task-N/claude/`.
2. **Worktree B — Codex:** `codex-implement.py` scoped to `worktrees/dual-task-N/codex/`:

   ```bash
   py -3 .claude/scripts/codex-implement.py \
       --task work/{feature}/tasks/T1.md \
       --worktree worktrees/dual-task-N/codex \
       --result-dir work/codex-implementations
   ```

For multiple tasks in the phase, the dual pairs themselves can be batched:

```bash
py -3 .claude/scripts/codex-wave.py \
    --tasks work/{feature}/tasks/T1.md,work/{feature}/tasks/T2.md \
    --parallel 2 \
    --worktree-base worktrees/dual-wave/codex
```

(with matching `TeamCreate` waves for the Claude halves)

## Judge Step
After BOTH executors for a task finish (or one times out), Opus spawns a judge subagent loaded with:
- The original task-N.md spec
- Both diffs (claude.diff + codex.diff)
- Both test outputs
- The `cross-model-review` skill

Judge returns one verdict: `pick_a` | `pick_b` | `merge_hybrid` | `both_fail`.

## Merge Strategy
| Verdict | Action |
|---------|--------|
| `pick_a` | Merge `worktrees/dual-task-N/claude/` branch; archive Codex diff in `work/codex-implementations/task-N-losing-diff.md`. |
| `pick_b` | Merge `worktrees/dual-task-N/codex/` branch; archive Claude diff in `work/codex-implementations/task-N-losing-diff.md`. |
| `merge_hybrid` | Human intervention — Opus performs manual cherry-pick combining both diffs; both archived. |
| `both_fail` | BLOCKED — escalate to human, mark REWORK for the task. |

## Claude's Role
- **Before:** write a maximally tight spec (acceptance criteria + test commands + scope fence). Dual wastes tokens if the spec is ambiguous.
- **During:** orchestrate both executor halves and the judge. Do not edit source files in either worktree.
- **After:** merge the winning diff. Archive the loser for post-mortem. Route any `both_fail` to FIX.

## Process
1. Read tech spec and all task files. Validate every task has `executor: dual` and a clean Scope Fence.
2. For each task (tasks can themselves run in parallel if waves.md allows):
   a. Create two worktrees from the base branch: `worktrees/dual-task-N/claude/` and `worktrees/dual-task-N/codex/`.
   b. Spawn in parallel:
      - Claude teammate via `TeamCreate` — writes in claude worktree.
      - `codex-implement.py` — writes in codex worktree.
   c. Wait for both (respect `--timeout`; a hung executor is treated as a fail for judging).
   d. Spawn judge subagent with `cross-model-review` skill; pass both diffs + spec.
   e. Apply judge verdict per Merge Strategy table.
3. After all tasks resolved, merge winning branches sequentially. Run test suite between merges.
4. Run full test suite: `uv run pytest`
5. Run linter: `uv run ruff check .`
6. If all pass — phase complete.

## Outputs
- Source code files (new/modified, merged from winning worktrees)
- `work/codex-implementations/task-{N}-result.md` (Codex half, per task)
- `work/codex-implementations/task-N-losing-diff.md` (archived loser diff)
- `work/{feature}/dual-judge-report.md` (judge verdicts + rationale per task)
- `work/{feature}/test-results.md`

## Quality Gate
```bash
uv run pytest --tb=short -q
uv run ruff check .
py -3 .claude/scripts/codex-scope-check.py --diff <(git diff main...HEAD) --fence work/{feature}/tasks/T*.md
```

### Verdicts
- PASS: Every task resolved to `pick_a`, `pick_b`, or clean `merge_hybrid`; full test suite green; no lint errors.
- CONCERNS: Tests pass but judge cited minor disagreements between executors worth documenting.
- REWORK: One or more tasks resolved to `both_fail` — route to FIX or re-spec.
- FAIL: Judge itself cannot decide (spec ambiguity) — escalate to human; likely spec needs rewrite before re-running.

## When to Use
- Auth / authorization / session handling
- Database migrations (schema or data) where rollback is painful
- Payment, billing, crypto, cryptographic protocols
- Complex algorithms with non-obvious correctness
- Any task where two independent implementations are cheaper than one bug in production

## When NOT to Use
- Trivial / well-tested / low-risk tasks — dual wastes tokens.
- Ambiguous specs — both executors will diverge unhelpfully; fix the spec first, then pick a simpler mode.
- Token budget tight — single execution (`CODEX_IMPLEMENT` or `AGENT_TEAMS`) is cheaper.
- UX polish — subjective, judging is unreliable.

## Relationship to existing modes
These modes are **orthogonal** — pick whichever fits this phase:
- `AGENT_TEAMS` (Claude-only parallel via `TeamCreate`) — unchanged, remains primary for tasks requiring skills + memory context
- `AO_HYBRID` — unchanged, remains for full-Claude-context parallel within one project
- `AO_FLEET` — unchanged, remains for cross-project work
- `CODEX_IMPLEMENT` — all tasks to Codex (see `IMPLEMENT-CODEX.md`)
- `HYBRID_TEAMS` — per-task executor dispatch (see `IMPLEMENT-HYBRID.md`)
- `DUAL_IMPLEMENT` (this mode) — dual executors per task with Opus judging

Opus picks per phase based on task profile. `DUAL_IMPLEMENT` is the heaviest mode — reserve for correctness-critical code.

## Agent Team Config
- Team size per task: 2 executors + 1 judge = 3 agents concurrent per task.
- Roles:
  - Claude teammate (implementer) in worktree A.
  - Codex session (implementer) in worktree B.
  - Judge subagent with `cross-model-review` skill, spawned after both halves finish.
- Skills per role:
  - Claude teammate: `verification-before-completion` + task-specific (e.g., `security-review`).
  - Codex: N/A (receives extracted Skill Contracts inline).
  - Judge: `cross-model-review` (mandatory).
- Prompt template: Claude teammate uses `.claude/guides/teammate-prompt-template.md`. Codex prompt baked into `codex-implement.py`. Judge prompt built inline from `dual-implement` skill.
- Each executor gets: task-N.md, tech-spec.md, and its own isolated worktree.

## Context Recovery
After compaction, re-read:
- `work/PIPELINE.md` (find current phase)
- `work/{feature}/tasks/*.md` (identify tasks lacking a judge verdict)
- `work/codex-implementations/task-*-result.md` (Codex half)
- `work/{feature}/dual-judge-report.md` (verdicts so far)
- `worktrees/dual-task-*/` (see which worktrees are still live)

## Phase Output
Claude orchestrator MUST produce a structured handoff block listing, per task: judge verdict, winning worktree, merged commit, and any `both_fail` escalations.

## Cross-links
- Scripts: `.claude/scripts/codex-implement.py`, `.claude/scripts/codex-wave.py`, `.claude/scripts/codex-scope-check.py`
- Skill: `.claude/skills/dual-implement/SKILL.md` (the protocol this phase runs)
- Skill: `.claude/skills/cross-model-review/SKILL.md` (used by the judge)
- Guide: `.claude/guides/teammate-prompt-template.md`
- Tech spec: `work/codex-primary/tech-spec.md` (Section 5.3)
- ADR: `.claude/adr/adr-012-codex-primary-implementer.md`
