---
name: expert-panel
description: |
  Multi-agent expert panel for task analysis before implementation.
  Spawns 3-5 specialized experts from pool of 10, selected by domain.
  Use when user says "Agent Teams Mode", "expert panel", or complex task needs multi-perspective analysis.
  Does NOT apply to simple tasks (1-2 files) or trivial bugs.
---

## Philosophy
Complex decisions benefit from multiple perspectives. No single viewpoint can identify all risks, trade-offs, and opportunities.

## Critical Constraints
**never:**
- Begin implementation without expert-analysis.md produced
- Use fewer than 3 experts

**always:**
- Select experts from different domains relevant to the task
- Produce consensus recommendations with explicit dissent

# Expert Panel

## Quick Reference

### Always Include
- Business Analyst
- System Architect

### Add by Domain (1-3, cap at 5 total)
| Keyword | Expert |
|---------|--------|
| auth, login, token, permission | Security Analyst |
| api, endpoint, webhook | API Designer |
| schema, migration, database | Data Architect |
| async, concurrent, parallel | Async Specialist |
| performance, cache, optimize | Performance Engineer |
| unknown lib, research | Researcher (codebase-mapping) |
| critical, migration, breaking | Risk Assessor (systematic-debugging) |

### Workflow
1. **SCOPE**: Classify domains, select 3-5 experts
2. **ANALYZE**: Spawn experts in parallel (READ-ONLY, no code changes)
3. **CONVERGE**: Lead collects findings, resolves conflicts via priority ladder
4. **DELIVER**: Write `work/expert-analysis.md`

### Output: work/expert-analysis.md
- Consensus Recommendations
- Architecture Recommendation
- Risk Assessment (probability + impact + mitigation)
- Trade-off Matrix
- Open Questions (for user)

Full workflow details: `cat .claude/guides/expert-panel-workflow.md`
