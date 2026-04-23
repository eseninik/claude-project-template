# Spec: Watchdog Дnushnost Fix

**Problem:** Codex Watchdog на Stop-хуке ловит ложноположительные аномалии, вызывает 10+ итерационные цепочки пробуждений. Пользователь жалуется что "после autoresearch стало душно". Корень НЕ в autoresearch — корень в: (a) нет state-памяти между wake'ами, (b) слишком широкие триггеры, (c) единственный канал реакции = блокировка Claude.

**Non-goals:**
- Не удаляем Codex Watchdog — он ценен, ловит галлюцинации.
- Не трогаем `codex-broker.py` parallel opinion — работает нормально.
- Не трогаем `codex-gate.py` (PreToolUse + TaskCreated) — **это by-design parallel Codex consultation**, не часть проблемы. Edit-cooldown 5min/5edit остаётся как есть; пользователь подтвердил что это норма.
- Не делаем gate consolidation (Layer 4) — это перф-оптимизация, не душнота.
- Не делаем fleet-sync на 13 ботов — отдельное действие с подтверждением.

**Scope clarification (revised 2026-04-23 09:35 по фидбеку user):** Fix касается ТОЛЬКО `codex-watchdog.py` (Stop hook, asyncRewake). Task-class detection и slash-commands управляют ТОЛЬКО watchdog, `codex-gate` остаётся нетронутым.

**Invariants:**
- Watchdog продолжает анализировать каждый Stop (покрытие не падает).
- HALT-уровень (exit 2, wake Claude) сохраняется для реальных галлюцинаций/лжи.
- Все hooks обратно совместимы по JSON stdin/stdout контракту.

---

## Layer 1 — Severity Triage

### Severity Enum

Codex возвращает один из 3 вердиктов:

| Severity | Channel | Claude Action | When |
|---|---|---|---|
| **HALT** | `exit 2 + stderr reason` | Claude просыпается и должен исправить | Доказанная ложь: "тесты прошли" когда не прошли, "файл создан" когда нет, "готово" с known bugs |
| **WARN** | `exit 0 + JSON systemMessage` | Показать пользователю, Claude продолжает | Нюансы, сомнительные решения, drive-by refactoring, пропуск тестов |
| **OBSERVE** | `exit 0 + append to .codex/watchdog-trail.jsonl` | Молчаливый лог | Обычные ответы, ничего критичного |

### Distribution target (approximate)
- HALT: ~3-5% от Stop-событий
- WARN: ~10-20%
- OBSERVE: ~75-85%

### Codex Prompt Contract
Codex получает response + task_class + инструкцию вернуть **строгий JSON**:
```json
{"severity": "HALT|WARN|OBSERVE", "reason": "brief", "evidence": "quote from response"}
```
Если Codex вернул не-JSON или невалидный severity → fallback на OBSERVE (never block on parse failure — это само по себе источник душноты).

### Confidence gating
Чтобы HALT не срабатывал на спорных кейсах: Codex-промпт требует `confidence: 0.0-1.0`. HALT срабатывает **только** если severity=HALT **и** confidence >= 0.85. Всё ниже становится WARN.

---

## Layer 2 — State Memory

### File: `.codex/watchdog-state.json`

Схема:
```json
{
  "session_id": "sha256 of first-prompt + timestamp",
  "recent_wakes": [
    {"ts": 1234567890, "sig_hash": "abc123", "anomaly_text_hash": "def456", "severity": "HALT"}
  ],
  "topic_halt_counts": {"anomaly_text_hash": 2},
  "cooldown_until_stop_event": 0
}
```

### Dedup rules (все проверяются перед отправкой в Codex)

1. **Signature dedup**: `sig_hash = sha256(response[-2000:])` — если тот же hash был в `recent_wakes` последние 3 события → **skip entirely** (Codex не вызываем, сразу exit 0). Причина: Claude может переотправить похожий ответ; повторно пробуждать бессмысленно.

2. **Anomaly-topic dedup**: если Codex вернул анoмалию с текстом близким к предыдущему (нормализованный text_hash), и `topic_halt_counts[hash] >= 2` → **downgrade HALT → WARN**. Claude уже услышал про это 2 раза.

3. **Post-HALT cooldown**: после любого HALT `cooldown_until_stop_event = current + 3`. Следующие 3 Stop работают в режиме **OBSERVE only** — Codex всё ещё анализирует, но максимум WARN. Причина: дать Claude зону реакции без повторного прерывания.

### Cleanup
`recent_wakes` truncated до последних 10 записей. `topic_halt_counts` сбрасывается при новой session_id.

---

## Layer 3 — Task-Class Detection

### Hook: `session-task-class.py`

Fires on **SessionStart** и **UserPromptSubmit**.

Анализирует первое (SessionStart) или текущее (UserPromptSubmit) сообщение пользователя, классифицирует, пишет в файл `.codex/task-class` (не env var — env plies между процессами не работает надёжно на Windows).

Остальные хуки читают `.codex/task-class` синхронно (0ms).

### Classifier rules (deterministic, regex + keyword)

Order: проверяется сверху вниз, первое совпадение выигрывает.

