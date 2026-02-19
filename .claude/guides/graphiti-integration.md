# Graphiti Integration Guide

> Knowledge graph memory system for semantic cross-session and cross-project learning.

## 1. What is Graphiti?

Graphiti is a temporally-aware knowledge graph framework (by Zep, uses FalkorDB or Neo4j) that provides semantic search across sessions. It stores entities, relationships, and episodes — enabling agents to recall relevant context from past sessions without manually loading files.

**Core capabilities:**
- Entity storage and relationship mapping between code concepts
- Semantic search via embeddings (find relevant memories by meaning, not keywords)
- Cross-session persistence — insights survive compaction and session boundaries
- Cross-project learning — patterns discovered in one project benefit others

**Episode types** (units of stored knowledge):
- `session_insight` — what was learned during a coding session
- `codebase_discovery` — file purposes, module relationships, architecture notes
- `pattern` — coding patterns, conventions, successful approaches
- `gotcha` — pitfalls, warnings, things that break unexpectedly
- `task_outcome` — what approach worked/failed for specific task types
- `qa_result` — QA findings: bugs found, fixes applied, validation outcomes

**Interface:** MCP server that Claude Code agents call via standard MCP tools.

## 2. Architecture — Dual-Layer Memory

```
PRIMARY:   Graphiti (semantic search, cross-session, cross-project)
FALLBACK:  File-based typed memory (.claude/memory/*.md, zero dependencies)
```

**Write order:**
1. ALWAYS save to file-based memory first (guaranteed to work, no dependencies)
2. Then save to Graphiti if available (richer retrieval, semantic search)

**Read order:**
1. Query Graphiti for semantically relevant context
2. Load file-based memory for structured state (activeContext.md, STATE.md)

**Failure mode:** If Graphiti is unavailable, the system continues with file-based memory only. No degradation in core functionality — Graphiti is additive, not required.

## 3. Setup & Configuration

### Prerequisites

- Docker Desktop installed and running
- LLM API key (OpenAI recommended, or OpenRouter/Anthropic/Gemini/Groq)
- Git clone of Graphiti repo: `git clone --depth 1 https://github.com/getzep/graphiti.git ~/graphiti`

### Step 1: Create .env file

```bash
cd ~/graphiti/mcp_server
cp .env.example .env
# Edit .env — set at minimum:
```

```env
# LLM provider (OpenAI-compatible API)
OPENAI_API_KEY=your_key_here
OPENAI_API_URL=https://api.openai.com/v1  # or https://openrouter.ai/api/v1

# Graph namespace
FALKORDB_DATABASE=your_project_name
GRAPHITI_GROUP_ID=your-project

# Concurrency (adjust for your LLM provider rate limits)
SEMAPHORE_LIMIT=8
```

### Step 2: Start Docker container

```bash
cd ~/graphiti/mcp_server/docker
docker compose up -d
```

This starts a **single container** with FalkorDB + MCP server:
- MCP endpoint: `http://localhost:8000/mcp/`
- Health check: `http://localhost:8000/health`
- FalkorDB UI: `http://localhost:3000/`

### Step 3: Configure Claude Code MCP

Add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "type": "http",
      "url": "http://localhost:8000/mcp/"
    }
  }
}
```

## 4. Episode Types & Group Modes

### Episode Types

| Type | What It Stores | Example |
|------|---------------|---------|
| `session_insight` | Session learnings | "Discovered that auth module requires Redis connection" |
| `codebase_discovery` | File/module knowledge | "src/auth/jwt.py handles token refresh with 15min TTL" |
| `pattern` | Coding conventions | "All API routes use dependency injection via FastAPI Depends" |
| `gotcha` | Pitfalls and warnings | "Windows paths break if not normalized — use pathlib everywhere" |
| `task_outcome` | Task approach results | "TDD approach for parser refactor caught 3 edge cases early" |
| `qa_result` | QA findings | "Missing null check in user.email caused 500 on GET /profile" |

### Group Modes

- **PROJECT mode** (default): All tasks share project-wide context. Use for general project knowledge.
- **SPEC mode**: Each task/spec gets an isolated memory namespace. Use when tasks are independent and should not pollute each other's context.

Set group mode per task in pipeline configuration:
```
graphiti_group: project   # or "spec:{spec-id}"
```

## 5. Agent Integration

### Context Loading (MANDATORY at session start — if Graphiti available)

When an agent starts, MUST load relevant Graphiti context:

```
1. search_nodes(query=<task_description>, limit=10)
   → Get entity summaries relevant to the current task
