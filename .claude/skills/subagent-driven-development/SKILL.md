---
name: subagent-driven-development
version: 3.1.0
description: |
  Use when executing implementation plans with independent tasks in the current session.
  Dispatches fresh subagent per task with code review between tasks.

  NEW in v3.0: WORKTREE MODE - tasks modifying same files now run in parallel
  using isolated git worktrees with automatic merge.

  NEW in v3.1: Post-execution validation, wave-level rollback, smoke tests.

changelog:
  - version: 3.1.0
    date: 2026-01-21
    changes:
      - Added post-execution file validation (actual vs declared)
      - Added wave-level rollback for human-required conflicts
      - Added concurrent session lock
      - Added post-merge smoke tests
      - Improved conflict classification (agent instructions)
  - version: 3.0.0
    date: 2026-01-21
    changes:
      - Added Worktree Mode for parallel execution of conflicting tasks
      - Added platform detection (Windows/Cyrillic fallback)
      - Added conflict classification for merge resolution
      - Breaking: Requires git 2.17+
---

# Subagent-Driven Development

Execute plan by dispatching fresh subagent per task, with code review after each.

**Core principle:** Fresh subagent per task + review between tasks = high quality, fast iteration

**NEW in v2.0:** Auto Wave Parallelization - automatically runs independent tasks in parallel when 3+ tasks have no dependencies.

**NEW in v3.0:** WORKTREE MODE - tasks modifying same files can now run in parallel using isolated git worktrees with automatic merge.

**NEW in v3.1:** Post-execution validation, wave-level rollback, post-merge smoke tests.

## Overview

**vs. Executing Plans (parallel session):**
- Same session (no context switch)
- Fresh subagent per task (no context pollution)
- Code review after each task (catch issues early)
- Faster iteration (no human-in-loop between tasks)
- **NEW:** Auto parallelization for independent tasks

**When to use:**
- Staying in this session
- Tasks are mostly independent
- Want continuous progress with quality gates

**When NOT to use:**
- Need to review plan first (use executing-plans)
- Tasks are sequentially dependent (task B needs output of task A in same file)
- Plan needs revision (brainstorm first)

**Common misconception:** "Tasks modify same files" ≠ "can't parallelize". Use Worktree Mode for this!

## Wave Parallelization (AUTO)

### When it activates:
- 3+ tasks in plan
- Tasks have `depends_on` field (or empty = independent)

### Two parallelization modes:

| Condition | Mode | How it works |
|-----------|------|--------------|
| Tasks modify **different** files | Standard parallel | Run in same worktree simultaneously |
| Tasks modify **same** files | **Worktree Mode** | Run in isolated worktrees → merge with conflict resolution |

**IMPORTANT:** "Same files" is NOT a reason to skip parallelization! Worktree Mode exists specifically for this case.

### MANDATORY Decision Algorithm

**You MUST follow this algorithm. No exceptions.**

```
START: Have 3+ tasks with depends_on: []?
  │
  ├─ NO → Execute sequentially (standard flow)
  │
  └─ YES → Check files_modified overlap
           │
           ├─ Files DON'T overlap → Standard parallel (same worktree)
           │
           └─ Files DO overlap → MUST use Worktree Mode
                                 │
                                 ├─ Platform check passes? → Execute in worktrees
                                 │
                                 └─ Platform check fails? → Sequential (fallback ONLY)
```

**BLOCKING RULE:** If files overlap AND platform check passes → Worktree Mode is MANDATORY.
Skipping Worktree Mode when it's available = violation of this skill.

### How it works:

**Step 1: Analyze dependencies**
```
Read all task.md files
For each task:
  - depends_on: [] → Wave 1 (independent)
  - depends_on: [001] → Wave after task-001
  - files_modified: [...] → check for conflicts
```

**Step 2: Build waves**
```
Wave 1: All tasks with depends_on: [] (and no file conflicts)
Wave 2: Tasks depending on Wave 1
Wave 3: Tasks depending on Wave 2
...
```

**Step 3: Check file conflicts**
```
IF two tasks in same wave modify same file:
  IF platform check passes (see Worktree Mode section):
    → Mark as "worktree-isolated"
    → Keep in same wave
    → Create separate worktrees for each
    → Execute in parallel
    → Validate actual changed files (v3.1)
    → Merge results sequentially
    → Run post-merge smoke test (v3.1)
    → Code review merged result
  ELSE:
    → Move one to next wave (fallback)
```

**Step 4: Execute waves**
```
FOR each wave:
  IF wave has 3+ tasks:
    → Spawn ALL subagents in parallel (max 3 concurrent)
    → Wait for ALL to complete
    → Run code review for each
  ELSE:
    → Execute sequentially (standard flow)

  THEN move to next wave
```

### Example:

