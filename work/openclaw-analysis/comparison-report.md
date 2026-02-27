# OpenClaw vs Our System — Memory & Context Persistence Comparison

> **Status:** DRAFT — will be updated with source code analysis from agents
> **Date:** 2026-02-22
> **Pipeline Phase:** RESEARCH → COMPARE

---

## Executive Summary

OpenClaw и наша система представляют **два фундаментально разных подхода** к сохранению памяти AI-агента:

| Аспект | OpenClaw | Наша система |
|--------|----------|-------------|
| **Архитектура** | Программная (TypeScript runtime) | Rule-based (CLAUDE.md behavioral rules) |
| **Enforcement** | Код *заставляет* модель сохранять | Правила *просят* модель сохранять |
| **Память** | Markdown + Vector Index (SQLite) | Markdown + Graphiti (Knowledge Graph) |
| **Поиск** | Hybrid BM25 + Vector (semantic) | Graphiti search_facts/search_nodes |
| **Compaction** | Auto-flush перед compaction (silent turn) | Manual re-read после compaction (CLAUDE.md rules) |
| **Session** | JSONL transcripts + session store | Нет transcript persistence |
| **Multi-agent** | Isolated workspaces per agent | Shared .claude/ с Agent Teams |

### Ключевой вывод

**OpenClaw превосходит** нашу систему в 3 критических областях:
1. **Automatic Memory Flush** — программная гарантия сохранения перед compaction
2. **Vector/Semantic Search** — recall по смыслу, а не только по ключевым словам
3. **Context Window Monitoring** — runtime знает точный объём контекста

**Наша система превосходит** OpenClaw в:
1. **Pipeline State Machine** — PIPELINE.md с <- CURRENT для multi-phase задач
2. **Typed Memory** — structured knowledge (patterns, gotchas, codebase-map)
3. **Agent Teams** — параллельные агенты с TeamCreate для сложных задач
4. **Graphiti Knowledge Graph** — entities + relationships (не просто chunks)

---

## 1. Memory Storage

### OpenClaw
- **Daily logs**: `memory/YYYY-MM-DD.md` — append-only per day
- **Long-term memory**: `MEMORY.md` — curated durable facts
- **Workspace files**: `AGENTS.md`, `SOUL.md`, `USER.md`, `IDENTITY.md`, `TOOLS.md`
- **Proposed bank/ (v2)**: `bank/entities/*.md`, `bank/opinions.md`, `bank/experience.md`
- **Location**: `~/.openclaw/workspace/`
- **Git-backed**: рекомендуется private repo

### Наша система
- **Active context**: `.claude/memory/activeContext.md` — session bridge (Did/Decided/Learned/Next)
- **Patterns**: `.claude/memory/patterns.md` — reusable patterns discovered by agents
- **Gotchas**: `.claude/memory/gotchas.md` — known pitfalls and warnings
- **Codebase map**: `.claude/memory/codebase-map.json` — file structure awareness
- **Session insights**: `.claude/memory/session-insights/` — per-session learnings
- **Pipeline state**: `work/PIPELINE.md` + `work/STATE.md`
- **Graphiti**: Knowledge graph via MCP (semantic layer)
- **Git-backed**: tracked in repo

### Сравнение

| Фактор | OpenClaw | Наша система | Победитель |
|--------|----------|-------------|-----------|
| Организация | Daily logs + curated memory | Typed categories (patterns/gotchas/context) | **Наша** — более структурировано |
| Recall quality | Daily log перечитывание (today+yesterday) | Full context re-read at session start | **Наша** — всё загружается |
| Scalability | ∞ days, vector search finds relevant | Grows linearly, manual reading | **OpenClaw** — vector search масштабируется |
| Human editability | Excellent (plain Markdown) | Excellent (plain Markdown) | **Ничья** |
| Git integration | Recommended, separate repo | Built into project repo | **Наша** — проектная специфика сохраняется |

---

## 2. Memory Search & Recall

### OpenClaw — Hybrid Search Engine

Самый впечатляющий компонент OpenClaw. Полноценный поисковый движок:

