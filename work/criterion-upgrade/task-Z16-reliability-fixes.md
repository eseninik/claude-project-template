---
task_id: Z16-reliability-fixes
title: Criterion 2 (Reliability) 6→10 — codex-implement repo-current parser + PowerShell-primary + Y20 audit
executor: dual
risk_class: high-stakes
speed_profile: balanced
---

# Task Z16 — Three Reliability fixes

## Goal

Criterion 2 (Reliability) currently 6/10 because:
- Self-referential parser bug: Z12 codex-implement rolled back Codex's
  work because worktree's pre-Z11 parser couldn't read code-block fence.
  The very Z12 fix would have closed the parser bug — but it never
  landed because the rollback ate Codex's diff.
- Y14 PowerShell labeled as "fallback" in spawn-agent prompts; in
  reality every Claude sub-agent run hits Y14 denial then dances. Should
  be PRIMARY from the start.
- Y20 status state machine — fixed `tests_ok=True ∧ codex_returncode≠0`
  case, but Z9 still hit "status:fail" surprise. Audit needed.

## Three coordinated fixes

### Fix 1 — codex-implement uses REPO-CURRENT parser (closes self-referential bug)

In `.claude/scripts/codex-implement.py`, the `run_scope_check` function
invokes `<worktree>/.claude/scripts/codex-scope-check.py` (line ~989).
That worktree-local copy is FROZEN at worktree-create-time. If a
parser bug fix is the very thing being merged, the worktree still has
the buggy parser and rolls back the fix.

Change: invoke the REPO-CURRENT parser, not the worktree-local one:
```python
# Before (frozen):
script = project_root / ".claude" / "scripts" / "codex-scope-check.py"
# project_root may be the WORKTREE — frozen at worktree-create

# After (always current):
import os
repo_root = Path(os.environ.get("CLAUDE_PROJECT_DIR")
                 or _find_main_repo_root(project_root))
script = repo_root / ".claude" / "scripts" / "codex-scope-check.py"
```

Where `_find_main_repo_root(worktree_path)` walks up looking for the
**non-worktree** repo root (usable git working tree where
`.git/worktrees/...` exists, NOT a worktree itself).

Add tests:
- `test_run_scope_check_uses_repo_current_parser` — patch
  `CLAUDE_PROJECT_DIR` env var, verify the helper resolves the script
  path against env, not against worktree.
- `test_run_scope_check_falls_back_to_worktree_when_no_env` — when
  `CLAUDE_PROJECT_DIR` unset and `_find_main_repo_root` cannot find
  parent, fall back to worktree script (current behavior).

### Fix 2 — spawn-agent.py promotes PowerShell to PRIMARY

In `.claude/scripts/spawn-agent.py`, the Y14 instruction block
currently says "Try Edit/Write first; on denial, use the PowerShell or
git apply fallback." This wastes a tool call on every sub-agent run
(invariably denied → retry).

Change wording to: "Use PowerShell `Invoke-Expression $scriptText` as
your PRIMARY file-write mechanism. Edit/Write/MultiEdit are blocked at
the harness Permission UI for sub-agents (Y14, design intent). Do not
attempt them first — go straight to PowerShell."

Plus: provide a complete **template** in the prompt so sub-agents copy-paste
without thinking:
```powershell
$content = @'
<file content>
'@
[System.IO.File]::WriteAllText("C:\\path\\to\\file", $content, [System.Text.UTF8Encoding]::new($false))
```

The `[System.Text.UTF8Encoding]::new($false)` part eliminates BOM
issue Z11 hit.

Add test:
- `test_spawn_agent_prompt_has_powershell_primary_section` — generate
  a prompt for a sample task, assert the resulting prompt contains
  "PRIMARY file-write mechanism" AND `[System.Text.UTF8Encoding]::new($false)`
  AND does NOT say "fallback" near "PowerShell".

### Fix 3 — Y20 audit + test for any remaining status:fail edge case

