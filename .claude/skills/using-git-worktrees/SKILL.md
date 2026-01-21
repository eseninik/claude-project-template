---
name: using-git-worktrees
version: 2.1.0
description: |
  Use for isolated workspace creation OR parallel task execution.

  v2.0 adds:
  - Multi-worktree creation for parallel tasks
  - Merge flow with conflict classification
  - Batch cleanup
  - Platform detection

  v2.1 adds:
  - Corrupted worktree recovery
  - Pre-cleanup safety check (uncommitted changes)

changelog:
  - version: 2.1.0
    date: 2026-01-21
    changes:
      - Added Corrupted Worktree Recovery section
      - Added Pre-Cleanup Safety Check (uncommitted changes)
  - version: 2.0.0
    date: 2026-01-21
    changes:
      - Added Multi-Worktree Parallel Execution section
      - Added Conflict Classification (5 types)
      - Added Batch Cleanup
      - Added Platform Detection
---

# Using Git Worktrees

## Overview

Git worktrees create isolated workspaces sharing the same repository, allowing work on multiple branches simultaneously without switching.

**Core principle:** Systematic directory selection + safety verification = reliable isolation.

**Announce at start:** "I'm using the using-git-worktrees skill to set up an isolated workspace."

## Directory Selection Process

Follow this priority order:

### 1. Check Existing Directories

```bash
# Check in priority order
ls -d .worktrees 2>/dev/null     # Preferred (hidden)
ls -d worktrees 2>/dev/null      # Alternative
```

**If found:** Use that directory. If both exist, `.worktrees` wins.

### 2. Check CLAUDE.md

```bash
grep -i "worktree.*director" CLAUDE.md 2>/dev/null
```

**If preference specified:** Use it without asking.

### 3. Ask User

If no directory exists and no CLAUDE.md preference:

```
No worktree directory found. Where should I create worktrees?

1. .worktrees/ (project-local, hidden)
2. ~/.config/superpowers/worktrees/<project-name>/ (global location)

Which would you prefer?
```

## Safety Verification

### For Project-Local Directories (.worktrees or worktrees)

**MUST verify .gitignore before creating worktree:**

```bash
# Check if directory pattern in .gitignore
grep -q "^\.worktrees/$" .gitignore || grep -q "^worktrees/$" .gitignore
```

**If NOT in .gitignore:**

Per Jesse's rule "Fix broken things immediately":
1. Add appropriate line to .gitignore
2. Commit the change
3. Proceed with worktree creation

**Why critical:** Prevents accidentally committing worktree contents to repository.

### For Global Directory (~/.config/superpowers/worktrees)

No .gitignore verification needed - outside project entirely.

## Creation Steps

### 1. Detect Project Name

```bash
project=$(basename "$(git rev-parse --show-toplevel)")
```

### 2. Create Worktree

```bash
# Determine full path
case $LOCATION in
  .worktrees|worktrees)
    path="$LOCATION/$BRANCH_NAME"
    ;;
  ~/.config/superpowers/worktrees/*)
    path="~/.config/superpowers/worktrees/$project/$BRANCH_NAME"
    ;;
esac

# Create worktree with new branch
git worktree add "$path" -b "$BRANCH_NAME"
cd "$path"
```

### 3. Run Project Setup

Auto-detect and run appropriate setup:

```bash
# Node.js
if [ -f package.json ]; then npm install; fi

# Rust
if [ -f Cargo.toml ]; then cargo build; fi

# Python
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
if [ -f pyproject.toml ]; then poetry install; fi

# Go
if [ -f go.mod ]; then go mod download; fi
```

### 4. Verify Clean Baseline

Run tests to ensure worktree starts clean:

```bash
# Examples - use project-appropriate command
npm test
cargo test
pytest
go test ./...
```

**If tests fail:** Report failures, ask whether to proceed or investigate.

**If tests pass:** Report ready.

### 5. Report Location

```
Worktree ready at <full-path>
Tests passing (<N> tests, 0 failures)
Ready to implement <feature-name>
```

## Quick Reference

| Situation | Action |
|-----------|--------|
| `.worktrees/` exists | Use it (verify .gitignore) |
| `worktrees/` exists | Use it (verify .gitignore) |
| Both exist | Use `.worktrees/` |
| Neither exists | Check CLAUDE.md → Ask user |
| Directory not in .gitignore | Add it immediately + commit |
| Tests fail during baseline | Report failures + ask |
| No package.json/Cargo.toml | Skip dependency install |

## Common Mistakes

**Skipping .gitignore verification**
- **Problem:** Worktree contents get tracked, pollute git status
- **Fix:** Always grep .gitignore before creating project-local worktree

**Assuming directory location**
- **Problem:** Creates inconsistency, violates project conventions
- **Fix:** Follow priority: existing > CLAUDE.md > ask

**Proceeding with failing tests**
- **Problem:** Can't distinguish new bugs from pre-existing issues
- **Fix:** Report failures, get explicit permission to proceed

**Hardcoding setup commands**
- **Problem:** Breaks on projects using different tools
- **Fix:** Auto-detect from project files (package.json, etc.)

## Example Workflow

```
You: I'm using the using-git-worktrees skill to set up an isolated workspace.

[Check .worktrees/ - exists]
[Verify .gitignore - contains .worktrees/]
[Create worktree: git worktree add .worktrees/auth -b feature/auth]
[Run npm install]
[Run npm test - 47 passing]

Worktree ready at /Users/jesse/myproject/.worktrees/auth
Tests passing (47 tests, 0 failures)
Ready to implement auth feature
```

---

## Multi-Worktree Parallel Execution (v2.0+)

For use with `subagent-driven-development` Worktree Mode.

### Creating Multiple Worktrees

