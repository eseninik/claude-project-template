---
name: qa-validation-loop
description: >
  Risk-proportional QA cycle with Reviewer and Fixer agents, depth adapts to task
  complexity. Includes Nyquist pre-flight requirement-to-test mapping before implementation.
  Use after IMPLEMENT phase, after code waves, or when user says
  "run QA". Do NOT use for generic code review, running tests, debugging, expert panel, or security-only audits.
roles: [qa-reviewer, nyquist-auditor]
---

# QA Validation Loop

## Overview

QA depth should match task risk -- trivial tasks need minimal checks, critical tasks need full review. A fresh pair of eyes catches what the author misses.

**Core principle:** Risk-proportional quality gates with independent reviewer and fixer agents.

## Critical Constraints

**Never:**
- Skip QA on high or critical risk tasks
- Reuse the same agent for re-review after fixes

**Always:**
- Use a fresh agent for re-review
- Escalate to human after 3 cycles of the same issue

## Evaluation Firewall

**Principle:** Acceptance criteria and test assertions are IMMUTABLE once approved. The implementer can change anything in the codebase EXCEPT:
- Test files (test_*.py, *.test.ts, *.spec.ts, etc.)
- Acceptance criteria in task/spec files
- Evaluation scripts or benchmark configurations
- Metric definitions

**Reviewer check:** During QA review, the reviewer MUST verify:
1. List all files modified by the implementer (from git diff or handoff)
2. Check if ANY modified file matches test/eval patterns
3. If test files were modified by the implementer:
   - Flag as **CRITICAL** issue: "Evaluation Firewall violation: implementer modified test/eval files"
   - The ONLY acceptable exception: implementer added NEW test files (not modified existing ones)
4. If acceptance criteria were weakened or removed → flag as **CRITICAL**

**Why this matters:** Without this firewall, agents can "game" quality gates by modifying tests to pass rather than fixing the actual code. This is the #1 failure mode in autonomous agent systems (ref: Karpathy's autoresearch design).

## Logging Coverage Review

**QA reviewer MUST check logging coverage in every code change.** Reference: `.claude/guides/logging-standards.md`

### Logging Checklist for Reviewer

| Check | Pass Criteria |
|-------|---------------|
| Entry/exit logging | Every new public function has INFO log at entry and exit |
| Error logging | Every catch/except block logs error with context (ERROR level) |
| External call logging | Every API/DB/file call has timing + result logging |
| No bare prints | No `print()`, `console.log()` used instead of logger |
| No sensitive data | No tokens, passwords, PII in log messages |
| Structured format | All logs use key=value or structured JSON, not freeform strings |
| Appropriate levels | DEBUG for details, INFO for flow, WARNING for issues, ERROR for failures |

### Logging Issue Severity

| What's Missing | QA Severity |
|----------------|-------------|
| No logging at all in new code | **CRITICAL** |
| Missing error logging in catch blocks | **CRITICAL** |
| Missing logging on external API calls | **IMPORTANT** |
| Using print()/console.log() instead of logger | **IMPORTANT** |
| Missing timing on slow operations | **MINOR** |
| Missing DEBUG logs for data transformations | **MINOR** |

## Cross-Model Verification (Codex)

**When:** After Claude QA reviewer completes, before final QA verdict.
**Why:** Different AI model catches confirmation bias — classes of errors that same-model review systematically misses.

### When to Invoke
- High-risk changes: auth, payments, migrations, security, public API
- Large changes: 5+ files across modules
- Complex refactoring: architectural changes

### When to Skip
- Docs/CSS/config-only changes
- Small fixes < 50 lines with existing test coverage
- Codex CLI not available (graceful degradation)

### How to Invoke
```bash
codex exec \
  "Review all uncommitted changes. Focus on correctness, security, performance, test coverage. Use AGENTS.md rubric." \
  -m gpt-5.4 \
  --sandbox read-only \
  --full-auto \
  --output-schema .codex/review-schema.json \
  -o .codex/reviews/latest.json \
  --ephemeral
```

### Mapping Codex Findings to QA Severity

| Codex Severity | QA Severity | Action |
|---------------|-------------|--------|
| BLOCKER | **CRITICAL** | Must fix before approval |
| IMPORTANT | **IMPORTANT** | Should fix, verify if valid |
| NIT | MINOR | Optional, fix if genuine improvement |

