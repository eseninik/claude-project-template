# Phase Mode: `DUAL_TEAMS` — parallel Claude teammates + Codex wave

> Every code-writing subtask in the phase runs on **both** tracks in parallel:
> N Claude teammates (via `TeamCreate` + `spawn-agent.py`) **and** N Codex
> sessions (via `codex-wave.py`) consume the same `tasks/T*.md` specs. Opus
> judges each `(Claude-diff, Codex-diff)` pair, picks a winner per subtask,
> merges winners into the main branch.
>
> This is Level 3 (`dual-implement` skill) scaled to the team level. It is
> the default `IMPLEMENT`-phase mode for any work with 3+ independent
> subtasks under the Always-Dual Code Delegation Protocol (CLAUDE.md).

## When to use

- `IMPLEMENT` phase with 3+ independent parallel subtasks
- Big features / refactors where both convergent-design signal and per-pair
  merit judging pay for themselves
- Any phase where Agent Teams alone or `CODEX_IMPLEMENT` alone would leave
  50 % of the "Always-Dual" contract unfulfilled

## When NOT to use

- Phases where every subtask is pure documentation or spec writing
  (use `SOLO` or `AGENT_TEAMS`)
- Phases with 1 subtask (use `dual-implement` skill directly)
- Tasks whose spec is not yet stable (both sides will diverge on ambiguity —
  fix the spec first)
- Phases where the dual-history / worktree footprint would exceed disk or
  Codex-rate-limit budget (fall back to `AGENT_TEAMS` + manual `dual-implement`
  on selected high-stakes subtasks)

## Dispatch

1. Opus writes the plan: one `tasks/T{i}.md` file per independent subtask,
   each with IMMUTABLE Acceptance Criteria, Scope Fence, Test Commands,
   `speed_profile` hint, and Skill Contracts.
2. Opus creates worktrees `worktrees/<feature>/claude/T{i}` and
   `worktrees/<feature>/codex/T{i}` for every subtask.
3. **Parallel launch (both sides at once, no sequential dependency):**
   - **Claude side** — `TeamCreate <feature>-claude` + one `spawn-agent.py`
     per subtask, with the worktree path embedded in the prompt. Teammates
     work independently; each commits on branch `claude/T{i}`.
   - **Codex side** — `py -3 .claude/scripts/codex-wave.py --tasks
     work/<feature>/tasks/T1.md,...,TN.md --parallel <N> --worktree-base
     worktrees/<feature>/codex` — each Codex session lives in its own
     worktree, consumes the same `T{i}.md` spec, produces
     `task-T{i}-result.md`.
4. **Barrier**: Opus waits for all `2N` agents to finish (wall-time ≈
   `max(task_i)`, not sum).
5. **Judge per pair** — either objectively via `.claude/scripts/judge.py`
   (test-driven scored verdict) or subjectively via the `cross-model-review`
   skill. Streaming mode is allowed: begin judging `(claude-T{i}, codex-T{i})`
   as soon as both sides of pair `i` finish, without waiting for other pairs.
6. **Merge winners** — for each subtask, merge the winner branch into the
   main feature branch (`--no-ff`). Archive loser diffs at
   `work/<feature>/dual-history/T{i}/<loser>-diff.diff`.
7. **Cleanup** — remove worktrees, delete per-subtask branches after merge.

## Parallelism limits

| Parameter | Default | Raise with |
|-----------|---------|------------|
| Claude teammates | `N` (= subtask count) | Harness tolerates up to ~10 in parallel |
| Codex `--parallel` | `3` | Raise carefully; $20 Codex tier rate-limits ≈ 4-5 concurrent |
| Total wall-time | `max(task_i) + judge_overhead` | Mostly bound by slowest task |

## Claude's role

Claude (Opus) does 4 things in this mode:

1. **Plans** the task decomposition and writes the `T{i}.md` specs.
2. **Spawns** both parallel tracks (TeamCreate + codex-wave).
3. **Judges** each `(claude, codex)` pair on merit — objective via
   `judge.py` where possible, subjective for style tie-breaks.
4. **Merges** winners, archives losers, commits with a clear dual-history
   trail.

Claude does NOT itself write implementation code in DUAL_TEAMS mode —
Claude teammates spawned via `spawn-agent.py` do the Claude-side writing,
in their own worktrees. (Claude can still refine/fix the merged result
after judging, subject to the `codex-delegate-enforcer.py` gate.)

## Enforcement

The Always-Dual Code Delegation Protocol (CLAUDE.md) is enforced by the
hook `.claude/hooks/codex-delegate-enforcer.py` at `PreToolUse(Edit|Write|MultiEdit)`.
In `DUAL_TEAMS` mode, every winning subtask commit has a fresh
`task-T{i}-result.md` covering its path → post-merge refinements pass the
gate. Losers leave no cover; that is intentional.

## Handoff block (Opus, per-pair, added to PIPELINE.md Decisions)

```
=== DUAL-TEAMS PAIR JUDGE: T{i} ===
Winner: claude | codex | hybrid
Test-scores: claude={S_c}, codex={S_g}   (from judge.py)
Rationale: [objective deltas that decided the call]
Loser archive: work/<feature>/dual-history/T{i}/...
Commit: [sha of merge]
=== END PAIR JUDGE ===
```

## Relationship to other modes

- `AGENT_TEAMS` (Claude-only parallel) — subset of `DUAL_TEAMS`; use when
  the work is pure documentation / spec / non-code and Codex participation
  would be wasted.
- `CODEX_IMPLEMENT` (Codex-only wave) — subset of `DUAL_TEAMS`; use only
  when Claude-side would add zero quality signal (rare) and speed matters
  more than merit compare.
- `DUAL_IMPLEMENT` (single-task Level 3) — 1-subtask version of `DUAL_TEAMS`.
  Use when the phase has exactly one subtask that is high-stakes enough
  to want both sides.
- `AO_HYBRID` and `AO_FLEET` — still available for full-Claude-context
  parallelism or cross-project work; those don't compose with Codex wave
  today (future work).

## Example PIPELINE.md phase

```markdown
### Phase: IMPLEMENT
- Status: PENDING
- Mode: DUAL_TEAMS
- Attempts: 0 of 2
- On PASS: -> QA_REVIEW
- On FAIL: -> FIX
- On BLOCKED: -> STOP
- Gate: for every T{i}.md, winning side's tests pass AND pair was judged on merit (not default-winner)
- Gate Type: AUTO (judge.py) + USER_APPROVAL (winner verdict when test-scores tie)
- Inputs: work/<feature>/tasks/T1..TN.md
- Outputs: main-branch merge commits per subtask + dual-history losers archived
- Checkpoint: pipeline-checkpoint-IMPLEMENT-DUAL-TEAMS
```
