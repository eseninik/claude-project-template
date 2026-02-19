---
name: verification-before-completion
description: |
  Enforces evidence-based completion claims: run verification commands and confirm output.
  Use before claiming work is complete, committing, creating PRs, or moving to next task.
  Does NOT replace qa-validation-loop for full review cycles.
---

# Verification Before Completion

## Checklist (MANDATORY before "done")

1. Run project tests: `uv run pytest` / `npm test` / `cargo test`
2. Run type check if applicable: `mypy` / `tsc` / `cargo check`
3. Check lint: `ruff check` / `eslint` / `clippy`
4. Verify EACH acceptance criterion with evidence (paste output)
5. If any check fails -> fix first, re-run, do NOT claim done
6. Stage changes + update `.claude/memory/activeContext.md`

## Evidence Format

```
VERIFY: [criterion]
RESULT: [pass/fail] -- [output snippet]
```

## Red Flags
- "Tests probably pass" without running them -> BLOCKED
- "Should work" without evidence -> BLOCKED
- Skipping type checks on typed projects -> BLOCKED
