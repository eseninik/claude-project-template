# Risk Assessment: Global Skills Migration (~/.claude/skills/)

**Assessment Date:** 2026-03-17
**Assessor:** Risk Assessor (Agent)
**Trigger:** Technical planning for scaling skills management across 11 bot projects

---

## Executive Summary

Migrating skills from project `.claude/skills/` to global `~/.claude/skills/` carries **MEDIUM-HIGH risk** with significant operational complexity. The current architecture has **zero infrastructure for precedence, project overrides, or skill isolation**. Without explicit design changes, migration will cause:

- Loss of project-specific skill variants
- Cross-project contamination risk
- Breaking changes to agent memory coupling
- Template sync confusion (init-project command breaks)
- Multi-user conflicts (if machine is shared)

**Recommendation: NO-GO for direct migration. Instead, implement a hybrid model with precedence rules first.**

---

## Risk Categories & Matrix

### 1. SKILL LOADING INFRASTRUCTURE RISK

**Probability:** HIGH (99%)
**Impact:** CRITICAL (all projects broken)
**Severity:** CRITICAL

#### Current State
- `generate-prompt.py` hardcodes: `skills_dir = root / '.claude' / 'skills'`
- No global fallback or precedence lookup
- No environment variable for skill path override
- Scripts assume single skill location per invocation

#### Risk: Claude Code Unknown Support
- **Actual Risk:** Claude Code Skill tool may NOT read from `~/.claude/skills/` — architecture may be project-only
- **Evidence Needed:** Test Claude Code Skill tool with global path (no public docs available)
- **Impact if True:** All 11 projects lose access to skills overnight

#### Risk: Precedence Ambiguity
- If Claude Code DOES support global skills, precedence is undefined:
  - Does project override global? (desired)
  - Does global override project? (catastrophic)
  - Can both exist simultaneously? (unknown)
- **Evidence Needed:** Reverse-engineer Skill tool behavior

#### Mitigation (if proceeding)
1. **BEFORE migration:** Run explicit precedence test on a copy of template-update
   ```bash
   # Create ~/.claude/skills/test-skill/SKILL.md
   # Create ./.claude/skills/test-skill/SKILL.md with different content
   # Invoke via Skill tool
   # Verify which one loads
   ```
2. Add environment variable support to `generate-prompt.py`:
   ```python
   CLAUDE_SKILLS_PATHS = os.getenv('CLAUDE_SKILLS_PATHS', '').split(':')
   # Fallback: ['./.claude/skills', '~/.claude/skills']
   # Precedence: left-to-right (project wins)
   ```
3. Document precedence in CLAUDE.md + SKILLS_INDEX.md

---

### 2. EVOLUTION DIVERGENCE RISK

**Probability:** MEDIUM (60%)
**Impact:** HIGH (multiple projects affected)
**Severity:** HIGH

#### Current State
- Skill Evolution (skill-evolution/SKILL.md) allows self-modification after execution
- Changes are written directly to skill file
- Skill Conductor (Mode 4 REVIEW) validates changes before apply
- No project-specific exemptions or overrides

#### Risk: One Project's Change Breaks Others
**Example Scenario:**
- LeadQualifier Bot uses qa-validation-loop
- Gets updated to check Python logging (via skill evolution)
- Legal Bot runs same skill but it's Node.js code
- Evolved skill fails on Legal Bot because Python logging doesn't exist

#### Risk: Skill Divergence Over Time
- If projects can override globally-evolved skills, over time you get:
  - `~/.claude/skills/qa-validation-loop/SKILL.md` (base)
  - `./Bots/LeadQualifier/.claude/skills/qa-validation-loop/SKILL.md` (custom)
  - `./Bots/Legal/.claude/skills/qa-validation-loop/SKILL.md` (custom)
- **Problem:** Skill Conductor can't validate all variants simultaneously

