# A1: Athena Memory & Persistence Analysis

## Architecture Overview

Athena implements a **dual-layer memory architecture** that separates **state** (human-readable markdown files) from **recall** (vector-embedded semantic search in Supabase). This is a deliberate architectural choice summarized in their docs as:

> - **Vector DB**: "Where did I see something about X?" (search/recall)
> - **Memory Bank**: "What am I working on right now?" (state/context)

The system is organized across three physical storage backends:

1. **Local Filesystem** (`.context/`, `.athena/`, `.agent/`) -- Markdown files for structured state, session logs, protocols, case studies, and configuration. This is the "Memory Bank."
2. **Supabase + pgvector** (cloud PostgreSQL) -- Vector embeddings of all knowledge artifacts for semantic search. This is the "VectorRAG" layer.
3. **Local SQLite + FTS5** (optional "Exocortex") -- An offline Wikipedia/DBPedia knowledge base (~6GB) for fact-checking and grounding without API calls.

Data flows **unidirectionally from filesystem to Supabase** via a sync engine (`sync.py`), tracked by a delta manifest (`delta_manifest.py`) that prevents redundant uploads.

### Data Flow Diagram (Conceptual)

```
  Markdown Files (local)
        |
        v
  DeltaManifest (change detection)
        |
        v
  sync.py (upsert to Supabase)
        |
        v
  Supabase Tables (sessions, protocols, case_studies, etc.)
  + pgvector embeddings (Gemini gemini-embedding-001, 3072 dims)
        |
        v
  search.py (Hybrid RAG: RRF fusion of canonical + tags + vectors + filesystem + GraphRAG)
        |
        v
  AI Agent context window
```

---

## Key Components

### 1. Memory Bank (4 Pillars) -- `examples/templates/memory_bank/`

The Memory Bank is a set of 4 markdown files that serve as the agent's **structured long-term state**:

| File | Purpose | Update Frequency |
|------|---------|-----------------|
| `activeContext.md` | Current focus, active tasks, recent decisions | Every session |
| `userContext.md` | User profile, preferences, constraints | When user preferences change |
| `productContext.md` | Product philosophy, goals, positioning | When strategy changes |
| `systemPatterns.md` | Architecture decisions, patterns, tech debt | When architecture evolves |

**Key design principle**: O(1) boot cost. The Memory Bank is designed to load the same ~10K tokens whether it is Session 1 or Session 10,000. A hard cap of ~15K tokens is enforced, with auto-compaction when exceeded.

**Token Budget Breakdown**:
- `userContext.md`: ~3K (near-zero growth -- identity is stable)
- `productContext.md`: ~2K (near-zero growth -- mission is stable)
- `activeContext.md`: ~5K (rolling -- compacts automatically)
- Boot script output: ~2K (fixed)
- System instructions: ~3K (fixed)

**Progressive Distillation Pipeline**:
```
Live conversation (100% fidelity)
  -> Session log (~15% -- key insights only)
    -> activeContext.md entry (~5% -- compressed summary)
      -> Eventually compacted out (~0.1% -- absorbed into userContext.md)
```

This is the most novel aspect of the Memory Bank: knowledge is progressively compressed through 4 stages, each retaining less detail but higher signal density.

### 2. Delta Manifest -- `src/athena/memory/delta_manifest.py`

The DeltaManifest is a **change-tracking engine** that determines which files need to be re-synced to Supabase. It uses a 3-tier detection strategy:

1. **O(1) New File Check**: Is the file in the manifest at all? If not, sync it.
2. **O(1) Quick Check**: Compare `size` + `mtime` against stored values. If both match, skip (likely unchanged).
3. **O(N) Deep Check**: If quick check fails, compute SHA-256 hash of normalized content (whitespace-trimmed, CRLF->LF) and compare against stored hash.

**Implementation details**:
- **Thread-safe**: Uses `threading.Lock` for shared manifest updates
- **Atomic writes**: Uses `tempfile.mkstemp` + `os.replace` pattern to prevent corruption on crash
- **Path stability**: All paths stored relative to `PROJECT_ROOT` to survive directory moves
- **Stale detection**: `get_stale_files()` identifies manifest entries for files that no longer exist on disk

