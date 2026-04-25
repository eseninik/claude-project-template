# dual-teams plan -- feature: validation

- timestamp: 2026-04-24T19:22:43Z
- worktree_base: `worktrees\validation`
- parallel: 2
- pairs: 2

## Task pairs
### task-V1-knowledge-decay-report
- task_file: `work\validation\tasks\task-V1-knowledge-decay-report.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\claude\task-V1-knowledge-decay-report` (branch `claude/dual-teams/task-V1-knowledge-decay-report`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\codex\task-V1-knowledge-decay-report` (branch `codex/dual-teams/task-V1-knowledge-decay-report`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\validation\prompts\task-V1-knowledge-decay-report-claude.md` [ok]

### task-V2-task-spec-validator
- task_file: `work\validation\tasks\task-V2-task-spec-validator.md`
- claude_worktree: `C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\claude\task-V2-task-spec-validator` (branch `claude/dual-teams/task-V2-task-spec-validator`)
- codex_worktree:  `C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\codex\task-V2-task-spec-validator` (branch `codex/dual-teams/task-V2-task-spec-validator`)
- claude_prompt:   `C:\Bots\Migrator bots\claude-project-template-update\work\validation\prompts\task-V2-task-spec-validator-claude.md` [ok]

## Codex wave (background)
- pid: `4652`
- log: `.claude\logs\codex-wave-validation-1777058565.log`
- cmd: `C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe .claude\scripts\codex-wave.py --tasks work\validation\tasks\task-V1-knowledge-decay-report.md,work\validation\tasks\task-V2-task-spec-validator.md --parallel 2 --worktree-base worktrees\validation\codex --base-branch HEAD`

## Instructions for Opus

1. Spawn N Claude teammates (one per task) via TeamCreate. Use each
   prompt file above; each teammate's cwd is its claude_worktree.

2. Wait on the Codex wave (background PID above). Monitor with:
       tasklist /FI "PID eq 4652"
       tail -f .claude\logs\codex-wave-validation-1777058565.log

3. Paired results:
   - Claude diffs: each claude_worktree (branch claude/dual-teams/T{i})
   - Codex diffs:  each codex_worktree (branch codex/dual-teams/T{i})
   - Codex result.md: work/codex-implementations/task-T{i}-result.md

4. Use cross-model-review skill to judge each pair; pick winner or hybrid.

