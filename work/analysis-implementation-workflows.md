# Comprehensive Analysis: Implementation Guides and Development Workflows

**Analysis Date**: 2026-03-17
**Analyzed By**: Research Agent
**Task**: Extract implementation patterns, agent definitions, command workflows, and orchestration approaches

---

## EXECUTIVE SUMMARY

Analyzed 9 critical documents from claude-code-best-practice repository:

### Implementation Guides (5 files)
1. Agent Teams Implementation
2. Commands Implementation
3. Skills Implementation
4. Sub-agents Implementation
5. Scheduled Tasks Implementation

### Development Workflows (4+ files)
1. RPI (Research-Plan-Implement) Workflow
2. RPI Agents (7 specialized agent definitions)
3. RPI Commands (3 command templates)
4. Cross-Model Workflow (Claude Code + Codex CLI)

**Key Finding**: Three complementary orchestration patterns emerge:
- **Command → Agent → Skill** (internal workflows, single model)
- **RPI Workflow** (feature development, multi-agent, multi-phase)
- **Cross-Model Workflow** (AI-assisted with human-in-the-loop feedback)

---

## PART 1: IMPLEMENTATION PATTERNS

### 1.1 Agent Teams Implementation

#### Pattern Overview
**Agent Teams** spawn **multiple independent Claude Code sessions** that coordinate via a **shared task list**. Unlike subagents (isolated context forks within one session), each teammate gets its own:
- Full context window
- CLAUDE.md loaded
- MCP servers available
- Skills preloaded
- tmux session for split-pane coordination

#### Architecture
```
┌──────────────────────────────────────────────────────────────┐
│                         LEAD (You)                           │
│       "Create an agent team to build X"                      │
└──────────────────────────┬───────────────────────────────────┘
                           │ spawns team (all parallel)
              ┌────────────┼────────────┐
              ▼            ▼            ▼
   ┌────────────────┐ ┌──────────┐ ┌──────────────┐
   │ Specialist 1   │ │Specialist2 │ │ Specialist 3 │
   │ (Independent   │ │(Independent│ │(Independent  │
   │  Claude Code   │ │Claude Code │ │Claude Code   │
   │  session)      │ │session)    │ │session)      │
   └───────┬────────┘ └────┬─────┘ └──────┬───────┘
           │               │              │
           ▼               ▼              ▼
   ┌──────────────────────────────────────────────────┐
   │            Shared Task List                      │
   │  ☐ Task 1                                        │
   │  ☐ Task 2                                        │
   │  ☐ Task 3                                        │
   └──────────────────────────────────────────────────┘
```

#### Time Orchestration Example
Real example from repo: team built complete time orchestrator workflow

**Team Structure**:
- **Command Architect**: Creates `.claude/commands/time-orchestrator.md`
- **Agent Engineer**: Creates `.claude/agents/time-agent.md` with preloaded skill
- **Skill Designer**: Creates `.claude/skills/time-svg-creator/SKILL.md`

**Data Contract** (critical for coordination):
```json
{
  "time": 14.5,
  "timezone": "GST",
  "formatted": "2:30 PM"
}
```

#### Implementation Steps
```bash
1. Install iTerm2 + tmux
   brew install --cask iterm2
   brew install tmux

2. Start tmux
   tmux new -s dev

3. Start Claude with team support
   CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude

4. Paste team bootstrap prompt (agent-teams-prompt.md)
   → Auto-spawns all team members
```

#### Key Rules for Agent Teams
- **Data contract FIRST**: Before anyone codes, agree on data format
- **Parallel execution**: All teammates work simultaneously, not sequentially
- **Shared task list**: Single source of truth (copy/paste from shared doc)
- **tmux session**: Each teammate in separate pane, visible on screen
- **Explicit dependencies**: "Task 2 depends on Task 1's output"

**Critical Gotcha**: Teammates must know about each other's work → explicit coordination via shared task list

---

### 1.2 Commands Implementation

#### Pattern Overview
**Commands** are the **entry point** of the Command → Agent → Skill orchestration pattern.

**File Format**: `.claude/commands/{name}.md` with YAML frontmatter + markdown body

#### Command Structure
```yaml
---
description: Fetch weather data for Dubai and create an SVG weather card
model: haiku
---

# Weather Orchestrator Command

[Markdown instructions]
```

#### Weather Orchestrator Example

**Purpose**: Entry point that orchestrates entire workflow

**Workflow** (3 steps):
```
Step 1: Ask User Preference
├─ Tool: AskUserQuestion
└─ Output: temperature unit (Celsius/Fahrenheit)

Step 2: Fetch Weather Data
├─ Tool: Agent (subagent_type: "weather-agent")
├─ Input: temperature unit
└─ Output: {temperature: 35, unit: "celsius"}

Step 3: Create SVG Weather Card
├─ Tool: Skill (skill: "weather-svg-creator")
├─ Input: temperature from context
└─ Output: orchestration-workflow/weather.svg
```

