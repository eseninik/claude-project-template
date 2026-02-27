# A9: Athena Workflows & Skills System Analysis

> **Analyst**: Research Agent (a9-workflows-skills)
> **Date**: 2026-02-23
> **Sources**: `.agent/workflows/`, `examples/workflows/`, `src/athena/core/skill_nudge.py`, `src/athena/core/skill_telemetry.py`, `examples/skills/`, `docs/WORKFLOWS.md`, `.agent/PROMPT_LIBRARY.md`

---

## 1. Executive Summary

Athena's workflow system is a **slash-command-driven orchestration layer** that maps user intents to predefined multi-phase execution scripts. The system comprises **49+ slash commands** (14 core + 35 example/extended) stored as Markdown files in `.agent/workflows/` and `examples/workflows/`. Unlike our CLAUDE.md-centric approach where behaviors are inline rules + on-demand skill files, Athena treats each workflow as a standalone, self-contained prompt document that the AI reads and executes step-by-step.

The skills subsystem adds a **programmatic suggestion layer** (`skill_nudge.py`) that matches user prompts against a keyword registry, plus a **telemetry layer** (`skill_telemetry.py`) that tracks invocation frequency and effectiveness over time.

**Key Differentiator**: Athena workflows are *user-facing interaction modes* (think/search/plan) while our skills are *agent-internal procedures* (verification-before-completion, qa-validation-loop). Athena is designed for a human-AI pair; our system is designed for agent-team orchestration.

---

## 2. Workflow Architecture

### 2.1 Directory Structure

```
.agent/workflows/          # Core workflows (14 files) - shipped with framework
  start.md                 # Session boot
  end.md                   # Session close + memory commit
  save.md                  # Mid-session checkpoint
  think.md                 # Deep reasoning (all phases)
  ultrathink.md            # Maximum depth (parallel orchestrator)
  search.md                # Web search with citations
  research.md              # Exhaustive multi-source investigation
  plan.md                  # Structured planning with pre-mortem
  brief.md                 # Pre-prompt clarification protocol
  refactor.md              # Full workspace optimization
  vibe.md                  # Ship at 70%, iterate fast
  deploy.md                # Sanitized public repo sync
  brand-generator.md       # AI branding package
  due-diligence.md         # Investigation workflow

examples/workflows/        # Extended workflows (35+ files) - community/custom
  diagnose.md              # Read-only workspace diagnostics
  audit.md                 # Cross-model validation (Gemini vs Claude)
  spec.md                  # Specification output from /brief interview
  fresh.md                 # Session hot-swap (close + reboot)
  tutorial.md              # Guided first-session walkthrough
  vibe.md                  # Duplicate/variant of core vibe
  416-agent-swarm.md       # Agent swarm coordination
  ads.md, ugc-factory.md   # Domain-specific workflows
  ... (35+ total)
```

### 2.2 Workflow File Format

Each workflow is a Markdown file with optional YAML frontmatter:

```yaml
---
description: Short description for the workflow index
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
---

# /command-name -- Title

## Behavior
What happens when invoked...

## Phases
Step-by-step execution...

## Tagging
#workflow #automation #category
```

**Key conventions**:
- `// turbo` annotation marks steps that are safe to auto-run without user confirmation
- Relative links reference other workflows for composability
- Rollback instructions for destructive operations
- Explicit latency profiles (ULTRA-LOW, MEDIUM, HIGH)

### 2.3 Workflow Categories

| Category | Workflows | Purpose |
|----------|-----------|---------|
| **Session Management** | /start, /end, /save, /fresh | Boot, close, checkpoint, hot-swap |
| **Reasoning Depth** | /think, /ultrathink | Escalating analysis depth (2K vs 5K+ tokens) |
| **Research** | /search, /research | Web search with citations, exhaustive investigation |
| **Planning** | /brief, /plan, /spec | Requirements clarification, structured planning |
| **Maintenance** | /refactor, /diagnose, /audit | Workspace health, optimization, cross-model validation |
| **Shipping** | /vibe, /deploy | Rapid iteration, public repo sync |
| **Domain-specific** | /brand-generator, /ads, /due-diligence | Specialized business workflows |
| **Onboarding** | /tutorial | Guided first-session walkthrough |

---

## 3. How Workflows Are Invoked

### 3.1 Slash Command Pattern

Users type `/command` in the chat, and the AI reads the corresponding `.md` file and follows its instructions:

