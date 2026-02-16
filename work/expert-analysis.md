---
date: 2026-02-16
task: "Deep research: autonomous pipeline architecture for Claude Code"
panel_size: 5
domains: [orchestration, persistence, templates, pipeline, anti-drift]
experts: [orchestration-researcher, patterns-researcher, persistence-researcher, doccheck-analyzer, web-deep-researcher]
---

# Expert Analysis: Autonomous Pipeline Architecture

## Task Scope

Comprehensive analysis of 12+ repositories/sources for building reliable autonomous development pipelines in Claude Code, compared against our current template system and real project usage (DocCheck Bot, 45+ sessions).

## Sources Analyzed

| Source | Stars | Type | Key Pattern |
|--------|-------|------|-------------|
| claude-flow (ruvnet) | 14k+ | Orchestration | SQLite memory + swarm topologies |
| claude-squad (smtg-ai) | 5.6k+ | Parallel agents | Git worktree isolation per agent |
| oh-my-claudecode | 1k+ | Plugin framework | 31 hooks, 7 execution modes, XML semantic tags |
| claude-code-templates (davila7) | 2k+ | Component marketplace | 600+ agents, installable components |
| claude-commands (badlogic) | 484 | State machine | 150 LOC markdown = full pipeline |
| claude-code-skills (levnikolaevich) | — | Skill hierarchy | L0-L3 orchestrator, 4-verdict quality gate |
| wshobson/agents | — | Plugin ecosystem | 99 agents, 3-tier model routing |
| ClaudeFast | — | Hook system | Context monitoring, threshold backups |
| Ralph Loop / ralph-wiggum | — | Fresh-context loop | New process per atomic task |
| ardmhacha24 | — | Enhanced Ralph | 4-layer learning system |
| Manus team | — | Production patterns | Todo rewriting, controlled variation |
| Shrivu Shankar | — | Enterprise patterns | Document & Clear, test-gated commits |
| Boris Cherny | — | CLAUDE.md patterns | Self-correcting error-to-rule loop |
| DocCheck Bot | — | Our real project | 45+ sessions, 335 tests |

---

## Critical Problem: Agent Teams Mode Lost After Compaction

### Problem Statement
User reports that after 1-2 compactions, the lead agent "forgets" to use Agent Teams Mode and starts doing everything sequentially. This dramatically increases execution time for complex tasks.

### Root Cause Analysis
1. **Silent Rule Dropping** — research confirms LLMs silently ignore instructions when context has 7-10+ rules after compaction
2. **AGENT TEAM PROPOSAL** is located mid-CLAUDE.md (lines 68-93) — NOT in the high-attention zone (beginning/end)
3. **No `# Summary instructions`** section telling compactor what to preserve
4. **Auto-behaviors are "soft" enforcement** — CLAUDE.md text, not hooks. Compaction treats them as "resolved" and compresses them out
5. **"Lost in the Middle" phenomenon** — information in the middle of context has lowest recall

### Why This Happens Specifically to Agent Teams
- Agent Teams Mode is a BEHAVIORAL rule ("when you see 3+ independent tasks, propose a team")
- Behavioral rules are the FIRST thing compaction drops (they look like "resolved instructions")
- Contrast with HARD CONSTRAINTS ("never commit secrets") which look like ongoing rules and survive better
- After compaction, lead agent retains WHAT to do but loses HOW to do it (Agent Teams is a "how")

---

## What Works in Our System (Keep These)

| Pattern | Evidence | Verdict |
|---------|----------|---------|
| Memory system (activeContext.md) | 31 commits in DocCheck Bot, high-quality Did/Decided/Learned/Next entries | WORKING WELL |
| Expert Panel | Used 4+ times with real 4-agent analysis, produces actionable expert-analysis.md | WORKING WELL |
| Verification culture | 300+ tests, test counts in every session log | WORKING WELL |
| STATE.md tracking | Updated every session, clear phase progression (15 phases) | WORKING WELL |
| ADR system | 4+ active decisions with rationale | WORKING WELL |
| Session bridging | Next Steps to Did pattern verifiable across sessions | WORKING WELL |
| Auto-behaviors concept | Correct approach per ALL research sources | CORRECT APPROACH |
| Agent Teams (TeamCreate) | Effective fresh-context per teammate, 10-agent teams work | WORKING WELL |
| Skills system (SKILL.md frontmatter) | Matches oh-my-claudecode and wshobson patterns | GOOD STANDARD |
| No hooks decision | Confirmed: hooks unreliable on Windows, oh-my-claudecode 31 hooks = fragility | CORRECT DECISION |

