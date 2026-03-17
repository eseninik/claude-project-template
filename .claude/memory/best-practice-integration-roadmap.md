# Claude Code Best Practice Integration Roadmap

**Analysis Date**: 2026-03-17
**Source**: `/tmp/claude-code-best-practice/` — 17 comprehensive documents
**Integration Strategy**: Incremental adoption of patterns into existing systems

---

## EXECUTIVE SUMMARY

The best-practice repository contains **11 core patterns** that enhance our template system. This roadmap prioritizes them by impact, effort, and alignment with our existing Autonomous Pipeline Protocol.

**Top 3 Quick Wins** (1-2 weeks):
1. Adopt memory decay system (Ebbinghaus) — already have knowledge.md
2. Document Command → Agent → Skill pattern in skill conductor review
3. Add parallel worktrees tip to onboarding

**Medium Efforts** (2-4 weeks):
1. Code Review + verification agents pattern
2. Monorepo skill discovery pattern for larger projects
3. Test time compute guidance in PIPELINE phases

**Strategic Initiatives** (1-2 months):
1. Agent Teams integration with results board
2. Memory architecture layering (user/project/local scopes)
3. Infrastructure degradation documentation

---

## PATTERN: 1 — COMMAND → AGENT → SKILL ORCHESTRATION

### Current Status in Our System
- ✅ Agents exist (registry.md)
- ✅ Skills exist (12+ in conductor review)
- ❌ Commands not documented
- ❌ Orchestration pattern not formalized

### Integration Action Items

**1.1 Document Commands System**
```
FILE: .claude/guides/command-orchestration.md
CONTENT:
- Command definition syntax
- When to use commands vs skills vs agents
- Frontmatter template + examples
- Data contract patterns (how command passes data to agents/skills)
```

**1.2 Add to Skill Conductor Modes**
- Mode 6 (NEW): "Validate Orchestration Pattern"
  - Check: Command → Agent → Skill flow is clear
  - Check: Data contracts defined (input/output)
  - Check: Correct tool invocation (Agent tool vs Skill tool)

**1.3 Update Teammate Prompt Template**
```
Add section: "## Orchestration Pattern"
- If task involves multiple components, use Command → Agent → Skill
- Agent handles autonomous work (separate context)
- Skill handles inline output (same context)
- Command orchestrates both
```

**Timeline**: 1 week (document patterns + review checklist)

---

## PATTERN: 2 — MEMORY DECAY (EBBINGHAUS)

### Current Status in Our System
- ✅ knowledge.md exists with patterns
- ✅ Memory engine script exists (.claude/scripts/memory-engine.py)
- ❌ Tier labels not visible in session start
- ❌ Decay calculation not documented
- ❌ Search modes not explained

### Integration Action Items

**2.1 Enhance Session Start Hook**
```
ENHANCEMENT: session-orient.py
CURRENT: Shows patterns + gotchas (unranked)
NEW: Add tier labels [active] [warm] [cold] [archive]

Example Output:
✓ [active] Pattern: Agent Teams for 3+ tasks (verified 2026-03-17)
✓ [warm]   Pattern: Worktree management (verified 2026-03-10)
⚠ [cold]   Pattern: XLA bugs in inference (verified 2026-02-19)
```

**2.2 Document Search Modes in CLAUDE.md**
```
SECTION: "## Memory Decay & Search Modes"
- heartbeat: Active only (~2K tokens) — quick checks
- normal: Active + warm (~5K tokens) — default
- deep: All tiers + Graphiti (~15K tokens) — critical decisions
- creative: Random cold/archive (~3K tokens) — brainstorm
```

**2.3 Add Memory Touch Command to Onboarding**
```
WHEN: You used a pattern during work
COMMAND: py -3 .claude/scripts/memory-engine.py knowledge-touch "Pattern Name"
EFFECT: Promotes pattern one tier (graduated recall, not straight to top)
```

