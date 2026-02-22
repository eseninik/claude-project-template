# Our Memory System — Comprehensive Audit

> Audit date: 2026-02-22
> Auditor: system-auditor agent
> Purpose: Establish baseline for comparison with OpenClaw memory system

---

## Architecture Overview

```
+------------------------------------------------------------------+
|                    CLAUDE.md (Always in Context)                   |
|  Behavioral rules enforce memory read/write at key moments:       |
|  Session Start | After Compaction | Phase Transition | Before Commit |
+-------+---------------------+--------------------+---------------+
        |                     |                    |
        v                     v                    v
+----------------+   +------------------+   +------------------+
| Layer 1:       |   | Layer 2:         |   | Layer 3:         |
| File-Based     |   | Graphiti KG      |   | Pipeline State   |
| Typed Memory   |   | (Semantic MCP)   |   | (work/)          |
+----------------+   +------------------+   +------------------+
| activeContext  |   | FalkorDB graph   |   | PIPELINE.md      |
| patterns.md    |   | add_memory()     |   | STATE.md         |
| gotchas.md     |   | search_nodes()   |   | attempt-history  |
| codebase-map   |   | search_facts()   |   | gate-results/    |
| session-insights|  | get_episodes()   |   | complexity-*.md  |
+----------------+   +------------------+   +------------------+
        |                     |                    |
        v                     v                    v
+------------------------------------------------------------------+
|                 Enforcement Layer (CLAUDE.md Rules)                |
|  BLOCKING RULES | FORBIDDEN LIST | AUTO-BEHAVIORS | HARD CONSTRAINTS |
+------------------------------------------------------------------+
        |
        v
+------------------------------------------------------------------+
|                 Agent Support Infrastructure                      |
|  Agent Registry (.claude/agents/registry.md)                      |
|  Focused Prompts (.claude/prompts/*.md)                           |
|  Recovery Manager (work/attempt-history.json)                     |
|  Complexity Assessment (.claude/guides/complexity-assessment.md)  |
+------------------------------------------------------------------+
```

**Design philosophy:** Rule-driven behavioral enforcement via CLAUDE.md. The system relies on
the agent reading and following markdown instructions — there is NO programmatic enforcement
(no hooks, no middleware, no code that forces memory operations). Everything is "honor system"
backed by strongly-worded BLOCKING labels and FORBIDDEN lists.

---

## Memory Layer 1: File-Based Typed Memory (.claude/memory/)

### activeContext.md

- **What it stores:** Session bridge document — Did/Decided/Learned/Next format for the most recent session, plus historical session log entries, recent decisions table, active questions, and next steps.
- **When loaded:** MANDATORY at session start (step 1 of Session Start protocol). Also after compaction (step 5 of After Compaction protocol).
- **When updated:** MANDATORY before every commit (blocking rule). Updated with Did/Decided/Learned/Next after every task completion.
- **Format:** Markdown with structured sections — Current Focus, Recent Decisions (table), Active Questions (checklist), Learned Patterns, Next Steps, Auto-Generated Summaries, Session Log (chronological entries).
- **Current state:** 369 lines. Contains detailed session logs going back to 2026-01-29. The file is large and growing — older session entries are never archived or pruned.
- **Strengths:**
  - Very detailed historical record
  - Human-readable, git-trackable
  - Good "what happened last session" context
- **Weaknesses:**
  - Grows without bound — no pruning mechanism in practice
  - "Session bridge" semantics are unclear — it functions more as a full project journal
  - Session Log entries are not machine-parseable (freeform markdown)
  - The "Auto-Generated Summaries" section exists but has no content — the hook system that populated it was removed
  - No schema validation — contents vary between sessions based on what the agent chose to write

### patterns.md

- **What it stores:** Reusable coding, architecture, and testing patterns discovered during work.
- **When loaded:** MANDATORY at session start.
- **When updated:** At session end, append new patterns (dedup first). At phase transitions (Phase Transition Protocol step 3).
- **Format:** Markdown with section headers (Coding Patterns, Architecture Patterns, Testing Patterns). Each pattern is a bullet with When/Pattern/Verified structure.
- **Current state:** Nearly empty — only 1 test pattern from 2026-02-18. Despite 20+ sessions logged in activeContext.md, almost no patterns have been recorded.
- **Strengths:**
  - Good conceptual design — semantic categories for different pattern types
  - Deduplication rules documented
