---
task_id: Z7-v02-v03-fixes
title: Close V02 (NotebookEdit) and V03 (newline-chained Bash) enforcer gaps revealed by Z5
executor: dual
risk_class: high-stakes
speed_profile: balanced
---

# Task Z7 — Close 2 enforcer gaps from Z5 live attack matrix

## Goal

Z5 live attack matrix revealed 2 of 18 vectors that bypass the Z1
enforcer in the real binary contract:

- **V02 — NotebookEdit on a notebook** is not blocked because `.ipynb`
  is not in `CODE_EXTENSIONS` and `_decide_edit` short-circuits to allow
  before checking the tool name. Notebooks contain executable code; they
  should be in scope.
- **V03 — Bash command with cat-heredoc followed on a new line by
  `git apply`** is not blocked because `_split_logical_commands` only
  splits on `; && || |` separators — newlines are NOT a separator, so
  the entire blob is parsed as one `cat` command (read-only whitelisted)
  and the trailing `git apply` is masked.

Fix both with minimal diff.

## Two fixes (one file, ~15-30 LOC)

### Fix V02 — `.ipynb` is code

In `.claude/hooks/codex-delegate-enforcer.py` add `.ipynb` to
`CODE_EXTENSIONS` (it's a frozenset). One-line change.

Rationale: `.ipynb` notebooks contain executable Python (and sometimes
JS/SQL/etc) cells. They are code in every meaningful sense. The
existing extension dispatch already routes `NotebookEdit` to the
edit-decision branch — the extension just needs to be recognized.

Note: this also applies to plain `Edit` of a `.ipynb` file, which is
the correct behavior.

### Fix V03 — Newlines split logical commands

In `.claude/hooks/codex-delegate-enforcer.py` find
`_split_logical_commands(cmd: str) -> list[str]`. Add `\n` to its
separator set.

Implementation hint (your design may differ):

```python
def _split_logical_commands(cmd: str) -> list[str]:
    """Split a Bash command line on logical operators that mean 'next command'.
    Operators: ; && || | and newline. Quotes preserved."""
    # ... existing logic split on ; && || | now also splits on \n outside quotes
```

The simplest approach: extend the existing tokenizer/splitter so that
an unquoted `\n` is treated like `;` (terminate current command, start
next). Heredocs are tricky — IF the existing logic supports heredoc
preservation (`<<EOF ... EOF`), keep that working. If not, the simpler
fix is: split on EVERY raw `\n` not inside quotes, then for each
sub-command run the existing classification.

This will correctly catch:
- `cat > file.diff <<EOF\n...content...\nEOF\ngit apply file.diff` →
  the trailing `git apply` is now its own command and gets classified.

Acceptable tradeoff: heredocs whose body contains code-like tokens
might confuse classification. Treat false-positives as preferable to
the known false-negative we're closing.

## Scope Fence — files you MAY modify

```
.claude/hooks/codex-delegate-enforcer.py
```

DO NOT modify any other file. The existing tests
(`test_codex_delegate_enforcer.py`,
`test_codex_delegate_enforcer_invariants.py`,
`test_enforcer_live_attacks.py`) are read-only — they validate your
fix. Modifying them is disqualifying.

## Read-Only Files / Evaluation Firewall

- `work/codify-enforcement/task-Z7-v02-v03-fixes.md` (this file)
- `.claude/hooks/test_codex_delegate_enforcer.py`
- `.claude/hooks/test_codex_delegate_enforcer_invariants.py`
- `.claude/hooks/test_enforcer_live_attacks.py`
- `.claude/scripts/judge.py` etc.

## Acceptance Criteria

After your changes the live attack matrix must produce 18/18 PASS:

```bash
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -v --tb=short
```

Specifically:
- `test_v02_notebook_edit_denied` → PASS (was failing)
- `test_v03_bash_heredoc_git_apply_denied` → PASS (was failing)
- All 16 other tests still PASS

AND existing tests still pass:
```bash
python -m pytest .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_gate.py .claude/scripts/test_codex_ask.py -q --tb=line
python .claude/scripts/dual-teams-selftest.py
```

105 existing tests must remain GREEN. If any regress, fix before claiming done.

## Test Commands

```bash
# 1. Live attack matrix — 18/18 must PASS
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -v --tb=short

# 2. Regression suite
python -m pytest .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_gate.py .claude/scripts/test_codex_ask.py -q --tb=line

# 3. Selftest
python .claude/scripts/dual-teams-selftest.py
```

## Implementation hints

- The CODE_EXTENSIONS frozenset is at the top of the file (~line 30).
  One-line addition.
- `_split_logical_commands` should be findable by grep
  `grep -n "_split_logical_commands\|split_logical" .claude/hooks/codex-delegate-enforcer.py`.
- Test your fixes locally in the worktree BEFORE committing:
  `python -m pytest .claude/hooks/test_enforcer_live_attacks.py::test_v02_notebook_edit_denied -v`
  and `::test_v03_bash_heredoc_git_apply_denied`.
- Minimal diff — every line traces to V02 or V03.

## Logging requirements

Modified function: at minimum keep existing log statements; if you add
a new branch (e.g. for newline splitting), add `logger.debug` describing
the split. Don't add new logger.info noise.

## Self-report format

```
=== TASK Z7 SELF-REPORT ===
- status: pass | fail | blocker
- v02 fix approach: <1 line>
- v03 fix approach: <1 line>
- live attack matrix: 18/18 PASS  / <X>/18 PASS
- 105 existing tests still passing: yes / no
- selftest: PASS / FAIL
- net lines added: <approx>
- files modified: [.claude/hooks/codex-delegate-enforcer.py]
- NOTE: <surprising findings>
- BLOCKER: <only if blocker>
- Final commit SHA: <git rev-parse HEAD>
=== END SELF-REPORT ===
```
