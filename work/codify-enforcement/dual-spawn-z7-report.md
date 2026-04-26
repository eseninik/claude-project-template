# dual-teams plan -- feature: codify-enforcement-z7

- timestamp: 2026-04-26T09:05:54Z
- worktree_base: `worktrees\codify-enforcement-z7`
- parallel: 1
- pairs: 1

## Task pairs
### task-Z7-v02-v03-fixes
- task_file: `work\codify-enforcement\task-Z7-v02-v03-fixes.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z7\claude\task-Z7-v02-v03-fixes` (branch `claude/dual-teams/task-Z7-v02-v03-fixes`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z7\codex\task-Z7-v02-v03-fixes` (branch `codex/dual-teams/task-Z7-v02-v03-fixes`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\codify-enforcement-z7\prompts\task-Z7-v02-v03-fixes-claude.md` [ok]

## Codex wave (background)
- pid: `22588`
- log: `.claude\logs\codex-wave-codify-enforcement-z7-1777194355.log`
- result_dir: C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations
- cmd: `C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe .claude\scripts\codex-wave.py --tasks work\codify-enforcement\task-Z7-v02-v03-fixes.md --parallel 1 --worktree-base worktrees\codify-enforcement-z7\codex --base-branch HEAD --result-dir C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations`

## Instructions for Opus

1. Spawn N Claude teammates (one per task) via TeamCreate. Use each
   prompt file above; each teammate's cwd is its claude_worktree.

2. Wait on the Codex wave (background PID above). Monitor with:
       tasklist /FI "PID eq 22588"
       tail -f .claude\logs\codex-wave-codify-enforcement-z7-1777194355.log

3. Paired results:
   - Claude diffs: each claude_worktree (branch claude/dual-teams/T{i})
   - Codex diffs:  each codex_worktree (branch codex/dual-teams/T{i})
   - Codex result.md: work/codex-implementations/task-T{i}-result.md

4. Use cross-model-review skill to judge each pair; pick winner or hybrid.

