# Health Check Guide

> Validates .claude/ directory integrity and auto-repairs common issues.

## Quick Start

Run `/health` to check project structure, or read this guide and perform checks manually.

## Required Structure

```
.claude/
├── agents/
│   └── registry.md          # Agent type definitions
├── adr/
│   ├── _template.md          # ADR template
│   └── decisions.md          # Decision log
├── guides/                   # Workflow guides
├── memory/
│   ├── activeContext.md       # Session bridge (< 150 lines)
│   ├── knowledge.md           # Patterns + gotchas with verified dates
│   ├── daily/                 # Daily logs
│   ├── archive/               # Archived sessions
│   └── observations/          # Typed observations
├── ops/
│   └── config.yaml            # Runtime config
├── prompts/                   # Agent prompt templates
├── scripts/                   # Automation scripts
├── shared/
│   ├── interview-templates/   # Interview YAML files
│   └── work-templates/        # Pipeline/phase templates
├── skills/
│   └── */SKILL.md             # Skill definitions
└── CLAUDE.md (project root)   # Main instructions
```

## Validation Rules

### Frontmatter Validation (Skills)

Every SKILL.md must have:
```yaml
---
name: skill-name           # Required, lowercase-kebab
description: >             # Required, 1-3 lines
  What it does. Use when X. Do NOT use for Y.
roles: [role1, role2]      # Required, from registry
---
```

### Config Validation (ops/config.yaml)

Required fields:
```yaml
execution_engine: teamcreate  # or ao_hybrid
memory:
  tiers:
    active: 14
    warm: 30
    cold: 90
```

### Pipeline Validation (work/PIPELINE.md)

Required per phase:
- Status: (PENDING/IN_PROGRESS/DONE/BLOCKED)
- Mode: (SOLO/AGENT_TEAMS/AO_HYBRID/AO_FLEET)
- On PASS/FAIL/REWORK transitions
- Gate description

## Common Issues and Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| "No CLAUDE.md found" | Wrong working directory | cd to project root |
| "registry.md missing" | Incomplete template init | Copy from shared/templates/new-project/ |
| "Stale knowledge entries" | Entries not touched in 30+ days | Run `memory-engine.py decay` |
| "activeContext.md too long" | Session not archived | Move old sections to archive/ |
| "Orphaned pipeline phase" | Phase unreachable via transitions | Fix On PASS/FAIL links |
| "Skill over 500 lines" | Needs refactoring | Move excess to references/ subdirectory |
