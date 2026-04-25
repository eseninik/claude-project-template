---
status: ACTIVE
mode: AUTONOMOUS
created: 2026-04-25
goal: Eliminate Y6+Y7 regressions via elegant sentinel-based fix; achieve 2 consecutive clean dual-teams runs; build new functional verification task; 2 more clean runs; declare PoC stable.
---

# PIPELINE — Round 2 fix + 2× clean validation + new functional check + 2× more clean runs

> Autonomous mode. User stepped away. Carte blanche to fix, test, loop until success.

## Diagnoses (refined from session resume context)

- **Y7-real (was misdiagnosed as missing `@` prefix)** — `codex-implement.preflight_worktree` refuses dirty tree → sees freshly-written `.dual-base-ref` (FIX-B sidecar) as untracked user work → kills Codex in 0.85s. Wave-runner re-labels rc=2 as `status=scope-violation`, hiding the real cause.
- **Y6-real** — `codex-delegate-enforcer.py` PreToolUse hook does not detect that the Claude teammate is operating inside a dual-teams worktree (its `worktrees/**` exempt only matches when the path is project-root-relative, but the teammate resolves paths inside its own worktree). First `Edit`/`Write` is denied → teammate retries → 600s watchdog kill.

## Elegant fix (single sentinel, two checks)

Use `.dual-base-ref` itself as the **dual-teams worktree signal**.
1. `.gitignore` — add `.dual-base-ref` so `git status --porcelain` no longer lists it. Makes `preflight_worktree` happy without weakening its safety against actual user-work loss. Also covers any future stray base-ref creation.
2. `codex-delegate-enforcer.py` — at hook entry, walk CWD ancestors for `.dual-base-ref`. If found → `permissionDecision=allow` + log `dual-teams-worktree`. Reason: dual-teams flow already provides Codex coverage in parallel; enforcer would otherwise deadlock the writer half.

Tests added for both. Existing 38 + 25 + 23 unit-test suites stay green.

## Phases

### Phase 1: FIX  <- CURRENT
- [ ] T1.1: Codex second opinion on the sentinel approach (heard once, refine)
- [ ] T1.2: Add `.dual-base-ref` to project-root `.gitignore`
- [ ] T1.3: Patch `codex-delegate-enforcer.py` — sentinel ancestor walk before resolve
- [ ] T1.4: Patch tests `test_codex_delegate_enforcer.py` — add dual-teams sentinel exempt test
- [ ] T1.5: Add small regression test in `test_codex_implement.py` covering "preflight ignores .dual-base-ref because git ignores it"
- [ ] T1.6: Update `.claude/memory/knowledge.md` — replace stale Y7 gotcha with the real one
- [ ] T1.7: Run all three test suites green
- [ ] Gate: 0 unit-test failures + Codex second opinion captured + activeContext updated

### Phase 2: VALIDATE-1 (1st clean dual-teams run)
- [ ] T2.1: Cleanup four stale validation worktrees (V-1, V-2 × claude+codex)
- [ ] T2.2: Re-launch dual-teams-spawn for V-1 + V-2 (codex-wave + Claude teammates in parallel)
- [ ] T2.3: Wait for both sides to complete; confirm scope-checks pass; Codex result.md populated
- [ ] T2.4: Run judge for each pair → emit verdicts
- [ ] T2.5: All 4 implementations PASS (status=pass + tests green) → Phase 2 done
- [ ] Gate: 4/4 pass; verdicts in work/validation/verdicts/

### Phase 3: VALIDATE-2 (2nd clean dual-teams run)
- [ ] T3.1: Same as Phase 2 but with **fresh task IDs** (V-3 + V-4) — same kind of task, different files, to avoid worktree-reuse confound
- [ ] T3.2: Run; confirm 4/4 pass again
- [ ] Gate: 2 consecutive clean runs achieved → Y6+Y7 fix verified

### Phase 4: NEW VERIFICATION TASK
- [ ] T4.1: Design a single end-to-end "self-test" task that exercises ALL fixed surfaces:
   - Creates a fake worktree with `.dual-base-ref`
   - Runs preflight → must pass
   - Spawns delegate-enforcer simulation → must allow
   - Runs codex-wave + dual-teams together
   - Verifies judge axes score correctly on committed + untracked changes
- [ ] T4.2: Implement as `.claude/scripts/dual-teams-selftest.py` (read-only, no side effects beyond a tmp dir)
- [ ] T4.3: Add unit tests
- [ ] Gate: self-test passes locally

### Phase 5: VALIDATE-3 (run new self-test + dual-teams)
- [ ] T5.1: Run `dual-teams-selftest.py` → pass
- [ ] T5.2: Re-run dual-teams V-5 + V-6 (yet another fresh pair) using the same fix
- [ ] T5.3: 4/4 pass + selftest pass
- [ ] Gate: 1st clean run with new functional check

### Phase 6: VALIDATE-4 (2nd clean run with new check)
- [ ] T6.1: Same again — V-7 + V-8 + selftest
- [ ] Gate: 2 consecutive clean runs WITH new functional check → declare PoC stable

### Phase 7: COMMIT + ACTIVECONTEXT + KNOWLEDGE
- [ ] T7.1: Single commit per phase with checkpoint tag
- [ ] T7.2: Update activeContext.md (Did/Decided/Learned/Next)
- [ ] T7.3: Update knowledge.md with Y6/Y7 corrected gotcha + sentinel pattern
- [ ] Final: Status=PIPELINE_COMPLETE

## Speed/quality improvements bundled in

The user asked for elegance + speed + quality. Bundled improvements:
- Single sentinel file → one mental model for "this is a dual worktree" (used in 2+ places)
- New `dual-teams-selftest.py` script → catches regressions without needing live codex (cheap fast)
- Clearer wave-runner status: `DirtyWorktreeError` no longer hides under `scope-violation` (T2.4 will adjust if relevant)

## Rollback policy

If 3+ consecutive failed validation rounds → STOP, hand the diagnostic context to the user, archive worktrees under `work/validation/failed-rounds/<timestamp>/`.
