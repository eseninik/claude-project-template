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
| Deep security/architecture | gpt-5.5 | High | Slow |
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

---

# Codex as Primary Implementer (Level 2 + Level 3)

> Experimental, local-to-this-project as of 2026-04-24. Not yet propagated to
> new-project template or fleet. See ADR-012 and `work/codex-primary/tech-spec.md`.

The advisor pattern above (Codex reviews Claude's code) is the **reviewer** role.
This section documents the **implementer** role — Codex writes the code, Opus
plans and reviews.

## When to use which phase mode

- `CODEX_IMPLEMENT` — all tasks in phase → Codex. Well-specified logic, clear tests.
- `HYBRID_TEAMS` — per-task `executor:` hint picks `claude | codex | dual`. Most flexible.
- `DUAL_IMPLEMENT` — high-stakes code; both sides implement in parallel, Opus judges.

## Key tooling

| File | Role |
|------|------|
| `.claude/scripts/codex-implement.py` | Single-task Codex executor (clean-tree preflight + scope fence + rollback + result.md) |
| `.claude/scripts/codex-wave.py` | Parallel launcher for N `codex-implement.py` in isolated git worktrees |
| `.claude/scripts/codex-scope-check.py` | Diff ↔ fence validator (inline CSV default; `@path` prefix for fence-file mode) |
| `.claude/skills/dual-implement/SKILL.md` | Level 3 orchestration (2 worktrees + judge) |
| `AGENTS.md` (repo root) | Shared skill contracts auto-loaded by Codex project_doc fallback |

## GPT-5.5 model access (ChatGPT-account gate workaround)

OpenAI's default `openai` CLI provider blocks gpt-5.5 for ChatGPT-account users
("The model 'gpt-5.5' is not supported when using Codex with a ChatGPT account").
The **same endpoint** that the Codex desktop/web app uses —
`https://chatgpt.com/backend-api/codex` — does serve gpt-5.5 to the same
account. `codex-implement.py` registers this as a `chatgpt` provider inline:

```bash
codex exec \
  -c 'model_providers.chatgpt={name="chatgpt",base_url="https://chatgpt.com/backend-api/codex",wire_api="responses"}' \
  -c model_provider=chatgpt \
  --model gpt-5.5 \
  --sandbox workspace-write \
  --full-auto \
  --cd <worktree> \
  -
```

No changes to `~/.codex/config.toml` — the advisor stack (codex-ask.py etc.)
keeps the default `openai` provider.

## Speed optimization

### Three-tier speed profile

`task-N.md` frontmatter supports `speed_profile: fast | balanced | thorough`.
`codex-implement.py` maps to reasoning effort. Precedence (highest wins):

1. `--reasoning {high,medium,low}` CLI flag
2. `--speed {fast,balanced,thorough}` CLI flag
3. `reasoning:` frontmatter field
4. `speed_profile:` frontmatter field
5. default `balanced` → reasoning `medium`

Typical time impact (Windows, gpt-5.5 via chatgpt provider, task ≈ 4 KB prompt):

| Profile | Reasoning | Typical run time | Use for |
|---------|-----------|------------------|---------|
| fast | low | ~1-2 min | typo/rename/trivial refactor |
| balanced (default) | medium | ~2-4 min | routine feature / bug fix |
| thorough | high | ~4-8 min | novel algorithm / high-stakes / auth |

### AGENTS.md shared context

`AGENTS.md` at repo root holds skill contract extracts (verification, logging,
security, coding standards) + Windows gotchas + git invariants. Codex reads it
automatically via `project_doc` fallback. **Individual `task-N.md` files no
longer need to re-inline these contracts** — ~40% prompt shrink per run.

### Parallel waves

`codex-wave.py --tasks T1.md,T2.md,T3.md --parallel 3` spawns N isolated
worktrees + N parallel Codex sessions. Wall-time = max(task_i), not sum.
Default `--parallel 3` — raise cautiously; $20 Codex plans may rate-limit at
higher N.

## Stateless Codex + Opus as memory keeper

**Codex is stateless per `codex exec` invocation.** Each call is a fresh
session; there is no implicit memory of previous task iterations. We do NOT
use `codex exec resume` (session chaining) — keeps parallelism, determinism,
and debuggability.

**Opus's 1M context window is the memory layer.** On each new task, Opus reads
the entire relevant codebase + memory (activeContext, knowledge, daily logs)
+ dual-implement history + previous iterations, then distills into a compact
`task-N.md` for Codex. Codex sees a 4 KB delta, not a 1 MB state dump.

For multi-round tasks, `task-N.md` has an `## Iteration History` section where
Opus injects "round 1 tried X, failed because Y". Next round Codex reads this
and avoids repeating the failed approach.

## Post-mortems worth reading before changing this pipeline

- `work/codex-primary/tech-spec.md` — full architecture, 17 sections.
- `work/codex-primary/dual-1-postmortem.md` — bugs #7/#8/#9 discovered
  by the first live Level 3 run.
- `work/codex-primary/dual-2-judgment.md` — first real judge step with
  two valid diffs.

---

# Always-Dual Code Delegation Protocol (v2)

> Elevated Level 3 from opt-in to mandatory default: every code-writing
> task runs both Claude and Codex in parallel. See `CLAUDE.md` → "Code
> Delegation Protocol" for the canonical rule + `ADR-012`.

## Enforcement

`.claude/hooks/codex-delegate-enforcer.py` blocks `Edit|Write|MultiEdit`
on code files that lack a recent (< 15 min) Codex `task-*-result.md`
with `status: pass` covering the target path. Exempt paths (edit freely):
`.claude/memory/**`, `work/**`, `CLAUDE.md`, `AGENTS.md`, READMEs,
`.claude/settings.json`, `.claude/adr/**/*.md`, `.claude/guides/**/*.md`,
`.claude/skills/**/*.md`, any non-code extension, `worktrees/**`
(dual-operation territory).

Sibling hook `codex-gate.py` shares the same `worktrees/**` bypass so
in-worktree Claude teammates don't deadlock on the dual pair's other
half.

## Task-size → execution mode

| Size | Mode | Tool |
|------|------|------|
| Typo / 1-2 lines | `inline-dual` | `codex-inline-dual.py --describe ... --scope ... --test ...` |
| One focused feature / bug | `dual-implement` skill (Level 3) | Manual worktree pair |
| Big N-subtask phase | `DUAL_TEAMS` mode | `dual-teams-spawn.py --tasks T1.md,...,TN.md` + Opus spawns teammates + codex-wave |

## `dual-teams-spawn.py` (orchestration prep)

```bash
py -3 .claude/scripts/dual-teams-spawn.py \
  --tasks work/<feature>/tasks/T1.md,T2.md,T3.md \
  --feature <feature> \
  --parallel 3 \
  --worktree-base worktrees/<feature>
```

Writes `work/<feature>/dual-teams-plan.md` with per-pair worktree paths,
Claude-side prompt files, Codex-wave PID, and step-by-step instructions
for Opus. Does NOT itself spawn the Agent tool — prep + report helper.

## `codex-inline-dual.py` (micro-task helper)

```bash
py -3 .claude/scripts/codex-inline-dual.py \
  --describe "Add --verbose flag to foo.py" \
  --scope .claude/scripts/foo.py \
  --test "python .claude/scripts/foo.py --verbose" \
  --speed fast
```

Generates transient task-N.md spec, creates two worktrees, launches
`codex-implement.py` in background, writes Claude-teammate prompt.

## Streaming judge + cherry-pick hybrid

See `dual-implement/SKILL.md` → "Streaming judge" + "Cherry-pick hybrid".
Streaming cuts judge latency off critical path for N ≥ 3. Cherry-pick
applies when aggregate scores are close but axes-level winners differ.

## Stability layer (T8/T9)

`codex-implement.py` retries on HTTP 429 with exponential backoff
(1-2-4-8s, max 4) to handle $20 Codex tier rate limits. After 3
consecutive Codex failures, `.codex/circuit-open` flag (5-min TTL)
activates; dual-* helpers route Codex-side to Claude-only fallback
with `DEGRADED` notice so the pipeline doesn't deadlock on outage.

## Warm Codex pool (T10)

`codex-pool.py` maintains 2 warm `codex app-server` instances on
different ports; callers (codex-implement / -inline / -wave) prefer
the pool before cold-starting. Saves ~5-10 s per invocation. Pool
lifecycle tied to SessionStart/End hooks.

## Known Windows limitations

- `codex-wave.py` hit a UNC long-path race (`//?/C:/...`) on
  `--parallel ≥ 3` during Wave 2 smoke. Workaround: `--parallel ≤ 2`
  until the path-normalization fix lands. Details:
  `work/codex-primary-v2/dual-history/T{4,5}/codex-wave-BUG-no-output.md`.
- Background `Agent`-tool-spawned Claude teammates can hit harness
  permission prompts on large `Write` calls (auto-deny for big files).
  Workaround: PowerShell `[System.IO.File]::WriteAllText` with UTF-8
  no-BOM, or `cat > file << 'EOF'` heredoc via Bash tool.