1. **SQLite-backed index** per agent (`~/.openclaw/memory/<agentId>.sqlite`)
2. **Chunking**: ~400 tokens per chunk, 80-token overlap
3. **Hybrid search**: BM25 (keyword) + Vector (semantic) с weighted merge
4. **MMR re-ranking**: Maximal Marginal Relevance для diversity
5. **Temporal decay**: Recent memories rank higher (half-life configurable)
6. **Embedding providers**: OpenAI, Gemini, Voyage, local GGUF
7. **Embedding cache**: SQLite cache для повторного индексирования
8. **Session transcript indexing**: Experimental — index session history
9. **QMD backend**: Optional local-first search sidecar (BM25 + vectors + reranking)

**Формула скоринга:**
```
finalScore = vectorWeight × vectorScore + textWeight × textScore
decayedScore = finalScore × e^(-λ × ageInDays)
```

**MMR diversity:**
```
select = argmax(λ × relevance − (1−λ) × max_similarity_to_selected)
```

### Наша система — Graphiti + Manual

1. **Graphiti**: Knowledge graph с entities + relationships + facts
2. **search_memory_facts()**: Поиск фактов по запросу
3. **search_nodes()**: Поиск entities по запросу
4. **Manual file reading**: Read patterns.md, gotchas.md at session start

### Сравнение

| Фактор | OpenClaw | Наша система | Победитель |
|--------|----------|-------------|-----------|
| Semantic recall | Vector embeddings (cosine similarity) | Graphiti semantic search | **Ничья** — оба semantic |
| Keyword recall | BM25 full-text search | Нет | **OpenClaw** — BM25 ловит точные совпадения |
| Relationship modeling | Нет (flat chunks) | Graphiti entities + edges | **Наша** — граф знаний |
| Recency weighting | Temporal decay (configurable half-life) | Нет | **OpenClaw** — явный temporal bias |
| Diversity | MMR re-ranking | Нет | **OpenClaw** — уникальные результаты |
| Offline capability | Local GGUF embeddings | Requires MCP server (Docker) | **OpenClaw** — работает offline |
| Infrastructure | SQLite (zero-config) | FalkorDB + MCP container | **OpenClaw** — проще |
| Scalability | Excellent (SQLite + vector index) | Good (graph scales well) | **Ничья** |

---

## 3. Compaction Survival

### OpenClaw — Automatic Memory Flush

**Программная гарантия** сохранения перед compaction:

1. When session nears `contextWindow - reserveTokensFloor - softThresholdTokens`:
2. OpenClaw triggers a **silent agentic turn** (invisible to user)
3. System prompt: "Session nearing compaction. Store durable memories now."
4. User prompt: "Write any lasting notes to memory/YYYY-MM-DD.md; reply with NO_REPLY if nothing to store."
5. Model writes to memory files
6. **One flush per compaction cycle** (tracked in sessions.json)
7. After flush: compaction summarizes and persists summary in JSONL

**Конфигурация:**
```json5
compaction: {
  reserveTokensFloor: 20000,
  memoryFlush: {
    enabled: true,
    softThresholdTokens: 4000,
    systemPrompt: "Session nearing compaction...",
    prompt: "Write any lasting notes..."
  }
}
```

### Наша система — Rule-Based Recovery

**Behavioural rules** в CLAUDE.md:

1. **Session Start (MANDATORY)**:
   - Read activeContext.md, patterns.md, gotchas.md
   - Query Graphiti (search_memory_facts, search_nodes)
   - Read PIPELINE.md, STATE.md
2. **After Compaction (MANDATORY)**:
   - Re-read ALL state files
   - Query Graphiti for context recovery
   - Find <- CURRENT in PIPELINE.md
3. **Phase Transition Protocol**:
   - Git commit + checkpoint tag
   - Insight extraction
   - Update typed memory + Graphiti
   - Re-read everything

### Сравнение

