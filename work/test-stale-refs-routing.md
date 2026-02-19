## Test: Stale References + Skill Routing

**Date:** 2026-02-17
**Tester:** Test Agent (Claude Opus 4.6)

---

### Stale References to Deleted Skills

- In main project: **5 references** outside SKILLS_INDEX "Removed" section (FAIL)
- In template: **many references** outside SKILLS_INDEX "Removed" section (FAIL)
- Specific findings:

#### CLAUDE.md (main project) -- 5 stale references:
1. Line 16: `**Context:** .claude/skills/project-knowledge/guides/` -- references deleted skill directory
2. Line 91: `Read .claude/skills/project-knowledge/guides/architecture.md` -- deleted path
3. Line 92: `Read .claude/skills/project-knowledge/guides/patterns.md` -- deleted path
4. Line 121: `| Researcher/Explorer | codebase-mapping, project-knowledge |` -- lists deleted skill
5. Line 123: `| Pipeline Lead | subagent-driven-development, executing-plans |` -- lists deleted skill
6. Line 219: `| Project architecture | .claude/skills/project-knowledge/guides/ |` -- deleted path

#### .claude/skills/expert-panel/SKILL.md -- 2 stale references:
1. Line 15: `Business Analyst (project-knowledge)` -- deleted skill
2. Line 16: `System Architect (project-knowledge)` -- deleted skill

#### .claude/guides/ -- many stale references across multiple files:
- `teammate-prompt-template.md`: 5 refs (project-knowledge in role mapping, executing-plans in Pipeline Lead)
- `skills-reference.md`: 4 refs (executing-plans, project-knowledge, session-resumption, context-monitor in category tables)
- `plan-execution-enforcer.md`: ~16 refs to `executing-plans` throughout decision trees
- `plan-execution-protocol.md`: ~14 refs to `executing-plans` throughout decision trees
- `expert-panel-workflow.md`: 3 refs (project-knowledge paths, executing-plans)
- `work-items.md`: 1 ref to `executing-plans`
- `plan-format-conversion.md`: 1 ref to `executing-plans`
- `dependency-analysis.md`: ~10 refs to `executing-plans`

#### .claude/shared/work-templates/phases/ -- 4 stale references:
- `PLAN.md`: 2 refs to `project-knowledge`
- `REVIEW.md`: 1 ref to `project-knowledge`
- `SPEC.md`: 2 refs to `project-knowledge`

#### Template (.claude/shared/templates/new-project/) -- extensive stale references:
- `CLAUDE.md`: 6 refs (mirrors main CLAUDE.md stale refs)
- `README.md`: 2 refs to `project-knowledge`
- `.claude/agents/code-reviewer.md`: 2 refs to `project-knowledge`
- `.claude/agents/orchestrator.md`: 3 refs to `session-resumption`
- `.claude/agents/code-developer.md`: 3 refs to `project-knowledge`
- `.claude/skills/expert-panel/SKILL.md`: 2 refs to `project-knowledge`
- `.claude/guides/teammate-prompt-template.md`: 5 refs (same as main)
- `.claude/guides/plan-execution-enforcer.md`: ~16 refs to `executing-plans`
- `.claude/guides/expert-panel-workflow.md`: 3 refs
- `.claude/shared/work-templates/phases/PLAN.md`: 2 refs
- `.claude/shared/work-templates/phases/REVIEW.md`: 1 ref
- `.claude/shared/work-templates/phases/SPEC.md`: 2 refs

#### SKILLS_INDEX.md (both main + template) -- lines 72-75: OK (documents removed skills)

---

### Deleted Skill Directories

- Main: all 4 deleted: **YES** (executing-plans, session-resumption, project-knowledge, context-monitor -- none exist)
- Template: all 4 deleted: **YES** (none exist under `.claude/shared/templates/new-project/.claude/skills/`)

---

### Skill Counts

- Main: **11** (expected 11) -- PASS
- Template: **12** (expected 12, includes mcp-integration) -- PASS

