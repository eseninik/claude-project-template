# Proactive Agent Patterns (KAIROS)

> Guide for building proactive/daemon-style agents that act without user prompts.
> Source: "Inside the Agent" webinar by Bayram Annakov (Empatika Labs), April 2026.
> Loaded via: `cat .claude/guides/proactive-agent-patterns.md`

---

## 1. Core Concept

Traditional agents are REACTIVE: user types → agent responds (TAOR loop triggered by user).
Proactive agents are AUTONOMOUS: timer/event triggers → agent checks state → acts if needed → notifies user.

The key shift: the OBSERVE phase of the TAOR loop is triggered by a timer or external event, not by user input. The agent emulates a user prompt internally.

---

## 2. KAIROS Architecture (from Claude Code source)

Five components work together:

| Component | Purpose | Our Implementation |
|-----------|---------|-------------------|
| **Cron Scheduler** | Periodic state checks | `/schedule` command, CronCreate tool |
| **Channels** | Bi-directional user communication | Telegram MCP, Discord MCP |
| **Proactive `<tick>`** | State evaluation + decision | Heartbeat prompt template |
| **BriefTool** | Structured notification delivery | Telegram send_message with summary format |
| **Team Context** | In-process teammate awareness | Agent Teams, work/results-board.md |

---

## 3. Heartbeat Pattern

### Basic Structure
```
Every N minutes:
  1. CHECK state (cheap operations first):
     - New files in inbox? (fs check — free)
     - Git changes since last check? (git log — free)
     - Error logs? (grep — free)
     - API health? (curl — free)
  2. EVALUATE (only if state changed):
     - Is this change significant enough to act on?
     - Does it match any registered trigger patterns?
  3. ACT (only if evaluation says yes):
     - Execute the appropriate action
     - Use graduated approach: simple action first, LLM only if complex
  4. NOTIFY (only if action was taken):
     - Send summary to user via Channel
     - Brief format: what changed, what was done, what needs attention
```

### Graduated Cost Model
```
Layer 1: File system checks (free)     — run every tick
Layer 2: Git/process checks (free)     — run every tick
Layer 3: Pattern matching (free)       — run when Layer 1-2 detect change
Layer 4: LLM evaluation (costs tokens) — run when Layer 3 matches trigger
Layer 5: LLM action (costs tokens)     — run when Layer 4 decides to act
```

Most ticks should resolve at Layer 1-2 (no cost). Only significant changes reach Layer 4-5.

---

## 4. Implementation with Our Tools

### Using /schedule (Cron)
```
# Check for new PRs every 30 minutes
/schedule "Check GitHub PRs" every 30m "gh pr list --state open --json number,title,updatedAt | check for new ones since last run"

# Memory consolidation daily at 6am
/schedule "Memory consolidation" daily 6am "/consolidate"

# Monitor error logs every hour
/schedule "Error monitor" every 1h "tail -100 /var/log/app.log | grep ERROR"
```

### Using /loop (Recurring)
```
# Continuous monitoring during active development
/loop 5m "Check if any tests broke: uv run pytest --tb=line -q 2>&1 | tail -5"
```

### Using Telegram MCP for Notifications
```
# In heartbeat action, notify user
mcp__telegram-mcp-1__send_message(chat_id, "🔍 Heartbeat Report:\n- 2 new PRs found\n- Test suite: 45/45 passing\n- No errors in logs")
```

---

## 5. Practical Examples

### Example 1: Lead Monitor Bot
```
Heartbeat: every 30 min
State check: Query CRM API for new leads since last check
Trigger: new_leads.count > 0
Action: Classify leads, assign to pipeline
Notify: Telegram message with lead summary
Cost: ~0 tokens per empty check, ~500 tokens per lead batch
```

### Example 2: PR Review Assistant
```
Heartbeat: every 15 min during work hours
State check: gh pr list --state open (free)
Trigger: new PR or updated PR since last check
Action: Read PR diff, run basic review checklist
Notify: Post review comments on PR + Telegram summary
Cost: ~0 for no-change ticks, ~2K tokens per review
```

### Example 3: Error Sentinel
```
Heartbeat: every 5 min
State check: grep ERROR /var/log/app.log | tail -5 (free)
Trigger: new error lines since last check
Action: Classify error, check if known pattern in knowledge.md
Notify: Telegram alert with error context + suggested fix
Cost: ~0 for clean logs, ~500 tokens per error classification
```

---

## 6. Token Cost Considerations

| Frequency | Daily Cost (if 50% have changes) | Monthly |
|-----------|----------------------------------|---------|
| Every 5 min | ~144K tokens | ~4.3M |
| Every 15 min | ~48K tokens | ~1.4M |
| Every 30 min | ~24K tokens | ~720K |
| Every 1 hour | ~12K tokens | ~360K |

**Recommendations:**
- Use graduated checks — most ticks resolve at Layer 1-2 (zero cost)
- Higher frequency for critical monitors (errors, security)
- Lower frequency for informational checks (PRs, leads)
- Disable heartbeat during inactive hours (nights, weekends) unless monitoring prod

---

## 7. Integration with AutoDream

AutoDream (background memory consolidation) is a natural heartbeat task:
- Run via /schedule at end of day or session boundaries
- Reads past conversations, deduplicates knowledge, resolves conflicts
- Uses memory-consolidation skill for the heavy lifting
- Notifies user only if conflicts found that need human decision

---

## 8. Limitations

- No persistent daemon on Windows (sessions end when terminal closes)
- /schedule requires Claude Code to be running
- Token costs can accumulate with high-frequency heartbeats
- Complex actions may fail without user context
- Not suitable for time-critical alerts (use proper monitoring for that)
