# Discuss-Phase Decision Capture

> Formalized decision gathering BEFORE planning. Captures user preferences, locked decisions, and deferred ideas to prevent scope creep and planning ambiguity.

## When to Use

- Before planning phase (after SPEC, before PLAN)
- When requirements have gray areas or ambiguous choices
- When user says "let's discuss", "what should we decide?", "before we plan"
- NOT for clear, well-specified tasks (skip directly to planning)

## Process

### 1. Load Context

Read all prior context:
- PROJECT.md / user-spec.md (what we're building)
- REQUIREMENTS.md or acceptance criteria
- Prior CONTEXT.md files (decisions from previous phases)
- STATE.md (accumulated decisions)
- Relevant source code (to avoid asking about things already decided by code)

### 2. Identify Gray Areas

Analyze the phase goal and identify domain-specific decision points. Generic categories are FORBIDDEN — be specific.

**Framework by deliverable type:**

| Deliverable | Gray Areas to Probe |
|-------------|-------------------|
| Something users SEE | Layout, density, states (empty/loading/error), responsiveness |
| Something users CALL | Response format, error responses, rate limiting, versioning |
| Something users RUN | Output format, flags/options, progress reporting, error recovery |
| Something users READ | Structure, tone, depth, navigation |
| Something that organizes | Grouping criteria, naming, duplicates, exceptions |

**Example (NOT generic):**
```
Phase: "User authentication"
Gray areas:
- Session handling: in-memory / Redis / JWT?
- Error responses: generic "invalid credentials" / detailed per-field?
- Multi-device: concurrent sessions allowed?
- Recovery: forgot password / biometric / 2FA?
```

### 3. Present Gray Areas

Show identified areas with relevant code context and prior decisions:
```
I've identified [N] areas where we need decisions before planning:

1. [Area 1] — [brief context, what code already does if relevant]
2. [Area 2] — [brief context]
3. [Area 3] — [brief context]

Which areas do you want to discuss? (numbers, or "all", or "skip")
```

### 4. Deep-Dive Questions

For each selected area, ask 4 concrete, scenario-based questions:

**Pattern:**
- Question about the common case
- Question about the edge case
- Question about the failure case
- Question about the integration point

After 4 questions, ask: "More questions about [area], or move to next?"

### 5. Capture Decisions

Write decisions to `work/{feature}/CONTEXT.md`:

```markdown
# Phase: [Name] — Context

Gathered: [date]
Status: Ready for planning

## Phase Boundary
[Clear statement of what this phase delivers — scope anchor]

## Implementation Decisions

### [Area 1]
- **Decision:** [what was chosen]
- **Rationale:** [why]
- **Constraint:** [any limits this imposes]

### [Area 2]
- **Decision:** [what was chosen]

### Claude's Discretion
[Areas where user said "you decide" — document what YOU will choose and why]

## Existing Code Insights

### Reusable Assets
- [Component/utility]: [how to reuse]

### Established Patterns
- [Pattern]: [how it constrains this phase]

### Integration Points
- [Where new code connects to existing]

## Deferred Ideas
[Ideas from discussion that belong in other phases — NOT lost, just parked]
- [Idea 1] — suggested during [area] discussion, belongs in Phase [N]
- [Idea 2] — future enhancement, not current scope
```

## Scope Guardrail

Phase boundary is FIXED. Discussion clarifies HOW, not WHETHER.

When user suggests scope creep:
> "That's a new capability — it deserves its own phase. Want me to note it for later?"

Capture in "Deferred Ideas" section. Never expand current phase scope.

## Integration

- **Pipeline:** Use between SPEC and PLAN phases
- **Output:** Consumed by planner agent as locked decisions
- **Downstream:** Planner MUST NOT contradict locked decisions from CONTEXT.md
- **Accumulation:** Each phase's CONTEXT.md is available to future phases

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Generic gray areas ("UI decisions") | Be domain-specific ("card layout: grid vs list vs masonry") |
| Asking one question per area | Ask 4 scenario-based questions minimum |
| Expanding scope during discussion | Use Deferred Ideas — phase boundary is fixed |
| Ignoring existing code decisions | Scout codebase FIRST — don't ask what's already decided |
| Skipping "Claude's Discretion" | Document YOUR choices for areas user didn't care about |
