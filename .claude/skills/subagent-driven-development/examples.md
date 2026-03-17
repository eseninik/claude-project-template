# Subagent-Driven Development — Examples

> Real-world examples from actual usage. Grows organically via skill-evolution pattern.
> Each example: what was the input → what the skill did → what was the output.

## Example 1: Fleet Sync — Bulk File Copy vs Read/Write

**Context**: Sync 5 new features to 11 bot projects (25+ files per project)

**Input**: 3 parallel agents, each handling 2-4 projects. Each agent copies ~25 files using Read → Write cycle.

**What happened**: One agent (syncer) took 10+ minutes and likely hung on Read/Write loop. Manual bash `cp` commands completed in seconds.

**Output**: All projects synced, but syncer agent had to be killed and work completed manually.

**Learning**: For bulk file operations (10+ files), use `bash cp -r` instead of Read/Write cycle. Read/Write is for content that needs modification. Straight copies should use bash.

---

## Example 2: Fleet Sync — Batch Assignment Pattern

**Context**: Update 11 projects with global skills migration

**Input**: 11 target projects, 3 task types (copy skills, cleanup duplicates, sync CLAUDE.md)

**What happened**: 3 agents with different responsibilities ran in parallel (not 11 agents, one per project). Each agent handled all 11 projects for its task type.

**Output**: All completed in ~5 minutes. No file conflicts because each agent touched different file types.

**Learning**: For fleet operations, parallelize by TASK TYPE (not by project). 3 agents × 11 projects > 11 agents × 3 tasks — less agent overhead, no file conflicts.

---
