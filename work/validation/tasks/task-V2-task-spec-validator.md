---
executor: dual
risk_class: routine
reasoning: high
speed_profile: balanced
---

# Task V-2: `.claude/scripts/task-spec-validator.py` — lint task-N.md files

## Your Task

Stand-alone lint CLI that validates `work/**/tasks/task-*.md` files against the canonical structure defined by `.claude/shared/work-templates/task-codex-template.md`. Catches missing sections, malformed frontmatter, weak acceptance criteria, scope-fence violations.

Called BEFORE dispatching any task to dual-teams-spawn.py / codex-implement.py to prevent teammates from wasting cycles on broken specs.

## Scope Fence

**Allowed:**
- `.claude/scripts/task-spec-validator.py` (new)
- `.claude/scripts/test_task_spec_validator.py` (new)

**Forbidden:** any other path.

## Test Commands

```bash
py -3 .claude/scripts/test_task_spec_validator.py
py -3 .claude/scripts/task-spec-validator.py --help
py -3 .claude/scripts/task-spec-validator.py work/fixes/tasks/task-FIX-A-judge-diff-baseline.md
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: CLI signature: `task-spec-validator.py [--json] [--strict] [--project-root PATH] <spec-file> [<spec-file>...]`. Accepts one or more spec paths; glob expansion via shell.
- [ ] AC2: For each file, performs these checks (each contributes to the report):
  - `frontmatter.present` — file starts with `---\n<yaml>\n---\n`
  - `frontmatter.executor` — value in `{claude, codex, dual}`
  - `frontmatter.risk_class` — value in `{routine, high-stakes}`
  - `section.your_task` — `## Your Task` section present + non-empty
  - `section.scope_fence` — `## Scope Fence` present, contains at least "**Allowed:**" and "**Forbidden:**" markers
  - `section.test_commands` — `## Test Commands` present, contains at least one fenced `bash` code block with non-empty commands
  - `section.acceptance_criteria` — `## Acceptance Criteria (IMMUTABLE)` (or "Acceptance Criteria") present with ≥ 5 checkbox items (`- [ ]` or `- [x]`)
  - `section.handoff` — `## Handoff Output` section present
  - `acceptance.contains_all_tests_pass` — ACs list includes at least one "All Test Commands ... exit 0" style item
- [ ] AC3: Each check returns `ok|warn|fail`. Default severity: missing section → `fail`, weak content (e.g. only 3 ACs) → `warn`, invalid frontmatter value → `fail`.
- [ ] AC4: Default output per spec:
  ```
  work/fixes/tasks/task-FIX-A-judge-diff-baseline.md:
    [OK]   frontmatter.present
    [OK]   frontmatter.executor (dual)
    [WARN] acceptance_criteria: 10 items (recommend ≥ 10)
    ...
    overall: ok/warn/fail
  SUMMARY: 1 file, 0 fail, 3 warn, 8 ok
  ```
- [ ] AC5: `--json` emits valid `{"files":[{"path","checks":[{"name","status","detail"}],"overall"}], "summary":{"fail":N,"warn":N,"ok":N,"files":N}}`.
- [ ] AC6: `--strict` escalates all warn → fail (exit 1 if ANY warn/fail); non-strict exits 0 if no fail, 1 if any fail.
- [ ] AC7: If a spec file doesn't exist → report `[FAIL] missing-file`, continue processing other specs, exit 1.
- [ ] AC8: Structured logging (JSON, stdlib `logging`, `--verbose` toggles DEBUG). Every check wrapped in try/except; on exception the check becomes `status=fail, detail=<exception msg>`.
- [ ] AC9: Stdlib only. Windows-compatible (pathlib). Under 350 lines script + 350 lines tests.
- [ ] AC10: Unit tests (≥12): (a) happy path passes all checks, (b) missing frontmatter → fail, (c) invalid executor value → fail, (d) missing Scope Fence → fail, (e) 3 ACs → warn, (f) no test commands block → fail, (g) `--strict` escalates warn→fail, (h) missing file → fail + exit 1, (i) multiple files, mixed results, (j) `--json` roundtrip, (k) `--json` schema complete, (l) exception during check → graceful `status=fail`.
- [ ] All Test Commands above exit 0.

## Constraints

- This validator is READ-ONLY — never modifies the input specs.
- Use `re.MULTILINE | re.DOTALL` carefully — spec sections are bounded by next `## ` heading.
- If a spec has its own `## Constraints` section with `heredoc` / platform-gotchas language, do NOT penalize — that's a feature, not a smell.
- If your file will exceed ~250 lines including logging, USE Bash heredoc (`cat > <path> <<'END_MARK'`) instead of Write — harness silently denies large Writes.
- Cross-platform: handle both `\n` and `\r\n` line endings gracefully.

## Handoff Output

Standard `=== PHASE HANDOFF: V-2-task-spec-validator ===` with sample run on this repo's existing task-FIX-A spec showing actual checks.
