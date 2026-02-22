# Agent Chains Guide

> On-demand guide for sequential agent pipelines where output becomes input.
> Loaded via: `cat .claude/guides/agent-chains.md`

---

## 1. What Are Agent Chains?

Agent chains are **sequential pipelines** of specialized subagents where each agent's output becomes the next agent's input. Unlike parallel Agent Teams (all work simultaneously), chains enforce quality through specialization and fresh perspectives at each step.

**Key principle:** Each agent in the chain has a SINGLE focused role. The chain produces higher quality than one agent doing everything.

**Analogy:** An assembly line where each station adds value. A document goes through Gatherer, Researcher, Writer, Critic — each bringing expertise the others lack.

---

## 2. When to Use / When Not

**Use when:**
- Deep quality is needed (specs, architecture decisions, security-critical code)
- Creative tasks benefit from critique cycles
- A single agent tends to miss issues or produce shallow output
- The task has natural sequential decomposition (each step depends on the previous)
- You need "fresh eyes" at each step to catch blind spots

**Do NOT use when:**
- The task is simple (1-2 files, straightforward change)
- Time is critical and parallel execution would be faster
- The task has no natural decomposition into sequential steps
- Subtasks are independent of each other (use Agent Teams instead)
- The expected quality gain does not justify the overhead

**Decision rule:** If subtasks are independent, use Agent Teams. If each step feeds the next, use Agent Chains. If both apply, combine them (chain phases where each phase may use a team internally).

---

## 3. Built-in Chain Patterns

### 3.1 Spec Chain (4 agents, sequential)

**Purpose:** Create high-quality specifications from vague requirements.

```
Agent 1: Gatherer
  Input:  User request (conversation, ticket, or brief)
  Role:   Extract requirements, identify ambiguities, list assumptions
  Output: work/requirements-raw.md (structured requirements list)

Agent 2: Researcher
  Input:  work/requirements-raw.md + codebase access
  Role:   Analyze existing codebase for relevant patterns, dependencies, constraints
  Output: work/requirements-context.md (requirements enriched with codebase context)

Agent 3: Writer
  Input:  work/requirements-context.md
  Role:   Write formal specification with acceptance criteria, edge cases, non-goals
  Output: work/user-spec.md (draft)

Agent 4: Critic
  Input:  work/user-spec.md (draft)
  Role:   Find gaps, contradictions, missing edge cases, suggest improvements
  Output: work/user-spec.md (final, with critic notes resolved)
```

**When to use:** Before implementing any feature with unclear or complex requirements. The spec chain turns "I want X" into a precise, actionable specification.

---

### 3.2 QA Chain (3 agents, loop max 3)

**Purpose:** Validate implementation quality through review-fix cycles.

```
Agent 1: Reviewer
  Input:  Changed files + acceptance criteria
  Role:   Find issues, classify as CRITICAL / IMPORTANT / MINOR
  Output: work/qa-issues.md (structured issues list)

Agent 2: Fixer
  Input:  work/qa-issues.md + source files
  Role:   Fix all CRITICAL and IMPORTANT issues
  Output: Fixed source files + work/qa-fixes.md (what was fixed and how)

Agent 3: Re-reviewer (fresh agent, NOT Agent 1)
  Input:  Fixed files + work/qa-issues.md + acceptance criteria
  Role:   Verify fixes resolved issues, check for new issues introduced
  Output: Updated work/qa-issues.md or "QA PASS"

Loop: If CRITICAL/IMPORTANT issues remain -> back to Agent 2 (max 3 iterations)
Exit: "QA PASS" or max iterations reached (escalate to human)
```

**When to use:** After implementing any non-trivial feature, especially when the code touches multiple modules or has complex logic. The fresh Re-reviewer catches issues the original Reviewer might accept due to anchoring bias.

---

### 3.3 Debug Chain (4 agents, sequential)

**Purpose:** Systematic debugging of complex issues that resist quick fixes.

```
Agent 1: Reproducer
  Input:  Bug report, error log, or failing test
  Role:   Create minimal reproduction, identify exact failure point
  Output: work/reproduction-report.md (steps, stack trace, affected files)

Agent 2: Analyzer
  Input:  work/reproduction-report.md + codebase access
  Role:   Trace root cause through code, form hypotheses ranked by likelihood
  Output: work/analysis.md (3 ranked hypotheses with supporting evidence)

Agent 3: Fixer
  Input:  work/analysis.md + top hypothesis
  Role:   Implement fix for most likely cause, write regression test
  Output: Fixed code + test file

Agent 4: Verifier
  Input:  Fix + original reproduction steps
  Role:   Run reproduction to confirm fix, run full test suite for regressions
  Output: work/verification-report.md (PASS/FAIL + regression results)
```

