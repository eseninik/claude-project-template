# A2: Athena Boot & Session Lifecycle Analysis

> Analyzed from: `winstonkoh87/Athena-Public` repository
> Date: 2026-02-23
> Focus: How Athena achieves ~10K token boot after 10,000 sessions

---

## Boot Sequence

Athena's boot is a **multi-phase orchestrated pipeline** with 8 distinct phases, executed from `src/athena/boot/orchestrator.py`. The boot entry point is `scripts/boot.py` (a stdlib-only resilient shim), which delegates to the SDK orchestrator.

### Phase-by-Phase Breakdown

| Phase | Name | What Happens | Loader |
|-------|------|-------------|--------|
| 0 | Flag Check | `--verify` flag detection for test mode | orchestrator.py |
| 1 | Watchdog & Pre-flight | SIGALRM watchdog (90s timeout), crash recovery check, canary (dead man switch) audit, security patching (CVE-2025-69872 DiskCache mitigation) | StateLoader, SystemLoader |
| 1.5 | System Sync | UI component sync (Antigravity IDE), daemon enforcement (`athenad.py`), boot timestamp write to `last_boot.log` | SystemLoader |
| 2 | Integrity | **Semantic Prime verification** -- SHA-384 hash check of `Core_Identity.md`. If hash mismatch: REFUSE TO BOOT. This is the identity tamper-detection gate. | IdentityLoader |
| 3 | Memory Recall | Load last session log, display focus & deferred items | MemoryLoader |
| 3.5 | Token Budget | Measure all boot files, auto-compact if over 20K hard cap (up to 3 passes) | token_budget module |
| 4 | Session Creation | Create new session log file (delegates to `create_session.py`) | MemoryLoader |
| 5 | Audit Reset | Reset semantic audit state for clean session | semantic_audit module |
| 6-7 | **Parallel Context Load** | 6 tasks run concurrently via ThreadPoolExecutor(max_workers=8) | Multiple loaders |
| 8 | Sidecar Launch | Launch sovereign index sidecar process | subprocess |

### Phase 6-7 Parallelization (Key Innovation)

Six independent operations run **concurrently** in a thread pool:

1. **Context capture** -- date/time/week metadata
2. **Semantic priming** -- Supabase vector search for "recent session context" (most expensive)
3. **Protocol injection** -- context-aware protocol matching from `protocols.json` (with disk-backed cache)
4. **Search cache pre-warming** -- pre-runs queries ["protocol", "session", "user profile"]
5. **System health check** -- vector API (Gemini embedding, 3072d) + Supabase database connectivity
6. **Hot file prefetch** -- reads files from `hot_manifest.json` into OS page cache

After parallel phase, three **synchronous** display operations:
- Learnings snapshot (from `USER_PROFILE.yaml` + `SYSTEM_LEARNINGS.md`)
- Cognitive profile display (from `Athena_Profile.md`)
- Committee of Seats (COS) initialization

### Boot Entry Point Resilience (`scripts/boot.py`)

The boot shim is deliberately **stdlib-only**. If the SDK fails to import, it drops into a Recovery Shell with 5 options:
1. Re-install dependencies
2. Git reset
3. Run `safe_boot.sh` (zero-dependency fallback)
4. Python REPL for manual debugging
5. Exit

This two-layer architecture (stdlib shim -> SDK orchestrator) ensures the system can always recover, even if the SDK is broken.

---

## Token Budget Management

### The Core Mechanism

Athena uses a **hard cap token budget system** defined in `src/athena/boot/loaders/token_budget.py`:

| Constant | Value | Purpose |
|----------|-------|---------|
| `HARD_CAP` | 20,000 tokens | Triggers auto-compaction |
| `ECL` | 200,000 tokens | Effective Context Length (model total) |
| `BOOT_SCRIPT_ESTIMATE` | 2,000 tokens | Fixed overhead for boot output |
| `SYSTEM_INSTRUCTIONS_ESTIMATE` | 3,000 tokens | Fixed overhead for IDE system prompt |
| Target (post-compact) | ~10,000 tokens | Operating target after compaction |

### What Gets Measured

Only **3 canonical Memory Bank files** plus 2 fixed estimates:

