---
name: dual-implement
description: >
  Parallel dual implementation for high-stakes code: Claude and Codex implement
  the same task-N.md in worktrees; Opus judges diffs, picks winner or hybrid.
  Use when task has executor: dual or risk_class: high-stakes (auth, migration,
  payment, crypto, complex algorithm), or user says "dual implement".
  Do NOT use for UI polish, refactors, docs, ambiguous specs,
  or when single-executor is adequate.
roles: [implementer, reviewer]
---

# Dual Implementation (Level 3)

## Overview

Dual implementation runs **Claude** and **Codex (GPT-5.5)** in parallel against the same iron-clad `task-N.md` spec, each inside its own git worktree. When both finish, Opus acts as judge (wearing the `cross-model-review` skill): compare the two diffs against the acceptance criteria, pick the stronger one, or cherry-pick a hybrid. The weaker diff is archived, not merged.

**Core principle:** Two independent implementers, one immutable spec, one judge. You trade roughly 2× tokens for meaningfully lower bug rate on code where correctness cost dominates token cost.

**Preconditions:**
- `task-N.md` exists and has an IMMUTABLE Acceptance Criteria section, Scope Fence, and Test Commands (see `.claude/shared/work-templates/task-codex-template.md`)
- `.claude/scripts/codex-implement.py` is present and executable (T1 output)
- `codex` CLI authenticated and `AGENTS.md` at repo root
- Base branch is clean (no uncommitted changes in files inside the Scope Fence)

## Triggers

Invoke this skill when ANY of:

- Task frontmatter has `executor: dual`
- Task frontmatter has `risk_class: high-stakes`
- Task touches auth, session management, payment, crypto, DB migration, or a non-trivial algorithm (sorting, scheduling, rate limiting, concurrency)
- User explicitly says "dual implement", "run both", "compare implementations", "dual-impl this", or similar
- Phase Mode in `work/PIPELINE.md` is `DUAL_IMPLEMENT`

If none of the above match → use Level 2 (single executor via `HYBRID_TEAMS` / `CODEX_IMPLEMENT` / plain `TeamCreate`) instead.

## When NOT to use

| Situation | Use instead |
|-----------|-------------|
| Trivial / low-risk change (< 50 lines, docs, config) | Single executor via `TeamCreate` or Codex single |
| UI polish, CSS, frontend styling | `TeamCreate` with Claude teammate (Opus is stronger here) |
| Ambiguous spec — acceptance criteria not iron-clad | Fix the spec first (`task-decomposition`); both executors will diverge unhelpfully |
| Cross-project / fleet operation | `ao-fleet-spawn` (dual-implement is single-project only) |
| Token budget tight | Level 2 single execution — dual roughly doubles spend |
| Task already proven easy for one executor with passing tests | Don't pay 2× for redundant confirmation |
| Spec depends on reading between lines, implicit context | Claude-only via `TeamCreate` — Codex refuses ambiguity |

## Protocol

Follow these steps in order. Do not skip the fence check or the judge step.

### 1. Verify trigger and preconditions

- Read `task-N.md`. Confirm `executor: dual` in frontmatter OR risk_class warrants dual.
- Confirm Acceptance Criteria are marked IMMUTABLE, Scope Fence is present, Test Commands exit code is defined.
- Verify `codex` CLI is authenticated (`codex --version` works).
- Verify base branch is clean for all files in Scope Fence (`git status`).

If any precondition fails → STOP. Either fix the spec (run `task-decomposition` again), install/authenticate Codex, or drop to Level 2.

### 2. Create two isolated worktrees

Both worktrees start from the same base commit. Names must be distinct and include the task id.

```bash
BASE_BRANCH=$(git rev-parse --abbrev-ref HEAD)
TASK_ID=T{N}
mkdir -p worktrees/dual-${TASK_ID}

git worktree add "worktrees/dual-${TASK_ID}/claude" -b "dual-${TASK_ID}-claude" "${BASE_BRANCH}"
git worktree add "worktrees/dual-${TASK_ID}/codex"  -b "dual-${TASK_ID}-codex"  "${BASE_BRANCH}"
```

See `using-git-worktrees` skill for recovery if a worktree is corrupted.

### 3. Spawn both executors in parallel

Both start at approximately the same wall-clock time. They MUST NOT share state.

**Claude branch** — spawn a teammate via `TeamCreate` + `spawn-agent.py`:

```bash
py -3 .claude/scripts/spawn-agent.py \
    --task "Implement task-${TASK_ID} in worktree worktrees/dual-${TASK_ID}/claude per its IMMUTABLE spec. Do NOT modify test files or acceptance criteria. Stay inside Scope Fence." \
    --team "dual-${TASK_ID}" \
    --name "claude-impl" \
    -o work/dual-${TASK_ID}/prompts/claude-prompt.md

# Then TeamCreate with that prompt (Claude teammate reads skills, memory, hooks).
```

