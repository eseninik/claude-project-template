# Typed Memory System

> Structured, searchable knowledge base for agents. Replaces unstructured notes with categorized, deduplicated memory files.

## What Is Typed Memory

Typed memory splits project knowledge into **semantic categories**, each stored in a dedicated file under `.claude/memory/`:

| Category | File | Purpose |
|----------|------|---------|
| Knowledge | `knowledge.md` | Patterns, gotchas, pitfalls, and recurring insights |
| Daily Logs | `daily/*.json` | Per-session structured logs of work done |

## Why Typed Memory Over a Single File

`activeContext.md` is a session bridge: Did / Decided / Learned / Next. It captures the *last session's state* but loses history.

Typed memory is the **knowledge base**:
- **Structured**: JSON and markdown with semantic sections, not free-form text
- **Searchable**: agents can grep for specific patterns or file entries
- **Deduplicated**: same pattern is recorded once, not repeated every session
- **Cumulative**: grows over time instead of being overwritten each session

Both systems coexist:
- `activeContext.md` = session handoff (short-term, overwritten)
- Typed memory = knowledge base (long-term, append-only with dedup)

## How Agents Use Typed Memory

### At Session START (MANDATORY — before any work)

MUST read these files for context before beginning work:

```
1. .claude/memory/knowledge.md       — learn established patterns and avoid known pitfalls
2. .claude/memory/activeContext.md   — pick up from last session
```

This gives the agent a complete picture without needing to re-explore the codebase.

### DURING Session

As you discover new information:

- **Discovered a pattern?** Note it; append to knowledge.md at session end
- **Hit a gotcha?** Note it; append to knowledge.md at session end
- **Working with teammates?** Include relevant typed memory sections in their prompts

### At Session END (MANDATORY — BLOCKING before commit)

Before committing or exiting, MUST update typed memory. These steps are BLOCKING — do NOT commit without them:

1. **knowledge.md** — append new patterns and gotchas under the right section:
   ```markdown
   ## Coding Patterns
   - All API endpoints use `@validate_input` decorator for request validation
   - Database queries use repository pattern via `src/db/repos/`

   ## Environment Gotchas
   - Windows: use `node + full JS path` for LSP — bare commands cause ENOENT
   ```

2. **Daily log** — update today's log with what happened:
   ```
   .claude/memory/daily/2026-02-18.md
   ```

3. **activeContext.md** — update Did/Decided/Learned/Next as always

## Daily Log Format

For each working day, create or update a daily log:

```markdown
# 2026-02-18

## What Happened
- Implemented login endpoint
- Added JWT token generation
- Created integration tests

## Discoveries
- Auth module uses bcrypt for password hashing
- Token expiry is configured in src/config.py

## What Worked
- Using repository pattern for DB access simplified testing

## What Failed
- Initial attempt to mock JWT directly — had to mock at config level instead

## Recommendations
- Consider adding refresh token support in next iteration
```

Daily logs are stored in `.claude/memory/daily/{YYYY-MM-DD}.md`. Old logs can be moved to `.claude/memory/archive/` when no longer needed for active context.

## Deduplication Rules

Before appending a pattern or gotcha:

1. **Read the existing file** first
2. **Check if a similar entry already exists** (same concept, even if worded differently)
3. **If duplicate**: skip it, or update the existing entry if the new version is better
4. **If new**: append under the correct section heading
5. **Never create duplicate sections** — always append to existing ones

Example dedup check:
```
Existing: "- All API endpoints use @validate_input decorator"
New:      "- Endpoints validate input with @validate_input"
→ DUPLICATE — skip the new entry
```

## Memory Injection into Teammate Prompts

When spawning teammates, include relevant typed memory sections in their prompt. Use the teammate-prompt-template.md and add a `## Context from Typed Memory` section:

```markdown
## Context from Typed Memory

### Relevant Patterns (from knowledge.md)
- All endpoints use @validate_input decorator
- Database queries use repository pattern

### Known Gotchas (from knowledge.md)
- bcrypt.hashpw requires bytes, not str
```

Only include sections relevant to the teammate's task. Do not dump the entire memory.

## Integration with activeContext.md

| Aspect | activeContext.md | Typed Memory |
|--------|-----------------|--------------|
| Scope | Last session only | All sessions cumulative |
| Format | Free-form Did/Decided/Learned/Next | Structured categories |
| Lifecycle | Overwritten each session | Append-only with dedup |
| Purpose | Session handoff | Knowledge base |
| Read when | Session start | Session start |
| Write when | Session end | Session end |

Both are updated at session end. activeContext.md captures *what just happened*. Typed memory captures *what we learned*.

## Integration with Graphiti

When Graphiti (semantic search MCP) is available:

- **Graphiti is PRIMARY** — use it for semantic search, relationship queries, context retrieval
- **Typed memory is the FILE-BASED FALLBACK** — always maintained regardless of Graphiti availability
- **Sync direction**: agents update typed memory files; Graphiti indexes them automatically
- **When Graphiti is unavailable**: typed memory provides full functionality via file reads and grep

This ensures the knowledge base is never lost, even without external services.

## File Locations Summary

```
.claude/memory/
  activeContext.md          — session bridge
  knowledge.md              — patterns + gotchas combined
  daily/                    — per-session JSON logs
    .gitkeep
  archive/                  — archived old sessions
    .gitkeep
```

## Quick Reference for Agents

```
SESSION START:
  read .claude/memory/knowledge.md
  read .claude/memory/activeContext.md

SESSION END:
  update activeContext.md with Did/Decided/Learned/Next
  update daily/{YYYY-MM-DD}.md with what happened
  update knowledge.md if new patterns/gotchas discovered (dedup first)
```
