# Athena-Public vs Our Template: Comparison Matrix

> Synthesized from 10 parallel research agent reports (217KB total analysis)
> Date: 2026-02-23

---

## Architectural Philosophy Comparison

| Dimension | Athena-Public | Our Template | Winner |
|-----------|--------------|-------------|--------|
| **Core Philosophy** | "OS for AI agents" — model-agnostic, retrieval-first | "AI-First Methodology" — Claude-native, prescriptive | Different paradigms |
| **Entry Point Size** | ~80 lines (lean directory/pointer) | ~300 lines (dense rulebook) | Athena (token efficiency) |
| **Context Loading** | On-demand, keyword-triggered, 3-tier adaptive | All-at-once via CLAUDE.md | Athena (efficiency) |
| **Token Management** | Explicit 20K hard cap + ASCII gauge + auto-compaction | Implicit (IDE-managed) | Athena (visibility) |
| **Agent Teams** | None (single-user paradigm) | Full team orchestration (TeamCreate) | Ours (parallelism) |
| **Pipeline State** | Session-based workflows | Formal state machine (PIPELINE.md) | Ours (rigor) |
| **Compaction Recovery** | Protocol 101 (aspirational) | Battle-tested re-read protocol | Ours (reliability) |
| **Memory Persistence** | Supabase + pgvector + ChromaDB + Markdown | Graphiti (Neo4j) + Markdown files | Different trade-offs |
| **Model Strategy** | Multi-model (Claude + Gemini + GPT) | Single-model (Claude Opus 4.6) | Athena (flexibility) |
| **Platform** | macOS-centric (AppleScript for swarm) | Cross-platform (Windows/Mac/Linux) | Ours (portability) |
| **Skill Count** | 1 implemented + 49 workflows | 11 production skills | Ours (maturity) |
| **Skill Triggers** | 5W1H metadata + keyword nudge + telemetry | YAML frontmatter + LLM routing | Athena (reliability) |
| **Quality Gate** | Numeric convergence (0-100, threshold 85) | Qualitative QA loop (PASS/FAIL) | Athena (objectivity) |
| **Search/RAG** | 8-source hybrid RRF + cross-encoder reranking | Graphiti nodes + facts search | Athena (breadth) |
| **Governance** | 6 laws + permissions + Triple-Lock + Doom Loop | HARD CONSTRAINTS + FORBIDDEN tables | Athena (enforcement) |
| **Security** | 4-tier permissions + secret mode + PII auto-redaction | Manual (inline rules) | Athena (formalization) |
| **Audit Trail** | Flight Recorder (immutable JSONL) | None | Athena |
| **Error Handling** | Diagnostic Relay (to-disk, PII-sanitized) | Inline (in-context) | Athena (context-safe) |
| **Session Metrics** | Composite efficiency score (0-100) | None | Athena |

---

## Domain-by-Domain Comparison

### Memory & Persistence (A1)
| Feature | Athena | Ours |
|---------|--------|------|
| Storage backend | Supabase pgvector (cloud) | Graphiti/Neo4j |
| Dynamic updates | Manual sync pipeline | Real-time add_memory() |
| Temporal reasoning | Session dates only | Temporal metadata on facts |
| Entity extraction | Expensive LLM one-time | Automatic from text |
| Contradiction handling | None | Facts marked as superseded |
| Progressive distillation | 4-stage (raw→session→compacted→vector) | 2-stage (raw→knowledge) |
| External knowledge | Exocortex (Wikipedia FTS5) | None |

### Boot & Lifecycle (A2)
| Feature | Athena | Ours |
|---------|--------|------|
| Boot speed | Sub-5s, parallelized (8 threads) | Not measured |
| Boot tokens | ~2K minimum, 20K hard cap | ~3K+ (full CLAUDE.md) |
| Adaptive loading | 3 tiers (Shikai/Bankai/Shukai) | None |
| Token gauge | ASCII progress bar, color-coded | None |
| Auto-compaction | 3-phase, age-based pruning | pre-compact-save.py hook |
| Session lifecycle | /start -> work -> /end (explicit commands) | Session Start protocol (auto-behaviors) |

### Protocol/Skills System (A3, A9)
| Feature | Athena | Ours |
|---------|--------|------|
| Total protocols/skills | 120+ protocols, 49 workflows | 11 skills |
| Categorization | 13 categories (decision, engineering, etc.) | Flat list |
| Skill triggers | 5W1H metadata + keyword nudge (programmatic) | YAML description + LLM routing |
| Telemetry | JSONL usage tracking | None |
| Dead skill detection | get_dead_skills() function | Manual review |
| Command stacking | /think /search /research = "Triple Crown" | None |
| Prompt library | 14 reusable meta-prompts | None |
| Reasoning depth | 3 tiers (normal/think/ultrathink) | Implicit |

