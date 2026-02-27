# A8: Athena MCP Server & Tools Architecture

> Analysis of Project Athena's MCP tool server, 9 tools, 2 resources, heartbeat daemon, latency management, diagnostic relay, and flight recorder.

---

## 1. MCP Server Architecture

**File**: `src/athena/mcp_server.py`
**Framework**: FastMCP v2.0+ (Python)
**Transport**: stdio (default for IDE integration) or SSE (optional, for remote/multi-client)
**Version**: 1.1.0

### Server Initialization

Athena uses `FastMCP` to define the MCP server with a descriptive `instructions` field that tells the AI client what the server does. This instruction string is sent to the model as part of the MCP handshake, guiding the model on when and how to use each tool.

```python
mcp = FastMCP(
    name="athena",
    version="1.1.0",
    instructions="Project Athena MCP Server -- a sovereign personal intelligence..."
)
```

### Architecture Diagram (from docs)

```
MCP Client (IDE)  -->  stdio/SSE  -->  MCP Server (FastMCP)
                                          |
                                   Permission Gate
                                          |
                                     Tool Router
                                  (9 tools, 2 resources)
                                          |
                                    Athena SDK (core)
                              search | sessions | governance
                              health | config   | permissions
```

### Key Architectural Decisions

1. **Permission-gated tools**: Every tool calls `get_permissions().gate("tool_name")` before executing. This is a centralized access-control layer.
2. **Tags on tools**: Each tool has MCP `tags` (e.g., `{"read", "memory", "search"}`) enabling clients to filter/discover tools by capability.
3. **Governance integration**: Search tools report to the Governance Engine (Triple-Lock protocol) to track whether searches were performed before checkpoints.
4. **Dual transport**: stdio for local IDE integration (Claude Desktop, Antigravity), SSE for remote multi-client scenarios.

---

## 2. The 9 MCP Tools

### Tool 1: `smart_search` (Hybrid RAG)

**Tags**: `read`, `memory`, `search`
**Permission**: READ | **Sensitivity**: INTERNAL

**Purpose**: Primary search tool. Runs hybrid RAG across 6+ retrieval sources with Reciprocal Rank Fusion (RRF).

**Parameters**:
- `query` (str): Search query
- `limit` (int, default 10): Max results
- `strict` (bool): Filter low-confidence results
- `rerank` (bool): Apply LLM-based cross-encoder reranking

**Implementation** (`src/athena/tools/search.py` -- 800+ lines):

The search pipeline runs 6 collectors in parallel using `ThreadPoolExecutor`:
1. **Canonical** -- Searches the CANONICAL.md constitution file
2. **Tags** -- Searches tag index files (A-M, N-Z splits)
3. **Vectors** -- Queries vector embeddings (Supabase/ChromaDB) with subtypes (case_study, session, protocol, graphrag, etc.)
4. **GraphRAG** -- Searches knowledge graph communities
5. **SQLite** -- Full-text search on local SQLite index
6. **Filenames** -- Fuzzy filename matching

Results are fused via **Weighted RRF** with per-source weights:
```python
WEIGHTS = {
    "case_study": 3.0,   # Highest weight for case studies
    "session": 3.0,       # And session logs
    "protocol": 2.8,      # Protocols highly valued
    "graphrag": 2.5,      # GraphRAG entities
    "tags": 2.2,
    "canonical": 2.0,
    "vector": 1.8,        # Generic vectors lower
    "sqlite": 1.5,        # Lowest for full-text
}
RRF_K = 60  # RRF smoothing constant
```

**"God Mode"**: A `GOD_MODE = True` flag enables aggressive latency optimization (parallel execution of all collectors, early exits).

**Reranking** (`src/athena/tools/reranker.py`): Optional cross-encoder reranking using `cross-encoder/ms-marco-MiniLM-L6-v2` from sentence-transformers. Lazy-loaded to avoid startup cost.

### Tool 2: `agentic_search` (RAG v2)

**Tags**: `read`, `memory`, `search`, `admin`
**Permission**: READ | **Sensitivity**: INTERNAL

**Purpose**: Multi-step query decomposition for complex, multi-part queries. This is the "agentic" upgrade to `smart_search`.

