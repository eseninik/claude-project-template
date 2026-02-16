# Scalable Pipeline Research: Synthesis Document

**Date:** 2026-02-16
**Phase:** 1 of 4 (Expert Research & Analysis)
**Team:** scalable-pipeline (5 research agents + lead synthesis)
**Sources:** expert-analysis.md, pipeline-review.md, deep research (35+ repos), autonomous-pipeline.md

---

## 1. Compaction-Proof Agent Teams Enforcement (CRITICAL)

### Root Cause: Why Agent Teams Gets Lost

1. **"Lost in the Middle" phenomenon** — behavioral rules in mid-CLAUDE.md have lowest recall after compaction. Agent Teams instruction sits at lines 68-93, the attention dead zone.

2. **Silent Rule Dropping** — research confirms LLMs ignore instructions when context has 7-10+ active rules post-compaction. Agent Teams is one of the first dropped.

3. **Behavioral vs Factual rules** — Agent Teams is a "HOW" rule ("when you see 3+ tasks, create a team"). Compaction treats "how" rules as "resolved" and compresses them. "WHAT" rules ("never commit secrets") survive because they look ongoing.

4. **No re-injection mechanism** — hooks removed (correct decision for Windows), so no SessionStart hook to re-inject Agent Teams after compaction.

5. **Circular dependency** — Post-compaction behavior requires compaction to preserve that very behavior. The only reliable anchor is what gets re-read from files.

### Solutions (Ranked by Effectiveness)

#### Solution 1: Ralph Loop — Fresh Context per Phase (BEST)

**How:** Shell script spawns `claude -p` for each pipeline phase. Each invocation gets clean 200K context. PROMPT.md re-read every iteration.

**Why it works:** Eliminates compaction entirely. Agent Teams instruction is in PROMPT.md which is freshly loaded every phase. No state loss possible.

**Tradeoff:** Requires `--dangerously-skip-permissions` for full autonomy. User can't interact mid-phase. Each phase must be self-contained.

**Effectiveness: 10/10** — compaction cannot happen if context resets every phase.

#### Solution 2: PIPELINE.md Mode Field Enforcement (STRONG)

**How:** Each phase has explicit `Mode: AGENT_TEAMS` field. After compaction, CLAUDE.md Summary Instructions say "re-read PIPELINE.md". Agent sees Mode field → must create team.

**Why it works:** Mode is encoded in the state file, not in conversation memory. Even if agent forgets the behavioral rule, the state file tells it what to do.

**Tradeoff:** Depends on Summary Instructions surviving compaction. Not 100% reliable but very good.

**Effectiveness: 7/10** — works in most cases, may fail after 3+ compactions.

#### Solution 3: Summary Instructions + High-Attention Placement (MODERATE)

**How:** `# Summary instructions` section at TOP of CLAUDE.md explicitly tells compactor: "preserve Agent Teams rules". Move AGENT TEAM PROPOSAL to beginning of CLAUDE.md.

**Why it works:** First and last sections get highest attention weight. Summary Instructions is an official Anthropic feature.

**Tradeoff:** Still relies on compaction algorithm respecting the hint. Not guaranteed.

**Effectiveness: 5/10** — helps but not sufficient alone.

#### Solution 4: PROMPT.md Agent Teams Encoding (MODERATE)

**How:** Every pipeline phase reads a PROMPT.md that explicitly says "If phase has 3+ tasks, use TeamCreate". This is the same mechanism as Ralph Loop but for interactive sessions.

**Why it works:** Re-reading a file after compaction re-introduces the rule into recent context (high-attention zone).

**Tradeoff:** Requires agent to actually re-read the file. Depends on post-compaction behavior.

**Effectiveness: 6/10** — requires the re-read behavior to survive.

#### Solution 5: Hybrid Ralph + Interactive (RECOMMENDED)

**How:** Use Ralph Loop for fully autonomous execution. Fall back to PIPELINE.md Mode + Summary Instructions for interactive sessions where user wants to participate.

**Why recommended:** Covers both use cases. Ralph Loop guarantees Agent Teams for autonomous work. PIPELINE.md Mode provides best-effort for interactive work.

**Effectiveness: 9/10** — best practical approach.

### Recommended Architecture