```
Tasks in plan:
  task-001: depends_on: []           → Wave 1
  task-002: depends_on: []           → Wave 1
  task-003: depends_on: []           → Wave 1
  task-004: depends_on: [001, 002]   → Wave 2
  task-005: depends_on: [004]        → Wave 3

Execution:
  Wave 1: [001, 002, 003] → 3 subagents IN PARALLEL
  (wait for all Wave 1 to complete)
  Wave 2: [004] → 1 subagent (sequential)
  Wave 3: [005] → 1 subagent (sequential)

Result: 3 tasks execute simultaneously instead of 5 sequential
```

### Why quality doesn't drop:
- Each subagent gets FRESH 200K tokens (no shared context)
- Tasks are INDEPENDENT (no logical dependencies)
- Code review after EACH wave (quality gate)
- File conflicts handled via Worktree Mode (isolation + merge)

---

## Worktree Mode (v3.0+)

**Purpose:** SOLVE the "same file" problem, not avoid it.

**When enabled:** Tasks modifying the same file run in parallel using isolated git worktrees, then merge results automatically.

**Key insight:** Without Worktree Mode, tasks with file conflicts must run sequentially. WITH Worktree Mode, they run in parallel and conflicts are resolved during merge phase.

**USE Worktree Mode when:**
- Multiple tasks modify overlapping files (e.g., all update `src/models/user.py`)
- Tasks are logically independent (don't need each other's output)
- You want parallelization despite file overlap

**DO NOT skip Worktree Mode just because files overlap** — that's exactly what it's for!

### Platform Detection

**Check before activating Worktree Mode:**

```bash
# Check 1: Platform
WORKTREE_MODE_AVAILABLE=true

if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ "$OS" == "Windows_NT" ]]; then
  # Check 2: Cyrillic in path
  if [[ "$(pwd)" =~ [а-яА-ЯёЁ] ]]; then
    WORKTREE_MODE_AVAILABLE=false
    FALLBACK_REASON="Windows + Cyrillic path detected"
  fi
fi

# Check 3: Git version (worktrees need 2.17+)
GIT_VERSION=$(git --version | grep -oE '[0-9]+\.[0-9]+')
if (( $(echo "$GIT_VERSION < 2.17" | bc -l) )); then
  WORKTREE_MODE_AVAILABLE=false
  FALLBACK_REASON="Git version < 2.17"
fi

# Check 4: Disk space (need project_size * 4)
PROJECT_SIZE=$(du -sm . | cut -f1)
AVAILABLE_SPACE=$(df -m . | tail -1 | awk '{print $4}')
REQUIRED_SPACE=$((PROJECT_SIZE * 4))
if (( AVAILABLE_SPACE < REQUIRED_SPACE )); then
  WORKTREE_MODE_AVAILABLE=false
  FALLBACK_REASON="Insufficient disk space (need ${REQUIRED_SPACE}MB, have ${AVAILABLE_SPACE}MB)"
fi
```

### Platform-Specific Script Execution

**Claude Code executes commands through Bash tool. On different platforms:**

| Platform | Shell | Detection |
|----------|-------|-----------|
| Linux/macOS | bash | Default |
| Windows (Git Bash) | bash | `$OSTYPE` = "msys" |
| Windows (WSL) | bash | `$OSTYPE` = "linux-gnu" |
| Windows (native) | PowerShell | When bash not available |

**Rule for this skill:**
1. ALL scripts in this document are written in **bash**
2. Claude Code on Windows typically runs through Git Bash (msys)
3. PowerShell snippets are provided **ONLY as reference for manual debugging**
4. Agent MUST use bash syntax when executing via Bash tool

**If bash commands fail on Windows:**
```
ERROR: Command failed (bash not available?)

This skill requires bash. On Windows, ensure:
- Git for Windows installed (includes Git Bash)
- OR WSL installed
- OR run commands manually using PowerShell equivalents below
```

**PowerShell equivalents (for manual use only):**

| Bash | PowerShell |
|------|------------|
| `ps -p $PID` | `Get-Process -Id $PID -EA SilentlyContinue` |
| `cat file` | `Get-Content file` |
| `rm -f file` | `Remove-Item file -Force -EA SilentlyContinue` |
| `rm -rf dir` | `Remove-Item dir -Recurse -Force -EA SilentlyContinue` |
| `grep pattern file` | `Select-String -Pattern pattern -Path file` |
| `mkdir -p dir` | `New-Item -ItemType Directory -Force dir` |

### Concurrent Session Prevention (v3.1)

**Before activating Worktree Mode, check for other active sessions:**

#### Lock File Mechanism

```bash
LOCK_FILE=".worktrees/.lock"

# Check for existing lock
if [ -f "$LOCK_FILE" ]; then
  LOCK_PID=$(cat "$LOCK_FILE" | head -1)
  LOCK_TIME=$(cat "$LOCK_FILE" | tail -1)

  # R1 FIX: Validate PID is a number before using
  if ! [[ "$LOCK_PID" =~ ^[0-9]+$ ]]; then
    echo "WARNING: Corrupted lock file (invalid PID: '$LOCK_PID')"
    echo "Removing corrupted lock..."
    rm -f "$LOCK_FILE"
  # Check if process still running
  elif ps -p $LOCK_PID > /dev/null 2>&1; then
    echo "ERROR: Another Worktree Mode session is active"
    echo "PID: $LOCK_PID, Started: $LOCK_TIME"
    echo "→ Falling back to sequential execution"
    WORKTREE_MODE_AVAILABLE=false
  else
    echo "Stale lock found (process $LOCK_PID not running)"
    echo "Removing stale lock..."
    rm -f "$LOCK_FILE"
  fi
fi

# Create lock if proceeding
if [ "$WORKTREE_MODE_AVAILABLE" = true ]; then
  mkdir -p .worktrees
  echo "$$" > "$LOCK_FILE"
  echo "$(date -Iseconds)" >> "$LOCK_FILE"
fi
```

