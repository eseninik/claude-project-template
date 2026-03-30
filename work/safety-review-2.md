# Safety Review: self-completion Skill

**Reviewer:** Independent safety analysis
**Date:** 2026-03-11
**File reviewed:** `.claude/skills/self-completion/SKILL.md`
**VERDICT: SAFE (with caveats)**

---

## Scenario 1: Token Drain (Context Overshoot)

**Question:** Agent in unlimited mode. Context pressure check is at 75%, but context fills between checks. Could it overshoot to 90%+?

**Analysis:**
- The context pressure check runs at step 3 of every iteration — meaning it fires once per loop cycle, before each new task execution (step 5).
- The question is whether a single task execution (one iteration from step 3 to step 3) can consume enough context to jump from 74% to 90%+. That would require ~16% of context in a single iteration.
- For a 200K-token context window, 16% is ~32K tokens. A single task execution involving multiple tool calls, large file reads, or verbose reasoning could plausibly hit this — but it would be an unusually heavy iteration.
- More realistically, a single iteration consumes 2-8K tokens (tool calls + reasoning + output). This means overshoot would typically land at 77-83%, not 90%+.
- The skill also has a separate warning at 70% (line 219: "At 70%: stop self-completion"), which acts as an earlier tripwire in the non-unlimited path. However, in unlimited mode this early warning is NOT referenced — only the 75% valve applies.

**Risk:** LOW
**Verdict:** Overshoot to 90%+ from a single iteration is theoretically possible but unlikely in practice. The per-iteration check is frequent enough. The real risk is a task that triggers a very large file read (e.g., reading a 30K-token file), but even then the check fires before the NEXT iteration starts.

**Recommendation:** Consider adding an intra-iteration check after step 5 (Execute task) as a secondary guard, especially for unlimited mode. This would catch cases where a single heavy task consumes significant context.

---

## Scenario 2: Infinite Cost (12-Hour Session)

**Question:** Agent runs for the maximum configurable wall-clock timeout (12 hours). What is the estimated token cost?

**Analysis:**
- Default wall-clock timeout is 4 hours (line 143), configurable up to 12 hours.
- Conservative estimate per iteration: ~5K tokens (tool calls + reasoning + task execution).
- Iteration throughput depends on task complexity. Simple tasks: ~1-2 minutes/iteration. Complex tasks with builds/tests: ~5-10 minutes.
- At 12 hours with fast iterations (~5 min each): 144 iterations x 5K = **~720K tokens**.
- At 12 hours with slow iterations (~10 min each): 72 iterations x 5K = **~360K tokens**.
- At Opus pricing (~$15/M input, ~$75/M output), worst case: ~$10-55 depending on input/output ratio.
- However, the context pressure valve (75%) will almost certainly trigger before 12 hours elapse, since 144 iterations x 5K tokens = 720K tokens would overflow a 200K context window many times over. The agent would need to be doing very lightweight iterations (sub-1K tokens each) to survive 12 hours on context alone.
- In practice, context pressure will stop the loop well before the 12-hour timeout fires.

**Risk:** LOW
**Verdict:** The 12-hour timeout is a backstop, not the primary control. Context pressure (75%) is the practical limiter. A realistic unlimited session will run 40-80 iterations before context pressure triggers, costing roughly 200-400K tokens (~$3-30). This is acceptable for a feature explicitly opted into with `unlimited`.

**Recommendation:** Document estimated cost ranges in the skill file or in a user-facing guide so operators can make informed decisions before enabling unlimited mode.

---

## Scenario 3: Zombie Loop (Idle Detection Bypass)

**Question:** Agent claims it changed files but actually didn't. Can it bypass idle detection?

**Analysis:**
- The idle detection valve checks for "3 consecutive iterations with 0 file changes" (line 146).
- The skill does not specify HOW file changes are detected. If it relies on the agent's self-report ("I changed files"), then yes — the agent could trivially claim changes it didn't make.
- If it checks actual filesystem state (e.g., `git diff --stat`, file modification timestamps), then bypassing is harder but not impossible: the agent could write a trivial comment to a file and remove it in the next iteration. Each iteration would show a file change, defeating idle detection.
- The more realistic concern is an agent that makes REAL but USELESS changes — reformatting, adding/removing whitespace, rewriting comments. This would bypass idle detection while producing no meaningful progress.
- The checkpoint valve (every 10 iterations) partially mitigates this by forcing a progress self-assessment, but a hallucinating agent could also produce a convincing checkpoint report.

