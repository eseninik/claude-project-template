# Results Board

> Shared knowledge board for agent coordination. All agents post results (including failures).
> Loaded via: `cat .claude/guides/results-board.md`

---

## What Is It

A shared file (`work/results-board.md`) where agents record their experiment results, approach outcomes, and discoveries. Inspired by Karpathy's AgentHub `#results` channel.

**Core principle:** Share negative results too. If Agent 1 tried approach X and it failed, Agent 2 should know before wasting time on the same approach.

---

## When to Use

- **Agent Teams mode** — multiple agents working in parallel on related tasks
- **Experiment Loop** — recording all experiment outcomes
- **Pipeline phases** — sharing learnings between phases
- **Any parallel work** where agents might duplicate effort

---

## File Location

`work/results-board.md` — auto-created at pipeline start or first agent entry.

---

## Entry Format

Each agent appends entries to the board. Format:

```
### [{timestamp}] {agent_name} — {task_name}
- **Approach:** {what was tried}
- **Result:** {what happened — metric value, error message, or outcome}
- **Status:** KEEP | DISCARD | CRASH | IN_PROGRESS
- **Commit:** {short hash or N/A}
- **Insight:** {what was learned, especially from failures}
```

Example entries:

```
### [2026-03-11 14:30] backend-dev — Optimize DB queries
- **Approach:** Added index on users.email column
- **Result:** Query time 450ms → 12ms (97% improvement)
- **Status:** KEEP
- **Commit:** a1b2c3d
- **Insight:** Missing index was root cause, not ORM overhead

### [2026-03-11 14:35] backend-dev — Optimize DB queries
- **Approach:** Switched from ORM to raw SQL
- **Result:** Query time 450ms → 380ms (only 15% improvement, more complex code)
- **Status:** DISCARD
- **Commit:** N/A (reverted)
- **Insight:** ORM overhead was minimal — the real bottleneck was the missing index

### [2026-03-11 14:40] api-dev — Add caching layer
- **Approach:** Redis cache for /api/users endpoint
- **Result:** CRASH — Redis connection refused (not installed on dev)
- **Status:** CRASH
- **Commit:** N/A
- **Insight:** Need Redis setup before implementing caching
```

---

## Agent Protocol

### Before Starting Work
```
IF work/results-board.md exists:
  Read the board
  Check for entries related to your task
  Note failed approaches to AVOID repeating them
  Note successful approaches to BUILD ON
```

### After Completing Work
```
Append your result entry to work/results-board.md
Include: approach, result, status, commit, insight
ESPECIALLY record failures — they save other agents time
```

### During Experiment Loop
```
Each experiment iteration appends to the board automatically
Format matches experiment-log.md but in board-friendly format
```

---

## Board Initialization

When creating a new pipeline or starting Agent Teams, initialize the board:

```markdown
# Results Board

> Shared results for team coordination. Read before starting, write after finishing.
> Each entry: what was tried, what happened, and what was learned.

---
```

---

## Integration Points

| System | How Results Board Integrates |
|--------|----------------------------|
| **Agent Teams** | Each agent reads board at start, appends at end |
| **Experiment Loop** | Auto-posts each experiment result |
| **Pipeline phases** | Results persist across phases |
| **Self-completion** | Each completed task gets a board entry |
| **QA Review** | Reviewer can check board for context on approaches tried |

---

## Anti-Patterns

| Anti-Pattern | Fix |
|-------------|-----|
| Only recording successes | Record ALL results, failures are MORE valuable |
| Verbose entries | Keep entries concise — 1-2 lines per field |
| Not reading board before starting | ALWAYS read first — avoid duplicate work |
| Deleting entries | Board is append-only — never delete |
| Skipping insight field | Always explain WHY something worked or failed |