#### Lock Release

**On worktree cleanup (success or failure):**

```bash
rm -f .worktrees/.lock
```

#### Windows Compatibility

```powershell
# Windows doesn't have ps -p, check if process exists
$LOCK_PID = Get-Content ".worktrees/.lock" -First 1
$process = Get-Process -Id $LOCK_PID -ErrorAction SilentlyContinue
if ($process) {
  Write-Error "Another session active"
} else {
  Remove-Item ".worktrees/.lock"
}
```

### Worktree Creation Flow

**When tasks with file conflicts are detected in same wave:**

```bash
# Step 1: Create worktrees for each conflicting task
for task_num in $CONFLICTING_TASKS; do
  WORKTREE_PATH=".worktrees/task-$task_num"
  BRANCH_NAME="wt/task-$task_num"

  git worktree add "$WORKTREE_PATH" -b "$BRANCH_NAME"
done

# Step 2: Record state
echo "WAVE_START=$(git rev-parse HEAD)" > .worktrees/.state
echo "WAVE_NUMBER=$WAVE_NUM" >> .worktrees/.state
echo "MERGE_ORDER=$CONFLICTING_TASKS" >> .worktrees/.state
```

### Disk Full Error Handling (v3.1)

**If disk space runs out during worktree creation:**

```bash
create_worktree() {
  local path=$1
  local branch=$2

  output=$(git worktree add "$path" -b "$branch" 2>&1)
  exit_code=$?

  if [ $exit_code -ne 0 ]; then
    if echo "$output" | grep -q "No space left on device"; then
      echo "ERROR: Disk full during worktree creation"
      echo ""
      echo "Cleaning up partial worktrees..."
      cleanup_all_worktrees
      echo ""
      echo "Please free up disk space and retry."
      echo "Required: approximately $(du -sh . | cut -f1) per worktree"
      return 1
    fi

    # Other error
    echo "ERROR: Failed to create worktree: $output"
    return 1
  fi

  return 0
}
```

**User Message on Disk Full:**

```
⚠️ Disk space exhausted during worktree creation

Operation aborted. Partial worktrees cleaned up.

Current disk usage:
$(df -h . | tail -1)

Project size:
$(du -sh .)

To proceed:
1. Free up disk space
2. Re-run the wave

Worktree Mode requires ~4x project size for 3 parallel worktrees.
```

### Worktree Execution

**Execute subagents in parallel, each in its own worktree:**

```bash
# Spawn subagents in parallel
for task_num in $CONFLICTING_TASKS; do
  WORKTREE_PATH=".worktrees/task-$task_num"

  # Dispatch subagent to work in worktree
  Task tool (general-purpose):
    description: "Implement Task $task_num in worktree"
    prompt: |
      You are implementing Task $task_num.

      IMPORTANT: Work in directory: $WORKTREE_PATH

      After implementation:
      1. Commit your changes to branch wt/task-$task_num
      2. Report what files you modified
done
```

### Sequential Merge Flow

**After all worktree subagents complete:**

```bash
# Step 1: Record pre-merge state
WAVE_START=$(grep "WAVE_START=" .worktrees/.state | cut -d= -f2)

# Step 2: Merge each worktree branch sequentially
for task_num in $CONFLICTING_TASKS; do
  BRANCH="wt/task-$task_num"

  echo "Merging $BRANCH..."

  git merge "$BRANCH" --no-edit

  if [ $? -ne 0 ]; then
    # Conflict detected - classify and handle
    echo "Merge conflict detected"
    # See Conflict Classification section
  fi

  # Update state
  sed -i "s/PENDING=/MERGED=$task_num,PENDING=/" .worktrees/.state
done
```

### Worktree Cleanup

**After successful merge or on failure:**

```bash
# Step 1: Remove worktrees
for task_num in $CONFLICTING_TASKS; do
  git worktree remove ".worktrees/task-$task_num" --force
done

# Step 2: Prune worktree metadata
git worktree prune

# Step 3: Delete branches
for task_num in $CONFLICTING_TASKS; do
  git branch -D "wt/task-$task_num"
done

# Step 4: Remove lock and state
rm -f .worktrees/.lock
rm -f .worktrees/.state

# Step 5: Cleanup directory if empty
rmdir .worktrees 2>/dev/null || true
```

---

## Post-Execution File Validation (v3.1)

