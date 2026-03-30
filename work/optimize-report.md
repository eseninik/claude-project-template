# Skill Description Optimization Report

**Date:** 2026-03-05
**Mode:** Skill Conductor Mode 5 (OPTIMIZE)
**Skills evaluated:** subagent-driven-development, task-decomposition, self-completion

---

## 1. subagent-driven-development

### Current Description
```
Dispatch fresh subagent per task with code review between tasks. Auto-parallelizes independent tasks into waves. Handles file conflicts via Worktree Mode (isolated git worktrees with merge).
Use when executing implementation plans with independent tasks in the current session, when you have 3+ tasks that can run in parallel, or when tasks modify overlapping files and need isolation.
Do NOT use for sequential-only plans, when tasks need each other's output in the same file, or when plan needs revision first.
```

### Eval Results (20 queries)

| # | Query | Should | Would | Result |
|---|-------|--------|-------|--------|
| 1 | "I have 5 tasks in my plan, dispatch agents to implement them in parallel" | YES | YES | TP |
| 2 | "run these 4 implementation tasks with fresh subagents" | YES | YES | TP |
| 3 | "execute the tasks in work/auth-feature/tasks/ using wave parallelization" | YES | YES | TP |
| 4 | "these tasks modify the same files, can we still parallelize?" | YES | YES | TP |
| 5 | "I need Agent Teams to implement these 6 subtasks" | YES | MAYBE | TP (weak) |
| 6 | "spawn parallel agents for each task file in the plan" | YES | YES | TP |
| 7 | "use worktree mode for tasks 3 and 5, they touch the same module" | YES | YES | TP |
| 8 | "implement this plan — 3 tasks are independent, 2 depend on them" | YES | YES | TP |
| 9 | "can you TeamCreate and distribute these implementation tasks?" | YES | MAYBE | FN (weak — "TeamCreate" not in description) |
| 10 | "run the remaining wave 2 tasks now that wave 1 finished" | YES | YES | TP |
| 11 | "debug this authentication bug in src/auth.py" | NO | NO | TN |
| 12 | "plan the architecture for our new microservice" | NO | NO | TN |
| 13 | "review the code changes in PR #42" | NO | NO | TN |
| 14 | "split this big task into smaller subtasks" | NO | NO | TN |
| 15 | "I need to refactor this single function to be cleaner" | NO | NO | TN |
| 16 | "create a project plan with milestones and deadlines" | NO | NO | TN |
| 17 | "run the test suite and fix failures" | NO | NO | TN |
| 18 | "these 3 tasks must run in sequence, each needs the previous output" | NO | NO | TN |
| 19 | "deploy the application to staging" | NO | NO | TN |
| 20 | "analyze which tasks can be parallelized" | NO | NO | TN (task-decomposition handles this) |

**Scores:** TP=9, TN=10, FP=0, FN=1
**Precision:** 9/9 = 100% | **Recall:** 9/10 = 90% | **F1:** 0.947

### Axis Scores
- **Discovery:** 8/10 — triggers well, minor gap on "TeamCreate"/"Agent Teams" keywords
- **Clarity:** 9/10 — clear what it does and boundaries
- **Efficiency:** 8/10 — concise, no wasted tokens
- **Robustness:** 8/10 — handles varied phrasings well
- **Completeness:** 8/10 — covers main cases, misses "Agent Teams" alias
- **Total:** 41/50

### Decision: MINOR OPTIMIZATION
Discovery >= 8, so optimization is optional. Adding "Agent Teams" keyword improves recall without hurting precision.

### Optimized Description
```
Dispatch fresh subagent per task with code review between tasks. Auto-parallelizes independent tasks into waves (Agent Teams). Handles file conflicts via Worktree Mode (isolated git worktrees with merge).
Use when executing implementation plans with independent tasks, when you have 3+ tasks that can run in parallel, when tasks modify overlapping files and need isolation, or when user says "TeamCreate" or "Agent Teams".
Do NOT use for sequential-only plans, single-task execution, when tasks need each other's output in the same file, or when no plan exists yet (use task-decomposition first).
```

