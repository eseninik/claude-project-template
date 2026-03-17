# Best Practice Research Index

**Analysis Date**: 2026-03-17
**Scope**: 17 documents from `/tmp/claude-code-best-practice/`
**Status**: Complete — two comprehensive deliverables created

---

## PRIMARY DOCUMENTS

### 1. best-practice-analysis.md (22.7 KB)
**Complete reference guide covering:**

| Section | Content |
|---------|---------|
| I. Orchestration | Command → Agent → Skill pattern, frontmatter templates, data flow |
| II. Agent Teams | Parallel execution, data contracts, coordination patterns |
| III. Memory | 3 scopes (user/project/local), Ebbinghaus decay, 4 memory systems |
| IV. Tool Use | allowed_callers field, batch processing, early termination |
| V. Infrastructure | 3 proven bugs (routing, TPU, compiler), MoE variance ±8-14% |
| VI. Boris Tips | 13 practical techniques organized by domain |
| VII. Settings | Priority hierarchy (5 levels), policy enforcement |
| VIII. Global vs Project | Directory structures and scope |
| IX. Monorepos | Nested skill discovery, priority, best practices |
| X. System Prompts | CLI vs SDK defaults, customization methods |
| XI. Chrome Tools | DevTools vs Claude-in-Chrome comparison |
| XII. Rate Limits | extra-usage, fast mode, cost tracking |

**Quick Links:**
- Orchestration deep-dive: Section I
- Parallelism techniques: Section II + VI
- Memory architecture: Section III
- Infrastructure reality: Section V
- Boris's quick wins: Section VI (tips 1, 2, 3, 4)

---

### 2. best-practice-integration-roadmap.md (18.7 KB)
**16-week implementation plan with 7 patterns:**

| Pattern | Timeline | Effort | Impact |
|---------|----------|--------|--------|
| 1. Command → Agent → Skill | Week 1-2 | 1 week | Medium |
| 2. Memory Decay | Week 3-4 | 2 weeks | High |
| 3. Parallel Execution | Week 5-6 | 3 weeks | **HIGHEST** |
| 4. Code Review Agents | Week 7-8 | 2 weeks | High |
| 5. Monorepo Skills | Week 9-10 | 3 weeks | Medium |
| 6. Infrastructure Docs | Week 11-12 | 1 week | Low-Medium |
| 7. CLAUDE.md Evolution | Week 13-14 | 2 weeks | High |

**Key Sections:**
- Executive summary: 7 patterns, top 3 quick wins
- Detailed integration actions for each pattern
- 16-week timeline with phases and deliverables
- Success metrics and risk mitigations
- Dependencies between teams

**Fast-Track Option:**
If you need quick wins only, implement:
1. Parallel worktrees guidance (Week 1-2)
2. Memory tier labels (Week 3-4)
3. Code review agents (Week 5-6)

---

## SUPPORTING CONTEXT

### Source Files Analyzed (17 documents)

**Orchestration & Architecture** (3 files):
- `orchestration-workflow.md` — Command → Agent → Skill pattern with weather example
- `agent-teams-prompt.md` — Multi-agent coordination for time orchestration workflow
- `claude-agent-command-skill.md` — Distinctions, frontmatter, auto-invocation rules

**Configuration & Memory** (4 files):
- `claude-agent-memory.md` — Agent memory scopes and MEMORY.md structure
- `claude-agent-sdk-vs-cli-system-prompts.md` — Customization methods and preset loading
- `claude-global-vs-project-settings.md` — Settings hierarchy and directory structure
- `claude-skills-for-larger-mono-repos.md` — Nested skill discovery and priority

**Technical Reports** (4 files):
- `claude-advanced-tool-use.md` — allowed_callers, batch processing, conditional logic
- `claude-usage-and-rate-limits.md` — extra-usage, fast mode, cost tracking
- `claude-in-chrome-v-chrome-devtools-mcp.md` — Chrome tools comparison matrix
- `llm-day-to-day-degradation.md` — Infrastructure bugs + MoE variance analysis

**Practical Guidance** (4 files):
- `claude-boris-10-tips-01-feb-26.md` — 10 team tips (parallelism, plan mode, skills, etc.)
- `claude-boris-12-tips-12-feb-26.md` — 12 customization tips (terminal, plugins, keybindings)
- `claude-boris-13-tips-03-jan-26.md` — 13 setup tips (parallel Claudes, Opus, subagents)
- `claude-boris-2-tips-10-mar-26.md` — Code review agents + test time compute (NEW Feb-Mar 2026)

---

## KEY FINDINGS SUMMARY

### Top 3 Productivity Unlocks
1. **Parallel Execution** — 3-5 git worktrees with own Claude sessions (5x-10x multiplier)
2. **Plan Mode First** — High-quality plan enables 1-shot implementation
3. **Memory Decay** — knowledge.md tiers keep active patterns front and center

### Infrastructure Realities (Proven)
- **3 infrastructure bugs** in Anthropic's Sept 2025 postmortem (not demand-based)
- **MoE routing variance** ±8-14% day-to-day (normal, from batch composition)
- **Multiple platforms** (AWS Trainium, NVIDIA, Google TPU) = different failure modes

### Orchestration Pattern
- **Command**: Entry point, orchestrates workflow (haiku)
- **Agent**: Autonomous separate context, preloaded skills (sonnet)
- **Skill**: Inline or preloaded, reusable knowledge module

