# Architecture Decision Records

> INDEX всех архитектурных решений проекта. Агент консультируется перед изменением архитектуры.

---

## Active Decisions

| ID | Title | Date | Status | Impact |
|----|-------|------|--------|--------|
| 001 | AUTO-BEHAVIORS вместо команд | 2026-01-29 | Accepted | High - меняет workflow |
| 002 | Двухуровневая память (STATE + activeContext) | 2026-01-29 | Accepted | Medium |
| 003 | Git hooks для автообновления | 2026-01-29 | Accepted | Medium |
| 004 | Plan execution enforcer | 2026-01-30 | Accepted | High - 100% enforcement |

---

## By Category

### Methodology
- ADR-001: AUTO-BEHAVIORS вместо команд
- ADR-002: Двухуровневая память

### Automation
- ADR-003: Git hooks для автообновления

### Enforcement
- ADR-004: Plan execution enforcer

### Architecture
<!-- ADR затрагивающие общую архитектуру -->

### Database
<!-- ADR по базе данных -->

---

## Superseded Decisions

| ID | Title | Superseded By | Date |
|----|-------|---------------|------|
| | | | |

---

## How to Use

**Агент автоматически:**
1. Читает этот INDEX перед архитектурными изменениями
2. Создаёт новый ADR при значимом решении
3. Обновляет INDEX при создании/изменении ADR

**Когда создавать ADR:**
- Выбор технологии/библиотеки
- Изменение структуры данных
- Новый паттерн интеграции
- Решение с долгосрочными последствиями
