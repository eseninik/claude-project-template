# A10: Context Engineering & Token Management Analysis

> **Source**: github.com/winstonkoh87/Athena-Public
> **Analyst**: Research Agent (Claude Opus 4.6)
> **Date**: 2026-02-23

---

## Executive Summary

Athena implements a sophisticated multi-layered context engineering system built around three core principles: (1) a hard-cap token budget with auto-compaction, (2) adaptive latency routing that loads context on-demand rather than all-at-once, and (3) an "exoskeleton architecture" that separates cognitive processing from I/O execution. The system evolved organically over 1000+ sessions and represents a mature approach to the fundamental LLM constraint: limited context windows must be managed as a non-renewable resource within each session.

---

## 1. Token Budget System

### 1.1 Architecture Overview

Athena's token budget is managed by `src/athena/boot/loaders/token_budget.py` and enforced via `src/athena/boot/constants.py`. The system defines:

| Constant | Value | Purpose |
|----------|-------|---------|
| `HARD_CAP` | 20,000 tokens | Triggers auto-compaction |
| `ECL` | 200,000 tokens | Effective Context Length (model budget) |
| `BOOT_SCRIPT_ESTIMATE` | 2,000 tokens | Fixed overhead for boot.py output |
| `SYSTEM_INSTRUCTIONS_ESTIMATE` | 3,000 tokens | IDE-injected system prompt |
| `MAX_COMPACT_PASSES` | 3 | Safety limit for compaction retries |

### 1.2 Boot Files (Memory Bank)

The "Memory Bank" consists of exactly three canonical files loaded at boot:

```python
BOOT_FILES = {
    "userContext.md": MEMORY_BANK_DIR / "userContext.md",
    "productContext.md": MEMORY_BANK_DIR / "productContext.md",
    "activeContext.md": MEMORY_BANK_DIR / "activeContext.md",
}
```

These live under `.context/memory_bank/`. The design goal is to keep total boot injection under 20K tokens (approximately 10K post-compaction target, 20K hard cap).

### 1.3 Token Counting

Uses `tiktoken` (cl100k_base encoding) with a fallback to `len(text) // 4` character-based estimation. This is a practical choice -- tiktoken is accurate but requires an external dependency.

### 1.4 The Budget Gauge

The `display_gauge()` function renders an ASCII progress bar:

```
0K ████████░░░░░░░ 20K
```

Color-coded: GREEN (under budget), RED (over cap). Displayed at the end of every boot sequence, providing immediate visibility into context health.

### 1.5 Auto-Compaction Flow

When boot tokens >= HARD_CAP:

1. Import `compact_active_context` from `.agent/scripts/compact_context.py`
2. Run up to 3 compaction passes (first normal, subsequent aggressive)
3. Re-measure after each pass
4. If still over budget after 3 passes, proceed with warning

**Key insight**: The compaction targets `activeContext.md` specifically -- this is the only file that grows unboundedly (the other two are relatively static).

### 1.6 How ~10K Boot Stays Constant

The mechanism is a feedback loop:

1. **userContext.md** and **productContext.md** are static (rarely change) -- they define user identity and project identity
2. **activeContext.md** is the only dynamic file -- it grows with each session
3. At boot, if total exceeds 20K, auto-compaction compresses activeContext.md
4. The compaction script (`compact_context.py`) implements three pruning strategies:
   - **Completed task pruning**: Only keeps last 3 `[x]` items in Active Tasks section
   - **Session marker pruning**: Only keeps last 3 `## Session XXXX Completed` markers
   - **Recent Context age pruning**: Removes entries older than 48 hours (24h in aggressive mode), caps at 5 entries (2 in aggressive)
5. Compacted items are summarized and moved to a "Recent Context" section before full archival to session logs

**Result**: Boot payload oscillates in a 10K-20K band. When it hits 20K, compaction pulls it back to ~10K.

---

## 2. Context Compaction Strategy

### 2.1 The compact_context.py Script