**2.4 Update knowledge.md Format**
```
CURRENT: ### Pattern Name (YYYY-MM-DD)

NEW: ### Pattern Name (created: YYYY-MM-DD, verified: YYYY-MM-DD)
     Tier: [calculated: active/warm/cold/archive]

EXAMPLE:
### Agent Teams Parallelism (created: 2026-02-10, verified: 2026-03-17)
- Rule: 3+ independent tasks → always use Agent Teams, never sequential
- Why: Parallel execution multiplier 5x-10x (measured in fleet sync)
- How to apply: Check PIPELINE.md Mode field; if AGENT_TEAMS → TeamCreate
```

**Timeline**: 2 weeks (hook enhancement + docs + verify engine)

---

## PATTERN: 3 — PARALLEL EXECUTION (WORKTREES & AGENT TEAMS)

### Current Status in Our System
- ✅ Worktree support exists (using-git-worktrees skill)
- ✅ Agent Teams implemented (TeamCreate)
- ✅ PIPELINE.md has Mode field
- ❌ Parallel worktree onboarding missing
- ❌ Coordination patterns underexplained

### Integration Action Items

**3.1 Enhance Onboarding Guide**
```
FILE: .claude/guides/onboarding-parallelism.md
CONTENT:
Section 1: "Parallel Execution is #1 Productivity Unlock"
- Spin up 3-5 git worktrees with own Claude sessions
- Name them: 2a, 2b, 2c (shell aliases for quick switching)
- Use tmux/terminal tabs (one tab per worktree)
- Dedicated "analysis" worktree for logs/queries
- Why: Independent contexts catch different bugs

Section 2: "Worktree Naming Pattern"
- Analysis: read-only, query logs/metrics
- Feature-A: implement feature-a branch
- Feature-B: implement feature-b branch
- Review: code review, verification, testing
- Main: keep main branch clean, pull-only
```

**3.2 Add to PIPELINE.md Guidance**
```
PHASE SELECTION GUIDE:
If Mode = AGENT_TEAMS:
  → Create team with N agents
  → Each agent in own task (no blockedBy)
  → Run TaskList to monitor progress

If Mode = SEQUENTIAL:
  → Continue using current approach
  → BUT consider: could this be 3+ parallel tasks?
```

**3.3 Create Results Board Skill**
```
NAME: results-board-monitor
DESCRIPTION: Append your findings to work/results-board.md
TRIGGER: At end of complex investigation
USAGE: Invoke as skill to log findings for other agents
FORMAT:
## Agent: {{agent-name}}
- Task: {{task-id}}
- Finding: {{finding}}
- Time: {{timestamp}}
```

**3.4 Document Coordination Pattern**
```
FILE: .claude/guides/agent-teams-coordination.md

PATTERN: Phase Handoff
├─ Phase 1 Complete: All agents output === PHASE HANDOFF === block
├─ Handoff contains: Status, Decisions, Blockers, Artifacts
├─ Phase 2 Agents read handoff before starting
└─ PIPELINE.md marker moves to next phase

PATTERN: Data Contract First
├─ Before parallelism, define interface
├─ Example: Agent returns {time, timezone, formatted}
│ Command passes through context to skill
│ Skill consumes as-is, no re-fetching
└─ This removes timing dependencies
```

**Timeline**: 3 weeks (onboarding + results board + coordination guide)

---

## PATTERN: 4 — TEST TIME COMPUTE & CODE REVIEW

### Current Status in Our System
- ✅ verification-before-completion skill exists
- ✅ qa-validation-loop skill exists
- ❌ Code Review agents pattern not formalized
- ❌ Test time compute guidance missing
- ❌ Uncorrelated context windows not explained

### Integration Action Items

**4.1 Formalize Code Review Pattern**
```
FILE: .claude/guides/code-review-agents.md

TRIGGER: After IMPLEMENT phase, before merging

PATTERN:
1. One agent writes code (implementer)
2. Second agent reviews (reviewer) — separate context, fresh eyes
3. Reviewer runs verification checks independently
4. If issues found: spawns fixer agent
5. Re-review with third agent (fresh eyes)
6. Max 3 cycles before escalating

WHY: Separate context windows produce uncorrelated bugs
     Same model, different window = different thinking path
```

