You are the Claude side of a dual micro-task. Your twin is Codex-GPT5.5 working the same spec in a parallel worktree. Opus will judge both diffs.

## Agent Type
coder

## Required Skills
- verification-before-completion
- logging-standards
- coding-standards

## Working Directory (CRITICAL)
C:\Bots\Migrator bots\claude-project-template-update\worktrees\inline\Z3-sync-script-recheck\claude

Branch: inline/Z3-sync-script-recheck/claude

## Task Spec (IMMUTABLE)
C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations\inline\task-Z3-sync-script-recheck.md

## Your Task
Re-verify safety of running work/sync-template-to-target.py to mirror .claude/ infrastructure into another bot project. Read the script, validate file mutations are well-bounded by EXCLUDE_NAMES + MIRROR_DIRS policy. Verification only — no code changes.

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

=== PHASE HANDOFF: inline-Z3-sync-script-recheck-claude ===
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
