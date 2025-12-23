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
| `openspec proposal` | Stage 1: Planning | **NOT needed** (documentation only) |
| `openspec apply` | Stage 2: Implementation | **Required: load SKILLS_INDEX** |
| `openspec archive` | Stage 3: Archiving | NOT needed |

---

## Task Classification Algorithm

```
STEP 1 — CLASSIFY REQUEST:

  "openspec proposal" / "proposal:" / "spec:" / "new feature"?
  → openspec/AGENTS.md (Stage 1: Planning)
  → Skills NOT needed (planning only, no code)

  "openspec apply" / "implement" / "continue" / "execute tasks"?
  → OpenSpec Stage 2: Implementation
  → REQUIRED: load SKILLS_INDEX.md (see below)

  "openspec archive" / "finalize change"?
  → openspec/AGENTS.md (Stage 3: Archiving)
  → Skills NOT needed

  "fix:" / "bug" / "error"?
  → Load SKILLS_INDEX.md
  → Select 1-3 skills based on complexity
  → OpenSpec NOT needed

  Otherwise (refactor, optimize, small change)?
  → Load SKILLS_INDEX.md
  → Select appropriate skills

STEP 2 — LOAD SKILLS (for apply/implement/fix):

  cat .claude/skills/SKILLS_INDEX.md
  → Select 1-3 skills for the task
  → cat .claude/skills/<folder>/SKILL.md
  → Execute according to skill
```

---

## Execution Mode Decision

**BEFORE starting any implementation, evaluate:**

```
DECISION TREE:

Q1: Tasks depend on each other?
  Yes → DIRECT execution (subagents won't help)
  No  → Q2

Q2: More than 5 independent tasks?
  No  → DIRECT execution (overhead not worth it)
  Yes → Q3

Q3: Each task > 50 lines of code?
  No  → DIRECT execution (small tasks faster directly)
  Yes → SUBAGENTS

DEFAULT: DIRECT execution. Subagents = exception, not rule.
```

**Quick reference:**
- 1-5 tasks, same module → DIRECT
- Sequential dependencies → DIRECT
- < 100 lines total → DIRECT
- 6+ independent tasks, 50+ lines each → Consider SUBAGENTS

---

## Loading Skills (MANDATORY)

**BEFORE writing/changing any code:**

```bash
cat .claude/skills/SKILLS_INDEX.md
```

**This is NOT optional. This is MANDATORY.**

SKILLS_INDEX contains:
- Skill categories (mandatory/situational/workflow)
- Entry points (which skill to start with)
- Skill descriptions and paths

**After loading index:**
1. Select 1-3 skills based on task type
2. Load each: `cat .claude/skills/<folder>/SKILL.md`
3. Follow skill instructions

---

## Required Triggers

| Situation | Action | When |
|-----------|--------|------|
| Any bug/fix | Load SKILLS_INDEX → select skills | BEFORE attempting fix |
| New code | `test-driven-development` required | BEFORE writing code |
| **After EVERY code change** | **Test + analyze logs + compare with requirements** | AFTER every fix/implementation |
| Claiming "done" | `verification-before-completion` | BEFORE claiming completion |
| Flaky tests | `condition-based-waiting` | On race conditions |

---

## CRITICAL: Mandatory Testing After Every Change

**This section is CRITICAL. Never skip. Never rationalize skipping.**

### When to Test

- After EVERY code change
- After EVERY fix
- After EVERY task from tasks.md
- After subagent work — subagent tests their part
- After every session (if work spans sessions)

### Testing Algorithm

```
AFTER EVERY CODE CHANGE:

1. WRITE TEST SCRIPT
   → Write script/program to test THIS SPECIFIC change
   → Not "does service work in general", but THIS change specifically
   → Any scripts, utilities, tests are allowed

2. RUN TEST
   → Execute test on real scenario
   → Collect execution logs

3. ANALYZE LOGS
   → Read logs in detail
   → Find execution result

4. COMPARE WITH REQUIREMENTS
   → Take original request / proposal / design / tasks.md
   → Compare expected result with actual result

5. CONCLUSION
   ├─ Result MATCHES expectation → Task complete ✓
   └─ Result DOES NOT match → Make fixes → Repeat from step 1
```

### What to Compare Against

| Source | Where to Find |
|--------|---------------|
| User request | Original message in chat |
| OpenSpec proposal | `proposal.md` — section "What Changes" |
| OpenSpec design | `design.md` — expected behavior |
| Task | `tasks.md` — specific checklist item |
| Bug report | Bug description and expected behavior |

### Output Format After Test

