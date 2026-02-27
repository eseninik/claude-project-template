# OpenClaw Memory System — Source Code Analysis

> Comprehensive analysis of OpenClaw's memory architecture from source code.
> Files analyzed: `src/agents/tools/memory-tool.ts`, `src/agents/memory-search.ts`,
> `src/auto-reply/reply/memory-flush.ts`, `src/auto-reply/reply/agent-runner-memory.ts`,
> `src/config/types.memory.ts`, `src/agents/tools/memory-tool.test.ts`,
> `src/cli/memory-cli.ts`, `src/memory/index.ts`, `src/memory/types.ts`,
> `src/memory/search-manager.ts`, `src/memory/manager.ts`, `src/memory/backend-config.ts`,
> `src/memory/internal.ts`, `src/memory/hybrid.ts`, `src/memory/embeddings.ts`,
> `src/memory/memory-schema.ts`, `src/memory/query-expansion.ts`,
> `src/memory/temporal-decay.ts`, `src/memory/mmr.ts`

---

## Architecture Overview

OpenClaw's memory system is a **production-grade, multi-layered semantic search engine** built around SQLite + vector embeddings + FTS5 full-text search. The architecture follows a layered design:

```
Layer 1: Agent Tools (memory_search, memory_get)
    |
Layer 2: Search Manager Factory (backend selection + fallback)
    |
Layer 3: Memory Index Manager (sync, search, indexing)
    |
Layer 4: Hybrid Search Engine (vector + BM25 + MMR + temporal decay)
    |
Layer 5: Storage (SQLite + sqlite-vec + FTS5)
    |
Layer 6: Embedding Providers (OpenAI / Gemini / Voyage / Local GGUF)
```

**Key design principle**: The system is designed for **graceful degradation**. If embedding providers are unavailable (no API key, quota exhausted), it falls back to FTS-only mode. If the primary backend (QMD) fails, it falls back to the builtin SQLite backend. Every layer has fallback paths.

**Two backend modes**:
1. **builtin** — SQLite-based, with vector search via `sqlite-vec` extension + FTS5
2. **qmd** — External `qmd` CLI tool with its own search engine, routed via MCP (`mcporter`)

---

## Memory Tools Implementation

### memory_search

**File**: `src/agents/tools/memory-tool.ts` (lines 42-90)

The `memory_search` tool is the primary interface for the agent to recall past knowledge. It is described as a **"Mandatory recall step"** — the tool description explicitly tells the agent to use it before answering questions about prior work.

**Parameters** (TypeBox schema):
- `query` (string, required) — semantic search query
- `maxResults` (number, optional) — limit results
- `minScore` (number, optional) — minimum relevance threshold

**Execution flow**:
1. Obtains the `MemorySearchManager` via `getMemorySearchManager()` factory
2. If manager unavailable → returns structured `{ disabled: true, unavailable: true }` with actionable error
3. Calls `manager.search(query, { maxResults, minScore, sessionKey })`
4. Resolves citation mode (auto/on/off) — auto = citations in direct chats, suppressed in groups
5. Decorates results with `Source: path#L1-L10` citations
6. For QMD backend: clamps results by `maxInjectedChars` budget (default 4000 chars)
7. Returns `{ results, provider, model, fallback, citations, mode }`

**Error handling**:
- Quota errors (429/insufficient_quota) get special messaging: "Memory search is unavailable because the embedding provider quota is exhausted."
- Non-quota errors get generic: "Memory search is unavailable due to an embedding/provider error."
- Both include actionable `action` field telling the user what to fix

### memory_get

**File**: `src/agents/tools/memory-tool.ts` (lines 92-125)

A **safe snippet reader** for `MEMORY.md` and `memory/*.md` files. Designed for the agent to drill into specific results after a `memory_search`.

**Parameters**:
- `path` (string, required) — relative path within workspace
- `from` (number, optional) — start line
- `lines` (number, optional) — number of lines to read

**Security**: Path traversal is prevented — only `MEMORY.md`, `memory.md`, and files under `memory/` directory are allowed. Additional paths can be whitelisted via `extraPaths` config. Files must end in `.md`.

---

## Vector Indexing & Hybrid Search

### Search Pipeline

**File**: `src/memory/manager.ts` — `search()` method

The search pipeline has three modes:

1. **Hybrid mode** (default, when embedding provider available):
   - Execute FTS keyword search AND vector search in parallel
   - Merge results using weighted combination
   - Apply temporal decay (optional)
   - Apply MMR diversity re-ranking (optional)

2. **Vector-only mode** (hybrid disabled):
   - Only vector cosine similarity search
   - Filter by `minScore` threshold

