# Project Knowledge

> Patterns + Gotchas combined. Single source of truth for project-specific knowledge.
> **IF YOU LEARNED SOMETHING THIS SESSION — ADD IT HERE.**
> Dedup before adding. One bullet per entry.
> **Observations:** Capture friction/surprises/gaps/insights in `.claude/memory/observations/`
> **Promotion:** Review pending observations → promote stable ones here
>
> **Decay System:** Each entry has a `verified:` date. Entries not verified in 90+ days → archive tier.
> Use `py -3 .claude/scripts/memory-engine.py knowledge .claude/memory/knowledge.md` to check tiers.
> When you USE a pattern during work → run `knowledge-touch` to refresh its verified date.

---

## Patterns

### Agent Teams Scale Well (2026-02-27, verified: 2026-02-27)
- When: 3+ independent tasks (different files/modules)
- Pattern: TeamCreate → parallel agents (5-10 per wave) → verify results
- 10 agents in parallel worked efficiently for analyze + port workflow
- Verified across 5+ sessions

### CLAUDE.md Rule Placement Matters (2026-02-16, verified: 2026-02-16)
- When: Adding enforcement rules to CLAUDE.md
- Pattern: Summary Instructions at TOP (highest attention zone, survives compaction)
- "Lost in the Middle" effect: mid-file rules have lowest recall
- Verified: agents consistently follow top-of-file rules

### Skill Descriptions > Skill Bodies (2026-02-17, verified: 2026-02-17)
- When: Making skills influence agent behavior
- Pattern: Frontmatter `description` in YAML is the ONLY part reliably read during autonomous work
- Bodies are optional quick-reference; critical procedures must be inlined in CLAUDE.md
- Verified: 4 parallel test agents confirmed

### Pipeline `<- CURRENT` Marker (2026-02-16, verified: 2026-02-16)
- When: Multi-phase tasks that may survive compaction
- Pattern: `<- CURRENT` on active phase line → agent greps and resumes
- File-based state machines survive compaction; in-memory state doesn't
- Verified: pipeline survived compaction and resumed correctly

### Test After Change (2026-02-17, verified: 2026-02-17)
- When: Testing typed memory write cycle
- Pattern: Agents should update knowledge.md after discovering reusable approaches
- Verified: 2026-02-18

### Fewer Rules = Higher Compliance (2026-02-22, verified: 2026-02-22)
- When: Designing agent instruction systems (CLAUDE.md, memory protocols)
- Pattern: Reduce mandatory steps to minimum viable set. 8→4 session start, 9→2+3 after task.
- "Two-Level Save": Level 1 MANDATORY (activeContext + daily log), Level 2 RECOMMENDED (knowledge.md + Graphiti)
- OpenClaw insight: they get high compliance through PROGRAMMATIC enforcement (automatic silent turns); we compensate with SIMPLICITY
- Verified: OpenClaw analysis of 18+ source files confirmed their approach

### Stale References Compound Across Template Mirrors (2026-02-22, verified: 2026-02-22)
- When: Restructuring file paths referenced in guides/prompts/templates
- Pattern: Every renamed file creates N×M stale refs (N=files referencing it × M=mirrors like new-project template)
- Always use parallel agents for stale ref fixes — one per file group — to avoid serial bottleneck
- Verify with targeted grep AFTER agents complete, not during
- Verified: 27 files fixed across 3 parallel agents in this session

### PreCompact Hook for Automatic Memory Save (2026-02-22, verified: 2026-02-22)
- When: Need to save session context before Claude Code compaction wipes the context window
- Pattern: Python script (`.claude/hooks/pre-compact-save.py`) triggered by `PreCompact` hook event
- Reads JSONL transcript → calls OpenRouter Haiku → saves to daily/ + activeContext.md
- Stdlib only (json, urllib.request, pathlib) — no pip install needed
- ALWAYS exit 0 — never block compaction
- API key in `.claude/hooks/.env` (gitignored), fallback to env var `OPENROUTER_API_KEY`
- `py -3` as Python command (Windows Python Launcher — reliable in Git Bash)
- Verified: real transcript extraction + API call + file write tested successfully
- Auto-curation added: daily dedup (<5 min), activeContext rotation (>150 lines), note limit (max 3)

