---
name: session-resumption
description: |
  Resumes incomplete work from a previous session by parsing STATE.md and loading relevant context.
  Checks for interrupted git operations (merge/rebase), stale worktrees, and uncommitted changes.
  Activate on session start when STATE.md has incomplete work, or when user says "/resume".
  Does NOT apply when starting fresh work with no prior state.
---

# Session Resumption

Resume incomplete work by checking git state, stale worktrees, and STATE.md, then presenting options to the user.

## Check Order (on session start)

```
- [ ] 1. Git State Check (merge/rebase in progress)
- [ ] 2. Worktree Cleanup Check (stale worktrees)
- [ ] 3. STATE.md Check (incomplete work)
```

## Check 1: Git State

### Interrupted merge

```bash
git rev-parse MERGE_HEAD >/dev/null 2>&1
```

If merge in progress, display conflicted files and offer:
1. Abort merge (`git merge --abort`)
2. Continue merge (resolve conflicts, then `git add` + `git commit`)
3. Show conflict details

### Interrupted rebase

```bash
test -d ".git/rebase-merge" -o -d ".git/rebase-apply"
```

If rebase in progress, offer:
1. Abort (`git rebase --abort`)
2. Continue (`git rebase --continue`)
3. Skip current commit (`git rebase --skip`)

### Uncommitted changes

```bash
git status --porcelain
```

If uncommitted changes exist, offer:
1. Stash (`git stash -m "Auto-stash before session"`)
2. Commit (prompt for message)
3. Continue anyway (warn about risks)

Resolve all git state issues before proceeding to next checks.

## Check 2: Stale Worktrees

```bash
git worktree list | grep "wt/task-"
```

If stale task worktrees found, offer:
1. **Cleanup** -- check for uncommitted changes first, then remove worktrees, prune, delete branches
2. **Resume merge** -- read `.worktrees/.state`, continue from last successful merge
3. **Keep** -- warn and continue, user handles manually

### Cleanup safety

Before removing any worktree, check for uncommitted changes. Default to stash if no user response:

```bash
cd .worktrees/task-001 && git status --porcelain
```

If uncommitted changes: stash (default), commit, discard, or abort cleanup.

## Check 3: STATE.md

Parse STATE.md sections (Russian headers):
- `## Текущая работа` -- task, phase, status, feature
- `## Следующие шаги` -- bullet list of next steps
- `## Блокеры` -- bullet list of blockers
- `## Session Notes` -- last session date
- `## Key Decisions` -- markdown table

### Display summary

```
Incomplete work found:

Feature: {feature}
Task: {task}
Phase: {phase}
Status: {status}
Last session: {date}

Next steps:
- {step_1}
- {step_2}

Continue from where you left off?
1. Yes -- resume work
2. No -- clear STATE.md, start fresh
3. Show details -- display full STATE.md
```

### On resume

Load context files in order:
1. `work/{feature}/user-spec.md` (if exists)
2. `work/{feature}/tech-spec.md` (if exists)
3. `work/{feature}/tasks/*.md` (check frontmatter status)
4. `.claude/skills/project-knowledge/guides/architecture.md`
5. `.claude/skills/project-knowledge/guides/patterns.md`

## Error Handling

| Condition | Action |
|-----------|--------|
| STATE.md missing | Report "No incomplete work found" |
| STATE.md malformed | Show raw contents, offer to clear and start fresh |
| STATE.md empty | Report "No active work" |
| Status is "completed" | Report "Previous work done. Ready for new task." |

## Example

```
[Session starts]

Agent: Checking for incomplete work...

  Incomplete work found:
  Feature: dark-mode
  Task: Task 3: Add theme toggle
  Phase: implementation
  Status: in_progress
  Last session: 2026-01-18

  Next steps:
  - Complete ThemeToggle component
  - Add tests for theme switching

  Continue? (yes/no/details)

User: yes

Agent: Loading context...
Agent: Continuing ThemeToggle component implementation.
```
