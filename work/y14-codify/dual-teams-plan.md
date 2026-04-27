# dual-teams plan -- feature: y14-codify

- timestamp: 2026-04-25T16:47:19Z
- worktree_base: `worktrees\y14-codify`
- parallel: 2
- pairs: 2

## Task pairs
### task-Y15-update-prompt-template
- task_file: `work\codex-implementations\inline\task-Y15-update-prompt-template.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\y14-codify\claude\task-Y15-update-prompt-template` (branch `claude/dual-teams/task-Y15-update-prompt-template`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\y14-codify\codex\task-Y15-update-prompt-template` (branch `codex/dual-teams/task-Y15-update-prompt-template`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\y14-codify\prompts\task-Y15-update-prompt-template-claude.md` [ok]

### task-Y16-update-spawn-agent
- task_file: `work\codex-implementations\inline\task-Y16-update-spawn-agent.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\y14-codify\claude\task-Y16-update-spawn-agent` (branch `claude/dual-teams/task-Y16-update-spawn-agent`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\y14-codify\codex\task-Y16-update-spawn-agent` (branch `codex/dual-teams/task-Y16-update-spawn-agent`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\y14-codify\prompts\task-Y16-update-spawn-agent-claude.md` [ok]

## Codex wave (background)
- pid: `30704`
- log: `.claude\logs\codex-wave-y14-codify-1777135641.log`
- result_dir: C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations
- cmd: `C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe .claude\scripts\codex-wave.py --tasks work\codex-implementations\inline\task-Y15-update-prompt-template.md,work\codex-implementations\inline\task-Y16-update-spawn-agent.md --parallel 2 --worktree-base worktrees\y14-codify\codex --base-branch HEAD --result-dir C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations`

## Instructions for Opus

1. Spawn N Claude teammates (one per task) via TeamCreate. Use each
   prompt file above; each teammate's cwd is its claude_worktree.

2. Wait on the Codex wave (background PID above). Monitor with:
       tasklist /FI "PID eq 30704"
       tail -f .claude\logs\codex-wave-y14-codify-1777135641.log

3. Paired results:
   - Claude diffs: each claude_worktree (branch claude/dual-teams/T{i})
   - Codex diffs:  each codex_worktree (branch codex/dual-teams/T{i})
   - Codex result.md: work/codex-implementations/task-T{i}-result.md

4. Use cross-model-review skill to judge each pair; pick winner or hybrid.