```
AUTONOMOUS MODE (user says "реализуй автономно"):
  → Ralph Loop: scripts/ralph.sh
  → Fresh context per phase
  → PROMPT.md loaded every iteration
  → Agent Teams guaranteed

INTERACTIVE MODE (user participates between phases):
  → PIPELINE.md with Mode: AGENT_TEAMS per phase
  → Summary Instructions in CLAUDE.md
  → Post-compaction: re-read PIPELINE.md → see Mode → create team
  → Best-effort but not guaranteed after 3+ compactions
```

---

## 2. Conditional Branching & Quality Gates

### PIPELINE.md v2 Format

The pipeline state machine needs per-phase transition rules, not just linear progression.

#### Phase Definition Format

```markdown
### Phase: IMPLEMENT
- Status: IN_PROGRESS | DONE | BLOCKED | SKIPPED
- Mode: AGENT_TEAMS
- Attempts: 1 of 3
- On PASS: -> TEST
- On FAIL: -> FIX
- On BLOCKED: -> STOP (alert user)
- Gate: all tests pass, lint clean, no type errors
```

#### Named Phase References

Phases reference each other by name, not number. This allows conditional transitions:
- `On PASS: -> TEST` (go to TEST phase)
- `On FAIL: -> FIX` (go to FIX phase)
- `On REWORK: -> IMPLEMENT` (loop back)

#### 4-Verdict Quality Gates

Each phase transition goes through a quality gate with 4 possible verdicts:

| Verdict | Action |
|---------|--------|
| **PASS** | Proceed to next phase as defined by `On PASS` |
| **CONCERNS** | Document concerns, proceed anyway |
| **REWORK** | Return to previous phase, increment Attempts |
| **FAIL** | Mark BLOCKED, stop pipeline, alert user |

#### Gate Types

- **AUTO**: Command-based (e.g., `uv run pytest`, `ruff check .`)
- **USER_APPROVAL**: Requires user confirmation
- **HYBRID**: Auto checks + user approval for critical transitions

### Rollback Mechanism

#### Git Checkpoint Tags

```
pipeline-checkpoint-SPEC       (after SPEC phase passes)
pipeline-checkpoint-REVIEW     (after REVIEW phase passes)
pipeline-checkpoint-PLAN       (after PLAN phase passes)
pipeline-checkpoint-IMPLEMENT  (after IMPLEMENT phase passes)
```

**Rollback command:** `git reset --hard pipeline-checkpoint-{phase}`

#### State Rollback

When rolling back, PIPELINE.md is also reverted:
1. Git reset to checkpoint tag
2. PIPELINE.md automatically reflects the rolled-back state
3. Agent reads PIPELINE.md → sees correct current phase

### Loop Constructs

#### Bounded Loops with Attempt Counter

```markdown
### Phase: FIX
- Attempts: 2 of 3
- Max Attempts: 3
- On PASS: -> TEST
- On MAX_ATTEMPTS: -> BLOCKED (alert user)
```

- Every loop phase has `Max Attempts` (default: 3)
- `Attempts` increments each time the phase is entered
- When `Attempts >= Max Attempts` → phase goes to BLOCKED
- Prevents infinite loops

#### Common Loop Patterns

```
TEST -> FIX -> TEST (fix-retest loop, max 3)
REVIEW -> IMPLEMENT -> REVIEW (revision loop, max 2)
DEPLOY -> FIX -> DEPLOY (deploy-retry loop, max 2)
```

---

## 3. Sub-Pipeline Nesting & Composability

### Three-Level Composition Model

```
L0: Master Pipeline (work/PIPELINE.md)
    ├── L1: Planning Sub-Pipeline (work/planning/PIPELINE.md)
    ├── L1: Development Sub-Pipeline (work/development/PIPELINE.md)
    ├── L1: Testing Sub-Pipeline (work/testing/PIPELINE.md)
    └── L1: Deployment Sub-Pipeline (work/deployment/PIPELINE.md)
        └── L2: Phase (individual phase within sub-pipeline)
```

### Sub-Pipeline Directive

In PIPELINE.md, a phase can reference a sub-pipeline:

```markdown
- [ ] Phase 3: Development <- CURRENT
  - Mode: SUB_PIPELINE
  - Pipeline: work/development/PIPELINE.md
  - On COMPLETE: -> Phase 4
  - On BLOCKED: -> STOP
```

The `SUB_PIPELINE` mode tells the agent to execute the referenced pipeline file as a nested state machine.

### Phase Template Building Blocks

Each phase is a reusable template that can be composed:

