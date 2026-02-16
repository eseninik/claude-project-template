# Autonomous Pipeline Guide (v2)

> On-demand guide for executing autonomous development pipelines.
> Loaded via: `cat .claude/guides/autonomous-pipeline.md`

---

## 1. Overview

The autonomous pipeline is a **state machine encoded in markdown** that drives multi-phase development without losing context. Components:

1. **PIPELINE.md** -- state machine with named phases, conditional transitions, and quality gates
2. **Ralph Loop** -- fresh-context shell script that eliminates compaction entirely
3. **Agent Teams** -- parallel execution via `Mode: AGENT_TEAMS` on phases with 3+ independent tasks
4. **Quality Gates** -- 4-verdict model (PASS/CONCERNS/REWORK/FAIL) with AUTO/USER_APPROVAL/HYBRID types
5. **Deploy Integration** -- git workflow, SSH deployment, health checks, stress testing

---

## 2. When to Use / When Not

**Use when:** 3+ phases, likely compaction (>60% context), autonomous execution needed, deploy/stress test phases, or user requests "pipeline"/"autonomous mode".

**Do NOT use when:** Simple bug fix (1-2 files), single-phase task, or task requiring constant user feedback.

---

## 3. Pipeline Creation

**Step 1: Analyze.** Break into phases. For each: Mode (`SOLO`/`AGENT_TEAMS`/`SUB_PIPELINE`), Gate Type (`AUTO`/`USER_APPROVAL`/`HYBRID`), transitions (PASS/FAIL/REWORK).

**Step 2: Create work/PIPELINE.md** from `.claude/shared/work-templates/PIPELINE-v2.md`. Delete unused phases, set first phase `<- CURRENT`, set `Status: IN_PROGRESS`.

**Step 3: Create work/PROMPT.md** (Ralph Loop only) from `.claude/shared/work-templates/PROMPT.md`. Customize context-loading and verification commands.

**Step 4: Execute.** Interactive: read PIPELINE.md, execute sequentially. Ralph Loop: `./scripts/ralph.sh`.

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

---

## 5. Quality Gates

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

## 6. Conditional Transitions

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

## 7. Phase Templates

Reference: `.claude/shared/work-templates/phases/`

| Template | Purpose |
|----------|---------|
| `SPEC.md` | User spec creation with acceptance criteria |
| `REVIEW.md` | Expert panel analysis |
| `PLAN.md` | Tech spec + task decomposition + wave analysis |
| `IMPLEMENT.md` | Code implementation via Agent Teams |
| `TEST.md` | Test suite execution |
| `FIX.md` | Bug fixing with debugging teams |
| `DEPLOY.md` | SSH deployment + health checks |
| `STRESS_TEST.md` | Locust load testing + performance report |

Delete unused phases from PIPELINE.md. Transitions still work for remaining phases.

---

## 8. Ralph Loop (Autonomous Mode)

`scripts/ralph.sh` eliminates compaction by giving each phase a fresh `claude -p` process with clean 200K context. State persists through files (PIPELINE.md, STATE.md, git), not conversation memory.

**Use Ralph Loop when:** 5+ phases, multiple AGENT_TEAMS phases, autonomous execution, session >100K tokens estimated.

**Use Interactive when:** 2-3 phases, user wants review between phases, phases need user input.

### Usage
```bash
./scripts/ralph.sh                           # Default: 20 iterations
./scripts/ralph.sh --max-iterations 10       # Custom limit
./scripts/ralph.sh --pipeline work/PIPELINE.md --prompt work/PROMPT.md
./scripts/ralph.sh --model claude-sonnet-4-5-20250929   # Override model
./scripts/ralph.sh --dry-run                 # Print without executing
```

### How It Works
```
for each iteration:
  1. Check PIPELINE.md for PIPELINE_COMPLETE -> exit 0
  2. Check PIPELINE.md for BLOCKED -> exit 1
  3. Spawn: claude -p "$(cat PROMPT.md)" --dangerously-skip-permissions
  4. Agent reads PIPELINE.md, finds <- CURRENT, executes ONE phase
  5. Agent updates PIPELINE.md, STATE.md, memory
  6. ralph.sh creates git checkpoint: pipeline-iter-{N}
  7. Loop with fresh context
```

