# QA Review Report: Experiment Loop + Results Board + Unlimited Mode + Evaluation Firewall

**Date:** 2026-03-11
**Reviewer:** qa-reviewer agent
**VERDICT: PASS**

---

## Files Reviewed

| # | File | Status | Issues |
|---|------|--------|--------|
| 1 | `.claude/skills/experiment-loop/SKILL.md` | PASS | 0 |
| 2 | `.claude/guides/results-board.md` | PASS | 0 |
| 3 | `.claude/skills/self-completion/SKILL.md` | PASS | 0 |
| 4 | `.claude/skills/qa-validation-loop/SKILL.md` | PASS | 0 |
| 5 | `.claude/guides/teammate-prompt-template.md` | PASS | 0 |
| 6 | `.claude/agents/registry.md` | PASS | 0 |
| 7 | `CLAUDE.md` | PASS | 0 |
| 8 | `.claude/shared/work-templates/PIPELINE-v3.md` | PASS | 0 |

---

## Per-File Analysis

### 1. experiment-loop/SKILL.md

- **Frontmatter:** Has `name`, `description`, `roles` -- correct format, matches other skills
- **Description formula:** follows `[What] + Use when [triggers] + Do NOT use for [negatives]` pattern
- **Roles:** `[experimenter, pipeline-lead]` -- both exist in registry
- **Algorithm:** Clear pseudocode with numbered steps, budget/time/context safety checks
- **Safety valves:** 6 defined (budget, time, context, crash, stagnation, scope) -- exceeds minimum
- **Evaluation Firewall:** Present (lines 56-62), consistent with qa-validation-loop definition
- **State preservation:** Defined with template (lines 142-153)
- **Experiment log format:** Clear table format with examples (lines 116-138)
- **Integration with Pipeline:** Shows EXPERIMENT phase template matching PIPELINE-v3.md
- **Completion markers:** Table of 5 markers with meanings (lines 207-213)

### 2. results-board.md

- **Entry format:** Defined with timestamp, agent_name, task_name, approach, result, status, commit, insight (lines 33-42)
- **Agent protocol:** Before-starting (read board) and after-completing (append result) defined (lines 73-93)
- **Integration points:** Table with 5 systems (Agent Teams, Experiment Loop, Pipeline phases, Self-completion, QA Review)
- **Anti-patterns:** Table with 5 anti-patterns and fixes
- **Board initialization:** Template provided (lines 99-108)

### 3. self-completion/SKILL.md

- **Unlimited mode section:** Present (lines 137-203), clearly separated
- **5 safety valves:** Context pressure, wall-clock timeout, idle detection, progress stall, iteration checkpoint -- all defined in table (lines 146-152)
- **Why each valve exists:** Explained (lines 155-160)
- **State preservation:** Template at lines 166-189, includes status, reason, completed/remaining tasks, resume instructions
- **Algorithm updated:** Lines 33-57 include `max_iterations == unlimited` branch with all safety valve checks
- **Idle detection clarified:** "no git-diff changes (not self-reported)" (line 48) -- good, prevents gaming
- **Configuration:** Shows `max_iterations: unlimited` with all configurable params (lines 196-203)

### 4. qa-validation-loop/SKILL.md

- **Evaluation Firewall section:** Present (lines 29-45), clearly defined
- **Reviewer check steps:** 4-step verification process (lines 37-44):
  1. List modified files
  2. Check against test/eval patterns
  3. Flag violations as CRITICAL (with exception for NEW test files)
  4. Flag weakened acceptance criteria
- **Why this matters:** Explained with Karpathy reference (line 45)
- **Consistent with experiment-loop:** Both reference the same firewall concept

### 5. teammate-prompt-template.md

- **Read-Only Files section:** Present in template (lines 77-84), titled "Read-Only Files (Evaluation Firewall)"
- **Default list:** test files, acceptance criteria, eval scripts, CI/CD configs
- **Escape clause:** "If you need to modify any read-only file, STOP and ask the team lead first"
- **Results Board section:** Present in template (lines 42-46), with read-before/write-after protocol
- **Position in template:** Results Board after Verification Rules, Read-Only Files at end -- logical ordering

