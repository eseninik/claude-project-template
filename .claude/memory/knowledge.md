# Project Knowledge

> Patterns + Gotchas combined. Single source of truth for project-specific knowledge.
> **IF YOU LEARNED SOMETHING THIS SESSION — ADD IT HERE.**
> Dedup before adding. One bullet per entry.

---

## Patterns

### Agent Teams Scale Well (2026-02-09)
- When: 3+ independent tasks (different files/modules)
- Pattern: TeamCreate → parallel agents (5-10 per wave) → verify results
- 10 agents in parallel worked efficiently for analyze + port workflow
- Verified across 5+ sessions

### CLAUDE.md Rule Placement Matters (2026-02-16)
- When: Adding enforcement rules to CLAUDE.md
- Pattern: Summary Instructions at TOP (highest attention zone, survives compaction)
- "Lost in the Middle" effect: mid-file rules have lowest recall
- Verified: agents consistently follow top-of-file rules

### Skill Descriptions > Skill Bodies (2026-02-17)
- When: Making skills influence agent behavior
- Pattern: Frontmatter `description` in YAML is the ONLY part reliably read during autonomous work
- Bodies are optional quick-reference; critical procedures must be inlined in CLAUDE.md
- Verified: 4 parallel test agents confirmed

### Pipeline `<- CURRENT` Marker (2026-02-16)
- When: Multi-phase tasks that may survive compaction
- Pattern: `<- CURRENT` on active phase line → agent greps and resumes
- File-based state machines survive compaction; in-memory state doesn't
- Verified: pipeline survived compaction and resumed correctly

### Test After Change (2026-02-17)
- When: Testing typed memory write cycle
- Pattern: Agents should update knowledge.md after discovering reusable approaches
- Verified: 2026-02-18

### Fewer Rules = Higher Compliance (2026-02-22)
- When: Designing agent instruction systems (CLAUDE.md, memory protocols)
- Pattern: Reduce mandatory steps to minimum viable set. 8→4 session start, 9→2+3 after task.
- "Two-Level Save": Level 1 MANDATORY (activeContext + daily log), Level 2 RECOMMENDED (knowledge.md + Graphiti)
- OpenClaw insight: they get high compliance through PROGRAMMATIC enforcement (automatic silent turns); we compensate with SIMPLICITY
- Verified: OpenClaw analysis of 18+ source files confirmed their approach

### Stale References Compound Across Template Mirrors (2026-02-22)
- When: Restructuring file paths referenced in guides/prompts/templates
- Pattern: Every renamed file creates N×M stale refs (N=files referencing it × M=mirrors like new-project template)
- Always use parallel agents for stale ref fixes — one per file group — to avoid serial bottleneck
- Verify with targeted grep AFTER agents complete, not during
- Verified: 27 files fixed across 3 parallel agents in this session

### PreCompact Hook for Automatic Memory Save (2026-02-22)
- When: Need to save session context before Claude Code compaction wipes the context window
- Pattern: Python script (`.claude/hooks/pre-compact-save.py`) triggered by `PreCompact` hook event
- Reads JSONL transcript → calls OpenRouter Haiku → saves to daily/ + activeContext.md
- Stdlib only (json, urllib.request, pathlib) — no pip install needed
- ALWAYS exit 0 — never block compaction
- API key in `.claude/hooks/.env` (gitignored), fallback to env var `OPENROUTER_API_KEY`
- `py -3` as Python command (Windows Python Launcher — reliable in Git Bash)
- Verified: real transcript extraction + API call + file write tested successfully

---

## Gotchas

### OpenRouter requires HTTP-Referer header (2026-02-19)
- OpenRouter API returns 401 "User not found" if requests lack `HTTP-Referer` header
- Symptom: Graphiti search/add_memory fails with 401, but API key is valid on dashboard
- Root cause: graphiti_core's AsyncOpenAI client doesn't send custom headers
- Fix: patch factories.py to create AsyncOpenAI with `default_headers={"HTTP-Referer": "http://localhost:8000", "X-Title": "Graphiti MCP"}`
- File: `~/graphiti/mcp_server/src/services/factories.py` (mounted as Docker volume)
- After patching: restart container with `docker compose -f docker-compose-falkordb.yml restart graphiti-mcp`

### Docker Desktop on Windows (2026-02-18)
- Docker Desktop on Windows may hang on "Starting Engine" — fix: `wsl --shutdown` + restart

### Windows PATH trap in Docker Compose (2026-02-19)
- NEVER use `PATH=/root/.local/bin:${PATH}` in compose `environment:` — on Windows `${PATH}` injects Windows PATH, breaking all container binaries
- Health check: override with `curl -f http://localhost:8000/health`
- `restart: unless-stopped` on both services

### Git Clone of Large Repos (2026-02-22)
- Git clone of 200MB+ repos can timeout/fail on Windows
- Workaround: use `gh api` to read files directly from GitHub (base64 decode)
- Faster and more reliable for analysis tasks

### Bash Hooks Unreliable on Windows (2026-02-13, updated 2026-02-22)
- 5 bash-based hooks were removed (statusLine, UserPromptSubmit, SessionStart, pre-commit, post-commit)
- Reason: .cmd wrappers cause ENOENT with spawn, anti-deadlock bugs, shell incompatibilities
- **Exception**: PreCompact hook re-added as single Python script (2026-02-22) — Python works cross-platform
- Rule: keep hooks SIMPLE (one Python file, stdlib only, always exit 0)

### Memory Compliance is ~30-40% (2026-02-22)
- Despite 40 CLAUDE.md rules, agents skip memory writes ~60-70% of the time
- Root cause: too many rules, no programmatic enforcement, attention decay
- Mitigation: fewer rules, stronger wording, simpler file structure
