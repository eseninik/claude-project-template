---
name: session-resumption
version: 2.0.0
description: |
  Resume incomplete work from previous session.

  AUTOMATIC TRIGGER:
  - Session start when STATE.md has incomplete work
  - User says "/resume" or "продолжить работу"

  Do NOT use for: starting fresh work (just start normally)

  NEW in v2.0:
  - Git State Check (interrupted merge/rebase)
  - Worktree Cleanup Check (stale worktrees from Worktree Mode)

changelog:
  - version: 2.0.0
    date: 2026-01-21
    changes:
      - Added Git State Check for interrupted merge/rebase
      - Added Worktree Cleanup Check for stale worktrees
      - Integration with subagent-driven-development Worktree Mode
---

# Session Resumption Skill

Resume incomplete work by parsing STATE.md and presenting resumption options to user.

## Overview

When a session starts and previous work is incomplete, this skill:
1. Parses STATE.md to extract current state
2. Displays a clear summary of where we left off
3. Asks user whether to resume or start fresh
4. If resuming, loads appropriate context and continues

## When to Use

Activate this skill when:
- Starting a new session with existing STATE.md
- STATE.md shows incomplete work (status != completed)
- User explicitly requests "/resume"

**Do NOT use for:**
- Fresh starts with no previous work
- Completed work (STATE.md status = completed)

---

## Check Order (v2.0)

On session start, perform checks in this order:

```
SESSION START:
  1. Git State Check (merge/rebase in progress)  ← NEW
  2. Worktree Cleanup Check (stale worktrees)    ← NEW
  3. STATE.md Check (incomplete work)            ← EXISTING
```

---

## Git State Check (v2.0 — FIRST CHECK)

**On session start, BEFORE anything else, check for interrupted git operations:**

### Check 1: Interrupted Merge

```bash
# Check if merge is in progress
if git rev-parse MERGE_HEAD >/dev/null 2>&1; then
  MERGE_IN_PROGRESS=true
  MERGING_BRANCH=$(git name-rev MERGE_HEAD --name-only 2>/dev/null || echo "unknown")
fi
```

**If merge in progress, display:**

```
⚠️ Found interrupted merge operation

Merging branch: wt/task-002
Status: Conflicts need resolution

Files with conflicts:
$(git diff --name-only --diff-filter=U)

This likely happened because:
- Previous session ended during Worktree Mode merge
- Network/power failure during merge
- Claude Code was terminated

Options:
1. Abort merge and rollback
   → git merge --abort
   → Returns to state before merge started

2. Continue merge
   → Resolve conflicts manually
   → Then: git add <files> && git commit

3. Show conflict details
   → Display git diff for conflicted files

Which option?
```

### Check 2: Interrupted Rebase

```bash
# Check if rebase is in progress
if [ -d ".git/rebase-merge" ] || [ -d ".git/rebase-apply" ]; then
  REBASE_IN_PROGRESS=true
fi
```

**If rebase in progress, display:**

```
⚠️ Found interrupted rebase operation

Options:
1. Abort rebase → git rebase --abort
2. Continue rebase → git rebase --continue (after resolving conflicts)
3. Skip current commit → git rebase --skip

Which option?
```

### Check 3: Uncommitted Changes in Main Branch

```bash
# Check for uncommitted changes
UNCOMMITTED=$(git status --porcelain)
if [ -n "$UNCOMMITTED" ]; then
  HAS_UNCOMMITTED=true
fi
```

**If uncommitted changes, warn:**

```
⚠️ Uncommitted changes in working directory

Modified files:
$(git status --short)

This may affect Worktree Mode operation.

Options:
1. Stash changes → git stash -m "Auto-stash before worktree mode"
2. Commit changes → Will prompt for commit message
3. Continue anyway → May cause issues (not recommended)

Which option?
```

### Integration with Worktree Cleanup

After Git State Check passes, proceed to Worktree Cleanup Check:

```
IF git state clean:
  → Proceed to Worktree Cleanup Check
ELSE:
  → Handle git state issue first
  → Then re-run checks
```

---

## Worktree Cleanup Check (v2.0)

**After Git State Check, check for stale worktrees:**

```bash
# Check for task worktrees from previous session
STALE_WORKTREES=$(git worktree list | grep "wt/task-" || true)

if [ -n "$STALE_WORKTREES" ]; then
  echo "Found stale task worktrees from previous session:"
  echo "$STALE_WORKTREES"
fi
```

