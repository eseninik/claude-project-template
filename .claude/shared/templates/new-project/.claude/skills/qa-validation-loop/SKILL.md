---
name: qa-validation-loop
description: |
  Risk-proportional QA cycle: depth adapts to task complexity assessment.
  Reviewer agent checks code, Fixer agent repairs issues. Loop max 3-5 iterations.
  Reads complexity from work/complexity-assessment.md to determine QA depth.
  Use after IMPLEMENT phase, after code waves, or when user says "run QA".
  Does NOT replace expert panel or test execution (TEST phase).
---

## Philosophy
QA depth should match task risk — trivial tasks need minimal checks, critical tasks need full review. A fresh pair of eyes catches what the author misses.

## Critical Constraints
**never:**
- Skip QA on high or critical risk tasks
- Reuse the same agent for re-review after fixes

**always:**
- Use a fresh agent for re-review
- Escalate to human after 3 cycles of the same issue

## Runtime Configuration (Step 0)
Before executing, check `.claude/ops/config.yaml`:
- `qa_depth` → if set to non-proportional value, use that depth instead of complexity-based
- `processing_depth` → affects reviewer thoroughness (quick=surface, standard=normal, deep=exhaustive)
- `max_retry_attempts` → maximum reviewer-fixer cycles before escalation

# QA Validation Loop

## Risk-Proportional QA Depth

Read `work/complexity-assessment.md` first. If not available, default to "medium".

| Risk Level | QA Depth | Max Iterations | Actions |
|------------|----------|----------------|---------|
| **trivial** | skip | 0 | Run verification-before-completion only |
| **low** | minimal | 1 | Single reviewer pass, unit tests only |
| **medium** | standard | 3 | Reviewer + Fixer loop, unit + integration tests |
| **high** | full | 5 | Reviewer + Fixer loop, full test suite + security scan |
| **critical** | full+human | 5 | Full loop + security scan + human review checkpoint |

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

## Depth-Specific Behavior

### trivial: Skip QA
- Just run verification-before-completion checklist
- No reviewer/fixer agents needed

### low: Minimal
- Single reviewer pass (no fixer loop)
- Only unit tests
- PASS if no CRITICAL issues

### medium: Standard (default)
- Full reviewer + fixer loop (max 3 iterations)
- Unit + integration tests
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

## Integration
- Uses complexity from: .claude/guides/complexity-assessment.md
- Uses prompts from: .claude/prompts/qa-reviewer.md, .claude/prompts/qa-fixer.md
- Agent types from: .claude/agents/registry.md (qa-reviewer, qa-fixer)
- Recovery tracking: work/attempt-history.json
- Memory injection: patterns + gotchas loaded for reviewer context
