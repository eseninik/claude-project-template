# dual-teams plan -- feature: y11-live

- timestamp: 2026-04-25T16:29:01Z
- worktree_base: `worktrees\y11-live`
- parallel: 1
- pairs: 1

## Task pairs
### task-Y11-LIVE-pytool-version
- task_file: `work\codex-implementations\inline\task-Y11-LIVE-pytool-version.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\y11-live\claude\task-Y11-LIVE-pytool-version` (branch `claude/dual-teams/task-Y11-LIVE-pytool-version`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\y11-live\codex\task-Y11-LIVE-pytool-version` (branch `codex/dual-teams/task-Y11-LIVE-pytool-version`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\y11-live\prompts\task-Y11-LIVE-pytool-version-claude.md` [ok]

## Codex wave (background)
- pid: `20392`
- log: `.claude\logs\codex-wave-y11-live-1777134542.log`
- result_dir: C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations
- cmd: `C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe .claude\scripts\codex-wave.py --tasks work\codex-implementations\inline\task-Y11-LIVE-pytool-version.md --parallel 1 --worktree-base worktrees\y11-live\codex --base-branch HEAD --result-dir C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations`

## Instructions for Opus

1. Spawn N Claude teammates (one per task) via TeamCreate. Use each
   prompt file above; each teammate's cwd is its claude_worktree.

2. Wait on the Codex wave (background PID above). Monitor with:
       tasklist /FI "PID eq 20392"
       tail -f .claude\logs\codex-wave-y11-live-1777134542.log

3. Paired results:
   - Claude diffs: each claude_worktree (branch claude/dual-teams/T{i})
   - Codex diffs:  each codex_worktree (branch codex/dual-teams/T{i})
   - Codex result.md: work/codex-implementations/task-T{i}-result.md

4. Use cross-model-review skill to judge each pair; pick winner or hybrid.

