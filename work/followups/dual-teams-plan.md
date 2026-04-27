# dual-teams plan -- feature: followups

- timestamp: 2026-04-25T10:12:49Z
- worktree_base: `worktrees\followups`
- parallel: 2
- pairs: 2

## Task pairs
### task-Y8-gate-sentinel
- task_file: `work\codex-implementations\inline\task-Y8-gate-sentinel.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\followups\claude\task-Y8-gate-sentinel` (branch `claude/dual-teams/task-Y8-gate-sentinel`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\followups\codex\task-Y8-gate-sentinel` (branch `codex/dual-teams/task-Y8-gate-sentinel`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\followups\prompts\task-Y8-gate-sentinel-claude.md` [ok]

### task-Y9-spawn-resultdir
- task_file: `work\codex-implementations\inline\task-Y9-spawn-resultdir.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\followups\claude\task-Y9-spawn-resultdir` (branch `claude/dual-teams/task-Y9-spawn-resultdir`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\followups\codex\task-Y9-spawn-resultdir` (branch `codex/dual-teams/task-Y9-spawn-resultdir`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\followups\prompts\task-Y9-spawn-resultdir-claude.md` [ok]

## Codex wave (background)
- pid: `21012`
- log: `.claude\logs\codex-wave-followups-1777111971.log`
- cmd: `C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe .claude\scripts\codex-wave.py --tasks work\codex-implementations\inline\task-Y8-gate-sentinel.md,work\codex-implementations\inline\task-Y9-spawn-resultdir.md --parallel 2 --worktree-base worktrees\followups\codex --base-branch HEAD`

## Instructions for Opus

1. Spawn N Claude teammates (one per task) via TeamCreate. Use each
   prompt file above; each teammate's cwd is its claude_worktree.

2. Wait on the Codex wave (background PID above). Monitor with:
       tasklist /FI "PID eq 21012"
       tail -f .claude\logs\codex-wave-followups-1777111971.log

3. Paired results:
   - Claude diffs: each claude_worktree (branch claude/dual-teams/T{i})
   - Codex diffs:  each codex_worktree (branch codex/dual-teams/T{i})
   - Codex result.md: work/codex-implementations/task-T{i}-result.md

4. Use cross-model-review skill to judge each pair; pick winner or hybrid.

