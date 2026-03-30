---
name: ao-hybrid-spawn
description: |
  Spawn full Claude Code sessions as isolated workers with skills, memory, hooks, and git worktrees via Agent Orchestrator within a SINGLE project.
  Use when: Mode: AO_HYBRID, tasks need full project context (skills, quality gates, memory), TeamCreate is insufficient because agents need loaded skills, execution_engine=ao_hybrid.
  Do NOT use for: cross-project/multi-repo ops (use ao-fleet-spawn), simple subagent tasks without context needs (use TeamCreate), or direct code changes.
roles: [ao-hybrid-coordinator]
---

# AO Hybrid Spawn

## Overview
Full-context agents for complex tasks. Each AO-spawned session is a complete Claude Code instance that loads CLAUDE.md, discovers skills, reads memory, and follows all quality gates. TeamCreate agents see CLAUDE.md as background text but never load skills or memory -- AO Hybrid solves this gap.

## Critical Constraints

**never:**
- Use `ao send` (broken on Windows -- bypasses runtime abstraction, calls tmux directly)
- Spawn without pre-flight check (`ao status`)
- Mix AO_HYBRID with TeamCreate in the same wave
- Leave sessions running after wave completes (resource leak)
- Skip handoff file verification after session completes

**always:**
- Use `--prompt-file` (not `--prompt`) for task delivery (avoids Windows cmd line limits)
- Write task prompts to `work/ao-prompts/task-{N}.md` before spawning
- Include `## Working Directory` and `## Result Output` sections in every prompt
- Use `ao-hybrid.sh` helper for spawn/status/wait/collect/cleanup
- Clean up all sessions after collecting results

## Protocol

### 1. Pre-flight
1. Run: `ao status`
2. Verify: project listed in `~/.agent-orchestrator.yaml`
3. Verify: no conflicting sessions from previous runs
4. If stale sessions found: `ao-hybrid.sh cleanup`

### 2. Build Prompts
For each task:
1. Use `teammate-prompt-template.md` structure as base
2. Add AO-specific sections:
   - `## Working Directory` -- isolated git worktree, no modifications outside it
   - `## Result Output` -- create `work/ao-results/{session-id}.md` with PHASE HANDOFF block
3. Write prompt to: `work/ao-prompts/task-{N}.md`
4. Include: Required Skills, Acceptance Criteria, Constraints, knowledge.md excerpts

### 3. Spawn Sessions
```bash
# Max 5 concurrent, use waves for more
bash .claude/scripts/ao-hybrid.sh spawn <task-id> work/ao-prompts/task-{N}.md
```
Each spawn creates a git worktree, launches Claude Code with `-p` flag (non-interactive), and records session ID in `work/ao-sessions.json`.

### 4. Monitor
```bash
bash .claude/scripts/ao-hybrid.sh wait --timeout 3600
```
Polls every 30 seconds. Terminal states: done, killed, exited, terminated.

### 5. Collect Results
```bash
bash .claude/scripts/ao-hybrid.sh collect <session-id>
```
Read handoff blocks from worktree result files. Validate: Status must be PASS for gate to pass. REWORK = re-spawn, BLOCKED = escalate to coordinator.

### 6. Merge Worktrees
Sequential merge (not parallel -- avoids conflicts):
1. `git merge --no-ff <worktree-branch> -m "merge: <task-name>"`
2. If conflict: classify (trivial auto-resolve vs needs human)
3. Run tests after each merge to catch integration issues

### 7. Cleanup
```bash
bash .claude/scripts/ao-hybrid.sh cleanup
```
Kills remaining sessions, removes worktrees, cleans `work/ao-sessions.json`.

## Failure Handling

**Spawn failure:**
1. Retry up to 3 times with 5s backoff
2. Log to `work/ao-errors/{task-id}.md`
3. Fallback: spawn that task via TeamCreate (degraded but functional)
4. If 50%+ tasks fail: abort AO_HYBRID, fallback entire wave to TeamCreate

**Session timeout:**
1. Kill timed-out session: `ao session kill <id>`
2. Check partial output in worktree
3. Re-spawn with same prompt if progress was made

**Merge conflict:**
1. Trivial (whitespace, import order): auto-resolve
2. Non-trivial: pause merge, show diff to coordinator

## TeamCreate vs AO Hybrid

| Aspect | TeamCreate | AO Hybrid |
|--------|------------|-----------|
| Context | CLAUDE.md as background text | Full CLAUDE.md loading |
| Skills | NOT loaded | Loaded and available |
| Memory | NOT loaded | knowledge.md, activeContext.md |
| Isolation | Shared process | Separate process + worktree |
| Speed | Fast spawn (~1s) | Slower spawn (~5-10s) |
| Use when | Simple tasks, no skills needed | Complex tasks, full context needed |

## Common Mistakes
- **Not running `ao status` before spawning** -- config may be broken or stale sessions lingering
- **Spawning more than 5 sessions without waves** -- causes resource exhaustion
- **Not checking handoff files after completion** -- missing results go unnoticed
- **Using `ao send`** -- broken on Windows, use spawn-only model instead
- **Mixing TeamCreate and AO_HYBRID in same wave** -- choose one execution engine per wave

## References
- Helper script: `.claude/scripts/ao-hybrid.sh`
- Teammate prompt template: `.claude/guides/teammate-prompt-template.md`
- Worktree merge protocol: `.claude/skills/subagent-driven-development/references/worktree-mode.md`
- AO config: `~/.agent-orchestrator.yaml`

## Related
- ↔ ao-fleet-spawn — multi-project alternative (AO across repos)
- → using-git-worktrees — worktree isolation used by spawned sessions
- → subagent-driven-development — references worktree-mode.md
- ← autonomous pipeline — triggered by Mode: AO_HYBRID in PIPELINE.md
