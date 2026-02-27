# Template-to-Project Skills Sync Report

**Date:** 2026-02-27
**Branch:** session/template-1
**Compared:** `.claude/skills/` (project, working tree) vs `.claude/shared/templates/new-project/.claude/skills/` (template, master branch)

---

## 1. Comparison Table

### Skills Present in Both Project and Template

| Skill Name | Project Lines | Template Lines | Status |
|---|---|---|---|
| error-recovery | 425 | 43 | MISMATCH |
| finishing-a-development-branch | 201 | 44 | MISMATCH |
| self-completion | 338 | 35 | MISMATCH |
| subagent-driven-development | 1424 | 83 | MISMATCH |
| systematic-debugging | 296 | 50 | MISMATCH |
| using-git-worktrees | 448 | 54 | MISMATCH |
| verification-before-completion | 140 | 46 | MISMATCH |

**All 7 overlapping skills are MISMATCHED.** Template versions are significantly smaller stubs (5-17x fewer lines) compared to the full project versions.

### Skills Only in Project (27 skills, not in template)

| Skill Name | Project Lines |
|---|---|
| api-design-principles | 511 |
| architecture-patterns | 319 |
| async-python-patterns | 348 |
| code-reviewer | 239 |
| condition-based-waiting | 121 |
| context-monitor | 293 |
| defense-in-depth | 128 |
| dispatching-parallel-agents | 181 |
| executing-plans | 77 |
| python-packaging | 455 |
| python-performance-optimization | 423 |
| python-testing-patterns | 507 |
| receiving-code-review | 210 |
| requesting-code-review | 106 |
| root-cause-tracing | 175 |
| secret-scanner | 290 |
| security-checklist | 404 |
| session-resumption | 521 |
| sharing-skills | 195 |
| telegram-bot-architecture | 511 |
| test-driven-development | 365 |
| test-generator | 359 |
| testing-anti-patterns | 303 |
| testing-skills-with-subagents | 388 |
| using-superpowers | 75 |
| uv-package-manager | 398 |
| writing-skills | 623 |

### Skills Only in Template (7 skills, not in project)

| Skill Name | Template Lines |
|---|---|
| ao-fleet-spawn | 104 |
| ao-hybrid-spawn | 186 |
| codebase-mapping | 42 |
| expert-panel | 54 |
| mcp-integration | 147 |
| qa-validation-loop | 98 |
| task-decomposition | 83 |

---

## 2. Discrepancies Found

### Critical Findings

1. **No skills are in sync.** All 7 skills that exist in both locations have completely different content. The template versions are minimal stubs (35-83 lines) while project versions are full implementations (140-1424 lines).

2. **27 project skills are missing from the template.** The project has 34 skills total; only 7 have a corresponding template entry. This means 27 skills developed in the project have never been synced to the template.

3. **7 template skills are missing from the project.** The template contains skills (`ao-fleet-spawn`, `ao-hybrid-spawn`, `codebase-mapping`, `expert-panel`, `mcp-integration`, `qa-validation-loop`, `task-decomposition`) that do not exist in the project's `.claude/skills/` directory. These may be newer additions to the template that haven't been pulled into the project.

4. **Content divergence is extreme.** For overlapping skills, the project versions are 5x to 17x larger than the template versions. The template stubs appear to be placeholders or early drafts, while the project has the fully developed skills.

### Summary Statistics

| Metric | Count |
|---|---|
| Total project skills | 34 |
| Total template skills | 14 |
| Skills in both | 7 |
| Skills only in project | 27 |
| Skills only in template | 7 |
| Skills in sync (matching) | 0 |
| Skills mismatched | 7 |

---

## 3. Overall Sync Status

## **FAIL**

The project skills and template skills are **not in sync**. Zero out of 7 overlapping skills match, 27 project skills are absent from the template, and 7 template skills are absent from the project. The template needs a complete refresh from the project's current skill implementations.
