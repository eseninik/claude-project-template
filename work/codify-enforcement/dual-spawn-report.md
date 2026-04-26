# dual-teams plan -- feature: codify-enforcement

- timestamp: 2026-04-26T05:34:35Z
- worktree_base: `worktrees\codify-enforcement`
- parallel: 1
- pairs: 1

## Task pairs
### task-Z1-invariants
- task_file: `work\codify-enforcement\task-Z1-invariants.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement\claude\task-Z1-invariants` (branch `claude/dual-teams/task-Z1-invariants`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement\codex\task-Z1-invariants` (branch `codex/dual-teams/task-Z1-invariants`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\codify-enforcement\prompts\task-Z1-invariants-claude.md` [ok]

## Codex wave (background)
- pid: `19480`
- log: `.claude\logs\codex-wave-codify-enforcement-1777181676.log`
- result_dir: C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations
- cmd: `C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe .claude\scripts\codex-wave.py --tasks work\codify-enforcement\task-Z1-invariants.md --parallel 1 --worktree-base worktrees\codify-enforcement\codex --base-branch HEAD --result-dir C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations`

## Instructions for Opus

1. Spawn N Claude teammates (one per task) via TeamCreate. Use each
   prompt file above; each teammate's cwd is its claude_worktree.

2. Wait on the Codex wave (background PID above). Monitor with:
       tasklist /FI "PID eq 19480"
       tail -f .claude\logs\codex-wave-codify-enforcement-1777181676.log

3. Paired results:
   - Claude diffs: each claude_worktree (branch claude/dual-teams/T{i})
   - Codex diffs:  each codex_worktree (branch codex/dual-teams/T{i})
   - Codex result.md: work/codex-implementations/task-T{i}-result.md

4. Use cross-model-review skill to judge each pair; pick winner or hybrid.

