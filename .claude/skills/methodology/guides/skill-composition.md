# Skill Composition Guide

> **How skills connect: inputs, outputs, and contracts for orchestration.**

This guide defines the interface contracts between skills, enabling automated orchestration and validation.

---

## Skill Contracts

### Planning Phase Skills

| Skill | Requires | Produces | Notes |
|-------|----------|----------|-------|
| `context-capture` | User description | Clarified requirements, context notes | Use when requirements vague |
| `user-spec-planning` | Project context (project.md, architecture.md) | `work/<feature>/user-spec.md` | Creates business requirements |
| `tech-spec-planning` | `user-spec.md` OR clear description | `work/<feature>/tech-spec.md` + `tasks/*.md` | Creates technical plan |
| `project-planning` | User interview | `project.md`, `features.md`, `roadmap.md` | New project setup |

### Execution Phase Skills

| Skill | Requires | Produces | Notes |
|-------|----------|----------|-------|
| `subagent-driven-development` | `tech-spec.md` + `tasks/*.md` | Implemented code + tests | Wave parallelization |
| `executing-plans` | Plan file (any format) | Implemented code + tests | External session execution |
| `test-driven-development` | Clear task + existing code | Tests + implementation | Single task TDD |

### Quality Phase Skills

| Skill | Requires | Produces | Notes |
|-------|----------|----------|-------|
| `user-acceptance-testing` | `user-spec.md` + implemented code | UAT checklist + user approval | MANDATORY after implementation |
| `verification-before-completion` | Completed task | Verification evidence | MANDATORY before "done" |
| `code-reviewer` | Changed files | Review JSON (approved/changes_required) | Quality gate |
| `systematic-debugging` | Bug/error description | Root cause + fix | MANDATORY for any bug |

### Infrastructure Skills

| Skill | Requires | Produces | Notes |
|-------|----------|----------|-------|
| `infrastructure` | Project requirements | CI/CD, Docker, hooks config | Setup once |
| `testing` | Project context | Testing strategy document | Defines test approach |

---

## Required Artifacts

Before invoking a skill, verify these artifacts exist:

### For `tech-spec-planning`:
```
REQUIRED (one of):
  - work/<feature>/user-spec.md (status: approved)
  - Clear description from user
  - Audit/analysis document

OPTIONAL (enhances quality):
  - .claude/skills/project-knowledge/guides/architecture.md
  - .claude/skills/project-knowledge/guides/patterns.md
```

### For `subagent-driven-development`:
```
REQUIRED:
  - work/<feature>/tech-spec.md (status: approved)
  - work/<feature>/tasks/*.md (at least one task)

REQUIRED (each task must have):
  - status: planned
  - depends_on: [] (list, can be empty)
  - files_modified: [] (list, can be empty)
```

### For `user-acceptance-testing`:
```
REQUIRED:
  - work/<feature>/user-spec.md (any status)
  - Implementation complete (all tasks done)

PRODUCES:
  - UAT checklist presented to user
  - User approval or issue list
```

### For `verification-before-completion`:
```
REQUIRED:
  - Completed implementation
  - Tests written and passing

PRODUCES:
  - Verification evidence (test output, manual checks)
  - Completion confirmation
```

---

## Skill Chains

### Feature Development Chain

```
[vague requirements] → context-capture → user-spec-planning → tech-spec-planning
                                                                    ↓
                                            subagent-driven-development
                                                                    ↓
                                              user-acceptance-testing
                                                                    ↓
                                           verification-before-completion
                                                                    ↓
                                                               [DONE]
```

**Detailed flow:**

1. **context-capture** (optional)
   - Input: Vague user request
   - Output: Clarified requirements
   - Skip if: Requirements already clear

2. **user-spec-planning**
   - Input: Project context + clarified requirements
   - Output: `work/<feature>/user-spec.md` (approved)
   - Blocks: Until user approves

3. **tech-spec-planning**
   - Input: `user-spec.md` + project guides
   - Output: `tech-spec.md` + `tasks/*.md` (approved)
   - Blocks: Until user approves

4. **subagent-driven-development**
   - Input: `tech-spec.md` + `tasks/*.md`
   - Output: Implemented code + tests + commits
   - Uses: TDD, code-reviewer (per task)

5. **user-acceptance-testing**
   - Input: `user-spec.md` + implemented code
   - Output: User approval
   - Blocks: Until user confirms

6. **verification-before-completion**
   - Input: Completed implementation
   - Output: Verification evidence
   - Blocks: Must pass before "done"

### Bug Fix Chain

```
[bug report] → systematic-debugging → root cause identified
                                              ↓
                          test-driven-development (write failing test)
                                              ↓
                                    implement fix
                                              ↓
                        verification-before-completion
                                              ↓
                                          [DONE]
```

**Rules:**
- ALWAYS use `systematic-debugging` first (never guess)
- Write failing test BEFORE fixing
- Verify fix with test + manual check

