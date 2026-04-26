---
executor: dual
speed_profile: fast
risk_class: routine
---

# Task inline/Z2-sync-script-recheck: Re-verify safety of running work/sync-template-to-target.py to mirror .claude/ infrastructure into another bot project. Read the script, validate that file mutations are well-bounded by EXCLUDE_NAMES + MIRROR_DIRS policy, that secrets cannot leak (.env in EXCLUDE_NAMES), that idempotency holds (filecmp before copy). No code changes required — verification only.

## Your Task

Re-verify safety of running work/sync-template-to-target.py to mirror .claude/ infrastructure into another bot project. Read the script, validate that file mutations are well-bounded by EXCLUDE_NAMES + MIRROR_DIRS policy, that secrets cannot leak (.env in EXCLUDE_NAMES), that idempotency holds (filecmp before copy). No code changes required — verification only.

## Scope Fence

**Allowed paths:**
- `work/sync-template-to-target.py`

## Test Commands

```bash
py -3 -c 'import ast; ast.parse(open("work/sync-template-to-target.py").read()); print("OK syntax")'
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: implementation satisfies: Re-verify safety of running work/sync-template-to-target.py to mirror .claude/ infrastructure into another bot project. Read the script, validate that file mutations are well-bounded by EXCLUDE_NAMES + MIRROR_DIRS policy, that secrets cannot leak (.env in EXCLUDE_NAMES), that idempotency holds (filecmp before copy). No code changes required — verification only.
- [ ] AC2: only files inside Scope Fence are modified
- [ ] AC3: Test Command `py -3 -c 'import ast; ast.parse(open("work/sync-template-to-target.py").read()); print("OK syntax")'` exits 0
- [ ] AC_hygiene: no secrets logged, structured logging on new code

## Constraints

- Windows-compatible
- Stdlib only unless scope explicitly allows a dep
- Match existing code style