**After subagent completes in worktree, BEFORE merge:**

### Step 2.5: Validate Actual Changed Files

**For each completed worktree:**

```bash
cd .worktrees/task-{N}
ACTUAL_FILES=$(git diff --name-only HEAD~1)
echo "Subagent modified: $ACTUAL_FILES"
```

### Compare with Declared

```
DECLARED_FILES = task.files_modified from task.md frontmatter
EXTRA_FILES = ACTUAL_FILES - DECLARED_FILES
```

### If Extra Files Found

```
⚠️ WARNING: Subagent modified undeclared files

Task 001 declared: [src/user.py]
Task 001 actually modified: [src/user.py, src/__init__.py, tests/conftest.py]

Undeclared files:
- src/__init__.py
- tests/conftest.py

Options:
1. Continue merge → accept extra files (risk: potential conflicts)
2. Abort and investigate → stop execution, examine changes
3. Re-run conflict detection → check for new conflicts with actual files

Which option?
```

### Re-Check Conflicts with Actual Files

```
FOR each worktree in wave:
  actual_files[worktree] = git diff --name-only HEAD~1

# Find overlapping files between worktrees
conflicts = []
for wt1, wt2 in combinations(worktrees, 2):
  overlap = actual_files[wt1] & actual_files[wt2]
  if overlap:
    conflicts.append((wt1, wt2, overlap))

IF conflicts:
  STOP: "Actual file conflict detected!"
  "Task 001 and Task 002 both modified: src/__init__.py"
  "This was not in declared files_modified."
  → Trigger Wave-Level Rollback
```

### Integration with Wave Execution

```
Wave execution flow:
1. Create worktrees
2. Spawn subagents in parallel
3. Wait for all to complete
4. **Validate actual files** ← NEW
5. If validation fails → rollback or user choice
6. If validation passes → proceed to merge
```

---

## Wave-Level Rollback (v3.1)

When merge requires human intervention, rollback the ENTIRE wave.

### Recording Wave Start

**Before ANY merge in wave:**

```bash
WAVE_START=$(git rev-parse HEAD)
echo "WAVE_START=$WAVE_START" >> .worktrees/.state
echo "WAVE_NUMBER=$WAVE_NUM" >> .worktrees/.state
```

### When to Trigger Wave Rollback

Wave rollback triggers when:
- ANY merge requires human intervention (`same_function`, `same_config`)
- Actual file conflict detected (from Post-Execution Validation)
- Merge causes test failures that can't be auto-fixed
- Post-merge smoke test fails critically

### Rollback Procedure

```bash
# 1. Abort current merge if in progress
git merge --abort 2>/dev/null || true

# 2. Reset to wave start
WAVE_START=$(grep "WAVE_START=" .worktrees/.state | cut -d= -f2)
git reset --hard $WAVE_START

# 3. Keep all worktrees for investigation
# (DO NOT cleanup worktrees)

# 4. Report to user
echo "Wave $WAVE_NUM rolled back to $WAVE_START"
echo "Worktrees preserved for investigation:"
git worktree list | grep wt/task-
```

### After Rollback — User Options

```
⚠️ Wave 1 rolled back

Reason: [same_function conflict / actual file conflict / smoke test failure]

Preserved worktrees:
- .worktrees/task-001 (changes: src/user.py)
- .worktrees/task-002 (changes: src/user.py) ← CONFLICT SOURCE

Merged commits reverted: 1

Options:
1. Manual resolution
   → Examine worktrees, fix conflict manually, then re-merge

2. Sequential fallback
   → Cleanup worktrees, execute tasks one by one (no parallelism)

3. Abort wave
   → Keep worktrees, stop execution, investigate

Which option?
```

### Option 1: Manual Resolution Flow

```
IF user chooses "Manual resolution":
  1. User examines .worktrees/task-001 and .worktrees/task-002
  2. User manually resolves conflict (edits files)
  3. User says "resolved"
  4. Agent verifies: git status shows no conflicts
  5. Agent continues: merge remaining worktrees
  6. Agent skips already-resolved conflict (don't re-merge)
```

### Option 2: Sequential Fallback Flow

```
IF user chooses "Sequential fallback":
  1. Cleanup all worktrees
  2. Re-add tasks to TODO (sequential)
  3. Execute tasks one by one
  4. No parallelism for this wave
```

### State File Format

```
# .worktrees/.state
WAVE_START=abc123def456
WAVE_NUMBER=1
LOCK_PID=12345
MERGE_ORDER=wt/task-001,wt/task-002,wt/task-003
MERGED=wt/task-001
PENDING=wt/task-002,wt/task-003
```

### Reading State File Safely (R4)

**Before using values from .state file, validate them:**