```
User: /think Should I leave my job?
AI: [Reads .agent/workflows/think.md, executes all phases 0-VII]
```

This is essentially the same pattern as Claude Code's `/skill` invocation, but Athena has **49 commands** vs our **7 commands**. The difference is that Athena workflows cover *interaction modes* (how to think) while our commands cover *project lifecycle* (init, resume, commit).

### 3.2 Composability (Stacking Commands)

Athena supports **command stacking** for combined modes:

```
/think /search /research    -->  "Triple Crown Mode" (DEFCON 1)
/brief build                -->  Brief with build extension
/brief interview            -->  Interview mode variant
```

This is a powerful pattern we lack. Our system has no equivalent of combining multiple interaction modes in a single invocation.

### 3.3 Complexity Routing

Athena uses explicit **depth tiers** for different situations:

| Depth | Token Budget | Trigger |
|-------|-------------|---------|
| Normal | Default | Most queries |
| /think | ~2000 tokens | Important decisions, $10K+ impact |
| /ultrathink | ~5000+ tokens | Life-altering, multi-stakeholder |

The `/ultrathink` workflow (v3.0) includes a **Parallel Orchestrator** that dispatches separate API calls to 4 tracks (Domain Expert, Adversarial Skeptic, Cross-Domain Pattern, Zero-Point First Principles) and converges results through an **Adversarial Convergence Gate** (score >= 85 to pass).

---

## 4. PROMPT_LIBRARY Concept

### 4.1 What It Is

`.agent/PROMPT_LIBRARY.md` is a curated collection of **14 reusable system prompts** organized by category:

| Category | Count | Examples |
|----------|-------|---------|
| Strategy | 4 | Pre-Mortem, Counter-Argument Generator, Opportunity Cost Calculator, Second-Order Effects |
| Analysis | 3 | MECE Breakdown, Assumption Auditor, Inversion Prompt |
| Coding | 3 | Code Explainer, Debug Partner, Code Review |
| Writing | 2 | Writing Improver, Hook Generator |
| Research | 2 | Deep Dive, Source Validator |

### 4.2 Design Philosophy

Each prompt follows a **"Stealable Meta-Prompt"** pattern:
- Self-contained (copy-paste into any AI)
- Numbered steps with clear structure
- Role assignment ("You are a strategic analyst...")
- Specific output format requirements
- `[INSERT]` placeholders for user input

### 4.3 How It Differs From Our Approach

| Aspect | Athena PROMPT_LIBRARY | Our Skills |
|--------|----------------------|------------|
| **Target** | Human user (templates to paste) | AI agent (procedures to follow) |
| **Format** | Copy-paste prompts with [INSERT] | YAML frontmatter + execution checklists |
| **Scope** | Thinking frameworks (strategy, analysis) | Engineering procedures (QA, debugging) |
| **Integration** | Manual selection by user | Auto-loaded by Claude Code routing |
| **Domain** | General decision-making | Software development |

**Key Insight**: Athena's PROMPT_LIBRARY is a "cookbook" of thinking patterns. Our skills are "SOPs" for engineering procedures. Both are valuable but serve fundamentally different purposes. The PROMPT_LIBRARY concept could be adapted for our agent prompts (e.g., pre-mortem before architecture decisions).

---

## 5. Skill Nudge System (skill_nudge.py)

### 5.1 Architecture

The skill nudge is a **2-Tier Keyword Matching Engine** that suggests relevant skills/protocols based on user prompt content:

```
User Prompt --> Negative Filter --> Tier 1 (Primary Keywords) --> Match!
                                --> Tier 2 (2+ Secondary Keywords) --> Match!
                                --> No Match (return empty)
```

### 5.2 How It Works

**SKILL_REGISTRY** (hardcoded dict) maps skill names to keyword configurations:

```python
SKILL_REGISTRY = {
    "Protocol 367: High Win-Rate Supremacy": {
        "primary": ["win rate", "kelly criterion", ...],   # Any ONE matches -> Tier 1 (conf=0.9)
        "secondary": ["trading", "risk", "drawdown", ...], # Need 2+ matches -> Tier 2 (conf=0.5-0.85)
        "hint": "Mathematical proof that High WR / Low RR dominates."
    },
    ...
}
```

**Matching logic**:
1. **Negative filter**: Skip if prompt contains "hello", "thanks", "test" etc.
2. **Tier 1**: Any single primary keyword match -> confidence 0.9
3. **Tier 2**: 2+ secondary keyword matches -> confidence scales (0.5 + 0.1 per match, max 0.85)
4. Sort by confidence descending, return top N results