- **Weaknesses:**
  - Extremely underutilized — 1 entry across entire project history
  - Agents consistently skip updating this file despite BLOCKING rules
  - No enforcement mechanism beyond CLAUDE.md text
  - Sections are empty templates — never populated in practice
  - The guide says "batch-update at session end" but this rarely happens

### gotchas.md

- **What it stores:** Known pitfalls, warnings, non-obvious behaviors that cause bugs.
- **When loaded:** MANDATORY at session start.
- **When updated:** At session end and phase transitions.
- **Format:** Markdown with sections (Environment Gotchas, Code Gotchas, Build/Deploy Gotchas).
- **Current state:** 2 entries — OpenRouter HTTP-Referer gotcha and Docker Desktop hang. Slightly better populated than patterns.md but still very sparse relative to the knowledge captured in activeContext.md session logs.
- **Strengths:**
  - When populated, provides immediately actionable warnings
  - Dated entries with verification status
- **Weaknesses:**
  - Same underutilization problem as patterns.md
  - Knowledge exists in activeContext.md session log but was never extracted to gotchas.md
  - Code Gotchas and Build/Deploy Gotchas sections completely empty
  - No automated extraction — relies entirely on agent discipline

### codebase-map.json

- **What it stores:** JSON map of project files, their purposes, categories, and relationships.
- **When loaded:** At session start (per typed memory guide).
- **When updated:** At session end, append new file discoveries.
- **Format:** JSON with `_schema`, `_usage`, `files` object (keyed by path), and `last_updated`.
- **Current state:** Contains exactly 1 entry (`scripts/ralph.sh` — which was subsequently DELETED). The map is not only sparse but stale/incorrect.
- **Strengths:**
  - JSON format is machine-parseable
  - Supports rich metadata per file (purpose, category, key_exports, depends_on)
- **Weaknesses:**
  - 1 entry for a project with 100+ files — virtually unused
  - The single entry references a deleted file (ralph.sh was removed in CLEANUP phase)
  - No agent has ever added meaningful entries despite the guide requiring it
  - No validation — can contain stale/incorrect entries indefinitely
  - Never queried in practice (agents use Glob/Grep instead)

### session-insights/

- **What it stores:** Per-session structured JSON logs with subtasks completed, discoveries, patterns found, gotchas encountered, recommendations.
- **When loaded:** Not explicitly loaded at session start (optional reference).
- **When updated:** At session end (optional — "for complex sessions").
- **Format:** JSON files named `{date}-{topic}.json`.
- **Current state:** Empty (only .gitkeep exists). Zero session insight files have ever been created.
- **Strengths:**
  - Good schema design with structured fields
  - Machine-parseable, could feed analytics
- **Weaknesses:**
  - Never used — 0 files across entire project history
  - Marked "optional" in the guide, which means agents always skip it
  - No tooling consumes these files even if they existed
  - Adds complexity without delivering value in current form

---

## Memory Layer 2: Graphiti Knowledge Graph

### Integration Architecture

- **Backend:** FalkorDB (Redis-compatible graph database) running in Docker
- **Interface:** MCP server (`graphiti-mcp`) exposing tools via HTTP at `localhost:8000/mcp/`
- **LLM dependency:** Uses OpenRouter/OpenAI for embeddings and entity extraction
- **Data model:** Episodes (raw knowledge), Nodes (entities), Facts (relationships between entities)
- **Group isolation:** `group_id` parameter namespaces knowledge per project

### What Is Stored

Episode types defined in guide:
- `session_insight` — session learnings
- `codebase_discovery` — file/module knowledge
- `pattern` — coding conventions
- `gotcha` — pitfalls
- `task_outcome` — approach results
- `qa_result` — QA findings

### When Queried

- MANDATORY at session start (3 Graphiti queries per Session Start protocol)
- MANDATORY after compaction (steps 3-4 of After Compaction protocol)
- Between pipeline phases (Phase Transition Protocol step 4)

### When Written

- At session end (After Task Completion steps 3-4)
- Between pipeline phases (Phase Transition Protocol step 4)
- After significant discoveries

### Current State

