---
name: context-monitor
version: 1.0.0
description: |
  Monitor context window usage and warn when approaching limits.
  Prevents quality degradation from context overflow.

  BACKGROUND SKILL - check periodically during long sessions.

  Do NOT use for: short tasks, single-file changes
---

# Context Monitor Skill

Monitor estimated context window usage and take action to prevent quality degradation.

## Overview

Claude's context window has finite capacity. As it fills:
- 0-30%: Peak quality
- 30-50%: Good quality
- 50-70%: Degradation begins
- 70%+: Low quality, risk of missed details

This skill estimates usage and recommends actions at thresholds.

## Context Usage Estimation (Heuristic)

Since there's no API for exact token measurement mid-session, we use heuristics:

### File Loading Estimates

| File Size | Estimated Impact |
|-----------|------------------|
| Small (<100 lines) | ~2% |
| Medium (100-500 lines) | ~5% |
| Large (>500 lines) | ~10% |
| Very Large (>1000 lines) | ~15-20% |

### Conversation Estimates

| Item | Estimated Impact |
|------|------------------|
| User message (short) | ~1% |
| User message (long/detailed) | ~2-3% |
| Assistant response (brief) | ~1-2% |
| Assistant response (detailed) | ~3-5% |
| Tool call + output | ~2-3% |
| Large tool output (>100 lines) | ~5-10% |

### Tracking Algorithm

```
ESTIMATE_USAGE():
  usage = 0

  # Count files read this session
  FOR file IN files_read:
    lines = count_lines(file)
    IF lines < 100:
      usage += 2
    ELIF lines < 500:
      usage += 5
    ELIF lines < 1000:
      usage += 10
    ELSE:
      usage += 15

  # Count conversation turns
  FOR turn IN conversation:
    IF turn.type == "user":
      usage += 1 if short else 2
    IF turn.type == "assistant":
      usage += 2 if brief else 4
    IF turn.type == "tool":
      usage += 3

  # Cap at 100%
  RETURN min(usage, 100)
```

## Threshold Actions

### At 40% - Soft Warning

```
SOFT_WARNING:
  message = """
  ⚠️ **Контекст: ~40%**

  Качество пока хорошее, но контекст заполняется.

  Рекомендации:
  - Завершите текущую задачу
  - Не загружайте новые большие файлы без необходимости
  """

  # Log but don't interrupt work
  LOG(message)
```

### At 50% - Warning

```
WARNING_50:
  message = """
  ⚠️ **Контекст: ~50%**

  Начинается деградация качества.

  Рекомендации:
  - Завершите текущую задачу как можно скорее
  - Используйте субагентов для новых задач
  - Рассмотрите новую сессию для следующей задачи
  """

  DISPLAY(message)
```

### At 70% - Block

```
BLOCK_70:
  message = """
  🛑 **Контекст: ~70% - КРИТИЧЕСКИЙ УРОВЕНЬ**

  Качество существенно снижено. Новые сложные задачи НЕ РЕКОМЕНДУЮТСЯ.

  **Варианты:**
  1. **Завершить сессию** - сохранить STATE.md, начать новую сессию
  2. **Использовать субагента** - делегировать задачу свежему агенту
  3. **Override** - продолжить на свой риск (качество не гарантировано)

  Что выбираете?
  """

  DISPLAY(message)
  WAIT_FOR_USER_DECISION()
```

## Subagent Dispatch Instructions

When context is high, delegate to fresh subagent:

```
DISPATCH_SUBAGENT(task):
  # Subagent gets fresh 200K context
  Task tool:
    subagent_type: general-purpose
    prompt: |
      You have a fresh context. Complete this task:

      {task_description}

      Context files to read:
      - {relevant_file_1}
      - {relevant_file_2}

      Return results when complete.
```

### What to Delegate

Good for subagent:
- Independent implementation tasks
- Code review of specific files
- Research/exploration
- Test writing

Keep in main context:
- Decision making requiring full history
- Coordination between tasks
- User interaction flow

## User Override Mechanism

User can override warnings:

```
OVERRIDE_RULES:
  # User says "продолжай" or "override" at 70%

  1. Log the override decision
  2. Continue with explicit warning:
     "Продолжаю по вашему запросу. Качество может быть снижено."
  3. Increase monitoring frequency
  4. Suggest subagent more aggressively for complex tasks
```

### Override Syntax

User can say:
- "продолжай несмотря на контекст"
- "override context warning"
- "ignore context limit"

## Integration

### With CLAUDE.md Rules

CLAUDE.md has context management rule:
```
Контекст > 50%: запустить субагента или разбить задачу
```

This skill implements that rule.

### With Orchestrator

Orchestrator can query context status:

```json
{
  "skill": "context-monitor",
  "query": "status",
  "response": {
    "estimated_usage": 55,
    "quality_level": "degrading",
    "recommendation": "use_subagent",
    "warning_shown": true
  }
}
```

### With Subagent-Driven-Development

When dispatching multiple subagents:
- Each subagent gets fresh context
- Main orchestrator tracks progress with minimal context
- Results are summarized, not loaded in full

## Monitoring Checkpoints

Check context at these points:

1. **After reading large files** - immediate check
2. **After completing a task** - before starting next
3. **After 10+ tool calls** - periodic check
4. **When user requests complex task** - pre-check

```
CHECK_CONTEXT():
  usage = ESTIMATE_USAGE()

  IF usage >= 70:
    BLOCK_70()
  ELIF usage >= 50:
    WARNING_50()
  ELIF usage >= 40:
    SOFT_WARNING()
  ELSE:
    # All good, continue
    pass
```

## Example Flow

```
[Session at ~45% context]

Agent: *reads large file (800 lines)*

Agent (internal): Context now ~55%, show warning

Agent:
  ⚠️ **Контекст: ~50%**

  Начинается деградация качества.
  Рекомендую завершить текущую задачу или использовать субагента.

User: Мне нужно ещё реализовать 3 задачи

Agent:
  Понял. Рекомендую использовать subagent-driven-development:
  - Каждая задача получит свежий контекст
  - Я буду координировать и ревьюить
  - Качество не пострадает

  Запустить subagent-driven-development?

User: да

Agent: *dispatches subagents for remaining tasks*
```

## Limitations

- Estimates are heuristic, not exact
- Different content types have different token densities
- Code vs prose have different ratios
- Actual impact varies by complexity

**Conservative approach:** When in doubt, estimate higher usage.
