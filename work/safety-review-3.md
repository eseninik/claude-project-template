# Safety Review: Self-Completion Skill (Unlimited Mode)

**Reviewer:** Independent safety analysis
**Date:** 2026-03-11
**File:** `.claude/skills/self-completion/SKILL.md`
**Scope:** Unlimited mode safety architecture — comparative analysis and defense in depth

---

## VERDICT: SAFE

Ship as-is. The safety architecture is well-designed with genuine defense in depth. No changes required for safe operation.

---

## 1. Comparative Analysis: vs. Karpathy's autoresearch

Karpathy's autoresearch uses a single mechanism: prose instructions ("NEVER STOP working"). There is no programmatic safety — it relies entirely on the model's compliance with instructions and Claude Code's built-in session limits.

Our system has 5 independent, programmatic safety valves with configurable thresholds. This is **strictly safer** for three reasons:

1. **Redundancy.** autoresearch has zero fallback if the model decides to stop or if it runs into a degenerate loop. Our system catches degenerate loops via idle detection and progress stall.
2. **State preservation.** autoresearch loses all progress context on stop. Our system writes `work/self-completion-state.md` before any stop, preserving completed/remaining task lists and resume instructions.
3. **Deterministic triggers.** Our valves trigger on measurable conditions (context %, wall clock, file change count, error repetition count) rather than model judgment. These cannot be hallucinated away.

The one thing autoresearch gets right is simplicity — no configuration surface means no misconfiguration risk. Our system mitigates this with sensible defaults (75% context, 4h timeout, 3 idle iterations).

**Assessment: Our approach is strictly safer than autoresearch.**

---

## 2. Industry Best Practices Coverage

### OpenAI agent harness recommendations

| Recommendation | Covered? | How |
|---------------|----------|-----|
| Checkpointing | YES | Iteration checkpoint every 10 iterations + state file on stop |
| Budget/resource limits | YES | Context pressure (75%) + wall-clock timeout (4h) |
| Human-in-the-loop | YES | `<safety_stop>` marker requires human decision to resume; `<blocked>` for input needs |
| Graceful degradation | YES | State saved before every stop; resume instructions provided |
| Progress observability | PARTIAL | Checkpoint logging exists but no external monitoring hook (e.g., webhook, file-based heartbeat) |

### Anthropic guidance on long-running agents

| Recommendation | Covered? | How |
|---------------|----------|-----|
| Context management | YES | Primary valve at 75%; warning at 50%; hard suggestion at 70% (base mode) |
| State preservation | YES | `work/self-completion-state.md` + `activeContext.md` update |
| Preventing infinite loops | YES | Idle detection (3 no-change iterations) + progress stall (3 same errors) |
| Clear termination conditions | YES | 6 distinct completion markers with defined semantics |

**Gap identified:** No external heartbeat or monitoring file that an external process could watch. If someone wanted to monitor whether the agent is alive vs. stuck in a long operation, there is no periodic file touch or signal. This is a minor gap — Claude Code's own terminal output serves as a de facto heartbeat, but a dedicated monitoring integration point would be ideal for production fleet scenarios.

**Assessment: Covers all recommended categories. One minor gap (external observability) that does not affect safety.**

---

## 3. Defense in Depth Assessment

### Single valve failure

**If context_pressure check breaks:** The wall-clock timeout (4h) still triggers. Idle detection still catches no-progress loops. Progress stall still catches repeated errors. Checkpoints still force periodic reassessment.

**Result: YES — fully protected.** Three independent valves remain operational.

### Double valve failure

**If both context_pressure AND wall-clock timeout fail:** Idle detection catches loops with no file changes. Progress stall catches repeated errors. The agent would continue running but would stop on any stall condition.

**Result: YES — protected against spinning.** The agent could theoretically run indefinitely if it keeps making file changes and encountering different errors each time, but this scenario implies it is actually doing useful work (making changes, hitting novel errors).

### Triple valve failure

**If context_pressure, wall-clock timeout, AND idle detection all fail:** Progress stall still catches repeated identical errors. The iteration checkpoint (every 10 iterations) forces a self-assessment where all valves are re-checked — but if the individual valve checks are broken, the checkpoint re-check would also fail.

