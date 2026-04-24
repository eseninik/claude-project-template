---
executor: dual
risk_class: high-stakes
speed_profile: thorough
---

# Task T1: `.claude/hooks/codex-delegate-enforcer.py` — Always-Dual enforcer

## Your Task

Replace the current bootstrap stub at `.claude/hooks/codex-delegate-enforcer.py`
with a full PreToolUse hook that enforces the Always-Dual Code Delegation
Protocol from project `CLAUDE.md`.

On `Edit`/`Write`/`MultiEdit` targeting a **code file** (by extension)
that is NOT in the exempt-path list, the hook must verify that a recent
(< 15 min) `work/codex-implementations/task-*-result.md` with `status: pass`
covers the target path via its Scope Fence. If no valid cover → deny with
a helpful recovery hint. Otherwise → allow.

Fail-open semantics: on ANY internal error the hook allows (never blocks
on infrastructure failure — protocol enforced by discipline as fallback).

## Scope Fence

**Allowed paths (may be written):**
- `.claude/hooks/codex-delegate-enforcer.py` (replace existing bootstrap stub)
- `.claude/hooks/test_codex_delegate_enforcer.py` (new — unit tests)

**Forbidden paths:**
- Any other hook or script
- `.claude/hooks/codex-gate.py` (reference only, read-only)
- `.claude/settings.json` (wiring is SOLO task T6, not here)
- `.claude/shared/templates/new-project/**`
- `work/**` except result-dir lookup which is runtime read-only

## Test Commands (run after implementation)

```bash
python .claude/hooks/test_codex_delegate_enforcer.py
python -c "import sys, importlib.util; spec = importlib.util.spec_from_file_location('enforcer', '.claude/hooks/codex-delegate-enforcer.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('import-ok')"
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: File `.claude/hooks/codex-delegate-enforcer.py` exists, valid Python.
- [ ] AC2: Reads hook payload from stdin as JSON (standard Claude Code hook protocol) with keys `hook_event_name`, `tool_name`, `tool_input`.
- [ ] AC3: Activates ONLY when `hook_event_name == "PreToolUse"` AND `tool_name in {"Edit", "Write", "MultiEdit"}`. Other events → pass-through (exit 0, no output).
- [ ] AC4: Extracts target path from `tool_input.file_path` for Edit/Write. For MultiEdit, extracts every edited path from `tool_input.edits[*].file_path` (or `tool_input.file_path` if single); every path must pass the check.
- [ ] AC5: **Code extensions** (module-level `set` constant): `.py .pyi .js .jsx .mjs .cjs .ts .tsx .sh .bash .zsh .go .rs .rb .java .kt .swift .c .cpp .cc .h .hpp .cs .php .sql .lua .r`
- [ ] AC6: **Exempt path patterns** (module-level list, matched via `fnmatch` or prefix):
  - `.claude/memory/**`
  - `work/**` (planning artifacts)
  - `CLAUDE.md`, `AGENTS.md`, `README.md`, `CHANGELOG.md`, `LICENSE`, `.gitignore`
  - `.claude/settings.json`, `.claude/ops/*.yaml`, `.mcp.json`
  - `.claude/adr/**/*.md`, `.claude/guides/**/*.md`, `.claude/skills/**/*.md`
  - Any file whose extension is NOT in the code-extension set
- [ ] AC7: For each target that is code AND not exempt, scan `work/codex-implementations/task-*-result.md`:
  - `time.time() - path.stat().st_mtime < 15 * 60` (15 minutes)
  - Parse `- status: <value>` line; must be `pass`
  - Parse `- task_file: <path>` line; load that task-N.md, extract Scope Fence → allowed list
  - Target must be prefix-matched by at least one allowed entry (use normalized `Path.resolve()`; dir-prefix ends with `/` or target equals a file-entry)
- [ ] AC8: If every target has a valid cover → exit 0 (allow), optional stdout log entry.
- [ ] AC9: If any target lacks valid cover → emit PreToolUse deny JSON to stdout:
  ```
  {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "<message>"}}
  ```
  Exit 0. Message contains: blocked target path, reason (no-cover / stale / scope-miss / fail-status), and hint string:
  `Use .claude/scripts/codex-inline-dual.py --describe "..." --scope <path> for micro-task, or write work/<feature>/tasks/task-N.md and run codex-implement.py. See CLAUDE.md "Code Delegation Protocol".`
- [ ] AC10: On ANY exception (parse error, missing dir, permission, etc.) → log to stderr and exit 0 (pass-through). Never crash, never silent-block on infra error.
- [ ] AC11: Structured stdlib `logging` — entry/exit for every function, error with context. Log file at `.claude/logs/codex-delegate-enforcer.log` if directory writable, else stderr only.
- [ ] AC12: Unit test file `.claude/hooks/test_codex_delegate_enforcer.py` covers at minimum these 10 cases:
  1. exempt path (e.g., `CLAUDE.md`) → allow
  2. code file + NO recent result.md → deny with JSON
  3. code file + stale (> 15 min) result.md → deny
  4. code file + fresh `status: pass` result.md with covering fence → allow
  5. code file + fresh pass result.md but fence does NOT cover target → deny
  6. code file + fresh `status: fail` result.md → deny
  7. non-code file (`.txt`, `.md`) → allow
  8. MultiEdit with multiple files, all covered → allow
  9. MultiEdit with one file uncovered → deny
  10. malformed result.md / corrupt JSON payload → pass-through (no crash)
  Plus 1 test: hook called on non-Edit event (e.g., Bash) → pass-through.
- [ ] AC13: Script under 450 lines; test file under 450 lines.
- [ ] AC14: Run-time < 200 ms typical, < 500 ms worst case. Use regex compile at module scope. Cache exempt-pattern compilation.
- [ ] All Test Commands exit 0.

## Skill Contracts

### verification-before-completion (per AGENTS.md)
Run every Test Command; quote stdout in handoff. Do not claim done on any non-zero.

### logging-standards (per AGENTS.md)
Entry/exit/error structured logs on every function. Never log user data.

### security-review (this IS a safety gate — applies)
- `Path.resolve()` normalization before any prefix matching (prevents `..` traversal in exempt-match)
- Time check via `time.time() - mtime`, not `datetime` subtraction (tz-safe)
- Defensive JSON parse: every field access via `.get()` with default
- No shell invocation needed; no subprocess at all
- Guard against a large number of result.md files (cap scan at 50 most-recent)

### coding-standards (per AGENTS.md)
- Reference `.claude/hooks/codex-gate.py` for existing gate-hook style; mirror its conventions
- Type hints on all public functions
- `pathlib.Path` everywhere

## Read-Only Files (Evaluation Firewall)

- `.claude/hooks/codex-gate.py` — reference only
- `.claude/hooks/test_codex_delegate_enforcer.py` — immutable once written
- `CLAUDE.md`, `AGENTS.md` — protocol spec, do not change here
- This task-T1-enforcer.md

## Constraints

- Windows-compatible
- Stdlib only
- Fail-open on uncertainty
- Must not modify `.claude/settings.json` (separate SOLO task)

## Handoff Output (MANDATORY)

Standard `=== PHASE HANDOFF: T1-enforcer ===` block. Include:
- `Decisions Made`: cover-match semantics (dir-prefix vs file-exact), how you handle MultiEdit
- `Tests`: output of all 11+ unit tests + the import smoke test
- `Backward compat`: verify old behavior preserved (hook returns exit 0 on non-relevant events)

## Iteration History

(First round — no prior attempts.)