```bash
# Create worktrees for each conflicting task
for task_num in $CONFLICTING_TASKS; do
  WORKTREE_PATH=".worktrees/task-$task_num"
  BRANCH_NAME="wt/task-$task_num"

  # Verify .gitignore first
  if ! grep -q "^\.worktrees/$" .gitignore; then
    echo ".worktrees/" >> .gitignore
    git add .gitignore
    git commit -m "chore: add .worktrees/ to .gitignore"
  fi

  git worktree add "$WORKTREE_PATH" -b "$BRANCH_NAME"
done
```

### Batch Cleanup

```bash
# Remove all task worktrees
for worktree in .worktrees/task-*; do
  if [ -d "$worktree" ]; then
    git worktree remove "$worktree" --force
  fi
done

# Prune worktree metadata
git worktree prune

# Delete branches
for branch in $(git branch | grep "wt/task-"); do
  git branch -D "$branch"
done
```

---

## Pre-Cleanup Safety Check (v2.1)

**Before removing any worktree, check for uncommitted changes:**

### Check for Uncommitted Work

```bash
WORKTREE_PATH=".worktrees/task-001"

# Check for uncommitted changes
cd "$WORKTREE_PATH"
UNCOMMITTED=$(git status --porcelain)

if [ -n "$UNCOMMITTED" ]; then
  echo "⚠️ Uncommitted changes in $WORKTREE_PATH:"
  git status --short
fi
```

### If Uncommitted Changes Found

```
⚠️ Uncommitted changes detected in worktree

Worktree: .worktrees/task-001
Branch: wt/task-001

Uncommitted files:
 M src/user.py
 A src/new_file.py
?? tests/test_new.py

Options:
1. Stash changes (Recommended)
   → git stash -m "Auto-stash from worktree cleanup"
   → Changes can be recovered later with: git stash pop

2. Commit changes
   → git add . && git commit -m "WIP: uncommitted work from worktree"
   → Creates a commit on the worktree branch

3. Discard changes
   → Proceed with removal (DATA LOSS WARNING)
   → Cannot be recovered

4. Abort cleanup
   → Keep worktree, stop cleanup process

Which option? [1]:
```

### Default Behavior

If no response in automated mode, default to **Stash** (option 1):
- Preserves work
- Allows cleanup to proceed
- User can recover later

### Integration with Batch Cleanup

```bash
# In batch cleanup loop
for worktree in .worktrees/task-*; do
  # Safety check before removal
  if has_uncommitted_changes "$worktree"; then
    handle_uncommitted_changes "$worktree"  # Stash/commit/discard
  fi

  git worktree remove "$worktree"
done
```

---

## Corrupted Worktree Recovery (v2.1)

Handle cases where worktree is corrupted or inconsistent.

### Detection Signs

A worktree may be corrupted if:
- `git worktree list` shows it, but directory doesn't exist
- Directory exists, but `git worktree remove` fails with "not a git worktree"
- Branch exists, but worktree was deleted manually
- `.git` file in worktree is missing or corrupted

### Detection Command

```bash
# Check worktree validity
git worktree list --porcelain | grep -A2 "worktree .worktrees/task-001"

# Signs of corruption:
# - "prunable" flag present
# - "locked" but no lock reason
# - Path exists but not recognized
```

### Recovery Procedure

```bash
# Step 1: Try normal remove first
git worktree remove .worktrees/task-001 2>/dev/null
if [ $? -eq 0 ]; then
  echo "Worktree removed normally"
  exit 0
fi

# Step 2: If fails, check what's wrong
if [ -d ".worktrees/task-001" ]; then
  echo "Directory exists but git doesn't recognize it"

  # Step 3: Force directory removal
  rm -rf .worktrees/task-001

  # Step 4: Prune worktree metadata
  git worktree prune

else
  echo "Directory doesn't exist, cleaning metadata"
  git worktree prune
fi

# Step 5: Delete orphan branch (if exists)
git branch -D wt/task-001 2>/dev/null || true

# Step 6: Verify cleanup
echo "Verification:"
git worktree list | grep task-001 && echo "WARNING: still in list" || echo "OK: removed from list"
git branch | grep wt/task-001 && echo "WARNING: branch exists" || echo "OK: branch removed"
```

### When Corruption Detected — User Message

```
⚠️ Corrupted worktree detected: .worktrees/task-001

Symptoms:
- Directory exists but git doesn't recognize it as worktree
- OR: Git metadata exists but directory is missing

Recovery will:
1. Remove directory (if exists)
2. Prune git worktree metadata
3. Delete orphan branch (wt/task-001)

This is safe and won't affect your main branch.

Proceed with recovery? (yes/no)
```

### Automatic Recovery in Session Resumption

When session-resumption detects stale worktrees, it should:
1. First try normal cleanup
2. If fails, offer corrupted recovery
3. Log recovery actions for debugging

---

## Red Flags

**Never:**
- Create worktree without .gitignore verification (project-local)
- Skip baseline test verification
- Proceed with failing tests without asking
- Assume directory location when ambiguous
- Skip CLAUDE.md check
- **Remove worktrees with uncommitted changes without warning (v2.1)**
- **Skip corrupted worktree recovery when needed (v2.1)**

**Always:**
- Follow directory priority: existing > CLAUDE.md > ask
- Verify .gitignore for project-local
- Auto-detect and run project setup
- Verify clean test baseline
- **Check for uncommitted changes before cleanup (v2.1)**
- **Attempt corrupted worktree recovery before giving up (v2.1)**

## Integration

**Called by:**
- Any skill needing isolated workspace

**Pairs with:**
- **finishing-a-development-branch** - REQUIRED for cleanup after work complete
- **executing-plans** or **subagent-driven-development** - Work happens in this worktree
