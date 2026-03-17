# Claude Code Best Practice Analysis
**Date**: 2026-03-17
**Source**: /tmp/claude-code-best-practice/ — Comprehensive analysis of orchestration workflows, agent-teams examples, and reports
**Status**: Complete analysis of all 17 key documents

---

## EXECUTIVE SUMMARY

This analysis synthesizes Claude Code best practices across four domains:
1. **Orchestration Architecture** — Command → Agent → Skill pattern
2. **Multi-Agent Coordination** — Agent Teams for parallel execution
3. **Infrastructure & Degradation** — Why Claude behaves unpredictably
4. **Boris Cherny Tips** — Practical techniques from Claude Code team

**Key Finding**: The most effective Claude Code workflows combine **parallel execution** (Agent Teams + git worktrees), **structured memory** (CLAUDE.md + agent memory), and **autonomous verification** (tests + reviews).

---

## I. ORCHESTRATION WORKFLOW PATTERN

### 1.1 The Command → Agent → Skill Architecture

The foundational pattern for complex workflows:

```
User Command (/weather-orchestrator)
    ↓
Command Orchestrates (handles user interaction)
    ├─ Step 1: AskUser for input (Celsius/Fahrenheit)
    ├─ Step 2: Agent Tool → Invoke weather-agent (separate context, autonomous)
    │   └─ Agent has preloaded skill (weather-fetcher)
    │   └─ Agent fetches data and returns to command
    └─ Step 3: Skill Tool → Invoke weather-svg-creator (inline, receives context data)
        └─ Skill creates SVG output + markdown
```

**Three distinct roles:**

| Component | Location | Invocation | Context | Model |
|-----------|----------|-----------|---------|-------|
| **Command** | `.claude/commands/` | User (`/command`) | Entry point, orchestrator | haiku |
| **Agent** | `.claude/agents/` | Agent Tool | Separate, autonomous | sonnet |
| **Skill (preloaded)** | `.claude/skills/` | Preloaded into agent | Agent startup injection | N/A |
| **Skill (direct)** | `.claude/skills/` | Skill Tool | Same as command | varies |

### 1.2 Key Distinctions Between Agents and Skills

**Agent** (Autonomous Subcontext):
- Separate execution context from command
- Can have **preloaded skills** (injected at startup as domain knowledge)
- Auto-invocable via description (set in `CLAUDE.md` or agent definition)
- Has tools available: Read, Write, Edit, Bash, Grep, Glob, etc.
- Uses `maxTurns` to limit iterations
- Memory scope: `user`, `project`, or `local`
- Color-coded for visual identification

**Skill** (Reusable Knowledge Module):
- NOT a separate context
- Either **preloaded into an agent** OR **invoked via Skill tool**
- Cannot auto-invoke (only user or command can invoke)
- Descriptions always in context (up to character budget)
- Full content only loaded on invocation
- Supports `disable-model-invocation: true` to prevent Claude from calling it
- Optional `user-invocable: false` when agent-only domain knowledge

### 1.3 Frontmatter Differences

**Agent Frontmatter:**
```yaml
---
name: my-agent
description: Use this agent PROACTIVELY when...
tools: Read, Write, Edit, Bash
model: sonnet
maxTurns: 10
permissionMode: acceptEdits
memory: user  # or project, local
skills:
  - my-skill
---
```

**Command Frontmatter:**
```yaml
---
description: Do something useful
argument-hint: [issue-number]
allowed-tools: Read, Edit, Bash(gh *)
model: sonnet
---
```

**Skill Frontmatter:**
```yaml
---
name: my-skill
description: Do something when the user asks for...
argument-hint: [file-path]
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Grep, Glob
model: sonnet
context: fork
agent: general-purpose
---
```

### 1.4 Practical Flow: Weather System Example

