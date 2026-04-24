---
executor: claude
risk_class: routine
reasoning: high
wave: 1
---

# Task T3: Phase Mode Documentation

## Your Task
Create three new phase-mode documents in `.claude/shared/work-templates/phases/`:
- `IMPLEMENT-CODEX.md` — for `Mode: CODEX_IMPLEMENT`
- `IMPLEMENT-HYBRID.md` — for `Mode: HYBRID_TEAMS`
- `DUAL-IMPLEMENT.md` — for `Mode: DUAL_IMPLEMENT`

These mirror the format of existing phase docs in the same directory (read one as template).

Content MUST match tech-spec.md Section 5 exactly (no inventing new behavior).

## Scope Fence
**Allowed paths:**
- `.claude/shared/work-templates/phases/IMPLEMENT-CODEX.md`
- `.claude/shared/work-templates/phases/IMPLEMENT-HYBRID.md`
- `.claude/shared/work-templates/phases/DUAL-IMPLEMENT.md`

**Forbidden paths:**
- `.claude/shared/templates/new-project/**` (out of scope — LOCAL only)
- Other phase docs (don't modify existing phase templates)
- `work/codex-primary/tech-spec.md`

## Test Commands
```bash
py -3 -c "from pathlib import Path; files = ['.claude/shared/work-templates/phases/IMPLEMENT-CODEX.md', '.claude/shared/work-templates/phases/IMPLEMENT-HYBRID.md', '.claude/shared/work-templates/phases/DUAL-IMPLEMENT.md']; [print(f, Path(f).exists(), Path(f).stat().st_size) for f in files]"
```

All three files must exist with size > 500 bytes.

## Acceptance Criteria (IMMUTABLE)
- [ ] AC1: All three files exist
- [ ] AC2: Each follows the structure of an existing phase doc (read `.claude/shared/work-templates/phases/IMPLEMENT.md` first as baseline)
- [ ] AC3: `IMPLEMENT-CODEX.md` describes: trigger, dispatch, Claude's role, when to use, when NOT to use — per tech-spec 5.1
- [ ] AC4: `IMPLEMENT-HYBRID.md` describes: per-task executor dispatch, parallelism for both Claude (TeamCreate) + Codex (codex-wave.py) — per tech-spec 5.2
- [ ] AC5: `DUAL-IMPLEMENT.md` describes: parallel dual executors, judge step, merge strategy — per tech-spec 5.3
- [ ] AC6: Each doc has concrete command examples (exact CLI invocations with real paths)
- [ ] AC7: Each doc has explicit "Relationship to AGENT_TEAMS/AO_HYBRID/AO_FLEET" note — they are orthogonal
- [ ] AC8: No TODO / FIXME / placeholder markers in final version
- [ ] AC9: No mention of future/out-of-scope items (e.g., no mention of template sync or fleet propagation — those are future work)
- [ ] All Test Commands exit 0

## Skill Contracts

### verification-before-completion
- Read tech-spec.md Section 5 before starting. Your docs must match exactly.
- Run Test Commands at end.
- Verify each AC.

### coding-standards
- Match the existing phase doc style (headings, sections, tone)
- Consistent heading hierarchy (# / ## / ###)
- Use fenced code blocks for shell examples
- Russian OR English — match existing phase docs (they're in English; stay in English)

## Read-Only Files (Evaluation Firewall)
- `work/codex-primary/tech-spec.md`
- Existing phase docs in `.claude/shared/work-templates/phases/` (reference only, don't modify)
- This task-N.md

## Constraints
- Length: each doc roughly 80-150 lines
- Must cross-link to scripts: `codex-implement.py`, `codex-wave.py`, dual-implement skill
- Must cross-link to tech-spec and ADR-012 (even though ADR not yet written — use placeholder path `.claude/adr/adr-012-codex-primary-implementer.md`)

## Handoff Output (MANDATORY)
Standard block. Files Modified: 3 files.

## Notes
- No code written in this task — pure documentation
- Base template: read `.claude/shared/work-templates/phases/IMPLEMENT.md` first, then mimic its layout
