# Health Check

Validate `.claude/` directory structure, check for missing files, invalid configs, and offer auto-repair.

## Usage
```
/health         # Run full health check
```

To auto-repair, say "repair" or "fix" after reviewing the report.

## Process

1. Run all health checks below
2. Report findings with OK/WARN/FAIL status
3. If user says "repair": auto-create missing files from templates

## Checks

### Structure Checks
- [ ] `.claude/agents/registry.md` exists
- [ ] `.claude/memory/activeContext.md` exists
- [ ] `.claude/memory/knowledge.md` exists
- [ ] `.claude/ops/config.yaml` exists
- [ ] `.claude/adr/decisions.md` exists
- [ ] `work/` directory exists

### Skill Checks
- [ ] All skills in `.claude/skills/*/SKILL.md` have valid frontmatter (name, description, roles)
- [ ] No skill exceeds 500 lines (flag for review)
- [ ] All skills referenced in CLAUDE.md trigger table exist

### Config Checks
- [ ] `.claude/ops/config.yaml` is valid YAML
- [ ] Memory config `.claude/memory/.memory-config.json` is valid JSON (if exists)

### Pipeline Checks (if work/PIPELINE.md exists)
- [ ] Has `<- CURRENT` marker
- [ ] All phases have required fields (Status, Mode, Gate)
- [ ] No orphaned phases (unreachable via transitions)

### Memory Checks
- [ ] activeContext.md < 150 lines (warn if exceeding)
- [ ] knowledge.md entries have `verified:` dates
- [ ] No daily logs older than 30 days without archival

## Report Format

```
=== Health Check Report ===

Structure:  [OK/WARN/FAIL] (N/M checks passed)
Skills:     [OK/WARN/FAIL] (N skills checked)
Config:     [OK/WARN/FAIL] (N configs valid)
Pipeline:   [OK/WARN/FAIL/N/A] (pipeline status)
Memory:     [OK/WARN/FAIL] (memory health)

Issues Found:
- [FAIL] .claude/adr/decisions.md missing
- [WARN] activeContext.md is 180 lines (limit: 150)
- [WARN] 3 knowledge.md entries not verified in 30+ days

Auto-repairable: 2
Say "repair" to fix automatically.
```

## Auto-Repair Actions

| Issue | Repair Action |
|-------|--------------|
| Missing directory | Create with `mkdir -p` |
| Missing activeContext.md | Create from template |
| Missing decisions.md | Create empty with header |
| Missing config.yaml | Create with defaults |
| activeContext.md too long | Archive old content |
| knowledge.md stale entries | Run `memory-engine.py decay` |
