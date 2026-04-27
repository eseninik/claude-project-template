You are the Claude side of a dual micro-task. Your twin is Codex-GPT5.5 working the same spec in a parallel worktree. Opus will judge both diffs.

## Agent Type
coder

## Required Skills
- verification-before-completion
- logging-standards
- coding-standards

## Working Directory (CRITICAL)
C:\Bots\Migrator bots\claude-project-template-update\worktrees\inline\Z16-claude-cover\claude

Branch: inline/Z16-claude-cover/claude

## Task Spec (IMMUTABLE)
C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations\inline\task-Z16-claude-cover.md

## Your Task
Z16 reliability fixes: codex-implement repo-current parser + spawn-agent PowerShell-primary + Y20 lock test

## Scope Fence (Allowed paths)
- `.claude/scripts/codex-implement.py`
- `.claude/scripts/test_codex_implement.py`
- `.claude/scripts/spawn-agent.py`
- `.claude/scripts/test_spawn_agent.py`

## Test Commands
```bash
py -3 -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_spawn_agent.py -q
```

## Acceptance Criteria
- `py -3 -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_spawn_agent.py -q` exits 0
- Only files inside Scope Fence are modified
- Structured logging on any new/modified function

## Handoff Output (MANDATORY when done)

=== PHASE HANDOFF: inline-Z16-claude-cover-claude ===
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
