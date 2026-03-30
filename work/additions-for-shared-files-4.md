# Additions for Shared Files — Results Board

## 1. For teammate-prompt-template.md

Add after "## Verification Rules (MANDATORY)" section, before "## Handoff Output":

```markdown
## Results Board
Before starting your task, check if `work/results-board.md` exists. If yes:
- Read it for context on what other agents have tried
- Note any failed approaches related to your task — do NOT repeat them
- After completing your task, append your result entry to the board
```

## 2. For CLAUDE.md CONTEXT LOADING TRIGGERS (Guides table)

Add row:

```
| Agent Teams coordination | `cat .claude/guides/results-board.md` |
```

## 3. For CLAUDE.md Agent Teams section

Add after "DO NOT do sequentially what can be parallelized.":

```
DO NOT skip reading work/results-board.md before starting — agents must learn from peers' results.
```
