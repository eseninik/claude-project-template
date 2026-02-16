---
name: using-git-worktrees
description: |
  Creates isolated git worktree workspaces for parallel task execution or feature isolation.
  Activate when needing an isolated workspace, parallel task execution in separate branches,
  or when subagent-driven-development requires Worktree Mode.
  Does NOT manage branch strategy or code review -- use finishing-a-development-branch for that.
---

# Using Git Worktrees

## Directory Selection (priority)
1. Existing `.worktrees/` (preferred) or `worktrees/`
2. CLAUDE.md preference
3. Ask user: `.worktrees/` (project-local) or `~/.config/superpowers/worktrees/<project>/` (global)

## Before Creating (Safety)

Verify `.gitignore` includes worktree dir:
```bash
grep -q "^\.worktrees/$" .gitignore || { echo ".worktrees/" >> .gitignore && git add .gitignore && git commit -m "chore: add .worktrees/ to .gitignore"; }
```
Global directory needs no check.

## Single Worktree

```bash
git worktree add ".worktrees/$BRANCH" -b "$BRANCH"
cd ".worktrees/$BRANCH"
# Auto-detect and install deps: package.json/Cargo.toml/requirements.txt/pyproject.toml/go.mod
# Run tests to verify clean baseline
```

## Multi-Worktree (parallel tasks)

```bash
for task_num in $CONFLICTING_TASKS; do
  git worktree add ".worktrees/task-$task_num" -b "wt/task-$task_num"
done
```

## Batch Cleanup

```bash
# 1. Check uncommitted changes (offer: stash/commit/discard/abort)
# 2. Remove worktrees
for wt in .worktrees/task-*; do
  git worktree remove "$wt" --force
done
git worktree prune
# 3. Delete branches
git branch -D $(git branch | grep "wt/task-")
```

## Corrupted Worktree Recovery

```bash
git worktree remove .worktrees/task-001 2>/dev/null || {
  rm -rf .worktrees/task-001 && git worktree prune
}
git branch -D wt/task-001 2>/dev/null || true
```

## Hard Rules
- Never create project-local worktree without .gitignore verification
- Never proceed with failing baseline tests without user permission
- Never remove worktrees with uncommitted changes without warning
- Pre-cleanup safety: always offer stash/commit/discard/abort for dirty worktrees