**Parameters**:
- `query` (str): Complex search query
- `limit` (int, default 10): Max results
- `validate` (bool): Cosine-validate results against original query

**Pipeline**: Decompose -> Parallel Retrieve -> Validate -> Synthesize

**Implementation** (`src/athena/tools/agentic_search.py`):

1. **Decomposition** (rule-based NLP, no LLM):
   - Multi-question detection ("What X and how Y?")
   - Conjunction/comma splitting ("risk and psychology")
   - Keyword cluster extraction (fallback for dense queries)
   - Always includes original query for recall
   - Caps at 4 sub-queries

2. **Parallel Retrieval**: Runs each sub-query through the full `run_search()` pipeline (which itself runs 6 collectors in parallel). This means up to 4x6 = 24 parallel retrieval operations.

3. **Validation**: Cosine similarity between each result's embedding and the original query embedding. Threshold: 0.25 (fail-open if embedding fails).

4. **Score Boosting**: Results found by multiple sub-queries get a 1.1x score multiplier. Provenance tracked per result.

**Design Decision**: No LLM for decomposition. This is "fast, free, deterministic" -- pure regex/NLP. This contrasts with typical agentic RAG systems that use an LLM planner.

### Tool 3: `quicksave`

**Tags**: `write`, `session`, `checkpoint`
**Permission**: WRITE | **Sensitivity**: INTERNAL

**Purpose**: Save a timestamped checkpoint to the current session log. The primary "write" tool -- Athena's equivalent of our `activeContext.md` updates.

**Parameters**:
- `summary` (str): What was accomplished/decided
- `bullets` (list[str], optional): Specific items to record

**Governance Integration**: Before saving, checks Triple-Lock compliance:
- Was semantic search performed this exchange?
- Was web search performed?
- If either missing -> returns TRIPLE-LOCK VIOLATION warning (but still saves)
- After save, resets exchange integrity state

### Tool 4: `health_check`

**Tags**: `read`, `system`, `health`
**Permission**: READ | **Sensitivity**: PUBLIC

**Purpose**: Audit system health for Vector API and Database subsystems.

**Returns**: Per-subsystem status (PASS/FAIL) and overall status.

### Tool 5: `recall_session`

**Tags**: `read`, `session`, `memory`
**Permission**: READ | **Sensitivity**: INTERNAL

**Purpose**: Retrieve the most recent session log content (tail N lines).

**Parameters**:
- `lines` (int, default 50): Lines from end of log to return

**Secret Mode**: If active, content is auto-redacted before returning.

### Tool 6: `governance_status`

**Tags**: `read`, `system`, `governance`
**Permission**: READ | **Sensitivity**: INTERNAL

**Purpose**: Check Triple-Lock governance state -- whether semantic search and web search have been performed in the current exchange.

**Returns**: Boolean flags for each search type, integrity score, compliance status.

### Tool 7: `list_memory_paths`

**Tags**: `read`, `system`, `config`
**Permission**: READ | **Sensitivity**: PUBLIC

**Purpose**: List all active memory directories that Athena indexes. Helps the AI understand what knowledge domains are available.

**Returns**: Core directories, extended directories, active count.

### Tool 8: `set_secret_mode`

**Tags**: `admin`, `security`, `mode`
**Permission**: ADMIN

**Purpose**: Toggle "Secret Mode" (demo/external mode). When active:
- Only PUBLIC tools accessible
- INTERNAL/SECRET tools blocked
- Content auto-redacted (API keys -> `[REDACTED]`)

**Use Case**: Screen sharing during demos, external pair-programming, client presentations.

### Tool 9: `permission_status`

**Tags**: `read`, `system`, `security`
**Permission**: READ

**Purpose**: Show the full permission state: caller level, secret mode status, accessible/blocked tools, and tool manifest.

---

## 3. MCP Resources (2)

### Resource 1: `athena://session/current`

Returns the full content of the active session log file. Read-only access to session state.

### Resource 2: `athena://memory/canonical`

Returns the content of CANONICAL.md -- Athena's "constitution" document. This is the foundational identity/rules document. Content is redacted in secret mode.

---

## 4. Permissioning Layer

**File**: `src/athena/core/permissions.py`

### Architecture

Three-layer security model:

