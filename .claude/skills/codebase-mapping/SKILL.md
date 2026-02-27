---
name: codebase-mapping
description: |
  Analyzes codebase structure into codebase-map.md.
  Discovers tech stack, entry points, modules, dependencies.
  Use when starting work on an existing/unfamiliar project.
  Does NOT apply to new projects built from scratch.
roles: [spec-researcher, business-analyst, system-architect]
---

## Philosophy
You must understand the territory before making changes. Mapping first prevents accidental breakage of unknown dependencies.

## Critical Constraints
**never:**
- Propose changes to code you haven't mapped
- Skip mapping for unfamiliar projects

**always:**
- Produce codebase-map.md with entry points, modules, and dependencies
- Identify tech stack and patterns before implementation

# Codebase Mapping

## Steps
1. Detect tech stack: `ls` root for package.json/pyproject.toml/Cargo.toml/go.mod
2. Find entry points: main.py, index.ts, main.go, src/main.rs
3. Map directory structure: `ls -R` top 2 levels
4. Identify modules: group by directory (routes/, models/, services/, tests/)
5. Check dependencies: requirements.txt/package.json deps section
6. Find config: .env.example, config/, settings
7. Write `codebase-map.md` with: stack, entry points, modules, deps, config

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
