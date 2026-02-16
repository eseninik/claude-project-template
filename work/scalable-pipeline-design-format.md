# PIPELINE.md v2 Format Design

**Date:** 2026-02-16
**Author:** format-designer agent
**Source:** scalable-pipeline-research.md, v1 PIPELINE.md template, autonomous-pipeline.md

---

## Problem Statement

The v1 PIPELINE.md is a flat checklist with linear phases. It lacks:
- Conditional transitions (PASS/FAIL routing)
- Quality gates with verdicts
- Attempt counters for bounded loops
- Sub-pipeline references
- Phase contracts (inputs/outputs)
- Execution mode annotation (interactive vs Ralph Loop)

The v2 format must be a **state machine encoded in markdown** that an LLM can parse after compaction using only the `<- CURRENT` marker as anchor.

---

## Design Decisions

### 1. Named Phases, Not Numbered

**Decision:** Phases use UPPERCASE semantic names (SPEC, PLAN, IMPLEMENT, etc.) instead of numbers.

**Rationale:** Named transitions (`On PASS: -> TEST`) are self-documenting. Numbered phases (`On PASS: -> Phase 5`) require counting. After compaction, an LLM can grep for `### Phase: TEST` but cannot reliably count to phase 5.

### 2. `<- CURRENT` on the Phase Header Line

**Decision:** The `<- CURRENT` marker sits on the `### Phase:` line, not on a status sub-field.

**Rationale:** After compaction, the agent needs one grep to find its location. Putting it on the header line means `grep "CURRENT" PIPELINE.md` returns the phase name directly. This is the single most important compaction-survival feature.

### 3. Markdown Only, No YAML/JSON

**Decision:** The entire file is markdown with a key-value convention (`- Key: Value`).

**Rationale:** CLAUDE.md and all project files are markdown. Mixing in YAML blocks creates parsing ambiguity. The `- Key: Value` list convention is already used in v1 and is both human-readable and LLM-parseable.

### 4. Inline Transitions, Not a Separate Table

**Decision:** Each phase defines its own `On PASS/FAIL/REWORK/BLOCKED` transitions inline.

**Rationale:** After compaction, only the current phase section may be in context. If transitions live in a separate table, the agent cannot determine next steps. Inline transitions are self-contained per phase.

### 5. Compact Contract Section

**Decision:** Each phase has `Inputs:` and `Outputs:` single-line fields rather than full Contract files.

**Rationale:** For the PIPELINE.md template, brevity matters (150-line limit). Full contract specifications belong in phase template files. PIPELINE.md needs just enough for the agent to know what files to read/produce.

### 6. Decisions Log is Append-Only

**Decision:** The `## Decisions` section at the bottom is append-only (new entries added, never removed).

**Rationale:** Decisions record prevents repeated mistakes. After compaction, the agent reads decisions to understand what was already tried. Editing or removing entries destroys this anti-drift history.

### 7. Execution Rules Embedded in Template

**Decision:** The template includes a `## Execution Rules` section with post-compaction recovery instructions.

**Rationale:** After compaction, CLAUDE.md Summary Instructions say "re-read PIPELINE.md". The Execution Rules section tells the agent how to use the file. Without this, the agent reads the file but may not know the protocol.

### 8. Mode Field Enforces Agent Teams

**Decision:** Every phase has `- Mode: SOLO | AGENT_TEAMS | SUB_PIPELINE`. The agent MUST respect this field.

**Rationale:** This is the primary compaction-survival mechanism for Agent Teams enforcement (Solution 2 from research). The mode is persisted in the state file, not in conversation memory.

---

## Format Specification

### Header

```markdown
# Pipeline: {name}

- Status: NOT_STARTED | IN_PROGRESS | BLOCKED | PIPELINE_COMPLETE
- Phase: {current phase name}
- Mode: INTERACTIVE | RALPH_LOOP
```

- **Status** controls Ralph Loop termination (PIPELINE_COMPLETE = exit, BLOCKED = error exit).
- **Phase** is a human-readable duplicate of the `<- CURRENT` marker for quick scanning.
- **Mode** tells the agent whether user interaction is expected between phases.

### Phase Block

```markdown
### Phase: {NAME}  <- CURRENT
- Status: PENDING | IN_PROGRESS | DONE | BLOCKED | SKIPPED
- Mode: SOLO | AGENT_TEAMS | SUB_PIPELINE
- Attempts: 0 of 3
- On PASS: -> {phase}
- On FAIL: -> {phase} | STOP
- On REWORK: -> {phase}
- On BLOCKED: -> STOP
- Gate: {what must be true to PASS}
- Gate Type: AUTO | USER_APPROVAL | HYBRID
- Inputs: {files/artifacts this phase reads}
- Outputs: {files/artifacts this phase produces}
- Checkpoint: pipeline-checkpoint-{NAME}
```

- `<- CURRENT` appears on exactly ONE phase header at a time.
- `Attempts: X of Y` tracks loop iterations. When X >= Y, phase goes BLOCKED.
- `Gate` is a one-line description. Detailed gate specs go in phase templates.
- `Checkpoint` is the git tag created after PASS.

### Sub-Pipeline Reference

When `Mode: SUB_PIPELINE`:
```markdown
### Phase: DEVELOPMENT  <- CURRENT
- Status: IN_PROGRESS
- Mode: SUB_PIPELINE
- Pipeline: work/development/PIPELINE.md
- On PASS: -> TEST
- On BLOCKED: -> STOP
```

The agent enters the referenced pipeline and executes it to completion before returning.

### Sections

1. **Header** -- pipeline identity and global status
2. **Phases** -- ordered phase definitions with transitions
3. **Decisions** -- append-only log of choices made during execution
4. **Execution Rules** -- post-compaction recovery instructions (always at bottom for high attention)

---

## Loop Examples

### TEST -> FIX -> TEST (bounded)

```
### Phase: TEST
- On PASS: -> DEPLOY
- On FAIL: -> FIX

### Phase: FIX
- Attempts: 0 of 3
- On PASS: -> TEST
- On BLOCKED: -> STOP
```

FIX loops back to TEST on success. After 3 failed attempts, FIX goes BLOCKED and pipeline stops.

### REVIEW -> IMPLEMENT -> REVIEW (revision)

```
### Phase: REVIEW
- On PASS: -> DEPLOY
- On REWORK: -> IMPLEMENT

### Phase: IMPLEMENT
- Attempts: 0 of 2
- On PASS: -> REVIEW
```

IMPLEMENT loops back to REVIEW. Max 2 revision cycles.

---

## Template Size

The v2 template with 8 standard phases, execution rules, and decisions section fits in ~120 lines. Well under the 150-line target. Phases that are not needed for a specific pipeline can be deleted -- the named transitions still work for remaining phases.