1. **Capability Tokens** (escalating levels):
   - `READ` -- Query/read data
   - `WRITE` -- Modify session logs, checkpoints
   - `ADMIN` -- Modify config, clear caches
   - `DANGEROUS` -- Delete data, run shell commands (future)

2. **Sensitivity Labels** (data classification):
   - `PUBLIC` -- Safe for demos, external sharing
   - `INTERNAL` -- Normal operational data
   - `SECRET` -- Credentials, finances, PII

3. **Action Types** (per-tool access control):
   - `ALLOW` -- Run without approval
   - `ASK` -- Prompt for approval
   - `DENY` -- Block the action

### Tool Registry

Every tool is registered with its required permission level and sensitivity label:

```python
TOOL_REGISTRY = {
    "smart_search": {"permission": READ, "sensitivity": INTERNAL},
    "quicksave": {"permission": WRITE, "sensitivity": INTERNAL},
    "health_check": {"permission": READ, "sensitivity": PUBLIC},
    # ...
}
```

### Content Auto-Classification

Pattern-based classification of content:
- **SECRET**: Matches `api_key`, `password`, `SUPABASE_KEY`, `trading`, `.env`
- **INTERNAL**: Matches `session_log`, `canonical`, `memory_bank`
- Everything else: **PUBLIC**

### Audit Trail

Every permission check is logged with timestamp, action, target, and outcome. Auto-truncated at 1,000 entries (to 500).

---

## 5. Heartbeat Daemon

**File**: `src/athena/tools/heartbeat.py`
**Dependency**: `watchdog` library

### Concept

A read-only file watcher that auto-indexes new/modified markdown documents to Supabase. It acts as a **persistent background process** that keeps Athena's vector memory in sync with the local file system.

### Architecture

```
File System (CORE_DIRS + EXTENDED_DIRS)
    |
    v (watchdog observer)
DebouncedSyncHandler
    |
    v (5-second debounce window)
sync_file_to_supabase()
    |
    v
Supabase (table per directory)
```

### Key Features

1. **Debounced writes**: 5-second debounce window batches rapid edits into a single sync operation per file. Uses `threading.Timer` with cancel-and-reschedule pattern.

2. **Table routing**: Maps file paths to Supabase tables based on CORE_DIRS and EXTENDED_DIRS configuration. Each memory directory syncs to a specific table.

3. **Three modes**:
   - `--dry-run`: Log what would be synced without actually syncing
   - `--once`: Single scan of all files, sync unsynced ones, then exit
   - Default: Run as foreground daemon watching for changes

4. **Manifest-based deduplication** (scan_once mode): Tracks file hashes to skip unchanged files.

5. **Read-only constraint**: Never modifies source files. Only reads them and writes to Supabase + log.

6. **Markdown-only**: Only processes `.md` files. Skips hidden files and temp files.

### Statistics Tracking

Tracks synced/skipped/errors counts, reported on shutdown.

---

## 6. Latency Management

**File**: `src/athena/tools/latency.py`

### Purpose

Simple network health probe that measures latency to the Google Gemini API endpoint. Used to determine if the network connection is suitable for API-heavy operations.

### Classification Tiers

| Latency | Status |
|---------|--------|
| < 200ms | ULTRA-FAST |
| < 800ms | FAST |
| < 2000ms | SLOW |
| >= 2000ms | LAG |
| Error | OFFLINE |

### Usage in Search ("God Mode")

The search module has `GOD_MODE = True` which enables aggressive latency optimization:
- All 6 search collectors run in parallel (ThreadPoolExecutor)
- Timeouts on futures (8 seconds per sub-query in agentic search, 30 seconds overall)
- Fail-open: If a collector fails, it returns empty results rather than blocking

This is an **adaptive routing** approach: the system always tries the fastest path and gracefully degrades when subsystems are slow/offline.

---

## 7. Diagnostic Relay (Protocol 500)

**File**: `src/athena/core/diagnostic_relay.py`

### Concept

An automated error-capture system that generates structured, PII-sanitized GitHub issue drafts when exceptions occur. It's a "federated telemetry with sovereignty" approach -- the system captures diagnostics locally but never sends them anywhere automatically.

### Pipeline

