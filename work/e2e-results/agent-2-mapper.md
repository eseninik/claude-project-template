# Agent 2 (mapper) — Skills Directory Map

## Evidence: 7-Step Mapping Process

### Step 1: Tech Stack Detection

Format: **YAML front matter + Markdown**
- All 13 skills use YAML front matter with `name:`, `description:`, and optionally `version:` and `changelog:`
- Body: Markdown with Philosophy / Critical Constraints / Process / Red Flags sections
- Skills are "micro-modules" in directories, each with a `SKILL.md` entry point
- No `package.json`, `pyproject.toml`, `go.mod`, etc. — pure documentation format
- Index file: `SKILLS_INDEX.md` at root of `.claude/skills/`
- One skill (`subagent-driven-development`) has a `references/` subdirectory for overflow docs

---

### Step 2: Entry Points

Each skill directory has exactly one entry point: `SKILL.md`

| Skill Directory | Entry Point |
|-----------------|-------------|
| `ao-fleet-spawn/` | `SKILL.md` |
| `ao-hybrid-spawn/` | `SKILL.md` |
| `codebase-mapping/` | `SKILL.md` |
| `error-recovery/` | `SKILL.md` |
| `expert-panel/` | `SKILL.md` |
| `finishing-a-development-branch/` | `SKILL.md` |
| `qa-validation-loop/` | `SKILL.md` |
| `self-completion/` | `SKILL.md` |
| `subagent-driven-development/` | `SKILL.md` + `references/worktree-mode.md` + `references/background-task-tracking.md` |
| `systematic-debugging/` | `SKILL.md` (+ test/creation logs — not part of skill, for development history) |
| `task-decomposition/` | `SKILL.md` |
| `using-git-worktrees/` | `SKILL.md` |
| `verification-before-completion/` | `SKILL.md` |

Exception files in `systematic-debugging/`: `CREATION-LOG.md`, `test-academic.md`, `test-pressure-1/2/3.md` — development artifacts, not skill content.

---

### Step 3: Directory Structure

```
.claude/skills/
├── SKILLS_INDEX.md                          # Master index, routing table
├── ao-fleet-spawn/
│   └── SKILL.md
├── ao-hybrid-spawn/
│   └── SKILL.md
├── codebase-mapping/
│   └── SKILL.md
├── error-recovery/
│   └── SKILL.md
├── expert-panel/
│   └── SKILL.md
├── finishing-a-development-branch/
│   └── SKILL.md
├── qa-validation-loop/
│   └── SKILL.md
├── self-completion/
│   └── SKILL.md
├── subagent-driven-development/
│   ├── SKILL.md                            # Core (1441 lines, most complex)
│   └── references/
│       ├── worktree-mode.md                # Overflow: worktree details
│       └── background-task-tracking.md     # Overflow: JSON tracking schema
├── systematic-debugging/
│   ├── SKILL.md
│   ├── CREATION-LOG.md                     # Dev artifact
│   ├── test-academic.md                    # Dev artifact
│   ├── test-pressure-1.md                  # Dev artifact
│   ├── test-pressure-2.md                  # Dev artifact
│   └── test-pressure-3.md                  # Dev artifact
├── task-decomposition/
│   └── SKILL.md
├── using-git-worktrees/
│   └── SKILL.md
└── verification-before-completion/
    └── SKILL.md
```

Total: 13 skill directories, 16 content files (excluding dev artifacts)

---

### Step 4: Module Grouping by Category

#### Category A: Parallelization & Execution (Core Pipeline)
Skills for executing work in parallel with agents

| Skill | Version | Size (approx) | Purpose |
|-------|---------|----------------|---------|
| `subagent-driven-development` | 3.1.0 | ~1441 lines | Wave-based parallel task execution via subagents |
| `task-decomposition` | 1.0.0 | ~600 lines | Analyze task → detect parallelization opportunity |
| `ao-hybrid-spawn` | — | ~187 lines | Spawn full Claude Code sessions via AO (in-project) |
| `ao-fleet-spawn` | — | ~105 lines | Spawn sessions across multiple projects via AO CLI |
| `using-git-worktrees` | 2.1.0 | ~449 lines | Isolated workspace per agent, conflict-safe merge |

#### Category B: Quality Gates
Skills that enforce quality at completion boundaries

| Skill | Version | Size (approx) | Purpose |
|-------|---------|----------------|---------|
| `qa-validation-loop` | — | ~99 lines | Risk-proportional Reviewer→Fixer loop |
| `verification-before-completion` | 1.0.0 | ~30 lines | Evidence-based completion gate |
| `finishing-a-development-branch` | 1.0.0 | ~32 lines | Merge/PR/cleanup checklist |