### TaskCompleted Hook as Quality Gate (2026-02-23, verified: 2026-02-23)
- When: Any agent marks a task as completed (TaskUpdate status=completed)
- Pattern: Python script (`.claude/hooks/task-completed-gate.py`) triggered by `TaskCompleted` event
- Exit code 2 = BLOCKS completion, stderr fed back to agent as feedback
- Checks: Python syntax (py_compile) + merge conflict markers at line start
- Logs all completions to `work/task-completions.md` (PASSED/BLOCKED)
- Skips `.claude/hooks/` files to avoid self-detection of marker strings
- Fires in teammate/subagent contexts — works with Agent Teams
- Verified: blocked real task completion in production (caught syntax error + false positives → fixed)

### Ebbinghaus Decay Prevents Knowledge Junk Drawer (2026-02-27, verified: 2026-02-27)
- When: knowledge.md grows with patterns/gotchas that may become stale
- Pattern: Each entry has `verified: YYYY-MM-DD`. Tiers auto-calculated: active(14d), warm(30d), cold(90d), archive(90+d)
- Engine: `.claude/scripts/memory-engine.py knowledge .claude/memory/` shows tier analysis
- Refresh: `knowledge-touch "Name"` promotes one tier (graduated, not reset to top)
- Creative: `creative 5 .claude/memory/` surfaces random cold/archive for serendipity
- Config: `.claude/ops/config.yaml` memory: section with decay_rate, tier thresholds
- Verified: 22 entries analyzed, 21 active + 1 warm, all commands working

### Three Memory Layers Complement Each Other (2026-02-27, verified: 2026-02-27)
- When: Designing AI agent memory architecture
- Pattern: AutoMemory (organic notes) + Custom Hooks (compliance/compaction survival) + Decay (temporal awareness)
- AutoMemory alone doesn't solve: compaction survival, pipeline state, structured knowledge, quality gates
- Hooks alone don't solve: knowledge staleness, serendipity, cost-controlled search
- Decay alone doesn't solve: multi-agent context, automatic saves, compliance enforcement
- All three together = complete cognitive architecture: remember + retrieve + forget + surprise

### PostToolUseFailure Hook as Error Logger (2026-02-23, verified: 2026-02-23)
- When: Any tool call fails (Bash, Edit, Write, MCP, etc.)
- Pattern: Python script (`.claude/hooks/tool-failure-logger.py`) triggered by `PostToolUseFailure`
- Notification-only — cannot block, always exit 0
- Logs tool name, context, error to `work/errors.md` — "black box" for post-session debugging
- Skips user interrupts (is_interrupt=true)
- Matcher: tool name (can filter to specific tools, we use catch-all)

---

## Gotchas

### OpenRouter requires HTTP-Referer header (2026-02-19, verified: 2026-02-19)
- OpenRouter API returns 401 "User not found" if requests lack `HTTP-Referer` header
- Symptom: Graphiti search/add_memory fails with 401, but API key is valid on dashboard
- Root cause: graphiti_core's AsyncOpenAI client doesn't send custom headers
- Fix: patch factories.py to create AsyncOpenAI with `default_headers={"HTTP-Referer": "http://localhost:8000", "X-Title": "Graphiti MCP"}`
- File: `~/graphiti/mcp_server/src/services/factories.py` (mounted as Docker volume)
- After patching: restart container with `docker compose -f docker-compose-falkordb.yml restart graphiti-mcp`

### Docker Desktop on Windows (2026-02-18, verified: 2026-02-18)
- Docker Desktop on Windows may hang on "Starting Engine" — fix: `wsl --shutdown` + restart

### Windows PATH trap in Docker Compose (2026-02-19, verified: 2026-02-19)
- NEVER use `PATH=/root/.local/bin:${PATH}` in compose `environment:` — on Windows `${PATH}` injects Windows PATH, breaking all container binaries
- Health check: override with `curl -f http://localhost:8000/health`
- `restart: unless-stopped` on both services

### Git Clone of Large Repos (2026-02-22, verified: 2026-02-22)
- Git clone of 200MB+ repos can timeout/fail on Windows
- Workaround: use `gh api` to read files directly from GitHub (base64 decode)
- Faster and more reliable for analysis tasks