3. **FTS-only mode** (no embedding provider):
   - Extract keywords from conversational queries
   - Search FTS5 with each keyword separately
   - Merge and deduplicate results by highest score

### Hybrid Merge Algorithm

**File**: `src/memory/hybrid.ts`

The hybrid merge uses a **weighted linear combination**:

```
final_score = vectorWeight * vectorScore + textWeight * textScore
```

**Default weights**: `vectorWeight = 0.7`, `textWeight = 0.3`

The merge process:
1. Build a map of all results by chunk ID
2. For items appearing in both vector and keyword results, combine scores
3. Apply temporal decay multiplier (exponential decay based on file age)
4. Sort by final score
5. Apply MMR re-ranking for diversity (if enabled)

### BM25 Text Search

**File**: `src/memory/hybrid.ts` — `bm25RankToScore()`

FTS5 returns BM25 rank values (lower = better). These are converted to [0, 1] scores:
```
score = 1 / (1 + max(0, rank))
```

FTS queries are constructed by AND-joining quoted tokens:
```
"token1" AND "token2" AND "token3"
```

### Vector Search

**File**: `src/memory/manager.ts` — `searchVector()`

Uses `sqlite-vec` extension for cosine similarity search in SQLite. Vectors are stored as JSON text in the `embedding` column and loaded into a virtual table (`chunks_vec`) for approximate nearest neighbor search.

**Candidate multiplier**: To ensure quality, the system fetches `maxResults * candidateMultiplier` (default 4x) candidates from each search backend before merging.

### MMR (Maximal Marginal Relevance)

**File**: `src/memory/mmr.ts`

Implements the Carbonell & Goldstein (1998) algorithm for **diversity-aware re-ranking**:

```
MMR = lambda * relevance - (1-lambda) * max_similarity_to_selected
```

**Key details**:
- Uses **Jaccard similarity** on tokenized text (not embedding vectors) for inter-result similarity
- Lambda default: 0.7 (biased toward relevance over diversity)
- Scores are normalized to [0,1] before MMR computation
- Disabled by default (opt-in)
- Iterative greedy selection: picks the item maximizing MMR score at each step

### Temporal Decay

**File**: `src/memory/temporal-decay.ts`

Applies exponential decay to scores based on file age:

```
multiplier = exp(-lambda * ageInDays)
lambda = ln(2) / halfLifeDays
```

**Default**: disabled; half-life = 30 days when enabled.

**Smart timestamp extraction**:
- Dated memory files (`memory/2024-01-15.md`) → parse date from filename
- Evergreen files (`MEMORY.md`, `memory/topics.md`) → **exempt from decay** (never decays)
- Other files → use filesystem `mtime`

### Query Expansion (FTS-only mode)

**File**: `src/memory/query-expansion.ts`

When no embedding provider is available, the system must extract useful keywords from conversational queries like "that thing we discussed about the API".

**Multilingual support**: Stop word lists for English, Chinese (Simplified), and Korean.

**Chinese handling**: Character-based n-gram tokenization (unigrams + bigrams) since no segmenter.

**Korean handling**: Strips trailing particles (조사) like 을/를/은/는 to extract stem keywords.

---

## Memory Flush (Pre-Compaction)

### Architecture

**File**: `src/auto-reply/reply/memory-flush.ts`

The memory flush is a **pre-compaction safety mechanism** that triggers the AI agent to save important memories to disk before the context window is compacted (summarized/truncated).

### Trigger Mechanism

**File**: `src/auto-reply/reply/agent-runner-memory.ts` — `runMemoryFlushIfNeeded()`

The flush is triggered when:

```
totalTokens >= contextWindowTokens - reserveTokensFloor - softThresholdTokens
```

Where:
- `softThresholdTokens` = 4000 (default) — how many tokens before compaction to trigger
- `reserveTokensFloor` = from PI compaction settings
- Additional guards: not a heartbeat, not CLI provider, workspace is writable

**Anti-duplicate**: Tracks `memoryFlushCompactionCount` to prevent flushing twice for the same compaction cycle.

### Flush Execution

The flush runs as an **embedded PI agent call** with a special prompt:

```
"Pre-compaction memory flush.
Store durable memories now (use memory/YYYY-MM-DD.md; create memory/ if needed).
IMPORTANT: If the file already exists, APPEND new content only and do not overwrite existing entries.
If nothing to store, reply with [SILENT_REPLY_TOKEN]."
```

The `YYYY-MM-DD` placeholder is replaced with the current date in the user's timezone.