1. **User triggers** `/weather-orchestrator`
2. **Command asks** "Celsius or Fahrenheit?"
3. **User responds** "Celsius"
4. **Command invokes Agent** via `Agent(agent: "weather-agent")`
   - Agent loads with `weather-fetcher` skill already injected
   - Agent runs: `TZ='UTC+2' date '+%H:%M'` (via bash in skill)
   - Agent returns: `{temp: 26, unit: "Celsius"}`
5. **Command invokes Skill** via `Skill(skill: "weather-svg-creator")`
   - Skill receives context: `{temp: 26, unit: "Celsius"}`
   - Skill creates SVG card + markdown summary
6. **Result**: weather.svg + output.md written to project

---

## II. MULTI-AGENT COORDINATION (Agent Teams)

### 2.1 When to Use Agent Teams

**TRIGGER**: 3+ independent parallel subtasks

**Example**: Build time orchestration workflow
- Task 1: Command Architect — design `/time-orchestrator` command
- Task 2: Agent Engineer — build `time-agent` + `time-fetcher` skill
- Task 3: Skill Designer — build `time-svg-creator` + templates

**Key**: These can run in parallel because they only need to agree on the **data contract** (interface), not wait on implementation.

### 2.2 Data Contract Pattern

```
Agent returns: {time, timezone, formatted}
Command passes: via context to skill
Skill consumes: receives data, generates output
```

This pattern ensures:
- Independent work streams
- Clear interface boundaries
- No hidden dependencies
- Easy parallel testing

### 2.3 Agent Teams Best Practices (from Boris Cherny)

**Run 5 Claudes in Parallel:**
- 3–5 git worktrees, each with own Claude session
- Name them: `2a`, `2b`, `2c` (shell aliases)
- Use tmux/terminal tabs for easy switching
- Dedicated "analysis" worktree for logs/queries

**Output Coordination:**
- Shared task list tracks dependencies
- Results Board (`.claude/guides/results-board.md`) — append-only log
- Phase handoff blocks between teams

---

## III. MEMORY ARCHITECTURE

### 3.1 Three Memory Scopes (Newest Pattern)

| Scope | Location | Version Control | Shared | Use Case |
|-------|----------|-----------------|--------|----------|
| **user** | `~/.claude/agent-memory/<agent-name>/` | No | No | Cross-project agent knowledge |
| **project** | `.claude/agent-memory/<agent-name>/` | Yes | Yes | Team-shared agent knowledge |
| **local** | `.claude/agent-memory-local/<agent-name>/` | No (git-ignored) | No | Personal project knowledge |

### 3.2 Agent Memory Structure

```
~/.claude/agent-memory/code-reviewer/
├── MEMORY.md                # Primary (first 200 lines auto-injected)
├── react-patterns.md        # Topic-specific files
├── security-checklist.md
└── archived-sessions/
```

**On startup**: First 200 lines of `MEMORY.md` injected into agent's system prompt
**During work**: Agent reads/writes freely via Read/Write/Edit tools
**Curation**: Move overflow details into topic-specific files

### 3.3 Four Complementary Memory Systems

| System | Who Writes | Who Reads | Scope | Best For |
|--------|-----------|-----------|-------|----------|
| **CLAUDE.md** | You (manual) | Main + all agents | Project | Team rules, no-gos, patterns |
| **Auto-memory** | Main Claude | Main Claude only | Per-project per-user | Session learnings |
| **Agent Memory** | Agent itself | That agent only | Configurable | Agent-specific knowledge |
| **Graphiti** (MCP) | Any agent | Via query | Semantic | Cross-session insights |

### 3.4 Memory Decay System (Ebbinghaus)

Knowledge in `CLAUDE.md` has relevance tiers based on freshness:

```yaml
Tier      Days Since Verified    Usage Pattern
---       ---                    ---
active    0-14                   Always shown
warm      15-30                  Shown + refresh check
cold      31-90                  Deep search only
archive   90+                    Random serendipity
```

**Refresh with**: `py -3 .claude/scripts/memory-engine.py knowledge-touch "Pattern Name"`