### Bash Hooks Unreliable on Windows (2026-02-13, updated 2026-02-22, verified: 2026-02-22)
- 5 bash-based hooks were removed (statusLine, UserPromptSubmit, SessionStart, pre-commit, post-commit)
- Reason: .cmd wrappers cause ENOENT with spawn, anti-deadlock bugs, shell incompatibilities
- **Exception**: PreCompact hook re-added as single Python script (2026-02-22) — Python works cross-platform
- Rule: keep hooks SIMPLE (one Python file, stdlib only, always exit 0)

### Hook Scripts Must Not Contain Their Own Detection Targets (2026-02-23, verified: 2026-02-23)
- Merge conflict checker script contained literal `<<<<<<<` strings as check targets
- The hook detected ITSELF as containing conflict markers — false positive that blocked real work
- Fix 1: Construct markers dynamically (`"<" * 7` instead of `"<<<<<<<"`)
- Fix 2: Skip `.claude/hooks/` directory from checks
- Fix 3: Only flag markers at LINE START (real conflicts always start at col 0)
- General rule: any self-referential check script must avoid containing its own patterns

### Claude Code Has 17 Hook Events (2026-02-23, verified: 2026-02-23)
- Was ~7 events in 2025, now 17 as of v2.1.50
- Key new events: TaskCompleted (gate), TeammateIdle (gate), PostToolUseFailure (notification)
- SubagentStart/Stop, WorktreeCreate/Remove, ConfigChange also available
- TaskCompleted exit 2 = blocks completion + feeds stderr to agent as feedback
- All hooks receive JSON on stdin with common fields (session_id, cwd, transcript_path, permission_mode, hook_event_name)

### Memory Compliance is ~30-40% (2026-02-22, verified: 2026-02-22)
- Despite 40 CLAUDE.md rules, agents skip memory writes ~60-70% of the time
- Root cause: too many rules, no programmatic enforcement, attention decay
- Mitigation: fewer rules, stronger wording, simpler file structure
- **UPDATE 2026-02-24:** Session-orient hook solves this — auto-injects context at session start (~100% compliance)

### Hook Enforcement > Instruction Enforcement (2026-02-24, verified: 2026-02-24)
- When: Designing agent quality systems
- Pattern: Hooks fire automatically regardless of agent attention state. Instructions require agents to remember.
- Arscontexta insight: "hooks are the agent habit system that replaces the missing basal ganglia"
- Our implementation: SessionStart hook auto-injects context, PostToolUse Write warns on schema issues
- Verified: 8/8 tests PASS after implementing arscontexta hook patterns

### Session-Orient Hook as Context Injection (2026-02-24, verified: 2026-02-24)
- When: Starting a new session — context must be loaded
- Pattern: Python hook on SessionStart event → reads activeContext.md, knowledge.md, PIPELINE.md → outputs to stdout (auto-injected)
- Windows gotcha: sys.stdout.reconfigure(encoding="utf-8") needed for Unicode content
- Pipeline detection: grep only `### Phase:` lines for `<- CURRENT` (avoid matching comments)
- Verified: produces all 5 sections with real project data

### Warn-Don't-Block Validation (2026-02-24, verified: 2026-02-24)
- When: Validating written files in real-time
- Pattern: PostToolUse Write hook checks schema but only WARNS (stdout), never BLOCKS (exit 0)
- Arscontexta insight: "speed > perfection at capture time — agent fixes while context fresh"
- Checks: YAML frontmatter, description field, empty files, merge conflicts
- Dynamic conflict markers (`"<" * 7`) to avoid self-detection
- Verified: warns on invalid files, silent on valid ones

### Structured Handoff Protocol (2026-02-24, verified: 2026-02-24)
- When: Pipeline phases transition, agents complete tasks
- Pattern: `=== PHASE HANDOFF ===` block with Status/Files/Tests/Decisions/Learnings/NextInput
- Reduces information loss between phases, enables automatic learning extraction
- Verified: handoff-protocol agent used its own format in completion message (self-referential proof)

### memory-engine.py CLI Accepts Both File and Directory (2026-02-27, verified: 2026-02-27)
- When: Running memory-engine.py commands like `knowledge`
- Gotcha: Agent passed `.claude/memory/knowledge.md` (file) but command expected directory → "not a directory" error
- Fix: Added `is_file()` check in main() — if target is file, use parent as dir and set knowledge_path from filename
- Pattern: CLI tools should accept both file paths and directory paths for usability
