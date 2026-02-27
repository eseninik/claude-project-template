---
name: ao-fleet-spawn
description: |
  Spawn and manage parallel agent sessions across multiple projects via Agent Orchestrator CLI.
  Use when a pipeline phase has Mode: AO_FLEET, or when executing the same task across multiple bot projects.
  Wraps: ao spawn, ao batch-spawn, ao session ls, ao session kill, ao session cleanup.
  Does NOT apply for single-project parallelism (use AGENT_TEAMS/TeamCreate instead).
  Does NOT apply for sequential single-project tasks (use SOLO mode).
---

## Philosophy
Fleet operations dispatch independent Claude Code sessions to separate project directories. Each session runs autonomously with its own context, CLAUDE.md, and pipeline. The orchestrator monitors status and collects results.

## Critical Constraints
**never:**
- Spawn fleet sessions without verifying `ao status` first (config must load)
- Mix AO_FLEET with AGENT_TEAMS in the same phase (choose one)
- Spawn sessions for projects not in `~/.agent-orchestrator.yaml`

**always:**
- Verify `ao status` loads before first spawn
- Monitor sessions with `ao session ls` after spawning
- Kill sessions with `ao session kill` when done (prevent zombie processes)
- Clean up with `ao session cleanup` after fleet operation completes

## Prerequisites
- `ao` CLI installed globally (`C:\Bots\agent-orchestrator`, npm link)
- `~/.agent-orchestrator.yaml` has target projects configured
- Windows runtime plugin active (`defaults.runtime: windows`)

## Fleet Spawn Protocol

### 1. Pre-flight Check
```bash
ao status              # verify config loads, see active sessions
```
If errors: check `~/.agent-orchestrator.yaml` (repo field required per project).

### 2. Single Project Spawn
```bash
ao spawn <project-id>                    # spawn without issue
ao spawn <project-id> "TASK-123"         # spawn with issue/task ID
ao spawn <project-id> --agent codex      # override agent type
```

### 3. Multi-Project Fleet Spawn
For fleet-wide operations, spawn sessions for each target project:
```bash
# Sequential spawn (with monitoring)
for project in call-rate-bot clients-legal-bot conference-bot; do
  ao spawn "$project"
done

# Or use a loop with task context
for project in call-rate-bot clients-legal-bot conference-bot; do
  ao spawn "$project" "sync-template-v2"
done
```

### 4. Monitor Fleet
```bash
ao session ls                            # all sessions across all projects
ao session ls -p call-rate-bot           # filter by project
```

Session statuses: `spawning` -> `working` -> `pr_open` -> `merged` / `killed`

### 5. Send Commands to Running Sessions
```bash
ao send <session-id> "your message here"
ao send <session-id> -f path/to/prompt.txt  # send file contents
```

### 6. Collect Results
After sessions complete, check each project's work/ directory for results:
```bash
for project_path in "C:/Bots/Migrator bots/Call Rate bot" ...; do
  cat "$project_path/work/PIPELINE.md"  # check pipeline status
done
```

### 7. Cleanup
```bash
ao session kill <session-id>             # kill specific session
ao session cleanup                       # auto-clean completed sessions
ao session cleanup -p call-rate-bot      # clean specific project
```

## When to Use AO_FLEET vs AGENT_TEAMS

| Criteria | AO_FLEET | AGENT_TEAMS |
|----------|----------|-------------|
| Scope | Multiple repos/projects | Single project |
| Sessions | Separate Claude Code processes | Subagents within one session |
| Context | Independent (each has own CLAUDE.md) | Shared (same conversation) |
| Communication | `ao send` / file-based | SendMessage / TaskList |
| Scale | 2-100+ projects | 2-10 subagents |
| Use case | Fleet sync, multi-repo deploy | Feature implementation, QA |

## Red Flags
- Using AO_FLEET for single-project work (use AGENT_TEAMS)
- Not monitoring sessions after spawn (sessions may fail silently)
- Leaving sessions running after task completes (zombie processes)
- Spawning without checking `ao status` first