**Output format**:
```python
[{"skill": "Protocol 367", "confidence": 0.9, "hint": "...", "tier": 1, "matched_keywords": [...]}]
```

### 5.3 Comparison with Our Skill Routing

| Aspect | Athena Skill Nudge | Our Skill Routing |
|--------|-------------------|-------------------|
| **Mechanism** | Python keyword matching (programmatic) | CLAUDE.md inline rules + Claude Code auto-routing |
| **Registry** | Hardcoded dict in `skill_nudge.py` | `SKILLS_INDEX.md` + YAML frontmatter descriptions |
| **Trigger** | Every user prompt scanned | Context triggers in CLAUDE.md blocking rules |
| **Output** | Suggestion with confidence score | Direct loading of skill file |
| **Extensibility** | Edit Python code to add skills | Add new SKILL.md file + update index |
| **Semantic understanding** | None (pure keyword matching) | LLM-based (Claude understands context) |

**Key Insight**: Athena's skill nudge is a **rules engine** (fast, deterministic, no LLM cost). Our system relies on **LLM routing** (slower, more context-aware, costs tokens). Athena's approach is better for high-volume suggestion (every prompt), while ours is better for nuanced context understanding. A hybrid could be valuable: keyword pre-filter -> LLM refinement.

---

## 6. Skill Telemetry System (skill_telemetry.py)

### 6.1 Architecture

A **JSONL append-only log** that tracks skill invocations:

```
.athena/skill_usage.jsonl
```

Each record:
```json
{
    "skill": "Protocol 367",
    "session": "2026-02-23-06",
    "timestamp": "2026-02-23T05:00:00",
    "trigger": "auto"  // or "manual"
}
```

### 6.2 Core API

| Function | Purpose |
|----------|---------|
| `log_skill_invocation()` | Record a skill usage event |
| `log_skill_change()` | Record when a skill file is added/modified/deleted |
| `get_skill_stats(days=30)` | Aggregated stats (count, last_used, auto_pct, top skills) |
| `get_dead_skills(known_skills, days=90)` | Find skills with 0 invocations in period |

### 6.3 What It Tracks

- **Invocation count** per skill over a time window
- **Auto vs manual trigger ratio** (what % were suggested by nudge vs user-initiated)
- **Session coverage** (which sessions used which skills)
- **Dead skills** (registered but never invoked in N days)
- **Skill file changes** (hot-reload events from file watcher daemon)

### 6.4 Comparison with Our System

**We have no equivalent.** Our system has no telemetry on which skills are used, how often, or whether they're effective. This is a significant gap:

| What Athena Tracks | What We Track |
|--------------------|---------------|
| Skill usage frequency | Nothing |
| Auto vs manual invocations | Nothing |
| Dead/unused skills | Nothing |
| Skill file changes | Nothing |
| Per-session skill coverage | Nothing |

**Recommendation**: Adding telemetry would help us:
1. Identify which skills are actually used vs dead weight
2. Measure auto-trigger accuracy
3. Track skill evolution over time
4. Prune unused skills with data

---

## 7. Workflow Deep-Dives

### 7.1 /start (Session Boot)

Ultra-low latency boot (~2K tokens):
1. Load Core_Identity.md (laws, identity, RSI)
2. Load project_state.md (workspace state)
3. Create new session log
4. Triple-Lock Reminder: Search -> Save -> Speak (every response)

**vs Our Session Start**: Our CLAUDE.md auto-behavior reads `activeContext.md` + `knowledge.md` + queries Graphiti. Similar in spirit but Athena's is a standalone workflow file while ours is inline rules.

### 7.2 /end (Session Close)

1. Review all checkpoints from session log
2. Identify key decisions and insights
3. Fill session log sections (Topics, Decisions, Action Items)
4. Git commit the session log

**vs Our After Task Completion**: Our system updates `activeContext.md` + `daily/{date}.md` + optionally `knowledge.md` + Graphiti. More structured but similar purpose.

### 7.3 /brief (Pre-Prompt Clarification)

The most sophisticated workflow, featuring:
- **4 variants**: Core, ++, build, research
- **Interview mode** (v3.1): Iterative questioning (max 10 per turn, no arbitrary cap)
- **Semantic Pre-Load**: Auto-searches knowledge base before drafting brief
- **Output**: Writes `_SPEC.md` to `.context/specs/`