The Claude teammate MUST:
- Work ONLY inside `worktrees/dual-${TASK_ID}/claude`
- Get `verification-before-completion` skill embedded
- Output the standard `=== PHASE HANDOFF ===` block

**Codex branch** — spawn `codex-implement.py` as a background process in the Codex worktree:

```bash
py -3 .claude/scripts/codex-implement.py \
    --task "work/{feature}/tasks/${TASK_ID}.md" \
    --worktree "worktrees/dual-${TASK_ID}/codex" \
    --result-dir "work/dual-${TASK_ID}/results" \
    --timeout 3600 \
    > work/dual-${TASK_ID}/logs/codex.log 2>&1 &
```

Codex runs under `--sandbox workspace-write` scoped to that worktree. Its result lands at `work/dual-${TASK_ID}/results/${TASK_ID}-result.md` with `status`, diff, test output, self-reported blockers.

### 4. Wait for both to finish

- Block until the Claude teammate emits its `=== PHASE HANDOFF ===` block AND `work/dual-${TASK_ID}/results/${TASK_ID}-result.md` exists.
- Each has an independent timeout (default 60 min); failure of one does NOT implicitly fail the other.
- If one times out: treat that branch as a failure in judging — the other can still win by default.

### 5. Post-flight scope check (both branches)

Run `codex-scope-check.py` on each diff. Any fence violation → rollback that branch with `git reset --hard` in its worktree, mark it FAILED in judging input.

```bash
py -3 .claude/scripts/codex-scope-check.py \
    --diff <(cd worktrees/dual-${TASK_ID}/claude && git diff "${BASE_BRANCH}") \
    --fence work/{feature}/tasks/${TASK_ID}.md

py -3 .claude/scripts/codex-scope-check.py \
    --diff <(cd worktrees/dual-${TASK_ID}/codex && git diff "${BASE_BRANCH}") \
    --fence work/{feature}/tasks/${TASK_ID}.md
```

### 6. Spawn judge with cross-model-review skill

Judge is a fresh Claude subagent (do NOT reuse either implementer). Input: both diffs + both test outputs + the original `task-N.md` spec. Judge MUST have the `cross-model-review` skill embedded.

Judge prompt structure:
- Full `task-N.md` content (spec + Acceptance Criteria + Scope Fence)
- Claude diff + Claude test output + Claude handoff block
- Codex diff + Codex test output + Codex `result.md`
- Explicit instruction: cite evidence from the diffs. Do NOT defer to either model. Check each AC against each diff.

Judge verdict must be one of: `pick_claude | pick_codex | merge_hybrid | both_fail`.

### 7. Act on verdict

| Verdict | Action |
|---------|--------|
| `pick_claude` | Merge `dual-${TASK_ID}-claude` branch into base. Archive Codex diff to `work/dual-${TASK_ID}/archive/codex.diff`. |
| `pick_codex`  | Merge `dual-${TASK_ID}-codex` branch into base. Archive Claude diff to `work/dual-${TASK_ID}/archive/claude.diff`. |
| `merge_hybrid` | Escalate to Opus for manual cherry-pick. Archive both diffs. Judge report explains which hunks from which side. |
| `both_fail`   | Do NOT merge either. Mark task BLOCKED. Archive both diffs and test outputs. Escalate to human. |

After merge, re-run Test Commands on the base branch to confirm no regression.

### 8. Cleanup

```bash
git worktree remove "worktrees/dual-${TASK_ID}/claude"
git worktree remove "worktrees/dual-${TASK_ID}/codex"
# Keep the result files and archive/ for auditability.
```

Delete the losing branch ONLY after the winner is merged and tests pass on base.

### 9. Record outcome

Append to `work/results-board.md` and update `work/PIPELINE.md`:
- Which side won (and why — quote the judge evidence)
- Any surprising divergence (often reusable pattern for `knowledge.md`)
- Total wall-clock cost vs estimated single-executor time

## Examples

### Example 1: Auth middleware replacement

Old JWT middleware stored session tokens in a way that failed compliance review. Replacement must: accept legacy tokens during a 30-day migration window, reject them after, never leak PII in logs, add structured logging per `logging-standards`. Legal risk — correctness cost >> token cost.

