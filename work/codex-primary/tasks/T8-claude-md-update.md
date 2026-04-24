---
executor: claude
risk_class: high-stakes
reasoning: high
wave: 2
---

# Task T8: Project CLAUDE.md — add "Codex Primary Implementer (Experimental, Local)" section

## Your Task
Append a new section to the **project-level** `CLAUDE.md` (at repo root) explaining the new Codex Primary Implementer capability. This is opt-in, experimental, scoped to THIS project only (for now).

**Critical**: do NOT modify global `~/.claude/CLAUDE.md` (that propagates to every project). Only edit this project's `CLAUDE.md` at the repo root.

## Scope Fence
**Allowed paths:**
- `CLAUDE.md` (MODIFY — append section at end, don't touch existing content)

**Forbidden paths:**
- `~/.claude/CLAUDE.md` (global)
- `.claude/shared/templates/new-project/CLAUDE.md` (will sync later after PoC)
- Any other `CLAUDE.md` file
- All other files in repo

## Test Commands
```bash
py -3 -c "from pathlib import Path; p = Path('CLAUDE.md'); content = p.read_text(encoding='utf-8'); assert 'Codex Primary Implementer' in content; assert 'Experimental, Local' in content or 'LOCAL' in content; assert 'codex-implement.py' in content; print('ok')"
```

## Acceptance Criteria (IMMUTABLE)
- [ ] AC1: New section added at END of existing CLAUDE.md (append, don't restructure)
- [ ] AC2: Section heading clearly marks experimental scope: `## Codex Primary Implementer (Experimental, Local)` or similar
- [ ] AC3: Explicit SCOPE notice in first paragraph: "LOCAL to this project only. NOT propagated to other bot projects or new-project template until PoC validates."
- [ ] AC4: Lists the three new phase modes with when-to-use guidance: CODEX_IMPLEMENT, HYBRID_TEAMS, DUAL_IMPLEMENT
- [ ] AC5: Points to tech-spec and ADR-012 for architectural detail
- [ ] AC6: Points to scripts: codex-implement.py, codex-wave.py, codex-scope-check.py
- [ ] AC7: Points to dual-implement skill
- [ ] AC8: Explicit note: "Agent Teams (TeamCreate), skills, memory, codex-ask second opinion — all unchanged and fully supported"
- [ ] AC9: No modification to existing sections of CLAUDE.md
- [ ] AC10: File still parses as valid markdown (no broken links, correct heading hierarchy)
- [ ] All Test Commands exit 0

## Skill Contracts

### verification-before-completion
- Run Test Commands.
- After modification, `git diff CLAUDE.md` to verify only additive changes.

### coding-standards
- Match existing CLAUDE.md tone (terse, rules-focused)
- Use existing heading styles (## for top-level section, ### for subsections)
- Keep new section under ~100 lines

### security-review (applies to high-stakes configuration change)
- This document guides Claude's behavior; bad instructions here cause systemic regressions
- Every new rule must have concrete, testable semantics
- Don't introduce ambiguity ("sometimes use X")

## Read-Only Files (Evaluation Firewall)
- `~/.claude/CLAUDE.md`
- `.claude/shared/templates/new-project/CLAUDE.md`
- `work/codex-primary/tech-spec.md`
- Every file except `CLAUDE.md` at repo root

## Constraints
- ONLY append. If restructuring is tempting — stop and ask.
- Must not contradict any existing rule in global CLAUDE.md or project CLAUDE.md
- Must make clear that OLD flows (AGENT_TEAMS, AO_HYBRID, AO_FLEET) are preferred default; new modes are specialized tools
- Must signal clearly that this is experimental (not yet fleet-wide)

## Handoff Output (MANDATORY)
Standard block. Include explicit diff summary: how many lines added, no lines removed.

## Notes
- Read existing project CLAUDE.md first to understand structure
- Goal is SIGNAL not noise — section should be short and pointer-heavy (links to tech-spec, ADR, skill, phase mode docs)
- Don't duplicate content from tech-spec; just summarize + link
