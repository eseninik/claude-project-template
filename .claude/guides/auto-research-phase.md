# Auto-Research Phase

> Lightweight automatic research phase. Runs at the start of every pipeline.
> For heavy analysis, use Expert Panel (manual trigger).

## Overview

Every pipeline task benefits from 2-3 minutes of structured analysis before implementation.
Auto-Research spawns 2-3 lightweight agents in parallel to analyze the task from different angles.

## Agents (always 3, parallel)

### 1. Requirement Analyst
- **Type**: requirement-analyst (read-only)
- **Job**: Parse the task, identify acceptance criteria, find ambiguities
- **Output**: Structured requirements list + questions for user (if any)

### 2. Technical Feasibility Analyst
- **Type**: feasibility-analyst (read-only)
- **Job**: Check existing codebase for constraints, find relevant files, assess complexity
- **Output**: Affected files list + technical risks + complexity estimate (LOW/MEDIUM/HIGH)

### 3. Risk Assessor
- **Type**: risk-assessor (read-only)
- **Job**: Identify risks, breaking changes, security concerns, edge cases
- **Output**: Risk matrix (probability + impact + mitigation)

## Output: work/{feature}/auto-research.md

```markdown
# Auto-Research: {task name}

## Requirements (from Requirement Analyst)
- [ ] Criterion 1
- [ ] Criterion 2
...

## Technical Analysis (from Feasibility Analyst)
- Complexity: LOW | MEDIUM | HIGH
- Affected files: [list]
- Technical risks: [list]
- Existing patterns to follow: [list]

## Risk Assessment
| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|

## GO/NO-GO
- [ ] Requirements clear (no ambiguities blocking implementation)
- [ ] Technical approach identified
- [ ] No HIGH risks without mitigation

**Decision**: GO / NO-GO (needs user input)
```

## When to Skip (complexity < threshold)

Auto-Research is skipped for:
- Single-file changes (1 file affected)
- Bug fixes with clear reproduction steps
- Documentation-only changes
- Config changes

These go directly to IMPLEMENT phase.

## Relationship to Expert Panel

| Aspect | Auto-Research | Expert Panel |
|--------|--------------|--------------|
| Trigger | Automatic (pipeline start) | Manual ("expert panel") |
| Agents | 3 (fixed) | 3-5 (selected by domain) |
| Duration | 2-3 minutes | 5-10 minutes |
| Output | auto-research.md | expert-analysis.md |
| Gate | GO/NO-GO (auto or user) | User approval required |
| Use for | Every pipeline task | Critical/architectural decisions |
| Roles | Requirement, Technical, Risk | Business, Architect, Security, API, etc. |