```bash
read_state_value() {
  local key=$1
  local file=".worktrees/.state"

  if [ ! -f "$file" ]; then
    echo ""
    return 1
  fi

  local value=$(grep "^${key}=" "$file" | cut -d= -f2)

  # Validate not empty
  if [ -z "$value" ]; then
    echo "WARNING: Empty or missing value for $key in .state file" >&2
    return 1
  fi

  echo "$value"
  return 0
}

# Usage example
WAVE_START=$(read_state_value "WAVE_START")
if [ $? -ne 0 ]; then
  echo "ERROR: Cannot read WAVE_START from state file"
  echo "State file may be corrupted. Options:"
  echo "1. Delete state file and start fresh: rm .worktrees/.state"
  echo "2. Manually inspect: cat .worktrees/.state"
  exit 1
fi
```

### State File Validation on Read

**When resuming from state file, validate ALL required fields:**

```bash
validate_state_file() {
  local required=("WAVE_START" "WAVE_NUMBER")
  local file=".worktrees/.state"

  if [ ! -f "$file" ]; then
    echo "ERROR: State file not found: $file"
    return 1
  fi

  for key in "${required[@]}"; do
    local value=$(grep "^${key}=" "$file" | cut -d= -f2)
    if [ -z "$value" ]; then
      echo "ERROR: State file missing or empty: $key"
      return 1
    fi
  done

  # Get WAVE_START for git ref validation
  local wave_start=$(grep "^WAVE_START=" "$file" | cut -d= -f2)

  # Validate WAVE_START is valid git ref
  if ! git rev-parse "$wave_start" >/dev/null 2>&1; then
    echo "ERROR: WAVE_START is not a valid git ref: $wave_start"
    return 1
  fi

  echo "State file validated successfully"
  return 0
}
```

### Corrupted State File Recovery

**If state file validation fails:**

```
⚠️ Corrupted state file detected

File: .worktrees/.state
Issue: [WAVE_START missing / invalid git ref / file truncated]

Options:
1. Delete state file and cleanup worktrees
   → rm .worktrees/.state
   → Cleanup all task worktrees
   → Start fresh

2. Attempt manual recovery
   → Show current state file contents
   → User can fix manually

Which option?
```

---

## How Claude Classifies Conflicts (v3.1)

**Step-by-step instructions for the agent:**

### Step 1: Read the Conflicted File

```bash
cat src/user.py
```

### Step 2: Find Conflict Markers

Look for this pattern:
```
<<<<<<< HEAD
[code that was in main branch]
=======
[code from worktree branch]
>>>>>>> wt/task-002
```

### Step 3: Analyze BOTH Sides

**Ask yourself these questions:**
- What did HEAD (main branch) add? Is it a function? An import? A config value?
- What did the worktree branch add? Is it a function? An import? A config value?
- Are they the SAME thing with different implementations, or DIFFERENT things?

### Step 4: Classify Using This Table

| I see in the conflict... | Classification | What to do |
|--------------------------|----------------|------------|
| Two DIFFERENT function definitions (different names) | `independent_additions` | Keep both functions |
| Two changes to the SAME function (same name) | `same_function` | **STOP** - ask human |
| Identical import lines | `duplicate_import` | Keep one, delete the duplicate |
| Different import lines | `independent_additions` | Keep both imports |
| Same config key with different values | `same_config` | **STOP** - ask human |
| Not sure / complex change | `unknown` | **STOP** - ask human |

### Step 5: Resolve or Stop

**If `independent_additions`:**
1. Remove the conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
2. Keep BOTH pieces of code
3. Ensure proper spacing between them
4. Save the file
5. Stage: `git add <file>`
6. Commit with message explaining resolution

**If `duplicate_import`:**
1. Remove the conflict markers
2. Keep ONE copy of the import line
3. Delete the duplicate
4. Save and stage

**If `same_function`, `same_config`, or `unknown`:**
1. DO NOT try to resolve automatically
2. Report to user immediately:

```
STOP: Conflict requires human resolution

File: src/user.py
Type: same_function

Both Task 001 and Task 002 modified the `process()` function.
I cannot determine which changes to keep.

The conflict:
<<<<<<< HEAD
def process(self, data):
    logger.info("Processing")  # Added by Task 001
    return self._internal_process(data)
=======
def process(self, data):
    if not self.validate(data):  # Added by Task 002
        raise ValueError("Invalid data")
    return self._internal_process(data)
>>>>>>> wt/task-002

Please resolve manually and tell me when done.
```

### Example: Resolving Independent Additions

**Before (conflict in file):**
```python
class User:
    def __init__(self, name):
        self.name = name

<<<<<<< HEAD
    def get_name(self):
        return self.name
=======
    def validate_email(self):
        return "@" in self.email
>>>>>>> wt/task-002
```

**I analyze:**
- HEAD added `get_name()` function
- Worktree added `validate_email()` function
- Different function names → `independent_additions`

**After (resolved):**
```python
class User:
    def __init__(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def validate_email(self):
        return "@" in self.email
```

**Commit:**
```bash
git add src/user.py
git commit -m "merge: resolved wt/task-002 (independent_additions)

Both methods added to User class:
- get_name() from task-001
- validate_email() from task-002"
```

---

## Post-Merge Smoke Test (v3.1)

**After ALL merges in wave complete, BEFORE full test suite:**

### Run Smoke Tests