**System prompt**:
```
"Pre-compaction memory flush turn.
The session is near auto-compaction; capture durable memories to disk.
You may reply, but usually [SILENT_REPLY_TOKEN] is correct."
```

The flush runs through `runWithModelFallback()` for resilience, and if it triggers a compaction internally, the compaction count is incremented.

### Sandbox Awareness

The flush respects sandbox configuration — if the workspace is read-only (`sandboxAccess !== "rw"`), the flush is skipped entirely.

---

## Storage Layer (SQLite)

### Schema

**File**: `src/memory/memory-schema.ts`

Four core tables + two virtual tables:

```sql
-- Metadata key-value store
CREATE TABLE meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

-- Tracked memory files
CREATE TABLE files (
  path TEXT PRIMARY KEY,
  source TEXT NOT NULL DEFAULT 'memory',  -- 'memory' | 'sessions'
  hash TEXT NOT NULL,     -- SHA-256 of file content
  mtime INTEGER NOT NULL,
  size INTEGER NOT NULL
);

-- Chunked content with embeddings
CREATE TABLE chunks (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  source TEXT NOT NULL DEFAULT 'memory',
  start_line INTEGER NOT NULL,
  end_line INTEGER NOT NULL,
  hash TEXT NOT NULL,       -- SHA-256 of chunk text
  model TEXT NOT NULL,      -- embedding model identifier
  text TEXT NOT NULL,       -- raw chunk text
  embedding TEXT NOT NULL,  -- JSON array of floats
  updated_at INTEGER NOT NULL
);

-- Embedding cache (prevents re-embedding unchanged chunks)
CREATE TABLE embedding_cache (
  provider TEXT NOT NULL,
  model TEXT NOT NULL,
  provider_key TEXT NOT NULL,
  hash TEXT NOT NULL,       -- SHA-256 of input text
  embedding TEXT NOT NULL,
  dims INTEGER,
  updated_at INTEGER NOT NULL,
  PRIMARY KEY (provider, model, provider_key, hash)
);

-- FTS5 virtual table for full-text search
CREATE VIRTUAL TABLE chunks_fts USING fts5(
  text,
  id UNINDEXED,
  path UNINDEXED,
  source UNINDEXED,
  model UNINDEXED,
  start_line UNINDEXED,
  end_line UNINDEXED
);

-- sqlite-vec virtual table for vector search (created dynamically)
-- chunks_vec
```

### Chunking Strategy

**File**: `src/memory/internal.ts` — `chunkMarkdown()`

- **Default chunk size**: 400 tokens (~1600 chars at 4 chars/token)
- **Default overlap**: 80 tokens (~320 chars)
- Line-aware chunking: chunks always start/end at line boundaries
- Long lines are segmented into maxChars portions
- Each chunk gets a SHA-256 hash for change detection
- Overlap is carried forward from the end of the previous chunk

### File Tracking & Sync

The manager tracks files via SHA-256 hashes. On sync:
1. List all memory files (`MEMORY.md`, `memory/*.md`, extra paths)
2. Compare file hashes with stored versions
3. Only re-chunk and re-embed changed files
4. Supports file watcher (chokidar) for real-time updates
5. Debounced sync (default 1500ms) to batch rapid changes

### Database Location

SQLite files are stored per-agent at:
```
{stateDir}/memory/{agentId}.sqlite
```

The state directory is resolved from environment variables or defaults to `~/.openclaw/`.

---

## Embedding Providers

### Abstraction Layer

**File**: `src/memory/embeddings.ts`

The `EmbeddingProvider` interface:
```typescript
interface EmbeddingProvider {
  id: string;           // "openai" | "local" | "gemini" | "voyage"
  model: string;        // model identifier
  maxInputTokens?: number;
  embedQuery(text: string): Promise<number[]>;
  embedBatch(texts: string[]): Promise<number[][]>;
}
```

### Supported Providers

| Provider | Default Model | Type |
|----------|--------------|------|
| OpenAI | `text-embedding-3-small` | Remote API |
| Gemini | `gemini-embedding-001` | Remote API |
| Voyage | `voyage-4-large` | Remote API |
| Local | `embeddinggemma-300m-qat-Q8_0.gguf` | Local GGUF via node-llama-cpp |

### Auto-Selection Logic

When `provider: "auto"`:
1. If local model file exists on disk → use local
2. Try each remote provider (OpenAI → Gemini → Voyage) in order
3. If all fail with missing API key → **degrade to FTS-only mode** (no crash)
4. Non-auth errors (network, etc.) are still fatal

### Vector Normalization

