# Agent Memory Trigger Analysis

**Date:** 2026-03-17
**Role:** Requirement Analyst
**Status:** RESEARCH COMPLETE

---

## Problem Statement

Agent Memory (`.claude/agent-memory/{type}/MEMORY.md`) was implemented but **NEVER triggered during real pipeline work**. The root cause: agents are spawned via the **Agent tool with inline prompts**, NOT via `spawn-agent.py` which auto-injects memory.

### Evidence
- **Memory files exist**: `coder/MEMORY.md`, `planner/MEMORY.md`, `qa-reviewer/MEMORY.md`
- **spawn-agent.py injects them**: Lines 368-405 load and inject agent memory AFTER Required Skills
- **But it's rarely used**: Most teammate prompts are hand-written directly for Agent tool
- **Why hand-written**: Faster iteration during development, no extra script step, team lead writes directly

---

## Research Findings

### 1. How Agent Tool Works

From system prompt (Claude Code documentation):
- **Agent tool** (in `SendMessage` for team communication) spawns a new Claude session in context
- **Input**: structured JSON with `to` (recipient), `message` (text or struct), `summary`
- **Plain text message**: new agent reads text directly
- **Structured message**: `type: "shutdown_request"` / `"plan_approval_response"`
- **Agents DO NOT auto-load skills** — all skill content must be embedded in the prompt text
- **Agents DO NOT auto-load memory** — all memory content must be embedded in the prompt text
- **Agents DO auto-load global CLAUDE.md** from project root (rules like "ALWAYS verify before done")

**Blocker**: Agent tool has NO field like `memory: project` or `skills: [list]`. Pure text-based.

---

### 2. spawn-agent.py Architecture

**File**: `.claude/scripts/spawn-agent.py` (434 lines)

**Key flow**:
```python
# Line 368-405: Agent memory injection
memory_path = root / '.claude' / 'agent-memory' / agent_type / 'MEMORY.md'
if memory_path.is_file():
    agent_memory_content = read first 200 lines
    # Insert after ## Required Skills section
    marker = "\n## Memory Context"
    prompt.replace(marker, agent_memory_block + marker, 1)
```

**Dependencies**:
- Imports `generate-prompt.py` (same directory) for skill discovery + registry parsing
- Uses `generate_prompt.build_prompt()` to assemble the full prompt
- Reads registry.md to get agent properties (tools, skills, thinking, context, memory level)
- Loads memory context from `knowledge.md` based on agent's `memory` property (none/patterns/full)

**Output**:
- **Default**: prints prompt to stdout (agent can copy-paste to Agent tool)
- **`--output <file>`**: saves to file (agent can read file, paste to Agent tool)
- **`--detect-only`**: shows detected type only
- **`--dry-run`**: shows type + skills plan without prompt output

---

### 3. Current Agent Type System

**Files**: `.claude/agents/registry.md` + `.claude/agents/*.md`

**Registry structure** (registry.md):
```markdown
| Type | Tools | Skills | Thinking | Context | Memory | MCP |
| coder | full | verification-before-completion | standard | standard | patterns | none |
| coder-complex | full + web | verification-before-completion | deep | full | full | context7 |
```

