# dual-teams plan -- feature: observability

- timestamp: 2026-04-24T18:16:27Z
- worktree_base: `worktrees\observability`
- parallel: 3
- pairs: 3

## Task pairs
### task-T-A-dual-status
- task_file: `work\observability\tasks\task-T-A-dual-status.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\observability\claude\task-T-A-dual-status` (branch `claude/dual-teams/task-T-A-dual-status`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\observability\codex\task-T-A-dual-status` (branch `codex/dual-teams/task-T-A-dual-status`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\observability\prompts\task-T-A-dual-status-claude.md` [ok]

### task-T-B-codex-health
- task_file: `work\observability\tasks\task-T-B-codex-health.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\observability\claude\task-T-B-codex-health` (branch `claude/dual-teams/task-T-B-codex-health`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\observability\codex\task-T-B-codex-health` (branch `codex/dual-teams/task-T-B-codex-health`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\observability\prompts\task-T-B-codex-health-claude.md` [ok]

### task-T-C-pipeline-status
- task_file: `work\observability\tasks\task-T-C-pipeline-status.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\observability\claude\task-T-C-pipeline-status` (branch `claude/dual-teams/task-T-C-pipeline-status`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\observability\codex\task-T-C-pipeline-status` (branch `codex/dual-teams/task-T-C-pipeline-status`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\observability\prompts\task-T-C-pipeline-status-claude.md` [ok]

## Codex wave (background)
- pid: `26452`
- log: `.claude\logs\codex-wave-observability-1777054591.log`
- cmd: `C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe .claude\scripts\codex-wave.py --tasks work\observability\tasks\task-T-A-dual-status.md,work\observability\tasks\task-T-B-codex-health.md,work\observability\tasks\task-T-C-pipeline-status.md --parallel 3 --worktree-base worktrees\observability\codex --base-branch HEAD`

## Instructions for Opus

1. Spawn N Claude teammates (one per task) via TeamCreate. Use each
   prompt file above; each teammate's cwd is its claude_worktree.

2. Wait on the Codex wave (background PID above). Monitor with:
       tasklist /FI "PID eq 26452"
       tail -f .claude\logs\codex-wave-observability-1777054591.log

3. Paired results:
   - Claude diffs: each claude_worktree (branch claude/dual-teams/T{i})
   - Codex diffs:  each codex_worktree (branch codex/dual-teams/T{i})
   - Codex result.md: work/codex-implementations/task-T{i}-result.md

4. Use cross-model-review skill to judge each pair; pick winner or hybrid.