**Search modes:**
- **heartbeat** (~2K tokens) — active only, quick check
- **normal** (~5K tokens) — active + warm, default
- **deep** (~15K tokens) — all tiers + Graphiti
- **creative** (~3K tokens) — random cold/archive for brainstorm

---

## IV. ADVANCED TOOL USE

### 4.1 The `allowed_callers` Field

Control WHERE a tool can be invoked from:

```json
{
  "name": "query_database",
  "allowed_callers": ["code_execution_20250825"]
  // Only callable from Python sandbox
  // Other options: ["direct"] or ["direct", "code_execution_20250825"]
}
```

**Pattern**: Use **one mode per tool**, not both. Gives Claude clearer guidance.

### 4.2 Advanced Tool Patterns

**Batch Processing** — Process N items in single inference:
```python
regions = ["West", "East", "Central", "North", "South"]
results = {}
for region in regions:
    data = await query_database(f"SELECT SUM(revenue) FROM sales WHERE region='{region}'")
    results[region] = data[0]["revenue"]
```

**Early Termination** — Stop at first success:
```python
endpoints = ["us-east", "eu-west", "apac"]
for endpoint in endpoints:
    status = await check_health(endpoint)
    if status == "healthy":
        break
```

**Conditional Tool Selection** — Choose tool based on data:
```python
file_info = await get_file_info(path)
if file_info["size"] < 10000:
    content = await read_full_file(path)
else:
    content = await read_file_summary(path)
```

### 4.3 Caller Field in Responses

Every tool use includes `caller` field:
```json
// Direct invocation
{ "caller": { "type": "direct" } }

// From code execution sandbox
{ "caller": { "type": "code_execution_20250825", "tool_id": "srvtoolu_abc123" } }
```

---

## V. INFRASTRUCTURE & DEGRADATION (Critical Findings)

### 5.1 The September 2025 Postmortem (Real Causes)

**Myth**: Claude degrades due to demand/load
**Reality**: Three separate infrastructure bugs proven real

**Bug #1 — Context Window Routing Error**
- Sonnet 4 requests routed to 1M-token servers instead of standard
- Timeline: Aug 5–Sept 18
- Impact: 16% of Sonnet 4 requests at worst, 30% of Claude Code users
- Insidious: "Sticky" routing — once on bad server, stayed there

**Bug #2 — TPU Output Corruption**
- Misconfiguration caused random high-probability tokens (Thai/Chinese mid-English)
- Affected: Opus 4.1, Opus 4, Sonnet 4
- Timeframe: Aug 25–Sept 2
- Symptom: Obvious code syntax errors, nonsense mid-response

**Bug #3 — XLA:TPU Compiler Miscompilation (Nastiest)**
- Root: Approximate top-k operation returned wrong results for certain batch sizes
- Why hidden: Changed behavior based on surrounding ops, only visible without debug tools
- Hidden for months: Previous workaround masking deeper compiler bug
- Solution: Switched from approximate to exact top-k (accepted minor efficiency loss)

### 5.2 MoE Routing Variance (Day-to-Day Noise)

Modern models use **Mixture-of-Experts**, where only a subset activates per input.

**Day-to-Day Variance** (even with zero bugs, zero changes):

| Provider | Range |
|----------|-------|
| OpenAI (GPT-4) | ±10–12% |
| Anthropic (Claude) | ±8–11% |
| Google (Gemini) | ±9–14% |

Concrete example: Same model scored **77% one day, 63% the next** on jailbreak resistance = 14pp swing from routing alone.

**Why it matters**: A/B tests cannot detect 5% signal when noise is 10–15%.

### 5.3 Why Detection Was Hard

- **Three hardware platforms** (AWS Trainium, NVIDIA GPUs, Google TPUs) each with different failure modes
- **Batch composition** determines which experts route — not deterministic across requests
- **Automated evals didn't catch it** — Claude "often recovers well from isolated mistakes"
- **Mixed symptom types** created confusion, didn't point to single cause