```
Exception caught
    |
    v
capture_diagnostic()
    |-- Captures: traceback, exception type, module, context
    |-- Sanitizes PII using regex patterns
    |-- Adds: Athena version, Python version, OS, timestamp
    |
    v
generate_issue_draft()
    |-- Creates GitHub-flavored Markdown issue template
    |
    v
save_diagnostic_draft()
    |-- Saves to .agent/diagnostics/issue-{timestamp}-{type}.md
    |-- Human reviews and manually submits to GitHub
```

### PII Sanitization Patterns

| Pattern | Replacement |
|---------|-------------|
| `/Users/{name}` | `/Users/<REDACTED>` |
| Email addresses | `<EMAIL_REDACTED>` |
| `sk-*` API keys | `<API_KEY_REDACTED>` |
| Supabase keys | `<SUPABASE_KEY_REDACTED>` |
| IP addresses | `<IP_REDACTED>` |

### Decorator Integration

Provides a `@diagnostic_wrapper("module_name")` decorator for easy integration:

```python
@diagnostic_wrapper("sync.py")
def sync_file_to_supabase(file_path, table_name):
    ...  # Exceptions auto-captured and saved as issue drafts
```

### Key Design: Human-in-the-Loop

Diagnostics are saved locally. The human must review and manually submit to GitHub. This is privacy-first: no automated telemetry.

---

## 8. Flight Recorder (Black Box)

**File**: `src/athena/core/flight_recorder.py`

### Concept

An immutable, append-only action log for forensic auditing. Records every high-stakes tool call (Write, Delete, Git operations) as JSONL entries.

### Record Format

```json
{
    "timestamp": 1709000000.0,
    "time_str": "2024-02-27 00:00:00",
    "tool": "quicksave",
    "params": {"summary": "..."},
    "status": "initiated",
    "rationale": "User requested checkpoint",
    "pid": 12345
}
```

### Storage

- **File**: `.athena/flight_recorder.jsonl`
- **Format**: JSON Lines (one JSON object per line, append-only)
- **Fail-safe**: If logging fails, it prints a warning but does NOT crash the system

### Design Properties

1. **Immutable**: Append-only. No delete or update operations.
2. **Minimal overhead**: Simple file append, no database.
3. **PID tracking**: Records process ID for multi-process forensics.
4. **Rationale field**: Captures WHY an action was taken, not just what.

---

## 9. Non-MCP Tools (CLI/Internal Only)

These tools exist in the `tools/` directory but are NOT exposed as MCP tools:

### `content_gen.py` -- Marketing Asset Generator

Generates marketing copy (Carousell, LinkedIn, Twitter) from SEO keywords. Uses prompt templates based on "Protocol 272" (visceral copywriting) and "CS-240" (outcome positioning). Currently a prompt scaffolder (outputs prompts for manual LLM use).

### `macro_graph.py` -- Knowledge Graph Visualizer

Auto-generates a Mermaid diagram of the workspace structure at `.context/KNOWLEDGE_GRAPH.md`. Maps Core Identity, SDK, Memory, Skills, and Distribution nodes.

### `public_sync.py` -- Dependency-Aware Public Deployment

