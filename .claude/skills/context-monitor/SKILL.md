---
name: context-monitor
description: |
  Estimates context window usage via heuristics and warns at thresholds (40%, 50%, 70%).
  Recommends subagent delegation or session end when context is high.
  Activate when a session is long-running, many files have been read, or context feels bloated.
  Does NOT measure exact token counts. Does NOT manage memory or compaction.
---

# Context Monitor

## Thresholds

| Usage | Action |
|-------|--------|
| 0-40% | Continue normally |
| 40-50% | Internal warning. Avoid loading large files |
| 50-70% | Warn user: "Context ~X%. Finish current task, use subagents for new tasks" |
| 70%+ | Block new complex tasks. Offer: 1) End session 2) Delegate to subagent 3) Override |

## Estimation Heuristics

| Item | Impact |
|------|--------|
| File <100 lines | ~2% |
| File 100-500 lines | ~5% |
| File 500-1000 lines | ~10% |
| File >1000 lines | ~15-20% |
| Short message/response | ~1-2% |
| Detailed response | ~3-5% |
| Tool call + output | ~2-3% |
| Large tool output (>100 lines) | ~5-10% |
| System prompt + skills baseline | ~10-15% |

## Check At
1. After reading large files (>500 lines)
2. After completing a task, before starting next
3. After 10+ tool calls
4. When user requests complex new task

## Subagent Delegation (when context high)
- Delegate: independent implementation, code review, research, test writing
- Keep in main: decisions requiring full history, coordination, user interaction

## User Override at 70%
1. Log override
2. Warn: "Continuing per request. Quality may be reduced."
3. Suggest subagent more aggressively for subsequent tasks

## Hard Rules
- Estimates are heuristic -- when uncertain, estimate higher
- Code is denser than prose (more tokens per line)
