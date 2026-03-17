# QA Reviewer Memory

> Persistent memory for qa-reviewer agents. First 200 lines auto-injected at startup.

## Patterns That Work

- Check logging coverage in ALL new/modified functions
- Verify acceptance criteria one by one with evidence
- Flag missing error handling in async code
- Check for hardcoded values and magic numbers

## Patterns That Fail

- Approving code without running tests
- Trusting agent self-reports without verification
- Missing structured logging checks

## Common Issues in This Project

- Missing logging in error handlers (most frequent)
- Forgotten edge cases in input validation
- Tests that don't actually assert outcomes

## Recent History

| Date | Task | Outcome | Learning |
|------|------|---------|----------|
