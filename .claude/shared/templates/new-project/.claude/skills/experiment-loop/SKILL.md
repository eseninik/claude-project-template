---
name: experiment-loop
description: >
  Autonomous experiment loop for iterative optimization with quantifiable metrics.
  Five stages (intake / triage / fitness / mode / loop+postmortem) refuse non-autoresearch-shaped problems before wasting iterations.
  Supports pure / barbell / via-negativa / inverted / human-in-loop modes.
  Use when task has a quantifiable success metric and needs iterative optimization, when user says
  "optimize", "find best", "experiment", "try variations", "autoresearch", "overnight agent",
  "Karpathy loop", or "iterate until better".
  Do NOT use for deterministic implementation tasks, bug fixes, one-shot changes, tasks without
  measurable metrics, or architecture/strategy questions (use expert-panel instead).
roles: [experimenter, pipeline-lead]
---

# Experiment Loop (autoresearch)

## Overview

Autonomous cycle for iterative optimization. Originally inspired by Karpathy's autoresearch pattern; extended with Bayram Annakov's triage / fitness / mode / plateau additions (MIT-licensed source, see attribution notes in reference files).

**Core principle:** Modify, measure, keep if better, discard if not. Repeat until budget exhausted, plateau detected, or guard violated.

**Hard-won lesson:** most candidate tasks are NOT autoresearch-shaped. Running the loop on a fat-tailed, reflexive, or slow-feedback problem converges to a local optimum of the wrong thing — efficiently. This skill's Stage 2 Triage catches that before the loop starts. Saying "this isn't autoresearch-shaped, here's why, here's what to do instead" is the correct output when a candidate fails triage.

## When to Use

- Task has a **quantifiable metric** (response rate, accuracy, performance, conversion, test pass rate)
- Multiple approaches could work and the best one is unknown
- User wants to "find the best" approach through systematic experimentation
- Optimization tasks where marginal improvements matter

## When NOT to Use

- Deterministic tasks (add endpoint, fix bug, refactor)
- No clear metric exists
- First-time implementation (nothing to compare against)
- Architecture / strategy questions — use `expert-panel` skill
- Safety-critical / irreversible actions where keep-or-revert cannot be automated

## Simplicity principles (non-negotiable)

1. **One atomic change per iteration.** Not five. Not "a batch of related tweaks." One. Revert is trivial; diagnosis is tractable.
2. **Small mutable surface.** Scope down before looping. If your surface is "the whole codebase" or "the whole prompt," the loop cannot converge.
3. **Simple fitness function.** One command. One number. Fixed corpus.
4. **Simple loop driver.** ~200 lines of Python (`templates/loop-driver.py`) — not a framework.
5. **Simplicity criterion (Karpathy).** A small improvement that adds ugly complexity is not worth it. Removing code at equal-or-better metric is a win. See decision table in `templates/iteration-prompt.md` Step 6.
6. **Escalate ambition, not iteration count, when stuck.** If timid tweaks plateau, the answer is BOLDER changes. See `references/anti-patterns.md` #13.
7. **Hard iteration cap + autonomous execution.** The driver enforces max iterations + dollar budget + plateau detection. Within those limits, the loop runs AUTONOMOUSLY — never pausing to ask permission.

## Evaluation Firewall (our hard constraint)

The evaluation function/metric is **IMMUTABLE** during the loop. The agent:
- **CAN modify**: implementation code, parameters, architecture, algorithms (inside the mutable surface)
- **CANNOT modify**: test files, evaluation scripts, acceptance criteria, metric definitions, fitness commands, goal.md, baseline.json

If the agent needs to change the evaluation, STOP and ask the human. Enforced by QA reviewer (see CLAUDE.md HARD CONSTRAINTS).

## Five stages, in order

Execute stages sequentially. Skip stages only when the user explicitly says "I've done that, start the loop."

