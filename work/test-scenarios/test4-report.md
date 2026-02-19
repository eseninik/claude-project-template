# Test 4 Report: QA Validation Gate

**Scenario:** Pretend IMPLEMENT phase just completed for `calculator.py` + `test_calculator.py`. Evaluate whether CLAUDE.md rules and `qa-validation-loop` skill actually trigger QA behavior.

---

## 1. Did you find the "After IMPLEMENT (QA Gate)" rule in CLAUDE.md?

**YES.**

Found at lines 174-181 under `# BLOCKING RULES` > `## After IMPLEMENT (QA Gate)`. The rule is:

```
1. Collect acceptance criteria from task/spec files
2. Spawn Reviewer agent: analyze changed files against criteria
3. If CRITICAL/IMPORTANT issues -> spawn Fixer agent
4. Re-review with fresh agent (max 3 cycles)
5. Track in work/qa-issues.md
6. Same issue 3+ times -> BLOCKED, ask human
```

Additionally, the HARD CONSTRAINTS table (line 143) contains:
> "Не пропускать QA review после IMPLEMENT | Запусти qa-validation-loop перед TEST"

And the CONTEXT LOADING TRIGGERS table (line 205) says:
> "QA validation needed | Follow 'After IMPLEMENT (QA Gate)' in BLOCKING RULES above"

And the KNOWLEDGE LOCATIONS table (line 222) points to:
> "QA validation skill | .claude/skills/qa-validation-loop/SKILL.md"

**Assessment:** The rule is present in FOUR separate locations (blocking rule, hard constraint, context trigger, knowledge location). That is strong redundancy.

---

## 2. Does the rule clearly describe what to do?

**YES, but with caveats.**

The inline rule in CLAUDE.md is a clear 6-step process. It tells me:
- WHAT to do (collect criteria, spawn reviewer, spawn fixer, re-review, track, escalate)
- WHEN to stop (max 3 cycles, or same issue 3+ times)
- WHERE to track (work/qa-issues.md)

**What is clear:**
- The sequence: reviewer -> evaluate -> fixer -> re-reviewer
- The escalation path: 3+ same issue -> ask human
- The tracking location: work/qa-issues.md

**What is NOT clear from the inline rule alone:**
- HOW to spawn the reviewer (Task tool? TeamCreate? What prompt to use?)
- What constitutes "acceptance criteria" if there is no task/spec file
- The verdict taxonomy (PASS/CONCERNS/REWORK/ESCALATE) is NOT in the inline rule -- only in the skill
- The reviewer and fixer prompt templates are NOT in the inline rule -- only in the skill
- Whether the reviewer should be a Task subagent or a TeamCreate teammate

---

## 3. Would you actually spawn a Reviewer agent in real work?

**YES, but only because the skill fills the gaps.**

Here is my honest reasoning chain:

1. I finish implementing calculator.py
2. I see the BLOCKING RULE "After IMPLEMENT (QA Gate)" -- this fires because I am explicitly looking for blocking rules
3. The rule says "Spawn Reviewer agent" -- OK, but how?
4. I check the CONTEXT LOADING TRIGGERS table -- it says "Follow 'After IMPLEMENT (QA Gate)' in BLOCKING RULES above", which is circular (points back to itself)
5. I check KNOWLEDGE LOCATIONS -- it points to `.claude/skills/qa-validation-loop/SKILL.md`
6. I load the skill -- NOW I get the reviewer prompt template and process details

**Problem:** Steps 4-6 require me to self-navigate. In a compaction scenario where I lose context, the inline rule alone would NOT give me enough to actually execute. I would know I SHOULD spawn a reviewer, but I would not have the prompt template or verdict taxonomy without loading the skill.

**In practice:** For this specific calculator scenario, I would:
- Collect acceptance criteria (functions work, tests pass, divide-by-zero handled)
- Spawn a Task subagent as Reviewer with the changed files and criteria
- If issues found (the fibonacci docstring says "BUG: off-by-one error" -- a reviewer would flag this), spawn a Fixer
- Track in work/qa-issues.md

---

## 4. Did the qa-validation-loop skill add value beyond the inline rule?

**YES, significantly.**

The skill adds these critical details that the inline rule lacks:

| Detail | Inline Rule | Skill |
|--------|------------|-------|
| Reviewer prompt template | Missing | "Analyze these files against acceptance criteria. For each issue: file, line, severity..." |
| Fixer prompt template | Missing | "Fix CRITICAL and IMPORTANT issues. Do not refactor. Verify each fix..." |
| Severity taxonomy | Missing | CRITICAL / IMPORTANT / MINOR |
| Verdict taxonomy | Missing | PASS / CONCERNS / REWORK / ESCALATE |
| What to skip in fixer | Missing | MINOR issues (fixer only handles CRITICAL+IMPORTANT) |
| NEEDS_HUMAN marker | Missing | "If unclear: mark NEEDS_HUMAN and skip" |
| Fresh re-reviewer | Mentioned ("fresh agent") | Explicit: "new agent, NOT the original reviewer" |
| What tool to use | Missing | "Task tool subagent" |

**The inline rule tells you WHAT to do. The skill tells you HOW to do it.** Both are needed.

