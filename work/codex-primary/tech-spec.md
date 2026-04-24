# Tech Spec: Codex Primary Implementer

**Version:** 1.0
**Date:** 2026-04-24
**Status:** DRAFT → awaiting user approval
**Scope:** LOCAL — this project only. NOT synced to new-project template or other bot projects.

---

## 1. Goal & Non-Goals

### Goal
Make **GPT-5.5 (via Codex CLI) the primary code implementer** for well-defined tasks, while **Opus 4.7 (Claude Code) stays the planner and reviewer**. Support both:
- **Level 2**: single-task delegation to Codex (sequential or batch-parallel)
- **Level 3**: dual implementation (Claude + Codex in parallel, Opus picks winner) for high-stakes code

Preserve every existing capability:
- Agent Teams (TeamCreate) for parallel Claude work
- AO Hybrid / AO Fleet for cross-project work
- Skills injection for every Claude teammate
- Memory (activeContext, knowledge, daily logs)
- Codex as second-opinion advisor (codex-ask.py, parallel-opinion hook, watchdog)
- cross-model-review skill

### Non-Goals
- Replace Claude for planning, decomposition, ambiguous specs, UX/frontend polish (Opus's strengths per Every review)
- Remove read-only sandbox default from Codex CLI (only codex-implement.py gets workspace-write, globally it stays read-only)
- Sync changes to `.claude/shared/templates/new-project/.claude/` (future step after PoC)
- Propagate to other bot projects via fleet-sync (future step)
- Change global `~/.claude/CLAUDE.md` (global rules stay as-is; all new behavior documented in project-level CLAUDE.md for now)
- Support Codex doing **planning** — Codex only executes against iron-clad specs

---

## 2. Architectural Principles

1. **Single contract, multiple execution strategies.** `work/{feature}/tasks/task-N.md` is the only interface between planner (Opus) and executor (Codex or Claude teammate). Level 2 runs one executor; Level 3 runs two against same spec.
2. **Evaluation Firewall.** Acceptance criteria + tests in task-N.md are IMMUTABLE. Executor (Codex or Claude) cannot modify them. QA verifies this.
3. **Scope fence.** Every task-N.md declares which paths may be written. Post-execution check verifies diff stays inside fence; violation → auto-rollback + BLOCKED.
4. **Skill contract extracts.** Opus, during task-decomposition, distills relevant skill invariants (verification, logging-standards, security-review) into explicit acceptance criteria in task-N.md. Codex doesn't see our skills — it sees the extracted contract.
5. **Backward compatibility.** Existing codex-advisor stack (codex-ask, parallel-opinion, watchdog, gate) untouched; new implementer path is additive.
6. **Local blast radius.** Only this project's `.claude/` modified; sandbox write is scoped per-invocation; existing advisor hooks preserve read-only default.

---

## 3. Component Inventory

### 3.1 New Scripts

| File | Purpose | Lines (est.) |
|------|---------|--------------|
| `.claude/scripts/codex-implement.py` | Run one `codex exec` against a task-N.md; workspace-write sandbox scoped to fence; capture diff, run tests, produce task-N-result.md | ~300 |
| `.claude/scripts/codex-wave.py` | Spawn N `codex-implement.py` processes in parallel, each inside its own git worktree. Monitors, aggregates results. | ~200 |
| `.claude/scripts/codex-scope-check.py` | Utility: given a diff and a scope fence, verify every modified path is inside fence. Exit 0 pass, 2 fail. | ~80 |

### 3.2 Modified Scripts / Hooks

| File | Change | Reason |
|------|--------|--------|
| `.claude/hooks/codex-gate.py` | Accept `work/codex-implementations/task-*-result.md` (< 3 min old, `status=ok`) as fresh opinion that unblocks subsequent Claude Edits targeting files in that task's scope fence | After Codex produces code, Claude should be able to refine it without re-running codex-ask.py for every hand-edit |

### 3.3 New Phase-Mode Docs

| File | Phase Mode | Description |
|------|-----------|-------------|
| `.claude/shared/work-templates/phases/IMPLEMENT-CODEX.md` | `CODEX_IMPLEMENT` | All tasks delegated to Codex. Good for logic-heavy, well-specified work. |
| `.claude/shared/work-templates/phases/IMPLEMENT-HYBRID.md` | `HYBRID_TEAMS` | Per-task `executor` hint in task-N.md; Opus dispatches each task to best executor. |
| `.claude/shared/work-templates/phases/DUAL-IMPLEMENT.md` | `DUAL_IMPLEMENT` | Every task runs both Claude + Codex in parallel worktrees; Opus judges diffs. |

### 3.4 New Templates / Skills

| File | Purpose |
|------|---------|
| `.claude/shared/work-templates/task-codex-template.md` | Extension of task-N.md format with Executor Hint, Scope Fence, Test Commands, Skill Contracts, Acceptance Criteria (IMMUTABLE) sections |
| `.claude/skills/dual-implement/SKILL.md` | Level 3 opt-in skill — triggers when task has `executor: dual` or high-stakes risk class |
| `.claude/adr/adr-012-codex-primary-implementer.md` | Architectural decision record |

### 3.5 Project-Level Documentation

| File | Change |
|------|--------|
| Project `CLAUDE.md` (root) | Add "Codex Primary Implementer (experimental, local)" section explaining the three phase modes + when to use each |
| `.claude/guides/codex-integration.md` | Add "Codex as Primary Implementer" subsection covering codex-implement.py, codex-wave.py, dual-implement skill, and integration with Agent Teams |

---

## 4. task-N.md Extended Contract

Current `task-N.md` (from task-decomposition skill) has: Your Task / Acceptance Criteria / Constraints / Read-Only Files.

**New required sections for Codex-executable tasks:**

```markdown
---
executor: claude | codex | dual        # Opus writes this during decomposition
risk_class: routine | high-stakes      # high-stakes → dual recommended
reasoning: high | medium               # override for codex-implement if not "high"
---

# Task T{N}: {short title}

## Your Task
{narrative description — what and why}

## Scope Fence
**Allowed paths (may be written):**
- path/to/dir1/
- path/to/specific/file2.py

**Forbidden paths (must NOT be modified):**
- path/to/tests/
- path/to/acceptance-criteria.md
- (+ default: all files listed in Read-Only Files below)

## Test Commands (run after implementation)
```bash
py -3 -m pytest path/to/test_x.py -v
py -3 -m mypy path/to/src/
```

## Acceptance Criteria (IMMUTABLE)
- [ ] AC1: {measurable, testable statement}
- [ ] AC2: {...}
- [ ] All Test Commands above exit 0
- [ ] Every new/modified function has structured logging per logging-standards contract below

## Skill Contracts (Opus extracted these from skills)

### verification-before-completion (contract extract)
- Before claiming done, run every Test Command above. If any fails, DO NOT claim done.
- Verify each AC with evidence. Quote test output when reporting.
- If acceptance criterion is subjective ("clean code"), treat it as a hard constraint, not a suggestion.

### logging-standards (contract extract)
- Every new function: structured logger call at entry (with params) + exit (with result) + every catch block (with context)
- NO bare `print()` / `console.log()` — only `logger.info/debug/warning/error/exception`
- Do NOT log passwords, tokens, API keys, PII.

### security-review (contract extract) [only if task touches auth/crypto/secrets]
- Validate all inputs at boundaries
- Never commit secrets; use env vars + .gitignore
- For SQL/shell: parameterize, don't interpolate
- Check OWASP top 10 patterns

## Read-Only Files (Evaluation Firewall)
- All test files (test_*, *.test.*, *.spec.*)
- Acceptance criteria files
- This task-N.md itself

## Constraints
{project-specific compatibility, API contracts, etc.}

## Handoff Output (MANDATORY)
Codex-implement.py writes a standardized result file:
`work/codex-implementations/task-{N}-result.md`
containing: status, diff, test output, self-reported blockers.
Claude teammates write the HANDOFF block from teammate-prompt-template.md.
```

---

## 5. Phase Modes (new)

### 5.1 `CODEX_IMPLEMENT`
- **Trigger:** all tasks in the phase have `executor: codex` or are routine logic with clear tests
- **Dispatch:** pipeline runs `codex-wave.py --tasks tasks/T*.md --parallel 3` (configurable)
- **Claude's role:** write spec (before), review diff + merge (after)
- **Use when:** well-defined tasks, logic-heavy, isolated modules, bug fixes, refactors
- **Do NOT use:** UX/frontend polish, ambiguous requirements, cross-cutting refactors that need "reading between lines"

### 5.2 `HYBRID_TEAMS` (most elegant; default recommendation)
- **Trigger:** tasks have mixed `executor:` hints; Opus judges per-task
- **Dispatch:** pipeline loops through tasks:
  - `executor: claude` → `TeamCreate` + Claude teammate (existing Agent Teams flow)
  - `executor: codex` → `codex-implement.py --task tasks/TN.md --worktree <path>`
  - `executor: dual` → invoke `dual-implement` skill for that task
- **Parallelism:** Claude teammates parallelize via TeamCreate; Codex sessions parallelize via background processes spawned by codex-wave.py
- **Claude's role:** plan, decompose (pick executor per task), orchestrate, review
- **Use when:** most projects; gives Opus flexibility to match each task to best executor

### 5.3 `DUAL_IMPLEMENT`
- **Trigger:** entire phase is high-stakes (all tasks `executor: dual`), or explicit pipeline override
- **Dispatch:** each task spawns TWO parallel executors — a Claude teammate in worktree A, codex-implement in worktree B
- **Judging:** Opus (or a spawned judge-agent with cross-model-review skill) compares diffs; picks or merges best
- **Use when:** auth, migrations, payments, crypto, complex algorithms where correctness cost dominates token cost

### 5.4 Relationship to existing modes
- `AGENT_TEAMS` (Claude-only parallel) — unchanged, remains primary for tasks requiring skills + memory context
- `AO_HYBRID` — unchanged, remains for full-Claude-context parallel within one project
- `AO_FLEET` — unchanged, remains for cross-project work
- New modes sit alongside; Opus picks per-phase

---

## 6. codex-implement.py Design

### 6.1 CLI
```bash
py -3 .claude/scripts/codex-implement.py \
    --task work/codex-primary/tasks/T1.md \
    --worktree .                              # or path to worktree dir
    [--reasoning high]                        # overrides task frontmatter
    [--timeout 3600]                          # seconds
    [--result-dir work/codex-implementations] # output dir
```

### 6.2 Behavior
1. **Parse** task-N.md frontmatter (executor, risk_class, reasoning) + extract sections (Scope Fence, Test Commands, Acceptance Criteria, Skill Contracts)
2. **Pre-flight**:
   - Verify cwd is inside worktree (or `.` = project root)
   - Verify git tree is clean (or warn)
   - Record HEAD sha as baseline
3. **Build prompt** for Codex:
   - Full task-N.md content
   - Explicit "Write code to satisfy acceptance criteria. Do NOT modify files in Forbidden Paths or Read-Only Files. Run Test Commands. Report result."
   - Append `AGENTS.md`/`CLAUDE.md` hint (Codex reads these automatically via project_doc fallback)
4. **Execute**:
   ```
   codex exec \
       --model gpt-5.5 \
       --sandbox workspace-write \
       --full-auto \
       --cd <worktree-abs-path> \
       --profile implementer \      # optional — see 6.5
       -- "<prompt>"
   ```
5. **Post-flight**:
   - `git diff HEAD` → capture full diff
   - `codex-scope-check.py --diff <diff> --fence <fence>` → verify in-scope
   - If out-of-scope → `git reset --hard HEAD` (rollback), exit 2, mark FAIL
   - If in-scope → run Test Commands, capture output
6. **Write result**: `work/codex-implementations/task-{N}-result.md` with:
   - status: pass | fail | scope-violation | timeout
   - diff (unified)
   - test output (stdout + stderr)
   - Codex self-report (any `BLOCKER:` / `NOTE:` lines from its exec output)
   - timestamp
7. **Exit code**: 0 = tests pass, 1 = tests fail but scope ok, 2 = scope violation or timeout

### 6.3 Error Handling
- **Codex process hang** → kill after timeout, rollback, exit 2
- **Scope violation** → rollback, exit 2 (Opus will see in result.md)
- **Test failure** → do NOT rollback (Opus can see diff + test output, decide whether to keep-and-fix or reset)
- **codex exec non-zero** → treat as failure; capture stderr

### 6.4 Logging (meta — codex-implement.py itself)
Per logging-standards: structured entry/exit/error logs for every function. Log goes to `work/codex-primary/logs/codex-implement-T{N}.log`.

### 6.5 Optional Profile
`~/.codex/profiles/implementer.toml` (NOT part of this pipeline — can be added post-PoC):
```toml
sandbox = "workspace-write"
approval_policy = "never"
model_reasoning_effort = "high"
```
If present, `--profile implementer` uses it.

---

## 7. codex-wave.py Design

### 7.1 CLI
```bash
py -3 .claude/scripts/codex-wave.py \
    --tasks work/codex-primary/tasks/T1.md,T2.md,T3.md \
    --parallel 3 \
    --worktree-base worktrees/codex-wave \
    [--timeout-per-task 3600]
```

### 7.2 Behavior
1. For each task: create git worktree at `worktrees/codex-wave/T{N}/` from base branch
2. Spawn up to `--parallel` concurrent processes, each running `codex-implement.py --task T{N}.md --worktree worktrees/codex-wave/T{N}`
3. Monitor via background process tracking
4. As each finishes: collect result.md, record in wave-results.md
5. After all finish: write aggregate report `work/codex-primary/codex-wave-report.md`
6. Does NOT merge worktree branches — Opus does that sequentially

### 7.3 Why this design
- Parallelism is real (multiple Codex CLIs simultaneously)
- Each task isolated in own worktree → no file conflicts
- Opus orchestrates merge (same pattern as AO Hybrid)
- Failures in one task don't block others

### 7.4 Parallelism limits
- Default `--parallel 3` (conservative; can be raised after validation)
- User tariff: $20 Codex — if rate-limited, wave retries with smaller parallelism
- Semaphore in codex-wave.py respects limit

---

## 8. codex-scope-check.py Design

Tiny utility script. Given:
- `--diff <file | -` (unified diff or `git diff HEAD` output)
- `--fence <comma-separated paths | fence-file>`

Parse diff headers (`diff --git a/... b/...`) → extract modified paths.
For each path: check it's under at least one allowed fence path AND not under any forbidden path.
Exit 0 = all paths in fence; exit 2 = violation. Stdout reports which paths violated.

Used both by codex-implement.py (post-flight) and by QA_REVIEW phase (retrospective audit).

---

## 9. codex-gate.py Update

### 9.1 Current behavior
Checks if codex opinion file is younger than 3 minutes; blocks Claude Edits otherwise.

### 9.2 New behavior
ALSO accept `work/codex-implementations/task-{N}-result.md` as valid opinion IF:
- File exists and is younger than 3 minutes
- `status: pass` in the result
- The file being edited by Claude is inside the task's Scope Fence

When Claude hand-edits a Codex-produced file (e.g., to fix a small issue or merge results), gate doesn't block unnecessarily.

### 9.3 Safety
Original behavior preserved as fallback — if no fresh codex-implement result exists, old codex-ask.py check runs.

---

## 10. dual-implement Skill (Level 3)

### 10.1 SKILL.md skeleton
```yaml
---
name: dual-implement
description: Parallel dual implementation for high-stakes code. Claude teammate and Codex (GPT-5.5) implement the same task-N.md in parallel worktrees. Opus judges diffs and picks or merges winner. Use when task has executor: dual or risk_class: high-stakes (auth, migration, payment, crypto, complex algorithms). Do NOT use for UI polish, routine refactors, or when Level 2 single execution is adequate.
roles: [implementer, reviewer]
---
```

### 10.2 Protocol
1. Ensure task-N.md has `executor: dual` or explicit trigger
2. Create two worktrees:
   - `worktrees/dual-task-N/claude/` (base branch)
   - `worktrees/dual-task-N/codex/` (base branch)
3. Spawn in parallel:
   - `TeamCreate` + Claude teammate prompt (per teammate-prompt-template.md) → implements in claude worktree
   - `codex-implement.py --task T{N}.md --worktree worktrees/dual-task-N/codex/` → implements in codex worktree
4. Wait for both (timeout protection)
5. Spawn judge: Claude subagent with `cross-model-review` skill, loaded with both diffs + task-N.md spec
6. Judge reports: `pick_a | pick_b | merge_hybrid | both_fail`
7. Action:
   - `pick_a` → merge claude branch, archive codex
   - `pick_b` → merge codex branch, archive claude
   - `merge_hybrid` → human intervention (Opus does manual cherry-pick)
   - `both_fail` → BLOCKED, escalate

### 10.3 When not to use
- Task is trivial / well-tested / low-risk — dual wastes tokens
- Ambiguous spec — both executors will diverge unhelpfully; fix spec first
- Token budget tight — single execution is cheaper

---

## 11. Agent Teams Preservation (critical)

User requirement: Agent Teams must keep working, every Claude teammate must keep calling codex-ask / cross-model-review / skills.

### 11.1 What does NOT change
- `TeamCreate` + `spawn-agent.py` flow — 100% unchanged
- Every Claude teammate prompt still has `## Required Skills` section with FULL skill content
- Every Claude teammate still has `## Codex Second Opinion (MANDATORY)` section calling codex-ask.py
- Existing advisor hooks (codex-parallel, codex-watchdog, codex-broker, codex-review, codex-stop-opinion) — untouched
- Memory injection, Results Board, handoff template — all as-is

### 11.2 What's added (orthogonally)
- New category of "teammate": Codex implementer spawned by codex-wave.py, NOT by TeamCreate
- Claude teammates CAN themselves spawn Codex via codex-implement.py (teammate is Opus-level agent, can delegate subtask)
- In HYBRID_TEAMS mode, one phase can contain both Claude teammates AND Codex sessions running in parallel
- Handoff block format is universal: Claude writes it per template, codex-implement.py emits equivalent format in task-N-result.md

### 11.3 Codex running parallel for speedup
User requirement: "может быть, нам нужно придумать, что-то похожее с кодексом, чтобы кодекс в том числе мог параллельно работать, для ускорения процесса".

Answer: `codex-wave.py` IS exactly this. It spawns N parallel Codex CLI processes (each in own git worktree), so 3 independent tasks finish in ~1× time instead of 3×. Analogous to TeamCreate for Claude but for Codex.

---

## 12. Skill Contract Extractors

When Opus runs task-decomposition for a Codex-bound task, it must inject skill invariants into task-N.md's **Skill Contracts** section.

### 12.1 Initial extractor mapping (manual, not automated in this pipeline)
| Skill | What Opus extracts into task-N.md |
|-------|-----------------------------------|
| verification-before-completion | "Run every Test Command. Verify each AC with evidence. Quote test output." |
| logging-standards | "Every new/modified function: structured logger entry/exit/error. No bare print/console.log. No sensitive data in logs." |
| security-review | (only for auth/crypto/secrets tasks) "Validate all inputs. No secrets in code. Parameterize SQL. OWASP top 10 check." |
| coding-standards | "Follow existing style. Match naming conventions. No drive-by refactors." |
| tdd-workflow | (only if task is TDD-style) "Tests first, RED→GREEN→REFACTOR. Coverage ≥ 80%." |

### 12.2 Future automation (out of scope for this pipeline)
A `skill-contract-extractor.py` script could auto-generate these extracts. For v1, Opus does it manually during task-decomposition.

---

## 13. Integration Points

### 13.1 PIPELINE.md Phase declarations
After v1 ships, future PIPELINE.md files can declare:
```markdown
### Phase: IMPLEMENT
- Mode: CODEX_IMPLEMENT | HYBRID_TEAMS | DUAL_IMPLEMENT
```
and the phase template has explicit instructions for each. Existing `AGENT_TEAMS` mode remains default recommendation.

### 13.2 task-decomposition skill
Extended (in Wave 2 via project CLAUDE.md note, not direct skill edit — avoid breaking global skill) to mention:
- Add frontmatter `executor:` to each task
- Add Scope Fence section
- Add Skill Contracts section
- Add Test Commands section

The global skill body stays unchanged; project CLAUDE.md explains the extension.

### 13.3 qa-validation-loop skill
Reviewer reads `task-N-result.md` the same way as any Claude teammate handoff. No skill modification needed.

### 13.4 cross-model-review skill
Stays primary tool for Opus-as-judge in DUAL_IMPLEMENT path. No modification needed.

---

## 14. Acceptance Criteria (pipeline-level)

### 14.1 Wave 1 acceptance (IMMUTABLE)
- [ ] codex-implement.py runs end-to-end on a synthetic task (tests pass, diff in fence, result.md written)
- [ ] codex-wave.py spawns 2 parallel codex-implement.py with isolated worktrees, both finish, aggregate report written
- [ ] codex-scope-check.py correctly rejects out-of-fence diff in synthetic test
- [ ] Phase mode docs complete and internally consistent (no TODO markers)
- [ ] task-codex-template.md contains all required sections
- [ ] codex-gate.py updated with unit test for result.md-as-opinion logic; old behavior preserved as fallback

### 14.2 Wave 2 acceptance (IMMUTABLE)
- [ ] dual-implement SKILL.md valid frontmatter (name, description ≤ 300 chars with Use when / Do NOT use, roles)
- [ ] SKILL.md includes Protocol + Examples sections
- [ ] ADR-012 follows .claude/adr/_template.md format
- [ ] Project CLAUDE.md has new section "Codex Primary Implementer (Experimental, Local)" with clear SCOPE notice

### 14.3 QA_REVIEW acceptance
- [ ] Zero CRITICAL findings
- [ ] Zero IMPORTANT findings unresolved
- [ ] Every new function has structured logging (per logging-standards)
- [ ] Evaluation Firewall respected (no executor touched tests or task-N.md)

### 14.4 PROOF_OF_CONCEPT acceptance (USER_APPROVAL)
- [ ] One real tiny task executed through codex-implement.py end-to-end; tests pass
- [ ] One task executed via dual-implement skill; Opus picks winner correctly; both diffs archived
- [ ] codex-gate.py correctly allows subsequent Claude edits within scope fence
- [ ] Total runtime measurement: does parallel wave actually deliver speedup vs sequential?
- [ ] User visually confirms quality of Codex-produced code

### 14.5 DOCUMENT acceptance
- [ ] codex-integration.md has new section covering all new scripts + phase modes + dual-implement skill
- [ ] knowledge.md has new Pattern entry (e.g., "Codex Primary Implementer for Well-Defined Tasks")
- [ ] activeContext.md reflects feature DONE state
- [ ] PIPELINE.md Status: PIPELINE_COMPLETE

---

## 15. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Codex rate-limits on $20 tariff when running parallel waves | Medium | Medium | codex-wave.py default `--parallel 3` (not 10); retry with `--parallel 1` on rate-limit; user can upgrade tariff later |
| Scope fence bypass via path traversal (`../..`) | Low | High | codex-scope-check.py normalizes paths with `os.path.realpath` before comparing |
| Codex produces code without logging | Medium | Medium | Skill Contracts section in task-N.md explicit; QA reviewer checks grep for logger calls |
| codex-gate.py regression (blocks when it shouldn't) | Medium | Low | Unit test for gate; fallback to old behavior preserved |
| Worktree leaks (not cleaned up on error) | Medium | Low | codex-wave.py has cleanup on exit; `ao-hybrid.sh cleanup` pattern applicable |
| Global skill or template file accidentally modified | Low | High | Scope Fence in PIPELINE.md explicit; QA_REVIEW checks `.claude/shared/templates/new-project/` untouched |
| Dual-implement judge picks wrong winner | Medium | Medium | Judge must cite evidence; both diffs archived; user can override |
| Claude teammate tries to spawn codex-implement but cwd wrong | Low | Medium | codex-implement.py pre-flight checks cwd; explicit error on mismatch |

---

## 16. Rollback Plan

Each wave commits separately with checkpoint tag. If PoC fails:
- `git reset --hard pipeline-checkpoint-PLAN` → abandons all implementation
- Advisor stack untouched → still functional
- activeContext.md notes failure + reason
- No cleanup needed in `.claude/shared/templates/new-project/` because we never wrote there

---

## 17. Out of Scope (future work)

1. Syncing all artifacts to `.claude/shared/templates/new-project/.claude/`
2. Fleet-syncing to other bot projects
3. Auto-skill-contract extractor script
4. Codex profile file `~/.codex/profiles/implementer.toml` (optional convenience)
5. UI/dashboard for tracking parallel Codex sessions
6. Token/cost tracking per codex-implement invocation
7. Auto-judge for dual-implement (currently Opus judges; could be meta-model)
8. Codex running Claude-style skills autonomously (requires separate skill-loader for Codex context)
