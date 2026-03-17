# Auto-Research: Global Skills Migration

## Requirements (from Requirement Analyst)
- [x] Skill tool invokes skills from ~/.claude/skills/ — VERIFIED
- [x] Precedence: project .claude/skills/ > global ~/.claude/skills/ — VERIFIED
- [x] Sub-agents load ONLY from ~/.claude/skills/ (Issue #10061) — actually FAVORS global
- [x] Hot-reload supported for skill changes — VERIFIED via changelog
- [ ] Parent directory traversal for skills — NOT implemented (Issue #26489)

## Technical Analysis (from Feasibility Analyst)
- Complexity: MEDIUM
- **15 skills already exist in ~/.claude/skills/** (825KB) — global structure already works!
- 14 skills are truly shared across all projects
- Freelance has 2 unique skills: freelance-ai-copywriter, mcp-integration
- Call Rate bot missing 2 skills (skill-evolution, skill-conductor)
- Migration scope: ~3,750 lines, 9 bot projects to update

## Risk Assessment
| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Skill loading broken | LOW (already works, 15 skills in global) | CRITICAL | Test before removing project copies |
| Evolution divergence | MEDIUM | HIGH | Project override via local .claude/skills/ |
| Template sync stale | LOW | MEDIUM | Template keeps skills for init-project |
| Rollback | LOW | MEDIUM | Keep project copies as backup initially |

## GO/NO-GO
- [x] Requirements clear
- [x] Technical approach identified (Hybrid: global + project override)
- [x] No HIGH risks without mitigation
- [x] 15 skills already working globally — proof of concept exists

**Decision: GO — Hybrid Model**

## Approach
1. Verify 15 global skills match template (update if needed)
2. Remove duplicate skills from all bot projects
3. Keep project-specific skills (Freelance: freelance-ai-copywriter, mcp-integration)
4. Template keeps skills for init-project (new projects start with local copies)
5. Update CLAUDE.md in all projects to reference global skills
