# Background Task Tracking Reference

Track parallel subagent execution in `work/background-tasks.json`.

## JSON Structure

```json
{
  "version": "1.0",
  "tasks": [
    {
      "id": "task-001-wave1",
      "taskFile": "work/feature/tasks/task-001.md",
      "taskTitle": "Create user model",
      "agent": "code-developer",
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

## Task Fields

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique: `task-{N}-wave{W}` |
| taskFile | string | Path to task.md |
| taskTitle | string | Human-readable title |
| agent | string | Agent type (code-developer, code-reviewer) |
| wave | number | Wave number |
| status | string | pending / running / completed / failed / cancelled |
| startedAt | string | ISO 8601 timestamp |
| completedAt | string | ISO 8601 or null |
| duration | number | Seconds or null |
| result | string | Summary or null |
| error | string | Error message or null |

## When Dispatching

Before spawning subagent:
1. Read `work/background-tasks.json`
2. Add task entry with status "running"
3. Write back
4. Spawn subagent

## On Completion

When subagent returns:
1. Read JSON
2. Update task: status, completedAt, duration, result (or error)
3. Check if wave complete (all tasks completed/failed)
4. If wave done: increment activeWave
5. Write back

## Wave Status Check

Before proceeding to next wave:
- Verify all wave tasks are completed or failed
- If any failed: handle failures before proceeding
- Report wave summary to user

## Status Report Format

```
Wave 1 Status (3 tasks):
  [x] task-001: Create user model (330s) - 5/5 tests
  [x] task-002: API endpoints (420s) - 8/8 tests
  [x] task-003: Validation layer (280s) - 6/6 tests

All Wave 1 tasks complete. Proceeding to Wave 2...
```

## Cleanup

After plan execution: archive to `work/completed/background-tasks-{feature}.json` or reset.
