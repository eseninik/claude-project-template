# Additions for Shared Files

These are exact text blocks to add to shared configuration files for experiment-loop skill integration.

---

## 1. For registry.md (new agent type — add under Implementation Agents)

```
| `experimenter` | full | experiment-loop, verification-before-completion | deep | full | full | none |
```

Note: experimenter uses deep thinking, full context and memory because it needs to form novel hypotheses.

---

## 2. For CLAUDE.md — CONTEXT LOADING TRIGGERS (Skills table)

```
| Optimization/experiment task | experiment-loop |
```

---

## 3. For PIPELINE-v3.md (add as comment block after NYQUIST_CHECK, before IMPLEMENT)

```
> To add an experiment phase for optimization tasks:
> ```
> ### Phase: EXPERIMENT
> - Status: PENDING
> - Mode: SOLO
> - Attempts: 0 of 1
> - On PASS: -> IMPLEMENT
> - On FAIL: -> PLAN
> - On BLOCKED: -> STOP
> - Gate: best metric meets threshold OR budget exhausted
> - Gate Type: AUTO
> - Inputs: baseline metric, experiment scope
> - Outputs: work/{feature}/experiment-log.md, experiment-state.md
> ```
> Use for tasks with quantifiable metrics that need iterative optimization.
> Skill: `.claude/skills/experiment-loop/SKILL.md`
```