| Фактор | OpenClaw | Наша система | Победитель |
|--------|----------|-------------|-----------|
| Pre-compaction save | AUTOMATIC (silent turn) | MANUAL (blocking rule in CLAUDE.md) | **OpenClaw** — гарантировано |
| Post-compaction recovery | Summary in JSONL | Re-read files + Graphiti | **Наша** — более полное восстановление |
| Compaction survival | Summary + memory files | PIPELINE.md + STATE.md + typed memory + Graphiti | **Наша** — больше контекста |
| Reliability | 100% (programmatic) | ~80% (depends on model following rules) | **OpenClaw** — не зависит от модели |
| Multi-phase tasks | Нет специальной поддержки | PIPELINE.md <- CURRENT marker | **Наша** — pipelines выживают |

---

## 4. Context Window Management

### OpenClaw
- **Context window guard**: Real-time token estimation
- **Session pruning**: Trims old tool results (soft + hard)
- **Auto-compaction**: Triggers when window is tight
- **Memory flush**: Pre-compaction silent turn
- `/context list` и `/context detail` для инспекции
- **Token counting**: Chars ≈ tokens × 4 estimation

### Наша система
- **Нет мониторинга контекстного окна**
- **Нет session pruning**
- **Нет автоматической compaction**
- Полагаемся на Claude Code встроенную compaction
- CLAUDE.md правила для recovery после compaction

### Сравнение

| Фактор | OpenClaw | Наша система | Победитель |
|--------|----------|-------------|-----------|
| Window monitoring | Real-time guard | Нет | **OpenClaw** |
| Pruning | Soft/hard trim old tool results | Нет | **OpenClaw** |
| Pre-compaction action | Auto memory flush | Нет | **OpenClaw** |
| Post-compaction recovery | JSONL summary | Re-read state files + Graphiti | **Наша** |
| Inspection tools | /context list, /context detail | Нет | **OpenClaw** |

---

## 5. Session & Transcript Management

### OpenClaw
- **JSONL transcripts**: Per-session history on disk
- **Session store**: `sessions.json` per agent
- **Session tools**: sessions_list, sessions_history, sessions_send, sessions_spawn
- **Session pruning**: TTL-based tool result trimming
- **Cross-session messaging**: Agent can send to another session
- **Session memory search**: Experimental — index transcripts for recall
- **Daily reset**: Sessions expire and refresh

### Наша система
- **Нет transcript persistence** (Claude Code manages internally)
- **Нет session tools**
- **Session bridge**: activeContext.md (manual bridge between sessions)
- **Session insights**: Per-session learnings saved to files
- **Graphiti**: Cross-session knowledge via knowledge graph

### Сравнение

| Фактор | OpenClaw | Наша система | Победитель |
|--------|----------|-------------|-----------|
| Transcript persistence | JSONL on disk | Нет (Claude Code internal) | **OpenClaw** |
| Cross-session recall | Session transcript indexing | Graphiti + activeContext.md | **Ничья** — разные подходы |
| Session tools | Full CRUD + spawn | Нет | **OpenClaw** |
| Knowledge extraction | Raw transcripts | Typed memory (patterns/gotchas) | **Наша** — structured knowledge |

---

## 6. Workspace & Bootstrap

### OpenClaw
- `AGENTS.md` — Operating instructions (наш CLAUDE.md)
- `SOUL.md` — Persona, tone, boundaries
- `USER.md` — User profile
- `IDENTITY.md` — Agent name/vibe
- `TOOLS.md` — Tool notes
- `HEARTBEAT.md` — Heartbeat checklist
- `BOOTSTRAP.md` — One-time first-run ritual
- Per-file truncation (`bootstrapMaxChars: 20000`)
- Total cap (`bootstrapTotalMaxChars: 150000`)

### Наша система
- `CLAUDE.md` — All-in-one instructions
- `.claude/memory/` — Typed memory
- `.claude/guides/` — On-demand guides
- `.claude/agents/` — Agent registry
- `.claude/prompts/` — Focused prompts
- `.claude/skills/` — Skills library

### Сравнение

