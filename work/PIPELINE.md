# Pipeline: Codex CLI Integration as Cross-Model Verifier

**Status:** IN_PROGRESS
**Created:** 2026-03-30
**Goal:** Integrate Codex CLI as additional validator/verifier alongside Claude Code in our development system

---

## Phase 1: RESEARCH ✅ COMPLETE
**Gate:** 4 research files analyzed, integration patterns identified
**Result:** Read all 4 files from /home/admin/files/. Key patterns: codex exec (shell-based, most reliable), Stop hook, SKILL.md, structured JSON output, AGENTS.md shared context.

## Phase 2: PLAN ✅ COMPLETE
**Gate:** Implementation plan with file list approved

### Artifacts to Create/Modify:

**NEW files:**
1. `.claude/guides/codex-integration.md` — comprehensive guide for Codex integration
2. `.claude/shared/templates/new-project/.claude/skills/cross-model-review/SKILL.md` — skill for invoking Codex verification
3. `.codex/review-schema.json` — JSON schema for structured Codex output
4. `.claude/hooks/codex-review.sh` — hook script for auto-running Codex review on Stop
5. `.claude/shared/templates/new-project/AGENTS.md` — shared agent instructions template

**MODIFIED files:**
6. `.claude/settings.json` — add Stop hook for Codex review
7. `~/.claude/CLAUDE.md` — add Codex integration rules
8. `.claude/guides/teammate-prompt-template.md` — add Codex verification step
9. `.claude/shared/templates/new-project/.claude/skills/qa-validation-loop/SKILL.md` — add Codex cross-review step
10. `.claude/shared/templates/new-project/.claude/skills/verification-before-completion/SKILL.md` — add Codex check
11. `.claude/skills/INDEX.md` — add cross-model-review skill entry

## Phase 3: IMPLEMENT <- CURRENT
**Mode:** AGENT_TEAMS (4 parallel tasks + 1 sequential)
**Gate:** All files created/modified, no conflicts

### Task Breakdown:
- T1: Create codex-integration.md guide + review-schema.json + codex-review.sh hook + AGENTS.md template
- T2: Create cross-model-review SKILL.md + update INDEX.md
- T3: Update qa-validation-loop + verification-before-completion skills
- T4: Update settings.json + CLAUDE.md (global) + teammate-prompt-template.md
- T5: Verify all changes + final consistency check (BLOCKED by T1-T4)

## Phase 4: COMPLETE
**Gate:** activeContext.md updated, commit made
