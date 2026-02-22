# Active Context

> Session bridge. Agent reads at start, updates at end. Max ~150 lines.
> Old sessions → `.claude/memory/archive/`

**Last updated:** 2026-02-22

---

## Current Focus

### PreCompact Memory Save Hook — COMPLETE ✓
**Task:** Implement automatic pre-compaction memory save (OpenClaw's "silent turn" pattern)

**What was built:**
- `.claude/hooks/pre-compact-save.py` — Python script, stdlib only, ~230 lines
- Reads JSONL transcript → calls OpenRouter Haiku → saves to daily/ + activeContext.md
- `.claude/hooks/.env` — API key (gitignored)
- `.claude/settings.json` — hook config (`py -3` command, 60s timeout)
- Template synced: hooks/, settings.json, .gitignore all updated

**Tests passed:**
- [x] Mock stdin (no transcript) — graceful exit 0
- [x] Real transcript + API call — extracted memory saved to daily/ + activeContext.md
- [x] No API key — graceful exit 0
- [x] .gitignore — .env excluded from git

---

## Recent Decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-22 | SIMPLIFY + STRENGTHEN + ENRICH strategy | OpenClaw analysis shows our compliance is ~30-40% despite 40 rules |
| 2026-02-22 | Merge patterns.md + gotchas.md → knowledge.md | One file = higher compliance than two |
| 2026-02-22 | Add daily/ logs (OpenClaw pattern) | Chronological memory has lowest friction |
| 2026-02-22 | Session Start 8→4 steps, After Task 9→2+3 | Fewer mandatory steps = higher compliance |
| 2026-02-22 | Keep Graphiti without deletion deadline | Powerful tool, needs better enforcement |
| 2026-02-19 | Ralph Loop removed, features extracted | User never uses Ralph Loop; 3 patterns preserved |

---

## Session Log

### 2026-02-22 (current)
**Did:** (1) Completed OpenClaw pipeline PIPELINE_COMPLETE. (2) Built PreCompact Memory Save Hook — Python script that auto-saves context before compaction via OpenRouter Haiku API. Tested successfully with real transcript.
**Decided:** Re-add PreCompact hook as single Python script (stdlib only). Previous bash hooks were removed due to Windows issues — Python is cross-platform.
**Learned:** `py -3` is the reliable Python launcher on Windows Git Bash. JSONL transcripts contain full conversation with type/role/content structure. PreCompact hooks receive JSON on stdin with session_id, transcript_path, cwd.
**Next:** System ready for use. Hook will automatically save context on every compaction.

### 2026-02-19
**Did:** Ralph Loop extraction pipeline (6 phases). Phase Transition Protocol integrated. Graphiti connected and verified.
**Decided:** Graphiti is ALWAYS available (no "if available" checks)
**Learned:** Phase Context Loading + insight extraction are the most valuable Ralph patterns
**Next:** OpenClaw analysis (now in progress)

### 2026-02-18
**Did:** Auto-Claude integration — 17 new files, 7 modified, template synced. Agent registry, typed memory, focused prompts, complexity assessment, recovery manager.
**Decided:** Always Opus 4.6. Typed memory as primary, Graphiti as enrichment.
**Learned:** Auto-Claude is sequential (1 subtask), our system is parallel (Agent Teams) — keep our approach