**When to use:** When a bug has resisted quick debugging attempts, involves multiple interacting systems, or when the root cause is unclear. The chain forces systematic analysis rather than trial-and-error.

**If Verifier reports FAIL:** Loop back to Analyzer with the verification report as additional context. Max 2 loops before escalating to human.

---

### 3.4 Architecture Decision Chain (3 agents, sequential)

**Purpose:** Make well-reasoned architecture decisions with adversarial review.

```
Agent 1: Option Explorer
  Input:  Decision context, constraints, priority ladder
  Role:   Research 3-5 viable options with trade-offs for each
  Output: work/options.md (structured comparison matrix)

Agent 2: Devil's Advocate
  Input:  work/options.md
  Role:   Attack each option — find failure modes, hidden costs, scaling issues
  Output: work/critique.md (weaknesses and risks per option)

Agent 3: Decision Maker
  Input:  work/options.md + work/critique.md + priority ladder
  Role:   Select best option given constraints, document rationale
  Output: ADR file in .claude/adr/ (architecture decision record)
```

**When to use:** Before making any decision that is hard to reverse: database choices, API contracts, module boundaries, framework selections. The Devil's Advocate step prevents confirmation bias.

---

### 3.5 Insight Extraction Chain (2 agents, sequential)

**Purpose:** Extract and persist learnings from completed work sessions automatically.

```
Agent 1: Diff Analyzer
  Input:  git diff of recent changes (or specific commit range)
  Role:   Analyze what changed, identify patterns used, discover gotchas
  Output: work/session-insights-raw.md (structured analysis)

  Process:
  1. Run git diff HEAD~N (where N = commits since last extraction)
  2. For each changed file: identify purpose, patterns used, potential gotchas
  3. Categorize findings: file_insights, patterns, gotchas, what_worked, what_failed
  4. Output structured markdown

Agent 2: Memory Updater
  Input:  work/session-insights-raw.md + existing .claude/memory/ files
  Role:   Deduplicate and merge new insights into typed memory
  Output: Updated .claude/memory/ files (knowledge.md, daily/YYYY-MM-DD.md)

  Process:
  1. Read existing knowledge.md — check for duplicates before adding
  2. Append new patterns to knowledge.md Patterns section (dedup first)
  3. Append new gotchas to knowledge.md Gotchas section (dedup first)
  4. Create or append to daily/YYYY-MM-DD.md with session data
  5. Delete work/session-insights-raw.md (temporary)
```

**When to use:** After EVERY implementation phase — triggered by Phase Transition Protocol between pipeline phases. Can also be run manually after significant coding sessions. The chain ensures no learnings are lost between phases.

**Key principle:** Agent 1 (Diff Analyzer) is READ-ONLY — it analyzes but doesn't modify memory files. Agent 2 (Memory Updater) handles all writes with deduplication. This separation prevents accidental data loss.

**Integration:**
- Phase Transition Protocol triggers this between pipeline phases
- Pipeline QA_REVIEW phase triggers this before QA review (ensures QA agent has latest context)
- Manual trigger: when you want to persist session learnings before ending a session

---

## 4. How to Execute a Chain

### 4.1 Using Task Tool (in-session)

Best for chains of 2-4 agents where total work fits in one session.

```
For each agent in the chain:
  1. Prepare input (output of previous agent, or initial context for first agent)
  2. Spawn agent via Task tool with a focused prompt:
     - State the agent's SINGLE role clearly
     - Specify exact input file(s) to read
     - Specify exact output file to write
     - Include acceptance criteria for the output
  3. Wait for agent to complete
  4. Read output file and validate quality before proceeding
  5. Pass output to next agent (reference the file path in the next prompt)
```

### 4.2 Using Pipeline Phases (cross-session)

Best for longer chains or when each step needs fresh 200K context.

```
Each chain step = one pipeline phase in work/PIPELINE.md
Phase outputs become next phase inputs via files in work/
Each phase gets a fresh agent with full context budget

Example PIPELINE.md entry:
  Phase 3: Write Specification    <- CURRENT
    Mode: SINGLE_AGENT
    Input: work/requirements-context.md
    Output: work/user-spec.md
    Acceptance: Has acceptance criteria, edge cases, non-goals sections
```

