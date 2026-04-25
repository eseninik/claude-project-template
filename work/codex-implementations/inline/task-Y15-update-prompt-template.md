---
executor: dual
risk_class: routine
reasoning: high
speed_profile: balanced
---

# Task Y15: codify Y14 finding in `.claude/guides/teammate-prompt-template.md` + project `CLAUDE.md`

## Your Task

Y14 (commit `1c5490b`) empirically confirmed: **Claude Code harness denies sub-agent `Write/Edit/MultiEdit` at the permission layer regardless of any configurable lever** (hooks, settings.json `permissions.allow`, Agent tool `mode` parameter — all 4 escalating attempts FAIL). The "STOP and explain to the user" message is design intent. Sub-agents must use Bash + PowerShell `Set-Content` / `[System.IO.File]::WriteAllText` as their **primary** file-creation mechanism, not as a fallback after Write fails.

The current `.claude/guides/teammate-prompt-template.md` says "use Bash heredoc IF target file > 250 lines" — that framing is wrong post-Y14: heredoc/PowerShell are needed for ALL sub-agent file creation, not just large ones. This task brings docs into line with reality.

Two files to update:
1. `.claude/guides/teammate-prompt-template.md` — replace the size-conditional advice with unconditional "PowerShell-first" pattern.
2. `CLAUDE.md` (project root) — add a short note in the Code Delegation Protocol section pointing teammate-spawners at the new canonical pattern.

## Scope Fence

**Allowed:**
- `.claude/guides/teammate-prompt-template.md` (modify)
- `CLAUDE.md` (modify — project root)

**Forbidden:** any other path.

## Test Commands

```bash
grep -E "PowerShell|Set-Content|Write tool denial|Y14" .claude/guides/teammate-prompt-template.md
grep -E "Y14|PowerShell.*sub-agent|teammate.*workaround" CLAUDE.md
py -3 -c "from pathlib import Path; t=Path('.claude/guides/teammate-prompt-template.md').read_text(encoding='utf-8'); assert 'PowerShell' in t and 'Set-Content' in t and 'Y14' in t, 'template missing canonical pattern'; print('template ok, len=', len(t))"
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: `.claude/guides/teammate-prompt-template.md` gains a new top-level section titled `## File creation in sub-agent context (Y14 finding)` placed BEFORE the existing "If your target file will exceed ~250 lines" subsection. Content covers:
  - One-paragraph summary of Y14 (Write tool denied at harness level for sub-agents, regardless of mode/permissions/hooks)
  - **Canonical pattern** = PowerShell `Set-Content -Encoding utf8 -Path <abs> -Value <here-string>`. Includes a concrete bash snippet showing the invocation.
  - Secondary fallback = Bash heredoc + git apply. Concrete snippet.
  - Note that `Edit` tool may behave similarly — try once via Edit if file already exists, fall back to PowerShell if denied.
  - Explicit pointer: "Do NOT spend cycles fighting the harness. The denials are design intent, not a bug. PowerShell IS the canonical mechanism."
- [ ] AC2: The existing "If your target file will exceed ~250 lines" subsection is REWORDED or REMOVED — the size threshold no longer applies (PowerShell is canonical for ALL writes, regardless of size).
- [ ] AC3: `CLAUDE.md` (project root) gets a short note (~5 lines) in the existing "Code Delegation Protocol" section pointing teammate-spawners at the updated `teammate-prompt-template.md` for the canonical PowerShell pattern. Reference Y14 commit (`1c5490b`).
- [ ] AC4: Both files remain syntactically valid markdown. No broken section anchors, no stray HTML, no lines > 200 chars.
- [ ] AC5: PowerShell snippet must work on Windows out of the box. Use `Set-Content -Encoding utf8 -NoNewline:$false`. Do NOT recommend `Out-File` (BOM issues) or `echo > file` (encoding issues).
- [ ] AC6: All Test Commands above exit 0.

## Constraints

- Both target files are EXEMPT paths under `codex-delegate-enforcer.py` (`.claude/guides/**/*.md` and `CLAUDE.md`). Edit/Write tool will not be hook-blocked; only the harness Permission UI may deny — fall back to PowerShell if so.
- Surgical: don't touch any file outside the Scope Fence. Don't reformat unrelated sections.
- Keep tone consistent with existing docs (terse, imperative, examples-first).
- Do NOT propagate to `.claude/shared/templates/new-project/` — that's a separate sync task per project CLAUDE.md ("LOCAL only until PoC validates").

## Handoff Output

Standard `=== PHASE HANDOFF: Y15-prompt-template ===` with:
- Diff stats per file (lines added/removed)
- Test command outputs (all 3 grep/python checks)
- One-line note documenting WHICH file-write mechanism was used (Edit / Write / PowerShell / Bash heredoc) for each file modification — this is part of the empirical record.