### Memory Architecture
- **User scope**: Cross-project agent knowledge
- **Project scope**: Team-shared agent knowledge
- **Local scope**: Personal project knowledge (git-ignored)
- **Decay**: Ebbinghaus tiers [active/warm/cold/archive] based on freshness

---

## QUICK REFERENCE: BORIS'S TOP TECHNIQUES

| Rank | Technique | Impact | Time to Implement |
|------|-----------|--------|-----------------|
| 1 | Parallel worktrees (3-5) | **HIGHEST** | 1 day |
| 2 | CLAUDE.md compounding | High | Ongoing |
| 3 | Plan mode first | High | Now (behavioral) |
| 4 | Create skills for 1x/day tasks | High | Variable |
| 5 | Code review agents (NEW) | High | 2 weeks |
| 6 | Subagents for compute | Medium | 1 week |
| 7 | Custom slash commands | Medium | Variable |
| 8 | Voice dictation | Medium | Setup only |
| 9 | MCP integrations (BigQuery, Slack) | Medium | Setup only |
| 10 | Status line customization | Low | 1 hour |

---

## INTEGRATION MILESTONES

**This Week (Week of 2026-03-17)**:
- [ ] Create Command guide
- [ ] Add tier labels to session-start
- [ ] Update onboarding with parallel worktrees

**Next 2 Weeks (Week of 2026-03-24)**:
- [ ] Implement memory decay with verified dates
- [ ] Document CLAUDE.md update process
- [ ] Create code-review-hunt-bugs skill

**Month 1 (by 2026-04-17)**:
- [ ] Monorepo skill discovery patterns
- [ ] Infrastructure degradation docs
- [ ] GitHub action for CLAUDE.md updates

**Month 2-4 (by 2026-05-17)**:
- [ ] Full integration testing
- [ ] Team training + demo videos
- [ ] Rollout to all bot projects (8-10 bots)

---

## ACCESSING THE ANALYSIS

### From This Project
```bash
# View analysis
cat .claude/memory/best-practice-analysis.md

# View roadmap
cat .claude/memory/best-practice-integration-roadmap.md

# Jump to section
grep -n "## VI. BORIS CHERNY" .claude/memory/best-practice-analysis.md
```

### Structure
Both documents use markdown headers (`#`, `##`, `###`) for easy navigation with:
- `grep -n "^##"` to find all major sections
- `grep -n "^###"` to find all subsections

### Search Patterns
```bash
# Find orchestration pattern details
grep -A 20 "Command → Agent → Skill" .claude/memory/best-practice-analysis.md

# Find infrastructure bugs
grep -B 5 "September 2025" .claude/memory/best-practice-analysis.md

# Find monorepo patterns
grep -A 10 "nested/descendant discovery" .claude/memory/best-practice-analysis.md

# Find Boris's tips
grep -A 5 "### 6\." .claude/memory/best-practice-analysis.md
```

---

## CROSS-REFERENCES

**Related in our system:**
- `.claude/memory/activeContext.md` — Current project state
- `.claude/memory/knowledge.md` — Patterns + gotchas (apply memory decay here)
- `.claude/memory/daily/` — Daily logs (reference for trends)
- `CLAUDE.md` — Update with new rules from roadmap
- `.claude/agents/registry.md` — Will reference Command orchestration pattern
- `.claude/skills/` — Will adopt nested discovery pattern

**External sources:**
- `/tmp/claude-code-best-practice/` — Raw analysis source
- Boris Cherny (@bcherny) on X — Original tweets with tips
- Anthropic Sept 2025 postmortem — Infrastructure reality basis

---

## USAGE RECOMMENDATIONS

**For Team Lead:**
Start with roadmap Weeks 1-2 (quick wins), then phase into medium efforts.

**For Implementers:**
Reference best-practice-analysis.md when building new features:
- Section III for memory architecture → Know where to save patterns
- Section I for commands → How to structure complex workflows
- Section VI for tips → Productivity techniques

**For QA/Reviewers:**
Use infrastructure realities (Section V) to understand:
- Why same test might pass/fail on different days
- How to validate results reliably (run 3x, 2/3 or 3/3 count)
- MoE variance is normal; adjust sample size accordingly

**For Researchers/Explorers:**
Use monorepo pattern (Section IX) when:
- Working in larger codebases
- Designing skill structures
- Determining what should be shared vs. nested

---

## METADATA

| Field | Value |
|-------|-------|
| Created | 2026-03-17 14:52 UTC |
| Analysis completed | 2026-03-17 15:30 UTC |
| Documents analyzed | 17 |
| Total content | ~6,000 lines analyzed |
| Deliverables | 2 comprehensive guides (41.4 KB total) |
| Integration roadmap | 16 weeks, 7 patterns, phased rollout |
| Owner | researcher-3 |
| Status | Ready for team review |

---

## NEXT ACTIONS

1. **Team Lead**: Review roadmap, approve Weeks 1-2 priorities
2. **Researcher-3**: Start Week 1-2 quick wins
3. **Coder-Complex**: Prepare for Week 7-8 monorepo skills work
4. **QA-Reviewer**: Plan for Week 6 code review agent testing
5. **Pipeline-Lead**: Prepare GitHub action integration for Week 12

**Async Communication**: Use #results channel in results-board.md for progress updates
