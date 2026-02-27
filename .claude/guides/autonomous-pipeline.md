# Autonomous Pipeline Guide (v3)

> On-demand guide for executing autonomous development pipelines.
> Loaded via: `cat .claude/guides/autonomous-pipeline.md`

---

## 1. Overview

The autonomous pipeline is a **state machine encoded in markdown** that drives multi-phase development without losing context. Components:

1. **PIPELINE.md** -- state machine with named phases, conditional transitions, and quality gates
2. **Phase Transition Protocol** -- knowledge preservation between phases via typed memory + Graphiti
3. **Agent Teams** -- parallel execution via `Mode: AGENT_TEAMS` on phases with 3+ independent tasks
4. **Quality Gates** -- 4-verdict model (PASS/CONCERNS/REWORK/FAIL) with AUTO/USER_APPROVAL/HYBRID types
5. **QA Validation Loop** -- automated review-fix cycle between implementation and testing
6. **Agent Chains** -- sequential agent pipelines for deep quality (spec chain, QA chain, debug chain)
7. **Deploy Integration** -- git workflow, SSH deployment, health checks, stress testing
8. **Typed Memory** -- structured knowledge persistence (.claude/memory/knowledge.md, daily/)
9. **Complexity Assessment** -- risk-proportional QA depth (.claude/guides/complexity-assessment.md)
10. **Recovery Manager** -- attempt tracking and circular fix detection (work/attempt-history.json)
11. **Graphiti Integration** -- semantic cross-session memory (.claude/guides/graphiti-integration.md)
12. **Focused Prompts** -- role-specific agent prompts (.claude/prompts/)
13. **Agent Registry** -- single source of truth for agent types (.claude/agents/registry.md)

---

## 2. When to Use / When Not

**Use when:** 3+ phases, likely compaction (>60% context), autonomous execution needed, deploy/stress test phases, or user requests "pipeline"/"autonomous mode".

**Do NOT use when:** Simple bug fix (1-2 files), single-phase task, or task requiring constant user feedback.

---

## 3. Pipeline Creation

**Step 1: Analyze.** Break into phases. For each: Mode (`SOLO`/`AGENT_TEAMS`/`SUB_PIPELINE`), Gate Type (`AUTO`/`USER_APPROVAL`/`HYBRID`), transitions (PASS/FAIL/REWORK).

**Step 2: Create work/PIPELINE.md** from `.claude/shared/work-templates/PIPELINE-v3.md`. Delete unused phases, set first phase `<- CURRENT`, set `Status: IN_PROGRESS`. Note: the v3 template includes a QA_REVIEW phase between IMPLEMENT and TEST by default; keep it unless the project has no implementation phases.

**Step 3: Execute.** Read PIPELINE.md, execute phase by phase with Phase Transition Protocol between phases.

---

## 4. Phase Execution Protocol

### SOLO
```
1. Read phase from PIPELINE.md, read Inputs
2. Implement changes, produce Outputs
3. Run quality gate, apply verdict
4. Update state, advance <- CURRENT
```

### AGENT_TEAMS
```
1. Analyze tasks for parallelization
2. TeamCreate (2-5 agents), prompts via .claude/guides/teammate-prompt-template.md
3. MANDATORY: each prompt has ## Required Skills section
4. Verify combined results against gate, apply verdict
```

### SUB_PIPELINE
```
1. Execute referenced Pipeline file to completion (or BLOCKED)
2. Return to parent, apply verdict based on sub-pipeline outcome
```

### AGENT_CHAINS (within a phase)
```
1. Identify chain type (spec, QA, debug, or custom)
2. Execute agents sequentially: output of agent N -> input of agent N+1
3. Each agent is a fresh subagent (never reuse)
4. Reference: .claude/guides/agent-chains.md
```

---

## 5. Phase Transition Protocol

Between completing one phase and starting the next, execute this protocol to preserve knowledge:

### Steps
1. **Git commit checkpoint**: `git add -A && git commit -m "pipeline: {PHASE} complete"` + `git tag pipeline-checkpoint-{PHASE}`
2. **Insight extraction** (2-3 min quick pass):
   - What worked in this phase?
   - What failed or required multiple attempts?
   - New patterns discovered?
   - New gotchas to record?
3. **Update typed memory**:
   - `.claude/memory/knowledge.md` Patterns section — append new patterns (deduplicate)
   - `.claude/memory/knowledge.md` Gotchas section — append new gotchas (deduplicate)
