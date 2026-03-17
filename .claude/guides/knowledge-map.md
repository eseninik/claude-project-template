# Knowledge Map

> Where to find information. Lookup table for agents.

## Core Memory
| Need | Location |
|------|----------|
| Session context | `.claude/memory/activeContext.md` |
| Patterns + Gotchas | `.claude/memory/knowledge.md` |
| Daily logs | `.claude/memory/daily/{YYYY-MM-DD}.md` |
| Archived sessions | `.claude/memory/archive/` |
| Agent type memory | `.claude/agent-memory/{type}/MEMORY.md` |

## Pipeline & Tasks
| Need | Location |
|------|----------|
| Pipeline state | `work/PIPELINE.md` |
| Task state | `work/STATE.md` |
| Architecture decisions | `.claude/adr/decisions.md` |
| Pipeline templates | `.claude/shared/work-templates/` |
| Phase templates | `.claude/shared/work-templates/phases/` |
| Nyquist test map | `work/{feature}/nyquist-map.md` |
| Decision context | `work/{feature}/CONTEXT.md` |
| Quick task tracking | `work/quick/{N}-{slug}.md` |
| Auto-research output | `work/{feature}/auto-research.md` |

## Agent System
| Need | Location |
|------|----------|
| Agent type registry | `.claude/agents/registry.md` |
| Focused prompt files | `.claude/prompts/` |
| Agent spawner | `.claude/scripts/spawn-agent.py` |
| Prompt generator | `.claude/scripts/generate-prompt.py` |

## Skills & Guides
| Need | Location |
|------|----------|
| QA validation skill | `.claude/skills/qa-validation-loop/SKILL.md` |
| Experiment Loop skill | `.claude/skills/experiment-loop/SKILL.md` |
| Skill evolution | `.claude/skills/skill-evolution/SKILL.md` |
| AO Fleet skill | `.claude/skills/ao-fleet-spawn/SKILL.md` |
| AO Hybrid skill | `.claude/skills/ao-hybrid-spawn/SKILL.md` |
| Logging standards | `.claude/guides/logging-standards.md` |
| Results Board guide | `.claude/guides/results-board.md` |
| Auto-research guide | `.claude/guides/auto-research-phase.md` |
| Context triggers | `.claude/guides/context-triggers.md` |

## Configuration
| Need | Location |
|------|----------|
| Runtime config | `.claude/ops/config.yaml` |
| AO config | `~/.agent-orchestrator.yaml` |
| Memory config | `.claude/memory/.memory-config.json` |
| Graphiti integration | `.claude/guides/graphiti-integration.md` |

## Scripts
| Need | Location |
|------|----------|
| Memory engine | `.claude/scripts/memory-engine.py` |
| AO Hybrid helper | `.claude/scripts/ao-hybrid.sh` |
| Health check | `.claude/commands/health.md` |