```markdown
# Phase Template: IMPLEMENT

## Metadata
- Default Mode: AGENT_TEAMS (for 3+ tasks)
- Default Gate: AUTO (tests + lint)
- Default Loop: TEST -> FIX -> TEST (max 3)

## Inputs
- tasks/*.md (task definitions)
- tech-spec.md (implementation spec)

## Process
1. Read all task files
2. Analyze parallelization potential (wave analysis)
3. If 3+ independent tasks → create Agent Team
4. Implement tasks (parallel or sequential)
5. Run quality gate

## Outputs
- Source code files
- Test files
- test-results.md

## Context Recovery
After compaction, re-read:
- work/PIPELINE.md (find current sub-phase)
- tasks/*.md (find uncompleted tasks)
- test-results.md (if exists, see what failed)
```

### Contract Files for Inter-Pipeline Coordination

Each phase/sub-pipeline produces artifacts consumed by the next:

```markdown
# Contract: PLAN -> IMPLEMENT

## Output of PLAN
- work/{feature}/tech-spec.md (architecture + API design)
- tasks/*.md (atomic task definitions with acceptance criteria)
- tasks/waves.md (parallelization analysis)

## Input Requirements for IMPLEMENT
- MUST have tasks/*.md with at least 1 task
- Each task MUST have acceptance criteria
- Wave analysis MUST be present for Agent Teams decisions

## Validation
- Count tasks: `ls tasks/*.md | wc -l` > 0
- Check criteria: each task has "## Acceptance Criteria" section
- Check waves: tasks/waves.md exists
```

### Parallel Sub-Pipelines

For full-stack projects, frontend and backend can run in parallel:

```markdown
- [ ] Phase 3: Development <- CURRENT
  - Mode: PARALLEL_SUB_PIPELINES
  - Pipelines:
    - work/frontend/PIPELINE.md (worktree: frontend-dev)
    - work/backend/PIPELINE.md (worktree: backend-dev)
  - Merge Strategy: sequential merge (backend first, then frontend)
  - On ALL_COMPLETE: -> Phase 4
  - On ANY_BLOCKED: -> STOP
```

Uses git worktrees for isolation. Each sub-pipeline runs in its own worktree to avoid conflicts.

### Depth Limit

Maximum nesting: 2 levels (Master → Sub-Pipeline → Phase). Deeper nesting adds complexity without benefit. If a phase needs further decomposition, use Agent Teams within the phase instead.

---

## 4. Deploy Integration & Full Project Lifecycle

### 11 Lifecycle Phases Catalog

| # | Phase | Description | Mode | Typical |
|---|-------|-------------|------|---------|
| 1 | SPEC | User requirements gathering | SOLO | Interactive interview |
| 2 | REVIEW | Expert panel analysis | AGENT_TEAMS | 3-5 expert agents |
| 3 | PLAN | Tech spec + task decomposition | SOLO/TEAMS | Wave analysis |
| 4 | IMPLEMENT | Coding with TDD | AGENT_TEAMS | Parallel developers |
| 5 | TEST | Integration/E2E testing | SOLO | Run test suite |
| 6 | FIX | Debug and fix failures | AGENT_TEAMS | Parallel debuggers |
| 7 | RETEST | Verify fixes | SOLO | Re-run failing tests |
| 8 | GIT_RELEASE | Branch management + PR | SOLO | Merge + tag |
| 9 | DEPLOY | Server deployment | SOLO | SSH + systemd |
| 10 | SMOKE_TEST | Post-deploy verification | SOLO | Health checks |
| 11 | STRESS_TEST | Load/performance testing | SOLO | Locust/k6 |

### Git Workflow Automation

```
Feature branch:  feature/{task-name}
Development:     dev (main development branch)
Production:      main (stable, deployed)

Pipeline creates: feature branch → implements → tests → merges to dev → deploys from dev
```

**Automated steps:**
1. `git checkout -b feature/{name}` from dev
2. Implement + test on feature branch
3. `gh pr create` with test results summary
4. Merge to dev (after review gate)
5. Deploy from dev to server

### Server Deployment (Windows → Linux VPS)

```bash
# SSH deployment for Python/Telegram bot projects
SSH_CMD="ssh -i ~/.ssh/key user@server"

# 1. Upload code
rsync -avz --exclude='.venv' --exclude='__pycache__' ./ user@server:/app/

# 2. Install dependencies
$SSH_CMD "cd /app && pip install -r requirements.txt"

# 3. Restart service
$SSH_CMD "sudo systemctl restart mybot.service"

# 4. Verify health
$SSH_CMD "sudo systemctl status mybot.service"
$SSH_CMD "curl -s http://localhost:8080/health"
```

### Stress Testing Integration

For Python/Telegram bot projects:

```python
# locustfile.py template
from locust import HttpUser, task, between

class BotUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def health_check(self):
        self.client.get("/health")

    @task(3)
    def send_message(self):
        self.client.post("/webhook", json={...})
```

**Pipeline integration:**
1. Deploy to server
2. Run: `locust -f locustfile.py --headless -u 100 -r 10 --run-time 60s`
3. Collect results → performance-report.md
4. Gate: response_time_p95 < 500ms, error_rate < 1%

### CI/CD (GitHub Actions)

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [dev]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: pytest
      - run: rsync -avz ./ ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }}:/app/
      - run: ssh ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }} "sudo systemctl restart mybot"
```

---

## 5. Phase Template Library

### Standard Template Format

Every phase template follows this structure:

```markdown
# Phase: {NAME}

## Metadata
- Default Mode: SOLO | AGENT_TEAMS
- Gate Type: AUTO | USER_APPROVAL | HYBRID
- Loop Target: {phase name if loopable}
- Max Attempts: {number}

## Inputs
{what this phase consumes}

## Process
{step-by-step execution}

## Outputs
{what this phase produces}

## Quality Gate
{specific checks for PASS/FAIL}

## Agent Team Config (if Mode = AGENT_TEAMS)
- Team size: {number}
- Roles: {list of roles}
- Skills per role: {from TEAM ROLE SKILLS MAPPING}

## Context Recovery
{what to re-read after compaction}
```

### 8 Phase Templates Summary

| Phase | Mode | Gate | Loop | Key Output |
|-------|------|------|------|------------|
| SPEC | SOLO | USER_APPROVAL | — | user-spec.md |
| REVIEW | AGENT_TEAMS | AUTO (no open Qs) | — | expert-analysis.md |
| PLAN | SOLO/TEAMS | USER_APPROVAL | — | tech-spec.md + tasks/*.md |
| IMPLEMENT | AGENT_TEAMS | AUTO (tests+lint) | → FIX | source code + tests |
| TEST | SOLO | AUTO (all pass) | → FIX | test-results.md |
| FIX | AGENT_TEAMS | AUTO (fixed tests pass) | → TEST (max 3) | fixed code |
| DEPLOY | SOLO | AUTO (health check) | → FIX (max 2) | deployment log |
| STRESS_TEST | SOLO | AUTO (perf thresholds) | — | performance-report.md |

---

## 6. Design Requirements for Phase 2

Based on all 5 research tracks, the architecture must satisfy:

### Must Have (P0)

1. **PIPELINE.md v2 format** with named phases, conditional transitions, Mode field, attempt counters
2. **Quality gates** with 4-verdict model (PASS/CONCERNS/REWORK/FAIL)
3. **8 phase templates** as reusable building blocks
4. **Ralph Loop script** for compaction-immune autonomous execution
5. **PROMPT.md template** with explicit Agent Teams enforcement
6. **Contract files** between phases (input/output specifications)
7. **Git checkpoint tags** for rollback between phases
8. **Summary Instructions** in CLAUDE.md for interactive mode resilience

### Should Have (P1)

9. **Sub-pipeline nesting** (Master → Sub-Pipeline → Phase)
10. **Parallel sub-pipelines** via worktree isolation
11. **Deploy integration** (SSH + systemd for Python projects)
12. **Stress test integration** (locust template)
13. **Model-aware routing** (opus/sonnet/haiku per role)
14. **GitHub Actions template** for CI/CD

### Nice to Have (P2)

15. **Parallel sub-pipeline coordination** (contract-based merge)
16. **Self-correcting CLAUDE.md loop** (errors → rules)
17. **Context monitoring** (estimate context usage per phase)
18. **Pipeline visualization** (mermaid diagram generation)

---

## Summary

The scalable pipeline system is built on 5 pillars:

1. **Compaction Immunity** — Ralph Loop for autonomous, PIPELINE.md Mode for interactive
2. **Conditional Execution** — Named phases with transitions, quality gates, bounded loops
3. **Composability** — Three-level nesting (Master → Sub-Pipeline → Phase), reusable templates
4. **Full Lifecycle** — 11 phases from SPEC to STRESS_TEST, including deploy
5. **File-First State** — All state in persistent files, conversation memory is disposable cache

Phase 2 (Architecture Design) should produce the concrete PIPELINE.md v2 format, phase template files, quality gate framework, and deploy integration design.
