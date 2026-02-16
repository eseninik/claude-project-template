# Ralph Loop v2 Design

**Date:** 2026-02-16
**Purpose:** Compaction-immune fresh-context execution engine for autonomous pipeline phases
**Script:** `work/pipeline-v2-draft/ralph.sh`
**Prompt:** `work/pipeline-v2-draft/PROMPT.md`

---

## 1. Core Concept

Ralph Loop solves the fundamental problem: **compaction destroys behavioral rules**. Agent Teams instructions, verification protocols, and phase awareness all degrade after 1-2 compactions.

**Solution:** Never compact. Each pipeline phase gets a fresh `claude -p` process with clean 200K context. State persists through files (PIPELINE.md, STATE.md, git), not conversation memory.

```
┌─────────────────────────────────────────────┐
│              ralph.sh (bash)                 │
│                                              │
│  for iteration in 1..MAX:                    │
│    ┌─────────────────────────────────┐       │
│    │ claude -p "$(cat PROMPT.md)"    │       │
│    │                                  │       │
│    │ 1. Read CLAUDE.md (auto-loaded) │       │
│    │ 2. Read PIPELINE.md             │       │
│    │ 3. Find <- CURRENT phase        │       │
│    │ 4. Execute phase                │       │
│    │ 5. Update state files           │       │
│    │ 6. Git commit checkpoint        │       │
│    └─────────────────────────────────┘       │
│    check: COMPLETE? BLOCKED? → exit          │
│  done                                        │
└─────────────────────────────────────────────┘
```

---

## 2. ralph.sh Script Design

### Arguments

| Flag | Default | Description |
|------|---------|-------------|
| `--max-iterations` | 20 | Safety limit to prevent infinite loops |
| `--pipeline` | `work/PIPELINE.md` | Path to pipeline state file |
| `--prompt` | `work/PROMPT.md` | Path to prompt template |
| `--model` | (claude default) | Override model for phases |
| `--dry-run` | false | Print what would execute without running |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Pipeline completed successfully |
| 1 | Pipeline blocked (requires user intervention) |
| 2 | Max iterations reached without completion |
| 3 | PROMPT.md or PIPELINE.md not found |

### Key Design Decisions

1. **One phase per iteration** -- each `claude -p` invocation executes exactly one pipeline phase, then exits. This keeps context usage well under the 200K limit.

2. **Status detection via grep** -- ralph.sh checks PIPELINE.md for `PIPELINE_COMPLETE` or `BLOCKED` strings after each iteration. These are simple, reliable markers.

3. **Git checkpoint after every iteration** -- ensures rollback is always possible. Tag format: `pipeline-iter-{N}`.

4. **`--dangerously-skip-permissions`** -- required for autonomous execution. Without it, `claude -p` would pause for permission prompts with no user present.

5. **No streaming output** -- `claude -p` runs silently. Progress is tracked via PIPELINE.md and git log.

---

## 3. PROMPT.md Design

### Requirements

- **Under 50 lines** -- loaded every iteration, must be lean
- **Self-contained** -- must include all instructions needed for one phase
- **Agent Teams enforcement** -- explicit "MUST use TeamCreate" rule
- **Idempotent** -- safe to re-run if iteration crashes mid-phase

### Structure

```
1. Context loading (read CLAUDE.md, PIPELINE.md, STATE.md)
2. Phase identification (find <- CURRENT)
3. Mode enforcement (AGENT_TEAMS -> TeamCreate, SOLO -> direct)
4. Execution
5. Quality gate
6. State update (PIPELINE.md, STATE.md, memory)
7. Git checkpoint
```

### Agent Teams Enforcement Mechanism

The critical innovation: PROMPT.md explicitly states the rule in every iteration.

```
If phase Mode = AGENT_TEAMS → MUST use TeamCreate tool.
Do NOT use Task tool for parallelism. TeamCreate ONLY.
```

Because PROMPT.md is loaded fresh every iteration via `claude -p "$(cat PROMPT.md)"`, this rule **cannot be lost to compaction**. It exists in the prompt, not in conversation history.

### What PROMPT.md Does NOT Include

