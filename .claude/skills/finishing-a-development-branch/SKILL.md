---
name: finishing-a-development-branch
description: |
  Guides completion of development work: verify tests, present merge/PR/keep/discard options, execute chosen workflow, clean up worktree.
  Use when implementation is complete and all tests pass. Trigger keywords: finish branch, merge, create PR, branch done, complete work.
  Does NOT cover ongoing development or code review -- use requesting-code-review before finishing.
---

# Finishing a Development Branch

Announce: "Using the finishing-a-development-branch skill to complete this work."

## Process

1. **Verify tests** -- run test suite. Fail -> stop, report. Pass -> continue.
2. **Determine base branch** -- `git merge-base HEAD main` or ask user
3. **Present 4 options**:
   - 1: Merge back to `<base>` locally
   - 2: Push and create PR
   - 3: Keep branch as-is
   - 4: Discard this work
4. **Execute choice** (see below)
5. **Clean up worktree** (Options 1,2,4 only)

## Option Details

| Option | Commands |
|--------|----------|
| 1. Merge | `checkout base` -> `pull` -> `merge feature` -> run tests -> `branch -d feature` |
| 2. PR | `push -u origin feature` -> `gh pr create --title --body` |
| 3. Keep | Report branch/worktree location. No cleanup. |
| 4. Discard | Show commits, require typed "discard" confirmation -> `branch -D feature` |

## Worktree Cleanup (Options 1, 2, 4)

```bash
git worktree remove <path>
```

## Quick Reference

| Option | Merge | Push | Keep Worktree | Delete Branch |
|--------|-------|------|---------------|---------------|
| 1 | Yes | No | No | Yes (soft) |
| 2 | No | Yes | Yes | No |
| 3 | No | No | Yes | No |
| 4 | No | No | No | Yes (force) |

## Hard Rules
- Never proceed with failing tests
- Never merge without verifying tests on result
- Never delete work without typed confirmation
- Never force-push without explicit request
- Always present exactly 4 options
