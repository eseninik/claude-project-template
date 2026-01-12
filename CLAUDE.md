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

# STOP! BLOCKING RULES

**These rules CANNOT be bypassed. Violation = task failure.**

## Dynamic Skill Selection

### When to re-evaluate skills:
- At the START of working on a task
- When CHANGING phases (research -> code -> tests -> completion)
- When the SITUATION CHANGED (found different problem, approach changed)

### Algorithm (MANDATORY):

```
1. STOP
2. Write to user: "Situation: [what I'm doing now]"
3. cat .claude/skills/SKILLS_INDEX.md
4. Analyze ALL 30 skills - which fit the current situation?
5. Write to user: "Skills: [list with brief reasoning]"
6. Load EACH: cat .claude/skills/<name>/SKILL.md
7. Follow loaded skills
```

### Checkpoint (BLOCKING):

**I CANNOT write/change code without this message:**
```
Situation: [description of current phase]
Skills: [skill1] (reason), [skill2] (reason)
```

This message = proof that I analyzed and selected.
**Without this message, writing code is FORBIDDEN.**

### Switching between skills:

When situation changes:
```
1. Write: "Phase change: [was] -> [became]"
2. Repeat selection algorithm
3. Old skills "unload", work with new ones
```

## After EVERY code change

```
1. Write test/script for THIS change
2. Run -> collect logs
3. Compare result with requirements (user request / tasks.md / proposal.md)
4. Doesn't match? -> Fix -> Repeat
```

**Without test, the change is NOT COMPLETE.**

## Before saying "done" / "fixed" / "complete"

```
1. Write: "Phase change: code -> verification"
2. cat .claude/skills/verification-before-completion/SKILL.md
3. Execute verification per skill
4. Only then claim completion
```

## After task completion - AUTO-COMMIT

**I CANNOT say "done" / "Ready for archive" without commit.**

```
1. Verification passed
2. git add <changed files>
3. git commit -m "type: description"
4. git push origin dev
5. Only then claim completion
```

**Without commit, task is NOT COMPLETE.**

## Rule Exceptions

A rule can be violated ONLY if:
1. Documented: which rule, why, what risks
2. User explicitly confirmed the exception

---

# OpenSpec Workflow

```
proposal/spec/new feature? -> openspec/AGENTS.md (skills NOT needed)
openspec apply?            -> Load skills -> TDD -> tests
openspec archive?          -> openspec/AGENTS.md (skills NOT needed)
```

---

# Reference Information

## Windows: Python Commands

**Problem:** `python` returns exit code 49 due to Cyrillic in path.

**Solution:** Use `py -3.12`:

```bash
py -3.12 -m pytest tests/
py -3.12 -m ruff check src tests
py -3.12 script.py
```

## Git Workflow

- `dev` - working branch, commit here
- `main` - production, auto-deploy

**Rules:**
1. Commit IMMEDIATELY after each completed change
2. DON'T touch `main` directly
3. `deploy` -> merge dev into main

```bash
git add <files> && git commit -m "fix: description" && git push origin dev
```

## Commands

```bash
py -3.12 -m pytest tests/ -v              # tests
py -3.12 -m ruff check src tests          # linting
py -3.12 -m pytest tests/ --cov=bot       # coverage
```

## Code Style

- Line length: 100
- Type hints on public functions
- snake_case (functions), PascalCase (classes)
- Async: `async def`, `await` for I/O

## aiogram Best Practices

1. Handlers thin - logic in services
2. Dependency injection via middleware
3. FSM states in separate files
4. AsyncMock for handler tests
5. Don't block event loop

---

# Detailed Instructions

<details>
<summary>Testing Algorithm (expand)</summary>

### After EVERY code change:

1. **WRITE TEST** - script/test for THIS change
2. **RUN** - execute, collect logs
3. **ANALYZE** - read logs in detail
4. **COMPARE** - compare with requirements:
   - User request
   - `proposal.md` / `design.md`
   - `tasks.md`