### 6. registry.md

- **Experimenter type:** Present in Implementation Agents table (line 69)
- **Properties:** Tools=full, Skills=experiment-loop+verification-before-completion, Thinking=deep, Context=full, Memory=full, MCP=none
- **Notes:** Line 74 describes the type correctly
- **"All three MUST run tests":** Line 75 updated to include experimenter alongside coder and coder-complex

### 7. CLAUDE.md

- **Experimenter in TEAM ROLE SKILLS MAPPING:** Line 241 -- `Experimenter | experimenter | experiment-loop, verification-before-completion`
- **Evaluation Firewall constraint in HARD CONSTRAINTS:** Line 271 -- new row added
- **Results Board trigger in Agent Teams:** Line 50 -- "DO NOT skip reading work/results-board.md before starting"
- **Results Board in CONTEXT LOADING TRIGGERS (Guides):** Line 425 -- `Agent Teams coordination | cat .claude/guides/results-board.md`
- **Experiment-loop in Skills table:** Line 445 -- `Optimization/experiment task | experiment-loop`
- **Knowledge locations:** Lines 472-473 -- both experiment-loop skill and results-board guide listed
- **Skills count note:** The description says "11 remaining" in TEAM ROLE SKILLS MAPPING header but there are now 12 skills with experiment-loop added -- see MINOR issue below

### 8. PIPELINE-v3.md

- **EXPERIMENT phase template:** Present as blockquote (lines 179-194)
- **Correct transitions:** On PASS -> IMPLEMENT, On FAIL -> PLAN, On BLOCKED -> STOP
- **Gate:** "best metric meets threshold OR budget exhausted"
- **Outputs:** experiment-log.md, experiment-state.md -- matches skill's output files
- **Skill reference:** Points to `.claude/skills/experiment-loop/SKILL.md` (line 194)
- **Consistent with experiment-loop SKILL.md:** The phase template in PIPELINE-v3.md (lines 181-192) matches the "Integration with Pipeline" section in the skill (lines 159-171)

---

## Cross-Reference Checks

| Check | Result |
|-------|--------|
| CLAUDE.md mentions experiment-loop -> skill exists | PASS |
| CLAUDE.md mentions results-board -> guide exists | PASS |
| registry.md has experimenter -> CLAUDE.md TEAM ROLE SKILLS MAPPING has it | PASS |
| teammate-prompt-template.md has Results Board -> guide exists | PASS |
| experiment-loop references results-board -> guide exists | PASS |
| experiment-loop references work/{feature}/experiment-log.md -> PIPELINE-v3 outputs match | PASS |
| experiment-loop Evaluation Firewall -> qa-validation-loop Evaluation Firewall consistent | PASS |
| CLAUDE.md knowledge locations -> both new files listed | PASS |
| CLAUDE.md skills triggers -> experiment-loop listed | PASS |
| CLAUDE.md hard constraints -> Evaluation Firewall row present | PASS |
| registry.md experimenter skills -> match CLAUDE.md TEAM ROLE SKILLS MAPPING | PASS |
| self-completion safety valves -> experiment-loop safety valves consistent concepts | PASS |

---

## Issues Found

### MINOR

1. **CLAUDE.md:224** -- TEAM ROLE SKILLS MAPPING header says "Skills (from 11 remaining)" but with experiment-loop added there are now 12 skills. The count "11" should be updated to "12". This is cosmetic and does not affect functionality.

---

## Overall Assessment

All 8 files are well-integrated, consistent with each other, and follow established project patterns. The four features (experiment-loop skill, results-board guide, unlimited mode with safety valves, evaluation firewall) are fully wired across CLAUDE.md, registry.md, teammate-prompt-template.md, and PIPELINE-v3.md. Cross-references are bidirectional and correct. No broken file paths found. No contradictions with existing content.

The only finding is a minor skill count label ("11 remaining" -> should be "12") in the TEAM ROLE SKILLS MAPPING table header in CLAUDE.md.

**VERDICT: PASS** (1 MINOR issue, no CRITICAL or IMPORTANT issues)