#### Risk: Evolution Log Becomes Unmaintainable
- skill-evolution logs changes to skill's reference.md
- If same skill is evolved by 3 different projects, which reference.md wins?
- Git merges on shared skill files become impossible

#### Mitigation
1. **Lock skills from evolution** — only core/stable skills go global
   - Define "core skills" (14 skills currently exist)
   - Lock from skill evolution: document in skill frontmatter `evolution: locked`
   - Implement `generate-prompt.py` check: warn if locked skill is used

2. **Project-specific skill variants** — keep override pattern
   - Project skill overrides global skill
   - Override retains its own evolution log
   - Document in skill frontmatter `extends: {global-skill-name}`

3. **Skill Conductor Mode 5 OPTIMIZE** — runs per-project
   - Don't optimize global skills once evolved by a project
   - Run optimization BEFORE global migration (one-time cost)

---

### 3. TEMPLATE SYNC CONFUSION RISK

**Probability:** MEDIUM (70%)
**Impact:** MEDIUM (new projects only)
**Severity:** MEDIUM

#### Current State
- `/init-project` command uses template skills from `~/.claude/shared/templates/new-project/.claude/skills/`
- New-project template is synced from main template via bot-fleet
- 18 bot projects + 1 new-project template = 19 skill copies to manage

#### Risk: Init-Project Becomes Stale
**Scenario:**
- Global skills are updated
- New-project template skills NOT updated (template sync breaks)
- New `/init-project` runs with old template skills
- New bot projects have outdated skills for 6 months

#### Risk: Template Divergence
- If global skills + template skills both exist:
  - Do init commands use global or template? (undefined)
  - If global, then template skills become orphaned (waste)
  - If template, then new bots don't benefit from global evolution

#### Risk: init-project Script Ambiguity
- `/init-project` may hardcode template skills path
- Or it may dynamically discover from ~/.claude/ (if supported)
- Without clarification, migration creates hidden bugs

#### Mitigation
1. **Define init-project skill source** — document before migration
   - Option A: Template skills (current, must sync)
   - Option B: Global skills (new, no sync needed)
   - Option C: Template → copies to project (hybrid)

2. **If choosing global:** Delete template skills
   - Remove: `.claude/shared/templates/new-project/.claude/skills/`
   - Update init-project to verify global skills exist
   - Document in CLAUDE.md: "Skills are now global only"

3. **Template sync automation** — if keeping template
   - Add bot-fleet job: sync global skills → template skills
   - Run post-skill-evolution (so template picks up improvements)

---

### 4. AGENT MEMORY + SKILLS COUPLING RISK

**Probability:** MEDIUM (50%)
**Impact:** HIGH (subtle breakage)
**Severity:** HIGH

#### Current State
- Agent memory is project-level: `.claude/agent-memory/{type}/MEMORY.md`
- Skills are project-level: `.claude/skills/{name}/SKILL.md`
- When skill evolves, it writes to `.claude/skills/{name}/reference.md`
- Agent can read both memory and skill files from project

#### Risk: Memory-Skill Isolation Violation
**Example:**
- coder agent memory (`./.claude/agent-memory/coder/MEMORY.md`) contains:
  - "When to use verification-before-completion skill"
  - "Common mistakes I make with this skill"

- Skill is moved to `~/.claude/skills/verification-before-completion/`
- Agent memory still references local path
- Cross-session, agent memory becomes orphaned reference (link rot)

#### Risk: Skill Evolution Writes Wrong Path
- Skill evolution script (skill-evolution/SKILL.md) writes logs to:
  ```
  skills/{skill-name}/reference.md — evolution log
  skills/{skill-name}/MEMORY.md — skill-level patterns
  ```
- If skills are global, evolution writes to `~/.claude/skills/`
- But agent memory is in `./Bots/{name}/.claude/agent-memory/`
- **Coupling is broken:** skill evolution can't see agent memory, and vice versa