Three-phase compaction:

**Phase 1 -- Completed Task Pruning**:
- Finds all `- [x]` lines in `## Active Tasks` section
- Keeps only the most recent N (3 normal, 1 aggressive)
- Moves pruned items to `## Recent Context` with timestamp

**Phase 2 -- Session Marker Pruning**:
- Finds `## Session XXXX Completed` headings
- Keeps only last N markers (3 normal, 1 aggressive)
- Removes older markers entirely

**Phase 3 -- Recent Context Aging**:
- Parses date-stamped entries in `## Recent Context`
- Removes entries older than threshold (48h normal, 24h aggressive)
- Enforces max entry cap (5 normal, 2 aggressive)

### 2.2 Session Archival

`archive_old_sessions()` moves session logs older than 7 days to an archive directory. This prevents the session log directory from growing unboundedly.

### 2.3 The compress_context.py Script

A separate tool using Gemini API for AI-powered compression:
- Walks a directory tree, reads source files
- Sends content to Gemini with a summarization prompt
- Caches results by file content hash (MD5)
- Supports model fallback chain
- Outputs compressed Markdown summaries

**Purpose**: Create compressed code documentation for future context injection -- not for boot, but for on-demand context loading.

### 2.4 Context Monitor (context_monitor.py)

Session hygiene monitoring:
- Counts conversation turns in session logs
- Three zones:
  - < 40 turns: Healthy
  - 40-80 turns: HIGH ENTROPY -- recommends summary injection
  - 80+ turns: CRITICAL ENTROPY -- requires hard archival (Protocol 280)

### 2.5 Protocol 415: Semantic Compaction (O(1) Context Law)

Core philosophy: **"Completed tasks are Dead Context."**

| State | Definition | Action |
|-------|-----------|--------|
| Active | `[ ] Task A` | Keep in activeContext.md |
| Freshly Done | `[x] Task A` (last 3) | Keep as "Recent Momentum" |
| Stale Done | `[x] Task A` (>3 ago) | COMPACT to summary or archive |

Rules:
1. Never delete without trace (must exist in session_logs first)
2. Summarize, don't just delete (10 micro-tasks -> 1 macro-accomplishment)
3. Preserve momentum (keep last 3 visible)

### 2.6 Protocol 101: Compaction Recovery

Addresses the fundamental problem: **compaction creates discontinuities**.

Discontinuity detection heuristics:
- Agent asks question already answered -> memory loss
- Agent contradicts earlier decision -> decision lost
- Agent repeats completed work -> progress lost
- User says "I already told you" -> general memory loss

Current approximation (without transcript access):
- Session logs with checkpoints
- STATE FREEZE protocol
- Manual session recovery on `/start`

Future vision (from r/ClaudeCode):
- Full transcript parser
- Compaction event detector
- Vector indexing for past sessions
- Subagent search delegation (avoids polluting main context)

---

## 3. Exoskeleton Architecture

### 3.1 The Mind/Body Split (Protocol 415-Exo)

Origin: Derived from OpenClaw analysis (Feb 2026). Uses the "Iron Man Suit" metaphor:

| Layer | Component | Tech Stack | Role |
|-------|-----------|-----------|------|
| **Mind** | Athena Core | Python | GraphRAG, Protocol Selection, Decision Making |
| **Bridge** | RPC/API | HTTP/JSON | Passing intent between Mind and Body |
| **Body** | Exoskeleton | Node.js/Go | WhatsApp/Telegram I/O, Voice, UI |

### 3.2 Key Doctrines

**"Stupid Suit" Doctrine**: The Body should be as brainless as possible. It receives sensory input, relays to Mind, and delivers responses. No independent decision-making.

**State Sovereignty**: Long-term state lives in the Mind (Markdown files, Vector DB). Ephemeral UI state lives in the Body. Body syncs TO Mind, never reverse.

**Security Air Gap**: Mind runs in secure environment; Body can be exposed to public internet. If Body is compromised, Mind's deep memory remains secure ("sacrificial limb" pattern).

