# Recovery Manager

Tracks attempt history per subtask, detects circular fixes, and provides recovery actions.
Prevents wasted effort by stopping repeated failing approaches and escalating to human.

## When to Use

- After 2+ failed attempts at the same subtask
- When systematic-debugging escalates (3+ failed hypotheses)
- When qa-validation-loop detects same issue 3+ iterations
- When build breaks after a code change
- On any unknown error during pipeline execution

## Attempt Tracking

Each attempt is recorded in `work/attempt-history.json`:

```json
{
  "subtask_id": "1.3",
  "timestamp": "2026-02-18T12:00:00Z",
  "approach": "Added null check before accessing user.id",
  "outcome": "failure",
  "error": "TypeError: cannot read property 'id' of undefined",
  "files_changed": ["src/api/handler.ts"],
  "keywords": ["null check", "user", "id", "guard"]
}
```

### Rules

- **Time window**: Only count attempts within the last 2 hours (older attempts are informational, not counted toward limits)
- **Max retries**: 5 per subtask before marking STUCK
- **History cap**: 50 attempts per subtask (oldest trimmed first)
- **Per-agent tracking**: In Agent Teams, each agent tracks its own attempts independently

### Recording an Attempt

After each subtask attempt:
1. Read `work/attempt-history.json` (create from template if missing)
2. Add attempt entry to the subtask's `attempts` array
3. Extract 3-5 keywords from the approach description
4. Increment `retry_count`
5. Run circular fix detection (see below)
6. Write updated file back

## Circular Fix Detection

Detects when you keep trying the same approach and failing.

### Algorithm

After each failed attempt, compare the current attempt's keywords against the previous 2 attempts:

1. Collect keyword sets from last 3 attempts (including current)
2. Compute pairwise Jaccard similarity: `|A intersection B| / |A union B|`
3. If ANY pair exceeds 30% similarity AND all 3 attempts failed -> circular fix detected

### On Circular Fix

1. **STOP** the current approach immediately
2. Set `circular_detected: true` in the subtask entry
3. List ALL approaches tried so far
4. Brainstorm a fundamentally different angle:
   - Different algorithm/data structure
   - Different API/library
   - Restructure the code instead of patching
   - Simplify requirements
5. If the alternative also triggers circular detection -> **escalate to human**

## Recovery Actions

| Failure Type | Action | Details |
|---|---|---|
| Build broken | rollback | `git reset` to last good commit from `good_commits` |
| Test failure (1-3) | retry | Reset subtask, try different approach |
| Test failure (4+) | escalate | Mark STUCK, notify human with full attempt history |
| Circular fix | skip + escalate | Mark STUCK, require human decision |
| Context exhausted | commit progress | Save completed work, document remaining in STATE.md |
| Unknown error (1-2) | retry | Standard retry, log error details |
| Unknown error (3+) | escalate | Mark STUCK, ask human |

### Rollback Procedure

1. Check `good_commits` array in attempt-history.json
2. Find the most recent good commit hash
3. `git stash` current changes (preserve work)
4. `git reset --soft {good_commit}` (keep changes staged, not lost)
5. Review what broke between good commit and current state
6. Try a different approach from the good commit baseline

## Good Commit Tracking

After each successful subtask completion:
1. Record the current commit hash in `good_commits` array: `{"hash": "abc1234", "subtask_id": "1.3", "timestamp": "..."}`
2. Keep max 20 good commits (trim oldest)
3. On build-breaking failure, rollback to the most recent good commit

## Prompt Injection for Retries

When retrying a subtask, prepend this context to the agent's prompt:

```markdown
## Previous Attempts (from Recovery Manager)

**Subtask**: {subtask_id} | **Retry**: {retry_count}/{max_retries}

| # | Approach | Outcome | Error |
|---|----------|---------|-------|
| 1 | {approach} | {outcome} | {error} |
| 2 | {approach} | {outcome} | {error} |

{IF circular_detected}
WARNING: Circular fix detected — approaches 1-{N} are too similar.
You MUST try a fundamentally different approach. Do NOT:
- Re-add the same fix with minor variations
- Try the same library/API with different parameters
- Patch around the same root cause

Instead: rethink the problem from scratch.
{/IF}
```

## Integration Points

### With systematic-debugging

The debugging skill escalates after 3+ failed hypotheses. At that point:
1. Record the failed debug session as an attempt
2. Run circular fix detection across debug attempts
3. If circular: recovery manager takes over, suggests alternative approach or escalates

### With qa-validation-loop

QA skill tracks same-issue recurrence (3+ iterations = BLOCKED). Connect:
1. Each QA iteration where the same issue persists = 1 attempt
2. If QA escalates with "same issue 3+ times", recovery manager marks subtask STUCK
3. Full attempt history is included in the escalation message to the human

### With Agent Teams

- Each agent maintains its own attempt tracking in the shared `work/attempt-history.json`
- Subtask IDs are namespaced per agent: `agent-1.subtask-3`
- Team lead checks attempt history before reassigning failed subtasks
- If an agent's subtask is STUCK, team lead can assign to a different agent with fresh context

### With pipeline (work/PIPELINE.md)

- On phase failure: record attempt, check if phase should be retried or skipped
- On STUCK: update PIPELINE.md phase status to BLOCKED
- On context exhaustion: commit, update PIPELINE.md with progress notes

## Example Flow

```
Subtask 1.3: "Fix user authentication endpoint"

Attempt 1: Added JWT validation middleware → FAIL (token expired error)
Attempt 2: Added token refresh logic → FAIL (token expired error persists)
Attempt 3: Extended token expiry time → FAIL (same error)

Recovery Manager:
  - Circular fix detected (all 3 attempts address token expiry with minor variations)
  - Jaccard similarity between keyword sets > 30%
  - Action: STOP. Suggest fundamentally different approach.
  - Suggestion: "Investigate whether the token is even reaching the middleware.
    Check request headers, proxy configuration, CORS settings."

Attempt 4: Checked request flow, found proxy stripping Auth header → SUCCESS
  - Record good commit
  - Clear circular_detected flag
```

## Template

Initial `work/attempt-history.json`: `.claude/shared/work-templates/attempt-history.json`