### Quick Task Chain (< 30 min)

```
[clear task] → test-driven-development → verification-before-completion → [DONE]
```

**Rules:**
- Skip planning skills if task is trivial
- Still require TDD and verification
- Use for: typo fixes, small refactors, config changes

---

## Error Recovery

### Missing Artifact Recovery

```
IF artifact missing:
  1. Log: "Missing required artifact: {artifact}"
  2. Check alternatives:
     - user-spec.md missing → Can user describe requirements?
     - tech-spec.md missing → Can we create minimal spec?
  3. If no alternative:
     - Invoke prerequisite skill
     - Resume after artifact created
```

### Skill Failure Recovery

```
IF skill fails:
  1. Check error type:
     - Transient (timeout, network) → Retry up to 3 times
     - Permanent (missing deps, invalid input) → Stop, report
     - Partial (some tasks done) → Resume from last successful

  2. For partial failure:
     - Mark completed tasks in STATE.md
     - Continue from first incomplete task
```

### User Rejection Recovery

```
IF user rejects output (user-spec, tech-spec):
  1. Collect feedback: What specifically is wrong?
  2. Make requested changes
  3. Re-present for approval
  4. Repeat until approved or user aborts
```

---

## Context Files Standard Locations

### Project Knowledge (read for understanding)
```
.claude/skills/project-knowledge/guides/
├── project.md        # What the project is
├── architecture.md   # How it's built
├── patterns.md       # Code patterns to follow
├── testing.md        # Testing approach
├── deployment.md     # How to deploy
├── database.md       # Data model
├── git-workflow.md   # Git conventions
└── ux.md             # User experience guidelines
```

### Work Items (read/write for feature work)
```
work/
├── STATE.md                    # Session state (always check first)
├── background-tasks.json       # Parallel task tracking
└── <feature-name>/
    ├── user-spec.md            # Business requirements
    ├── tech-spec.md            # Technical plan
    └── tasks/
        ├── 1.md                # Atomic task
        ├── 2.md
        └── ...
```

### Shared Templates (read for creating files)
```
~/.claude/shared/
├── work-templates/
│   ├── user-spec.md.template
│   ├── tech-spec.md.template
│   └── tasks/task.md.template
└── interview-templates/
    └── feature.yml
```

---

## Orchestrator Integration

The orchestrator uses this guide to:

1. **Validate prerequisites** before skill invocation
2. **Chain skills** based on their contracts
3. **Recover from errors** using defined patterns
4. **Track progress** through skill chains

### Pre-invocation Check

```
BEFORE invoking any skill:
  1. Read this file (skill-composition.md)
  2. Find skill in contracts table
  3. Check "Requires" column
  4. For each required artifact:
     - File exists? Check with ls/Read
     - Content valid? Check status field in frontmatter
  5. If missing:
     - Identify prerequisite skill
     - Invoke prerequisite first
     - Then invoke original skill
```

### Post-invocation Check

```
AFTER skill completes:
  1. Verify "Produces" artifacts exist
  2. Verify artifacts have correct format
  3. Update STATE.md with progress
  4. Determine next skill in chain (if any)
```

---

## Validation Examples

### Example 1: Starting feature development

```
User: "autowork: add dark mode"

Orchestrator checks:
1. Does work/dark-mode/user-spec.md exist? NO
2. Therefore: Cannot start subagent-driven-development
3. Action: Start with user-spec-planning

Flow:
  user-spec-planning → (creates user-spec.md)
  tech-spec-planning → (creates tech-spec.md + tasks)
  subagent-driven-development → (implements)
  user-acceptance-testing → (user confirms)
  verification-before-completion → (evidence collected)
  [DONE]
```

### Example 2: Resuming partial work

```
User: "continue"

Orchestrator checks STATE.md:
  Current Work: dark-mode
  Phase: implementation
  Status: task 3 of 5 complete

Action: Resume subagent-driven-development at task 4
```

### Example 3: Bug report

```
User: "login doesn't work"

Orchestrator classification:
  Intent: bug fix
  Confidence: high

Required skills:
  1. systematic-debugging (mandatory for bugs)
  2. test-driven-development (after root cause found)
  3. verification-before-completion

Does NOT need: user-spec-planning, tech-spec-planning
```

---

## Summary

| Phase | Skills | Validation |
|-------|--------|------------|
| Planning | context-capture → user-spec-planning → tech-spec-planning | Each produces required artifact for next |
| Execution | subagent-driven-development OR executing-plans | Requires approved tech-spec + tasks |
| Quality | user-acceptance-testing → verification-before-completion | BLOCKING - cannot skip |
| Bugs | systematic-debugging → TDD → verification | Always debug first |

**Key Rules:**
1. Never invoke skill without checking prerequisites
2. Never skip quality phase skills
3. Always update STATE.md after each skill
4. Chain skills in correct order (contracts define order)