**4.2 Add Test Time Compute Section to CLAUDE.md**
```
## Test Time Compute

More tokens = better results (at the problem level, not token level)

Techniques:
- Separate context windows (uncorrelated thinking)
- Multiple verification agents (fresh eyes each)
- Extended inference (deeper analysis in one agent)
- Plan mode first (high-quality plan → 1-shot implementation)

In the limit: agents will write bug-free code
```

**4.3 Create Code Review Skill**
```
NAME: code-review-hunt-bugs
DESCRIPTION: Deep review looking for bugs the implementer missed
TRIGGER: Run after IMPLEMENT phase
SEARCH FOR:
- Off-by-one errors
- Missing error handling
- Race conditions
- Type mismatches
- Logic errors in conditionals
```

**4.4 Document Code Review Scoring**
```
RUBRIC (in qa-validation-loop):
- Critical bugs: 1 found → must fix before merge
- Important: 2+ found → add to backlog
- Minor: 3+ found → document in PR
- Zero issues: Ready to merge
```

**Timeline**: 2 weeks (guides + review skill + rubric)

---

## PATTERN: 5 — SKILL STRUCTURE IN MONOREPOS

### Current Status in Our System
- ✅ Skills in root `.claude/skills/` exist
- ✅ Skill conductor review complete (all 13 skills)
- ❌ Nested package skills not documented
- ❌ Discovery pattern not explained
- ❌ Priority/conflict handling missing

### Integration Action Items

**5.1 Document Nested Skill Discovery**
```
FILE: .claude/guides/monorepo-skills.md

PATTERN: Skill Loading
- Root: `.claude/skills/` → loaded immediately (shared)
- Nested: `packages/{name}/.claude/skills/` → discovered on-demand
- Only files in active editing directory are discovered
- Descriptions in context, full content on-demand

EXAMPLE:
.claude/skills/
  └─ shared-conventions/SKILL.md      ← Always loaded

packages/frontend/.claude/skills/
  └─ react-patterns/SKILL.md          ← Loaded when editing frontend/

packages/backend/.claude/skills/
  └─ api-design/SKILL.md              ← Loaded when editing backend/
```

**5.2 Create Skill Placement Guidelines**
```
SHARED (root):
- Version control conventions (git, branching)
- Code style (linting, formatting)
- Testing standards (test structure)
- PR/review process
- Deployment workflows

FRONTEND (packages/frontend/):
- React component patterns
- CSS/styling conventions
- Testing React components
- Performance optimization

BACKEND (packages/backend/):
- API design patterns
- Database queries
- Error handling
- Authentication/authorization

DATABASE (packages/db/):
- Migration patterns
- Schema conventions
- Query optimization
```

**5.3 Update Skill Conductor for Nested Discovery**
```
NEW REVIEW MODE: "Monorepo Validation"
- Verify root skills are truly shared
- Check nested skills have package namespacing
- Ensure descriptions load; content on-demand
- Validate no conflicts in naming
- Measure description/content size split
```

**5.4 Add Migration Guide**
```
FOR EXISTING PROJECTS:
1. Audit current skills → which are truly shared?
2. Move non-shared → packages/{name}/.claude/skills/
3. Rename with package prefix (frontend-*, backend-*)
4. Test discovery in editing different packages
5. Measure context savings
```

**Timeline**: 3 weeks (guides + conductor update + migration playbook)

---

## PATTERN: 6 — INFRASTRUCTURE DEGRADATION DOCUMENTATION

### Current Status in Our System
- ❌ No documentation of infrastructure realities
- ❌ No guidance on handling ±8-14% variance
- ❌ No post-mortem lessons captured

### Integration Action Items

**6.1 Create Infrastructure Reality Document**
```
FILE: .claude/guides/infrastructure-realities.md

SECTION 1: The September 2025 Bugs (Proven)
- Context window routing (16% Sonnet 4 affected)
- TPU output corruption (nonsense tokens)
- XLA compiler miscompilation (batch-dependent)
- Timeline, symptoms, solutions for each

SECTION 2: MoE Routing Variance (Day-to-Day ±8-14%)
- Root cause: Batch composition determines expert routing
- Normal behavior, not bugs
- Implications: A/B tests need larger sample sizes
- Same model, same weights, different outputs on different days

SECTION 3: Practical Implications
- Don't trust single evaluation run
- Run tests 3+ times across days for reliability
- Code review agents catch infrastructure variance bugs
- Multiple context windows reduce variance impact
```