| Class | Strictness | Rule (case-insensitive, OR) | Examples |
|---|---|---|---|
| `deploy` | max | `deploy`, `deployment`, `в прод`, `to prod`, `production`, `ssh contabo`, `systemctl`, `release` | "задеплой на прод" |
| `refactor` | max-1 | `refactor`, `рефактор`, `migrate`, `rewrite`, `переписать` | "отрефактори модуль" |
| `feature` | medium | `добавь`, `implement`, `build`, `создай`, `feature`, `новый` + (file/module word) | "добавь endpoint" |
| `bugfix` | low | `fix`, `bug`, `баг`, `починить`, `исправь`, `ошибк` | "почини баг с логином" |
| `typo` | very-low | `rename`, `typo`, `переименуй`, `typo`, `опечатк` | "переименуй переменную" |
| `chat` | off | короткое (< 80 chars), нет имён файлов/модулей, вопросительное или бытовое | "а что по задаче X?" |
| `feature` (fallback) | medium | если ничего не подошло → default | — |

### Per-class hook behavior matrix (watchdog only)

| Hook | chat | typo | bugfix | feature | refactor | deploy |
|---|---|---|---|---|---|---|
| `codex-watchdog` | **skip** | OBSERVE only | HALT only | HALT+WARN | all 3 | all 3 (stricter) |
| `codex-gate.PreToolUse` | unchanged (5min/5edit) | unchanged | unchanged | unchanged | unchanged | unchanged |
| `codex-gate.TaskCreated` | unchanged (on) | unchanged | unchanged | unchanged | unchanged | unchanged |
| `task-completed-gate` | unchanged (on) | unchanged | unchanged | unchanged | unchanged | unchanged |

`codex-gate` остаётся как есть — это by-design parallel Codex consultation, не часть проблемы душноты. Task-class влияет только на **watchdog**.

### User override (Layer 5)
`/watchdog` command может форсировать class независимо от классификатора. Override сохраняется в `.codex/task-class-override` и имеет приоритет.

---

## Layer 5 — Slash Commands

### `/watchdog` subcommands

| Command | Effect |
|---|---|
| `/watchdog status` | Печатает current task-class, strictness, cooldown-state, последние 3 wake-записи |
| `/watchdog strict` | Force max strictness (deploy-level) на 30 минут |
| `/watchdog normal` | Revert to auto-classifier |
| `/watchdog off 30m` | Полностью выключает watchdog на N минут (gate остаётся активным). Syntax: `off [duration]`, duration defaults to 30m |
| `/watchdog class <name>` | Force-override task-class (chat/typo/bugfix/feature/refactor/deploy) |

Implementation: slash-command = markdown file в `.claude/commands/watchdog.md`, исполняется как Claude Code slash. Команда пишет в `.codex/task-class-override` с expiry timestamp. Хуки читают override в первую очередь.

---

## Acceptance Criteria (IMMUTABLE — Evaluation Firewall)

**AC1: Severity triage работает.**
Дан Codex вердикт JSON с severity=WARN — watchdog выходит с exit 0, пишет systemMessage, Claude НЕ пробуждается. Verifiable: unit test stubs Codex response, проверяет exit code + stdout JSON.

**AC2: HALT сохраняется для реальных галлюцинаций.**
Дан Codex вердикт JSON с severity=HALT и confidence=0.9 — watchdog выходит с exit 2. Verifiable: unit test.

**AC3: State memory предотвращает петли.**
Одинаковая сигнатура ответа 2 раза подряд → второй вызов watchdog НЕ идёт в Codex (skip). Verifiable: unit test, проверить что вторая invocation отрабатывает за < 100ms (нет WS-вызова).

**AC4: Post-HALT cooldown.**
После HALT следующие 3 Stop-события не могут выдать HALT (макс WARN). Verifiable: unit test.

**AC5: Task-class detector работает.**
Дан первый prompt "задеплой на прод" → `.codex/task-class` = `deploy`. Дан "привет что-то по боту?" → `chat`. Verifiable: unit test с 12+ prompt-сэмплами (2 per class).

**AC6: FP replay — live кейс из сессии не срабатывает.**
Записанный в `work/watchdog-fix/fp-replay.md` сегодняшний false-positive ("Linear MCP works with caveat") при task_class=`chat` → exit 0 OBSERVE, не HALT. Verifiable: unit test с сохранённой копией моего ответа.

**AC7: Slash commands функционируют.**
`/watchdog off 10m` → `.codex/task-class-override` содержит `{"class":"off","until":<ts+600>}` → watchdog/gate проверяют и skip. Verifiable: integration test или ручной smoke.

---

## Test Plan

Unit tests в `.claude/hooks/test_watchdog_fix.py`:
- 4 теста на severity triage (каждый severity + parse failure)
- 3 теста на state memory (dedup, topic-count, cooldown)
- 12 тестов на task-class classifier (2 per class)
- 1 integration test на FP replay из session
- 1 тест на task-class override через `.codex/task-class-override`

Total: ~21 tests. Должны все passing перед merge.

---

## Rollback Plan

Каждая фаза = checkpoint commit. Если после IMPL любая фаза ломает Claude Code session: `git reset --hard pipeline-checkpoint-<last-good>`. `.codex/watchdog-state.json` файл может быть удалён безопасно — watchdog его re-создаст.

---

## Sign-off

SPEC frozen: 2026-04-23 09:32. Changes to AC/schemas after этой точки требуют явного approval пользователя.
