---
executor: dual
speed_profile: fast
risk_class: routine
---

# Task inline/Z16-claude-cover: Z16 reliability fixes: codex-implement repo-current parser + spawn-agent PowerShell-primary + Y20 lock test

## Your Task

Z16 reliability fixes: codex-implement repo-current parser + spawn-agent PowerShell-primary + Y20 lock test

## Scope Fence

**Allowed paths:**
- `.claude/scripts/codex-implement.py`
- `.claude/scripts/test_codex_implement.py`
- `.claude/scripts/spawn-agent.py`
- `.claude/scripts/test_spawn_agent.py`

## Test Commands

```bash
py -3 -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_spawn_agent.py -q
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: implementation satisfies: Z16 reliability fixes: codex-implement repo-current parser + spawn-agent PowerShell-primary + Y20 lock test
- [ ] AC2: only files inside Scope Fence are modified
- [ ] AC3: Test Command `py -3 -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_spawn_agent.py -q` exits 0
- [ ] AC_hygiene: no secrets logged, structured logging on new code

## Constraints

- Windows-compatible
- Stdlib only unless scope explicitly allows a dep
- Match existing code style