### 3.3 Context Engineering Implication

The exoskeleton architecture means the context window is exclusively managed by the Python-based Mind layer. The Node.js Body layer never holds context state -- it only streams I/O. This architectural decision keeps token budget management centralized and predictable.

---

## 4. Adaptive Latency Principle (Protocol 417)

### 4.1 Three-Phase Model

| Phase | User State | Latency Tolerance | Priority |
|-------|-----------|-------------------|----------|
| **Start-up** | Initiating session | LOW (seconds) | Speed to "Ready" |
| **Working** | In active focus | MINIMAL (sub-second) | Zero disruption |
| **Shutdown** | Wrapping up | HIGH (minutes OK) | Thorough closure |

### 4.2 Implementation Rules

**Start-up**: Heavy imports MUST be lazy-loaded. Health checks run in background threads. "Ready" prompt appears before all checks complete. Goal: sub-5-second boot.

**Working (Flow State)**: All disk IO non-blocking. Synchronous network calls prohibited in hot paths. Use cached data, refresh asynchronously. Exception: explicit `/think` or `/ultrathink`.

**Shutdown**: Slower operations acceptable. Session synthesis, learning propagation, integrity checks can block.

### 4.3 Adaptive Context Loading (The "Bleach" Scaling Law)

Three cognitive tiers with different context load levels:

| Mode | Trigger | Load | Use Case |
|------|---------|------|----------|
| **Shikai** (L1) | `/start`, standard chat | ~2K tokens (Core Identity) | Quick Q&A, simple coding |
| **Bankai** (L2) | `/think`, complex topics | ~10K tokens (Profile + Skills) | Strategy, debugging |
| **Shukai** (L3) | `/ultrathink` | ~100K+ tokens (Full Context + Graph) | Architecture, life decisions |

### 4.4 On-Demand Files

The example `token_budget.py` script defines a clear split:

**BOOT_FILES** (loaded immediately): Only `Core_Identity.md` (~2K tokens)

**ON_DEMAND_FILES** (loaded when triggered):
- `TAG_INDEX.md` -- triggered by "tag lookup, file search"
- `SKILL_INDEX.md` -- triggered by "protocol/skill request"
- `User_Profile_Core.md` -- triggered by "bio, typology"
- `Psychology_L1L5.md` -- triggered by "trauma, therapy"
- `Operating_Principles.md` -- triggered by "decision frameworks"
- `Business_Frameworks.md` -- triggered by "marketing, SEO"
- `Output_Standards.md` -- triggered by `/think` or `/ultrathink`
- `Constraints_Master.md` -- triggered by "ethical edge case"
- `System_Manifest.md` -- triggered by "architecture query"

**Key insight**: The user profile was split from a monolithic file into 6 sharded modules specifically for token efficiency. Each shard is loaded only when its trigger keywords appear.

---

## 5. Flight Recorder & Diagnostic Relay

### 5.1 Flight Recorder (The Black Box)

`src/athena/core/flight_recorder.py` -- an append-only JSONL log recording every high-stakes tool call (Write, Delete, Git).

Each entry contains:
- Timestamp (epoch + human-readable)
- Tool name + parameters
- Status (initiated/completed/failed)
- Rationale (why this action was taken)
- Process ID

**Context engineering relevance**: The flight recorder exists OUTSIDE the context window. It's a persistent audit trail that doesn't consume tokens but can be queried when forensic analysis is needed.

### 5.2 Diagnostic Relay (Protocol 500)

`src/athena/core/diagnostic_relay.py` -- captures framework errors, sanitizes PII, and generates GitHub issue drafts.

PII sanitization covers:
- Absolute file paths (macOS/Linux/Windows)
- Email addresses
- API keys (sk-*, supabase_*)
- IP addresses

**Context engineering relevance**: Error diagnostics are written to disk as Markdown files rather than injected into context. This prevents error dumps from consuming context budget.

