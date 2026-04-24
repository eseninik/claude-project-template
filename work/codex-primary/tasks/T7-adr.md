---
executor: claude
risk_class: routine
reasoning: medium
wave: 2
---

# Task T7: ADR-012 Codex Primary Implementer

## Your Task
Create `.claude/adr/adr-012-codex-primary-implementer.md` — architectural decision record documenting the choice to add GPT-5.5 as primary implementer via Codex CLI, preserving Opus as planner.

Must follow the format of `.claude/adr/_template.md` (read that first).

## Scope Fence
**Allowed paths:**
- `.claude/adr/adr-012-codex-primary-implementer.md` (new)

**Forbidden paths:**
- Other ADRs (read them for reference, don't modify)
- `work/codex-primary/tech-spec.md`
- `.claude/adr/decisions.md` (update only if other ADRs do — check the pattern; if yes, add index line; if no, skip)

## Test Commands
```bash
py -3 -c "from pathlib import Path; p = Path('.claude/adr/adr-012-codex-primary-implementer.md'); assert p.exists(); content = p.read_text(); required = ['# ADR-012', '## Context', '## Decision', '## Consequences', '## Alternatives']; missing = [s for s in required if s not in content]; assert not missing, f'missing: {missing}'; print('ok')"
```

## Acceptance Criteria (IMMUTABLE)
- [ ] AC1: File exists at `.claude/adr/adr-012-codex-primary-implementer.md`
- [ ] AC2: Follows `.claude/adr/_template.md` structure — sections: Context, Decision, Consequences (positive + negative), Alternatives Considered, Status
- [ ] AC3: Status field is `ACCEPTED` with date 2026-04-24
- [ ] AC4: Context section summarizes the problem: GPT-5.5 codes better than Opus 4.7 per Every/benchmarks, but Opus is better at planning. How to combine?
- [ ] AC5: Decision section clearly states: Opus = planner/reviewer, Codex = executor via codex-implement.py / codex-wave.py / dual-implement skill. Three new phase modes (CODEX_IMPLEMENT, HYBRID_TEAMS, DUAL_IMPLEMENT). Local scope only initially.
- [ ] AC6: Consequences section lists both positive (speed, better codes for routine tasks) and negative (workspace-write sandbox risk, Codex doesn't see skills directly, $20 tariff limits)
- [ ] AC7: Alternatives section lists at least 4 alternatives: full role swap (Codex does everything), model upgrade only (keep Codex as advisor, just switch to 5.5), task-class routing only (reuse session-task-class.py), status quo (keep Opus primary)
- [ ] AC8: Cross-links to tech-spec.md and each new phase mode doc
- [ ] No TODO / FIXME / placeholder
- [ ] All Test Commands exit 0

## Skill Contracts

### verification-before-completion
- Read `.claude/adr/_template.md` FIRST; match its structure.
- Run Test Commands at end.

### coding-standards
- ADR tone: concise, decision-focused, historical record
- No more than ~300 lines — ADRs should be digestible
- Past-tense for context, present-tense for decision, future-tense for consequences

## Read-Only Files (Evaluation Firewall)
- `work/codex-primary/tech-spec.md`
- `.claude/adr/_template.md`
- Other ADRs

## Constraints
- Must cite the concrete evidence that prompted the decision: Every review metrics, Terminal-Bench 2.0 scores, Opus vs GPT-5.5 trade-offs
- Must note scope limitation (LOCAL only) and future-work (global propagation contingent on PoC)

## Handoff Output (MANDATORY)
Standard block. Files Modified: 1-2 files.

## Notes
- ADR numbering: verify no existing ADR-012 (use next available if conflict)
- Cross-check with other ADRs for style consistency
