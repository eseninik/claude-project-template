# Codex CLI Integration Guide

> Cross-model verification: Claude Code implements, Codex CLI validates.

## Обзор

Codex CLI используется как независимый верификатор кода, написанного Claude Code.
Два разных LLM-провайдера проверяют одну и ту же работу — это устраняет confirmation bias
(эффект эхо-камеры), когда модель проверяет собственный код.

---

## Prerequisites

- codex CLI установлен: `npm i -g @openai/codex` или `which codex`
- OpenAI API key или ChatGPT Plus/Pro подписка
- AGENTS.md в корне проекта (общий контекст для обоих инструментов)
- Review schema: `.codex/review-schema.json`

---

## Architecture

```
┌─────────────┐     implements      ┌──────────────┐
│ Claude Code  │ ──────────────────► │  Codebase    │
│ (primary)    │                     │              │
└─────────────┘                     └──────┬───────┘
                                           │
                                    reads (read-only)
                                           │
                                    ┌──────▼───────┐
                                    │  Codex CLI   │
                                    │ (verifier)   │
                                    └──────┬───────┘
                                           │
                                    structured JSON
                                           │
                                    ┌──────▼───────┐
                                    │ Claude Code  │
                                    │ (reads result)│
                                    └──────────────┘
```

**Ключевые принципы:**
- Claude Code = primary implementer (пишет код, запускает тесты, принимает решения)
- Codex CLI = independent verifier (read-only ревью, структурированный вывод, НИКОГДА не модифицирует код)
- Разделение предотвращает confirmation bias (echo chamber effect)
- Shell-based `codex exec` — production-ready; MCP server — experimental

---

## Integration Points

### 1. Stop Hook (Automatic)

Запускается автоматически, когда Claude завершает задачу. Настроен в `.claude/settings.json`.

- Скрипт: `.claude/hooks/codex-review.sh`
- Блокирует завершение при BLOCKER issues
- Включает risk classifier для пропуска тривиальных изменений
- Защита от бесконечных циклов через `stop_hook_active`

**Конфигурация в settings.json:**
```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/codex-review.sh"
          }
        ]
      }
    ]
  }
}
```

### 2. SKILL.md (Explicit)

Вызывается через skill `cross-model-review` когда нужна верификация Codex.

**Когда вызывать:**
- Перед PR
- После реализации фичи
- После QA validation loop
- Для security-critical кода

### 3. QA Validation Loop

Codex review запускается как дополнительный шаг в qa-validation-loop skill.

- После Claude QA reviewer, перед финальным вердиктом
- BLOCKER от Codex = CRITICAL QA issue
- Добавляет cross-model perspective к ревью

### 4. Agent Teams

При создании Agent Teams для реализации:
- Включить `cross-model-review` в Required Skills для QA-агентов
- High-risk задачи должны иметь отдельный шаг верификации Codex

---

## codex exec Commands

### Quick review (pre-commit)

```bash
codex exec "Review staged changes. Focus on correctness and security." \
  --model codex-mini-latest \
  --sandbox read-only \
  --ask-for-approval never
```

### Deep review (pre-merge)

```bash
codex exec "Review all changes on current branch vs main. Focus on security, logic errors, edge cases, test coverage. Use AGENTS.md rubric." \
  --model gpt-5.3-codex \
  --sandbox read-only \
  --ask-for-approval never \
  --output-schema .codex/review-schema.json \
  -o .codex/reviews/latest.json
```

### Targeted review (отдельный файл)

```bash
codex exec "Review file src/auth/login.py for security vulnerabilities, injection attacks, and token handling." \
  --model gpt-5.3-codex \
  --sandbox read-only
```

### Diff-based review (конкретные изменения)

```bash
git diff HEAD~1 | codex exec "Review this diff for bugs, security issues, and missing error handling." \
  --model codex-mini-latest \
  --sandbox read-only \
  --ask-for-approval never
```

---

## Model Selection

| Задача | Модель | Стоимость | Скорость |
|--------|--------|-----------|----------|
| Quick syntax/lint check | codex-mini-latest | Low | Fast |
| Standard code review | gpt-5.3-codex | Medium | Medium |
| Deep security/architecture | gpt-5.4 | High | Slow |
| Pre-commit hook | codex-mini-latest | Low | Fast |

**Правило выбора:** начинай с `codex-mini-latest`, переключайся на `gpt-5.3-codex` для
финального ревью или когда нужен глубокий анализ.

---

## Sandbox Modes

