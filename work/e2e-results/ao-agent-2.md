# AO Task 2: CLAUDE.md Skill Trigger Coverage Analysis

> Generated: 2026-02-27
> Branch: session/template-2
> Commit base: 6356fcf (refactor: CLAUDE.md variant B - progressive disclosure)

---

## 1. Key Finding: No "Skills (invoke via Skill tool)" Trigger Table Exists

The current CLAUDE.md (variant B — progressive disclosure, commit `6356fcf`) does **not** contain a "Skills (invoke via Skill tool)" trigger table with 13 skills. The CLAUDE.md was refactored in two recent commits:

- `1cdff94` — restructured with Context Loading Triggers
- `6356fcf` — variant B with progressive disclosure

### What CLAUDE.md Actually Contains

| Section | Type | Count | Details |
|---------|------|-------|---------|
| **CONTEXT LOADING TRIGGERS** | Guide triggers (not skills) | 8 | Maps situations → `.claude/guides/*.md` files |
| **Dynamic Skill Selection** | Blocking rule | — | Delegates to `SKILLS_INDEX.md` for skill lookup |
| **Direct skill references** | Inline mentions | 2 | `verification-before-completion`, `subagent-driven-development` |
| **Previous version (HEAD~1)** | KEY SKILLS table | 8 | 4 categories, 8 skills — removed in latest refactor |

The skill trigger mechanism is **delegated** to `.claude/skills/SKILLS_INDEX.md` via the "Dynamic Skill Selection" blocking rule (CLAUDE.md lines 63-73).

---

## 2. CLAUDE.md Direct Skill References

These skills are referenced directly in CLAUDE.md (not via SKILLS_INDEX.md):

| Skill | CLAUDE.md Location | Context | SKILL.md Exists | Description Match |
|-------|-------------------|---------|-----------------|-------------------|
| `verification-before-completion` | Line 103 (Before "готово" rule) | `cat .claude/skills/verification-before-completion/SKILL.md` | YES | YES — "Use when about to claim work is complete, fixed, or passing" matches "Before готово" trigger |
| `subagent-driven-development` | Lines 66, 86-88 (Dynamic Skill Selection, Plan Execution) | AUTO-CHECK for 3+ tasks; Plan execution | YES | YES — "Use when executing implementation plans with independent tasks" matches plan execution trigger |

**Verdict: Both direct references match their SKILL.md descriptions.**

---

## 3. SKILLS_INDEX.md Entry Points Table Coverage

Since CLAUDE.md delegates skill selection to SKILLS_INDEX.md, this is the **effective trigger table**. It contains 24 entries:

| # | Situation (Trigger) | Skill | SKILL.md Exists | Description Alignment | Verdict |
|---|---------------------|-------|-----------------|----------------------|---------|
| 1 | Понять проект | `project-knowledge` | **NO** (no dir) | N/A — skill directory missing | GAP |
| 2 | Новый/незнакомый проект | `codebase-mapping` | **NO** (no dir) | N/A — skill directory missing | GAP |
| 3 | Новый проект с нуля | `methodology` | PARTIAL (dir exists, no SKILL.md) | N/A — SKILL.md missing | GAP |
| 4 | Неясные требования | `context-capture` | **NO** (no dir) | N/A — skill directory missing | GAP |
| 5 | Планирование фичи | `user-spec-planning` | **NO** (no dir) | N/A — skill directory missing | GAP |
| 6 | Bug / Error | `systematic-debugging` | YES | YES — "Use when encountering any bug, test failure, or unexpected behavior" | MATCH |
| 7 | New code (any) | `test-driven-development` | YES | YES — "Use when implementing any feature or bugfix" | MATCH |
| 8 | Executing plan | `executing-plans` | YES | YES — "Use when partner provides a complete implementation plan" | MATCH |
| 9 | Parallel tasks with file conflicts | `subagent-driven-development` | YES | YES — "Use when executing implementation plans with independent tasks" | MATCH |
| 10 | Flaky test | `condition-based-waiting` | YES | YES — "Use when tests have race conditions, timing dependencies" | MATCH |
| 11 | Реализация завершена | `user-acceptance-testing` | **NO** (no dir) | N/A — skill directory missing | GAP |
| 12 | Before "done" | `verification-before-completion` | YES | YES — "Use when about to claim work is complete" | MATCH |
| 13 | Finishing branch | `finishing-a-development-branch` | YES | YES — "Use when implementation is complete, all tests pass" | MATCH |
| 14 | Infrastructure setup | `infrastructure` | **NO** (no dir) | N/A — skill directory missing | GAP |
| 15 | Testing strategy | `testing` | **NO** (no dir) | N/A — skill directory missing | GAP |
| 16 | Python async code | `async-python-patterns` | YES | YES — "Use when working with asyncio, aiohttp, aiogram" | MATCH |
| 17 | Telegram bot | `telegram-bot-architecture` | YES | YES — "Use when structuring Telegram bot projects with aiogram" | MATCH |
| 18 | Personal data | `security-checklist` | YES | YES — "Use when working with personal data, API keys, authentication" | MATCH |
| 19 | New API endpoint | `api-design-principles` | YES | YES — "Use when designing REST APIs, webhooks, or any HTTP endpoints" | MATCH |
| 20 | Major refactoring | `architecture-patterns` | YES | YES — "Use when designing application architecture, refactoring code structure" | MATCH |
| 21 | New project setup | `python-packaging` | YES | YES — "Use when setting up new Python project" | MATCH |
| 22 | Performance issues | `python-performance-optimization` | YES | YES — "Use when code is slow, needs profiling, or requires optimization" | MATCH |
| 23 | Need tests scaffold | `test-generator` | YES | YES — "BACKGROUND SKILL - Automatically generates test scaffolds" | MATCH |
| 24 | Code review needed | `code-reviewer` | YES | YES — "BACKGROUND SKILL - Automatically activated when writing or modifying code" | MATCH |

