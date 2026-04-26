---
executor: dual
speed_profile: fast
risk_class: routine
---

# Task inline/Z9-smoke-after-y26: Re-verify safety of running work/sync-template-to-target.py post-Y26-fix. Codex should now be able to write into the worktree (sandbox bypass enabled). Verification only.

## Your Task

Re-verify safety of running work/sync-template-to-target.py post-Y26-fix. Codex should now be able to write into the worktree (sandbox bypass enabled). Verification only.

## Scope Fence

**Allowed paths:**
- `work/sync-template-to-target.py`

## Test Commands

```bash
py -3 -m py_compile work/sync-template-to-target.py
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: implementation satisfies: Re-verify safety of running work/sync-template-to-target.py post-Y26-fix. Codex should now be able to write into the worktree (sandbox bypass enabled). Verification only.
- [ ] AC2: only files inside Scope Fence are modified
- [ ] AC3: Test Command `py -3 -m py_compile work/sync-template-to-target.py` exits 0
- [ ] AC_hygiene: no secrets logged, structured logging on new code

## Constraints

- Windows-compatible
- Stdlib only unless scope explicitly allows a dep
- Match existing code style

