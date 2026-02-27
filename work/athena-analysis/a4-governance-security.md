# A4: Athena Governance & Security System Analysis

> **Analyst**: Research Agent (A4)
> **Date**: 2026-02-23
> **Sources**: `src/athena/core/governance.py`, `security.py`, `permissions.py`, `ruin_check.py`, `cos.py`, `sandbox.py`, `health.py`, `docs/SECURITY.md`, `examples/framework/Core_Identity.md`, 6 CoS agent templates, 5 safety protocols, `docs/TOP_10_PROTOCOLS.md`, `docs/SPEC_SHEET.md`

---

## 1. Constitutional Laws (7 Laws: #0 through #7)

Athena has **7 constitutional laws** (not 6 as initially assumed) defined in `examples/framework/Core_Identity.md`. These are hierarchical, with Law #1 being the supreme override.

### Law #0: Subjective Utility First
- **Principle**: Respect the user's utility function; AI serves user's goals, not generic "best practices"
- **Override conditions**: Ruin risk >5% (Law #1), self-deception detected, exploitation of others
- **Nature**: Personalization anchor -- the system adapts to the user, not the reverse

### Law #1: No Irreversible Ruin (SUPREME LAW)
- **Principle**: Veto any path with >5% probability of irreversible ruin
- **5-Layer Ruin Taxonomy**: Financial, Reputational, Legal, Psychological, Moral
- **Theoretical basis**: Ergodicity theory (Taleb, 2018) -- time average != ensemble average in non-ergodic systems
- **Enforcement**: Hard veto via `ruin_check.py` (regex pattern matching for destructive commands) + Protocol 001 (full ruin calculator)
- **Key insight**: Uses the absorbing barrier concept from probability theory -- a 1% chance of ruin repeated N times = 100% ruin certainty

### Law #2: Context Over Confidence (Arena Physics)
- **Principle**: Diagnose WHY something isn't working before trying harder
- **SDR Score**: Signal-to-Drag Ratio -- if >5:1, exit the arena instead of working harder
- **The Boxer Fallacy**: "Working harder when SDR >5:1 = efficient path to ruin"

### Law #3: Actions Over Words (Revealed Preference)
- **Principle**: Judge by behavior, not statements
- **Weight split**: Public statements 5-30% vs Private actions 70-95%
- **Detection**: 2x soft rejection = 1x hard rejection

### Law #4: Modular Architecture
- **Principle**: Extend through protocols, not monolithic prompts
- **Rule**: Never expand Core Identity; push complexity to edges
- **Effect on governance**: Each governance concern gets its own protocol file

### Law #5: Epistemic Rigor (No Orphan Stats)
- **Principle**: All external claims must have traceable sources
- **Enforcement**: Specific citation requirements by claim type (academic, named framework, statistics)

### Law #6: The Triple-Lock (Search -> Save -> Speak)
- **Principle**: Every response must be grounded in retrieved context
- **Enforcement**: `governance.py` tracks whether semantic search AND web search were performed
- **Violation**: Bypassing sequence is a protocol violation, flagged by `GovernanceEngine.verify_exchange_integrity()`

### Law #7: The Propose Step (Search -> Save -> Speak -> Propose)
- **Principle**: Every substantive response must end with a concrete, executable next action
- **Constraint**: Must be executable, not vague "let me know" fillers

---

## 2. Capability Levels (4 Permission Levels)

Defined in `src/athena/core/permissions.py` via the `Permission` enum:

| Level | Enum Value | Description | Example Tools |
|-------|-----------|-------------|---------------|
| **READ** | `Permission.READ` | Can query/read data | `smart_search`, `recall_session`, `health_check` |
| **WRITE** | `Permission.WRITE` | Can modify session logs, checkpoints | `quicksave` |
| **ADMIN** | `Permission.ADMIN` | Can modify config, clear caches, manage sessions | `clear_cache`, `set_secret_mode`, `run_evaluator` |
| **DANGEROUS** | `Permission.DANGEROUS` | Can delete data, run shell commands | (Future, currently unused) |

### Permission Hierarchy
- Numeric levels: READ=0, WRITE=1, ADMIN=2, DANGEROUS=3
- A caller with level N can access all tools requiring level <= N
- Default caller level: `Permission.WRITE` (can read and write, but not admin/dangerous)

---

## 3. Permission System Architecture

### Three-Layer Gating (`PermissionEngine.gate()`)

The permission system uses a combined gate with three sequential checks:

1. **Capability Check** (`check()`): Is the caller's permission level >= required level for this tool?
2. **Sensitivity Check** (`check_sensitivity()`): In secret mode, is the tool's data sensitivity allowed?
3. **Granular Rules Check** (`GranularPermissionEngine.check()`): Do glob-based allow/ask/deny rules permit this tool+input combination?

### Tool Registry
- Each tool pre-registered with required permission level + sensitivity label
- Unknown tools default to WRITE permission requirement
- Example: `smart_search` = READ + INTERNAL, `quicksave` = WRITE + INTERNAL

### Sensitivity Labels (3 levels)

| Label | Description | Access in Secret Mode? |
|-------|-------------|----------------------|
| `PUBLIC` | Safe for demos, external sharing | Allowed |
| `INTERNAL` | Normal operational data | Blocked |
| `SECRET` | Credentials, PII, trading data | Blocked + Redacted |

### Secret Mode
- Purpose: Screen sharing, demos, client presentations
- Effect: Only PUBLIC tools accessible; sensitive content auto-redacted
- Toggle: `set_secret_mode(True/False)`
- Persisted to `.agent/state/permissions.json`

### Granular Permission Engine (OpenCode-inspired)
- **Origin**: Stolen from OpenCode (anomalyco/opencode, 109K stars), Feb 2026
- **Pattern**: Glob-based rules with last-match-wins semantics
- **Actions**: `allow`, `ask` (client prompts user), `deny`
- **Default rules include**:
  - `*.env` files: DENY read access
  - `rm *` commands: DENY
  - `git *` commands: ALLOW
  - Doom loop triggers: ASK (require approval)

### Audit Trail
- Every permission check logged with timestamp, action, target, outcome
- Auto-pruned at 1000 entries (keeps last 500)
- Sensitive details logged as `[REDACTED_TARGET]` to prevent leaks in logs

---

## 4. Ruin Check Mechanism (`ruin_check.py`)

### How It Prevents Catastrophic Actions

The ruin check is a **mechanical kill-switch** -- a simple, fast regex-based scanner that runs BEFORE command execution.

**Protected patterns (regex):**
```
rm -rf \.context
rm -rf \.agent
rm -rf /
truncate -s 0 \.context
delete_file.*\.context
overwrite_file.*\.context.*empty=True
```

**Architecture:**
- CLI-callable: `python ruin_check.py "<proposed_command>"`
- Returns exit code 0 (safe) or 1 (ruinous)
- Designed to be integrated as a pre-execution hook
- Intentionally simple: fast regex, no ML, no false negatives on known patterns

**Limitations:**
- Only catches known destructive patterns (not a general-purpose safety net)
- Focused on protecting `.context` and `.agent` directories (the "memory")
- Does not evaluate semantic risk, only syntactic patterns
- Complements (not replaces) the full Law #1 ruin calculator in Protocol 001

### Multi-Layer Ruin Prevention Stack

| Layer | Mechanism | Scope |
|-------|-----------|-------|
| **Regex scanner** | `ruin_check.py` | Known destructive shell commands |
| **Permission engine** | `permissions.py` | Tool access gating |
| **Granular rules** | `GranularPermissionEngine` | Glob-based input filtering |
| **Doom loop detector** | `governance.py` | Infinite retry prevention |
| **Protocol 001** | Decision protocol | Full ruin probability calculator |
| **Protocol 48** | Circuit breaker | Cumulative damage threshold |
| **Protocol 68** | Anti-Karason | Self-deception detection |
| **Docker sandbox** | `sandbox.py` | Isolated execution environment |

---

## 5. CoS (Committee of Seats) Agent System

### Architecture (`cos.py`)

The CoS is a **multi-perspective reasoning framework** -- not independent agents running in parallel, but a structured way to invoke different analytical lenses.

### 6 Core Seats

| Seat | Perspective Question | Color | Tools |
|------|---------------------|-------|-------|
| **The Strategist** | "Does this serve the goal?" | Blue | Read, Grep, Glob, WebSearch |
| **The Guardian** | "What could go wrong?" | Red | Read, Grep, Glob (read-only) |
| **The Operator** | "How do we build it?" | Green | Read, Grep, Glob, Bash |
| **The Architect** | "Is the structure sound?" | Cyan | Read, Grep, Glob (read-only) |
| **The Skeptic** | "What are we missing?" | Yellow | Read, Grep, Glob (read-only) |
| **The Compliance Gate** | "Should we ship this?" | Magenta | Read, Grep, Glob, Bash |

### 13 Specialized Roles (Protocol 333)

Each specialized role maps to a core seat:

| Specialized Role | Maps To Seat |
|-----------------|-------------|
| Product Manager | Strategist |
| Business Analyst | Strategist |
| Security Engineer | Guardian |
| Risk Officer | Guardian |
| Frontend Developer | Operator |
| Backend Developer | Operator |
| DevOps Engineer | Operator |
| System Architect | Architect |
| Database Architect | Architect |
| QA Engineer | Skeptic |
| Red Teamer | Skeptic |
| Legal/Compliance | Compliance Gate |
| Tech Lead | Compliance Gate |

### Complexity-Based Committee Selection (Protocol 166: Deep Think Proxy)

```python
def get_committee_for_complexity(complexity: int) -> List[Seat]:
    if complexity < 30:
        return [Seat.OPERATOR]                              # Simple: just do it
    elif complexity < 70:
        return [Seat.STRATEGIST, Seat.OPERATOR, Seat.SKEPTIC]  # Medium: 3 perspectives
    else:
        return list(Seat)                                    # Complex: full committee
```

### Athena Framework Protocol (Common to all agents)

Every CoS agent follows the same 5-step protocol:
1. **Recall Prior Decisions**: Search memory (smart_search) for relevant history
2. **Review Project Identity**: Read Core_Identity.md for constraints and philosophy
3. **Discover/Analyze**: Domain-specific investigation using available tools
4. **Analyze and Recommend**: Apply specialized lens with specific output format
5. **Save Findings**: Quicksave checkpoint with one-line summary

### Agent-Specific Output Formats

- **Strategist**: Alignment, Priority (P0-P3), Scope Risk, Recommendation, Rationale
- **Guardian**: Risk Level, Findings (with file:line), Remediation, Approved status
- **Operator**: Complexity, Reusable Patterns, Task Breakdown, Dependencies, Risks
- **Architect**: Structural Impact, Pattern Compliance, Breaking Changes, Tech Debt, Design Notes
- **Skeptic**: Confidence Level, Assumptions Found, Edge Cases, Test Gaps, Verdict
- **Compliance Gate**: Tests, Documentation, Breaking Changes, Session Logged, Gate Decision

---

## 6. Sandbox Execution Modes (`sandbox.py`)

### Architecture
- **Origin**: Extracted from OpenClaw's Host/Sandbox boundary ("The Great Steal 2.0")
- **Pattern**: `athenad /sandbox/exec` -> Docker container -> stdout -> response

### Docker Sandbox Security Controls

| Control | Setting | Purpose |
|---------|---------|---------|
| `--rm` | Auto-cleanup | No leftover containers |
| `--read-only` | Read-only root filesystem | Prevent persistent writes |
| `--tmpfs /tmp:rw,size=64m` | Writable temp (64MB max) | Controlled scratch space |
| `--memory 256m` | Memory limit | Prevent OOM attacks |
| `--cpus 1.0` | CPU limit | Prevent resource exhaustion |
| `--network none` | No network (default) | Prevent data exfiltration |
| Volume mount | `:ro` (read-only) | Script access without modification |

### Execution Flow

```
SandboxExecRequest(script, timeout=30, allow_network=False)
  -> Write script to temp file
  -> docker run with security controls
  -> Capture stdout/stderr + exit code
  -> Return SandboxExecResponse
  -> Clean up temp file
```

### Availability Check
- Verifies Docker is installed AND the `athena-sandbox:latest` image exists
- Graceful fallback: returns error response if Docker unavailable

---

## 7. Governance Engine (`governance.py`)

### Triple-Lock Protocol Enforcement

The GovernanceEngine tracks whether the two required search steps were performed:
1. `mark_search_performed(query)` -- semantic search happened
2. `mark_web_search_performed(query)` -- web search happened
3. `verify_exchange_integrity()` -- returns True only if BOTH completed

State persisted to `{state_dir}/exchange_state.json` and reset after each verification check.

### Doom Loop Detector (from OpenCode, Feb 2026)

**Purpose**: Circuit breaker for token-burning agentic failures where the same tool call repeats with identical arguments.

**Mechanism:**
- Records tool calls with SHA-256 hash of arguments
- Time-windowed (60s default) to avoid false positives
- Threshold: 3 identical calls within window = DOOM LOOP DETECTED
- Returns True to caller, enabling upstream halt logic

**Statistics tracking**: Total violations, history size, configurable threshold/window

---

## 8. Security Hardening (`security.py`)

### CVE-2025-69872 Mitigation
- **Vulnerability**: Default pickle serialization in diskcache allows arbitrary code execution from malicious cache files
- **Fix**: Hot-patches dspy's DiskCache to use JSON serialization instead of pickle
- **Implementation**: Closes old FanoutCache, reopens with `disk=diskcache.JSONDisk`
- **Scope**: Only patches dspy's cache, not general diskcache usage

---

## 9. Health Monitoring (`health.py`)

Simple health check system with two checks:
1. **Vector API**: Verifies Gemini Embedding API returns correct 3072-dimension embeddings
2. **Database**: Verifies Supabase connectivity via sessions table query
- Results: PASS/FAIL with diagnostic details
- Designed to run on boot (`/start`) and on-demand

---

## 10. Safety Protocol System (5 Protocols)

### Protocol 001: Law of Ruin
- **Ranked #1** out of 108 protocols (MCDA score: 4.70)
- Full ergodicity-based ruin calculator
- 5-Layer Ruin Taxonomy (Biological, Legal, Financial, Social, Psychological)
- Decision engine: Ruin Possible? -> No (proceed) / Yes >5% (VETO) / Unknown (sandbox -> re-evaluate)

### Protocol 048: Circuit Breaker (Systemic Pause)
- **Ranked #7** (score: 4.10)
- Macro-level complement to micro-level 3-Second Override
- Domain-specific thresholds (e.g., trading: 5R cumulative loss, work: 2 missed deadlines)
- Forced protocol: STOP -> PAUSE (24h) -> AAR -> DIAGNOSE -> VERDICT
- External enforcement option: circuit breaker CANNOT be overridden by operator alone

### Protocol 068: Anti-Karason (Reality Integration)
- Self-deception detector ("The Karason Effect": conviction overrides reality)
- Triggers when Confidence >80% but Evidence <20%
- Mirror approach (not judge): presents delta between belief and reality
- 4-step execution: Pause -> Assessment Table -> Confrontation Question -> Override (if Law #1 violated)

### Protocol 104: Seymour Skeptic Layer
- Origin: Project Vend (Anthropic, 2025)
- Adversarial safety layer for high-stakes requests
- Catches: status claims, exception requests, unusual asks, confident assertions
- Anti-patterns: appeal to authority, social proof, urgency pressure, specificity-as-credibility

### Protocol 241: Honesty Protocol
- Prime directive: Accuracy > Helpfulness
- Trigger phrases: missing data, outdated info, uncertain facts, specific stats without source
- Knowledge/Inference separation: explicitly label what is known vs inferred

### Risk Playbooks (Operational)
- R001: Leveraged trading >50% net worth -> RED VETO
- R002: Public social media visibility risk -> CIRCUIT BREAKER
- R003: Compulsion trigger (intensity 70-90%) -> SCHEMA_INTERCEPT + time-lock
- R00X: Shadow persona breach -> SANDBOX MODE
- R004: Rogue clients -> Diplomatic disengagement
- R005: Employee entitlement -> Measured leader response

---

## 11. Comparison with Our Template's Constraints

### Our Approach (CLAUDE.md HARD CONSTRAINTS + FORBIDDEN)

| Aspect | Our Template | Athena |
|--------|-------------|--------|
| **Constraint format** | Static table in CLAUDE.md | Dynamic protocols in separate files + code enforcement |
| **Enforcement mechanism** | LLM instruction following only | Code-level enforcement (`ruin_check.py`, `permissions.py`, `governance.py`) + LLM instruction |
| **Ruin prevention** | "Don't delete data without confirmation" | 5-layer taxonomy + ergodicity math + regex scanner + Protocol 001 calculator |
| **Permission model** | Implicit (tool restrictions per agent type) | Explicit 4-level hierarchy with sensitivity labels and audit trail |
| **Secret handling** | ".env + .gitignore" convention | Secret Mode (toggle blocks all non-PUBLIC tools + auto-redaction) |
| **Loop detection** | "Same approach 3+ times -> STOP" | Code-level DoomLoopDetector with SHA-256 hashing + time windows |
| **Multi-perspective review** | Agent Teams (QA Reviewer role) | Committee of Seats (6 specialized perspectives with structured output) |
| **Sandbox execution** | N/A | Docker-based sandbox with network/memory/CPU isolation |
| **Granular tool control** | Agent-type-based (read-only vs full) | Glob-based rules per tool + input pattern (allow/ask/deny) |
| **Audit trail** | No formal audit | Every permission check logged with timestamp |
| **Verification gate** | "NEVER say done without tests" | Compliance Gate agent + Triple-Lock + integrity score |
| **Context grounding** | Memory read at session start | Enforced Triple-Lock (Search -> Save -> Speak) with code tracking |
| **Compulsion/bias detection** | N/A | Anti-Karason protocol + Seymour Skeptic Layer |

### Key Differences

1. **Code vs Prose**: Athena enforces governance in Python code; our template relies on LLM instruction following. Code enforcement is deterministic and unbypassable; LLM instructions can be forgotten after compaction.

2. **Depth of Ruin Prevention**: Athena has a multi-layer stack (regex + permissions + protocols + sandbox); our template has a single-line constraint. Athena's approach is grounded in probability theory (ergodicity, Kelly criterion).

3. **Permission Granularity**: Athena gates EVERY tool call through 3 checks (capability + sensitivity + granular rules); our template only differentiates agent types (read-only vs full access).

4. **Multi-Perspective Reasoning**: Athena's CoS is a structured framework with 6 specialized lenses, each with defined output format and Athena-specific protocol. Our Agent Teams are more flexible but less structured for governance decisions.

5. **Observability**: Athena has audit logging, integrity scores, and doom loop statistics. Our template has no formal observability for governance.

### What We Could Adopt

| Athena Feature | Adaptation for Our Template | Priority |
|----------------|---------------------------|----------|
| **Doom Loop Detector** | Add to hooks or as a pre-tool-call check | HIGH -- prevents token waste |
| **Ruin Check Hook** | Pre-commit/pre-bash hook scanning for destructive patterns | HIGH -- complements existing constraints |
| **Structured CoS for decisions** | Define output formats for our QA Reviewer role | MEDIUM -- improves review consistency |
| **Secret Mode concept** | Environment-aware constraint toggling | LOW -- less relevant for dev-only template |
| **Granular tool rules** | Glob-based allow/deny in settings.json | MEDIUM -- more precise than agent-type gating |
| **Triple-Lock enforcement** | Require memory search before task completion | MEDIUM -- prevents context drift |
| **Audit trail** | Log tool calls and permission decisions to daily log | LOW -- useful for debugging but adds overhead |

---

## 12. Summary

Athena's governance system is a **defense-in-depth architecture** built around the central principle of ruin prevention (Law #1). Its key innovation is enforcing governance at multiple layers simultaneously:

1. **Constitutional layer**: 7 Laws providing philosophical foundation
2. **Code enforcement layer**: Permission engine, ruin check, doom loop detector
3. **Protocol layer**: 269 decision protocols (9 safety-specific) providing structured reasoning
4. **Multi-perspective layer**: CoS with 6 seats providing adversarial review
5. **Execution isolation layer**: Docker sandbox for untrusted code
6. **Observability layer**: Audit trail, integrity scores, health checks

The system's most distinctive quality is its **theoretical grounding** -- using ergodicity theory, the Kelly criterion, and probability theory to justify its safety constraints, rather than relying on intuitive rules. This gives the constraints a mathematical foundation that is harder to argue against or relax.

For our template, the highest-value adoptions would be the **Doom Loop Detector** (code-level, prevents token waste) and a **Ruin Check Hook** (pre-execution pattern scanning), as these provide deterministic safety guarantees that survive LLM context compaction.
