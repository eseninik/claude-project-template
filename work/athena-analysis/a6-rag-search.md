# A6: Athena RAG & Hybrid Search System Analysis

> **Analyst**: Research Agent (a6-rag-search)
> **Date**: 2026-02-23
> **Source**: github.com/winstonkoh87/Athena-Public

---

## Executive Summary

Athena implements a **multi-source hybrid RAG** system that fuses results from **8 distinct retrieval sources** using **Weighted Reciprocal Rank Fusion (RRF)** with optional **cross-encoder reranking**. The system also includes an **Agentic Search** layer for complex multi-part queries and integrates both **GraphRAG** (community-based) and **LightRAG** (Ollama-powered local graph). This is one of the most sophisticated open-source personal RAG architectures available.

---

## 1. Multi-Source Retrieval Architecture

Athena's search system (`src/athena/tools/search.py`) collects results from **8 parallel collectors**, each targeting a different data modality:

### 1.1 The 8 Retrieval Sources

| # | Source | Collector Function | What It Searches | Technology |
|---|--------|--------------------|------------------|------------|
| 1 | **Canonical Markdown** | `collect_canonical()` | CANONICAL.md curated index | Keyword density scoring (2+ keyword hits per line) |
| 2 | **Tag Index** | `collect_tags()` | TAG_INDEX_A-M.md / TAG_INDEX_N-Z.md | `grep -i` subprocess with sharded indexes |
| 3 | **Vector Memory** | `collect_vectors()` | 11 Supabase pgvector tables | Google `text-embedding-004` (3072-dim), cosine similarity |
| 4 | **GraphRAG** | `collect_graphrag()` | Communities + entities via knowledge graph | JSON community matching + ChromaDB entity vectors |
| 5 | **Filename Search** | `collect_filenames()` | Project filesystem | `find` command with OR keyword logic |
| 6 | **Framework Docs** | `collect_framework_docs()` | .framework/ and memory_bank/ dirs | File content scanning with keyword density |
| 7 | **SQLite Index** | `collect_sqlite()` | Local athena.db (files + tags) | SQLite LIKE queries on paths and tag names |
| 8 | **Exocortex** | `collect_exocortex()` | Wikipedia abstracts (exocortex.db) | SQLite FTS5 full-text search |

### 1.2 Vector Memory Sub-Types (11 Supabase Tables)

The vector source searches across **11 domain-specific tables** in parallel using `ThreadPoolExecutor`:

| Table | Search Function | Limit | Threshold |
|-------|----------------|-------|-----------|
| `protocols` | `search_protocols()` | 10 | 0.3 |
| `case_studies` | `search_case_studies()` | 10 | 0.3 |
| `sessions` | `search_sessions()` | 3-5 | 0.35 |
| `capabilities` | `search_capabilities()` | 3-5 | 0.3 |
| `playbooks` | `search_playbooks()` | 3-5 | 0.3 |
| `workflows` | `search_workflows()` | 3-5 | 0.3 |
| `entities` | `search_entities()` | 3-5 | 0.3 |
| `references` | `search_references()` | 3-5 | 0.3 |
| `frameworks` | `search_frameworks()` | 3-5 | 0.3 |
| `user_profile` | `search_user_profile()` | 3-5 | 0.3 |
| `system_docs` | `search_system_docs()` | 3-5 | 0.3 |

**Key Detail**: Vector results are **split by subtype** before RRF fusion, so each domain (e.g., `case_study`, `session`, `protocol`) gets its own weight in the fusion algorithm. This prevents high-volume domains from drowning out rarer but high-value matches.

### 1.3 Parallel Execution Architecture

```
User Query
    |
    v
[Embedding Generation] (text-embedding-004, 3072-dim)
    |
    v
[ThreadPoolExecutor (8 workers)]
    |--- collect_canonical()      --> keyword density
    |--- collect_tags()           --> grep subprocess
    |--- collect_vectors()        --> 11 parallel Supabase RPC calls
    |    |--- search_protocols()
    |    |--- search_case_studies()
    |    |--- search_sessions()
    |    |--- ... (8 more)
    |--- collect_graphrag()       --> subprocess to query_graphrag.py
    |--- collect_filenames()      --> find subprocess
    |--- collect_framework_docs() --> file scanning
    |--- collect_sqlite()         --> local SQLite queries
    |--- collect_exocortex()      --> FTS5 search
    |
    v
[Weighted RRF Fusion]
    |
    v
[Optional: Cross-Encoder Reranking]
    |
    v
[Confidence Filtering + Presentation]
```

