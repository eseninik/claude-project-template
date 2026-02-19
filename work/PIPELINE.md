# Pipeline: Extract Ralph Loop Features + Graphiti Integration

- Status: PIPELINE_COMPLETE
- Phase: FINAL_SYNC (DONE)
- Mode: INTERACTIVE

> Extract useful patterns from Ralph Loop into interactive pipeline flow.
> Integrate Graphiti for automatic context preservation.
> Test everything, then remove Ralph Loop.

---

## Phases

### Phase: FIX_GRAPHITI  [DONE]
- Status: DONE
- Mode: SOLO
- Attempts: 1 of 3
- On PASS: -> IMPLEMENT
- On FAIL: -> STOP
- On BLOCKED: -> STOP
- Gate: Graphiti search_memory_facts and add_memory work without errors
- Gate Type: AUTO
- Inputs: Graphiti docker container (running), ~/.claude.json MCP config
- Outputs: Working Graphiti with valid API key, verified read/write cycle
- Checkpoint: pipeline-checkpoint-FIX_GRAPHITI

### Phase: IMPLEMENT  [DONE]
- Status: DONE
- Mode: AGENT_TEAMS
- Attempts: 0 of 2
- On PASS: -> SYNC
- On FAIL: -> STOP
- On REWORK: -> IMPLEMENT
- On BLOCKED: -> STOP
- Gate: All target files modified, no syntax errors, cross-references valid
- Gate Type: AUTO
- Inputs: Analysis from discussion (Phase Transition Protocol, Graphiti integration, Insight Extraction)
- Outputs: Modified CLAUDE.md, autonomous-pipeline.md, PIPELINE-v3.md, phase templates
- Checkpoint: pipeline-checkpoint-IMPLEMENT
- Tasks:
  - T1: CLAUDE.md — add Phase Transition Protocol, Graphiti in Before Commit, strengthen Session Start/After Compaction
  - T2: autonomous-pipeline.md — add Phase Transition Protocol section, update Memory Updates, de-emphasize Ralph Loop
  - T3: PIPELINE-v3.md template — add Phase Transition Protocol to Execution Rules
  - T4: Phase templates (IMPLEMENT.md, PLAN.md, etc.) — add phase-specific context loading instructions
  - T5: Repurpose insight-extractor.md for in-session use (not Ralph Loop post-processing)

### Phase: SYNC  [DONE]
- Status: DONE
- Mode: AGENT_TEAMS
- Attempts: 0 of 1
- On PASS: -> TEST
- On FAIL: -> IMPLEMENT
- On BLOCKED: -> STOP
- Gate: All modified files have matching copies in shared/templates/new-project/
- Gate Type: AUTO
- Inputs: All modified files from IMPLEMENT
- Outputs: Synced new-project template
- Checkpoint: pipeline-checkpoint-SYNC

### Phase: TEST  [DONE]
- Status: DONE
- Mode: AGENT_TEAMS
- Attempts: 0 of 2
- On PASS: -> CLEANUP
- On FAIL: -> IMPLEMENT
- On REWORK: -> IMPLEMENT
- On BLOCKED: -> STOP
- Gate: All test scenarios pass, context preservation verified
- Gate Type: AUTO
- Inputs: Full modified system
- Outputs: work/context-preservation-test-report.md
- Checkpoint: pipeline-checkpoint-TEST
- Tests:
  - Test1: Graphiti write/read cycle — add_memory then search, verify data returns
  - Test2: Phase Transition Protocol — simulate phase completion, verify all 5 steps execute
  - Test3: Session Start protocol — verify Graphiti query happens at session start
  - Test4: Cross-reference integrity — grep for stale Ralph Loop refs, broken links

### Phase: CLEANUP  [DONE]
- Status: DONE
- Mode: AGENT_TEAMS
- Attempts: 0 of 1
- On PASS: -> FINAL_SYNC
- On FAIL: -> STOP
- On BLOCKED: -> STOP
- Gate: No ralph.sh, no PROMPT.md template, no Ralph Loop references in active docs
- Gate Type: AUTO
- Inputs: Verified working system from TEST
- Outputs: Cleaned codebase without Ralph Loop artifacts
- Checkpoint: pipeline-checkpoint-CLEANUP
- Tasks:
  - C1: Delete scripts/ralph.sh (main + template)
  - C2: Delete/repurpose .claude/shared/work-templates/PROMPT.md
  - C3: Clean Ralph Loop references from autonomous-pipeline.md, CLAUDE.md, SKILLS_INDEX.md
  - C4: Clean Ralph Loop references from new-project template

### Phase: FINAL_SYNC  [DONE]
- Status: DONE
- Mode: SOLO
- Attempts: 0 of 1
- On PASS: -> COMPLETE
- On FAIL: -> STOP
- Gate: Template matches main, no stale refs anywhere
- Gate Type: AUTO
- Inputs: Cleaned codebase
- Outputs: Final synced template
- Checkpoint: pipeline-checkpoint-FINAL_SYNC

---

## Decisions

- [ANALYZE] Phase Transition Protocol extracted from Ralph Loop: commit → insight extraction → memory save → context refresh → start next phase
- [ANALYZE] Graphiti integration: write in Before Commit (blocking rule), read in Session Start + After Compaction
- [ANALYZE] Insight Extraction repurposed for in-session use between pipeline phases (was Ralph Loop post-processing)
- [ANALYZE] Ralph Loop to be removed after features extracted (user doesn't use it, interactive flow + Agent Teams is primary)
- [FIX_GRAPHITI] Root cause: OpenRouter requires HTTP-Referer header, Graphiti AsyncOpenAI client didn't send it
- [FIX_GRAPHITI] Fix: patched ~/graphiti/mcp_server/src/services/factories.py — added default_headers with HTTP-Referer + X-Title for OpenRouter detection
- [FIX_GRAPHITI] Container restarted. Claude Code needs restart to re-establish MCP session. Then verify search + add_memory work.

---

## Execution Rules

1. **Start of session / after compaction:** Re-read this file. Find `<- CURRENT`. Resume from that phase.
2. **Phase execution:** Read phase Inputs. Execute. Produce Outputs. Run Gate check.
3. **Gate verdicts:** PASS (advance), CONCERNS (log + advance), REWORK (go to On REWORK, increment Attempts), FAIL (go to On FAIL or STOP).
4. **Attempts overflow:** When Attempts X >= max Y, set Status: BLOCKED, stop pipeline.
5. **Agent Teams:** If Mode = AGENT_TEAMS, use TeamCreate. Build prompts with Required Skills section.
6. **After each phase:** Update this file (move `<- CURRENT`, set Status: DONE). Update work/STATE.md. Update memory. Git commit.
7. **Pipeline complete:** When last phase passes, set top-level Status: PIPELINE_COMPLETE.
