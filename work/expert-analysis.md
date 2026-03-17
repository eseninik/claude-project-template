# Expert Analysis: Boris Cherny Principles vs. Current CLAUDE.md

**Date:** 2026-03-01
**Task:** Should we update CLAUDE.md based on Boris Cherny's (creator of Claude Code) published methodology?
**Panel:** Business Analyst, System Architect, Risk Assessor

---

## Executive Summary

**Verdict: Selective adoption. Our system already exceeds Cherny's framework in 7 of 9 principles.**

Key conflict resolved: Business Analyst/System Architect say "add elegance + lessons". Risk Assessor says "CLAUDE.md is already at compliance-risk length — adding 6 more rules drops compliance below 30%." **Consensus:** 2 genuine gaps exist, but both can be addressed with ≤ 5 net new lines in CLAUDE.md.

---

## Coverage Scorecard

| Cherny Principle | Our Coverage | Verdict |
|---|---|---|
| Planning mode by default | PIPELINE.md + phase gates + compaction survival | **EXCEEDS** |
| Subagent strategy | Agent Teams + AO Hybrid + AO Fleet + spawn-agent.py | **EXCEEDS** |
| Self-improvement loop | knowledge.md + Ebbinghaus decay + observations/ | **PARTIAL** — no failure-focused file |
| Verification before completion | verification-before-completion skill + blocking rule + hook | **EXCEEDS** |
| Require elegance (balanced) | Not present | **MISSING** |
| Autonomous bug fixing | systematic-debugging skill + retry protocol | **MATCHES** |
| Plan first / track progress | PIPELINE.md + TaskCreate | **EXCEEDS** |
| Simplicity first | "Fewer Rules = Higher Compliance" (active pattern) | **EXCEEDS** |
| No laziness / root cause | Debugging blocking rule + gotchas | **MATCHES** |

**Coverage: 7/9 principles already covered, 2 missing.**

---

## Genuine Gaps (2 of 9)

### Gap 1: Elegance Review Gate — HIGH PRIORITY

**What's missing:** No gate between IMPLEMENT and TEST that asks "Is there a more elegant way?"

Our QA loop checks **correctness**. It does not check **design quality**. Cherny's elegance check prevents technical debt accumulation — each hacky fix that passes QA creates compounding maintenance cost.

**Risk Assessor constraint:** Must be implemented without adding verbose rules. One-liners only.

**Proposed minimal addition to Summary Instructions:**
```
- **ELEGANCE**: After IMPLEMENT, before QA: ask "Is there a simpler way?" If yes → reimplement. Skip for 1-line fixes.
```

**One row in HARD CONSTRAINTS:**
```
| Не проверять элегантность после IMPLEMENT | Спроси: "Есть ли способ проще?" |
```

**Effort:** 10 minutes. **ROI:** Prevents technical debt accumulation.

---

### Gap 2: Failure-Driven Self-Improvement — MEDIUM PRIORITY

**What's missing:** After user feedback or circular fix — no explicit "write a rule for yourself" mechanism. Our knowledge.md is **discovery-oriented** ("here's what works"). Cherny's lessons are **failure-oriented** ("here's what I keep breaking"). These complement each other.

**Three-Layer Memory Model (System Architect synthesis):**
1. **Lessons** (defensive) — rules from failures, no decay, session-start priority
2. **Knowledge.md** (constructive) — patterns, Ebbinghaus decay
3. **Graphiti** (semantic) — cross-session search

**Proposed minimal addition to AUTO-BEHAVIORS → Session Start:**
```
3. IF work/tasks/lessons.md exists → read top 5 lessons (rules from past failures)
```

Create `work/tasks/lessons.md` as project artifact (not a CLAUDE.md section). Recovery manager auto-appends when circular fix detected.

**Effort:** 20 minutes + template file.

---

## REJECTED Changes (with rationale)

| Cherny Principle | Why NOT to Add |
|---|---|
| Planning mode by default | PIPELINE.md already enforces this. Adding "3+ steps → plan" duplicates existing behavior |
| Subagent strategy | Agent Teams + AO already exceed this. Adding it is documentation debt |
| Verification before completion | Already a blocking rule + skill + hook. Any addition duplicates |
| Autonomous bug fixing | systematic-debugging covers it. Gap 2 (lessons) handles the "don't repeat" aspect |
| tasks/todo.md with checkboxes | PIPELINE.md + TaskCreate is strictly superior. Two task systems = confusion |
| Root-cause documentation | 70% overlap with knowledge.md gotchas. Marginal ROI doesn't justify complexity cost |