#### Risk: Graphiti Memory Coupling
- Graphiti saves facts as: `"skill: verification-before-completion (path: .claude/skills/...)"
- If global, paths become `~/.claude/skills/...` for all projects
- Graphiti queries can't disambiguate which project's usage

#### Mitigation
1. **Keep agent memory project-local** — NO change
   - Agent memory stays in `.claude/agent-memory/`
   - Skills go global, but agent memory references are versioned docs (not symlinks)

2. **Skill evolution writes to project** — hybrid approach
   - Skill (global): `~/.claude/skills/{name}/SKILL.md` (immutable after evolution)
   - Evolution log: `./.claude/skills/{name}/REFERENCE-EVOLVED.md` (project-local)
   - agent memory: `./.claude/agent-memory/{type}/MEMORY.md` (project-local)
   - Decouple paths from actual locations

3. **Graphiti qualification** — tag skill source
   - Save fact as: `"skill: verification-before-completion (source: global, projects: [proj1, proj2])"`
   - Queries now know which projects use global vs. local

---

### 5. ROLLBACK & REVERSAL RISK

**Probability:** HIGH (85% — if proceeding, you WILL need rollback)
**Impact:** MEDIUM
**Severity:** MEDIUM

#### Current State
- Project skills are in git (tracked, versioned)
- Global skills would be untracked (outside project repos)
- No backup strategy defined

#### Risk: Untracked Global Skills Disappear
**Scenario:**
1. Migrate skills to `~/.claude/skills/` (untracked)
2. Accidentally `rm -rf ~/.claude/`
3. Skills are gone. All 11 projects are broken. No git history to recover from.

#### Risk: Partial Migration Breaks Everything
**Scenario:**
1. Move 12 of 18 skills to global
2. generate-prompt.py tries to load all 18
3. 6 missing global skills cause script errors
4. All agent spawning fails
5. Can't easily rollback because you forgot which 6 are still local

#### Mitigation
1. **Backup strategy before migration:**
   ```bash
   # Before moving any skills
   tar -czf ~/.claude/skills-backup-$(date +%Y%m%d).tar.gz ~/.claude/skills/
   git -C "C:\Bots\Migrator bots\claude-project-template-update" commit -m "Pre-migration skills snapshot"
   ```

2. **Atomic migration with checklist:**
   - Create `work/MIGRATION_SKILLS.md` with skill-by-skill checklist
   - Move 1 skill, test all 11 projects
   - Verify scripts still work
   - Only move next skill after verification

3. **Keep project skills as backups (post-migration):**
   - Don't delete `.claude/skills/` from projects immediately
   - Run scripts against projects for 2 weeks in dual-read mode
   - Once verified, THEN delete project copies

---

### 6. MULTI-USER & PERMISSIONS RISK

**Probability:** MEDIUM (40% — depends on machine usage)
**Impact:** MEDIUM
**Severity:** MEDIUM

#### Current State
- User is single account on Windows 11
- But future team members may use same machine
- Global skills would affect ALL users

#### Risk: User A Breaks Skills for User B
**Scenario:**
1. User A migrates skills to `~/.claude/skills/`
2. User A runs skill evolution, changes qa-validation-loop
3. User B clones a bot project, runs `/init-project`
4. User B gets User A's modified qa-validation-loop
5. User B's project fails because the evolved skill doesn't match User B's stack

#### Risk: Permission Conflicts
- If User A creates `~/.claude/skills/` with restrictive permissions
- User B can't write skill evolution logs
- Scripts fail with permission denied

#### Mitigation
1. **Document multi-user constraints** — if applicable
   - IF single-user machine: no risk
   - IF multi-user machine: skills must be per-user, NOT global

2. **Establish skill governance policy:**
   - Who can evolve global skills?
   - How do you prevent User A from breaking User B?
   - Answer: Don't use global skills for multi-user setups

3. **Alternative: User-local skills** (if needed later)
   - Global path: `~/.claude/skills/` for single user
   - Team path: `~/team-shared/.claude/skills/` for shared machine
   - Project path: `./.claude/skills/` for project-specific overrides
   - Precedence: project > team > global

---

## Technical Dependency Analysis

### Scripts That Must Be Updated (if proceeding)

1. **generate-prompt.py** (126 lines)
   - Line 214: `skills_dir = root / '.claude' / 'skills'` ← hardcoded
   - Must add: global fallback with precedence
   - Estimated: +40 lines

2. **spawn-agent.py** (112 lines)
   - Imports generate-prompt.py
   - No changes needed (imports handle it)
   - Estimated: 0 lines

3. **ao-hybrid.sh** (scripts/ao-hybrid spawn)
   - May hardcode `./.claude/skills/` in prompts
   - Estimated: ~5 lines to update

4. **CLAUDE.md (project + global)**
   - Must document precedence rules
   - Must update memory decay path references
   - Estimated: +20 lines in CLAUDE.md

5. **.lsp.json (if skills affect LSP)**
   - Unlikely, but verify

### Files That Become Redundant (if proceeding)

- `.claude/shared/templates/new-project/.claude/skills/*` — 18 skill directories
- Bot project `./.claude/skills/*` — 11 projects × 18 skills = 198 directories
- **Total:** 216 redundant directories, ~2.3 MB of disk space (not critical)

### Files That Break (definite, if precedence not implemented)

- **ALL:** `.claude/scripts/generate-prompt.py` (can't find skills)
- **ALL:** `/init-project` command (if it uses template skills)
- **ALL:** Teammate prompts that invoke skills (Skill tool fails)
- **ALL:** Agent memory references to local skill paths

---

## GO/NO-GO Criteria

### BLOCKING GATE 1: Skill Loading Verification
- [ ] Test Skill tool with global path on a test project
- [ ] Document precedence behavior (global vs. project)
- [ ] If "unknown/unsupported" → **NO-GO**

### BLOCKING GATE 2: Script Updates & Testing
- [ ] Update generate-prompt.py with precedence logic
- [ ] Update CLAUDE.md with precedence rules
- [ ] Test on all 11 bot projects (or at least 3 representative ones)
- [ ] If any project has errors → **NO-GO**

### BLOCKING GATE 3: Agent Memory Decoupling
- [ ] Verify agent memory still loads correctly with global skills
- [ ] Update agent memory references (if hardcoded paths)
- [ ] Verify skill evolution writes to correct location
- [ ] If any memory/skill coupling breaks → **NO-GO**

### BLOCKING GATE 4: Rollback Strategy
- [ ] Create backup of all skills (pre-migration)
- [ ] Define rollback procedure in work/MIGRATION_SKILLS.md
- [ ] If rollback takes >30 min → **RETHINK**

### BLOCKING GATE 5: Acceptance Criteria
- [ ] Zero "skill not found" errors across all projects
- [ ] Agent spawning works for all 24 agent types
- [ ] Skill evolution still works (with proper logging)
- [ ] `/init-project` creates new bot with correct skills
- [ ] If any criterion fails → **NO-GO**

---

## Alternative Strategies (Lower Risk)

### Option A: Hybrid Model (RECOMMENDED)
**Cost:** 40-60 lines of code, 2-3 hours
**Risk:** LOW
**Benefits:** Keeps benefits of global skills, avoids breaking changes

```
Structure:
  ~/.claude/skills/                     (core/stable skills only)
  ./.claude/skills/                     (project overrides + local skills)

Precedence: project > global (project always wins)

Scripts:
  generate-prompt.py:
    - Try project skills first
    - Fall back to global
    - Error if not found in either

Agent Memory:
  - Stays project-local
  - References can be unversioned (e.g., "verification-before-completion skill")
  - Decoupled from actual file paths

Evolution:
  - Only global "locked" skills get evolved
  - Project overrides are immutable (no evolution)
```

### Option B: Project-Local Skills (CURRENT, NO CHANGE)
**Cost:** 0 lines of code
**Risk:** ZERO
**Benefits:** Zero disruption, everything works

```
Keep all skills in ./.claude/skills/ per project
Sync via template + bot-fleet as-is
No global state, no coupling issues
Trade-off: 216 redundant directories (not a problem)
```

### Option C: Centralized Skill Registry (FUTURE)
**Cost:** 200+ lines of code, 1-2 weeks
**Risk:** MEDIUM (requires major refactoring)
**Benefits:** True single source of truth, no duplication

```
Design:
  Central skill repo: github.com/user/skills
  Local cache: ~/.claude/skills/ (downloaded)

  generate-prompt.py:
    1. Check cache (~/.claude/skills/)
    2. If missing or stale, fetch from central repo
    3. Update cache, use local copy

Agent Evolution:
  - Evolves in central repo (PR-based, reviewed)
  - Cache is read-only to individual projects

This is long-term ideal but complex today.
```

---

## Recommendation

### PRIMARY: GO with Option A (Hybrid Model)

**Rationale:**
1. **Minimal disruption:** Only update generate-prompt.py
2. **Maximum safety:** Project overrides prevent cross-project breakage
3. **Preserves evolution:** Global locked skills can still improve
4. **Solves real problem:** Shared core skills across projects
5. **Reversible:** Easy to revert if issues arise

**Next Steps:**
1. Design precedence logic in detail
2. Update generate-prompt.py (40 lines)
3. Create work/MIGRATION_SKILLS.md with checklist
4. Test on 3 representative projects (template-update, LeadQualifier, Legal)
5. Gradually move stable skills to global (~2 skills/day)

### SECONDARY: ACCEPT Option B (Status Quo)

**If Option A proves too risky after initial testing:**
- Keep current project-local skill structure
- Focus on other scaling improvements (agent memory, Graphiti, template sync)
- Revisit global skills after 6 months when Claude Code docs clarify

---

## Summary Table

| Risk | Probability | Impact | Mitigation | Gate | Decision |
|------|-------------|--------|-----------|------|----------|
| Skill loading broken | HIGH | CRITICAL | Precedence test | GATE 1 | BLOCK |
| Evolution divergence | MEDIUM | HIGH | Lock global skills | Impl | DESIGN |
| Template sync stale | MEDIUM | MEDIUM | Auto sync script | Impl | DESIGN |
| Memory/skill coupling | MEDIUM | HIGH | Decouple paths | Impl | DESIGN |
| Rollback catastrophic | HIGH | MEDIUM | Backup + checklist | GATE 4 | DESIGN |
| Multi-user conflicts | MEDIUM | MEDIUM | Policy + docs | N/A | DESIGN |

**Overall Status:** NO-GO for direct migration → **REDESIGN as Option A (Hybrid), then IMPLEMENT with gates**

---

## Appendix: Evidence Collection Needed

To make final GO/NO-GO decision, collect:

1. **Skill tool behavior test:**
   ```
   Test 1: Create ~/.claude/skills/test-skill/SKILL.md with role: [coder]
   Test 2: Create ./.claude/skills/test-skill/SKILL.md with role: [qa-reviewer]
   Test 3: Invoke Skill tool with "test-skill" from project
   Result: Which role loads? (identifies precedence)
   ```

2. **init-project examination:**
   ```bash
   grep -r "\.claude/skills\|shared/templates" C:\Bots\Migrator\ bots\claude-project-template-update\CLAUDE.md
   grep -r "skills" C:\Bots\Migrator\ bots\claude-project-template-update\.claude\commands\init-project.md
   # Determine: Does init-project use template or dynamic discovery?
   ```

3. **Agent memory reference audit:**
   ```bash
   grep -r "\.claude/skills" C:\Bots\Migrator\ bots\claude-project-template-update\.claude\agent-memory\
   # Any hardcoded skill paths? If yes, must be updated.
   ```

---

**Assessment Complete**
Risk Assessor, AUTO_RESEARCH Phase
2026-03-17 16:45 UTC
