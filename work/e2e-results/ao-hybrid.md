# E2E Test: AO Hybrid Agents with Autonomous Skill Discovery

**Date:** 2026-02-27
**Phase:** TEST_AO_HYBRID
**Result:** PASS (with CONCERNS)

## Test Design

2 AO Hybrid agents spawned via `ao spawn --prompt-file`, each as a full Claude Code session:

| Agent | Session ID | Branch | Task |
|-------|-----------|--------|------|
| ao-verify-sync | template-1 | session/template-1 | Compare project vs template skills |
| ao-analyze-triggers | template-2 | feat/ao-task-2-skill-trigger-coverage | Analyze CLAUDE.md skill trigger coverage |

## Results

### AO Agent 1: Template Sync Verifier — PASS (with CONCERNS)
- **Worktree:** `C:/Users/Lenovo/.worktrees/claude-project-template-update/template-1`
- **Base commit:** `6356fcf` (NOT current HEAD — stale branch reuse, see Concerns)
- **Output:** `work/e2e-results/ao-agent-1.md` — 102-line sync comparison report
- **Git commit:** `6bb50ca chore: add template-to-project skills sync audit report`
- **Key finding:** Reported FAIL (project vs template mismatch) — but this was caused by stale worktree base. The agent's worktree was based on commit `6356fcf` (before skills restoration), so it correctly found the template stubs didn't match full project skills.
- **CONCERN:** Mixed up project-level skills (13) with global skills (34 total seen). The agent scanned `~/.claude/skills/` as well as `.claude/skills/`.
- **AO mechanism proof:** Agent started, read CLAUDE.md, executed task, wrote results, made commit — full lifecycle.

### AO Agent 2: Trigger Coverage Analyzer — PASS
- **Worktree:** `C:/Users/Lenovo/.worktrees/claude-project-template-update/template-2`
- **Base commit:** `855636e` (current master HEAD — correct)
- **Output:** `work/e2e-results/ao-agent-2.md` — 192-line coverage analysis
- **Git commit:** `4982aea feat: analyze CLAUDE.md skill trigger coverage`
- **Key findings:**
  - CLAUDE.md references 2 skills directly (both valid)
  - SKILLS_INDEX.md has 24 entry points, 19/24 exist (79% coverage)
  - 13 "phantom skills" referenced but don't have SKILL.md in project (global skills)
  - 15 skills without entry point triggers (discoverable via categories only)
  - 100% description alignment for existing skills
- **AO mechanism proof:** Agent started, read CLAUDE.md, analyzed SKILLS_INDEX.md, executed full 7-section analysis, wrote results, made commit.

## Gate Verdict

| Criterion | Status | Evidence |
|-----------|--------|---------|
| 2 AO agents complete | PASS | Both wrote results and made commits |
| Evidence of autonomous skill invocation | CONCERNS | No direct Skill tool invocation logs visible. Agents followed patterns consistent with verification and codebase-mapping skills, but we cannot confirm Skill tool was called from worktree logs alone |
| AO Hybrid spawn mechanism works | PASS | `ao spawn --prompt-file` created sessions, sessions worked in isolated worktrees, produced git commits, terminated cleanly |

## Concerns

### 1. Stale worktree base (template-1)
- Branch `session/template-1` already existed from a previous AO session
- The AO system reused this branch instead of creating a fresh one from HEAD
- Result: agent worked on code from commit `6356fcf` (before skills restoration), not `855636e`
- **Mitigation:** Always use unique session/branch names, or delete old branches before spawning

### 2. No direct skill invocation proof
- AO agents are full Claude Code sessions with Skill tool access
- Both agents produced structured outputs consistent with skill protocols
- However, we cannot confirm they explicitly called `Skill tool` vs just following CLAUDE.md rules
- **Root cause:** AO agent tool call logs are not accessible from the lead agent
- **Mitigation:** Future tests should include "Report which skills you invoked" in the prompt

### 3. Global vs project skill confusion (template-1)
- Agent 1 saw 34 skills (including 27 global) instead of 13 project skills
- The `.claude/skills/` path resolves differently inside worktrees
- **Mitigation:** Specify absolute paths in prompts when comparing directories

## AO Lifecycle Evidence

| Phase | template-1 | template-2 |
|-------|-----------|-----------|
| Spawn | `ao spawn` + `--prompt-file` | Same |
| Session status | `[spawning]` → `[running]` → `[killed]` | Same |
| Worktree isolation | Own branch, own directory | Same |
| CLAUDE.md read | Yes (references in output) | Yes (detailed analysis) |
| Output file | `ao-agent-1.md` (102 lines) | `ao-agent-2.md` (192 lines) |
| Git commit | `6bb50ca` | `4982aea` |
| Completion | 150s | 240s |

## Valuable Side-Findings from Agent 2

Agent 2's analysis surfaced real issues in the skills infrastructure:
1. **13 phantom skills** in SKILLS_INDEX.md (referenced but missing from project — they're global-level)
2. **15 orphaned skills** with no entry point triggers
3. **SKILLS_INDEX skill count inflated** (claims 47, only 34 have SKILL.md)
4. These findings can be addressed as follow-up improvements

## Artifacts

- `work/e2e-results/ao-agent-1.md` — Template sync comparison (102 lines)
- `work/e2e-results/ao-agent-2.md` — Trigger coverage analysis (192 lines)
- Worktree branches: `session/template-1`, `feat/ao-task-2-skill-trigger-coverage`