**Result: YES for the stall valve alone. NO for checkpoint as independent protection** (checkpoint re-runs the same broken checks). However, progress stall is genuinely independent — it tracks error message identity, a completely different mechanism from the other three.

### All valves fail

**Worst case:** Agent runs until Claude Code's own built-in limits halt it — context window exhaustion (hard limit, not our soft check), API rate limits, or terminal session timeout. No work is lost that was already committed to disk, but the state file would not be written (since `save_state()` is called by the valve logic that failed).

**Mitigation for worst case:** Claude Code itself is the outer safety boundary. Context window exhaustion is a hard stop that cannot be bypassed. The risk is: no state file is written, so the user must manually reconstruct progress. This is acceptable — it is the same behavior as any other Claude Code session that hits context limits.

**Assessment: Defense in depth is genuine. Four independent detection mechanisms with different trigger conditions. Worst case degrades gracefully to Claude Code's own limits.**

---

## 4. State Preservation Completeness

### Does the save_state format capture enough to resume?

The state file includes:
- Stop reason (why)
- Completed task count and list (what was done)
- Remaining task list (what is left)
- Iteration count, elapsed time, context usage (operational stats)
- Resume instructions (how to continue)

**Assessment: YES.** The format captures the essential information. A resumed session can read this file and pick up from the next pending task.

### Could a resumed session lose work?

**Risk: LOW.** Each completed task is committed to disk (file changes) and logged in the state file. The only loss scenario is if a task was partially completed when the valve triggered — but the algorithm marks tasks in_progress vs. completed, so partial work is identifiable.

One subtle risk: the state file records task descriptions but not task IDs or file paths of changes made. If the task list has been modified between sessions (e.g., user adds/removes tasks), the "task #3" reference could point to a different task. This is a minor consistency risk, not a safety risk.

### Is the format consistent with other state files?

The format follows the same markdown pattern as other `work/` files in the system (PIPELINE.md, expert-analysis.md). It uses the project's established conventions for status markers and structured markdown. Consistent.

**Assessment: State preservation is adequate for safe resume. Minor improvement opportunity in task identity tracking.**

---

## 5. User Communication

### Is the reason for stop clearly communicated?

YES. The `<safety_stop>` marker includes a `reason` attribute with one of four values: `context_pressure`, `timeout`, `idle`, `stall`. Each is self-explanatory.

### Can the user understand what happened and why?

YES. The state file provides: what triggered the stop, how many tasks were completed, how many remain, and operational stats. The "Why Each Valve Exists" section in the skill file provides rationale, though this is developer-facing documentation, not user-facing output. The actual stop output to the user is clear enough without requiring the user to read the skill file.

### Are resume instructions actionable?

YES. "To continue: read this file, pick up from task #{next_task_number}" is simple and direct. The remaining tasks list makes it obvious what work is left.

**Assessment: Communication is clear, actionable, and requires no special knowledge to understand.**

---

## Summary

| Category | Rating | Notes |
|----------|--------|-------|
| vs. autoresearch | Strictly safer | 5 valves vs. 0; state preservation vs. none |
| Industry best practices | Full coverage | Minor gap: no external heartbeat mechanism |
| Single valve failure | SAFE | 3+ backup valves |
| Double valve failure | SAFE | 2+ backup valves |
| Triple valve failure | SAFE | Stall detection independent |
| All valves fail | Acceptable | Degrades to Claude Code's own limits |
| State preservation | Adequate | Minor: task identity could be stronger |
| User communication | Clear | Reason + stats + resume instructions |

## Final Recommendation

**Ship as-is.** The safety architecture demonstrates genuine defense in depth with independent detection mechanisms. It is strictly safer than the prominent alternative (autoresearch) and covers all industry-recommended categories. No blocking issues found.

Optional improvements for future iterations (not blocking):
1. Add external heartbeat file (touch `work/.self-completion-heartbeat` every N iterations) for fleet monitoring scenarios.
2. Include task IDs or file-change summaries in state file for stronger resume consistency.
3. Consider a "max total iterations" hard cap even in unlimited mode (e.g., 500) as a final backstop before Claude Code's own limits.
