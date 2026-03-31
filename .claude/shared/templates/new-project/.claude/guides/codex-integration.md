# Codex CLI Integration Guide

> Cross-model verification: Claude Code implements, Codex CLI validates.

## Обзор

Codex CLI используется как независимый верификатор кода, написанного Claude Code.
Два разных LLM-провайдера проверяют одну и ту же работу — это устраняет confirmation bias
(эффект эхо-камеры), когда модель проверяет собственный код.

---

## Prerequisites

- Codex CLI v0.117.0+ (Rust-based): `npm i -g @openai/codex` или `which codex`
- OpenAI API key или ChatGPT Plus/Pro подписка
- Config: `~/.codex/config.toml` (model, sandbox defaults)
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

## Dual-Mode Architecture

Codex работает в двух режимах: параллельный advisor на каждый запрос + явный deep review по запросу.

```
User Request → UserPromptSubmit hook
                    ↓ (background, non-blocking)
              codex-parallel.py → Codex gpt-5.4 → .codex/reviews/parallel-opinion.md
                                                        ↓
Claude Code processes request ──────────────────→ reads opinion → combined response

For high-risk code (explicit):
Claude → cross-model-review skill → codex exec → structured JSON review
```

**Два режима работы (дополняют друг друга):**

| Режим | Когда | Как |
|-------|-------|-----|
| **Mode 1: Parallel Advisor** (automatic) | На КАЖДЫЙ запрос пользователя | UserPromptSubmit hook → `codex-parallel.py` в фоне, пишет opinion в `.codex/reviews/parallel-opinion.md`, Claude читает перед ответом |
| **Mode 2: Deep Code Review** (explicit) | Для high-risk кода, перед PR | Claude вызывает `cross-model-review` skill → `codex exec` с `--output-schema` → structured JSON |

- **Mode 1 (Parallel Advisor)** = always-on background advisor — запускается на каждый запрос, не блокирует UI
- **Mode 2 (Deep Code Review)** = on-demand deep analysis — явный запуск для security-critical, migrations, API changes
- **Stop hook: REMOVED** — блокировал UI на 60-90с, заменён на UserPromptSubmit (параллельный, non-blocking)

---

## Integration Points

### 1. Parallel Advisor — UserPromptSubmit Hook (Automatic)

Запускается автоматически на КАЖДЫЙ запрос пользователя в фоновом режиме. Настроен в `.claude/settings.json`.

- Скрипт: `.claude/hooks/codex-parallel.py`
- Работает параллельно с Claude Code — не блокирует UI
- Пишет opinion в `.codex/reviews/parallel-opinion.md`
- Claude читает opinion перед формированием ответа
- Always active — no manual invocation needed

**Конфигурация в settings.json:**
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "py -3 .claude/hooks/codex-parallel.py"
          }
        ]
      }
    ]
  }
}
```

> **Note:** Stop hook was removed — it blocked the UI for 60-90 seconds waiting for Codex response.
> UserPromptSubmit runs in background, providing non-blocking parallel advice.

### 2. Deep Code Review — SKILL.md (Explicit)

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

### Review uncommitted changes (pre-commit)

```bash
codex exec review --uncommitted \
  -m gpt-5.4 \
  --sandbox read-only \
  --ephemeral
```

### Review against base branch (pre-merge)

```bash
codex exec review --base main \
  -m gpt-5.4 \
  --sandbox read-only \
  --output-schema .codex/review-schema.json \
  -o .codex/reviews/latest.json
```

### Review specific commit

```bash
codex exec review --commit HEAD \
  -m gpt-5.4 \
  --sandbox read-only
```

### Custom targeted review (specific file/concern)

```bash
codex exec "Review file src/auth/login.py for security vulnerabilities, injection attacks, and token handling." \
  -m gpt-5.4 \
  --sandbox read-only \
  --ephemeral
```

### Custom diff-based review

```bash
git diff HEAD~1 | codex exec "Review this diff for bugs, security issues, and missing error handling." \
  -m gpt-5.4 \
  --sandbox read-only \
  --ephemeral
```

### Structured output with JSON schema

```bash
codex exec review --uncommitted \
  -m gpt-5.4 \
  --sandbox read-only \
  --output-schema .codex/review-schema.json \
  -o .codex/reviews/latest.json \
  --json
```

---

## CLI Reference (v0.117.0)

| Flag | Description |
|------|-------------|
| `-m gpt-5.4` | Model selection |
| `--sandbox read-only` | Read-only filesystem access |
| `--full-auto` | Low-friction sandboxed execution |
| `--ephemeral` | Don't persist session |
| `-o FILE` | Output last message to file |
| `--output-schema FILE` | JSON schema for structured output |
| `--json` | JSONL event stream to stdout |
| `-c key=value` | Inline config override |
| `-C DIR` | Change working directory |
| `--skip-git-repo-check` | Allow outside git repo |

---

## Model Selection

| Задача | Модель | Скорость |
|--------|--------|----------|
| All reviews (default) | gpt-5.4 | Standard |
| Quick syntax/lint check | gpt-5.4-mini | Fast |
| Dedicated coding tasks | gpt-5.3-codex | Medium |

**Правило:** используй `gpt-5.4` для всего. Переключайся на `gpt-5.4-mini` только
когда нужна скорость и задача тривиальна.

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
- 5+ файлов изменено across modules
- Новый endpoint добавлен

---

## Troubleshooting

| Проблема | Решение |
|----------|---------|
| `codex: command not found` | `npm i -g @openai/codex` |
| Authentication error | Set `OPENAI_API_KEY` или `codex auth` |
| Timeout on large diffs | Use `-m gpt-5.4-mini` для скорости |
| Schema validation fails | Проверить `.codex/review-schema.json` синтаксис |
| Parallel opinion not appearing | Проверить `codex-parallel.py` и UserPromptSubmit hook в settings.json |
| Empty review output | Убедиться что есть uncommitted changes |

---

## Related Files

| Файл | Назначение |
|------|------------|
| `.codex/review-schema.json` | Structured output schema |
| `~/.codex/config.toml` | Codex CLI configuration |
| `.claude/hooks/codex-parallel.py` | UserPromptSubmit hook — parallel advisor (Python) |
| `.claude/hooks/codex-review.py` | Deep review script — used by cross-model-review skill (Python) |
| `.claude/skills/cross-model-review/SKILL.md` | Explicit invocation skill |
| `AGENTS.md` | Shared project context (оба инструмента читают) |
| `.codex/reviews/latest.json` | Последний результат ревью |
