# Final Recommendations: OpenClaw Memory Patterns Integration

> Pipeline Phase: COMPARE
> Date: 2026-02-22
> Decision Type: USER_APPROVAL required

---

## Стратегический вывод

**Мы НЕ переходим на систему OpenClaw целиком.** OpenClaw — это runtime-приложение (TypeScript), мы — CLAUDE.md rule-based система для Claude Code. Программный enforcement невозможен в нашем контексте (hooks удалены по ADR, нет middleware).

**Вместо этого: SIMPLIFY + STRENGTHEN + ENRICH.**

---

## ПЛАН ДЕЙСТВИЙ (3 категории)

### A. УБРАТЬ (Delete/Archive) — Мёртвая инфраструктура

Файлы, которые никогда не использовались и создают ложное чувство покрытия:

| Файл | Записей | Действие | Причина |
|------|---------|----------|---------|
| `.claude/memory/session-insights/` | 0 | **DELETE** | Ни один агент никогда не создал файл. Overhead без value. |
| `.claude/memory/codebase-map.json` | 1 (стейлый) | **DELETE** | 1 запись ссылается на удалённый файл. Агенты используют Glob/Grep. |
| `work/attempt-history.json` | 0 | **SIMPLIFY** | Хорошая идея, но никогда не заполняется. Убрать JSON schema, оставить простой лог. |

**Эффект:** Убираем 3 файла, которые упоминаются в ~15 правилах CLAUDE.md. Каждое упоминание — это attention drain на модель. Меньше правил = выше compliance с оставшимися.

### B. УПРОСТИТЬ + УСИЛИТЬ — Существующие компоненты

#### B1. activeContext.md → Ротация + Архивирование

**Проблема:** 369 строк, растёт без ограничений. Старые session logs бесполезны.

**Решение (по паттерну OpenClaw daily logs):**
- Оставить activeContext.md как "текущая сессия" (Did/Decided/Learned/Next)
- Добавить `.claude/memory/archive/` для старых записей
- Правило в CLAUDE.md: при > 150 строках — перенести старые сессии в `archive/YYYY-MM.md`
- Текущий activeContext.md = только **последние 3 сессии** + текущий фокус

#### B2. patterns.md + gotchas.md → Merge into one file

**Проблема:** 2 отдельных файла, оба почти пусты. Два файла = два места, куда забывают писать.

**Решение:**
- Объединить в `.claude/memory/knowledge.md`
- Формат: `## Patterns` + `## Gotchas` в одном файле
- Один файл для чтения, один файл для записи — проще compliance
- Добавить яркий reminder в начало файла: "IF YOU LEARNED SOMETHING THIS SESSION, ADD IT HERE"

#### B3. Graphiti → Decide: Use or Remove

**Проблема:** Полноценная инфраструктура (Docker, FalkorDB, MCP) с НУЛЁМ данных.

**Варианты:**
1. **KEEP + ENFORCE** — Добавить в Session Start: обязательный `add_memory()` в конце каждой сессии. Если compliance не вырастет за 5 сессий → удалить.
2. **REMOVE** — Убрать Graphiti, упростить Session Start (минус 3 запроса), убрать Docker dependency. Использовать только file-based memory.
3. **REPLACE** — Вместо Graphiti использовать простой text search по .claude/memory/ (grep-based). Не нужен Docker, не нужен LLM для embedding.

**Рекомендация:** Вариант 1 (KEEP + ENFORCE) с дедлайном 5 сессий. Графити потенциально мощнее flat files. Но если за 5 сессий не заполнится — вариант 2.

### C. ЗАИМСТВОВАТЬ от OpenClaw — Новые паттерны

#### C1. Daily Log Pattern (ВЫСОКИЙ ПРИОРИТЕТ)

**Что:** Добавить `.claude/memory/daily/YYYY-MM-DD.md` — хронологический лог.

**Зачем:**
- OpenClaw использует это как PRIMARY memory store
- Проще, чем typed categories — просто "что произошло сегодня"
- Естественный формат — пиши как дневник
- Обнаружение: session-insights/ пусто потому что JSON schema слишком формальна. Daily log в Markdown = zero friction.

**Формат:**
```markdown
# 2026-02-22

## Work Done
- Analyzed OpenClaw memory system with 3 parallel agents
- Created comparison report (90KB total analysis)

## Key Decisions
- Keep PIPELINE.md system (OpenClaw has no equivalent)
- Simplify typed memory (merge patterns + gotchas)

## Learned
- OpenClaw uses pre-compaction memory flush — programmatic guarantee
- Our compliance rate is ~30-40% — need to simplify rules

## Gotchas Found
- Git clone of 214MB repos fails — use `gh api` for reading files
```

**Правило в CLAUDE.md:** "Перед завершением сессии — обновить `daily/YYYY-MM-DD.md`"
Это ЗАМЕНЯЕТ session-insights/ (JSON) — та же цель, но Markdown проще.

#### C2. Strengthened Post-Compaction Rules (ВЫСОКИЙ ПРИОРИТЕТ)

**Что:** Усилить формулировки After Compaction в CLAUDE.md по паттерну OpenClaw.

**Зачем:** OpenClaw инжектит: "The conversation summary is a HINT, NOT a substitute. Execute your startup sequence NOW." Мы можем использовать ту же формулировку.

**Изменение в CLAUDE.md Summary Instructions:**
```
After compaction: THE COMPACTION SUMMARY IS A HINT, NOT TRUTH.
Re-read work/PIPELINE.md + .claude/memory/activeContext.md + .claude/memory/knowledge.md IMMEDIATELY.
If PIPELINE.md has <- CURRENT marker: resume from that phase.
DO NOT proceed without re-reading these files.
```