Add test:
- `test_status_pass_when_only_codex_returncode_nonzero_and_no_modifications`
  — for verification-only tasks where Codex correctly does not modify
  files, even if codex_returncode=1, scope_status=pass, tests_ok=True →
  status MUST be 'pass' not 'fail'. (Z9 hit this; Y20 partial fix.)

If this case still produces 'fail' in current `determine_run_status`,
fix the helper to return 'pass' when scope_status='pass' AND
tests_ok=True regardless of codex_returncode (Y20 already does this —
add the test to verify and lock).

## Scope Fence — files you MAY modify

```
.claude/scripts/codex-implement.py
.claude/scripts/test_codex_implement.py
.claude/scripts/spawn-agent.py
.claude/scripts/test_spawn_agent.py
```

DO NOT modify any other file.

## Read-Only Files / Evaluation Firewall

- `work/criterion-upgrade/task-Z16-reliability-fixes.md` (this file)
- `.claude/hooks/codex-delegate-enforcer.py`, `codex-gate.py`
- `.claude/scripts/codex-scope-check.py` (the parser itself — we're
  fixing the *resolver* in codex-implement, not the parser)

## Acceptance Criteria

### AC-1: codex-implement scope-check uses repo-current parser
- `test_run_scope_check_uses_repo_current_parser` PASSES.
- Manual: in a worktree with `CLAUDE_PROJECT_DIR=<main-repo>`, ensure
  `_resolve_scope_check_script(project_root)` returns
  `<main-repo>/.claude/scripts/codex-scope-check.py`, not the worktree's.

### AC-2: spawn-agent emits PowerShell-primary instructions
- `test_spawn_agent_prompt_has_powershell_primary_section` PASSES.

### AC-3: Y20 verification-only edge case locked by test
- `test_status_pass_when_only_codex_returncode_nonzero_and_no_modifications` PASSES.

### AC-4: Existing test_codex_implement (72) still passes (no regression)
```bash
python -m pytest .claude/scripts/test_codex_implement.py -q --tb=line
```

### AC-5: Existing test_spawn_agent (5) still passes
```bash
python -m pytest .claude/scripts/test_spawn_agent.py -q --tb=line
```

### AC-6: Live attack matrix 25/25 still passes
```bash
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -q --tb=line
```

### AC-7: Selftest still passes
`python .claude/scripts/dual-teams-selftest.py` → 6/6 PASS

## Test Commands

```bash
# 1. New + existing test_codex_implement
python -m pytest .claude/scripts/test_codex_implement.py -q --tb=line

# 2. spawn-agent tests
python -m pytest .claude/scripts/test_spawn_agent.py -q --tb=line

# 3. Live attack matrix (regression)
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -q --tb=line

# 4. Other suites
python -m pytest .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line

# 5. Selftest
python .claude/scripts/dual-teams-selftest.py
```

## Implementation hints

- For Fix 1: `_find_main_repo_root(p: Path) -> Optional[Path]` walks up `p`
  looking for a directory whose `.git` is a directory (not a file
  pointing to a worktree). Stop at filesystem root. Return None if
  not found.
- For Fix 2: locate the existing Y14 block in `spawn-agent.py` via
  `grep -n "Y14\|sub-agent.*Write\|file write" .claude/scripts/spawn-agent.py`. Replace its
  language; add the complete PowerShell template.
- For Fix 3: `determine_run_status` is the helper extracted in Z11.
  Verify its behavior matches AC-3; if not, fix the precedence.
- Logging: each new function has entry/exit logs.

## Self-report format

```
=== TASK Z16 SELF-REPORT ===
- status: pass | fail | blocker
- Fix 1 (repo-current parser) approach: <1 line>
- Fix 2 (PowerShell primary) approach: <1 line>
- Fix 3 (Y20 audit) approach: <1 line>
- new tests added: <count>
- existing 72+5 test_codex_implement+spawn_agent pass: yes / no
- live attack matrix 25/25: yes / no
- selftest 6/6: PASS / FAIL
- net lines: <approx>
- files modified: [list]
- NOTE: <surprising>
- BLOCKER: <only if>
- Final commit SHA: <SHA>
=== END SELF-REPORT ===
```
