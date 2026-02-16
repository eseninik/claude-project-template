---
name: executing-plans
description: |
  Executes implementation plans in controlled batches with review checkpoints between batches.
  Use when a partner provides a complete implementation plan, or user says "execute plan", "start implementation".
  Does NOT create plans (use tech-spec-planning) or handle single ad-hoc tasks.
---

# Executing Plans

## When to Use
- Partner provides a complete implementation plan
- User says "execute plan" / "start implementation"

## When NOT to Use
- No plan exists (use tech-spec-planning first)
- Single ad-hoc task (just do it)

## Process

1. **Load plan** -- read plan file, identify questions/concerns
2. **Raise concerns** BEFORE starting (if any)
3. **Execute batch** (3 tasks default):
   - Mark in_progress -> follow steps exactly -> verify -> mark completed
4. **Report**: show what was done + verification output, say "Ready for feedback", WAIT
5. **Apply feedback** if any, then next batch (repeat 3-4)
6. **UAT** (mandatory after all tasks):
   - Announce phase change to UAT
   - Read user-acceptance-testing skill + user-spec.md
   - Present UAT checklist, WAIT for user
   - Issues found -> fix -> re-run UAT
7. **Complete**: use finishing-a-development-branch skill

## Stop Conditions

STOP executing immediately when:
- Blocker hit (missing dependency, unclear instruction)
- Plan has critical gaps
- Verification fails repeatedly after fix attempts

Ask for clarification rather than guessing.

## Hard Rules
- No skipping UAT -- implementation is NOT complete without it
- Plan changes mid-execution -> stop, re-read plan, adjust remaining tasks
- No fixes without verification after each batch
