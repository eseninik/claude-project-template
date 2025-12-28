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

# BLOCKING RULES

**These rules CANNOT be bypassed. Violation = task failure.**

## Before ANY code (fix/feature/refactor)

```
1. cat .claude/skills/SKILLS_INDEX.md
2. Select 1-3 skills → load EACH: cat .claude/skills/<name>/SKILL.md
3. Follow the skill
```

**Writing/changing code WITHOUT these steps is FORBIDDEN.**

## After EVERY code change

```
1. Write test/script for THIS specific change
2. Run → collect logs
3. Compare result with requirements (user request / tasks.md / proposal.md)
4. Doesn't match? → Fix → Repeat
```

**Without test, the change is NOT COMPLETE.**

## Before saying "done" / "fixed" / "complete"

```
cat .claude/skills/verification-before-completion/SKILL.md
→ Execute verification
→ Only then claim completion
```

## Rule Exceptions

A rule can be violated ONLY if:
1. Documented: which rule, why, what risks
2. User explicitly confirmed the exception

---

# OpenSpec Workflow

```
proposal/spec/new feature? → openspec/AGENTS.md (skills NOT needed)
openspec apply?            → Load skills → TDD → tests
openspec archive?          → openspec/AGENTS.md (skills NOT needed)
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

- `dev` — working branch, commit here
- `main` — production, auto-deploy

**Rules:**
1. Commit IMMEDIATELY after each completed change
2. DON'T touch `main` directly
3. `deploy` → merge dev into main

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

1. Handlers thin — logic in services
2. Dependency injection via middleware
3. FSM states in separate files
4. AsyncMock for handler tests
5. Don't block event loop

---

# Detailed Instructions

<details>
<summary>Testing Algorithm (expand)</summary>

### After EVERY code change:

1. **WRITE TEST** — script/test for THIS change
2. **RUN** — execute, collect logs
3. **ANALYZE** — read logs in detail
4. **COMPARE** — compare with requirements:
   - User request
   - `proposal.md` / `design.md`
   - `tasks.md`
5. **CONCLUDE**:
   - Matches → Done
   - Doesn't match → Fix → Repeat from step 1

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
   - **TEST** — verify the change
   - Mark `[x]` in tasks.md
4. After ALL tasks:
   - `verification-before-completion`
5. Report: "Ready for `openspec archive`"

</details>

<details>
<summary>Bug Fix Flow (expand)</summary>

```
1. cat .claude/skills/SKILLS_INDEX.md
2. Evaluate complexity:
   - Simple → systematic-debugging
   - Medium → + TDD
   - Complex → + code-review
3. Load selected skills
4. Find root cause
5. Write failing test
6. Fix
7. Test → logs → compare with bug description
8. verification-before-completion
```

</details>

<details>
<summary>Execution Mode Decision (expand)</summary>

```
Q1: Tasks depend on each other?
  Yes → DIRECT execution
  No  → Q2

Q2: More than 5 independent tasks?
  No  → DIRECT execution
  Yes → Q3

Q3: Each task > 50 lines of code?
  No  → DIRECT execution
  Yes → SUBAGENTS

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

- `@.claude/skills` — loads EVERYTHING, fills context
- Code without loading skills
- Bug-fix without `systematic-debugging`
- "Done" without `verification-before-completion`
- Change without test
- Violating rules without documented exception