---

## Risk Matrix

| Risk | P×I | Analysis |
|---|---|---|
| **CLAUDE.md complexity growth** | **4×5 = CRITICAL** | Active pattern: "Fewer Rules = Higher Compliance". Compliance ~30-40% at current length. Each new rule dilutes attention. Mitigation: ≤ 5 net new lines total. |
| tasks/lessons.md vs knowledge.md duplication | 2×2 = LOW | Different abstraction levels: lessons = tactical rules, knowledge = strategic patterns. Complementary. |
| Planning mode redundancy | 1×0 = NONE | PIPELINE.md already enforces this — same behavior, no conflict. |
| "Require elegance" subjectivity | 2×1 = LOW | Cherny's "balanced" framing is the key. Skip for 1-line fixes. Not a blocking gate. |
| tasks/todo.md vs TaskCreate | 2×3 = MEDIUM-LOW | TaskCreate is superset. Keep `session-todos.md` as optional human-readable artifact only. |

---

## Architecture Recommendation (System Architect)

**Option B: Minimal targeted integration** (NOT full restructuring)

```
+ Add: work/tasks/lessons.md (new project artifact file)
+ Add: 1 bullet in Session Start (read lessons.md)
+ Add: 1 line in Summary Instructions (elegance)
+ Add: 1 row in HARD CONSTRAINTS (elegance)
~ Enhance: recovery-manager.md (auto-generate lesson on circular fix)

Total CLAUDE.md delta: +4 lines, +1 table row
New files: 1 (work/tasks/lessons.md template)
Breaking changes: ZERO
```

**Why not Option A (just a side reference):** Lessons without session-start loading won't be read. Must be in Session Start sequence.

**Why not Option C (full unification):** Over-engineering. The two systems serve different purposes and should remain separate.

---

## Consensus Recommendations

### Rec 1: ADD Elegance Gate — 2 lines total in CLAUDE.md
```
In Summary Instructions (1 line):
"**ELEGANCE**: After IMPLEMENT, before QA: ask 'Is there a simpler way?'
If yes and non-trivial → reimplement first. Skip for 1-line fixes."

In HARD CONSTRAINTS (1 row):
| Не проверять элегантность после IMPLEMENT | Спроси себя: "Есть ли способ проще?" |
```

### Rec 2: ADD Lessons File + Session Start Hook — 1 line in CLAUDE.md
```
In AUTO-BEHAVIORS → Session Start, add bullet:
"3. IF work/tasks/lessons.md exists → read top 5 lessons"

Create: work/tasks/lessons.md (template, not in CLAUDE.md body)
Enhance: recovery-manager.md to auto-append lessons on circular fix detection
```

### Rec 3: NO CLAUDE.md restructuring
The other 7 principles are already covered. Documenting them again = complexity cost with zero compliance benefit. Cherny's system is **simpler** than ours because it's designed for single-session use. Our system handles compaction, multi-bot fleets, and cross-session memory — necessarily more complex.

---

## Implementation Plan (if approved)

**Phase 1 — Elegance Gate (30 min, SOLO):**
1. Add 1 line to `Summary Instructions` in CLAUDE.md
2. Add 1 row to `HARD CONSTRAINTS` in CLAUDE.md
3. Sync to new-project template

**Phase 2 — Lessons Mechanism (45 min, SOLO):**
1. Create `work/tasks/lessons.md` template
2. Add 1 bullet to `AUTO-BEHAVIORS → Session Start` in CLAUDE.md
3. Update `recovery-manager.md` to auto-generate lessons on circular fix
4. Sync to new-project template

**Total CLAUDE.md delta:** +4 lines, +1 table row (~1% size increase)
**Compliance risk:** NEGLIGIBLE

---

## Open Questions for User

1. **Elegance gate scope:** Code changes only, or also prompt/CLAUDE.md changes?
2. **Lessons file location:** `work/tasks/lessons.md` (per-project, gitignored) or `.claude/memory/lessons.md` (methodology-level, synced to template)?
3. **Auto-generation threshold:** Lessons auto-created after 3 failed attempts OR only after explicit user feedback?