**vs Our Planning**: We use `work/PIPELINE.md` for multi-phase tasks. Athena's `/brief` is more focused on *requirements gathering* before execution, while our pipeline is *execution tracking*.

### 7.4 /refactor (Workspace Optimization)

10-phase, 15-30 minute workflow:
1. Mode activation (ultrathink)
2. Determine refactor level (Hygiene/Component/Architecture/Rewrite)
3. Run /diagnose
4. Pre-remediation git checkpoint
5. Fix orphans, broken links
6. Optimization pass (merge, archive, normalize)
7. Session log archive
8. Supabase memory sync
9. Cache maintenance + context compression
10. Verification gate + index regeneration + commit

**Unique**: This is a *workspace maintenance* workflow. We have nothing equivalent. Our system maintains itself through CLAUDE.md rules but has no dedicated optimization workflow.

### 7.5 /audit (Cross-Model Validation)

Multi-phase audit with:
- **Recursion limit** (max 2 recursive calls)
- **No-Touch List** (files never auto-modified: .env, auth, migrations, identity)
- **Gemini vs Claude protocol**: Each model audits the other's blind spots
- **Fact-check with web search** for claim verification
- **Tie-breaking protocol**: External source > test execution > user preference > protocol library

**Unique concept**: Cross-model adversarial auditing. We have no equivalent.

### 7.6 /tutorial (Onboarding)

7-stage guided walkthrough:
1. Welcome (what you cloned)
2. Core Loop (/start -> Work -> /end)
3. Build Your Profile (15-25min interview)
4. Search Demo (show RAG in action)
5. Save & Checkpoint
6. Key Commands reference
7. Graduation

**Notable**: The onboarding interview builds a `user_profile.md` that personalizes all future interactions. We have no onboarding flow.

---

## 8. Skills System (examples/skills/)

### 8.1 Structure

```
examples/skills/
  README.md
  coding/
    diagnostic-refactor/
      SKILL.md
  research/    (TODO)
  communication/ (TODO)
```

### 8.2 Skill File Format (SKILL.md)

Skills use YAML frontmatter similar to our system:

```yaml
---
name: Diagnostic-First Refactoring
description: A non-destructive analysis protocol for refactoring code.
created: 2026-02-04
source: r/vibecoding community pattern
---
```

The body contains:
1. **The Prompt** (universal polyglot system prompt)
2. **Output Format** (structured template, e.g., "Bill of Materials")
3. **Execution Workflow** (numbered steps)
4. **Comparison Table** (traditional vs this approach)

### 8.3 Example: Diagnostic-First Refactoring

The "Surgeon's Scan" pattern:
1. **Diagnose first, cut second** - AI produces analysis report before any code edits
2. **Bill of Materials output**: Issue Matrix table with LOC reduction estimates
3. **Granular approval**: User approves specific line items before AI executes changes
4. **5 focus areas**: Dead code, cognitive complexity, redundancy, performance, modernization

### 8.4 Comparison with Our Skills

| Aspect | Athena Skills | Our Skills |
|--------|--------------|------------|
| **Count** | 1 implemented + 2 TODO categories | 11 active skills |
| **Maturity** | Early stage (mostly planned) | Production (optimized from 30+ to 11) |
| **Format** | YAML frontmatter + prompt + workflow | YAML frontmatter + description + checklist |
| **Scope** | Prompt engineering patterns | Engineering procedures |
| **Integration** | Manual read + follow | Auto-loaded descriptions, on-demand bodies |
| **Nudge** | skill_nudge.py suggests relevant skills | CLAUDE.md context triggers |
| **Telemetry** | skill_telemetry.py tracks usage | None |

---

## 9. Unique Patterns Worth Adopting

### 9.1 Command Stacking / Composability

```
/think /search /research -> "Triple Crown Mode"
```

Our system has no composable mode stacking. We could add:
```
/expert-panel /deep-research -> Combined expert analysis with web research
```

### 9.2 Skill Telemetry

Athena's JSONL-based tracking of which skills are used, how often, and whether auto-suggested. Simple to implement, high value for optimization.

### 9.3 Tiered Reasoning Depth

Explicit depth tiers (normal -> /think -> /ultrathink) with token budgets. Our system has no concept of reasoning depth control. Could map to:
- Normal: Standard agent execution
- Deep: Extended thinking budget
- Ultra: Parallel multi-agent analysis (our Expert Panel)