#### Category C: Analysis & Research
Skills that gather information before action

| Skill | Version | Size (approx) | Purpose |
|-------|---------|----------------|---------|
| `codebase-mapping` | — | ~30 lines | Map unknown codebase → codebase-map.md |
| `expert-panel` | — | ~42 lines | Multi-agent expert analysis before implementation |
| `systematic-debugging` | 1.0.0 | ~38 lines | 4-phase root-cause debugging framework |

#### Category D: Automation & Recovery
Skills for autonomous operation and error handling

| Skill | Version | Size (approx) | Purpose |
|-------|---------|----------------|---------|
| `self-completion` | 1.0.0 | ~23 lines | Auto-continue through pending todo items |
| `error-recovery` | 1.0.0 | ~31 lines | Retry table + 3-strike escalation protocol |

---

### Step 5: Skill Dependencies (Cross-References)

#### Explicit Cross-References Found

| Source Skill | References | Reference Type |
|-------------|-----------|----------------|
| `ao-hybrid-spawn` | `subagent-driven-development/references/worktree-mode.md` | Worktree merge protocol |
| `ao-hybrid-spawn` | `ao-fleet-spawn` | "For cross-project fleet ops, use ao-fleet-spawn" |
| `ao-hybrid-spawn` | `.claude/guides/teammate-prompt-template.md` | Prompt building |
| `ao-fleet-spawn` | `~/.agent-orchestrator.yaml` | Config dependency |
| `subagent-driven-development` | `ao-hybrid-spawn` | "AO Hybrid Mode" section |
| `subagent-driven-development` | `using-git-worktrees` | Worktree Mode integration |
| `subagent-driven-development` | `verification-before-completion` | Referenced in workflow |
| `subagent-driven-development` | `finishing-a-development-branch` | "REQUIRED SUB-SKILL" at Step 8 |
| `using-git-worktrees` | `subagent-driven-development` | "For use with Worktree Mode" (v2.0+) |
| `using-git-worktrees` | `finishing-a-development-branch` | "Pairs with" in Integration section |
| `task-decomposition` | `subagent-driven-development` | "If tasks/*.md exist → use subagent-driven-development" |
| `qa-validation-loop` | `.claude/prompts/qa-reviewer.md` | Prompt for reviewer agent |
| `qa-validation-loop` | `.claude/prompts/qa-fixer.md` | Prompt for fixer agent |
| `qa-validation-loop` | `.claude/agents/registry.md` | Agent type lookup |
| `qa-validation-loop` | `.claude/guides/complexity-assessment.md` | Risk level input |
| `SKILLS_INDEX.md` | All 13 skills | Routing table |

#### Implicit Dependencies (functional pipeline)

```
task-decomposition  →  subagent-driven-development  →  using-git-worktrees
                                                     →  ao-hybrid-spawn
                                                     →  verification-before-completion
                                                     →  finishing-a-development-branch

ao-hybrid-spawn  →  ao-fleet-spawn (alternative, not dependency)

qa-validation-loop  →  verification-before-completion (trivial depth)

systematic-debugging  →  verification-before-completion (after fix)
```

---

### Step 6: Config Locations

YAML front matter in each `SKILL.md` acts as the skill's config:

```yaml
---
name: skill-name          # Routing key (Claude Code uses this for routing)
description: |            # Auto-loaded for trigger matching
  ...
version: x.y.z           # Optional — present in 5 of 13 skills
changelog:                # Optional — present in 3 of 13 skills (subagent-driven-development, using-git-worktrees)
---
```

Skills that have version + changelog (evolved, complex):
- `subagent-driven-development` v3.1.0 — most evolved, 3 major versions
- `using-git-worktrees` v2.1.0 — 2 major versions
- `error-recovery` v1.0.0

Skills with NO version (newer simplified format):
- `ao-fleet-spawn`, `ao-hybrid-spawn`, `codebase-mapping`, `expert-panel`, `qa-validation-loop`

External config referenced:
- `~/.agent-orchestrator.yaml` — AO fleet/hybrid spawn config
- `.claude/ops/config.yaml` — `qa_depth`, `execution_engine`, `max_retry_attempts`
- `work/complexity-assessment.md` — QA depth input
- `work/background-tasks.json` — Parallel task tracking state

---

### Step 7: Skills Map (Structured Output)

## Skills Ecosystem Map

