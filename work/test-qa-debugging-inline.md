## Test: QA Gate + Debugging Inline

### QA Gate in CLAUDE.md
- Full procedure inlined: YES
- Steps include: reviewer spawn, fixer spawn, max 3 cycles, escalation: YES
- "cat skill" reference in QA section: NO (correct -- none found)

Details: Lines 175-181 of CLAUDE.md contain "After IMPLEMENT (QA Gate)" with 6 steps covering:
  1. Collect acceptance criteria
  2. Spawn Reviewer agent
  3. Spawn Fixer agent on CRITICAL/IMPORTANT issues
  4. Re-review with fresh agent (max 3 cycles)
  5. Track in work/qa-issues.md
  6. Escalation: same issue 3+ times -> BLOCKED, ask human

### Debugging in CLAUDE.md
- 4-phase framework inlined: YES (condensed into 5 steps)
- Steps include: investigate, hypothesize, test, fix: YES
- "cat skill" reference in debugging section: NO (correct -- none found)

Details: Lines 183-189 of CLAUDE.md contain "Debugging (when error/bug occurs)" with 5 steps:
  1. Investigate: "Read error completely -- find exact failure line"
  2. Hypothesize + Test: "Form 2-3 hypotheses, test most likely first"
  3. Fix: "Fix root cause, not symptom"
  4. Verify: "Verify fix + check regressions"
  5. Escalate: "3+ failed attempts -> change approach entirely"

Note: The 4 phases (investigate, hypothesize, test, fix) are present but "hypothesize" and "test" are merged into a single step. This is an acceptable condensation for inline rules -- the full 4-phase breakdown remains in the skill file for detailed reference.

### Skill Files (lean check)
- qa-validation-loop lines: 39 (should be <50) -- PASS
- systematic-debugging lines: 38 (should be <50) -- PASS
- Both are checklists, not detailed procedures: YES

Details:
  - qa-validation-loop/SKILL.md: 39 lines, structured as process steps + prompts + verdicts
  - systematic-debugging/SKILL.md: 38 lines, structured as 4 phases + red flags checklist

### CONTEXT LOADING TRIGGERS
- QA validation row references BLOCKING RULES (not skill file): YES

Details: Line 206 reads:
  `| QA validation needed | Follow "After IMPLEMENT (QA Gate)" in BLOCKING RULES above |`
This correctly points to the inline blocking rule rather than a `cat` command to a skill file.

### Additional Checks
- No `cat .claude/skills/qa-validation-loop` references anywhere in CLAUDE.md: CONFIRMED
- No `cat .claude/skills/systematic-debugging` references anywhere in CLAUDE.md: CONFIRMED
- QA skill is listed in KNOWLEDGE LOCATIONS table (line 224) as a reference location, which is appropriate for discoverability without being a loading trigger

### VERDICT: PASS

All criteria met:
1. QA Gate procedure is fully inlined in BLOCKING RULES with all required elements (reviewer spawn, fixer spawn, max 3 cycles, escalation).
2. Debugging framework is inlined in BLOCKING RULES with all 4 phases represented (investigate, hypothesize, test, fix) in condensed form.
3. No "cat skill" references exist in either blocking rule section.
4. Both skill files are lean checklists under 50 lines each.
5. CONTEXT LOADING TRIGGERS correctly routes QA validation to BLOCKING RULES, not to a skill file.
