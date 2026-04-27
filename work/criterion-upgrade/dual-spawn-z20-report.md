# dual-teams plan -- feature: criterion-upgrade-z20

- timestamp: 2026-04-26T15:41:58Z
- worktree_base: `worktrees\criterion-upgrade-z20`
- parallel: 1
- pairs: 1

## Task pairs
### task-Z20-security-sandbox-allowlist
- task_file: `work\criterion-upgrade\task-Z20-security-sandbox-allowlist.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z20\claude\task-Z20-security-sandbox-allowlist` (branch `claude/dual-teams/task-Z20-security-sandbox-allowlist`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z20\codex\task-Z20-security-sandbox-allowlist` (branch `codex/dual-teams/task-Z20-security-sandbox-allowlist`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\criterion-upgrade-z20\prompts\task-Z20-security-sandbox-allowlist-claude.md` [ok]

## Codex wave (background)
- pid: `24596`
- log: `.claude\logs\codex-wave-criterion-upgrade-z20-1777218120.log`
- result_dir: C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations
- cmd: `C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe .claude\scripts\codex-wave.py --tasks work\criterion-upgrade\task-Z20-security-sandbox-allowlist.md --parallel 1 --worktree-base worktrees\criterion-upgrade-z20\codex --base-branch HEAD --result-dir C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations`

## Instructions for Opus

1. Spawn N Claude teammates (one per task) via TeamCreate. Use each
   prompt file above; each teammate's cwd is its claude_worktree.

2. Wait on the Codex wave (background PID above). Monitor with:
       tasklist /FI "PID eq 24596"
       tail -f .claude\logs\codex-wave-criterion-upgrade-z20-1777218120.log

3. Paired results:
   - Claude diffs: each claude_worktree (branch claude/dual-teams/T{i})
   - Codex diffs:  each codex_worktree (branch codex/dual-teams/T{i})
   - Codex result.md: work/codex-implementations/task-T{i}-result.md

4. Use cross-model-review skill to judge each pair; pick winner or hybrid.