**If found, present options:**

```
Found stale task worktrees from previous session:
- .worktrees/task-001 (branch: wt/task-001)
- .worktrees/task-002 (branch: wt/task-002)

This may indicate interrupted Worktree Mode execution.

State file: $(cat .worktrees/.state 2>/dev/null || echo "not found")

Options:
1. Cleanup worktrees and start fresh
   → Remove all task worktrees and branches
   → Clear state file

2. Attempt to resume merge from where it stopped
   → Read .worktrees/.state
   → Continue from last successful merge
   → Requires state file to exist

3. Keep worktrees (investigate manually)
   → Just warn and continue
   → User will handle cleanup

Which option?
```

### Option 1: Cleanup (with safety check)

```bash
# Check for uncommitted changes first (Pre-Cleanup Safety)
for worktree in .worktrees/task-*; do
  if [ -d "$worktree" ]; then
    cd "$worktree"
    if [ -n "$(git status --porcelain)" ]; then
      echo "⚠️ Uncommitted changes in $worktree"
      # Offer stash/commit/discard options
    fi
    cd -
  fi
done

# Then cleanup
git worktree remove .worktrees/task-001 --force
git worktree remove .worktrees/task-002 --force
git branch -D wt/task-001 wt/task-002
git worktree prune
rm -f .worktrees/.state
rm -f .worktrees/.lock
```

### Option 2: Resume merge

- Read `.worktrees/.state` if exists
- Get WAVE_START, MERGED, PENDING
- Continue from last successful merge
- If no state file, fall back to Option 1

### Option 3: Keep

- Just warn and continue
- User will handle manually
- May cause issues if user forgets

---

## STATE.md Parsing Algorithm

STATE.md uses Russian section headers. Parse these sections:

```
PARSE(state_file):
  sections = {}

  # Find "Текущая работа" (Current Work)
  current_work = extract_section("## Текущая работа")
  IF current_work:
    sections.task = extract_field("Task:|Задача:")
    sections.phase = extract_field("Phase:|Фаза:")
    sections.status = extract_field("Status:|Статус:")
    sections.feature = extract_field("Feature:|Фича:")

  # Find "Следующие шаги" (Next Steps)
  next_steps = extract_section("## Следующие шаги")
  IF next_steps:
    sections.next_steps = extract_bullet_list(next_steps)

  # Find "Блокеры" (Blockers)
  blockers = extract_section("## Блокеры")
  IF blockers:
    sections.blockers = extract_bullet_list(blockers)

  # Find "Session Notes" (usually English)
  session_notes = extract_section("## Session Notes")
  IF session_notes:
    sections.last_session_date = extract_date(session_notes)
    sections.notes = session_notes

  # Find "Key Decisions" table
  decisions = extract_section("## Key Decisions")
  IF decisions:
    sections.decisions = parse_markdown_table(decisions)

  RETURN sections
```

### Field Extraction Helpers

```
extract_field(pattern):
  # Match "Pattern: value" or "Pattern value"
  regex = f"{pattern}\\s*(.+)"
  match = search(regex, section)
  RETURN match.group(1).strip() if match else null

extract_bullet_list(section):
  lines = section.split("\n")
  items = []
  FOR line IN lines:
    IF line.startswith("- ") OR line.startswith("* "):
      items.append(line[2:].strip())
  RETURN items

extract_date(section):
  # Look for date pattern YYYY-MM-DD
  regex = r"\d{4}-\d{2}-\d{2}"
  match = search(regex, section)
  RETURN match.group(0) if match else null
```

## Resumption Summary Display

Present parsed information clearly to user (in Russian):

```
DISPLAY_SUMMARY(parsed):
  message = """
  📋 **Незавершённая работа**

  **Фича:** {parsed.feature}
  **Задача:** {parsed.task}
  **Фаза:** {parsed.phase}
  **Статус:** {parsed.status}
  **Последняя сессия:** {parsed.last_session_date}
  """

  IF parsed.next_steps:
    message += """
  **Следующие шаги:**
  """
    FOR step IN parsed.next_steps:
      message += f"  - {step}\n"

  IF parsed.blockers:
    message += """
  **Блокеры:**
  """
    FOR blocker IN parsed.blockers:
      message += f"  - ⚠️ {blocker}\n"

  RETURN message
```