### Conflict Resolution (Claude QA vs Codex)
1. **Reproducible issue** (failing test, obvious bug) → CRITICAL regardless of which model found it
2. **Style/approach disagreement** → defer to AGENTS.md/CLAUDE.md rules as norm
3. **Security disagreement** → err on caution, escalate to security-auditor agent
4. **Same issue disputed after 2 rounds** → BLOCKED, escalate to human
5. **Lint/format disputes** → deterministic tools decide (prettier, eslint, black, ruff)

## Runtime Configuration

Before executing, check `.claude/ops/config.yaml`:
- `qa_depth` -- if set to non-proportional value, use that depth instead of complexity-based
- `processing_depth` -- affects reviewer thoroughness (quick=surface, standard=normal, deep=exhaustive)
- `max_retry_attempts` -- maximum reviewer-fixer cycles before escalation

## Risk-Proportional QA Depth

Read `work/complexity-assessment.md` first. If not available, default to "medium".

| Risk Level | QA Depth | Max Iterations | Actions |
|------------|----------|----------------|---------|
| **trivial** | skip | 0 | Run verification-before-completion only |
| **low** | minimal | 1 | Single reviewer pass, unit tests only |
| **medium** | standard | 3 | Reviewer + Fixer loop, unit + integration tests |
| **high** | full | 5 | Reviewer + Fixer loop, full test suite + security scan |
| **critical** | full+human | 5 | Full loop + security scan + human review checkpoint |

## Nyquist Pre-Flight Validation

Named after the Nyquist frequency (minimum sampling rate to preserve information), this layer ensures every requirement has planned test coverage BEFORE implementation begins.

### When to Run
- AFTER task decomposition, BEFORE implementation
- When PIPELINE.md has a NYQUIST_CHECK phase
- When user runs "/gsd:validate-phase" equivalent
- Can be skipped for trivial risk tasks

### Pre-Flight Process

