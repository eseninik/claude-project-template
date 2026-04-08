---
name: semantic-search
description: >
  Semantic search across all memory layers using ChromaDB embeddings.
  Finds memories by meaning, not keywords. Adapted from MemPalace.
  Use when grep/keyword search fails to find relevant context, when searching
  across sessions ("what did we discuss about X"), or for deep memory retrieval.
  Do NOT use for simple file lookup (use Glob), current session context (use activeContext.md),
  or structured queries (use knowledge-graph skill).
roles: [coder, planner, qa-reviewer, insight-extractor]
---

# Semantic Search

Search across all Claude Code memory layers by **meaning**, not keywords.
Backed by ChromaDB embeddings. Adapted from [MemPalace](https://github.com/milla-jovovich/mempalace).

## When to Use

| Situation | Use this? | Better alternative |
|-----------|-----------|-------------------|
| "What did we discuss about auth redesign?" | Yes | -- |
| Keyword search returned nothing relevant | Yes | -- |
| Deep memory retrieval across sessions | Yes | -- |
| Finding a specific file by name | No | Glob |
| Current session context | No | activeContext.md |
| Structured pattern lookup | No | knowledge.md / grep |
| Graph-based entity queries | No | knowledge-graph skill |

## Semantic vs Keyword Search

**Grep/keyword** finds exact text matches. It misses:
- Paraphrased concepts ("auth middleware rewrite" vs "security layer refactor")
- Related context across different files and sessions
- Historical discussions where different words described the same idea

**Semantic search** finds meaning-similar content. It costs:
- ChromaDB dependency (`pip install chromadb>=0.5.0,<0.7`)
- Index build time (first run indexes all sources)
- Storage (~50-200MB in `~/.claude/memory/search_index/`)

## Commands

### Index (build/rebuild the search index)

```bash
# Full reindex -- all sources
py -3 .claude/scripts/semantic-search.py index

# Index only one source
py -3 .claude/scripts/semantic-search.py index --source knowledge
py -3 .claude/scripts/semantic-search.py index --source daily
py -3 .claude/scripts/semantic-search.py index --source observations
py -3 .claude/scripts/semantic-search.py index --source context
py -3 .claude/scripts/semantic-search.py index --source sessions
```

### Search (find memories by meaning)

```bash
# Basic search
py -3 .claude/scripts/semantic-search.py search "why did we choose structlog"

# Limit results
py -3 .claude/scripts/semantic-search.py search "deployment pipeline" --limit 10

# Filter by source
py -3 .claude/scripts/semantic-search.py search "auth" --source sessions
py -3 .claude/scripts/semantic-search.py search "gotcha" --source knowledge
```

### Status (check index health)

```bash
py -3 .claude/scripts/semantic-search.py status
```

## Sources Indexed

| Source | Files | Chunking Strategy |
|--------|-------|-------------------|
| knowledge | `.claude/memory/knowledge.md` | Split on `###` headers |
| daily | `.claude/memory/daily/*.md` | Split on `##` headers |
| observations | `.claude/memory/observations/*.md` | Each file = one chunk |
| context | `.claude/memory/activeContext.md` | Split on `##` headers |
| sessions | `~/.claude/projects/*/sessions/*.jsonl` | Exchange pairs (user + assistant) |

Chunk size: 800 chars with 100 char overlap (MemPalace defaults).

## Integration with Memory Decay

Combine with the memory decay system for time-aware retrieval:

1. **Semantic search** finds relevant memories by meaning
2. **Check `verified:` date** on knowledge.md entries to assess freshness
3. **Use `memory-engine.py knowledge-touch`** to refresh patterns you actually used

## Output Format

Results include:
- **Source** and **filename** for traceability
- **Section header** when available
- **Similarity score** (0.0 = unrelated, 1.0 = exact match)
- **Verbatim text** -- never summaries (MemPalace principle)

## Prerequisites

```bash
pip install chromadb>=0.5.0,<0.7
```

ChromaDB is optional. Without it, the script exits with install instructions.
Index is stored at `~/.claude/memory/search_index/` (persistent across sessions).
