# AO Hybrid Mode Reference

When `execution_engine: ao_hybrid` in config.yaml, or pipeline phase has `Mode: AO_HYBRID`:

1. Use `ao-hybrid-spawn` skill instead of TeamCreate
2. Each agent = full Claude Code session (CLAUDE.md, skills, hooks, memory)
3. Agents work in isolated git worktrees created by AO
4. Results collected via file reads + worktree merging

## Decision Tree

- Tasks need skills/memory/hooks -> AO Hybrid
- Simple context-light tasks -> TeamCreate (faster, lighter)
- 5+ concurrent agents -> AO Hybrid recommended (better isolation)

## Reference

Full AO Hybrid skill: `cat .claude/skills/ao-hybrid-spawn/SKILL.md`
