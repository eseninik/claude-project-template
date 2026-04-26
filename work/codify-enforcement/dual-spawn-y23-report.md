# dual-teams plan -- feature: codify-enforcement-y23

- timestamp: 2026-04-26T08:48:47Z
- worktree_base: `worktrees\codify-enforcement-y23`
- parallel: 1
- pairs: 1

## Task pairs
### task-Y23-codex-ask-v125
- task_file: `work\codify-enforcement\task-Y23-codex-ask-v125.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-y23\claude\task-Y23-codex-ask-v125` (branch `claude/dual-teams/task-Y23-codex-ask-v125`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-y23\codex\task-Y23-codex-ask-v125` (branch `codex/dual-teams/task-Y23-codex-ask-v125`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\codify-enforcement-y23\prompts\task-Y23-codex-ask-v125-claude.md` [ok]

## Codex wave (background)
- pid: `3688`
- log: `.claude\logs\codex-wave-codify-enforcement-y23-1777193328.log`
- result_dir: C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations
- cmd: `C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe .claude\scripts\codex-wave.py --tasks work\codify-enforcement\task-Y23-codex-ask-v125.md --parallel 1 --worktree-base worktrees\codify-enforcement-y23\codex --base-branch HEAD --result-dir C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations`

## Instructions for Opus

1. Spawn N Claude teammates (one per task) via TeamCreate. Use each
   prompt file above; each teammate's cwd is its claude_worktree.

2. Wait on the Codex wave (background PID above). Monitor with:
       tasklist /FI "PID eq 3688"
       tail -f .claude\logs\codex-wave-codify-enforcement-y23-1777193328.log

3. Paired results:
   - Claude diffs: each claude_worktree (branch claude/dual-teams/T{i})
   - Codex diffs:  each codex_worktree (branch codex/dual-teams/T{i})
   - Codex result.md: work/codex-implementations/task-T{i}-result.md

4. Use cross-model-review skill to judge each pair; pick winner or hybrid.