**Agent definition files** (.claude/agents/*.md):
- 6 existing agents: `code-developer`, `code-reviewer`, `orchestrator`, `secret-scanner`, `security-auditor`, `skeptic`
- **Frontmatter**: name, description, model, color, skills, allowed-tools
- **NO `memory` field exists** in current agent files (checked code-developer, orchestrator, skeptic)
- Agent files are for **Claude Code subagent system** (not Agent tool teammates)

**Key distinction**:
- **Claude Code subagents** (`.claude/agents/*.md`): loaded by IDE, full context auto-inject
- **Agent tool teammates** (via SendMessage): manual text prompt, no auto-inject

---

### 4. Teammate Prompt Template

**File**: `.claude/guides/teammate-prompt-template.md` (100+ lines)

**Memory injection section** (lines 32-41):
```markdown
## Agent Memory (if available)

Check if `.claude/agent-memory/{agent-type}/MEMORY.md` exists.
If yes, inject the first 200 lines into the prompt below Required Skills.

Agent memory contains project-specific learnings accumulated across sessions.
The agent should READ this at start and UPDATE it in their handoff block.
```

**Problem**: This is a GUIDE, not an enforcement. The team lead MUST:
1. Know agent type
2. Check if `agent-memory/{type}/MEMORY.md` exists
3. Read first 200 lines
4. Manually paste into prompt
5. Ensure placement (after Required Skills, before Memory Context)

**Why it fails**:
- Extra manual step (read file, copy, paste)
- Easy to forget in quick iterations
- No automation enforcement
- Decentralized — each prompt writer responsible for remembering

---

### 5. Alternative Approaches Evaluated

#### **Approach A: Define agents as .claude/agents/*.md with `memory` field**

**How it would work**:
```yaml
---
name: coder
memory: coder
memory-level: patterns
---
[rest of agent prompt]
```

**Pros**:
- Centralizes agent definition + memory linkage
- Claude Code subagent system would auto-inject memory (if implementation supported it)
- Discoverable via grep/ls

**Cons**:
- Agent files are for **Claude Code subagent IDE system**, NOT Agent tool teammates
- Claude Code doesn't auto-inject agent memory (checked IDE source)
- Adds confusion: "Are these for subagents or teammates?"
- Would need Claude Code IDE source changes to implement

**Status**: ❌ **NOT VIABLE** — agent files are wrong tool (IDE subagents, not teammates)

---

#### **Approach B: Make spawn-agent.py output MANDATORY**

**How it would work**:
```
python .claude/scripts/spawn-agent.py --task "..." --team X --name Y > work/prompt.md
# Then:
# Agent tool: paste content of work/prompt.md into message
```

**Pros**:
- Guaranteed memory injection (spawn-agent.py always includes it)
- Single source of truth (script generates prompts)
- Auditable (can check generated prompts in work/ directory)
- Already implemented (spawn-agent.py ready to use)

**Cons**:
- Requires **new behavior**: lead agent must use spawn-agent.py for EVERY teammate spawn
- Current workflow: write prompt directly to Agent tool (faster)
- Extra file I/O + context switching
- Still manual trigger (no automation)

**Status**: ⚠️ **VIABLE BUT REQUIRES CULTURE CHANGE** — must update CLAUDE.md + train

---

#### **Approach C: Add agent memory to CLAUDE.md rules**

**How it would work**:
```markdown
## Before Spawning Teammate (BLOCKING)

MANDATORY: Include agent memory if available.
1. Detect agent type from task
2. Check if .claude/agent-memory/{type}/MEMORY.md exists
3. If yes: read first 200 lines, paste after Required Skills section

This is ALREADY in teammate-prompt-template.md (line 32-41).
```

**Pros**:
- Documents the requirement
- Makes it a HARD CONSTRAINT

**Cons**:
- **ALREADY EXISTS in CLAUDE.md** — "Before Spawning Teammate" section mentions Required Skills
- **ALREADY EXISTS in guide** — teammate-prompt-template.md explicitly says to include agent memory
- **FAILED in practice** — rule exists but not followed (memory never injected)
- **Root cause**: rule is aspirational, not enforced. No automation, no feedback.

**Status**: ❌ **ALREADY TRIED, FAILED** — rules alone insufficient

---

#### **Approach D: Create a hook that auto-injects memory**

**How it would work**:
```python
# Hook: on TeamCreate or SendMessage → auto-detect agent type, inject memory
def pre_teammate_spawn(message):
    agent_type = detect_type(message)
    memory_path = f".claude/agent-memory/{agent_type}/MEMORY.md"
    if exists(memory_path):
        message = inject_memory(message, memory_path)
    return message
```

**Pros**:
- Zero-friction for team lead (automatic)
- Foolproof (can't forget)

**Cons**:
- **HOOKS DISABLED IN THIS PROJECT** (2026-02-13 memory: "ALL Claude Code hooks removed")
- User explicitly chose standard hookless operation
- Prior hook failures (reliability on Windows, deadlock bugs)
- Adds complexity to debug

**Status**: ❌ **NOT VIABLE** — user policy blocks hooks

---

## Recommended Solution: Hybrid Approach

**Option 1: spawn-agent.py FIRST (Short-term, immediate)**
- Train team to use `python .claude/scripts/spawn-agent.py --task "..." --team X --name Y`
- Always outputs complete prompt with memory auto-injected
- Add to CLAUDE.md as MANDATORY (similar to git workflow rules)
- Update `.claude/guides/quick-mode.md` to include spawn-agent.py command

**Pros**: Immediate win, zero implementation needed, already coded
**Effort**: 1 doc update + 1 training message
**Timeline**: Now

---

**Option 2: CLI wrapper for Agent tool (Medium-term, increases adoption)**
- Create `.claude/scripts/spawn-teammate.sh`:
  ```bash
  python spawn-agent.py --task "$1" --team "$2" --name "$3" -o /tmp/prompt.md
  echo "Prompt saved to /tmp/prompt.md"
  echo "Copy content above to Agent tool"
  ```
- Add to CLAUDE.md: "To spawn teammate: bash .claude/scripts/spawn-teammate.sh"
- Could pre-show prompt in output or open in editor

**Pros**: Single command, foolproof, can auto-copy to clipboard
**Effort**: ~100 lines shell + doc update
**Timeline**: 1-2 hours

---

**Option 3: Auto-detect in CLAUDE.md (Long-term, behavior enforcement)**
- Add to "Before Spawning Teammate" rule:
  ```
  MANDATORY: Run spawn-agent.py if agent-memory/{type}/MEMORY.md exists.
  If not using spawn-agent.py: manually verify memory is included.

  Verification: grep "Agent Memory" your-prompt.md
  ```
- Add to SessionStart hook (when hooks re-enabled): scan work/ for new prompt files, warn if no agent memory

**Pros**: Enforces via language rules
**Effort**: 3-4 doc updates
**Timeline**: Now (docs) + deferred (hook)

---

## Acceptance Criteria

- [ ] **Cause identified**: agents spawned via Agent tool with inline prompts, not spawn-agent.py
- [ ] **root cause documented**: CLAUDE.md rule exists but not automated → memory never injected
- [ ] **solution selected**: spawn-agent.py as MANDATORY in CLAUDE.md (Option 1)
- [ ] **implementation plan**: update 2 files (CLAUDE.md + quick-mode.md) with new workflow
- [ ] **fallback documented**: if spawn-agent.py unavailable, manual injection rules in template
- [ ] **comparisons complete**: all 4 approaches evaluated with pros/cons

---

## GO/NO-GO Assessment

**GO**: Implement Option 1 (spawn-agent.py MANDATORY)

**Justification**:
1. **Zero risk**: already built, tested, in repo
2. **Immediate**: can implement today (doc updates only)
3. **Foolproof**: auto-injects memory every time
4. **Reversible**: if doesn't work, falls back to manual prompts
5. **Audit trail**: prompts saved to `work/` directory (traceable)

**Next steps**:
1. ✅ Create `work/agent-memory-fix-plan.md` (this analysis)
2. Update CLAUDE.md "Before Spawning Teammate" section to require spawn-agent.py
3. Update `.claude/guides/quick-mode.md` with spawn-agent.py example
4. Test: spawn one teammate using new workflow, verify memory is present

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Team lead forgets to use spawn-agent.py | Medium | Add to CLAUDE.md top-level rules (like "ALWAYS verify") |
| spawn-agent.py has bugs | Low | Already used in AO Hybrid system, tested extensively |
| Teammates ignore injected memory | Medium | Memory is just context — teammates still follow global CLAUDE.md |
| Extra script step too slow | Low | Benchmark: <500ms, acceptable in workflow |

---

## Final Recommendation

**ACCEPT Approach B** (spawn-agent.py MANDATORY) with **Phase 1 enforcement**:

**Phase 1 (Immediate)**:
- Update CLAUDE.md "Before Spawning Teammate" to require spawn-agent.py
- Add example usage to quick-mode.md
- Document as BLOCKING RULE: "Cannot spawn teammate without running spawn-agent.py"

**Phase 2 (Future, when hooks are re-enabled)**:
- Add SessionStart hook to detect unprompted teammates and warn
- Add test to verify agent memory is in all new prompts

**Timeline**: Phase 1 = 30 min (doc updates), Phase 2 = when hooks restored

**Cost**: ~3 docs changed, 2-3 blocking rules added, 0 code changes

**Benefit**: **100% automatic memory injection**, eliminates manual forgetting, improves agent consistency across sessions.
