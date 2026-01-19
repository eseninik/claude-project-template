---
created: 2026-01-19
status: approved
branch: feature/oh-my-opencode-patterns
---

# Tech Spec: Oh-My-OpenCode Pattern Integration

**User Spec:** [user-spec.md](user-spec.md)

## Solution

Implement a layered automation system that progressively automates the manual "Dynamic Skill Selection" ceremony while maintaining backwards compatibility. The orchestrator agent will handle intent classification and skill selection, while **skills** (not hooks) provide session resumption and error recovery.

**Key insight from analysis:** Claude Code doesn't have a hooks framework for session lifecycle events. We use skills instead, which are cross-platform and integrate with orchestrator.

The implementation follows the existing patterns in the template:
- Agents in `.claude/agents/` with YAML frontmatter
- Skills in `.claude/skills/` with SKILL.md structure
- Commands in `.claude/commands/` as markdown
- ~~Hooks~~ → Skills (hooks don't work for our use cases)

## Architecture

### What we create/modify

0. **Skill Composition Guide** (`.claude/skills/methodology/guides/skill-composition.md`)
   - Documents input/output contracts between skills
   - Prerequisites and produced artifacts
   - Skill chains for common workflows
   - **MUST be created BEFORE orchestrator**

1. **Orchestrator Agent** (`.claude/agents/orchestrator.md`)
   - Primary entry point for all requests
   - Intent classification (trivial/explicit/exploratory/ambiguous)
   - Automatic skill selection based on intent
   - Task delegation to appropriate subagents
   - **Respects BLOCKING rules from CLAUDE.md** (enforcer, not optimizer)

2. **Session Resumption Skill** (`.claude/skills/session-resumption/SKILL.md`) + `/resume` command
   - Reads work/STATE.md at session start
   - Detects incomplete work
   - Offers structured resumption flow
   - **Replaces session-start hook (hooks don't support this)**

3. **Context Monitor Skill** (`.claude/skills/context-monitor/SKILL.md`)
   - **Heuristic estimation** (no API for real measurement)
   - Warning at ~50% (estimated), BLOCK at ~70%
   - Suggests subagent dispatch when blocked
   - Conservative approach: trigger early (40%) to be safe

4. **Self-Completion Skill** (`.claude/skills/self-completion/SKILL.md`)
   - Detects incomplete TodoWrite items
   - Auto-continues until <done> marker
   - Iteration tracking with max 5 attempts

5. **Background Tasks Tracking** (`work/background-tasks.json`)
   - Schema for tracking parallel subagent tasks
   - Status: pending/running/completed/failed
   - Wave number, timestamps, agent type
   - **Per-feature state** to avoid race conditions

6. **Error Recovery Skill** (`.claude/skills/error-recovery/SKILL.md`)
   - Structured recovery patterns for edit/bash/test errors
   - **Replaces recovery hooks (hooks can't intercept errors)**
   - Integrates with systematic-debugging for test failures
   - Max retry limits, escalation to user

7. **CLAUDE.md Updates**
   - Add "autowork" keyword mode
   - Integrate orchestrator as default entry point
   - Keep manual skill selection as fallback
   - Reference new skills in appropriate sections

### Data Flow

```
User Request
    ↓
Session Resumption Check (orchestrator first action)
    ↓
IF incomplete work → Ask: resume or fresh?
    ↓
Orchestrator Agent (intent classification)
    ↓
┌─────────────────────────────────────────────────┐
│  Intent Type                                    │
├─────────────────────────────────────────────────┤
│  trivial     → Direct response (no skills)     │
│  explicit    → Auto-select skills → Execute    │
│  exploratory → context-capture → user-spec     │
│  ambiguous   → Clarifying question             │
└─────────────────────────────────────────────────┘
    ↓
Context Monitor (check usage, warn/block if needed)
    ↓
Execution (with error-recovery skill on failures)
    ↓
Self-Completion (if todos remain)
    ↓
Quality Gates (UAT, verification - BLOCKING)
    ↓
Commit
```

## Key Decisions

### Decision 1: Orchestrator as Opus Agent

**Decision:** Use opus model for orchestrator
**Rationale:** Intent classification requires higher reasoning capability. Other agents (code-developer, code-reviewer) remain on sonnet for cost efficiency.

### Decision 2: Skills Instead of Hooks

**Decision:** Use skills for session resumption and error recovery
**Rationale:**
- Claude Code hooks framework doesn't support session lifecycle events
- Bash scripts don't work reliably on Windows (user's environment)
- Skills are cross-platform and integrate with orchestrator
- Skills can be invoked programmatically and manually (/resume command)

### Decision 3: Heuristic Context Estimation

**Decision:** Use heuristic estimation for context usage (no API available)
**Rationale:**
- Cannot query actual token usage mid-session
- Estimate based on: file sizes loaded + conversation length + skills loaded
- Conservative threshold (40%) to prevent quality degradation
- User can override block if needed

### Decision 4: Skill Composition Guide First

**Decision:** Create skill composition guide BEFORE orchestrator
**Rationale:**
- Analysis revealed skills don't document their contracts
- Orchestrator needs to know what each skill requires/produces
- Without contracts, orchestrator will call skills in wrong order
- Prevents "missing artifact" failures

### Decision 5: Orchestrator as Enforcer

**Decision:** Orchestrator enforces BLOCKING rules, doesn't optimize them away
**Rationale:**
- CLAUDE.md blocking rules exist because shortcuts led to failures
- UAT is MANDATORY - orchestrator cannot skip it
- Verification is MANDATORY before completion claims
- Phase transitions require explicit announcements

### Decision 6: Per-Feature State Files

**Decision:** Use `work/<feature>/state.json` in addition to global STATE.md
**Rationale:**
- Multiple parallel subagents can cause race conditions on STATE.md
- Per-feature state prevents writes from overwriting each other
- Global STATE.md remains single source of truth for session-level state
- Feature state tracks task progress within that feature

### Decision 7: Backwards Compatibility

**Decision:** Keep manual skill selection as fallback
**Rationale:**
- Allows gradual migration
- Useful for edge cases orchestrator misclassifies
- Users can override with explicit skill requests
- Existing workflows continue to work

## Data Models

### Background Tasks Schema (work/background-tasks.json)

```json
{
  "version": "1.0",
  "tasks": [
    {
      "id": "task-001-1705680000",
      "taskFile": "work/feature/tasks/1.md",
      "taskTitle": "Create user model",
      "agent": "code-developer",
      "wave": 1,
      "status": "pending|running|completed|failed",
      "startedAt": "2026-01-19T10:00:00Z",
      "completedAt": null,
      "result": null,
      "error": null
    }
  ],
  "activeWave": 1,
  "lastUpdated": "2026-01-19T10:00:00Z"
}
```

### Intent Classification

```typescript
type Intent = {
  type: 'trivial' | 'explicit' | 'exploratory' | 'ambiguous';
  confidence: number; // 0-1
  suggestedSkills: string[];
  reason: string;
}
```

### Context Estimation (Heuristic)

```typescript
type ContextEstimate = {
  filesLoaded: number;
  estimatedTokens: number;
  percentUsed: number; // 0-100
  recommendation: 'continue' | 'warning' | 'block';
}

// Estimation formula (conservative):
// small file (<100 lines): ~500 tokens
// medium file (100-500 lines): ~2000 tokens
// large file (>500 lines): ~5000 tokens
// skill loaded: ~3000 tokens
// conversation turn: ~1000 tokens
// total budget: ~200000 tokens
```

## Dependencies

**New packages:** None required

**Uses existing:**
- Agent task delegation (Task tool)
- TodoWrite for tracking
- STATE.md for persistence
- Existing skills (systematic-debugging, TDD, verification, UAT)

**Does NOT use:**
- ~~Claude Code hooks mechanism~~ (doesn't support our use cases)
- External databases
- Platform-specific bash scripts

## Testing

**Integration tests:**
- Test orchestrator classifies sample requests correctly
- Test session-resumption skill detects incomplete STATE.md
- Test context-monitor estimates are reasonable
- Test error-recovery skill handles each error type
- Test self-completion iterates correctly

**E2E tests:**
- Full "autowork" flow from request to completion
- Session resumption scenario
- Context overflow → subagent dispatch scenario
- Error → recovery → success scenario

## Risks & Mitigations

### Risk 1: Orchestrator misclassifies intent
**Impact:** Wrong skills loaded, wrong approach taken
**Mitigation:**
- Keep manual skill selection as fallback
- Log classifications for tuning
- User can override: "use TDD skill"
- Orchestrator asks clarifying questions when unsure

### Risk 2: Context estimation inaccurate
**Impact:** Either too aggressive (blocks too early) or too late (quality degrades)
**Mitigation:**
- Conservative estimates (40% threshold for warning)
- User can override block
- Monitor actual quality degradation (task failures)
- Adjust heuristics based on experience

### Risk 3: Skills don't compose as expected
**Impact:** Orchestrator calls skill A, but skill B fails because artifact missing
**Mitigation:**
- Task 0: Create skill composition guide FIRST
- Document input/output contracts
- Orchestrator validates artifacts before calling skill
- Error recovery handles missing artifacts

### Risk 4: STATE.md race conditions
**Impact:** Parallel subagents overwrite each other's decisions
**Mitigation:**
- Per-feature state files (`work/<feature>/state.json`)
- Global STATE.md for session-level state only
- Append-only mode for decisions/notes
- File locking where possible

### Risk 5: Breaking existing workflows
**Impact:** Users who rely on manual skill selection find it doesn't work
**Mitigation:**
- All new features are additive
- Existing CLAUDE.md rules remain unchanged
- Manual mode always available
- Orchestrator is opt-in via "autowork:" prefix

### Risk 6: Orchestrator skips quality gates
**Impact:** Features shipped without UAT/verification
**Mitigation:**
- Orchestrator is ENFORCER of rules, not optimizer
- UAT is BLOCKING - cannot proceed without user confirmation
- Verification-before-completion is BLOCKING
- Commit only after verification proof

## Implementation Tasks

- [ ] [Task 0: Create Skill Composition Guide](tasks/0.md) ← **START HERE**
- [ ] [Task 1: Create Orchestrator Agent](tasks/1.md)
- [ ] [Task 2: Create Session Resumption Skill](tasks/2.md) *(changed from hook)*
- [ ] [Task 3: Create Context Monitor Skill](tasks/3.md)
- [ ] [Task 4: Create Background Tasks Tracking](tasks/4.md)
- [ ] [Task 5: Add Autowork Mode to CLAUDE.md](tasks/5.md)
- [ ] [Task 6: Create Error Recovery Skill](tasks/6.md) *(changed from hooks)*
- [ ] [Task 7: Create Self-Completion Skill](tasks/7.md)
- [ ] [Task 8: Update SKILLS_INDEX.md](tasks/8.md)
- [ ] [Task 9: Integration Testing](tasks/9.md)
- [ ] [Task 10: Documentation and Examples](tasks/10.md)

## Wave Execution Plan

| Wave | Tasks | Reason |
|------|-------|--------|
| **Wave 1** | 0 (composition guide) | Must be first - documents skill contracts |
| **Wave 2** | 1, 2, 3, 4, 6, 7 | Independent skills/agents (parallel) |
| **Wave 3** | 5, 8 | Depend on orchestrator and skills |
| **Wave 4** | 9 | Integration tests (all components ready) |
| **Wave 5** | 10 | Documentation (after tests confirm working) |

## Critical Files Summary

| # | Path | Type | Description |
|---|------|------|-------------|
| 0 | `.claude/skills/methodology/guides/skill-composition.md` | NEW | Skill contracts (FIRST) |
| 1 | `.claude/agents/orchestrator.md` | NEW | Central orchestrator |
| 2 | `.claude/skills/session-resumption/SKILL.md` | NEW | Resume incomplete work |
| 3 | `.claude/commands/resume.md` | NEW | /resume command |
| 4 | `.claude/skills/context-monitor/SKILL.md` | NEW | Context usage tracking |
| 5 | `work/background-tasks.json` | NEW | Parallel task tracking |
| 6 | `.claude/skills/error-recovery/SKILL.md` | NEW | Error recovery patterns |
| 7 | `.claude/skills/self-completion/SKILL.md` | NEW | Auto-continue todos |
| 8 | `CLAUDE.md` | UPDATE | Autowork mode section |
| 9 | `.claude/skills/SKILLS_INDEX.md` | UPDATE | New skills + orchestrator |
| 10 | `.claude/skills/subagent-driven-development/SKILL.md` | UPDATE | Background task integration |
| 11 | `.claude/skills/methodology/guides/autowork-guide.md` | NEW | User documentation |
