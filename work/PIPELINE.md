# Pipeline: Memory Decay Integration (agent-memory-skill)

- Status: PIPELINE_COMPLETE
- Phase: ALL DONE
- Mode: AGENT_TEAMS

> Integrate Ebbinghaus forgetting curve + tiered search + creative mode from agent-memory-skill into our template.
> Source repo: /tmp/agent-memory-skill/memory-engine.py (645 lines, zero deps)
> After compaction: find `<- CURRENT`, read that phase, continue.

---

## Phases

### Phase: IMPLEMENT
- Status: DONE
- Mode: AGENT_TEAMS(4)
- Attempts: 0 of 2
- On PASS: -> INTEGRATE
- On FAIL: -> STOP
- On REWORK: -> IMPLEMENT
- On BLOCKED: -> STOP
- Gate: memory-engine.py works, knowledge.md has decay metadata, session-orient shows tiers, config.yaml has memory section
- Gate Type: AUTO
- Inputs: /tmp/agent-memory-skill/memory-engine.py, .claude/memory/knowledge.md, .claude/hooks/session-orient.py, .claude/ops/config.yaml
- Outputs: .claude/scripts/memory-engine.py (adapted), updated knowledge.md, updated session-orient.py, updated config.yaml
- Checkpoint: pipeline-checkpoint-IMPLEMENT

  **Tasks:**
  1. Port memory-engine.py → .claude/scripts/memory-engine.py (adapt for our structure, add knowledge.md-aware commands)
  2. Add decay metadata (last_verified dates) to all 29 entries in knowledge.md
  3. Update session-orient.py to calculate tiers and show tier distribution
  4. Extend ops/config.yaml with memory: section (decay_rate, tier thresholds, etc.)

### Phase: INTEGRATE
- Status: DONE
- Mode: SOLO
- Attempts: 0 of 2
- On PASS: -> VERIFY
- On FAIL: -> IMPLEMENT
- On REWORK: -> IMPLEMENT
- On BLOCKED: -> STOP
- Gate: All commands work (scan, decay, touch, creative, stats), session-orient shows tiers, CLAUDE.md has search protocol
- Gate Type: AUTO
- Inputs: All outputs from IMPLEMENT
- Outputs: Updated CLAUDE.md (search protocol section), tested commands
- Checkpoint: pipeline-checkpoint-INTEGRATE

### Phase: VERIFY
- Status: DONE
- Mode: SOLO
- Attempts: 0 of 1
- On PASS: -> SYNC
- On FAIL: -> INTEGRATE
- On BLOCKED: -> STOP
- Gate: memory-engine.py scan/decay/stats pass, session-orient outputs tier info, config.yaml valid YAML
- Gate Type: AUTO
- Inputs: All integrated code
- Outputs: work/verify-results.md
- Checkpoint: pipeline-checkpoint-VERIFY

### Phase: SYNC
- Status: DONE
- Mode: AGENT_TEAMS(2)
- Attempts: 0 of 1
- On PASS: -> COMPLETE
- On FAIL: -> STOP
- On BLOCKED: -> STOP
- Gate: Template files match main project files
- Gate Type: USER_APPROVAL
- Inputs: All verified code
- Outputs: Synced template files
- Checkpoint: pipeline-checkpoint-SYNC

  **Tasks:**
  1. Sync .claude/scripts/, .claude/hooks/, .claude/ops/ to .claude/shared/templates/new-project/
  2. Update MEMORY.md auto-memory with new learnings

---

## Decisions

- [IMPLEMENT] Decision: Port memory-engine.py as-is with minimal adaptations. Reason: Zero deps, clean code, well-structured. Our adaptations: add knowledge.md-specific parsing, keep all original commands.
- [IMPLEMENT] Decision: Add last_verified date to knowledge.md entry headers, NOT full YAML frontmatter per entry. Reason: Keep human readability. Dates in headers are enough for decay calculation.
- [IMPLEMENT] Decision: Decay formula same as original: relevance = max(0.1, 1.0 - days × 0.015). Reason: Proven, tunable, simple.

---

## Execution Rules

1. **Start of session / after compaction:** Re-read this file. Find `<- CURRENT`. Resume from that phase.
2. **Phase execution:** Read phase Inputs. Execute. Produce Outputs. Run Gate check.
3. **Gate verdicts:** PASS (advance), CONCERNS (log + advance), REWORK (go to On REWORK, increment Attempts), FAIL (go to On FAIL or STOP).
4. **Attempts overflow:** When Attempts X >= max Y, set Status: BLOCKED, stop pipeline.
5. **Agent Teams:** If Mode = AGENT_TEAMS, use TeamCreate. Build prompts with Required Skills section.
6. **After each phase:** Update this file (move `<- CURRENT`, set Status: DONE). Update memory. Git commit with checkpoint tag.
