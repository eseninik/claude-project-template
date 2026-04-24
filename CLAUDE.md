# Project: Claude Project Template Update

> Template upgrade automation with AI-First methodology integration

**Memory:** `.claude/memory/activeContext.md` | **ADR:** `.claude/adr/` | **Branch:** `dev`

## Project-Specific Notes
- Main template: `.claude/` in project root
- New-project template: `.claude/shared/templates/new-project/.claude/`
- BOTH must be updated when making template changes
- Template CLAUDE.md (in shared/templates) should match global ~/.claude/CLAUDE.md structure
- Codex CLI integration: `.claude/guides/codex-integration.md` | Skill: `cross-model-review`

## Bridge-stubs for staging sessions
When a Claude Code session's CWD is inside a staging subdir (e.g. `work/dp-notifier/files/v2/`), hook commands like `py -3 .claude/hooks/X.py` resolve relative to that CWD and fail unless a bridge-stub exists at `<staging>/.claude/hooks/X.py`. Stubs re-exec the real hook from the repo root.

**After ANY change to `.claude/settings.json` hook wiring, or after creating a new staging dir, run:**
```
py -3 .claude/scripts/sync-bridge-stubs.py
```
The sync script reads `settings.json`, finds every `.claude/hooks/` dir under `work/`, `deploy/`, `staging/` and ensures each has an up-to-date canonical stub for every hook. Safe idempotent — run any time. Canonical stub: `.claude/scripts/bridge-stub-template.py` (filename-derived, uses `subprocess.run` for Windows path-with-spaces safety).

## Codex Primary Implementer (Experimental, Local)

**SCOPE — READ FIRST.** This section is **LOCAL to this project only**. It is **NOT propagated** to other bot projects or to `.claude/shared/templates/new-project/CLAUDE.md` until the PoC validates. Do not copy this section elsewhere; do not sync via template scripts until promotion is explicitly approved. The default phase modes remain `AGENT_TEAMS`, `AO_HYBRID`, and `AO_FLEET` as documented in global `~/.claude/CLAUDE.md`. The modes below are **specialized, opt-in tools**, not replacements.

### What it is
Opus plans, decomposes, and reviews; **Codex (GPT-5.5) executes** well-defined, scope-fenced implementation tasks. The pattern keeps Opus as the judge/architect and lets a second model do logic-heavy, well-specified work where a fresh perspective or higher throughput helps.

### New phase modes (choose per task — not always-on)

- **`CODEX_IMPLEMENT`** — every implementation task in the phase is delegated to Codex. Use when tasks are logic-heavy, well-specified, and unambiguous (algorithms, protocol code, data transforms) and where an independent executor reduces confirmation-bias risk. Avoid for tasks requiring deep repo conventions or heavy cross-file refactors.
- **`HYBRID_TEAMS`** — per-task `executor:` dispatch (`claude` | `codex` | `dual`). Most flexible mode. Use when a wave mixes task shapes: some tasks suit Claude (conventions, wide context), others suit Codex (self-contained logic), and a few warrant both (high-stakes).
- **`DUAL_IMPLEMENT`** — high-stakes code: Claude and Codex implement the task **in parallel**, Opus acts as judge and picks or merges. Use for auth, crypto, payments, migrations, or any change where two independent attempts catch more bugs than one. Expect ~2× token cost — reserve for genuinely risky diffs.

### Pointers (canonical docs — do not duplicate here)
- Tech-spec: `work/codex-primary/tech-spec.md`
- ADR: `.claude/adr/adr-012-codex-primary-implementer.md`
- Phase-mode docs: `.claude/shared/work-templates/phases/IMPLEMENT-CODEX.md`, `.claude/shared/work-templates/phases/IMPLEMENT-HYBRID.md`, `.claude/shared/work-templates/phases/DUAL-IMPLEMENT.md`
- Scripts: `.claude/scripts/codex-implement.py`, `.claude/scripts/codex-wave.py`, `.claude/scripts/codex-scope-check.py`
- Skill: `.claude/skills/dual-implement/SKILL.md`

### Compatibility (unchanged — fully supported)
Agent Teams (TeamCreate), skills injection, memory (activeContext / knowledge / daily), `codex-ask` second opinion, existing codex-advisor hooks (`codex-parallel`, `codex-watchdog`, `codex-broker`, `codex-review`, `codex-stop-opinion`, `codex-gate`) — **all unchanged and fully supported**. The new modes compose with existing infrastructure; they do not replace or disable any of it.