4. **Save to Graphiti**: `add_memory(name="phase_{PHASE}_insight", episode_body=<what was learned>)`
5. **Context refresh**: Re-read `work/PIPELINE.md` + `work/STATE.md` + typed memory files
6. **Advance**: Move `<- CURRENT` marker to next phase, start execution

### Why This Matters
- Interactive mode loses context gradually (compaction, attention decay)
- Phase transitions are natural checkpoints for knowledge preservation
- Without this protocol, insights from early phases are lost by later phases
- Graphiti persists knowledge across sessions, not just within one

### When to Skip
- Never fully skip. At minimum do steps 1 and 6 (commit + advance).
- Steps 2-5 can be abbreviated for trivial phases (e.g., a SOLO phase that only reads files).

### Structured Handoff Format

Agents completing a phase MUST output a structured handoff block. This enables:
- Automatic extraction of learnings for knowledge.md
- Clear file change tracking between phases
- Decision audit trail

See teammate-prompt-template.md for the full handoff format.

---

## 6. Quality Gates

### 4-Verdict Model

| Verdict | Action |
|---------|--------|
| **PASS** | Git checkpoint tag, advance `<- CURRENT` to `On PASS` target |
| **CONCERNS** | Log in Decisions, checkpoint, advance |
| **REWORK** | Increment `Attempts`. If `>= Max` -> FAIL. Else re-execute phase |
| **FAIL** | Set `Status: BLOCKED`, stop pipeline, alert user |

**Priority rule:** Worst verdict wins. FAIL > REWORK > CONCERNS > PASS.

### Gate Types

- **AUTO** -- Shell commands. All exit 0 = PASS, any non-zero = REWORK.
- **USER_APPROVAL** -- Present artifact to user. User picks verdict.
- **HYBRID** -- Auto first. Fail = REWORK (skip user). Pass = ask user for final verdict.

### Execution Protocol
```
1. Phase signals completion -> read Gate from PIPELINE.md
2. Execute checks (commands / prompt / auto+user)
3. Worst verdict wins -> record in work/gate-results/{phase}-attempt-{n}.md
4. Apply: advance, rework, or block
```

---

## 7. Conditional Transitions

Each phase defines its own transitions inline:
```markdown
### Phase: IMPLEMENT  <- CURRENT
- On PASS: -> TEST
- On FAIL: -> FIX
- On REWORK: -> PLAN
- On BLOCKED: -> STOP
```

**Bounded loops:** `Attempts: X of Y` prevents infinite cycling. When `Attempts >= Max`, auto-escalates to BLOCKED.
```
TEST -> FAIL -> FIX -> PASS -> TEST   (loop)
FIX: Attempts 3 of 3 -> BLOCKED       (bounded exit)
```

**Named phases:** UPPERCASE semantic names (SPEC, PLAN, IMPLEMENT, etc.). `On PASS: -> TEST` is self-documenting and survives compaction -- grep `### Phase: TEST` directly.

---

## 8. Phase Templates

Reference: `.claude/shared/work-templates/phases/`

| Template | Purpose |
|----------|---------|
| `SPEC.md` | User spec creation with acceptance criteria |
| `REVIEW.md` | Expert panel analysis |
| `PLAN.md` | Tech spec + task decomposition + wave analysis |
| `IMPLEMENT.md` | Code implementation via Agent Teams |
| `TEST.md` | Test suite execution |
| `FIX.md` | Bug fixing with debugging teams |
| `QA_REVIEW.md` | Automated reviewer+fixer cycle |
| `DEPLOY.md` | SSH deployment + health checks |
| `STRESS_TEST.md` | Locust load testing + performance report |

Delete unused phases from PIPELINE.md. Transitions still work for remaining phases.

---

## 9. Agent Chains

Agent Chains are sequential agent pipelines within a phase. Use when a phase needs multiple specialized perspectives.

**Built-in chains:**
- Spec Chain: Gatherer -> Researcher -> Writer -> Critic
- QA Chain: Reviewer -> Fixer -> Re-reviewer (loop max 3)
- Debug Chain: Reproducer -> Analyzer -> Fixer -> Verifier

**Integration with pipeline:**
- SPEC phase can use Spec Chain for deeper specifications
- QA_REVIEW phase uses QA Chain automatically
- FIX phase can use Debug Chain for systematic debugging

**Full reference:** `cat .claude/guides/agent-chains.md`

---

## 10. Deploy Integration

**Git workflow:** `feature/{name} -> dev -> main -> deploy to server`

