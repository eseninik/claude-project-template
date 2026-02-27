---
name: using-git-worktrees
description: |
  Creates isolated git worktree workspaces for parallel task execution.
  Activate when needing isolated workspace or parallel tasks with file conflicts.
  Does NOT manage branch strategy — use finishing-a-development-branch for that.
---

## Philosophy
Isolation prevents conflicts. When multiple agents work on the same codebase, worktrees ensure they can't corrupt each other's work.

## Critical Constraints
**never:**
- Have multiple agents modify the same files without worktree isolation
- Leave orphaned worktrees after completion

**always:**
- Clean up worktrees after merging
- Use worktrees when 5+ concurrent agents or file overlap detected

# Using Git Worktrees

## Create
```bash
# Ensure .gitignore
grep -q "^\.worktrees/$" .gitignore || echo ".worktrees/" >> .gitignore

# Single worktree
git worktree add ".worktrees/$BRANCH" -b "$BRANCH"

# Multiple (parallel tasks)
for task in task-1 task-2 task-3; do
  git worktree add ".worktrees/$task" -b "wt/$task"
done
```

## Clean Up
```bash
for wt in .worktrees/task-*; do
  git worktree remove "$wt" --force
done
git branch -D $(git branch | grep "wt/task-")
git worktree prune
```

## Agent Teams (worktree-per-agent)
- For AGENT_TEAMS phases with file conflicts: create worktree per task
- Agents work in isolation, merge back after completion
- Configure via teammate prompt `## Working Directory` section

## Rules
- Never create worktree without .gitignore check
- Never remove worktree with uncommitted changes without warning
- Always `git worktree prune` after cleanup
