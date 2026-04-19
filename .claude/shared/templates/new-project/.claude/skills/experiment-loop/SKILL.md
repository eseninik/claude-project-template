---
name: experiment-loop
description: >
  Autonomous experiment loop for iterative optimization with quantifiable metrics.
  Hypothesis, experiment, measure, keep/discard cycle with full journal logging.
  Use when task has a quantifiable success metric and needs iterative optimization,
  when user says "optimize", "find best", "experiment", "try variations", or "iterate until better".
  Do NOT use for deterministic implementation tasks, bug fixes, one-shot changes, or tasks without measurable metrics.
roles: [experimenter, pipeline-lead]
---

# Experiment Loop

## Overview

Autonomous cycle for iterative optimization. Inspired by Karpathy's autoresearch pattern.

**Core principle:** Modify, measure, keep if better, discard if not. Repeat until budget exhausted or threshold met.

## When to Use

- Task has a **quantifiable metric** (response rate, accuracy, performance, conversion, test pass rate)
- Multiple approaches could work and the best one is unknown
- User wants to "find the best" approach through systematic experimentation
- Optimization tasks where marginal improvements matter

## When NOT to Use

- Deterministic tasks (add endpoint, fix bug, refactor)
- No clear metric exists
- First-time implementation (nothing to compare against)

## Critical Constraints

**Never:**
- Modify evaluation files, test scripts, or metric definitions during the loop
- Skip recording failed experiments in the log
- Repeat an approach already tried (always read the log first)
- Start without establishing a baseline metric

**Always:**
- Record ALL experiments (successes, failures, crashes)
- Prefer small, isolated changes per experiment
- Equal results with less code = KEEP (simplicity wins)
- Save state on any stop condition

## Prerequisites

Before starting the loop:

1. **Define the metric**: What number are we optimizing? Lower or higher is better?
2. **Define the baseline**: Run current code, record the baseline metric value
3. **Define the scope**: What files/parameters CAN be changed? What is IMMUTABLE?
4. **Define the budget**: Max experiments (default: 20), max time (default: 2 hours)

## Evaluation Firewall

The evaluation function/metric is IMMUTABLE. The agent:
- **CAN modify**: implementation code, parameters, architecture, algorithms
- **CANNOT modify**: test files, evaluation scripts, acceptance criteria, metric definitions

If the agent needs to change the evaluation, STOP and ask the human.

## Algorithm

```
experiment_count = 0
max_experiments = 20  # configurable
best_metric = baseline_value
best_commit = HEAD
metric_direction = "lower"  # or "higher"

LOOP:
  1. Check budget
     IF experiment_count >= max_experiments: OUTPUT <budget_exhausted>, RETURN
     IF wall_clock > max_time: OUTPUT <time_exhausted>, RETURN
     IF context_pressure > 75%: OUTPUT <safety_stop>, save state, RETURN

  2. Form hypothesis
     Read experiment log (work/{feature}/experiment-log.md)
     Read previous failures to avoid repeating
     Choose a NEW approach (must differ from all previous)

  3. Implement change
     Modify ONLY files in the mutable scope
     git add + git commit -m "experiment: {hypothesis_summary}"

  4. Run experiment
     Execute the measurement command
     Record: metric_value, duration, resource_usage
     IF crash/timeout (>10 min): treat as DISCARD

  5. Evaluate
     is_better = (metric_direction == "lower" AND metric_value < best_metric)
                 OR (metric_direction == "higher" AND metric_value > best_metric)

  6. Record in experiment log (ALWAYS — successes AND failures)
     Append row to work/{feature}/experiment-log.md

  7. Decision
     IF is_better:
       best_metric = metric_value
       best_commit = HEAD
       STATUS = KEEP
     ELSE:
       git reset --hard HEAD~1  (revert to last good state)
       STATUS = DISCARD

  8. Post to results board
     IF work/results-board.md exists: append entry

  9. INCREMENT experiment_count
     CONTINUE to step 1
```

## Experiment Log Format

File: `work/{feature}/experiment-log.md`

```markdown
# Experiment Log: {feature}

## Config
- Metric: {metric_name}
- Direction: {lower|higher} is better
- Baseline: {baseline_value}
- Best: {best_value} (experiment #{best_number})
- Total experiments: {count}

## Log

| # | Timestamp | Hypothesis | Metric | Delta | Status | Commit | Duration |
|---|-----------|-----------|--------|-------|--------|--------|----------|
| 1 | 2026-03-11 14:30 | baseline | 0.997 | — | BASELINE | a1b2c3d | — |
| 2 | 2026-03-11 14:35 | increase learning rate | 0.993 | -0.004 | KEEP | b2c3d4e | 5m |
| 3 | 2026-03-11 14:40 | switch to GeLU | 1.005 | +0.008 | DISCARD | — | 5m |
| 4 | 2026-03-11 14:45 | double width | — | — | CRASH | — | OOM |
```

## State Preservation

On any stop (budget, time, safety, manual), write `work/{feature}/experiment-state.md`:

```markdown
# Experiment State: {feature}

- Status: PAUSED
- Reason: {budget_exhausted|time_exhausted|safety_stop|manual}
- Best metric: {value} at commit {hash}
- Experiments run: {count} of {max}
- Time elapsed: {duration}
- Resume: checkout {best_commit}, continue from experiment #{next}
```

## Integration with Pipeline

Optional phase in PIPELINE.md (between PLAN and IMPLEMENT):

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
- Outputs: work/{feature}/experiment-log.md, work/{feature}/experiment-state.md
```

## Safety Valves

1. **Experiment budget**: max_experiments (default 20) — hard cap on iterations
2. **Time budget**: max_time (default 2 hours) — wall-clock limit
3. **Context pressure**: >75% — mandatory stop with state save
4. **Crash detection**: experiment timeout (10 min) — auto-discard
5. **Stagnation**: 5 consecutive DISCARDs with <1% delta — suggest different strategy
6. **Scope enforcement**: changes outside mutable scope — reject + revert

## Configuration

```
INVOKE skill: experiment-loop
  metric: val_bpb
  direction: lower
  baseline: 0.997
  max_experiments: 50
  max_time: 4h
  mutable_files: [src/model.py, src/config.py]
  immutable_files: [tests/*, eval.py]
  measure_command: "python eval.py --output-metric"
```

## Common Mistakes

1. **Changing the evaluation** — NEVER modify test/eval files during experiment loop
2. **Not recording failures** — ALL experiments go in the log, including crashes
3. **Repeating failed approaches** — always read the log before forming hypothesis
4. **No baseline** — must establish baseline metric before first experiment
5. **Too large changes** — prefer small, isolated changes per experiment
6. **Ignoring simplicity** — equal results with less code = KEEP (Karpathy's rule)

## Completion Markers

| Marker | Meaning |
|--------|---------|
| `<budget_exhausted>` | Hit max experiments |
| `<time_exhausted>` | Hit time limit |
| `<threshold_met>` | Metric reached target value |
| `<safety_stop>` | Context pressure or other safety valve |
| `<stagnation>` | 5 consecutive non-improvements |

## Related
- → skill-evolution — after successful experiment, propose skill improvements
- → verification-before-completion — verify experiment results
- ← PIPELINE.md EXPERIMENT phase — optional pipeline phase
