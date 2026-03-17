# Worktree Mode Reference

Detailed procedures for running parallel tasks that modify overlapping files using isolated git worktrees.

## Platform Detection

Check before activating:

```bash
WORKTREE_MODE_AVAILABLE=true

# Windows + Cyrillic path = fallback
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ "$OS" == "Windows_NT" ]]; then
  if [[ "$(pwd)" =~ [а-яА-ЯёЁ] ]]; then
    WORKTREE_MODE_AVAILABLE=false
    FALLBACK_REASON="Windows + Cyrillic path detected"
  fi
fi

# Git version 2.17+ required
GIT_VERSION=$(git --version | grep -oE '[0-9]+\.[0-9]+')
if (( $(echo "$GIT_VERSION < 2.17" | bc -l) )); then
  WORKTREE_MODE_AVAILABLE=false
fi

# Disk space: need project_size * 4
PROJECT_SIZE=$(du -sm . | cut -f1)
AVAILABLE_SPACE=$(df -m . | tail -1 | awk '{print $4}')
if (( AVAILABLE_SPACE < PROJECT_SIZE * 4 )); then
  WORKTREE_MODE_AVAILABLE=false
fi
```

## Concurrent Session Lock

```bash
LOCK_FILE=".worktrees/.lock"

if [ -f "$LOCK_FILE" ]; then
  LOCK_PID=$(head -1 "$LOCK_FILE")
  if ! [[ "$LOCK_PID" =~ ^[0-9]+$ ]]; then
    rm -f "$LOCK_FILE"  # corrupted lock
  elif ps -p $LOCK_PID > /dev/null 2>&1; then
    echo "ERROR: Another session active (PID: $LOCK_PID)"
    WORKTREE_MODE_AVAILABLE=false
  else
    rm -f "$LOCK_FILE"  # stale lock
  fi
fi

# Create lock
if [ "$WORKTREE_MODE_AVAILABLE" = true ]; then
  mkdir -p .worktrees
  echo "$$" > "$LOCK_FILE"
  echo "$(date -Iseconds)" >> "$LOCK_FILE"
fi
```

## Worktree Creation

```bash
for task_num in $CONFLICTING_TASKS; do
  git worktree add ".worktrees/task-$task_num" -b "wt/task-$task_num"
done

# Record state
echo "WAVE_START=$(git rev-parse HEAD)" > .worktrees/.state
echo "WAVE_NUMBER=$WAVE_NUM" >> .worktrees/.state
echo "MERGE_ORDER=$CONFLICTING_TASKS" >> .worktrees/.state
```

### Disk full handling

If `git worktree add` fails with "No space left on device": clean up partial worktrees, report to user, abort.

## Subagent Execution in Worktrees

Each subagent works in its own worktree directory and commits to its branch:

```
Task tool (general-purpose):
  prompt: |
    Implement Task N.
    IMPORTANT: Work in directory: .worktrees/task-N
    After implementation: commit to branch wt/task-N, report modified files.
```

## Post-Execution File Validation

Before merging, compare actual vs declared files:

```bash
cd .worktrees/task-N
ACTUAL_FILES=$(git diff --name-only HEAD~1)
```

If subagent modified undeclared files, offer:
1. Continue merge (accept extra files)
2. Abort and investigate
3. Re-run conflict detection with actual files

If actual files from two worktrees overlap (but were not declared), trigger wave rollback.

## Sequential Merge

```bash
WAVE_START=$(grep "WAVE_START=" .worktrees/.state | cut -d= -f2)

for task_num in $CONFLICTING_TASKS; do
  git merge "wt/task-$task_num" --no-edit
  if [ $? -ne 0 ]; then
    # Conflict -- classify and handle
  fi
done
```

## Conflict Classification

Read the conflicted file, find conflict markers, then classify:

| Pattern | Classification | Action |
|---------|---------------|--------|
| Two different functions (different names) | independent_additions | Keep both |
| Same function modified by both | same_function | STOP -- ask human |
| Identical import lines | duplicate_import | Keep one |
| Different import lines | independent_additions | Keep both |
| Same config key, different values | same_config | STOP -- ask human |
| Complex/unclear | unknown | STOP -- ask human |

### Auto-resolvable (independent_additions, duplicate_import)

1. Remove conflict markers
2. Keep both pieces (or deduplicate imports)
3. `git add <file>` + commit

### Human-required (same_function, same_config, unknown)

Do NOT auto-resolve. Report to user and trigger wave rollback.

## Post-Merge Smoke Test

After all merges complete:

```bash
pytest tests/smoke/ -v --timeout=60 2>/dev/null ||
pytest tests/ -k "smoke" -v --timeout=60 2>/dev/null ||
pytest tests/ -v --timeout=120 -x --ignore=tests/e2e/ 2>/dev/null ||
echo "WARNING: No smoke tests found"
```

Any failure = STOP and ask user. Do not determine if failure is "related" or not.

## Wave-Level Rollback

Trigger when: merge requires human intervention, actual file conflict detected, smoke test fails.

```bash
git merge --abort 2>/dev/null || true
WAVE_START=$(grep "WAVE_START=" .worktrees/.state | cut -d= -f2)
git reset --hard $WAVE_START
# Keep worktrees for investigation
```

After rollback, offer: manual resolution, sequential fallback, or abort.

## Cleanup

```bash
for task_num in $CONFLICTING_TASKS; do
  git worktree remove ".worktrees/task-$task_num" --force
done
git worktree prune
for task_num in $CONFLICTING_TASKS; do
  git branch -D "wt/task-$task_num"
done
rm -f .worktrees/.lock .worktrees/.state
rmdir .worktrees 2>/dev/null || true
```

## State File Format

```
WAVE_START=abc123def456
WAVE_NUMBER=1
MERGE_ORDER=wt/task-001,wt/task-002,wt/task-003
MERGED=wt/task-001
PENDING=wt/task-002,wt/task-003
```

Validate all required fields before use. If corrupted: offer to delete and start fresh.

## Windows Notes

All scripts are bash. On Windows, commands run through Git Bash (msys). PowerShell equivalents for manual debugging only:

| Bash | PowerShell |
|------|------------|
| `ps -p $PID` | `Get-Process -Id $PID -EA SilentlyContinue` |
| `rm -f file` | `Remove-Item file -Force -EA SilentlyContinue` |
| `rm -rf dir` | `Remove-Item dir -Recurse -Force` |