```
## Test Result

**Change:** [what was changed]
**Test:** [how tested — script, command, scenario]
**Expected (from requirements):** [what should have happened]
**Actual (from logs):** [what actually happened]
**Status:** ✓ Matches / ✗ Does not match

[If does not match — what needs to be fixed]
```

### Example Cycle

```
Task: Add email validation to registration form

1. Wrote validation code
2. Wrote test script: curl with invalid email
3. Ran, collected logs
4. Expected (from tasks.md): "return 400 error with message"
5. Actual (from logs): returned 200 OK
6. DOES NOT match → fix code → rerun test
7. Actual (from logs): returned 400 with message
8. Matches ✓ → task complete
```

### Skills for Test Scripts

If test requires writing code — apply skills like for any code:

| Situation | Skills |
|-----------|--------|
| Simple curl/request | Not needed |
| Test with logic | `test-driven-development` |
| Complex mocks/stubs | `testing-anti-patterns` |
| Test with race conditions | `condition-based-waiting` |

**Test code = code. Same rules apply.**

### FORBIDDEN in Testing

- Skipping testing ("it works anyway")
- Testing "in your head" without actual run
- Marking task complete without test
- Ignoring mismatch between result and requirements
- Writing test code without skills when they're needed

---

## Escape Hatch: Rule Exceptions

Rules can be violated ONLY if:

1. **Documented:**
   ```
   RULE EXCEPTION:
   - Rule: [which rule is being violated]
   - Reason: [why exception is justified]
   - Risk: [what risks this creates]
   - Mitigation: [how to minimize risks]
   ```

2. **User confirmed the exception**

Without documentation and confirmation — violation is FORBIDDEN.

---

## During `openspec apply`

**Required order of actions:**

1. Read `proposal.md`, `design.md` (if exists), `tasks.md`
2. Load index: `cat .claude/skills/SKILLS_INDEX.md`
3. For each task from tasks.md:
   - Select skills (usually: `test-driven-development` + `executing-plans`)
   - Load: `cat .claude/skills/<folder>/SKILL.md`
   - Execute task according to skill
   - **TEST the change (see Testing Algorithm above)**
   - Mark `[x]` in tasks.md after completion
4. After ALL tasks:
   - Load `verification-before-completion`
   - Verify everything works
5. Report: "Ready for `openspec archive`"

---

## Typical Scenarios

### New Feature (full cycle)

```
STAGE 1 — OpenSpec (no skills):
  openspec/AGENTS.md → create proposal
  → proposal.md, tasks.md, design.md (documentation)
  → wait for approval
  → Skills NOT needed

STAGE 2 — Implementation (with skills):
  using-git-worktrees (isolation) — optional

  For EACH task:
    1. test-driven-development → write code
    2. TEST → script/command to verify this specific change
    3. ANALYZE LOGS → compare with tasks.md
    4. If DOES NOT match → fix → rerun test
    5. Mark [x] in tasks.md

  After ALL tasks:
    verification-before-completion
    finishing-a-development-branch

STAGE 3 — OpenSpec (no skills):
  openspec archive <change-id> --yes
```

### Bug Fix (without OpenSpec)

```
1. LOAD SKILLS INDEX
   cat .claude/skills/SKILLS_INDEX.md

2. ANALYZE COMPLEXITY
   → Simple (typo, obvious error): 1 skill
   → Medium (logic, validation): 2 skills
   → Complex (architecture, refactoring): 3 skills

3. SELECT SKILLS (examples):
   → Simple: systematic-debugging
   → Medium: systematic-debugging + TDD
   → Complex: systematic-debugging + TDD + code-review

4. EXECUTE:
   → Find root cause
   → Write failing test
   → Fix

5. TEST → script to verify fix
   → If test script requires code → apply skills!

6. ANALYZE LOGS → compare with bug description

7. If DOES NOT match → fix → repeat

8. verification-before-completion → verify
```

### Continue Implementation

```
1. openspec show <change-id> → understand context
2. Read tasks.md → find incomplete tasks
3. cat .claude/skills/SKILLS_INDEX.md
4. Select skills for current task
5. Continue work
```

---

## Forbidden

- `@.claude/skills` — loads EVERYTHING, fills context
- Loading skills "just in case"
- Writing code without `openspec proposal` for new features
- **Fixing bugs without loading SKILLS_INDEX first**
- Claiming "done" without `verification-before-completion`
- **Skipping testing after code changes**
- **Marking task done without real test + log analysis**
- **Writing test code without applying skills when needed**
- **Violating rules without documented exception**

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
