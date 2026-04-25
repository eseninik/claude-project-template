---
executor: dual
risk_class: routine
reasoning: high
speed_profile: balanced
---

# Task Y8: codex-gate.py — exempt dual-teams worktrees via `.dual-base-ref` sentinel (mirror Y6 fix)

## Your Task

**Y8 root cause.** `.claude/hooks/codex-gate.py` is a `PreToolUse` hook that blocks `Edit`/`Write`/`MultiEdit` when EITHER:
- (a) last `codex-ask` consultation was > `COOLDOWN_MINUTES = 5` minutes ago, OR
- (b) > `MAX_EDITS_PER_CONSULTATION = 5` edits have happened since last consultation.

Both gates fire deterministically when a Claude **sub-agent** runs inside a dual-teams worktree for 10–15 minutes (typical task duration). Sub-agents inherit the orchestrator's `codex-ask` freshness state but can't easily trigger UI to refresh it. Result: their first post-cooldown Edit is denied → Phase 3 V-3 and V-4 teammates resorted to PowerShell `[System.IO.File]::WriteAllText` workarounds.

The Y6 fix already solved an exactly-analogous problem in `codex-delegate-enforcer.py`: walk ancestors looking for `.dual-base-ref` sentinel; when present → auto-allow. Same fix, same sentinel, different hook.

**Implement an `is_dual_teams_worktree(project_dir: Path) -> bool` helper at module scope (mirror the existing one in `codex-delegate-enforcer.py`) and call it at the start of `codex-gate.py`'s PreToolUse path. If True → log `dual-teams-worktree`, exit 0 (allow), skip the cooldown check entirely.** Rationale identical to Y6: a dual-teams worktree already has a parallel Codex sibling running on the same task spec, so Codex consultation IS happening by construction; the gate would only deadlock the writer half.

## Scope Fence

**Allowed:**
- `.claude/hooks/codex-gate.py` (modify — add `is_dual_teams_worktree` helper + early-allow branch in the PreToolUse handler)
- `.claude/hooks/test_codex_gate.py` (modify — add tests; do NOT remove existing tests)

**Forbidden:**
- Every other path under `.claude/hooks/` and `.claude/scripts/`
- Any `work/*` or `worktrees/*` path

## Test Commands

```bash
py -3 .claude/hooks/test_codex_gate.py
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: New module-level function `is_dual_teams_worktree(project_dir: Path) -> bool` returns `True` iff `project_dir` *or any of its ancestors up to the filesystem root* contains a regular file named `.dual-base-ref`. Behavior must mirror the helper in `codex-delegate-enforcer.py`: bounded walk, `seen` set against cycles, `OSError` tolerance per probe.
- [ ] AC2: In the existing PreToolUse path of `codex-gate.py`, immediately after the existing `event` and `tool_name` early-returns (where `tool_name in {"Edit","Write","MultiEdit"}` is gated), call `is_dual_teams_worktree(project_dir)`. If True → log INFO `gate.passthrough reason=dual-teams-worktree project=<path>` and exit 0 (allow). Skip the cooldown / count check entirely.
- [ ] AC3: When sentinel is absent, behavior is byte-for-byte identical to before — every existing test in `test_codex_gate.py` still passes.
- [ ] AC4: NEW tests in `test_codex_gate.py` (≥ 4):
   - (a) `is_dual_teams_worktree` returns True with sentinel in project_dir
   - (b) Returns True with sentinel in a parent dir (deep nesting)
   - (c) Returns False when no sentinel in chain
   - (d) PreToolUse path returns 0 (allow) when sentinel present and cooldown WOULD have expired (last codex-ask 10 min ago)
- [ ] AC5: Logging matches the file's existing convention (`logger = logging.getLogger("codex-gate")`, `logger.info(...)`). Do NOT introduce a new logger.
- [ ] AC6: Stdlib only. Windows + POSIX both supported (`pathlib.Path` not `os.path`).
- [ ] AC7: Helper signature exactly `is_dual_teams_worktree(project_dir: Path) -> bool` (matches the existing helper in codex-delegate-enforcer.py for consistency).
- [ ] AC8: Do NOT touch `COOLDOWN_MINUTES`, `MAX_EDITS_PER_CONSULTATION`, or any other thresholds — the cooldown logic itself is correct, we are just adding a precondition exempt for dual-teams worktrees.
- [ ] All Test Commands above exit 0.

## Constraints

- The sentinel walk is an ADDITIONAL gate, not a replacement — it precedes the existing cooldown check. Existing logic stays intact for non-worktree contexts.
- Code duplication of `is_dual_teams_worktree` between codex-gate.py and codex-delegate-enforcer.py is acceptable for now (no shared module exists; introducing one would be out-of-scope). When (if) we extract a shared `_dual_teams_helpers.py`, both call-sites can import.
- No new third-party dependencies.
- If your patch grows past ~30 added lines in the hook + 60 added lines of tests, that's a sign of over-engineering — push back into the helper or simplify.
- Tests must be self-contained (use `tempfile.TemporaryDirectory`).

## Handoff Output

Standard `=== PHASE HANDOFF: Y8-gate-sentinel ===` with:
- Diff stats (lines added in hook + tests)
- Output of `py -3 .claude/hooks/test_codex_gate.py` showing all tests pass
- One-line note: "fix mirrors Y6: sentinel ancestor walk in codex-gate PreToolUse path."
