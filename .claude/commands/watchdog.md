---
description: Управление Codex Watchdog (severity-graded). Usage — /watchdog [status|strict|normal|off|class] [args]
---

# /watchdog — Codex Watchdog Control

Контролирует ТОЛЬКО Codex Watchdog (Stop hook), НЕ трогает `codex-gate` (PreToolUse parallel review — by-design и остаётся активным всегда).

## Invocation

Пользователь ввёл: `/watchdog $ARGUMENTS`

Парсинг первого слова `$ARGUMENTS`:

### Подкоманды

| Команда | Что делает |
|---|---|
| `/watchdog` или `/watchdog status` | Показать текущий state |
| `/watchdog strict [30m]` | Форсировать `deploy`-level строгость на N минут (default 30m) |
| `/watchdog normal` | Снять override, вернуть автоклассификатор |
| `/watchdog off [30m]` | Полностью выключить watchdog на N минут (default 30m) |
| `/watchdog class <name>` | Форсировать конкретный task-class (chat/typo/bugfix/feature/refactor/deploy) |

### Парсинг duration

`30m` → 1800 сек, `5m` → 300, `1h` → 3600, `2h` → 7200. Если duration не указан, default 30m (1800s).

## Выполнение

### Если команда = `status` или пустая:
1. Прочитать `.codex/task-class` (если есть)
2. Прочитать `.codex/task-class-override` (если есть, проверить `until > now`)
3. Прочитать `.codex/watchdog-state.json` (recent_wakes, cooldown_remaining)
4. Последние 3 записи из `.codex/watchdog-trail.jsonl`
5. Вывести пользователю в виде Markdown таблицы:
   - Current task-class (source: detector/override/default)
   - Override active until: (timestamp + human readable)
   - Cooldown remaining: N stops
   - Recent wakes: last 3 with severity + timestamp

### Если команда = `strict`, `off`, или `class <name>`:
1. Парсить duration (default 1800s если не указан)
2. Compute `until = time.time() + duration_seconds`
3. Определить class value:
   - `strict` → class = `deploy`
   - `off` → class = `off` (watchdog hook читает и skip'ает)
   - `class X` → class = X (validate X in {chat, typo, bugfix, feature, refactor, deploy})
4. Write `.codex/task-class-override` с JSON:
   ```json
   {"class": "<value>", "until": <unix_ts>, "set_at": <now>, "source": "slash_command"}
   ```
5. Подтвердить пользователю: `Watchdog override: class=X active until <timestamp>`.

### Если команда = `normal`:
1. Удалить `.codex/task-class-override` если существует.
2. Подтвердить: `Watchdog override cleared — автоклассификатор активен`.

## Validation

- Неизвестная подкоманда → показать usage table.
- Неизвестный class → показать список KNOWN_CLASSES.
- Duration parse fail → default 30m, warn пользователю.

## Safety

- Файл `.codex/task-class-override` — TTL-based (expires at `until`). Stale overrides игнорируются хуками.
- НЕ трогать `.codex/watchdog-state.json` — это runtime state, управляется хуком.
- НЕ удалять `.codex/watchdog-trail.jsonl` (логи) — даже при `/watchdog off`, только при явном `/watchdog clear-trail` (не в этой версии).

## Примеры

```
/watchdog
→ [показывает текущий статус]

/watchdog off 15m
→ Watchdog override: class=off active until 2026-04-23 09:55 (15m)

/watchdog strict
→ Watchdog override: class=deploy active until 2026-04-23 10:15 (30m)

/watchdog class bugfix
→ Watchdog override: class=bugfix active until 2026-04-23 10:15 (30m)

/watchdog normal
→ Watchdog override cleared — автоклассификатор активен
```