| File | Path | Role |
|------|------|------|
| `userContext.md` | `.context/memory_bank/userContext.md` | Persistent user profile |
| `productContext.md` | `.context/memory_bank/productContext.md` | Project/product context |
| `activeContext.md` | `.context/memory_bank/activeContext.md` | Rolling session state (compactable) |
| boot.py output | (estimated) | Fixed 2K estimate |
| System instructions | (estimated) | Fixed 3K estimate |

### Token Counting

Uses `tiktoken` with `cl100k_base` encoding (OpenAI tokenizer). Falls back to `len(text) // 4` if tiktoken is unavailable.

### Auto-Compaction Algorithm

```
IF total_boot_tokens >= 20,000:
    FOR attempt IN 1..3:
        IF attempt == 1: normal compaction
        IF attempt > 1: aggressive compaction
        compact_active_context(aggressive=bool)
        re-measure
        IF total < 20,000: BREAK
    ELSE:
        WARN "Compaction exhausted" and proceed over budget
```

Key insight: **Only `activeContext.md` is compacted.** `userContext.md` and `productContext.md` are treated as stable (rarely change). This means the system targets ~10K post-compact by aggressively summarizing only the rolling session state.

### Visual Budget Gauge

The system displays an ASCII progress bar at boot:
```
📊 Token Budget:
   ✅ userContext.md              2,500 tokens
   ✅ productContext.md           3,200 tokens
   🔴 activeContext.md            8,500 tokens
   ✅ boot.py output              2,000 tokens
   ✅ System instructions         3,000 tokens
   ──────────────────────────────────────────
   Total: 19,200 / 20,000 tokens
   0K ████████████████░░░ 20K
   💡 ~180K tokens available for this session.
```

### Why This Works at 10K Sessions

The genius is the **bounded surface area**: no matter how many sessions have occurred, only 3 files are loaded at boot. Historical knowledge is compressed into `userContext.md` (learnings, preferences) and `productContext.md` (project state), while `activeContext.md` is continuously compacted to stay within budget. Historical session logs are NOT loaded at boot -- they're searchable via Supabase vector search but don't consume boot tokens.

---

## Session Compounding

### The `/start` -> Work -> `/end` Loop

From `docs/YOUR_FIRST_SESSION.md`, the compounding mechanism is:

| Sessions | Compounding Effect |
|----------|-------------------|
| 1 | Basic identity: name, role, goals |
| 10 | Anticipates preferences |
| 50 | Knows decision frameworks, communication style |
| 200 | Catches blind spots proactively |
| 500+ | Functions like a long-tenured colleague |

### How Compounding Actually Works

1. **Profile Interview** (Session 1): Interactive Q&A builds `user_profile.md` covering identity, goals, decision style, strengths, blind spots, values, communication preferences

2. **Active Knowledge Injection** (`boot_knowledge.py`): At every boot, parses `User_Profile_Core.md` for sections tagged as Constraint, Rule, Protocol, Conviction, Preference, or Boundary. These are force-fed into the context window. This fixes the "Hydration Gap" -- the problem where knowledge exists on disk but the agent ignores it.

3. **Quicksave Checkpoints**: Mid-session saves with governance enforcement:
   - **Triple-Lock Protocol**: Must perform Semantic Search + Web Research BEFORE saving (logged as violation if skipped)
   - **Promise Gate (Protocol 416)**: If the summary contains "I will..." language, verifies files were actually changed
   - **Context Hygiene (Protocol 168)**: Monitors session entropy

4. **Session Logs**: Each session creates a dated log (`YYYY-MM-DD-session-N.md`) with Focus, Decisions, Action Items. Deferred items carry forward to next boot.

5. **System Learnings**: A table in `SYSTEM_LEARNINGS.md` accumulates dated insights. The 2 most recent are shown at boot.

6. **Workspace Indexing** (shutdown): `index_workspace.py` generates:
   - `TAG_INDEX.md`: Maps `#tags` to files across the codebase
   - `PROTOCOL_SUMMARIES.md`: Compressed table of all protocols with triggers

### The Compounding Architecture