---

## What's Missing (Gap Analysis)

### GAP 1: No Compaction Recovery Mechanism (CRITICAL)
**Problem:** After compaction, lead agent loses behavioral rules (Agent Teams Mode, plan execution protocol, etc.)
**Research says:** Use `# Summary instructions` in CLAUDE.md + state machine files read after every compaction
**Our status:** No summary instructions, no post-compaction re-read protocol
**Impact:** Agent Teams Mode lost -> sequential execution -> 3-5x slower

### GAP 2: No State Machine File with Explicit Markers (HIGH)
**Problem:** STATE.md is prose-based, requires reading 134 lines to find current state
**Research says:** Use markers like `<- CURRENT`, machine-parseable status, one file per pipeline run
**Our status:** STATE.md has phase descriptions, no explicit markers
**Impact:** After compaction, agent can't quickly orient itself

### GAP 3: CLAUDE.md Not Customized Per Project (HIGH)
**Problem:** DocCheck Bot CLAUDE.md still says "Project: Claude Project Template Update"
**Research says:** CLAUDE.md should be project-specific contract with tech stack, commands, invariants
**Our status:** Generic template text copied verbatim, no project-specific context
**Impact:** Agent lacks project-specific constraints, makes generic decisions

### GAP 4: activeContext.md = Layer 3 Noise Accumulation (MEDIUM)
**Problem:** 438 lines with 10+ historical session logs, no rotation
**Research says:** Three-layer model: activeContext should be Layer 2 (working set), not Layer 3 (history)
**Our status:** Mixing current focus + historical sessions in one growing file
**Impact:** Context waste when loading, relevant info buried in noise

### GAP 5: No Consolidated Patterns File (MEDIUM)
**Problem:** Project-wide learnings scattered across session logs
**Research says:** ardmhacha24 Layer 1 = consolidated patterns, highest-signal, read FIRST every iteration
**Our status:** Patterns in activeContext.md session logs, not extracted/consolidated
**Impact:** Same mistakes repeated across sessions

### GAP 6: No Self-Correcting CLAUDE.md Loop (MEDIUM)
**Problem:** Agent makes same mistakes across sessions
**Research says:** Boris Cherny: every error triggers CLAUDE.md update, system improves with each failure
**Our status:** Mistakes go into activeContext.md Learned section but never become CLAUDE.md rules
**Impact:** No compounding improvement of agent behavior

### GAP 7: No Model-Aware Agent Routing (LOW)
**Problem:** All teammates use same model regardless of task complexity
**Research says:** wshobson 3-tier (42 Opus, 39 Sonnet, 18 Haiku), oh-my-claudecode 3-tier routing
**Our status:** No model specification per role
**Impact:** Overpaying for simple tasks, underperforming on complex ones

### GAP 8: No Fresh-Context Pattern for Lead Agent (LOW-MEDIUM)
**Problem:** Lead agent accumulates context across multiple phases
**Research says:** Ralph Loop: new process per phase, state in files
**Our status:** Lead runs entire session, relies on compaction survival
**Impact:** Lead agent degrades over long sessions

---

## Recommendations: 5 Tiers

### Tier 1: CLAUDE.md Compaction Hardening (IMMEDIATE, no code)

**1.1 Add Summary Instructions section (TOP of CLAUDE.md)**
```markdown
# Summary instructions
When compacting, ALWAYS preserve:
- AGENT TEAM PROPOSAL trigger and criteria (3+ independent tasks -> team)
- Current pipeline phase from work/PIPELINE.md
- BLOCKING RULES section (all 5 rules)
- HARD CONSTRAINTS section
After compaction, immediately re-read work/PIPELINE.md and work/STATE.md.
```

**1.2 Move AGENT TEAM PROPOSAL to HIGH-ATTENTION zone**
Currently at lines 68-93 (middle). Move to TOP, right after SESSION START. Compaction preserves beginning and end better.