```bash
# Quick verification that merge didn't break basics
# Try in order of preference:

# 1. Dedicated smoke tests
pytest tests/smoke/ -v --timeout=60 2>/dev/null && exit 0

# 2. Tests marked as smoke
pytest tests/ -k "smoke" -v --timeout=60 2>/dev/null && exit 0

# 3. Quick subset - first failure stops
pytest tests/ -v --timeout=120 -x --ignore=tests/e2e/ 2>/dev/null && exit 0

# 4. No tests found - warn and continue
echo "WARNING: No smoke tests found, skipping smoke test phase"
```

### On Success

```
✓ Post-merge smoke test passed (12 tests in 3.2s)

Proceeding to code review...
```

### Smoke Test Failure Policy (STRICT)

**RULE: Any failure = STOP and ask user**

Do NOT try to determine if failure is "related" or "unrelated" to merge.
Human judgment required for ALL smoke test failures.

**On ANY failure:**

```
⚠️ Post-merge smoke test FAILED

Failed tests:
- tests/test_user.py::test_user_creation
- tests/test_legacy.py::test_deprecated_api

I cannot determine if these failures are caused by the merge.

Options:
1. Investigate failures
   → I will examine test output and merged code

2. Wave rollback
   → Reset to WAVE_START, preserve worktrees

3. User confirms pre-existing
   → User states these tests were already failing before merge
   → I will proceed (user takes responsibility)

Which option?
```

**Exception:** If user explicitly pre-approved known failing tests:
```yaml
# In task context or user message:
known_failing_tests:
  - tests/test_legacy.py::test_deprecated_api
```
Then skip these specific tests in failure analysis.

---

## The Process

### 1. Load Plan & Analyze Waves

**Step 1.1:** Read plan file (tech-spec.md or plan file)

**Step 1.2:** Read all task files and extract:
```
For each task.md:
  - task number
  - depends_on (default: [] if not specified)
  - files_modified (default: [] if not specified)
```

**Step 1.3:** Build wave assignment:
```
wave_map = {}
for task in tasks:
  if task.depends_on is empty:
    wave_map[task] = 1
  else:
    max_dependency_wave = max(wave_map[dep] for dep in task.depends_on)
    wave_map[task] = max_dependency_wave + 1

# Check file conflicts within waves
for wave in waves:
  files_in_wave = collect all files_modified from tasks in wave
  if any file appears twice:
    move later task to next wave
```

**Step 1.4:** Create TodoWrite with all tasks

**Step 1.5:** Announce wave plan to user:
```
"Wave analysis complete:
  Wave 1: [task-001, task-002, task-003] (parallel)
  Wave 2: [task-004] (depends on Wave 1)
  Wave 3: [task-005] (depends on Wave 2)

Starting execution..."
```

### 2. Execute Wave (or Task)

**IF current wave has 3+ tasks:**

Spawn ALL subagents in parallel:
```
Task tool (general-purpose) x3:
  description: "Implement Task N: [task name]"
  prompt: |
    You are implementing Task N from [plan-file].
    ... (same as before)
```

Wait for ALL subagents to complete.
Run code review for each completed task.
Move to next wave.

**ELSE (wave has 1-2 tasks):**

Execute sequentially (standard flow below).

### 2-alt. Execute Single Task with Subagent (sequential mode)

For each task in wave (when wave has <3 tasks):

**Dispatch fresh subagent:**
```
Task tool (general-purpose):
  description: "Implement Task N: [task name]"
  prompt: |
    You are implementing Task N from [plan-file].

    Read that task carefully. Your job is to:
    1. Implement exactly what the task specifies
    2. Write tests (following TDD if task says to)
    3. Verify implementation works
    4. Commit your work
    5. Report back

    Work from: [directory]

    Report: What you implemented, what you tested, test results, files changed, any issues
```

**Subagent reports back** with summary of work.

### 3. Review Subagent's Work

**Dispatch code-reviewer subagent:**
```
Task tool (superpowers:code-reviewer):
  Use template at requesting-code-review/code-reviewer.md

  WHAT_WAS_IMPLEMENTED: [from subagent's report]
  PLAN_OR_REQUIREMENTS: Task N from [plan-file]
  BASE_SHA: [commit before task]
  HEAD_SHA: [current commit]
  DESCRIPTION: [task summary]
```

**Code reviewer returns:** Strengths, Issues (Critical/Important/Minor), Assessment

### 4. Apply Review Feedback

**If issues found:**
- Fix Critical issues immediately
- Fix Important issues before next task
- Note Minor issues

**Dispatch follow-up subagent if needed:**
```
"Fix issues from code review: [list issues]"
```

### 5. Mark Complete, Next Task

- Mark task as completed in TodoWrite
- Move to next task
- Repeat steps 2-5

### 6. Final Review

After all tasks complete, dispatch final code-reviewer:
- Reviews entire implementation
- Checks all plan requirements met
- Validates overall architecture

### 7. User Acceptance Testing (MANDATORY)

**After final code review passes, BEFORE completion:**