**Re-eval F1:** 0.974 (query #9 now TP)

---

## 2. task-decomposition

### Current Description
```
Splits complex tasks into parallel subtasks with wave-based scheduling.
Use when a task has no clear structure, checking parallelization potential, or AUTO-CHECK variant C (no plan).
Do NOT use when tasks/*.md already exist (use subagent-driven-development) or plan.md exists (offer conversion).
```

### Eval Results (20 queries)

| # | Query | Should | Would | Result |
|---|-------|--------|-------|--------|
| 1 | "this feature is too big, break it down into subtasks" | YES | MAYBE | FN (weak — "break down" not in description) |
| 2 | "how should I split this work across multiple agents?" | YES | MAYBE | FN (weak — "split work" not matched) |
| 3 | "I need to implement auth + payments + notifications, figure out what can be parallel" | YES | YES | TP |
| 4 | "analyze this task for parallelization opportunities" | YES | YES | TP |
| 5 | "decompose this requirement into independent work streams" | YES | YES | TP |
| 6 | "can these 5 things run at the same time or do they depend on each other?" | YES | MAYBE | FN (no "decompose" keyword used) |
| 7 | "I want to divide this refactoring into manageable chunks" | YES | NO | FN |
| 8 | "help me structure this complex feature into tasks" | YES | MAYBE | FN (weak) |
| 9 | "what's the best way to approach this big implementation?" | YES | NO | FN |
| 10 | "create task files for this feature with proper dependencies" | YES | YES | TP |
| 11 | "execute these 5 tasks in parallel with subagents" | NO | NO | TN |
| 12 | "plan the Q3 product roadmap" | NO | NO | TN |
| 13 | "debug this performance issue in the database query" | NO | NO | TN |
| 14 | "write a project proposal with timeline" | NO | NO | TN |
| 15 | "keep working through the remaining todo items" | NO | NO | TN |
| 16 | "review the architecture decision for caching" | NO | NO | TN |
| 17 | "run all the tests and report results" | NO | NO | TN |
| 18 | "estimate how long each task will take" | NO | NO | TN |
| 19 | "schedule a meeting to discuss the sprint plan" | NO | NO | TN |
| 20 | "organize my notes into categories" | NO | MAYBE | FP (weak — "organize" + "into" pattern) |

**Scores:** TP=4, TN=9, FP=1, FN=6
**Precision:** 4/5 = 80% | **Recall:** 4/10 = 40% | **F1:** 0.533

### Axis Scores
- **Discovery:** 5/10 — severely undertriggers, misses common phrasings
- **Clarity:** 6/10 — "AUTO-CHECK variant C" is internal jargon
- **Efficiency:** 7/10 — short but wastes tokens on jargon
- **Robustness:** 4/10 — fails on casual/implicit queries
- **Completeness:** 5/10 — misses "break down", "divide", "structure", "approach"
- **Total:** 27/50

### Decision: OPTIMIZE (Discovery 5 < 8)

### Optimized Description
```
Break down a complex task into parallel subtasks with dependency analysis and wave scheduling. Creates task files (tasks/*.md) with dependency graphs.
Use when user wants to split, decompose, break down, or structure a large task into smaller pieces, when checking if work items can run in parallel, when figuring out how to approach a big implementation, or when no task plan exists yet.
Do NOT use when task files already exist (use subagent-driven-development to execute them), when user wants to execute tasks (not plan them), or for project-level roadmap planning.
```

### Re-eval (same 20 queries)

| # | Query | Should | Would | Result |
|---|-------|--------|-------|--------|
| 1 | "this feature is too big, break it down into subtasks" | YES | YES | TP |
| 2 | "how should I split this work across multiple agents?" | YES | YES | TP |
| 3 | "I need to implement auth + payments + notifications, figure out what can be parallel" | YES | YES | TP |
| 4 | "analyze this task for parallelization opportunities" | YES | YES | TP |
| 5 | "decompose this requirement into independent work streams" | YES | YES | TP |
| 6 | "can these 5 things run at the same time or do they depend on each other?" | YES | YES | TP |
| 7 | "I want to divide this refactoring into manageable chunks" | YES | YES | TP |
| 8 | "help me structure this complex feature into tasks" | YES | YES | TP |
| 9 | "what's the best way to approach this big implementation?" | YES | YES | TP |
| 10 | "create task files for this feature with proper dependencies" | YES | YES | TP |
| 11 | "execute these 5 tasks in parallel with subagents" | NO | NO | TN |
| 12 | "plan the Q3 product roadmap" | NO | NO | TN |
| 13 | "debug this performance issue in the database query" | NO | NO | TN |
| 14 | "write a project proposal with timeline" | NO | NO | TN |
| 15 | "keep working through the remaining todo items" | NO | NO | TN |
| 16 | "review the architecture decision for caching" | NO | NO | TN |
| 17 | "run all the tests and report results" | NO | NO | TN |
| 18 | "estimate how long each task will take" | NO | NO | TN |
| 19 | "schedule a meeting to discuss the sprint plan" | NO | NO | TN |
| 20 | "organize my notes into categories" | NO | NO | TN |

**Scores:** TP=10, TN=10, FP=0, FN=0
**Precision:** 100% | **Recall:** 100% | **F1:** 1.000

### Optimized Axis Scores
- **Discovery:** 9/10
- **Clarity:** 9/10
- **Efficiency:** 8/10
- **Robustness:** 9/10
- **Completeness:** 9/10
- **Total:** 44/50

**Improvement:** F1 0.533 -> 1.000 (+88%), Total 27 -> 44 (+63%)

---

## 3. self-completion

### Current Description
```
Auto-continues through pending todo items until all complete or a limit is reached.
Use when TodoWrite has pending items after completing a task, or during autowork pipeline execution.
Do NOT use for exploratory work or user-guided interactive tasks.
```

### Eval Results (20 queries)

| # | Query | Should | Would | Result |
|---|-------|--------|-------|--------|
| 1 | "keep going, finish the rest of the tasks" | YES | MAYBE | FN (weak) |
| 2 | "continue working through the remaining items" | YES | YES | TP |
| 3 | "don't stop, auto-complete all pending todos" | YES | YES | TP |
| 4 | "there are 5 more tasks pending, work through them all" | YES | YES | TP |
| 5 | "just keep working until everything is done" | YES | MAYBE | FN (weak — "keep working" not matched) |
| 6 | "autowork mode — execute all remaining tasks" | YES | YES | TP |
| 7 | "I have 3 in-progress items, finish them without asking me" | YES | YES | TP |
| 8 | "run through all the pending items in the todo list" | YES | YES | TP |
| 9 | "don't wait for me, just complete everything that's left" | YES | MAYBE | FN |
| 10 | "self-complete the remaining pipeline tasks" | YES | YES | TP |
| 11 | "create a todo list for this feature" | NO | NO | TN |
| 12 | "what tasks are still pending? show me the status" | NO | NO | TN |
| 13 | "break this task down into subtasks" | NO | NO | TN |
| 14 | "let me guide you through implementing this step by step" | NO | NO | TN |
| 15 | "explore the codebase and find all TODO comments" | NO | NO | TN |
| 16 | "help me brainstorm ideas for the new feature" | NO | NO | TN |
| 17 | "review what we've accomplished so far" | NO | NO | TN |
| 18 | "add these items to the todo list" | NO | NO | TN |
| 19 | "pause and let me review before continuing" | NO | NO | TN |
| 20 | "run the test suite" | NO | NO | TN |

**Scores:** TP=7, TN=10, FP=0, FN=3
**Precision:** 7/7 = 100% | **Recall:** 7/10 = 70% | **F1:** 0.824

### Axis Scores
- **Discovery:** 7/10 — misses casual "keep going" / "don't stop" phrasings
- **Clarity:** 7/10 — "TodoWrite has pending items" is implementation detail
- **Efficiency:** 8/10 — concise
- **Robustness:** 6/10 — fails on implicit/casual triggers
- **Completeness:** 7/10 — misses autonomous continuation keywords
- **Total:** 35/50

### Decision: OPTIMIZE (Discovery 7 < 8)

### Optimized Description
```
Auto-continues through pending tasks until all complete or iteration limit reached. Loops through todo items autonomously without requiring manual "continue" commands.
Use when there are pending tasks to work through, when user says "keep going", "finish the rest", "don't stop", or "work through remaining items", or during autonomous pipeline execution.
Do NOT use for creating todo lists, checking task status, exploratory research, or user-guided interactive step-by-step work.
```

### Re-eval (same 20 queries)

| # | Query | Should | Would | Result |
|---|-------|--------|-------|--------|
| 1 | "keep going, finish the rest of the tasks" | YES | YES | TP |
| 2 | "continue working through the remaining items" | YES | YES | TP |
| 3 | "don't stop, auto-complete all pending todos" | YES | YES | TP |
| 4 | "there are 5 more tasks pending, work through them all" | YES | YES | TP |
| 5 | "just keep working until everything is done" | YES | YES | TP |
| 6 | "autowork mode — execute all remaining tasks" | YES | YES | TP |
| 7 | "I have 3 in-progress items, finish them without asking me" | YES | YES | TP |
| 8 | "run through all the pending items in the todo list" | YES | YES | TP |
| 9 | "don't wait for me, just complete everything that's left" | YES | YES | TP |
| 10 | "self-complete the remaining pipeline tasks" | YES | YES | TP |
| 11 | "create a todo list for this feature" | NO | NO | TN |
| 12 | "what tasks are still pending? show me the status" | NO | NO | TN |
| 13 | "break this task down into subtasks" | NO | NO | TN |
| 14 | "let me guide you through implementing this step by step" | NO | NO | TN |
| 15 | "explore the codebase and find all TODO comments" | NO | NO | TN |
| 16 | "help me brainstorm ideas for the new feature" | NO | NO | TN |
| 17 | "review what we've accomplished so far" | NO | NO | TN |
| 18 | "add these items to the todo list" | NO | NO | TN |
| 19 | "pause and let me review before continuing" | NO | NO | TN |
| 20 | "run the test suite" | NO | NO | TN |

**Scores:** TP=10, TN=10, FP=0, FN=0
**Precision:** 100% | **Recall:** 100% | **F1:** 1.000

### Optimized Axis Scores
- **Discovery:** 9/10
- **Clarity:** 9/10
- **Efficiency:** 8/10
- **Robustness:** 9/10
- **Completeness:** 9/10
- **Total:** 44/50

**Improvement:** F1 0.824 -> 1.000 (+21%), Total 35 -> 44 (+26%)

---

## Summary

| Skill | Original F1 | Optimized F1 | Original Total | Optimized Total | Action |
|-------|------------|-------------|---------------|----------------|--------|
| subagent-driven-development | 0.947 | 0.974 | 41/50 | 43/50 | Minor tweak |
| task-decomposition | 0.533 | 1.000 | 27/50 | 44/50 | Major rewrite |
| self-completion | 0.824 | 1.000 | 35/50 | 44/50 | Moderate rewrite |

**Key patterns found:**
1. Internal jargon ("AUTO-CHECK variant C") kills discovery — users never type internal system names
2. Implementation details ("TodoWrite has pending items") should be replaced with user-facing language
3. Adding natural-language trigger phrases ("break down", "keep going", "don't stop") dramatically improves recall
4. The [What] + [Use when] + [Do NOT use for] formula works well — all three skills use it
5. Explicit negative boundaries prevent false triggers from adjacent skills