#### Key Command Patterns
1. **Collect user input** via AskUserQuestion
2. **Delegate data fetching** to Agent (which has preloaded skill)
3. **Invoke skill** for output creation (reads data from context, not re-fetch)

#### Command Implementation Rules
- **Commands are orchestrators**, not implementers
- **Never duplicate work**: If Agent fetches data, Skill reads from context
- **User interaction layer**: Commands handle UI/UX, not business logic
- **Explicit handoff**: Commands must tell agents/skills what data they're using

---

### 1.3 Skills Implementation

#### Pattern Overview
**Two distinct skill patterns**:

| Pattern | Invocation | Pre-loaded? | Example |
|---------|-----------|-----------|---------|
| **Agent Skill** | Preloaded via `skills:` frontmatter | YES | `weather-fetcher` |
| **Standalone Skill** | Invoked via `Skill()` tool | NO | `weather-svg-creator` |

#### File Format
```yaml
---
name: weather-fetcher
description: Instructions for fetching weather data from Open-Meteo
user-invocable: false  # ← Agent skills hide from /menu
---

# Weather Fetcher Skill

Instructions for fetching...
```

#### Agent Skill Pattern (Preloaded)
**Purpose**: Inject domain knowledge into agent's context at startup

**Example**: `weather-fetcher` skill in agent's frontmatter
```yaml
skills:
  - weather-fetcher  # ← Loaded into agent context automatically
```

**When to use**:
- Domain knowledge needed by agent
- Step-by-step instructions for complex tasks
- Reusable procedures that agents invoke implicitly

**Implementation Note**:
- Set `user-invocable: false` (hide from menu)
- Not invoked directly; serves as context injection
- Agent "reads" skill as part of startup context

#### Standalone Skill Pattern (Direct Invocation)
**Purpose**: Self-contained task that can be invoked directly

**Example**: `weather-svg-creator` called from command
```
Use the Skill tool to invoke the weather-svg-creator skill:
  skill: weather-svg-creator
```

**When to use**:
- Independent tasks that don't need prior context
- Reusable utilities (formatting, rendering, etc.)
- Skills that have clear input/output contracts

