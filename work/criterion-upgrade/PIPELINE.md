# Criterion Upgrade Pipeline — Path to 10/10

> Autonomous sequential criterion upgrades. Each criterion → tasks → dual runs → live verify → loop until 10/10.
> After each criterion completion, run regression on all previous criteria.
> If Codex limits exhausted → pause + notify user.

**Pipeline started:** 2026-04-26 (Round 8)
**Status:** ACTIVE — Criterion 1 (Functional Coverage)

---

## Initial scores (from Round 7 verdict)

| # | Criterion | Score | Target |
|---|-----------|-------|--------|
| 1 | Functional Coverage | 8 | 10 |
| 2 | Reliability | 6 | 10 |
| 3 | Security | 7 | 10 |
| 4 | Determinism | 5 | 10 |
| 5 | Maintainability | 6 | 10 |
| 6 | Scaling | 6 | 10 |
| 7 | Judge Quality | 5 | 10 |

---

## Criterion 1: Functional Coverage 8→10  ← CURRENT

**What 10/10 means:** Every conceivable code-write path (including indirect) is detected by the enforcer; live attack matrix grows from 18 to 25+ tests covering newly-identified vectors; conservative-parser false-positives (`py -c` reads incorrectly classified as writes) eliminated.

**Gaps identified:**
- V13: CronCreate background task spawning a code-writing script
- V14: MCP filesystem servers (e.g. `mcp__filesystem__write_file`) bypass Bash matcher entirely
- V15: Compiled binaries (`./my-tool` no shebang) — Bash matcher classifier doesn't detect arbitrary executables
- V16: `bash -s`/`sh -c` heredoc-to-interpreter (caught by always-cover rule? need test)
- V17: Conservative `py -c` read-only false-positive (legitimate read commands blocked) — reduces UX
- V18: NotebookEdit edge cases (cells with `%%bash` magic running shell)

**Sub-tasks:**
- **Z13** [PENDING]: Expand live attack matrix with V13-V18 tests. Discover real gaps.
- **Z14** [PENDING]: Fix discovered gaps in `codex-delegate-enforcer.py`.
- **Z15** [PENDING]: Refine `py -c` false-positive (Z13 may reveal it isn't actual issue or has wider scope).

**Verification ritual:**
1. After each task merge: live attack matrix + 268 unit tests + selftest 6/6
2. After all merged: count `passed/expected`; if 25+/25+ AND no false-positives in real workflow → 10/10
3. Sync to QA Legal, repeat verify there

**Exit criteria:** matrix has ≥25 tests, all PASS; no false-positive denials in 5 representative workflows; cross-tested in QA Legal.

---

## Criterion 2: Reliability 6→10  [QUEUED]

**What 10/10 means:** Dual-implement runs end-to-end without manual intervention; Y14 root-fixed (or stable mechanism); harness Permission UI denials become impossible or auto-recovered.

**Sub-tasks (preliminary):**
- Z16: Y14 investigation — find Claude Code setting that allows sub-agent Edit
- Z17: PowerShell-first as guaranteed mechanism in spawn-agent.py
- Z18: Codex returncode noise classification (post-Y20 audit)
- Z19: Self-referential parser-bug protection — codex-implement uses repo-CURRENT parser

---

## Criterion 3: Security 7→10  [QUEUED]

**What 10/10 means:** Defense in depth — bypass-sandbox wrapped in OS-level sandbox; explicit FS allowlist for reads.

**Sub-tasks (preliminary):**
- Z20: Wrap codex.cmd in Sandboxie (Windows) / firejail (Linux). Document fallback.
- Z21: Filesystem-read allowlist config — paths Codex may read outside `--cd`
- Z22: External security review checkpoint (mark with NOTE; not autonomously possible)

---

## Criterion 4: Determinism 5→10  [QUEUED]

**What 10/10 means:** Chaos test (30 identical specs) shows < 5% variance; Y14 deterministic; encoding standardized.

**Sub-tasks (preliminary):**
- Z23: Chaos test suite — N runs of identical mini-task, measure variance
- Z24: Encoding standardization — UTF-8 no-BOM, LF or CRLF deliberately
- Z25: Codex CLI flag abstraction audit (Y26 partially did this)

---

## Criterion 5: Maintainability 6→10  [QUEUED]

**What 10/10 means:** CI runs full matrix + 268 tests + canary dual on every PR; memory archive automated; structured CHANGELOG.

**Sub-tasks (preliminary):**
- Z26: `.github/workflows/dual-implement-ci.yml` — tests + selftest + matrix on every PR
- Z27: Memory archive automation when activeContext > 200 lines
- Z28: CHANGELOG.md scaffold + commit hook to update on every fix tag

---

## Criterion 6: Scaling 6→10  [QUEUED]

**What 10/10 means:** Sync N projects safely; refuses overwrite of locally-modified without `--force`; rollback on failure; per-project auth automated.

**Sub-tasks (preliminary):**
- Z29: sync-template-to-target.py — refuse overwrite if target uncommitted; require `--force`
- Z30: Rollback mechanism — store pre-sync state, allow `--rollback`
- Z31: Per-project auth verification — `verify-codex-auth.py`

---

## Criterion 7: Judge Quality 5→10  [QUEUED]

**What 10/10 means:** All 6 axes active; judge merit-based consistently in stress tests; Y27 fixed; tie threshold tuned.

**Sub-tasks (preliminary):**
- Z32: Y27 codex-ask timeout — bump to 600s OR `--strategic` flag with longer timeout
- Z33: Install radon, configure mypy.ini — activate complexity + type_check axes
- Z34: Re-tune tie threshold based on 5+ observed verdicts (delta = 2σ)
- Z35: Improve `logging_coverage` heuristic — count delegated calls to logged helpers

---

## State machine

After each task merge:
1. Live attack matrix + 268 unit tests + selftest in main
2. Sync to QA Legal, run identical tests
3. If exit criteria met: criterion DONE, advance
4. If failed: corrective task spec, dual run, repeat

After full criterion DONE:
1. Cross-regression: all previous criteria's tests
2. If any regress: corrective task spec immediately
3. If all stable: declare 10/10 + advance

After all 7 criteria DONE:
1. Final 30-task chaos test
2. 1-day idle observation
3. Declare 10/10 system-wide

If Codex limits hit:
1. Save state to PIPELINE.md (mark current task PAUSED)
2. Notify user: "Codex limits exhausted. Please relogin and reply to resume."
3. Wait.

---

## Progress log

- 2026-04-26 17:50 — Pipeline created. Starting Criterion 1 (Functional Coverage).
