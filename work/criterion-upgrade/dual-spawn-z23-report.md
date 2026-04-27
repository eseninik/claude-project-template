# dual-teams plan -- feature: criterion-upgrade-z23

- timestamp: 2026-04-26T18:13:25Z
- worktree_base: `worktrees\criterion-upgrade-z23`
- parallel: 1
- pairs: 1

## Task pairs
### task-Z23-determinism-chaos-encoding
- task_file: `work\criterion-upgrade\task-Z23-determinism-chaos-encoding.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z23\claude\task-Z23-determinism-chaos-encoding` (branch `claude/dual-teams/task-Z23-determinism-chaos-encoding`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z23\codex\task-Z23-determinism-chaos-encoding` (branch `codex/dual-teams/task-Z23-determinism-chaos-encoding`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\criterion-upgrade-z23\prompts\task-Z23-determinism-chaos-encoding-claude.md` [ok]

## Codex wave (background)
- pid: `30712`
- log: `.claude\logs\codex-wave-criterion-upgrade-z23-1777227206.log`
- result_dir: C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations
- cmd: `C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe .claude\scripts\codex-wave.py --tasks work\criterion-upgrade\task-Z23-determinism-chaos-encoding.md --parallel 1 --worktree-base worktrees\criterion-upgrade-z23\codex --base-branch HEAD --result-dir C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations`

## Instructions for Opus

1. Spawn N Claude teammates (one per task) via TeamCreate. Use each
   prompt file above; each teammate's cwd is its claude_worktree.

2. Wait on the Codex wave (background PID above). Monitor with:
       tasklist /FI "PID eq 30712"
       tail -f .claude\logs\codex-wave-criterion-upgrade-z23-1777227206.log

3. Paired results:
   - Claude diffs: each claude_worktree (branch claude/dual-teams/T{i})
   - Codex diffs:  each codex_worktree (branch codex/dual-teams/T{i})
   - Codex result.md: work/codex-implementations/task-T{i}-result.md

4. Use cross-model-review skill to judge each pair; pick winner or hybrid.