1. **Extract Requirements**
   - Read task files (work/{feature}/tasks/*.md)
   - Extract acceptance criteria, success criteria, done criteria
   - Build requirement list with IDs

2. **Map to Test Coverage**
   For each requirement, determine:
   | Requirement | Test Type | Test File | Command | Status |
   |-------------|-----------|-----------|---------|--------|
   | REQ-01: User can login | Integration | test_auth.py | pytest test_auth.py::test_login | PLANNED |
   | REQ-02: Invalid email shows error | Unit | test_validation.py | pytest test_validation.py::test_email | PLANNED |

3. **Classify Test Types**
   | Behavior | Test Type |
   |----------|-----------|
   | Pure function I/O | Unit |
   | API endpoint | Integration |
   | CLI command | Smoke |
   | DB/filesystem operation | Integration |
   | UI interaction | E2E |
   | Cross-service communication | Integration |

4. **Gap Analysis**
   - COVERED: requirement has planned test
   - PARTIAL: requirement has test but doesn't cover all cases
   - MISSING: requirement has no planned test

   If MISSING > 0: generate test plan entries for gaps

5. **Output: work/{feature}/nyquist-map.md**
   ```markdown
   # Nyquist Validation Map

   ## Coverage Summary
   - Total requirements: N
   - Covered: X (Y%)
   - Partial: A
   - Missing: B

   ## Requirement-Test Matrix
   | ID | Requirement | Test Type | Test File | Status |
   |----|-------------|-----------|-----------|--------|
   | ... | ... | ... | ... | COVERED/PARTIAL/MISSING |

   ## Gap Closure Plan
   For each MISSING:
   - Requirement: [text]
   - Suggested test: [description]
   - Test type: [unit/integration/e2e]
   - File: [suggested path]
   ```

### Integration with Pipeline

Add NYQUIST_CHECK phase to PIPELINE.md (optional, between PLAN and IMPLEMENT):

```
### Phase: NYQUIST_CHECK
- Status: PENDING
- Mode: SOLO
- On PASS: -> IMPLEMENT
- On FAIL: -> PLAN
- Gate: all requirements have planned test coverage (0 MISSING)
- Gate Type: AUTO
```

### Retroactive Validation

For already-implemented phases without Nyquist:
1. Read SUMMARY.md or completed task files
2. Reconstruct requirement-test mapping from actual test files
3. Run gap analysis against original requirements
4. Generate tests for gaps using nyquist-auditor agent

## Process (standard depth, max 3 iterations)

1. **Read complexity** from work/complexity-assessment.md -> determine QA depth
2. **Collect** acceptance criteria from task files / user-spec.md
3. **Spawn Reviewer** (Task tool, agent type: qa-reviewer from registry):
   - Input: changed files list + acceptance criteria + complexity level
   - Use prompt: .claude/prompts/qa-reviewer.md
   - Output: issues with severity (CRITICAL / IMPORTANT / MINOR) with evidence
4. **Evaluate**: No CRITICAL/IMPORTANT -> PASS. Otherwise -> continue
5. **Spawn Fixer** (Task tool, agent type: qa-fixer from registry):
   - Input: CRITICAL + IMPORTANT issues only
   - Use prompt: .claude/prompts/qa-fixer.md
   - Fixes targeted issues, verifies each fix
6. **Spawn fresh Re-reviewer** (new agent, NOT the original reviewer)
7. **Track** in work/qa-issues.md: iteration, issues found, issues fixed
8. **Recovery**: if same issue 3+ iterations -> check work/attempt-history.json -> ESCALATE

## Post-Implementation Nyquist Audit

After implementation, verify the Nyquist map was fulfilled:

1. Re-read nyquist-map.md
2. For each PLANNED test:
   - Does test file exist? (Level 1: Exists)
   - Does test have real assertions? (Level 2: Substantive)
   - Does test actually run? (Level 3: Executable)
3. Update status: PLANNED -> COVERED | PARTIAL | MISSING
4. If gaps found:
   - Generate minimal behavioral tests
   - Max 3 debug iterations per gap
   - If test still fails after 3 attempts -> ESCALATE

### Audit Output

Three possible outcomes:
- **GAPS_FILLED**: All requirements now have working tests
- **PARTIAL**: Some gaps filled, some escalated (list both)
- **ESCALATE**: Implementation bugs found -- DO NOT fix implementation, only report

## Depth-Specific Behavior

### trivial: Skip QA
- Just run verification-before-completion checklist
- No reviewer/fixer agents needed

### low: Minimal
- Single reviewer pass (no fixer loop)
- Only unit tests
- Check for logging presence in new code (CRITICAL if missing)
- PASS if no CRITICAL issues

### medium: Standard (default)
- Full reviewer + fixer loop (max 3 iterations)
- Unit + integration tests
- Full logging coverage review per Logging Checklist above
- PASS if no CRITICAL/IMPORTANT issues

### high: Full
- Full reviewer + fixer loop (max 5 iterations)
- Full test suite (unit + integration + e2e)
- Security scan (check for OWASP top 10, secrets, injection)
- PASS if no CRITICAL/IMPORTANT + security clean

### critical: Full + Human
- Same as high
- PLUS: human review checkpoint before PASS
- Create work/human-review-request.md with summary

## Verdicts
- **PASS**: No CRITICAL/IMPORTANT remaining
- **CONCERNS**: Only MINOR remaining (proceed)
- **REWORK**: Issues fixable (next iteration)
- **ESCALATE**: Same issue 3+ times or critical security finding

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Reusing same reviewer agent after fixer | Spawn a fresh agent -- same reviewer has bias |
| Skipping QA on "simple" changes | Check complexity-assessment.md -- even low risk gets one pass |
| Fixing MINOR issues in fixer loop | Fixer handles CRITICAL + IMPORTANT only -- MINOR proceeds |
| Running QA without acceptance criteria | Collect criteria first -- reviewer needs them for evaluation |
| Continuing after same issue 3+ times | ESCALATE to human -- loop is stuck |
| Not checking logging coverage | Use Logging Checklist -- missing logs cause blind debugging |

## Integration
- Uses complexity from: .claude/guides/complexity-assessment.md
- Uses prompts from: .claude/prompts/qa-reviewer.md, .claude/prompts/qa-fixer.md
- Agent types from: .claude/agents/registry.md (qa-reviewer, qa-fixer)
- Recovery tracking: work/attempt-history.json
- Memory injection: patterns + gotchas loaded for reviewer context

## Related
- → verification-before-completion — logging and artifact checks
- → systematic-debugging — when QA finds complex bugs
- ← subagent-driven-development — QA after implementation waves
- ← PIPELINE.md QA_REVIEW phase — mandatory after IMPLEMENT