All embeddings are L2-normalized after generation:
```typescript
function sanitizeAndNormalizeEmbedding(vec: number[]): number[] {
  const sanitized = vec.map(v => Number.isFinite(v) ? v : 0);
  const magnitude = Math.sqrt(sanitized.reduce((sum, v) => sum + v * v, 0));
  if (magnitude < 1e-10) return sanitized;
  return sanitized.map(v => v / magnitude);
}
```

### Batch Processing

Supports batch embedding with:
- Configurable concurrency (default 2)
- Poll-based batch API for OpenAI/Gemini
- Failure tracking with circuit breaker (2 failures → disable batch)
- Separate batch implementations per provider

### Embedding Cache

The `embedding_cache` table prevents re-computing embeddings for unchanged text. Keyed by `(provider, model, provider_key, hash)`. Optional max entries cap with LRU eviction.

### Fallback Chain

```
Requested Provider → Fallback Provider → FTS-only mode
```

Example: `provider: "openai", fallback: "local"` → if OpenAI fails, try local → if local fails and both are auth errors, degrade to FTS-only.

---

## Error Handling & Fallbacks

### Multi-Layer Fallback Architecture

1. **Backend fallback** (search-manager.ts): `FallbackMemoryManager` wraps QMD primary with builtin fallback
   - If QMD search fails at runtime → switches to builtin index transparently
   - Evicts cached QMD manager so next request retries fresh
   - Preserves status reporting even during fallback

2. **Provider fallback** (embeddings.ts): Primary embedding provider → fallback provider → FTS-only
   - Missing API key errors trigger graceful degradation
   - Network errors remain fatal (likely transient, user should retry)

3. **Search mode fallback** (manager.ts): Hybrid → vector-only → FTS-only
   - If no embedding provider → FTS-only with keyword extraction
   - If FTS unavailable → vector-only
   - If both unavailable → empty results with warning

4. **Tool-level fallback** (memory-tool.ts): Returns structured error objects instead of throwing
   - `{ disabled: true, unavailable: true, error, warning, action }`
   - Agent sees actionable error and can inform user

### Quota-Specific Handling

The system detects embedding quota exhaustion (`429`, `insufficient_quota`) and provides specific guidance:
- Warning: "embedding provider quota is exhausted"
- Action: "Top up or switch embedding provider, then retry memory_search"

### Test Coverage

**File**: `src/agents/tools/memory-tool.test.ts`

Tests verify:
- Quota failures return structured `unavailable` payloads
- Non-quota failures return generic `unavailable` payloads
- Error messages are preserved in the response

---

## Configuration System

### Memory Search Config

**File**: `src/agents/memory-search.ts`

A deeply-nested configuration object with agent-level overrides:

```typescript
type ResolvedMemorySearchConfig = {
  enabled: boolean;
  sources: Array<"memory" | "sessions">;
  extraPaths: string[];
  provider: "openai" | "local" | "gemini" | "voyage" | "auto";
  remote?: { baseUrl, apiKey, headers, batch };
  fallback: "openai" | "gemini" | "local" | "voyage" | "none";
  model: string;
  local: { modelPath, modelCacheDir };
  store: { driver: "sqlite", path, vector: { enabled, extensionPath } };
  chunking: { tokens: 400, overlap: 80 };
  sync: { onSessionStart, onSearch, watch, watchDebounceMs, intervalMinutes, sessions };
  query: {
    maxResults: 6,
    minScore: 0.35,
    hybrid: {
      enabled: true,
      vectorWeight: 0.7,
      textWeight: 0.3,
      candidateMultiplier: 4,
      mmr: { enabled: false, lambda: 0.7 },
      temporalDecay: { enabled: false, halfLifeDays: 30 }
    }
  };
  cache: { enabled: true, maxEntries? };
};
```

Config merging: `agents.defaults.memorySearch` < agent-specific `memorySearch` override.

### Memory Backend Config

**File**: `src/memory/backend-config.ts`

For QMD backend: resolves collections, paths, update intervals, limits, mcporter config.
For builtin: just returns `{ backend: "builtin", citations }`.

---

## CLI Interface

**File**: `src/cli/memory-cli.ts`

Three subcommands:

### `openclaw memory status`
- Shows provider, model, indexed files/chunks, dirty state, store path
- `--deep`: probes embedding provider availability
- `--index`: reindexes if dirty (implies `--deep`)
- `--json`: machine-readable output
- Rich terminal output with colors/themes

### `openclaw memory index`
- Force reindex all memory files
- `--force`: full reindex even if not dirty
- Progress bar with ETA calculation
- Handles multiple agents

### `openclaw memory search <query>`
- Interactive search from terminal
- Shows score, path:line-range, and snippet
- `--max-results`, `--min-score` options
- `--json` for machine-readable output