### 5.3 System Pulse

`src/athena/core/system_pulse.py` -- a minimal health dashboard:
- Daemon status (online/offline/unknown)
- Total session count
- Last flight recorder action
- Memory integrity status

Designed for quick visual health checks without loading heavy context.

---

## 6. Session Efficiency Tracking

### 6.1 Composite Efficiency Score

`src/athena/core/session_efficiency.py` implements a weighted efficiency metric:

| Component | Weight | What It Measures |
|-----------|--------|-----------------|
| Skill Utilization | 35% | % of prompts that triggered a skill |
| Token Efficiency | 35% | Boot tokens used vs 20K ceiling |
| Context Reuse | 20% | Memory bank cache hits vs total queries |
| Retry Density | 10% | Lower retries = better (inverted) |

### 6.2 Token Efficiency Scoring

Nuanced scoring with sweet spots:
- 0-60% usage: 1.0 (excellent -- plenty of headroom)
- 60-80% usage: Linear decay from 1.0 to 0.5
- 80-100% usage: Steeper decay from 0.5 to 0.0
- >100% usage: 0.0 (over budget)

### 6.3 Grades

| Grade | Score | Color |
|-------|-------|-------|
| Excellent | 80+ | Green |
| Good | 60-79 | Yellow |
| Needs Work | <60 | Red |

---

## 7. .context/ Directory as "Canonical Context"

### 7.1 Structure

The `.context/` directory serves as Athena's "canonical context" store:

```
.context/
  CANONICAL.md          -- Project README (identity document)
  PROTOCOL_SUMMARIES.md -- Compressed protocol index
  TAG_INDEX.md          -- Master tag index (legacy monolithic)
  TAG_INDEX_A-M.md      -- Sharded tag index (A-M)
  TAG_INDEX_N-Z.md      -- Sharded tag index (N-Z)
  project_state.md      -- Living workspace snapshot
  memory_bank/
    userContext.md       -- User identity (static)
    productContext.md    -- Product identity (static)
    activeContext.md     -- Session state (dynamic, compacted)
  memories/
    session_logs/        -- Per-session logs
    case_studies/        -- Archived case studies
  research/              -- Research artifacts
  specs/                 -- Technical specifications
  inputs/                -- External input documents
  cache/
    compression/         -- AI-compressed file summaries
```

### 7.2 Design Principles

1. **Human-readable**: Everything is Markdown. Git-versioned. Portable.
2. **Sharded for tokens**: TAG_INDEX was split from monolithic to A-M/N-Z shards. User Profile split into 6 modules.
3. **Static vs Dynamic separation**: userContext.md and productContext.md rarely change. activeContext.md changes every session and is the primary compaction target.
4. **Canonical = Truth**: `.context/` is the single source of truth. The Vector DB (Supabase) is "insurance," not primary.

---

## 8. Boot Orchestration

### 8.1 Parallelized Boot Sequence

`src/athena/boot/orchestrator.py` implements a multi-phase boot:

1. **Phase 0**: Check for `--verify` flag
2. **Phase 1**: Watchdog + pre-flight (environment verification, daemon enforcement, security patches, crash detection)
3. **Phase 1.5**: System sync + boot timestamp
4. **Phase 2**: Identity integrity (semantic prime verification)
5. **Phase 3**: Memory recall (last session)
6. **Phase 3.5**: Token budget check + auto-compaction
7. **Phase 4**: Session creation
8. **Phase 5**: Audit reset
9. **Phases 6-7**: Parallel execution via `ThreadPoolExecutor(max_workers=8)`:
   - Context capture
   - Semantic priming
   - Protocol injection
   - Search cache pre-warming
   - System health check
   - Hot file prefetch
10. **Phase 8**: Sidecar launch (sovereign index)
11. **Final**: Display token budget gauge