**6.2 Add Degradation Recovery Skill**
```
NAME: handle-infrastructure-variance
DESCRIPTION: When results seem wrong, validate with multiple runs
PATTERN:
1. Run test/evaluation once
2. If suspicious result → run 2 more times
3. If 2/3 or 3/3 consistent → likely real result
4. If split 1-1-1 or 2-1 → likely infrastructure variance
5. If variance suspected: increase sample size before conclusions
```

**6.3 Update QA Validation Loop**
```
ENHANCEMENT: Session-to-session testing
CURRENT: Single test run
NEW: Run tests in 3 separate sessions (different days/times if possible)
SCORING:
- All 3 pass → high confidence (real fix)
- 2/3 pass → medium confidence (probably real)
- 1/3 pass → low confidence (might be variance)
```

**Timeline**: 1 week (document + update QA skill)

---

## PATTERN: 7 — CLAUDE.MD EVOLUTION (COMPOUNDING)

### Current Status in Our System
- ✅ CLAUDE.md exists (comprehensive)
- ✅ Team has reviewed and updated it
- ❌ Compounding pattern not formalized
- ❌ Update process not automated
- ❌ GitHub action for PR tagging not set up

### Integration Action Items

**7.1 Formalize CLAUDE.md Update Process**
```
RULE: "Update CLAUDE.md After Every Correction"

PROCESS:
1. Claude makes mistake → you correct it
2. You say: "Update your CLAUDE.md so you don't make that mistake again"
3. Claude adds rule to CLAUDE.md
4. Format: Short rule + Why + How to apply
5. Team reviews rule in PR (optional)
6. Rule compounds over time → mistake rate drops

EVIDENCE: Boris Cherny says this is #2 most impactful after parallelism
```

**7.2 Document CLAUDE.md Sections**
```
SECTION 1: Hard Constraints (non-negotiables)
SECTION 2: Blocking Rules (gates before action)
SECTION 3: Architecture Decisions (why we chose this)
SECTION 4: Memory Locations (where to find things)
SECTION 5: Forbidden Patterns (never do this)
SECTION 6: Tools/Skills Mapping (which tool for what)

→ Keep ~5-10 rules per section, move overflow to reference files
```

**7.3 Create GitHub Action Integration**
```
ACTION: @claude-bot on PR
EFFECT:
- Extracts code changes
- Generates CLAUDE.md rule candidates
- Posts as PR comment
- Team reviews + accepts/rejects
- Auto-commits rule to CLAUDE.md

EXAMPLE OUTPUT:
## Suggested CLAUDE.md Update
**Rule**: Never use `git checkout -f` without confirmation
**Why**: Overrides uncommitted work without asking
**How to apply**: Before adding to HARD CONSTRAINTS, verify no active branches
```

**Timeline**: 2 weeks (process doc + action setup + initial rules)

---

## INTEGRATION TIMELINE (16-WEEK ROADMAP)

### Week 1-2: Quick Wins
- [ ] Create best-practice-analysis.md (✅ DONE)
- [ ] Document Command → Agent → Skill pattern
- [ ] Add tier labels to session start
- [ ] Create onboarding parallelism guide

**Owner**: researcher-3
**Blockers**: None
**Deliverable**: 4 new guides, enhanced session start

### Week 3-4: Memory Decay & Onboarding
- [ ] Enhance memory-engine.py output (tier labels)
- [ ] Update knowledge.md format with verified dates
- [ ] Create memory-touch command guide
- [ ] Add parallel worktrees to onboarding

**Owner**: researcher-3
**Blockers**: None
**Deliverable**: Enhanced memory system, updated onboarding

