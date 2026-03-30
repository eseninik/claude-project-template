---
name: task-decomposition
description: |
  Break down a complex task into parallel subtasks with DAG-based dependency analysis, XML task structure, and wave scheduling. Creates task files (tasks/*.md) with dependency graphs and formal DAG construction.
  Use when user wants to split, decompose, break down, or structure a large task into smaller pieces, when checking if work items can run in parallel, when figuring out how to approach a big implementation, or when no task plan exists yet.
  Do NOT use when task files already exist (use subagent-driven-development to execute them), when user wants to execute tasks (not plan them), or for project-level roadmap planning.
roles: [planner, complexity-assessor, wave-coordinator, dag-analyzer]
---

# Task Decomposition

## Overview

Analyze a complex task to discover independent subtasks that can run in parallel.
Core principle: identify work streams, check independence, group into execution waves.

## Process

### 1. Load Knowledge Base

```bash
cat .claude/knowledge/parallelization-patterns.md
```

Extract: typical task patterns, recognition triggers, independence algorithm, examples.

### 2. Parse Task Description

Extract from the user's task:
1. Keywords (match against pattern triggers)
2. Structure (lists, conjunctions, file references)
3. Mentioned files/modules
4. Dependencies between parts

**Extraction techniques:**

- **Pattern matching** — check keywords against knowledge base triggers
  - Example: "JWT authentication" matches "Authentication" pattern
- **List extraction** — numbered/bulleted lists become subtasks directly
- **File extraction** — "Update user.py, api.py, auth.py" = 3 file-based subtasks
- **Conjunctions** — "X, and also Y", "X, besides Z" = 2+ subtasks

### 3. Determine Subtasks

**If pattern matched:** use subtasks from the pattern definition.

**If no pattern:** extract from text structure (lists, conjunctions, files).

### 4. Check Independence

For each pair of subtasks (A, B):

| Condition | Result |
|-----------|--------|
| Different files | INDEPENDENT |
| Same file, different functions/classes | INDEPENDENT (worktree possible) |
| "using result of", "based on" | DEPENDENT |
| Sequential keywords but no data flow | INDEPENDENT |
| Uncertain | UNCERTAIN |

### 5. Build Waves

```
Wave 1: All tasks with zero dependencies
For each remaining task:
  max_wave = max(wave[dep] for dep in task.dependencies)
  wave[task] = max_wave + 1
```

## Formal DAG Construction

### Algorithm

1. Parse all tasks — extract `depends_on` and `files_modified`
2. Build adjacency list: task — [dependencies]
3. Topological sort (detect cycles — if cycle found, STOP and report)
4. Assign waves using critical path:
   - Wave 0: tasks with no dependencies
   - Wave N: max(wave[dep] for dep in task.deps) + 1
5. Within each wave, check file conflicts:
   - No overlap — standard parallel
   - Overlap detected — mark for Worktree Mode
6. Output: tasks/waves.md with DAG visualization

### DAG Visualization Format

```markdown
# Wave Analysis

## Dependency Graph

task-1 ---\
task-2 ----+--- task-4 ---\
task-3 ---/                +--- task-6
            task-5 --------/

## Wave Assignment
| Wave | Tasks | Parallel | Dependencies |
|------|-------|----------|-------------|
| 1 | task-1, task-2, task-3 | Yes (3) | None |
| 2 | task-4, task-5 | Yes (2) | Wave 1 |
| 3 | task-6 | No (1) | Wave 2 |

## File Conflict Matrix
| | task-1 | task-2 | task-3 |
|---|--------|--------|--------|
| task-1 | - | None | config.yaml |
| task-2 | None | - | None |
| task-3 | config.yaml | None | - |

Conflicts: task-1 <-> task-3 on config.yaml -> Worktree Mode required
```

### 6. Calculate Confidence

Start at 50% base:

| Factor | Adjustment |
|--------|-----------|
| Pattern matched | +30% |
| Explicit list found | +20% |
| Different files | +10% |
| UNCERTAIN dependencies exist | -20% |

**Thresholds:**
- **>90%** High — propose confidently
- **60-90%** Medium — propose with "recommended" note
- **<60%** Low — ask for details first

### 7. Present Recommendation

**If subtasks < 3:** recommend sequential execution.

**If subtasks >= 3 and confidence > 80%:**
```
I see the task can be split into [N] independent subtasks:
1. [subtask 1]
2. [subtask 2]
3. [subtask 3]

Wave analysis:
- Wave 1: [list] (parallel)
- Wave 2: [list] (depends on Wave 1)

Options:
1. Create work/{feature}/tasks/*.md and execute in parallel (recommended)
   -> Saves ~[X]% time
2. Work sequentially
3. Give me more details to refine the plan

Which option?
```

**If confidence 60-80%:** present subtasks but ask about uncertain dependencies before proceeding.

**If confidence < 60%:** ask for specifics (which components, which files, what dependencies).

### 8. Generate Task Files (if user approves)

```bash
mkdir -p work/{feature-name}/tasks/
```

Each `task-{N}.md`:

```markdown
---
depends_on: []
files_modified:
  - path/to/file
---

# Task {N}: [Subtask Name]

## Description
[What to do]

## Implementation Details
[Steps from pattern or extracted]

## Done Criteria
- [ ] Code written
- [ ] Tests written
- [ ] Tests pass
- [ ] Committed
```

## XML Task Structure

For Claude-optimized parsing, tasks support XML format within markdown:

### Task File Format (Enhanced)

```markdown
---
depends_on: []
wave: 1
files_modified:
  - path/to/file
must_haves:
  truths: ["Users can log in via email"]
  artifacts: ["src/auth/login.ts", "src/auth/login.test.ts"]
  key_links: ["login.ts imports from auth-provider.ts"]
---

# Task {N}: [Name]

<objective>
What this task accomplishes and why.
</objective>

<tasks>
<task type="auto">
  <name>Implement login endpoint</name>
  <files>src/auth/login.ts</files>
  <action>Create POST /auth/login handler with email/password validation</action>
  <verify>curl -s http://localhost:3000/auth/login -d '{"email":"test@test.com"}' | jq .token</verify>
  <done>Login endpoint returns JWT token for valid credentials</done>
</task>

<task type="checkpoint:human-verify">
  <what-built>Login form with error states</what-built>
  <how-to-verify>
    1. Navigate to /login
    2. Enter invalid email -- see error message
    3. Enter valid creds -- redirect to dashboard
  </how-to-verify>
  <resume-signal>Type "approved" or describe issues</resume-signal>
</task>
</tasks>

<success_criteria>
- Login endpoint returns 200 with JWT for valid credentials
- Login endpoint returns 401 for invalid credentials
- Login form displays validation errors
</success_criteria>
```

### Checkpoint Types in Tasks

| Type | Usage | Auto-Mode |
|------|-------|-----------|
| `auto` | Fully automated task | Execute normally |
| `checkpoint:human-verify` | Claude built it, user checks visually | Auto-approve in YOLO mode |
| `checkpoint:decision` | User must choose between options | Auto-select first option |
| `checkpoint:human-action` | Requires manual action (2FA, OAuth) | Always pause |

## Decimal Phase Support

When gap-closure work is needed between existing phases, use decimal numbering:

### When to Use
- Verification found gaps after Phase 3 -- create Phase 3.1
- UAT failed on Phase 2 -- create Phase 2.1 for fixes
- Urgent insertion needed -- Phase N.M where M is sequential

### Numbering Rules
- Integer phases: 1, 2, 3 (planned work)
- Decimal phases: 3.1, 3.2 (gap closure / urgent inserts)
- Execution order: 1 -> 2 -> 2.1 -> 3 -> 3.1 -> 3.2 -> 4
- No renumbering of existing phases needed

### Task File Naming
- Standard: `task-001.md`, `task-002.md`
- Decimal phase: `task-003.1-001.md` (phase 3.1, task 1)

### In PIPELINE.md

```
### Phase: 3
- Status: DONE

### Phase: 3.1 (Gap Closure)
- Status: PENDING
- Inserted: after verification gaps in Phase 3
- On PASS: -> Phase 4
```

### 9. Hand Off to Execution

After creating tasks/*.md:
1. AUTO-CHECK variant A triggers
2. subagent-driven-development loads
3. Wave analysis runs
4. Parallel execution begins

## Integration with AUTO-CHECK

```
AUTO-CHECK question: "Is there a clear plan?"

A. Plan in work/*/tasks/*.md format?
   -> subagent-driven-development

B. Plan in other format (plan.md)?
   -> Offer conversion

C. No plan (this skill):
   1. Invoke task-decomposition
   2. Apply steps 1-7
   3. Present recommendation
   4. If user chooses "create tasks/*.md"
      -> Generate structure, then subagent-driven-development
```

## Common Mistakes

1. **Creating tasks/*.md without user consent** — always ask first
2. **Claiming high confidence with unclear dependencies** — be conservative
3. **Ignoring explicit dependency markers** ("using result of", "based on")
4. **Forcing parallelization on < 3 subtasks** — sequential is fine for small sets
5. **Not checking for existing plans** — if tasks/*.md or plan.md already exist, use them

When uncertain: ask the user. Sequential is always the safe fallback.

See `references/examples.md` for worked examples at each confidence level.

## Related
- → subagent-driven-development — executes the decomposed tasks
- → using-git-worktrees — parallel execution in isolated worktrees
- ← tech-spec-planning — tech spec feeds task breakdown
- ← complex tasks — triggered by need to split/structure work
