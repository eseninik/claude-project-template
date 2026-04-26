---
task_id: Z5-live-attack-matrix
title: End-to-end live attack matrix for codex-delegate-enforcer (12 bypass vectors via fake-codex shim)
executor: dual
risk_class: high-stakes
speed_profile: thorough
---

# Task Z5 — Live attack matrix for codex-delegate-enforcer

## Goal

Build a **subprocess-level live integration test harness** that proves
all 12 documented bypass vectors are blocked by the Z1 enforcer, AND
that the 6 positive controls are allowed. Each test crafts a `PreToolUse`
JSON payload, pipes it via stdin into `python .claude/hooks/codex-delegate-enforcer.py`
as a subprocess, asserts exit code (2=deny, 0=allow) + stderr substring.

Why beyond the existing 35 unit tests:
- Unit tests `import` the hook module — they may miss env-var, working
  directory, stdin parsing, or process-spawn bugs that only surface in
  the actual subprocess invocation Claude Code harness uses.
- Z1 documents 12 bypass vectors. Unit tests cover ~7-8. We need EVERY
  vector exercised live at the binary contract level.
- The harness becomes the regression suite for any future enforcer change.

**Codex review feedback baked into this design:** use a **fake codex
shim** for tests that depend on Codex availability (PATH-injected fake
`codex.cmd`). Do NOT rely on real installed Codex. This makes tests
deterministic regardless of developer's CLI state.

## The 18 test cases (12 deny + 6 allow)

### Deny cases (each must produce exit code 2 + reason in stderr)

| # | Vector | Crafted tool call |
|---|--------|-------------------|
| V1 | `work/**` blanket exemption (Invariant 1) | `Edit(file_path="work/sync-template-to-target.py")` |
| V2 | NotebookEdit not intercepted (Invariant 2) | `NotebookEdit(notebook_path="src/foo.ipynb", new_source="...")` |
| V3 | Bash heredoc + git apply | `Bash(command="cat > /tmp/p.diff <<EOF\\n...\\nEOF\\ngit apply /tmp/p.diff")` |
| V4 | Bash sed -i on code | `Bash(command="sed -i 's/x/y/g' src/main.py")` |
| V5 | Bash cp/mv between code paths | `Bash(command="cp src/a.py src/b.py")` |
| V6 | PowerShell Set-Content on code | `Bash(command='powershell -NoProfile -Command "Set-Content -Path src/foo.py -Value test"')` |
| V7 | python -c with file write | `Bash(command='python -c "open(\\'src/x.py\\',\\'w\\').write(\\'\\')"')` |
| V8 | Edit on `.claude/scripts/**/*.py` | `Edit(file_path=".claude/scripts/rogue.py")` |
| V9 | Bash invokes a script that mass-mutates | `Bash(command="py -3 work/sync-template-to-target.py --apply")` |
| V10 | git checkout file restore | `Bash(command="git checkout main src/auth.py")` |
| V11 | `worktrees/**` over-exemption (no sentinel) | `Edit(file_path="worktrees/random-not-dual-teams/foo.py")` (where that worktree has NO `.dual-base-ref`) |
| V12 | 15-min staleness with wrong path | `Edit(file_path="src/new.py")` while a recent (<15 min) result.md covers `src/old.py` only |

### Allow cases (each must produce exit code 0)

| # | Allow case | Sample |
|---|------------|--------|
| A1 | Edit on `.md` in `work/` | `Edit(file_path="work/notes.md")` |
| A2 | Bash `pytest` | `Bash(command="pytest tests/")` |
| A3 | Bash `git status` | `Bash(command="git status")` |
| A4 | Bash `cp README.md /tmp/` | `Bash(command="cp README.md /tmp/")` |
| A5 | Edit inside `.dual-base-ref` worktree (sentinel allows) | `Edit(file_path="<tmp_worktree>/.claude/foo.py")` where `<tmp_worktree>/.dual-base-ref` exists |
| A6 | Edit with valid recent path-exact cover | `Edit(file_path="src/auth.py")` after writing `task-fake-result.md` with `status:pass` and Scope Fence containing `src/auth.py` |

## Scope Fence — files you MAY modify

```
.claude/hooks/test_enforcer_live_attacks.py
```

DO NOT modify any other file. If you discover a real enforcer bug while
running tests, do NOT fix the enforcer in this run — record as `NOTE:`
in self-report so a follow-up can address it. This task only BUILDS the
test matrix.

## Read-Only Files / Evaluation Firewall

