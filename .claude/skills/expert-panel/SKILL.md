---
description: |
  WHAT: Multi-agent expert panel for task analysis before implementation.
  WHEN: User says "Agent Teams Mode", "экспертная панель", or complex task needs multi-perspective analysis.
  NOT: Simple tasks (1-2 files), trivial bugs, tasks user marks as "без панели".
triggers:
  - agent teams mode
  - expert panel
  - экспертная панель
  - multi-perspective analysis
  - complex architecture decision
---

# Expert Panel

> Adaptive multi-agent analysis: 3-5 experts from a pool of 10, selected by task domain.

---

## Adaptive Role Pool

Select 3-5 roles based on task domain. **Always include** Business Analyst + System Architect. Add 1-3 domain-specific roles. Cap at 5.

| Role | Domain Trigger | Skills to Load | Include When |
|------|---------------|----------------|--------------|
| **Business Analyst** | Any feature with user impact | project-knowledge | Always for features |
| **System Architect** | Any architectural task | project-knowledge | Always for impl tasks |
| **Security Analyst** | Auth, PII, payments, external APIs | — (Opus knows OWASP) | Security-relevant tasks |
| **QA Strategist** | Any implementation task | verification-before-completion | Always for impl tasks |
| **Performance Engineer** | High-load, optimization, caching | — (general knowledge) | Performance matters |
| **API Designer** | Endpoints, integrations, webhooks | — (general knowledge) | API work |
| **Data Architect** | Schema changes, migrations, data flow | project-knowledge | Data model changes |
| **Async Specialist** | Event-driven, async, concurrent | — (general knowledge) | Async code involved |
| **Researcher** | Unknown domains, new libraries | codebase-mapping | Unfamiliar domain |
| **Risk Assessor** | Critical systems, migrations, breaking changes | systematic-debugging | High-risk changes |

---

## Domain Detection Algorithm

```
1. Parse task description for keywords
2. Map keywords → domains:
   - auth|login|password|token|permission → SECURITY
   - api|endpoint|webhook|rest|graphql → API
   - schema|migration|database|model → DATA
   - async|concurrent|parallel|event → ASYNC
   - performance|speed|cache|optimize → PERFORMANCE
   - unknown lib|new framework|research → RESEARCH
   - critical|migration|breaking|production → RISK
3. Always include: Business Analyst, System Architect
4. Add QA Strategist if implementation expected
5. Add domain-specific roles (1-3) based on detected domains
6. Cap total at 5 experts
```

### Selection Examples

| Task | Detected Domains | Panel (3-5) |
|------|-----------------|-------------|
| "Add user authentication" | SECURITY | BA, Architect, Security, QA (4) |
| "New REST API for orders" | API, DATA | BA, Architect, API Designer, QA (4) |
| "Optimize database queries" | PERFORMANCE, DATA | BA, Architect, Performance, Data Architect (4) |
| "Migrate to async handlers" | ASYNC, RISK | BA, Architect, Async Specialist, Risk, QA (5) |
| "Add Telegram bot feature" | — | BA, Architect, QA (3) |

---

## Panel Workflow

### Phase: SCOPE (lead, before team)
1. Classify task domain (algorithm above)
2. Select expert roles
3. Map skills to each role
4. Prepare panel composition summary for user

### Phase: ANALYZE (parallel, all experts)
Each expert receives:
- Task description
- Project context (architecture.md, patterns.md)
- Their domain-specific focus area
- Priority Ladder reference (`cat .claude/guides/priority-ladder.md`)

Each expert produces:
- Domain-specific findings (2-5 bullet points)
- Risks from their perspective
- Recommendations with priority level

### Phase: DEBATE (SendMessage between experts)
- Lead collects all analyses
- Identifies conflicts between expert recommendations
- Resolves conflicts using Priority Ladder (higher level wins)

### Phase: CONVERGE (lead collects)
- Merge non-conflicting recommendations
- Apply Priority Ladder to conflicts
- Build consensus summary

### Phase: DELIVER (lead writes)
- Write `work/expert-analysis.md` using output template below
- Present summary to user
- List open questions requiring user input

---

## Expert Analysis Output Template

```markdown
---
date: YYYY-MM-DD
task: "[task description]"
panel_size: N
domains: [domain1, domain2, ...]
experts: [role1, role2, ...]
---

# Expert Panel Analysis

## Task Scope
[1-2 sentences defining what was analyzed]

## Panel Composition
| Role | Focus Area | Skills Used |
|------|-----------|-------------|
| ... | ... | ... |

## Consensus Recommendations
[Bullet points all experts agree on]

## Architecture Recommendation
[Recommended approach with justification]

## Risk Assessment
| Risk | Probability | Impact (Ladder Level) | Mitigation |
|------|-------------|----------------------|------------|
| ... | ... | ... | ... |

## Trade-off Matrix
| Criterion | Option A | Option B |
|-----------|----------|----------|
| SAFETY | ... | ... |
| CORRECTNESS | ... | ... |
| SECURITY | ... | ... |
| RELIABILITY | ... | ... |
| SIMPLICITY | ... | ... |
| COST | ... | ... |
| ELEGANCE | ... | ... |

## Failure Modes
| Mode | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| ... | ... | ... | ... |

## Priority Conflicts Resolved
| Conflict | Resolution | Ladder Levels |
|----------|-----------|---------------|
| ... | ... | ... |

## Recommended Implementation
[Step-by-step approach, suitable for tech-spec input]

## Open Questions
[Questions requiring user input before proceeding]
```

---

## Anti-Patterns

- Running panel for trivial tasks (1-2 files, simple change) — waste of resources
- Always using all 10 roles — cap at 5, match to domain
- Skipping Priority Ladder for conflicts — leads to opinion-based decisions
- Panel experts modifying code — they are READ-ONLY analysts
- Ignoring open questions and proceeding to implementation
