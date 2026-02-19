# Typed Memory System

> Structured, searchable knowledge base for agents. Replaces unstructured notes with categorized, deduplicated memory files.

## What Is Typed Memory

Typed memory splits project knowledge into **four semantic categories**, each stored in a dedicated file under `.claude/memory/`:

| Category | File | Purpose |
|----------|------|---------|
| Codebase Map | `codebase-map.json` | What files exist, what they do, how they relate |
| Patterns | `patterns.md` | Recurring coding, architecture, and testing patterns |
| Gotchas | `gotchas.md` | Known pitfalls, warnings, non-obvious behaviors |
| Session Insights | `session-insights/*.json` | Per-session structured logs of work done |

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
1. .claude/memory/codebase-map.json  — understand project structure
2. .claude/memory/patterns.md        — learn established patterns
3. .claude/memory/gotchas.md         — avoid known pitfalls
4. .claude/memory/activeContext.md   — pick up from last session
```

This gives the agent a complete picture without needing to re-explore the codebase.

### DURING Session

As you discover new information:

- **Found a new important file?** Note it mentally; batch-update codebase-map at session end
- **Discovered a pattern?** Note it; append to patterns.md at session end
- **Hit a gotcha?** Note it; append to gotchas.md at session end
- **Working with teammates?** Include relevant typed memory sections in their prompts

### At Session END (MANDATORY — BLOCKING before commit)

Before committing or exiting, MUST update typed memory. These steps are BLOCKING — do NOT commit without them:

1. **Codebase Map** — add entries for any newly discovered/created files:
   ```json
   "files": {
     "src/auth/login.py": {
       "purpose": "Handles user authentication flow",
       "category": "auth",
       "key_exports": ["login_user", "verify_token"],
       "depends_on": ["src/db/users.py", "src/config.py"],
       "discovered_by": "session-2026-02-18"
     }
   }
   ```

2. **Patterns** — append new bullets under the right section:
   ```markdown
   ## Coding Patterns
   - All API endpoints use `@validate_input` decorator for request validation
   - Database queries use repository pattern via `src/db/repos/`
   ```

3. **Gotchas** — append new bullets under the right section:
   ```markdown
   ## Environment Gotchas
   - Windows: use `node + full JS path` for LSP — bare commands cause ENOENT
   ```

4. **Session Insights** — create a JSON file (optional, for complex sessions):
   ```
   .claude/memory/session-insights/2026-02-18-feature-auth.json
   ```

5. **activeContext.md** — update Did/Decided/Learned/Next as always

## Session Insights Format

For complex sessions, create a structured JSON log:

```json
{
  "session_id": "2026-02-18-feature-auth",
  "model": "claude-opus-4-6",
  "date": "2026-02-18",
  "duration_estimate": "~45 min",
  "subtasks_completed": [
    "Implemented login endpoint",
    "Added JWT token generation",
    "Created integration tests"
  ],
  "discoveries": [
    "Auth module uses bcrypt for password hashing",
    "Token expiry is configured in src/config.py"
  ],
  "patterns_found": [
    "All endpoints follow request -> validate -> service -> response pattern"
  ],
  "gotchas_encountered": [
    "bcrypt.hashpw requires bytes, not str — must encode first"
  ],
  "what_worked": [
    "Using repository pattern for DB access simplified testing"
  ],
  "what_failed": [
    "Initial attempt to mock JWT directly — had to mock at config level instead"
  ],
  "recommendations": [
    "Consider adding refresh token support in next iteration"
  ]
}
```

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

### Relevant Files (from codebase-map.json)
- `src/auth/login.py` — handles authentication flow
- `src/db/users.py` — user database operations

### Relevant Patterns
- All endpoints use @validate_input decorator
- Database queries use repository pattern

### Known Gotchas
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
  activeContext.md          — session bridge (existing)
  codebase-map.json         — file discovery map (new)
  patterns.md               — coding/arch/test patterns (new)
  gotchas.md                — known pitfalls (new)
  session-insights/         — per-session JSON logs (new)
    .gitkeep
    2026-02-18-example.json — example session log
```

## Quick Reference for Agents

```
SESSION START:
  read .claude/memory/codebase-map.json
  read .claude/memory/patterns.md
  read .claude/memory/gotchas.md
  read .claude/memory/activeContext.md

SESSION END:
  update codebase-map.json with new file discoveries
  append new patterns to patterns.md (dedup first)
  append new gotchas to gotchas.md (dedup first)
  optionally create session-insights/<date>-<topic>.json
  update activeContext.md with Did/Decided/Learned/Next
```