**Deploy phases:** GIT_RELEASE (PR + merge + tag) -> DEPLOY (rsync + restart) -> SMOKE_TEST (health check) -> STRESS_TEST (locust).

**SSH deployment:** rsync uploads code, systemctl restarts service. Env vars (`DEPLOY_SSH_HOST`, `DEPLOY_SSH_KEY`, etc.) from `.env` (never committed).

**Health checks:** Poll health endpoint 3x with 5s delay. Check journalctl for errors.

**Stress testing:** Locust with standard config. Thresholds: p95 < 500ms, error rate < 1%. Results: `work/performance-report.md`.

See full details: `work/scalable-pipeline-design-deploy.md`

---

## 11. Compaction Recovery

When compaction occurs during interactive mode:
1. System auto-loads CLAUDE.md (always in context)
2. CLAUDE.md Summary Instructions remind: "re-read PIPELINE.md"
3. Agent reads `work/PIPELINE.md`, finds `<- CURRENT` marker
4. Agent reads `work/STATE.md` for latest results
5. Agent continues from where it left off

**Why v3 survives compaction:**
- `<- CURRENT` on phase header line -- one grep finds location
- Mode field persisted in file, not memory
- Inline transitions -- each phase self-contained
- Execution Rules section at PIPELINE.md bottom tells agent the protocol
- Phase Transition Protocol preserves knowledge between phases

---

## 12. Memory Updates

After each phase (MANDATORY -- do NOT skip):
1. **PIPELINE.md**: Set phase `Status: DONE`, advance `<- CURRENT`
2. **work/STATE.md**: Record phase results
3. **.claude/memory/activeContext.md**: Did/Decided/Learned/Next
4. **Graphiti**: `add_memory(name="phase_insight", episode_body=<learnings from this phase>)`
5. **Typed memory**:
   - `.claude/memory/knowledge.md` Patterns section: New patterns (deduplicate)
   - `.claude/memory/knowledge.md` Gotchas section: New gotchas (deduplicate)
   - `.claude/memory/daily/YYYY-MM-DD.md`: Daily session log
6. **work/attempt-history.json**: Record good commit hash
7. **Git commit**: Checkpoint with meaningful message + tag

These steps are automated by the Phase Transition Protocol (section 5).

---

## 13. Anti-Drift Patterns

**Todo-list rewriting:** PIPELINE.md is re-read every phase, keeping state in agent's recent attention.

**Controlled variation:** If agents loop on same error 3+ times -- try different angle, spawn fresh agent, or mark BLOCKED.

**Keep wrong turns:** Do not strip errors. Decisions section captures what was tried and why it failed (append-only).

---

## 14. Quick Reference

```
CREATE:     PIPELINE.md (from PIPELINE-v3.md template)
TEMPLATE:   .claude/shared/work-templates/PIPELINE-v3.md
PHASES:     .claude/shared/work-templates/phases/{SPEC,REVIEW,PLAN,IMPLEMENT,QA_REVIEW,TEST,FIX,DEPLOY,STRESS_TEST}.md
CHAINS:     .claude/guides/agent-chains.md
QA SKILL:   .claude/skills/qa-validation-loop/SKILL.md

EXECUTE:    Find <- CURRENT -> read Inputs -> implement -> run Gate -> apply verdict -> update state
MODES:      SOLO (direct) | AGENT_TEAMS (TeamCreate) | AGENT_CHAINS (sequential) | SUB_PIPELINE (nested)
GATES:      AUTO (commands) | USER_APPROVAL (human) | HYBRID (auto + human)
VERDICTS:   PASS (advance) | CONCERNS (log + advance) | REWORK (retry) | FAIL (block)

MEMORY:     .claude/memory/ (knowledge.md, daily/)
REGISTRY:   .claude/agents/registry.md (agent types, tools, skills, thinking levels)
PROMPTS:    .claude/prompts/ (planner.md, coder.md, qa-reviewer.md, qa-fixer.md, insight-extractor.md)
COMPLEXITY: .claude/guides/complexity-assessment.md
RECOVERY:   .claude/guides/recovery-manager.md
GRAPHITI:   .claude/guides/graphiti-integration.md

TRANSITION: Git commit -> insight extraction -> typed memory -> Graphiti -> context refresh -> advance
RECOVER:    Re-read PIPELINE.md -> find <- CURRENT -> continue
UPDATE:     PIPELINE.md + STATE.md + activeContext.md + git commit
FINISH:     All phases DONE -> Status: PIPELINE_COMPLETE
```