- `work/codify-enforcement/task-Z5-live-attack-matrix.md` (this file)
- `.claude/hooks/codex-delegate-enforcer.py` (DO NOT modify, only invoke as subprocess)
- `.claude/hooks/test_codex_delegate_enforcer.py`,
  `.claude/hooks/test_codex_delegate_enforcer_invariants.py` (reference only)

## Acceptance Criteria

A new test file `.claude/hooks/test_enforcer_live_attacks.py` must exist
and contain ALL 18 test functions. The file must run via:

```bash
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -v --tb=short
```

Test naming convention (lowercase, descriptive):
- `test_v01_work_py_denied`, `test_v02_notebook_edit_denied`, …,
  `test_v12_stale_artifact_wrong_path_denied`
- `test_a01_work_md_allowed`, `test_a02_bash_pytest_allowed`, …,
  `test_a06_valid_cover_allowed`

Each test must:
1. Build a `PreToolUse` JSON payload as the dict the harness sends
   (use existing unit tests as schema reference — typically
   `{"tool_name": "...", "tool_input": {...}, "session_id": "..."}`)
2. Spawn the hook: `subprocess.run([sys.executable, str(HOOK_PATH)],
   input=json.dumps(payload), capture_output=True, text=True, timeout=10,
   env={**os.environ, "CLAUDE_PROJECT_DIR": str(REPO_ROOT)})`
3. For DENY tests: assert `r.returncode == 2`, assert reason substring
   in `r.stderr` (substring identifying invariant or target path).
4. For ALLOW tests: assert `r.returncode == 0`.

For tests requiring a recent cover artifact (V12, A6): use a `tmp_path`
pytest fixture to write a fake `task-fake-Z5-result.md` into
`work/codex-implementations/` of the repo root with appropriate
`status:pass` and Scope Fence content; clean up after test (use a
`yield` fixture).

For tests requiring a worktree directory (V11, A5):
- A5: create `tmp_path/wt/.dual-base-ref` (any content), then run hook
  with `CLAUDE_PROJECT_DIR=tmp_path/wt`, target a `.py` file inside.
- V11: create `tmp_path/worktrees/random/foo.py` (NO sentinel anywhere),
  then run hook with `CLAUDE_PROJECT_DIR=<repo root>`, target the file.
  The hook should NOT find `.dual-base-ref` walking up → DENY.

## Test Commands

ALL must succeed:

```bash
# 1. The new live attack matrix
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -v --tb=short

# 2. Existing 89 enforcer/gate/invariants tests (regression)
python -m pytest .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/scripts/test_codex_ask.py -q --tb=line

# 3. Selftest must still pass
python .claude/scripts/dual-teams-selftest.py
```

The new file's expected count: 18 test functions. **Some MAY fail** —
that is acceptable for THIS task because failures reveal genuine
enforcer gaps (Z7+ will fix). The deliverable is the test FILE itself
plus the gap inventory in the self-report.

## Implementation hints

- Use `pathlib.Path(__file__).resolve().parents[2]` to locate repo root
  from inside the test file.
- Use `subprocess.run(..., timeout=10)` — enforcer should be fast (<1s).
- Use `pytest.fixture` for `tmp_cover_artifact` and `tmp_worktree` so
  each test is hermetic.
- Use `pytest.mark.parametrize` if it makes the 12 deny tests cleaner —
  keep test names descriptive (so failures are obvious).
- Read the existing unit tests to understand the JSON schema the hook
  expects on stdin and how it returns deny/allow signals (exit code +
  optional JSON `permissionDecision` in stdout).
- For tests that need fresh cover, write the artifact ATOMICALLY before
  the subprocess call (write+close, then run).
- Prefer relative paths in payloads where possible.

## Logging requirements

The test file is a test file — no production logging required. Each
test SHOULD have a docstring explaining which vector it covers and the
expected reason substring. Example:
```python
def test_v05_bash_cp_code_to_code_denied(repo_root):
    """V5 — Bash cp between two code paths must DENY (Invariant 2)."""
    ...
```

## Self-report format

```
=== TASK Z5 SELF-REPORT ===
- status: pass | fail | blocker
- new tests added: <count> (expected 18)
- new tests PASSING (no enforcer gap): <count>
- new tests FAILING (real enforcer gap to fix in Z7+): <count>
- existing 105 tests still passing: yes / no
- selftest 6/6: PASS / FAIL
- net lines added: <approx>
- files modified: [list]
- enforcer-stdin-schema: <one line — what the hook expects>
- vectors that REVEALED a real enforcer gap: [list V01..V12 with brief reason]
- NOTE: <surprising findings>
- BLOCKER: <only if you couldn't even build the harness>
- Final commit SHA: <git rev-parse HEAD>
=== END SELF-REPORT ===
```
