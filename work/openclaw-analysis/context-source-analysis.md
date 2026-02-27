# OpenClaw Context Management — Source Code Analysis

> Analyzed from: `openclaw/openclaw` GitHub repository
> Files analyzed: 10 TypeScript source files
> Date: 2026-02-22

---

## Context Assembly Pipeline

OpenClaw's context is assembled through a layered pipeline:

1. **Model Discovery & Context Window Resolution** (`src/agents/context.ts`):
   - On startup, lazy-loads model metadata from Pi Coding Agent's model registry
   - Discovers available models via `discoverModels()` from `pi-model-discovery.js`
   - Applies context window sizes from two sources (in priority order):
     - User's `models.json` config overrides (`applyConfiguredContextWindows`)
     - Auto-discovered model metadata (`applyDiscoveredContextWindows`)
   - When multiple providers expose the same model ID with different context windows, **prefers the smaller window** — fail-safe design to prevent token overestimation
   - Results cached in `MODEL_CACHE` (Map<string, number>), populated once at import time via async IIFE

2. **Context Window Resolution** (`context-window-guard.ts`):
   - `resolveContextWindowInfo()` determines effective context window from multiple sources:
     - `modelsConfig` (user override in config) — highest priority
     - `model` (auto-discovered from provider) — second priority
     - `default` (fallback) — lowest priority
   - Global cap via `agents.defaults.contextTokens` config — if set and smaller, overrides all
   - Returns `ContextWindowInfo` with `tokens` count and `source` string for debugging

3. **Command Context Building** (`src/auto-reply/reply/commands-context.ts`):
   - Builds `CommandContext` from incoming message parameters
   - Resolves authorization, sender identity, surface/channel info
   - Handles group vs DM contexts (strips mentions in group mode)
   - Normalizes command body for downstream processing

4. **Skills Context** (`src/agents/skills/bundled-context.ts`):
   - Resolves bundled skills directory and loads skill definitions
   - Caches loaded skills per directory path to avoid re-reading filesystem
   - Uses `loadSkillsFromDir()` from Pi Coding Agent SDK
   - Returns set of available skill names for context injection

---

## Context Window Guard

The guard system (`context-window-guard.ts`) provides a two-tier protection mechanism:

### Constants
- `CONTEXT_WINDOW_HARD_MIN_TOKENS = 16,000` — absolute minimum; below this, block the request
- `CONTEXT_WINDOW_WARN_BELOW_TOKENS = 32,000` — warning threshold

### Guard Evaluation (`evaluateContextWindowGuard`)
```
Input: ContextWindowInfo + optional thresholds
Output: ContextWindowGuardResult { tokens, source, shouldWarn, shouldBlock }
```

