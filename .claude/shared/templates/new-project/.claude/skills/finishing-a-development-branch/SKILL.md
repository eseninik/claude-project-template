---
name: finishing-a-development-branch
description: |
  Guides completion of dev work: verify tests, merge/PR, clean up.
  Use when implementation is complete and tests pass.
  Trigger: finish branch, merge, create PR, branch done.
  Does NOT cover ongoing development -- use qa-validation-loop first.
---

## Philosophy
A branch is only done when tests pass, memory is updated, and the work is properly handed off. Incomplete completion is worse than no completion.

## Critical Constraints
**never:**
- Merge without all tests passing
- Create a PR without updating memory files

**always:**
- Run full test suite before merge
- Update activeContext.md and daily log before PR creation

# Finishing a Development Branch

## Checklist
1. Run full test suite -- ALL must pass
2. Run verification-before-completion checklist
3. Present options to user:
   - **Merge** to target branch (dev/main)
   - **Create PR** via `gh pr create`
   - **Keep** branch for more work
   - **Discard** branch
4. Execute chosen option
5. Clean up worktree if applicable:
   ```bash
   git worktree remove .worktrees/{branch} --force
   git branch -D {branch}
   git worktree prune
   ```
6. Update activeContext.md

## PR Creation
```bash
gh pr create --title "{title}" --body "## Summary\n{bullets}\n\n## Test Plan\n{checklist}"
```
