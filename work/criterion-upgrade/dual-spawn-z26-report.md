# dual-teams plan -- feature: criterion-upgrade-z26

- timestamp: 2026-04-26T18:26:19Z
- worktree_base: `worktrees\criterion-upgrade-z26`
- parallel: 1
- pairs: 1

## Task pairs
### task-Z26-maintainability-ci-memory-changelog
- task_file: `work\criterion-upgrade\task-Z26-maintainability-ci-memory-changelog.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z26\claude\task-Z26-maintainability-ci-memory-changelog` (branch `claude/dual-teams/task-Z26-maintainability-ci-memory-changelog`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z26\codex\task-Z26-maintainability-ci-memory-changelog` (branch `codex/dual-teams/task-Z26-maintainability-ci-memory-changelog`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\criterion-upgrade-z26\prompts\task-Z26-maintainability-ci-memory-changelog-claude.md` [ok]

## Codex wave (background)
- pid: `31240`
- log: `.claude\logs\codex-wave-criterion-upgrade-z26-1777227980.log`
- result_dir: C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations
- cmd: `C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe .claude\scripts\codex-wave.py --tasks work\criterion-upgrade\task-Z26-maintainability-ci-memory-changelog.md --parallel 1 --worktree-base worktrees\criterion-upgrade-z26\codex --base-branch HEAD --result-dir C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations`

## Instructions for Opus

1. Spawn N Claude teammates (one per task) via TeamCreate. Use each
   prompt file above; each teammate's cwd is its claude_worktree.

2. Wait on the Codex wave (background PID above). Monitor with:
       tasklist /FI "PID eq 31240"
       tail -f .claude\logs\codex-wave-criterion-upgrade-z26-1777227980.log

3. Paired results:
   - Claude diffs: each claude_worktree (branch claude/dual-teams/T{i})
   - Codex diffs:  each codex_worktree (branch codex/dual-teams/T{i})
   - Codex result.md: work/codex-implementations/task-T{i}-result.md

4. Use cross-model-review skill to judge each pair; pick winner or hybrid.