---

## Key Patterns Worth Adopting

### 1. Graceful Degradation Chain
**Pattern**: Every layer has a fallback. Embedding fails → FTS-only. QMD fails → builtin. Tool fails → structured error.
**Why**: Memory should never crash the agent. Degraded search is better than no search.
**Applicability**: Our Graphiti-based system has a single point of failure (Graphiti MCP server). If it's down, memory is completely unavailable.

### 2. Pre-Compaction Memory Flush
**Pattern**: Automatically trigger memory persistence when the context window is near compaction threshold.
**Why**: Prevents knowledge loss during context window truncation.
**Applicability**: Our system relies on manual `activeContext.md` updates. An automatic pre-compaction flush would capture knowledge that might otherwise be lost.

### 3. Hybrid Search (Vector + BM25)
**Pattern**: Combine semantic vector search (70% weight) with keyword BM25 search (30% weight).
**Why**: Vector search catches semantic meaning; BM25 catches exact terms, code identifiers, and names that embeddings may miss.
**Applicability**: Our Graphiti system uses only entity/relationship matching. Adding a local vector+BM25 index for `.claude/memory/` files would give much better recall.

### 4. Content-Addressed Chunk Caching
**Pattern**: SHA-256 hash each chunk; only re-embed when content changes. Cache embeddings by (provider, model, hash).
**Why**: Embedding API calls are expensive. Caching avoids re-embedding unchanged content.
**Applicability**: If we add any embedding-based search, this pattern is essential for cost control.

### 5. Temporal Decay with Evergreen Exemption
**Pattern**: Exponential decay for dated memory files, but exempt `MEMORY.md` and non-dated files.
**Why**: Recent memories are more relevant, but core knowledge (MEMORY.md) should always rank high.
**Applicability**: Our `patterns.md` and `gotchas.md` are evergreen; `session-insights/` are dated. This distinction maps perfectly.

### 6. Query Expansion for FTS Fallback
**Pattern**: Extract keywords from conversational queries ("that thing about the API" → ["API"]) for FTS search.
**Why**: FTS needs keywords, but users ask in natural language.
**Applicability**: Useful if we add any FTS-based search. Also shows the importance of multilingual support (CJK handling).

### 7. Structured Error Responses (Not Exceptions)
**Pattern**: Tools return `{ disabled: true, unavailable: true, error, warning, action }` instead of throwing.
**Why**: The agent can understand and communicate the issue to the user.
**Applicability**: Our MCP tools could benefit from structured error responses that help the agent self-diagnose issues.

### 8. Two-Phase Search (Search Then Get)
**Pattern**: `memory_search` returns snippets with citations; `memory_get` reads full context. Keeps initial search results small.
**Why**: Prevents flooding the context window. Agent only reads full content when needed.
**Applicability**: Our `search_memory_facts` returns all data at once. A two-phase approach would reduce unnecessary context consumption.

### 9. File Watcher with Debounced Sync
**Pattern**: Watch memory files for changes; debounce (1500ms) and re-index automatically.
**Why**: Memory stays indexed without manual intervention.
**Applicability**: Could watch `.claude/memory/` for changes and auto-sync to any search index.

### 10. Agent-Scoped Memory Isolation
**Pattern**: Each agent gets its own SQLite database and can have different memory search configs.
**Why**: Multi-agent systems need isolated memory contexts.
**Applicability**: Our Agent Teams could benefit from per-agent memory scoping rather than shared global memory.

---

## Summary Comparison

| Feature | OpenClaw | Our System |
|---------|----------|------------|
| Storage | SQLite + sqlite-vec + FTS5 | Markdown files + Graphiti (Neo4j/FalkorDB) |
| Search | Hybrid (vector 70% + BM25 30%) | Graphiti entity/relationship matching |
| Embeddings | OpenAI/Gemini/Voyage/Local GGUF | None (Graphiti uses LLM for extraction) |
| Pre-compaction | Automatic memory flush | Manual activeContext.md update |
| Fallback | 3-layer degradation chain | Single point of failure |
| Chunking | 400 tokens with 80-token overlap | No chunking (whole-file reads) |
| Diversity | MMR re-ranking (Jaccard similarity) | None |
| Recency | Temporal decay (configurable half-life) | None |
| CLI | `memory status/index/search` | None |
| Multi-language | EN/ZH/KO stop words | N/A |
| Error handling | Structured `{ disabled, error, action }` | MCP error propagation |
| Caching | Embedding cache in SQLite | None |
| Real-time sync | File watcher + debounce | Manual file reads |