### Week 5-6: Code Review Agents
- [ ] Create code-review-hunt-bugs skill
- [ ] Document test time compute pattern
- [ ] Create code review scoring rubric
- [ ] Update qa-validation-loop with 3-run validation

**Owner**: qa-reviewer
**Blockers**: research-3 Week 3-4
**Deliverable**: Code review agent + QA enhancements

### Week 7-8: Monorepo Skills
- [ ] Document nested skill discovery
- [ ] Create placement guidelines by package
- [ ] Update skill conductor with nested validation
- [ ] Create migration guide for existing projects

**Owner**: coder-complex
**Blockers**: research-3 Week 1-2
**Deliverable**: Monorepo skill guidance + conductor update

### Week 9-10: Infrastructure Documentation
- [ ] Create infrastructure realities guide
- [ ] Add degradation recovery skill
- [ ] Update QA validation with multi-session testing
- [ ] Document MoE variance implications

**Owner**: researcher-3
**Blockers**: None
**Deliverable**: Infrastructure reality doc + variance handling

### Week 11-12: CLAUDE.md Compounding
- [ ] Document CLAUDE.md update process
- [ ] Formalize sections and structure
- [ ] Create GitHub action for rule suggestions
- [ ] Set up @claude-bot PR integration

**Owner**: pipeline-lead
**Blockers**: research-3 Week 1-2 (for rule format)
**Deliverable**: Automated CLAUDE.md evolution system

### Week 13-14: Integration & Testing
- [ ] Test all new guides with real tasks
- [ ] Verify tier labels appear correctly
- [ ] Validate code review agent on sample PR
- [ ] Test nested skill discovery in practice

**Owner**: qa-reviewer
**Blockers**: All above
**Deliverable**: Integration test report

### Week 15-16: Team Training & Rollout
- [ ] Record quick demo videos (parallel worktrees, code review agents)
- [ ] Update project README with new patterns
- [ ] Create checklists for each pattern
- [ ] Rollout to all bot projects (8 to 10 bots)

**Owner**: pipeline-lead
**Blockers**: Week 13-14
**Deliverable**: Training materials + rollout checklist

---

## SUCCESS METRICS

After full integration, we should see:

1. **Productivity**: Sessions with 3+ parallel worktrees become standard
2. **Quality**: Code review agents catch 2-3 bugs/PR (measured from tool output)
3. **Knowledge**: knowledge.md patterns grow, decay predictably
4. **Mistakes**: Repeated errors → CLAUDE.md rules → error rate drops 20%+
5. **Monorepos**: Nested skills reduce root-level skill clutter by 40%
6. **Reliability**: Multi-session test validation reduces false passes by 15%

---

## RISKS & MITIGATIONS

| Risk | Mitigation |
|------|-----------|
| Memory decay formula too aggressive | Use research preset (0.01 decay rate), monitor in week 3-4 |
| Code review agents find too many non-issues | Train on real PR feedback, adjust rubric weekly |
| Nested skill discovery confuses users | Add `/discover-skills` command showing discovery tree |
| CLAUDE.md grows too large | Monthly trim: archive 50+ cold rules to reference files |
| Parallel worktrees = context switching overhead | Shell aliases + tmux panels reduce switching time |
| GitHub action unreliable | Start with manual PR comments, automate only when stable |

---

## DEPENDENCIES & HAND-OFFS

```
researcher-3 (Weeks 1-2, 5-6, 9-10)
    ↓ deliverables
coder-complex (Week 7-8) — Use guides to update skills
qa-reviewer (Week 6, 13-14) — Test and validate
pipeline-lead (Week 12, 15-16) — Integrate and rollout
    ↓ final deliverable
All teams (Week 15-16) — Adopt patterns
```

---

## NEXT STEPS

1. **Immediate** (today): Send analysis to team-lead ✅
2. **This week**: Create Command guide + session-start enhancement
3. **Next week**: Begin memory decay implementation
4. **Ongoing**: Collect feedback from team on each pattern

**Owner**: researcher-3
**Deadline for Week 1-2 deliverables**: 2026-03-24
**Full integration target**: 2026-05-12 (16 weeks from start)
