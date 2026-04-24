# Waves — Codex Primary Implementer Pipeline

## Dependency Graph (DAG)

```
                          [ PLAN complete ]
                                 │
        ┌──────┬──────┬──────┬───┴───┬──────┐
        ▼      ▼      ▼      ▼       ▼      ▼
       T1     T2     T3     T4      T5   (Wave 1 — 5 parallel teammates)
       │      │      │      │       │
       └──────┴──────┴──┬───┴───────┘
                        ▼
                [ Wave 1 gate: all PASS ]
                        │
              ┌─────────┼─────────┐
              ▼         ▼         ▼
             T6        T7        T8   (Wave 2 — 3 parallel teammates)
              │         │         │
              └─────────┼─────────┘
                        ▼
                [ Wave 2 gate: all PASS ]
                        │
                        ▼
                  [ QA_REVIEW ]
                        │
                        ▼
                [ PROOF_OF_CONCEPT ]
                        │
                        ▼
                   [ DOCUMENT ]
                        │
                        ▼
                [ PIPELINE_COMPLETE ]
```

## Wave 1 — Foundations (all parallel)

Contract: every task in Wave 1 is independent. Each operates on its own scope fence. No task reads another's output. The coordination contract is `tech-spec.md` — which is IMMUTABLE during Wave 1.

| Task | File created/modified | Scope Fence | Depends on |
|------|----------------------|-------------|------------|
| **T1** | `.claude/scripts/codex-implement.py` + unit test | `.claude/scripts/codex-implement.py`, `test_codex_implement.py` | tech-spec only |
| **T2** | `.claude/scripts/codex-wave.py` + `codex-scope-check.py` + tests | `.claude/scripts/codex-wave.py`, `codex-scope-check.py`, tests | tech-spec only |
| **T3** | 3 phase-mode docs in `.claude/shared/work-templates/phases/` | those 3 new md files | tech-spec only |
| **T4** | `.claude/shared/work-templates/task-codex-template.md` | that single file | tech-spec only |
| **T5** | `.claude/hooks/codex-gate.py` (modify) + unit test | codex-gate.py + test_codex_gate.py | tech-spec only (knows T1's result.md schema from spec) |

**Parallelism:** 5 teammates simultaneously. Each in main project worktree (scope fences don't overlap, so no file conflict risk). No git worktree isolation needed for Wave 1 (unlike full AO Hybrid) because Scope Fences are strictly disjoint.

**Wave 1 gate criteria:**
- All 5 handoff blocks report `Status: PASS`
- Every unit test from every task file exits 0
- `codex-scope-check.py` (new from T2) successfully rejects a synthetic out-of-fence diff
- `git diff` shows only files inside the union of all 5 Scope Fences; no surprise modifications

## Wave 2 — Skills, ADR, Docs (all parallel)

Contract: all tasks in Wave 2 reference Wave 1 outputs but don't modify them. Each produces documentation / skills / ADR — no further code changes.

| Task | File created/modified | Scope Fence | Depends on |
|------|----------------------|-------------|------------|
| **T6** | `.claude/skills/dual-implement/SKILL.md` (+ optional refs) | `.claude/skills/dual-implement/**` | T1, T2 (the skill calls them — by reference) |
| **T7** | `.claude/adr/adr-012-codex-primary-implementer.md` | that file only | tech-spec |
| **T8** | Project `CLAUDE.md` (append section) | `CLAUDE.md` only | tech-spec, T1-T7 names (for references) |

**Parallelism:** 3 teammates simultaneously.

**Wave 2 gate criteria:**
- All 3 handoff blocks report `Status: PASS`
- dual-implement SKILL.md valid frontmatter; body passes skill-conductor checklist
- ADR-012 follows `_template.md`
- Project CLAUDE.md: only additive changes (verify via `git diff`)

## QA_REVIEW

Sequential after both waves. One qa-reviewer agent reviews all changes against tech-spec acceptance criteria + scope fence integrity. If any CRITICAL/IMPORTANT finding, qa-fixer agent fixes; then re-review. Max 3 cycles.

## PROOF_OF_CONCEPT

Single-operator phase. Opus picks a real tiny task (suggestion: trivial fix somewhere in `.claude/scripts/`, like improving a `--help` message or adding a missing type hint). Writes it as task-PoC.md with executor: codex. Runs `codex-implement.py --task tasks/PoC.md` end-to-end. Captures result.md. Then runs same task via dual-implement skill; captures both diffs; verifies judge works.

User reviews PoC outcome and approves quality.

## DOCUMENT

Final sequential phase. Opus updates:
- `.claude/guides/codex-integration.md` — new "Codex as Primary Implementer" section
- `.claude/memory/knowledge.md` — new pattern
- `.claude/memory/activeContext.md` — mark DONE
- `work/codex-primary/PIPELINE.md` — Status: PIPELINE_COMPLETE

## Key Integrity Invariants (checked by QA_REVIEW)

1. Scope Fence union exactly matches PIPELINE.md Scope Fence — no file outside that set was modified.
2. `.claude/shared/templates/new-project/**` untouched.
3. Global `~/.claude/CLAUDE.md` untouched.
4. Existing advisor hooks (codex-ask, codex-parallel, codex-watchdog, codex-broker, codex-review, codex-stop-opinion) — untouched.
5. Existing skills — untouched (new dual-implement added only).
6. `AGENTS.md` and other Codex project_doc fallbacks unchanged unless explicitly needed.

## Teammate Spawn Notes (for Wave 1 + 2)

All teammates spawned via TeamCreate with Agent type `coder` (general full-access).
Prompts built via `.claude/scripts/spawn-agent.py` with:
- `--task` = full task-N.md content
- `--team codex-primary-wave-1` (or `wave-2`)
- `--name T{N}-impl`
Required Skills injected: `verification-before-completion`, `logging-standards` (as contract extract), `coding-standards` (as reference).
Codex Second Opinion block included per template (every teammate calls codex-ask.py before and after).

## Parallelism Numbers

- Wave 1: **5 parallel Claude teammates** (via TeamCreate) — classic Agent Teams
- Wave 2: **3 parallel Claude teammates** (via TeamCreate)
- No Codex implementers used in waves 1/2 (we're building the Codex executor; can't use it to build itself yet)
- PoC phase: first real Codex implementer invocation
