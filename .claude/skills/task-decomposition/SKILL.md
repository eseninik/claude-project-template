---
name: task-decomposition
description: |
  Analyzes a task and determines whether it can be split into parallel subtasks.
  Activate when checking for parallelization opportunities, user asks "can this be parallelized?",
  or a complex task has no clear structure.
  Does NOT apply when tasks/*.md already exist (use subagent-driven-development) or a plan.md exists.
---

# Task Decomposition

## When to Use
- Complex task with no clear structure
- User asks "can this be parallelized?"
- 3+ potential independent subtasks detected

## When NOT to Use
- tasks/*.md already exist (use subagent-driven-development)
- plan.md exists (offer conversion)
- <3 subtasks (parallelization overhead not worth it)

## Algorithm

1. **Parse** task text for: keywords, lists, file references, dependency markers ("after", "using result of")
2. **Check independence** for each pair (A, B):
   - Different files -> INDEPENDENT
   - Same file, different functions -> INDEPENDENT (Worktree Mode)
   - B uses output of A -> DEPENDENT
   - "first X, then Y" with real data dep -> DEPENDENT
   - "first X, then Y" without data dep -> INDEPENDENT
   - Unclear -> UNCERTAIN
3. **Build waves**:
   - Wave 1: all tasks with no dependencies
   - Remaining: wave = max(wave of deps) + 1
4. **Calculate confidence**:
   - Base 50% + 30% pattern match + 20% explicit list + 10% different files - 20% UNCERTAIN deps
5. **Recommend**:
   - `>90%`: recommend confidently
   - `60-90%`: recommend with note
   - `<60%`: ask for details

## Output Format

```
Task splits into N subtasks:
1. {subtask} ({files})
2. {subtask} ({files})

Waves: Wave 1 [1,2,3] parallel | Wave 2 [4] depends on Wave 1
Confidence: X%

Options: 1) Create tasks/*.md (parallel) 2) Sequential 3) Clarify
```

## Task File Creation (if user approves)

```bash
mkdir -p work/{feature}/tasks/
# Each file: frontmatter (depends_on, files_modified) + description + done criteria
```

After creation, subagent-driven-development takes over.

## Hard Rules
- Never create tasks/*.md without user consent
- Never claim high confidence when dependencies unclear
- Sequential is safer when uncertain