5. **CONCLUDE**:
   - Matches -> Done
   - Doesn't match -> Fix -> Repeat from step 1

### Report format:

```
## Test Result

**Change:** [what was changed]
**Test:** [how tested]
**Expected:** [what was expected per requirements]
**Actual:** [what happened]
**Status:** Matches / Does not match
```

</details>

<details>
<summary>OpenSpec Apply (expand)</summary>

1. Read `proposal.md`, `design.md`, `tasks.md`
2. `cat .claude/skills/SKILLS_INDEX.md`
3. For each task:
   - Select skills (usually TDD + executing-plans)
   - Load each skill
   - Execute task per skill
   - **TEST** - verify the change
   - Mark `[x]` in tasks.md
4. After ALL tasks:
   - `verification-before-completion`
5. Report: "Ready for `openspec archive`"

</details>

<details>
<summary>Bug Fix Flow (expand)</summary>

### Phase 1: Research
```
Situation: Investigating bug, looking for root cause
Skills: systematic-debugging (finding cause), [+ others as needed]
```
-> Load skills -> Find root cause

### Phase 2: Writing code
```
Phase change: research -> code
Situation: Writing fix in Python
Skills: async-python-patterns (async code), [+ others as needed]
```
-> Load skills -> Write fix

### Phase 3: Tests
```
Phase change: code -> tests
Situation: Writing tests for fix
Skills: test-driven-development, python-testing-patterns
```
-> Load skills -> Write tests -> Run

### Phase 4: Completion
```
Phase change: tests -> verification
Situation: Verifying everything is ready
Skills: verification-before-completion
```
-> Load skill -> Verify -> Claim "done"

</details>

<details>
<summary>Execution Mode Decision (expand)</summary>

```
Q1: Tasks depend on each other?
  Yes -> DIRECT execution
  No  -> Q2

Q2: More than 5 independent tasks?
  No  -> DIRECT execution
  Yes -> Q3

Q3: Each task > 50 lines of code?
  No  -> DIRECT execution
  Yes -> SUBAGENTS

DEFAULT: DIRECT. Subagents = exception.
```

</details>

<details>
<summary>Python Skills Reference (expand)</summary>

| Task | Skills |
|------|--------|
| Any async code | `async-python-patterns` |
| Writing tests | `python-testing-patterns` |
| New handler/router | `telegram-bot-architecture` |
| Personal data | `security-checklist` |
| New API/webhook | `api-design-principles` |
| Architecture refactor | `architecture-patterns` |
| Performance issues | `python-performance-optimization` |

</details>

<details>
<summary>Security Checklist (expand)</summary>

Before ANY code handling personal data:
- [ ] Load `security-checklist` skill
- [ ] Validate all user input
- [ ] Encrypt sensitive data at rest
- [ ] Mask PII in logs
- [ ] Use parameterized queries
- [ ] Set file upload limits

</details>

<details>
<summary>New Project Setup (expand)</summary>

```bash
git clone <template> my-new-project
cd my-new-project
claude
/init-project
```

Claude automatically:
1. Takes name from folder
2. Reads `~/.claude/deploy.json`
3. Creates GitHub repo
4. Configures Secrets
5. Connects to server
6. Adds Deploy Key
7. Runs test deploy

Global config `~/.claude/deploy.json`:
```json
{
  "github_owner": "eseninik",
  "server_host": "16.170.136.118",
  "server_user": "ubuntu",
  "base_path": "/home/ubuntu",
  "ssh_key": "C:/Users/USERNAME/.ssh/id_ed25519",
  "ssh_config": "C:/Users/USERNAME/.ssh/config"
}
```

</details>

---

# FORBIDDEN

- `@.claude/skills` - loads EVERYTHING, fills context
- Code without checkpoint message "Situation: ... Skills: ..."
- Phase change without message "Phase change: X -> Y"
- "Done" without loading `verification-before-completion`
- Change without test
- Violating rules without documented exception