### Governance & Security (A4)
| Feature | Athena | Ours |
|---------|--------|------|
| Constitutional laws | 6 formal laws | HARD CONSTRAINTS table |
| Permission levels | 4 tiers (READ/WRITE/ADMIN/DANGEROUS) | None |
| Data sensitivity | 3 labels (PUBLIC/INTERNAL/SECRET) | None |
| Ruin prevention | ruin_check.py (pre-flight gate) | Inline rules |
| Doom loop detection | 3+ identical tool calls in 60s = break | Retry limits in CLAUDE.md |
| Secret mode | Toggle for demos, auto-PII redaction | None |
| Audit trail | Flight recorder + permission log | None |

### Agent Coordination (A5)
| Feature | Athena | Ours |
|---------|--------|------|
| Isolation model | Git worktrees (full copy per agent) | Shared worktree or SDK worktree |
| Communication | Filesystem polling (JSON) | SDK SendMessage |
| Spawning | OS-level (Terminal.app AppleScript) | API-level (TeamCreate) |
| Reasoning model | 4 adversarial tracks (A/B/C/D) | Role-based (coder, reviewer, etc.) |
| Quality gate | Numeric convergence (85/100) | QA validation loop |
| Cross-validation | Trilateral feedback (multi-provider) | None |
| Budget enforcement | Gatekeeper (soft 80% / hard 100%) | None |
| Git safety rules | Protocol 413 (6 explicit rules) | Implicit caution |

### RAG & Search (A6)
| Feature | Athena | Ours |
|---------|--------|------|
| Retrieval sources | 8 parallel collectors | 2 (search_nodes, search_facts) |
| Fusion method | Weighted RRF (17 per-subtype weights) | Native Graphiti ranking |
| Reranking | Cross-encoder (ms-marco-MiniLM) | None |
| Query decomposition | Agentic search (rule-based, no LLM cost) | None |
| Caching | Exact + semantic cache | None |
| Tiered latency | Fast (<200ms) + Full pipeline (5-8s) | Single speed |
| Embedding model | text-embedding-004 (3072-dim) | Graphiti built-in |

### CLAUDE.md Approach (A7)
| Feature | Athena | Ours |
|---------|--------|------|
| Size | ~80 lines | ~300 lines |
| Philosophy | "Pointer/directory" — tells WHERE to find rules | "Rulebook" — contains ALL rules |
| Token cost per session | ~500 tokens entry + on-demand | ~3000+ tokens always |
| Scalability | 308+ protocols without entry file bloat | Every new behavior = more CLAUDE.md lines |
| Model-agnostic | Yes (AGENTS.md = CLAUDE.md) | No (Claude Code specific) |
| Compaction safety | Weaker (relies on /start) | Stronger (embedded recovery rules) |
| Compliance guarantee | Lower (agent must search) | Higher (rules always in context) |

### MCP & Tools (A8)
| Feature | Athena | Ours |
|---------|--------|------|
| MCP server | Custom FastMCP (Python) | Third-party Graphiti MCP |
| Tools count | 9 custom + 2 resources | 8 Graphiti tools |
| Permission gating | Every tool call gated | Open access |
| Governance | Triple-Lock (search before save) | None |
| Background sync | Heartbeat daemon (file watcher) | None |
| Diagnostic relay | PII-sanitized error reports to disk | None |
| TUI dashboard | Rich-based terminal UI | None |

### Context Engineering (A10)
| Feature | Athena | Ours |
|---------|--------|------|
| Token budget tracking | Explicit 20K hard cap + gauge | None |
| Adaptive loading | 3-tier (2K/10K/100K+) | None (all-at-once) |
| File sharding | Yes (Tag Index A-M/N-Z, Profile 6-way) | No (monolithic files) |
| Context zones | 4-zone (Green/Yellow/Orange/Red) | None |
| Session efficiency | Composite 0-100 score | None |
| Error-to-disk | Diagnostic Relay + Flight Recorder | Inline errors |
| Multi-model arbitrage | Gemini for research, Claude for coding | Single model |
| Compaction passes | 3-phase automated (normal + aggressive) | Single hook |

---

## Summary Scores (1-5 scale)

| Area | Athena | Ours | Notes |
|------|--------|------|-------|
| Token efficiency | ⭐⭐⭐⭐⭐ | ⭐⭐ | Athena's adaptive loading is a killer feature |
| Agent orchestration | ⭐⭐ | ⭐⭐⭐⭐⭐ | Our TeamCreate/Pipeline is far superior |
| Memory architecture | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Different strengths (breadth vs dynamism) |
| Governance/security | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Athena's formal layers are stronger |
| Search quality | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 8-source RRF vs single Graphiti search |
| Skill system | ⭐⭐⭐ | ⭐⭐⭐⭐ | We have more mature skills |
| Compaction resilience | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Our recovery protocol is battle-tested |
| Platform portability | ⭐⭐ | ⭐⭐⭐⭐⭐ | Athena's swarm is macOS-only |
| Observability | ⭐⭐⭐⭐⭐ | ⭐ | Flight recorder, telemetry, efficiency score |
| Scalability (protocols) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Athena scales to 300+ without bloat |