**1.3 Add "Always Y" to every "Never X" constraint**
Research (Shankar): "Never pure negative constraints" are ineffective.
- "Не делать всё самому" -> "Не делать всё самому: ВСЕГДА предлагай Agent Teams для 3+ задач"
- "Не говорить готово без verification" -> "Не говорить готово: ВСЕГДА запускай verification-before-completion"

**1.4 Shorten CLAUDE.md to ~300 lines**
Research: >7-10 rules leads to silent dropping. Move detailed sections to on-demand guides. Keep CLAUDE.md as a CONTRACT (Layer 1), not a manual.

### Tier 2: Pipeline State Machine File (HIGH PRIORITY)

Create `work/PIPELINE.md` — a machine-readable file that survives compaction:

```markdown
# Pipeline: [Task Name]
## Status: IN_PROGRESS
## Mode: AGENT_TEAMS (3+ independent tasks detected)
## Current Phase: 2 of 4

- [x] Phase 1: Analysis <- DONE (Agent Teams: 3 researchers)
- [ ] Phase 2: Implementation <- CURRENT (Agent Teams: 4 developers)
  - Mode: AGENT_TEAMS
  - Tasks: task-1.md, task-2.md, task-3.md, task-4.md
  - Acceptance: all tests pass
- [ ] Phase 3: Fix bugs (Agent Teams: dispatching-parallel-agents)
- [ ] Phase 4: Verification (Agent Teams: 2 reviewers)

## Execution Rule
EVERY phase with 3+ tasks -> USE AGENT TEAMS (TeamCreate)
DO NOT execute phases sequentially when parallelizable
```

**Auto-behavior addition:**
```
## AFTER COMPACTION (always)
1. Re-read work/PIPELINE.md
2. Re-read work/STATE.md
3. Check current phase Mode: if AGENT_TEAMS, propose team
4. Continue from <- CURRENT marker
```

### Tier 3: Three-Layer Context Separation (MEDIUM PRIORITY)

**3.1 Split activeContext.md:**
- `activeContext.md` — ONLY current focus + recent decisions + next steps (Layer 2, max 50 lines)
- `sessionHistory.md` — historical session logs (Layer 3, rotated)
- Archive sessions older than 5 entries

**3.2 Create consolidated-patterns.md:**
- Extract recurring patterns from session logs
- Read FIRST at session start (like ardmhacha24 Layer 1)
- Example: "Phone truncation: use smart truncation, not generic", "Always check field_mappings/ before modifying extraction"

**3.3 Customize CLAUDE.md per project:**
- Replace template header with actual project name/description
- Add project-specific tech stack, commands, invariants
- Add project-specific "common mistakes" from session history

### Tier 4: Ralph Loop for Autonomous Sessions (MEDIUM PRIORITY)

Create `scripts/ralph.sh` for long-running autonomous work:

```bash
#!/bin/bash
PIPELINE_FILE="work/PIPELINE.md"
PROMPT_FILE="work/PROMPT.md"
MAX_ITERATIONS=20

for i in $(seq 1 $MAX_ITERATIONS); do
  echo "=== Phase $i ==="
  claude -p "$(cat $PROMPT_FILE)" --dangerously-skip-permissions
  git add -A && git commit -m "checkpoint: phase $i"
  if grep -q "PIPELINE_COMPLETE" "$PIPELINE_FILE"; then
    echo "Pipeline complete!"
    break
  fi
done
```

With `work/PROMPT.md`:
```markdown
Read CLAUDE.md, work/PIPELINE.md, and work/STATE.md.
Complete the next unchecked phase.
IMPORTANT: If phase has 3+ tasks, use Agent Teams (TeamCreate).
After completion, update PIPELINE.md (mark done, advance <- CURRENT).
If all phases complete, write PIPELINE_COMPLETE to PIPELINE.md.
```

**Key benefit:** Each phase gets FRESH 200K context. No compaction. Agent Teams Mode instruction is in PROMPT.md which is re-read every iteration.

### Tier 5: Self-Correcting System (LOW PRIORITY, long-term)

**5.1 Error-to-Rule Pipeline:**
Add auto-behavior:
```
## AFTER ERROR (always)
1. If this error could have been prevented by a rule:
   a. Add rule to CLAUDE.md (if project-wide)
   b. Or add to consolidated-patterns.md (if project-specific)
2. Format: "LEARNED: [what happened] -> RULE: [what to do instead]"
```