---

## 5. Are the inline rules sufficient to guide QA behavior without loading the full skill?

**NO.**

An agent following only the inline rule would know it must:
- Spawn a reviewer
- Spawn a fixer if needed
- Track in qa-issues.md
- Escalate after 3 cycles

But it would NOT know:
- What prompt to give the reviewer (the reviewer prompt template is only in the skill)
- What severity levels to use (CRITICAL/IMPORTANT/MINOR only in the skill)
- What verdict to emit (PASS/CONCERNS/REWORK/ESCALATE only in the skill)
- That the fixer should skip MINOR issues (only in the skill)
- That unclear issues should be marked NEEDS_HUMAN (only in the skill)

An experienced agent could improvise all of these. But the point of a skill system is to NOT rely on improvisation. The inline rule is a trigger; the skill is the execution guide.

---

## 6. What's missing or unclear?

### In the inline rule (CLAUDE.md):

1. **No pointer to load the skill.** The CONTEXT LOADING TRIGGERS entry for "QA validation needed" says "Follow 'After IMPLEMENT (QA Gate)' in BLOCKING RULES above" -- this is circular. It should say: `cat .claude/skills/qa-validation-loop/SKILL.md` like every other trigger entry. This is the biggest gap.

2. **No automatic trigger mechanism.** The rule says "After IMPLEMENT" but there is no pipeline phase detection that automatically triggers it. In a pipeline with phases, the agent must manually remember to check blocking rules after completing IMPLEMENT. If the pipeline template included a built-in "QA_GATE" phase between IMPLEMENT and TEST, it would be automatic.

3. **"acceptance criteria from task/spec files" is vague.** What if there are no spec files? The calculator scenario has no spec file. The agent must improvise criteria from the code and tests themselves.

4. **work/qa-issues.md format is unspecified.** The inline rule says "Track in work/qa-issues.md" but does not define the format. The skill says "iteration, issues found, issues fixed" but no template is provided.

### In the skill:

5. **No example of a complete qa-issues.md entry.** Would be helpful for consistency across sessions.

6. **Task tool vs TeamCreate is ambiguous.** The skill says "Task tool subagent" but the Agent Teams rule says "3+ tasks -> TeamCreate". If you have reviewer + fixer + re-reviewer, that is 3 agents -- does the Agent Teams rule override? In practice, these should be sequential (Task tool), not parallel (TeamCreate), but the rules could conflict.

### In the overall system:

7. **The hard constraint (line 143) is in Russian while the blocking rule is in English.** Mixed languages could cause an agent to miss one of them during pattern matching.

8. **verification-before-completion vs qa-validation-loop overlap.** The verification skill says "Does NOT replace qa-validation-loop for full review cycles" which is good, but the ordering is unclear: does QA validation loop run BEFORE or AFTER verification-before-completion? Both are "after implement" / "before done" triggers.

---

## 7. Overall: Would the QA gate trigger reliably in real autonomous work?

**PARTIALLY -- maybe 60-70% of the time.**

### When it WOULD trigger:
- Agent is following a PIPELINE.md with explicit phases and reads blocking rules between phases
- Agent is operating in a session where CLAUDE.md context is fresh (no compaction)
- Agent has been explicitly told "run QA" or "qa-validation-loop" by the user

### When it WOULD NOT trigger:
- After compaction: the agent re-reads PIPELINE.md and STATE.md, but does NOT re-read the blocking rules section. It would jump straight to the next phase.
- In ad-hoc work without a pipeline: the "After IMPLEMENT" trigger assumes pipeline phases exist. In freeform coding (user says "implement X"), the agent would not think "I just finished IMPLEMENT phase, check blocking rules."
- The circular context loading trigger (pointing back to itself instead of to the skill) means the agent might find the inline rule but not load the full skill, leading to a half-baked QA process.

### What would make it 90%+ reliable:
1. **Fix the circular trigger:** Change `CONTEXT LOADING TRIGGERS` entry to `cat .claude/skills/qa-validation-loop/SKILL.md`
2. **Add QA_GATE as a mandatory pipeline phase** in the pipeline template (between IMPLEMENT and TEST), so it is structural, not behavioral
3. **Add the reviewer prompt template to the inline rule** so the agent can execute without loading the skill
4. **Add to compaction summary instructions:** "After IMPLEMENT -> run QA gate (blocking rule)"

---

## Summary Table

| Question | Answer |
|----------|--------|
| Found "After IMPLEMENT (QA Gate)" rule? | YES -- in 4 locations |
| Rule clearly actionable? | YES for trigger, NO for execution details |
| Would spawn Reviewer in real work? | YES, but need the skill for prompts |
| Skill adds value beyond inline? | YES, significantly |
| Inline sufficient without skill? | NO |
| QA gate triggers reliably? | 60-70% -- compaction and circular triggers are weak points |

**Bottom line:** The QA gate is well-designed in principle. The inline rule + skill complement each other properly. The main failure mode is that the system relies on the agent voluntarily checking blocking rules after implementation, and the context loading trigger is circular (does not point to the skill file). Fix those two things and reliability jumps significantly.
