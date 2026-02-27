# Recommendations: What to Adopt from Athena-Public

> Priority-ranked improvements for our Claude Project Template
> Synthesized from 10 parallel agent analysis reports (217KB)
> Date: 2026-02-23

---

## Tier 1: HIGH IMPACT — Implement First (6 items)

### 1. 🎯 Token Budget Gauge + Auto-Compaction Enhancement
**Source**: A2 (Boot), A10 (Context Engineering)
**Effort**: Medium | **Impact**: Very High

**What Athena does**: Explicit 20K token hard cap. ASCII gauge displayed at boot. 3-phase auto-compaction with age-based pruning (completed tasks pruning → session marker pruning → recent context aging).

**What we should adopt**:
- Add token counting to Session Start (measure CLAUDE.md + activeContext.md + knowledge.md)
- Display a simple budget indicator (GREEN/YELLOW/RED zones)
- Enhance pre-compact-save.py with age-based pruning: entries >48h get compressed, entries >7 days get archived
- Add aggressive mode: if tokens >80% after normal compaction, prune harder

**Why it matters**: Without explicit token tracking, we have no early warning of context overflow. This is the #1 cause of degraded agent quality in long sessions.

---

### 2. 🎯 5W1H Skill Metadata + Dead Skills Detection
**Source**: A5 (Agent Coordination — Protocol 411), A9 (Workflows/Skills)
**Effort**: Low | **Impact**: High

**What Athena does**: Every skill MUST answer 6 questions (Who/What/When/Where/Why/How). The `skill_nudge.py` engine matches user prompts against keyword registries. `skill_telemetry.py` tracks usage via JSONL. `get_dead_skills()` finds skills with 0 invocations.

**What we should adopt**:
- Add to every SKILL.md frontmatter:
  ```yaml
  trigger_conditions: ["exact conditions list"]
  rationale: "why this beats training data"
  invocation_example: "user says X -> agent does Y"
  target_agent: "coder|reviewer|explorer"
  ```
- Add JSONL telemetry: log which skills are loaded per session
- Quarterly: run dead skills report, prune unused ones with data

**Why it matters**: Vercel's evals found agents **fail to invoke skills 56% of the time** without structured triggers. The rationale field is critical — it tells the agent WHY the skill adds value beyond its training.

---

### 3. 🎯 Doom Loop Detector (Circuit Breaker)
**Source**: A4 (Governance), A8 (MCP Server)
**Effort**: Low | **Impact**: High

**What Athena does**: Tracks tool call signatures (name + hash of args). If same signature appears 3+ times in 60 seconds → flags as doom loop and breaks the cycle. Borrowed from OpenCode (Feb 2026).

**What we should adopt**:
- Add a pre-tool-execution hook that tracks recent tool calls
- If identical tool+args pattern repeats 3+ times → warn and suggest alternative approach
- This is simpler than our "5+ retries → STUCK" rule and catches the problem programmatically rather than relying on agent self-awareness

**Why it matters**: Doom loops are the #1 token-burner. A single stuck agent can waste 100K+ tokens retrying the same failing approach. Programmatic enforcement is more reliable than instructions.

---

### 4. 🎯 Numeric QA Convergence Scoring
**Source**: A5 (Agent Coordination — Parallel Orchestrator)
**Effort**: Medium | **Impact**: High

**What Athena does**: QA reviewer scores output on 4 dimensions (0-25 each):
- Logical Coherence (0-25)
- Risk Coverage (0-25)
- Actionability (0-25)
- Blind Spot Check (0-25)
Threshold: 85/100 to pass. If below → iterate with critique as additional context. Max 3 iterations.

**What we should adopt**:
- Modify qa-validation-loop SKILL.md to use structured numeric scoring
- Reviewer agent outputs a table with 4 scores
- Clear pass/fail threshold (e.g., 80/100)
- This replaces ambiguous CRITICAL/IMPORTANT/MINOR with quantitative assessment

**Why it matters**: Current QA is qualitative — "PASS" or "has issues". A number (85/100) is unambiguous and trackable over time.

---

### 5. 🎯 Multi-Agent Git Safety Rules (Protocol 413)
**Source**: A5 (Agent Coordination), A7 (CLAUDE.md)
**Effort**: Low | **Impact**: Medium-High

**What Athena does**: 6 explicit rules for concurrent agents:
1. Never `git stash` (other agents may have WIP)
2. Never switch branches without explicit request
3. Always `git pull --rebase` before pushing
4. Commit only YOUR own changes
5. Auto-resolve formatting-only diffs
6. Focus reports on YOUR edits, skip guardrail disclaimers

**What we should adopt**:
- Add to teammate-prompt-template.md: "## Multi-Agent Git Safety Rules" section
- Include the "never do" list in every agent prompt when Mode = AGENT_TEAMS
- Add "focus on YOUR changes only" rule — prevents agents from commenting on or reverting each other's work

