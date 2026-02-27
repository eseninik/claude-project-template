# Architecture Decision Records

> INDEX всех архитектурных решений проекта. Агент консультируется перед изменением архитектуры.

---

## Active Decisions

| ID | Title | Date | Status | Impact |
|----|-------|------|--------|--------|
| 001 | AUTO-BEHAVIORS вместо команд | 2026-01-29 | Accepted | High - меняет workflow |
| 002 | Двухуровневая память (STATE + activeContext) | 2026-01-29 | Accepted | Medium |
| 004 | Plan execution enforcer | 2026-01-30 | Accepted | High - 100% enforcement |
| 006 | Two-Phase Agent Teams with Expert Panel | 2026-02-11 | Accepted | High - multi-perspective planning |

---

## By Category

### Methodology
- ADR-001: AUTO-BEHAVIORS вместо команд
- ADR-002: Двухуровневая память

### Enforcement
- ADR-004: Plan execution enforcer

### Agent Teams
- ADR-006: Two-Phase Agent Teams with Expert Panel

### Architecture
<!-- ADR затрагивающие общую архитектуру -->

### Database
<!-- ADR по базе данных -->

---

## Removed Decisions

| ID | Title | Removed | Reason |
|----|-------|---------|--------|
| 003 | Git hooks для автообновления | 2026-02-13 | Hooks removed — unreliable on Windows |
| 005 | Context Recovery Hook System | 2026-02-13 | Hooks removed |
| 007 | Pyramid Backup System | 2026-02-13 | Hooks removed |

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