```
1. Announce: "Phase change: implementation -> UAT"
2. Load UAT skill: cat .claude/skills/user-acceptance-testing/SKILL.md
3. Read user-spec.md from feature folder
4. Generate UAT scenarios from user-spec
5. Present checklist to user for testing
6. WAIT for user response
7. If issues found:
   - Fix issues (dispatch subagent if needed)
   - Re-run UAT for fixed items
8. If passed: Proceed to Step 8
```

**Without UAT confirmation from user, implementation is NOT complete.**

### 8. Complete Development

After UAT passes:
- Announce: "I'm using the finishing-a-development-branch skill to complete this work."
- **REQUIRED SUB-SKILL:** Use superpowers:finishing-a-development-branch
- Follow that skill to verify tests, present options, execute choice

## Example Workflow

### Sequential Mode (< 3 independent tasks)

```
You: I'm using Subagent-Driven Development to execute this plan.

[Load plan, analyze waves]
Wave analysis: Wave 1 has 2 tasks → sequential mode

Task 1: Hook installation script
[Dispatch implementation subagent]
Subagent: Implemented install-hook with tests, 5/5 passing
[Code review] → Ready

Task 2: Recovery modes
[Dispatch implementation subagent]
Subagent: Added verify/repair, 8/8 tests passing
[Code review] → Issues found → Fix → Ready

[Final review]
Done!
```

### Parallel Mode (3+ independent tasks)

```
You: I'm using Subagent-Driven Development to execute this plan.

[Load plan, analyze waves]
Wave analysis complete:
  Wave 1: [task-001, task-002, task-003] (parallel - 3 independent)
  Wave 2: [task-004] (depends on 001, 002)
  Wave 3: [task-005] (depends on 004)

Starting Wave 1 (PARALLEL)...

[Spawn 3 subagents simultaneously]
  Subagent 1: Implementing task-001...
  Subagent 2: Implementing task-002...
  Subagent 3: Implementing task-003...

[All complete]
  Subagent 1: Done - user model created, 5/5 tests
  Subagent 2: Done - API endpoints, 8/8 tests
  Subagent 3: Done - validation layer, 6/6 tests

[Code review for each]
  Review 001: Ready
  Review 002: Ready
  Review 003: Minor issue → Fix → Ready

Wave 1 complete. Starting Wave 2...

[Task 004 - sequential]
Subagent: Integration layer complete
[Review] → Ready

Wave 2 complete. Starting Wave 3...

[Task 005 - sequential]
Subagent: E2E tests complete
[Review] → Ready

[Final review]
All 5 tasks complete.

Phase change: implementation -> UAT
[Load UAT skill]
[Generate scenarios from user-spec.md]

UAT Checklist:
1. [ ] Create new user with valid data → user appears in DB
2. [ ] API returns user list → correct format
3. [ ] Invalid email rejected → validation error shown

User: "All scenarios passed!"

UAT passed. Ready to complete.
```

## Advantages