- **Docker setup:** Configured and running (docker-compose-falkordb.yml)
- **MCP config:** Registered in `~/.claude.json`
- **Actual data:** Currently EMPTY. The team lead confirmed Graphiti has no facts or nodes stored. Despite being set up and working (write/read cycle verified on 2026-02-19), no persistent knowledge has accumulated.
- **OpenRouter gotcha:** Required HTTP-Referer header fix in factories.py (documented in gotchas.md)

### Strengths

- Semantic search (embedding-based similarity, not keyword matching)
- Cross-session persistence independent of file state
- Cross-project potential (different group_ids)
- Temporal awareness — can track when facts were created/invalidated
- Entity relationship mapping — can answer "what is related to X?"
- Dual-layer design: Graphiti as PRIMARY search, file-based as FALLBACK

### Weaknesses

- **Currently empty** — all the infrastructure exists but contains zero useful knowledge
- **External dependency** — requires Docker, FalkorDB, LLM API key, network access
- **Fragile setup** — Windows PATH trap documented, OpenRouter header fix needed, restart required after container restart
- **No automatic population** — depends entirely on agent following CLAUDE.md rules
- **Write-order unclear in practice** — guide says "file-based first, then Graphiti" but agents often skip both
- **No bulk import** — guide references `scripts/import-memories-to-graphiti.py` but this script does not exist
- **Group ID management** — must be manually coordinated; docker-compose environment overrides env_file

---

## Memory Layer 3: Pipeline State (work/)

### PIPELINE.md

- **What it stores:** State machine encoding multi-phase development pipelines. Contains phase definitions with status, mode, attempt counts, transition rules, gate types, inputs/outputs, and checkpoint tags.
- **How it preserves state across compaction:** The `<- CURRENT` marker on the active phase header line enables O(1) recovery via grep. Phase status (PENDING/IN_PROGRESS/DONE) and attempt counts are persisted in the file, not in agent memory.
- **Format:** Markdown with structured phase blocks, each containing standardized fields.
- **Current state:** Active pipeline for "OpenClaw Memory System Analysis & Integration" — RESEARCH phase in progress.
- **Strengths:**
  - Survives compaction perfectly — agent can grep for `<- CURRENT` and resume
  - Self-documenting — phase transitions, gates, and modes are human-readable
  - Decisions section provides append-only audit trail
  - Execution Rules at bottom remind agent of the protocol
  - Conditional transitions (On PASS/FAIL/REWORK/BLOCKED) handle all outcomes
  - Bounded retry loops prevent infinite cycling
- **Weaknesses:**
  - Manual state management — agent must remember to move `<- CURRENT` and update Status
  - No validation that state transitions are legal (agent could set invalid status)
  - Large pipelines become unwieldy (9+ phases in template)
  - No machine-readable format — relies on markdown parsing conventions

### STATE.md

- **What it tracks:** Current task context — task name, pipeline reference, active phase, mode, status, plus key decisions table, deliverables, and problem/goal/approach description.
- **When updated:** After each phase completion, after task completion.
- **Current state:** Refers to previous completed pipeline (Ralph Loop extraction). Not yet updated for current OpenClaw pipeline.
- **Strengths:**
  - Compact summary of current project state
  - Readable at a glance
- **Weaknesses:**
  - Frequently stale — not always updated when PIPELINE.md changes
  - Duplicates information from PIPELINE.md (pipeline phase, status)
  - Deliverables section left as "TBD" and never filled in

### attempt-history.json

- **What it tracks:** Recovery Manager data — failed attempt approaches, outcomes, errors, keywords, circular fix detection, good commit hashes.
- **When updated:** After each subtask attempt (success or failure). Good commits recorded on success.
- **Current state:** Empty template — no attempts or good commits recorded.
- **Strengths:**
  - Enables circular fix detection (Jaccard similarity on keyword sets)
  - Bounded retries (5 max per subtask)
  - Prompt injection for retries provides previous attempt context
  - Good commit tracking enables safe rollbacks
- **Weaknesses:**
  - Never used in practice (empty across entire project history)
  - Relies on agent discipline to record attempts
  - No automated recording — manual JSON editing
  - Keywords extraction is subjective — different agents extract different keywords

---

## Context Injection Mechanisms

### CLAUDE.md Rules

The entire memory system is enforced through CLAUDE.md behavioral rules. Key enforcement mechanisms:

1. **Summary Instructions (top of file):** 12 compaction-survival rules including memory reload, pipeline resume, Graphiti queries, verification gates.

2. **AUTO-BEHAVIORS:** Four mandatory protocols:
   - Session Start (8 steps, includes memory + Graphiti + pipeline)
   - Before Code Changes (2 steps)
   - After Task Completion (9 steps, BLOCKING)
   - On Architecture Decision (3 steps)

3. **BLOCKING RULES:** 8 blocking gates including:
   - Before Commit: update activeContext.md + stage it
   - Before "done": MANDATORY verification gate
   - After IMPLEMENT: QA gate
   - On Retry: Recovery Manager

4. **HARD CONSTRAINTS:** 12 constraints including:
   - "Never commit without updating memory"
   - "Never skip Graphiti queries"
   - "Never recover after compaction without memory"

5. **FORBIDDEN list:** 12 forbidden behaviors including:
   - Starting work without reading memory
   - Finishing work without updating memory
   - Skipping Graphiti queries

6. **CONTEXT LOADING TRIGGERS:** 16 situation-specific triggers that tell the agent which guide to load.

### Session Start Protocol

Step-by-step what happens (MANDATORY):

```
1. Read .claude/memory/activeContext.md        -- session bridge
2. Read .claude/memory/patterns.md             -- typed memory
   Read .claude/memory/gotchas.md              -- typed memory
3. Query Graphiti:
   - search_memory_facts("recent session insights", max_facts=5)
   - search_memory_facts("known gotchas and pitfalls", max_facts=5)
   - search_nodes(<current task description>, max_nodes=5)
4. Read work/STATE.md                          -- project state
5. IF work/PIPELINE.md exists with <- CURRENT  -- resume pipeline
6. IF work/attempt-history.json exists         -- load recovery context
7. IF unfinished work -> announce continuation
8. ELSE -> announce readiness
```

Steps 1-3 are explicitly marked "NOT optional."

### After Compaction Protocol

Step-by-step recovery:

```
1. Re-read work/PIPELINE.md — find <- CURRENT phase
2. Re-read .claude/memory/activeContext.md + patterns.md + gotchas.md
3. Query Graphiti:
   - search_memory_facts(query=<current task>, max_facts=10)
   - search_nodes(query=<current task>, max_nodes=10)
4. Re-read work/STATE.md
5. Check phase Mode: if AGENT_TEAMS -> create team
6. Continue execution from <- CURRENT
7. DO NOT restart from beginning
```

Warning message: "FAILURE TO RELOAD MEMORY AFTER COMPACTION = CONTEXT LOSS = BUGS"

### Phase Transition Protocol

Between pipeline phases:

```
1. Git commit checkpoint: git add -A && git commit + git tag
2. Quick insight extraction:
   - What worked in this phase?
   - What failed or required multiple attempts?
   - New patterns discovered?
   - New gotchas to record?
3. Update typed memory:
   - patterns.md (append, deduplicate)
   - gotchas.md (append, deduplicate)
   - codebase-map.json (new files)
4. Save to Graphiti: add_memory(name="phase_{PHASE}_insight", ...)
5. Context refresh: Re-read PIPELINE.md + STATE.md + typed memory
6. Advance <- CURRENT marker
```

---

## Strengths

### 1. Compaction Resilience
The `<- CURRENT` marker in PIPELINE.md is a genuinely clever mechanism. It survives compaction because CLAUDE.md (always in context) tells the agent to re-read PIPELINE.md and grep for the marker. This is the strongest part of the system and works reliably.

### 2. Multi-Layer Redundancy
Three independent memory layers (file-based, Graphiti, pipeline state) provide defense-in-depth. If one fails, the others still function. The file-based layer requires zero external dependencies.

### 3. Human-Readable, Git-Trackable
All memory is markdown/JSON stored in the repository. Changes are visible in git diffs, reviewable in PRs, and portable across machines. No opaque binary formats or external databases required for core functionality.

### 4. Comprehensive Enforcement Rules
CLAUDE.md contains extensive, overlapping enforcement:
- Summary Instructions (survives compaction)
- AUTO-BEHAVIORS (positive instructions)
- BLOCKING RULES (gates)
- HARD CONSTRAINTS (restrictions)
- FORBIDDEN list (anti-patterns)
This redundancy increases the probability that at least one mention survives attention decay.