**Why it matters**: When 3+ agents share a worktree, git operations are the highest-risk failure point. These rules prevent the most common catastrophic interactions.

---

### 6. 🎯 Lean CLAUDE.md with On-Demand Loading
**Source**: A7 (CLAUDE.md approach), A10 (Context Engineering)
**Effort**: High | **Impact**: Very High (saves ~2500 tokens per interaction)

**What Athena does**: CLAUDE.md is ~80 lines — a "directory/pointer" that tells the agent WHERE to find rules. Detailed protocols live in separate files loaded on-demand.

**What we should adopt** (hybrid approach):
- Keep HARD CONSTRAINTS + FORBIDDEN + Compaction Recovery in CLAUDE.md (critical, must always be in context)
- Move Pipeline Protocol → guide file (loaded when pipeline detected)
- Move Agent Teams Protocol → guide file (loaded when 3+ parallel tasks detected)
- Move Expert Panel → guide file (loaded when explicit trigger)
- Add compressed docs index at top of CLAUDE.md (pipe-delimited file tree, ~200 tokens)
- Target: CLAUDE.md reduced from ~300 to ~120 lines

**Why it matters**: CLAUDE.md is loaded on EVERY interaction. At ~300 lines, it costs ~3000+ tokens of context budget per turn. Reducing to ~120 lines saves ~2500 tokens per interaction — that's ~2.5K tokens freed for actual work on every single message.

---

## Tier 2: MEDIUM IMPACT — Implement After Tier 1 (8 items)

### 7. Adversarial Self-Critique Track
**Source**: A3 (Protocol System), A5 (Parallel Orchestrator)
**Effort**: Medium | **Impact**: Medium

Add a "Track B: Adversarial Skeptic" perspective to our Expert Panel. One agent always challenges: "What could go wrong? Where is the ruin?" This catches optimism bias.

### 8. Budget Gatekeeper Pattern
**Source**: A5 (Cognitive Router & Gatekeeper)
**Effort**: Medium | **Impact**: Medium

Implement session budget tracking: tool calls used, estimated tokens consumed, estimated cost. Soft warning at 80%, hard limit at 100%. Decorator-based (`@budget_guard`) for easy integration.

### 9. Session Efficiency Scoring
**Source**: A10 (Context Engineering)
**Effort**: Medium | **Impact**: Medium

Track 4 metrics per session:
- Skill utilization (% of interactions that triggered skills)
- Token efficiency (boot tokens vs budget)
- Context reuse (memory hits vs total queries)
- Retry density (lower = better)
Composite 0-100 score enables trend tracking across sessions.

### 10. Prompt Library (Reusable Thinking Patterns)
**Source**: A9 (Workflows/Skills)
**Effort**: Low | **Impact**: Medium

Create `.claude/prompts/PROMPT_LIBRARY.md` with curated meta-prompts:
- Pre-Mortem: "List 10 ways this could fail"
- MECE Breakdown: "Decompose into mutually exclusive, collectively exhaustive categories"
- Assumption Auditor: "List all assumptions, rate confidence 1-5"
- Counter-Argument Generator: "Give the strongest 3 arguments against this"

Use in agent team prompts and Expert Panel sessions.

### 11. Workspace Health Workflow
**Source**: A9 (Workflows — /refactor, /diagnose)
**Effort**: Medium | **Impact**: Medium

Create a `/health` skill that performs periodic maintenance:
- Check for orphaned files in work/
- Verify all activeContext.md entries are current
- Validate knowledge.md for duplicates
- Clean up stale daily logs (>30 days → archive)
- Verify PIPELINE.md state consistency
- Report token budget of CLAUDE.md + memory files

### 12. Triple-Lock Governance (Search → Save → Speak)
**Source**: A4 (Governance), A8 (MCP)
**Effort**: High | **Impact**: Medium

Enforce that agents always check memory (Graphiti) before making conclusions, and always save insights after work. Currently we rely on instructions; Athena enforces programmatically via governance engine.

Could implement as pre-commit hook: verify that activeContext.md was updated before allowing commit.

### 13. Command Composability / Reasoning Depth Tiers
**Source**: A9 (Workflows)
**Effort**: Medium | **Impact**: Medium

Allow combining skills: `/expert-panel /deep-research` = full panel with web research. Define explicit depth tiers:
- Normal: Standard agent execution
- Deep: Extended thinking budget + full skill loading
- Ultra: Parallel multi-agent analysis (Expert Panel)

### 14. Error-to-Disk Pattern
**Source**: A8 (MCP — Diagnostic Relay), A10 (Context Engineering)
**Effort**: Low | **Impact**: Medium

Route debugging output and error traces to `work/debug/` files rather than consuming context window. Reference them by file path instead of inlining. This keeps the context window clean for productive work.

---