## User Interaction

After displaying summary, ask user:

```
ASK_USER:
  "Продолжить с того места, где остановились?

  Варианты:
  1. **Да** - продолжить работу
  2. **Нет** - начать заново (STATE.md будет очищен)
  3. **Показать детали** - показать больше контекста"
```

### Response Handling

```
HANDLE_RESPONSE(response):
  IF response == "да" OR response == "1" OR response == "continue":
    # Resume from current state
    LOAD_CONTEXT(parsed.feature)
    CONTINUE_FROM_PHASE(parsed.phase, parsed.status)
    RETURN { action: "resume", context_loaded: true }

  IF response == "нет" OR response == "2" OR response == "fresh":
    # Clear STATE.md and start fresh
    CLEAR_STATE_MD()
    RETURN { action: "fresh", context_loaded: false }

  IF response == "детали" OR response == "3" OR response == "details":
    # Show more details
    SHOW_FULL_STATE_MD()
    # Ask again
    RETURN ASK_USER()
```

## Context Loading on Resume

When resuming, load relevant context:

```
LOAD_CONTEXT(feature):
  # Read feature specs if they exist
  IF exists(work/{feature}/user-spec.md):
    Read: work/{feature}/user-spec.md

  IF exists(work/{feature}/tech-spec.md):
    Read: work/{feature}/tech-spec.md

  # Read tasks to understand progress
  IF exists(work/{feature}/tasks/):
    FOR task_file IN glob(work/{feature}/tasks/*.md):
      Read: task_file
      # Check status in frontmatter

  # Load project context guides
  Read: .claude/skills/project-knowledge/guides/architecture.md
  Read: .claude/skills/project-knowledge/guides/patterns.md
```

## Integration with Orchestrator

This skill provides structured output for orchestrator:

```json
{
  "skill": "session-resumption",
  "action": "resume",
  "state": {
    "feature": "dark-mode",
    "task": "Task 3: Add theme toggle",
    "phase": "implementation",
    "status": "in_progress",
    "lastSession": "2026-01-18"
  },
  "nextSteps": [
    "Complete theme toggle component",
    "Write tests",
    "Run verification"
  ],
  "blockers": [],
  "contextLoaded": [
    "work/dark-mode/tech-spec.md",
    "work/dark-mode/tasks/3.md"
  ]
}
```

## Error Handling

### Missing STATE.md

```
IF NOT exists(work/STATE.md):
  Tell user: "Нет незавершённой работы. STATE.md не найден."
  RETURN { action: "none", reason: "no_state_file" }
```

### Malformed STATE.md

```
IF parse_error:
  Tell user: "STATE.md повреждён или имеет неверный формат."
  Show: raw contents of STATE.md
  Ask: "Хотите очистить и начать заново?"
  RETURN { action: "error", reason: "malformed" }
```

### Empty STATE.md

```
IF parsed.task == null AND parsed.status == null:
  Tell user: "STATE.md пуст - нет активной работы."
  RETURN { action: "none", reason: "empty_state" }
```

### Completed Work

```
IF parsed.status == "completed" OR parsed.status == "завершено":
  Tell user: "Предыдущая работа завершена. Готовы к новой задаче."
  RETURN { action: "completed", reason: "work_done" }
```

## Example Flow

```
[Session starts]

Agent: Checking for incomplete work...
Agent: *reads work/STATE.md*

Agent displays:
  📋 **Незавершённая работа**

  **Фича:** dark-mode
  **Задача:** Task 3: Add theme toggle component
  **Фаза:** implementation
  **Статус:** in_progress
  **Последняя сессия:** 2026-01-18

  **Следующие шаги:**
  - Complete ThemeToggle component
  - Add tests for theme switching
  - Integrate with settings page

  **Блокеры:**
  - (нет)

  Продолжить с того места, где остановились?

User: да

Agent: Загружаю контекст...
Agent: *reads tech-spec.md, tasks/3.md*
Agent: Продолжаю реализацию ThemeToggle компонента.
```

## /resume Command Integration

The `/resume` command uses this skill:

```markdown
# /resume command

1. Invoke session-resumption skill
2. Display summary
3. Handle user response
4. If resume: continue work
5. If fresh: clear state, await new task
```