**Key context engineering decisions**:
- Phases 6-7 run in parallel (ThreadPoolExecutor with 8 workers) to minimize boot latency
- Token budget check happens BEFORE session creation (Phase 3.5), ensuring compaction runs before context is loaded
- Sidecar runs as independent process (won't block boot)

---

## 9. Protocol 89: Hybrid Token Conservation

### Three-Agent Workflow

| Phase | Agent | Rationale |
|-------|-------|-----------|
| PLAN | Gemini (large context) | Best for research, doesn't burn Claude tokens |
| EXECUTE | Claude (Opus 4.5) | Best for coding, skip redundant research |
| TEST | External MCP (Testsprite) | Doesn't burn either model's tokens |

**Key insight**: "Plan-First, Execute-Second" -- Gemini produces a roadmap.md, Claude consumes it. Claude skips research entirely, conserving tokens for execution.

### Token Economics

| Action | Token Cost | Better Alternative |
|--------|-----------|-------------------|
| Debugging with Claude | HIGH (6-10% session) | Use Testsprite, feed errors back |
| Research with Claude | MEDIUM | Use Gemini (free tier) |
| Planning with Claude | MEDIUM | Use Gemini (larger context) |
| Coding with Gemini | MEDIUM | Use Claude (better execution) |

---

## 10. Protocol 85: Token Hygiene

### Zone System

| Threshold | Zone | Action |
|-----------|------|--------|
| 0-50% | GREEN | Normal operation |
| 50-70% | YELLOW | Consider handoff doc |
| 70-85% | ORANGE | Create handoff, prepare fresh start |
| 85%+ | RED | STOP. Handoff mandatory. |

### Anti-Patterns

| Bad | Good |
|-----|------|
| Letting context fill to 90%+ | Proactive handoff at 70% |
| Repeating full context each turn | Reference by file path |
| Loading all modules on /start | Adaptive loading (Protocol 77) |

---

## 11. Comparison with Our Approach

### Our System (CLAUDE.md + activeContext.md + knowledge.md)

| Aspect | Our Approach | Athena's Approach |
|--------|-------------|-------------------|
| **Boot context source** | CLAUDE.md (monolithic, loaded by IDE) | 3 sharded Memory Bank files + token budget gauge |
| **Token budget tracking** | None (implicit, IDE-managed) | Explicit 20K hard cap with ASCII gauge, auto-compaction |
| **Context compaction** | Manual (pre-compact hook) | Automated 3-phase compaction with age-based pruning |
| **Adaptive loading** | None (everything in CLAUDE.md) | 3-tier adaptive latency (Shikai/Bankai/Shukai) |
| **Session state** | activeContext.md (single file) | activeContext.md + session logs + flight recorder |
| **Knowledge persistence** | knowledge.md + Graphiti | Memory Bank files + VectorRAG + GraphRAG + Supabase |
| **Boot speed** | Not measured | Sub-5-second target, parallelized boot with ThreadPoolExecutor |
| **Session efficiency** | Not tracked | Composite 0-100 score with 4 weighted components |
| **Error handling** | Inline (in context) | Diagnostic Relay writes to disk, avoids context pollution |
| **File sharding** | No (single CLAUDE.md) | Yes (Tag Index split A-M/N-Z, User Profile split 6 ways) |
| **Cross-model optimization** | Single model (Claude) | Gemini for planning, Claude for coding, Testsprite for testing |
| **Compaction recovery** | Post-compaction file re-read | Protocol 101 with discontinuity detection heuristics |
| **Context zones** | None | 4-zone system (Green/Yellow/Orange/Red) |
| **Agent teams** | TeamCreate parallel agents | Not agent-team-focused (single-user paradigm) |

### Key Differences

**1. Explicit vs Implicit Token Management**
Athena treats tokens as a measurable, visible resource with a hard cap, gauge, and auto-compaction. Our system relies on IDE-level context management with no explicit token tracking. Athena's approach provides early warning and automated remediation; ours depends on the compaction summary + manual re-reading.

**2. Adaptive Loading vs All-at-Once**
Athena's biggest context engineering innovation is on-demand context loading. Only Core Identity (~2K tokens) loads at boot; everything else loads when triggered by query keywords. Our system loads the entire CLAUDE.md at session start regardless of task type. This means Athena's working context is leaner for simple tasks.

**3. Sharding Strategy**
Athena proactively shards large files (Tag Index, User Profile) to enable selective loading. Our knowledge is concentrated in fewer, larger files (CLAUDE.md, knowledge.md) which limits granular loading.

**4. Session Efficiency Metrics**
Athena quantifies session quality with a composite score. We have no equivalent metric. This means Athena can track improvement trends over time while we rely on qualitative assessment.

**5. Error Isolation**
Athena's Diagnostic Relay and Flight Recorder keep error context OUT of the context window by writing to disk. Our system handles errors inline, which can consume context budget during debugging sessions.

**6. Multi-Model Token Arbitrage**
Athena's Protocol 89 allocates different tasks to different models based on cost-efficiency (Gemini for research, Claude for coding). Our system is single-model, so all token consumption hits the same budget.

### What We Could Adopt

1. **Token budget gauge**: Implement explicit token counting for CLAUDE.md + activeContext.md + knowledge.md with a visible gauge
2. **Adaptive loading**: Split knowledge.md into topic-specific shards that load on-demand based on task keywords
3. **Auto-compaction with age pruning**: Enhance pre-compact-save.py with age-based pruning (entries older than N hours get compressed)
4. **Session efficiency scoring**: Track skill utilization, token efficiency, context reuse, and retry density per session
5. **Context zones**: Define Green/Yellow/Orange/Red zones for our context usage and trigger handoff protocols
6. **File sharding**: Split CLAUDE.md into boot-critical vs on-demand sections
7. **Error-to-disk pattern**: Route debugging output to disk files rather than consuming context window

### What They Could Adopt From Us

1. **Agent Teams**: Athena is single-user focused; we have mature agent team orchestration with TeamCreate, task dependencies, and parallel execution
2. **Pipeline State Machine**: Our PIPELINE.md with phase markers and gates is more structured than Athena's session-based workflow
3. **Graphiti integration**: We use structured knowledge graphs for semantic context; Athena uses VectorRAG primarily
4. **Post-compaction recovery protocol**: Our "re-read PIPELINE.md + activeContext.md + knowledge.md" after compaction is explicit and battle-tested
5. **QA validation loops**: Our qa-validation-loop skill with reviewer/fixer agents is more mature

---

## 12. Key Takeaways

### Athena's Context Engineering Strengths

1. **Token budget is a first-class citizen** -- measured, displayed, auto-managed with hard caps
2. **Adaptive latency is the killer feature** -- loads only what's needed, when it's needed
3. **Boot is parallelized and fast** -- ThreadPoolExecutor with 8 workers, lazy imports, sub-5s target
4. **Everything writes to Markdown** -- human-readable, git-versioned, portable, no vendor lock-in
5. **Compaction is automated and multi-pass** -- 3 phases, aggressive mode, with safety limits
6. **Session efficiency is quantified** -- 4-component weighted score enables trend tracking
7. **Errors don't pollute context** -- Diagnostic Relay writes to disk, Flight Recorder is append-only JSONL
8. **Multi-model arbitrage** -- different models for different task types optimizes total token spend

### Athena's Context Engineering Weaknesses

1. **Single-user paradigm** -- no agent team support, no parallel task execution
2. **Compaction recovery is aspirational** -- Protocol 101 describes the ideal but current implementation is basic (session logs + manual review)
3. **No pipeline state machine** -- no formal phase tracking for multi-step tasks
4. **TAG_INDEX is massive** -- even sharded, the full tag index is 100K+ characters
5. **Gemini dependency** -- compress_context.py requires Gemini API, adding cost and external dependency
6. **No formal QA gate** -- no reviewer/fixer agent loop for code quality

---

*Analysis complete. All source files verified from github.com/winstonkoh87/Athena-Public.*
