# Z13 Findings — Vectors V13-V18 actual enforcer behavior

This task added 6 new live-attack tests to `.claude/hooks/test_enforcer_live_attacks.py`
to expand Functional Coverage from 19 to 25 vectors. Each new test asserts the
**EXPECTED CORRECT** enforcer behavior. Tests that fail today reveal real gaps
that task **Z14** will fix.

## Verification baseline

- Existing 19 tests (V01-V12 deny + A01-A07 allow): **all PASS** (no regression).
- New 6 tests (V13-V18): mixed — see table below.
- Other suites (`test_codex_implement.py`, `test_codex_inline_dual.py`,
  `test_codex_ask.py`, `test_judge.py`, `test_codex_delegate_enforcer_invariants.py`,
  `test_codex_delegate_enforcer.py`, `test_codex_gate.py`): **249 passed**.
- `dual-teams-selftest.py`: **6/6 PASS**.

## Per-vector results

| #   | Vector                                              | Test result | Real gap? | Recommended Z14 fix |
|-----|-----------------------------------------------------|-------------|-----------|---------------------|
| V13 | `schtasks /Create ... /TR "py -3 work/sync.py"`     | **FAIL**    | yes       | Add `schtasks`/`at`/`crontab`/`Register-ScheduledTask` to `_BASH_MUTATING_VERBS` (or a new scheduler set), and re-tokenize the `/TR` (Windows) / `-Command` / cron-line argument so the nested invocation is reclassified by the same parser. |
| V14 | `mcp__filesystem__write_file` MCP tool              | **FAIL**    | yes       | Two changes: (1) extend `decide()` dispatch to recognize any `tool_name` matching `^mcp__.*(write|edit|create|patch|put|append).*$` and treat its `tool_input.path` as the target; (2) update `.claude/settings.json` PreToolUse matcher from `Edit\|Write\|MultiEdit\|Bash\|NotebookEdit` to also include `mcp__.*`. |
| V15 | `./my-tool --output src/foo.py` (compiled binary)   | **FAIL**    | yes       | When `verb` is unknown (none of readonly/test-runner/package-manager/git/pwsh/inplace/mutating/interpreter), still scan all positional+flag-value tokens via `_extract_code_path_args` and require_cover if any code-extension path is present. Treat `./*` and `*.exe` argv[0] as "binary unknown" rather than fully allow. |
| V16 | `bash -s <<EOF\necho "x" > src/foo.py\nEOF`         | PASS        | no        | None — `bash -s` already triggers `bash-stdin-opaque` deny via the existing `has_dash_s` shortcut. (The newline-split also independently catches the redirect inside the heredoc body.) |
| V17 | `python -c "import json; print(open('config.json').read())"` | PASS        | no        | None — `_classify_interpreter` correctly treats this as `python-c-no-write` because the snippet has neither `,'w'`/`,'a'` patterns nor a `open(..., 'w'\|'a'` literal. The "currently DENIES" claim in the spec is outdated; current code already allows. |
| V18 | `NotebookEdit` cell with `%%bash\necho x > src/y.py` | PASS        | no (partial) | None for current code path: `.ipynb` is in `CODE_EXTENSIONS` (Z7-V02), so the edit denies on the extension alone. **Latent gap**: if the notebook path were ever non-`.ipynb`, the `new_source` body is not parsed, so cell-magic mutations would slip. Z14 could add a body-parse pass that scans `new_source` for `%%bash`, `%%sh`, `!` magic and reclassifies via `parse_bash_command`. Low priority — not a live bypass today. |

## Summary

- **Total new tests:** 6
- **Currently passing (no real gap):** 3 (V16, V17, V18)
- **Currently failing (real gap, fix in Z14):** 3 (V13, V14, V15)
- **Existing 19 tests still pass:** yes
- **Other test suites still pass:** yes (249/249)
- **Selftest:** 6/6 PASS

### Gaps discovered (Z14 target list)

1. **Scheduler/cron pass-through (V13)** — `schtasks`, `at`, `crontab`,
   `Register-ScheduledTask` are unknown verbs that smuggle nested code-writer
   invocations as opaque string args. The `/TR` (Windows) and cron-line
   payloads need to be re-tokenized and reclassified. Severity: **HIGH**
   (background persistence + invisible code mutation).

2. **MCP write tools (V14)** — Both the dispatcher and the settings.json
   matcher are blind to `mcp__*` tool names. Any MCP server providing a
   `write_file`/`edit_file` etc. tool currently bypasses the enforcer
   entirely. Severity: **HIGH** (clean bypass; no parser changes needed,
   just plumbing).

3. **Unknown-verb argv scan (V15)** — The existing parser only inspects
   positional argv for the known mutating/inplace branches. A compiled
   binary (`./my-tool`, `*.exe`, anything not in the seven recognized
   verb classes) currently allows any argv even when one of those args
   has a `.py`/`.ts`/etc. extension. Adding a "code-extension argv
   triggers cover" rule for the unknown-verb fallback closes this and
   is low-risk (pure tightening). Severity: **MEDIUM**.

### Notes on V17 / V18 false alarms in the task spec

- The spec for V17 said "currently this DENIES (false-positive)". Live test
  shows it ALREADY allows correctly. The spec was likely written against an
  earlier enforcer version; nothing to fix.
- The spec for V18 implied bash-magic was the deny driver. In reality the
  `.ipynb` extension alone causes the deny. The bash-magic cell-body parse
  is a latent improvement, not an active bypass — keeping the test as a
  guard against accidental removal of `.ipynb` from `CODE_EXTENSIONS`.

### Functional Coverage progress

- Before Z13: 19 vectors tested → Criterion 1 score 8/10.
- After Z13: 25 vectors tested → Criterion 1 score should reach 10/10
  *once Z14 closes V13/V14/V15 gaps and all 25 tests are green*.
- Until Z14 lands: 22/25 green is the documented baseline; the 3 reds
  are intentional discovery markers.
