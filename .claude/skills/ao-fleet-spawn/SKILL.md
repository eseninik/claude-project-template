---
name: ao-fleet-spawn
description: |
  Spawn parallel agent sessions across MULTIPLE projects/repositories via Agent Orchestrator (ao) CLI.
  Use when: Mode: AO_FLEET in pipeline, task targets all bots / multiple repos, cross-project sync, multi-repo migration, "все боты", fleet operations.
  Do NOT use for: single-project parallelism (use TeamCreate), single-project full-context agents (use ao-hybrid-spawn), deployment, or git operations.
roles: [fleet-orchestrator]
---

# AO Fleet Spawn

## Overview
Fleet operations dispatch independent Claude Code sessions to separate project directories. Each session runs autonomously with its own context, CLAUDE.md, and pipeline. The orchestrator monitors status and collects results.

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
```bash
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
  cat "$project_path/work/PIPELINE.md"
done
```

### 7. Cleanup
```bash
ao session kill <session-id>             # kill specific session
ao session cleanup                       # auto-clean completed sessions
ao session cleanup -p call-rate-bot      # clean specific project
```

## AO_FLEET vs AGENT_TEAMS

| Criteria | AO_FLEET | AGENT_TEAMS |
|----------|----------|-------------|
| Scope | Multiple repos/projects | Single project |
| Sessions | Separate Claude Code processes | Subagents within one session |
| Context | Independent (each has own CLAUDE.md) | Shared (same conversation) |
| Communication | `ao send` / file-based | SendMessage / TaskList |
| Scale | 2-100+ projects | 2-10 subagents |
| Use case | Fleet sync, multi-repo deploy | Feature implementation, QA |

## Common Mistakes
- **Not running `ao status` before spawning** -- config may be broken or stale sessions lingering
- **Using AO_FLEET for single-project work** -- use AGENT_TEAMS instead, much lighter
- **Not monitoring sessions after spawn** -- sessions may fail silently without notification
- **Leaving sessions running after task completes** -- causes zombie processes and resource leaks