The manifest is persisted at `.athena/state/manifest.json` as a JSON file with entries like:
```json
{
  "version": "1.1",
  "files": {
    "relative/path/to/file.md": {
      "hash": "sha256...",
      "size": 1234,
      "mtime": 1708900000.0,
      "last_synced": "2026-02-12T...",
      "remote_id": null
    }
  }
}
```

### 3. Vector Storage & Embeddings -- `src/athena/memory/vectors.py`

The vector layer provides:

- **Embedding generation** using Google's `gemini-embedding-001` model (3072 dimensions in MASTER_SCHEMA, 768 in legacy schema.sql)
- **Persistent embedding cache** (`PersistentEmbeddingCache`): JSON-backed, thread-safe, with background async disk saves via daemon threads. Uses MD5 hash of text as cache key.
- **Thread-local Supabase clients**: Each thread gets its own `create_client()` instance via `threading.local()` to prevent httpx connection state corruption in parallel search operations.
- **Atomic cache writes**: Same `tempfile.mkstemp` + `os.replace` pattern as the DeltaManifest.

The search layer exposes dedicated RPC wrappers for each Supabase table:
- `search_sessions`, `search_case_studies`, `search_protocols`
- `search_capabilities`, `search_playbooks`, `search_references`
- `search_frameworks`, `search_workflows`, `search_entities`
- `search_user_profile`, `search_system_docs`, `search_insights`

Each wrapper calls a corresponding Supabase RPC function that computes `1 - (embedding <=> query_embedding)` (cosine distance) with a configurable threshold (default 0.3) and result limit.

### 4. Sync Engine -- `src/athena/memory/sync.py`

The sync engine connects the local filesystem to Supabase:

- **Per-file sync** (`sync_file_to_supabase`): Reads file content, extracts metadata (YAML frontmatter), generates embedding, and upserts to the appropriate Supabase table.
- **Exponential backoff retries**: 3 attempts with `wait = 2^attempt + 0.5` seconds.
- **Smart table routing**: `_enrich_data_by_table()` adds table-specific fields (e.g., `date` + `session_number` for sessions, `code` for protocols, etc.).
- **Conflict resolution**: Upserts on `file_path` (unique constraint), with fallback to `code` for protocols/case_studies.
- **Content truncation**: Only first 30,000 characters of content are embedded (`get_embedding(content[:30000])`).
- **Deletion support**: `delete_file_from_vector()` removes entries by file_path, routing to the correct table based on path patterns.

### 5. Supabase Schema -- `supabase/MASTER_SCHEMA.sql`

The production schema (v8.1) defines 8 core tables:

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `sessions` | Daily interaction logs | date, session_number, summary, embedding, metadata JSONB |
| `case_studies` | Pattern analysis documents | code (unique), tags[], embedding |
| `protocols` | Reusable thinking patterns | code, name, category, tags[], embedding |
| `capabilities` | Tool/capability definitions | name (unique), tags[], embedding |
| `playbooks` | Operational playbooks | name, tags[], embedding |
| `references` | Reference documents | name, tags[], embedding |
| `frameworks` | Framework documents | name, tags[], embedding |
| `workflows` | Workflow definitions | name, description, tags[], embedding |

**Notable schema features**:
- All tables use `UUID` primary keys (gen_random_uuid)
- All have `vector(3072)` embedding columns (upgraded from 768 in v8.1)
- All have `JSONB metadata` columns for extensible attributes
- All have `file_path TEXT UNIQUE` for upsert conflict resolution
- **No IVFFlat indexes** in MASTER_SCHEMA (intentionally removed due to pgvector <0.5.0 limitation with >2000 dims). Uses exact search instead, which is acceptable for <100K rows.
- **Auto-enrichment triggers**: `auto_enrich_metadata()` function fires on INSERT/UPDATE for every table, auto-populating `auto_tags` from name/title and updating `updated_at`.

### 6. Hybrid RAG Search -- `src/athena/tools/search.py`

The search system implements **Reciprocal Rank Fusion (RRF)** across multiple retrieval sources:

**Source types and weights**:
```
case_study: 3.0    session: 3.0      protocol: 2.8
graphrag: 2.5      user_profile: 2.5  framework_docs: 2.5
framework: 2.3     tags: 2.2          canonical: 2.0
filename: 2.0      vector: 1.8        capability: 1.8
playbook: 1.8      workflow: 1.8      entity: 1.8
reference: 1.8     system_doc: 1.8    sqlite: 1.5
exocortex: 1.5
```

**Search pipeline**:
1. **Collect** results from multiple sources in parallel (ThreadPoolExecutor):
   - Canonical index (keyword matching from `CANONICAL.md`)
   - Tag index (grep-based matching from sharded `TAG_INDEX_A-M.md` / `TAG_INDEX_N-Z.md`)
   - Vector search (11 parallel Supabase RPC calls across all tables)
   - GraphRAG (community-based knowledge graph search)
   - Filesystem search (filename matching)
   - SQLite/Exocortex (local FTS5 search)
2. **Fuse** results using RRF with `k=60` and per-source weights
3. **Rerank** (optional) for final ordering
4. **Cache** results in semantic query cache (LRU + cosine similarity matching)

**Semantic Query Cache** (`src/athena/core/cache.py`):
- Exact match: MD5 hash of normalized query -> O(1) lookup
- Semantic match: Cosine similarity against cached query embeddings (threshold 0.90)
- TTL: 24 hours, max 100 entries, LRU eviction
- Disk-persistent (JSON file at `.agent/state/search_cache.json`)

### 7. Boot & Session Lifecycle -- `src/athena/boot/loaders/memory.py`

The `MemoryLoader` class handles session startup:

1. **`recall_last_session()`**: Finds the most recent session log, displays its focus and any deferred/pending action items.
2. **`create_session()`**: Creates a new session log file via a scripts module.
3. **`capture_context()`**: Outputs current date/time with timezone and week number.
4. **`prime_semantic()`**: Runs a "recent session context" query against Supabase to warm up the vector pipeline.
5. **`prewarm_search_cache()`**: Pre-runs 3 common queries ("protocol", "session", "user profile") to populate the semantic cache.
6. **`display_learnings_snapshot()`**: Shows recent user preferences from `USER_PROFILE.yaml` and recent entries from `SYSTEM_LEARNINGS.md`.

### 8. Exocortex -- Local Knowledge Base

An optional ~6GB SQLite FTS5 database built from DBPedia/Wikipedia abstracts:
- Download: `exocortex.py download` (~900MB compressed)
- Index: `exocortex.py index` (parses BZ2 TTL triples -> SQLite FTS5)
- Query: ~0.002s per search (vs 1-2s for API calls)
- Graceful degradation: If `exocortex.db` doesn't exist, the system skips it silently.

### 9. Configuration & Directory Structure -- `src/athena/core/config.py`

The config module defines a unified memory topology:

**Core Directories** (mapped to Supabase tables):
```python
CORE_DIRS = {
    "sessions": SESSIONS_DIR,              # .context/memories/session_logs/
    "case_studies": MEMORIES_DIR / "case_studies",
    "protocols": AGENT_DIR / "skills" / "protocols",
    "capabilities": AGENT_DIR / "skills" / "capabilities",
    "workflows": AGENT_DIR / "workflows",
    "system_docs": FRAMEWORK_DIR / "v8.2-stable" / "modules",
}
```

**Extended Directories** (additional knowledge silos):
- `analysis/`, `Marketing/`, `proposals/`, `Winston/` -> mapped to case_studies or system_docs tables
- `.athena/`, `.projects/`, research, specs -> system_docs

**Additional Memory Files**:
- `.athena/memory/USER_PROFILE.yaml` -- Structured user preferences
- `.athena/memory/SYSTEM_LEARNINGS.md` -- Tabular learning log
- `.context/CANONICAL.md` -- Canonical knowledge index
- `.context/TAG_INDEX_A-M.md` / `TAG_INDEX_N-Z.md` -- Sharded tag indexes

---

## Novel Patterns

### 1. Progressive Distillation with Token Budget Enforcement

The most innovative pattern is the **4-stage progressive distillation pipeline** with a hard 15K token cap:

```
Conversation -> Session Log (15%) -> activeContext.md (5%) -> userContext.md (0.1%)
```