| Фактор | OpenClaw | Наша система | Победитель |
|--------|----------|-------------|-----------|
| Separation of concerns | 7 specialized files | 1 CLAUDE.md + many supporting files | **OpenClaw** — cleaner separation |
| Extensibility | Skills directory + managed skills | Skills + guides + agents + prompts | **Наша** — более богатая экосистема |
| Size management | Auto-truncation per file | Manual (guides loaded on-demand) | **OpenClaw** — автоматический контроль |

---

## 7. Multi-Agent

### OpenClaw
- **Isolated workspaces**: Each agent has own workspace + sessions + auth
- **Multi-account routing**: Route channels/peers to specific agents
- **Agent-to-agent messaging**: sessions_send between agents
- **Sub-agent spawning**: sessions_spawn for isolated tasks
- **Safety**: Per-agent sandbox + tool restrictions

### Наша система
- **Agent Teams**: TeamCreate + Task + SendMessage
- **Shared workspace**: All agents share .claude/ and project files
- **Agent types**: Registry with tools/skills/thinking/memory per type
- **Git worktrees**: Isolation via git worktree for file conflicts
- **Pipeline coordination**: Shared task list + message routing

### Сравнение

| Фактор | OpenClaw | Наша система | Победитель |
|--------|----------|-------------|-----------|
| Agent isolation | Full workspace isolation | Shared workspace, optional worktrees | **OpenClaw** — полная изоляция |
| Task coordination | Session messaging | Task list + direct messaging | **Наша** — structured task management |
| Parallel execution | Multi-account routing | Agent Teams (3-10 agents) | **Наша** — более гибко для dev tasks |
| Pipeline management | Нет формальной поддержки | PIPELINE.md state machine | **Наша** |

---

## 8. Unique OpenClaw Features Not In Our System

1. **Memory Flush (Pre-Compaction Silent Turn)**
   - Программная гарантия сохранения перед compaction
   - У нас: только CLAUDE.md правила (ненадёжно)

2. **Vector/Semantic Search over Markdown**
   - SQLite + embeddings для recall по смыслу
   - У нас: Graphiti (другой подход, но без local file indexing)

3. **Hybrid Search (BM25 + Vector)**
   - Keyword + semantic в одном запросе
   - У нас: только Graphiti semantic search

4. **Temporal Decay**
   - Свежие записи ранжируются выше
   - У нас: нет temporal weighting

5. **MMR Diversity Re-ranking**
   - Убирает дубликаты из результатов поиска
   - У нас: нет

6. **Session Transcript Indexing**
   - Индексирование истории разговоров для recall
   - У нас: нет (sessions не сохраняются)

7. **Context Window Guard**
   - Real-time мониторинг заполнения контекста
   - У нас: нет

8. **Session Pruning**
   - Автоматическая очистка старых tool results
   - У нас: нет

9. **Daily Log Pattern (YYYY-MM-DD.md)**
   - Хронологическая организация памяти
   - У нас: categorical (patterns/gotchas/context)

---

## 9. Unique Our Features Not In OpenClaw

1. **Pipeline State Machine (PIPELINE.md)**
   - Формальные фазы с gates и transitions
   - Compaction-resilient (<- CURRENT marker)

2. **Typed Memory Categories**
   - Patterns, Gotchas, Codebase Map — structured knowledge
   - OpenClaw: flat daily logs

3. **Graphiti Knowledge Graph**
   - Entities + relationships + temporal facts
   - OpenClaw: flat vector chunks

4. **Agent Teams (TeamCreate)**
   - Parallel agent execution with shared task list
   - OpenClaw: isolated agents, no shared task coordination

5. **Phase Transition Protocol**
   - Structured knowledge preservation between pipeline phases
   - OpenClaw: no pipeline concept

6. **Agent Registry**
   - 24 agent types with tools/skills/thinking/memory specs
   - OpenClaw: per-workspace agent config

7. **Expert Panel Mode**
   - Multi-expert analysis before implementation
   - OpenClaw: no equivalent

8. **Complexity Assessment**
   - 5-tier risk classification → QA depth
   - OpenClaw: no equivalent

9. **Recovery Manager**
   - Attempt tracking, circular fix detection
   - OpenClaw: no equivalent

---

## 10. Recommendations

