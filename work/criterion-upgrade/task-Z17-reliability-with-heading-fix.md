---
task_id: Z17-reliability-with-heading-fix
title: Criterion 2 Reliability — 4 fixes including parse_scope_fence heading-suffix robustness
executor: dual
risk_class: high-stakes
speed_profile: balanced
---

# Task Z17

## Goal

Criterion 2 (Reliability) currently 6/10. Z16 attempted 3 fixes but
hit a self-referential rollback because task spec heading
`## Scope Fence — files you MAY modify` produced an empty fence
(em-dash suffix broke section extraction in codex-implement.py).
Z17 retries with plain `## Scope Fence` heading AND adds a 4th fix
that closes the heading-suffix issue for future task specs.

## Four coordinated fixes

### Fix 1 — codex-implement uses REPO-CURRENT parser

`run_scope_check` invokes the worktree-local `codex-scope-check.py`
which is FROZEN at worktree-create-time. If a parser fix is the very
thing being merged, the worktree still has the buggy parser and rolls
back the fix.

Resolve `CLAUDE_PROJECT_DIR` env var first; else walk up from worktree
to find the non-worktree repo root; else fall back to worktree-local.

Helper `_resolve_scope_check_script(project_root)` extracted for tests.

### Fix 2 — spawn-agent.py promotes PowerShell to PRIMARY

Replace existing Y14 "fallback" wording with "PRIMARY mechanism".
Provide complete template with `[System.Text.UTF8Encoding]::new($false)`
to eliminate BOM (Z11 hit this).

### Fix 3 — Y20 verification-only edge case test

Test locks `tests_ok=True ∧ scope_status='pass' ∧ codex_returncode!=0
∧ no actual file modifications → status='pass'`. Verifies Y20 fix
from Z11 holds for verification-only Codex runs.

### Fix 4 — parse_scope_fence robust to heading suffix (NEW)

Section parser currently uses exact heading text. Heading
`## Scope Fence — files you MAY modify` produces section name
`Scope Fence — files you MAY modify`, not `Scope Fence`.

Change: when heading contains ` — ` (em-dash + spaces) or ` - ` (hyphen
+ spaces) AFTER the first word, also register the prefix as alias.
Use `re.split(r"\s[-—]\s", heading_text, maxsplit=1)[0].strip()`.

## Scope Fence

```
.claude/scripts/codex-implement.py
.claude/scripts/test_codex_implement.py
.claude/scripts/spawn-agent.py
.claude/scripts/test_spawn_agent.py
```

DO NOT modify any other file.

## Read-Only Files / Evaluation Firewall

- `work/criterion-upgrade/task-Z17-reliability-with-heading-fix.md` (this file)
- `.claude/hooks/codex-delegate-enforcer.py`
- `.claude/scripts/codex-scope-check.py`

## Acceptance Criteria

### AC-1: Fix 1 tests pass

Three new tests in `test_codex_implement.py`:
- `test_resolve_scope_check_uses_env_var` — when env CLAUDE_PROJECT_DIR set, uses that
- `test_resolve_scope_check_walks_up_from_worktree` — no env, walks up to non-worktree root
- `test_resolve_scope_check_falls_back_to_worktree` — neither yields → worktree script

### AC-2: Fix 2 test passes

`test_spawn_agent_prompt_has_powershell_primary_section` in `test_spawn_agent.py`.
Generated prompt MUST contain "PRIMARY" near "PowerShell" AND
`[System.Text.UTF8Encoding]::new($false)` AND must NOT contain "fallback"
within 5 lines of the PowerShell instruction.

### AC-3: Fix 3 test passes

`test_status_pass_when_only_codex_returncode_nonzero_and_no_modifications`
in `test_codex_implement.py`. Locks Y20 behavior.

### AC-4: Fix 4 tests pass

Four new tests in `test_codex_implement.py`:
- `test_parse_section_handles_em_dash_suffix` — `## Scope Fence — desc`
  yields section accessible by `Scope Fence`
- `test_parse_section_handles_hyphen_suffix` — `## Test Commands - desc` ditto
- `test_parse_section_no_suffix_unchanged` — plain `## Scope Fence` works
- `test_parse_scope_fence_em_dash_heading_yields_paths` — full integration:
  task spec with em-dash heading + code-block paths → returned list non-empty

### AC-5: Existing 72 test_codex_implement + 5 test_spawn_agent still pass

```bash
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_spawn_agent.py -q --tb=line
```

### AC-6: Live attack matrix 25/25 still passes

```bash
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -q --tb=line
```

### AC-7: Selftest still passes

`python .claude/scripts/dual-teams-selftest.py` → 6/6 PASS

## Test Commands

```bash
# 1. test_codex_implement
python -m pytest .claude/scripts/test_codex_implement.py -q --tb=line

# 2. test_spawn_agent
python -m pytest .claude/scripts/test_spawn_agent.py -q --tb=line

# 3. Live attack matrix (regression)
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -q --tb=line

# 4. Other suites
python -m pytest .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line

# 5. Selftest
python .claude/scripts/dual-teams-selftest.py
```

## Implementation hints

- Fix 1: `_find_main_repo_root(p: Path) -> Optional[Path]` walks up looking for a directory whose `.git` is a directory (not a file pointing to a worktree).
- Fix 4: locate the section parser via `grep -n "sections\[\|sections.update\|^def parse_task\|## " codex-implement.py`. After registering exact heading, also register the prefix-before-em-dash-or-hyphen as alias.
- For testing Fix 4, use literal `## Scope Fence — embedded em-dash` in test fixtures (string literal, not file). Do NOT use em-dash in section headings of THIS task spec — keep this spec safe.
- Logging: each new helper has entry/exit logs.

## Self-report format

```
=== TASK Z17 SELF-REPORT ===
- status: pass | fail | blocker
- Fix 1 (repo-current parser) approach: <1 line>
- Fix 2 (PowerShell primary) approach: <1 line>
- Fix 3 (Y20 audit) approach: <1 line>
- Fix 4 (heading suffix robust) approach: <1 line>
- new tests added: <count>
- existing 77 tests still pass: yes / no
- live attack matrix 25/25: yes / no
- selftest 6/6: PASS / FAIL
- net lines: <approx>
- files modified: [list]
- NOTE: <surprising>
- BLOCKER: <only if>
- Final commit SHA: <SHA>
=== END SELF-REPORT ===
```
