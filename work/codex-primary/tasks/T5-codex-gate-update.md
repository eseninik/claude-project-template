---
executor: claude
risk_class: high-stakes
reasoning: high
wave: 1
---

# Task T5: Update `.claude/hooks/codex-gate.py`

## Your Task
Extend codex-gate.py to recognize `work/codex-implementations/task-*-result.md` as a valid "fresh codex opinion" when Claude edits files inside that task's Scope Fence.

See tech-spec.md Section 9 for exact behavior.

**This is high-stakes** because codex-gate blocks Claude's Edit/Write ops globally. A regression here breaks everything. Preserve old behavior as fallback.

## Scope Fence
**Allowed paths:**
- `.claude/hooks/codex-gate.py` (MODIFY)
- `.claude/hooks/test_codex_gate.py` (new — unit test)

**Forbidden paths:**
- Any other hook
- `.claude/shared/templates/new-project/.claude/hooks/codex-gate.py` (will be synced later, not in this pipeline)
- `.claude/scripts/codex-ask.py` (don't modify its interface — gate must remain compatible)

## Test Commands
```bash
py -3 .claude/hooks/test_codex_gate.py
# Integration smoke test — ensure gate still validates normal codex-ask.py opinion
py -3 .claude/scripts/codex-ask.py "ping"
```

## Acceptance Criteria (IMMUTABLE)
- [ ] AC1: Old behavior preserved — if no fresh `task-*-result.md` exists, gate falls back to existing codex-ask.py opinion freshness check
- [ ] AC2: New behavior activated when: (a) a recent `work/codex-implementations/task-{N}-result.md` exists (< 3 min old), (b) its `status: pass`, (c) the file being edited is inside that task's Scope Fence (parsed from task-{N}.md)
- [ ] AC3: If multiple recent task-result.md files match, gate uses the one with matching scope fence
- [ ] AC4: Gate logs (structured) which opinion source it accepted: `codex-ask` | `codex-implement` | `none-stale`
- [ ] AC5: Unit test covers: (a) no opinions at all -> block, (b) fresh codex-ask.py opinion -> pass, (c) stale codex-ask.py but fresh task-result.md in scope -> pass, (d) fresh task-result.md but file NOT in scope -> block, (e) task-result.md with `status: fail` -> block
- [ ] AC6: No changes to gate's PreToolUse hook contract (Claude Code still receives same JSON response structure)
- [ ] AC7: All new logic has structured logging (entry/exit/decision)
- [ ] All Test Commands exit 0

## Skill Contracts

### verification-before-completion
- Run Test Commands. If any fail, do NOT claim done.
- Test the integration smoke — opening a normal Edit after codex-ask.py must still work.

### logging-standards
- Every new decision branch logs its choice with context (path, opinion age, source)
- Use existing logger setup in codex-gate.py — don't reinvent

### security-review (applies — this is a safety gate)
- Be paranoid about time checks: use `time.time() - mtime` not `datetime` subtraction (avoid tz pitfalls)
- Don't follow symlinks when reading task-result.md (use `Path.resolve().is_relative_to(project_root)`)
- On ANY parse error in task-result.md -> fall back to old behavior, don't crash the gate (Edit would be permanently blocked)

### coding-standards
- Minimal diff — change as little as possible in existing codex-gate.py
- Add new logic as a separate function, don't intermingle with existing logic
- Match existing code style

## Read-Only Files (Evaluation Firewall)
- `work/codex-primary/tech-spec.md`
- `.claude/hooks/test_codex_gate.py` once written
- `.claude/scripts/codex-ask.py`

## Constraints
- Backward compat is CRITICAL — every Claude Edit on any project goes through this gate
- If you break codex-gate.py, Claude becomes unable to edit any file without manual codex-ask.py before every edit (very bad UX)
- Fallback on ANY error — never let the gate crash

## Handoff Output (MANDATORY)
Standard block. Include explicit section "Backward Compatibility Verification" showing test output proving old behavior unchanged.

## Notes
- Read existing codex-gate.py FIRST before writing any changes
- Identify the exact function that does the freshness check — modify only that
- T1's task-result.md schema is your input format; read tech-spec 6.2 step 6