**Timeout Strategy**: God Mode sets a 5-second hard timeout on all collectors (8s in normal mode). Timed-out sources are silently skipped.

---

## 2. RRF (Reciprocal Rank Fusion) Implementation

### 2.1 Standard RRF Formula

```
RRF_score(d) = SUM over sources: weight(s) * score_mod(d) * 1/(k + rank(d, s))
```

Where:
- `k = 60` (standard RRF constant from Cormack et al., 2009)
- `weight(s)` = source-specific weight (see table below)
- `score_mod(d)` = `0.5 + doc.score` (dynamic modifier, range 0.5-1.5)
- `rank(d, s)` = 1-indexed position in source's ranked list

### 2.2 Source Weight Configuration

Athena uses a **granular per-subtype weight system** with 17 distinct weights:

| Source | Weight | Rationale |
|--------|--------|-----------|
| `case_study` | **3.0** | Highest-value curated analysis |
| `session` | **3.0** | Conversational history (temporal continuity) |
| `protocol` | **2.8** | Reusable thinking patterns |
| `graphrag` | **2.5** | Structured knowledge clusters |
| `user_profile` | **2.5** | Personal context |
| `framework_docs` | **2.5** | Identity/system docs |
| `framework` | **2.3** | Core framework modules |
| `tags` | **2.2** | Explicit keyword matches |
| `canonical` | **2.0** | Curated single source of truth |
| `filename` | **2.0** | Literal file matching |
| `vector` | **1.8** | Generic vector matches |
| `capability` | **1.8** | Tool/skill definitions |
| `playbook` | **1.8** | Strategic guides |
| `workflow` | **1.8** | Automation scripts |
| `entity` | **1.8** | Named entities |
| `reference` | **1.8** | External citations |
| `system_doc` | **1.8** | System documentation |
| `sqlite` | **1.5** | Local fallback index |
| `exocortex` | **1.5** | Wikipedia abstracts |

### 2.3 Dynamic Score Modifier

Unlike pure RRF which only uses rank position, Athena adds a **dynamic score modifier**:

```python
score_mod = 0.5 + doc.score  # Range: 0.5 to 1.5
contrib = weight * score_mod * (1.0 / (k + rank))
```

This means a document with a high native similarity score (e.g., 0.9 cosine) gets a 1.4x multiplier vs. a document with 0.0 score getting only 0.5x. This is a notable deviation from standard RRF which is purely rank-based.

### 2.4 Confidence Levels

After fusion, results are categorized:

| Level | Threshold | Badge |
|-------|-----------|-------|
| HIGH | >= 0.03 | `[HIGH]` |
| MEDIUM | >= 0.02 | `[MED]` |
| LOW | < 0.02 | `[LOW]` |

In **strict mode**, results below MEDIUM are suppressed entirely.

---

## 3. Reranking System

### 3.1 Cross-Encoder Reranker

File: `src/athena/tools/reranker.py`

| Property | Value |
|----------|-------|
| **Model** | `cross-encoder/ms-marco-MiniLM-L6-v2` |
| **Library** | `sentence_transformers.CrossEncoder` |
| **Input** | (query, content) pairs |
| **Output** | Unbounded logit scores |
| **Top-K** | Configurable (default: 5) |

The reranker is **optional** (activated via `--rerank` flag). When active:
1. Takes top 25 RRF-fused candidates
2. Runs cross-encoder inference on all (query, content) pairs
3. Re-sorts by cross-encoder score
4. Returns top-k

### 3.2 RRF Pipeline Alternative Reranker

File: `scripts/core/retrieval/pipeline.py`

The formal `RRFPipeline` class has an alternative reranking strategy using **Gemini 1.5 Flash** as a reranker:

```python
model = genai.GenerativeModel("gemini-1.5-flash")
prompt = f'Rate the relevance of these documents to the query: "{query}"...'
```

This LLM-based reranker is used in the `scripts/core/retrieval/pipeline.py` formal pipeline but NOT in the main `search.py` production path. The production path uses the local cross-encoder.