This ensures the agent's boot cost stays O(1) regardless of how many sessions have occurred. The "operating band" oscillates between ~10K and ~15K tokens naturally, with auto-compaction triggering at the upper bound. This is a fundamentally different approach from systems that accumulate unlimited context.

### 2. O(1)/O(N) Tiered Change Detection

The DeltaManifest's 3-tier detection (existence -> size+mtime -> SHA-256) is a well-engineered optimization. Most files pass the O(1) quick check, avoiding expensive hash computation. This is borrowed from build-system design (like Make's timestamp checking) but applied to memory sync.

### 3. Thread-Local Supabase Clients

Using `threading.local()` for Supabase client instances prevents httpx connection state corruption during parallel search operations. This is a subtle but critical detail when running 11+ concurrent vector searches.

### 4. Persistent Embedding Cache with Background Saves

The `PersistentEmbeddingCache` uses daemon threads for disk writes, preventing blocking on I/O during embedding lookups. Combined with MD5-keyed caching, this avoids redundant API calls to Gemini for previously-seen content.

### 5. Semantic Query Cache with Cosine Similarity Matching

The `QueryCache` goes beyond exact-match caching -- it finds semantically similar previous queries using cosine similarity (threshold 0.90) on their embeddings. This means "what is caching" and "explain caching" can share cached results.

### 6. Reciprocal Rank Fusion (RRF) with Domain-Specific Weights

Rather than relying on a single retrieval method, Athena fuses results from 15+ sources (vectors, tags, canonical, filesystem, GraphRAG, exocortex) using weighted RRF. The weights are tuned per-domain (case studies and sessions weighted 3.0, exocortex 1.5), reflecting empirical relevance.

### 7. Auto-Enrichment Database Triggers

Supabase triggers automatically populate `auto_tags` and `updated_at` on every INSERT/UPDATE, reducing client-side bookkeeping and ensuring metadata consistency.

### 8. Exocortex as Offline Grounding Layer

Using a local 6GB Wikipedia/DBPedia SQLite database for fact-checking is a creative approach to reducing hallucination without API costs. The graceful degradation pattern (silently skip if absent) keeps it optional.

### 9. Deferred Action Item Handoff

The boot loader's `recall_last_session()` specifically parses session logs for "Pending" action items and surfaces them prominently. This creates a cross-session continuity mechanism beyond just loading context.

---

## Comparison Points

### Athena vs. File-Based `.claude/memory/` Approach

