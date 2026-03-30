---
name: codebase-mapping
description: |
  Map an unfamiliar codebase into structured codebase-map.md: tech stack, entry points, modules, dependencies, config, tests.
  Use when: onboarding to a new/existing repository, "map this codebase", "what does this project do", "understand this repo", exploring unfamiliar project structure, or need project overview before making changes.
  Do NOT use for: new projects from scratch, explaining specific functions, finding specific definitions (use search), or fixing bugs.
roles: [spec-researcher, business-analyst, system-architect]
---

# Codebase Mapping

## Overview
Understand the territory before making changes. Mapping first prevents accidental breakage of unknown dependencies and gives a shared mental model of the project structure.

## Mapping Steps

1. **Detect tech stack**: Check root for `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`
2. **Find entry points**: Look for `main.py`, `index.ts`, `main.go`, `src/main.rs`
3. **Map directory structure**: List top 2 levels of directories
4. **Identify modules**: Group by directory (routes/, models/, services/, tests/)
5. **Check dependencies**: Read requirements.txt / package.json deps section
6. **Find config**: Look for `.env.example`, `config/`, settings files
7. **Write codebase-map.md**: Consolidate findings into structured output

## Output: codebase-map.md

```markdown
# Codebase Map
- **Stack:** Python 3.12 + FastAPI + SQLAlchemy
- **Entry:** src/main.py
- **Modules:** routes/, models/, services/, core/
- **Tests:** tests/ (pytest)
- **Config:** .env + config/settings.py
- **Dependencies:** [key deps list]
```

## Common Mistakes
- **Proposing changes to code you haven't mapped** -- always map before modifying unfamiliar code
- **Skipping dependency analysis** -- hidden dependencies cause cascading breakage
- **Mapping only top-level structure** -- module internals and cross-module dependencies matter too
- **Not identifying test infrastructure** -- knowing how to run tests is critical for verification

## Related
- ← expert-panel — Researcher/Architect roles use this skill
- ← project-planning — project understanding phase
- ← tech-spec-planning — architecture context gathering