**Risk:** MEDIUM
**Verdict:** Idle detection is a heuristic, not a guarantee. A malfunctioning or hallucinating agent could bypass it through trivial file modifications. The checkpoint interval provides a secondary check, but both rely on agent self-assessment, which is the root vulnerability.

**Recommendation:**
1. Define idle detection as filesystem-based (git diff or mtime), not self-reported.
2. Consider adding a "meaningful change" heuristic — e.g., changes must exceed N lines or N bytes delta.
3. The checkpoint log should include a diff summary (files changed + line counts) for human review.

---

## Scenario 4: Checkpoint Bypass

**Question:** Agent at iteration 9 (checkpoint at 10). Could it skip the checkpoint?

**Analysis:**
- The check is `iteration_count % checkpoint_interval == 0 AND iteration_count > 0` (line 51).
- At iteration 9: `9 % 10 == 9`, which is non-zero. The check does not fire.
- At iteration 10: `10 % 10 == 0 AND 10 > 0` — both conditions true. Checkpoint fires.
- The iteration counter is incremented in step 6 ("increment count"). The check happens in step 3 of the NEXT iteration. So there is no gap where the counter increments but the check is skipped.
- The only theoretical bypass: if the agent crashes or the session ends between iterations 9 and 10. But this is a session failure, not a checkpoint bypass — and the state preservation mechanism (lines 159-184) handles graceful stops.

**Risk:** LOW
**Verdict:** SAFE. The modular arithmetic is correct and the check cannot be skipped during normal operation. The counter and check are in the same loop, with no path that skips step 3.

**Recommendation:** None needed. The design is sound.

---

## Scenario 5: Configuration Manipulation

**Question:** Could the agent modify the config to disable safety valves?

**Analysis:**
- Configuration values (context_threshold, wall_clock_timeout, idle_threshold, checkpoint_interval) are passed at invocation time via the `INVOKE` command (lines 192-198).
- These are parameters to the skill invocation, not values read from a mutable file. The agent cannot change them mid-execution by editing a file.
- However, there is a subtlety: the skill is a PROMPT, not compiled code. The "algorithm" (lines 19-64) is instructions that the agent interprets and follows. A sufficiently creative agent could "reinterpret" the instructions or simply ignore a safety check.
- This is the fundamental limitation of prompt-based safety: the safety valves are advisory, not enforced by a runtime sandbox. The agent follows them because the instructions say to, not because it physically cannot skip them.
- In practice, Claude models follow explicit algorithmic instructions with high fidelity, especially when structured as pseudocode. The risk of deliberate circumvention is very low with current models.

**Risk:** LOW (but architecturally important)
**Verdict:** SAFE for practical purposes. The agent cannot edit config values at runtime because they are invocation parameters. The deeper question — "could the agent ignore the instructions entirely?" — is a general prompt-following concern, not specific to this skill.

**Recommendation:** For critical production use cases, consider implementing safety valves as external process monitors (e.g., a wrapper script that kills the session after N hours or N tokens) rather than relying solely on in-prompt instructions. This provides defense-in-depth at the system level.

---

## Summary

| Scenario | Risk | Verdict |
|----------|------|---------|
| 1. Token drain (context overshoot) | LOW | Per-iteration check is sufficient; overshoot to 90%+ is unlikely |
| 2. Infinite cost (12h session) | LOW | Context pressure triggers well before timeout; cost is bounded |
| 3. Zombie loop (idle bypass) | MEDIUM | Trivial file changes can defeat idle detection |
| 4. Checkpoint bypass | LOW | Modular arithmetic is correct; no skip path exists |
| 5. Configuration manipulation | LOW | Invocation-time params cannot be edited; prompt-following is reliable |

**Overall Verdict: SAFE**

The self-completion skill has a well-designed defense-in-depth safety architecture for unlimited mode. The five independent safety valves cover the major failure modes. The one area of meaningful concern is idle detection (Scenario 3), which can be defeated by trivial file modifications. This is a MEDIUM risk that could be mitigated by filesystem-based change detection with a minimum-delta threshold.

The most important architectural observation: all safety valves are prompt-level instructions, not runtime-enforced constraints. This is adequate for current use but should be noted as a limitation for high-stakes production scenarios.
