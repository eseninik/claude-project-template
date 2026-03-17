# Context Loading Triggers

> Reference: when to load which guide or skill. Lookup table for agents.

## Guides (load via `cat`)

| Situation | Load |
|-----------|------|
| Pipeline execution | `cat .claude/guides/autonomous-pipeline.md` |
| Plan for implementation | `cat .claude/guides/plan-execution-enforcer.md` |
| Spawning teammate | `cat .claude/guides/teammate-prompt-template.md` |
| Expert Panel | `cat .claude/guides/expert-panel-workflow.md` |
| Phase template needed | `cat .claude/shared/work-templates/phases/{PHASE}.md` |
| Agent type lookup | `cat .claude/agents/registry.md` |
| Graphiti memory setup | `cat .claude/guides/graphiti-integration.md` |
| Decision capture before planning | `cat .claude/guides/discuss-phase-decisions.md` |
| Quick ad-hoc task | `cat .claude/guides/quick-mode.md` |
| Project health check | `cat .claude/guides/health-check.md` |
| Agent Teams coordination | `cat .claude/guides/results-board.md` |
| Writing/modifying code | `cat .claude/guides/logging-standards.md` |
| Auto-research phase | `cat .claude/guides/auto-research-phase.md` |
| Memory decay details | `cat .claude/guides/memory-decay.md` |

## Skills (invoke via Skill tool)

| Situation | Skill to Invoke |
|-----------|----------------|
| Debugging any error | systematic-debugging |
| Before claiming "done" | verification-before-completion |
| Executing plan with subtasks | subagent-driven-development |
| Decomposing complex task | task-decomposition |
| QA after implementation | qa-validation-loop |
| Tool call failures | error-recovery |
| Branch merge/PR | finishing-a-development-branch |
| Worktree needed | using-git-worktrees |
| Pending todos after task | self-completion |
| Expert panel requested | expert-panel |
| Unknown codebase | codebase-mapping |
| AO Hybrid execution | ao-hybrid-spawn |
| Fleet cross-project ops | ao-fleet-spawn |
| Pre-implementation test mapping | qa-validation-loop (Nyquist mode) |
| Optimization/experiment task | experiment-loop |
| Skill improved from usage | skill-evolution |