### 4.3 Hybrid: Chain + Team

Some chain steps can internally use Agent Teams for parallel work.

```
Example: Debug Chain where Analyzer examines 3 hypotheses in parallel

Chain step 1: Reproducer (single agent)
Chain step 2: Analyzer team (3 agents, one per hypothesis, parallel)
Chain step 3: Fixer (single agent, takes top-ranked hypothesis)
Chain step 4: Verifier (single agent)
```

---

## 5. Chain Execution Rules

1. **Fresh agent per step** — NEVER reuse the same agent for multiple chain steps. Each agent brings unbiased perspective. Context pollution defeats the purpose of chains.

2. **Explicit output format** — Every agent MUST write its output to a specific file with a defined structure. No "just tell me what you found" — write it to `work/{output-name}.md`.

3. **Validation between steps** — The lead (you) reads each agent's output before spawning the next. If the output is insufficient, re-run that step or provide feedback, do not propagate bad output forward.

4. **Fail-fast** — If any agent produces low-quality output that cannot be salvaged, STOP the chain. Investigate why and fix the prompt or approach before continuing.

5. **Max chain length: 6 agents** — Longer chains have diminishing returns and high overhead. If you need more steps, restructure as pipeline phases.

6. **Bounded loops only** — Any loop in the chain (like QA review-fix) MUST have a maximum iteration count (typically 3). Unbounded loops can run indefinitely.

7. **Output files persist** — All intermediate outputs stay in `work/` for traceability. Do not delete them until the chain completes successfully.

---

## 6. Creating Custom Chains

Use this template when defining a new chain:

```markdown
### Chain: {Name} ({N} agents, {sequential | loop max N})

**Purpose:** {One sentence: what this chain achieves}
**When to use:** {Trigger conditions}

Agent 1: {Role Name}
  Input:  {What it receives — file path or description}
  Role:   {Single focused responsibility}
  Output: work/{output-file}.md

Agent 2: {Role Name}
  Input:  work/{previous-output}.md
  Role:   {Single focused responsibility}
  Output: work/{output-file}.md

...

Exit condition: {When the chain is considered complete}
Failure mode: {What to do if a step fails}
```

**Guidelines for custom chains:**
- Each agent should have exactly ONE responsibility
- Name roles by function (Gatherer, Analyzer, Critic), not by implementation
- Always specify concrete file paths for inputs and outputs
- Include exit conditions and failure modes
- Consider whether any step could be parallelized (hybrid chain + team)

---

## 7. Anti-Patterns

| Anti-Pattern | Why It Fails | Instead Do |
|---|---|---|
| Chaining simple tasks | Overhead exceeds benefit for trivial work | Just do it directly |
| Reusing agents across steps | Context pollution, anchoring bias, no fresh perspective | Always spawn fresh agent per step |
| Unbounded loops | Can run forever burning tokens | Always set max iterations (2-3) |
| Skipping validation between steps | Garbage propagates and compounds | Lead validates every intermediate output |
| Chains longer than 6 steps | Diminishing returns, high latency | Restructure as pipeline phases |
| Vague output specs | Next agent cannot parse input reliably | Define exact file path and structure |
| Running chain when tasks are independent | Sequential bottleneck for no quality gain | Use Agent Teams for parallel work |
| No failure mode defined | Chain hangs when a step produces bad output | Define fail-fast rules per chain |

---

## 8. Chains vs Teams vs Pipeline — Quick Reference

| Dimension | Agent Chains | Agent Teams | Pipeline Phases |
|---|---|---|---|
| Execution | Sequential | Parallel | Sequential (across sessions) |
| Best for | Quality through specialization | Speed through parallelism | Large multi-session work |
| Agent count | 2-6 per chain | 2-10 per team | 1+ per phase |
| Output flow | Each feeds the next | All feed the lead | Files persist across sessions |
| Overhead | Medium | Medium | Low (file-based) |
| Use when | Steps depend on each other | Steps are independent | Work exceeds one session |

**Built-in chains:** Spec (3.1), QA (3.2), Debug (3.3), Architecture Decision (3.4), Insight Extraction (3.5).

Combinations are valid: a pipeline phase can execute an agent chain, and a chain step can spawn an agent team internally.
