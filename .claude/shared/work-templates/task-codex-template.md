# Task Template (Codex-Executable) — `task-codex-template.md`

> Canonical template for task-N.md files authored by Opus during task-decomposition.
> Used when a task will be executed by **Codex** (GPT-5.5 via `codex-implement.py`),
> by a **Claude** teammate (via `spawn-agent.py` + TeamCreate), or by **both in parallel**
> (via the `dual-implement` skill).
>
> Related docs:
> - Tech Spec Section 4: `work/codex-primary/tech-spec.md` (authoritative contract)
> - Sibling template: `.claude/guides/teammate-prompt-template.md` (Claude teammate prompts)
> - ADR-012: `.claude/adr/adr-012-codex-primary-implementer.md` (decision record — placeholder OK until Wave 2 lands)

---

## How to use this template

1. **Copy** this file to `work/{feature}/tasks/T{N}-{short-title}.md`
2. **Replace** every `{placeholder}` below with task-specific content
3. **Pick an executor** per the decision table below
4. **Delete** this "How to use" block from your copy (keep only the task content)

### Choosing `executor:` — claude vs codex vs dual

| executor | Pick when | Avoid when |
|---|---|---|
| `claude` | Task needs skills + memory context, ambiguous requirements, UX/frontend polish, cross-cutting refactor, or agent must read between the lines | Task is already fully specified and logic-heavy (Codex is cheaper there) |
| `codex` | Well-defined logic, isolated module, clear tests, backend/script/algorithm, bug fix with obvious contract | Requirements are ambiguous, task needs skill-based reasoning, UX judgment required |
| `dual` | High-stakes code where correctness cost >> token cost: auth, migrations, payments, crypto, complex algorithms. Opus judges both diffs and picks winner | Trivial/low-risk tasks (wastes tokens), ambiguous specs (both executors will diverge) |

### Choosing `risk_class:`
- `routine` — standard task, single executor is fine
- `high-stakes` — security/money/correctness-critical; `dual` strongly recommended

### Choosing `reasoning:`
- `high` — default for non-trivial tasks; Codex uses `model_reasoning_effort=high`
- `medium` — simple scripted changes, CRUD endpoints, docs

---

<!-- ======== COPY FROM HERE DOWNWARD INTO YOUR task-N.md ======== -->

---
executor: claude         # allowed: claude | codex | dual
risk_class: routine      # allowed: routine | high-stakes
reasoning: high          # allowed: high | medium
---

# Task T{N}: {short title}

## Your Task
{One or two paragraphs: what must be built and WHY. Reference the user-spec / tech-spec
section that motivates this task so the executor can check scope questions against it.}

## Scope Fence

**Allowed paths (may be written):**
- `{path/to/module/}`
- `{path/to/specific/file.py}`

**Forbidden paths (must NOT be modified):**
- `{path/to/tests/}`                <!-- tests are IMMUTABLE -->
- `{path/to/acceptance-criteria.md}`
- All files listed under `## Read-Only Files (Evaluation Firewall)` below

## Test Commands

<!-- One or more commands that prove the task is done. All must exit 0. -->
```bash
py -3 -m pytest {path/to/test_x.py} -v
py -3 -m mypy {path/to/src/}
```

## Acceptance Criteria (IMMUTABLE)

<!-- Measurable, testable. Do NOT edit these after task is dispatched. -->
- [ ] AC1: {observable statement — e.g., "GET /status returns 200 with `{status: ok}` JSON"}
- [ ] AC2: {...}
- [ ] All Test Commands above exit 0
- [ ] Every new/modified function has structured logging per `logging-standards` contract below

## Skill Contracts

<!--
Opus, during task-decomposition, distills skill invariants here.
The executor (Claude or Codex) reads THESE contracts, not the skill files themselves —
Codex cannot load our SKILL.md files. Keep each contract 2-5 bullets, concrete.
-->

### verification-before-completion (contract extract)
- Run every Test Command above before claiming done. If any fails → fix, do NOT claim done.
- Verify each Acceptance Criterion with evidence. Quote relevant test output in the handoff.
- If an AC is subjective ("clean code", "fast"), treat it as a hard constraint and explain how you satisfied it.

### logging-standards (contract extract)
- Every new/modified function: structured logger call at entry (with params), at exit (with result), and inside every catch block (with context).
- NO bare `print()` / `console.log()` — only `logger.info/debug/warning/error/exception`.
- NEVER log passwords, tokens, API keys, or PII.

### security-review (contract extract) [INCLUDE ONLY FOR AUTH/CRYPTO/SECRETS TASKS]
<!-- Delete this subsection if task does not touch auth, crypto, or secrets. -->
- Validate all inputs at trust boundaries (HTTP handlers, file reads, env vars).
- No secrets in code — env vars + `.gitignore`.
- Parameterize all SQL and shell commands — never string-interpolate user input.
- Run the OWASP top-10 mental checklist before claiming done.

### coding-standards (contract extract)
- Match existing style, naming, and file organization in the touched module.
- No drive-by refactors — every changed line must trace to this task's AC.
- Early returns over deep nesting; single responsibility per function.

## Read-Only Files (Evaluation Firewall)

<!-- Executors CANNOT modify these. QA audits this post-execution. -->
- All test files (`test_*`, `*.test.*`, `*.spec.*`)
- This task-N.md itself
- Acceptance criteria / user-spec / tech-spec files referenced above
- Codex review output (`.codex/reviews/*.json`)
- CI/CD pipeline configs (`.github/workflows/*`, etc.)

## Constraints

- {Project-specific compatibility, e.g., "Must not break existing `/legacy` endpoint"}
- {Performance budgets, API contracts, framework version pins}
- {Anything NOT covered by acceptance criteria but that the executor must honor}

## Handoff Output (MANDATORY)

<!--
Claude teammates output the === PHASE HANDOFF === block from teammate-prompt-template.md.
codex-implement.py automatically writes work/codex-implementations/task-{N}-result.md
in equivalent format (status, diff, test output, blockers).
Both formats are accepted by the QA reviewer and codex-gate.py.
-->

**Required fields (Claude teammate):**
```
=== PHASE HANDOFF: T{N}-{name} ===
Status: PASS | REWORK | BLOCKED
Files Modified:
- {path/to/file1}
Tests: {passed/failed/skipped counts}
Skills Invoked: {list or none}
Decisions Made: {key decision + rationale}
Learnings: {Friction / Surprise / Pattern — or NONE}
Next Phase Input: {what next agent needs to know}
=== END HANDOFF ===
```

**Required fields (Codex executor — auto-generated by codex-implement.py):**
- `status`: pass | fail | scope-violation | timeout
- unified `diff` vs baseline HEAD
- test command stdout/stderr
- any `BLOCKER:` / `NOTE:` lines from the Codex session
- timestamp
