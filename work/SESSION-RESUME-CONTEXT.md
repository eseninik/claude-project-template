# Session Resume Context — 2026-04-25 (terminal restart needed)

> Save this. Restart terminal. New session reads this file first to resume exactly where we stopped.

## TL;DR — Where we are

**Round 1 (bug fixes) — DONE.** Y1 + Y2 + Y3 all merged into `fix/watchdog-dushnost`.
**Round 2 (stealth test #1) — FAILED.** Both V-1 + V-2 Claude teammates stalled by watchdog (600s no progress) before producing any code.
**Codex side of stealth test #1** — codex-wave PID 4652 was running when terminal broke; status unknown. May have completed either V-1 or V-2 or both.

## Round 1 results (already complete + merged)

Branch: `fix/watchdog-dushnost`
HEAD before stealth test #1 was launched: `9d01f21`

| Commit | What it fixed |
|--------|---------------|
| `d3dfe19` | Y1 + Y3 docs: heredoc + Windows .CMD gotchas in `task-codex-template.md` and `teammate-prompt-template.md` |
| `55d03d0` | Y2 fix-A claude: `judge_axes.py` + `judge.py` + tests — `_ensure_untracked_visible`, `_resolve_base`, `git diff <base>` semantics |
| `184f897` | Merge fix-A (TIE → Claude) |
| `faeb27c` | Y2 fix-B claude: `.dual-base-ref` sidecar in `dual-teams-spawn.py` + `codex-wave.py` |
| `9d01f21` | Merge fix-B (TIE → Claude) |

Test suite green:
- `test_judge.py`: 39 tests OK (28 pre-existing + 11 new)
- `test_dual_teams_spawn.py`: 21 tests OK
- `test_codex_wave.py`: 25 tests OK

Live verification (already done):
- Y2 axes that previously SKIP'd ("empty diff", "no modified .py files") now SCORE on both committed and untracked sides. `logging_coverage` 0.116-0.124, `lint_clean` 1.000 — proving the bug is fixed.
- `.dual-base-ref` sidecars present in all 4 freshly-created worktrees with correct base SHA `9d01f21...` — proving FIX-B works at orchestration time.

## Round 2 status (validation stealth test #1) — FAILED ALL 4

**ALL FOUR implementations failed.** Diagnosis confirmed from log inspection:

| Side | Task | Outcome | Root cause |
|------|------|---------|------------|
| Claude V-1 | knowledge-decay-report | watchdog stall @ 600s | Y6 (NEW bug — unknown) |
| Claude V-2 | task-spec-validator | watchdog stall @ 600s | Y6 (NEW bug — unknown) |
| Codex V-1 | knowledge-decay-report | scope-violation rc=2 in 0.85s | Y7 (known: scope-fence missing `@` prefix for new-file mode) |
| Codex V-2 | task-spec-validator | scope-violation rc=2 in 0.85s | Y7 (same) |

### Y7 — task spec scope-fence missing `@` prefix (KNOWN gotcha)

Both task specs declared:
```
**Allowed:**
- `.claude/scripts/knowledge-decay-report.py` (new)
- `.claude/scripts/test_knowledge_decay_report.py` (new)
```

Per known gotcha "Codex Scope-Fence File Mode Needs Explicit @ Prefix" (already in `.claude/memory/knowledge.md`), for FILE-mode (single-file new file) the scope-check expects `@<path>` syntax:
```
**Allowed:**
- `@.claude/scripts/knowledge-decay-report.py` (new)
- `@.claude/scripts/test_knowledge_decay_report.py` (new)
```
Without `@`, codex-scope-check.py interprets the line as something else and rejects all diffs as out-of-scope.

**This is a known gotcha I forgot to apply when authoring V-1 / V-2 specs.** Easy fix: add `@` prefix to all "Allowed:" lines in both spec files, then re-launch.

### Y6 — Claude teammate watchdog stall (NEW bug, needs investigation)

Both V-1 Claude (`aff8c29010123e752`) and V-2 Claude (`a06c935f5b6b25b6f`) stalled at the SAME flow point — right after their initial 2-3 reads, before any Write attempt. Last messages:
- V-1: "Now I have the full context. Let me explore the existing memory-engine.py and knowledge.md to understand the format."
- V-2: "Now let me look at canonical template reference and existing task spec to understand the structure."

Both stalled for 600s before being killed. Same flow point + symmetric failure = systemic, not coincidence.

**Hypotheses to test on resume:**
1. **Hook deadlock** — codex-watchdog.py / codex-parallel.py / codex-stop-opinion.py blocks indefinitely on first Bash use after worktree-cd. Test: run `py -3 .claude/hooks/<each-hook>.py` manually in a fresh shell, see if it returns.
2. **Prompt size** — both teammate prompts were 309 lines. Maybe new sub-agent harness throttles or chokes on 1.5K+ token initial context.
3. **Tool hook chain** — PostToolUse hook produces output that's piped into next tool input on Windows in a way that blocks stdin. Specifically: Read tool's output going through codex-parallel.py.

Easiest experiment: spawn a single Claude teammate with a TINY prompt (100 lines) and a trivial task (touch a file in work/). If it also stalls → harness/hook issue, not size. If it succeeds → size issue, need to compress spawn-agent.py output.

### Background process state on terminal-restart

- codex-wave PID 4652: **DEAD** (wave completed at 22:22:46 — both tasks failed scope-check fast, parent exited cleanly)
- No orphaned codex-implement.py / codex.exe processes
- 2 failed Agent tasks already returned (not running)
- Monitor `baemhvdwr` already auto-cleared (timed out)

**Nothing to kill. Clean restart.**

### Preserved artefacts (do NOT delete)

- `worktrees/validation/{claude,codex}/task-V1-*` and `task-V2-*` — 4 worktrees with sidecars present, just no commits/output
- `work/validation/tasks/task-V1-knowledge-decay-report.md` — broken spec (missing @)
- `work/validation/tasks/task-V2-task-spec-validator.md` — broken spec (missing @)
- `.claude/logs/codex-wave-validation-1777058565.log` — full log for Y6/Y7 forensics

## What to check on restart

1. **Is codex-wave PID 4652 still alive?**
   ```powershell
   Get-WmiObject Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like "*codex-wave*validation*" } | Select-Object ProcessId,CommandLine
   ```
   If yes: it's still producing Codex output for V-1 and/or V-2.

2. **Did Codex produce any results?**
   ```bash
   ls -la worktrees/validation/codex/task-V1-knowledge-decay-report/work/codex-implementations/ 2>/dev/null
   ls -la worktrees/validation/codex/task-V2-task-spec-validator/work/codex-implementations/ 2>/dev/null
   ```

3. **Read codex-wave log:**
   `.claude/logs/codex-wave-validation-1777058565.log`

## Decision tree on restart

### Path A: codex-wave still running, terminate cleanly first
```powershell
Stop-Process -Id 4652 -Force
# Then kill any orphaned codex-implement.py / codex.exe children (use Get-WmiObject above)
```

### Path B: codex-wave finished, both Codex sides have result.md
- Skip Claude side (both stalled). This is itself a finding worth documenting.
- Consider: re-launch Claude teammates with shorter task or different approach. Or skip Claude entirely for this round and judge "Codex-only".
- Better: investigate WHY both Claude teammates stalled at 600s — the same point in their flow ("about to read X, let me explore Y"). Might be a hook issue.

### Path C: codex-wave finished, no Codex results
- Wave failed silently. Check the log + circuit-state.json.

### What to do next regardless of path

The Claude-teammate-stall is itself a NEW bug worth investigating before continuing:
- **Y6 (new)**: Background Claude teammates appear to stall at the very beginning of their work (after first 1-2 reads), get killed by 600s watchdog. Both V-1 and V-2 stalled at the same flow point.
- Hypothesis: PostToolUse hook stuck in deadlock (codex-parallel.py or codex-watchdog.py). Or: writing extensive task prompts caused harness throttling. Or: my dual-teams-spawn prompt was 309 lines — possibly too verbose for new sessions.

## Known good state for resume

Working tree dirty? Run `git status --short` first. If only `.claude/memory/activeContext.md` modified, that's expected (auto-update). If anything else, investigate before continuing.

Branch: `fix/watchdog-dushnost`. Don't switch.

## Pending tasks (after sorting Round 2)

1. **Investigate Y6** (Claude teammate stall) — reproducible? Hook issue? Watchdog tuning?
2. **Re-run stealth test #1** (V-1 + V-2) once Y6 is understood.
3. **Stealth test #2** (different scenarios) — only after #1 yields 10/10.
4. **Per-user contract**: TWO consecutive perfect runs needed for "production-ready" verdict.

## Files to read on resume

In order:
1. **`work/SESSION-RESUME-CONTEXT.md`** — this file (you're here)
2. **`work/observability/debrief.md`** — round 0 (the original 4-bug discovery)
3. **`work/fixes/verdicts/`** — verdict JSONs from Round 1
4. **`work/validation/dual-teams-plan.md`** — Round 2 plan as launched
5. **`.claude/logs/codex-wave-validation-1777058565.log`** — Round 2 codex-wave log
6. **`work/validation/tasks/task-V1-*.md` and `task-V2-*.md`** — Round 2 task specs

## Quick commands cheatsheet

```bash
# Status
git log --oneline -5
git status --short
git worktree list

# Test fixes still working
py -3 .claude/scripts/test_judge.py 2>&1 | grep -E "Ran |OK|FAIL"
py -3 .claude/scripts/judge.py --help | grep base

# Cleanup validation worktrees if abandoning Round 2
for wt in worktrees/validation/claude/* worktrees/validation/codex/*; do
  [ -d "$wt" ] && git worktree remove --force "$wt"
done

# OR — re-run Round 2 from scratch (after Y6 investigation)
py -3 .claude/scripts/dual-teams-spawn.py \
  --tasks work/validation/tasks/task-V1-knowledge-decay-report.md,work/validation/tasks/task-V2-task-spec-validator.md \
  --feature validation \
  --parallel 2 \
  --worktree-base worktrees/validation
```

## Verdicts so far (the 1st round)

```
work/fixes/verdicts/task-FIX-A-verdict.json: TIE delta=-0.0015
work/fixes/verdicts/task-FIX-B-verdict.json: TIE delta=+0.0003
```

Both axes that were broken (logging_coverage, lint_clean) now produce real scores on both committed-and-untracked sides. Y2 fix is verified live, not just in unit tests.

## Background tasks that need cleanup before restart

- `codex-wave PID 4652` (likely orphaned) — kill it
- Monitor task `baemhvdwr` (timed out — auto-cleared)
- Two failed agent tasks — already returned, no cleanup needed

---

End of context. New session: read this top-to-bottom, decide path A/B/C, continue.
