---
executor: dual
speed_profile: fast
risk_class: routine
---

# Task inline/Z3-sync-script-recheck: Re-verify safety of running work/sync-template-to-target.py to mirror .claude/ infrastructure into another bot project. Read the script, validate file mutations are well-bounded by EXCLUDE_NAMES + MIRROR_DIRS policy. Verification only — no code changes.

## Your Task

Re-verify safety of running work/sync-template-to-target.py to mirror .claude/ infrastructure into another bot project. Read the script, validate file mutations are well-bounded by EXCLUDE_NAMES + MIRROR_DIRS policy. Verification only — no code changes.

## Scope Fence

**Allowed paths:**
- `work/sync-template-to-target.py`

## Test Commands

```bash
py -3 -m py_compile work/sync-template-to-target.py
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: implementation satisfies: Re-verify safety of running work/sync-template-to-target.py to mirror .claude/ infrastructure into another bot project. Read the script, validate file mutations are well-bounded by EXCLUDE_NAMES + MIRROR_DIRS policy. Verification only — no code changes.
- [ ] AC2: only files inside Scope Fence are modified
- [ ] AC3: Test Command `py -3 -m py_compile work/sync-template-to-target.py` exits 0
- [ ] AC_hygiene: no secrets logged, structured logging on new code

## Constraints

- Windows-compatible
- Stdlib only unless scope explicitly allows a dep
- Match existing code style

