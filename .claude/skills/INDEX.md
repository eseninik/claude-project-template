# Skills Index

> Navigation hub for 22 agent skills. Agent scans categories, follows chains to relevant skills.
> Each skill has `## Related` section with cross-references for graph traversal.

---

## Planning & Specification

```
project-planning → user-spec-planning → tech-spec-planning → task-decomposition
```

| Skill | Purpose |
|-------|---------|
| project-planning | Interview → project.md + features.md + roadmap.md |
| user-spec-planning | Interview → user-spec.md with acceptance criteria |
| tech-spec-planning | Architecture + tasks/*.md from user-spec |
| task-decomposition | DAG-based parallel subtask breakdown with waves |
| project-knowledge | Documentation hub: architecture, patterns, DB, deploy |

## Execution & Parallelism

```
task-decomposition → subagent-driven-development ──→ qa-validation-loop
                          ├── using-git-worktrees     → finishing-a-development-branch
                          ├── ao-hybrid-spawn (full-context alternative)
                          └── ao-fleet-spawn (multi-project alternative)
```

| Skill | Purpose |
|-------|---------|
| subagent-driven-development | Dispatch subagent per task, auto-parallelize into waves |
| ao-hybrid-spawn | Full Claude Code sessions with skills/memory/hooks (single project) |
| ao-fleet-spawn | Parallel sessions across multiple projects/repos |
| using-git-worktrees | Isolated workspaces for parallel branch work |
| self-completion | Auto-continue through pending tasks until done |

## Quality & Verification

```
qa-validation-loop → verification-before-completion
                         ↑
systematic-debugging ────┘
```

| Skill | Purpose |
|-------|---------|
| qa-validation-loop | Risk-proportional QA with Reviewer + Fixer agents |
| verification-before-completion | Evidence-based completion gate (goal-backward) |
| systematic-debugging | 4-phase debugging: investigate → analyze → test → fix |
| error-recovery | Structured recovery for tool/test/timeout failures |

## Analysis & Research

| Skill | Purpose |
|-------|---------|
| expert-panel | 3-5 domain experts for deep analysis before implementation |
| codebase-mapping | Map unfamiliar codebase → codebase-map.md |
| experiment-loop | Autonomous hypothesis → experiment → measure → keep/discard |
| mcp-integration | On-demand MCP server calls (search, scraping, docs) |

## Skill Lifecycle

```
skill-conductor (CREATE) → skill-evolution (IMPROVE from usage) → skill-conductor (VALIDATE)
```

| Skill | Purpose |
|-------|---------|
| skill-conductor | Full lifecycle: CREATE/IMPROVE/VALIDATE/REVIEW/OPTIMIZE/PACKAGE |
| skill-evolution | Self-improving from real execution learnings |

## Infrastructure & Finishing

| Skill | Purpose |
|-------|---------|
| infrastructure | CI/CD, testing, Docker, pre-commit hooks, auto-deploy |
| finishing-a-development-branch | 4 options: merge, PR, keep, discard |