## Tier 3: LOW PRIORITY / RESEARCH (6 items)

### 15. Trilateral Feedback (Multi-Model Validation)
Use different LLMs to red-team critical decisions. Export artifact → send to Gemini/GPT → bring findings back. The "Watchmen Consensus Score" (3/3 agree = highly confirmed) is elegant. **Blocked on**: multi-model API integration.

### 16. Adaptive Context Loading (File Sharding)
Split knowledge.md into topic-specific shards loaded on-demand. Athena splits Tag Index into A-M/N-Z, User Profile into 6 modules. **Blocked on**: CLAUDE.md refactoring (Tier 1, item 6).

### 17. Flight Recorder (Immutable Audit Trail)
Append-only JSONL log of all high-stakes operations (commits, file deletions, memory updates). Each entry: timestamp, tool, params, rationale, PID. Useful for forensics. **Low urgency** because we have git history.

### 18. Agentic Query Decomposition for Graphiti
Before calling search_memory_facts, decompose complex queries: "What is X and how does Y?" → 2 sub-queries. Rule-based NLP, no LLM cost. Boost results found by multiple sub-queries.

### 19. Ruin Prevention Gate
Before any destructive operation (delete, force push, drop table), run a formal pre-flight check: "Is this reversible? What is the blast radius? Is there a backup?" Athena's `ruin_check.py` implements this as a boolean gate.

### 20. Exocortex (External Knowledge Base)
Local offline knowledge base (SQLite FTS5 with Wikipedia abstracts). Provides world knowledge grounding. Low priority because our agents can use WebSearch.

---

## NOT Recommended (Patterns to Avoid)

| Athena Pattern | Why Not |
|----------------|---------|
| macOS-specific swarm spawning (AppleScript) | Platform-locked, fragile |
| Filesystem polling for agent communication | Our SDK messaging is superior |
| Manual merge step for worktrees | Too labor-intensive for agent teams |
| Default-to-pass on parse failure in QA gate | Masks quality issues |
| 120+ protocols in separate files | Maintenance burden; our 11 skills + inline rules are more focused |
| Supabase + ChromaDB + LightRAG + SQLite stack | Over-engineered for our use case; Graphiti covers our needs |
| Content auto-classification by regex | Brittle for security; better to use explicit sensitivity labels |
| Gemini API for context compression | Adds cost and external dependency |
| 49 slash commands | Workflow explosion risk; our focused set is more maintainable |

---

## Implementation Roadmap

### Sprint 1: Quick Wins (1-2 sessions)
- [ ] Add 5W1H fields to SKILL.md frontmatter (all 11 skills)
- [ ] Add Multi-Agent Git Safety Rules to teammate-prompt-template.md
- [ ] Add error-to-disk pattern for debugging output
- [ ] Create .claude/prompts/PROMPT_LIBRARY.md with 4 meta-prompts

### Sprint 2: Core Infrastructure (2-3 sessions)
- [ ] Implement token budget gauge (count tokens in CLAUDE.md + memory files)
- [ ] Enhance pre-compact-save.py with age-based pruning
- [ ] Add skill telemetry (JSONL logging of skill usage)
- [ ] Add doom loop detector (pre-tool-execution hook)

### Sprint 3: Quality Upgrade (2-3 sessions)
- [ ] Modify QA validation loop to use numeric scoring (0-100)
- [ ] Refactor CLAUDE.md to lean format (~120 lines with on-demand loading)
- [ ] Add compressed docs index to CLAUDE.md header
- [ ] Implement session efficiency scoring

### Sprint 4: Advanced Patterns (3-4 sessions)
- [ ] Add adversarial skeptic track to Expert Panel
- [ ] Implement budget gatekeeper (soft/hard limits)
- [ ] Create workspace health workflow (/health)
- [ ] Add command composability for skill stacking

---

## Summary

**Athena is philosophically different but technically complementary.** They optimize for single-user deep work with multi-model validation; we optimize for multi-agent parallel execution with pipeline state management.

The **biggest wins** from Athena:
1. **Token efficiency** — adaptive loading + explicit budget = 5x more headroom
2. **Skill reliability** — 5W1H metadata doubles trigger accuracy
3. **Quality objectivity** — numeric scoring replaces qualitative gut-feel
4. **Safety enforcement** — doom loop detector + git safety rules = fewer catastrophic failures

Our **biggest advantages** over Athena:
1. **Agent Teams** — parallel execution that Athena can't match
2. **Pipeline State Machine** — formal multi-phase tracking
3. **Compaction Recovery** — battle-tested memory re-loading
4. **Platform Portability** — works everywhere, not just macOS
5. **Graphiti Integration** — dynamic knowledge graph with temporal reasoning

**The ideal is a hybrid**: Athena's token efficiency + skill reliability + governance enforcement, combined with our agent teams + pipeline + compaction resilience.