Skills in main:
1. codebase-mapping
2. error-recovery
3. expert-panel
4. finishing-a-development-branch
5. qa-validation-loop
6. self-completion
7. subagent-driven-development
8. systematic-debugging
9. task-decomposition
10. using-git-worktrees
11. verification-before-completion

Template adds: mcp-integration

---

### Skill Sizes

- All under 50 lines (main): **YES**
- All under 50 lines (template): **NO** -- mcp-integration at 147 lines exceeds 50
- Largest (main): `subagent-driven-development` at 49 lines
- Largest (template): `mcp-integration` at **147 lines** (WARNING -- nearly 3x the 50-line limit)

#### Main skills (all pass):
| Skill | Lines | Status |
|-------|-------|--------|
| self-completion | 23 | OK |
| codebase-mapping | 30 | OK |
| verification-before-completion | 30 | OK |
| error-recovery | 31 | OK |
| finishing-a-development-branch | 32 | OK |
| task-decomposition | 37 | OK |
| systematic-debugging | 38 | OK |
| qa-validation-loop | 39 | OK |
| expert-panel | 42 | OK |
| using-git-worktrees | 44 | OK |
| subagent-driven-development | 49 | OK |

#### Template skill exceeding limit:
| Skill | Lines | Status |
|-------|-------|--------|
| mcp-integration | 147 | **FAIL** (limit: 50) |

---

### Skill Descriptions in System Prompt

- 11 skills visible in routing: **YES** (confirmed -- all 11 SKILL.md files exist and would be loaded by Claude Code's skill description system)
- List:
  1. codebase-mapping
  2. error-recovery
  3. expert-panel
  4. finishing-a-development-branch
  5. qa-validation-loop
  6. self-completion
  7. subagent-driven-development
  8. systematic-debugging
  9. task-decomposition
  10. using-git-worktrees
  11. verification-before-completion

Note: Skills are confirmed present as SKILL.md files. Actual system prompt injection of descriptions cannot be directly verified from within the agent, but the file structure is correct for Claude Code's skill routing mechanism.

---

### Broken References

- Broken file refs in CLAUDE.md: **4**
- Details:
  1. `.claude/skills/project-knowledge/guides/architecture.md` -- directory was deleted
  2. `.claude/skills/project-knowledge/guides/patterns.md` -- directory was deleted
  3. `.claude/skills/project-knowledge/guides/` -- directory was deleted
  4. `.claude/skills/mcp-integration/SKILL.md` -- skill only exists in template, not in main project

---

### VERDICT: FAIL

**Reasons for failure:**

1. **Widespread stale references to deleted skills** -- The 4 deleted skill names (`executing-plans`, `session-resumption`, `project-knowledge`, `context-monitor`) appear extensively across CLAUDE.md, guides, work-templates, and template files. The directory deletion was completed, but the textual references were NOT cleaned up. This is the primary failure -- agents following these references will encounter missing files and broken workflows.

2. **Broken file paths in CLAUDE.md** -- 4 paths referenced in CLAUDE.md do not exist, including critical ones like the project architecture guides (`project-knowledge/guides/architecture.md` and `patterns.md`) and `mcp-integration/SKILL.md`.

3. **Template mcp-integration skill exceeds size limit** -- At 147 lines, it is nearly 3x the 50-line standard. This was noted as a known issue (mcp-integration was moved to template-only in a previous round but was not trimmed).

**Recommended fixes (priority order):**
1. Replace all `project-knowledge/guides/` paths with new locations (or create replacement guide files)
2. Remove `executing-plans` from role mapping tables and decision trees (replace with `subagent-driven-development` or pipeline system references)
3. Remove `session-resumption` and `context-monitor` from role mappings and guides
4. Fix `mcp-integration/SKILL.md` reference in CLAUDE.md (either remove or note it's template-only)
5. Trim template `mcp-integration/SKILL.md` to under 50 lines
