# dual-teams plan -- feature: validation

- timestamp: 2026-04-25T07:55:54Z
- worktree_base: `worktrees\validation-2`
- parallel: 2
- pairs: 2

## Task pairs
### task-V3-worktree-cleaner
- task_file: `work\validation\tasks\task-V3-worktree-cleaner.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation-2\claude\task-V3-worktree-cleaner` (branch `claude/dual-teams/task-V3-worktree-cleaner`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation-2\codex\task-V3-worktree-cleaner` (branch `codex/dual-teams/task-V3-worktree-cleaner`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\validation\prompts\task-V3-worktree-cleaner-claude.md` [ok]

### task-V4-verdict-summarizer
- task_file: `work\validation\tasks\task-V4-verdict-summarizer.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation-2\claude\task-V4-verdict-summarizer` (branch `claude/dual-teams/task-V4-verdict-summarizer`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation-2\codex\task-V4-verdict-summarizer` (branch `codex/dual-teams/task-V4-verdict-summarizer`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\validation\prompts\task-V4-verdict-summarizer-claude.md` [ok]

## Codex wave (background)
- pid: `36092`
- log: `.claude\logs\codex-wave-validation-1777103756.log`
- cmd: `C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe .claude\scripts\codex-wave.py --tasks work\validation\tasks\task-V3-worktree-cleaner.md,work\validation\tasks\task-V4-verdict-summarizer.md --parallel 2 --worktree-base worktrees\validation-2\codex --base-branch HEAD`

## Instructions for Opus

1. Spawn N Claude teammates (one per task) via TeamCreate. Use each
   prompt file above; each teammate's cwd is its claude_worktree.

2. Wait on the Codex wave (background PID above). Monitor with:
       tasklist /FI "PID eq 36092"
       tail -f .claude\logs\codex-wave-validation-1777103756.log

3. Paired results:
   - Claude diffs: each claude_worktree (branch claude/dual-teams/T{i})
   - Codex diffs:  each codex_worktree (branch codex/dual-teams/T{i})
   - Codex result.md: work/codex-implementations/task-T{i}-result.md

4. Use cross-model-review skill to judge each pair; pick winner or hybrid.

