---
description: Run expert panel analysis for a task
allowed-tools:
  - Skill
  - Read
  - Glob
  - Grep
  - Task
  - TeamCreate
  - TeamDelete
  - TaskCreate
  - TaskUpdate
  - TaskList
  - TaskGet
  - SendMessage
  - Bash
  - Write
  - Edit
  - AskUserQuestion
---

# Expert Panel Analysis

Run multi-agent expert panel to analyze a task from multiple perspectives.

## Instructions

1. Load the expert panel skill and workflow:
   - `cat .claude/skills/expert-panel/SKILL.md`
   - `cat .claude/guides/expert-panel-workflow.md`
   - `cat .claude/guides/priority-ladder.md`

2. Take the user's task description: $ARGUMENTS

3. Execute **Phase 0 + Phase 1 only** (analysis, no implementation):
   - Domain Detection → select 3-5 expert roles
   - TeamCreate "expert-panel"
   - Spawn expert teammates (READ-ONLY analysis)
   - Collect analyses, resolve conflicts via Priority Ladder
   - Write `work/expert-analysis.md`
   - Shutdown panel team

4. Present results to user with:
   - Consensus recommendations
   - Risk assessment
   - Trade-off matrix
   - Open questions

**NOTE:** This command runs analysis only. Implementation is a separate step.
If user wants full Agent Teams Mode (analysis + implementation), they should say "используй Agent Teams Mode" instead.