---

## VI. BORIS CHERNY'S PRACTICAL TIPS

### 6.1 Do More in Parallel (Biggest Unlock)

**Parallel Execution**:
- Spin up 3–5 git worktrees at once, each with own Claude session
- Name worktrees with aliases: `2a`, `2b`, `2c`
- Hop between them in one keystroke
- Dedicated "analysis" worktree for logs/BigQuery

**Why it works**: Most productive unlock from Claude Code team

### 6.2 Start Complex Tasks in Plan Mode

**Process**:
1. One Claude writes the plan
2. Second Claude reviews as staff engineer
3. Fix gray areas → re-plan
4. Switch to implementation → 1-shot completion

**Key insight**: "Pour energy into the plan so Claude can 1-shot implementation"

### 6.3 Invest in CLAUDE.md (Compounding)

**After every correction**:
```
"Update your CLAUDE.md so you don't make that mistake again."
```

**Tips from team**:
- Ruthlessly edit over time until mistake rate drops
- Point CLAUDE.md at task-specific notes directory
- Share single CLAUDE.md with team
- Tag @claude on PRs to update it via GitHub action

### 6.4 Create Your Own Skills (Reuse)

**If you do something > 1x/day, turn it into a skill**

Examples:
- `/techdebt` — find + kill duplicated code (run at end of session)
- Sync Slack + GDrive + Asana + GitHub into one context dump
- dbt model writer + reviewer + test runner
- Analytics queries (haven't written SQL in 6 months)

**Pattern**: Check into `.claude/skills/` and reuse across all projects

### 6.5 Claude Fixes Most Bugs by Itself

**Techniques**:
- Enable Slack MCP, paste bug thread: "fix."
- Say "Go fix failing CI tests" (no micromanaging)
- Point Claude at docker logs for distributed system troubleshooting

**Key**: Provide feedback loop so Claude can verify

### 6.6 Level Up Prompting

a. **Challenge Claude**: "Grill me on these changes, don't PR until I pass"
b. **After mediocre fix**: "Knowing everything now, scrap this + implement elegant solution"
c. **Write detailed specs** to reduce ambiguity

### 6.7 Terminal & Environment Setup

**Tools**:
- **Ghostty** — synchronized rendering, 24-bit color, proper unicode
- **Status line** — show context usage + git branch + model
- **Color-coded tabs** — one tab per task/worktree
- **Voice dictation** — speak 3x faster, prompts get more detailed

### 6.8 Use Subagents to Throw Compute

**Pattern**: Append "use subagents" to requests where you want more compute

**Practical examples**:
- Separate context window for reviewer catches bugs
- Auto-approve safe permission requests (route to Opus via hook)
- Keep main agent context clean by offloading tasks

**Key insight**: Separate context windows = uncorrelated bugs → better detection

### 6.9 Use Claude for Analytics

**No SQL in 6 months** approach:
- BigQuery skill checked into codebase
- Ask Claude to `bq` CLI pull + analyze
- Works for any DB with CLI/MCP/API

### 6.10 Customize Everything (Check into Git)

| Customization | Command | Location |
|---------------|---------|----------|
| Terminal | `/terminal-setup` | themes, newlines, vim mode |
| Model effort | `/model` | Low/Medium/High tokens |
| Plugins | `/plugin` | LSPs, MCPs, skills |
| Custom agents | drop `.md` | `.claude/agents/` |
| Permissions | `/permissions` | allow/block lists (git-commit) |
| Sandboxing | `/sandbox` | open-source runtime |
| Status line | `/statusline` | context usage, branch, cost |
| Keybindings | `/keybindings` | remap any key |
| Output styles | `/config` | Explanatory/Learning/Custom |

### 6.11 Code Review & Test Time Compute (New, Feb-Mar 2026)

**Code Review** (NEW):
- Team of agents runs deep review on every PR
- Catches bugs developers would miss
- Auto-dispatch when PR opens

**Test Time Compute**:
- More tokens = better results
- Separate context windows = uncorrelated thinking
- Like engineering teams: one author → multiple reviewers

**In the limit**: Agents will write bug-free code with multiple uncorrelated windows

---

## VII. SETTINGS HIERARCHY (Priority Order)

| Priority | Location | Scope | Version Control |
|----------|----------|-------|-----------------|
| 1 | Command line flags | Session | N/A |
| 2 | `.claude/settings.local.json` | Project | No (git-ignored) |
| 3 | `.claude/settings.json` | Project | Yes |
| 4 | `~/.claude/settings.local.json` | User | N/A |
| 5 | `~/.claude/settings.json` | User | N/A |

**Policy**: `managed-settings.json` (org-enforced) cannot be overridden by lower-priority rules

---

## VIII. GLOBAL VS PROJECT SCOPE

### 8.1 Global Directory Structure (`~/.claude/`)

```
~/.claude/
├── settings.json                 # User settings (all projects)
├── settings.local.json           # Personal overrides
├── CLAUDE.md                     # User memory (all projects)
├── agents/                       # User subagents (all projects)
├── commands/                     # User commands (all projects)
├── skills/                       # User skills (all projects)
├── rules/                        # Modular user rules
├── tasks/                        # GLOBAL-ONLY
├── teams/                        # GLOBAL-ONLY (team configs)
├── projects/                     # GLOBAL-ONLY (per-project auto-memory)
├── keybindings.json              # GLOBAL-ONLY (shortcuts)
└── hooks/                        # User-level hooks
```

### 8.2 Project Directory Structure (`.claude/`)

```
.claude/
├── settings.json                 # Team-shared settings
├── settings.local.json           # Personal project overrides
├── CLAUDE.md                     # Project memory
├── agents/                       # Project subagents
├── commands/                     # Custom slash commands
├── skills/                       # Custom skills
├── rules/                        # Project-level modular rules
├── agent-memory/                 # Agent-specific memory
├── hooks/                        # Project hooks
└── plugins/                      # Installed plugins
```

---

## IX. SKILLS IN MONOREPOS

### 9.1 Skill Discovery Pattern

**Root-level skill**: Loaded immediately
```
.claude/skills/shared-conventions/SKILL.md  ← In context from start
```

**Nested skills**: Discovered on-demand when files edited
```
packages/frontend/.claude/skills/react-patterns/SKILL.md
# Loaded only when working in packages/frontend/
```

**Priority when names clash**:
1. Enterprise (org-wide)
2. Personal (`~/.claude/skills/`)
3. Project (`.claude/skills/`)

### 9.2 Description vs Full Content

**Descriptions** → Always in context (up to character budget)
**Full content** → Loaded on-demand when invoked

Optimization: Descriptions ~50 lines, supporting files in `references/` and `examples.md`

### 9.3 Best Practices for Monorepos

1. **Shared workflows** → root `.claude/skills/`
2. **Package-specific** → `packages/{name}/.claude/skills/`
3. **Dangerous skills** → `disable-model-invocation: true`
4. **Concise descriptions** — they're always in context
5. **Namespace names** — `frontend-review`, `backend-deploy`

---

## X. SYSTEM PROMPTS: CLI vs SDK

### 10.1 CLI Default System Prompt

```
[Tool instructions (Write, Read, Edit, Bash, Grep, Glob, etc.)]
[Git safety protocols]
[Code reference guidelines]
[Professional objectivity]
[Security + injection defense]
[Environment context (OS, dir, date)]
[CLAUDE.md content] ← Auto-loaded if present
[MCP tool descriptions] ← If configured
[Plan/Explore mode prompts]
[Session/conversation context]
```

### 10.2 Agent SDK Default (Minimal)

```
[Essential tool instructions only]
[Basic operational context]
```

### 10.3 Agent SDK with `claude_code` Preset

```typescript
const response = await query({
  prompt: "...",
  options: {
    systemPrompt: {
      type: "preset",
      preset: "claude_code"  // Matches CLI functionality
    }
  }
});
```

Result: Modular system prompt (matches CLI) BUT does NOT auto-load CLAUDE.md

### 10.4 Customization Methods

| Method | Effect | Preserves Tools |
|--------|--------|-----------------|
| `--system-prompt "..."` (CLI) | Replaces entirely | ✅ Yes |
| `--append-system-prompt "..."` (CLI) | Appends while preserving | ✅ Yes |
| SDK `systemPrompt: { preset: "claude_code", append: "..." }` | Preserves + appends | ✅ Yes |
| SDK custom `systemPrompt: "..."` | Replaces entirely | ❌ No (loses tools) |

---

## XI. CHROME TOOLS COMPARISON

### 11.1 Claude in Chrome (16 Tools)

✅ **Use when**:
- Manual testing while logged in
- Exploratory testing with visual context
- Testing with auth state dependencies
- Recording workflows for replay

Strengths: Full visual interaction, account access, natural user flow

### 11.2 Chrome DevTools MCP (17 Tools)

✅ **Use when**:
- Performance testing (Core Web Vitals, traces)
- Deep debugging (network, console, DOM)
- Headless CI/CD automation
- Stable script-based testing

Strengths: Headless support, performance profiling, CI/CD integration

**Tool Coverage**:
- DevTools: 17 tools (performance, network, debugging)
- Claude in Chrome: 16 tools (browser control, form interaction)
- Playwright: 21 tools (modern, assertion-heavy)

---

## XII. USAGE & RATE LIMITS

### 12.1 `/extra-usage` Command (Pay-as-You-Go)

When you hit plan rate limits, overflow billing continues work:

| Aspect | Detail |
|--------|--------|
| Daily limit | $2,000/day |
| Billing | Standard API rates (separate from subscription) |
| Limit reset | Every 5 hours |
| Setup | `/extra-usage` CLI or Settings > Usage on claude.ai |

### 12.2 Fast Mode (`/fast`)

- Uses Opus 4.6 with faster output
- **Always billed to extra usage** from first token
- Does NOT consume subscription plan limits

### 12.3 `/cost` Command

For API key users (not subscription):
- Session spending breakdown
- Token usage
- Code changes count

---

## SYNTHESIS & PATTERNS FOR OUR SYSTEM

### Key Takeaways to Integrate

1. **Command → Agent → Skill** is the canonical pattern for orchestration
2. **Agent Teams** (3+ parallel tasks) beat sequential execution
3. **Shared CLAUDE.md** (checked into git, updated after corrections) compounds over time
4. **Memory scopes** (user/project/local) provide layered persistence
5. **Parallel execution** (worktrees + multiple Claudes) is #1 productivity unlock
6. **Test time compute** (multiple context windows, subagents) catches bugs
7. **Infrastructure variance** (±8–14%) is real; plan for it
8. **Skill descriptions** are always loaded; full content on-demand
9. **Customization matters** — check settings.json into git for team consistency
10. **Monorepos** benefit from root-level shared skills + nested package-specific skills

### Recommended Integration Points

1. **Skill structure** — adopt reference.md + examples.md pattern
2. **Memory decay** — implement Ebbinghaus tiers in knowledge.md
3. **Agent Teams mode** — add to PIPELINE.md phases
4. **Test time compute** — value of code review + verification agents
5. **Parallel worktrees** — document in onboarding

---

## REFERENCES

- Orchestration: `/tmp/claude-code-best-practice/orchestration-workflow/`
- Agent Teams: `/tmp/claude-code-best-practice/agent-teams/`
- Reports: `/tmp/claude-code-best-practice/reports/`
- Tips: `/tmp/claude-code-best-practice/tips/`
- Source: Boris Cherny ([@bcherny](https://x.com/bcherny)) — Feb 1, Feb 12, Jan 3, Mar 10 2026
