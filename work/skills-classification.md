# Skills Classification — Phase 2 Results

> Based on Phase 1 analysis by 4 research agents + lead synthesis

## Root Cause: Why Skills Aren't Used

1. **Skills = generic documentation, not executable logic.** Loading 200 lines of "how to do TDD" adds nothing to Opus, which already knows TDD perfectly.
2. **No automatic loading mechanism.** Skills require manual `cat .claude/skills/.../SKILL.md`. No agent spontaneously does this.
3. **Agent definitions have `skills` field** but this is Piebald marketplace feature, not available for Task-spawned teammates.
4. **Context cost > value.** Loading 2-3 skills = 400-600 tokens of generic advice, displacing actual task context.
5. **The teammate-prompt-template says "load these skills"** but teammates treat it as optional reading, not mandatory instructions.

## Classification Matrix

### ESSENTIAL (6) — Keep and improve
Skills that provide unique procedural value the agent can't derive.

| Skill | Reason | Action |
|-------|--------|--------|
| **verification-before-completion** | Unique checklist preventing false "done" claims | KEEP - referenced in CLAUDE.md BLOCKING RULES |
| **expert-panel** | Complex orchestration protocol (10 roles, 4 phases) | KEEP - unique workflow |
| **subagent-driven-development** | Wave parallelization + worktree mode logic | KEEP - complex procedure |
| **session-resumption** | Git state checks + worktree recovery | KEEP - startup protocol |
| **project-knowledge** | Project-specific docs router (not generic) | KEEP - per-project value |
| **codebase-mapping** | Discovery protocol for unknown codebases | KEEP - procedural |

### USEFUL (8) — Keep but reduce to checklists
Skills with some unique value but bloated with generic advice.

| Skill | Reason | Action |
|-------|--------|--------|
| **executing-plans** | Batch execution with review checkpoints | KEEP - trim to 50 lines |
| **task-decomposition** | Parallelization detection algorithm | KEEP - trim to 50 lines |
| **systematic-debugging** | 4-phase framework useful as checklist | KEEP - trim to checklist |
| **error-recovery** | Retry/backoff patterns specific to CC tools | KEEP - trim |
| **context-monitor** | Threshold-based warnings | KEEP - trim |
| **finishing-a-development-branch** | Merge/PR workflow | KEEP - trim |
| **using-git-worktrees** | Worktree management procedures | KEEP - trim |
| **self-completion** | Auto-continue protocol | KEEP - trim |

### MARGINAL (17) — Merge into guides or remove
Skills that duplicate what Opus already knows perfectly.

| Skill | Reason | Action |
|-------|--------|--------|
| **test-driven-development** | Opus knows TDD, 183 lines of generic advice | MERGE into CLAUDE.md one-liner: "Use TDD" |
| **async-python-patterns** | Opus knows asyncio patterns | MERGE or REMOVE |
| **python-testing-patterns** | Opus knows pytest | MERGE or REMOVE |
| **telegram-bot-architecture** | Opus knows aiogram patterns | MERGE or REMOVE |
| **python-packaging** | Opus knows pyproject.toml | REMOVE |
| **python-performance-optimization** | Opus knows profiling | REMOVE |
| **uv-package-manager** | Opus knows uv commands | REMOVE |
| **architecture-patterns** | Opus knows Clean Architecture | REMOVE |
| **api-design-principles** | Opus knows REST API design | REMOVE |
| **security-checklist** | Generic OWASP checklist | MERGE into one-liner |
| **secret-scanner** | Opus can scan for secrets without a skill | REMOVE |
| **defense-in-depth** | Generic validation advice | REMOVE |
| **condition-based-waiting** | Generic async testing advice | REMOVE |
| **dispatching-parallel-agents** | Subsumed by subagent-driven-dev | REMOVE |
| **root-cause-tracing** | Subsumed by systematic-debugging | MERGE |
| **testing-anti-patterns** | Generic testing advice | MERGE into code-reviewer |
| **test-generator** | Opus generates tests without a skill | REMOVE |

### REMOVE (13) — No pipeline value
Skills that are meta, duplicate, or never used.

| Skill | Reason | Action |
|-------|--------|--------|
| **methodology** | Meta-documentation about the template itself | REMOVE |
| **project-planning** | Interview protocol, not pipeline-relevant | REMOVE (keep as command) |
| **user-spec-planning** | Interview protocol | REMOVE (keep as command) |
| **tech-spec-planning** | Interview protocol | REMOVE (keep as command) |
| **context-capture** | Vague "exploratory discussion" | REMOVE |
| **infrastructure** | Generic CI/CD setup | REMOVE |
| **testing** | Generic strategy doc | REMOVE |
| **skill-development** | Meta-skill about creating skills | REMOVE |
| **command-manager** | Meta-skill about managing commands | REMOVE |
| **documentation** | Meta-skill about docs | REMOVE |
| **code-reviewer** | Agent can review code without a skill | REMOVE |
| **requesting-code-review** | Process doc, not a skill | REMOVE |
| **receiving-code-review** | Process doc, not a skill | REMOVE |
| **user-acceptance-testing** | Generic UAT checklist | REMOVE |
| **mcp-integration** | Workflow doc, should be a guide | MOVE to guides/ |

## Summary

| Category | Count | % of 44 |
|----------|-------|---------|
| ESSENTIAL | 6 | 14% |
| USEFUL | 8 | 18% |
| MARGINAL | 17 | 39% |
| REMOVE | 13 | 30% |

**Total after cleanup: 14 skills** (6 essential + 8 useful) = 68% reduction.

## Key Insight for Pipeline

For the autonomous pipeline, skills should work differently:
1. **CLAUDE.md contains all behavioral rules** (they're already there)
2. **Pipeline phases reference guides** (not skills) for procedural knowledge
3. **Skills only exist for complex, multi-step procedures** that can't be a one-liner
4. **Most "skills" should become one-line rules** in CLAUDE.md instead

## Decision: New Architecture

Instead of 44 skills, the system should have:
- **6 ESSENTIAL skills** — complex procedures loaded on-demand
- **8 USEFUL skills** — trimmed to 50-line checklists
- **CLAUDE.md rules** — one-liners for everything else ("Use TDD", "Validate inputs")
- **Guides** — reference documentation loaded when needed (already exists)
