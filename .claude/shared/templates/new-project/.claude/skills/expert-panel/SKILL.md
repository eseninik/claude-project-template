---
name: expert-panel
description: |
  Multi-agent expert panel: spawns 3-5 domain experts (architect, security, performance, etc.) for DEEP analysis BEFORE implementation.
  Use when: user says "Agent Teams Mode" / "expert panel" / "экспертная панель", complex task needs multi-perspective analysis, risk assessment, architecture review from multiple angles, or trade-off evaluation across domains.
  Do NOT use for: simple bugs, single-file changes, code explanation, PR review, implementation (use TeamCreate/AO), automated scanning, or lightweight analysis (use auto-research phase instead).
roles: []
---

# Expert Panel

## Overview
Complex decisions benefit from multiple perspectives. The expert panel spawns 3-5 domain-specific agents in parallel to analyze a task from different angles, then converges their findings into a consensus recommendation before any implementation begins.

## Expert Selection

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

## Workflow

1. **SCOPE**: Classify domains from the task description, select 3-5 experts
2. **ANALYZE**: Spawn experts in parallel (READ-ONLY, no code changes)
3. **CONVERGE**: Lead collects findings, resolves conflicts via priority ladder
4. **DELIVER**: Write `work/expert-analysis.md`

## Output: work/expert-analysis.md

The analysis file must contain:
- Consensus Recommendations
- Architecture Recommendation
- Risk Assessment (probability + impact + mitigation)
- Trade-off Matrix
- Open Questions (for user)

Full workflow details: `cat .claude/guides/expert-panel-workflow.md`

## Common Mistakes
- **Starting implementation without expert-analysis.md** -- the entire point is analysis BEFORE code
- **Using fewer than 3 experts** -- insufficient perspective diversity
- **Letting experts modify code** -- experts are READ-ONLY analysts, not implementers
- **Skipping the convergence step** -- raw expert output without synthesis is not actionable

## Relationship to Auto-Research

Auto-Research (automatic, 3 agents) handles lightweight analysis for EVERY pipeline task.
Expert Panel (manual, 3-5 agents) handles DEEP analysis for critical/architectural decisions.

| Auto-Research | Expert Panel |
|---------------|-------------|
| Automatic | Manual trigger |
| 3 fixed agents | 3-5 domain-selected |
| 2-3 minutes | 5-10 minutes |
| GO/NO-GO gate | Detailed recommendations |
| Every pipeline | Critical decisions only |

Use Auto-Research for most tasks. Escalate to Expert Panel when:
- Architecture changes affecting 3+ modules
- Security-critical features
- Breaking changes or migrations
- User explicitly requests deep analysis

## Related
- → codebase-mapping — used by Researcher/Architect expert roles
- → systematic-debugging — used by Risk Assessor expert role
- ← task requiring multi-perspective analysis before implementation
