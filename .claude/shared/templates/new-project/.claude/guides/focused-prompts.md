# Focused Prompts Guide

> Why focused prompts beat mega-prompts, and how to use each one.
> Loaded via: `cat .claude/guides/focused-prompts.md`

---

## 1. Why Focused Prompts

A single mega-prompt that tries to cover planning, coding, reviewing, and fixing leads to:
- **Token waste**: 80% of instructions are irrelevant to the current role
- **Attention dilution**: the model pays equal attention to all instructions, reducing focus
- **Role confusion**: agents try to plan AND code AND review simultaneously
- **Compaction loss**: long prompts lose critical details when context is compressed

Focused prompts solve this by giving each agent ONLY the instructions it needs. A coder does not need QA review phases. A reviewer does not need implementation rules. Result: sharper focus, lower token cost, better output.

---

## 2. Available Prompts

| File | Role | When to Use | Lines |
|------|------|-------------|-------|
| `planner.md` | Planning Agent | Before implementation: decompose task into waves | ~150 |
| `coder.md` | Implementation Agent | Per subtask: implement, test, verify | ~120 |
| `qa-reviewer.md` | QA Review Agent | After implementation: review against criteria | ~150 |
| `qa-fixer.md` | QA Fix Agent | After review: fix CRITICAL/IMPORTANT issues | ~80 |
| `insight-extractor.md` | Insight Agent | Post-session: extract patterns and gotchas | ~80 |

---

## 3. How Prompts Integrate with Agent Teams

When spawning teammates, the prompt file becomes part of the teammate's instructions:

```
1. Select the right prompt for the agent's role
2. Read the prompt file content
3. Prepend task-specific context (files, acceptance criteria)
4. Append memory injection (patterns, gotchas relevant to this task)
5. Include the Required Skills section (per teammate-prompt-template.md)
6. Spawn the agent with the assembled prompt
```

The teammate-prompt-template.md remains the STRUCTURAL template (Required Skills, Verification Rules, Acceptance Criteria). The focused prompt provides the BEHAVIORAL instructions (how to do the work).

---

## 4. Prompt Assembly Flow

```
+---------------------------+
| teammate-prompt-template  |  <- Structure (identity, skills, constraints)
+---------------------------+
            |
            v
+---------------------------+
| focused prompt (role)     |  <- Behavior (phases, steps, rules)
+---------------------------+
            |
            v
+---------------------------+
| task-specific context     |  <- Data (files, criteria, commands)
+---------------------------+
            |
            v
+---------------------------+
| memory injection          |  <- History (patterns, gotchas, recent context)
+---------------------------+
            |
            v
+---------------------------+
| FINAL ASSEMBLED PROMPT    |  -> Sent to agent
+---------------------------+
```

### Memory Injection

Before spawning an agent, check:
- `.claude/memory/activeContext.md` -- extract recent context
- `.claude/memory/knowledge.md` -- find patterns and gotchas matching files in the task

Prepend relevant entries to the prompt:
```
## Relevant Patterns
- Repository pattern: all DB queries through repos/ (from knowledge.md)

## Known Gotchas
- Async sessions must use context manager (from knowledge.md)

## Recent Context
- Auth module refactored yesterday, imports changed (from activeContext.md)
```

Only inject entries that match the agent's task scope. Do NOT dump all memory.

---

## 5. Pipeline Integration

In a PIPELINE.md execution:

| Phase | Prompt Used | Agent Mode |
|-------|-------------|------------|
| PLAN | `planner.md` | SOLO or Agent Chain (Spec Chain) |
| IMPLEMENT | `coder.md` | AGENT_TEAMS (one per subtask) |
| QA_REVIEW | `qa-reviewer.md` + `qa-fixer.md` | Agent Chain (QA Chain) |
| TEST | (no prompt -- direct test execution) | SOLO |
| FIX | `coder.md` + `qa-reviewer.md` | Agent Chain (Debug Chain) |
| POST-SESSION | `insight-extractor.md` | SOLO |

---

## 6. Creating Custom Prompts

To add a new role-specific prompt:

1. Create `.claude/prompts/{role-name}.md`
2. Follow this structure:
   ```markdown
   # {Role Name} Prompt
   > One-line description. Model: Opus 4.6 (claude-opus-4-6)

   ## Identity
   You are a {Role} Agent powered by Opus 4.6. Your SOLE job is to {one sentence}.

   ## Step/Phase N: {name}
   {instructions}

   ## Rules
   {hard constraints for this role}
   ```
3. Add the prompt to the table in Section 2 of this guide
4. Keep prompts under 200 lines (the whole point is focus)
5. Include a Rules section at the end with hard constraints

### Prompt Quality Checklist
- [ ] Single clear identity statement
- [ ] Numbered phases/steps (not walls of text)
- [ ] Concrete output format specified
- [ ] Rules section with hard constraints
- [ ] Under 200 lines
- [ ] References Opus 4.6 (claude-opus-4-6) as the model

---

## 7. Anti-Patterns

| Anti-Pattern | Why It Fails | Instead Do |
|---|---|---|
| One mega-prompt for all roles | Attention dilution, token waste | Use role-specific focused prompt |
| Copying entire prompt into every agent | Defeats the purpose of focus | Assemble: template + prompt + context |
| Injecting all memory into every agent | Irrelevant context competes for attention | Only inject memory matching task scope |
| Prompts over 300 lines | Back to mega-prompt territory | Split into prompt + reference guide |
| No Rules section | Agent invents its own boundaries | Always end with explicit constraints |
| Mixing implementation + review in one prompt | Role confusion, self-review bias | Separate coder and reviewer agents |
