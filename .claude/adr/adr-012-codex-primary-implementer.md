# ADR-012: Codex Primary Implementer (Experimental, Local)

**Date:** 2026-04-24
**Status:** ACCEPTED
**Scope:** LOCAL — this project only. Not propagated to `.claude/shared/templates/new-project/` or other bot projects until a successful PoC.

---

## Context

Recent evidence indicated that GPT-5.5, accessed via Codex CLI, writes better code than Opus 4.7 on well-specified, logic-heavy tasks:

- Every's review (2026-04) concluded that GPT-5.5 produces tighter, more correct code on routine implementation tasks and handles long debugging sessions without losing thread.
- Terminal-Bench 2.0 scored GPT-5.5 at **82.7%** on agentic coding flows, ahead of peer frontier models.
- SWE-Bench Pro scored GPT-5.5 at **58.6%** versus Opus 4.7 at **53.4%** on real-world repo patches.

At the same time, Opus 4.7 remained stronger at:

- Planning, decomposition, and ambiguous spec interpretation
- UX / frontend polish and taste-driven decisions
- Long-horizon orchestration (Agent Teams, pipelines, AO Hybrid / Fleet)
- Reading between the lines when the spec is vague

The project already had a substantial Opus-side infrastructure: `TeamCreate` Agent Teams, skills (verification-before-completion, logging-standards, security-review), memory (activeContext / knowledge / daily logs), and a Codex advisor stack (codex-ask.py, parallel-opinion hook, watchdog). Codex appeared in that stack only as a **second-opinion advisor** running in read-only sandbox; it never wrote code.

The question was: how do we put the coding lead of GPT-5.5 to work **without** sacrificing Opus's planning strength, the Agent Teams infrastructure, the skill contracts, or the memory system that makes Claude teammates reliable?

A direct GPT-5.5 API doesn't exist at the time of this decision, so full migration is infeasible; the only route is Codex CLI, which brings its own constraints (workspace-write sandbox scoping, no direct access to our skill bodies, $20 user tariff).

---

## Decision

Adopt a **planner / executor split**:

- **Opus 4.7 = planner + reviewer.** Writes the spec (task-N.md with Scope Fence, Acceptance Criteria IMMUTABLE, Test Commands, Skill Contracts), orchestrates, judges diffs.
- **Codex (GPT-5.5) = executor.** Runs inside a scoped workspace-write sandbox against the spec, emits a result artifact, never sees or modifies the spec.

Three new implementation scripts, three new phase modes, one new opt-in skill:

**Scripts** (under `.claude/scripts/`):
- `codex-implement.py` — single-task Codex execution against one `task-N.md`, with post-flight scope check, test run, and structured result.
- `codex-wave.py` — spawns N parallel `codex-implement.py` processes, each in its own git worktree; aggregates results.
- `codex-scope-check.py` — utility: verifies every path in a diff stays inside the task's declared Scope Fence.

**Phase modes** (under `.claude/shared/work-templates/phases/`):
- `CODEX_IMPLEMENT` (IMPLEMENT-CODEX.md) — whole phase delegated to Codex wave; good for routine, logic-heavy, well-specified work.
- `HYBRID_TEAMS` (IMPLEMENT-HYBRID.md) — per-task `executor:` hint (`claude` | `codex` | `dual`) in task-N.md; Opus dispatches each task to the best executor. Default recommendation.
- `DUAL_IMPLEMENT` (DUAL-IMPLEMENT.md) — every task runs both a Claude teammate and Codex in parallel worktrees; Opus judges diffs. For high-stakes code (auth, migrations, payments, crypto, hard algorithms).

**Skill** (opt-in, Level 3):
- `.claude/skills/dual-implement/SKILL.md` — triggers when a task has `executor: dual` or risk_class `high-stakes`. Orchestrates the parallel Claude + Codex worktrees and the judge step.

**Single contract.** `task-N.md` remains the one interface between planner and any executor. It gains required sections: `executor:` / `risk_class:` / `reasoning:` frontmatter, Scope Fence, Test Commands, Acceptance Criteria (IMMUTABLE), Skill Contracts (Opus-extracted summaries), Read-Only Files (Evaluation Firewall). Claude teammates and Codex sessions both consume the same file.

**Scope: LOCAL only.** Changes land inside this project's `.claude/` tree. The advisor stack (codex-ask, parallel-opinion, watchdog, gate, review) is preserved unchanged. No edits to `~/.claude/CLAUDE.md`, to the new-project template, or to other bot projects until a PoC proves value.

---

## Rationale

- GPT-5.5 has a measurable lead on routine coding; ignoring it costs code quality and speed on tasks where Opus's planning premium isn't needed.
- Opus's planning + memory infrastructure is the actual moat; swapping it out for a pure Codex pipeline would lose more than it gains.
- A single IMMUTABLE contract (task-N.md) lets us swap executors without touching the planner or the QA reviewer — both read the same artifact.
- Scope Fence + post-flight scope check are the blast-radius control for workspace-write sandbox: a Codex session that writes outside its fence is auto-rolled back.
- Skill Contracts (Opus extracts invariants into task-N.md) are the bridge for an executor that can't load our skill bodies directly. Logging, verification, security checklist all become explicit acceptance criteria.
- LOCAL scope keeps blast radius contained; if the PoC fails, `git reset --hard pipeline-checkpoint-PLAN` unwinds everything and the advisor stack is untouched.

---