2. search_facts(query=<task_description>, limit=10)
   → Get relationship facts relevant to the current task
3. get_episodes(type="pattern", limit=20)
   → Get known coding patterns for this project
4. get_episodes(type="gotcha", limit=20)
   → Get known pitfalls to avoid
5. get_episodes(type="session_insight", limit=3)
   → Get recent session history for continuity
6. Format results as markdown and prepend to agent prompt
```

### Memory Save (MANDATORY post-session — if Graphiti available)

After each session or significant work unit, MUST save to Graphiti:

```
1. Insight extractor analyzes session transcript
2. Extracted insights → add_episode(type="session_insight", content=...)
3. New patterns → add_episode(type="pattern", content=...)
4. New gotchas → add_episode(type="gotcha", content=...)
5. File discoveries → add_episode(type="codebase_discovery", content=...)
6. ALSO update file-based memory (.claude/memory/activeContext.md)
```

### MCP Tools Available to Agents

| Tool | Purpose |
|------|---------|
| `mcp__graphiti-memory__search_nodes` | Search entity summaries by semantic similarity |
| `mcp__graphiti-memory__search_facts` | Search relationship facts between entities |
| `mcp__graphiti-memory__add_episode` | Add new knowledge to the graph |
| `mcp__graphiti-memory__get_episodes` | Retrieve recent episodes by type |

## 6. Integration with File-Based Memory

Graphiti is the semantic search layer ON TOP OF file-based memory. Both layers are always maintained:

| Aspect | File-Based (.claude/memory/) | Graphiti |
|--------|------------------------------|----------|
| Availability | Always (zero deps) | When configured |
| Search | Exact match / manual lookup | Semantic similarity |
| Cross-project | No | Yes |
| Structure | Markdown files, JSON | Knowledge graph |
| Update trigger | Before every commit | Post-session extraction |
| Failure impact | Critical (breaks pipeline) | Non-critical (graceful fallback) |

**Migration path:** Existing file-based memories can be bulk-imported into Graphiti:
```bash
# Import existing memory files into Graphiti
python scripts/import-memories-to-graphiti.py .claude/memory/
```

## 7. Integration with Pipeline

Each pipeline phase benefits from Graphiti context:

| Phase | Graphiti Provides |
|-------|-------------------|
| SPEC | Similar past specs, requirement patterns |
| PLAN | Past task approaches, time estimates, gotchas |
| IMPLEMENT | Relevant file discoveries, coding patterns, past bugs |
| QA/REVIEW | Past QA findings, known bug patterns, validation approaches |
| Post-session | Automatic save of new insights, patterns, gotchas |

**Phase Transition Protocol integration:** Between phases, save to both memory layers — file-based (guaranteed) then Graphiti.

## 8. When to Use Graphiti vs File-Based Only

| Scenario | Recommendation |
|----------|----------------|
| Single project, < 10 sessions | File-based sufficient |
| Multiple projects, cross-learning needed | Graphiti recommended |
| Long-running project, 50+ sessions | Graphiti strongly recommended |
| Offline / minimal setup | File-based only |
| Team of developers sharing knowledge | Graphiti essential |
| CI/CD pipelines (no persistent state) | File-based only |

**Rule of thumb:** If you find yourself re-discovering the same patterns or gotchas across sessions, Graphiti will pay for itself quickly.

## 9. Troubleshooting

| Problem | Solution |
|---------|----------|
| Graphiti not connecting | Ensure Docker is running, check `curl http://localhost:8000/health` |
| Embedding dimension mismatch | Happens when changing embedding providers. Clear the DB and re-import. |
| Memory not being saved | Check MCP server logs: `docker compose logs` in mcp_server/docker/. |
| Slow queries | Reduce `limit` parameter. Check if embedding index needs rebuilding. |
| Duplicate episodes | Graphiti deduplicates by content hash. If seeing duplicates, check episode metadata. |
| Fallback not working | File-based memory is independent. If it fails, check file permissions on `.claude/memory/`. |

**Debug mode:** Set `GRAPHITI_DEBUG=true` to log all MCP calls and responses.

**Complete failure recovery:** If Graphiti DB is corrupted, delete and re-import from file-based memory. File-based memory is the source of truth.