#### C3. Simplified Session Start (СРЕДНИЙ ПРИОРИТЕТ)

**Что:** Сократить Session Start с 8 шагов до 4.

**Зачем:** 8 шагов с 3 Graphiti запросами — это слишком много. OpenClaw читает 4 файла (SOUL.md, USER.md, memory.md, today+yesterday memory/) — просто и эффективно.

**Новый Session Start:**
```
1. Read .claude/memory/activeContext.md (session bridge)
2. Read .claude/memory/knowledge.md (patterns + gotchas)
3. Read work/PIPELINE.md IF exists (find <- CURRENT)
4. IF Graphiti available: search_memory_facts(<task>, max_facts=5)
```

4 шага вместо 8. Graphiti как optional enrichment, не как mandatory.

#### C4. "Two-Phase Save" Pattern (СРЕДНИЙ ПРИОРИТЕТ)

**Что:** Разделить "After Task Completion" на 2 уровня по тяжести.

**Зачем:** Сейчас 9 шагов — агенты пропускают. OpenClaw разделяет на "всегда" (memory flush) и "если время есть" (reflection).

**Level 1 (MANDATORY — всегда, без исключений):**
1. Обновить activeContext.md (Did/Decided/Learned/Next)
2. Обновить daily/YYYY-MM-DD.md (что произошло)

**Level 2 (RECOMMENDED — если сессия была продуктивной):**
3. Обновить knowledge.md (новые patterns/gotchas)
4. add_memory() в Graphiti
5. Обновить work/STATE.md

2 обязательных шага вместо 9 — compliance вырастет с 30% до 80%+.

---

## НЕ ЗАИМСТВОВАТЬ от OpenClaw

| Фича OpenClaw | Причина отказа |
|---------------|----------------|
| Vector search / SQLite index | Нет runtime для индексирования. Graphiti уже даёт semantic search. |
| Session pruning | Нет контроля над Claude Code context window. |
| Context window guard | Нет доступа к token counting в Claude Code. |
| Pre-compaction silent turn | Нет runtime — не можем программно запустить. |
| AGENTS.md / SOUL.md / USER.md split | CLAUDE.md уже работает как единый файл. Split добавит complexity. |
| Session transcript persistence | Claude Code управляет sessions internally. |
| Embedding providers | Overhead для нашего use case. Graphiti покрывает semantic search. |

**Ключевое ограничение:** Мы не имеем runtime control. Всё, что OpenClaw делает программно (memory flush, pruning, guard), мы можем только *попросить* через CLAUDE.md rules. Поэтому заимствуем только то, что работает через rules.

---

## ИТОГОВАЯ АРХИТЕКТУРА (после изменений)

```
.claude/memory/
├── activeContext.md          # Session bridge (последние 3 сессии, max 150 строк)
├── knowledge.md              # Merged patterns + gotchas (one file to rule them all)
├── daily/                    # NEW: Daily logs по паттерну OpenClaw
│   ├── 2026-02-22.md
│   └── 2026-02-21.md
└── archive/                  # Archived old sessions from activeContext.md
    └── 2026-01.md

work/
├── PIPELINE.md               # KEEP: Pipeline state machine (наше преимущество)
├── STATE.md                  # KEEP: Simplified project state
└── openclaw-analysis/        # This analysis (can be archived after)

УДАЛЕНО:
├── .claude/memory/session-insights/    # Replaced by daily/
├── .claude/memory/codebase-map.json    # Never used, agents use Glob/Grep
└── work/attempt-history.json           # Simplified to just notes in daily log
```

**CLAUDE.md изменения:**
- Session Start: 8 → 4 шага
- After Task: 9 → 2 mandatory + 3 recommended
- After Compaction: усиленная формулировка ("HINT, NOT TRUTH")
- Убраны все упоминания удалённых файлов (~15 ссылок)

---

## МЕТРИКИ УСПЕХА

| Метрика | Текущее | Целевое | Как измерить |
|---------|---------|---------|-------------|
| Memory compliance | ~30-40% | >80% | Количество сессий с обновлённым activeContext.md + daily log |
| Knowledge entries | 3 (1+2) | 20+ за 10 сессий | Записей в knowledge.md |
| Daily logs created | 0 | 1 per session | Файлов в daily/ |
| activeContext.md size | 369 lines | <150 lines | wc -l |
| CLAUDE.md rule count | ~40 rules | ~25 rules | Fewer but stronger |
| Graphiti facts (if kept) | 0 | 10+ за 5 сессий | search_memory_facts count |

---

## ПОРЯДОК ИМПЛЕМЕНТАЦИИ

1. **DELETE мёртвые файлы** (session-insights/, codebase-map.json)
2. **CREATE daily/ directory** + first daily log
3. **MERGE patterns.md + gotchas.md → knowledge.md**
4. **TRIM activeContext.md** (archive old entries)
5. **UPDATE CLAUDE.md** (simplified rules, removed dead references, strengthened compaction)
6. **TEST** — 3 тестовые сессии с новой системой
7. **EVALUATE** — compare compliance metrics

---

## RISK ASSESSMENT

| Риск | Вероятность | Mitigation |
|------|------------|------------|
| Compliance не вырастет | Low | Упрощение с 40 → 25 правил математически увеличивает attention per rule |
| Knowledge.md тоже будет пуст | Medium | Daily log — path of least resistance. Если daily заполняется, knowledge получит данные |
| Graphiti останется пустым | High | Дедлайн 5 сессий. Если не заполнится — удалить dependency |
| Потеря данных при архивации activeContext.md | Low | Archive, не delete. Git tracking. |
