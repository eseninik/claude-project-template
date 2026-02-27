---
name: task-decomposition
description: |
  Analyzes tasks for parallel subtask splitting.
  Detects work streams (DB/API/UI/Tests) for smarter parallelization.
  Use when complex task has no clear structure or checking parallelization.
  Does NOT apply when tasks/*.md already exist (use subagent-driven-development).
---

## Philosophy
Good decomposition maximizes parallelism by identifying truly independent work streams. Dependencies between tasks are the enemy of speed.

## Critical Constraints
**never:**
- Mark dependent tasks as parallel
- Create tasks without checking for shared file dependencies

**always:**
- Detect work streams (DB/API/UI/Tests/Config)
- Calculate parallelization potential as percentage

## Runtime Configuration (Step 0)
Before executing, check `.claude/ops/config.yaml`:
- `pipeline_mode` → if `solo`, skip parallelization analysis
- `processing_depth` → affects decomposition granularity (quick=coarse, deep=fine-grained)

# Task Decomposition

## Algorithm
1. **Parse** task for subtasks (keywords, file references, dependency markers)
2. **Check independence** for each pair:
   - Different files → INDEPENDENT
   - B uses output of A → DEPENDENT
   - Unclear → UNCERTAIN (ask or go sequential)
3. **Detect work streams**: group by layer
   | Stream | Files | Usually Independent? |
   |--------|-------|---------------------|
   | Database | models/, migrations/ | Yes |
   | API | routes/, handlers/ | Depends on DB |
   | Logic | services/, core/ | Depends on DB |
   | UI | components/, pages/ | Depends on API |
   | Tests | tests/ | Depends on all |
   | Config | config/, docker/ | Yes |
4. **Build waves**: independent streams = Wave 1, dependent = Wave 2+
5. **Report**: N subtasks across M streams, confidence %

## Output
```
Task splits into N subtasks across M streams:
Stream: Database [tasks 1,2] (Wave 1)
Stream: API [tasks 3,4] (Wave 2, depends on Database)
Confidence: X%
Options: 1) Create tasks (parallel) 2) Sequential 3) Clarify
```

## Complexity Assessment

After decomposition, assess overall task risk:

| Level | Criteria | QA Depth |
|-------|----------|----------|
| **trivial** | 1 file, < 20 lines, no logic change | Skip QA, verification only |
| **low** | 2-3 files, single module, clear pattern | Unit tests only |
| **medium** | 4-10 files, 2+ modules, some unknowns | Unit + integration tests |
| **high** | 10+ files, cross-cutting, external APIs | Full QA loop + security scan |
| **critical** | Architecture change, data migration, security | Full QA + human review required |

Assessment factors:
- **Scope**: estimated files, services, modules affected
- **Integration**: external services, new dependencies, research needed
- **Infrastructure**: Docker, DB, config changes
- **Knowledge**: familiar patterns? research required? unfamiliar tech?
- **Risk**: concerns list, security implications

Output the assessment:
```
Complexity: {level}
Confidence: {%}
QA Depth: {recommended validation}
Concerns: {list}
```

Reference: `.claude/guides/complexity-assessment.md`
