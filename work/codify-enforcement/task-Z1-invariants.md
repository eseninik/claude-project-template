---
task_id: Z1
title: Codify Always-Dual enforcement — 4 invariants closing 12 bypass vectors
executor: dual
risk_class: high-stakes
speed_profile: thorough
---

# Task Z1 — Codify Always-Dual enforcement (4 invariants closing 12 bypass vectors)

## Goal

Make the dual-implement enforcement **structurally unbypassable** for any
code-writing operation a Claude Code session can perform in this repo.
Today the enforcer (`.claude/hooks/codex-delegate-enforcer.py`) misses 12
distinct vectors (work/** blanket exempt, Bash command mutations, stale
artifact reuse across multi-stage tasks, etc.). Close all 12 with **one
elegant rule expressed as four invariants** — minimal diff, maximum coverage.

## The Rule

> **CODE = CODEX. Always. Path doesn't matter. Tool doesn't matter.
> Session stage doesn't matter. Autonomy doesn't matter. If a tool call's
> EFFECT mutates a file with a code extension, there MUST be a Codex
> artifact whose Scope Fence EXPLICITLY LISTS THIS path, with
> `status: pass`, in the last 15 minutes. No exceptions, no path
> exemptions for code, no temporal carryover from unrelated stages.**

## Four Invariants (acceptance criteria expressed as behavior)

### Invariant 1 — Extension wins (path exemption is non-code only)

`is_code_extension(path)` is checked **before** `is_exempt(path)`.
Any file with an extension in `CODE_EXTENSIONS` requires a Codex cover
**regardless of where it lives**. Path exemptions (`work/**`,
`worktrees/**`, etc.) only protect non-code extensions (`.md`, `.json`,
`.yaml`, `.toml`, `.txt`, `.lock`, etc.).

Rationale: closes vectors 1, 8, 11 (work/** blanket exempt, freely-writable
.claude/scripts/, worktrees/** over-exemption). Helper scripts are code,
no matter where they live.

### Invariant 2 — Bash counts as a write (effect-based interception)

PreToolUse(Bash) parses the command and identifies code-path mutations:

**Mutating verbs/operators that require cover (when target has code ext):**
- `cp`, `mv`, `install`, `rsync`
- `rm` (deletion is a mutation)
- `sed -i`, `awk -i inplace`, `perl -i`
- `tee`, redirects `>`, `>>` to a code path
- `git apply`, `git mv`, `git rm`, `git checkout <ref> <code-path>`
- `git restore <code-path>`, `git reset --hard` (when working tree dirty on code paths)
- `python <script.py>`, `py -3 <script.py>`, `bash <script.sh>`, `sh <script>`,
  `node <script.js>`, `deno`, `ruby`, `perl <script.pl>` — flag the **script
  being executed**, since it can mutate downstream
- `python -c "open(...).write(...)"`, `python -c "import shutil; shutil.copy(...)"`
- `python -` / `bash -s` / `sh -c "<heredoc>"` — always require cover
  (cannot statically inspect)
- PowerShell mutating cmdlets: `Set-Content`, `Add-Content`, `Out-File`,
  `New-Item -ItemType File`, `Copy-Item`, `Move-Item`, `Remove-Item`,
  `[System.IO.File]::WriteAllText`, `[System.IO.File]::AppendAllText`
- `cat > <code-path>`, `cat >> <code-path>` (heredoc to code file)

**Whitelisted verbs (never require cover, never block):**
- Read-only: `ls`, `cat`, `head`, `tail`, `less`, `more`, `wc`, `file`, `stat`,
  `find` (without `-delete`/`-exec rm`), `grep`, `rg`, `ag`, `sort`, `uniq`,
  `cut`, `tr`, `diff`, `cmp`, `tree`
- Git read: `git status`, `git log`, `git diff`, `git show`, `git blame`,
  `git ls-files`, `git rev-parse`, `git branch --show-current`,
  `git remote`, `git fetch`, `git worktree list`
- Test/build runners (their own writes are bytecode/coverage, not source):
  `pytest`, `uv run pytest`, `unittest`, `mypy`, `ruff check`, `ruff format`
  (when invoked as check, not autofix), `npm test`, `yarn test`, `cargo test`,
  `go test`, `tsc --noEmit`, `eslint` (check), `prettier --check`
- Package managers (lock files are not code in CODE_EXTENSIONS):
  `uv sync`, `uv lock`, `pip install`, `npm install`, `pnpm install`,
  `cargo build`, `go mod`
- Project's own dual-implement tooling:
  `python .claude/scripts/codex-implement.py`, `codex-wave.py`,
  `codex-inline-dual.py`, `dual-teams-spawn.py`, `dual-teams-selftest.py`,
  `judge.py`, `judge_axes.py`, `codex-ask.py` — these ARE the dual workflow

**Special-case explicit cover requirement (always cover, no whitelist):**
- `python -` / `bash -s` / `sh -c` / `pwsh -c` — opaque heredoc-to-interpreter
- Any `*.py / *.sh / *.js / *.ts / *.rb / *.pl` script execution that is NOT
  in the project's own dual-implement whitelist above

Rationale: closes vectors 2 (NotebookEdit add to matcher), 3 (heredoc+git apply),
4 (sed -i / awk), 5 (cp/mv/rsync), 6 (PowerShell Set-Content), 7 (python -c),
10 (git checkout file restore).

### Invariant 3 — Path-exact coverage (no temporal carryover)

A Codex artifact's Scope Fence must **explicitly list** the target file
being mutated. "Any fresh pass result within 15 minutes" is **not** a
sufficient cover.

Implementation: `find_cover(target_path)` must return False unless
some artifact's parsed Scope Fence contains `target_path` (case-insensitive,
normalized, supports glob patterns like `src/auth/*.py`).

Rationale: closes vector 12 (15-min staleness window) AND the user-reported
multi-stage drift (autonomous task, stage 1 ran Codex, stage 2 didn't —
because stage 1's artifact was "fresh pass" but didn't cover stage 2's
files). Stage 2 now must run its own Codex.

### Invariant 4 — Skip-token audit + actionable block messages

Two parts:

**Part A — Skip-token ledger.** When the enforcer LEGITIMATELY allows a
write (cover found, OR truly exempt non-code path, OR whitelisted Bash),
it appends a structured JSONL entry to `work/codex-implementations/skip-ledger.jsonl`:
```json
{"ts":"2026-04-26T..","tool":"Bash","cmd":"pytest tests/","decision":"allow","reason":"whitelist"}
{"ts":"...","tool":"Edit","path":"src/auth.py","decision":"allow","reason":"covered-by:task-Z3-result.md"}
{"ts":"...","tool":"Edit","path":"src/auth.py","decision":"deny","reason":"no-cover-for-path"}
```
This makes silent bypasses impossible — every decision is in append-only audit.

**Part B — Actionable block message.** When the enforcer DENIES a write,
the error message includes a ready-to-run command to start the dual run for
THIS specific file:
```
BLOCK: no Codex cover for src/auth.py
Run this to start the dual-implement track for this file:

  py -3 .claude/scripts/codex-inline-dual.py \
    --describe "Edit/Write to src/auth.py" \
    --paths src/auth.py

Then retry your edit. Or for a multi-file task, use:
  py -3 .claude/scripts/dual-teams-spawn.py --tasks <task.md> ...
```

Rationale: removes the "I forgot, retry blindly" failure mode. Closes the
proactive-companion gap from research findings.

## Scope Fence — files you MAY modify

```
.claude/hooks/codex-delegate-enforcer.py
.claude/hooks/test_codex_delegate_enforcer.py
.claude/settings.json
CLAUDE.md           (only the "Code Delegation Protocol" section + "Exempt paths" subsection — preserve all other sections verbatim)
```

DO NOT modify any other file. Specifically NOT:
- `.claude/hooks/codex-gate.py` (overlapping but separate concern; document
  any required follow-up as `NOTE:` in self-report)
- `.claude/scripts/dual-teams-selftest.py` (Read-Only Evaluation Firewall)
- `.claude/scripts/judge.py`, `judge_axes.py` (Read-Only Evaluation Firewall)
- `work/codify-enforcement/task-Z1-invariants.md` (THIS spec — IMMUTABLE)

## Read-Only Files / Evaluation Firewall

These define the success criteria. Do NOT modify them; modifying them is
disqualifying:

- `work/codify-enforcement/task-Z1-invariants.md` (this file)
- `.claude/scripts/dual-teams-selftest.py` (must still pass after change)
- `.claude/scripts/judge.py`, `judge_axes.py` (judge will compare your diff)

## Acceptance Criteria (each must produce concrete evidence)

A new test file `.claude/hooks/test_codex_delegate_enforcer_invariants.py`
must contain ALL of the following test cases and ALL must pass via
`uv run pytest .claude/hooks/test_codex_delegate_enforcer_invariants.py -q`
(or `python -m pytest` if uv is unavailable):

### AC-1 (Invariant 1 — Extension wins)
- `test_work_py_requires_cover()` — Edit on `work/sync-template-to-target.py` → DENY (was previously ALLOW)
- `test_work_md_still_exempt()` — Edit on `work/notes.md` → ALLOW
- `test_claude_scripts_py_requires_cover()` — Edit on `.claude/scripts/foo.py` → DENY
- `test_worktrees_py_outside_dual_requires_cover()` — Edit on `worktrees/random/foo.py` (NOT a dual-teams worktree) → DENY
- `test_worktrees_dual_teams_py_allow()` — Edit on a worktree containing `.dual-base-ref` sentinel → ALLOW (preserves Y6/Y11)

### AC-2 (Invariant 2 — Bash counts)
- `test_bash_python_script_in_work_requires_cover()` — Bash `py -3 work/sync-template-to-target.py` → DENY
- `test_bash_pytest_allow()` — Bash `pytest tests/` → ALLOW (whitelisted)
- `test_bash_cp_code_to_code_requires_cover()` — Bash `cp src/a.py src/b.py` → DENY
- `test_bash_cp_md_to_md_allow()` — Bash `cp README.md /tmp/` → ALLOW
- `test_bash_sed_i_on_code_requires_cover()` — Bash `sed -i 's/x/y/' src/auth.py` → DENY
- `test_bash_sed_i_on_md_allow()` — Bash `sed -i 's/x/y/' work/notes.md` → ALLOW
- `test_bash_redirect_to_code_requires_cover()` — Bash `echo "x" > src/foo.py` → DENY
- `test_bash_heredoc_to_code_requires_cover()` — Bash `cat > src/foo.py <<EOF\n...\nEOF` → DENY
- `test_bash_powershell_set_content_code_requires_cover()` — Bash `powershell -Command "Set-Content -Path src/foo.py -Value '...'"` → DENY
- `test_bash_powershell_set_content_md_allow()` — Bash `powershell -Command "Set-Content -Path notes.md -Value '...'"` → ALLOW
- `test_bash_git_apply_requires_cover()` — Bash `git apply patch.diff` → DENY (we cannot inspect patch contents safely)
- `test_bash_git_checkout_code_file_requires_cover()` — Bash `git checkout main src/auth.py` → DENY
- `test_bash_codex_ask_allow()` — Bash `py -3 .claude/scripts/codex-ask.py "..."` → ALLOW (project's own dual tooling)
- `test_bash_dual_teams_spawn_allow()` — Bash `py -3 .claude/scripts/dual-teams-spawn.py --tasks ...` → ALLOW
- `test_bash_python_dash_c_open_write_requires_cover()` — Bash `python -c "open('src/x.py','w').write('...')"` → DENY
- `test_bash_python_dash_c_print_allow()` — Bash `python -c "print(2+2)"` → ALLOW (no file mutation pattern)
- `test_bash_ls_allow()` — Bash `ls -la work/` → ALLOW
- `test_bash_git_status_allow()` — Bash `git status` → ALLOW

### AC-3 (Invariant 3 — Path-exact coverage)
- `test_artifact_covers_path_a_blocks_path_b()` — Codex artifact lists `src/a.py` in Scope Fence; Edit on `src/b.py` → DENY (no carryover)
- `test_artifact_covers_path_a_allows_path_a()` — Same artifact; Edit on `src/a.py` → ALLOW
- `test_glob_in_scope_fence_matches()` — Artifact lists `src/auth/*.py`; Edit on `src/auth/login.py` → ALLOW
- `test_stale_artifact_outside_15min_blocks()` — Artifact older than 15 min covering exact path → DENY (preserves existing TTL)
- `test_failed_artifact_blocks_even_if_covers_path()` — Artifact with `status: fail` covering path → DENY

### AC-4 (Invariant 4 — Audit ledger + actionable message)
- `test_skip_ledger_appends_on_allow()` — Allowed Edit appends one JSONL line to `work/codex-implementations/skip-ledger.jsonl` with `decision:"allow"` + reason
- `test_skip_ledger_appends_on_deny()` — Denied Edit appends one JSONL line with `decision:"deny"` + reason
- `test_skip_ledger_jsonl_parseable()` — All ledger lines parse as valid JSON with required keys (`ts`, `tool`, `decision`, `reason`)
- `test_block_message_includes_inline_dual_command()` — DENY error message contains the substring `codex-inline-dual.py --describe` and the actual target path

### AC-5 (regression — existing behavior preserved)
- `test_existing_36_tests_still_pass()` — `pytest .claude/hooks/test_codex_delegate_enforcer.py` → all 36 existing tests pass
- `test_dual_teams_selftest_still_passes()` — `py -3 .claude/scripts/dual-teams-selftest.py` → exit 0, 6/6 PASS

## Test Commands

Run in this order. ALL must succeed before claiming done.

```bash
# 1. New invariant tests (your additions)
python -m pytest .claude/hooks/test_codex_delegate_enforcer_invariants.py -q --tb=line

# 2. Existing enforcer tests (must still pass — regression)
python -m pytest .claude/hooks/test_codex_delegate_enforcer.py -q --tb=line

# 3. Existing gate tests (overlapping concern — must still pass)
python -m pytest .claude/hooks/test_codex_gate.py -q --tb=line

# 4. Selftest (system-level health)
python .claude/scripts/dual-teams-selftest.py

# 5. JSON validity of settings.json (we modified the matcher)
python -c "import json; json.load(open('.claude/settings.json'))"

# 6. Settings.json sanity — Bash matcher present
python -c "import json; s=json.load(open('.claude/settings.json')); m=s['hooks']['PreToolUse'][0]['matcher']; assert 'Bash' in m, f'Bash not in matcher: {m}'; print('OK matcher:', m)"
```

## Implementation hints (non-binding — pick what fits your design)

- For Bash command parsing: use `shlex.split()` for tokenization (handles
  quotes correctly), then a small token-classifier. Keep the parser pure
  Python stdlib — no external deps.
- For Scope Fence parsing: existing `find_cover()` already reads result
  files. Extend its parser to extract a list of paths (current implementation
  may only check existence — verify by reading the file). Use `pathlib.Path`
  + `fnmatch` for glob support.
- For skip-ledger: open in `"a"` (append) mode, write one JSON line, flush.
  Path: `work/codex-implementations/skip-ledger.jsonl`. Create parent dir
  if missing. Catch and swallow ledger-write errors (log via stderr) — never
  let ledger I/O failure block the enforcement decision.
- For settings.json: change `"matcher": "Edit|Write|MultiEdit"` to
  `"matcher": "Edit|Write|MultiEdit|Bash|NotebookEdit"`. Be conservative
  on adding hooks — keep existing chain order.
- For CLAUDE.md update: locate the `## Code Delegation Protocol — Always Dual`
  section and the `### Exempt paths` subsection. Replace ONLY the bullet for
  `work/**` with one that says "non-code only", and add a new subsection
  `### The Four Invariants` immediately after `### Rule`. Preserve everything
  else verbatim. ~10-15 lines net change in CLAUDE.md.

## Logging requirements

Every modified function in `codex-delegate-enforcer.py` MUST have:
- `logger.info("entry: <name>", extra={...params...})` at function start
- `logger.info("exit: <name>", extra={duration_ms, decision, ...})` at end
- `logger.exception(...)` in every `except` block

The existing file already uses stdlib `logging`. Mirror its pattern.

## Self-report format (when done)

End your run with this block:

```
=== TASK Z1 SELF-REPORT ===
- status: pass | fail | blocker
- new tests added: <count>
- existing tests still passing: <count> / <expected total>
- selftest: PASS / FAIL
- settings.json json-valid: yes / no
- net lines added: <approx>
- files modified: [list]
- NOTE: <anything reviewer should know — surprising decisions, hidden constraints, follow-ups>
- BLOCKER: <only if status=blocker — explain what stopped you>
=== END SELF-REPORT ===
```
