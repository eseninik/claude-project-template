# dual-teams plan -- feature: codify-enforcement-z5

- timestamp: 2026-04-26T08:58:34Z
- worktree_base: `worktrees\codify-enforcement-z5`
- parallel: 1
- pairs: 1

## Task pairs
### task-Z5-live-attack-matrix
- task_file: `work\codify-enforcement\task-Z5-live-attack-matrix.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\claude\task-Z5-live-attack-matrix` (branch `claude/dual-teams/task-Z5-live-attack-matrix`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z5\codex\task-Z5-live-attack-matrix` (branch `codex/dual-teams/task-Z5-live-attack-matrix`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\codify-enforcement-z5\prompts\task-Z5-live-attack-matrix-claude.md` [ok]

## Codex wave (background)
- pid: `33416`
- log: `.claude\logs\codex-wave-codify-enforcement-z5-1777193915.log`
- result_dir: C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations
- cmd: `C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe .claude\scripts\codex-wave.py --tasks work\codify-enforcement\task-Z5-live-attack-matrix.md --parallel 1 --worktree-base worktrees\codify-enforcement-z5\codex --base-branch HEAD --result-dir C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations`

## Instructions for Opus

1. Spawn N Claude teammates (one per task) via TeamCreate. Use each
   prompt file above; each teammate's cwd is its claude_worktree.

2. Wait on the Codex wave (background PID above). Monitor with:
       tasklist /FI "PID eq 33416"
       tail -f .claude\logs\codex-wave-codify-enforcement-z5-1777193915.log

3. Paired results:
   - Claude diffs: each claude_worktree (branch claude/dual-teams/T{i})
   - Codex diffs:  each codex_worktree (branch codex/dual-teams/T{i})
   - Codex result.md: work/codex-implementations/task-T{i}-result.md

4. Use cross-model-review skill to judge each pair; pick winner or hybrid.

