# Checkpoint Recovery

Wave-level checkpointing for subagent-driven-development. Complements PIPELINE.md `<- CURRENT` (phase-level) with wave-level granularity.

## Checkpoint File

Location: `work/{feature}/checkpoint.yml`

```yaml
feature: feature-name
current_wave: 2
total_waves: 3
waves:
  1:
    status: completed  # pending | in_progress | completed | failed
    tasks: [1, 2, 3]
    started_at: "2026-03-05T10:00:00"
    completed_at: "2026-03-05T10:15:00"
    results:
      - task: 1
        status: completed
        files_changed: ["src/auth.py", "tests/test_auth.py"]
      - task: 2
        status: completed
        files_changed: ["src/api.py"]
      - task: 3
        status: completed
        files_changed: ["src/models.py"]
  2:
    status: in_progress
    tasks: [4, 5]
    started_at: "2026-03-05T10:16:00"
    results: []
  3:
    status: pending
    tasks: [6]
    results: []
decisions:
  - "Used worktree mode for tasks 2,3 (file overlap in src/api.py)"
  - "Task 4 depends on task 1 output (auth module)"
```

## When to Save

Save checkpoint.yml after:
1. Each wave completes (status: completed, add completed_at)
2. Each wave starts (status: in_progress, add started_at)
3. Each task within a wave completes (add to results[])
4. Significant decisions are made (append to decisions[])

## When to Read

Read checkpoint.yml:
1. At session start / after compaction -- determine which wave to resume
2. Before starting a new wave -- verify previous wave completed
3. When reporting progress -- show wave N of M

## Resume Protocol

```
1. Read work/{feature}/checkpoint.yml
2. Find wave with status: in_progress
   - If found: resume from that wave
   - Check results[] to see which tasks completed
   - Only re-run tasks NOT in results[]
3. If no in_progress wave: find first pending wave
4. If all completed: report "all waves done"
```

## Integration with PIPELINE.md

```
PIPELINE.md <- CURRENT = which PHASE we're in (IMPLEMENT, TEST, etc.)
checkpoint.yml = which WAVE within IMPLEMENT we're in

After compaction:
1. Read PIPELINE.md -> find phase
2. If phase is IMPLEMENT -> read checkpoint.yml -> find wave
3. Resume from wave, not from beginning of phase
```
