# Quality Gate Framework

**Date:** 2026-02-16 | **Component:** Phase 2 — Quality Gates Design

---

## 1. 4-Verdict Model

| Verdict | Meaning | Pipeline Action |
|---------|---------|-----------------|
| **PASS** | All checks green | Create git checkpoint tag, advance `<- CURRENT` to `On PASS` target |
| **CONCERNS** | Minor issues found | Log in PIPELINE.md Decisions, create checkpoint, advance |
| **REWORK** | Significant issues | Increment `Attempts`, return to phase. If `>= Max Attempts` -> FAIL |
| **FAIL** | Fundamental problem | Set status `BLOCKED`, stop pipeline, alert user |

**Priority rule:** Multiple checks -> worst verdict wins. FAIL > REWORK > CONCERNS > PASS.

---

## 2. Gate Types

**AUTO** — Shell commands, verdict by exit codes:
```yaml
Gate: { Type: AUTO, Commands: [uv run pytest, ruff check ., mypy src/] }
PASS: all exit codes == 0 | REWORK: any != 0
```

**USER_APPROVAL** — Human decides after reviewing artifact:
```yaml
Gate: { Type: USER_APPROVAL, Prompt: "Review {artifact}. Approve?" }
Allowed: [PASS, CONCERNS, REWORK, FAIL]
```

**HYBRID** — Auto first, user confirms on auto-pass:
```yaml
Gate: { Type: HYBRID, Auto: [test -f artifact.md, grep check] }
Auto Fail -> REWORK (skip user) | Auto Pass -> ask user for verdict
```

---

## 3. Per-Phase Gate Definitions

| Phase | Type | Commands / Check | PASS | REWORK |
|-------|------|------------------|------|--------|
| SPEC | USER_APPROVAL | User reviews `work/{feature}/user-spec.md` | User approves | User requests changes |
| REVIEW | HYBRID | `test -f work/expert-analysis.md` + `! grep 'OPEN QUESTION'` | Auto pass + user confirms | Auto fail or user rejects |
| PLAN | USER_APPROVAL | User reviews `tech-spec.md` + `tasks/*.md` exist with criteria | User approves | User requests changes |
| IMPLEMENT | AUTO | `uv run pytest -q` + `ruff check .` + `mypy src/` | All exit 0 | Any exit != 0 |
| TEST | AUTO | `uv run pytest --tb=long -v` | 0 failures | Any failures |
| FIX | AUTO | `uv run pytest -q` (max 3 attempts) | Previously failing tests pass | Tests still failing |
| DEPLOY | AUTO | `ssh $TARGET "systemctl status $SVC"` + `curl -sf health` (max 2) | Service active + 200 | Service failed or no 200 |
| STRESS_TEST | AUTO | `locust --headless -u 100 -r 10 --run-time 60s` | p95 < 500ms, err < 1% | p95 >= 1000ms or err >= 5% |

**STRESS_TEST CONCERNS zone:** p95 500-1000ms OR err 1-5% -> document, proceed.

---

## 4. Gate Execution Protocol

```
1. PHASE SIGNALS COMPLETION
   Agent finishes work, ready for gate check.

2. READ GATE DEFINITION from PIPELINE.md for current phase.

3. EXECUTE CHECKS
   AUTO: Run commands sequentially, capture stdout/stderr/exit code.
   USER_APPROVAL: Present artifact summary + prompt.
   HYBRID: Run auto first. Fail -> REWORK. Pass -> ask user.

4. DETERMINE VERDICT
   Worst verdict wins across all commands.

5. RECORD RESULTS
   -> work/gate-results/{phase}-attempt-{n}.md (commands, output, verdict)

6. APPLY VERDICT
   PASS:     git tag pipeline-checkpoint-{phase} -> PIPELINE.md DONE -> advance <- CURRENT -> commit
   CONCERNS: log in Decisions -> same as PASS
   REWORK:   increment Attempts -> if >= Max -> FAIL; else re-execute phase
   FAIL:     status BLOCKED -> pipeline BLOCKED -> alert user -> stop
```

---

## 5. Gate Failure Handling

### Retry Logic
- REWORK increments `Attempts` in PIPELINE.md. Default `Max Attempts`: 3.
- `Attempts >= Max Attempts` -> auto-escalate to FAIL.
- Each retry uses previous gate results as debugging context.

### Rollback
```
On REWORK (code phases): git stash, fix forward incrementally. No full reset.
On FAIL (any phase):     git reset --hard pipeline-checkpoint-{previous-phase}
                         PIPELINE.md reverts. Pipeline stops, user takes over.
```
**Why fix forward on REWORK:** Resetting discards diagnostic info. Gate results guide targeted fixes.

### Escalation Chain
```
Attempt 1 REWORK -> retry with gate feedback
Attempt 2 REWORK -> try different approach
Attempt 3 REWORK -> auto-FAIL (max reached) -> BLOCKED, user alerted
```

### CONCERNS Tracking
Record in PIPELINE.md Decisions: `### Decision: Proceeded past {phase} with concerns` — what passed, what had warnings, why safe to proceed.

---

## 6. Gate Results Storage

**In PIPELINE.md** (brief, under the phase):
```markdown
- Gate Verdict: PASS (attempt 2)
- Gate Summary: 47/47 tests pass, ruff clean, mypy clean
```

**Detailed:** `work/gate-results/{phase}-attempt-{n}.md` — timestamp, each command + exit code + output, verdict.

**Git tags** (on PASS/CONCERNS): `pipeline-checkpoint-{PHASE_NAME}`
- Create: `git tag -f pipeline-checkpoint-{PHASE}`
- Rollback: `git reset --hard pipeline-checkpoint-{PHASE}`

---

## 7. PIPELINE.md Integration Example

```markdown
### Phase: IMPLEMENT
- Status: IN_PROGRESS <- CURRENT
- Mode: AGENT_TEAMS
- Attempts: 1 of 3
- On PASS: -> TEST
- On REWORK: -> IMPLEMENT
- On FAIL: -> BLOCKED
- Gate:
  - Type: AUTO
  - Commands: uv run pytest -q && ruff check . && mypy src/
  - PASS: all exit codes == 0
  - REWORK: any exit code != 0
```

Self-contained — agent reads this after compaction and knows exactly how to verify and what each verdict triggers.
