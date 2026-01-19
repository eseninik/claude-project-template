---
created: 2026-01-19
status: approved
type: feature
---

# User Spec: Улучшение Claude Project Template на основе Oh-My-OpenCode паттернов

## Что делаем

Улучшаем шаблон проекта Claude Code, добавляя автоматизацию оркестрации задач, управление контекстом, recovery-механизмы и режимы "autowork". Цель - убрать ручную церемонию выбора skills и автоматизировать рутинные операции.

## Зачем

Текущий шаблон требует ручного "Dynamic Skill Selection" ceremony перед каждым изменением кода. Это:
1. Замедляет работу (надо читать SKILLS_INDEX, выбирать, загружать)
2. Создает friction в workflow
3. Не использует возможности автоматического определения контекста

Oh-My-OpenCode показал что можно автоматизировать:
- Классификацию намерений (trivial/explicit/exploratory)
- Автоматический выбор skills
- Восстановление после ошибок через hooks
- Автопродолжение незавершенной работы

## Как должно работать

### Phase 1: Automatic Orchestration

1. **При старте сессии:**
   - Hook проверяет work/STATE.md
   - Если есть незавершенная работа → показывает сводку
   - Предлагает 5-секундный countdown для auto-resume
   - Пользователь может отменить набрав что-то

2. **При запросе от пользователя:**
   - Orchestrator автоматически классифицирует intent
   - Если trivial (вопрос, объяснение) → отвечает напрямую
   - Если explicit (четкая задача) → автоматически выбирает skills и запускает
   - Если exploratory → уточняет через context-capture

3. **При коде:**
   - Context Monitor отслеживает заполненность контекста
   - При 50% → warning
   - При 70% → BLOCK, предлагает запустить субагента

### Phase 2: Execution Improvements

4. **Режим "autowork":**
   - Пользователь пишет "autowork: добавь авторизацию"
   - Система автоматически:
     - Создает user-spec через интервью
     - Создает tech-spec
     - Генерирует tasks
     - Запускает subagent-driven-development
     - Проводит UAT
   - Минимум intervention от пользователя

5. **Background Task Tracking:**
   - При параллельных субагентах → записывает в work/background-tasks.json
   - Можно проверить статус
   - При завершении → уведомляет

### Phase 3: Recovery & Resilience

6. **Recovery Hooks:**
   - Ошибка Edit tool → retry с другим подходом
   - Timeout bash → notify и предложить alternatives
   - Test failure → auto-trigger systematic-debugging

7. **Self-Completion:**
   - Если TodoWrite показывает незавершенные todos
   - Продолжает автоматически до маркера <done>
   - Отслеживает iteration count (max 5 попыток)

## Критерии готовности

- [ ] Orchestrator agent создан и корректно классифицирует intents
- [ ] Session-start hook работает и предлагает auto-resume
- [ ] Context Monitor skill отслеживает и блокирует при 70%
- [ ] "autowork" keyword запускает полный pipeline
- [ ] Background tasks отслеживаются в JSON
- [ ] Recovery hooks перехватывают ошибки и пытаются восстановиться
- [ ] Self-completion автопродолжает незавершенные todos
- [ ] Все компоненты интегрированы в CLAUDE.md

## Что НЕ делаем

- MCP интеграция (optional, оставляем на потом)
- Полная замена manual skill selection (оставляем как fallback)
- Multi-model routing (doc-writer на haiku) - оставляем все на sonnet пока