**Exit codes:** 0 = complete, 1 = blocked, 2 = max iterations reached, 3 = files not found.

**PROMPT.md** (`.claude/shared/work-templates/PROMPT.md`): Keep under 50 lines. Loaded every iteration, so Agent Teams enforcement **cannot be lost to compaction**.

---

## 9. Deploy Integration

**Git workflow:** `feature/{name} -> dev -> main -> deploy to server`

**Deploy phases:** GIT_RELEASE (PR + merge + tag) -> DEPLOY (rsync + restart) -> SMOKE_TEST (health check) -> STRESS_TEST (locust).

**SSH deployment:** rsync uploads code, systemctl restarts service. Env vars (`DEPLOY_SSH_HOST`, `DEPLOY_SSH_KEY`, etc.) from `.env` (never committed).

**Health checks:** Poll health endpoint 3x with 5s delay. Check journalctl for errors.

**Stress testing:** Locust with standard config. Thresholds: p95 < 500ms, error rate < 1%. Results: `work/performance-report.md`.

See full details: `work/scalable-pipeline-design-deploy.md`

---

## 10. Compaction Recovery

When compaction occurs during interactive mode:
1. System auto-loads CLAUDE.md (always in context)
2. CLAUDE.md Summary Instructions remind: "re-read PIPELINE.md"
3. Agent reads `work/PIPELINE.md`, finds `<- CURRENT` marker
4. Agent reads `work/STATE.md` for latest results
5. Agent continues from where it left off

**Why v2 survives compaction:**
- `<- CURRENT` on phase header line -- one grep finds location
- Mode field persisted in file, not memory
- Inline transitions -- each phase self-contained
- Execution Rules section at PIPELINE.md bottom tells agent the protocol
- Ralph Loop eliminates compaction entirely

---

## 11. Memory Updates

After each phase (MANDATORY -- do NOT skip):
1. **PIPELINE.md**: Set phase `Status: DONE`, advance `<- CURRENT`
2. **work/STATE.md**: Record phase results
3. **.claude/memory/activeContext.md**: Did/Decided/Learned/Next
4. **Git commit**: Checkpoint with meaningful message + tag

---

## 12. Anti-Drift Patterns

**Todo-list rewriting:** PIPELINE.md is re-read every phase, keeping state in agent's recent attention.

**Controlled variation:** If agents loop on same error 3+ times -- try different angle, spawn fresh agent, or mark BLOCKED.

**Keep wrong turns:** Do not strip errors. Decisions section captures what was tried and why it failed (append-only).

---

## 13. Quick Reference

```
CREATE:     PIPELINE.md (from PIPELINE-v2.md template) + PROMPT.md (Ralph Loop only)
TEMPLATE:   .claude/shared/work-templates/PIPELINE-v2.md
PHASES:     .claude/shared/work-templates/phases/{SPEC,REVIEW,PLAN,IMPLEMENT,TEST,FIX,DEPLOY,STRESS_TEST}.md
PROMPT:     .claude/shared/work-templates/PROMPT.md
SCRIPT:     scripts/ralph.sh

EXECUTE:    Find <- CURRENT -> read Inputs -> implement -> run Gate -> apply verdict -> update state
MODES:      SOLO (direct) | AGENT_TEAMS (TeamCreate) | SUB_PIPELINE (nested)
GATES:      AUTO (commands) | USER_APPROVAL (human) | HYBRID (auto + human)
VERDICTS:   PASS (advance) | CONCERNS (log + advance) | REWORK (retry) | FAIL (block)

RECOVER:    Re-read PIPELINE.md -> find <- CURRENT -> continue
UPDATE:     PIPELINE.md + STATE.md + activeContext.md + git commit
FINISH:     All phases DONE -> Status: PIPELINE_COMPLETE
```