**Implementation Note**:
- Leave `user-invocable: true` (default, shows in menu)
- Must be self-contained (can run standalone)
- Reads input from conversation context (previous agent's output)

#### Skill Structure Best Practices
```markdown
---
name: skill-name
description: [What] + Use when [triggers] + Do NOT use for [negatives]
user-invocable: false/true
---

# Skill Name

## Task
[Clear description of what skill does]

## Instructions
[Step-by-step instructions]

## Expected Input
[Format of data skill receives]

## Expected Output
[Format of data skill returns]
```

---

### 1.4 Sub-agents Implementation

#### Pattern Overview
**Sub-agents** are **isolated context forks within a single Claude Code session**. Different from Agent Teams (which are independent sessions).

**Sub-agents are invoked via the Agent tool**:
```
Use the Agent tool to invoke the weather-agent:
  subagent_type: weather-agent
  prompt: "Fetch temperature for Dubai in Celsius"
```

#### Agent Definition Structure
```yaml
---
name: weather-agent
description: Use this agent PROACTIVELY when you need to fetch weather data
tools: WebFetch, Read, Write, Edit
model: sonnet
color: green
maxTurns: 5
permissionMode: acceptEdits
memory: project
skills:
  - weather-fetcher
---

# Weather Agent

Instructions for agent...
```

#### Key Frontmatter Fields
| Field | Purpose | Example |
|-------|---------|---------|
| `name` | Agent identifier | `weather-agent` |
| `description` | When to use (trigger condition) | "Use PROACTIVELY when..." |
| `tools` | Tools available to agent | `WebFetch, Read, Write` |
| `model` | Which Claude model | `sonnet`, `opus`, `haiku` |
| `color` | Terminal UI color | `green`, `blue`, `red` |
| `maxTurns` | Conversation limit | `5`, `10`, `20` |
| `permissionMode` | Auto-approval level | `acceptAll`, `acceptEdits` |
| `memory` | Memory scope | `project`, `session`, `none` |
| `skills` | Preloaded skills | `- weather-fetcher` |

#### Weather Agent Example
**Role**: Fetch weather data with preloaded `weather-fetcher` skill

**Responsibilities**:
1. Follow weather-fetcher instructions
2. Fetch from Open-Meteo API
3. Return temperature value + unit
4. Update memory with reading details

**Output Format**:
```
Temperature: 35°C
Unit: celsius
Timestamp: 2024-03-17T14:30:00Z
```

#### Sub-agent Invocation Pattern
```
1. Caller (command or main agent) uses Agent tool
2. Sub-agent receives prompt + preloaded skills
3. Sub-agent executes task in isolated context
4. Sub-agent returns result to caller
5. Caller uses result in next step
```

---

### 1.5 Scheduled Tasks Implementation

#### Pattern Overview
**Scheduled tasks** use CronCreate/CronList/CronDelete tools to manage recurring workflows.

#### Loop Skill Example
```bash
/loop 1m "tell current time"
```

**Behavior**:
- Parses interval: `1m` → `*/1 * * * *` (every minute)
- Creates cron job
- Fires every minute, runs command
- Auto-expires after 3 days
- Session-scoped (stops when Claude exits)

#### Implementation Details
- **Minimum granularity**: 1 minute (cron limit)
- **Session scope**: Lives only in current session memory
- **Auto-expiry**: 3 days maximum lifetime
- **Cancellation**: `cron cancel <job-id>`

#### Use Cases
```bash
/loop 1m "check deploy status"
/loop 5m /simplify
/loop 10m "run tests"
```

#### Cron Tools API
- `CronCreate(cron: "*/5 * * * *", prompt: "...", recurring: true/false)`
- `CronList()` - show all active jobs
- `CronDelete(id: "job-id")` - cancel job

---

## PART 2: DEVELOPMENT WORKFLOWS

### 2.1 RPI Workflow (Research-Plan-Implement)

#### Overview
**RPI** = **R**esearch → **P**lan → **I**mplement

A **systematic development workflow** with **validation gates** at each phase. Prevents wasted effort on non-viable features and ensures comprehensive documentation.

#### Feature Folder Structure
```
rpi/{feature-slug}/
├── REQUEST.md                    # Step 1: Initial description
├── research/
│   └── RESEARCH.md              # Step 2: GO/NO-GO analysis
├── plan/
│   ├── PLAN.md                  # Step 3: Implementation roadmap
│   ├── pm.md                    # Product requirements
│   ├── ux.md                    # UX design
│   └── eng.md                   # Technical specification
└── implement/
    └── IMPLEMENT.md             # Step 4: Implementation record
```

#### RPI Workflow Steps

**Step 1: Describe Feature**
```
User: "Add OAuth2 authentication with Google and GitHub"

Process:
1. Create feature folder: rpi/oauth2-authentication/
2. Create REQUEST.md with feature description
3. Move to Step 2: Research

Output: rpi/oauth2-authentication/REQUEST.md
```

**Step 2: Research (GO/NO-GO Gate)**
```bash
/rpi:research rpi/oauth2-authentication/REQUEST.md
```

**Phases**:
1. **Parse Feature Request** → requirement-parser agent extracts structured requirements
2. **Product Analysis** → product-manager agent assesses user value + market fit
3. **Technical Discovery** → Explore agent deeply analyzes codebase
4. **Technical Feasibility** → senior-software-engineer assesses buildability
5. **Strategic Assessment** → technical-cto-advisor aligns with org standards
6. **Generate Report** → documentation-analyst-writer produces RESEARCH.md

**Output**: `research/RESEARCH.md` with verdict:
- **GO**: Proceed to planning
- **NO-GO**: Stop, not worth building
- **CONDITIONAL**: Go with caveats

**Step 3: Plan (Multi-Spec Gate)**
```bash
/rpi:plan oauth2-authentication
```

**Produces** (for different stakeholders):
- `plan/PLAN.md` - 3 phases, 15 tasks
- `plan/pm.md` - User stories + acceptance criteria
- `plan/ux.md` - Login UI flows
- `plan/eng.md` - Technical architecture

**Step 4: Implement (Phase Gates)**
```bash
/rpi:implement oauth2-authentication [--phase N]
```

**Phase Loop** (for each phase):
```
┌─────────────────────────────┐
│ Phase N: [Name]             │
├─────────────────────────────┤
│                             │
│ 1. Code Discovery           │
│    └─ Explore agent         │
│                             │
│ 2. Implementation           │
│    └─ senior-software-eng   │
│                             │
│ 3. Self-Validation          │
│    └─ Engineer checks list  │
│                             │
│ 4. Code Review              │
│    └─ code-reviewer agent   │
│                             │
│ 5. Validation Gate          │
│    └─ User approves (PASS/FAIL) │
│                             │
│ 6. Documentation Update     │
│    └─ Update PLAN.md        │
│                             │
└─────────────────────────────┘
```

---

### 2.2 RPI Agents (7 Specialized Roles)

#### Agent 1: Requirement Parser
**Role**: Extract structured requirements from feature descriptions

**Responsibilities**:
- Parse unstructured feature descriptions
- Extract explicit + implicit requirements
- Identify goals, constraints, success criteria
- Categorize feature type + complexity
- Clarify ambiguities + flag assumptions
- Search codebase for similar features

**Output Format**:
```markdown
## Feature Parsing Results

### Feature Overview
- Feature Name: [name]
- Feature Type: [UI | API | Infrastructure | Enhancement]
- Target Component: [component name]
- Complexity Estimate: [Simple | Medium | Complex]

### Goals and Objectives
1. [Primary goal]
2. [Secondary goal]

### Functional Requirements
**Must Have**:
- [Requirement 1]
- [Requirement 2]

**Nice to Have**:
- [Requirement 3]

### Non-Functional Requirements
- Performance: [requirements]
- Security: [requirements]
- Scalability: [requirements]
- Compatibility: [requirements]

### Constraints
- [Technical constraints]
- [Timeline constraints]
- [Resource constraints]

### User Impact
- Primary Users: [who]
- User Benefit: [how they benefit]
- UX Impact: [expected changes]

### Assumptions
1. [Assumption - needs validation]

### Clarifying Questions
1. [Question 1]
2. [Question 2]

### Complexity Factors
- [Factor 1]
- [Factor 2]

### Related Context
- Similar Features: [found patterns]
- Existing Patterns: [reusable code]
- Documentation: [relevant docs]

### Recommendation
[Proceed | Need clarification | Suggest alternative]
```

**Tools Available**: Read, Grep, Glob, WebFetch

**Success Metric**: All downstream agents have info they need, no critical gaps remain

---

#### Agent 2: Product Manager
**Role**: Assess user value + market fit + strategic alignment

**Responsibilities**:
- Analyze user value and impact
- Evaluate market fit + product vision alignment
- Check constitutional alignment (project principles)
- Assess constraints compliance
- Provide product viability score
- Identify product red flags

**Output**:
- Product viability score (High/Medium/Low)
- User value assessment
- Strategic alignment evaluation
- Constitutional alignment summary
- Priority recommendation
- Product concerns/red flags

**Note**: Brief role definition in repo (557 bytes), likely auto-generated prompts used

---

#### Agent 3: Senior Software Engineer
**Role**: Pragmatic implementer who plans sanely + ships small reversible slices

**Operating Principles**:
- Adopt > Adapt > Invent (use existing patterns first)
- Keep changes reversible + observable
- Milestones, not timelines
- Feature flags/kill-switches when possible

**Concise Working Loop**:
1. Clarify ask + acceptance criteria
2. Quick "does this already exist?" check
3. Plan briefly (milestones; any new deps with rationale)
4. TDD-first, small commits; keep boundaries clean
5. Verify (unit + targeted e2e); add metrics/logs if warranted
6. Deliver PR with rationale, trade-offs, rollout/rollback notes

**Model**: Opus (for complexity)
**Responsibilities in RPI**:
- Phase 2.5: Technical discovery + feasibility assessment (code exploration)
- Phase 3: Design architecture + specify implementation approach
- Phase 4+: Actual implementation with reversibility

---

#### Agent 4: Technical CTO Advisor
**Role**: Align technological decisions with org standards + venture success metrics

**Critical Distinction**: Platform vs Products
- **Platform** (internal): Can use complex orchestration
- **Products** (user-facing): Match complexity to actual requirements

**Key Responsibilities**:
- Strategic technical decision-making
- Risk assessment across 5 categories:
  - **Technical** (scalability, performance, security, maintainability, integration)
  - **Business** (market, competitive, financial, operational, strategic)
- Alignment with engineering standards + AI-first principles
- Integration with organizational knowledge

**Decision-Making Process**:
1. Context Analysis
2. Technical Evaluation
3. Business Alignment Assessment
4. Risk-Investment Correlation
5. Strategic Recommendation

**Success Metrics**:
- Technical justification provided
- Risk assessment comprehensive
- Business alignment clear
- Implementation plan specific
- Success metrics defined
- Monitoring strategy documented

**Model**: Opus (for deep strategic thinking)

---

#### Agent 5: UX Designer
**Role**: Design user experience + interaction flows

**Output**: UX mockups, flow diagrams, interaction patterns for feature

**Note**: Brief role definition (469 bytes), likely generates focused prompts

---

#### Agent 6: Documentation Analyst Writer
**Role**: Generate comprehensive documentation for all phases

**Responsibilities**:
- Synthesize findings from all agents
- Create clear, structured reports
- Generate phase-specific documentation
- Ensure completeness + clarity
- Make knowledge actionable for next phase

**Outputs**:
- Research report (RESEARCH.md)
- Planning documentation (pm.md, ux.md, eng.md, PLAN.md)
- Implementation documentation (IMPLEMENT.md)

---

#### Agent 7: Code Reviewer
**Role**: Validate code against quality + security standards

**Responsibilities** (implied):
- Security review
- Correctness verification
- Maintainability assessment
- Code style compliance
- Testing coverage validation

**Note**: Brief definition (727 bytes), implies comprehensive review checklist

---

### 2.3 RPI Command Structure

#### Command 1: `/rpi:research`

**Purpose**: Research + GO/NO-GO decision gate

**Input**: Feature slug (e.g., `rpi/oauth2-authentication/REQUEST.md`)

**Phases**:
1. **Load Context** → Read REQUEST.md + project constitution
2. **Parse Feature** → requirement-parser agent
3. **Product Analysis** → product-manager agent
4. **Technical Discovery** → Explore agent (code exploration - CRITICAL)
5. **Technical Feasibility** → senior-software-engineer
6. **Strategic Assessment** → technical-cto-advisor
7. **Generate Report** → documentation-analyst-writer

**Output**: `research/RESEARCH.md` with:
- Product analysis
- Technical feasibility assessment
- Risk summary
- **GO/NO-GO recommendation** (validation gate)

**Validation Gate**:
- GO → Proceed to planning
- NO-GO → Stop
- CONDITIONAL → Go with caveats

---

#### Command 2: `/rpi:plan`

**Purpose**: Create comprehensive planning documentation

**Input**: Feature slug (e.g., `oauth2-authentication`)

**Prerequisites**: `research/RESEARCH.md` exists with GO recommendation

**Phases**:
1. **Load Context** → Read research report + constitution
2. **Understand Requirements** → Parse feature scope
3. **Analyze Technical Requirements** → Review architecture
4. **Design Architecture** → High-level design
5. **Break Down Implementation** → Create phased tasks
6. **Generate Documentation** → Multiple docs for different roles
7. **Validate Output** → Quality gates

**Output Files**:
```
plan/
├── PLAN.md           # 3 phases, 15 tasks, checklist
├── pm.md             # Product requirements + user stories
├── ux.md             # UX flows + wireframes
└── eng.md            # Technical specification + architecture
```

**Key Principle**: "Create planning documentation for different stakeholders"
- PM reads pm.md
- Designer reads ux.md
- Engineer reads eng.md + PLAN.md

---

#### Command 3: `/rpi:implement`

**Purpose**: Execute phased implementation with validation gates

**Input**: Feature slug + optional phase number

**Flags**:
```bash
/rpi:implement oauth2-authentication           # Start from phase 1
/rpi:implement oauth2-authentication --phase 2 # Start from phase 2
/rpi:implement oauth2-authentication --validate-only # Validate only
/rpi:implement oauth2-authentication --skip-validation # Skip gate (caution)
```

**Prerequisites**: `plan/PLAN.md` exists

**Phase Loop** (for each phase):
```
1. Code Discovery
   └─ Explore agent analyzes files affected by phase

2. Implementation
   └─ senior-software-engineer agent executes tasks

3. Self-Validation
   └─ Engineer validates against phase checklist

4. Code Review
   └─ code-reviewer agent validates code quality

5. Validation Gate
   └─ STOP and request user approval
      ├─ PASS: Continue to next phase
      ├─ CONDITIONAL: Note issues, continue
      └─ FAIL: Fix and re-validate

6. Documentation Update
   └─ Update phase status in PLAN.md

7. Optional: Constitutional Validation
   └─ constitutional-validator agent (if constitution exists)
```

**Output**: `implement/IMPLEMENT.md` tracking:
- Phase completion status
- Issues found + resolved
- Code review findings
- Validation gate results

---

### 2.4 Cross-Model Workflow (Claude Code + Codex CLI)

#### Overview
**Orchestrates AI-assisted development with human feedback at critical gates**

**Models Used**:
- **Claude Code** (Opus 4.6) - Planning + Implementation
- **Codex CLI** (GPT-5.4) - QA review + Verification

#### Four-Step Workflow

**STEP 1: PLAN**
```
Terminal 1: Claude Code (Opus 4.6, Plan Mode)
├─ Claude interviews via AskUserQuestion
├─ Asks about requirements, constraints, tech choices
├─ Produces phased plan with test gates
└─ Output: plans/{feature-name}.md
```

**STEP 2: QA REVIEW (Codex)**
```
Terminal 2: Codex CLI (GPT-5.4)
├─ Codex reviews plan against ACTUAL codebase
├─ Inserts intermediate phases ("Phase 2.5")
├─ Marks with "Codex Finding" headings
├─ ADDS to plan, never rewrites existing phases
└─ Output: plans/{feature-name}.md (UPDATED)
```

**STEP 3: IMPLEMENT**
```
Terminal 1: Claude Code (NEW session, Opus 4.6)
├─ Claude implements phase-by-phase
├─ Executes with test gates at each phase
├─ Uses Codex findings from Phase 2
└─ Output: Feature code + tests
```

**STEP 4: VERIFY**
```
Terminal 2: Codex CLI (NEW session, GPT-5.4)
├─ Codex verifies implementation against plan
├─ Checks each phase completion
├─ Validates test gates passed
└─ Output: Verification report
```

#### Key Principles
1. **Sequential Model Handoff**: Plan (Claude) → Review (Codex) → Implement (Claude) → Verify (Codex)
2. **Humans in the Loop**: Critical gates pause for human feedback between steps
3. **Plan Augmentation**: Codex ADDS findings, doesn't rewrite Claude's work
4. **Test Gates**: Each phase has explicit test requirements
5. **Separate Sessions**: Each tool gets fresh session (no context bleed)

#### Comparison: RPI vs Cross-Model
| Aspect | RPI | Cross-Model |
|--------|-----|-------------|
| **Planning** | Multi-agent (requirement-parser, PM, engineer, CTO) | Single model (Claude, plan mode) |
| **QA Gate** | Built into command workflow | External (Codex CLI) |
| **Implementation** | Single multi-phase command | New Claude session |
| **Verification** | Built into phase validation gates | External Codex verification |
| **Human Feedback** | Per-phase approval gates | After Planning, after Verify |

---

## PART 3: ORCHESTRATION PATTERNS

### 3.1 Command → Agent → Skill Pattern

#### Data Flow
```
User Input
    ↓
┌─────────────────────────────────────────┐
│ COMMAND (Entry Point)                   │
│ - Collects user preferences              │
│ - Asks clarifying questions              │
│ - Delegates to agent                     │
└──────────────┬──────────────────────────┘
               ↓ (uses Agent tool)
┌─────────────────────────────────────────┐
│ AGENT (Data Fetcher)                    │
│ - Has preloaded skill                    │
│ - Fetches/processes data                 │
│ - Returns result to command              │
└──────────────┬──────────────────────────┘
               ↓ (returns data)
┌─────────────────────────────────────────┐
│ COMMAND (Data Processor)                 │
│ - Receives agent's data                  │
│ - Passes to skill for rendering          │
└──────────────┬──────────────────────────┘
               ↓ (uses Skill tool)
┌─────────────────────────────────────────┐
│ SKILL (Output Creator)                  │
│ - Reads data from context                │
│ - Creates output (SVG, file, etc.)       │
│ - Writes to disk                         │
└─────────────────────────────────────────┘
```

#### Weather Example: Concrete Implementation
```
1. User runs: /weather-orchestrator
   ↓
2. Command asks: "Celsius or Fahrenheit?"
   ↓
3. User inputs: "Celsius"
   ↓
4. Command invokes agent:
   Agent tool(subagent_type: "weather-agent", prompt: "Fetch temp in Celsius")
   ↓
5. Agent uses weather-fetcher skill to fetch from Open-Meteo API
   Returns: {temperature: 35, unit: "celsius"}
   ↓
6. Command invokes skill with result in context:
   Skill tool(skill: "weather-svg-creator")
   ↓
7. Skill reads temperature from context
   Creates SVG card
   Writes to: orchestration-workflow/weather.svg
   ↓
8. Output: Beautiful SVG weather card displayed
```

#### Key Rule: No Redundant Work
- **Agent fetches**: Data lives in context
- **Skill invoked**: Skill reads from context, doesn't re-fetch
- **Prevents**: Duplicate API calls, network waste, latency

### 3.2 Parallel Agent Coordination (Agent Teams)

#### Data Contract (Critical)
All agents must agree on:
```json
{
  "feature": "time-orchestration",
  "components": {
    "command": "time-orchestrator.md",
    "agent": "time-agent.md",
    "skill": "time-svg-creator"
  },
  "data_format": {
    "time": "number (float hours)",
    "timezone": "string (city or code)",
    "formatted": "string (human-readable)"
  }
}
```

#### Task Coordination
```
Shared Task List (copy/paste friendly):

☐ Task 1: Command Architect
  - Create .claude/commands/time-orchestrator.md
  - Responsible for: asking user, sequencing workflow
  - Depends on: none
  - Outputs: command file
  - Input from Agent: temperature + timezone

☐ Task 2: Agent Engineer
  - Create .claude/agents/time-agent.md with weather-fetcher skill
  - Responsible for: fetching real-time data
  - Depends on: none
  - Outputs: agent file, returns data via context
  - Input to Skill: temperature, timezone, formatted

☐ Task 3: Skill Designer
  - Create .claude/skills/time-svg-creator/SKILL.md
  - Responsible for: rendering SVG output
  - Depends on: Task 2 (agent must provide data)
  - Outputs: SVG file
  - Input from Command: temperature, timezone, formatted
```

---

## PART 4: KEY INSIGHTS & PATTERNS

### 4.1 Skill Design Patterns

#### Pattern 1: Agent Skills (Preloaded Context)
**When to use**:
- Procedural knowledge needed by agent
- Step-by-step instructions for complex tasks
- Domain expertise that guides agent behavior

**Example**: weather-fetcher → preloaded into weather-agent
- Provides step-by-step instructions for fetching
- Tells agent which API to use + how to format request
- Agent reads skill, follows instructions, returns result

**Implementation**:
```yaml
skills:
  - weather-fetcher  # Loaded automatically at startup
```

**Key Rule**: Set `user-invocable: false` (hide from menu)

---

#### Pattern 2: Standalone Skills (Direct Invocation)
**When to use**:
- Self-contained tasks with clear input/output
- Reusable utilities (formatting, rendering, validation)
- Skills that work independently

**Example**: weather-svg-creator → invoked directly from command
- Receives data from context (no re-fetch)
- Transforms + renders
- Writes output to disk

**Implementation**:
```
Skill tool(skill: "weather-svg-creator")
```

**Key Rule**: Leave `user-invocable: true` (show in menu)

---

### 4.2 Agent Definition Best Practices

#### Description Field (Critical)
**Pattern**: `[What] + Use when [triggers] + Do NOT use for [negatives]`

```yaml
description: |
  Use this agent PROACTIVELY when you need to fetch weather data
  for Dubai, UAE. This agent fetches real-time temperature from
  Open-Meteo using its preloaded weather-fetcher skill.
  DO NOT use for historical data or long-range forecasts.
```

**Why This Matters**:
- Agent is invoked when condition matches
- Claude reads description to decide when to use agent
- Explicit "do NOT use" prevents misuse

---

#### Model Selection
| Task | Model | Reasoning |
|------|-------|-----------|
| Complex research/planning | opus | Full reasoning, multi-step analysis |
| Coding tasks | sonnet | Balance speed + quality for implementation |
| Simple transformations | haiku | Speed + low cost for routine tasks |

---

### 4.3 RPI Workflow Validation Gates

#### Gate 1: Research GO/NO-GO
**Decision Point**: After Phase 2 (Multi-agent analysis)

**Criteria**:
- Is this aligned with product vision?
- Is this technically feasible?
- Are we taking on acceptable risk?
- Do we have a clear implementation approach?

**Verdict Options**:
- **GO**: Proceed to planning immediately
- **NO-GO**: Stop feature, not worth building
- **CONDITIONAL**: Go with caveats + mitigation strategies

**Who Decides**: Human + AI recommendation (CTO advisor)

#### Gate 2: Per-Phase Validation (Implementation)
**Decision Point**: After Code Review phase

**Criteria**:
- Does code pass linting + tests?
- Are edge cases handled?
- Is documentation updated?
- Are no security issues introduced?
- Is phase objective fully met?

**Verdict Options**:
- **PASS**: Phase complete, proceed to next
- **CONDITIONAL PASS**: Issues noted but acceptable, proceed
- **FAIL**: Fix issues, re-validate

**Who Decides**: Human (approves after code-reviewer agent report)

---

### 4.4 Multi-Phase Implementation Pattern

#### Phase Structure (Generic)
```markdown
## Phase N: [Phase Name]

### Overview
[1-2 sentence description of what this phase delivers]

### Tasks
1. [Task 1]
   - Prerequisites: [What must be done before this]
   - Acceptance: [How to verify completion]
2. [Task 2]
   - ...

### Validation Checklist
- [ ] All tasks completed
- [ ] Tests passing
- [ ] No breaking changes
- [ ] Documentation updated
- [ ] Code reviewed

### Success Criteria
[Specific measurable criteria]
```

#### Example: OAuth2 Authentication Implementation

```
Phase 1: Backend Foundation
├─ Task 1.1: Create OAuth provider config
├─ Task 1.2: Implement Google OAuth flow
├─ Task 1.3: Implement GitHub OAuth flow
└─ Validation Gate: Google + GitHub login working

Phase 2: Frontend Integration
├─ Task 2.1: Create login UI component
├─ Task 2.2: Integrate auth flow
├─ Task 2.3: Store + manage session tokens
└─ Validation Gate: End-to-end login works

Phase 3: Testing & Polish
├─ Task 3.1: Write integration tests
├─ Task 3.2: Add error handling
├─ Task 3.3: Document oauth flow
└─ Validation Gate: 100% test coverage, no bugs
```

---

### 4.5 Cross-Model Handoff Pattern

#### Terminal 1 → Terminal 2 Handoff (Planning)
```
Terminal 1: Claude Code
├─ Produces: plans/{feature}.md with full plan
├─ Format: Structured markdown with phases + tasks
└─ Hands off to Terminal 2

Terminal 2: Codex CLI
├─ Reads: plans/{feature}.md
├─ Analyzes: Against actual codebase
├─ Adds: "Codex Finding" intermediate phases
├─ Preserves: Original Claude phases (never rewrites)
└─ Updates: plans/{feature}.md with additions
```

#### Terminal 2 → Terminal 1 Handoff (Implementation)
```
Terminal 2: Codex (completed review)
├─ Outputs: Review findings in plan
└─ Signals: "Plan ready for implementation"

Terminal 1: Claude (NEW session)
├─ Reads: Updated plans/{feature}.md
├─ Notes: Codex findings in Phase 2.5
├─ Implements: Phases 1, 2.5, 2, 3, etc.
└─ Produces: Implementation code + tests
```

---

## PART 5: IMPLEMENTATION CHECKLIST

### Starting a New Feature (RPI Workflow)

```
☐ Step 1: Describe Feature
  ├─ Create folder: rpi/{feature-slug}/
  ├─ Write REQUEST.md with description
  └─ Output: rpi/{feature-slug}/REQUEST.md

☐ Step 2: Research
  ├─ Run: /rpi:research rpi/{feature-slug}/REQUEST.md
  ├─ Wait for: research/RESEARCH.md with GO/NO-GO
  ├─ If NO-GO: Stop, reconsider feature
  └─ If GO: Proceed to planning

☐ Step 3: Plan
  ├─ Run: /rpi:plan {feature-slug}
  ├─ Review: plan/PLAN.md, pm.md, ux.md, eng.md
  ├─ Adjust as needed (human review loop)
  └─ When ready: Proceed to implementation

☐ Step 4: Implement
  ├─ Run: /rpi:implement {feature-slug}
  ├─ For each phase:
  │  ├─ Code Discovery (Explore agent)
  │  ├─ Implementation (senior-software-engineer)
  │  ├─ Code Review (code-reviewer)
  │  ├─ Validation Gate (user approval)
  │  └─ Documentation Update
  └─ When all phases complete: Feature done
```

### Starting Agent Teams Workflow

```
☐ Phase 1: Establish Data Contract
  ├─ Agree on data structure: {field: type}
  ├─ Document in shared task list
  └─ All team members have copy

☐ Phase 2: Divide Tasks
  ├─ Create shared task list
  ├─ Each teammate picks task
  ├─ Document dependencies explicitly
  └─ Make list copy/paste friendly

☐ Phase 3: Setup Terminal
  ├─ brew install --cask iterm2
  ├─ brew install tmux
  ├─ tmux new -s dev
  └─ Split into 3+ panes (one per teammate)

☐ Phase 4: Start Claude (per pane)
  ├─ CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude
  ├─ Each teammate in own pane
  ├─ All can see each other's work
  └─ Paste shared task list into chat

☐ Phase 5: Coordinate
  ├─ Announce task completion in shared chat
  ├─ Other teammates read + react
  ├─ If dependency hit: wait for upstream task
  ├─ Verify data contract honored
  └─ When all done: Integrate

☐ Phase 6: Integrate
  ├─ One teammate integrates components
  ├─ Run end-to-end test
  ├─ Verify data flows correctly
  └─ Output: Final integrated feature
```

---

## PART 6: COMPARISON TABLE

### Orchestration Approaches

| Aspect | Agent Teams | RPI Workflow | Cross-Model |
|--------|------------|-------------|------------|
| **Scope** | Short features (hours) | Complex features (days/weeks) | Large features (weeks) |
| **Concurrency** | Full parallel (3-10 agents) | Sequential phases + parallel agents | Phases with human gates |
| **Human Involvement** | Data contract + final integration | Per-phase approval gates | Planning + verification gates |
| **Team Structure** | Specialized roles per component | Multi-phase roles (parser, PM, engineer, CTO) | Specialized models (Claude, Codex) |
| **Output** | Integrated feature code | Fully documented + implemented feature | Verified implementation |
| **Complexity** | Medium | High | Very High |
| **Setup Time** | ~5 min (tmux) | None (command-based) | ~10 min (2 terminals) |
| **Best For** | Building specific features in parallel | New feature development with rigor | Enterprise features with audit trail |

---

## APPENDIX: AGENT REGISTRY REFERENCE

### Agent Field Summary

```yaml
name:           # Identifier for agent
description:    # When to use + triggers
tools:          # Available tools (WebFetch, Read, Write, Edit, etc.)
model:          # opus/sonnet/haiku
color:          # green/blue/red (for tmux UI)
maxTurns:       # Conversation limit (5, 10, 20)
permissionMode: # acceptAll/acceptEdits/askAlways
memory:         # project/session/none
skills:         # List of preloaded skills
```

### Model Selection Guide
- **opus**: Deep analysis, multi-step reasoning, planning, architecture
- **sonnet**: Balanced - coding, engineering, reasonable complexity
- **haiku**: Simple transformations, fast operations, cost optimization

### Permission Modes
- **acceptAll**: Agent auto-approves file changes (fast)
- **acceptEdits**: Agent auto-approves edits to existing files (safer)
- **askAlways**: Ask user before every tool use (slowest but safest)

---

## CONCLUSION

### Key Takeaways

1. **Three Complementary Patterns**:
   - **Agent Teams**: Parallel specialists building one feature
   - **RPI Workflow**: Multi-phase feature development with gates
   - **Cross-Model**: AI-assisted with human feedback at critical points

2. **Command → Agent → Skill** is the foundation:
   - Commands orchestrate (user interaction layer)
   - Agents fetch/process (business logic)
   - Skills transform/render (output creation)

3. **Data Contracts** prevent integration failures:
   - Explicit format: `{field: type}`
   - Documented in shared task list
   - All parties agree before coding

4. **Validation Gates** catch problems early:
   - GO/NO-GO decision after research
   - Per-phase approval during implementation
   - Code review before proceeding

5. **Multi-Agent RPI** ensures completeness:
   - requirement-parser → structured requirements
   - product-manager → user value + alignment
   - senior-engineer → technical feasibility
   - technical-cto → strategic alignment
   - documentation-analyst → clear reports

6. **Skill Design** matters:
   - Agent skills = preloaded context (instructions)
   - Standalone skills = direct invocation (utilities)
   - Clear description = proper invocation

---

**Document Generated**: 2026-03-17
**Source**: 9 files analyzed from claude-code-best-practice repository
**Total Lines Analyzed**: ~8,500 lines of markdown + code
**Patterns Identified**: 23 core patterns extracted