| Stage | Purpose | Reference | Output |
|-------|---------|-----------|--------|
| 1. Intake | Collect goal, metric, surface, guard, budget | — | goal.md draft |
| 2. Triage | Is this problem autoresearch-shaped? | `references/triage-checklist.md` | Verdict + mode |
| 3. Fitness design | Build or validate the fitness function | `references/fitness-design.md` | baseline.json + sanity check |
| 4. Mode selection | Pick pure / barbell / via-negativa / inverted / human-in-loop | `references/modes.md` | Mode recorded in goal.md |
| 5. Loop + post-mortem | Scaffold, run, diagnose plateau if reached | `references/plateau-ideation.md` + `references/anti-patterns.md` | journal.md + plateau diagnosis |

**Load each reference file on demand during the stage that needs it. Do not preload.**

---

### Stage 1: Intake

Ask all five in one structured message, not one at a time:

1. **Goal** — what should be better after this runs? State as "before → after."
2. **Candidate metric** — how would you know it's better? A number is ideal; a deterministic rubric is the fallback.
3. **Mutable surface** — what files, prompts, config, copy, or parameters can the agent change? Be specific.
4. **Guard** — what must not regress? Safety tests, brand rules, legal constraints, downstream dependencies.
5. **Budget** — iterations, wall-clock, or dollars.

If the user cannot answer 2 or 3, continue anyway. Triage will surface it and Stage 3 will force a resolution.

Start filling `templates/goal.md` with known values; leave unknowns as placeholders.

### Stage 2: Triage

Load `references/triage-checklist.md`. Walk the candidate through five dimensions and score each green / yellow / red:

- Feedback latency
- Metric mechanicality
- Tail shape (thin vs fat-tailed)
- Sample size vs noise
- Surface locality (atomic diff vs system redesign)

**Decision rules:**
- All green → pure optimizer mode, proceed to Stage 3
- Any yellow → mode adaptation required, proceed to Stage 3 with concerns noted
- Any red → either adapt the mode OR **refuse the loop and offer alternatives** (expert-panel, human-in-loop, fix the upstream bottleneck first, smaller better-shaped sub-problem)

**Refusal is a feature. Do not start the loop to be agreeable.**

**Override: force.** If the user explicitly overrides a red verdict via `override: force` in `goal.md` with a mandatory reason, log BOTH the override AND the original triage verdict in `experiments/journal.md`. The loop runs, but Stage 6 plateau diagnosis will carry the unresolved red dimension as the primary suspect.

### Stage 3: Fitness design

Load `references/fitness-design.md`. The fitness function is where autoresearch dies when it dies — not in the loop mechanics.

Required before the loop can start (seven requirements):
1. Fitness is a command (or deterministic chain) that outputs a number
2. It runs on a fixed corpus with fixed seeds (stationary across iterations)
3. Baseline has been recorded to `experiments/baseline.json` (includes `direction: higher|lower`)
4. Significance threshold defined (what delta is real vs noise)
5. Sanity check done: score known-good and known-bad by hand, confirm the metric agrees
6. Guard metrics defined: what must not regress
7. **LLM-prompt loops only:** compliance audit — verify the model follows the prompt (≥70% on baseline traces)

If 1-4 are not met, the skill's answer is: "fix the fitness function first, then come back." This is the single highest-leverage intervention.

### Stage 4: Mode selection

Load `references/modes.md`. Pick exactly one:

| Mode | When |
|------|------|
| **Pure optimizer** | Small mutable surface, fast feedback, clean metric, thin-tailed |
| **Barbell** | Fat-tailed, reflexive domain — 85% immutable proven baseline + 15% wild experiments |
| **Via negativa** | Fragile system — ask "what to kill" not "what to add" |
| **Inverted** | Imbalanced classes — optimize rejection of bad, not selection of good |
| **Human-in-loop** | Slow feedback or irreversible actions — agent proposes, human decides |

Record the mode in `goal.md`. It controls what the loop is allowed to propose.

### Stage 5: Loop + post-mortem

#### Scaffold (once)

