# ADR-006: Two-Phase Agent Teams with Expert Panel

**Date:** 2026-02-11
**Status:** Accepted

---

## Context

Agent Teams Mode only supported **execution** (parallel implementation of tasks). The planning phase was single-agent interview (user-spec, tech-spec). This left a gap: no multi-perspective analysis before implementation.

When multiple experts analyze a problem, they catch issues that a single agent misses: security implications, performance bottlenecks, data model concerns, API design flaws. Real subagents with separate contexts produce better analysis than single-agent role-play.

## Decision

Implement two-phase Agent Teams: **Expert Panel** (planning) followed by **Implementation Team** (execution). The phrase "используй Agent Teams Mode" triggers both phases automatically.

## Rationale

- Real subagents > role-play: separate contexts prevent cross-contamination of perspectives
- Adaptive panel (3-5 from pool of 10) > fixed experts: saves resources, matches task complexity
- Two separate teams (panel shutdown → impl team) > combined: prevents context bloat
- expert-analysis.md as bridge file: standard format that tech-spec-planning can consume
- Priority Ladder for conflict resolution: deterministic, not opinion-based

## Alternatives Considered

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Single-agent role-play | Simple, no team overhead | Perspective contamination, shallow analysis | Quality too low for complex decisions |
| Fixed 7 experts always | Comprehensive coverage | Wasteful for simple tasks, high token cost | 3-5 adaptive is 40-60% cheaper |
| Combined panel+impl team | One team creation | Context bloat, mixed concerns | Panel agents don't need impl tools |
| Skip panel, straight to impl | Faster start | Missed architectural issues, rework | Rework cost > panel cost for complex tasks |

## Consequences

### Positive
- Multi-perspective analysis catches issues before implementation
- Adaptive role selection matches panel size to task complexity
- Priority Ladder provides deterministic conflict resolution
- expert-analysis.md creates audit trail of design decisions

### Negative
- Additional latency before implementation starts (~2-5 min for panel)
- More token usage for planning phase
- Requires user to wait for panel before coding begins

### Trade-offs
- Slower start but fewer rewrites (net positive for complex tasks)
- More upfront cost but less debugging cost later

## Implementation Notes

- Skill: `.claude/skills/expert-panel/SKILL.md` — role pool, domain detection, output template
- Workflow: `.claude/guides/expert-panel-workflow.md` — step-by-step orchestration
- Conflict resolution: `.claude/guides/priority-ladder.md` — 7-level priority framework
- Command: `.claude/commands/expert-panel.md` — standalone analysis without implementation
- Trigger: "используй Agent Teams Mode" / "Agent Teams Mode" / "экспертная панель"

## For AI Agents

- Before changing: Check if expert-analysis.md exists from prior panel run
- If proposing alternative: Explain why different expert composition is needed
- Related files: CLAUDE.md (AUTO-BEHAVIORS), SKILLS_INDEX.md (entry point), teammate-prompt-template.md (panel role mappings)