- `task-T3.md` written with `executor: dual`, `risk_class: high-stakes`, Scope Fence locked to `auth/middleware.py` + `auth/migration.py`, four ACs, Test Commands cover legacy-accept + post-window-reject + no-PII + logging coverage.
- Two worktrees spawned. Claude teammate takes ~28 min and structures via a legacy-token adapter class. Codex finishes in ~18 min with an inline branch in the verify function.
- Scope check: both pass. Tests: both pass. Judge (cross-model-review) cites: Claude's adapter is cleaner for the 30-day cutover but misses a timing-attack edge case on the legacy path; Codex has tighter verification but no seam for the eventual removal.
- Verdict: `merge_hybrid` — take Codex's verify logic, Claude's adapter shell. Opus cherry-picks accordingly. Base tests green.

### Example 2: DB migration with backfill

A non-null column added to a 5M-row `orders` table needs two migrations (add nullable + backfill + switch to not-null) with zero downtime. See `database-migrations` skill for the safe pattern.

- `task-T7.md` gets `executor: dual` because a wrong migration is unrecoverable in prod.
- Claude proposes concurrent index + transaction wrap. Codex proposes batched UPDATE loop. Both pass smoke tests on 10k-row fixture.
- Judge checks both against `database-migrations` contract (safe patterns, rollback plan, no full-table lock). Codex's batched loop respects the contract more strictly; Claude's single UPDATE risks a long lock on production-sized data.
- Verdict: `pick_codex`. Claude's diff archived with the judge's rationale for future reference.

### Example 3: When to drop to Level 2 instead

A typo fix in an error message string. User reflexively says "dual implement this."

- Check triggers: no `executor: dual`, no `risk_class: high-stakes`, no high-risk domain keywords, just a string literal change.
- Matching `When NOT to use` row: "Trivial / low-risk change (< 50 lines, docs, config)".
- Skip this skill. Apply fix directly or via single `TeamCreate` teammate. Do not spawn two worktrees for a one-line edit.

## Streaming judge (speed optimization)

Default flow waits for ALL pairs to finish before judging any. **Streaming
judge** starts per-pair judging the moment pair `i` finishes, regardless of
whether pairs `j != i` are still running. Reduces wall-time by overlapping
judge latency with remaining executor latency.

When to use: when N ≥ 3 subtasks AND pair latencies are uneven (slowest
dominates default wall-time; streaming hides judge latency inside slowest).

How to use: `dual-teams-spawn.py` emits per-pair "ready" signals into
`work/<feature>/dual-teams-plan.md` as each `(claude-T{i}, codex-T{i})`
pair completes. Opus (orchestrator) polls the plan and calls `judge.py`
on ready pairs immediately. Merge happens sequentially regardless.

Implementation knob: `dual-teams-spawn.py --judge-mode=streaming`
(default: `barrier`).

## Cherry-pick hybrid (quality optimization)

Instead of the binary `pick_a | pick_b` default, the judge may return
`merge_hybrid` when the two sides excel on different axes (e.g., Claude's
test coverage is better but Codex's algorithm is tighter). Opus then
manually cherry-picks the strongest functions/sections from each diff.

When to use: when `judge.py` (or `cross-model-review`) reports similar
aggregate scores (delta < 0.05) but divergent axis-level winners.

Mechanic:
1. `judge.py` verdict JSON has `rationale_auto` naming the dominant axis
   per side.
2. If scores are close + axes are orthogonal: Opus invokes
   `cross-model-review` skill to get a per-function/per-section pick list.
3. Opus applies the pick list via manual `git cherry-pick -p` or explicit
   file-level merge; both losing halves (the rejected parts) are archived
   at `work/<feature>/dual-history/T{i}/` with annotation.
4. Opus re-runs all Test Commands on the hybrid to confirm it passes both
   sides' invariants before committing.

When NOT to use: when judge verdict is decisive (delta ≥ 0.1) or when the
task is small enough that the merge effort exceeds the quality gain.

## Related

- [cross-model-review](../cross-model-review/SKILL.md) — judge uses this skill to compare the two diffs; core tool for Step 6
- [verification-before-completion](~/.claude/skills/verification-before-completion/SKILL.md) — embedded in both implementer prompts; evidence-based completion gate
- [subagent-driven-development](~/.claude/skills/subagent-driven-development/SKILL.md) — underlying pattern for the Claude branch (TeamCreate dispatch)
- [using-git-worktrees](~/.claude/skills/using-git-worktrees/SKILL.md) — worktree creation, isolation, and recovery in Step 2
- [ao-hybrid-spawn](~/.claude/skills/ao-hybrid-spawn/SKILL.md) — alternative for full-Claude-context parallel when Codex is unavailable or unsuitable
- `.claude/guides/codex-integration.md` — full Codex CLI setup and advisor stack context
- `.claude/shared/work-templates/task-codex-template.md` — the `task-N.md` format this skill consumes