Additional Entry Points (implicit, from "Then" column):

| # | Skill | SKILL.md Exists | Referenced As |
|---|-------|-----------------|---------------|
| 25 | `tech-spec-planning` | **NO** (no dir) | Follow-up to user-spec-planning |
| 26 | `project-planning` | **NO** (no dir) | Follow-up to methodology |
| 27 | `using-git-worktrees` | YES | Auto with subagent-driven-development |
| 28 | `secret-scanner` | YES | Follow-up to security-checklist |
| 29 | `python-testing-patterns` | YES | Follow-up to async-python-patterns |

---

## 4. Skills in `.claude/skills/` NOT Covered by Any Trigger Table

These 34 skills have SKILL.md files. Skills **not referenced** in either CLAUDE.md or SKILLS_INDEX.md Entry Points:

| Skill | Has SKILL.md | In SKILLS_INDEX Categories | In Entry Points | Status |
|-------|-------------|---------------------------|-----------------|--------|
| `defense-in-depth` | YES | YES (Situational) | NO | In catalog, not in Entry Points |
| `dispatching-parallel-agents` | YES | YES (Situational) | NO | In catalog, not in Entry Points |
| `root-cause-tracing` | YES | YES (Situational) | NO | In catalog, not in Entry Points |
| `error-recovery` | YES | YES (Automation) | NO | In catalog, not in Entry Points |
| `self-completion` | YES | YES (Automation) | NO | In catalog, not in Entry Points |
| `session-resumption` | YES | YES (Automation) | YES (Session start) | Covered |
| `context-monitor` | YES | YES (Automation) | YES (Context overflow) | Covered |
| `receiving-code-review` | YES | YES (Code Review) | NO | In catalog, not in Entry Points |
| `requesting-code-review` | YES | YES (Code Review) | NO | In catalog, not in Entry Points |
| `sharing-skills` | YES | YES (Meta) | NO | In catalog, not in Entry Points |
| `using-superpowers` | YES | YES (Meta) | NO | In catalog, not in Entry Points |
| `writing-skills` | YES | YES (Meta) | NO | In catalog, not in Entry Points |
| `testing-skills-with-subagents` | YES | YES (Meta) | NO | In catalog, not in Entry Points |
| `testing-anti-patterns` | YES | YES (Testing & Quality) | NO | In catalog, not in Entry Points |
| `uv-package-manager` | YES | YES (Python-specific) | NO | In catalog, not in Entry Points |

**Note:** These 15 skills exist in the SKILLS_INDEX.md category tables but lack Entry Points entries. They're discoverable through category browsing but not through the primary trigger-based lookup.

---

## 5. SKILLS_INDEX.md References to Non-Existent Skills

These skills are referenced in SKILLS_INDEX.md but have no SKILL.md or even no directory:

| Skill | Directory | SKILL.md | Category in Index | Impact |
|-------|-----------|----------|-------------------|--------|
| `project-knowledge` | NO | NO | Project Knowledge | HIGH — used for "Понять проект" entry point |
| `codebase-mapping` | NO | NO | Context & Mapping | HIGH — used for new/unfamiliar projects |
| `context-capture` | NO | NO | Context & Mapping | HIGH — used for unclear requirements |
| `user-spec-planning` | NO | NO | Methodology & Planning | HIGH — used for feature planning |
| `tech-spec-planning` | NO | NO | Methodology & Planning | HIGH — follow-up to user-spec-planning |
| `project-planning` | NO | NO | Methodology & Planning | MEDIUM — new project planning |
| `user-acceptance-testing` | NO | NO | Mandatory | HIGH — required after implementation |
| `infrastructure` | NO | NO | Infrastructure & Testing | MEDIUM — CI/CD setup |
| `testing` | NO | NO | Infrastructure & Testing | MEDIUM — testing strategy |
| `methodology` | YES | NO | Methodology & Planning | MEDIUM — dir exists but SKILL.md missing |
| `skill-creator` | NO | NO | Meta | LOW — referenced in Meta category |
| `command-manager` | NO | NO | Meta | LOW — referenced in Meta category |
| `documentation` | NO | NO | Meta | LOW — referenced in Meta category |