---

## 4. Embedding Strategy

### 4.1 Primary: Google text-embedding-004

| Property | Value |
|----------|-------|
| **Model** | `text-embedding-004` (Google Gemini API) |
| **Dimensions** | 3072 (in Supabase), documented as 768 in some docs |
| **Max Input** | ~32,000 characters (truncated) |
| **Index Type** | IVFFlat (lists=100) |
| **Similarity** | Cosine distance (`<=>` operator) |
| **Storage** | Supabase pgvector (cloud) |
| **Cost** | Free tier (1,500 req/day) |

**Note**: The docs mention both 3072-dim (in SQL schema and VectorRAG docs) and 768-dim (in LightRAG config). The production system uses 3072-dim via Supabase.

### 4.2 Secondary: Ollama Local Embeddings (LightRAG)

| Property | Value |
|----------|-------|
| **Model** | `llama3.1:8b` (via Ollama) |
| **Dimensions** | 768 |
| **Max Tokens** | 8,192 |
| **Storage** | Local LightRAG graph store |

---

## 5. GraphRAG Integration

Athena has **three separate** graph-based retrieval mechanisms:

### 5.1 GraphRAG (JSON Communities + ChromaDB)

File: `scripts/core/retrieval/graphrag.py`, `.agent/scripts/query_graphrag.py`

- **Entity Extraction**: LLM-powered (Gemini Flash), ~$30-50 to build
- **Community Detection**: Leiden algorithm, ~1,460 auto-detected clusters
- **Storage**: `communities.json` (~800KB), `knowledge_graph.gpickle` (~46MB), ChromaDB (~78MB)
- **Query**: Tokenize query -> match against community keywords + ChromaDB entity vectors
- **Weight**: 2.5x in main search, 2.0x in formal pipeline

### 5.2 KNOWLEDGE_GRAPH.md Parser

File: `scripts/core/retrieval/graphrag.py` (KnowledgeGraphParser class)

- **Format**: Simple markdown with `[TYPE] name: description` entities
- **Relationships**: `source RELATION target` patterns (USES, DEPENDS_ON, etc.)
- **Query**: Token matching with multi-hop traversal (default 2 hops)
- **No LLM required**: Pure text parsing

### 5.3 LightRAG (Ollama-powered Local Graph)

File: `.agent/scripts/lightrag_wrapper.py`

- **Backend**: LightRAG library with Ollama (llama3.1:8b)
- **Modes**: local, global, hybrid, naive
- **Storage**: `.context/memory_bank/lightrag_store/`
- **Purpose**: Multi-hop reasoning on indexed markdown files
- **Fully local**: No API costs

---

## 6. Agentic Search

File: `src/athena/tools/agentic_search.py`

### 6.1 Architecture

A **4-phase pipeline** for complex multi-part queries:

```
Phase 1: DECOMPOSE (rule-based NLP, no LLM)
    |
    v
Phase 2: PARALLEL RETRIEVAL (each sub-query through full search pipeline)
    |
    v
Phase 3: VALIDATE (cosine similarity against original query, threshold 0.25)
    |
    v
Phase 4: SYNTHESIZE (merge, boost multi-source hits by 1.1x)
```

### 6.2 Query Decomposition Strategies

1. **Multi-question detection**: "What is X and how does Y?" -> 2 sub-queries
2. **Conjunction splitting**: "X and Y", "X vs Y", comma-separated -> 2-4 sub-queries
3. **Keyword clustering**: Dense single queries -> split tokens into 2 clusters
4. **Always includes original**: Full query is always a sub-query for recall

**Key Design Decision**: No LLM for decomposition -- rule-based NLP only. This is fast, free, and deterministic.

### 6.3 Validation

Results are validated against the original query embedding:
- Cosine similarity threshold: 0.25
- Below threshold: filtered out
- Fail-open: if embedding fails, keep the result

### 6.4 Multi-Source Boosting

Documents found by multiple sub-queries get a **1.1x score boost**:

```python
existing.rrf_score = max(existing.rrf_score, result.rrf_score) * 1.1
```

---

## 7. Caching System

### 7.1 Exact Cache

- Key: `"{query}|{limit}|{strict}|{rerank}"`
- Returns cached fused results on exact match

### 7.2 Semantic Cache

