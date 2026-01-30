# ADR-004: Plan Execution Enforcer

**Date:** 2026-01-30
**Status:** Accepted

---

## Context

Боты загружали plan-execution-protocol.md но пропускали wave analysis и parallelization calculation. Пример: план jiggly-dancing-token.md с PP=50% был реализован последовательно вместо tasks/*.md + subagent-driven.

**Корневая причина:** Текущий BLOCKING RULE говорил "EXECUTE GATE FUNCTION from protocol", но не было структурного enforcement - агент мог пропустить без видимых последствий.

## Decision

Извлечь enforcement логику в отдельный guide (plan-execution-enforcer.md) с обязательным checkpoint box форматом. CLAUDE.md секция "Plan Detected" сокращена до 3 строк.

## Rationale

- Паттерн "Before Commit" уже доказал 100% enforcement через structured checklist
- Mandatory checkpoint box делает пропуск видимым
- Механический расчёт (формула PP) исключает intuitive reasoning
- Минимальный footprint в CLAUDE.md (-9 строк) при on-demand загрузке

## Alternatives Considered

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Expand CLAUDE.md | All in one place | +25 строк, loaded every session | Violates "минимум строк" |
| Merge into protocol | One guide | 400+ строк, mixes logic | Too long, mixed concerns |
| Pre-tool-call hook only | Automated | Black box, unproven | No visible compliance |

## Consequences

### Positive
- CLAUDE.md: -9 строк (180 → 171)
- 100% enforcement через structured output
- Visible compliance (checkpoint box easy to verify)

### Negative
- +300 tokens average (on-demand load for 20% of sessions)
- One more guide file to maintain

### Trade-offs
- Token cost acceptable - prevents wrong decisions that waste more tokens on rework

## Implementation Notes

**Files changed:**
- `CLAUDE.md` lines 112-123 → 3 lines
- `.claude/guides/plan-execution-enforcer.md` - new (302 lines)
- `.claude/shared/templates/new-project/` - synced

**Checkpoint format:** Bordered YAML box with self-verification checklist.

## For AI Agents

- Before changing: Verify checkpoint mechanism still works
- If proposing alternative: Must maintain 100% enforcement rate
- Related files: CLAUDE.md, plan-execution-protocol.md, dependency-analysis.md