**vs. Manual execution:**
- Subagents follow TDD naturally
- Fresh context per task (no confusion)
- Parallel-safe (subagents don't interfere)

**vs. Executing Plans:**
- Same session (no handoff)
- Continuous progress (no waiting)
- Review checkpoints automatic

**Cost:**
- More subagent invocations
- But catches issues early (cheaper than debugging later)

## Red Flags

**Never:**
- Skip code review between tasks (or after each wave)
- Proceed with unfixed Critical issues
- Run parallel tasks that modify SAME files WITHOUT Worktree Mode
- **Skip Worktree Mode when files overlap AND platform check passes** ← VIOLATION
- Implement without reading plan task
- Run more than 3 subagents in parallel (quality degrades)
- Claim "files overlap so can't parallelize" — use Worktree Mode instead!

**If subagent fails task:**
- Dispatch fix subagent with specific instructions
- Don't try to fix manually (context pollution)

**If parallel execution has conflicts:**
- Stop all subagents
- Rebuild wave map with stricter file conflict detection
- Restart from last successful wave

**Worktree Mode specific (v3.1):**
- Skip post-execution validation (may miss undeclared file changes)
- Skip wave-level rollback when human conflict detected
- Ignore concurrent session lock
- Skip post-merge smoke test
- Remove worktrees with uncommitted changes without warning
- Proceed after smoke test failure without user confirmation
- Auto-resolve `same_function` or `same_config` conflicts (always ask human)

## Integration

**Required workflow skills:**
- **requesting-code-review** - REQUIRED: Review after each task (see Step 3)
- **user-acceptance-testing** - REQUIRED: UAT after final review (see Step 7)
- **finishing-a-development-branch** - REQUIRED: Complete development after UAT (see Step 8)

**Subagents must use:**
- **test-driven-development** - Subagents follow TDD for each task

**Alternative workflow:**
- **executing-plans** - Use for parallel session instead of same-session execution

See code-reviewer template: requesting-code-review/code-reviewer.md

## Background Task Tracking

Track parallel subagent execution in `work/background-tasks.json` for visibility and debugging.

### JSON Structure

```json
{
  "version": "1.0",
  "tasks": [
    {
      "id": "task-001-wave1",
      "taskFile": "work/feature/tasks/task-001.md",
      "taskTitle": "Create user model",
      "agent": "code-developer",
      "model": "claude-opus-4-5-20251101",
      "wave": 1,
      "status": "completed",
      "startedAt": "2026-01-19T10:00:00Z",
      "completedAt": "2026-01-19T10:05:30Z",
      "duration": 330,
      "result": "User model created with 5/5 tests passing",
      "error": null
    }
  ],
  "activeWave": 1,
  "lastUpdated": "2026-01-19T10:05:30Z"
}
```

### Task Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (e.g., `task-001-wave1`) |
| `taskFile` | string | Path to task.md file |
| `taskTitle` | string | Human-readable task title |
| `agent` | string | Agent type (`code-developer`, `code-reviewer`) |
| `model` | string | Model used for execution |
| `wave` | number | Wave number (1, 2, 3...) |
| `status` | string | `pending` / `running` / `completed` / `failed` / `cancelled` |
| `startedAt` | string | ISO 8601 timestamp when started |
| `completedAt` | string | ISO 8601 timestamp when completed (null if running) |
| `duration` | number | Duration in seconds (null if not completed) |
| `result` | string | Summary of accomplishment (null if not completed) |
| `error` | string | Error message if failed (null if no error) |

### When Dispatching Tasks

**Before spawning subagent:**

```python
# 1. Read current state
tasks_json = read("work/background-tasks.json")

# 2. Add new task entry
new_task = {
    "id": f"task-{task_num}-wave{wave_num}",
    "taskFile": "work/feature/tasks/task-001.md",
    "taskTitle": "Task title from task.md",
    "agent": "code-developer",
    "model": "claude-opus-4-5-20251101",
    "wave": wave_num,
    "status": "running",
    "startedAt": now_iso8601(),
    "completedAt": null,
    "duration": null,
    "result": null,
    "error": null
}

# 3. Update JSON
tasks_json["tasks"].append(new_task)
tasks_json["activeWave"] = wave_num
tasks_json["lastUpdated"] = now_iso8601()

# 4. Write back
write("work/background-tasks.json", tasks_json)

# 5. THEN spawn subagent
```

### On Task Completion

**When subagent returns:**

```python
# 1. Read current state
tasks_json = read("work/background-tasks.json")

# 2. Find and update task
for task in tasks_json["tasks"]:
    if task["id"] == completed_task_id:
        task["status"] = "completed"  # or "failed"
        task["completedAt"] = now_iso8601()
        task["duration"] = calculate_duration(task["startedAt"], task["completedAt"])
        task["result"] = subagent_summary  # what was accomplished
        task["error"] = error_message if failed else null
        break

# 3. Check if wave complete
wave_tasks = [t for t in tasks_json["tasks"] if t["wave"] == current_wave]
if all(t["status"] in ["completed", "failed"] for t in wave_tasks):
    tasks_json["activeWave"] = current_wave + 1  # or null if done

# 4. Update timestamp
tasks_json["lastUpdated"] = now_iso8601()

# 5. Write back
write("work/background-tasks.json", tasks_json)
```

### Checking Wave Status

**Before proceeding to next wave:**

```python
# Read and check wave status
tasks_json = read("work/background-tasks.json")

current_wave = tasks_json["activeWave"]
wave_tasks = [t for t in tasks_json["tasks"] if t["wave"] == current_wave]

# Check all completed
all_done = all(t["status"] in ["completed", "failed"] for t in wave_tasks)
any_failed = any(t["status"] == "failed" for t in wave_tasks)

if not all_done:
    # Still waiting for subagents
    running = [t["taskTitle"] for t in wave_tasks if t["status"] == "running"]
    print(f"Wave {current_wave} still running: {running}")
    return

if any_failed:
    # Handle failures before proceeding
    failed = [t for t in wave_tasks if t["status"] == "failed"]
    for task in failed:
        print(f"FAILED: {task['taskTitle']}")
        print(f"Error: {task['error']}")
    # Decide: fix and retry, or abort
    return

# All passed - proceed to next wave
print(f"Wave {current_wave} complete. Proceeding to Wave {current_wave + 1}")
```

### Status Messages

**Report to user after each wave:**

```
Wave 1 Status (3 tasks):
  [x] task-001: Create user model (330s) - 5/5 tests
  [x] task-002: API endpoints (420s) - 8/8 tests
  [x] task-003: Validation layer (280s) - 6/6 tests

All Wave 1 tasks complete. Proceeding to Wave 2...
```

### Cleanup

**After plan execution completes:**

```python
# Option 1: Archive
mv work/background-tasks.json work/completed/background-tasks-{feature}.json

# Option 2: Reset for next run
reset_json = {
    "version": "1.0",
    "description": "Tracks parallel subagent task execution",
    "tasks": [],
    "activeWave": null,
    "lastUpdated": null
}
write("work/background-tasks.json", reset_json)
```
