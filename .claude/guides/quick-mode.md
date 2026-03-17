# Quick Mode

> Lightweight execution path for ad-hoc tasks that need GSD guarantees (atomic commits, state tracking) but skip optional pipeline steps.

## When to Use

- Bug fixes that don't need full pipeline
- Small features (1-3 files changed)
- Config changes, dependency updates
- Tasks where full PIPELINE.md is overkill
- User says "quick fix", "just do it", "small change"

## When NOT to Use

- Tasks touching 5+ files across modules → use full pipeline
- Architectural changes → use full pipeline with expert panel
- Cross-project changes → use AO Fleet
- Tasks with unclear requirements → use discuss-phase first

## Process

### 1. Assess Task

Quick assessment (no formal complexity file):
- Files affected: 1-3 → Quick Mode OK
- Risk: low/trivial → Quick Mode OK
- Dependencies: none → Quick Mode OK
- If ANY of these fail → suggest full pipeline

### 2. Plan (Lightweight)

No formal PLAN.md. Instead, announce:
```
Quick Mode: [task description]
Files: [list of files to modify]
Approach: [1-2 sentences]
Verification: [how to verify]
```

### 3. Execute

Standard execution with these guarantees:
- Atomic commits (one per logical change)
- Tests run before claiming done
- verification-before-completion applies (including Goal-Backward + 3-Level checks)

### 4. Track

Create minimal tracking in `work/quick/`:
```bash
mkdir -p work/quick/
```

File: `work/quick/{N}-{slug}.md`
```markdown
# Quick: [Task Description]

- Date: [YYYY-MM-DD]
- Status: [done/in-progress]
- Files: [list]
- Commit: [hash]
- Verification: [evidence]
```

### 5. Verify

Even Quick Mode requires:
- Run relevant tests
- Goal-backward check: "Did I actually solve the problem?"
- 3-level artifact check on new files (Exists → Substantive → Wired)

### 6. Commit

Standard commit with `quick:` prefix:
```
quick: [description]
```

## Composable Flags (Mental Model)

These aren't CLI flags — they're decision points:

| Decision | Default | Override |
|----------|---------|----------|
| Discussion phase | Skip | Add if requirements unclear |
| Plan checking | Skip | Add if risk > low |
| Full QA review | Skip | Add if risk > medium |
| Nyquist validation | Skip | Add if new feature (not fix) |

## Integration

- Quick Mode tasks are tracked separately from pipeline phases
- They don't affect pipeline progress
- Quick tasks still update activeContext.md + daily log
- If a "quick" task grows complex mid-execution → STOP, create PIPELINE.md

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using Quick Mode for 5+ file changes | Switch to full pipeline |
| Skipping verification in Quick Mode | Verification is MANDATORY even in Quick Mode |
| Not tracking quick tasks | Always create work/quick/{N}-{slug}.md |
| Quick task growing into feature | STOP and create proper PIPELINE.md |
| Skipping goal-backward check | "Did I solve the problem?" is always required |
