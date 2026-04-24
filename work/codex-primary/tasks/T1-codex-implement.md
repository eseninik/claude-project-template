---
executor: claude
risk_class: routine
reasoning: high
wave: 1
---

# Task T1: `.claude/scripts/codex-implement.py`

## Your Task
Implement the single-task Codex executor. It reads a task-N.md file, runs `codex exec` with workspace-write sandbox scoped to the task's Scope Fence, captures the diff, runs Test Commands, and writes a standardized task-N-result.md.

See tech-spec.md Section 6 for complete behavior spec — this task is that spec, realized.

## Scope Fence
**Allowed paths (may be written):**
- `.claude/scripts/codex-implement.py` (new file)
- `.claude/scripts/test_codex_implement.py` (new file — unit tests)

**Forbidden paths (must NOT be modified):**
- `.claude/shared/templates/new-project/**` (out of this pipeline's scope)
- Any other script or hook
- `work/codex-primary/tech-spec.md` (spec is immutable)
- `work/codex-primary/PIPELINE.md` (pipeline state managed by orchestrator)

## Test Commands (run after implementation)
```bash
py -3 .claude/scripts/test_codex_implement.py
py -3 -c "from pathlib import Path; import importlib.util; spec = importlib.util.spec_from_file_location('codex_implement', '.claude/scripts/codex-implement.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('import ok')"
py -3 .claude/scripts/codex-implement.py --help
```

## Acceptance Criteria (IMMUTABLE)
- [ ] AC1: `codex-implement.py --help` shows all CLI flags from tech-spec 6.1 (--task, --worktree, --reasoning, --timeout, --result-dir)
- [ ] AC2: Parses task-N.md frontmatter (executor, risk_class, reasoning) and sections (Scope Fence, Test Commands, Acceptance Criteria, Skill Contracts) correctly — covered by unit test
- [ ] AC3: Pre-flight verifies cwd is inside worktree and records HEAD sha
- [ ] AC4: Builds a Codex prompt that embeds full task-N.md content
- [ ] AC5: Calls `codex exec --model gpt-5.5 --sandbox workspace-write --full-auto --cd <worktree-abs>` (exact invocation per tech-spec 6.2 step 4)
- [ ] AC6: Post-flight runs `git diff HEAD`, calls codex-scope-check.py (may be missing at T1 build time — wrap in subprocess.run with clear error if missing), runs Test Commands
- [ ] AC7: Writes `work/codex-implementations/task-{N}-result.md` with exact schema from tech-spec 6.2 step 6 (status, diff, test output, self-report, timestamp)
- [ ] AC8: Exit codes: 0 tests pass, 1 tests fail (scope ok), 2 scope violation OR timeout
- [ ] AC9: Every function in the script has structured logging (entry/exit/error per logging-standards)
- [ ] AC10: Unit test file covers: frontmatter parsing, section extraction, scope fence parsing, exit code mapping, error handling (missing task file, timeout simulation)
- [ ] All Test Commands above exit 0

## Skill Contracts

### verification-before-completion (contract extract)
- Run every Test Command above. If any fails, DO NOT claim done.
- Verify each AC with evidence. Quote test output when reporting.

### logging-standards (contract extract)
- Every function: `logger = logging.getLogger(__name__)` at module top; `logger.info("entry: ...", extra={...})` at function entry; `logger.info("exit: ...", extra={...})` at return; `logger.exception(...)` in every except block
- Use `structlog` if already used elsewhere in the project, otherwise stdlib `logging` with JSON formatter
- NO bare `print()` except for final user-visible CLI output (help text, status summary) — that can use `print()` since it's not log data
- Do NOT log sensitive data (task content may contain secrets; log only task path and metadata, not full task body)

### coding-standards (contract extract)
- Follow existing Python style in `.claude/scripts/` (see codex-ask.py as reference)
- Type hints on all functions
- Use `pathlib.Path` not string manipulation
- Use `subprocess.run` with `check=False, capture_output=True, text=True, timeout=...` — never shell=True

## Read-Only Files (Evaluation Firewall)
- `.claude/scripts/test_codex_implement.py` (once written, tests are immutable)
- `work/codex-primary/tech-spec.md`
- This task-N.md file itself

## Constraints
- Windows compatibility: use `pathlib`, forward slashes in subprocess args are fine
- Must work when cwd = project root OR cwd = a git worktree under the project
- Must not require external packages beyond what's already in `.claude/scripts/` (stdlib preferred)
- codex-scope-check.py may not exist yet — handle gracefully (warn + skip scope check with noting in result.md)

## Handoff Output (MANDATORY)
Output the standard `=== PHASE HANDOFF: T1-codex-implement ===` block per teammate-prompt-template.md with:
- Files Modified (2 files)
- Tests passed/failed counts
- Skills Invoked
- Decisions Made (key design choices not covered by tech-spec)
- Learnings

## Notes
- Reference script: `.claude/scripts/codex-ask.py` — follow its style, CLI arg handling pattern, subprocess usage
- If `codex exec` CLI exits non-zero, capture stderr into result.md and mark status=fail
- Timeout: use `subprocess.run(..., timeout=<seconds>)` → `subprocess.TimeoutExpired` → kill + rollback