**13 skills referenced in SKILLS_INDEX.md do not have SKILL.md files.** These are likely global/user-level skills (available via `~/.claude/skills/`) rather than project-level skills, which explains why they appear in the system prompt's skill list but not in the project's `.claude/skills/` directory.

---

## 6. CLAUDE.md Context Loading Triggers (Guides, Not Skills)

For completeness, the 8 guide triggers in CLAUDE.md's "CONTEXT LOADING TRIGGERS" section:

| Situation | Guide | File | Exists |
|-----------|-------|------|--------|
| Сложное решение, конфликт правил | decision-making | `.claude/guides/decision-making.md` | Not verified (out of scope) |
| Произошла ошибка | error-handling | `.claude/guides/error-handling.md` | Not verified |
| Нужно дать честную оценку | honesty-principles | `.claude/guides/honesty-principles.md` | Not verified |
| Проверить что можно/нельзя | constraints-reference | `.claude/guides/constraints-reference.md` | Not verified |
| Начало новой фичи | work-items | `.claude/guides/work-items.md` | Not verified |
| Нужны принципы приоритетов | principles | `.claude/guides/principles.md` | Not verified |
| Детали верификации | verification-protocol | `.claude/guides/verification-protocol.md` | Not verified |
| Справка по командам | reference | `.claude/guides/reference.md` | Not verified |

**These are guide triggers, not skill triggers.** They load `.claude/guides/*.md` files, not `.claude/skills/*/SKILL.md` files.

---

## 7. Overall Coverage Assessment

### Summary Statistics

| Metric | Value |
|--------|-------|
| Skills with SKILL.md in `.claude/skills/` | **34** |
| Skills referenced in SKILLS_INDEX.md Entry Points | **24** (primary) + **5** (secondary) |
| Entry Points skills that actually exist (SKILL.md) | **19/24** (79%) |
| Entry Points skills missing SKILL.md | **5/24** (21%) — likely global skills |
| SKILLS_INDEX.md total unique skills referenced | **47** (per its own count) |
| Skills referenced but missing from project `.claude/skills/` | **13** |
| Skills with SKILL.md but no Entry Points trigger | **15** (discoverable via categories only) |
| CLAUDE.md direct skill references | **2** (both valid) |

### Gaps and Issues

1. **STRUCTURAL: No direct skill trigger table in CLAUDE.md.** The CLAUDE.md delegates skill selection entirely to SKILLS_INDEX.md. The task's expected "Skills (invoke via Skill tool)" trigger table with 13 skills does not exist — it was removed/replaced during the progressive disclosure refactoring (commit `6356fcf`).

2. **13 PHANTOM SKILLS:** SKILLS_INDEX.md references 13 skills that don't have SKILL.md files in the project's `.claude/skills/`. These are: `project-knowledge`, `codebase-mapping`, `context-capture`, `user-spec-planning`, `tech-spec-planning`, `project-planning`, `user-acceptance-testing`, `infrastructure`, `testing`, `methodology` (dir only), `skill-creator`, `command-manager`, `documentation`. These are likely **global-level skills** installed in `~/.claude/skills/` rather than project-level skills.

3. **15 SKILLS WITHOUT ENTRY POINTS:** Skills like `defense-in-depth`, `dispatching-parallel-agents`, `root-cause-tracing`, `error-recovery`, `self-completion`, `receiving-code-review`, `requesting-code-review`, and 8 others exist with SKILL.md files but have no Entry Points trigger. They're only discoverable by browsing SKILLS_INDEX.md categories.

4. **SKILLS_INDEX INFLATED COUNT:** Claims "Total: 47 skills" but only 34 have SKILL.md files in the project. The 13 missing ones inflate the count.

5. **DESCRIPTION ALIGNMENT: 100% for existing skills.** All 19 skills that both exist in Entry Points AND have SKILL.md files show correct alignment between their trigger situations and YAML descriptions.

### Recommendations

1. **Add a KEY SKILLS summary back to CLAUDE.md** — the previous version (HEAD~1) had an 8-skill summary table that provided quick reference without requiring SKILLS_INDEX.md lookup.

2. **Mark global vs project skills in SKILLS_INDEX.md** — the 13 "missing" skills should be annotated as `(global)` so users don't look for them in `.claude/skills/`.

3. **Add Entry Points for the 15 orphaned skills** — skills like `defense-in-depth`, `dispatching-parallel-agents`, `error-recovery` etc. should have situation triggers in the Entry Points table.

4. **Fix the skill count** — update "Total: 47 skills" to reflect actual counts: 34 project-level + 13 global-level.

5. **Create methodology/SKILL.md** — the `methodology` directory exists but has no SKILL.md, making it undiscoverable via standard skill loading.
