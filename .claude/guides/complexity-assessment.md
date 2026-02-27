# Complexity Assessment Guide

Determine QA depth proportional to task risk. Run after task-decomposition or inline during planning.

## Risk Levels

### Trivial
- **Scope**: 1 file, < 20 lines changed
- **Nature**: typo fix, config tweak, string change, comment update
- **No logic changes**, no new code paths
- **QA**: skip qa-validation-loop, run verification-before-completion only

### Low
- **Scope**: 2-3 files, single module
- **Nature**: small feature, bug fix with clear root cause, refactor within one module
- **Follows established patterns**, no new dependencies
- **QA**: unit tests, basic code review (single reviewer pass)

### Medium
- **Scope**: 4-10 files, 2+ modules
- **Nature**: new feature spanning multiple layers, API endpoint + service + tests
- **Some unknowns** but mostly familiar patterns
- **QA**: full qa-validation-loop (reviewer + fixer, max 3 iterations), unit + integration tests

### High
- **Scope**: 10+ files, cross-cutting changes
- **Nature**: multi-service feature, external API integration, significant refactoring
- **External dependencies**, new libraries, unfamiliar patterns
- **QA**: full QA loop + security scan + extra review pass

### Critical
- **Scope**: architecture change, data migration, auth/security system
- **Nature**: database schema migration, authentication flow change, infrastructure overhaul
- **High blast radius**, hard to reverse, security implications
- **QA**: full QA loop + security scan + mandatory human review checkpoint

## Assessment Algorithm

Evaluate 5 factors, then derive the risk level:

### 1. Scope Analysis
- Count estimated files changed
- Count modules/services affected
- Check if changes are cross-cutting (affects multiple layers)
- 1 file = trivial baseline, 10+ files = high baseline

### 2. Integration Analysis
- External services involved? (APIs, databases, queues)
- New dependencies added?
- Research needed for unfamiliar APIs?
- Any external integration bumps level by +1

### 3. Infrastructure Analysis
- Docker/container changes?
- Database schema changes?
- Config/environment changes?
- CI/CD pipeline changes?
- Any infrastructure change bumps level by +1

### 4. Knowledge Analysis
- Familiar patterns and codebase areas?
- Research required before implementation?
- Unfamiliar technology or libraries?
- Low familiarity bumps level by +1

### 5. Risk Analysis
- List concrete concerns
- Security implications (auth, input validation, data exposure)?
- Data loss potential?
- Any security concern sets minimum level to high

**Final level** = max(baseline from scope, adjustments from factors 2-5)

## QA Depth by Level

| Level | Validation Loop | Tests Required | Security | Human Review |
|-------|----------------|----------------|----------|-------------|
| trivial | skip | none (existing pass) | no | no |
| low | skip | unit tests | no | no |
| medium | standard (3 cycles max) | unit + integration | no | no |
| high | standard + extra pass | unit + integration + e2e | yes | no |
| critical | standard + extra pass | unit + integration + e2e | yes | **yes** |

### Validation Recommendations Output

After assessment, produce these flags for downstream consumption:

- **skip_validation**: true only for trivial
- **minimal_mode**: true for low (unit tests only, single review)
- **test_types_required**: unit | unit+integration | unit+integration+e2e
- **security_scan_required**: true for high and critical
- **human_review_required**: true for critical only

## Pipeline Integration

The QA_REVIEW phase reads complexity from `work/complexity-assessment.md`:

1. **During PLAN/DECOMPOSE**: task-decomposition skill generates complexity assessment
2. **Write to file**: save assessment to `work/complexity-assessment.md` using the template
3. **QA_REVIEW reads**: phase executor checks risk level and applies corresponding QA depth
4. **Skip fast path**: if trivial/low, QA_REVIEW runs minimal checks and proceeds

Pipeline flow:
```
DECOMPOSE -> writes work/complexity-assessment.md
    |
IMPLEMENT -> developer works
    |
QA_REVIEW -> reads complexity-assessment.md -> applies QA depth
    |
    trivial -> verification-before-completion only
    low     -> unit tests + single reviewer
    medium  -> qa-validation-loop (reviewer+fixer, 3 cycles)
    high    -> qa-validation-loop + security scan
    critical -> qa-validation-loop + security + STOP for human
```

## How to Generate Assessment

### Option A: Inline (during task-decomposition)
After decomposing subtasks, add complexity assessment to output. Best for simple cases.

### Option B: Dedicated Agent
Spawn a complexity-assessor agent that reads the task spec and produces `work/complexity-assessment.md`. Best for large tasks where assessment itself needs analysis.

### Option C: Human Override
Human can manually set complexity level in `work/complexity-assessment.md`. Always takes precedence.

## Examples

### Trivial: Fix typo in README
- 1 file, 1 line change, no logic
- Complexity: trivial, Confidence: 99%
- QA: run existing tests, verify fix, done

### Low: Add validation to existing form field
- 2 files (component + test), single module
- Familiar pattern, no new deps
- Complexity: low, Confidence: 90%
- QA: write unit test, single review pass

### Medium: Add user profile page
- 6 files (route, handler, service, model, template, test)
- 2 modules (API + UI), follows existing patterns
- Complexity: medium, Confidence: 80%
- QA: unit + integration tests, qa-validation-loop

### High: Integrate Stripe payment processing
- 12+ files across 3 services
- External API (Stripe), new dependency, webhook handling
- Complexity: high, Confidence: 70%
- QA: full QA loop, security scan for payment data handling

### Critical: Migrate auth from sessions to JWT
- 20+ files, every authenticated endpoint affected
- Security system change, data migration for existing sessions
- Complexity: critical, Confidence: 60%
- QA: full QA loop, security scan, human review before merge

## Template

Use `work-templates/complexity-assessment.md` for structured output.