- Uses query embedding to find semantically similar cached queries
- Checked before running full search pipeline
- Prevents redundant searches for paraphrased queries

---

## 8. Fast Search (Reflex Tier)

File: `examples/scripts/fast_search.py`

A **lightweight <200ms** search tier for:
1. Exact filename matches (via `mdfind`/`fd`/`find`)
2. Tag lookups (via `rg`/`grep`)
3. UUID/ID matches (via `rg`/`grep`)

This bypasses the full RRF pipeline entirely for simple lookups.

---

## 9. Hybrid Router

File: `examples/scripts/hybrid_router.py`

Routes between local knowledge and web search:

| Classification | Trigger | Action |
|----------------|---------|--------|
| `local_only` | "protocol", "athena", "define" | Search Exocortex only |
| `web_only` | "latest", "news", "2026", "price" | Prompt user to search web (HITL) |
| `hybrid` | Default | Both local + manual web bridge |

**Unique**: Uses a Human-in-the-Loop (HITL) pattern where the user manually pastes web search results from Gemini/ChatGPT free tiers.

---

## 10. Comparison with Our Graphiti-Based Memory Search

### 10.1 Architecture Comparison

| Dimension | Athena (Hybrid RRF) | Our System (Graphiti) |
|-----------|---------------------|----------------------|
| **Graph Model** | Static markdown + JSON communities + LightRAG | Dynamic episodic knowledge graph (Neo4j) |
| **Retrieval Sources** | 8 parallel collectors | Single Graphiti search (nodes + facts) |
| **Fusion** | Weighted RRF (17 source weights) | Native Graphiti ranking |
| **Embedding Model** | text-embedding-004 (3072-dim) | Graphiti's built-in (configurable) |
| **Reranking** | Cross-encoder (ms-marco-MiniLM) | None (Graphiti internal) |
| **Temporal** | Session logs with dates | Episodic edges with temporal metadata |
| **Update Cost** | Manual sync pipeline | Real-time add_memory() |
| **Query Decomposition** | Agentic search (rule-based) | None built-in |
| **Storage** | Supabase + SQLite + ChromaDB + JSON | Neo4j graph database |
| **Caching** | Exact + semantic cache | None built-in |

### 10.2 What Athena Does Better

1. **Multi-source fusion**: 8 retrieval paths catch what others miss. The RRF fusion with per-subtype weights is mathematically principled and well-tuned.

2. **Agentic query decomposition**: Complex queries are broken into sub-queries and run in parallel. Our system relies on the caller to formulate good queries.

3. **Tiered latency**: Fast search (<200ms) for simple lookups, full pipeline (5-8s) for complex queries. Different quality levels for different needs.

4. **Caching layers**: Both exact and semantic caching prevent redundant expensive searches.

5. **Cross-encoder reranking**: The ms-marco cross-encoder significantly improves precision for the final top-k results.

6. **Exocortex (external knowledge)**: Wikipedia abstracts provide world knowledge grounding that pure project-memory systems lack.

### 10.3 What Graphiti Does Better

1. **Dynamic updates**: `add_memory()` instantly integrates new information without manual sync pipelines. Athena requires running `supabase_sync.py`.

2. **Temporal reasoning**: Graphiti's temporal metadata on facts allows "what was true at time T?" queries. Athena's temporal support is limited to session dates.

3. **Relationship-first**: Graphiti models relationships as first-class citizens (facts connecting entities). Athena's graph is secondary to its vector search.

4. **Simplicity**: Single API (`search_nodes`, `search_memory_facts`) vs. 8 collector functions + RRF fusion + reranking.

5. **Automatic entity extraction**: Graphiti extracts entities and relationships from unstructured text automatically. Athena's GraphRAG requires expensive one-time LLM processing.

6. **Contradiction handling**: Graphiti can mark facts as superseded when new conflicting information arrives. Athena has no built-in contradiction resolution.

### 10.4 Adoption Opportunities

| Athena Pattern | Applicability to Our System | Priority |
|----------------|----------------------------|----------|
| **RRF fusion of multiple sources** | Could wrap Graphiti nodes + facts + external search with RRF | Medium |
| **Agentic query decomposition** | Decompose complex queries before calling search_memory_facts | High |
| **Cross-encoder reranking** | Post-process Graphiti results with ms-marco reranker | Medium |
| **Tiered latency** | Fast path for simple lookups, full pipeline for complex | Low |
| **Semantic caching** | Cache Graphiti query results by embedding similarity | Medium |
| **Exocortex integration** | Add external knowledge source alongside Graphiti | Low |
| **Per-subtype weighting** | Weight different entity types differently in results | Medium |

