# AGENTS.md — Shared Agent Context

> Auto-loaded by Codex CLI via `~/.codex/config.toml` `project_doc` fallback
> (`AGENTS.md` takes precedence over `CLAUDE.md`). Keep this file focused:
> shared invariants that every task delegated to Codex should follow, so
> individual `task-N.md` specs don't have to re-inline them on every run.
>
> Claude Code reads `CLAUDE.md`, not this file. Project-wide rules specific
> to Claude's behavior (hook wiring, Agent Teams policy, memory protocol)
> stay in `CLAUDE.md`. Only put things here that apply when **any** agent —
> Codex, Copilot, Gemini CLI — writes code in this repo.

## Repo shape (one-liner)

`claude-project-template-update` is the **source template** for all AI-First
bot projects. Edits to `.claude/` here propagate downstream via fleet-sync
to real bot projects. The code you touch here shapes many downstream
codebases. Think twice before refactoring widely.

## Universal skill contracts (apply to ALL code changes)

These are the extracts that every task-N.md used to repeat. Now they live
here once and are implicit for every Codex invocation.

### Verification (before claiming done)

- Run every Test Command listed in your task file. Quote the stdout in
  your self-report (`NOTE: ...` lines).
- Verify each Acceptance Criterion with concrete evidence — a passing
  assert, an expected output line, a file contents check.
- If any Test Command exits non-zero, do NOT claim done. Fix or
  `BLOCKER: <reason>` so the reviewer can unblock.
- Never modify test files, acceptance-criteria files, or any file listed
  under "Read-Only Files / Evaluation Firewall" in the task spec.

### Logging standards

- Every new function: structured logger call at entry (with params) and
  exit (with result), and every `except` block logs via `logger.exception`
  with context.
- Use `structlog` if the repo already uses it; otherwise stdlib `logging`
  with the existing formatter conventions in that file.
- `print()` is for user-facing CLI output only (help text, JSON output,
  status summary). **Never use `print()` for log data.**
- Never log sensitive values: passwords, API keys, access tokens, PII,
  full request bodies with user data.

### Security (applies when code touches auth, crypto, secrets, user input)

- Validate all inputs at boundaries. Parameterize SQL/shell/path;
  never string-interpolate untrusted data.
- Never commit secrets. Use env vars + `.gitignore`. If you see a secret
  in committed code, `BLOCKER` and stop.
- For paths: normalize with `Path.resolve()` and check `is_relative_to`
  a known root, to block traversal via `..`.
- Consult the OWASP top 10 check list for any auth/session code.

### Coding standards

- **Minimal diff.** Every line added or removed must trace back to the
  task's Acceptance Criteria. No drive-by refactoring, reformatting, or
  "while I'm here" cleanups. If you see something unrelated, note it as
  `NOTE:` in the self-report but don't touch it.
- **Match existing style.** Before writing a new function, read the
  surrounding file. Mirror its naming conventions, type-hint usage,
  docstring style, import ordering, and module-level constant patterns.
- **Use `pathlib.Path`**, not string manipulation, for any filesystem
  work. Platform-portable paths matter — this repo runs on Windows.
- **`subprocess.run(..., check=False, capture_output=True, text=True, timeout=...)`**.
  Never `shell=True`. Always set a timeout.
- **Type hints** on public function signatures. Prefer `list[...]`,
  `dict[...]`, `X | None` over `List[...]`, `Dict[...]`, `Optional[X]`
  when the file already uses modern syntax (check imports: if
  `from __future__ import annotations` is present, modern syntax is fine).

## Windows gotchas (this project is Windows-primary)

- Many scripts are invoked via the `.CMD` wrapper at
  `C:\Users\Lenovo\AppData\Roaming\npm\codex.CMD`. When spawning Codex
  yourself, **pass the prompt via stdin** (sentinel arg `-`), not via
  argv. Windows `cmd.exe` mangles multi-KB markdown with backticks,
  quotes, and `#`.
- `py -3` vs `python`: Codex's sandboxed shell often does NOT have the
  `py` launcher in PATH. Prefer `python` in Test Commands for maximum
  compatibility. If a Test Command invokes `py -3` and you see
  `No installed Python found!`, that is the reason — it is NOT a
  Python installation problem.
- Paths with spaces: this repo lives under `C:\Bots\Migrator bots\...`.
  Quote paths in subprocess calls. Prefer forward slashes for git —
  both `git` and `pathlib` handle them correctly on Windows.
- Line endings: config is `core.autocrlf` managed. Don't introduce
  explicit `\r\n` in strings; let git handle conversion.

## Git invariants

- **Clean working tree required** before any auto-implementer run
  (`codex-implement.py` enforces this in pre-flight). If you need to
  modify a file, stage your own prior work first.
- **Never amend** published commits. Create new commits for fixes.
- **No `--no-verify`** on commits unless explicitly requested.
- Scope Fence in the task file is literal. Do not broaden the fence
  by interpretation. If the fence says "only file X", do not touch
  file Y even if that seems necessary — report `BLOCKER` instead.

## Speed profile (optional guidance)

If the task frontmatter carries `speed_profile`, treat it as guidance
about how much thoroughness is expected:

- `fast` — routine, well-specified, tight deadline. Do the simplest
  correct thing. Fewer helper functions, less docstring prose. Skip
  speculative hardening.
- `balanced` (default) — normal coding standards apply; structured logs,
  helpful docstrings, safe defaults.
- `thorough` — high-stakes or novel problem. Add explicit edge-case
  handling, extended docstrings, aggressive logging, defensive
  assertions.

Reasoning effort is set upstream by the invoker; this field exists to
calibrate stylistic tradeoffs in your output, not to change correctness
requirements. Acceptance Criteria are ALWAYS immutable regardless of
profile.

## When in doubt

Output a `BLOCKER:` line in your self-report and stop. A clear "I don't
know why this is necessary" is far more valuable to the reviewer than
a plausible-looking guess committed as code. Opus (the reviewer) has
the full-project context to unblock you — you just need to ask.

## References for deeper context

- `.claude/adr/adr-012-codex-primary-implementer.md` — architectural
  decision record: why Opus plans + Codex implements.
- `work/codex-primary/tech-spec.md` — full tech-spec for the
  codex-primary pipeline (section 4 = task-N.md format).
- `.claude/shared/work-templates/phases/IMPLEMENT-CODEX.md`,
  `IMPLEMENT-HYBRID.md`, `DUAL-IMPLEMENT.md` — phase-mode docs.
- `work/codex-primary/dual-1-postmortem.md` +
  `dual-2-judgment.md` — real-run learnings (what breaks in practice).