Create in the user's working directory (or a subdirectory they pick):
- `goal.md` — filled from `templates/goal.md`: goal / metric / surface / guard / mode / budget / triage record / fitness checklist
- The fitness command (script, notebook, evaluator — user's choice, not the skill's)
- `experiments/` directory for per-iteration logs and driver output
- `experiments/baseline.json` with the starting metric, direction, threshold, sanity check results
- `loop-driver.py` and `iteration-prompt.md` copied from `templates/` (for autonomous runs)

#### Drive the loop (three options, in order of preference)

1. **External Python driver (recommended).** Use `templates/loop-driver.py`:
   ```bash
   python loop-driver.py --max-iter 50 --max-budget-usd 10
   ```
   (On Windows: `py -3 loop-driver.py ...`)

   Default permission mode is `acceptEdits` (safer, auditable). For truly unattended overnight runs, pass `--permission-mode bypassPermissions` AND ensure your project has a narrow Bash allowlist in `.claude/settings.json`. Each iteration is a fresh `claude -p` session reading the journal.

2. **Integrated Pipeline phase.** Add an `EXPERIMENT` phase to `work/PIPELINE.md` (see "Integration with Pipeline" below). Useful when the loop is part of a larger multi-phase initiative.

3. **Interactive / manual.** User approves each iteration in a single Claude Code session. OK for N ≤ 5. Tedious above that.

#### Hard caps are mandatory

Every driver MUST enforce:
- **Max iterations** — default 50, hard cap. Raise only with a written reason in `goal.md`.
- **Dollar budget** — via `claude -p --max-budget-usd`.
- **Wall-clock budget** — via `timeout` or driver-level check.
- **Plateau detection** — default 10 iterations without significance-threshold improvement → stop.
- **Guard violation** — immediate stop, no retries.
- **Context pressure** — >75% → safety stop with state save.
- **Crash detection** — experiment timeout (10 min) → auto-discard.

Any trigger writes `experiments/STOP` with a one-line reason and exits.

#### Per-iteration algorithm (driven by `iteration-prompt.md`)

See `templates/iteration-prompt.md` for the full per-iteration contract. Summary:

1. Read state: `goal.md`, `experiments/journal.md`, `experiments/baseline.json`, `git log --oneline -20`
2. Plateau check: if last 10 kept deltas < significance, run `plateau-ideation.md` before declaring STOP
3. Propose ONE atomic change respecting the mode and mutable surface
4. `git commit` with `experiment:` prefix BEFORE running fitness
5. Run fitness + all guard checks
6. Keep or revert per simplicity criterion decision table
7. Append one line to `experiments/journal.md` + post to `work/results-board.md` if it exists
8. Check termination signals → exit (driver starts next iteration)

#### Post-mortem (when the loop stops)

Produce:
- Final metric vs baseline, with significance
- Top 3 changes that stuck, top 3 changes that were reverted
- **Plateau diagnosis** if plateaued — consult `references/anti-patterns.md` and name one:
  - Wrong search space → change the mutable surface
  - Wrong metric → fitness does not correlate with the real goal
  - Broken measurement → sample size, stationarity, or confounded labels
  - Genuine local optimum → switch mode to barbell
  - Out of budget → more iterations would help

**Before declaring plateau, run `references/plateau-ideation.md` workflow. This is mandatory, not optional.** Specifically:

1. Mine the last 10 reverts for pattern (axis + failure mode for each). Tradeoff reverts (primary lifted, guard broke) are especially rich.
2. Run the taxonomy coverage check. If fewer than ~6 of 8 axes have been touched with substantive changes, the loop is NOT plateaued — propose on an untouched axis.
3. Only when coverage is satisfied AND revert mining surfaces no untouched direction: invoke `cross-model-review` skill with the three structured prompts from `plateau-ideation.md` Move 3.
4. Only when all three are exhausted: declare plateau and pick a cause above.

**The plateau diagnosis IS the deliverable when the loop doesn't improve.** Foreground it, don't bury it.

## Integration with Pipeline

Optional phase in `work/PIPELINE.md` (between PLAN and IMPLEMENT):