### 5. Structured Pipeline State Machine
PIPELINE.md is a well-designed state machine with conditional transitions, bounded retries, quality gates, and mode declarations. It handles complex multi-phase workflows with clear escalation paths.

### 6. Agent Team Integration
The system includes memory injection into teammate prompts via `## Context from Typed Memory` sections. The agent registry maps 24 agent types to specific memory levels (none/patterns/full).

### 7. Dual Memory Strategy
Typed memory (cumulative knowledge base) vs activeContext.md (session bridge) is a sound architectural separation. One captures "what we know" (patterns, gotchas), the other captures "what just happened."

### 8. Recovery Manager Design
The circular fix detection algorithm (Jaccard similarity on keywords) is thoughtful. Bounded retries with escalation prevent infinite loops. Good commit tracking enables safe rollbacks.

---

## Weaknesses

### 1. Zero Programmatic Enforcement (Critical)
The entire system relies on the LLM agent voluntarily following CLAUDE.md rules. There is:
- No code that forces memory reads at session start
- No code that forces memory writes before commit
- No validation that memory files were actually updated
- No hooks (explicitly removed — ADR decision)
- No middleware, no CI checks, no pre-commit validation

**Evidence of failure:** patterns.md has 1 entry, gotchas.md has 2 entries, codebase-map.json has 1 stale entry, session-insights/ is empty — all despite 20+ documented sessions. The rules say MANDATORY but compliance is clearly low.

### 2. Knowledge Stays in activeContext.md (Critical)
The session log in activeContext.md contains rich knowledge — patterns, gotchas, architectural decisions — but this knowledge is never extracted into the typed memory files. The "Learned" sections of session logs contain exactly the content that should be in patterns.md and gotchas.md, but the extraction step is consistently skipped.

**Root cause:** The extraction requires extra effort at session end when the agent is typically wrapping up. There is no automated tooling to assist with extraction.

### 3. Graphiti Is Empty Despite Working Infrastructure (High)
Graphiti was set up on 2026-02-19 (OpenRouter fix, write/read cycle verified). Three days later, it contains zero facts and zero nodes. The infrastructure cost (Docker, FalkorDB, LLM API) yields zero retrieval value because nothing was ever stored persistently.

### 4. activeContext.md Grows Without Bound (Medium)
At 369 lines, activeContext.md is already large. Session log entries are never archived. Over time, this file will become so large that agents waste context window on old session logs that are no longer relevant. The system has an `archive/` directory mentioned in questions but no archival process.

### 5. No Schema Validation (Medium)
Memory files have no schema validation. Agents can write whatever format they choose:
- codebase-map.json could receive malformed JSON
- patterns.md entries vary in format between sessions
- activeContext.md has no enforced structure
- attempt-history.json relies on agents producing valid JSON

### 6. Duplicate State (Medium)
STATE.md and PIPELINE.md contain overlapping information (phase, status, mode). activeContext.md also captures phase status in its "Current Focus" section. When one is updated and others are not, inconsistencies arise. STATE.md currently references a completed pipeline while PIPELINE.md has a new active one.

### 7. No Semantic Search Over Local Files (Medium)
File-based memory relies on exact-match grep or manual lookup. There is no local vector search or embedding-based retrieval over .claude/memory/ files. Graphiti provides semantic search but is external and currently empty.

### 8. Memory System Complexity (Medium)
The memory system involves 7+ files across 3 layers, 4 protocols (session start, after compaction, phase transition, after task), and 6 enforcement mechanisms. This complexity itself is a source of non-compliance — agents may not process all rules due to attention limits.

### 9. No Cross-Project Learning in Practice (Low)
Graphiti supports cross-project learning via group_ids, but:
- Graphiti is empty
- File-based memory is project-local
- No mechanism to share patterns.md/gotchas.md between projects
- The MEMORY.md auto-memory file provides some cross-project persistence but is unstructured

### 10. Session Insights Never Used (Low)
The session-insights/ directory with its JSON schema is pure overhead — never populated, never consumed. It adds to documentation and cognitive load without delivering value.

---

## Comparison Points for OpenClaw

### 1. Enforcement Mechanism
- **Our system:** Pure CLAUDE.md behavioral rules (honor system)
- **Compare:** Does OpenClaw use any programmatic enforcement? Pre-commit hooks? Middleware? Schema validation? If OpenClaw has any automated enforcement, it would be a significant advantage.

