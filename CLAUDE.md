<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

---

## Workflow: OpenSpec + Skills

### Main Principle

```
OpenSpec = WHAT to do (proposal, tasks, specs)
Skills   = HOW to do it (TDD, debugging, verification)
```

### OpenSpec Commands

| Command | Phase | Skills |
|---------|-------|--------|
| `openspec proposal` | Stage 1: Planning | Not needed |
| `openspec apply` | Stage 2: Implementation | **Required: SKILLS_INDEX** |
| `openspec archive` | Stage 3: Archiving | Not needed |

---

### Task Classification Algorithm

```
STEP 1 — CLASSIFY:

  "openspec proposal" / "proposal:" / "spec:" / "new feature"?
  → openspec/AGENTS.md (Stage 1: Planning)
  → Skills NOT needed

  "openspec apply" / "implement" / "continue" / "execute tasks"?
  → OpenSpec Stage 2: Implementation
  → REQUIRED: load SKILLS_INDEX.md (see below)

  "openspec archive" / "finalize change"?
  → openspec/AGENTS.md (Stage 3: Archiving)
  → Skills NOT needed

  "fix:" / "bug" / "error"?
  → Skills directly: systematic-debugging
  → OpenSpec NOT needed

  Otherwise?
  → cat .claude/skills/SKILLS_INDEX.md
  → Select appropriate skills

STEP 2 — LOAD SKILLS (for apply/implement/fix):

  cat .claude/skills/SKILLS_INDEX.md
  → Select 1-3 skills for the task
  → cat .claude/skills/<folder>/SKILL.md
  → Execute according to skill
```

---

### Execution Mode Decision (STEP 0)

**BEFORE starting any implementation (fix, apply, coding), evaluate:**

```
COMPLEXITY CHECK:

  Count tasks/changes:
  - 1-5 simple tasks in same module → DIRECT execution
  - 6+ tasks OR complex logic → Consider subagents

  Check dependencies:
  - Tasks are sequential (each depends on previous) → DIRECT execution
  - Tasks are independent (can parallelize) → SUBAGENTS may help

  Estimate scope:
  - < 100 lines of code, 1-3 files → DIRECT execution
  - > 200 lines, 5+ files, multiple modules → Consider subagents

DECISION MATRIX:

  DIRECT execution (no subagents):
  ✓ Simple sequential tasks
  ✓ Code already written in plan
  ✓ Few files to modify
  ✓ Changes are straightforward insertions/modifications

  SUBAGENT execution:
  ✓ 10+ independent tasks
  ✓ Complex analysis needed per task
  ✓ Multiple unrelated modules
  ✓ Can benefit from parallel execution

DEFAULT: Start with DIRECT execution. Subagents are overhead for simple work.
```

---

### During `openspec apply`

**Required order of actions:**

1. Read `proposal.md`, `design.md` (if exists), `tasks.md`
2. Load index: `cat .claude/skills/SKILLS_INDEX.md`
3. For each task from tasks.md:
   - Select skills (usually: `test-driven-development` + `executing-plans`)
   - Load: `cat .claude/skills/<folder>/SKILL.md`
   - Execute task according to skill
   - Mark `[x]` in tasks.md after completion
4. After ALL tasks:
   - Load `verification-before-completion`
   - Verify everything works
5. Report: "Ready for `openspec archive`"

---

### Required Triggers

| Situation | Skill | When to load |
|-----------|-------|--------------|
| Any bug | `systematic-debugging` | BEFORE attempting fix |
| New code | `test-driven-development` | BEFORE writing code |
| "Done" / completion | `verification-before-completion` | BEFORE claiming completion |
| Flaky tests | `condition-based-waiting` | On race conditions |

---

### Forbidden

- `@.claude/skills` — loads EVERYTHING, fills context
- Loading skills "just in case"
- Writing code without `openspec proposal` for new features
- Fixing bugs without `systematic-debugging`
- Claiming "done" without `verification-before-completion`

---

## Project Overview

<!-- TODO: Describe your project here -->

**Primary language**: <!-- TODO: e.g., Russian, English -->

## Commands

```bash
# TODO: Add your project commands
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Linting and formatting
ruff check src tests
ruff format src tests
mypy src
```

## Architecture

<!-- TODO: Describe your architecture -->

## Environment Variables

```bash
# TODO: List required environment variables
```

## Code Style

- Line length: 100
- Type hints required on public functions
- snake_case (functions), PascalCase (classes)
- Async: `async def`, use `await` for I/O

## Git Workflow (CI/CD)

**Branches:**
- `dev` — development (no auto-deploy)
- `main` — production (auto-deploy to server)

**Rules for Claude:**
1. After each code change → `git add . && git commit && git push origin dev`
2. On "deploy" command → use `--squash` merge to create a clean single commit:
   ```bash
   git checkout main
   git merge --squash dev
   git commit -m "feat: <meaningful description of the change>"
   git push origin main
   git checkout dev
   ```
3. Push to main automatically deploys to server via GitHub Actions

**Why `--squash`:** Multiple dev commits get combined into one clean commit on main, with a meaningful message instead of "chore: update checkboxes" from the last micro-commit.

## Project Initialization (for Claude)

**IMPORTANT:** When starting a new project from this template, Claude MUST:

1. **Check if GitHub CLI is installed:**
   ```bash
   gh --version
   ```

2. **If not installed — install it:**
   - Windows: `winget install --id GitHub.cli`
   - macOS: `brew install gh`
   - Linux: see https://github.com/cli/cli/blob/trunk/docs/install_linux.md

3. **Check authentication:**
   ```bash
   gh auth status
   ```
   If not authenticated, ask user to run `gh auth login`

4. **Create GitHub repository and push:**
   ```bash
   gh repo create <project-name> --private --source=. --remote=origin --push
   ```

This ensures all projects have proper GitHub integration from the start.