### Category A: ADOPT from OpenClaw (High Impact, Low Risk)

1. **Daily Log Pattern** — Add `memory/YYYY-MM-DD.md` daily logs alongside typed memory
   - Low effort, high value for chronological recall
   - Complements existing patterns.md/gotchas.md (they stay)

2. **Temporal Organization** — Date-based memory alongside categorical
   - Today+yesterday auto-loaded at session start
   - Older entries searchable via Graphiti

3. **Pre-Compaction Memory Save Rule Enhancement**
   - Add explicit "save to memory before compaction" rule
   - Can't do silent turn (no runtime control), but can strengthen CLAUDE.md rule
   - Make it FIRST priority in "After Task Completion"

### Category B: CONSIDER from OpenClaw (Medium Impact, Medium Risk)

4. **Vector Search over Local Files**
   - Could add embedding index over .claude/memory/*.md
   - Graphiti already provides semantic search, but local vector adds keyword recall
   - Risk: complexity, embedding provider dependency

5. **Workspace File Separation**
   - Split CLAUDE.md into AGENTS.md (rules) + SOUL.md (persona) + USER.md (user profile)
   - OpenClaw pattern of 7 specialized files is cleaner
   - Risk: breaking existing workflow, migration effort

6. **Daily Memory Rotation**
   - Auto-create `memory/YYYY-MM-DD.md` per session
   - Archive old entries, keep recent ones loaded
   - Risk: file proliferation

### Category C: KEEP our approach (Our System Better)

7. **Pipeline State Machine** — Keep PIPELINE.md (OpenClaw has nothing comparable)
8. **Typed Memory Categories** — Keep patterns.md, gotchas.md, codebase-map.json
9. **Agent Teams** — Keep TeamCreate for parallel dev tasks
10. **Graphiti Knowledge Graph** — Keep for relationship-aware recall
11. **Phase Transition Protocol** — Keep for knowledge preservation
12. **Agent Registry** — Keep for structured team composition

### Category D: HYBRID approach (Best of Both)

13. **Memory Architecture**: Keep typed memory + add daily logs + enhance Graphiti
14. **Search**: Keep Graphiti for graph queries + consider local vector for keyword recall
15. **Compaction**: Keep PIPELINE.md recovery + add stronger pre-compaction save rules
16. **Context**: Keep our rules + add context usage awareness

---

## 11. Proposed Migration Plan (Draft)

### Phase 1: Low-Risk Enhancements (No Breaking Changes)
- Add daily log pattern (`memory/YYYY-MM-DD.md`)
- Strengthen pre-compaction memory save rules in CLAUDE.md
- Add context usage awareness rules

### Phase 2: Search Enhancement (Medium Risk)
- Evaluate: Graphiti enrichment vs local vector search
- If Graphiti sufficient: enhance with better fact extraction
- If local vector needed: add SQLite + embeddings for .claude/memory/

### Phase 3: Workspace Restructuring (Higher Risk)
- Evaluate splitting CLAUDE.md into specialized files
- Test: does separation improve or hurt agent behavior?
- If positive: migrate gradually

### Stress Test Design
- Baseline: current system on 3 standard tasks
- Post-change: same tasks with new system
- Metrics: memory recall accuracy, compaction survival, task completion quality

---

## Appendix: Architecture Diagrams

### OpenClaw Memory Flow
```
User Message → Agent Loop → Tool Calls → Memory Write
                    ↓
            Context Window Guard
                    ↓ (threshold)
            Memory Flush (silent turn)
                    ↓
            Compaction (JSONL summary)
                    ↓
            Session Pruning (tool results)
```

### Our Memory Flow
```
Session Start → Read activeContext.md, patterns.md, gotchas.md
              → Query Graphiti
              → Read PIPELINE.md, STATE.md
                    ↓
            Work (with CLAUDE.md rules)
                    ↓
            Phase Transition Protocol
              → Git commit + checkpoint
              → Insight extraction
              → Update typed memory + Graphiti
                    ↓
            After Compaction
              → Re-read ALL state files
              → Query Graphiti
              → Find <- CURRENT in PIPELINE.md
```