---

## 11. Key Technical Insights

### 11.1 "God Mode" Latency Optimization

Athena has a `GOD_MODE = True` flag that aggressively reduces latency:
- Cuts per-table vector search limits from 5 to 3
- Reduces overall timeout from 8s to 5s
- Enables "Low Entropy Query" bypass (skips vectors for short generic queries)

### 11.2 Adaptive Vector Bypass

For short, generic queries (<5 words, no domain-specific terms), Athena **skips vector search entirely** and relies on tags + canonical + GraphRAG. This is a smart latency optimization since short queries often match well with keyword methods.

### 11.3 Domain Filtering

Vector results include a `domain` field (e.g., "personal", "technical"). By default, personal domain results are excluded unless `--include-personal` is passed. This prevents personal data from leaking into professional queries.

### 11.4 Score Modifier Innovation

The `score_mod = 0.5 + doc.score` addition to RRF is a pragmatic enhancement. Standard RRF is purely rank-based, which means a document at rank 1 with 0.95 similarity and a document at rank 1 with 0.31 similarity contribute equally. Athena's modifier breaks this tie, which is particularly valuable when source quality varies significantly.

### 11.5 Fail-Open Design

Every collector is wrapped in try/except and returns `[]` on failure. Timed-out collectors are silently skipped. This means the system degrades gracefully -- even if Supabase is down, tags + canonical + filenames still work.

---

## 12. File Reference Index

| File | Purpose | Lines |
|------|---------|-------|
| `src/athena/tools/search.py` | Main hybrid search orchestrator (8 collectors + RRF) | ~965 |
| `src/athena/tools/agentic_search.py` | Multi-step query decomposition + parallel search | ~280 |
| `src/athena/tools/reranker.py` | Cross-encoder reranking (ms-marco-MiniLM) | ~50 |
| `scripts/core/retrieval/pipeline.py` | Formal RRF pipeline class + AthenaRetriever | ~310 |
| `scripts/core/retrieval/graphrag.py` | KNOWLEDGE_GRAPH.md parser + graph search | ~190 |
| `examples/scripts/smart_search.py` | Legacy shim -> athena.tools.search | ~40 |
| `examples/scripts/fast_search.py` | <200ms reflex tier (filenames, tags, IDs) | ~120 |
| `examples/scripts/hybrid_router.py` | Local/Web query router (HITL bridge) | ~150 |
| `examples/scripts/reranker.py` | Standalone reranker module | ~60 |
| `.agent/scripts/lightrag_wrapper.py` | LightRAG integration (Ollama local graph) | ~100 |
| `.agent/scripts/query_graphrag.py` | JSON knowledge graph query interface | ~55 |
| `docs/SEMANTIC_SEARCH.md` | Triple-path retrieval documentation | ~150 |
| `docs/GRAPHRAG.md` | GraphRAG architecture + cost analysis | ~200 |
| `docs/VECTORRAG.md` | VectorRAG (Supabase pgvector) documentation | ~350 |
| `docs/KNOWLEDGE_GRAPH.md` | Compressed knowledge graph index | ~60 |

---

## 13. Summary Verdict

Athena's search system is a **production-grade hybrid RAG** with:
- **8 retrieval sources** running in parallel
- **Weighted RRF fusion** with 17 per-subtype weights and dynamic score modifiers
- **Cross-encoder reranking** for precision
- **Agentic query decomposition** for complex queries (no LLM cost)
- **3 graph engines** (JSON communities, KNOWLEDGE_GRAPH.md parser, LightRAG)
- **Tiered latency** (fast reflex + full pipeline)
- **Semantic + exact caching**
- **Graceful degradation** via fail-open design

The primary trade-off vs. Graphiti is **complexity vs. dynamism**: Athena has more retrieval paths but requires manual sync pipelines, while Graphiti offers real-time updates with simpler queries. The most transferable patterns are **agentic query decomposition**, **cross-encoder reranking**, and **per-subtype RRF weighting**.