```
Session N boot:
  ┌─ userContext.md (accumulated preferences/learnings)
  ├─ productContext.md (project state)
  ├─ activeContext.md (last session's rolling state, compacted)
  ├─ User_Profile_Core.md constraints (force-injected)
  ├─ Last session log (focus + deferred items)
  └─ Semantic search: "recent session context" (Supabase vectors)

Session N work:
  ├─ Quicksaves with triple-lock enforcement
  ├─ Decision ledger entries
  └─ Context hygiene monitoring

Session N shutdown:
  ├─ Session log closed (status: Active -> Closed)
  ├─ Key decisions extracted
  ├─ Workspace indexes rebuilt (TAG_INDEX, PROTOCOL_SUMMARIES)
  └─ Git commit
```

---

## Shutdown & State Save

### Shutdown Sequence (`src/athena/boot/shutdown.py`)

1. **Find current session**: Searches `session_logs/` for today's `YYYY-MM-DD-session-*.md` (most recent)
2. **Close session log**:
   - Replace `Status: Active` with `Status: Closed (HH:MM)`
   - Append `## Session Closed` section with end time, duration placeholder, key takeaways, and deferred items
3. **Optional Supabase sync**: If `SUPABASE_URL` is configured, hints at cloud sync availability

### Shutdown Script (`scripts/shutdown.py`)

Simpler than the SDK shutdown:
1. Run `index_workspace.py` (rebuild TAG_INDEX + PROTOCOL_SUMMARIES)
2. Print shutdown confirmation

### `/end` Workflow (`.agent/workflows/end.md`)

The agent-facing workflow adds semantic richness:
1. Read all checkpoints from current session log
2. Identify key decisions and insights
3. Fill in session log: Key Topics, Decisions Made, Action Items
4. Git add and commit with format: "Session XX: <brief summary>"
5. Confirm: "Session XX closed and committed."

### State Preservation Guarantees

- **Crash recovery**: `StateLoader.check_prior_crashes()` reads `.athena/crash_reports/*.json` and alerts at next boot
- **Boot timeout**: 90-second SIGALRM watchdog dumps forensics to crash report before exiting
- **Dead Man Switch**: `DEAD_MAN_SWITCH.md` tracks mandatory audit dates; overdue audits are flagged prominently
- **Overdue flag**: Written to `.athena/overdue_audit.flag` for programmatic detection

---

## Novel Patterns

### 1. Two-Layer Boot Architecture (Resilience Pattern)
`scripts/boot.py` (stdlib-only shim) wraps `athena.boot.orchestrator` (full SDK). If the SDK breaks, the shim provides a recovery shell. This is a pattern we don't see in other agent frameworks -- the boot process itself is fault-tolerant.

### 2. Semantic Prime Hash Verification (Identity Tamper Detection)
SHA-384 hash of `Core_Identity.md` is verified at every boot. If the hash doesn't match `EXPECTED_CORE_HASH`, the system **refuses to boot**. This prevents accidental or malicious identity drift across sessions.

### 3. Bounded Boot Surface with Unbounded Knowledge
Only 3 files are loaded at boot (hard cap: 20K tokens), but the entire session history is available via Supabase vector search. This is the key architectural decision that keeps boot at ~10K tokens regardless of session count.

### 4. Active Knowledge Injection (Hydration Gap Fix)
`boot_knowledge.py` force-parses user constraints and injects them into context. This solves the common problem where knowledge exists in files but the agent never reads it proactively.

### 5. Protocol Cache with Disk Persistence
`IdentityLoader.inject_auto_protocols()` uses a disk-backed JSON cache (`protocol_cache.json`) keyed by context clues. Repeated boots with the same context skip protocol matching entirely.

### 6. Parallel Boot Phase with ThreadPoolExecutor
Phases 6-7 run 6 operations concurrently (max_workers=8). This includes the most expensive operation (semantic priming with Supabase) running in parallel with cheaper operations like context capture and health checks.

### 7. Hot File Prefetch Manifest
`hot_manifest.json` lists frequently-accessed files. At boot, these are read into memory (OS page cache), reducing latency for the first real access during the session.

### 8. Triple-Lock Enforcement on Saves
Quicksaves enforce Search -> Save -> Speak order. Missing a step is logged as a governance violation. This ensures the agent doesn't save hallucinated state.

### 9. Progressive Compaction (Normal -> Aggressive)
Auto-compaction tries normal mode first, then switches to aggressive on retry. This preserves detail when possible but ensures the budget is met.

### 10. Sidecar Process Architecture
A "sovereign index" sidecar is launched as an independent process. This keeps background indexing separate from the main agent loop.

---

## Potential Improvements for Our System