- **shouldWarn**: `true` when `0 < tokens < 32,000` (warn threshold)
- **shouldBlock**: `true` when `0 < tokens < 16,000` (hard minimum)
- Zero tokens = no guard action (unknown window size, don't block)
- Both flags can be true simultaneously (a blocked model also triggers warning)

### Resolution Priority
```
1. modelsConfig (user-specified per-model context window)
2. model (auto-discovered from provider API)
3. default (hardcoded fallback)
4. agentContextTokens cap (if configured and smaller than resolved value)
```

This is a **preventive guard**, not a runtime pruner. It fires at session setup to warn or block before work begins with an undersized context window.

---

## Context Pruning System

The pruning system (`src/agents/pi-extensions/context-pruning/`) is OpenClaw's core context management mechanism. It operates as a Pi Coding Agent extension that intercepts context events.

### Architecture Overview

```
Extension (extension.ts)
  ├── registers on "context" event
  ├── reads runtime settings from session-scoped registry
  └── delegates to pruner

Runtime (runtime.ts)
  ├── WeakMap-based registry keyed by SessionManager instance
  └── stores EffectiveContextPruningSettings per session

Settings (settings.ts)
  ├── config schema & defaults
  └── computeEffectiveSettings() — validates & normalizes config

Pruner (pruner.ts)
  ├── estimateContextChars() — char-based token estimation
  ├── softTrimToolResultMessage() — head+tail trimming
  └── pruneContextMessages() — orchestrates soft→hard pipeline

Tools (tools.ts)
  └── makeToolPrunablePredicate() — glob-based allow/deny filtering
```

### Pruning Strategy

The pruner uses a **two-phase progressive strategy** based on context utilization ratio:

```
ratio = estimated_context_chars / (context_window_tokens * 4)

Phase 1 (Soft Trim): ratio >= softTrimRatio (default 0.3 = 30% full)
  → Trim long tool results to head+tail excerpts

Phase 2 (Hard Clear): ratio >= hardClearRatio (default 0.5 = 50% full)
  → Replace entire tool results with placeholder text
```

Key decisions:
- **Token estimation**: Uses `CHARS_PER_TOKEN_ESTIMATE = 4` (1 token ~ 4 chars)
- **Image estimation**: Each image block counted as 8,000 chars but never pruned
- **Protected tail**: Last N assistant messages are never pruned (default: 3)
- **Bootstrap protection**: Messages before the first user message are NEVER pruned — this protects identity/SOUL.md reads
- **Tool filtering**: Only tool results matching the allow/deny glob patterns are candidates

### Soft vs Hard Pruning Implementation

#### Soft Trim (`softTrimToolResultMessage`)
```
Trigger: ratio >= 0.3 (softTrimRatio)
Action: Trim tool result text to head + "..." + tail
Defaults:
  maxChars: 4,000 (skip if result is smaller)
  headChars: 1,500 (first N chars preserved)
  tailChars: 1,500 (last N chars preserved)
```

Produces output like:
```
[first 1500 chars of tool output]
...
[last 1500 chars of tool output]

[Tool result trimmed: kept first 1500 chars and last 1500 chars of 45000 chars.]
```

**Notable**: Skips image-containing tool results entirely. The head/tail extraction works across multi-block content (multiple text segments joined with newlines).

#### Hard Clear
```
Trigger: ratio >= 0.5 (hardClearRatio)
Additional gate: total prunable tool chars >= minPrunableToolChars (50,000)
Action: Replace entire tool result content with placeholder
Default placeholder: "[Old tool result content cleared]"
```

Hard clear iterates through prunable tool indexes (oldest first) and stops as soon as ratio drops below `hardClearRatio`. This means it clears the minimum number of old tool results needed.

### Processing Order

1. Estimate total context chars
2. If ratio < softTrimRatio → return unchanged (context is small enough)
3. Identify prunable tool result messages in the prunable range
4. Apply soft trim to each, tracking char savings
5. If ratio still >= hardClearRatio AND hard clear enabled AND enough prunable chars exist:
   - Replace tool results with placeholder, oldest first
   - Stop when ratio drops below threshold
6. Return modified messages array (or original if no changes)

### TTL-based Pruning

The `cache-ttl` mode (`extension.ts`) adds a time-gating layer on top of the pruning logic:

```
mode: "cache-ttl"
ttlMs: 300,000 (5 minutes default, configurable via duration string like "5m")

On each context event:
  1. Check if TTL has expired since lastCacheTouchAt
  2. If NOT expired → skip pruning entirely (return undefined)
  3. If expired → run pruner
  4. If pruner made changes → update lastCacheTouchAt to now
```

This prevents the pruner from running on every single context event. The "cache" refers to the prompt cache — by not modifying context within the TTL window, cached prefixes remain valid longer, saving inference cost.

**Key insight**: The TTL resets only when pruning actually modifies something. If the pruner runs but makes no changes (context is small), the TTL is NOT reset — next event will also try pruning.

---

## Post-Compaction Context

The post-compaction system (`src/auto-reply/reply/post-compaction-context.ts`) handles context restoration after a conversation compaction event.

### Implementation

1. **Source**: Reads `AGENTS.md` from the workspace root
2. **Sections extracted**: `"Session Startup"` and `"Red Lines"` (H2/H3 headings, case-insensitive)
3. **Max size**: 3,000 chars — truncated with `"...[truncated]..."` marker if exceeded
4. **Output format**:
```
[Post-compaction context refresh]

Session was just compacted. The conversation summary above is a hint,
NOT a substitute for your startup sequence. Execute your Session Startup
sequence now — read the required files before responding to the user.

Critical rules from AGENTS.md:

[extracted sections content]
```

### Section Extraction Algorithm (`extractSections`)

- Matches H2 (`##`) or H3 (`###`) headings case-insensitively
- Tracks fenced code blocks (```) to avoid matching headings inside code
- Each section captures content until a heading of same or higher level
- Multiple target sections can be extracted in one pass

### Design Philosophy

The post-compaction message explicitly tells the AI that the **compaction summary is a hint, not truth**. It forces the agent to re-execute its startup sequence rather than relying on the compacted context. This mirrors our system's approach of re-reading state files after compaction.

---

## Compaction + Memory Flush Integration

Based on the analyzed source code, OpenClaw's compaction integration works through several mechanisms:

1. **Pre-compaction**: The context pruning system continuously keeps context size manageable, reducing the frequency of compaction events
2. **During compaction**: Standard Pi Coding Agent compaction occurs (conversation summarization)
3. **Post-compaction**:
   - `readPostCompactionContext()` injects critical AGENTS.md sections back into context
   - The injected message explicitly instructs the agent to re-execute startup (read required files)
   - This creates a **two-layer recovery**: compaction summary + forced re-read of source-of-truth files

The pruning system's `cache-ttl` mode is also relevant here — after compaction, the context is small again, so the pruner naturally becomes inactive until context grows back past thresholds.

---

## Skills & Bootstrap Context

### Bundled Skills Loading (`bundled-context.ts`)

```typescript
resolveBundledSkillsContext(opts) → { dir?: string, names: Set<string> }
```

- Resolves the bundled skills directory path
- Loads all skills from directory using Pi SDK's `loadSkillsFromDir()`
- **Source tagging**: Skills are tagged as `"openclaw-bundled"` for provenance tracking
- **Caching**: Results are cached per directory path — subsequent calls with the same dir return cached names
- **Graceful degradation**: If bundled dir can't be resolved, logs warning once and returns empty set

### Bootstrap Protection in Pruner

The pruner has a critical safety rule in `pruneContextMessages()`:

```typescript
const firstUserIndex = findFirstUserIndex(messages);
const pruneStartIndex = firstUserIndex === null ? messages.length : firstUserIndex;
```

**Everything before the first user message is immune to pruning.** This protects:
- SOUL.md / identity file reads
- AGENTS.md initial loading
- System prompt injection
- Workspace context bootstrapping
- Skill definitions

This means bootstrap context (skills, workspace rules, identity) survives indefinitely in the context window, while conversation history (tool results) gets progressively pruned.

---

## Key Patterns Worth Adopting

### 1. Two-Phase Progressive Pruning
**What**: Soft trim (head+tail) before hard clear (full replacement). Start gentle, escalate only if needed.
**Why**: Preserves partial information as long as possible. The head+tail approach keeps the "what was this about" context even when trimming 90% of a tool result.
**For us**: We have no automatic pruning. Tool results from file reads, grep, etc. accumulate until compaction. A similar system could automatically trim old `Read` and `Grep` results.

### 2. Ratio-Based Thresholds
**What**: Trigger pruning based on `context_chars / context_window` ratio, not absolute sizes.
**Why**: Adapts automatically to different model context windows. A 200K window model gets pruned later than a 32K model.
**For us**: We could calculate our context utilization and proactively prune before hitting compaction.

### 3. Cache-TTL Mode
**What**: Don't re-prune within a time window to preserve prompt caching.
**Why**: Every context modification invalidates the API's prompt cache prefix, costing money. The 5-minute TTL balances freshness vs cache efficiency.
**For us**: If we implement pruning, the TTL concept would be valuable for cost optimization.

### 4. Bootstrap Protection Zone
**What**: Never prune anything before the first user message.
**Why**: Identity files, workspace rules, and system setup are critical and small relative to tool results.
**For us**: Our CLAUDE.md rules and session startup files should similarly be protected from any future pruning mechanism.

### 5. Post-Compaction Forced Re-Read
**What**: After compaction, inject a message saying "the summary is a hint, not truth — re-execute startup."
**Why**: Compaction summaries lose detail. Forcing re-read of source-of-truth files prevents context drift.
**For us**: We already do this manually (re-read PIPELINE.md + STATE.md + activeContext.md). OpenClaw automates it. We could add a similar auto-injection to our post-compaction recovery.

### 6. Tool-Level Pruning Selectivity
**What**: Glob-based allow/deny lists to control which tool results are prunable.
**Why**: Some tool results (e.g., test output, error messages) are more valuable than others (e.g., large file reads). Allow/deny lists let you protect critical results.
**For us**: If implementing pruning, we'd want to protect `Bash` (test results) while aggressively pruning old `Read` (file contents that can be re-read) and `Grep` results.

### 7. Image-Aware Estimation
**What**: Count image blocks at ~8K chars for estimation but never prune them.
**Why**: Images are hard to partially trim and often directly relevant. But their size must be counted so text pruning starts earlier when images consume the window.
**For us**: We use screenshots and diagrams occasionally. A future pruning system should account for their token cost.

### 8. Minimum Prunable Threshold
**What**: `minPrunableToolChars: 50,000` — don't bother with hard clear unless there's enough to actually reclaim.
**Why**: Prevents churn — clearing a handful of small tool results for minimal gain while losing context.
**For us**: Good engineering practice. Only prune when the payoff justifies the context loss.

---

## Configuration Defaults Reference

| Setting | Default | Purpose |
|---------|---------|---------|
| mode | `cache-ttl` | Only mode currently supported |
| ttlMs | 300,000 (5 min) | Cache protection window |
| keepLastAssistants | 3 | Protected recent messages |
| softTrimRatio | 0.3 (30%) | Soft trim activation threshold |
| hardClearRatio | 0.5 (50%) | Hard clear activation threshold |
| minPrunableToolChars | 50,000 | Minimum chars before hard clear |
| softTrim.maxChars | 4,000 | Skip trim if result is smaller |
| softTrim.headChars | 1,500 | Chars to keep from start |
| softTrim.tailChars | 1,500 | Chars to keep from end |
| hardClear.enabled | true | Allow full replacement |
| hardClear.placeholder | "[Old tool result content cleared]" | Replacement text |
| CONTEXT_WINDOW_HARD_MIN_TOKENS | 16,000 | Block if window too small |
| CONTEXT_WINDOW_WARN_BELOW_TOKENS | 32,000 | Warn if window small |
| CHARS_PER_TOKEN_ESTIMATE | 4 | Token estimation ratio |
| IMAGE_CHAR_ESTIMATE | 8,000 | Per-image char estimate |

---

## Comparison with Our System

| Aspect | OpenClaw | Our System |
|--------|----------|------------|
| Context pruning | Automatic, two-phase (soft+hard) | None — accumulate until compaction |
| Context window monitoring | Guard with warn/block thresholds | None |
| Post-compaction recovery | Automated AGENTS.md re-injection | Manual re-read protocol in CLAUDE.md |
| Token estimation | char/4 ratio with image awareness | Not tracked |
| Tool result management | Glob-based selective pruning | All tool results kept equally |
| Cache optimization | TTL-based pruning delay | Not applicable |
| Bootstrap protection | Auto-detected (before first user msg) | Relies on CLAUDE.md ordering |
| Configuration | Rich config object with validation | CLAUDE.md rules (no runtime config) |
