# dual-teams plan -- feature: codify-enforcement-z10

- timestamp: 2026-04-26T12:30:20Z
- worktree_base: `worktrees\codify-enforcement-z10`
- parallel: 1
- pairs: 1

## Task pairs
### task-Z10-y19-y22-script-infra
- task_file: `work\codify-enforcement\task-Z10-y19-y22-script-infra.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z10\claude\task-Z10-y19-y22-script-infra` (branch `claude/dual-teams/task-Z10-y19-y22-script-infra`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z10\codex\task-Z10-y19-y22-script-infra` (branch `codex/dual-teams/task-Z10-y19-y22-script-infra`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\codify-enforcement-z10\prompts\task-Z10-y19-y22-script-infra-claude.md` [ok]

## Codex wave (background)
- pid: `15448`
- log: `.claude\logs\codex-wave-codify-enforcement-z10-1777206621.log`
- result_dir: C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations
- cmd: `C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe .claude\scripts\codex-wave.py --tasks work\codify-enforcement\task-Z10-y19-y22-script-infra.md --parallel 1 --worktree-base worktrees\codify-enforcement-z10\codex --base-branch HEAD --result-dir C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations`

## Instructions for Opus

1. Spawn N Claude teammates (one per task) via TeamCreate. Use each
   prompt file above; each teammate's cwd is its claude_worktree.

2. Wait on the Codex wave (background PID above). Monitor with:
       tasklist /FI "PID eq 15448"
       tail -f .claude\logs\codex-wave-codify-enforcement-z10-1777206621.log

3. Paired results:
   - Claude diffs: each claude_worktree (branch claude/dual-teams/T{i})
   - Codex diffs:  each codex_worktree (branch codex/dual-teams/T{i})
   - Codex result.md: work/codex-implementations/task-T{i}-result.md

4. Use cross-model-review skill to judge each pair; pick winner or hybrid.

