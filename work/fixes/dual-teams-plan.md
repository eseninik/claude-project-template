# dual-teams plan -- feature: fixes

- timestamp: 2026-04-24T19:08:36Z
- worktree_base: `worktrees\fixes`
- parallel: 2
- pairs: 2

## Task pairs
### task-FIX-A-judge-diff-baseline
- task_file: `work\fixes\tasks\task-FIX-A-judge-diff-baseline.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\fixes\claude\task-FIX-A-judge-diff-baseline` (branch `claude/dual-teams/task-FIX-A-judge-diff-baseline`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\fixes\codex\task-FIX-A-judge-diff-baseline` (branch `codex/dual-teams/task-FIX-A-judge-diff-baseline`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\fixes\prompts\task-FIX-A-judge-diff-baseline-claude.md` [ok]

### task-FIX-B-dual-base-ref-sidecar
- task_file: `work\fixes\tasks\task-FIX-B-dual-base-ref-sidecar.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\fixes\claude\task-FIX-B-dual-base-ref-sidecar` (branch `claude/dual-teams/task-FIX-B-dual-base-ref-sidecar`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\fixes\codex\task-FIX-B-dual-base-ref-sidecar` (branch `codex/dual-teams/task-FIX-B-dual-base-ref-sidecar`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\fixes\prompts\task-FIX-B-dual-base-ref-sidecar-claude.md` [ok]

## Codex wave (background)
- pid: `27788`
- log: `.claude\logs\codex-wave-fixes-1777057718.log`
- cmd: `C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe .claude\scripts\codex-wave.py --tasks work\fixes\tasks\task-FIX-A-judge-diff-baseline.md,work\fixes\tasks\task-FIX-B-dual-base-ref-sidecar.md --parallel 2 --worktree-base worktrees\fixes\codex --base-branch HEAD`

## Instructions for Opus

1. Spawn N Claude teammates (one per task) via TeamCreate. Use each
   prompt file above; each teammate's cwd is its claude_worktree.

2. Wait on the Codex wave (background PID above). Monitor with:
       tasklist /FI "PID eq 27788"
       tail -f .claude\logs\codex-wave-fixes-1777057718.log

3. Paired results:
   - Claude diffs: each claude_worktree (branch claude/dual-teams/T{i})
   - Codex diffs:  each codex_worktree (branch codex/dual-teams/T{i})
   - Codex result.md: work/codex-implementations/task-T{i}-result.md

4. Use cross-model-review skill to judge each pair; pick winner or hybrid.

