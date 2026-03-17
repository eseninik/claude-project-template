# Pipeline: Best Practice Integration (5 Features)

- Status: PIPELINE_COMPLETE
- Phase: COMPLETE
- Mode: AGENT_TEAMS

> 5 features from claude-code-best-practice analysis. All touch different files — fully parallel.
> No SPEC/PLAN needed — features designed and approved in discussion.

---

## Features

1. **Agent Memory** — `.claude/agent-memory/` directory with templates
2. **Per-Phase Fresh Session Verification** — Update pipeline template + verification skill
3. **Auto-Research Phase** — Lightweight RPI (2-3 agents) auto-triggered in pipeline
4. **Self-Evolving Agent Pattern** — Skills improve from usage + Skill Conductor gate
5. **Skill Examples** — examples.md template + organic growth via self-evolving

---

## Phases

### Phase: IMPLEMENT
- Status: DONE
- Mode: AGENT_TEAMS
- Attempts: 1 of 2
- On PASS: -> QA_REVIEW
- On FAIL: -> STOP
- Gate: all 5 features implemented, files exist, no syntax errors
- Gate Type: AUTO
- Inputs: feature specs from discussion, existing skill/pipeline files
- Outputs: new/modified files for all 5 features
- Checkpoint: pipeline-checkpoint-IMPLEMENT

### Phase: QA_REVIEW
- Status: PENDING
- Mode: AGENT_TEAMS
- Attempts: 0 of 2
- On PASS: -> SYNC
- On REWORK: -> FIX
- Gate: no CRITICAL issues in qa-review-report.md
- Gate Type: AUTO
- Inputs: implemented features
- Outputs: work/qa-review-report.md

### Phase: FIX
- Status: PENDING
- Mode: SOLO
- Attempts: 0 of 3
- On PASS: -> QA_REVIEW
- On BLOCKED: -> STOP
- Gate: all QA issues resolved
- Gate Type: AUTO

### Phase: SYNC
- Status: DONE
- Mode: AGENT_TEAMS
- Attempts: 0 of 1
- On PASS: -> VERIFY
- On BLOCKED: -> STOP
- Gate: new-project template mirrors main .claude/
- Gate Type: AUTO
- Inputs: all modified/new files
- Outputs: synced template files

### Phase: VERIFY  <- CURRENT
- Status: DONE
- Mode: SOLO
- Attempts: 0 of 1
- On PASS: -> COMPLETE
- On FAIL: -> FIX
- Gate: all features work, files exist with substantive content
- Gate Type: AUTO
- Outputs: verification report

### Phase: COMPLETE
- Status: PENDING
- Mode: SOLO
- On PASS: -> DONE
- Gate: memory updated, git committed

---

## Decisions

- [DISCUSS] All 5 features approved by user in interactive discussion
- [DISCUSS] rules/ directory — REJECTED (agents ignore non-CLAUDE.md files, compliance ~10-20%)
- [DISCUSS] Autocompact 50% — REJECTED (not needed with 1M context, 95% is optimal)
- [DISCUSS] Cross-model Codex — REJECTED (we use only Claude)
- [DISCUSS] Self-evolving needs Skill Conductor as quality gate
- [DISCUSS] Per-phase verification uses fresh AO sessions, not subagents
- [DISCUSS] Skill examples grow organically via self-evolving, not pre-filled

---

## Execution Rules

1. **Start of session / after compaction:** Re-read this file. Find `<- CURRENT`. Resume from that phase.
2. **Phase execution:** Read phase Inputs. Execute. Produce Outputs. Run Gate check.
3. **Gate verdicts:** PASS (advance), REWORK (go to On REWORK), FAIL (go to On FAIL or STOP).
4. **Agent Teams:** If Mode = AGENT_TEAMS, use TeamCreate. Build prompts with Required Skills section.
5. **After each phase:** Update this file (move `<- CURRENT`). Update memory. Git commit.
