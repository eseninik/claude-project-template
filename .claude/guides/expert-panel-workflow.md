# Expert Panel Workflow

> Step-by-step orchestration guide for the lead agent running an Expert Panel.

---

## Prerequisites

Before starting, load:
- `cat .claude/skills/expert-panel/SKILL.md` — role pool, domain detection, output template
- `cat .claude/guides/priority-ladder.md` — conflict resolution framework
- `cat .claude/guides/teammate-prompt-template.md` — prompt structure

---

## When NOT to Run Panel

Skip expert panel and use direct implementation when:
- Task touches 1-2 files with obvious changes
- User says "без панели" / "простая задача" / "just do it"
- Task is a bug fix with clear root cause
- Task is documentation-only

In these cases, fall through to existing AGENT TEAM PROPOSAL or sequential execution.

---

## Full Workflow

### Phase 0: Domain Detection (lead, no team)

```
1. Read task description
2. Run Domain Detection Algorithm (from SKILL.md):
   - Parse keywords → domains
   - Always: Business Analyst + System Architect
   - Add QA Strategist if implementation expected
   - Add 1-3 domain-specific roles
   - Cap at 5
3. Present to user:
   "Запускаю Expert Panel: [N] экспертов
    - [Role 1]: [focus]
    - [Role 2]: [focus]
    - ...
    Продолжить?"
4. Wait for user confirmation
5. TeamCreate "expert-panel"
```

### Phase 1: Expert Panel (TeamCreate, real agents)

#### Step 1: Create Team
```
TeamCreate:
  team_name: "expert-panel"
  description: "Expert analysis for: [task summary]"
```

#### Step 2: Create Tasks (one per expert)
```
TaskCreate for each expert:
  subject: "[Role] analysis of [task]"
  description: "Analyze from [domain] perspective..."
```

#### Step 3: Spawn Expert Teammates

Use this prompt template for each expert (extends teammate-prompt-template.md):

```
You are a teammate on team "expert-panel". Your name is "{role-name}".

## Required Skills
Before starting work, load and follow these skills:
- {skill-1}: `cat .claude/skills/{skill-1}/SKILL.md`
- {skill-2}: `cat .claude/skills/{skill-2}/SKILL.md`

Also load the Priority Ladder:
- priority-ladder: `cat .claude/guides/priority-ladder.md`

## Your Role
You are the {Role Name} on an expert panel analyzing: {task description}

## Your Focus
Analyze this task ONLY from the {domain} perspective:
- {focus area 1}
- {focus area 2}
- {focus area 3}

## Project Context
Read these before analysis:
- `cat .claude/skills/project-knowledge/guides/architecture.md`
- `cat .claude/skills/project-knowledge/guides/patterns.md`

## Output Format
Send your analysis to the team lead via SendMessage with:
1. Key findings (2-5 bullet points)
2. Risks from your perspective (with Priority Ladder level)
3. Recommendations (with priority justification)
4. Open questions (if any)

## Constraints
- READ-ONLY: Do NOT modify any files
- Focus on YOUR domain only — other experts cover other areas
- Use Priority Ladder levels when assessing risks
- Be specific and actionable, not generic
```

#### Step 4: Collect Analyses

Wait for all experts to send their analyses via SendMessage.

#### Step 5: Resolve Conflicts

```
For each pair of conflicting recommendations:
1. Identify the Priority Ladder level of each
2. Higher level wins (SAFETY > CORRECTNESS > SECURITY > ...)
3. Document the resolution
```

#### Step 6: Write Expert Analysis

Write `work/expert-analysis.md` using the output template from SKILL.md.

#### Step 7: Shutdown Panel Team

```
SendMessage type: "shutdown_request" to each expert
TeamDelete after all experts shut down
```

### Phase 2: Transition (lead, no team)

```
1. Present expert-analysis.md summary to user
2. Highlight open questions — get answers
3. Highlight priority conflicts — confirm resolutions
4. User approval to proceed
5. IF complex implementation:
   → Generate tech-spec via tech-spec-planning skill
   → Generate tasks/*.md for wave execution
6. IF simple implementation:
   → Proceed directly with implementation plan from expert-analysis.md
```

### Phase 3: Implementation (existing pipeline)

```
1. Load plan-execution-protocol: `cat .claude/guides/plan-execution-enforcer.md`
2. Run wave analysis on tasks
3. Execute via:
   - subagent-driven-development (independent tasks)
   - executing-plans (tasks needing human review)
   - TeamCreate (3+ non-trivial parallel tasks)
4. Standard verification-before-completion flow
```

---

## Role-Specific Focus Areas

| Role | Focus Questions |
|------|----------------|
| **Business Analyst** | Who benefits? What's the user flow? What are edge cases? |
| **System Architect** | How does it fit existing architecture? What patterns to use? Dependencies? |
| **Security Analyst** | What attack vectors? Data exposure? Auth implications? |
| **QA Strategist** | What tests are needed? What can break? How to verify? |
| **Performance Engineer** | Bottlenecks? Scaling concerns? Resource usage? |
| **API Designer** | Endpoint design? Backward compatibility? Error handling? |
| **Data Architect** | Schema changes? Migration path? Data integrity? |
| **Async Specialist** | Race conditions? Error propagation? Cleanup? |
| **Researcher** | What's unknown? What docs to read? What precedents exist? |
| **Risk Assessor** | What's the worst case? Rollback plan? Blast radius? |

---

## Examples

### Example: "Add OAuth2 login"

**Domain Detection:** SECURITY, API
**Panel (4):** Business Analyst, System Architect, Security Analyst, API Designer

- BA: User flow analysis, social login providers, error states
- Architect: Token storage, session management, middleware integration
- Security: OAuth2 grant types, token rotation, PKCE, redirect validation
- API Designer: Authorization endpoints, callback handling, error responses

### Example: "Migrate database to PostgreSQL"

**Domain Detection:** DATA, RISK
**Panel (4):** Business Analyst, System Architect, Data Architect, Risk Assessor

- BA: Feature impact, downtime requirements, data validation
- Architect: ORM changes, connection pooling, migration strategy
- Data: Schema mapping, data type conversion, index strategy
- Risk: Rollback plan, data loss scenarios, performance regression

### Example: "Simple new bot command"

**Skip panel** — trivial task, 1-2 files. Use direct implementation.