- **Stack:** Markdown + YAML front matter (documentation-as-code)
- **Entry:** Each skill's `SKILL.md` (13 entry points total)
- **Index:** `.claude/skills/SKILLS_INDEX.md` (routing table)
- **Modules:** 4 categories — Parallelization, Quality Gates, Analysis, Automation
- **Tests:** `systematic-debugging/` has dev pressure tests (not runtime tests)
- **Config:** YAML front matter per skill + external `config.yaml` + AO config
- **Dependencies:** Explicit cross-refs between 7 skill pairs; functional pipeline

### Routing Logic

Skills are triggered by:
1. **Situation matching** (user says "expert panel", "Agent Teams Mode")
2. **Context detection** (tasks/*.md exist, errors occur, branch finishing)
3. **Pipeline phase Mode** (AO_FLEET, AO_HYBRID in PIPELINE.md)
4. **CLAUDE.md BLOCKING RULES** (inline in CLAUDE.md, not in skill files)

### Key Architectural Observations

1. **Size asymmetry**: `subagent-driven-development` (1441 lines) vs `verification-before-completion` (30 lines). Complex skills with multi-version evolution get large; quality gate skills stay minimal.

2. **References overflow pattern**: When a skill exceeds ~300 lines, content moves to `references/` subdirectory. Only `subagent-driven-development` uses this pattern — suggesting the others have not yet hit that threshold.

3. **Version-gated features**: `using-git-worktrees` and `subagent-driven-development` use `changelog:` YAML to track feature additions per version (v3.0: worktree mode, v3.1: rollback/validation). This makes it easy to know "when was this added".

4. **Mutual exclusion constraints**: `ao-fleet-spawn` and `ao-hybrid-spawn` are mutually exclusive per phase. `task-decomposition` hands off to `subagent-driven-development` (does not overlap). These skills form clean handoff chains, not circular dependencies.

5. **External resource coupling**: `qa-validation-loop` depends on 4 external resources (prompts, registry, complexity guide, attempt-history). It's the most externally coupled skill.

### Skill Line Count Summary (from SKILLS_INDEX.md)

| Skill | Lines |
|-------|-------|
| verification-before-completion | 30 |
| qa-validation-loop | 39 |
| expert-panel | 42 |
| subagent-driven-development | 49 (SKILLS_INDEX says 49, actual SKILL.md = 1441 — index counts core, not overflow) |
| task-decomposition | 37 |
| systematic-debugging | 38 |
| using-git-worktrees | 44 |
| error-recovery | 31 |
| codebase-mapping | 30 |
| finishing-a-development-branch | 32 |
| self-completion | 23 |
| **Total (SKILLS_INDEX)** | **~395 lines** |

Note: SKILLS_INDEX counts only core SKILL.md bodies for quick-reference. `subagent-driven-development` actual full size is ~1441 lines including inline worktree mode and background tracking (reference files are additional).

---

## Acceptance Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|---------|
| All 7 mapping steps executed with evidence | PASS | Steps 1-7 above with explicit outputs |
| Skills map written to work/e2e-results/agent-2-mapper.md | PASS | This file |
| Cross-references between skills identified | PASS | Step 5: 15 explicit refs + implicit pipeline |
| Categories assigned to all 13 skills | PASS | Step 4: 4 categories, all 13 assigned |

---

=== PHASE HANDOFF: mapper ===
Status: PASS
Files Modified:
- /c/Bots/Migrator bots/claude-project-template-update/work/e2e-results/agent-2-mapper.md
Tests: N/A (read-only mapping task)
Decisions Made:
- Assigned 4 categories: Parallelization/Execution, Quality Gates, Analysis/Research, Automation/Recovery
- Counted subagent-driven-development as 1441 lines actual (vs 49 in SKILLS_INDEX — index counts core body only)
- Classified systematic-debugging dev artifacts as non-skill content (CREATION-LOG, test-pressure files)
Learnings:
- Friction: e2e-results/ directory needed creating (did not pre-exist) | MINOR
- Surprise: subagent-driven-development embeds both reference files' content inline AND has separate references/ overflow — it's a 1441-line monolith
- Pattern: Skills with changelog: in YAML front matter are the evolved/complex ones; simpler skills drop versioning entirely
Next Phase Input: 13 skills mapped, 4 categories, 15 cross-references identified. `subagent-driven-development` is the hub skill — most other execution skills reference or hand off to it. Quality gate skills (verification-before-completion, qa-validation-loop) are called at pipeline exits. AO skills (ao-fleet-spawn, ao-hybrid-spawn) are mutually exclusive execution engines.
=== END HANDOFF ===