Syncs private documents to the Athena-Public GitHub repository:
1. Recursively follows markdown link dependencies
2. Sanitizes content (replaces absolute file:/// links with relative paths)
3. Strips PII
4. Maps private directories to public docs structure

### `athena_client.py` -- HTTP Client

Simple HTTP client for talking to a local Athena API server (health, context, agent/think endpoints). Used by the TUI dashboard.

### `athena_tui.py` -- Terminal UI Dashboard

Rich-based terminal dashboard showing:
- System health status
- Active memory bank content
- Component status
- Real-time polling with `rich.live`

### `reranker.py` -- Cross-Encoder Reranking

Not directly exposed as MCP tool, but called internally by `smart_search` when `rerank=True`. Uses `cross-encoder/ms-marco-MiniLM-L6-v2`.

---

## 10. Governance Engine (Triple-Lock Protocol)

**File**: `src/athena/core/governance.py`

### Concept

Enforces that every AI interaction cycle follows the pattern:
1. **Semantic Search** (query local knowledge base)
2. **Web Search** (query external sources)
3. **Quicksave** (checkpoint with both sources verified)

If quicksave is called without both searches performed, it flags a TRIPLE-LOCK VIOLATION.

### Doom Loop Detector

Borrowed from OpenCode (Feb 2026). Detects infinite retry loops:
- Tracks tool call signatures (tool_name + hash of args)
- If same signature appears 3+ times within 60-second window -> flagged as doom loop
- Acts as a circuit breaker for token-burning agentic failures

---

## 11. Comparison with Our MCP Usage

| Aspect | Athena | Our Template (Graphiti-only) |
|--------|--------|------------------------------|
| **MCP Framework** | FastMCP (Python) | External Graphiti MCP server |
| **Number of Tools** | 9 custom tools + 2 resources | ~8 Graphiti tools (add_memory, search_nodes, search_facts, etc.) |
| **Search** | Custom hybrid RAG (6 sources + RRF fusion + reranking) | Graphiti knowledge graph search |
| **Agentic Search** | Built-in query decomposition pipeline | Not available -- single queries only |
| **Permission System** | Full 4-tier capability tokens + 3-tier sensitivity + secret mode | None -- all tools open |
| **Governance** | Triple-Lock protocol (semantic + web search before save) | None -- no enforced workflow |
| **Audit/Logging** | Flight recorder (immutable JSONL) + diagnostic relay | None |
| **Background Sync** | Heartbeat daemon (file watcher -> Supabase auto-index) | No background processes |
| **Latency Mgmt** | Network health probe + God Mode parallel execution | No latency awareness |
| **Session State** | quicksave + recall_session via MCP | Manual activeContext.md updates |
| **Data Redaction** | Auto-PII sanitization + secret mode | None |
| **Custom Server** | Yes -- full custom FastMCP server | No -- using third-party MCP server |

### Key Gaps We Could Address

1. **Permission gating**: Athena gates every tool call through a permission layer. We have no access control on Graphiti operations.

2. **Governance workflow**: Athena's Triple-Lock ensures the AI doesn't save conclusions without first searching. We could implement similar gates (e.g., require search_memory_facts before add_memory).

3. **Flight recorder**: Athena logs all high-stakes operations immutably. We have no audit trail for memory operations.

4. **Heartbeat/auto-sync**: Athena's file watcher keeps memory in sync with the filesystem. Our memory updates are manual and explicit.

5. **Doom loop detection**: Athena detects and breaks infinite retry loops. We have retry limits in CLAUDE.md rules but no programmatic enforcement.

6. **Diagnostic relay**: Athena auto-generates PII-sanitized issue drafts from exceptions. We have no automated error reporting.

### Key Strengths of Our Approach

1. **Simplicity**: Graphiti MCP is a mature, maintained third-party server. Less code to maintain.

2. **Knowledge graph**: Graphiti's entity-relationship graph is more sophisticated than Athena's vector-only approach for relationship discovery.

3. **No infrastructure**: We don't need Supabase, ChromaDB, or other external services. Graphiti handles its own storage.

4. **Standard MCP protocol**: We consume a standard MCP server rather than building our own, making it easier to swap/upgrade.

---

## 12. Summary

Athena's MCP server is a **custom-built, permission-gated, governance-enforced tool server** exposing 9 tools and 2 resources. The architecture reflects a "sovereign personal intelligence" philosophy -- everything is self-hosted, privacy-first, and under full user control.

The most innovative aspects are:
- **Triple-Lock governance**: Enforcing a research-before-save workflow
- **Heartbeat daemon**: Background file-watching with debounced auto-indexing
- **Diagnostic relay**: PII-sanitized error capture with human-in-the-loop submission
- **Flight recorder**: Immutable action audit log
- **Permission/sensitivity layering**: Fine-grained access control with demo/secret mode
- **Doom loop detection**: Circuit breaker for runaway AI tool loops

The MCP server acts as the **single interface** between AI clients and Athena's capabilities, centralizing access control, governance, and audit in one place.

---

*Analysis completed: 2026-02-23*
*Sources: src/athena/mcp_server.py, src/athena/tools/*, src/athena/core/diagnostic_relay.py, src/athena/core/flight_recorder.py, src/athena/core/permissions.py, src/athena/core/governance.py, docs/MCP_SERVER.md*
