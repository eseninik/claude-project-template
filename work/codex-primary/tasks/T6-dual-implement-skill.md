---
executor: claude
risk_class: routine
reasoning: high
wave: 2
---

# Task T6: `.claude/skills/dual-implement/SKILL.md`

## Your Task
Create the dual-implement skill at `.claude/skills/dual-implement/SKILL.md`. This skill orchestrates Level 3 — parallel dual implementation (Claude teammate + Codex GPT-5.5) against the same task spec, with Opus judging the diffs.

See tech-spec.md Section 10 for complete protocol.

## Scope Fence
**Allowed paths:**
- `.claude/skills/dual-implement/SKILL.md` (new)
- `.claude/skills/dual-implement/references/` (new, optional — can hold longer examples)
- `.claude/skills/dual-implement/examples.md` (optional — usage examples)

**Forbidden paths:**
- `.claude/shared/templates/new-project/.claude/skills/**` (will sync later)
- Other skills (don't modify them)
- `.claude/scripts/codex-implement.py` and friends (T1/T2 outputs; this skill CALLS them, doesn't define them)

## Test Commands
```bash
py -3 -c "import yaml; from pathlib import Path; content = Path('.claude/skills/dual-implement/SKILL.md').read_text(); assert content.startswith('---\n'), 'missing frontmatter'; fm_end = content.index('\n---\n', 4); fm = yaml.safe_load(content[4:fm_end]); assert 'name' in fm and fm['name'] == 'dual-implement'; assert 'description' in fm and 50 < len(fm['description']) < 400, f'desc length {len(fm.get(\"description\",\"\"))}'; assert 'Use when' in fm['description']; assert 'Do NOT use' in fm['description']; print('ok')"
```

## Acceptance Criteria (IMMUTABLE)
- [ ] AC1: File starts with YAML frontmatter containing `name: dual-implement`, valid `description` (50-400 chars, with "Use when" and "Do NOT use" phrases), `roles` list
- [ ] AC2: Description follows skill-conductor formula: `[What] + Use when [triggers] + Do NOT use for [negatives]`
- [ ] AC3: Body contains sections: `## Triggers`, `## Protocol`, `## When NOT to use`, `## Examples`, `## Related` (cross-links to other skills: cross-model-review, verification-before-completion, ao-hybrid-spawn)
- [ ] AC4: Protocol section lists exact steps from tech-spec 10.2 (ensure trigger, create 2 worktrees, spawn parallel, wait, judge, merge/archive)
- [ ] AC5: Protocol mentions: Claude worktree spawned via `TeamCreate` + `spawn-agent.py`; Codex worktree via `codex-implement.py`
- [ ] AC6: Has at least one Example showing a real case (e.g., "auth middleware replacement")
- [ ] AC7: Body under 500 lines (long examples go in references/ or examples.md)
- [ ] AC8: No unused workflow/process cruft in description (description is for triggering the skill, body is for execution)
- [ ] All Test Commands exit 0

## Skill Contracts

### verification-before-completion
- Run Test Commands. Frontmatter validator must pass.
- Read tech-spec Section 10 FIRST; your skill must match protocol exactly.

### skill-conductor (contract extract — this is a skill about skills)
- description format: `[What] + Use when [triggers] + Do NOT use for [negatives]`
- Frontmatter fields: only `name`, `description`, `roles` — no version/changelog
- Body: triggers, protocol, when-not-to-use, examples, related
- NO workflow in description — agent must read body

### coding-standards
- Mirror existing skill format (e.g., `.claude/skills/cross-model-review/SKILL.md` or `.claude/skills/qa-validation-loop/SKILL.md`)
- Clear language, action-oriented

## Read-Only Files (Evaluation Firewall)
- `work/codex-primary/tech-spec.md`
- Other skills (reference them via `## Related`, don't modify them)
- This task-N.md

## Constraints
- Skill must be invokable via the `Skill` tool with `skill: dual-implement`
- Must cross-reference: `cross-model-review`, `verification-before-completion`, `subagent-driven-development`, `using-git-worktrees`, `ao-hybrid-spawn`
- Triggers: task has `executor: dual` OR `risk_class: high-stakes` OR user says "dual implement" / "compare implementations"

## Handoff Output (MANDATORY)
Standard block. Files Modified: 1-3 files (SKILL.md + optional examples/references).

## Notes
- Read `.claude/skills/cross-model-review/SKILL.md` as the closest existing analog
- Read `.claude/skills/skill-conductor/SKILL.md` or `references/` for description-writing formula
- The skill does NOT have to run any code itself — it's an orchestration skill; the code runs via TeamCreate + codex-implement.py as dispatched by Opus
