---
name: cross-model-review
description: >
  Invoke Codex CLI for cross-model code review after implementation. Provides independent
  verification from a different AI model to catch confirmation bias and blind spots.
  Use before PRs, after completing features/refactoring/bugfixes, after QA validation,
  or when user says "codex review", "cross-model review", "second opinion".
  Do NOT use for: docs-only changes, CSS/style changes, config file edits, or changes < 50 lines
  with existing test coverage.
roles: [qa-reviewer, coder, coder-complex, verifier]
---

# Cross-Model Review with Codex CLI

## Overview

Cross-model verification eliminates confirmation bias by having a different AI model (Codex/GPT) review code written by Claude. This catches classes of errors that same-model review systematically misses.

**Core principle:** Two independent models catch more bugs than one model reviewing itself.

## Prerequisites

Before running cross-model review, verify:
1. `codex` CLI is installed: `which codex || echo "Install: npm i -g @openai/codex"`
2. Authentication configured: `OPENAI_API_KEY` set or `codex auth` completed
3. Review schema exists: `.codex/review-schema.json`
4. AGENTS.md in project root (shared context for both tools)

If any prerequisite is missing, skip cross-model review and note it in handoff.

## When to Run

### ALWAYS run when:
- Auth, payments, or cryptography code changed
- Database migrations added or modified
- Public API contracts changed
- External API integrations added/changed
- Security-sensitive code modified
- 5+ files changed across different modules

### SKIP when ALL of these are true:
- Total changes < 50 lines
- Only docs, comments, CSS, or config files changed
- Existing tests fully cover changed code and pass
- No auth/payments/migrations/security code touched

## Workflow

### Step 1: Local Quality Gate (fast)
Run local tests and lint first. Don't waste Codex tokens on code that doesn't compile/pass.

```bash
# Run your project's test command
make test  # or: uv run pytest / npm test / cargo test

# Run linter
make lint  # or: uv run ruff check / npm run lint
```

If tests fail → fix first, then come back.

### Step 2: Generate Diff Summary
```bash
git diff --stat
git diff --name-only
```

Check if bypass criteria are met. If yes, skip to Step 6.

### Step 3: Run Codex Review

**Standard review (recommended):**
```bash
codex exec \
  "Review all uncommitted changes. Focus on correctness, security, performance, test coverage, and logging. Use AGENTS.md rubric. Return JSON matching the schema." \
  -m gpt-5.5 \
  --sandbox read-only \
  --full-auto \
  --ephemeral \
  --output-schema .codex/review-schema.json \
  -o .codex/reviews/latest.json
```

**Quick review (for smaller changes):**
```bash
codex exec \
  "Review uncommitted changes for obvious bugs and security issues." \
  -m gpt-5.5-mini \
  --sandbox read-only \
  --full-auto \
  --ephemeral
```

**Branch review (before PR/merge):**
```bash
codex exec \
  "Review all changes on current branch vs main. Focus on architecture, security, and edge cases." \
  -m gpt-5.5 \
  --sandbox read-only \
  --full-auto \
  --ephemeral \
  --output-schema .codex/review-schema.json \
  -o .codex/reviews/latest.json
```

### Step 4: Parse and Triage Results

Read `.codex/reviews/latest.json` and categorize:

```bash
# Check verdict
jq '.verdict' .codex/reviews/latest.json

# List BLOCKERs
jq '.findings[] | select(.severity=="BLOCKER")' .codex/reviews/latest.json

# List IMPORTANTs
jq '.findings[] | select(.severity=="IMPORTANT")' .codex/reviews/latest.json
```

### Step 5: Act on Findings

| Severity | Action |
|----------|--------|
| **BLOCKER** | Fix immediately. Re-run review after fix. |
| **IMPORTANT** | Fix if valid. If disagree, verify by reading referenced code. |
| **NIT** | Optional. Fix if it genuinely improves code. |

**Conflict resolution:**
- If Codex finding contradicts Claude's design → check AGENTS.md/CLAUDE.md rules
- If security disagreement → err on caution, fix it
- After 2 rounds of disagreement on same issue → escalate to human

### Step 6: Report

Output a summary:
```
Cross-Model Review (Codex): [PASS/FAIL/SKIPPED]
- Verdict: [pass/fail/needs_human_review]
- Confidence: [0-1]
- BLOCKERs: [count]
- IMPORTANTs: [count]
- NITs: [count]
- Bypass reason: [if skipped]
```

## Model Selection Guide

| Scenario | Model | Rationale |
|----------|-------|-----------|
| Pre-commit quick check | `gpt-5.5-mini` | Fast, cheap, catches obvious errors |
| Standard code review | `gpt-5.5` | Good balance of depth and speed |
| Security audit | `gpt-5.5` | Strong at finding vulnerabilities |
| Architecture review | `gpt-5.5` | Best reasoning for complex decisions |

## Related

- `qa-validation-loop` — includes cross-model review step
- `verification-before-completion` — includes cross-model check
- `.claude/guides/codex-integration.md` — full integration guide
