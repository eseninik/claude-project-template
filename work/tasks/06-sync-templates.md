# Task 06: Sync Templates with New Hooks

**depends_on:** 01-pre-commit-hook, 03-post-commit-fallback
**files_modified:** `.claude/shared/templates/new-project/.claude/hooks/pre-commit.sh`, `.claude/shared/templates/new-project/.claude/hooks/post-commit.sh`, `.claude/shared/templates/new-project/.claude/memory/activeContext.md`
**wave:** 2

## Objective

Synchronize new-project template with updated hooks and memory structure.

## Specification

Copy to `.claude/shared/templates/new-project/`:
1. `.claude/hooks/pre-commit.sh` (new)
2. `.claude/hooks/post-commit.sh` (updated)
3. Update `.claude/memory/activeContext.md` with Auto-Generated section

## Acceptance Criteria

- [ ] Template has pre-commit.sh
- [ ] Template has updated post-commit.sh
- [ ] Template activeContext.md has Auto-Generated section