- Full CLAUDE.md contents (loaded automatically by claude -p)
- Phase-specific logic (that's in PIPELINE.md phase definitions)
- Project-specific code patterns (that's in skills/project-knowledge)

---

## 4. Ralph Loop vs Interactive Mode

| Feature | Ralph Loop | Interactive Mode |
|---------|-----------|------------------|
| Compaction immunity | **Guaranteed** (fresh context per phase) | Best-effort (PIPELINE.md Mode field) |
| Agent Teams survival | **Guaranteed** (PROMPT.md reloaded) | Depends on Summary Instructions |
| User interaction | None during phase | Full (user can guide, override) |
| Permissions | `--dangerously-skip-permissions` | Normal permission prompts |
| Error recovery | Automatic (REWORK/BLOCKED) | User-guided |
| Context per phase | Full 200K clean | Degraded after compaction |
| Speed | Slower (process startup overhead) | Faster (no restart) |
| Use when | "реализуй автономно" / long pipelines | User wants to participate / short pipelines |

### When to Use Ralph Loop

- Pipeline has 5+ phases
- Multiple phases use AGENT_TEAMS mode
- User explicitly requests autonomous execution
- Session will likely exceed context window (>100K tokens estimated)

### When to Use Interactive Mode

- Pipeline has 2-3 phases
- User wants to review between phases
- Phases need user input (e.g., SPEC phase with interview)
- Quick iteration where process restart overhead matters

---

## 5. State Management

### File Responsibilities

| File | Written by | Read by | Purpose |
|------|-----------|---------|---------|
| `PIPELINE.md` | Agent (each phase) | ralph.sh + Agent | Phase state machine |
| `STATE.md` | Agent (each phase) | Agent | Detailed execution state |
| `activeContext.md` | Agent (each phase) | Agent (next iteration) | Cross-session memory |
| `PROMPT.md` | User/pipeline creator | ralph.sh | Iteration prompt |

### PIPELINE.md Status Markers

ralph.sh detects these strings in PIPELINE.md:

```
PIPELINE_COMPLETE  → exit 0 (success)
BLOCKED            → exit 1 (needs user)
<- CURRENT         → execute this phase
```

### Git Checkpoint Strategy

```bash
# After each iteration
git add -A
git commit -m "pipeline: phase {name} iteration {N}"
git tag "pipeline-iter-{N}"
```

**Rollback:** `git reset --hard pipeline-iter-{N-1}` restores full state including PIPELINE.md.

---

## 6. Error Handling

### Phase Failure

```
Agent detects test failure or error:
1. Increments Attempts counter in PIPELINE.md
2. If Attempts < Max Attempts → sets phase to REWORK transition
3. If Attempts >= Max Attempts → sets status to BLOCKED
4. Updates STATE.md with error details
5. Commits checkpoint
6. Exits (ralph.sh picks up new state next iteration)
```

### Crash Recovery

If `claude -p` crashes mid-phase:
1. ralph.sh detects non-zero exit code
2. PIPELINE.md may be partially updated
3. Next iteration reads PIPELINE.md → finds `<- CURRENT` still on same phase
4. Agent re-reads STATE.md → sees what was partially done
5. Resumes or restarts the phase

### Infinite Loop Prevention

- `MAX_ITERATIONS` hard limit (default: 20)
- Per-phase `Max Attempts` (default: 3)
- ralph.sh tracks iteration count independently of agent state
- Exit code 2 if max iterations reached

---

## 7. Security Considerations

### `--dangerously-skip-permissions`

This flag is **required** for Ralph Loop autonomy but removes all permission gates:
- File system writes (any file)
- Shell command execution (any command)
- Network access

**Mitigations:**
- Pipeline is created and reviewed by user before execution
- Git checkpoints allow full rollback
- PIPELINE.md constrains what phases can do
- Server deploys still require SSH key (not stored in repo)

### Secrets

- `.env` files never committed (in .gitignore)
- SSH keys referenced by path, never inline
- ralph.sh reads env vars from shell environment, not from files in repo

---

## 8. Example Execution Flow

```
$ ./scripts/ralph.sh --max-iterations 15

[Iteration 1] Reading PIPELINE.md... Phase: SPEC (SOLO)
  claude -p running... (executes SPEC phase)
  Phase SPEC complete. Git checkpoint: pipeline-iter-1

[Iteration 2] Reading PIPELINE.md... Phase: REVIEW (AGENT_TEAMS)
  claude -p running... (creates expert panel team)
  Phase REVIEW complete. Git checkpoint: pipeline-iter-2

[Iteration 3] Reading PIPELINE.md... Phase: PLAN (SOLO)
  claude -p running... (creates tech-spec + tasks)
  Phase PLAN complete. Git checkpoint: pipeline-iter-3

[Iteration 4] Reading PIPELINE.md... Phase: IMPLEMENT (AGENT_TEAMS)
  claude -p running... (creates developer team via TeamCreate)
  Phase IMPLEMENT complete. Git checkpoint: pipeline-iter-4

[Iteration 5] Reading PIPELINE.md... Phase: TEST (SOLO)
  claude -p running... (runs pytest)
  Tests failed. REWORK -> FIX phase.
  Git checkpoint: pipeline-iter-5

[Iteration 6] Reading PIPELINE.md... Phase: FIX (AGENT_TEAMS)
  claude -p running... (creates debugger team)
  Phase FIX complete. Git checkpoint: pipeline-iter-6

[Iteration 7] Reading PIPELINE.md... Phase: TEST (SOLO)
  claude -p running... (re-runs pytest)
  All tests pass. PASS -> DEPLOY.
  Git checkpoint: pipeline-iter-7

[Iteration 8] Reading PIPELINE.md... Phase: DEPLOY (SOLO)
  claude -p running... (rsync + systemctl)
  Deploy complete. Git checkpoint: pipeline-iter-8

[Iteration 9] Reading PIPELINE.md... Status: PIPELINE_COMPLETE
  Pipeline complete! Total iterations: 9
  Exit code: 0
```