| Режим | Использование | Безопасность |
|-------|---------------|-------------|
| `read-only` | ВСЕГДА для верификации | Codex не может изменить файлы |
| `workspace-write` | Только для auto-fix сценариев | НЕ для review |
| `--dangerously-bypass-...` | НИКОГДА в production | Полный доступ к системе |

**Правило:** для cross-model verification ВСЕГДА используй `read-only`.

---

## Structured Output

Все Codex reviews используют `.codex/review-schema.json` для machine-parseable результатов.

### Парсинг результатов с jq

```bash
# Проверить наличие блокеров
jq '.summary.has_blockers' .codex/reviews/latest.json

# Список всех findings
jq '.findings[] | "\(.severity): \(.title) [\(.location.path):\(.location.line_start)]"' \
  .codex/reviews/latest.json

# Только BLOCKER findings
jq '[.findings[] | select(.severity=="BLOCKER")]' .codex/reviews/latest.json

# Вердикт
jq '.verdict' .codex/reviews/latest.json

# Количество issues по severity
jq '[.findings[] | .severity] | group_by(.) | map({(.[0]): length}) | add' \
  .codex/reviews/latest.json
```

### Формат результата

```json
{
  "summary": {
    "has_blockers": false,
    "has_important": true,
    "files_touched": ["src/auth.py", "src/api.py"],
    "suggested_next_actions": ["Add input validation for email field"]
  },
  "findings": [
    {
      "severity": "IMPORTANT",
      "title": "Missing input validation",
      "explanation": "User email is passed directly to query without sanitization",
      "location": { "path": "src/auth.py", "line_start": 42, "line_end": 45 },
      "recommendation": "Add email format validation before database query"
    }
  ],
  "verdict": {
    "status": "pass",
    "confidence": 0.85,
    "rationale": "No critical issues. One important finding needs attention."
  }
}
```

---

## Conflict Resolution (Claude vs Codex disagree)

| Ситуация | Действие |
|----------|----------|
| Reproducible issue (failing tests, obvious bug) | Blocker regardless of who found it |
| Style/approach disagreement | Defer to AGENTS.md/CLAUDE.md rules |
| Security disagreement | Escalate: spawn separate security-auditor agent |
| After 2 rounds of disagreement | BLOCKED, escalate to human |
| Lint/format disputes | Let deterministic tools decide (prettier, eslint, black) |

**Принцип:** конкретные, воспроизводимые проблемы всегда приоритетнее субъективных мнений.

---

## Bypass Criteria

### Когда ПРОПУСКАТЬ Codex review

Skip когда ВСЕ условия истинны:
- Изменения < 50 строк
- Только docs/comments/CSS/config файлы
- Существующие тесты покрывают изменённый код и проходят
- Нет auth/payments/migrations/security-critical кода

### Когда ВСЕГДА запускать Codex review

- Auth, payments, cryptography код изменён
- Database migrations добавлены
- Public API contracts изменены
- External API integrations добавлены/изменены
- 5+ файлов изменено across modules
- Новый endpoint добавлен
- Middleware/interceptors изменены

---

## Troubleshooting

| Проблема | Решение |
|----------|---------|
| `codex: command not found` | `npm i -g @openai/codex` |
| Authentication error | Set `OPENAI_API_KEY` или `codex auth` |
| Timeout on large diffs | Use `--model codex-mini-latest` для скорости |
| Schema validation fails | Проверить `.codex/review-schema.json` синтаксис |
| Infinite loop в Stop hook | Проверить `stop_hook_active` guard в скрипте |
| Rate limit hit | Подождать 5 минут или использовать lighter model |
| Empty review output | Убедиться что есть uncommitted changes |
| JSON parse error | Проверить что codex вернул валидный JSON |

---

## Cost Optimization

- Используй `codex-mini-latest` для частых проверок (pre-commit, PostToolUse)
- Резервируй `gpt-5.3-codex` для финального review gate
- ChatGPT Plus ($20/mo) включает Codex CLI usage
- Skip review для тривиальных изменений (risk classifier в hook)
- Batch reviews: лучше один deep review после фичи, чем 10 quick reviews на каждый файл

---

## Related Files

| Файл | Назначение |
|------|------------|
| `.codex/review-schema.json` | Structured output schema |
| `.claude/hooks/codex-review.sh` | Stop hook script |
| `.claude/skills/cross-model-review/SKILL.md` | Explicit invocation skill |
| `AGENTS.md` | Shared project context (оба инструмента читают) |
| `.codex/reviews/` | Directory с результатами ревью |
| `.codex/reviews/latest.json` | Последний результат ревью |
