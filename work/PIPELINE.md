# Pipeline: ECC Cherry-Pick Integration

- Status: IN_PROGRESS
- Phase: IMPLEMENT
- Mode: AGENT_TEAMS

> Cherry-pick HIGH + MEDIUM priority components from everything-claude-code into our template system.
> Also: fix Graphiti MCP connection, verify RTK hook.
> Source repo: /tmp/everything-claude-code/

---

## Phases

### Phase: IMPLEMENT  <- CURRENT
- Status: IN_PROGRESS
- Mode: AGENT_TEAMS
- Attempts: 1 of 2
- On PASS: -> VERIFY
- On FAIL: -> FIX
- Gate: all 12 tasks completed, files created
- Gate Type: AUTO

Wave 1 (parallel, independent — 11 agents):
- Task 1: Fix Graphiti MCP connection
- Task 2: Verify RTK hook
- Task 3: Import Security Guide
- Task 4: Implement Hook Profiles
- Task 5: Import 10-15 generic skills
- Task 6: Import language rule packs
- Task 7: Add Config Protection hook
- Task 8: Add Build-Error-Resolvers
- Task 9: Implement Continuous Learning Loop
- Task 10: Add JSON Schema validation
- Task 11: Expand MCP catalog

Wave 2 (depends on Wave 1):
- Task 12: Sync all to new-project template

### Phase: VERIFY
- Status: PENDING
- Mode: SOLO
- Attempts: 0 of 1
- On PASS: -> COMPLETE
- On FAIL: -> FIX
- Gate: all new files exist, hooks work, skills load
- Gate Type: AUTO

### Phase: COMPLETE
- Status: PENDING
- Mode: SOLO
- Gate: memory updated, git committed

---

## Decisions

- [IMPLEMENT] Skip AUTO_RESEARCH/SPEC/PLAN — task is well-defined cherry-pick, not feature development.
- [IMPLEMENT] Wave 1 = 11 parallel tasks (independent files/dirs). Wave 2 = template sync (depends on all).
- [IMPLEMENT] Security Guide: adapt, don't copy verbatim — our system has different hooks/agents.
- [IMPLEMENT] Skills: convert to our SKILL.md format with frontmatter + triggers.
- [IMPLEMENT] Hook Profiles: add to hook_base.py, not individual hooks.