## Alternatives Considered

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| (a) Full role swap — Codex does everything (plan + execute + review) | Maximal use of GPT-5.5's coding lead; one tool to configure | Loses Opus's planning strength; loses Agent Teams / memory / skills infrastructure; no GPT-5.5 API available (Codex CLI only); ambiguous specs handled worse | Throws away the planner moat; no API to build a proper orchestrator against |
| (b) Model upgrade only — keep Codex as advisor, just switch its model to 5.5 | Zero architectural change; smallest blast radius | Doesn't exploit coding lead at all — Codex stays read-only; advisor was never the bottleneck | Under-uses the evidence; changes nothing about who writes code |
| (c) Task-class routing only — reuse `session-task-class.py` to pick model per task, no executor split | Minimal new code; piggy-backs on existing infrastructure | Routing granularity is too coarse — per-session, not per-task; no scope fence enforcement; no parallelism primitive for Codex | Doesn't give Opus the per-task dispatch control we need; no isolation when things go wrong |
| (d) Status quo — keep Opus as primary, Codex as advisor only | Zero risk; zero new code | Forgoes the measured coding lead on the exact tasks where it matters most; every routine task stays as expensive as a non-routine one | Misses the opportunity entirely; the benchmarks and review evidence are load-bearing |

---

## Consequences

### Positive
- **Speed on routine tasks.** `codex-wave.py` runs N parallel Codex sessions in isolated worktrees — 3 independent tasks finish in ~1× time instead of 3×.
- **Better code quality on logic-heavy work.** GPT-5.5's Terminal-Bench / SWE-Bench lead translates directly to fewer reviewer rewrites on routine tasks.
- **Agent Teams preserved.** `TeamCreate`, `spawn-agent.py`, skill injection, memory, Results Board, handoff template — all unchanged. New executor path is additive.
- **Clear division of labor.** Opus does what it's best at (plan, decompose, judge); Codex does what it's best at (execute against iron-clad spec).
- **Auditable contract.** task-N.md is the single source of truth for both executors; QA reads the same file regardless of who wrote the code.
- **Reversible.** Scope is LOCAL; rollback is `git reset --hard pipeline-checkpoint-PLAN`.

### Negative
- **Workspace-write sandbox risk.** Codex gets write permission inside the fence. Mitigated by `codex-scope-check.py` on every invocation + auto-rollback on violation; the sandbox default for advisor flows stays read-only.
- **Codex doesn't see skills directly.** Skill bodies aren't loaded into Codex context. Mitigated by Skill Contracts (Opus extracts invariants into task-N.md), but adds a manual step during task-decomposition and a risk of under-specification.
- **$20 Codex tariff limits parallel wave width.** Default `codex-wave.py --parallel 3` is conservative; rate-limit fallback retries with `--parallel 1`. Heavier parallelism requires a paid tariff upgrade.
- **Complexity surface.** Three phase modes + new scripts + new skill = more for a future reader to understand. Mitigated by documenting in project CLAUDE.md and codex-integration.md, and by the clear LOCAL scope.
- **Evaluation Firewall dependency.** The whole design rests on the reviewer (and the gate hook) enforcing that executors never touch tests or task-N.md. A single leak here silently invalidates all correctness guarantees.

### Trade-offs
- More moving parts today in exchange for a faster, higher-quality implementation loop on routine tasks.
- A narrower sandbox (per-task fence) in exchange for letting a second model write code at all.
- A bigger planning investment (extract skill contracts, define fence) in exchange for executor agnosticism at implementation time.

---

## Implementation Notes

- **Tech spec (authoritative design):** `work/codex-primary/tech-spec.md`
- **Phase mode docs:**
  - `.claude/shared/work-templates/phases/IMPLEMENT-CODEX.md`
  - `.claude/shared/work-templates/phases/IMPLEMENT-HYBRID.md`
  - `.claude/shared/work-templates/phases/DUAL-IMPLEMENT.md`
- **Scripts:**
  - `.claude/scripts/codex-implement.py`
  - `.claude/scripts/codex-wave.py`
  - `.claude/scripts/codex-scope-check.py`
- **Opt-in skill (Level 3):** `.claude/skills/dual-implement/SKILL.md`
- **Gate hook update:** `.claude/hooks/codex-gate.py` — accepts `work/codex-implementations/task-*-result.md` as a fresh opinion when the edit target is inside that task's fence. Old behavior preserved as fallback.
- **Preserved unchanged:** `codex-ask.py`, parallel-opinion hook, watchdog, review hook, `cross-model-review` skill, all Agent Teams flows, all memory files.

---

## For AI Agents

- **Before changing:** Read `work/codex-primary/tech-spec.md` for the authoritative design. Confirm the change is inside LOCAL scope — do not propagate to `.claude/shared/templates/new-project/` or other projects without an explicit PoC approval step.
- **If proposing an alternative:** State which rejected alternative (a/b/c/d above) you are reviving and what new evidence justifies it; or describe a genuinely new option and its trade-offs.
- **When dispatching a task:** Check `executor:` in task-N.md frontmatter. `claude` → normal Agent Teams flow. `codex` → `codex-implement.py`. `dual` → dual-implement skill. Never execute without a Scope Fence section.
- **When reviewing a Codex result:** Read `work/codex-implementations/task-{N}-result.md`. Verify `status: pass`, verify diff stayed inside fence (re-run `codex-scope-check.py` if in doubt), verify all Test Commands ran.
- **Scope invariants:** The advisor stack is off-limits to this ADR's changes. Never let an executor modify test files, task-N.md, or files in Read-Only Files. Never extend workspace-write outside the declared fence.
- **Future-work gate:** Global propagation (new-project template, other bot projects) is contingent on a successful PoC. Do not pre-emptively sync.
- **Related files:** `work/codex-primary/tech-spec.md`, the three phase-mode docs, `.claude/skills/dual-implement/SKILL.md`, `.claude/guides/codex-integration.md`, project `CLAUDE.md`.