### 2. Memory Population Rate
- **Our system:** Very low — typed memory files nearly empty despite extensive usage
- **Compare:** How well-populated are OpenClaw's memory stores? What drives population (automated vs manual)?

### 3. Knowledge Extraction
- **Our system:** No automated extraction — agents must manually copy insights from session logs to typed memory
- **Compare:** Does OpenClaw have automated insight extraction? LLM-powered summarization? Automatic pattern detection?

### 4. Compaction Resilience
- **Our system:** Strong — `<- CURRENT` marker + CLAUDE.md rules
- **Compare:** How does OpenClaw handle context compaction? Is it better or worse?

### 5. Semantic Search
- **Our system:** Graphiti (external, empty) + grep (keyword only)
- **Compare:** Does OpenClaw have local vector search? Embedding-based retrieval? How does it find relevant past knowledge?

### 6. Memory File Growth
- **Our system:** Unbounded growth in activeContext.md, no archival
- **Compare:** Does OpenClaw have pruning, archival, or summarization of old memory?

### 7. Schema/Validation
- **Our system:** None — freeform markdown
- **Compare:** Does OpenClaw enforce memory schemas? Validate formats?

### 8. Cross-Session Continuity
- **Our system:** activeContext.md (session bridge) + Graphiti (empty) + MEMORY.md (auto-memory)
- **Compare:** How does OpenClaw maintain continuity between sessions? Is it more reliable?

### 9. Agent Coordination Memory
- **Our system:** Agent registry with memory injection levels (none/patterns/full), teammate prompt template with typed memory section
- **Compare:** How do OpenClaw agents share context? Is there shared memory between parallel agents?

### 10. Pipeline State Management
- **Our system:** Markdown state machine with conditional transitions, quality gates, bounded retries
- **Compare:** Does OpenClaw have equivalent pipeline/workflow state management? How does it track multi-phase work?

### 11. Recovery and Debugging Memory
- **Our system:** Recovery Manager with attempt tracking, circular fix detection, rollback — but never used in practice
- **Compare:** Does OpenClaw have attempt tracking? How does it handle repeated failures?

### 12. Memory Architecture Simplicity
- **Our system:** Complex — 7+ files, 3 layers, 4 protocols, 6 enforcement mechanisms
- **Compare:** Is OpenClaw's memory architecture simpler? Does simplicity improve compliance?

---

## Summary Statistics

| Metric | Value | Assessment |
|--------|-------|------------|
| Memory files defined | 7+ (activeContext, patterns, gotchas, codebase-map, session-insights, STATE, PIPELINE) | High design complexity |
| Memory files actively used | 2 (activeContext.md, PIPELINE.md) | 28% utilization |
| Graphiti nodes stored | 0 | Infrastructure without data |
| Graphiti facts stored | 0 | Infrastructure without data |
| patterns.md entries | 1 | Near-zero knowledge capture |
| gotchas.md entries | 2 | Minimal knowledge capture |
| codebase-map.json entries | 1 (stale) | Unused and incorrect |
| session-insights/ files | 0 | Completely unused |
| Session log entries (activeContext) | 20+ | Well-maintained |
| CLAUDE.md enforcement rules | ~40 rules across 6 mechanisms | Extensive but voluntary |
| Programmatic enforcement | 0 hooks, 0 validators, 0 checks | Pure honor system |
| Pipeline compaction survival | Reliable | Strongest feature |
| Agent types in registry | 24 | Comprehensive |
| Overall compliance rate | ~30-40% (estimated from file state) | Below design intent |

---

## Key Takeaway

The system has **excellent design** but **poor execution**. The architecture is thoughtful — typed memory categories, dual-layer redundancy, semantic search, pipeline state machines, recovery management. But almost all of this infrastructure sits empty because there is no mechanism to ensure agents actually populate it. The only reliably maintained files are activeContext.md (because it is the most visible and frequently referenced) and PIPELINE.md (because pipeline execution depends on it directly).

The fundamental gap is: **knowledge that exists in activeContext.md session logs never gets extracted into the structured memory files designed to hold it.** The system was designed to separate "session bridge" from "knowledge base" but in practice only the session bridge gets updated.
