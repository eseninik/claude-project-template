# Bot Upgrade Synthesis — Research Phase Complete

## Upgrade Matrix

| Bot | Skills | Hooks | Guides | Memory | Registry | Prompts | Ops | CLAUDE.md | Action Level |
|-----|--------|-------|--------|--------|----------|---------|-----|-----------|-------------|
| Legal Bot | 11 ✓ (no Phil) | 3/5 | 24/25 | Good | ✓ | 5 ✓ | ✗ | Generic header | TARGETED |
| DocCheck Bot | 12 ✓ (no Phil) | 0/5 | 24/25 | Good | ✓ | 5 ✓ | ✗ | 345 lines ✓ | MIGRATION |
| QualityControl | 11 ✓ (no Phil) | 0/5 (3 bash) | 25 ✓ | Good | ✓ | 5 ✓ | ✗ | 490 lines ✓ | MIGRATION |
| Call Rate Bot | 45 old | 3 bash/unreg | 13 partial | Minimal | ✗ | ✗ | ✗ | Project-spec | FULL |
| Conference Bot | 46 old | 0 | 16 partial | Minimal | ✗ | ✗ | ✗ | Generic header | FULL |
| LeadQualifier | 46 old | 1 bash/unreg | 11 partial | MISSING | ✗ | ✗ | ✗ | Project-spec | FULL |
| Sales Check | 44 old | 1 bash/unreg | 12 partial | Minimal | ✗ | ✗ | ✗ | Project-spec | FULL |

## Universal Gaps (ALL 7 bots need)
1. Skills: Add Philosophy + Critical Constraints sections
2. observations/ directory: Create .claude/memory/observations/.gitkeep
3. ops/config.yaml: Copy from template
4. observation-capture.md: Copy guide from template

## Per-Category Actions

### TARGETED (Legal Bot)
- Copy: session-orient.py, write-validate.py
- Register: SessionStart + PostToolUse hooks in settings.json (preserve mcpServers)
- Copy: ops/config.yaml, observation-capture.md
- Create: observations/ dir
- Replace: 11 skill SKILL.md files with Philosophy versions

### MIGRATION (DocCheck + QualityControl)
- Copy: ALL 5 hooks
- Create: settings.json with ALL 5 hook registrations (preserve settings.local.json)
- Copy: ops/config.yaml, observation-capture.md
- Create: observations/ + daily/ dirs
- Replace: skill SKILL.md files with Philosophy versions
- Copy: autonomous-pipeline.md + teammate-prompt-template.md updates
- Copy: phase templates with handoff protocol

### FULL (CallRate, Conference, LeadQualifier, SalesCheck)
- DELETE: old skills (44-46 directories)
- COPY: 11 new skills + SKILLS_INDEX.md from template
- COPY: ALL 5 hooks
- CREATE: settings.json with hooks (preserve settings.local.json)
- COPY: ALL guides (~27 files) from template
- COPY: agents/registry.md from template
- COPY: prompts/ (5 files) from template
- COPY: ops/config.yaml
- CREATE: full memory structure (activeContext.md, knowledge.md, daily/, observations/, archive/)
- COPY: shared/work-templates/ (PIPELINE-v3, phases/)
- UPDATE: CLAUDE.md (new template format, PRESERVE project-specific sections)
- COPY: adr/ template if missing

## Key Preservation Rules
- NEVER overwrite: settings.local.json, existing activeContext.md, existing knowledge.md, existing ADR decisions
- ALWAYS preserve: CLAUDE.md project header (name, description, branch), MCP server configs
- MERGE settings.json: add hooks alongside existing content (Legal Bot has mcpServers)