```markdown
### Phase: EXPERIMENT
- Status: PENDING
- Mode: SOLO
- Attempts: 0 of 1
- On PASS: -> IMPLEMENT (with best approach from experiments)
- On FAIL: -> PLAN (no approach met threshold)
- On BLOCKED: -> STOP
- Gate: best metric meets threshold OR budget exhausted with best-so-far
- Gate Type: AUTO
- Inputs: baseline metric, experiment scope, budget
- Outputs: work/{feature}/experiment-log.md, experiments/journal.md, experiments/STOP
- Sub-stages (internal checklist, not separate phases):
  - [ ] Stage 1: Intake (goal.md draft)
  - [ ] Stage 2: Triage (verdict + mode)
  - [ ] Stage 3: Fitness design (baseline.json + sanity check)
  - [ ] Stage 4: Mode selection (recorded in goal.md)
  - [ ] Stage 5: Loop run (journal.md)
  - [ ] Stage 6: Post-mortem (plateau diagnosis if applicable)
```

## Results Board integration

If `work/results-board.md` exists (shared log for agent coordination), each iteration appends:
```
[experiment-loop iter {{ITER}}] metric=<n> kept=<yes|no> change=<one-line>
```

Other agents reading results-board.md see experiment progress in real-time.

## Configuration (loop-driver.py flags)

```
--max-iter N              # default 50
--max-budget-usd X        # default 10.0
--plateau-window N        # default 10 iterations
--goal PATH               # default goal.md
--prompt PATH             # default iteration-prompt.md
--permission-mode MODE    # acceptEdits (default) | bypassPermissions
--resume                  # continue from existing journal state
```

## Completion markers

| Marker | Meaning |
|--------|---------|
| `<budget_exhausted>` | Hit max iterations or dollar cap |
| `<time_exhausted>` | Hit wall-clock limit |
| `<threshold_met>` | Metric reached target value |
| `<safety_stop>` | Context pressure or other safety valve |
| `<stagnation>` | Plateau-window exhausted (see plateau-ideation.md first) |
| `<guard_violation>` | Guard failed, unable to revert cleanly |

## Common mistakes

1. **Starting Stage 5 without Stage 2-3** — premature loop, anti-pattern #12
2. **Changing the evaluation** — NEVER modify test/eval/goal files during the loop (Evaluation Firewall)
3. **Not recording failures** — ALL experiments go in the log, including crashes
4. **Repeating failed approaches** — always read the journal before forming a hypothesis
5. **No compliance audit on LLM-prompt loops** — see anti-pattern #14
6. **Timid tweaks on a plateau** — escalate ambition, don't add iterations (anti-pattern #13)

## File layout

```
<feature-dir>/
├── goal.md                    # from templates/goal.md
├── experiments/
│   ├── baseline.json          # metric, direction, threshold, sanity check
│   ├── journal.md             # one line per iteration
│   ├── driver.log             # driver logging output
│   └── STOP                   # (present only when loop terminated, contains reason)
├── iteration-prompt.md        # from templates/iteration-prompt.md
└── loop-driver.py             # from templates/loop-driver.py
```

## Related

- → `skill-evolution` — after successful experiment, propose skill improvements
- → `verification-before-completion` — verify experiment results before declaring done
- → `cross-model-review` — Codex second opinion at Stage 6 plateau diagnosis
- → `expert-panel` — escalation when triage refuses or when architecture-level rethink needed
- → `systematic-debugging` — if fitness function produces unexpected results
- ← `PIPELINE.md` EXPERIMENT phase — optional pipeline phase

## Attribution

- **Core loop structure:** Andrej Karpathy, autoresearch pattern (github.com/karpathy)
- **Triage / fitness / modes / plateau-ideation / anti-patterns:** adapted from Bayram Annakov's MIT-licensed autoresearch skill (github.com/BayramAnnakov/ai-native-product-skills)
- **Conceptual inspiration:** Nassim Nicholas Taleb (tail shape, barbell, via negativa, turkey metaphor), Daniel Kahneman (compliance verification principle)
- **Our additions:** Evaluation Firewall, Pipeline integration, Results Board integration, direction-aware plateau tracking, Python cross-platform driver
