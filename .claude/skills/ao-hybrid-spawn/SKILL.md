---
name: ao-hybrid-spawn
description: |
  Spawn parallel worker agents as full Claude Code sessions via Agent Orchestrator.
  Each worker gets its own CLAUDE.md, skills, memory, and git worktree.
  Use when AGENT_TEAMS tasks need full project context (skills, hooks, quality gates).
  Trigger: execution_engine=ao_hybrid in config.yaml, or Mode: AO_HYBRID in pipeline phase.
  Wraps: ao spawn --prompt-file, ao session ls, ao session cleanup.
  Does NOT apply for cross-project fleet ops (use ao-fleet-spawn).
  Does NOT apply for simple subagent tasks without context needs (use TeamCreate).
---

# AO Hybrid Spawn

## Philosophy

Full-context agents > lightweight subagents for complex tasks. Each AO-spawned session is a complete Claude Code instance that loads CLAUDE.md, discovers skills, reads memory, and follows all quality gates. The coordinator (lead agent in current session) handles task decomposition and result collection.

Key difference from TeamCreate: TeamCreate agents see CLAUDE.md as background text but never load skills or memory. AO-spawned agents are independent Claude Code processes that follow the full startup protocol.

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

## Runtime Configuration (Step 0)

```
Check .claude/ops/config.yaml:
- execution_engine -> must be "ao_hybrid" (or pipeline phase Mode: AO_HYBRID)
- pipeline_mode -> "agent_teams" (AO_HYBRID is an execution engine, not a pipeline mode)
- max_retry_attempts -> used for spawn retry count
```

## Protocol

### 1. Pre-flight

```
1. Run: ao status
2. Verify: project listed in ~/.agent-orchestrator.yaml
3. Verify: no conflicting sessions from previous runs
4. If stale sessions found: ao-hybrid.sh cleanup
```

### 2. Build Prompts

```
For each task:
1. Use teammate-prompt-template.md structure as base
2. Add these AO-specific sections:
   ## Working Directory
   Your working directory is an isolated git worktree.
   All file operations are relative to this directory.
   Do NOT modify files outside your worktree.
   Commit your changes with a descriptive message.

   ## Result Output (MANDATORY)
   When done, create: work/ao-results/{session-id}.md
   Use this format:
   === PHASE HANDOFF: {task_name} ===
   Status: PASS | REWORK | BLOCKED
   Files Modified: [list with paths]
   Tests: [pass/fail counts]
   Decisions Made: [list]
   Learnings: [list]
   === END HANDOFF ===

3. Write prompt to: work/ao-prompts/task-{N}.md
4. Prompt MUST include: Required Skills, Acceptance Criteria, Constraints
5. Prompt MUST include: relevant excerpts from knowledge.md
```

### 3. Spawn Sessions

```
For each task (max 5 concurrent, use waves for more):
  bash .claude/scripts/ao-hybrid.sh spawn <task-id> work/ao-prompts/task-{N}.md

Each spawn:
- Creates git worktree via AO's workspace plugin
- Launches Claude Code with -p flag (non-interactive, processes prompt and exits)
- Records session ID in work/ao-sessions.json
```

### 4. Monitor

```
bash .claude/scripts/ao-hybrid.sh wait --timeout 3600

Polls every 30 seconds. Shows: session count, active, done, failed.
Terminal states: done, killed, exited, terminated.
```

### 5. Collect Results

```
For each completed session:
  bash .claude/scripts/ao-hybrid.sh collect <session-id>

Read handoff blocks from worktree result files.
Validate: Status must be PASS for gate to pass.
If Status is REWORK: log issue, may need re-spawn.
If Status is BLOCKED: escalate to coordinator.
```

### 6. Merge Worktrees

```
Sequential merge (not parallel -- avoids conflicts):
1. For each session's worktree branch:
   git merge --no-ff <worktree-branch> -m "merge: <task-name>"
2. If conflict: classify (trivial auto-resolve vs needs human)
3. Run tests after each merge to catch integration issues
```

### 7. Cleanup

```
bash .claude/scripts/ao-hybrid.sh cleanup

Kills any remaining sessions, removes worktrees, cleans work/ao-sessions.json.
```

## Failure Handling

```
SPAWN FAILURE:
  1. Retry spawn up to 3 times with 5s backoff
  2. If still failing: log to work/ao-errors/{task-id}.md
  3. Fallback: spawn that task via TeamCreate (degraded but functional)
  4. If 50%+ tasks fail: abort AO_HYBRID, fallback entire wave to TeamCreate

SESSION TIMEOUT:
  1. Kill timed-out session: ao session kill <id>
  2. Check partial output in worktree
  3. Re-spawn with same prompt if progress was made
  4. Fallback to TeamCreate if re-spawn also fails

MERGE CONFLICT:
  1. Trivial (whitespace, import order): auto-resolve
  2. Non-trivial: pause merge, show diff to coordinator
  3. Coordinator resolves or asks human
```

## Comparison: TeamCreate vs AO Hybrid

```
| Aspect    | TeamCreate                    | AO Hybrid                          |
|-----------|-------------------------------|-------------------------------------|
| Context   | CLAUDE.md as background text  | Full CLAUDE.md loading              |
| Skills    | NOT loaded                    | Loaded and available                |
| Memory    | NOT loaded                    | knowledge.md, activeContext.md      |
| Hooks     | NOT triggered                 | SessionStart, PreCompact, etc.      |
| Isolation | Shared process                | Separate process + worktree         |
| Speed     | Fast spawn (~1s)              | Slower spawn (~5-10s)               |
| Use when  | Simple tasks, no skills needed| Complex tasks, full context needed  |
```

## Red Flags

- Not running `ao status` before spawning (config may be broken)
- Spawning more than 5 sessions without waves (resource exhaustion)
- Not checking handoff files after completion (missing results)
- Not cleaning up sessions (zombie processes, stale worktrees)
- Using `ao send` (broken on Windows, use spawn-only model)
- Mixing TeamCreate and AO_HYBRID in same wave

## References

- Helper script: `.claude/scripts/ao-hybrid.sh`
- Teammate prompt template: `.claude/guides/teammate-prompt-template.md`
- Worktree merge protocol: `.claude/skills/subagent-driven-development/references/worktree-mode.md`
- AO config: `~/.agent-orchestrator.yaml`
- AO Fleet (cross-project): `.claude/skills/ao-fleet-spawn/SKILL.md`
