## Test: Verification Before Done

### CLAUDE.md Blocking Rules
- Has inline test commands: YES (`uv run pytest` / `npm test` / `cargo test`)
- Has inline acceptance criteria check: YES ("Verify EACH acceptance criterion with evidence")
- Has "cat skill" reference: NO (correct -- no `cat .claude/skills/verification-before-completion/SKILL.md` in the blocking rule)
- Specific commands found:
  1. `uv run pytest` / `npm test` / `cargo test` (line 169)
  2. `mypy` / `tsc` / `cargo check` (line 170)
  3. "Verify EACH acceptance criterion with evidence" (line 171)
  4. "If ANY check fails -> fix first -> re-run -> NOT done" (line 172)
  5. "Update activeContext.md" (line 173)

### PROMPT.md (Ralph Loop)
- Has Section 4 (Verification): YES ("## 4. Verification (MANDATORY before advancing)")
- Has inline test commands: YES (`uv run pytest` / `npm test` / `cargo test`)
- References external skill files: NO (correct -- all rules are self-contained)

### Teammate Prompt Template
- Has inline Verification Rules section: YES ("## Verification Rules (MANDATORY)")
- Rules are actionable (not "read skill"): YES
  - "Run tests before claiming done"
  - "Verify each acceptance criterion with evidence"
  - "If any check fails -> fix first, do NOT claim done"

### VERDICT: PASS

All three files contain fully inline, actionable verification rules. No file references `cat .claude/skills/verification-before-completion/SKILL.md` in its verification section. The "Before done" blocking rule in CLAUDE.md provides concrete test commands (`uv run pytest`, `mypy`, etc.), explicit acceptance criteria checking, and a fail-fix-rerun guard -- all without requiring any external skill file to be loaded. The PROMPT.md and teammate template follow the same pattern with self-contained verification steps.
