---
name: knowledge-graph
description: >
  Temporal knowledge graph for tracking entity relationships with time validity.
  SQLite-based, zero external dependencies. Adapted from MemPalace.
  Use when tracking project/API/tool relationships, when facts change over time,
  or when user says "add to graph" / "what do we know about X".
  Do NOT use for session memory (use activeContext.md) or patterns (use knowledge.md).
roles: [coder, planner, insight-extractor]
---

# Knowledge Graph Skill

Temporal entity-relationship graph stored in SQLite. Tracks **what** is connected to **what**, and **when** those connections were valid. Zero external dependencies.

## When to Use

- Tracking relationships between projects, APIs, tools, people
- Recording facts that change over time (e.g., "Bot X used auth v1 until March, then switched to v2")
- User says "add to graph", "what do we know about X", "track this relationship"
- Building project dependency maps
- Auditing what changed and when

## When NOT to Use

- Session context (use `activeContext.md`)
- Reusable patterns/gotchas (use `knowledge.md`)
- Temporary task state (use `work/STATE.md` or tasks)

## CLI Commands

All commands use: `py -3 .claude/scripts/knowledge-graph.py <command> [args]`

### Add an entity

```bash
py -3 .claude/scripts/knowledge-graph.py add-entity "LeadQualifier Bot" --type project
py -3 .claude/scripts/knowledge-graph.py add-entity "AmoCRM API" --type api
py -3 .claude/scripts/knowledge-graph.py add-entity "Redis" --type tool --properties '{"version": "7.2"}'
```

Types: `project`, `tool`, `api`, `person`, `concept`, `service`, `unknown`

### Add a relationship (triple)

```bash
py -3 .claude/scripts/knowledge-graph.py add-triple "LeadQualifier Bot" "uses" "AmoCRM API" --valid-from 2026-01
py -3 .claude/scripts/knowledge-graph.py add-triple "LeadQualifier Bot" "depends_on" "Redis" --valid-from 2026-02
py -3 .claude/scripts/knowledge-graph.py add-triple "Bot" "deployed_on" "Contabo VPS" --source-file deploy.yaml
```

Common predicates: `uses`, `depends_on`, `integrates`, `deployed_on`, `owned_by`, `replaces`, `extends`

### Query an entity

```bash
py -3 .claude/scripts/knowledge-graph.py query "LeadQualifier Bot"
py -3 .claude/scripts/knowledge-graph.py query "LeadQualifier Bot" --as-of 2026-02-15
py -3 .claude/scripts/knowledge-graph.py query "AmoCRM API" --direction incoming
```

### Query by relationship type

```bash
py -3 .claude/scripts/knowledge-graph.py query-rel "uses"
py -3 .claude/scripts/knowledge-graph.py query-rel "depends_on" --as-of 2026-03
```

### Invalidate a fact

```bash
py -3 .claude/scripts/knowledge-graph.py invalidate "Bot" "uses" "old_auth" --ended 2026-03
```

### Timeline

```bash
py -3 .claude/scripts/knowledge-graph.py timeline                    # all facts chronologically
py -3 .claude/scripts/knowledge-graph.py timeline "LeadQualifier Bot" # single entity
```

### Stats

```bash
py -3 .claude/scripts/knowledge-graph.py stats
```

### Export to markdown

```bash
py -3 .claude/scripts/knowledge-graph.py export
py -3 .claude/scripts/knowledge-graph.py export > /tmp/kg-snapshot.md  # save for prompt injection
```

## Python API

```python
from knowledge_graph import KnowledgeGraph

kg = KnowledgeGraph()  # default: ~/.claude/memory/knowledge_graph.sqlite3
kg.add_entity("Bot", entity_type="project")
kg.add_triple("Bot", "uses", "API", valid_from="2026-01")
results = kg.query_entity("Bot")
kg.invalidate("Bot", "uses", "old_thing", ended="2026-03")
md = kg.export_markdown()
```

## Storage

- Database: `~/.claude/memory/knowledge_graph.sqlite3`
- Uses SQLite WAL mode for concurrent reads
- Override with `--db /path/to/other.sqlite3`

## Integration with Memory System

The knowledge graph complements (does not replace) the existing memory files:

| What | Where |
|------|-------|
| Session state | `activeContext.md` |
| Patterns/gotchas | `knowledge.md` |
| Entity relationships | Knowledge Graph (this) |
| Daily logs | `daily/{date}.md` |

Use `export` to snapshot the graph into markdown for prompt injection when needed.
