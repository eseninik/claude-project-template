---
name: OpenSpec: Apply
description: Implement an approved OpenSpec change and keep tasks in sync.
category: OpenSpec
tags: [openspec, apply]
---
<!-- OPENSPEC:START -->
**Guardrails**
- Favor straightforward, minimal implementations first and add complexity only when it is requested or clearly required.
- Keep changes tightly scoped to the requested outcome.
- Refer to `openspec/AGENTS.md` (located inside the `openspec/` directory—run `ls openspec` or `openspec update` if you don't see it) if you need additional OpenSpec conventions or clarifications.

**Steps**
Track these steps as TODOs and complete them one by one.
1. Read `changes/<id>/proposal.md`, `design.md` (if present), and `tasks.md` to confirm scope and acceptance criteria.
2. **Load skills index:** `cat .claude/skills/SKILLS_INDEX.md` — select appropriate skills for implementation.
3. For each task:
   - Load selected skills: `cat .claude/skills/<folder>/SKILL.md`
   - Execute task following skill guidance
   - **Test the change** (write test script, run, analyze logs, compare with requirements)
   - Mark `- [x]` in tasks.md after verified completion
4. After ALL tasks: load `verification-before-completion` skill and verify everything works.
5. Report: "Ready for `openspec archive`"

**Reference**
- Use `openspec show <id> --json --deltas-only` if you need additional context from the proposal while implementing.
<!-- OPENSPEC:END -->
