---
executor: claude
risk_class: routine
reasoning: high
wave: 1
---

# Task T4: Extended task-N.md Template (`task-codex-template.md`)

## Your Task
Create `.claude/shared/work-templates/task-codex-template.md` — the canonical template for Codex-executable task files. Contains all required sections from tech-spec.md Section 4.

This template is used by Opus (manually or via task-decomposition skill extension) when preparing tasks for Codex or dual execution.

## Scope Fence
**Allowed paths:**
- `.claude/shared/work-templates/task-codex-template.md` (new)
- `.claude/shared/work-templates/README.md` (append note about new template, if file exists; otherwise skip)

**Forbidden paths:**
- `.claude/shared/templates/new-project/**`
- Other work-templates files
- `work/codex-primary/tech-spec.md`

## Test Commands
```bash
py -3 -c "from pathlib import Path; p = Path('.claude/shared/work-templates/task-codex-template.md'); assert p.exists(), 'missing'; content = p.read_text(); required = ['executor:', 'risk_class:', 'reasoning:', '## Scope Fence', '## Test Commands', '## Acceptance Criteria (IMMUTABLE)', '## Skill Contracts', '## Read-Only Files', '## Handoff Output']; missing = [s for s in required if s not in content]; assert not missing, f'missing sections: {missing}'; print('ok')"
```

## Acceptance Criteria (IMMUTABLE)
- [ ] AC1: File contains YAML frontmatter with `executor`, `risk_class`, `reasoning` fields (with allowed-values comments)
- [ ] AC2: File contains these exact section headings: `## Your Task`, `## Scope Fence`, `## Test Commands`, `## Acceptance Criteria (IMMUTABLE)`, `## Skill Contracts`, `## Read-Only Files (Evaluation Firewall)`, `## Constraints`, `## Handoff Output (MANDATORY)`
- [ ] AC3: `## Skill Contracts` section has sub-examples for: verification-before-completion, logging-standards, security-review (with note "only for auth/crypto/secrets tasks"), coding-standards
- [ ] AC4: Each section has a `{placeholder}` or clear comment marker where users fill in content
- [ ] AC5: Has a "How to use" block at the top explaining when to choose `executor: claude` vs `codex` vs `dual`
- [ ] AC6: References tech-spec.md and ADR-012 (placeholder link is fine)
- [ ] All Test Commands exit 0

## Skill Contracts

### verification-before-completion
- Read tech-spec.md Section 4 — your template must match.
- Run Test Commands at end.

### coding-standards
- Mirror the structure and tone of other work-templates
- Clear placeholder markers (e.g., `{replace me}`)

## Read-Only Files (Evaluation Firewall)
- `work/codex-primary/tech-spec.md`
- This task-N.md

## Constraints
- Length: ~100-150 lines
- Must be usable as-is (copy → edit) — should work when somebody reads it in 6 months without context
- Cross-linking: point to `teammate-prompt-template.md` (sibling doc), tech-spec, ADR-012

## Handoff Output (MANDATORY)
Standard block. Files Modified: 1 file (or 2 if README updated).

## Notes
- Reference doc: `.claude/guides/teammate-prompt-template.md` — similar structural goals, different audience
- Keep it readable — this is user-facing template, not internal spec