| Dimension | Athena | Our `.claude/memory/` System |
|-----------|--------|-------------------------------|
| **State Storage** | 4 markdown files (Memory Bank) | `activeContext.md` + `knowledge.md` + daily logs |
| **Semantic Search** | Supabase pgvector (cloud) | Graphiti MCP (knowledge graph) |
| **Change Tracking** | DeltaManifest (size/mtime/hash) | Git (implicit via commits) |
| **Boot Cost** | ~10K-15K tokens, hard-capped | Variable, depends on file sizes |
| **Token Management** | Progressive distillation with auto-compaction | Manual management, compaction via summary |
| **Embedding Model** | Gemini gemini-embedding-001 (3072d) | Graphiti-managed (opaque) |
| **Cache Layer** | Persistent LRU + semantic similarity | None explicit |
| **Offline Knowledge** | Exocortex (SQLite FTS5, Wikipedia) | None |
| **Search Fusion** | RRF across 15+ sources | Single source (Graphiti) |
| **Session Continuity** | Deferred action item parsing + Memory Bank | `<- CURRENT` marker in PIPELINE.md |
| **Schema** | 8 typed Supabase tables with triggers | Flat files + Graphiti graph |
| **Sync Model** | Filesystem -> Supabase (one-directional) | Files are source of truth (no sync needed) |
| **Multi-Agent** | Not explicitly addressed in memory layer | Agent Teams with shared file-based context |
| **Compaction** | Automatic at 15K token threshold | Manual (relies on CC's compaction + hooks) |

### Strengths of Athena's Approach
1. **Token-bounded boot**: The 15K hard cap with auto-compaction is more reliable than hoping files stay small.
2. **Multi-source search fusion**: RRF across 15+ sources provides higher recall than single-source search.
3. **Persistent caching at every layer**: Embedding cache, query cache, and search cache reduce latency and API costs.
4. **Typed knowledge tables**: Sessions, protocols, case studies each have dedicated schemas vs. flat files.

### Strengths of Our `.claude/memory/` Approach
1. **No external dependencies**: Files are the source of truth; no Supabase, no API keys needed.
2. **Git-native**: Changes are tracked by git, providing full history and rollback.
3. **Multi-agent coordination**: Agent Teams can read/write shared files; Athena's memory is single-agent.
4. **Graphiti knowledge graph**: Richer relationship modeling than flat vector similarity.
5. **Simplicity**: No sync engine, no manifest, no embedding cache to maintain.

---

## Potential Improvements for Our System

### High Priority (High Impact, Feasible)

1. **Token Budget Enforcement for activeContext.md**
   - Implement a ~10K token hard cap on `activeContext.md` with automatic compaction.
   - Athena's progressive distillation is elegant: recent entries stay detailed, older ones get compressed.
   - **Implementation**: A pre-compact hook that measures token count and trims oldest entries when exceeding threshold.

2. **Persistent Semantic Query Cache**
   - Add a query cache for Graphiti that avoids re-searching the same or similar queries.
   - Athena's dual-mode cache (exact hash + cosine similarity) is particularly clever.
   - **Implementation**: JSON file at `.claude/memory/cache/query_cache.json` with TTL and LRU eviction.

3. **Deferred Action Item Parsing**
   - On session start, parse `activeContext.md` for uncompleted "Next" items and surface them prominently.
   - Currently we load context but don't parse it for actionable continuity items.
   - **Implementation**: Add parsing logic to session-start sequence in CLAUDE.md instructions.

### Medium Priority (Moderate Impact)

4. **Typed Knowledge Categories**
   - Instead of a single `knowledge.md`, consider splitting into typed files: `patterns.md`, `gotchas.md`, `decisions.md` (partially done via ADR).
   - Athena's separation of protocols, case studies, capabilities maps well to different knowledge types.
   - Each type could have different retention/compaction rules.

5. **Change Detection for Memory Files**
   - Before syncing to Graphiti, check if files actually changed (size/mtime/hash).
   - Avoids redundant `add_memory` calls that waste API tokens.
   - **Implementation**: Simple JSON manifest tracking last-synced hash per file.

6. **Search Result Fusion**
   - When querying for context, combine Graphiti results with file-based grep/glob results using a lightweight RRF.
   - Currently we only query Graphiti or files, not both fused together.

### Lower Priority (Nice to Have)

7. **Embedding Cache for Graphiti**
   - If Graphiti supports custom embeddings, cache them locally to reduce API calls.
   - Athena's `PersistentEmbeddingCache` pattern is directly reusable.

8. **Memory Bank Template Standardization**
   - Adopt Athena's 4-pillar structure more formally:
     - `activeContext.md` (already exists -- keep as-is)
     - `userContext.md` (currently part of knowledge.md or implicit)
     - `productContext.md` (currently implicit in CLAUDE.md)
     - `systemPatterns.md` (partially exists as knowledge.md)

9. **Session Log Progressive Distillation**
   - Daily logs (`daily/YYYY-MM-DD.md`) could be auto-compacted after N days, with key insights migrated to `knowledge.md`.
   - Prevents daily log directory from growing unbounded.

10. **Local Offline Knowledge Base**
    - An exocortex-like local knowledge store could be useful for projects with large documentation sets.
    - Could index project docs, API references, or framework documentation into SQLite FTS5 for instant lookup.

---

## Summary

Athena's memory system is a **production-grade, multi-layered architecture** designed for 1000+ session continuity. Its core insight is the separation of state (Memory Bank markdown) from recall (Supabase vectors), connected by a delta-syncing engine with comprehensive change detection. The progressive distillation pipeline with token budgets ensures O(1) boot cost regardless of session count, while the hybrid RAG search fuses 15+ retrieval sources for high recall.

The most transferable patterns for our system are: (1) token budget enforcement with auto-compaction, (2) persistent semantic query caching, and (3) deferred action item parsing for cross-session continuity. These can be implemented incrementally without requiring the full Supabase infrastructure.