### 1. Replace Unbounded File Loading with Token Budget Gauge

**Current state**: Our session start reads `activeContext.md` + `knowledge.md` without measuring total token cost. As these files grow, boot cost increases unboundedly.

**Athena pattern**: Measure tokens for all boot files, display a gauge, auto-compact if over budget.

**Recommendation**: Add a `measure_boot_tokens()` step to Session Start that counts tokens for `activeContext.md` + `knowledge.md` + `daily/*.md`. Display a simple gauge. If over a threshold (e.g., 15K tokens), auto-compact `activeContext.md` before proceeding.

### 2. Add Active Knowledge Injection

**Current state**: We load `knowledge.md` as a flat file. Critical constraints can be buried among less important patterns.

**Athena pattern**: `boot_knowledge.py` parses structured sections (Constraint, Rule, Protocol) and force-injects them prominently.

**Recommendation**: Add priority markers to `knowledge.md` entries (e.g., `[CRITICAL]`, `[GOTCHA]`). At session start, extract and display critical items first before loading the full file.

### 3. Implement Boot Watchdog Timeout

**Current state**: No timeout on session start operations. If Graphiti or file reads hang, the session start blocks indefinitely.

**Athena pattern**: 90-second SIGALRM watchdog with crash forensics dump.

**Recommendation**: Wrap session start in a timeout (Windows-compatible, since SIGALRM is Unix-only). If boot exceeds 60 seconds, dump state and proceed with minimal context.

### 4. Add Crash Recovery Detection

**Current state**: No mechanism to detect if the previous session crashed (vs. clean exit). After a crash, we start fresh without knowing what went wrong.

**Athena pattern**: `StateLoader.check_prior_crashes()` reads crash reports and alerts at boot.

**Recommendation**: Write a sentinel file at session start, delete at clean exit. If the sentinel exists at next boot, display a crash recovery warning and load the last known good state.

### 5. Parallelize Session Start Operations

**Current state**: Session start reads files sequentially (activeContext -> knowledge -> Graphiti query -> daily log).

**Athena pattern**: ThreadPoolExecutor runs 6 operations in parallel.

**Recommendation**: Use Agent Teams or parallel tool calls to read memory files and query Graphiti simultaneously, rather than sequentially.

### 6. Implement Bounded Boot Surface

**Current state**: We load `activeContext.md` + `knowledge.md` + potentially large daily logs. No hard cap on what gets loaded.

**Athena pattern**: Exactly 3 files measured, hard cap at 20K tokens, auto-compaction of the rolling file.

**Recommendation**: Define a canonical "boot set" (e.g., `activeContext.md` + `knowledge.md` only, max 15K tokens combined). Daily logs should be searchable but NOT loaded at boot. If the boot set exceeds the cap, compact `activeContext.md` automatically.

### 7. Add Identity Hash Verification

**Current state**: CLAUDE.md and settings can be silently modified without detection.

**Athena pattern**: SHA-384 hash of `Core_Identity.md` verified at boot. Mismatch = refuse to boot.

**Recommendation**: Store a hash of critical config files (CLAUDE.md, settings.json). At session start, verify the hash. If it changed since last session, alert the user explicitly (don't refuse to boot, but make it visible).

### 8. Structured Shutdown Protocol

**Current state**: "After Task Completion" protocol updates memory files but doesn't create a formal session close record.

**Athena pattern**: Session logs get explicit close timestamps, status transitions, deferred item sections.

**Recommendation**: Add a formal `/end` behavior: close the current "session" in daily logs with a summary, extract deferred items to a `next_session_deferred.md` file that gets loaded at next boot.

### 9. Workspace Indexing at Shutdown

**Current state**: No automatic indexing of the workspace at session end.

**Athena pattern**: `index_workspace.py` rebuilds tag indexes and protocol summaries at every shutdown.

**Recommendation**: At session end, regenerate a lightweight index of recently changed files and their purposes. Store in a `workspace_index.md` that helps the next session quickly orient.

### 10. Hot File Prefetch Manifest

**Current state**: No mechanism to pre-warm frequently accessed files.

**Athena pattern**: `hot_manifest.json` lists files to prefetch at boot.

**Recommendation**: Track which files are read most often across sessions. Maintain a `hot_files.json` that lists the top 10 most-accessed files. At session start, mention these files in context so the agent knows where to look first.
