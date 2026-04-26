You are the Claude side of a dual micro-task. Your twin is Codex-GPT5.5 working the same spec in a parallel worktree. Opus will judge both diffs.

## Agent Type
coder

## Required Skills
- verification-before-completion
- logging-standards
- coding-standards

## Working Directory (CRITICAL)
C:\Bots\Migrator bots\claude-project-template-update\worktrees\inline\Z9-smoke-after-y26\claude

Branch: inline/Z9-smoke-after-y26/claude

## Task Spec (IMMUTABLE)
C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations\inline\task-Z9-smoke-after-y26.md

## Your Task
Re-verify safety of running work/sync-template-to-target.py post-Y26-fix. Codex should now be able to write into the worktree (sandbox bypass enabled). Verification only.

## Scope Fence (Allowed paths)
- `work/sync-template-to-target.py`

## Test Commands
```bash
py -3 -m py_compile work/sync-template-to-target.py
```

## Acceptance Criteria
- `py -3 -m py_compile work/sync-template-to-target.py` exits 0
- Only files inside Scope Fence are modified
- Structured logging on any new/modified function

## Handoff Output (MANDATORY when done)

=== PHASE HANDOFF: inline-Z9-smoke-after-y26-claude ===
Status: PASS | REWORK | BLOCKED
Files Modified:
- [path]
Tests: [results of each Test Command]
Decisions: [key choices + rationale]
Learnings:
- Friction: ... | NONE
- Surprise: ... | NONE
Next Phase Input: [what Opus needs for judging]
=== END HANDOFF ===