**5.2 Model-Aware Routing:**
Add to TEAM ROLE SKILLS MAPPING:
```
| Role | Model | Rationale |
|------|-------|-----------|
| Architect/Planner | opus | Complex reasoning |
| Developer/Implementer | sonnet | Standard work |
| Researcher/Explorer | haiku | Fast lookups |
| Reviewer | sonnet | Code analysis |
| Security | sonnet | Pattern matching |
```

**5.3 Quality Gate Enhancement:**
Upgrade verification-before-completion with 4-verdict model:
- **PASS** — all checks green, proceed
- **CONCERNS** — minor issues, document and proceed
- **REWORK** — significant issues, fix and re-verify
- **FAIL** — fundamental problem, escalate to user

---

## Per-Project vs. Global Template

### Answer: BOTH, with clear separation

| Layer | Where | What | Changes How Often |
|-------|-------|------|-------------------|
| **Template infrastructure** | `.claude/shared/templates/new-project/` | Pipeline scripts, skills, guides, CLAUDE.md skeleton | Rarely (template upgrades) |
| **Project CLAUDE.md** | Each project `CLAUDE.md` | Project name, tech stack, commands, invariants, common mistakes | Per project, updated as project evolves |
| **Pipeline file** | Each project `work/PIPELINE.md` | Current task pipeline, phases, agent modes | Per task/session |
| **Memory** | Each project `.claude/memory/` | Session context, patterns, decisions | Every session |

### What goes in template (apply to ALL projects):
- Summary instructions section (compaction hardening)
- AGENT TEAM PROPOSAL auto-behavior (with high-attention placement)
- AFTER COMPACTION auto-behavior (re-read pipeline + state)
- Pipeline file structure (PIPELINE.md template)
- Ralph Loop script (scripts/ralph.sh)
- Three-layer context structure
- Model-aware routing table
- Quality gate 4-verdict model

### What's per-project (customize each time):
- CLAUDE.md header (project name, description, tech stack)
- CLAUDE.md commands section (project-specific CLI commands)
- CLAUDE.md invariants (project-specific constraints)
- consolidated-patterns.md (project-specific learnings)
- work/PIPELINE.md content (current task phases)

---

## Trade-off Matrix

| Criterion | Current System | With Tier 1-2 | With Tier 1-4 (Full) |
|-----------|---------------|---------------|---------------------|
| **Agent Teams survival** | Lost after 1-2 compactions | Survives via Summary Instructions + PIPELINE.md | Guaranteed (fresh context per phase) |
| **Setup complexity** | Zero (CLAUDE.md only) | Low (add sections + PIPELINE.md) | Medium (Ralph script + prompt template) |
| **Compaction resilience** | Low (soft rules) | Medium (state machine + summary) | High (no compaction in Ralph) |
| **Per-project cost** | Minimal | +15 min setup (customize CLAUDE.md) | +30 min (script + prompt + pipeline) |
| **Token efficiency** | Poor (lead accumulates) | Same | Better (fresh context per phase) |
| **Maintenance** | Low | Low | Medium (script + PROMPT.md upkeep) |

---

## Implementation Priority

```
WEEK 1: Tier 1 (CLAUDE.md hardening) + Tier 2 (PIPELINE.md)
  Impact: Agent Teams survival after compaction
  Dependencies: zero
  Apply to: template + DocCheck Bot

WEEK 2: Tier 3 (Three-layer context)
  Impact: cleaner context, faster orientation
  Apply to: DocCheck Bot first, then template

WEEK 3+: Tier 4 (Ralph Loop) + Tier 5 (Self-correcting)
  Impact: full compaction immunity for autonomous sessions
  Test on: real autonomous session in DocCheck Bot
```

---

## Open Questions (Require User Input)

1. **Ralph Loop adoption**: Ready to use `claude -p` headless mode for autonomous sessions? Or prefer staying in interactive mode?

2. **CLAUDE.md size target**: Current CLAUDE.md ~280 lines. Research recommends ~300-500 max. Need to shorten or current size is acceptable?

3. **Model routing**: Want to specify model (opus/sonnet/haiku) per teammate role? Saves tokens but adds complexity.

4. **activeContext.md rotation**: Automatically archive sessions older than 5 entries? Or do you use history for context?

5. **Per-project customization**: Ready to spend 15-30 min customizing CLAUDE.md per /init-project? Or want to maximize automation?
