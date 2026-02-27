# Template Diff Report

Comparison: main `.claude/` vs template `.claude/shared/templates/new-project/.claude/`
Branch: `master`
Date: 2026-02-27

## Summary
- Files checked: 9
- In sync: 6
- Out of sync: 1
- Missing from template: 2

## Details

### Required comparisons (per acceptance criteria)

| File | Status | Notes |
|------|--------|-------|
| `.claude/scripts/memory-engine.py` | MATCH | Identical in both locations |
| `.claude/scripts/sync-from-github.sh` | MISSING | Exists in main only; not present in template |
| `.claude/ops/config.yaml` | MATCH | Identical in both locations |
| `.claude/agents/registry.md` | MATCH | Identical in both locations |

### Additional agent files compared

| File | Status | Notes |
|------|--------|-------|
| `.claude/agents/code-developer.md` | MATCH | Identical in both locations |
| `.claude/agents/code-reviewer.md` | DIFF | 2 line differences (lines 22, 177) — minor wording changes in `.claude/adr/decisions.md` references |
| `.claude/agents/orchestrator.md` | MATCH | Identical in both locations |
| `.claude/agents/secret-scanner.md` | MISSING | Exists in main only; not present in template |
| `.claude/agents/security-auditor.md` | MATCH | Identical in both locations |

## Diff Details

### `.claude/agents/code-reviewer.md` (lines 22, 177)

```diff
< Line 22 (main):    - **Project context**: Architecture decisions from `.claude/adr/decisions.md` describing project architecture, standards, and patterns
> Line 22 (template): - **Project context**: Architecture decisions from .claude/adr/decisions.md describing project standards and patterns

< Line 177 (main):   - Consider project context and constraints from `.claude/adr/decisions.md`
> Line 177 (template): - Consider project context and constraints from .claude/adr/
```

Main version has backtick-wrapped paths and includes "architecture" in description; template version has bare paths and truncated reference on line 177.
