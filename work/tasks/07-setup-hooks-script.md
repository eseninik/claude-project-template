# Task 07: Update Setup Hooks Script

**depends_on:** 01-pre-commit-hook, 03-post-commit-fallback
**files_modified:** `.claude/scripts/setup-hooks.sh`
**wave:** 2

## Objective

Update setup-hooks.sh to install pre-commit hook.

## Specification

Update `.claude/scripts/setup-hooks.sh` to:
1. Install pre-commit hook (new)
2. Keep existing post-commit installation
3. Set executable permissions

## Acceptance Criteria

- [ ] setup-hooks.sh installs pre-commit hook
- [ ] Both hooks get executable permission