### 9.4 Workspace Maintenance Workflow

`/refactor` as a dedicated multi-phase maintenance procedure. We could create a periodic "health check" workflow for our template projects.

### 9.5 `// turbo` Annotation

Marking steps as safe to auto-run without user confirmation. We could use this in our pipeline phase templates.

### 9.6 Negative Keywords in Skill Nudge

Simple but effective: don't suggest skills for greetings ("hello", "thanks"). Prevents noise in low-stakes interactions.

### 9.7 Dead Skills Detection

`get_dead_skills()` finds registered skills with 0 invocations. Data-driven pruning instead of gut-feel cleanup.

### 9.8 PROMPT_LIBRARY as Reusable Thinking Patterns

Curated meta-prompts (Pre-Mortem, Assumption Auditor, MECE Breakdown) that can be applied across domains. Could adapt for our agent team prompts.

---

## 10. Gaps in Athena's System

### 10.1 No Agent Team Orchestration

Athena is designed for a **single human-AI pair**. It has no concept of:
- Multiple agents working in parallel (our TeamCreate)
- Agent type registry with role-specific tools
- Worktree-based parallel development
- QA validation loops between agents

### 10.2 No Pipeline State Machine

No equivalent of our `work/PIPELINE.md` with `<- CURRENT` markers. Athena's `/plan` creates a `task.md` but lacks:
- Multi-phase execution with gates
- Compaction recovery protocol
- Phase transition protocol with git checkpoints

### 10.3 Skills System Is Immature

Only 1 skill implemented vs our 11. The skill_nudge registry is hardcoded in Python, not declarative. The skills directory is mostly TODO.

### 10.4 No Compaction Recovery

Athena has no protocol for surviving context compaction. Our system has explicit "THE SUMMARY IS A HINT, NOT TRUTH" recovery procedures.

### 10.5 Workflow Explosion Risk

49+ workflows create maintenance burden. Many in `examples/workflows/` appear to be niche (ugc-factory, voice-agent-deploy, archive-client). Our approach of consolidating into 11 skills + inline rules is more maintainable.

---

## 11. Summary Comparison Table

| Dimension | Athena | Our System | Winner |
|-----------|--------|------------|--------|
| **Workflow count** | 49+ slash commands | 7 commands + 11 skills | Athena (breadth), Ours (focus) |
| **Invocation** | `/command` in chat | `/command` + auto-triggers | Tie |
| **Composability** | Command stacking (/think /search) | None | Athena |
| **Depth control** | Explicit tiers (think/ultrathink) | Expert Panel (implicit) | Athena |
| **Skill suggestion** | Keyword matching (programmatic) | LLM routing (semantic) | Hybrid ideal |
| **Telemetry** | JSONL skill tracking | None | Athena |
| **Agent orchestration** | None (single AI) | Full team system | Ours |
| **Pipeline execution** | /plan creates task.md | PIPELINE.md state machine | Ours |
| **Compaction recovery** | None | Full protocol | Ours |
| **Maintenance** | /refactor, /diagnose, /audit | Manual / inline rules | Athena |
| **Onboarding** | /tutorial (7 stages) | /init-project | Athena |
| **Skill maturity** | 1 implemented | 11 optimized | Ours |
| **Prompt Library** | 14 reusable meta-prompts | None (inline only) | Athena |

---

## 12. Recommendations for Our System

### High Priority
1. **Add Skill Telemetry**: Adapt Athena's JSONL pattern to track which skills/guides are actually loaded and used
2. **Add Dead Skills Detection**: Data-driven identification of unused skills for pruning
3. **Adopt `// turbo` annotation**: Mark auto-runnable steps in pipeline phase templates

### Medium Priority
4. **Create Workspace Health Workflow**: Adapt /diagnose concept for template project maintenance
5. **Add Prompt Library**: Curate reusable thinking patterns for agent team prompts (Pre-Mortem, MECE, etc.)
6. **Implement Command Composability**: Allow combining modes (e.g., `/expert-panel /research`)

### Low Priority / Consider
7. **Keyword Pre-Filter for Skill Routing**: Athena's approach could reduce LLM routing cost
8. **Onboarding Tutorial**: Guided first-use experience for template users
9. **Cross-Model Audit Concept**: Interesting for QA but adds significant complexity
10. **Reasoning Depth Tiers**: Explicit token budget control per task complexity

---

*End of A9 Analysis*
