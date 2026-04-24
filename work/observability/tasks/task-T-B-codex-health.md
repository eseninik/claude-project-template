---
executor: dual
risk_class: routine
speed_profile: balanced
---

# Task T-B: `.claude/scripts/codex-health.py` — Codex infrastructure diagnostic

## Your Task

Diagnostic CLI that answers "is my Always-Dual setup ready to run, and if not, what's wrong?" by running these checks:

1. `codex` CLI on PATH
2. `codex --version` returns non-empty
3. `codex login status` output includes "ChatGPT" or "API"
4. `~/.codex/config.toml` has `model_provider = "chatgpt"` AND `[model_providers.chatgpt]` section with `base_url = "https://chatgpt.com/backend-api/codex"`
5. `.codex/circuit-state.json` parseable; if `.codex/circuit-open` present — report when it expires
6. `.claude/hooks/codex-delegate-enforcer.py` exists + importable
7. `.claude/settings.json` has PreToolUse entry referencing `codex-delegate-enforcer.py`
8. `.codex/pool-state.json` exists → report pool size + alive count (shell out to `codex-pool.py status`)
9. Scripts present + `py_compile` clean: `codex-ask.py`, `codex-implement.py`, `codex-wave.py`, `codex-inline-dual.py`, `dual-teams-spawn.py`, `judge.py`, `judge_axes.py`, `codex-pool.py`

## Scope Fence
**Allowed:** `.claude/scripts/codex-health.py` (new), `.claude/scripts/test_codex_health.py` (new).
**Forbidden:** any other path.

## Test Commands
```bash
python .claude/scripts/test_codex_health.py
python .claude/scripts/codex-health.py --help
python .claude/scripts/codex-health.py || true
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: CLI `codex-health.py [--json] [--project-root <path>]`. Human-readable default (✓/✗/⚠). `--json` emits `{"checks": [{"name","status","detail"}], "summary":{"ok","warn","fail","overall"}}`.
- [ ] AC2: Each check → `ok` / `warn` / `fail`. Missing-optional → warn (e.g. no pool). Missing-required → fail (e.g. codex CLI absent).
- [ ] AC3: Overall: `fail` if any fail, else `warn` if any warn, else `ok`. Exit: `ok`/`warn` → 0; `fail` → 1.
- [ ] AC4: Each check wrapped in try/except; exception msg becomes detail, status=fail.
- [ ] AC5: Subprocess calls use `subprocess.run(..., timeout=15, capture_output=True, text=True, check=False)`. Timeout → `warn`, detail="timeout".
- [ ] AC6: TOML parsing via stdlib `tomllib` (Python ≥ 3.11).
- [ ] AC7: `--json` valid json.loads-able.
- [ ] AC8: Structured logging.
- [ ] AC9: Stdlib only. Under 350 lines script + 350 lines tests.
- [ ] AC10: Unit tests (≥10) with mocks: all-ok, missing CLI → fail+exit1, expired circuit-open → warn, active circuit → fail, missing config.toml provider → fail, subprocess timeout → warn, malformed config.toml → graceful fail, missing pool → warn, syntax error in tracked script → fail, JSON schema match.
- [ ] All Test Commands exit 0.

## Constraints
- Windows-compatible
- `Path.home()` for user-config paths
- Never print secrets: only `login_type`, never token value

## Handoff Output
Standard `=== PHASE HANDOFF: T-B-codex-health ===` with sample JSON.
