---
name: skill-evolution
description: >
  Self-evolving pattern for skills: after successful execution, proposes
  improvements to SKILL.md, examples.md, and reference.md based on real usage.
  Skill Conductor validates changes. Use when a skill was just executed
  successfully and produced useful learnings, when user says "improve this
  skill", "update skill from experience", or after experiment-loop completes.
  Do NOT use for creating new skills (use skill-conductor CREATE), for manual
  skill editing, or when skill execution failed.
roles: [pipeline-lead, experimenter]
---

# Skill Evolution

## Overview

Skills improve through a genetic algorithm-like cycle:
- **Mutation**: After successful execution, agent proposes changes
- **Selection**: Skill Conductor (Mode 4 REVIEW) validates/optimizes
- **Application**: Approved changes are applied to skill files

Without selection (Conductor gate), skills degrade via bloat.
Without mutation (self-evolving), skills stagnate.

## Evolution Trigger

After ANY skill executes successfully, the lead agent MAY trigger evolution if:
1. The skill execution revealed a new pattern (something worked unexpectedly well)
2. The skill execution hit an edge case not covered by current instructions
3. A mistake was made that the skill should warn about in future

Evolution is OPTIONAL — not every execution needs it. Only trigger when there's genuine learning.

## Evolution Protocol

```
1. COLLECT
   - What skill was executed?
   - What was the input/context?
   - What was the outcome? (success/partial/unexpected)
   - What learning emerged? (new pattern / edge case / mistake to avoid)

2. PROPOSE
   Generate a delta (proposed change) to one or more skill files:
   - SKILL.md: New pattern in Common Mistakes, updated workflow step
   - examples.md: New input/output example from real execution
   - reference.md: New reference data discovered during execution

   Delta format:
   ```markdown
   ## Proposed Evolution

   **Skill**: {skill-name}
   **Trigger**: {what happened}
   **Change type**: pattern | example | warning | reference

   ### File: {filename}
   **Section**: {section to modify}
   **Action**: ADD | MODIFY
   **Content**:
   {the proposed content to add/modify}
   ```

3. VALIDATE (Skill Conductor Gate)
   Submit delta to Skill Conductor Mode 4 REVIEW:
   - Description follows formula: [What] + [When] + [Not for]?
   - SKILL.md stays < 500 lines?
   - No workflow/process leaked into description?
   - Cross-skill disambiguation maintained?
   - Change is genuinely useful (not noise)?

   Conductor verdict:
   - APPROVE → apply the change
   - MODIFY → Conductor suggests adjustments, apply modified version
   - REJECT → discard with reason logged

4. APPLY (if approved)
   - Edit the skill file with the approved delta
   - Log the evolution in skill's reference.md or MEMORY.md:
     ```
     ## Evolution Log
     | Date | Change | Trigger | Conductor Verdict |
     |------|--------|---------|-------------------|
     | YYYY-MM-DD | Added edge case warning | QA found missing null check | APPROVE |
     ```

5. VERIFY
   - Re-read the modified skill
   - Check it still loads correctly (valid YAML frontmatter)
   - Check total lines < 500
```

## Safety Constraints

1. **No self-modification during execution** — evolution happens AFTER skill completes
2. **Conductor gate is mandatory** — no direct SKILL.md edits without review
3. **Max 1 evolution per skill per session** — prevents rapid bloat
4. **Description is sacred** — only Conductor Mode 5 OPTIMIZE can change descriptions
5. **Append-only examples** — new examples are added, existing ones are not modified
6. **Evolution log required** — every change is tracked with date + trigger + verdict

## Integration with Agent Memory

Evolution complements agent memory:
- **Agent memory** (`agent-memory/{type}/MEMORY.md`): agent-level learnings (how I work)
- **Skill evolution** (`skills/{name}/SKILL.md`): skill-level improvements (how the skill works)

Both accumulate knowledge, but at different granularity.

## Common Mistakes

- **Evolving after failed execution** — only evolve from SUCCESSFUL runs (failures go to debugging)
- **Adding noise** — not every execution teaches something; only propose genuine learnings
- **Skipping Conductor** — direct edits bypass quality control and cause skill degradation
- **Bloating SKILL.md** — if approaching 500 lines, move details to reference.md
- **Changing description** — description optimization is Conductor Mode 5 only

## Related
- → skill-conductor — validates proposed changes (Mode 4 REVIEW gate)
- ← experiment-loop — triggers evolution after successful experiments
- ← successful skill execution — proposes improvements from real usage
