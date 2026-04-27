---
executor: dual
speed_profile: fast
risk_class: routine
---

# Task inline/Z6-sync-after-y23: Re-verify safety of running work/sync-template-to-target.py to mirror .claude/ infrastructure into QA Legal after Y23 codex-ask fix landed. Verification only.

## Your Task

Re-verify safety of running work/sync-template-to-target.py to mirror .claude/ infrastructure into QA Legal after Y23 codex-ask fix landed. Verification only.

## Scope Fence

**Allowed paths:**
- `work/sync-template-to-target.py`

## Test Commands

```bash
py -3 -m py_compile work/sync-template-to-target.py
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: implementation satisfies: Re-verify safety of running work/sync-template-to-target.py to mirror .claude/ infrastructure into QA Legal after Y23 codex-ask fix landed. Verification only.
- [ ] AC2: only files inside Scope Fence are modified
- [ ] AC3: Test Command `py -3 -m py_compile work/sync-template-to-target.py` exits 0
- [ ] AC_hygiene: no secrets logged, structured logging on new code

## Constraints

- Windows-compatible
- Stdlib only unless scope explicitly allows a dep
- Match existing code style

