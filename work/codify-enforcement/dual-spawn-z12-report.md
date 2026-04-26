# dual-teams plan -- feature: codify-enforcement-z12

- timestamp: 2026-04-26T13:07:50Z
- worktree_base: `worktrees\codify-enforcement-z12`
- parallel: 1
- pairs: 1

## Task pairs
### task-Z12-y21-y25-judge-diagnostic
- task_file: `work\codify-enforcement\task-Z12-y21-y25-judge-diagnostic.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\claude\task-Z12-y21-y25-judge-diagnostic` (branch `claude/dual-teams/task-Z12-y21-y25-judge-diagnostic`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic` (branch `codex/dual-teams/task-Z12-y21-y25-judge-diagnostic`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\codify-enforcement-z12\prompts\task-Z12-y21-y25-judge-diagnostic-claude.md` [ok]

## Codex wave (background)
- pid: `18120`
- log: `.claude\logs\codex-wave-codify-enforcement-z12-1777208871.log`
- result_dir: C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations
- cmd: `C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe .claude\scripts\codex-wave.py --tasks work\codify-enforcement\task-Z12-y21-y25-judge-diagnostic.md --parallel 1 --worktree-base worktrees\codify-enforcement-z12\codex --base-branch HEAD --result-dir C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations`

## Instructions for Opus

1. Spawn N Claude teammates (one per task) via TeamCreate. Use each
   prompt file above; each teammate's cwd is its claude_worktree.

2. Wait on the Codex wave (background PID above). Monitor with:
       tasklist /FI "PID eq 18120"
       tail -f .claude\logs\codex-wave-codify-enforcement-z12-1777208871.log

3. Paired results:
   - Claude diffs: each claude_worktree (branch claude/dual-teams/T{i})
   - Codex diffs:  each codex_worktree (branch codex/dual-teams/T{i})
   - Codex result.md: work/codex-implementations/task-T{i}-result.md

4. Use cross-model-review skill to judge each pair; pick winner or hybrid.

