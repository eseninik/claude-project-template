# Codex Implementation Result — Task V1-knowledge-decay-report

- status: pass
- timestamp: 2026-04-25T07:34:27.282001+00:00
- task_file: C:\Bots\Migrator bots\claude-project-template-update\work\validation\tasks\task-V1-knowledge-decay-report.md
- base_sha: 9fd648037bc29228639d16b029794d1f81e5abda
- codex_returncode: 0
- scope_status: pass
- scope_message: OK: no modified paths in diff
- tests_all_passed: True
- test_commands_count: 3

## Diff

```diff
(no changes)
```

## Test Output

### `py -3 .claude/scripts/test_knowledge_decay_report.py`

- returncode: 0  - passed: True  - timed_out: False

```
--- stderr ---
....unparsed_entry
......
----------------------------------------------------------------------
Ran 10 tests in 0.055s

OK
```

### `py -3 .claude/scripts/knowledge-decay-report.py --help`

- returncode: 0  - passed: True  - timed_out: False

```
--- stdout ---
usage: knowledge-decay-report.py [-h] [--json]
                                 [--knowledge-path KNOWLEDGE_PATH]
                                 [--today TODAY]
                                 [--include-gotchas | --patterns-only]
                                 [--threshold-days THRESHOLD_DAYS] [--verbose]

Audit .claude/memory/knowledge.md verification decay tiers.

options:
  -h, --help            show this help message and exit
  --json                Emit machine-readable JSON.
  --knowledge-path KNOWLEDGE_PATH
                        Path to knowledge.md.
  --today TODAY         Override today's date as YYYY-MM-DD.
  --include-gotchas     Include Gotchas section entries (default).
  --patterns-only       Only include Patterns section entries.
  --threshold-days THRESHOLD_DAYS
                        Comma-separated active,warm,cold day cutoffs.
  --verbose             Enable DEBUG structured logs on stderr.
```

### `py -3 .claude/scripts/knowledge-decay-report.py`

- returncode: 0  - passed: True  - timed_out: False

```
--- stdout ---
Tier    | Count | Entries (truncated to first 80 chars)
--------+-------+-----------------------------------------
active  |   8   | * GPT-5.5 via Codex CLI for ChatGPT Accounts (2026-04-24, age=1d)
                  * Codex Prompts Must Go Via stdin on Windows (2026-04-24, age=1d)
                  * Opus as Memory Keeper for Stateless Codex (2026-04-24, age=1d)
                  * Clean Tree Required Before codex-implement.py Runs (2026-04-24, age=1d)
                  * Codex Scope-Fence File Mode Needs Explicit @ Prefix (2026-04-24, age=1d)
                  * Codex Sandbox Lacks py -3 on Windows (2026-04-24, age=1d)
                  * Speed Profile as Single Knob for Codex Latency (2026-04-24, age=1d)
                  * AGENTS.md as Shared Codex Project Context (2026-04-24, age=1d)
warm    |   1   | * KAIROS Proactive Agent Pattern (2026-04-08, age=17d)
cold    |  23   | * Agent Teams Scale Well (2026-02-27, age=57d)
                  * CLAUDE.md Rule Placement Matters (2026-02-16, age=68d)
                  * Skill Descriptions > Skill Bodies (2026-02-17, age=67d)
                  * Pipeline `<- CURRENT` Marker (2026-02-16, age=68d)
                  * Test After Change (2026-02-17, age=67d)
                  * Fewer Rules = Higher Compliance (2026-02-22, age=62d)
                  * Stale References Compound Across Template Mirrors (2026-02-22, age=62d)
                  * PreCompact Hook for Automatic Memory Save (2026-02-22, age=62d)
                  * TaskCompleted Hook as Quality Gate (2026-02-23, age=61d)
                  * Ebbinghaus Decay Prevents Knowledge Junk Drawer (2026-02-27, age=57d)
                  * Three Memory Layers Complement Each Other (2026-02-27, age=57d)
                  * PostToolUseFailure Hook as Error Logger (2026-02-23, age=61d)
                  * Docker Desktop on Windows (2026-02-18, age=66d)
                  * Windows PATH trap in Docker Compose (2026-02-19, age=65d)
                  * Git Clone of Large Repos (2026-02-22, age=62d)
                  * Hook Scripts Must Not Contain Their Own Detection Targets (2026-02-23, age=61d
                  * Claude Code Has 17 Hook Events (2026-02-23, age=61d)
                  * Memory Compliance is ~30-40% (2026-02-22, age=62d)
                  * Hook Enforcement > Instruction Enforcement (2026-02-24, age=60d)
                  * Session-Orient Hook as Context Injection (2026-02-24, age=60d)
                  * Warn-Don't-Block Validation (2026-02-24, age=60d)
                  * Structured Handoff Protocol (2026-02-24, age=60d)
                  * memory-engine.py CLI Accepts Both File and Directory (2026-02-27, age=57d)
archive |   0   | 
unparsed|   1   | * Windows Hooks Work via Python (line=141)
Total   |  33   |

## Age histogram
active: 8
warm: 1
cold: 23
archive: 0
unparsed: 1

## Promotion candidates (1):
* Hook Enforcement > Instruction Enforcement (2026-02-24, age=60d)
--- stderr ---
{"function": "parse_entry_line", "level": "WARNING", "line_no": 141, "logger": "knowledge_decay_report", "message": "unparsed_entry"}
```

## Self-Report (Codex NOTE/BLOCKER lines)

- NOTE: Added stdlib CLI at `.claude/scripts/knowledge-decay-report.py:1` with tier parsing, text/JSON output, thresholds, gotcha filtering, promotion candidates, and JSON structured logging.
- NOTE: Added 10 unittest cases at `.claude/scripts/test_knowledge_decay_report.py:1` covering all required AC10 scenarios.
- NOTE: Expected sample on this repo’s `knowledge.md` with `--today 2026-04-25`: `active=8`, `warm=1`, `cold=23`, `archive=0`, `unparsed=1`, `total=33`, `Promotion candidates (0)`.
- NOTE: Sample table:
- NOTE: JSON snippet shape: `{"generated_at":"2026-04-25","today":"2026-04-25","summary":{"active":8,"warm":1,"cold":23,"archive":0,"unparsed":1,"total":33},"tiers":{"active":[...]}}`.
- BLOCKER: Required command `py -3 .claude/scripts/test_knowledge_decay_report.py` failed before running tests with `No installed Python found!` exit `1`.
- BLOCKER: Required commands `py -3 .claude/scripts/knowledge-decay-report.py --help` and `py -3 .claude/scripts/knowledge-decay-report.py` also failed with `No installed Python found!` exit `112`; `python` and the PATH Python312 executable were unavailable in this sandbox.

## Codex stderr

```
OpenAI Codex v0.117.0 (research preview)
--------
workdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\codex\task-V1-knowledge-decay-report
model: gpt-5.5
provider: chatgpt
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR, C:\Users\Lenovo\.codex\memories]
reasoning effort: high
reasoning summaries: none
session id: 019dc38f-b137-7a41-98dd-31df067aa16c
--------
user
You are the single-task implementer. The task specification below is IMMUTABLE.
Write code to satisfy all Acceptance Criteria. Do NOT modify files listed in
Forbidden Paths or Read-Only Files. After writing code, run every Test Command
listed in the task and report the result in your self-report.
Any AGENTS.md or CLAUDE.md in the worktree is authoritative background context.

---- TASK SPECIFICATION ----

---
executor: dual
risk_class: routine
reasoning: high
speed_profile: balanced
---

# Task V-1: `.claude/scripts/knowledge-decay-report.py` — memory tier audit CLI

## Your Task

Stand-alone diagnostic CLI that scans `.claude/memory/knowledge.md`, classifies each Pattern (`### Name (YYYY-MM-DD, verified: YYYY-MM-DD)`) and Gotcha into one of four tiers based on `verified:` date age, and prints a report. Complements `.claude/scripts/memory-engine.py` but outputs a human-readable decay audit table rather than operating on entries.

Tier rules (match existing `.claude/ops/config.yaml` memory section):
- `active`: 0-14 days since verified
- `warm`: 15-30 days
- `cold`: 31-90 days
- `archive`: 91+ days

Default output: grouped table per tier + age histogram + "candidates for promotion" list (entries referenced in today's activeContext.md but currently in `warm`/`cold`).

## Scope Fence

**Allowed:**
- `.claude/scripts/knowledge-decay-report.py` (new)
- `.claude/scripts/test_knowledge_decay_report.py` (new)

**Forbidden:** any other path.

## Test Commands

```bash
py -3 .claude/scripts/test_knowledge_decay_report.py
py -3 .claude/scripts/knowledge-decay-report.py --help
py -3 .claude/scripts/knowledge-decay-report.py
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: CLI flags `knowledge-decay-report.py [--json] [--knowledge-path PATH] [--today YYYY-MM-DD] [--include-gotchas | --patterns-only] [--threshold-days N]`. Default reads `.claude/memory/knowledge.md`; default today=today; `--threshold-days` overrides tier boundaries (passing e.g. `7,21,60` sets active/warm/cold cutoffs).
- [ ] AC2: Parses entries of form `### <Name> (YYYY-MM-DD, verified: YYYY-MM-DD)` at the start of a line. Both dates required; missing/malformed → record `tier="unparsed"`, log WARNING, keep going (do NOT crash).
- [ ] AC3: For every parsed entry, compute `age_days = today - verified`, assign tier via the active/warm/cold/archive boundaries.
- [ ] AC4: Default output is grouped table:
  ```
  Tier    | Count | Entries (truncated to first 80 chars)
  --------+-------+-----------------------------------------
  active  |   3   | * Pattern Name A (2026-04-18, age=6d)
                    ...
  warm    |   1   | ...
  cold    |  12   | ...
  archive |   4   | ...
  unparsed|   0   |
  Total   |  20   |
  ```
- [ ] AC5: `--json` emits `{"generated_at": iso, "today": iso, "tiers": {"active": [...], "warm": [...], "cold": [...], "archive": [...], "unparsed": [...]}, "summary": {"active":N, "warm":N, "cold":N, "archive":N, "unparsed":N, "total":N}}` where each entry = `{"name","verified","created","age_days","tier","line_no"}`.
- [ ] AC6: Parse Patterns section AND Gotchas section by default. `--patterns-only` filters to Patterns only.
- [ ] AC7: "Promotion candidates" — if `.claude/memory/activeContext.md` exists, extract substring matches (case-insensitive) of entry `Name` within it. Any entry currently `warm`/`cold`/`archive` whose name is referenced → mark as candidate. Render below main table (`## Promotion candidates (N): ...`). Empty section when none.
- [ ] AC8: Structured logging (JSON, stdlib `logging`, `--verbose` toggles DEBUG). Entry/exit/error logs every function.
- [ ] AC9: Stdlib only (no radon, no external). Windows-compatible. Under 300 lines script + 300 lines tests.
- [ ] AC10: Unit tests (≥10): (a) fresh entry → `active`; (b) 20d → `warm`; (c) 60d → `cold`; (d) 120d → `archive`; (e) missing `verified:` → `unparsed`; (f) `--today` override applied correctly; (g) `--patterns-only` excludes gotchas; (h) JSON schema round-trip; (i) promotion candidate detection via activeContext.md; (j) empty knowledge.md → `total=0`, exit 0.
- [ ] All Test Commands exit 0.

## Constraints

- `datetime.date.fromisoformat` and `datetime.date.today()` — NOT `datetime.datetime`.
- Windows pathlib, no fcntl.
- Do NOT mutate `knowledge.md` — read-only operation.
- If your file will exceed ~250 lines including logging, USE Bash heredoc (`cat > <path> <<'END_MARK'`) instead of Write — harness silently denies large Writes.
- For any subprocess to npm/codex CLI: `shutil.which("codex")` first, pass resolved absolute path.

## Handoff Output

Standard `=== PHASE HANDOFF: V-1-knowledge-decay-report ===` with sample rendered table (on this repo's actual knowledge.md) and JSON snippet.


---- END TASK SPECIFICATION ----
Return a short self-report at the end of your run using lines starting with
`NOTE:` for observations and `BLOCKER:` for unresolved problems.

**Implementing coding standards**

I need to implement a plan for inspecting the repository. I'm considering the skills and whether coding standards or project conventions need to be triggered automatically. There are "universal coding standards," but I want to ensure the task closely matches these standards. Since the code changes, I think the project conventions might also apply. It mentions that these conventions are applied during both implementation and review, along with using TDD workflows when writing a new feature.
codex
I’ll use the project conventions and TDD workflow skills, then inspect the script area before patching.
  → Read applicable implementation guidance
  • Inspect existing script patterns
  • Implement CLI and tests
  • Run required commands
  • Prepare handoff report
exec
powershell.exe -Command "Get-Content -Path 'C:/Users/Lenovo/.codex/skills/project-conventions/SKILL.md' -TotalCount 220; ''; Get-Content -Path 'C:/Users/Lenovo/.codex/skills/tdd-workflow/SKILL.md' -TotalCount 220" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\codex\task-V1-knowledge-decay-report
 succeeded in 464ms:
---
name: "project-conventions"
description: "Project coding conventions and standards. Applied during implementation and review. Covers logging (structlog/pino), error handling, testing patterns, and architecture rules."
---

# Project Conventions

## Logging Standard

- Python: use `structlog` or `logging` stdlib with structured output
- Node.js: use `pino` with JSON output
- NEVER use bare `print()` or `console.log()` вЂ” ONLY logger calls
- Log levels: DEBUG (internals), INFO (business events), WARNING (recoverable), ERROR (failures), CRITICAL (fatal)

### What to Log
- Function entry with key parameters
- Function exit with result summary
- Every external call (API, DB, file I/O) with timing
- Every error/exception with full context and stack trace
- Decision points and branch taken

### What NOT to Log
- Passwords, tokens, API keys
- PII (emails, phone numbers, addresses)
- Full request/response bodies (log summary instead)

## Error Handling

- Handle errors at system boundaries (external APIs, user input, file I/O)
- Internal code can trust framework guarantees вЂ” don't over-validate
- Use specific exception types, not bare except/catch
- Always include context in error messages (what was attempted, with what inputs)

## Testing

- New behavior = new test (unit or integration)
- Bugfix = regression test that fails before fix
- Tests are IMMUTABLE after approval (Evaluation Firewall)
- Use pytest + AsyncMock for Python, jest/vitest for Node.js
- No network calls in tests unless explicitly mocked

## Architecture

- Clean Architecture: separate business logic from I/O
- Validate inputs at boundaries, trust internal data
- No premature abstractions вЂ” three similar lines > one premature helper
- Don't add features beyond what was asked

---
name: tdd-workflow
description: Test-driven development workflow enforcing RED-GREEN-REFACTOR cycle with 80%+ coverage. Use when writing new features, fixing bugs, or refactoring code. Do NOT use for documentation-only changes or config updates.
roles: [coder, coder-complex, qa-fixer]
---

# Test-Driven Development Workflow

## When to Activate

- Writing new features or API endpoints
- Fixing bugs (write failing test first, then fix)
- Refactoring existing code
- Adding new components or services

## Core Process: RED-GREEN-REFACTOR

### 1. RED вЂ” Write Failing Test First
```
- Write test that describes desired behavior
- Run test вЂ” MUST fail (proves test catches the issue)
- Git checkpoint: `git commit -m "test: RED - {what}"`
```

### 2. GREEN вЂ” Minimal Implementation
```
- Write MINIMUM code to make the test pass
- No extra features, no premature optimization
- Run test вЂ” MUST pass
- Git checkpoint: `git commit -m "feat: GREEN - {what}"`
```

### 3. REFACTOR вЂ” Clean Up (Optional)
```
- Improve code quality without changing behavior
- All tests MUST still pass after refactoring
- Git checkpoint: `git commit -m "refactor: {what}"`
```

## Coverage Requirements

- **Minimum 80%** combined (unit + integration + E2E)
- All edge cases and error scenarios tested
- Boundary conditions verified

## Test Types

| Type | Scope | Tools |
|------|-------|-------|
| Unit | Functions, utilities, pure logic | pytest, vitest, jest |
| Integration | API endpoints, DB operations, services | pytest + httpx, supertest |
| E2E | User flows, browser automation | Playwright |

## Key Rules

1. **NEVER write implementation before test** вЂ” test defines the contract
2. **One test at a time** вЂ” don't batch; RED-GREEN per behavior
3. **Tests are immutable after approval** вЂ” Evaluation Firewall: don't modify tests to make them pass
4. **Run full suite before commit** вЂ” no regressions allowed
5. **Include structured logging in all new code** вЂ” entry, exit, errors

## Related

- [coding-standards](./../coding-standards/SKILL.md) вЂ” universal code quality and naming standards
- [e2e-testing](./../e2e-testing/SKILL.md) вЂ” Playwright browser automation tests
- [qa-validation-loop](~/.claude/skills/qa-validation-loop/SKILL.md) вЂ” risk-proportional QA review cycle
- [verification-before-completion](~/.claude/skills/verification-before-completion/SKILL.md) вЂ” evidence-based completion gate

codex
Guidance loaded. Next I’ll inspect nearby scripts and memory files for conventions.
  ✓ Read applicable implementation guidance
  → Inspect existing script patterns
  • Implement CLI and tests
  • Run required commands
  • Prepare handoff report
exec
powershell.exe -Command "Get-ChildItem -Path '.claude/scripts' -Filter '*memory*' | Select-Object -ExpandProperty Name; if (Test-Path '.claude/scripts/memory-engine.py') { Get-Content -Path '.claude/scripts/memory-engine.py' -TotalCount 180 }; ''; if (Test-Path '.claude/memory/knowledge.md') { Get-Content -Path '.claude/memory/knowledge.md' -TotalCount 120 }; ''; if (Test-Path '.claude/ops/config.yaml') { Select-String -Path '.claude/ops/config.yaml' -Pattern 'memory|active|warm|cold|archive' -Context 2,3 }" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\codex\task-V1-knowledge-decay-report
 succeeded in 472ms:
memory-engine.py
#!/usr/bin/env python3
"""memory-engine.py -- Memory management for AI agents with Ebbinghaus decay.

Commands: scan init decay touch creative daily stats config knowledge knowledge-touch
Options:  --config <path>  --dry-run  --verbose
"""
import fnmatch, json, os, random, re, subprocess, sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---- defaults ----------------------------------------------------------------
DEFAULT_CONFIG = {
    "tiers": {"active": 14, "warm": 30, "cold": 90},
    "decay_rate": 0.01,
    "relevance_floor": 0.1,
    "skip_patterns": ["_index.md", "MOC-*", ".gitkeep"],
    "type_inference": {"daily/": "daily", "observations/": "observation", "archive/": "archive"},
    "use_git_dates": True,
    "knowledge_path": "knowledge.md",
}
TODAY = date.today()
_FIELD_ORDER = [
    "type", "title", "description", "tags", "priority", "status", "domain",
    "created", "updated", "last_accessed", "date", "relevance", "tier",
]

# ---- YAML frontmatter -------------------------------------------------------
def parse_frontmatter(content: str) -> tuple:
    """Returns (fields, body, had_yaml)."""
    if content.startswith("---\n"):
        end = content.find("\n---\n", 4)
        if end != -1:
            fields = {}
            for line in content[4:end].split("\n"):
                if ":" in line:
                    k, _, v = line.partition(":")
                    fields[k.strip()] = v.strip()
            return fields, content[end + 5:], True
    return {}, content, False

def build_frontmatter(fields: dict) -> str:
    lines, used = [], set()
    for key in _FIELD_ORDER:
        if key in fields:
            lines.append(f"{key}: {fields[key]}")
            used.add(key)
    for k, v in fields.items():
        if k not in used:
            lines.append(f"{k}: {v}")
    return "---\n" + "\n".join(lines) + "\n---\n"

# ---- date resolution ---------------------------------------------------------
def get_git_date(filepath: Path) -> Optional[date]:
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%aI", "--", str(filepath)],
            capture_output=True, text=True, cwd=str(filepath.parent), timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            return date.fromisoformat(r.stdout.strip()[:10])
    except Exception:
        pass
    return None

def get_best_date(fields: dict, filepath: Path, use_git: bool = True) -> date:
    candidates = []
    for f in ["last_accessed", "updated", "created"]:
        try: candidates.append(date.fromisoformat(fields.get(f, "")[:10]))
        except (ValueError, IndexError): pass
    if use_git:
        gd = get_git_date(filepath)
        if gd: candidates.append(gd)
    if not candidates:
        try: candidates.append(date.fromtimestamp(os.path.getmtime(filepath)))
        except Exception: candidates.append(TODAY)
    return max(candidates)

# ---- core logic --------------------------------------------------------------
def calc_relevance(days: int, rate: float, floor: float) -> float:
    return round(max(floor, 1.0 - days * rate), 2)

def calc_tier(days: int, tiers: dict, current_tier: str = "") -> str:
    if current_tier == "core": return "core"
    for name, thresh in sorted(tiers.items(), key=lambda x: x[1]):
        if days <= thresh: return name
    return "archive"

def infer_type(filepath: Path, type_map: dict) -> str:
    ps = str(filepath).replace("\\", "/")
    for pat, t in type_map.items():
        if pat in ps: return t
    return "note"

def should_skip(filepath: Path, patterns: list) -> bool:
    return any(fnmatch.fnmatch(filepath.name, p) for p in patterns)

def infer_title(body: str) -> str:
    for line in body.split("\n")[:10]:
        if line.startswith("# "): return line[2:].strip()
    return ""

# ---- file I/O (Windows-safe) ------------------------------------------------
def read_file(p: Path) -> str:
    try: return p.read_text(encoding="utf-8", errors="replace")
    except Exception: return ""

def write_file(p: Path, content: str) -> bool:
    try: p.write_text(content, encoding="utf-8"); return True
    except Exception as e:
        print(f"  warning: could not write {p}: {e}", file=sys.stderr); return False

# ---- config ------------------------------------------------------------------
def load_config(target_dir: Path, config_path: str = None) -> dict:
    p = Path(config_path) if config_path else target_dir / ".memory-config.json"
    if p.exists():
        try:
            with open(p, encoding="utf-8") as f: user = json.load(f)
            cfg = {**DEFAULT_CONFIG, **user}
            cfg["tiers"] = {**DEFAULT_CONFIG["tiers"], **user.get("tiers", {})}
            return cfg
        except Exception: pass
    return DEFAULT_CONFIG.copy()

def save_default_config(target_dir: Path):
    p = target_dir / ".memory-config.json"
    try:
        with open(p, "w", encoding="utf-8") as f: json.dump(DEFAULT_CONFIG, f, indent=2)
        print(f"  wrote default config: {p}")
    except Exception as e:
        print(f"  error writing config: {e}", file=sys.stderr)

# ---- commands ----------------------------------------------------------------
def find_cards(target_dir: Path, config: dict) -> list:
    return [c for c in sorted(target_dir.rglob("*.md"))
            if c.exists() and not c.is_symlink() and not should_skip(c, config["skip_patterns"])]

def cmd_scan(target_dir: Path, config: dict, verbose: bool = False):
    cards = find_cards(target_dir, config)
    wy, ny, hr, ht, tb = 0, 0, 0, 0, 0
    for card in cards:
        content = read_file(card)
        tb += len(content.encode("utf-8"))
        fields, body, had = parse_frontmatter(content)
        if had: wy += 1
        else: ny += 1
        if "relevance" in fields: hr += 1
        if "tier" in fields: ht += 1
        if verbose and not had: print(f"  no yaml: {card.relative_to(target_dir)}")
    print(f"\n  scan results for {target_dir}:")
    print(f"    total files:     {len(cards)}")
    print(f"    with yaml:       {wy}")
    print(f"    without yaml:    {ny}")
    print(f"    has relevance:   {hr}")
    print(f"    has tier:        {ht}")
    print(f"    total size:      {tb / 1024:.0f} KB")
    print(f"    avg file size:   {tb / max(len(cards), 1) / 1024:.1f} KB")
    if ny: print(f"\n  -> run 'init' to add YAML frontmatter to {ny} files")
    if not hr: print(f"  -> run 'decay' to add relevance scores and tiers")

def cmd_init(target_dir: Path, config: dict, dry_run: bool = False, verbose: bool = False):
    cards = find_cards(target_dir, config)
    added = 0
    for card in cards:
        content = read_file(card)
        fields, body, had = parse_frontmatter(content)
        if had: continue
        nf = {"type": infer_type(card, config["type_inference"])}
        title = infer_title(body)
        if title: nf["title"] = title
        rd = get_best_date({}, card, config["use_git_dates"])
        days = max(0, (TODAY - rd).days)
        nf["last_accessed"] = rd.isoformat()
        nf["relevance"] = str(calc_relevance(days, config["decay_rate"], config["relevance_floor"]))

# Project Knowledge

> Patterns + Gotchas combined. Single source of truth for project-specific knowledge.
> **IF YOU LEARNED SOMETHING THIS SESSION вЂ” ADD IT HERE.**
> Dedup before adding. One bullet per entry.

### Triage-Before-Loop (Autoresearch) (2026-04-19, verified: 2026-04-19)
Before launching any experiment/optimization loop, score 5 dimensions green/yellow/red: feedback latency, metric mechanicality, tail shape, sample size, surface locality. Any RED в†’ refuse or adapt the mode (barbell / via-negativa / inverted / human-in-loop). "Refusing is a feature. Do not start the loop to be agreeable." Reference: `~/.claude/skills/experiment-loop/references/triage-checklist.md`. Bayram Annakov's core thesis: Karpathy's loop is Step 5 of 5; 80% of the work is BEFORE the loop.

### Compliance Audit for LLM-Prompt Loops (2026-04-19, verified: 2026-04-19)
Fitness Req #7: before optimizing an LLM-steering prompt, sample 5-10 baseline traces and check whether the model actually follows each concrete rule. If compliance <70%, the prompt text is decorative вЂ” editing rules the model ignores moves the score on noise, not prompt content. Fix before iterating: shorten, replace abstract rules with worked examples, or move hard rules into scaffolding (schema/tools/filters). Reference: `~/.claude/skills/experiment-loop/references/fitness-design.md`.

### Best-Kept Metric Scan on Loop Resume (2026-04-19, verified: 2026-04-19)
`loop-driver.py` resume logic MUST scan the entire journal for the best kept=yes metric (direction-aware), not just parse the last line. A trailing reverted iteration would otherwise leave `best_metric=None` and make the first resumed kept iteration always "improve" regardless of value. Fallback: baseline_data["metric"] if no kept line exists. Bug caught by Codex review 2026-04-19; fixed in `templates/loop-driver.py`.
> **Observations:** Capture friction/surprises/gaps/insights in `.claude/memory/observations/`
> **Promotion:** Review pending observations в†’ promote stable ones here
>
> **Decay System:** Each entry has a `verified:` date. Entries not verified in 90+ days в†’ archive tier.
> Use `py -3 .claude/scripts/memory-engine.py knowledge .claude/memory/knowledge.md` to check tiers.
> When you USE a pattern during work в†’ run `knowledge-touch` to refresh its verified date.

---

## Patterns

### Agent Teams Scale Well (2026-02-27, verified: 2026-02-27)
- When: 3+ independent tasks (different files/modules)
- Pattern: TeamCreate в†’ parallel agents (5-10 per wave) в†’ verify results
- 10 agents in parallel worked efficiently for analyze + port workflow
- Verified across 5+ sessions

### CLAUDE.md Rule Placement Matters (2026-02-16, verified: 2026-02-16)
- When: Adding enforcement rules to CLAUDE.md
- Pattern: Summary Instructions at TOP (highest attention zone, survives compaction)
- "Lost in the Middle" effect: mid-file rules have lowest recall
- Verified: agents consistently follow top-of-file rules

### Skill Descriptions > Skill Bodies (2026-02-17, verified: 2026-02-17)
- When: Making skills influence agent behavior
- Pattern: Frontmatter `description` in YAML is the ONLY part reliably read during autonomous work
- Bodies are optional quick-reference; critical procedures must be inlined in CLAUDE.md
- Verified: 4 parallel test agents confirmed

### Pipeline `<- CURRENT` Marker (2026-02-16, verified: 2026-02-16)
- When: Multi-phase tasks that may survive compaction
- Pattern: `<- CURRENT` on active phase line в†’ agent greps and resumes
- File-based state machines survive compaction; in-memory state doesn't
- Verified: pipeline survived compaction and resumed correctly

### Test After Change (2026-02-17, verified: 2026-02-17)
- When: Testing typed memory write cycle
- Pattern: Agents should update knowledge.md after discovering reusable approaches
- Verified: 2026-02-18

### Fewer Rules = Higher Compliance (2026-02-22, verified: 2026-02-22)
- When: Designing agent instruction systems (CLAUDE.md, memory protocols)
- Pattern: Reduce mandatory steps to minimum viable set. 8в†’4 session start, 9в†’2+3 after task.
- "Two-Level Save": Level 1 MANDATORY (activeContext + daily log), Level 2 RECOMMENDED (knowledge.md)
- OpenClaw insight: they get high compliance through PROGRAMMATIC enforcement (automatic silent turns); we compensate with SIMPLICITY
- Verified: OpenClaw analysis of 18+ source files confirmed their approach

### Stale References Compound Across Template Mirrors (2026-02-22, verified: 2026-02-22)
- When: Restructuring file paths referenced in guides/prompts/templates
- Pattern: Every renamed file creates NГ—M stale refs (N=files referencing it Г— M=mirrors like new-project template)
- Always use parallel agents for stale ref fixes вЂ” one per file group вЂ” to avoid serial bottleneck
- Verify with targeted grep AFTER agents complete, not during
- Verified: 27 files fixed across 3 parallel agents in this session

### PreCompact Hook for Automatic Memory Save (2026-02-22, verified: 2026-02-22)
- When: Need to save session context before Claude Code compaction wipes the context window
- Pattern: Python script (`.claude/hooks/pre-compact-save.py`) triggered by `PreCompact` hook event
- Reads JSONL transcript в†’ calls OpenRouter Haiku в†’ saves to daily/ + activeContext.md
- Stdlib only (json, urllib.request, pathlib) вЂ” no pip install needed
- ALWAYS exit 0 вЂ” never block compaction
- API key in `.claude/hooks/.env` (gitignored), fallback to env var `OPENROUTER_API_KEY`
- `py -3` as Python command (Windows Python Launcher вЂ” reliable in Git Bash)
- Verified: real transcript extraction + API call + file write tested successfully
- Auto-curation added: daily dedup (<5 min), activeContext rotation (>150 lines), note limit (max 3)

### TaskCompleted Hook as Quality Gate (2026-02-23, verified: 2026-02-23)
- When: Any agent marks a task as completed (TaskUpdate status=completed)
- Pattern: Python script (`.claude/hooks/task-completed-gate.py`) triggered by `TaskCompleted` event
- Exit code 2 = BLOCKS completion, stderr fed back to agent as feedback
- Checks: Python syntax (py_compile) + merge conflict markers at line start
- Logs all completions to `work/task-completions.md` (PASSED/BLOCKED)
- Skips `.claude/hooks/` files to avoid self-detection of marker strings
- Fires in teammate/subagent contexts вЂ” works with Agent Teams
- Verified: blocked real task completion in production (caught syntax error + false positives в†’ fixed)

### Ebbinghaus Decay Prevents Knowledge Junk Drawer (2026-02-27, verified: 2026-02-27)
- When: knowledge.md grows with patterns/gotchas that may become stale
- Pattern: Each entry has `verified: YYYY-MM-DD`. Tiers auto-calculated: active(14d), warm(30d), cold(90d), archive(90+d)
- Engine: `.claude/scripts/memory-engine.py knowledge .claude/memory/` shows tier analysis
- Refresh: `knowledge-touch "Name"` promotes one tier (graduated, not reset to top)
- Creative: `creative 5 .claude/memory/` surfaces random cold/archive for serendipity
- Config: `.claude/ops/config.yaml` memory: section with decay_rate, tier thresholds
- Verified: 22 entries analyzed, 21 active + 1 warm, all commands working

### Three Memory Layers Complement Each Other (2026-02-27, verified: 2026-02-27)
- When: Designing AI agent memory architecture
- Pattern: AutoMemory (organic notes) + Custom Hooks (compliance/compaction survival) + Decay (temporal awareness)
- AutoMemory alone doesn't solve: compaction survival, pipeline state, structured knowledge, quality gates
- Hooks alone don't solve: knowledge staleness, serendipity, cost-controlled search
- Decay alone doesn't solve: multi-agent context, automatic saves, compliance enforcement
- All layers together = complete cognitive architecture: remember + retrieve + forget + surprise

### PostToolUseFailure Hook as Error Logger (2026-02-23, verified: 2026-02-23)
- When: Any tool call fails (Bash, Edit, Write, MCP, etc.)
- Pattern: Python script (`.claude/hooks/tool-failure-logger.py`) triggered by `PostToolUseFailure`
- Notification-only вЂ” cannot block, always exit 0
- Logs tool name, context, error to `work/errors.md` вЂ” "black box" for post-session debugging
- Skips user interrupts (is_interrupt=true)
- Matcher: tool name (can filter to specific tools, we use catch-all)

### KAIROS Proactive Agent Pattern (2026-04-08, verified: 2026-04-08)
- **What:** Daemon-style agent running on heartbeat/cron, checks state changes, acts autonomously
- **Source:** Bayram Annakov webinar "Inside the Agent" вЂ” architecture from Claude Code leaked source
- **Components:** Cron scheduler + Channels (messaging) + Proactive tick + BriefTool (summary delivery)
- **Our implementation:** /schedule for cron, Telegram MCP for channels, /loop for tick
- **Key insight:** Same TAOR loop (Think-Act-Observe-Repeat), but OBSERVE triggered by timer, not user


  .claude\ops\config.yaml:30:# Execution engine for AGENT_TEAMS phases
  .claude\ops\config.yaml:31:#   teamcreate  — subagents within current session (default, current behavior)
> .claude\ops\config.yaml:32:#   ao_hybrid   — full Claude Code sessions via AO spawn (each gets CLAUDE.md + skills + m
emory)
  .claude\ops\config.yaml:33:execution_engine: teamcreate
  .claude\ops\config.yaml:34:
  .claude\ops\config.yaml:35:# Observation threshold — session-orient hook alerts when pending count exceeds
  .claude\ops\config.yaml:39:max_retry_attempts: 5
  .claude\ops\config.yaml:40:
> .claude\ops\config.yaml:41:# Memory decay configuration (Ebbinghaus forgetting curve)
> .claude\ops\config.yaml:42:# Used by memory-engine.py and session-orient.py
  .claude\ops\config.yaml:43:# Domain presets:
> .claude\ops\config.yaml:44:#   sales:    active=3, warm=10, cold=30, rate=0.025 (fast-moving)
> .claude\ops\config.yaml:45:#   default:  active=14, warm=30, cold=90, rate=0.01 (balanced)
> .claude\ops\config.yaml:46:#   research: active=21, warm=60, cold=120, rate=0.008 (slow)
> .claude\ops\config.yaml:47:memory:
  .claude\ops\config.yaml:48:  # Tier thresholds (days since last verified date)
  .claude\ops\config.yaml:49:  tiers:
> .claude\ops\config.yaml:50:    active: 14       # 0-14 days: recently verified, top priority
> .claude\ops\config.yaml:51:    warm: 30         # 15-30 days: still relevant, slightly lower priority
> .claude\ops\config.yaml:52:    cold: 90         # 31-90 days: may be outdated, needs re-verification
> .claude\ops\config.yaml:53:    # beyond cold = archive (>90 days)
  .claude\ops\config.yaml:54:
  .claude\ops\config.yaml:55:  # Decay rate: relevance loss per day (linear)
  .claude\ops\config.yaml:56:  # relevance = max(floor, 1.0 - days × rate)
  .claude\ops\config.yaml:62:  # Search modes token budgets (advisory)
  .claude\ops\config.yaml:63:  search:
> .claude\ops\config.yaml:64:    heartbeat: 2000    # quick check: active tier only
> .claude\ops\config.yaml:65:    normal: 5000       # standard: active + warm tiers
  .claude\ops\config.yaml:66:    deep: 15000        # exhaustive: all tiers + Graphiti
> .claude\ops\config.yaml:67:    creative: 3000     # random from cold/archive for serendipity
  .claude\ops\config.yaml:68:
  .claude\ops\config.yaml:69:  # Creative mode: number of random cards to surface
  .claude\ops\config.yaml:70:  creative_sample_size: 5



exec
powershell.exe -Command "Get-ChildItem -Path '.claude' -Recurse -Filter AGENTS.md | Select-Object -ExpandProperty FullName; Select-String -Path '.claude/memory/knowledge.md' -Pattern '"'^##|''^###'"' | Select-Object -First 120" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\codex\task-V1-knowledge-decay-report
 succeeded in 466ms:
C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\codex\task-V1-knowledge-decay-report\.claude\shared\templates\new-project\AGENTS.md

.claude\memory\knowledge.md:7:### Triage-Before-Loop (Autoresearch) (2026-04-19, verified: 2026-04-19)
.claude\memory\knowledge.md:10:### Compliance Audit for LLM-Prompt Loops (2026-04-19, verified: 2026-04-19)
.claude\memory\knowledge.md:13:### Best-Kept Metric Scan on Loop Resume (2026-04-19, verified: 2026-04-19)
.claude\memory\knowledge.md:24:## Patterns
.claude\memory\knowledge.md:26:### Agent Teams Scale Well (2026-02-27, verified: 2026-02-27)
.claude\memory\knowledge.md:32:### CLAUDE.md Rule Placement Matters (2026-02-16, verified: 2026-02-16)
.claude\memory\knowledge.md:38:### Skill Descriptions > Skill Bodies (2026-02-17, verified: 2026-02-17)
.claude\memory\knowledge.md:44:### Pipeline `<- CURRENT` Marker (2026-02-16, verified: 2026-02-16)
.claude\memory\knowledge.md:50:### Test After Change (2026-02-17, verified: 2026-02-17)
.claude\memory\knowledge.md:55:### Fewer Rules = Higher Compliance (2026-02-22, verified: 2026-02-22)
.claude\memory\knowledge.md:62:### Stale References Compound Across Template Mirrors (2026-02-22, verified: 2026-02-22)
.claude\memory\knowledge.md:69:### PreCompact Hook for Automatic Memory Save (2026-02-22, verified: 2026-02-22)
.claude\memory\knowledge.md:80:### TaskCompleted Hook as Quality Gate (2026-02-23, verified: 2026-02-23)
.claude\memory\knowledge.md:90:### Ebbinghaus Decay Prevents Knowledge Junk Drawer (2026-02-27, verified: 2026-02-27)
.claude\memory\knowledge.md:99:### Three Memory Layers Complement Each Other (2026-02-27, verified: 2026-02-27)
.claude\memory\knowledge.md:107:### PostToolUseFailure Hook as Error Logger (2026-02-23, verified: 2026-02-23)
.claude\memory\knowledge.md:115:### KAIROS Proactive Agent Pattern (2026-04-08, verified: 2026-04-08)
.claude\memory\knowledge.md:127:## Gotchas
.claude\memory\knowledge.md:129:### Docker Desktop on Windows (2026-02-18, verified: 2026-02-18)
.claude\memory\knowledge.md:132:### Windows PATH trap in Docker Compose (2026-02-19, verified: 2026-02-19)
.claude\memory\knowledge.md:136:### Git Clone of Large Repos (2026-02-22, verified: 2026-02-22)
.claude\memory\knowledge.md:141:### Windows Hooks Work via Python (2026-02-13, updated 2026-03-19, verified: 2026-03-19
)
.claude\memory\knowledge.md:150:### Hook Scripts Must Not Contain Their Own Detection Targets (2026-02-23, verified: 20
26-02-23)
.claude\memory\knowledge.md:158:### Claude Code Has 17 Hook Events (2026-02-23, verified: 2026-02-23)
.claude\memory\knowledge.md:165:### Memory Compliance is ~30-40% (2026-02-22, verified: 2026-02-22)
.claude\memory\knowledge.md:171:### Hook Enforcement > Instruction Enforcement (2026-02-24, verified: 2026-02-24)
.claude\memory\knowledge.md:178:### Session-Orient Hook as Context Injection (2026-02-24, verified: 2026-02-24)
.claude\memory\knowledge.md:185:### Warn-Don't-Block Validation (2026-02-24, verified: 2026-02-24)
.claude\memory\knowledge.md:193:### Structured Handoff Protocol (2026-02-24, verified: 2026-02-24)
.claude\memory\knowledge.md:199:### memory-engine.py CLI Accepts Both File and Directory (2026-02-27, verified: 2026-02
-27)
.claude\memory\knowledge.md:205:### GPT-5.5 via Codex CLI for ChatGPT Accounts (2026-04-24, verified: 2026-04-24)
.claude\memory\knowledge.md:215:### Codex Prompts Must Go Via stdin on Windows (2026-04-24, verified: 2026-04-24)
.claude\memory\knowledge.md:221:### Opus as Memory Keeper for Stateless Codex (2026-04-24, verified: 2026-04-24)
.claude\memory\knowledge.md:229:### Clean Tree Required Before codex-implement.py Runs (2026-04-24, verified: 2026-04-2
4)
.claude\memory\knowledge.md:236:### Codex Scope-Fence File Mode Needs Explicit @ Prefix (2026-04-24, verified: 2026-04-
24)
.claude\memory\knowledge.md:242:### Codex Sandbox Lacks py -3 on Windows (2026-04-24, verified: 2026-04-24)
.claude\memory\knowledge.md:247:### Speed Profile as Single Knob for Codex Latency (2026-04-24, verified: 2026-04-24)
.claude\memory\knowledge.md:253:### AGENTS.md as Shared Codex Project Context (2026-04-24, verified: 2026-04-24)



codex
I found the relevant memory structure. I’ll add focused tests first, then the CLI implementation.
  ✓ Read applicable implementation guidance
  ✓ Inspect existing script patterns
  → Implement CLI and tests
  • Run required commands
  • Prepare handoff report
**Considering testing implementation**

I need to implement tests, possibly by importing the hyphen script using importlib.util. While I can write tests with the unittest standard library, I’m pondering if to do that after creating the script. TDD suggests starting with tests, but since the script isn’t created yet, I can work on both simultaneously. I also need to check line counts after I design the script and consider how to effectively log events and manage decorators for logging functions. This could get a bit complicated!
**Reflecting on test functions and logging**

I'm considering whether code changes include test functions, which seems universal but may be impractical. I could add a setUp method without logging, but I might choose to ignore that for tests. I need to ensure logs are formatted in JSON and think about the JsonFormatter class I’ll create. I’m also weighing when to configure logging levels based on verbosity. It seems crucial that every function logs its entry, exit, and errors, even if logging isn't configured yet!
apply patch
patch: completed
C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\codex\task-V1-knowledge-decay-report\.claude/scripts/test_knowledge_decay_report.py
diff --git a/.claude/scripts/test_knowledge_decay_report.py b/.claude/scripts/test_knowledge_decay_report.py
new file mode 100644
index 0000000000000000000000000000000000000000..f5e06729bb3a550ff345b4cf8b883c350128a62a
--- /dev/null
+++ b/.claude/scripts/test_knowledge_decay_report.py
@@ -0,0 +1,83 @@
+import importlib.util
+import json
+import tempfile
+import unittest
+from datetime import date
+from pathlib import Path
+
+
+SCRIPT_PATH = Path(__file__).with_name("knowledge-decay-report.py")
+SPEC = importlib.util.spec_from_file_location("knowledge_decay_report", SCRIPT_PATH)
+report = importlib.util.module_from_spec(SPEC)
+SPEC.loader.exec_module(report)
+
+
+def write_memory(root, knowledge_text, active_text=None):
+    memory = Path(root) / ".claude" / "memory"
+    memory.mkdir(parents=True)
+    knowledge_path = memory / "knowledge.md"
+    knowledge_path.write_text(knowledge_text, encoding="utf-8")
+    if active_text is not None:
+        (memory / "activeContext.md").write_text(active_text, encoding="utf-8")
+    return knowledge_path
+
+
+class KnowledgeDecayReportTests(unittest.TestCase):
+    def make_report(self, text, today="2026-04-25", active_text=None, include_gotchas=True):
+        with tempfile.TemporaryDirectory() as root:
+            knowledge_path = write_memory(root, text, active_text)
+            return report.make_report(
+                knowledge_path,
+                date.fromisoformat(today),
+                include_gotchas,
+                (14, 30, 90),
+            )
+
+    def test_fresh_entry_active(self):
+        data = self.make_report("## Patterns\n### Fresh (2026-04-20, verified: 2026-04-20)\n")
+        self.assertEqual(data["tiers"]["active"][0]["tier"], "active")
+
+    def test_twenty_days_warm(self):
+        data = self.make_report("## Patterns\n### Warm One (2026-04-05, verified: 2026-04-05)\n")
+        self.assertEqual(data["summary"]["warm"], 1)
+
+    def test_sixty_days_cold(self):
+        data = self.make_report("## Patterns\n### Cold One (2026-02-24, verified: 2026-02-24)\n")
+        self.assertEqual(data["tiers"]["cold"][0]["age_days"], 60)
+
+    def test_hundred_twenty_days_archive(self):
+        data = self.make_report("## Patterns\n### Old One (2025-12-26, verified: 2025-12-26)\n")
+        self.assertEqual(data["summary"]["archive"], 1)
+
+    def test_missing_verified_unparsed(self):
+        data = self.make_report("## Patterns\n### Missing Verified (2026-01-01)\n")
+        self.assertEqual(data["tiers"]["unparsed"][0]["tier"], "unparsed")
+
+    def test_today_override_applied(self):
+        data = self.make_report("## Patterns\n### Override (2026-04-01, verified: 2026-04-01)\n", today="2026-04-08")
+        self.assertEqual(data["tiers"]["active"][0]["age_days"], 7)
+
+    def test_patterns_only_excludes_gotchas(self):
+        text = "## Patterns\n### Pattern A (2026-04-20, verified: 2026-04-20)\n## Gotchas\n### Gotcha A (2026-04-20, verified: 2026-04-20)\n"
+        data = self.make_report(text, include_gotchas=False)
+        self.assertEqual(data["summary"]["total"], 1)
+        self.assertEqual(data["tiers"]["active"][0]["name"], "Pattern A")
+
+    def test_json_schema_round_trip(self):
+        data = self.make_report("## Patterns\n### Json One (2026-04-20, verified: 2026-04-20)\n")
+        loaded = json.loads(json.dumps(data))
+        self.assertEqual(set(["generated_at", "today", "tiers", "summary"]).issubset(loaded), True)
+        self.assertEqual(set(loaded["tiers"]["active"][0]), set(["name", "verified", "created", "age_days", "tier", "line_no"]))
+
+    def test_promotion_candidate_detection(self):
+        text = "## Patterns\n### Promote Me (2026-04-01, verified: 2026-04-01)\n"
+        data = self.make_report(text, active_text="We should revisit promote me today.")
+        self.assertEqual(data["promotion_candidates"][0]["name"], "Promote Me")
+
+    def test_empty_knowledge_total_zero(self):
+        data = self.make_report("")
+        self.assertEqual(data["summary"]["total"], 0)
+
+
+if __name__ == "__main__":
+    unittest.main()

diff --git a/.claude/scripts/test_knowledge_decay_report.py b/.claude/scripts/test_knowledge_decay_report.py
new file mode 100644
index 0000000000000000000000000000000000000000..f5e06729bb3a550ff345b4cf8b883c350128a62a
--- /dev/null
+++ b/.claude/scripts/test_knowledge_decay_report.py
@@ -0,0 +1,83 @@
+import importlib.util
+import json
+import tempfile
+import unittest
+from datetime import date
+from pathlib import Path
+
+
+SCRIPT_PATH = Path(__file__).with_name("knowledge-decay-report.py")
+SPEC = importlib.util.spec_from_file_location("knowledge_decay_report", SCRIPT_PATH)
+report = importlib.util.module_from_spec(SPEC)
+SPEC.loader.exec_module(report)
+
+
+def write_memory(root, knowledge_text, active_text=None):
+    memory = Path(root) / ".claude" / "memory"
+    memory.mkdir(parents=True)
+    knowledge_path = memory / "knowledge.md"
+    knowledge_path.write_text(knowledge_text, encoding="utf-8")
+    if active_text is not None:
+        (memory / "activeContext.md").write_text(active_text, encoding="utf-8")
+    return knowledge_path
+
+
+class KnowledgeDecayReportTests(unittest.TestCase):
+    def make_report(self, text, today="2026-04-25", active_text=None, include_gotchas=True):
+        with tempfile.TemporaryDirectory() as root:
+            knowledge_path = write_memory(root, text, active_text)
+            return report.make_report(
+                knowledge_path,
+                date.fromisoformat(today),
+                include_gotchas,
+                (14, 30, 90),
+            )
+
+    def test_fresh_entry_active(self):
+        data = self.make_report("## Patterns\n### Fresh (2026-04-20, verified: 2026-04-20)\n")
+        self.assertEqual(data["tiers"]["active"][0]["tier"], "active")
+
+    def test_twenty_days_warm(self):
+        data = self.make_report("## Patterns\n### Warm One (2026-04-05, verified: 2026-04-05)\n")
+        self.assertEqual(data["summary"]["warm"], 1)
+
+    def test_sixty_days_cold(self):
+        data = self.make_report("## Patterns\n### Cold One (2026-02-24, verified: 2026-02-24)\n")
+        self.assertEqual(data["tiers"]["cold"][0]["age_days"], 60)
+
+    def test_hundred_twenty_days_archive(self):
+        data = self.make_report("## Patterns\n### Old One (2025-12-26, verified: 2025-12-26)\n")
+        self.assertEqual(data["summary"]["archive"], 1)
+
+    def test_missing_verified_unparsed(self):
+        data = self.make_report("## Patterns\n### Missing Verified (2026-01-01)\n")
+        self.assertEqual(data["tiers"]["unparsed"][0]["tier"], "unparsed")
+
+    def test_today_override_applied(self):
+        data = self.make_report("## Patterns\n### Override (2026-04-01, verified: 2026-04-01)\n", today="2026-04-08")
+        self.assertEqual(data["tiers"]["active"][0]["age_days"], 7)
+
+    def test_patterns_only_excludes_gotchas(self):
+        text = "## Patterns\n### Pattern A (2026-04-20, verified: 2026-04-20)\n## Gotchas\n### Gotcha A (2026-04-20, verified: 2026-04-20)\n"
+        data = self.make_report(text, include_gotchas=False)
+        self.assertEqual(data["summary"]["total"], 1)
+        self.assertEqual(data["tiers"]["active"][0]["name"], "Pattern A")
+
+    def test_json_schema_round_trip(self):
+        data = self.make_report("## Patterns\n### Json One (2026-04-20, verified: 2026-04-20)\n")
+        loaded = json.loads(json.dumps(data))
+        self.assertEqual(set(["generated_at", "today", "tiers", "summary"]).issubset(loaded), True)
+        self.assertEqual(set(loaded["tiers"]["active"][0]), set(["name", "verified", "created", "age_days", "tier", "line_no"]))
+
+    def test_promotion_candidate_detection(self):
+        text = "## Patterns\n### Promote Me (2026-04-01, verified: 2026-04-01)\n"
+        data = self.make_report(text, active_text="We should revisit promote me today.")
+        self.assertEqual(data["promotion_candidates"][0]["name"], "Promote Me")
+
+    def test_empty_knowledge_total_zero(self):
+        data = self.make_report("")
+        self.assertEqual(data["summary"]["total"], 0)
+
+
+if __name__ == "__main__":
+    unittest.main()

codex
Tests are in place. Now I’ll add the CLI with minimal, stdlib-only logic.
apply patch
patch: completed
C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\codex\task-V1-knowledge-decay-report\.claude/scripts/knowledge-decay-report.py
diff --git a/.claude/scripts/knowledge-decay-report.py b/.claude/scripts/knowledge-decay-report.py
new file mode 100644
index 0000000000000000000000000000000000000000..145c275c929084d0d84834375b0241c46b4effdc
--- /dev/null
+++ b/.claude/scripts/knowledge-decay-report.py
@@ -0,0 +1,283 @@
+#!/usr/bin/env python3
+"""Audit knowledge.md entries by verification age tier."""
+import argparse
+import json
+import logging
+import re
+import sys
+from datetime import date
+from pathlib import Path
+
+
+TIERS = ("active", "warm", "cold", "archive", "unparsed")
+DEFAULT_THRESHOLDS = (14, 30, 90)
+ENTRY_RE = re.compile(r"^###\s+(.+?)\s+\((\d{4}-\d{2}-\d{2}),\s*verified:\s*(\d{4}-\d{2}-\d{2})\)\s*$")
+HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
+
+
+class JsonFormatter(logging.Formatter):
+    def format(self, record):
+        payload = {
+            "level": record.levelname,
+            "message": record.getMessage(),
+            "logger": record.name,
+        }
+        if record.exc_info:
+            payload["exc_info"] = self.formatException(record.exc_info)
+        for key, value in getattr(record, "context", {}).items():
+            payload[key] = value
+        return json.dumps(payload, sort_keys=True)
+
+
+logger = logging.getLogger("knowledge_decay_report")
+
+
+def configure_logging(verbose):
+    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
+    handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(JsonFormatter())
+    root = logging.getLogger()
+    root.handlers.clear()
+    root.addHandler(handler)
+    root.setLevel(logging.DEBUG if verbose else logging.WARNING)
+    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})
+
+
+def parse_args(argv):
+    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
+    parser = argparse.ArgumentParser(description="Audit .claude/memory/knowledge.md verification decay tiers.")
+    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
+    parser.add_argument("--knowledge-path", default=".claude/memory/knowledge.md", help="Path to knowledge.md.")
+    parser.add_argument("--today", help="Override today's date as YYYY-MM-DD.")
+    group = parser.add_mutually_exclusive_group()
+    group.add_argument("--include-gotchas", action="store_true", help="Include Gotchas section entries (default).")
+    group.add_argument("--patterns-only", action="store_true", help="Only include Patterns section entries.")
+    parser.add_argument("--threshold-days", default="14,30,90", help="Comma-separated active,warm,cold day cutoffs.")
+    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG structured logs on stderr.")
+    args = parser.parse_args(argv)
+    logger.debug("exit", extra={"context": {"function": "parse_args", "json": args.json}})
+    return args
+
+
+def parse_thresholds(value):
+    logger.debug("entry", extra={"context": {"function": "parse_thresholds", "value": value}})
+    try:
+        parts = tuple(int(part.strip()) for part in value.split(","))
+        if len(parts) != 3 or parts[0] < 0 or not (parts[0] < parts[1] < parts[2]):
+            raise ValueError("thresholds must be three increasing non-negative integers")
+        logger.debug("exit", extra={"context": {"function": "parse_thresholds", "thresholds": parts}})
+        return parts
+    except ValueError:
+        logger.exception("invalid_thresholds", extra={"context": {"function": "parse_thresholds", "value": value}})
+        raise
+
+
+def parse_today(value):
+    logger.debug("entry", extra={"context": {"function": "parse_today", "provided": bool(value)}})
+    try:
+        result = date.fromisoformat(value) if value else date.today()
+        logger.debug("exit", extra={"context": {"function": "parse_today", "today": result.isoformat()}})
+        return result
+    except ValueError:
+        logger.exception("invalid_today", extra={"context": {"function": "parse_today", "value": value}})
+        raise
+
+
+def classify_age(age_days, thresholds):
+    logger.debug("entry", extra={"context": {"function": "classify_age", "age_days": age_days}})
+    active, warm, cold = thresholds
+    if age_days <= active:
+        tier = "active"
+    elif age_days <= warm:
+        tier = "warm"
+    elif age_days <= cold:
+        tier = "cold"
+    else:
+        tier = "archive"
+    logger.debug("exit", extra={"context": {"function": "classify_age", "tier": tier}})
+    return tier
+
+
+def blank_report(today_value):
+    logger.debug("entry", extra={"context": {"function": "blank_report", "today": today_value.isoformat()}})
+    result = {
+        "generated_at": date.today().isoformat(),
+        "today": today_value.isoformat(),
+        "tiers": {tier: [] for tier in TIERS},
+        "summary": {tier: 0 for tier in TIERS},
+        "promotion_candidates": [],
+    }
+    result["summary"]["total"] = 0
+    logger.debug("exit", extra={"context": {"function": "blank_report"}})
+    return result
+
+
+def extract_name(line):
+    logger.debug("entry", extra={"context": {"function": "extract_name"}})
+    text = line[4:].strip()
+    name = text.split(" (", 1)[0].strip() or text[:80]
+    logger.debug("exit", extra={"context": {"function": "extract_name", "name": name}})
+    return name
+
+
+def parse_entry_line(line, line_no, today_value, thresholds):
+    logger.debug("entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+    match = ENTRY_RE.match(line)
+    if not match:
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.warning("unparsed_entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+    try:
+        name, created_text, verified_text = match.groups()
+        created = date.fromisoformat(created_text)
+        verified = date.fromisoformat(verified_text)
+        age_days = (today_value - verified).days
+        tier = classify_age(age_days, thresholds)
+        entry = {
+            "name": name,
+            "verified": verified.isoformat(),
+            "created": created.isoformat(),
+            "age_days": age_days,
+            "tier": tier,
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": tier}})
+        return entry
+    except ValueError:
+        logger.exception("malformed_entry_dates", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+
+
+def iter_relevant_lines(text, include_gotchas):
+    logger.debug("entry", extra={"context": {"function": "iter_relevant_lines", "include_gotchas": include_gotchas}})
+    section = None
+    for line_no, line in enumerate(text.splitlines(), start=1):
+        heading = HEADING_RE.match(line)
+        if heading:
+            title = heading.group(1).strip().lower()
+            section = title if title in {"patterns", "gotchas"} else None
+            continue
+        if line.startswith("### ") and section == "patterns":
+            yield line_no, line
+        elif line.startswith("### ") and section == "gotchas" and include_gotchas:
+            yield line_no, line
+    logger.debug("exit", extra={"context": {"function": "iter_relevant_lines"}})
+
+
+def detect_promotion_candidates(report, knowledge_path):
+    logger.debug("entry", extra={"context": {"function": "detect_promotion_candidates", "path": str(knowledge_path)}})
+    try:
+        active_path = knowledge_path.parent / "activeContext.md"
+        if not active_path.exists():
+            logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": 0}})
+            return []
+        active_text = active_path.read_text(encoding="utf-8", errors="replace").lower()
+        candidates = []
+        for tier in ("warm", "cold", "archive"):
+            for entry in report["tiers"][tier]:
+                if entry["name"].lower() in active_text:
+                    candidates.append(entry)
+        logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": len(candidates)}})
+        return candidates
+    except OSError:
+        logger.exception("active_context_read_failed", extra={"context": {"function": "detect_promotion_candidates"}})
+        return []
+
+
+def make_report(knowledge_path, today_value, include_gotchas, thresholds):
+    logger.debug("entry", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+    report = blank_report(today_value)
+    try:
+        text = Path(knowledge_path).read_text(encoding="utf-8", errors="replace")
+    except OSError:
+        logger.exception("knowledge_read_failed", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+        raise
+    for line_no, line in iter_relevant_lines(text, include_gotchas):
+        entry = parse_entry_line(line, line_no, today_value, thresholds)
+        report["tiers"][entry["tier"]].append(entry)
+    for tier in TIERS:
+        report["summary"][tier] = len(report["tiers"][tier])
+    report["summary"]["total"] = sum(report["summary"][tier] for tier in TIERS)
+    report["promotion_candidates"] = detect_promotion_candidates(report, Path(knowledge_path))
+    logger.debug("exit", extra={"context": {"function": "make_report", "total": report["summary"]["total"]}})
+    return report
+
+
+def format_entry(entry):
+    logger.debug("entry", extra={"context": {"function": "format_entry", "tier": entry["tier"]}})
+    if entry["tier"] == "unparsed":
+        text = f"* {entry['name']} (line={entry['line_no']})"
+    else:
+        text = f"* {entry['name']} ({entry['verified']}, age={entry['age_days']}d)"
+    result = text[:80]
+    logger.debug("exit", extra={"context": {"function": "format_entry", "length": len(result)}})
+    return result
+
+
+def format_text_report(report):
+    logger.debug("entry", extra={"context": {"function": "format_text_report", "total": report["summary"]["total"]}})
+    lines = [
+        "Tier    | Count | Entries (truncated to first 80 chars)",
+        "--------+-------+-----------------------------------------",
+    ]
+    for tier in TIERS:
+        entries = report["tiers"][tier]
+        first = format_entry(entries[0]) if entries else ""
+        lines.append(f"{tier:<8}| {len(entries):^5} | {first}")
+        for entry in entries[1:]:
+            lines.append(f"{'':8}  {'':5}   {format_entry(entry)}")
+    lines.append(f"Total   | {report['summary']['total']:^5} |")
+    lines.extend(["", "## Age histogram"])
+    for tier in TIERS:
+        lines.append(f"{tier}: {report['summary'][tier]}")
+    candidates = report["promotion_candidates"]
+    lines.extend(["", f"## Promotion candidates ({len(candidates)}):"])
+    for entry in candidates:
+        lines.append(format_entry(entry))
+    result = "\n".join(lines)
+    logger.debug("exit", extra={"context": {"function": "format_text_report", "length": len(result)}})
+    return result
+
+
+def main(argv=None):
+    if argv is None:
+        argv = sys.argv[1:]
+    args = parse_args(argv)
+    configure_logging(args.verbose)
+    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
+    try:
+        today_value = parse_today(args.today)
+        thresholds = parse_thresholds(args.threshold_days)
+        data = make_report(Path(args.knowledge_path), today_value, not args.patterns_only, thresholds)
+        if args.json:
+            print(json.dumps(data, indent=2, sort_keys=True))
+        else:
+            print(format_text_report(data))
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 0}})
+        return 0
+    except (OSError, ValueError) as exc:
+        logger.exception("fatal_error", extra={"context": {"function": "main"}})
+        print(f"error: {exc}", file=sys.stderr)
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 2}})
+        return 2
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/.claude/scripts/test_knowledge_decay_report.py b/.claude/scripts/test_knowledge_decay_report.py
new file mode 100644
index 0000000000000000000000000000000000000000..f5e06729bb3a550ff345b4cf8b883c350128a62a
--- /dev/null
+++ b/.claude/scripts/test_knowledge_decay_report.py
@@ -0,0 +1,83 @@
+import importlib.util
+import json
+import tempfile
+import unittest
+from datetime import date
+from pathlib import Path
+
+
+SCRIPT_PATH = Path(__file__).with_name("knowledge-decay-report.py")
+SPEC = importlib.util.spec_from_file_location("knowledge_decay_report", SCRIPT_PATH)
+report = importlib.util.module_from_spec(SPEC)
+SPEC.loader.exec_module(report)
+
+
+def write_memory(root, knowledge_text, active_text=None):
+    memory = Path(root) / ".claude" / "memory"
+    memory.mkdir(parents=True)
+    knowledge_path = memory / "knowledge.md"
+    knowledge_path.write_text(knowledge_text, encoding="utf-8")
+    if active_text is not None:
+        (memory / "activeContext.md").write_text(active_text, encoding="utf-8")
+    return knowledge_path
+
+
+class KnowledgeDecayReportTests(unittest.TestCase):
+    def make_report(self, text, today="2026-04-25", active_text=None, include_gotchas=True):
+        with tempfile.TemporaryDirectory() as root:
+            knowledge_path = write_memory(root, text, active_text)
+            return report.make_report(
+                knowledge_path,
+                date.fromisoformat(today),
+                include_gotchas,
+                (14, 30, 90),
+            )
+
+    def test_fresh_entry_active(self):
+        data = self.make_report("## Patterns\n### Fresh (2026-04-20, verified: 2026-04-20)\n")
+        self.assertEqual(data["tiers"]["active"][0]["tier"], "active")
+
+    def test_twenty_days_warm(self):
+        data = self.make_report("## Patterns\n### Warm One (2026-04-05, verified: 2026-04-05)\n")
+        self.assertEqual(data["summary"]["warm"], 1)
+
+    def test_sixty_days_cold(self):
+        data = self.make_report("## Patterns\n### Cold One (2026-02-24, verified: 2026-02-24)\n")
+        self.assertEqual(data["tiers"]["cold"][0]["age_days"], 60)
+
+    def test_hundred_twenty_days_archive(self):
+        data = self.make_report("## Patterns\n### Old One (2025-12-26, verified: 2025-12-26)\n")
+        self.assertEqual(data["summary"]["archive"], 1)
+
+    def test_missing_verified_unparsed(self):
+        data = self.make_report("## Patterns\n### Missing Verified (2026-01-01)\n")
+        self.assertEqual(data["tiers"]["unparsed"][0]["tier"], "unparsed")
+
+    def test_today_override_applied(self):
+        data = self.make_report("## Patterns\n### Override (2026-04-01, verified: 2026-04-01)\n", today="2026-04-08")
+        self.assertEqual(data["tiers"]["active"][0]["age_days"], 7)
+
+    def test_patterns_only_excludes_gotchas(self):
+        text = "## Patterns\n### Pattern A (2026-04-20, verified: 2026-04-20)\n## Gotchas\n### Gotcha A (2026-04-20, verified: 2026-04-20)\n"
+        data = self.make_report(text, include_gotchas=False)
+        self.assertEqual(data["summary"]["total"], 1)
+        self.assertEqual(data["tiers"]["active"][0]["name"], "Pattern A")
+
+    def test_json_schema_round_trip(self):
+        data = self.make_report("## Patterns\n### Json One (2026-04-20, verified: 2026-04-20)\n")
+        loaded = json.loads(json.dumps(data))
+        self.assertEqual(set(["generated_at", "today", "tiers", "summary"]).issubset(loaded), True)
+        self.assertEqual(set(loaded["tiers"]["active"][0]), set(["name", "verified", "created", "age_days", "tier", "line_no"]))
+
+    def test_promotion_candidate_detection(self):
+        text = "## Patterns\n### Promote Me (2026-04-01, verified: 2026-04-01)\n"
+        data = self.make_report(text, active_text="We should revisit promote me today.")
+        self.assertEqual(data["promotion_candidates"][0]["name"], "Promote Me")
+
+    def test_empty_knowledge_total_zero(self):
+        data = self.make_report("")
+        self.assertEqual(data["summary"]["total"], 0)
+
+
+if __name__ == "__main__":
+    unittest.main()

diff --git a/.claude/scripts/knowledge-decay-report.py b/.claude/scripts/knowledge-decay-report.py
new file mode 100644
index 0000000000000000000000000000000000000000..145c275c929084d0d84834375b0241c46b4effdc
--- /dev/null
+++ b/.claude/scripts/knowledge-decay-report.py
@@ -0,0 +1,283 @@
+#!/usr/bin/env python3
+"""Audit knowledge.md entries by verification age tier."""
+import argparse
+import json
+import logging
+import re
+import sys
+from datetime import date
+from pathlib import Path
+
+
+TIERS = ("active", "warm", "cold", "archive", "unparsed")
+DEFAULT_THRESHOLDS = (14, 30, 90)
+ENTRY_RE = re.compile(r"^###\s+(.+?)\s+\((\d{4}-\d{2}-\d{2}),\s*verified:\s*(\d{4}-\d{2}-\d{2})\)\s*$")
+HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
+
+
+class JsonFormatter(logging.Formatter):
+    def format(self, record):
+        payload = {
+            "level": record.levelname,
+            "message": record.getMessage(),
+            "logger": record.name,
+        }
+        if record.exc_info:
+            payload["exc_info"] = self.formatException(record.exc_info)
+        for key, value in getattr(record, "context", {}).items():
+            payload[key] = value
+        return json.dumps(payload, sort_keys=True)
+
+
+logger = logging.getLogger("knowledge_decay_report")
+
+
+def configure_logging(verbose):
+    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
+    handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(JsonFormatter())
+    root = logging.getLogger()
+    root.handlers.clear()
+    root.addHandler(handler)
+    root.setLevel(logging.DEBUG if verbose else logging.WARNING)
+    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})
+
+
+def parse_args(argv):
+    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
+    parser = argparse.ArgumentParser(description="Audit .claude/memory/knowledge.md verification decay tiers.")
+    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
+    parser.add_argument("--knowledge-path", default=".claude/memory/knowledge.md", help="Path to knowledge.md.")
+    parser.add_argument("--today", help="Override today's date as YYYY-MM-DD.")
+    group = parser.add_mutually_exclusive_group()
+    group.add_argument("--include-gotchas", action="store_true", help="Include Gotchas section entries (default).")
+    group.add_argument("--patterns-only", action="store_true", help="Only include Patterns section entries.")
+    parser.add_argument("--threshold-days", default="14,30,90", help="Comma-separated active,warm,cold day cutoffs.")
+    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG structured logs on stderr.")
+    args = parser.parse_args(argv)
+    logger.debug("exit", extra={"context": {"function": "parse_args", "json": args.json}})
+    return args
+
+
+def parse_thresholds(value):
+    logger.debug("entry", extra={"context": {"function": "parse_thresholds", "value": value}})
+    try:
+        parts = tuple(int(part.strip()) for part in value.split(","))
+        if len(parts) != 3 or parts[0] < 0 or not (parts[0] < parts[1] < parts[2]):
+            raise ValueError("thresholds must be three increasing non-negative integers")
+        logger.debug("exit", extra={"context": {"function": "parse_thresholds", "thresholds": parts}})
+        return parts
+    except ValueError:
+        logger.exception("invalid_thresholds", extra={"context": {"function": "parse_thresholds", "value": value}})
+        raise
+
+
+def parse_today(value):
+    logger.debug("entry", extra={"context": {"function": "parse_today", "provided": bool(value)}})
+    try:
+        result = date.fromisoformat(value) if value else date.today()
+        logger.debug("exit", extra={"context": {"function": "parse_today", "today": result.isoformat()}})
+        return result
+    except ValueError:
+        logger.exception("invalid_today", extra={"context": {"function": "parse_today", "value": value}})
+        raise
+
+
+def classify_age(age_days, thresholds):
+    logger.debug("entry", extra={"context": {"function": "classify_age", "age_days": age_days}})
+    active, warm, cold = thresholds
+    if age_days <= active:
+        tier = "active"
+    elif age_days <= warm:
+        tier = "warm"
+    elif age_days <= cold:
+        tier = "cold"
+    else:
+        tier = "archive"
+    logger.debug("exit", extra={"context": {"function": "classify_age", "tier": tier}})
+    return tier
+
+
+def blank_report(today_value):
+    logger.debug("entry", extra={"context": {"function": "blank_report", "today": today_value.isoformat()}})
+    result = {
+        "generated_at": date.today().isoformat(),
+        "today": today_value.isoformat(),
+        "tiers": {tier: [] for tier in TIERS},
+        "summary": {tier: 0 for tier in TIERS},
+        "promotion_candidates": [],
+    }
+    result["summary"]["total"] = 0
+    logger.debug("exit", extra={"context": {"function": "blank_report"}})
+    return result
+
+
+def extract_name(line):
+    logger.debug("entry", extra={"context": {"function": "extract_name"}})
+    text = line[4:].strip()
+    name = text.split(" (", 1)[0].strip() or text[:80]
+    logger.debug("exit", extra={"context": {"function": "extract_name", "name": name}})
+    return name
+
+
+def parse_entry_line(line, line_no, today_value, thresholds):
+    logger.debug("entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+    match = ENTRY_RE.match(line)
+    if not match:
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.warning("unparsed_entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+    try:
+        name, created_text, verified_text = match.groups()
+        created = date.fromisoformat(created_text)
+        verified = date.fromisoformat(verified_text)
+        age_days = (today_value - verified).days
+        tier = classify_age(age_days, thresholds)
+        entry = {
+            "name": name,
+            "verified": verified.isoformat(),
+            "created": created.isoformat(),
+            "age_days": age_days,
+            "tier": tier,
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": tier}})
+        return entry
+    except ValueError:
+        logger.exception("malformed_entry_dates", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+
+
+def iter_relevant_lines(text, include_gotchas):
+    logger.debug("entry", extra={"context": {"function": "iter_relevant_lines", "include_gotchas": include_gotchas}})
+    section = None
+    for line_no, line in enumerate(text.splitlines(), start=1):
+        heading = HEADING_RE.match(line)
+        if heading:
+            title = heading.group(1).strip().lower()
+            section = title if title in {"patterns", "gotchas"} else None
+            continue
+        if line.startswith("### ") and section == "patterns":
+            yield line_no, line
+        elif line.startswith("### ") and section == "gotchas" and include_gotchas:
+            yield line_no, line
+    logger.debug("exit", extra={"context": {"function": "iter_relevant_lines"}})
+
+
+def detect_promotion_candidates(report, knowledge_path):
+    logger.debug("entry", extra={"context": {"function": "detect_promotion_candidates", "path": str(knowledge_path)}})
+    try:
+        active_path = knowledge_path.parent / "activeContext.md"
+        if not active_path.exists():
+            logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": 0}})
+            return []
+        active_text = active_path.read_text(encoding="utf-8", errors="replace").lower()
+        candidates = []
+        for tier in ("warm", "cold", "archive"):
+            for entry in report["tiers"][tier]:
+                if entry["name"].lower() in active_text:
+                    candidates.append(entry)
+        logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": len(candidates)}})
+        return candidates
+    except OSError:
+        logger.exception("active_context_read_failed", extra={"context": {"function": "detect_promotion_candidates"}})
+        return []
+
+
+def make_report(knowledge_path, today_value, include_gotchas, thresholds):
+    logger.debug("entry", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+    report = blank_report(today_value)
+    try:
+        text = Path(knowledge_path).read_text(encoding="utf-8", errors="replace")
+    except OSError:
+        logger.exception("knowledge_read_failed", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+        raise
+    for line_no, line in iter_relevant_lines(text, include_gotchas):
+        entry = parse_entry_line(line, line_no, today_value, thresholds)
+        report["tiers"][entry["tier"]].append(entry)
+    for tier in TIERS:
+        report["summary"][tier] = len(report["tiers"][tier])
+    report["summary"]["total"] = sum(report["summary"][tier] for tier in TIERS)
+    report["promotion_candidates"] = detect_promotion_candidates(report, Path(knowledge_path))
+    logger.debug("exit", extra={"context": {"function": "make_report", "total": report["summary"]["total"]}})
+    return report
+
+
+def format_entry(entry):
+    logger.debug("entry", extra={"context": {"function": "format_entry", "tier": entry["tier"]}})
+    if entry["tier"] == "unparsed":
+        text = f"* {entry['name']} (line={entry['line_no']})"
+    else:
+        text = f"* {entry['name']} ({entry['verified']}, age={entry['age_days']}d)"
+    result = text[:80]
+    logger.debug("exit", extra={"context": {"function": "format_entry", "length": len(result)}})
+    return result
+
+
+def format_text_report(report):
+    logger.debug("entry", extra={"context": {"function": "format_text_report", "total": report["summary"]["total"]}})
+    lines = [
+        "Tier    | Count | Entries (truncated to first 80 chars)",
+        "--------+-------+-----------------------------------------",
+    ]
+    for tier in TIERS:
+        entries = report["tiers"][tier]
+        first = format_entry(entries[0]) if entries else ""
+        lines.append(f"{tier:<8}| {len(entries):^5} | {first}")
+        for entry in entries[1:]:
+            lines.append(f"{'':8}  {'':5}   {format_entry(entry)}")
+    lines.append(f"Total   | {report['summary']['total']:^5} |")
+    lines.extend(["", "## Age histogram"])
+    for tier in TIERS:
+        lines.append(f"{tier}: {report['summary'][tier]}")
+    candidates = report["promotion_candidates"]
+    lines.extend(["", f"## Promotion candidates ({len(candidates)}):"])
+    for entry in candidates:
+        lines.append(format_entry(entry))
+    result = "\n".join(lines)
+    logger.debug("exit", extra={"context": {"function": "format_text_report", "length": len(result)}})
+    return result
+
+
+def main(argv=None):
+    if argv is None:
+        argv = sys.argv[1:]
+    args = parse_args(argv)
+    configure_logging(args.verbose)
+    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
+    try:
+        today_value = parse_today(args.today)
+        thresholds = parse_thresholds(args.threshold_days)
+        data = make_report(Path(args.knowledge_path), today_value, not args.patterns_only, thresholds)
+        if args.json:
+            print(json.dumps(data, indent=2, sort_keys=True))
+        else:
+            print(format_text_report(data))
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 0}})
+        return 0
+    except (OSError, ValueError) as exc:
+        logger.exception("fatal_error", extra={"context": {"function": "main"}})
+        print(f"error: {exc}", file=sys.stderr)
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 2}})
+        return 2
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/.claude/scripts/test_knowledge_decay_report.py b/.claude/scripts/test_knowledge_decay_report.py
new file mode 100644
index 0000000000000000000000000000000000000000..f5e06729bb3a550ff345b4cf8b883c350128a62a
--- /dev/null
+++ b/.claude/scripts/test_knowledge_decay_report.py
@@ -0,0 +1,83 @@
+import importlib.util
+import json
+import tempfile
+import unittest
+from datetime import date
+from pathlib import Path
+
+
+SCRIPT_PATH = Path(__file__).with_name("knowledge-decay-report.py")
+SPEC = importlib.util.spec_from_file_location("knowledge_decay_report", SCRIPT_PATH)
+report = importlib.util.module_from_spec(SPEC)
+SPEC.loader.exec_module(report)
+
+
+def write_memory(root, knowledge_text, active_text=None):
+    memory = Path(root) / ".claude" / "memory"
+    memory.mkdir(parents=True)
+    knowledge_path = memory / "knowledge.md"
+    knowledge_path.write_text(knowledge_text, encoding="utf-8")
+    if active_text is not None:
+        (memory / "activeContext.md").write_text(active_text, encoding="utf-8")
+    return knowledge_path
+
+
+class KnowledgeDecayReportTests(unittest.TestCase):
+    def make_report(self, text, today="2026-04-25", active_text=None, include_gotchas=True):
+        with tempfile.TemporaryDirectory() as root:
+            knowledge_path = write_memory(root, text, active_text)
+            return report.make_report(
+                knowledge_path,
+                date.fromisoformat(today),
+                include_gotchas,
+                (14, 30, 90),
+            )
+
+    def test_fresh_entry_active(self):
+        data = self.make_report("## Patterns\n### Fresh (2026-04-20, verified: 2026-04-20)\n")
+        self.assertEqual(data["tiers"]["active"][0]["tier"], "active")
+
+    def test_twenty_days_warm(self):
+        data = self.make_report("## Patterns\n### Warm One (2026-04-05, verified: 2026-04-05)\n")
+        self.assertEqual(data["summary"]["warm"], 1)
+
+    def test_sixty_days_cold(self):
+        data = self.make_report("## Patterns\n### Cold One (2026-02-24, verified: 2026-02-24)\n")
+        self.assertEqual(data["tiers"]["cold"][0]["age_days"], 60)
+
+    def test_hundred_twenty_days_archive(self):
+        data = self.make_report("## Patterns\n### Old One (2025-12-26, verified: 2025-12-26)\n")
+        self.assertEqual(data["summary"]["archive"], 1)
+
+    def test_missing_verified_unparsed(self):
+        data = self.make_report("## Patterns\n### Missing Verified (2026-01-01)\n")
+        self.assertEqual(data["tiers"]["unparsed"][0]["tier"], "unparsed")
+
+    def test_today_override_applied(self):
+        data = self.make_report("## Patterns\n### Override (2026-04-01, verified: 2026-04-01)\n", today="2026-04-08")
+        self.assertEqual(data["tiers"]["active"][0]["age_days"], 7)
+
+    def test_patterns_only_excludes_gotchas(self):
+        text = "## Patterns\n### Pattern A (2026-04-20, verified: 2026-04-20)\n## Gotchas\n### Gotcha A (2026-04-20, verified: 2026-04-20)\n"
+        data = self.make_report(text, include_gotchas=False)
+        self.assertEqual(data["summary"]["total"], 1)
+        self.assertEqual(data["tiers"]["active"][0]["name"], "Pattern A")
+
+    def test_json_schema_round_trip(self):
+        data = self.make_report("## Patterns\n### Json One (2026-04-20, verified: 2026-04-20)\n")
+        loaded = json.loads(json.dumps(data))
+        self.assertEqual(set(["generated_at", "today", "tiers", "summary"]).issubset(loaded), True)
+        self.assertEqual(set(loaded["tiers"]["active"][0]), set(["name", "verified", "created", "age_days", "tier", "line_no"]))
+
+    def test_promotion_candidate_detection(self):
+        text = "## Patterns\n### Promote Me (2026-04-01, verified: 2026-04-01)\n"
+        data = self.make_report(text, active_text="We should revisit promote me today.")
+        self.assertEqual(data["promotion_candidates"][0]["name"], "Promote Me")
+
+    def test_empty_knowledge_total_zero(self):
+        data = self.make_report("")
+        self.assertEqual(data["summary"]["total"], 0)
+
+
+if __name__ == "__main__":
+    unittest.main()

codex
Implementation is added. I’ll run the required commands now and fix anything they expose.
  ✓ Read applicable implementation guidance
  ✓ Inspect existing script patterns
  ✓ Implement CLI and tests
  → Run required commands
  • Prepare handoff report
diff --git a/.claude/scripts/knowledge-decay-report.py b/.claude/scripts/knowledge-decay-report.py
new file mode 100644
index 0000000000000000000000000000000000000000..145c275c929084d0d84834375b0241c46b4effdc
--- /dev/null
+++ b/.claude/scripts/knowledge-decay-report.py
@@ -0,0 +1,283 @@
+#!/usr/bin/env python3
+"""Audit knowledge.md entries by verification age tier."""
+import argparse
+import json
+import logging
+import re
+import sys
+from datetime import date
+from pathlib import Path
+
+
+TIERS = ("active", "warm", "cold", "archive", "unparsed")
+DEFAULT_THRESHOLDS = (14, 30, 90)
+ENTRY_RE = re.compile(r"^###\s+(.+?)\s+\((\d{4}-\d{2}-\d{2}),\s*verified:\s*(\d{4}-\d{2}-\d{2})\)\s*$")
+HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
+
+
+class JsonFormatter(logging.Formatter):
+    def format(self, record):
+        payload = {
+            "level": record.levelname,
+            "message": record.getMessage(),
+            "logger": record.name,
+        }
+        if record.exc_info:
+            payload["exc_info"] = self.formatException(record.exc_info)
+        for key, value in getattr(record, "context", {}).items():
+            payload[key] = value
+        return json.dumps(payload, sort_keys=True)
+
+
+logger = logging.getLogger("knowledge_decay_report")
+
+
+def configure_logging(verbose):
+    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
+    handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(JsonFormatter())
+    root = logging.getLogger()
+    root.handlers.clear()
+    root.addHandler(handler)
+    root.setLevel(logging.DEBUG if verbose else logging.WARNING)
+    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})
+
+
+def parse_args(argv):
+    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
+    parser = argparse.ArgumentParser(description="Audit .claude/memory/knowledge.md verification decay tiers.")
+    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
+    parser.add_argument("--knowledge-path", default=".claude/memory/knowledge.md", help="Path to knowledge.md.")
+    parser.add_argument("--today", help="Override today's date as YYYY-MM-DD.")
+    group = parser.add_mutually_exclusive_group()
+    group.add_argument("--include-gotchas", action="store_true", help="Include Gotchas section entries (default).")
+    group.add_argument("--patterns-only", action="store_true", help="Only include Patterns section entries.")
+    parser.add_argument("--threshold-days", default="14,30,90", help="Comma-separated active,warm,cold day cutoffs.")
+    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG structured logs on stderr.")
+    args = parser.parse_args(argv)
+    logger.debug("exit", extra={"context": {"function": "parse_args", "json": args.json}})
+    return args
+
+
+def parse_thresholds(value):
+    logger.debug("entry", extra={"context": {"function": "parse_thresholds", "value": value}})
+    try:
+        parts = tuple(int(part.strip()) for part in value.split(","))
+        if len(parts) != 3 or parts[0] < 0 or not (parts[0] < parts[1] < parts[2]):
+            raise ValueError("thresholds must be three increasing non-negative integers")
+        logger.debug("exit", extra={"context": {"function": "parse_thresholds", "thresholds": parts}})
+        return parts
+    except ValueError:
+        logger.exception("invalid_thresholds", extra={"context": {"function": "parse_thresholds", "value": value}})
+        raise
+
+
+def parse_today(value):
+    logger.debug("entry", extra={"context": {"function": "parse_today", "provided": bool(value)}})
+    try:
+        result = date.fromisoformat(value) if value else date.today()
+        logger.debug("exit", extra={"context": {"function": "parse_today", "today": result.isoformat()}})
+        return result
+    except ValueError:
+        logger.exception("invalid_today", extra={"context": {"function": "parse_today", "value": value}})
+        raise
+
+
+def classify_age(age_days, thresholds):
+    logger.debug("entry", extra={"context": {"function": "classify_age", "age_days": age_days}})
+    active, warm, cold = thresholds
+    if age_days <= active:
+        tier = "active"
+    elif age_days <= warm:
+        tier = "warm"
+    elif age_days <= cold:
+        tier = "cold"
+    else:
+        tier = "archive"
+    logger.debug("exit", extra={"context": {"function": "classify_age", "tier": tier}})
+    return tier
+
+
+def blank_report(today_value):
+    logger.debug("entry", extra={"context": {"function": "blank_report", "today": today_value.isoformat()}})
+    result = {
+        "generated_at": date.today().isoformat(),
+        "today": today_value.isoformat(),
+        "tiers": {tier: [] for tier in TIERS},
+        "summary": {tier: 0 for tier in TIERS},
+        "promotion_candidates": [],
+    }
+    result["summary"]["total"] = 0
+    logger.debug("exit", extra={"context": {"function": "blank_report"}})
+    return result
+
+
+def extract_name(line):
+    logger.debug("entry", extra={"context": {"function": "extract_name"}})
+    text = line[4:].strip()
+    name = text.split(" (", 1)[0].strip() or text[:80]
+    logger.debug("exit", extra={"context": {"function": "extract_name", "name": name}})
+    return name
+
+
+def parse_entry_line(line, line_no, today_value, thresholds):
+    logger.debug("entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+    match = ENTRY_RE.match(line)
+    if not match:
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.warning("unparsed_entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+    try:
+        name, created_text, verified_text = match.groups()
+        created = date.fromisoformat(created_text)
+        verified = date.fromisoformat(verified_text)
+        age_days = (today_value - verified).days
+        tier = classify_age(age_days, thresholds)
+        entry = {
+            "name": name,
+            "verified": verified.isoformat(),
+            "created": created.isoformat(),
+            "age_days": age_days,
+            "tier": tier,
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": tier}})
+        return entry
+    except ValueError:
+        logger.exception("malformed_entry_dates", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+
+
+def iter_relevant_lines(text, include_gotchas):
+    logger.debug("entry", extra={"context": {"function": "iter_relevant_lines", "include_gotchas": include_gotchas}})
+    section = None
+    for line_no, line in enumerate(text.splitlines(), start=1):
+        heading = HEADING_RE.match(line)
+        if heading:
+            title = heading.group(1).strip().lower()
+            section = title if title in {"patterns", "gotchas"} else None
+            continue
+        if line.startswith("### ") and section == "patterns":
+            yield line_no, line
+        elif line.startswith("### ") and section == "gotchas" and include_gotchas:
+            yield line_no, line
+    logger.debug("exit", extra={"context": {"function": "iter_relevant_lines"}})
+
+
+def detect_promotion_candidates(report, knowledge_path):
+    logger.debug("entry", extra={"context": {"function": "detect_promotion_candidates", "path": str(knowledge_path)}})
+    try:
+        active_path = knowledge_path.parent / "activeContext.md"
+        if not active_path.exists():
+            logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": 0}})
+            return []
+        active_text = active_path.read_text(encoding="utf-8", errors="replace").lower()
+        candidates = []
+        for tier in ("warm", "cold", "archive"):
+            for entry in report["tiers"][tier]:
+                if entry["name"].lower() in active_text:
+                    candidates.append(entry)
+        logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": len(candidates)}})
+        return candidates
+    except OSError:
+        logger.exception("active_context_read_failed", extra={"context": {"function": "detect_promotion_candidates"}})
+        return []
+
+
+def make_report(knowledge_path, today_value, include_gotchas, thresholds):
+    logger.debug("entry", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+    report = blank_report(today_value)
+    try:
+        text = Path(knowledge_path).read_text(encoding="utf-8", errors="replace")
+    except OSError:
+        logger.exception("knowledge_read_failed", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+        raise
+    for line_no, line in iter_relevant_lines(text, include_gotchas):
+        entry = parse_entry_line(line, line_no, today_value, thresholds)
+        report["tiers"][entry["tier"]].append(entry)
+    for tier in TIERS:
+        report["summary"][tier] = len(report["tiers"][tier])
+    report["summary"]["total"] = sum(report["summary"][tier] for tier in TIERS)
+    report["promotion_candidates"] = detect_promotion_candidates(report, Path(knowledge_path))
+    logger.debug("exit", extra={"context": {"function": "make_report", "total": report["summary"]["total"]}})
+    return report
+
+
+def format_entry(entry):
+    logger.debug("entry", extra={"context": {"function": "format_entry", "tier": entry["tier"]}})
+    if entry["tier"] == "unparsed":
+        text = f"* {entry['name']} (line={entry['line_no']})"
+    else:
+        text = f"* {entry['name']} ({entry['verified']}, age={entry['age_days']}d)"
+    result = text[:80]
+    logger.debug("exit", extra={"context": {"function": "format_entry", "length": len(result)}})
+    return result
+
+
+def format_text_report(report):
+    logger.debug("entry", extra={"context": {"function": "format_text_report", "total": report["summary"]["total"]}})
+    lines = [
+        "Tier    | Count | Entries (truncated to first 80 chars)",
+        "--------+-------+-----------------------------------------",
+    ]
+    for tier in TIERS:
+        entries = report["tiers"][tier]
+        first = format_entry(entries[0]) if entries else ""
+        lines.append(f"{tier:<8}| {len(entries):^5} | {first}")
+        for entry in entries[1:]:
+            lines.append(f"{'':8}  {'':5}   {format_entry(entry)}")
+    lines.append(f"Total   | {report['summary']['total']:^5} |")
+    lines.extend(["", "## Age histogram"])
+    for tier in TIERS:
+        lines.append(f"{tier}: {report['summary'][tier]}")
+    candidates = report["promotion_candidates"]
+    lines.extend(["", f"## Promotion candidates ({len(candidates)}):"])
+    for entry in candidates:
+        lines.append(format_entry(entry))
+    result = "\n".join(lines)
+    logger.debug("exit", extra={"context": {"function": "format_text_report", "length": len(result)}})
+    return result
+
+
+def main(argv=None):
+    if argv is None:
+        argv = sys.argv[1:]
+    args = parse_args(argv)
+    configure_logging(args.verbose)
+    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
+    try:
+        today_value = parse_today(args.today)
+        thresholds = parse_thresholds(args.threshold_days)
+        data = make_report(Path(args.knowledge_path), today_value, not args.patterns_only, thresholds)
+        if args.json:
+            print(json.dumps(data, indent=2, sort_keys=True))
+        else:
+            print(format_text_report(data))
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 0}})
+        return 0
+    except (OSError, ValueError) as exc:
+        logger.exception("fatal_error", extra={"context": {"function": "main"}})
+        print(f"error: {exc}", file=sys.stderr)
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 2}})
+        return 2
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/.claude/scripts/test_knowledge_decay_report.py b/.claude/scripts/test_knowledge_decay_report.py
new file mode 100644
index 0000000000000000000000000000000000000000..f5e06729bb3a550ff345b4cf8b883c350128a62a
--- /dev/null
+++ b/.claude/scripts/test_knowledge_decay_report.py
@@ -0,0 +1,83 @@
+import importlib.util
+import json
+import tempfile
+import unittest
+from datetime import date
+from pathlib import Path
+
+
+SCRIPT_PATH = Path(__file__).with_name("knowledge-decay-report.py")
+SPEC = importlib.util.spec_from_file_location("knowledge_decay_report", SCRIPT_PATH)
+report = importlib.util.module_from_spec(SPEC)
+SPEC.loader.exec_module(report)
+
+
+def write_memory(root, knowledge_text, active_text=None):
+    memory = Path(root) / ".claude" / "memory"
+    memory.mkdir(parents=True)
+    knowledge_path = memory / "knowledge.md"
+    knowledge_path.write_text(knowledge_text, encoding="utf-8")
+    if active_text is not None:
+        (memory / "activeContext.md").write_text(active_text, encoding="utf-8")
+    return knowledge_path
+
+
+class KnowledgeDecayReportTests(unittest.TestCase):
+    def make_report(self, text, today="2026-04-25", active_text=None, include_gotchas=True):
+        with tempfile.TemporaryDirectory() as root:
+            knowledge_path = write_memory(root, text, active_text)
+            return report.make_report(
+                knowledge_path,
+                date.fromisoformat(today),
+                include_gotchas,
+                (14, 30, 90),
+            )
+
+    def test_fresh_entry_active(self):
+        data = self.make_report("## Patterns\n### Fresh (2026-04-20, verified: 2026-04-20)\n")
+        self.assertEqual(data["tiers"]["active"][0]["tier"], "active")
+
+    def test_twenty_days_warm(self):
+        data = self.make_report("## Patterns\n### Warm One (2026-04-05, verified: 2026-04-05)\n")
+        self.assertEqual(data["summary"]["warm"], 1)
+
+    def test_sixty_days_cold(self):
+        data = self.make_report("## Patterns\n### Cold One (2026-02-24, verified: 2026-02-24)\n")
+        self.assertEqual(data["tiers"]["cold"][0]["age_days"], 60)
+
+    def test_hundred_twenty_days_archive(self):
+        data = self.make_report("## Patterns\n### Old One (2025-12-26, verified: 2025-12-26)\n")
+        self.assertEqual(data["summary"]["archive"], 1)
+
+    def test_missing_verified_unparsed(self):
+        data = self.make_report("## Patterns\n### Missing Verified (2026-01-01)\n")
+        self.assertEqual(data["tiers"]["unparsed"][0]["tier"], "unparsed")
+
+    def test_today_override_applied(self):
+        data = self.make_report("## Patterns\n### Override (2026-04-01, verified: 2026-04-01)\n", today="2026-04-08")
+        self.assertEqual(data["tiers"]["active"][0]["age_days"], 7)
+
+    def test_patterns_only_excludes_gotchas(self):
+        text = "## Patterns\n### Pattern A (2026-04-20, verified: 2026-04-20)\n## Gotchas\n### Gotcha A (2026-04-20, verified: 2026-04-20)\n"
+        data = self.make_report(text, include_gotchas=False)
+        self.assertEqual(data["summary"]["total"], 1)
+        self.assertEqual(data["tiers"]["active"][0]["name"], "Pattern A")
+
+    def test_json_schema_round_trip(self):
+        data = self.make_report("## Patterns\n### Json One (2026-04-20, verified: 2026-04-20)\n")
+        loaded = json.loads(json.dumps(data))
+        self.assertEqual(set(["generated_at", "today", "tiers", "summary"]).issubset(loaded), True)
+        self.assertEqual(set(loaded["tiers"]["active"][0]), set(["name", "verified", "created", "age_days", "tier", "line_no"]))
+
+    def test_promotion_candidate_detection(self):
+        text = "## Patterns\n### Promote Me (2026-04-01, verified: 2026-04-01)\n"
+        data = self.make_report(text, active_text="We should revisit promote me today.")
+        self.assertEqual(data["promotion_candidates"][0]["name"], "Promote Me")
+
+    def test_empty_knowledge_total_zero(self):
+        data = self.make_report("")
+        self.assertEqual(data["summary"]["total"], 0)
+
+
+if __name__ == "__main__":
+    unittest.main()

exec
powershell.exe -Command 'py -3 .claude/scripts/test_knowledge_decay_report.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\codex\task-V1-knowledge-decay-report
2026-04-25T07:38:06.251869Z ERROR codex_core::tools::router: error={"output":"No installed Python found!\r\n","metadata":{"exit_code":1,"duration_seconds":0.3}}
 exited 1 in 254ms:
No installed Python found!

diff --git a/.claude/scripts/knowledge-decay-report.py b/.claude/scripts/knowledge-decay-report.py
new file mode 100644
index 0000000000000000000000000000000000000000..145c275c929084d0d84834375b0241c46b4effdc
--- /dev/null
+++ b/.claude/scripts/knowledge-decay-report.py
@@ -0,0 +1,283 @@
+#!/usr/bin/env python3
+"""Audit knowledge.md entries by verification age tier."""
+import argparse
+import json
+import logging
+import re
+import sys
+from datetime import date
+from pathlib import Path
+
+
+TIERS = ("active", "warm", "cold", "archive", "unparsed")
+DEFAULT_THRESHOLDS = (14, 30, 90)
+ENTRY_RE = re.compile(r"^###\s+(.+?)\s+\((\d{4}-\d{2}-\d{2}),\s*verified:\s*(\d{4}-\d{2}-\d{2})\)\s*$")
+HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
+
+
+class JsonFormatter(logging.Formatter):
+    def format(self, record):
+        payload = {
+            "level": record.levelname,
+            "message": record.getMessage(),
+            "logger": record.name,
+        }
+        if record.exc_info:
+            payload["exc_info"] = self.formatException(record.exc_info)
+        for key, value in getattr(record, "context", {}).items():
+            payload[key] = value
+        return json.dumps(payload, sort_keys=True)
+
+
+logger = logging.getLogger("knowledge_decay_report")
+
+
+def configure_logging(verbose):
+    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
+    handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(JsonFormatter())
+    root = logging.getLogger()
+    root.handlers.clear()
+    root.addHandler(handler)
+    root.setLevel(logging.DEBUG if verbose else logging.WARNING)
+    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})
+
+
+def parse_args(argv):
+    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
+    parser = argparse.ArgumentParser(description="Audit .claude/memory/knowledge.md verification decay tiers.")
+    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
+    parser.add_argument("--knowledge-path", default=".claude/memory/knowledge.md", help="Path to knowledge.md.")
+    parser.add_argument("--today", help="Override today's date as YYYY-MM-DD.")
+    group = parser.add_mutually_exclusive_group()
+    group.add_argument("--include-gotchas", action="store_true", help="Include Gotchas section entries (default).")
+    group.add_argument("--patterns-only", action="store_true", help="Only include Patterns section entries.")
+    parser.add_argument("--threshold-days", default="14,30,90", help="Comma-separated active,warm,cold day cutoffs.")
+    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG structured logs on stderr.")
+    args = parser.parse_args(argv)
+    logger.debug("exit", extra={"context": {"function": "parse_args", "json": args.json}})
+    return args
+
+
+def parse_thresholds(value):
+    logger.debug("entry", extra={"context": {"function": "parse_thresholds", "value": value}})
+    try:
+        parts = tuple(int(part.strip()) for part in value.split(","))
+        if len(parts) != 3 or parts[0] < 0 or not (parts[0] < parts[1] < parts[2]):
+            raise ValueError("thresholds must be three increasing non-negative integers")
+        logger.debug("exit", extra={"context": {"function": "parse_thresholds", "thresholds": parts}})
+        return parts
+    except ValueError:
+        logger.exception("invalid_thresholds", extra={"context": {"function": "parse_thresholds", "value": value}})
+        raise
+
+
+def parse_today(value):
+    logger.debug("entry", extra={"context": {"function": "parse_today", "provided": bool(value)}})
+    try:
+        result = date.fromisoformat(value) if value else date.today()
+        logger.debug("exit", extra={"context": {"function": "parse_today", "today": result.isoformat()}})
+        return result
+    except ValueError:
+        logger.exception("invalid_today", extra={"context": {"function": "parse_today", "value": value}})
+        raise
+
+
+def classify_age(age_days, thresholds):
+    logger.debug("entry", extra={"context": {"function": "classify_age", "age_days": age_days}})
+    active, warm, cold = thresholds
+    if age_days <= active:
+        tier = "active"
+    elif age_days <= warm:
+        tier = "warm"
+    elif age_days <= cold:
+        tier = "cold"
+    else:
+        tier = "archive"
+    logger.debug("exit", extra={"context": {"function": "classify_age", "tier": tier}})
+    return tier
+
+
+def blank_report(today_value):
+    logger.debug("entry", extra={"context": {"function": "blank_report", "today": today_value.isoformat()}})
+    result = {
+        "generated_at": date.today().isoformat(),
+        "today": today_value.isoformat(),
+        "tiers": {tier: [] for tier in TIERS},
+        "summary": {tier: 0 for tier in TIERS},
+        "promotion_candidates": [],
+    }
+    result["summary"]["total"] = 0
+    logger.debug("exit", extra={"context": {"function": "blank_report"}})
+    return result
+
+
+def extract_name(line):
+    logger.debug("entry", extra={"context": {"function": "extract_name"}})
+    text = line[4:].strip()
+    name = text.split(" (", 1)[0].strip() or text[:80]
+    logger.debug("exit", extra={"context": {"function": "extract_name", "name": name}})
+    return name
+
+
+def parse_entry_line(line, line_no, today_value, thresholds):
+    logger.debug("entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+    match = ENTRY_RE.match(line)
+    if not match:
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.warning("unparsed_entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+    try:
+        name, created_text, verified_text = match.groups()
+        created = date.fromisoformat(created_text)
+        verified = date.fromisoformat(verified_text)
+        age_days = (today_value - verified).days
+        tier = classify_age(age_days, thresholds)
+        entry = {
+            "name": name,
+            "verified": verified.isoformat(),
+            "created": created.isoformat(),
+            "age_days": age_days,
+            "tier": tier,
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": tier}})
+        return entry
+    except ValueError:
+        logger.exception("malformed_entry_dates", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+
+
+def iter_relevant_lines(text, include_gotchas):
+    logger.debug("entry", extra={"context": {"function": "iter_relevant_lines", "include_gotchas": include_gotchas}})
+    section = None
+    for line_no, line in enumerate(text.splitlines(), start=1):
+        heading = HEADING_RE.match(line)
+        if heading:
+            title = heading.group(1).strip().lower()
+            section = title if title in {"patterns", "gotchas"} else None
+            continue
+        if line.startswith("### ") and section == "patterns":
+            yield line_no, line
+        elif line.startswith("### ") and section == "gotchas" and include_gotchas:
+            yield line_no, line
+    logger.debug("exit", extra={"context": {"function": "iter_relevant_lines"}})
+
+
+def detect_promotion_candidates(report, knowledge_path):
+    logger.debug("entry", extra={"context": {"function": "detect_promotion_candidates", "path": str(knowledge_path)}})
+    try:
+        active_path = knowledge_path.parent / "activeContext.md"
+        if not active_path.exists():
+            logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": 0}})
+            return []
+        active_text = active_path.read_text(encoding="utf-8", errors="replace").lower()
+        candidates = []
+        for tier in ("warm", "cold", "archive"):
+            for entry in report["tiers"][tier]:
+                if entry["name"].lower() in active_text:
+                    candidates.append(entry)
+        logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": len(candidates)}})
+        return candidates
+    except OSError:
+        logger.exception("active_context_read_failed", extra={"context": {"function": "detect_promotion_candidates"}})
+        return []
+
+
+def make_report(knowledge_path, today_value, include_gotchas, thresholds):
+    logger.debug("entry", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+    report = blank_report(today_value)
+    try:
+        text = Path(knowledge_path).read_text(encoding="utf-8", errors="replace")
+    except OSError:
+        logger.exception("knowledge_read_failed", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+        raise
+    for line_no, line in iter_relevant_lines(text, include_gotchas):
+        entry = parse_entry_line(line, line_no, today_value, thresholds)
+        report["tiers"][entry["tier"]].append(entry)
+    for tier in TIERS:
+        report["summary"][tier] = len(report["tiers"][tier])
+    report["summary"]["total"] = sum(report["summary"][tier] for tier in TIERS)
+    report["promotion_candidates"] = detect_promotion_candidates(report, Path(knowledge_path))
+    logger.debug("exit", extra={"context": {"function": "make_report", "total": report["summary"]["total"]}})
+    return report
+
+
+def format_entry(entry):
+    logger.debug("entry", extra={"context": {"function": "format_entry", "tier": entry["tier"]}})
+    if entry["tier"] == "unparsed":
+        text = f"* {entry['name']} (line={entry['line_no']})"
+    else:
+        text = f"* {entry['name']} ({entry['verified']}, age={entry['age_days']}d)"
+    result = text[:80]
+    logger.debug("exit", extra={"context": {"function": "format_entry", "length": len(result)}})
+    return result
+
+
+def format_text_report(report):
+    logger.debug("entry", extra={"context": {"function": "format_text_report", "total": report["summary"]["total"]}})
+    lines = [
+        "Tier    | Count | Entries (truncated to first 80 chars)",
+        "--------+-------+-----------------------------------------",
+    ]
+    for tier in TIERS:
+        entries = report["tiers"][tier]
+        first = format_entry(entries[0]) if entries else ""
+        lines.append(f"{tier:<8}| {len(entries):^5} | {first}")
+        for entry in entries[1:]:
+            lines.append(f"{'':8}  {'':5}   {format_entry(entry)}")
+    lines.append(f"Total   | {report['summary']['total']:^5} |")
+    lines.extend(["", "## Age histogram"])
+    for tier in TIERS:
+        lines.append(f"{tier}: {report['summary'][tier]}")
+    candidates = report["promotion_candidates"]
+    lines.extend(["", f"## Promotion candidates ({len(candidates)}):"])
+    for entry in candidates:
+        lines.append(format_entry(entry))
+    result = "\n".join(lines)
+    logger.debug("exit", extra={"context": {"function": "format_text_report", "length": len(result)}})
+    return result
+
+
+def main(argv=None):
+    if argv is None:
+        argv = sys.argv[1:]
+    args = parse_args(argv)
+    configure_logging(args.verbose)
+    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
+    try:
+        today_value = parse_today(args.today)
+        thresholds = parse_thresholds(args.threshold_days)
+        data = make_report(Path(args.knowledge_path), today_value, not args.patterns_only, thresholds)
+        if args.json:
+            print(json.dumps(data, indent=2, sort_keys=True))
+        else:
+            print(format_text_report(data))
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 0}})
+        return 0
+    except (OSError, ValueError) as exc:
+        logger.exception("fatal_error", extra={"context": {"function": "main"}})
+        print(f"error: {exc}", file=sys.stderr)
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 2}})
+        return 2
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/.claude/scripts/test_knowledge_decay_report.py b/.claude/scripts/test_knowledge_decay_report.py
new file mode 100644
index 0000000000000000000000000000000000000000..f5e06729bb3a550ff345b4cf8b883c350128a62a
--- /dev/null
+++ b/.claude/scripts/test_knowledge_decay_report.py
@@ -0,0 +1,83 @@
+import importlib.util
+import json
+import tempfile
+import unittest
+from datetime import date
+from pathlib import Path
+
+
+SCRIPT_PATH = Path(__file__).with_name("knowledge-decay-report.py")
+SPEC = importlib.util.spec_from_file_location("knowledge_decay_report", SCRIPT_PATH)
+report = importlib.util.module_from_spec(SPEC)
+SPEC.loader.exec_module(report)
+
+
+def write_memory(root, knowledge_text, active_text=None):
+    memory = Path(root) / ".claude" / "memory"
+    memory.mkdir(parents=True)
+    knowledge_path = memory / "knowledge.md"
+    knowledge_path.write_text(knowledge_text, encoding="utf-8")
+    if active_text is not None:
+        (memory / "activeContext.md").write_text(active_text, encoding="utf-8")
+    return knowledge_path
+
+
+class KnowledgeDecayReportTests(unittest.TestCase):
+    def make_report(self, text, today="2026-04-25", active_text=None, include_gotchas=True):
+        with tempfile.TemporaryDirectory() as root:
+            knowledge_path = write_memory(root, text, active_text)
+            return report.make_report(
+                knowledge_path,
+                date.fromisoformat(today),
+                include_gotchas,
+                (14, 30, 90),
+            )
+
+    def test_fresh_entry_active(self):
+        data = self.make_report("## Patterns\n### Fresh (2026-04-20, verified: 2026-04-20)\n")
+        self.assertEqual(data["tiers"]["active"][0]["tier"], "active")
+
+    def test_twenty_days_warm(self):
+        data = self.make_report("## Patterns\n### Warm One (2026-04-05, verified: 2026-04-05)\n")
+        self.assertEqual(data["summary"]["warm"], 1)
+
+    def test_sixty_days_cold(self):
+        data = self.make_report("## Patterns\n### Cold One (2026-02-24, verified: 2026-02-24)\n")
+        self.assertEqual(data["tiers"]["cold"][0]["age_days"], 60)
+
+    def test_hundred_twenty_days_archive(self):
+        data = self.make_report("## Patterns\n### Old One (2025-12-26, verified: 2025-12-26)\n")
+        self.assertEqual(data["summary"]["archive"], 1)
+
+    def test_missing_verified_unparsed(self):
+        data = self.make_report("## Patterns\n### Missing Verified (2026-01-01)\n")
+        self.assertEqual(data["tiers"]["unparsed"][0]["tier"], "unparsed")
+
+    def test_today_override_applied(self):
+        data = self.make_report("## Patterns\n### Override (2026-04-01, verified: 2026-04-01)\n", today="2026-04-08")
+        self.assertEqual(data["tiers"]["active"][0]["age_days"], 7)
+
+    def test_patterns_only_excludes_gotchas(self):
+        text = "## Patterns\n### Pattern A (2026-04-20, verified: 2026-04-20)\n## Gotchas\n### Gotcha A (2026-04-20, verified: 2026-04-20)\n"
+        data = self.make_report(text, include_gotchas=False)
+        self.assertEqual(data["summary"]["total"], 1)
+        self.assertEqual(data["tiers"]["active"][0]["name"], "Pattern A")
+
+    def test_json_schema_round_trip(self):
+        data = self.make_report("## Patterns\n### Json One (2026-04-20, verified: 2026-04-20)\n")
+        loaded = json.loads(json.dumps(data))
+        self.assertEqual(set(["generated_at", "today", "tiers", "summary"]).issubset(loaded), True)
+        self.assertEqual(set(loaded["tiers"]["active"][0]), set(["name", "verified", "created", "age_days", "tier", "line_no"]))
+
+    def test_promotion_candidate_detection(self):
+        text = "## Patterns\n### Promote Me (2026-04-01, verified: 2026-04-01)\n"
+        data = self.make_report(text, active_text="We should revisit promote me today.")
+        self.assertEqual(data["promotion_candidates"][0]["name"], "Promote Me")
+
+    def test_empty_knowledge_total_zero(self):
+        data = self.make_report("")
+        self.assertEqual(data["summary"]["total"], 0)
+
+
+if __name__ == "__main__":
+    unittest.main()

**Figuring out Python commands**

It seems like the alias for Python isn't picking the local version. I could try using an alias, but that's not persistent with each command. If I test the command "py -3 ...", it uses the installed alias but fails. I can't edit anything outside of what's allowed. I need to run Python and also the remaining "py -3" commands to see where they fail. Checking if Python exists is a good first step.
codex
`py -3` is unavailable in this sandbox, so I’ll run the same commands with `python` for code validation too.
exec
powershell.exe -Command 'python .claude/scripts/test_knowledge_decay_report.py; $testExit=$LASTEXITCODE; python .claude/scripts/knowledge-decay-report.py --help; $helpExit=$LASTEXITCODE; python .claude/scripts/knowledge-decay-report.py; $runExit=$LASTEXITCODE; Write-Output "PYTHON_EQUIV_EXITS test=$testExit help=$helpExit run=$runExit"; exit (($testExit -ne 0) -or ($helpExit -ne 0) -or ($runExit -ne 0))' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\codex\task-V1-knowledge-decay-report
2026-04-25T07:38:21.569086Z ERROR codex_core::tools::router: error={"output":"PYTHON_EQUIV_EXITS test= help= run=\r\npython : Имя \"python\" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте пр\r\nавильность написания имени, а также наличие и правильность пути, после чего повторите попытку.\r\nстрока:2 знак:1\r\n+ python .claude/scripts/test_knowledge_decay_report.py; $testExit=$LAS ...\r\n+ ~~~~~~\r\n    + CategoryInfo          : ObjectNotFound: (python:String) [], CommandNotFoundException\r\n    + FullyQualifiedErrorId : CommandNotFoundException\r\n \r\npython : Имя \"python\" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте пр\r\nавильность написания имени, а также наличие и правильность пути, после чего повторите попытку.\r\nстрока:2 знак:81\r\n+ ... st_knowledge_decay_report.py; $testExit=$LASTEXITCODE; python .claude ...\r\n+                                                            ~~~~~~\r\n    + CategoryInfo          : ObjectNotFound: (python:String) [], CommandNotFoundException\r\n    + FullyQualifiedErrorId : CommandNotFoundException\r\n \r\npython : Имя \"python\" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте пр\r\nавильность написания имени, а также наличие и правильность пути, после чего повторите попытку.\r\nстрока:2 знак:163\r\n+ ... ledge-decay-report.py --help; $helpExit=$LASTEXITCODE; python .claude ...\r\n+                                                            ~~~~~~\r\n    + CategoryInfo          : ObjectNotFound: (python:String) [], CommandNotFoundException\r\n    + FullyQualifiedErrorId : CommandNotFoundException\r\n \r\n","metadata":{"exit_code":1,"duration_seconds":1.3}}
 exited 1 in 1338ms:
PYTHON_EQUIV_EXITS test= help= run=
python : Имя "python" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте пр
авильность написания имени, а также наличие и правильность пути, после чего повторите попытку.
строка:2 знак:1
+ python .claude/scripts/test_knowledge_decay_report.py; $testExit=$LAS ...
+ ~~~~~~
    + CategoryInfo          : ObjectNotFound: (python:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 
python : Имя "python" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте пр
авильность написания имени, а также наличие и правильность пути, после чего повторите попытку.
строка:2 знак:81
+ ... st_knowledge_decay_report.py; $testExit=$LASTEXITCODE; python .claude ...
+                                                            ~~~~~~
    + CategoryInfo          : ObjectNotFound: (python:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 
python : Имя "python" не распознано как имя командлета, функции, файла сценария или выполняемой программы. Проверьте пр
авильность написания имени, а также наличие и правильность пути, после чего повторите попытку.
строка:2 знак:163
+ ... ledge-decay-report.py --help; $helpExit=$LASTEXITCODE; python .claude ...
+                                                            ~~~~~~
    + CategoryInfo          : ObjectNotFound: (python:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

diff --git a/.claude/scripts/knowledge-decay-report.py b/.claude/scripts/knowledge-decay-report.py
new file mode 100644
index 0000000000000000000000000000000000000000..145c275c929084d0d84834375b0241c46b4effdc
--- /dev/null
+++ b/.claude/scripts/knowledge-decay-report.py
@@ -0,0 +1,283 @@
+#!/usr/bin/env python3
+"""Audit knowledge.md entries by verification age tier."""
+import argparse
+import json
+import logging
+import re
+import sys
+from datetime import date
+from pathlib import Path
+
+
+TIERS = ("active", "warm", "cold", "archive", "unparsed")
+DEFAULT_THRESHOLDS = (14, 30, 90)
+ENTRY_RE = re.compile(r"^###\s+(.+?)\s+\((\d{4}-\d{2}-\d{2}),\s*verified:\s*(\d{4}-\d{2}-\d{2})\)\s*$")
+HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
+
+
+class JsonFormatter(logging.Formatter):
+    def format(self, record):
+        payload = {
+            "level": record.levelname,
+            "message": record.getMessage(),
+            "logger": record.name,
+        }
+        if record.exc_info:
+            payload["exc_info"] = self.formatException(record.exc_info)
+        for key, value in getattr(record, "context", {}).items():
+            payload[key] = value
+        return json.dumps(payload, sort_keys=True)
+
+
+logger = logging.getLogger("knowledge_decay_report")
+
+
+def configure_logging(verbose):
+    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
+    handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(JsonFormatter())
+    root = logging.getLogger()
+    root.handlers.clear()
+    root.addHandler(handler)
+    root.setLevel(logging.DEBUG if verbose else logging.WARNING)
+    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})
+
+
+def parse_args(argv):
+    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
+    parser = argparse.ArgumentParser(description="Audit .claude/memory/knowledge.md verification decay tiers.")
+    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
+    parser.add_argument("--knowledge-path", default=".claude/memory/knowledge.md", help="Path to knowledge.md.")
+    parser.add_argument("--today", help="Override today's date as YYYY-MM-DD.")
+    group = parser.add_mutually_exclusive_group()
+    group.add_argument("--include-gotchas", action="store_true", help="Include Gotchas section entries (default).")
+    group.add_argument("--patterns-only", action="store_true", help="Only include Patterns section entries.")
+    parser.add_argument("--threshold-days", default="14,30,90", help="Comma-separated active,warm,cold day cutoffs.")
+    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG structured logs on stderr.")
+    args = parser.parse_args(argv)
+    logger.debug("exit", extra={"context": {"function": "parse_args", "json": args.json}})
+    return args
+
+
+def parse_thresholds(value):
+    logger.debug("entry", extra={"context": {"function": "parse_thresholds", "value": value}})
+    try:
+        parts = tuple(int(part.strip()) for part in value.split(","))
+        if len(parts) != 3 or parts[0] < 0 or not (parts[0] < parts[1] < parts[2]):
+            raise ValueError("thresholds must be three increasing non-negative integers")
+        logger.debug("exit", extra={"context": {"function": "parse_thresholds", "thresholds": parts}})
+        return parts
+    except ValueError:
+        logger.exception("invalid_thresholds", extra={"context": {"function": "parse_thresholds", "value": value}})
+        raise
+
+
+def parse_today(value):
+    logger.debug("entry", extra={"context": {"function": "parse_today", "provided": bool(value)}})
+    try:
+        result = date.fromisoformat(value) if value else date.today()
+        logger.debug("exit", extra={"context": {"function": "parse_today", "today": result.isoformat()}})
+        return result
+    except ValueError:
+        logger.exception("invalid_today", extra={"context": {"function": "parse_today", "value": value}})
+        raise
+
+
+def classify_age(age_days, thresholds):
+    logger.debug("entry", extra={"context": {"function": "classify_age", "age_days": age_days}})
+    active, warm, cold = thresholds
+    if age_days <= active:
+        tier = "active"
+    elif age_days <= warm:
+        tier = "warm"
+    elif age_days <= cold:
+        tier = "cold"
+    else:
+        tier = "archive"
+    logger.debug("exit", extra={"context": {"function": "classify_age", "tier": tier}})
+    return tier
+
+
+def blank_report(today_value):
+    logger.debug("entry", extra={"context": {"function": "blank_report", "today": today_value.isoformat()}})
+    result = {
+        "generated_at": date.today().isoformat(),
+        "today": today_value.isoformat(),
+        "tiers": {tier: [] for tier in TIERS},
+        "summary": {tier: 0 for tier in TIERS},
+        "promotion_candidates": [],
+    }
+    result["summary"]["total"] = 0
+    logger.debug("exit", extra={"context": {"function": "blank_report"}})
+    return result
+
+
+def extract_name(line):
+    logger.debug("entry", extra={"context": {"function": "extract_name"}})
+    text = line[4:].strip()
+    name = text.split(" (", 1)[0].strip() or text[:80]
+    logger.debug("exit", extra={"context": {"function": "extract_name", "name": name}})
+    return name
+
+
+def parse_entry_line(line, line_no, today_value, thresholds):
+    logger.debug("entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+    match = ENTRY_RE.match(line)
+    if not match:
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.warning("unparsed_entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+    try:
+        name, created_text, verified_text = match.groups()
+        created = date.fromisoformat(created_text)
+        verified = date.fromisoformat(verified_text)
+        age_days = (today_value - verified).days
+        tier = classify_age(age_days, thresholds)
+        entry = {
+            "name": name,
+            "verified": verified.isoformat(),
+            "created": created.isoformat(),
+            "age_days": age_days,
+            "tier": tier,
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": tier}})
+        return entry
+    except ValueError:
+        logger.exception("malformed_entry_dates", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+
+
+def iter_relevant_lines(text, include_gotchas):
+    logger.debug("entry", extra={"context": {"function": "iter_relevant_lines", "include_gotchas": include_gotchas}})
+    section = None
+    for line_no, line in enumerate(text.splitlines(), start=1):
+        heading = HEADING_RE.match(line)
+        if heading:
+            title = heading.group(1).strip().lower()
+            section = title if title in {"patterns", "gotchas"} else None
+            continue
+        if line.startswith("### ") and section == "patterns":
+            yield line_no, line
+        elif line.startswith("### ") and section == "gotchas" and include_gotchas:
+            yield line_no, line
+    logger.debug("exit", extra={"context": {"function": "iter_relevant_lines"}})
+
+
+def detect_promotion_candidates(report, knowledge_path):
+    logger.debug("entry", extra={"context": {"function": "detect_promotion_candidates", "path": str(knowledge_path)}})
+    try:
+        active_path = knowledge_path.parent / "activeContext.md"
+        if not active_path.exists():
+            logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": 0}})
+            return []
+        active_text = active_path.read_text(encoding="utf-8", errors="replace").lower()
+        candidates = []
+        for tier in ("warm", "cold", "archive"):
+            for entry in report["tiers"][tier]:
+                if entry["name"].lower() in active_text:
+                    candidates.append(entry)
+        logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": len(candidates)}})
+        return candidates
+    except OSError:
+        logger.exception("active_context_read_failed", extra={"context": {"function": "detect_promotion_candidates"}})
+        return []
+
+
+def make_report(knowledge_path, today_value, include_gotchas, thresholds):
+    logger.debug("entry", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+    report = blank_report(today_value)
+    try:
+        text = Path(knowledge_path).read_text(encoding="utf-8", errors="replace")
+    except OSError:
+        logger.exception("knowledge_read_failed", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+        raise
+    for line_no, line in iter_relevant_lines(text, include_gotchas):
+        entry = parse_entry_line(line, line_no, today_value, thresholds)
+        report["tiers"][entry["tier"]].append(entry)
+    for tier in TIERS:
+        report["summary"][tier] = len(report["tiers"][tier])
+    report["summary"]["total"] = sum(report["summary"][tier] for tier in TIERS)
+    report["promotion_candidates"] = detect_promotion_candidates(report, Path(knowledge_path))
+    logger.debug("exit", extra={"context": {"function": "make_report", "total": report["summary"]["total"]}})
+    return report
+
+
+def format_entry(entry):
+    logger.debug("entry", extra={"context": {"function": "format_entry", "tier": entry["tier"]}})
+    if entry["tier"] == "unparsed":
+        text = f"* {entry['name']} (line={entry['line_no']})"
+    else:
+        text = f"* {entry['name']} ({entry['verified']}, age={entry['age_days']}d)"
+    result = text[:80]
+    logger.debug("exit", extra={"context": {"function": "format_entry", "length": len(result)}})
+    return result
+
+
+def format_text_report(report):
+    logger.debug("entry", extra={"context": {"function": "format_text_report", "total": report["summary"]["total"]}})
+    lines = [
+        "Tier    | Count | Entries (truncated to first 80 chars)",
+        "--------+-------+-----------------------------------------",
+    ]
+    for tier in TIERS:
+        entries = report["tiers"][tier]
+        first = format_entry(entries[0]) if entries else ""
+        lines.append(f"{tier:<8}| {len(entries):^5} | {first}")
+        for entry in entries[1:]:
+            lines.append(f"{'':8}  {'':5}   {format_entry(entry)}")
+    lines.append(f"Total   | {report['summary']['total']:^5} |")
+    lines.extend(["", "## Age histogram"])
+    for tier in TIERS:
+        lines.append(f"{tier}: {report['summary'][tier]}")
+    candidates = report["promotion_candidates"]
+    lines.extend(["", f"## Promotion candidates ({len(candidates)}):"])
+    for entry in candidates:
+        lines.append(format_entry(entry))
+    result = "\n".join(lines)
+    logger.debug("exit", extra={"context": {"function": "format_text_report", "length": len(result)}})
+    return result
+
+
+def main(argv=None):
+    if argv is None:
+        argv = sys.argv[1:]
+    args = parse_args(argv)
+    configure_logging(args.verbose)
+    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
+    try:
+        today_value = parse_today(args.today)
+        thresholds = parse_thresholds(args.threshold_days)
+        data = make_report(Path(args.knowledge_path), today_value, not args.patterns_only, thresholds)
+        if args.json:
+            print(json.dumps(data, indent=2, sort_keys=True))
+        else:
+            print(format_text_report(data))
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 0}})
+        return 0
+    except (OSError, ValueError) as exc:
+        logger.exception("fatal_error", extra={"context": {"function": "main"}})
+        print(f"error: {exc}", file=sys.stderr)
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 2}})
+        return 2
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/.claude/scripts/test_knowledge_decay_report.py b/.claude/scripts/test_knowledge_decay_report.py
new file mode 100644
index 0000000000000000000000000000000000000000..f5e06729bb3a550ff345b4cf8b883c350128a62a
--- /dev/null
+++ b/.claude/scripts/test_knowledge_decay_report.py
@@ -0,0 +1,83 @@
+import importlib.util
+import json
+import tempfile
+import unittest
+from datetime import date
+from pathlib import Path
+
+
+SCRIPT_PATH = Path(__file__).with_name("knowledge-decay-report.py")
+SPEC = importlib.util.spec_from_file_location("knowledge_decay_report", SCRIPT_PATH)
+report = importlib.util.module_from_spec(SPEC)
+SPEC.loader.exec_module(report)
+
+
+def write_memory(root, knowledge_text, active_text=None):
+    memory = Path(root) / ".claude" / "memory"
+    memory.mkdir(parents=True)
+    knowledge_path = memory / "knowledge.md"
+    knowledge_path.write_text(knowledge_text, encoding="utf-8")
+    if active_text is not None:
+        (memory / "activeContext.md").write_text(active_text, encoding="utf-8")
+    return knowledge_path
+
+
+class KnowledgeDecayReportTests(unittest.TestCase):
+    def make_report(self, text, today="2026-04-25", active_text=None, include_gotchas=True):
+        with tempfile.TemporaryDirectory() as root:
+            knowledge_path = write_memory(root, text, active_text)
+            return report.make_report(
+                knowledge_path,
+                date.fromisoformat(today),
+                include_gotchas,
+                (14, 30, 90),
+            )
+
+    def test_fresh_entry_active(self):
+        data = self.make_report("## Patterns\n### Fresh (2026-04-20, verified: 2026-04-20)\n")
+        self.assertEqual(data["tiers"]["active"][0]["tier"], "active")
+
+    def test_twenty_days_warm(self):
+        data = self.make_report("## Patterns\n### Warm One (2026-04-05, verified: 2026-04-05)\n")
+        self.assertEqual(data["summary"]["warm"], 1)
+
+    def test_sixty_days_cold(self):
+        data = self.make_report("## Patterns\n### Cold One (2026-02-24, verified: 2026-02-24)\n")
+        self.assertEqual(data["tiers"]["cold"][0]["age_days"], 60)
+
+    def test_hundred_twenty_days_archive(self):
+        data = self.make_report("## Patterns\n### Old One (2025-12-26, verified: 2025-12-26)\n")
+        self.assertEqual(data["summary"]["archive"], 1)
+
+    def test_missing_verified_unparsed(self):
+        data = self.make_report("## Patterns\n### Missing Verified (2026-01-01)\n")
+        self.assertEqual(data["tiers"]["unparsed"][0]["tier"], "unparsed")
+
+    def test_today_override_applied(self):
+        data = self.make_report("## Patterns\n### Override (2026-04-01, verified: 2026-04-01)\n", today="2026-04-08")
+        self.assertEqual(data["tiers"]["active"][0]["age_days"], 7)
+
+    def test_patterns_only_excludes_gotchas(self):
+        text = "## Patterns\n### Pattern A (2026-04-20, verified: 2026-04-20)\n## Gotchas\n### Gotcha A (2026-04-20, verified: 2026-04-20)\n"
+        data = self.make_report(text, include_gotchas=False)
+        self.assertEqual(data["summary"]["total"], 1)
+        self.assertEqual(data["tiers"]["active"][0]["name"], "Pattern A")
+
+    def test_json_schema_round_trip(self):
+        data = self.make_report("## Patterns\n### Json One (2026-04-20, verified: 2026-04-20)\n")
+        loaded = json.loads(json.dumps(data))
+        self.assertEqual(set(["generated_at", "today", "tiers", "summary"]).issubset(loaded), True)
+        self.assertEqual(set(loaded["tiers"]["active"][0]), set(["name", "verified", "created", "age_days", "tier", "line_no"]))
+
+    def test_promotion_candidate_detection(self):
+        text = "## Patterns\n### Promote Me (2026-04-01, verified: 2026-04-01)\n"
+        data = self.make_report(text, active_text="We should revisit promote me today.")
+        self.assertEqual(data["promotion_candidates"][0]["name"], "Promote Me")
+
+    def test_empty_knowledge_total_zero(self):
+        data = self.make_report("")
+        self.assertEqual(data["summary"]["total"], 0)
+
+
+if __name__ == "__main__":
+    unittest.main()

**Finding Python in PATH**

I’m trying to figure out if Python is in my PATH. It looks like it isn’t, but maybe it's in a virtual environment (.venv)? I think I should look for it. I could use a command like "where" to check its location. This should help me confirm if Python is set up correctly, allowing me to proceed smoothly with whatever task I'm working on. Let's see what I can find!
codex
Neither launcher is on PATH. I’ll locate any local Python executable before continuing validation.
exec
powershell.exe -Command '$candidates = @(); $env:PATH.Split('"';') | ForEach-Object { if ("'$_ -and (Test-Path $_)) { Get-ChildItem -Path $_ -Filter '"'python*.exe' -ErrorAction SilentlyContinue | ForEach-Object { "'$candidates += $_.FullName } } }; Get-ChildItem -Path . -Recurse -Filter '"'python*.exe' -ErrorAction SilentlyContinue | Select-Object -First 10 -ExpandProperty FullName; "'$candidates | Select-Object -Unique -First 20' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\codex\task-V1-knowledge-decay-report
 succeeded in 484ms:
Test-Path : Access is denied
строка:2 знак:73
+ ... :PATH.Split(';') | ForEach-Object { if ($_ -and (Test-Path $_)) { Get ...
+                                                      ~~~~~~~~~~~~
    + CategoryInfo          : PermissionDenied: (C:\Users\Lenovo...ndows-msvc\path:String) [Test-Path], UnauthorizedAc 
   cessException
    + FullyQualifiedErrorId : ItemExistsUnauthorizedAccessError,Microsoft.PowerShell.Commands.TestPathCommand
 
Test-Path : Access is denied
строка:2 знак:73
+ ... :PATH.Split(';') | ForEach-Object { if ($_ -and (Test-Path $_)) { Get ...
+                                                      ~~~~~~~~~~~~
    + CategoryInfo          : PermissionDenied: (C:\Users\Lenovo...thon312\Scripts:String) [Test-Path], UnauthorizedAc 
   cessException
    + FullyQualifiedErrorId : ItemExistsUnauthorizedAccessError,Microsoft.PowerShell.Commands.TestPathCommand
 
Test-Path : Access is denied
строка:2 знак:73
+ ... :PATH.Split(';') | ForEach-Object { if ($_ -and (Test-Path $_)) { Get ...
+                                                      ~~~~~~~~~~~~
    + CategoryInfo          : PermissionDenied: (C:\Users\Lenovo...ython\Python312:String) [Test-Path], UnauthorizedAc 
   cessException
    + FullyQualifiedErrorId : ItemExistsUnauthorizedAccessError,Microsoft.PowerShell.Commands.TestPathCommand
 
Test-Path : Access is denied
строка:2 знак:73
+ ... :PATH.Split(';') | ForEach-Object { if ($_ -and (Test-Path $_)) { Get ...
+                                                      ~~~~~~~~~~~~
    + CategoryInfo          : PermissionDenied: (C:\Users\Lenovo...ft\WinGet\Links:String) [Test-Path], UnauthorizedAc 
   cessException
    + FullyQualifiedErrorId : ItemExistsUnauthorizedAccessError,Microsoft.PowerShell.Commands.TestPathCommand
 
Test-Path : Access is denied
строка:2 знак:73
+ ... :PATH.Split(';') | ForEach-Object { if ($_ -and (Test-Path $_)) { Get ...
+                                                      ~~~~~~~~~~~~
    + CategoryInfo          : PermissionDenied: (C:\Users\Lenovo...-full_build\bin:String) [Test-Path], UnauthorizedAc 
   cessException
    + FullyQualifiedErrorId : ItemExistsUnauthorizedAccessError,Microsoft.PowerShell.Commands.TestPathCommand
 

diff --git a/.claude/scripts/knowledge-decay-report.py b/.claude/scripts/knowledge-decay-report.py
new file mode 100644
index 0000000000000000000000000000000000000000..145c275c929084d0d84834375b0241c46b4effdc
--- /dev/null
+++ b/.claude/scripts/knowledge-decay-report.py
@@ -0,0 +1,283 @@
+#!/usr/bin/env python3
+"""Audit knowledge.md entries by verification age tier."""
+import argparse
+import json
+import logging
+import re
+import sys
+from datetime import date
+from pathlib import Path
+
+
+TIERS = ("active", "warm", "cold", "archive", "unparsed")
+DEFAULT_THRESHOLDS = (14, 30, 90)
+ENTRY_RE = re.compile(r"^###\s+(.+?)\s+\((\d{4}-\d{2}-\d{2}),\s*verified:\s*(\d{4}-\d{2}-\d{2})\)\s*$")
+HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
+
+
+class JsonFormatter(logging.Formatter):
+    def format(self, record):
+        payload = {
+            "level": record.levelname,
+            "message": record.getMessage(),
+            "logger": record.name,
+        }
+        if record.exc_info:
+            payload["exc_info"] = self.formatException(record.exc_info)
+        for key, value in getattr(record, "context", {}).items():
+            payload[key] = value
+        return json.dumps(payload, sort_keys=True)
+
+
+logger = logging.getLogger("knowledge_decay_report")
+
+
+def configure_logging(verbose):
+    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
+    handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(JsonFormatter())
+    root = logging.getLogger()
+    root.handlers.clear()
+    root.addHandler(handler)
+    root.setLevel(logging.DEBUG if verbose else logging.WARNING)
+    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})
+
+
+def parse_args(argv):
+    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
+    parser = argparse.ArgumentParser(description="Audit .claude/memory/knowledge.md verification decay tiers.")
+    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
+    parser.add_argument("--knowledge-path", default=".claude/memory/knowledge.md", help="Path to knowledge.md.")
+    parser.add_argument("--today", help="Override today's date as YYYY-MM-DD.")
+    group = parser.add_mutually_exclusive_group()
+    group.add_argument("--include-gotchas", action="store_true", help="Include Gotchas section entries (default).")
+    group.add_argument("--patterns-only", action="store_true", help="Only include Patterns section entries.")
+    parser.add_argument("--threshold-days", default="14,30,90", help="Comma-separated active,warm,cold day cutoffs.")
+    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG structured logs on stderr.")
+    args = parser.parse_args(argv)
+    logger.debug("exit", extra={"context": {"function": "parse_args", "json": args.json}})
+    return args
+
+
+def parse_thresholds(value):
+    logger.debug("entry", extra={"context": {"function": "parse_thresholds", "value": value}})
+    try:
+        parts = tuple(int(part.strip()) for part in value.split(","))
+        if len(parts) != 3 or parts[0] < 0 or not (parts[0] < parts[1] < parts[2]):
+            raise ValueError("thresholds must be three increasing non-negative integers")
+        logger.debug("exit", extra={"context": {"function": "parse_thresholds", "thresholds": parts}})
+        return parts
+    except ValueError:
+        logger.exception("invalid_thresholds", extra={"context": {"function": "parse_thresholds", "value": value}})
+        raise
+
+
+def parse_today(value):
+    logger.debug("entry", extra={"context": {"function": "parse_today", "provided": bool(value)}})
+    try:
+        result = date.fromisoformat(value) if value else date.today()
+        logger.debug("exit", extra={"context": {"function": "parse_today", "today": result.isoformat()}})
+        return result
+    except ValueError:
+        logger.exception("invalid_today", extra={"context": {"function": "parse_today", "value": value}})
+        raise
+
+
+def classify_age(age_days, thresholds):
+    logger.debug("entry", extra={"context": {"function": "classify_age", "age_days": age_days}})
+    active, warm, cold = thresholds
+    if age_days <= active:
+        tier = "active"
+    elif age_days <= warm:
+        tier = "warm"
+    elif age_days <= cold:
+        tier = "cold"
+    else:
+        tier = "archive"
+    logger.debug("exit", extra={"context": {"function": "classify_age", "tier": tier}})
+    return tier
+
+
+def blank_report(today_value):
+    logger.debug("entry", extra={"context": {"function": "blank_report", "today": today_value.isoformat()}})
+    result = {
+        "generated_at": date.today().isoformat(),
+        "today": today_value.isoformat(),
+        "tiers": {tier: [] for tier in TIERS},
+        "summary": {tier: 0 for tier in TIERS},
+        "promotion_candidates": [],
+    }
+    result["summary"]["total"] = 0
+    logger.debug("exit", extra={"context": {"function": "blank_report"}})
+    return result
+
+
+def extract_name(line):
+    logger.debug("entry", extra={"context": {"function": "extract_name"}})
+    text = line[4:].strip()
+    name = text.split(" (", 1)[0].strip() or text[:80]
+    logger.debug("exit", extra={"context": {"function": "extract_name", "name": name}})
+    return name
+
+
+def parse_entry_line(line, line_no, today_value, thresholds):
+    logger.debug("entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+    match = ENTRY_RE.match(line)
+    if not match:
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.warning("unparsed_entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+    try:
+        name, created_text, verified_text = match.groups()
+        created = date.fromisoformat(created_text)
+        verified = date.fromisoformat(verified_text)
+        age_days = (today_value - verified).days
+        tier = classify_age(age_days, thresholds)
+        entry = {
+            "name": name,
+            "verified": verified.isoformat(),
+            "created": created.isoformat(),
+            "age_days": age_days,
+            "tier": tier,
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": tier}})
+        return entry
+    except ValueError:
+        logger.exception("malformed_entry_dates", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+
+
+def iter_relevant_lines(text, include_gotchas):
+    logger.debug("entry", extra={"context": {"function": "iter_relevant_lines", "include_gotchas": include_gotchas}})
+    section = None
+    for line_no, line in enumerate(text.splitlines(), start=1):
+        heading = HEADING_RE.match(line)
+        if heading:
+            title = heading.group(1).strip().lower()
+            section = title if title in {"patterns", "gotchas"} else None
+            continue
+        if line.startswith("### ") and section == "patterns":
+            yield line_no, line
+        elif line.startswith("### ") and section == "gotchas" and include_gotchas:
+            yield line_no, line
+    logger.debug("exit", extra={"context": {"function": "iter_relevant_lines"}})
+
+
+def detect_promotion_candidates(report, knowledge_path):
+    logger.debug("entry", extra={"context": {"function": "detect_promotion_candidates", "path": str(knowledge_path)}})
+    try:
+        active_path = knowledge_path.parent / "activeContext.md"
+        if not active_path.exists():
+            logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": 0}})
+            return []
+        active_text = active_path.read_text(encoding="utf-8", errors="replace").lower()
+        candidates = []
+        for tier in ("warm", "cold", "archive"):
+            for entry in report["tiers"][tier]:
+                if entry["name"].lower() in active_text:
+                    candidates.append(entry)
+        logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": len(candidates)}})
+        return candidates
+    except OSError:
+        logger.exception("active_context_read_failed", extra={"context": {"function": "detect_promotion_candidates"}})
+        return []
+
+
+def make_report(knowledge_path, today_value, include_gotchas, thresholds):
+    logger.debug("entry", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+    report = blank_report(today_value)
+    try:
+        text = Path(knowledge_path).read_text(encoding="utf-8", errors="replace")
+    except OSError:
+        logger.exception("knowledge_read_failed", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+        raise
+    for line_no, line in iter_relevant_lines(text, include_gotchas):
+        entry = parse_entry_line(line, line_no, today_value, thresholds)
+        report["tiers"][entry["tier"]].append(entry)
+    for tier in TIERS:
+        report["summary"][tier] = len(report["tiers"][tier])
+    report["summary"]["total"] = sum(report["summary"][tier] for tier in TIERS)
+    report["promotion_candidates"] = detect_promotion_candidates(report, Path(knowledge_path))
+    logger.debug("exit", extra={"context": {"function": "make_report", "total": report["summary"]["total"]}})
+    return report
+
+
+def format_entry(entry):
+    logger.debug("entry", extra={"context": {"function": "format_entry", "tier": entry["tier"]}})
+    if entry["tier"] == "unparsed":
+        text = f"* {entry['name']} (line={entry['line_no']})"
+    else:
+        text = f"* {entry['name']} ({entry['verified']}, age={entry['age_days']}d)"
+    result = text[:80]
+    logger.debug("exit", extra={"context": {"function": "format_entry", "length": len(result)}})
+    return result
+
+
+def format_text_report(report):
+    logger.debug("entry", extra={"context": {"function": "format_text_report", "total": report["summary"]["total"]}})
+    lines = [
+        "Tier    | Count | Entries (truncated to first 80 chars)",
+        "--------+-------+-----------------------------------------",
+    ]
+    for tier in TIERS:
+        entries = report["tiers"][tier]
+        first = format_entry(entries[0]) if entries else ""
+        lines.append(f"{tier:<8}| {len(entries):^5} | {first}")
+        for entry in entries[1:]:
+            lines.append(f"{'':8}  {'':5}   {format_entry(entry)}")
+    lines.append(f"Total   | {report['summary']['total']:^5} |")
+    lines.extend(["", "## Age histogram"])
+    for tier in TIERS:
+        lines.append(f"{tier}: {report['summary'][tier]}")
+    candidates = report["promotion_candidates"]
+    lines.extend(["", f"## Promotion candidates ({len(candidates)}):"])
+    for entry in candidates:
+        lines.append(format_entry(entry))
+    result = "\n".join(lines)
+    logger.debug("exit", extra={"context": {"function": "format_text_report", "length": len(result)}})
+    return result
+
+
+def main(argv=None):
+    if argv is None:
+        argv = sys.argv[1:]
+    args = parse_args(argv)
+    configure_logging(args.verbose)
+    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
+    try:
+        today_value = parse_today(args.today)
+        thresholds = parse_thresholds(args.threshold_days)
+        data = make_report(Path(args.knowledge_path), today_value, not args.patterns_only, thresholds)
+        if args.json:
+            print(json.dumps(data, indent=2, sort_keys=True))
+        else:
+            print(format_text_report(data))
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 0}})
+        return 0
+    except (OSError, ValueError) as exc:
+        logger.exception("fatal_error", extra={"context": {"function": "main"}})
+        print(f"error: {exc}", file=sys.stderr)
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 2}})
+        return 2
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/.claude/scripts/test_knowledge_decay_report.py b/.claude/scripts/test_knowledge_decay_report.py
new file mode 100644
index 0000000000000000000000000000000000000000..f5e06729bb3a550ff345b4cf8b883c350128a62a
--- /dev/null
+++ b/.claude/scripts/test_knowledge_decay_report.py
@@ -0,0 +1,83 @@
+import importlib.util
+import json
+import tempfile
+import unittest
+from datetime import date
+from pathlib import Path
+
+
+SCRIPT_PATH = Path(__file__).with_name("knowledge-decay-report.py")
+SPEC = importlib.util.spec_from_file_location("knowledge_decay_report", SCRIPT_PATH)
+report = importlib.util.module_from_spec(SPEC)
+SPEC.loader.exec_module(report)
+
+
+def write_memory(root, knowledge_text, active_text=None):
+    memory = Path(root) / ".claude" / "memory"
+    memory.mkdir(parents=True)
+    knowledge_path = memory / "knowledge.md"
+    knowledge_path.write_text(knowledge_text, encoding="utf-8")
+    if active_text is not None:
+        (memory / "activeContext.md").write_text(active_text, encoding="utf-8")
+    return knowledge_path
+
+
+class KnowledgeDecayReportTests(unittest.TestCase):
+    def make_report(self, text, today="2026-04-25", active_text=None, include_gotchas=True):
+        with tempfile.TemporaryDirectory() as root:
+            knowledge_path = write_memory(root, text, active_text)
+            return report.make_report(
+                knowledge_path,
+                date.fromisoformat(today),
+                include_gotchas,
+                (14, 30, 90),
+            )
+
+    def test_fresh_entry_active(self):
+        data = self.make_report("## Patterns\n### Fresh (2026-04-20, verified: 2026-04-20)\n")
+        self.assertEqual(data["tiers"]["active"][0]["tier"], "active")
+
+    def test_twenty_days_warm(self):
+        data = self.make_report("## Patterns\n### Warm One (2026-04-05, verified: 2026-04-05)\n")
+        self.assertEqual(data["summary"]["warm"], 1)
+
+    def test_sixty_days_cold(self):
+        data = self.make_report("## Patterns\n### Cold One (2026-02-24, verified: 2026-02-24)\n")
+        self.assertEqual(data["tiers"]["cold"][0]["age_days"], 60)
+
+    def test_hundred_twenty_days_archive(self):
+        data = self.make_report("## Patterns\n### Old One (2025-12-26, verified: 2025-12-26)\n")
+        self.assertEqual(data["summary"]["archive"], 1)
+
+    def test_missing_verified_unparsed(self):
+        data = self.make_report("## Patterns\n### Missing Verified (2026-01-01)\n")
+        self.assertEqual(data["tiers"]["unparsed"][0]["tier"], "unparsed")
+
+    def test_today_override_applied(self):
+        data = self.make_report("## Patterns\n### Override (2026-04-01, verified: 2026-04-01)\n", today="2026-04-08")
+        self.assertEqual(data["tiers"]["active"][0]["age_days"], 7)
+
+    def test_patterns_only_excludes_gotchas(self):
+        text = "## Patterns\n### Pattern A (2026-04-20, verified: 2026-04-20)\n## Gotchas\n### Gotcha A (2026-04-20, verified: 2026-04-20)\n"
+        data = self.make_report(text, include_gotchas=False)
+        self.assertEqual(data["summary"]["total"], 1)
+        self.assertEqual(data["tiers"]["active"][0]["name"], "Pattern A")
+
+    def test_json_schema_round_trip(self):
+        data = self.make_report("## Patterns\n### Json One (2026-04-20, verified: 2026-04-20)\n")
+        loaded = json.loads(json.dumps(data))
+        self.assertEqual(set(["generated_at", "today", "tiers", "summary"]).issubset(loaded), True)
+        self.assertEqual(set(loaded["tiers"]["active"][0]), set(["name", "verified", "created", "age_days", "tier", "line_no"]))
+
+    def test_promotion_candidate_detection(self):
+        text = "## Patterns\n### Promote Me (2026-04-01, verified: 2026-04-01)\n"
+        data = self.make_report(text, active_text="We should revisit promote me today.")
+        self.assertEqual(data["promotion_candidates"][0]["name"], "Promote Me")
+
+    def test_empty_knowledge_total_zero(self):
+        data = self.make_report("")
+        self.assertEqual(data["summary"]["total"], 0)
+
+
+if __name__ == "__main__":
+    unittest.main()

**Exploring access issues**

I'm wondering about the PATH including python312 but hitting an access issue due to the sandbox. Can I run it absolutely? Maybe I can execute it from a writable location? It seems like it might be blocked. I’m considering whether I need to execute from the path, even if testing isn't possible. I might try using Get-Command for python. This should help clarify what I can actually do!
exec
powershell.exe -Command 'Get-Command py -ErrorAction SilentlyContinue | Format-List *; Get-Command python -ErrorAction SilentlyContinue | Format-List *; Get-Command python3 -ErrorAction SilentlyContinue | Format-List *; $env:PATH' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\codex\task-V1-knowledge-decay-report
 succeeded in 1205ms:


HelpUri            : 
FileVersionInfo    : File:             C:\WINDOWS\py.exe
                     InternalName:     Python Launcher
                     OriginalFilename: py.exe
                     FileVersion:      3.12.10
                     FileDescription:  Python
                     Product:          Python
                     ProductVersion:   3.12.10
                     Debug:            False
                     Patched:          False
                     PreRelease:       False
                     PrivateBuild:     False
                     SpecialBuild:     False
                     Language:         Language Neutral
                     
Path               : C:\WINDOWS\py.exe
Extension          : .exe
Definition         : C:\WINDOWS\py.exe
Source             : C:\WINDOWS\py.exe
Version            : 3.12.10150.1013
Visibility         : Public
OutputType         : {System.String}
Name               : py.exe
CommandType        : Application
ModuleName         : 
Module             : 
RemotingCapability : PowerShell
Parameters         : 
ParameterSets      : 



C:\Users\Lenovo\.codex\tmp\arg0\codex-arg0YXnwDx;C:\Users\Lenovo\AppData\Roaming\npm\node_modules\@openai\codex\node_modules\@openai\codex-win32-x64\vendor\x86_64-pc-windows-msvc\path;C:\Users\Lenovo\bin;C:\Program Files\Git\mingw64\bin;C:\Program Files\Git\usr\local\bin;C:\Program Files\Git\usr\bin;C:\Program Files\Git\usr\bin;C:\Program Files\Git\mingw64\bin;C:\Program Files\Git\usr\bin;C:\Users\Lenovo\bin;C:\Users\Lenovo\AppData\Local\Programs\Microsoft VS Code;C:\WINDOWS\system32;C:\WINDOWS;C:\WINDOWS\System32\Wbem;C:\WINDOWS\System32\WindowsPowerShell\v1.0;C:\WINDOWS\System32\OpenSSH;C:\Program Files\cursor\resources\app\bin;C:\Program Files\nodejs;C:\Program Files\Git\cmd;C:\Program Files\GitHub CLI;C:\Program Files\Docker\Docker\resources\bin;C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\Scripts;C:\Users\Lenovo\AppData\Local\Programs\Python\Python312;C:\Users\Lenovo\AppData\Local\Microsoft\WindowsApps;C:\Users\Lenovo\AppData\Roaming\npm;C:\Users\Lenovo\AppData\Local\Programs\Microsoft VS Code\bin;C:\Users\Lenovo\AppData\Local\Microsoft\WinGet\Links;C:\Program Files\Docker\Docker\resources\bin;C:\Users\Lenovo\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin;C:\Users\Lenovo\.local\bin;C:\Program Files\Git\usr\bin\vendor_perl;C:\Program Files\Git\usr\bin\core_perl;C:\Users\Lenovo\.claude\plugins\cache\openai-codex\codex\1.0.2\bin

diff --git a/.claude/scripts/knowledge-decay-report.py b/.claude/scripts/knowledge-decay-report.py
new file mode 100644
index 0000000000000000000000000000000000000000..145c275c929084d0d84834375b0241c46b4effdc
--- /dev/null
+++ b/.claude/scripts/knowledge-decay-report.py
@@ -0,0 +1,283 @@
+#!/usr/bin/env python3
+"""Audit knowledge.md entries by verification age tier."""
+import argparse
+import json
+import logging
+import re
+import sys
+from datetime import date
+from pathlib import Path
+
+
+TIERS = ("active", "warm", "cold", "archive", "unparsed")
+DEFAULT_THRESHOLDS = (14, 30, 90)
+ENTRY_RE = re.compile(r"^###\s+(.+?)\s+\((\d{4}-\d{2}-\d{2}),\s*verified:\s*(\d{4}-\d{2}-\d{2})\)\s*$")
+HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
+
+
+class JsonFormatter(logging.Formatter):
+    def format(self, record):
+        payload = {
+            "level": record.levelname,
+            "message": record.getMessage(),
+            "logger": record.name,
+        }
+        if record.exc_info:
+            payload["exc_info"] = self.formatException(record.exc_info)
+        for key, value in getattr(record, "context", {}).items():
+            payload[key] = value
+        return json.dumps(payload, sort_keys=True)
+
+
+logger = logging.getLogger("knowledge_decay_report")
+
+
+def configure_logging(verbose):
+    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
+    handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(JsonFormatter())
+    root = logging.getLogger()
+    root.handlers.clear()
+    root.addHandler(handler)
+    root.setLevel(logging.DEBUG if verbose else logging.WARNING)
+    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})
+
+
+def parse_args(argv):
+    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
+    parser = argparse.ArgumentParser(description="Audit .claude/memory/knowledge.md verification decay tiers.")
+    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
+    parser.add_argument("--knowledge-path", default=".claude/memory/knowledge.md", help="Path to knowledge.md.")
+    parser.add_argument("--today", help="Override today's date as YYYY-MM-DD.")
+    group = parser.add_mutually_exclusive_group()
+    group.add_argument("--include-gotchas", action="store_true", help="Include Gotchas section entries (default).")
+    group.add_argument("--patterns-only", action="store_true", help="Only include Patterns section entries.")
+    parser.add_argument("--threshold-days", default="14,30,90", help="Comma-separated active,warm,cold day cutoffs.")
+    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG structured logs on stderr.")
+    args = parser.parse_args(argv)
+    logger.debug("exit", extra={"context": {"function": "parse_args", "json": args.json}})
+    return args
+
+
+def parse_thresholds(value):
+    logger.debug("entry", extra={"context": {"function": "parse_thresholds", "value": value}})
+    try:
+        parts = tuple(int(part.strip()) for part in value.split(","))
+        if len(parts) != 3 or parts[0] < 0 or not (parts[0] < parts[1] < parts[2]):
+            raise ValueError("thresholds must be three increasing non-negative integers")
+        logger.debug("exit", extra={"context": {"function": "parse_thresholds", "thresholds": parts}})
+        return parts
+    except ValueError:
+        logger.exception("invalid_thresholds", extra={"context": {"function": "parse_thresholds", "value": value}})
+        raise
+
+
+def parse_today(value):
+    logger.debug("entry", extra={"context": {"function": "parse_today", "provided": bool(value)}})
+    try:
+        result = date.fromisoformat(value) if value else date.today()
+        logger.debug("exit", extra={"context": {"function": "parse_today", "today": result.isoformat()}})
+        return result
+    except ValueError:
+        logger.exception("invalid_today", extra={"context": {"function": "parse_today", "value": value}})
+        raise
+
+
+def classify_age(age_days, thresholds):
+    logger.debug("entry", extra={"context": {"function": "classify_age", "age_days": age_days}})
+    active, warm, cold = thresholds
+    if age_days <= active:
+        tier = "active"
+    elif age_days <= warm:
+        tier = "warm"
+    elif age_days <= cold:
+        tier = "cold"
+    else:
+        tier = "archive"
+    logger.debug("exit", extra={"context": {"function": "classify_age", "tier": tier}})
+    return tier
+
+
+def blank_report(today_value):
+    logger.debug("entry", extra={"context": {"function": "blank_report", "today": today_value.isoformat()}})
+    result = {
+        "generated_at": date.today().isoformat(),
+        "today": today_value.isoformat(),
+        "tiers": {tier: [] for tier in TIERS},
+        "summary": {tier: 0 for tier in TIERS},
+        "promotion_candidates": [],
+    }
+    result["summary"]["total"] = 0
+    logger.debug("exit", extra={"context": {"function": "blank_report"}})
+    return result
+
+
+def extract_name(line):
+    logger.debug("entry", extra={"context": {"function": "extract_name"}})
+    text = line[4:].strip()
+    name = text.split(" (", 1)[0].strip() or text[:80]
+    logger.debug("exit", extra={"context": {"function": "extract_name", "name": name}})
+    return name
+
+
+def parse_entry_line(line, line_no, today_value, thresholds):
+    logger.debug("entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+    match = ENTRY_RE.match(line)
+    if not match:
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.warning("unparsed_entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+    try:
+        name, created_text, verified_text = match.groups()
+        created = date.fromisoformat(created_text)
+        verified = date.fromisoformat(verified_text)
+        age_days = (today_value - verified).days
+        tier = classify_age(age_days, thresholds)
+        entry = {
+            "name": name,
+            "verified": verified.isoformat(),
+            "created": created.isoformat(),
+            "age_days": age_days,
+            "tier": tier,
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": tier}})
+        return entry
+    except ValueError:
+        logger.exception("malformed_entry_dates", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+
+
+def iter_relevant_lines(text, include_gotchas):
+    logger.debug("entry", extra={"context": {"function": "iter_relevant_lines", "include_gotchas": include_gotchas}})
+    section = None
+    for line_no, line in enumerate(text.splitlines(), start=1):
+        heading = HEADING_RE.match(line)
+        if heading:
+            title = heading.group(1).strip().lower()
+            section = title if title in {"patterns", "gotchas"} else None
+            continue
+        if line.startswith("### ") and section == "patterns":
+            yield line_no, line
+        elif line.startswith("### ") and section == "gotchas" and include_gotchas:
+            yield line_no, line
+    logger.debug("exit", extra={"context": {"function": "iter_relevant_lines"}})
+
+
+def detect_promotion_candidates(report, knowledge_path):
+    logger.debug("entry", extra={"context": {"function": "detect_promotion_candidates", "path": str(knowledge_path)}})
+    try:
+        active_path = knowledge_path.parent / "activeContext.md"
+        if not active_path.exists():
+            logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": 0}})
+            return []
+        active_text = active_path.read_text(encoding="utf-8", errors="replace").lower()
+        candidates = []
+        for tier in ("warm", "cold", "archive"):
+            for entry in report["tiers"][tier]:
+                if entry["name"].lower() in active_text:
+                    candidates.append(entry)
+        logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": len(candidates)}})
+        return candidates
+    except OSError:
+        logger.exception("active_context_read_failed", extra={"context": {"function": "detect_promotion_candidates"}})
+        return []
+
+
+def make_report(knowledge_path, today_value, include_gotchas, thresholds):
+    logger.debug("entry", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+    report = blank_report(today_value)
+    try:
+        text = Path(knowledge_path).read_text(encoding="utf-8", errors="replace")
+    except OSError:
+        logger.exception("knowledge_read_failed", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+        raise
+    for line_no, line in iter_relevant_lines(text, include_gotchas):
+        entry = parse_entry_line(line, line_no, today_value, thresholds)
+        report["tiers"][entry["tier"]].append(entry)
+    for tier in TIERS:
+        report["summary"][tier] = len(report["tiers"][tier])
+    report["summary"]["total"] = sum(report["summary"][tier] for tier in TIERS)
+    report["promotion_candidates"] = detect_promotion_candidates(report, Path(knowledge_path))
+    logger.debug("exit", extra={"context": {"function": "make_report", "total": report["summary"]["total"]}})
+    return report
+
+
+def format_entry(entry):
+    logger.debug("entry", extra={"context": {"function": "format_entry", "tier": entry["tier"]}})
+    if entry["tier"] == "unparsed":
+        text = f"* {entry['name']} (line={entry['line_no']})"
+    else:
+        text = f"* {entry['name']} ({entry['verified']}, age={entry['age_days']}d)"
+    result = text[:80]
+    logger.debug("exit", extra={"context": {"function": "format_entry", "length": len(result)}})
+    return result
+
+
+def format_text_report(report):
+    logger.debug("entry", extra={"context": {"function": "format_text_report", "total": report["summary"]["total"]}})
+    lines = [
+        "Tier    | Count | Entries (truncated to first 80 chars)",
+        "--------+-------+-----------------------------------------",
+    ]
+    for tier in TIERS:
+        entries = report["tiers"][tier]
+        first = format_entry(entries[0]) if entries else ""
+        lines.append(f"{tier:<8}| {len(entries):^5} | {first}")
+        for entry in entries[1:]:
+            lines.append(f"{'':8}  {'':5}   {format_entry(entry)}")
+    lines.append(f"Total   | {report['summary']['total']:^5} |")
+    lines.extend(["", "## Age histogram"])
+    for tier in TIERS:
+        lines.append(f"{tier}: {report['summary'][tier]}")
+    candidates = report["promotion_candidates"]
+    lines.extend(["", f"## Promotion candidates ({len(candidates)}):"])
+    for entry in candidates:
+        lines.append(format_entry(entry))
+    result = "\n".join(lines)
+    logger.debug("exit", extra={"context": {"function": "format_text_report", "length": len(result)}})
+    return result
+
+
+def main(argv=None):
+    if argv is None:
+        argv = sys.argv[1:]
+    args = parse_args(argv)
+    configure_logging(args.verbose)
+    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
+    try:
+        today_value = parse_today(args.today)
+        thresholds = parse_thresholds(args.threshold_days)
+        data = make_report(Path(args.knowledge_path), today_value, not args.patterns_only, thresholds)
+        if args.json:
+            print(json.dumps(data, indent=2, sort_keys=True))
+        else:
+            print(format_text_report(data))
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 0}})
+        return 0
+    except (OSError, ValueError) as exc:
+        logger.exception("fatal_error", extra={"context": {"function": "main"}})
+        print(f"error: {exc}", file=sys.stderr)
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 2}})
+        return 2
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/.claude/scripts/test_knowledge_decay_report.py b/.claude/scripts/test_knowledge_decay_report.py
new file mode 100644
index 0000000000000000000000000000000000000000..f5e06729bb3a550ff345b4cf8b883c350128a62a
--- /dev/null
+++ b/.claude/scripts/test_knowledge_decay_report.py
@@ -0,0 +1,83 @@
+import importlib.util
+import json
+import tempfile
+import unittest
+from datetime import date
+from pathlib import Path
+
+
+SCRIPT_PATH = Path(__file__).with_name("knowledge-decay-report.py")
+SPEC = importlib.util.spec_from_file_location("knowledge_decay_report", SCRIPT_PATH)
+report = importlib.util.module_from_spec(SPEC)
+SPEC.loader.exec_module(report)
+
+
+def write_memory(root, knowledge_text, active_text=None):
+    memory = Path(root) / ".claude" / "memory"
+    memory.mkdir(parents=True)
+    knowledge_path = memory / "knowledge.md"
+    knowledge_path.write_text(knowledge_text, encoding="utf-8")
+    if active_text is not None:
+        (memory / "activeContext.md").write_text(active_text, encoding="utf-8")
+    return knowledge_path
+
+
+class KnowledgeDecayReportTests(unittest.TestCase):
+    def make_report(self, text, today="2026-04-25", active_text=None, include_gotchas=True):
+        with tempfile.TemporaryDirectory() as root:
+            knowledge_path = write_memory(root, text, active_text)
+            return report.make_report(
+                knowledge_path,
+                date.fromisoformat(today),
+                include_gotchas,
+                (14, 30, 90),
+            )
+
+    def test_fresh_entry_active(self):
+        data = self.make_report("## Patterns\n### Fresh (2026-04-20, verified: 2026-04-20)\n")
+        self.assertEqual(data["tiers"]["active"][0]["tier"], "active")
+
+    def test_twenty_days_warm(self):
+        data = self.make_report("## Patterns\n### Warm One (2026-04-05, verified: 2026-04-05)\n")
+        self.assertEqual(data["summary"]["warm"], 1)
+
+    def test_sixty_days_cold(self):
+        data = self.make_report("## Patterns\n### Cold One (2026-02-24, verified: 2026-02-24)\n")
+        self.assertEqual(data["tiers"]["cold"][0]["age_days"], 60)
+
+    def test_hundred_twenty_days_archive(self):
+        data = self.make_report("## Patterns\n### Old One (2025-12-26, verified: 2025-12-26)\n")
+        self.assertEqual(data["summary"]["archive"], 1)
+
+    def test_missing_verified_unparsed(self):
+        data = self.make_report("## Patterns\n### Missing Verified (2026-01-01)\n")
+        self.assertEqual(data["tiers"]["unparsed"][0]["tier"], "unparsed")
+
+    def test_today_override_applied(self):
+        data = self.make_report("## Patterns\n### Override (2026-04-01, verified: 2026-04-01)\n", today="2026-04-08")
+        self.assertEqual(data["tiers"]["active"][0]["age_days"], 7)
+
+    def test_patterns_only_excludes_gotchas(self):
+        text = "## Patterns\n### Pattern A (2026-04-20, verified: 2026-04-20)\n## Gotchas\n### Gotcha A (2026-04-20, verified: 2026-04-20)\n"
+        data = self.make_report(text, include_gotchas=False)
+        self.assertEqual(data["summary"]["total"], 1)
+        self.assertEqual(data["tiers"]["active"][0]["name"], "Pattern A")
+
+    def test_json_schema_round_trip(self):
+        data = self.make_report("## Patterns\n### Json One (2026-04-20, verified: 2026-04-20)\n")
+        loaded = json.loads(json.dumps(data))
+        self.assertEqual(set(["generated_at", "today", "tiers", "summary"]).issubset(loaded), True)
+        self.assertEqual(set(loaded["tiers"]["active"][0]), set(["name", "verified", "created", "age_days", "tier", "line_no"]))
+
+    def test_promotion_candidate_detection(self):
+        text = "## Patterns\n### Promote Me (2026-04-01, verified: 2026-04-01)\n"
+        data = self.make_report(text, active_text="We should revisit promote me today.")
+        self.assertEqual(data["promotion_candidates"][0]["name"], "Promote Me")
+
+    def test_empty_knowledge_total_zero(self):
+        data = self.make_report("")
+        self.assertEqual(data["summary"]["total"], 0)
+
+
+if __name__ == "__main__":
+    unittest.main()

codex
`py.exe` exists but can’t find installs. I’ll try the absolute Python path from PATH.
exec
powershell.exe -Command "& 'C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python312\\python.exe' --version; & 'C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python312\\python.exe' .claude/scripts/test_knowledge_decay_report.py; "'$testExit=$LASTEXITCODE; & '"'C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python312\\python.exe' .claude/scripts/knowledge-decay-report.py --help; "'$helpExit=$LASTEXITCODE; & '"'C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python312\\python.exe' .claude/scripts/knowledge-decay-report.py; "'$runExit=$LASTEXITCODE; Write-Output "ABS_PYTHON_EXITS test=$testExit help=$helpExit run=$runExit"; exit (($testExit -ne 0) -or ($helpExit -ne 0) -or ($runExit -ne 0))' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\codex\task-V1-knowledge-decay-report
2026-04-25T07:38:56.322972Z ERROR codex_core::tools::router: error={"output":"ABS_PYTHON_EXITS test= help= run=\r\n& : Имя \"C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python312\\python.exe\" не распознано как имя командлета, функции,\r\n файла сценария или выполняемой программы. Проверьте правильность написания имени, а также наличие и правильность пути,\r\n после чего повторите попытку.\r\nстрока:2 знак:3\r\n+ & 'C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python312\\python.exe ...\r\n+   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\r\n    + CategoryInfo          : ObjectNotFound: (C:\\Users\\Lenovo...n312\\python.exe:String) [], CommandNotFoundException\r\n    + FullyQualifiedErrorId : CommandNotFoundException\r\n \r\n& : Имя \"C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python312\\python.exe\" не распознано как имя командлета, функции,\r\n файла сценария или выполняемой программы. Проверьте правильность написания имени, а также наличие и правильность пути,\r\n после чего повторите попытку.\r\nстрока:2 знак:85\r\n+ ... -version; & 'C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python312\\ ...\r\n+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\r\n    + CategoryInfo          : ObjectNotFound: (C:\\Users\\Lenovo...n312\\python.exe:String) [], CommandNotFoundException\r\n    + FullyQualifiedErrorId : CommandNotFoundException\r\n \r\n& : Имя \"C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python312\\python.exe\" не распознано как имя командлета, функции,\r\n файла сценария или выполняемой программы. Проверьте правильность написания имени, а также наличие и правильность пути,\r\n после чего повторите попытку.\r\nстрока:2 знак:229\r\n+ ... EXITCODE; & 'C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python312\\ ...\r\n+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\r\n    + CategoryInfo          : ObjectNotFound: (C:\\Users\\Lenovo...n312\\python.exe:String) [], CommandNotFoundException\r\n    + FullyQualifiedErrorId : CommandNotFoundException\r\n \r\n& : Имя \"C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python312\\python.exe\" не распознано как имя командлета, функции,\r\n файла сценария или выполняемой программы. Проверьте правильность написания имени, а также наличие и правильность пути,\r\n после чего повторите попытку.\r\nстрока:2 знак:375\r\n+ ... EXITCODE; & 'C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python312\\ ...\r\n+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\r\n    + CategoryInfo          : ObjectNotFound: (C:\\Users\\Lenovo...n312\\python.exe:String) [], CommandNotFoundException\r\n    + FullyQualifiedErrorId : CommandNotFoundException\r\n \r\n","metadata":{"exit_code":1,"duration_seconds":0.5}}
 exited 1 in 488ms:
ABS_PYTHON_EXITS test= help= run=
& : Имя "C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe" не распознано как имя командлета, функции,
 файла сценария или выполняемой программы. Проверьте правильность написания имени, а также наличие и правильность пути,
 после чего повторите попытку.
строка:2 знак:3
+ & 'C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe ...
+   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (C:\Users\Lenovo...n312\python.exe:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 
& : Имя "C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe" не распознано как имя командлета, функции,
 файла сценария или выполняемой программы. Проверьте правильность написания имени, а также наличие и правильность пути,
 после чего повторите попытку.
строка:2 знак:85
+ ... -version; & 'C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\ ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (C:\Users\Lenovo...n312\python.exe:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 
& : Имя "C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe" не распознано как имя командлета, функции,
 файла сценария или выполняемой программы. Проверьте правильность написания имени, а также наличие и правильность пути,
 после чего повторите попытку.
строка:2 знак:229
+ ... EXITCODE; & 'C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\ ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (C:\Users\Lenovo...n312\python.exe:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 
& : Имя "C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe" не распознано как имя командлета, функции,
 файла сценария или выполняемой программы. Проверьте правильность написания имени, а также наличие и правильность пути,
 после чего повторите попытку.
строка:2 знак:375
+ ... EXITCODE; & 'C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\ ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (C:\Users\Lenovo...n312\python.exe:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

diff --git a/.claude/scripts/knowledge-decay-report.py b/.claude/scripts/knowledge-decay-report.py
new file mode 100644
index 0000000000000000000000000000000000000000..145c275c929084d0d84834375b0241c46b4effdc
--- /dev/null
+++ b/.claude/scripts/knowledge-decay-report.py
@@ -0,0 +1,283 @@
+#!/usr/bin/env python3
+"""Audit knowledge.md entries by verification age tier."""
+import argparse
+import json
+import logging
+import re
+import sys
+from datetime import date
+from pathlib import Path
+
+
+TIERS = ("active", "warm", "cold", "archive", "unparsed")
+DEFAULT_THRESHOLDS = (14, 30, 90)
+ENTRY_RE = re.compile(r"^###\s+(.+?)\s+\((\d{4}-\d{2}-\d{2}),\s*verified:\s*(\d{4}-\d{2}-\d{2})\)\s*$")
+HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
+
+
+class JsonFormatter(logging.Formatter):
+    def format(self, record):
+        payload = {
+            "level": record.levelname,
+            "message": record.getMessage(),
+            "logger": record.name,
+        }
+        if record.exc_info:
+            payload["exc_info"] = self.formatException(record.exc_info)
+        for key, value in getattr(record, "context", {}).items():
+            payload[key] = value
+        return json.dumps(payload, sort_keys=True)
+
+
+logger = logging.getLogger("knowledge_decay_report")
+
+
+def configure_logging(verbose):
+    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
+    handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(JsonFormatter())
+    root = logging.getLogger()
+    root.handlers.clear()
+    root.addHandler(handler)
+    root.setLevel(logging.DEBUG if verbose else logging.WARNING)
+    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})
+
+
+def parse_args(argv):
+    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
+    parser = argparse.ArgumentParser(description="Audit .claude/memory/knowledge.md verification decay tiers.")
+    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
+    parser.add_argument("--knowledge-path", default=".claude/memory/knowledge.md", help="Path to knowledge.md.")
+    parser.add_argument("--today", help="Override today's date as YYYY-MM-DD.")
+    group = parser.add_mutually_exclusive_group()
+    group.add_argument("--include-gotchas", action="store_true", help="Include Gotchas section entries (default).")
+    group.add_argument("--patterns-only", action="store_true", help="Only include Patterns section entries.")
+    parser.add_argument("--threshold-days", default="14,30,90", help="Comma-separated active,warm,cold day cutoffs.")
+    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG structured logs on stderr.")
+    args = parser.parse_args(argv)
+    logger.debug("exit", extra={"context": {"function": "parse_args", "json": args.json}})
+    return args
+
+
+def parse_thresholds(value):
+    logger.debug("entry", extra={"context": {"function": "parse_thresholds", "value": value}})
+    try:
+        parts = tuple(int(part.strip()) for part in value.split(","))
+        if len(parts) != 3 or parts[0] < 0 or not (parts[0] < parts[1] < parts[2]):
+            raise ValueError("thresholds must be three increasing non-negative integers")
+        logger.debug("exit", extra={"context": {"function": "parse_thresholds", "thresholds": parts}})
+        return parts
+    except ValueError:
+        logger.exception("invalid_thresholds", extra={"context": {"function": "parse_thresholds", "value": value}})
+        raise
+
+
+def parse_today(value):
+    logger.debug("entry", extra={"context": {"function": "parse_today", "provided": bool(value)}})
+    try:
+        result = date.fromisoformat(value) if value else date.today()
+        logger.debug("exit", extra={"context": {"function": "parse_today", "today": result.isoformat()}})
+        return result
+    except ValueError:
+        logger.exception("invalid_today", extra={"context": {"function": "parse_today", "value": value}})
+        raise
+
+
+def classify_age(age_days, thresholds):
+    logger.debug("entry", extra={"context": {"function": "classify_age", "age_days": age_days}})
+    active, warm, cold = thresholds
+    if age_days <= active:
+        tier = "active"
+    elif age_days <= warm:
+        tier = "warm"
+    elif age_days <= cold:
+        tier = "cold"
+    else:
+        tier = "archive"
+    logger.debug("exit", extra={"context": {"function": "classify_age", "tier": tier}})
+    return tier
+
+
+def blank_report(today_value):
+    logger.debug("entry", extra={"context": {"function": "blank_report", "today": today_value.isoformat()}})
+    result = {
+        "generated_at": date.today().isoformat(),
+        "today": today_value.isoformat(),
+        "tiers": {tier: [] for tier in TIERS},
+        "summary": {tier: 0 for tier in TIERS},
+        "promotion_candidates": [],
+    }
+    result["summary"]["total"] = 0
+    logger.debug("exit", extra={"context": {"function": "blank_report"}})
+    return result
+
+
+def extract_name(line):
+    logger.debug("entry", extra={"context": {"function": "extract_name"}})
+    text = line[4:].strip()
+    name = text.split(" (", 1)[0].strip() or text[:80]
+    logger.debug("exit", extra={"context": {"function": "extract_name", "name": name}})
+    return name
+
+
+def parse_entry_line(line, line_no, today_value, thresholds):
+    logger.debug("entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+    match = ENTRY_RE.match(line)
+    if not match:
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.warning("unparsed_entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+    try:
+        name, created_text, verified_text = match.groups()
+        created = date.fromisoformat(created_text)
+        verified = date.fromisoformat(verified_text)
+        age_days = (today_value - verified).days
+        tier = classify_age(age_days, thresholds)
+        entry = {
+            "name": name,
+            "verified": verified.isoformat(),
+            "created": created.isoformat(),
+            "age_days": age_days,
+            "tier": tier,
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": tier}})
+        return entry
+    except ValueError:
+        logger.exception("malformed_entry_dates", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+
+
+def iter_relevant_lines(text, include_gotchas):
+    logger.debug("entry", extra={"context": {"function": "iter_relevant_lines", "include_gotchas": include_gotchas}})
+    section = None
+    for line_no, line in enumerate(text.splitlines(), start=1):
+        heading = HEADING_RE.match(line)
+        if heading:
+            title = heading.group(1).strip().lower()
+            section = title if title in {"patterns", "gotchas"} else None
+            continue
+        if line.startswith("### ") and section == "patterns":
+            yield line_no, line
+        elif line.startswith("### ") and section == "gotchas" and include_gotchas:
+            yield line_no, line
+    logger.debug("exit", extra={"context": {"function": "iter_relevant_lines"}})
+
+
+def detect_promotion_candidates(report, knowledge_path):
+    logger.debug("entry", extra={"context": {"function": "detect_promotion_candidates", "path": str(knowledge_path)}})
+    try:
+        active_path = knowledge_path.parent / "activeContext.md"
+        if not active_path.exists():
+            logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": 0}})
+            return []
+        active_text = active_path.read_text(encoding="utf-8", errors="replace").lower()
+        candidates = []
+        for tier in ("warm", "cold", "archive"):
+            for entry in report["tiers"][tier]:
+                if entry["name"].lower() in active_text:
+                    candidates.append(entry)
+        logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": len(candidates)}})
+        return candidates
+    except OSError:
+        logger.exception("active_context_read_failed", extra={"context": {"function": "detect_promotion_candidates"}})
+        return []
+
+
+def make_report(knowledge_path, today_value, include_gotchas, thresholds):
+    logger.debug("entry", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+    report = blank_report(today_value)
+    try:
+        text = Path(knowledge_path).read_text(encoding="utf-8", errors="replace")
+    except OSError:
+        logger.exception("knowledge_read_failed", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+        raise
+    for line_no, line in iter_relevant_lines(text, include_gotchas):
+        entry = parse_entry_line(line, line_no, today_value, thresholds)
+        report["tiers"][entry["tier"]].append(entry)
+    for tier in TIERS:
+        report["summary"][tier] = len(report["tiers"][tier])
+    report["summary"]["total"] = sum(report["summary"][tier] for tier in TIERS)
+    report["promotion_candidates"] = detect_promotion_candidates(report, Path(knowledge_path))
+    logger.debug("exit", extra={"context": {"function": "make_report", "total": report["summary"]["total"]}})
+    return report
+
+
+def format_entry(entry):
+    logger.debug("entry", extra={"context": {"function": "format_entry", "tier": entry["tier"]}})
+    if entry["tier"] == "unparsed":
+        text = f"* {entry['name']} (line={entry['line_no']})"
+    else:
+        text = f"* {entry['name']} ({entry['verified']}, age={entry['age_days']}d)"
+    result = text[:80]
+    logger.debug("exit", extra={"context": {"function": "format_entry", "length": len(result)}})
+    return result
+
+
+def format_text_report(report):
+    logger.debug("entry", extra={"context": {"function": "format_text_report", "total": report["summary"]["total"]}})
+    lines = [
+        "Tier    | Count | Entries (truncated to first 80 chars)",
+        "--------+-------+-----------------------------------------",
+    ]
+    for tier in TIERS:
+        entries = report["tiers"][tier]
+        first = format_entry(entries[0]) if entries else ""
+        lines.append(f"{tier:<8}| {len(entries):^5} | {first}")
+        for entry in entries[1:]:
+            lines.append(f"{'':8}  {'':5}   {format_entry(entry)}")
+    lines.append(f"Total   | {report['summary']['total']:^5} |")
+    lines.extend(["", "## Age histogram"])
+    for tier in TIERS:
+        lines.append(f"{tier}: {report['summary'][tier]}")
+    candidates = report["promotion_candidates"]
+    lines.extend(["", f"## Promotion candidates ({len(candidates)}):"])
+    for entry in candidates:
+        lines.append(format_entry(entry))
+    result = "\n".join(lines)
+    logger.debug("exit", extra={"context": {"function": "format_text_report", "length": len(result)}})
+    return result
+
+
+def main(argv=None):
+    if argv is None:
+        argv = sys.argv[1:]
+    args = parse_args(argv)
+    configure_logging(args.verbose)
+    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
+    try:
+        today_value = parse_today(args.today)
+        thresholds = parse_thresholds(args.threshold_days)
+        data = make_report(Path(args.knowledge_path), today_value, not args.patterns_only, thresholds)
+        if args.json:
+            print(json.dumps(data, indent=2, sort_keys=True))
+        else:
+            print(format_text_report(data))
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 0}})
+        return 0
+    except (OSError, ValueError) as exc:
+        logger.exception("fatal_error", extra={"context": {"function": "main"}})
+        print(f"error: {exc}", file=sys.stderr)
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 2}})
+        return 2
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/.claude/scripts/test_knowledge_decay_report.py b/.claude/scripts/test_knowledge_decay_report.py
new file mode 100644
index 0000000000000000000000000000000000000000..f5e06729bb3a550ff345b4cf8b883c350128a62a
--- /dev/null
+++ b/.claude/scripts/test_knowledge_decay_report.py
@@ -0,0 +1,83 @@
+import importlib.util
+import json
+import tempfile
+import unittest
+from datetime import date
+from pathlib import Path
+
+
+SCRIPT_PATH = Path(__file__).with_name("knowledge-decay-report.py")
+SPEC = importlib.util.spec_from_file_location("knowledge_decay_report", SCRIPT_PATH)
+report = importlib.util.module_from_spec(SPEC)
+SPEC.loader.exec_module(report)
+
+
+def write_memory(root, knowledge_text, active_text=None):
+    memory = Path(root) / ".claude" / "memory"
+    memory.mkdir(parents=True)
+    knowledge_path = memory / "knowledge.md"
+    knowledge_path.write_text(knowledge_text, encoding="utf-8")
+    if active_text is not None:
+        (memory / "activeContext.md").write_text(active_text, encoding="utf-8")
+    return knowledge_path
+
+
+class KnowledgeDecayReportTests(unittest.TestCase):
+    def make_report(self, text, today="2026-04-25", active_text=None, include_gotchas=True):
+        with tempfile.TemporaryDirectory() as root:
+            knowledge_path = write_memory(root, text, active_text)
+            return report.make_report(
+                knowledge_path,
+                date.fromisoformat(today),
+                include_gotchas,
+                (14, 30, 90),
+            )
+
+    def test_fresh_entry_active(self):
+        data = self.make_report("## Patterns\n### Fresh (2026-04-20, verified: 2026-04-20)\n")
+        self.assertEqual(data["tiers"]["active"][0]["tier"], "active")
+
+    def test_twenty_days_warm(self):
+        data = self.make_report("## Patterns\n### Warm One (2026-04-05, verified: 2026-04-05)\n")
+        self.assertEqual(data["summary"]["warm"], 1)
+
+    def test_sixty_days_cold(self):
+        data = self.make_report("## Patterns\n### Cold One (2026-02-24, verified: 2026-02-24)\n")
+        self.assertEqual(data["tiers"]["cold"][0]["age_days"], 60)
+
+    def test_hundred_twenty_days_archive(self):
+        data = self.make_report("## Patterns\n### Old One (2025-12-26, verified: 2025-12-26)\n")
+        self.assertEqual(data["summary"]["archive"], 1)
+
+    def test_missing_verified_unparsed(self):
+        data = self.make_report("## Patterns\n### Missing Verified (2026-01-01)\n")
+        self.assertEqual(data["tiers"]["unparsed"][0]["tier"], "unparsed")
+
+    def test_today_override_applied(self):
+        data = self.make_report("## Patterns\n### Override (2026-04-01, verified: 2026-04-01)\n", today="2026-04-08")
+        self.assertEqual(data["tiers"]["active"][0]["age_days"], 7)
+
+    def test_patterns_only_excludes_gotchas(self):
+        text = "## Patterns\n### Pattern A (2026-04-20, verified: 2026-04-20)\n## Gotchas\n### Gotcha A (2026-04-20, verified: 2026-04-20)\n"
+        data = self.make_report(text, include_gotchas=False)
+        self.assertEqual(data["summary"]["total"], 1)
+        self.assertEqual(data["tiers"]["active"][0]["name"], "Pattern A")
+
+    def test_json_schema_round_trip(self):
+        data = self.make_report("## Patterns\n### Json One (2026-04-20, verified: 2026-04-20)\n")
+        loaded = json.loads(json.dumps(data))
+        self.assertEqual(set(["generated_at", "today", "tiers", "summary"]).issubset(loaded), True)
+        self.assertEqual(set(loaded["tiers"]["active"][0]), set(["name", "verified", "created", "age_days", "tier", "line_no"]))
+
+    def test_promotion_candidate_detection(self):
+        text = "## Patterns\n### Promote Me (2026-04-01, verified: 2026-04-01)\n"
+        data = self.make_report(text, active_text="We should revisit promote me today.")
+        self.assertEqual(data["promotion_candidates"][0]["name"], "Promote Me")
+
+    def test_empty_knowledge_total_zero(self):
+        data = self.make_report("")
+        self.assertEqual(data["summary"]["total"], 0)
+
+
+if __name__ == "__main__":
+    unittest.main()

codex
Absolute Python is unavailable too. I’ll still execute the remaining exact required commands for the report.
exec
powershell.exe -Command 'py -3 .claude/scripts/knowledge-decay-report.py --help; Write-Output "HELP_EXIT=$LASTEXITCODE"; py -3 .claude/scripts/knowledge-decay-report.py; Write-Output "RUN_EXIT=$LASTEXITCODE"' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\codex\task-V1-knowledge-decay-report
 succeeded in 429ms:
HELP_EXIT=112
RUN_EXIT=112
No installed Python found!
No installed Python found!

diff --git a/.claude/scripts/knowledge-decay-report.py b/.claude/scripts/knowledge-decay-report.py
new file mode 100644
index 0000000000000000000000000000000000000000..145c275c929084d0d84834375b0241c46b4effdc
--- /dev/null
+++ b/.claude/scripts/knowledge-decay-report.py
@@ -0,0 +1,283 @@
+#!/usr/bin/env python3
+"""Audit knowledge.md entries by verification age tier."""
+import argparse
+import json
+import logging
+import re
+import sys
+from datetime import date
+from pathlib import Path
+
+
+TIERS = ("active", "warm", "cold", "archive", "unparsed")
+DEFAULT_THRESHOLDS = (14, 30, 90)
+ENTRY_RE = re.compile(r"^###\s+(.+?)\s+\((\d{4}-\d{2}-\d{2}),\s*verified:\s*(\d{4}-\d{2}-\d{2})\)\s*$")
+HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
+
+
+class JsonFormatter(logging.Formatter):
+    def format(self, record):
+        payload = {
+            "level": record.levelname,
+            "message": record.getMessage(),
+            "logger": record.name,
+        }
+        if record.exc_info:
+            payload["exc_info"] = self.formatException(record.exc_info)
+        for key, value in getattr(record, "context", {}).items():
+            payload[key] = value
+        return json.dumps(payload, sort_keys=True)
+
+
+logger = logging.getLogger("knowledge_decay_report")
+
+
+def configure_logging(verbose):
+    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
+    handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(JsonFormatter())
+    root = logging.getLogger()
+    root.handlers.clear()
+    root.addHandler(handler)
+    root.setLevel(logging.DEBUG if verbose else logging.WARNING)
+    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})
+
+
+def parse_args(argv):
+    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
+    parser = argparse.ArgumentParser(description="Audit .claude/memory/knowledge.md verification decay tiers.")
+    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
+    parser.add_argument("--knowledge-path", default=".claude/memory/knowledge.md", help="Path to knowledge.md.")
+    parser.add_argument("--today", help="Override today's date as YYYY-MM-DD.")
+    group = parser.add_mutually_exclusive_group()
+    group.add_argument("--include-gotchas", action="store_true", help="Include Gotchas section entries (default).")
+    group.add_argument("--patterns-only", action="store_true", help="Only include Patterns section entries.")
+    parser.add_argument("--threshold-days", default="14,30,90", help="Comma-separated active,warm,cold day cutoffs.")
+    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG structured logs on stderr.")
+    args = parser.parse_args(argv)
+    logger.debug("exit", extra={"context": {"function": "parse_args", "json": args.json}})
+    return args
+
+
+def parse_thresholds(value):
+    logger.debug("entry", extra={"context": {"function": "parse_thresholds", "value": value}})
+    try:
+        parts = tuple(int(part.strip()) for part in value.split(","))
+        if len(parts) != 3 or parts[0] < 0 or not (parts[0] < parts[1] < parts[2]):
+            raise ValueError("thresholds must be three increasing non-negative integers")
+        logger.debug("exit", extra={"context": {"function": "parse_thresholds", "thresholds": parts}})
+        return parts
+    except ValueError:
+        logger.exception("invalid_thresholds", extra={"context": {"function": "parse_thresholds", "value": value}})
+        raise
+
+
+def parse_today(value):
+    logger.debug("entry", extra={"context": {"function": "parse_today", "provided": bool(value)}})
+    try:
+        result = date.fromisoformat(value) if value else date.today()
+        logger.debug("exit", extra={"context": {"function": "parse_today", "today": result.isoformat()}})
+        return result
+    except ValueError:
+        logger.exception("invalid_today", extra={"context": {"function": "parse_today", "value": value}})
+        raise
+
+
+def classify_age(age_days, thresholds):
+    logger.debug("entry", extra={"context": {"function": "classify_age", "age_days": age_days}})
+    active, warm, cold = thresholds
+    if age_days <= active:
+        tier = "active"
+    elif age_days <= warm:
+        tier = "warm"
+    elif age_days <= cold:
+        tier = "cold"
+    else:
+        tier = "archive"
+    logger.debug("exit", extra={"context": {"function": "classify_age", "tier": tier}})
+    return tier
+
+
+def blank_report(today_value):
+    logger.debug("entry", extra={"context": {"function": "blank_report", "today": today_value.isoformat()}})
+    result = {
+        "generated_at": date.today().isoformat(),
+        "today": today_value.isoformat(),
+        "tiers": {tier: [] for tier in TIERS},
+        "summary": {tier: 0 for tier in TIERS},
+        "promotion_candidates": [],
+    }
+    result["summary"]["total"] = 0
+    logger.debug("exit", extra={"context": {"function": "blank_report"}})
+    return result
+
+
+def extract_name(line):
+    logger.debug("entry", extra={"context": {"function": "extract_name"}})
+    text = line[4:].strip()
+    name = text.split(" (", 1)[0].strip() or text[:80]
+    logger.debug("exit", extra={"context": {"function": "extract_name", "name": name}})
+    return name
+
+
+def parse_entry_line(line, line_no, today_value, thresholds):
+    logger.debug("entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+    match = ENTRY_RE.match(line)
+    if not match:
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.warning("unparsed_entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+    try:
+        name, created_text, verified_text = match.groups()
+        created = date.fromisoformat(created_text)
+        verified = date.fromisoformat(verified_text)
+        age_days = (today_value - verified).days
+        tier = classify_age(age_days, thresholds)
+        entry = {
+            "name": name,
+            "verified": verified.isoformat(),
+            "created": created.isoformat(),
+            "age_days": age_days,
+            "tier": tier,
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": tier}})
+        return entry
+    except ValueError:
+        logger.exception("malformed_entry_dates", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+
+
+def iter_relevant_lines(text, include_gotchas):
+    logger.debug("entry", extra={"context": {"function": "iter_relevant_lines", "include_gotchas": include_gotchas}})
+    section = None
+    for line_no, line in enumerate(text.splitlines(), start=1):
+        heading = HEADING_RE.match(line)
+        if heading:
+            title = heading.group(1).strip().lower()
+            section = title if title in {"patterns", "gotchas"} else None
+            continue
+        if line.startswith("### ") and section == "patterns":
+            yield line_no, line
+        elif line.startswith("### ") and section == "gotchas" and include_gotchas:
+            yield line_no, line
+    logger.debug("exit", extra={"context": {"function": "iter_relevant_lines"}})
+
+
+def detect_promotion_candidates(report, knowledge_path):
+    logger.debug("entry", extra={"context": {"function": "detect_promotion_candidates", "path": str(knowledge_path)}})
+    try:
+        active_path = knowledge_path.parent / "activeContext.md"
+        if not active_path.exists():
+            logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": 0}})
+            return []
+        active_text = active_path.read_text(encoding="utf-8", errors="replace").lower()
+        candidates = []
+        for tier in ("warm", "cold", "archive"):
+            for entry in report["tiers"][tier]:
+                if entry["name"].lower() in active_text:
+                    candidates.append(entry)
+        logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": len(candidates)}})
+        return candidates
+    except OSError:
+        logger.exception("active_context_read_failed", extra={"context": {"function": "detect_promotion_candidates"}})
+        return []
+
+
+def make_report(knowledge_path, today_value, include_gotchas, thresholds):
+    logger.debug("entry", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+    report = blank_report(today_value)
+    try:
+        text = Path(knowledge_path).read_text(encoding="utf-8", errors="replace")
+    except OSError:
+        logger.exception("knowledge_read_failed", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+        raise
+    for line_no, line in iter_relevant_lines(text, include_gotchas):
+        entry = parse_entry_line(line, line_no, today_value, thresholds)
+        report["tiers"][entry["tier"]].append(entry)
+    for tier in TIERS:
+        report["summary"][tier] = len(report["tiers"][tier])
+    report["summary"]["total"] = sum(report["summary"][tier] for tier in TIERS)
+    report["promotion_candidates"] = detect_promotion_candidates(report, Path(knowledge_path))
+    logger.debug("exit", extra={"context": {"function": "make_report", "total": report["summary"]["total"]}})
+    return report
+
+
+def format_entry(entry):
+    logger.debug("entry", extra={"context": {"function": "format_entry", "tier": entry["tier"]}})
+    if entry["tier"] == "unparsed":
+        text = f"* {entry['name']} (line={entry['line_no']})"
+    else:
+        text = f"* {entry['name']} ({entry['verified']}, age={entry['age_days']}d)"
+    result = text[:80]
+    logger.debug("exit", extra={"context": {"function": "format_entry", "length": len(result)}})
+    return result
+
+
+def format_text_report(report):
+    logger.debug("entry", extra={"context": {"function": "format_text_report", "total": report["summary"]["total"]}})
+    lines = [
+        "Tier    | Count | Entries (truncated to first 80 chars)",
+        "--------+-------+-----------------------------------------",
+    ]
+    for tier in TIERS:
+        entries = report["tiers"][tier]
+        first = format_entry(entries[0]) if entries else ""
+        lines.append(f"{tier:<8}| {len(entries):^5} | {first}")
+        for entry in entries[1:]:
+            lines.append(f"{'':8}  {'':5}   {format_entry(entry)}")
+    lines.append(f"Total   | {report['summary']['total']:^5} |")
+    lines.extend(["", "## Age histogram"])
+    for tier in TIERS:
+        lines.append(f"{tier}: {report['summary'][tier]}")
+    candidates = report["promotion_candidates"]
+    lines.extend(["", f"## Promotion candidates ({len(candidates)}):"])
+    for entry in candidates:
+        lines.append(format_entry(entry))
+    result = "\n".join(lines)
+    logger.debug("exit", extra={"context": {"function": "format_text_report", "length": len(result)}})
+    return result
+
+
+def main(argv=None):
+    if argv is None:
+        argv = sys.argv[1:]
+    args = parse_args(argv)
+    configure_logging(args.verbose)
+    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
+    try:
+        today_value = parse_today(args.today)
+        thresholds = parse_thresholds(args.threshold_days)
+        data = make_report(Path(args.knowledge_path), today_value, not args.patterns_only, thresholds)
+        if args.json:
+            print(json.dumps(data, indent=2, sort_keys=True))
+        else:
+            print(format_text_report(data))
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 0}})
+        return 0
+    except (OSError, ValueError) as exc:
+        logger.exception("fatal_error", extra={"context": {"function": "main"}})
+        print(f"error: {exc}", file=sys.stderr)
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 2}})
+        return 2
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/.claude/scripts/test_knowledge_decay_report.py b/.claude/scripts/test_knowledge_decay_report.py
new file mode 100644
index 0000000000000000000000000000000000000000..f5e06729bb3a550ff345b4cf8b883c350128a62a
--- /dev/null
+++ b/.claude/scripts/test_knowledge_decay_report.py
@@ -0,0 +1,83 @@
+import importlib.util
+import json
+import tempfile
+import unittest
+from datetime import date
+from pathlib import Path
+
+
+SCRIPT_PATH = Path(__file__).with_name("knowledge-decay-report.py")
+SPEC = importlib.util.spec_from_file_location("knowledge_decay_report", SCRIPT_PATH)
+report = importlib.util.module_from_spec(SPEC)
+SPEC.loader.exec_module(report)
+
+
+def write_memory(root, knowledge_text, active_text=None):
+    memory = Path(root) / ".claude" / "memory"
+    memory.mkdir(parents=True)
+    knowledge_path = memory / "knowledge.md"
+    knowledge_path.write_text(knowledge_text, encoding="utf-8")
+    if active_text is not None:
+        (memory / "activeContext.md").write_text(active_text, encoding="utf-8")
+    return knowledge_path
+
+
+class KnowledgeDecayReportTests(unittest.TestCase):
+    def make_report(self, text, today="2026-04-25", active_text=None, include_gotchas=True):
+        with tempfile.TemporaryDirectory() as root:
+            knowledge_path = write_memory(root, text, active_text)
+            return report.make_report(
+                knowledge_path,
+                date.fromisoformat(today),
+                include_gotchas,
+                (14, 30, 90),
+            )
+
+    def test_fresh_entry_active(self):
+        data = self.make_report("## Patterns\n### Fresh (2026-04-20, verified: 2026-04-20)\n")
+        self.assertEqual(data["tiers"]["active"][0]["tier"], "active")
+
+    def test_twenty_days_warm(self):
+        data = self.make_report("## Patterns\n### Warm One (2026-04-05, verified: 2026-04-05)\n")
+        self.assertEqual(data["summary"]["warm"], 1)
+
+    def test_sixty_days_cold(self):
+        data = self.make_report("## Patterns\n### Cold One (2026-02-24, verified: 2026-02-24)\n")
+        self.assertEqual(data["tiers"]["cold"][0]["age_days"], 60)
+
+    def test_hundred_twenty_days_archive(self):
+        data = self.make_report("## Patterns\n### Old One (2025-12-26, verified: 2025-12-26)\n")
+        self.assertEqual(data["summary"]["archive"], 1)
+
+    def test_missing_verified_unparsed(self):
+        data = self.make_report("## Patterns\n### Missing Verified (2026-01-01)\n")
+        self.assertEqual(data["tiers"]["unparsed"][0]["tier"], "unparsed")
+
+    def test_today_override_applied(self):
+        data = self.make_report("## Patterns\n### Override (2026-04-01, verified: 2026-04-01)\n", today="2026-04-08")
+        self.assertEqual(data["tiers"]["active"][0]["age_days"], 7)
+
+    def test_patterns_only_excludes_gotchas(self):
+        text = "## Patterns\n### Pattern A (2026-04-20, verified: 2026-04-20)\n## Gotchas\n### Gotcha A (2026-04-20, verified: 2026-04-20)\n"
+        data = self.make_report(text, include_gotchas=False)
+        self.assertEqual(data["summary"]["total"], 1)
+        self.assertEqual(data["tiers"]["active"][0]["name"], "Pattern A")
+
+    def test_json_schema_round_trip(self):
+        data = self.make_report("## Patterns\n### Json One (2026-04-20, verified: 2026-04-20)\n")
+        loaded = json.loads(json.dumps(data))
+        self.assertEqual(set(["generated_at", "today", "tiers", "summary"]).issubset(loaded), True)
+        self.assertEqual(set(loaded["tiers"]["active"][0]), set(["name", "verified", "created", "age_days", "tier", "line_no"]))
+
+    def test_promotion_candidate_detection(self):
+        text = "## Patterns\n### Promote Me (2026-04-01, verified: 2026-04-01)\n"
+        data = self.make_report(text, active_text="We should revisit promote me today.")
+        self.assertEqual(data["promotion_candidates"][0]["name"], "Promote Me")
+
+    def test_empty_knowledge_total_zero(self):
+        data = self.make_report("")
+        self.assertEqual(data["summary"]["total"], 0)
+
+
+if __name__ == "__main__":
+    unittest.main()

**Considering exit command issues**

I’m facing a situation with the exit command where the overall command completed successfully, but individual parts failed. I need to think about finding the right syntax for compiling. I'm not using Python here, so maybe I should look into static options. I wonder if I could find a minimal approach or perhaps even try using a command like `py -0p`. It’s a bit perplexing, but I’ll figure it out!
exec
powershell.exe -Command 'py -0p; Write-Output "PYLIST_EXIT=$LASTEXITCODE"; Get-ChildItem -Path '"'.claude/scripts/knowledge-decay-report.py','.claude/scripts/test_knowledge_decay_report.py' | Select-Object Name,Length; (Get-Content '.claude/scripts/knowledge-decay-report.py').Count; (Get-Content '.claude/scripts/test_knowledge_decay_report.py').Count" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\codex\task-V1-knowledge-decay-report
 succeeded in 439ms:
No installed Pythons found!
PYLIST_EXIT=0

Name                           Length
----                           ------
knowledge-decay-report.py       12212
test_knowledge_decay_report.py   3717
283
83



diff --git a/.claude/scripts/knowledge-decay-report.py b/.claude/scripts/knowledge-decay-report.py
new file mode 100644
index 0000000000000000000000000000000000000000..145c275c929084d0d84834375b0241c46b4effdc
--- /dev/null
+++ b/.claude/scripts/knowledge-decay-report.py
@@ -0,0 +1,283 @@
+#!/usr/bin/env python3
+"""Audit knowledge.md entries by verification age tier."""
+import argparse
+import json
+import logging
+import re
+import sys
+from datetime import date
+from pathlib import Path
+
+
+TIERS = ("active", "warm", "cold", "archive", "unparsed")
+DEFAULT_THRESHOLDS = (14, 30, 90)
+ENTRY_RE = re.compile(r"^###\s+(.+?)\s+\((\d{4}-\d{2}-\d{2}),\s*verified:\s*(\d{4}-\d{2}-\d{2})\)\s*$")
+HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
+
+
+class JsonFormatter(logging.Formatter):
+    def format(self, record):
+        payload = {
+            "level": record.levelname,
+            "message": record.getMessage(),
+            "logger": record.name,
+        }
+        if record.exc_info:
+            payload["exc_info"] = self.formatException(record.exc_info)
+        for key, value in getattr(record, "context", {}).items():
+            payload[key] = value
+        return json.dumps(payload, sort_keys=True)
+
+
+logger = logging.getLogger("knowledge_decay_report")
+
+
+def configure_logging(verbose):
+    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
+    handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(JsonFormatter())
+    root = logging.getLogger()
+    root.handlers.clear()
+    root.addHandler(handler)
+    root.setLevel(logging.DEBUG if verbose else logging.WARNING)
+    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})
+
+
+def parse_args(argv):
+    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
+    parser = argparse.ArgumentParser(description="Audit .claude/memory/knowledge.md verification decay tiers.")
+    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
+    parser.add_argument("--knowledge-path", default=".claude/memory/knowledge.md", help="Path to knowledge.md.")
+    parser.add_argument("--today", help="Override today's date as YYYY-MM-DD.")
+    group = parser.add_mutually_exclusive_group()
+    group.add_argument("--include-gotchas", action="store_true", help="Include Gotchas section entries (default).")
+    group.add_argument("--patterns-only", action="store_true", help="Only include Patterns section entries.")
+    parser.add_argument("--threshold-days", default="14,30,90", help="Comma-separated active,warm,cold day cutoffs.")
+    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG structured logs on stderr.")
+    args = parser.parse_args(argv)
+    logger.debug("exit", extra={"context": {"function": "parse_args", "json": args.json}})
+    return args
+
+
+def parse_thresholds(value):
+    logger.debug("entry", extra={"context": {"function": "parse_thresholds", "value": value}})
+    try:
+        parts = tuple(int(part.strip()) for part in value.split(","))
+        if len(parts) != 3 or parts[0] < 0 or not (parts[0] < parts[1] < parts[2]):
+            raise ValueError("thresholds must be three increasing non-negative integers")
+        logger.debug("exit", extra={"context": {"function": "parse_thresholds", "thresholds": parts}})
+        return parts
+    except ValueError:
+        logger.exception("invalid_thresholds", extra={"context": {"function": "parse_thresholds", "value": value}})
+        raise
+
+
+def parse_today(value):
+    logger.debug("entry", extra={"context": {"function": "parse_today", "provided": bool(value)}})
+    try:
+        result = date.fromisoformat(value) if value else date.today()
+        logger.debug("exit", extra={"context": {"function": "parse_today", "today": result.isoformat()}})
+        return result
+    except ValueError:
+        logger.exception("invalid_today", extra={"context": {"function": "parse_today", "value": value}})
+        raise
+
+
+def classify_age(age_days, thresholds):
+    logger.debug("entry", extra={"context": {"function": "classify_age", "age_days": age_days}})
+    active, warm, cold = thresholds
+    if age_days <= active:
+        tier = "active"
+    elif age_days <= warm:
+        tier = "warm"
+    elif age_days <= cold:
+        tier = "cold"
+    else:
+        tier = "archive"
+    logger.debug("exit", extra={"context": {"function": "classify_age", "tier": tier}})
+    return tier
+
+
+def blank_report(today_value):
+    logger.debug("entry", extra={"context": {"function": "blank_report", "today": today_value.isoformat()}})
+    result = {
+        "generated_at": date.today().isoformat(),
+        "today": today_value.isoformat(),
+        "tiers": {tier: [] for tier in TIERS},
+        "summary": {tier: 0 for tier in TIERS},
+        "promotion_candidates": [],
+    }
+    result["summary"]["total"] = 0
+    logger.debug("exit", extra={"context": {"function": "blank_report"}})
+    return result
+
+
+def extract_name(line):
+    logger.debug("entry", extra={"context": {"function": "extract_name"}})
+    text = line[4:].strip()
+    name = text.split(" (", 1)[0].strip() or text[:80]
+    logger.debug("exit", extra={"context": {"function": "extract_name", "name": name}})
+    return name
+
+
+def parse_entry_line(line, line_no, today_value, thresholds):
+    logger.debug("entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+    match = ENTRY_RE.match(line)
+    if not match:
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.warning("unparsed_entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+    try:
+        name, created_text, verified_text = match.groups()
+        created = date.fromisoformat(created_text)
+        verified = date.fromisoformat(verified_text)
+        age_days = (today_value - verified).days
+        tier = classify_age(age_days, thresholds)
+        entry = {
+            "name": name,
+            "verified": verified.isoformat(),
+            "created": created.isoformat(),
+            "age_days": age_days,
+            "tier": tier,
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": tier}})
+        return entry
+    except ValueError:
+        logger.exception("malformed_entry_dates", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+
+
+def iter_relevant_lines(text, include_gotchas):
+    logger.debug("entry", extra={"context": {"function": "iter_relevant_lines", "include_gotchas": include_gotchas}})
+    section = None
+    for line_no, line in enumerate(text.splitlines(), start=1):
+        heading = HEADING_RE.match(line)
+        if heading:
+            title = heading.group(1).strip().lower()
+            section = title if title in {"patterns", "gotchas"} else None
+            continue
+        if line.startswith("### ") and section == "patterns":
+            yield line_no, line
+        elif line.startswith("### ") and section == "gotchas" and include_gotchas:
+            yield line_no, line
+    logger.debug("exit", extra={"context": {"function": "iter_relevant_lines"}})
+
+
+def detect_promotion_candidates(report, knowledge_path):
+    logger.debug("entry", extra={"context": {"function": "detect_promotion_candidates", "path": str(knowledge_path)}})
+    try:
+        active_path = knowledge_path.parent / "activeContext.md"
+        if not active_path.exists():
+            logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": 0}})
+            return []
+        active_text = active_path.read_text(encoding="utf-8", errors="replace").lower()
+        candidates = []
+        for tier in ("warm", "cold", "archive"):
+            for entry in report["tiers"][tier]:
+                if entry["name"].lower() in active_text:
+                    candidates.append(entry)
+        logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": len(candidates)}})
+        return candidates
+    except OSError:
+        logger.exception("active_context_read_failed", extra={"context": {"function": "detect_promotion_candidates"}})
+        return []
+
+
+def make_report(knowledge_path, today_value, include_gotchas, thresholds):
+    logger.debug("entry", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+    report = blank_report(today_value)
+    try:
+        text = Path(knowledge_path).read_text(encoding="utf-8", errors="replace")
+    except OSError:
+        logger.exception("knowledge_read_failed", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+        raise
+    for line_no, line in iter_relevant_lines(text, include_gotchas):
+        entry = parse_entry_line(line, line_no, today_value, thresholds)
+        report["tiers"][entry["tier"]].append(entry)
+    for tier in TIERS:
+        report["summary"][tier] = len(report["tiers"][tier])
+    report["summary"]["total"] = sum(report["summary"][tier] for tier in TIERS)
+    report["promotion_candidates"] = detect_promotion_candidates(report, Path(knowledge_path))
+    logger.debug("exit", extra={"context": {"function": "make_report", "total": report["summary"]["total"]}})
+    return report
+
+
+def format_entry(entry):
+    logger.debug("entry", extra={"context": {"function": "format_entry", "tier": entry["tier"]}})
+    if entry["tier"] == "unparsed":
+        text = f"* {entry['name']} (line={entry['line_no']})"
+    else:
+        text = f"* {entry['name']} ({entry['verified']}, age={entry['age_days']}d)"
+    result = text[:80]
+    logger.debug("exit", extra={"context": {"function": "format_entry", "length": len(result)}})
+    return result
+
+
+def format_text_report(report):
+    logger.debug("entry", extra={"context": {"function": "format_text_report", "total": report["summary"]["total"]}})
+    lines = [
+        "Tier    | Count | Entries (truncated to first 80 chars)",
+        "--------+-------+-----------------------------------------",
+    ]
+    for tier in TIERS:
+        entries = report["tiers"][tier]
+        first = format_entry(entries[0]) if entries else ""
+        lines.append(f"{tier:<8}| {len(entries):^5} | {first}")
+        for entry in entries[1:]:
+            lines.append(f"{'':8}  {'':5}   {format_entry(entry)}")
+    lines.append(f"Total   | {report['summary']['total']:^5} |")
+    lines.extend(["", "## Age histogram"])
+    for tier in TIERS:
+        lines.append(f"{tier}: {report['summary'][tier]}")
+    candidates = report["promotion_candidates"]
+    lines.extend(["", f"## Promotion candidates ({len(candidates)}):"])
+    for entry in candidates:
+        lines.append(format_entry(entry))
+    result = "\n".join(lines)
+    logger.debug("exit", extra={"context": {"function": "format_text_report", "length": len(result)}})
+    return result
+
+
+def main(argv=None):
+    if argv is None:
+        argv = sys.argv[1:]
+    args = parse_args(argv)
+    configure_logging(args.verbose)
+    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
+    try:
+        today_value = parse_today(args.today)
+        thresholds = parse_thresholds(args.threshold_days)
+        data = make_report(Path(args.knowledge_path), today_value, not args.patterns_only, thresholds)
+        if args.json:
+            print(json.dumps(data, indent=2, sort_keys=True))
+        else:
+            print(format_text_report(data))
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 0}})
+        return 0
+    except (OSError, ValueError) as exc:
+        logger.exception("fatal_error", extra={"context": {"function": "main"}})
+        print(f"error: {exc}", file=sys.stderr)
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 2}})
+        return 2
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/.claude/scripts/test_knowledge_decay_report.py b/.claude/scripts/test_knowledge_decay_report.py
new file mode 100644
index 0000000000000000000000000000000000000000..f5e06729bb3a550ff345b4cf8b883c350128a62a
--- /dev/null
+++ b/.claude/scripts/test_knowledge_decay_report.py
@@ -0,0 +1,83 @@
+import importlib.util
+import json
+import tempfile
+import unittest
+from datetime import date
+from pathlib import Path
+
+
+SCRIPT_PATH = Path(__file__).with_name("knowledge-decay-report.py")
+SPEC = importlib.util.spec_from_file_location("knowledge_decay_report", SCRIPT_PATH)
+report = importlib.util.module_from_spec(SPEC)
+SPEC.loader.exec_module(report)
+
+
+def write_memory(root, knowledge_text, active_text=None):
+    memory = Path(root) / ".claude" / "memory"
+    memory.mkdir(parents=True)
+    knowledge_path = memory / "knowledge.md"
+    knowledge_path.write_text(knowledge_text, encoding="utf-8")
+    if active_text is not None:
+        (memory / "activeContext.md").write_text(active_text, encoding="utf-8")
+    return knowledge_path
+
+
+class KnowledgeDecayReportTests(unittest.TestCase):
+    def make_report(self, text, today="2026-04-25", active_text=None, include_gotchas=True):
+        with tempfile.TemporaryDirectory() as root:
+            knowledge_path = write_memory(root, text, active_text)
+            return report.make_report(
+                knowledge_path,
+                date.fromisoformat(today),
+                include_gotchas,
+                (14, 30, 90),
+            )
+
+    def test_fresh_entry_active(self):
+        data = self.make_report("## Patterns\n### Fresh (2026-04-20, verified: 2026-04-20)\n")
+        self.assertEqual(data["tiers"]["active"][0]["tier"], "active")
+
+    def test_twenty_days_warm(self):
+        data = self.make_report("## Patterns\n### Warm One (2026-04-05, verified: 2026-04-05)\n")
+        self.assertEqual(data["summary"]["warm"], 1)
+
+    def test_sixty_days_cold(self):
+        data = self.make_report("## Patterns\n### Cold One (2026-02-24, verified: 2026-02-24)\n")
+        self.assertEqual(data["tiers"]["cold"][0]["age_days"], 60)
+
+    def test_hundred_twenty_days_archive(self):
+        data = self.make_report("## Patterns\n### Old One (2025-12-26, verified: 2025-12-26)\n")
+        self.assertEqual(data["summary"]["archive"], 1)
+
+    def test_missing_verified_unparsed(self):
+        data = self.make_report("## Patterns\n### Missing Verified (2026-01-01)\n")
+        self.assertEqual(data["tiers"]["unparsed"][0]["tier"], "unparsed")
+
+    def test_today_override_applied(self):
+        data = self.make_report("## Patterns\n### Override (2026-04-01, verified: 2026-04-01)\n", today="2026-04-08")
+        self.assertEqual(data["tiers"]["active"][0]["age_days"], 7)
+
+    def test_patterns_only_excludes_gotchas(self):
+        text = "## Patterns\n### Pattern A (2026-04-20, verified: 2026-04-20)\n## Gotchas\n### Gotcha A (2026-04-20, verified: 2026-04-20)\n"
+        data = self.make_report(text, include_gotchas=False)
+        self.assertEqual(data["summary"]["total"], 1)
+        self.assertEqual(data["tiers"]["active"][0]["name"], "Pattern A")
+
+    def test_json_schema_round_trip(self):
+        data = self.make_report("## Patterns\n### Json One (2026-04-20, verified: 2026-04-20)\n")
+        loaded = json.loads(json.dumps(data))
+        self.assertEqual(set(["generated_at", "today", "tiers", "summary"]).issubset(loaded), True)
+        self.assertEqual(set(loaded["tiers"]["active"][0]), set(["name", "verified", "created", "age_days", "tier", "line_no"]))
+
+    def test_promotion_candidate_detection(self):
+        text = "## Patterns\n### Promote Me (2026-04-01, verified: 2026-04-01)\n"
+        data = self.make_report(text, active_text="We should revisit promote me today.")
+        self.assertEqual(data["promotion_candidates"][0]["name"], "Promote Me")
+
+    def test_empty_knowledge_total_zero(self):
+        data = self.make_report("")
+        self.assertEqual(data["summary"]["total"], 0)
+
+
+if __name__ == "__main__":
+    unittest.main()

**Assessing potential issues**

I'm thinking about a few potential issues with the help command exiting before configuring logging, and the debugging not providing output. Then there’s structured logging with JSON and verbosity toggling to DEBUG. Since the default is WARNING, I still get unparsed warnings in JSON. I'm also considering improving the "generated_at" output. Maybe I need to check date formats. Additionally, I wonder if parsing tests for thresholds should be enforced, but it might not be necessary. There's also an indentation issue to resolve.
**Considering PowerShell checks**

I'm thinking it might be a good idea to run a PowerShell static check to extract regex patterns, but not using Python. I wonder if I could use a package that might be installed via uv. I need to search for "python" in uv because maybe it could help. Also, should I use the command "uv run python"? I’ll need to check the available commands to ensure I’m on the right track.
codex
The scripts are within line limits. I’ll check for alternate Python runners like `uv` before finalizing.
exec
powershell.exe -Command 'Get-Command uv -ErrorAction SilentlyContinue | Format-List *; Get-Command rye -ErrorAction SilentlyContinue | Format-List *; Get-Command hatch -ErrorAction SilentlyContinue | Format-List *; Get-Command conda -ErrorAction SilentlyContinue | Format-List *' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\codex\task-V1-knowledge-decay-report
2026-04-25T07:39:47.026988Z ERROR codex_core::tools::router: error={"output":"","metadata":{"exit_code":1,"duration_seconds":1.2}}
 exited 1 in 1194ms:
diff --git a/.claude/scripts/knowledge-decay-report.py b/.claude/scripts/knowledge-decay-report.py
new file mode 100644
index 0000000000000000000000000000000000000000..145c275c929084d0d84834375b0241c46b4effdc
--- /dev/null
+++ b/.claude/scripts/knowledge-decay-report.py
@@ -0,0 +1,283 @@
+#!/usr/bin/env python3
+"""Audit knowledge.md entries by verification age tier."""
+import argparse
+import json
+import logging
+import re
+import sys
+from datetime import date
+from pathlib import Path
+
+
+TIERS = ("active", "warm", "cold", "archive", "unparsed")
+DEFAULT_THRESHOLDS = (14, 30, 90)
+ENTRY_RE = re.compile(r"^###\s+(.+?)\s+\((\d{4}-\d{2}-\d{2}),\s*verified:\s*(\d{4}-\d{2}-\d{2})\)\s*$")
+HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
+
+
+class JsonFormatter(logging.Formatter):
+    def format(self, record):
+        payload = {
+            "level": record.levelname,
+            "message": record.getMessage(),
+            "logger": record.name,
+        }
+        if record.exc_info:
+            payload["exc_info"] = self.formatException(record.exc_info)
+        for key, value in getattr(record, "context", {}).items():
+            payload[key] = value
+        return json.dumps(payload, sort_keys=True)
+
+
+logger = logging.getLogger("knowledge_decay_report")
+
+
+def configure_logging(verbose):
+    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
+    handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(JsonFormatter())
+    root = logging.getLogger()
+    root.handlers.clear()
+    root.addHandler(handler)
+    root.setLevel(logging.DEBUG if verbose else logging.WARNING)
+    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})
+
+
+def parse_args(argv):
+    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
+    parser = argparse.ArgumentParser(description="Audit .claude/memory/knowledge.md verification decay tiers.")
+    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
+    parser.add_argument("--knowledge-path", default=".claude/memory/knowledge.md", help="Path to knowledge.md.")
+    parser.add_argument("--today", help="Override today's date as YYYY-MM-DD.")
+    group = parser.add_mutually_exclusive_group()
+    group.add_argument("--include-gotchas", action="store_true", help="Include Gotchas section entries (default).")
+    group.add_argument("--patterns-only", action="store_true", help="Only include Patterns section entries.")
+    parser.add_argument("--threshold-days", default="14,30,90", help="Comma-separated active,warm,cold day cutoffs.")
+    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG structured logs on stderr.")
+    args = parser.parse_args(argv)
+    logger.debug("exit", extra={"context": {"function": "parse_args", "json": args.json}})
+    return args
+
+
+def parse_thresholds(value):
+    logger.debug("entry", extra={"context": {"function": "parse_thresholds", "value": value}})
+    try:
+        parts = tuple(int(part.strip()) for part in value.split(","))
+        if len(parts) != 3 or parts[0] < 0 or not (parts[0] < parts[1] < parts[2]):
+            raise ValueError("thresholds must be three increasing non-negative integers")
+        logger.debug("exit", extra={"context": {"function": "parse_thresholds", "thresholds": parts}})
+        return parts
+    except ValueError:
+        logger.exception("invalid_thresholds", extra={"context": {"function": "parse_thresholds", "value": value}})
+        raise
+
+
+def parse_today(value):
+    logger.debug("entry", extra={"context": {"function": "parse_today", "provided": bool(value)}})
+    try:
+        result = date.fromisoformat(value) if value else date.today()
+        logger.debug("exit", extra={"context": {"function": "parse_today", "today": result.isoformat()}})
+        return result
+    except ValueError:
+        logger.exception("invalid_today", extra={"context": {"function": "parse_today", "value": value}})
+        raise
+
+
+def classify_age(age_days, thresholds):
+    logger.debug("entry", extra={"context": {"function": "classify_age", "age_days": age_days}})
+    active, warm, cold = thresholds
+    if age_days <= active:
+        tier = "active"
+    elif age_days <= warm:
+        tier = "warm"
+    elif age_days <= cold:
+        tier = "cold"
+    else:
+        tier = "archive"
+    logger.debug("exit", extra={"context": {"function": "classify_age", "tier": tier}})
+    return tier
+
+
+def blank_report(today_value):
+    logger.debug("entry", extra={"context": {"function": "blank_report", "today": today_value.isoformat()}})
+    result = {
+        "generated_at": date.today().isoformat(),
+        "today": today_value.isoformat(),
+        "tiers": {tier: [] for tier in TIERS},
+        "summary": {tier: 0 for tier in TIERS},
+        "promotion_candidates": [],
+    }
+    result["summary"]["total"] = 0
+    logger.debug("exit", extra={"context": {"function": "blank_report"}})
+    return result
+
+
+def extract_name(line):
+    logger.debug("entry", extra={"context": {"function": "extract_name"}})
+    text = line[4:].strip()
+    name = text.split(" (", 1)[0].strip() or text[:80]
+    logger.debug("exit", extra={"context": {"function": "extract_name", "name": name}})
+    return name
+
+
+def parse_entry_line(line, line_no, today_value, thresholds):
+    logger.debug("entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+    match = ENTRY_RE.match(line)
+    if not match:
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.warning("unparsed_entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+    try:
+        name, created_text, verified_text = match.groups()
+        created = date.fromisoformat(created_text)
+        verified = date.fromisoformat(verified_text)
+        age_days = (today_value - verified).days
+        tier = classify_age(age_days, thresholds)
+        entry = {
+            "name": name,
+            "verified": verified.isoformat(),
+            "created": created.isoformat(),
+            "age_days": age_days,
+            "tier": tier,
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": tier}})
+        return entry
+    except ValueError:
+        logger.exception("malformed_entry_dates", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+
+
+def iter_relevant_lines(text, include_gotchas):
+    logger.debug("entry", extra={"context": {"function": "iter_relevant_lines", "include_gotchas": include_gotchas}})
+    section = None
+    for line_no, line in enumerate(text.splitlines(), start=1):
+        heading = HEADING_RE.match(line)
+        if heading:
+            title = heading.group(1).strip().lower()
+            section = title if title in {"patterns", "gotchas"} else None
+            continue
+        if line.startswith("### ") and section == "patterns":
+            yield line_no, line
+        elif line.startswith("### ") and section == "gotchas" and include_gotchas:
+            yield line_no, line
+    logger.debug("exit", extra={"context": {"function": "iter_relevant_lines"}})
+
+
+def detect_promotion_candidates(report, knowledge_path):
+    logger.debug("entry", extra={"context": {"function": "detect_promotion_candidates", "path": str(knowledge_path)}})
+    try:
+        active_path = knowledge_path.parent / "activeContext.md"
+        if not active_path.exists():
+            logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": 0}})
+            return []
+        active_text = active_path.read_text(encoding="utf-8", errors="replace").lower()
+        candidates = []
+        for tier in ("warm", "cold", "archive"):
+            for entry in report["tiers"][tier]:
+                if entry["name"].lower() in active_text:
+                    candidates.append(entry)
+        logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": len(candidates)}})
+        return candidates
+    except OSError:
+        logger.exception("active_context_read_failed", extra={"context": {"function": "detect_promotion_candidates"}})
+        return []
+
+
+def make_report(knowledge_path, today_value, include_gotchas, thresholds):
+    logger.debug("entry", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+    report = blank_report(today_value)
+    try:
+        text = Path(knowledge_path).read_text(encoding="utf-8", errors="replace")
+    except OSError:
+        logger.exception("knowledge_read_failed", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+        raise
+    for line_no, line in iter_relevant_lines(text, include_gotchas):
+        entry = parse_entry_line(line, line_no, today_value, thresholds)
+        report["tiers"][entry["tier"]].append(entry)
+    for tier in TIERS:
+        report["summary"][tier] = len(report["tiers"][tier])
+    report["summary"]["total"] = sum(report["summary"][tier] for tier in TIERS)
+    report["promotion_candidates"] = detect_promotion_candidates(report, Path(knowledge_path))
+    logger.debug("exit", extra={"context": {"function": "make_report", "total": report["summary"]["total"]}})
+    return report
+
+
+def format_entry(entry):
+    logger.debug("entry", extra={"context": {"function": "format_entry", "tier": entry["tier"]}})
+    if entry["tier"] == "unparsed":
+        text = f"* {entry['name']} (line={entry['line_no']})"
+    else:
+        text = f"* {entry['name']} ({entry['verified']}, age={entry['age_days']}d)"
+    result = text[:80]
+    logger.debug("exit", extra={"context": {"function": "format_entry", "length": len(result)}})
+    return result
+
+
+def format_text_report(report):
+    logger.debug("entry", extra={"context": {"function": "format_text_report", "total": report["summary"]["total"]}})
+    lines = [
+        "Tier    | Count | Entries (truncated to first 80 chars)",
+        "--------+-------+-----------------------------------------",
+    ]
+    for tier in TIERS:
+        entries = report["tiers"][tier]
+        first = format_entry(entries[0]) if entries else ""
+        lines.append(f"{tier:<8}| {len(entries):^5} | {first}")
+        for entry in entries[1:]:
+            lines.append(f"{'':8}  {'':5}   {format_entry(entry)}")
+    lines.append(f"Total   | {report['summary']['total']:^5} |")
+    lines.extend(["", "## Age histogram"])
+    for tier in TIERS:
+        lines.append(f"{tier}: {report['summary'][tier]}")
+    candidates = report["promotion_candidates"]
+    lines.extend(["", f"## Promotion candidates ({len(candidates)}):"])
+    for entry in candidates:
+        lines.append(format_entry(entry))
+    result = "\n".join(lines)
+    logger.debug("exit", extra={"context": {"function": "format_text_report", "length": len(result)}})
+    return result
+
+
+def main(argv=None):
+    if argv is None:
+        argv = sys.argv[1:]
+    args = parse_args(argv)
+    configure_logging(args.verbose)
+    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
+    try:
+        today_value = parse_today(args.today)
+        thresholds = parse_thresholds(args.threshold_days)
+        data = make_report(Path(args.knowledge_path), today_value, not args.patterns_only, thresholds)
+        if args.json:
+            print(json.dumps(data, indent=2, sort_keys=True))
+        else:
+            print(format_text_report(data))
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 0}})
+        return 0
+    except (OSError, ValueError) as exc:
+        logger.exception("fatal_error", extra={"context": {"function": "main"}})
+        print(f"error: {exc}", file=sys.stderr)
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 2}})
+        return 2
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/.claude/scripts/test_knowledge_decay_report.py b/.claude/scripts/test_knowledge_decay_report.py
new file mode 100644
index 0000000000000000000000000000000000000000..f5e06729bb3a550ff345b4cf8b883c350128a62a
--- /dev/null
+++ b/.claude/scripts/test_knowledge_decay_report.py
@@ -0,0 +1,83 @@
+import importlib.util
+import json
+import tempfile
+import unittest
+from datetime import date
+from pathlib import Path
+
+
+SCRIPT_PATH = Path(__file__).with_name("knowledge-decay-report.py")
+SPEC = importlib.util.spec_from_file_location("knowledge_decay_report", SCRIPT_PATH)
+report = importlib.util.module_from_spec(SPEC)
+SPEC.loader.exec_module(report)
+
+
+def write_memory(root, knowledge_text, active_text=None):
+    memory = Path(root) / ".claude" / "memory"
+    memory.mkdir(parents=True)
+    knowledge_path = memory / "knowledge.md"
+    knowledge_path.write_text(knowledge_text, encoding="utf-8")
+    if active_text is not None:
+        (memory / "activeContext.md").write_text(active_text, encoding="utf-8")
+    return knowledge_path
+
+
+class KnowledgeDecayReportTests(unittest.TestCase):
+    def make_report(self, text, today="2026-04-25", active_text=None, include_gotchas=True):
+        with tempfile.TemporaryDirectory() as root:
+            knowledge_path = write_memory(root, text, active_text)
+            return report.make_report(
+                knowledge_path,
+                date.fromisoformat(today),
+                include_gotchas,
+                (14, 30, 90),
+            )
+
+    def test_fresh_entry_active(self):
+        data = self.make_report("## Patterns\n### Fresh (2026-04-20, verified: 2026-04-20)\n")
+        self.assertEqual(data["tiers"]["active"][0]["tier"], "active")
+
+    def test_twenty_days_warm(self):
+        data = self.make_report("## Patterns\n### Warm One (2026-04-05, verified: 2026-04-05)\n")
+        self.assertEqual(data["summary"]["warm"], 1)
+
+    def test_sixty_days_cold(self):
+        data = self.make_report("## Patterns\n### Cold One (2026-02-24, verified: 2026-02-24)\n")
+        self.assertEqual(data["tiers"]["cold"][0]["age_days"], 60)
+
+    def test_hundred_twenty_days_archive(self):
+        data = self.make_report("## Patterns\n### Old One (2025-12-26, verified: 2025-12-26)\n")
+        self.assertEqual(data["summary"]["archive"], 1)
+
+    def test_missing_verified_unparsed(self):
+        data = self.make_report("## Patterns\n### Missing Verified (2026-01-01)\n")
+        self.assertEqual(data["tiers"]["unparsed"][0]["tier"], "unparsed")
+
+    def test_today_override_applied(self):
+        data = self.make_report("## Patterns\n### Override (2026-04-01, verified: 2026-04-01)\n", today="2026-04-08")
+        self.assertEqual(data["tiers"]["active"][0]["age_days"], 7)
+
+    def test_patterns_only_excludes_gotchas(self):
+        text = "## Patterns\n### Pattern A (2026-04-20, verified: 2026-04-20)\n## Gotchas\n### Gotcha A (2026-04-20, verified: 2026-04-20)\n"
+        data = self.make_report(text, include_gotchas=False)
+        self.assertEqual(data["summary"]["total"], 1)
+        self.assertEqual(data["tiers"]["active"][0]["name"], "Pattern A")
+
+    def test_json_schema_round_trip(self):
+        data = self.make_report("## Patterns\n### Json One (2026-04-20, verified: 2026-04-20)\n")
+        loaded = json.loads(json.dumps(data))
+        self.assertEqual(set(["generated_at", "today", "tiers", "summary"]).issubset(loaded), True)
+        self.assertEqual(set(loaded["tiers"]["active"][0]), set(["name", "verified", "created", "age_days", "tier", "line_no"]))
+
+    def test_promotion_candidate_detection(self):
+        text = "## Patterns\n### Promote Me (2026-04-01, verified: 2026-04-01)\n"
+        data = self.make_report(text, active_text="We should revisit promote me today.")
+        self.assertEqual(data["promotion_candidates"][0]["name"], "Promote Me")
+
+    def test_empty_knowledge_total_zero(self):
+        data = self.make_report("")
+        self.assertEqual(data["summary"]["total"], 0)
+
+
+if __name__ == "__main__":
+    unittest.main()

codex
No alternate runner is available. I’ll do a final diff check and inspect the changed files.
exec
powershell.exe -Command 'git diff --check; Write-Output "DIFF_CHECK_EXIT=$LASTEXITCODE"; git diff -- .claude/scripts/knowledge-decay-report.py .claude/scripts/test_knowledge_decay_report.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\codex\task-V1-knowledge-decay-report
2026-04-25T07:39:54.184127Z ERROR codex_core::tools::router: error={"output":"Total output lines: 483\n\nDIFF_CHECK_EXIT=129\r\ndiff --git a/.claude/scripts/knowledge-decay-report.py b/.claude/scripts/test_knowledge_decay_report.py\nindex 145c275..f5e0672 100644\n--- a/.claude/scripts/knowledge-decay-report.py\n+++ b/.claude/scripts/test_knowledge_decay_report.py\n@@ -1,283 +1,83 @@\n-#!/usr/bin/env python3\n-\"\"\"Audit knowledge.md entries by verification age tier.\"\"\"\n-import argparse\n+import importlib.util\n import json\n-import logging\n-import re\n-import sys\n+import tempfile\n+import unittest\n from datetime import date\n from pathlib import Path\n \n \n-TIERS = (\"active\", \"warm\", \"cold\", \"archive\", \"unparsed\")\n-DEFAULT_THRESHOLDS = (14, 30, 90)\n-ENTRY_RE = re.compile(r\"^###\\s+(.+?)\\s+\\((\\d{4}-\\d{2}-\\d{2}),\\s*verified:\\s*(\\d{4}-\\d{2}-\\d{2})\\)\\s*$\")\n-HEADING_RE = re.compile(r\"^##\\s+(.+?)\\s*$\")\n+SCRIPT_PATH = Path(__file__).with_name(\"knowledge-decay-report.py\")\n+SPEC = importlib.util.spec_from_file_location(\"knowledge_decay_report\", SCRIPT_PATH)\n+report = importlib.util.module_from_spec(SPEC)\n+SPEC.loader.exec_module(report)\n \n \n-class JsonFormatter(logging.Formatter):\n-    def format(self, record):\n-        payload = {\n-            \"level\": record.levelname,\n-            \"message\": record.getMessage(),\n-            \"logger\": record.name,\n-        }\n-        if record.exc_info:\n-            payload[\"exc_info\"] = self.formatException(record.exc_info)\n-        for key, value in getattr(record, \"context\", {}).items():\n-            payload[key] = value\n-        return json.dumps(payload, sort_keys=True)\n+def write_memory(root, knowledge_text, active_text=None):\n+    memory = Path(root) / \".claude\" / \"memory\"\n+    memory.mkdir(parents=True)\n+    knowledge_path = memory / \"knowledge.md\"\n+    knowledge_path.write_text(knowledge_text, encoding=\"utf-8\")\n+    if active_text is not None:\n+        (memory / \"activeContext.md\").write_text(active_text, encoding=\"utf-8\")\n+    return knowledge_path\n \n \n-logger = logging.getLogger(\"knowledge_decay_report\")\n+class KnowledgeDecayReportTests(unittest.TestCase):\n+    def make_report(self, text, today=\"2026-04-25\", active_text=None, include_gotchas=True):\n+        with tempfile.TemporaryDirectory() as root:\n+            knowledge_path = write_memory(root, text, active_text)\n+            return report.make_report(\n+                knowledge_path,\n+                date.fromisoformat(today),\n+                include_gotchas,\n+                (14, 30, 90),\n+            )\n \n+    def test_fresh_entry_active(self):\n+        data = self.make_report(\"## Patterns\\n### Fresh (2026-04-20, verified: 2026-04-20)\\n\")\n+        self.assertEqual(data[\"tiers\"][\"active\"][0][\"tier\"], \"active\")\n \n-def configure_logging(verbose):\n-    logger.debug(\"entry\", extra={\"context\": {\"function\": \"configure_logging\", \"verbose\": verbose}})\n-    handler = logging.StreamHandler(sys.stderr)\n-    handler.setFormatter(JsonFormatter())\n-    root = logging.getLogger()\n-    root.handlers.clear()\n-    root.addHandler(handler)\n-    root.setLevel(logging.DEBUG if verbose else logging.WARNING)\n-    logger.debug(\"exit\", extra={\"context\": {\"function\": \"configure_logging\", \"level\": root.level}})\n+    def test_twenty_days_warm(self):\n+        data = self.make_report(\"## Patterns\\n### Warm One (2026-04-05, verified: 2026-04-05)\\n\")\n+        self.assertEqual(data[\"summary\"][\"warm\"], 1)\n \n+    def test_sixty_days_cold(self):\n+        data = self.make_report(\"## Patterns\\n### Cold One (2026-02-24, verified: 2026-02-24)\\n\")\n+        self.assertEqual(data[\"tiers\"][\"cold\"][0][\"age_days\"], 60)\n \n-def parse_args(argv):\n-    logger.debug(\"entry\", extra={\"context\": {\"function\": \"parse_args\", \"argc\": len(argv)}})\n-    parser = argparse.ArgumentParser(description=\"Audit .claude/memory/knowledge.md verification decay tiers.\")\n-    parser.add_argument(\"--json\", action=\"store_true\", help=\"Emit machine-readable JSON.\")\n-    parser.add_argument(\"--knowledge-path\", default=\".claude/memory/knowledge.md\", help=\"Path to knowledge.md.\")\n-    parser.add_argument(\"--today\", help=\"Override today's date as YYYY-MM-DD.\")\n-    group = parser.add_mutually_exclusive_group()\n-    group.add_argument(\"--include-gotchas\", action=\"store_true\", help=\"Include Gotchas section entries (default).\")\n-    group.add_argument(\"--patterns-only\", action=\"store_true\", help=\"Only include Patterns section entries.\")\n-    parser.add_argument(\"--threshold-days\", default=\"14,30,90\", help=\"Comma-separated active,warm,cold day cutoffs.\")\n-    parser.add_argument(\"--verbose\", action=\"store_true\", help=\"Enable DEBUG structured logs on stderr.\")\n-    args = parser.parse_args(argv)\n-    logger.debug(\"exit\", extra={\"context\": {\"function\": \"parse_args\", \"json\": args.json}})\n-    return args\n+    def test_hundred_twenty_days_archive(self):\n+        data = self.make_report(\"## Patterns\\n### Old One (2025-12-26, verified: 2025-12-26)\\n\")\n+        self.assertEqual(data[\"summary\"][\"archive\"], 1)\n \n+    def test_missing_verified_unparsed(self):\n+        data = self.make_report(\"## Patterns\\n### Missing Verified …14150 chars truncated… prefix\n    --default-prefix      use default prefixes a/ and b/\n    --inter-hunk-context <n>\n                          show context between diff hunks up to the specified number of lines\n    --output-indicator-new <char>\n                          specify the character to indicate a new line instead of '+'\n    --output-indicator-old <char>\n                          specify the character to indicate an old line instead of '-'\n    --output-indicator-context <char>\n                          specify the character to indicate a context instead of ' '\n\nDiff rename options\n    -B, --break-rewrites[=<n>[/<m>]]\n                          break complete rewrite changes into pairs of delete and create\n    -M, --find-renames[=<n>]\n                          detect renames\n    -D, --irreversible-delete\n                          omit the preimage for deletes\n    -C, --find-copies[=<n>]\n                          detect copies\n    --[no-]find-copies-harder\n                          use unmodified files as source to find copies\n    --no-renames          disable rename detection\n    --[no-]rename-empty   use empty blobs as rename source\n    --[no-]follow         continue listing the history of a file beyond renames\n    -l <n>                prevent rename/copy detection if the number of rename/copy targets exceeds given limit\n\nDiff algorithm options\n    --minimal             produce the smallest possible diff\n    -w, --ignore-all-space\n                          ignore whitespace when comparing lines\n    -b, --ignore-space-change\n                          ignore changes in amount of whitespace\n    --ignore-space-at-eol ignore changes in whitespace at EOL\n    --ignore-cr-at-eol    ignore carrier-return at the end of line\n    --ignore-blank-lines  ignore changes whose lines are all blank\n    -I, --[no-]ignore-matching-lines <regex>\n                          ignore changes whose all lines match <regex>\n    --[no-]indent-heuristic\n                          heuristic to shift diff hunk boundaries for easy reading\n    --patience            generate diff using the \"patience diff\" algorithm\n    --histogram           generate diff using the \"histogram diff\" algorithm\n    --diff-algorithm <algorithm>\n                          choose a diff algorithm\n    --anchored <text>     generate diff using the \"anchored diff\" algorithm\n    --word-diff[=<mode>]  show word diff, using <mode> to delimit changed words\n    --word-diff-regex <regex>\n                          use <regex> to decide what a word is\n    --color-words[=<regex>]\n                          equivalent to --word-diff=color --word-diff-regex=<regex>\n    --[no-]color-moved[=<mode>]\n                          moved lines of code are colored differently\n    --[no-]color-moved-ws <mode>\n                          how white spaces are ignored in --color-moved\n\nOther diff options\n    --[no-]relative[=<prefix>]\n                          when run from subdir, exclude changes outside and show relative paths\n    -a, --[no-]text       treat all files as text\n    -R                    swap two inputs, reverse the diff\n    --[no-]exit-code      exit with 1 if there were differences, 0 otherwise\n    --[no-]quiet          disable all output of the program\n    --[no-]ext-diff       allow an external diff helper to be executed\n    --[no-]textconv       run external text conversion filters when comparing binary files\n    --ignore-submodules[=<when>]\n                          ignore changes to submodules in the diff generation\n    --submodule[=<format>]\n                          specify how differences in submodules are shown\n    --ita-invisible-in-index\n                          hide 'git add -N' entries from the index\n    --ita-visible-in-index\n                          treat 'git add -N' entries as real in the index\n    -S <string>           look for differences that change the number of occurrences of the specified string\n    -G <regex>            look for differences that change the number of occurrences of the specified regex\n    --pickaxe-all         show all changes in the changeset with -S or -G\n    --pickaxe-regex       treat <string> in -S as extended POSIX regular expression\n    -O <file>             control the order in which files appear in the output\n    --rotate-to <path>    show the change in the specified path first\n    --skip-to <path>      skip the output to the specified path\n    --find-object <object-id>\n                          look for differences that change the number of occurrences of the specified object\n    --diff-filter [(A|C|D|M|R|T|U|X|B)...[*]]\n                          select files by diff type\n    --max-depth <depth>   maximum tree depth to recurse\n    --output <file>       output to a specific file\n\nwarning: in the working copy of '.claude/scripts/knowledge-decay-report.py', LF will be replaced by CRLF the next time Git touches it\nwarning: in the working copy of '.claude/scripts/test_knowledge_decay_report.py', LF will be replaced by CRLF the next time Git touches it\n","metadata":{"exit_code":1,"duration_seconds":0.4}}
 exited 1 in 426ms:
DIFF_CHECK_EXIT=129
diff --git a/.claude/scripts/knowledge-decay-report.py b/.claude/scripts/test_knowledge_decay_report.py
index 145c275..f5e0672 100644
--- a/.claude/scripts/knowledge-decay-report.py
+++ b/.claude/scripts/test_knowledge_decay_report.py
@@ -1,283 +1,83 @@
-#!/usr/bin/env python3
-"""Audit knowledge.md entries by verification age tier."""
-import argparse
+import importlib.util
 import json
-import logging
-import re
-import sys
+import tempfile
+import unittest
 from datetime import date
 from pathlib import Path
 
 
-TIERS = ("active", "warm", "cold", "archive", "unparsed")
-DEFAULT_THRESHOLDS = (14, 30, 90)
-ENTRY_RE = re.compile(r"^###\s+(.+?)\s+\((\d{4}-\d{2}-\d{2}),\s*verified:\s*(\d{4}-\d{2}-\d{2})\)\s*$")
-HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
+SCRIPT_PATH = Path(__file__).with_name("knowledge-decay-report.py")
+SPEC = importlib.util.spec_from_file_location("knowledge_decay_report", SCRIPT_PATH)
+report = importlib.util.module_from_spec(SPEC)
+SPEC.loader.exec_module(report)
 
 
-class JsonFormatter(logging.Formatter):
-    def format(self, record):
-        payload = {
-            "level": record.levelname,
-            "message": record.getMessage(),
-            "logger": record.name,
-        }
-        if record.exc_info:
-            payload["exc_info"] = self.formatException(record.exc_info)
-        for key, value in getattr(record, "context", {}).items():
-            payload[key] = value
-        return json.dumps(payload, sort_keys=True)
+def write_memory(root, knowledge_text, active_text=None):
+    memory = Path(root) / ".claude" / "memory"
+    memory.mkdir(parents=True)
+    knowledge_path = memory / "knowledge.md"
+    knowledge_path.write_text(knowledge_text, encoding="utf-8")
+    if active_text is not None:
+        (memory / "activeContext.md").write_text(active_text, encoding="utf-8")
+    return knowledge_path
 
 
-logger = logging.getLogger("knowledge_decay_report")
+class KnowledgeDecayReportTests(unittest.TestCase):
+    def make_report(self, text, today="2026-04-25", active_text=None, include_gotchas=True):
+        with tempfile.TemporaryDirectory() as root:
+            knowledge_path = write_memory(root, text, active_text)
+            return report.make_report(
+                knowledge_path,
+                date.fromisoformat(today),
+                include_gotchas,
+                (14, 30, 90),
+            )
 
+    def test_fresh_entry_active(self):
+        data = self.make_report("## Patterns\n### Fresh (2026-04-20, verified: 2026-04-20)\n")
+        self.assertEqual(data["tiers"]["active"][0]["tier"], "active")
 
-def configure_logging(verbose):
-    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
-    handler = logging.StreamHandler(sys.stderr)
-    handler.setFormatter(JsonFormatter())
-    root = logging.getLogger()
-    root.handlers.clear()
-    root.addHandler(handler)
-    root.setLevel(logging.DEBUG if verbose else logging.WARNING)
-    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})
+    def test_twenty_days_warm(self):
+        data = self.make_report("## Patterns\n### Warm One (2026-04-05, verified: 2026-04-05)\n")
+        self.assertEqual(data["summary"]["warm"], 1)
 
+    def test_sixty_days_cold(self):
+        data = self.make_report("## Patterns\n### Cold One (2026-02-24, verified: 2026-02-24)\n")
+        self.assertEqual(data["tiers"]["cold"][0]["age_days"], 60)
 
-def parse_args(argv):
-    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
-    parser = argparse.ArgumentParser(description="Audit .claude/memory/knowledge.md verification decay tiers.")
-    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
-    parser.add_argument("--knowledge-path", default=".claude/memory/knowledge.md", help="Path to knowledge.md.")
-    parser.add_argument("--today", help="Override today's date as YYYY-MM-DD.")
-    group = parser.add_mutually_exclusive_group()
-    group.add_argument("--include-gotchas", action="store_true", help="Include Gotchas section entries (default).")
-    group.add_argument("--patterns-only", action="store_true", help="Only include Patterns section entries.")
-    parser.add_argument("--threshold-days", default="14,30,90", help="Comma-separated active,warm,cold day cutoffs.")
-    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG structured logs on stderr.")
-    args = parser.parse_args(argv)
-    logger.debug("exit", extra={"context": {"function": "parse_args", "json": args.json}})
-    return args
+    def test_hundred_twenty_days_archive(self):
+        data = self.make_report("## Patterns\n### Old One (2025-12-26, verified: 2025-12-26)\n")
+        self.assertEqual(data["summary"]["archive"], 1)
 
+    def test_missing_verified_unparsed(self):
+        data = self.make_report("## Patterns\n### Missing Verified (2026-01-01)\n")
+        self.assertEqual(data["tiers"]["unparsed"][0]["tier"], "unparsed")
 
-def parse_thresholds(value):
-    logger.debug("entry", extra={"context": {"function": "parse_thresholds", "value": value}})
-    try:
-        parts = tuple(int(part.strip()) for part in value.split(","))
-        if len(parts) != 3 or parts[0] < 0 or not (parts[0] < parts[1] < parts[2]):
-            raise ValueError("thresholds must be three increasing non-negative integers")
-        logger.debug("exit", extra={"context": {"function": "parse_thresholds", "thresholds": parts}})
-        return parts
-    except ValueError:
-        logger.exception("invalid_thresholds", extra={"context": {"function": "parse_thresholds", "value": value}})
-        raise
+    def test_today_override_applied(self):
+        data = self.make_report("## Patterns\n### Override (2026-04-01, verified: 2026-04-01)\n", today="2026-04-08")
+        self.assertEqual(data["tiers"]["active"][0]["age_days"], 7)
 
+    def test_patterns_only_excludes_gotchas(self):
+        text = "## Patterns\n### Pattern A (2026-04-20, verified: 2026-04-20)\n## Gotchas\n### Gotcha A (2026-04-20, verified: 2026-04-20)\n"
+        data = self.make_report(text, include_gotchas=False)
+        self.assertEqual(data["summary"]["total"], 1)
+        self.assertEqual(data["tiers"]["active"][0]["name"], "Pattern A")
 
-def parse_today(value):
-    logger.debug("entry", extra={"context": {"function": "parse_today", "provided": bool(value)}})
-    try:
-        result = date.fromisoformat(value) if value else date.today()
-        logger.debug("exit", extra={"context": {"function": "parse_today", "today": result.isoformat()}})
-        return result
-    except ValueError:
-        logger.exception("invalid_today", extra={"context": {"function": "parse_today", "value": value}})
-        raise
+    def test_json_schema_round_trip(self):
+        data = self.make_report("## Patterns\n### Json One (2026-04-20, verified: 2026-04-20)\n")
+        loaded = json.loads(json.dumps(data))
+        self.assertEqual(set(["generated_at", "today", "tiers", "summary"]).issubset(loaded), True)
+        self.assertEqual(set(loaded["tiers"]["active"][0]), set(["name", "verified", "created", "age_days", "tier", "line_no"]))
 
+    def test_promotion_candidate_detection(self):
+        text = "## Patterns\n### Promote Me (2026-04-01, verified: 2026-04-01)\n"
+        data = self.make_report(text, active_text="We should revisit promote me today.")
+        self.assertEqual(data["promotion_candidates"][0]["name"], "Promote Me")
 
-def classify_age(age_days, thresholds):
-    logger.debug("entry", extra={"context": {"function": "classify_age", "age_days": age_days}})
-    active, warm, cold = thresholds
-    if age_days <= active:
-        tier = "active"
-    elif age_days <= warm:
-        tier = "warm"
-    elif age_days <= cold:
-        tier = "cold"
-    else:
-        tier = "archive"
-    logger.debug("exit", extra={"context": {"function": "classify_age", "tier": tier}})
-    return tier
-
-
-def blank_report(today_value):
-    logger.debug("entry", extra={"context": {"function": "blank_report", "today": today_value.isoformat()}})
-    result = {
-        "generated_at": date.today().isoformat(),
-        "today": today_value.isoformat(),
-        "tiers": {tier: [] for tier in TIERS},
-        "summary": {tier: 0 for tier in TIERS},
-        "promotion_candidates": [],
-    }
-    result["summary"]["total"] = 0
-    logger.debug("exit", extra={"context": {"function": "blank_report"}})
-    return result
-
-
-def extract_name(line):
-    logger.debug("entry", extra={"context": {"function": "extract_name"}})
-    text = line[4:].strip()
-    name = text.split(" (", 1)[0].strip() or text[:80]
-    logger.debug("exit", extra={"context": {"function": "extract_name", "name": name}})
-    return name
-
-
-def parse_entry_line(line, line_no, today_value, thresholds):
-    logger.debug("entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
-    match = ENTRY_RE.match(line)
-    if not match:
-        entry = {
-            "name": extract_name(line),
-            "verified": None,
-            "created": None,
-            "age_days": None,
-            "tier": "unparsed",
-            "line_no": line_no,
-        }
-        logger.warning("unparsed_entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
-        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
-        return entry
-    try:
-        name, created_text, verified_text = match.groups()
-        created = date.fromisoformat(created_text)
-        verified = date.fromisoformat(verified_text)
-        age_days = (today_value - verified).days
-        tier = classify_age(age_days, thresholds)
-        entry = {
-            "name": name,
-            "verified": verified.isoformat(),
-            "created": created.isoformat(),
-            "age_days": age_days,
-            "tier": tier,
-            "line_no": line_no,
-        }
-        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": tier}})
-        return entry
-    except ValueError:
-        logger.exception("malformed_entry_dates", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
-        entry = {
-            "name": extract_name(line),
-            "verified": None,
-            "created": None,
-            "age_days": None,
-            "tier": "unparsed",
-            "line_no": line_no,
-        }
-        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
-        return entry
-
-
-def iter_relevant_lines(text, include_gotchas):
-    logger.debug("entry", extra={"context": {"function": "iter_relevant_lines", "include_gotchas": include_gotchas}})
-    section = None
-    for line_no, line in enumerate(text.splitlines(), start=1):
-        heading = HEADING_RE.match(line)
-        if heading:
-            title = heading.group(1).strip().lower()
-            section = title if title in {"patterns", "gotchas"} else None
-            continue
-        if line.startswith("### ") and section == "patterns":
-            yield line_no, line
-        elif line.startswith("### ") and section == "gotchas" and include_gotchas:
-            yield line_no, line
-    logger.debug("exit", extra={"context": {"function": "iter_relevant_lines"}})
-
-
-def detect_promotion_candidates(report, knowledge_path):
-    logger.debug("entry", extra={"context": {"function": "detect_promotion_candidates", "path": str(knowledge_path)}})
-    try:
-        active_path = knowledge_path.parent / "activeContext.md"
-        if not active_path.exists():
-            logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": 0}})
-            return []
-        active_text = active_path.read_text(encoding="utf-8", errors="replace").lower()
-        candidates = []
-        for tier in ("warm", "cold", "archive"):
-            for entry in report["tiers"][tier]:
-                if entry["name"].lower() in active_text:
-                    candidates.append(entry)
-        logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": len(candidates)}})
-        return candidates
-    except OSError:
-        logger.exception("active_context_read_failed", extra={"context": {"function": "detect_promotion_candidates"}})
-        return []
-
-
-def make_report(knowledge_path, today_value, include_gotchas, thresholds):
-    logger.debug("entry", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
-    report = blank_report(today_value)
-    try:
-        text = Path(knowledge_path).read_text(encoding="utf-8", errors="replace")
-    except OSError:
-        logger.exception("knowledge_read_failed", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
-        raise
-    for line_no, line in iter_relevant_lines(text, include_gotchas):
-        entry = parse_entry_line(line, line_no, today_value, thresholds)
-        report["tiers"][entry["tier"]].append(entry)
-    for tier in TIERS:
-        report["summary"][tier] = len(report["tiers"][tier])
-    report["summary"]["total"] = sum(report["summary"][tier] for tier in TIERS)
-    report["promotion_candidates"] = detect_promotion_candidates(report, Path(knowledge_path))
-    logger.debug("exit", extra={"context": {"function": "make_report", "total": report["summary"]["total"]}})
-    return report
-
-
-def format_entry(entry):
-    logger.debug("entry", extra={"context": {"function": "format_entry", "tier": entry["tier"]}})
-    if entry["tier"] == "unparsed":
-        text = f"* {entry['name']} (line={entry['line_no']})"
-    else:
-        text = f"* {entry['name']} ({entry['verified']}, age={entry['age_days']}d)"
-    result = text[:80]
-    logger.debug("exit", extra={"context": {"function": "format_entry", "length": len(result)}})
-    return result
-
-
-def format_text_report(report):
-    logger.debug("entry", extra={"context": {"function": "format_text_report", "total": report["summary"]["total"]}})
-    lines = [
-        "Tier    | Count | Entries (truncated to first 80 chars)",
-        "--------+-------+-----------------------------------------",
-    ]
-    for tier in TIERS:
-        entries = report["tiers"][tier]
-        first = format_entry(entries[0]) if entries else ""
-        lines.append(f"{tier:<8}| {len(entries):^5} | {first}")
-        for entry in entries[1:]:
-            lines.append(f"{'':8}  {'':5}   {format_entry(entry)}")
-    lines.append(f"Total   | {report['summary']['total']:^5} |")
-    lines.extend(["", "## Age histogram"])
-    for tier in TIERS:
-        lines.append(f"{tier}: {report['summary'][tier]}")
-    candidates = report["promotion_candidates"]
-    lines.extend(["", f"## Promotion candidates ({len(candidates)}):"])
-    for entry in candidates:
-        lines.append(format_entry(entry))
-    result = "\n".join(lines)
-    logger.debug("exit", extra={"context": {"function": "format_text_report", "length": len(result)}})
-    return result
-
-
-def main(argv=None):
-    if argv is None:
-        argv = sys.argv[1:]
-    args = parse_args(argv)
-    configure_logging(args.verbose)
-    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
-    try:
-        today_value = parse_today(args.today)
-        thresholds = parse_thresholds(args.threshold_days)
-        data = make_report(Path(args.knowledge_path), today_value, not args.patterns_only, thresholds)
-        if args.json:
-            print(json.dumps(data, indent=2, sort_keys=True))
-        else:
-            print(format_text_report(data))
-        logger.debug("exit", extra={"context": {"function": "main", "returncode": 0}})
-        return 0
-    except (OSError, ValueError) as exc:
-        logger.exception("fatal_error", extra={"context": {"function": "main"}})
-        print(f"error: {exc}", file=sys.stderr)
-        logger.debug("exit", extra={"context": {"function": "main", "returncode": 2}})
-        return 2
+    def test_empty_knowledge_total_zero(self):
+        data = self.make_report("")
+        self.assertEqual(data["summary"]["total"], 0)
 
 
 if __name__ == "__main__":
-    raise SystemExit(main())
+    unittest.main()
warning: Not a git repository. Use --no-index to compare two paths outside a working tree
usage: git diff --no-index [<options>] <path> <path> [<pathspec>...]

Diff output format options
    -p, --patch           generate patch
    -s, --no-patch        suppress diff output
    -u                    generate patch
    -U, --unified[=<n>]   generate diffs with <n> lines context
    -W, --[no-]function-context
                          generate diffs with <n> lines context
    --raw                 generate the diff in raw format
    --patch-with-raw      synonym for '-p --raw'
    --patch-with-stat     synonym for '-p --stat'
    --numstat             machine friendly --stat
    --shortstat           output only the last line of --stat
    -X, --dirstat[=<param1>,<param2>...]
                          output the distribution of relative amount of changes for each sub-directory
    --cumulative          synonym for --dirstat=cumulative
    --dirstat-by-file[=<param1>,<param2>...]
                          synonym for --dirstat=files,<param1>,<param2>...
    --check               warn if changes introduce conflict markers or whitespace errors
    --summary             condensed summary such as creations, renames and mode changes
    --name-only           show only names of changed files
    --name-status         show only names and status of changed files
    --stat[=<width>[,<name-width>[,<count>]]]
                          generate diffstat
    --stat-width <width>  generate diffstat with a given width
    --stat-name-width <width>
                          generate diffstat with a given name width
    --stat-graph-width <width>
                          generate diffstat with a given graph width
    --stat-count <count>  generate diffstat with limited lines
    --[no-]compact-summary
                          generate compact summary in diffstat
    --binary              output a binary diff that can be applied
    --[no-]full-index     show full pre- and post-image object names on the "index" lines
    --[no-]color[=<when>] show colored diff
    --ws-error-highlight <kind>
                          highlight whitespace errors in the 'context', 'old' or 'new' lines in the diff
    -z                    do not munge pathnames and use NULs as output field terminators in --raw or --numstat
    --[no-]abbrev[=<n>]   use <n> digits to display object names
    --src-prefix <prefix> show the given source prefix instead of "a/"
    --dst-prefix <prefix> show the given destination prefix instead of "b/"
    --line-prefix <prefix>
                          prepend an additional prefix to every line of output
    --no-prefix           do not show any source or destination prefix
    --default-prefix      use default prefixes a/ and b/
    --inter-hunk-context <n>
                          show context between diff hunks up to the specified number of lines
    --output-indicator-new <char>
                          specify the character to indicate a new line instead of '+'
    --output-indicator-old <char>
                          specify the character to indicate an old line instead of '-'
    --output-indicator-context <char>
                          specify the character to indicate a context instead of ' '

Diff rename options
    -B, --break-rewrites[=<n>[/<m>]]
                          break complete rewrite changes into pairs of delete and create
    -M, --find-renames[=<n>]
                          detect renames
    -D, --irreversible-delete
                          omit the preimage for deletes
    -C, --find-copies[=<n>]
                          detect copies
    --[no-]find-copies-harder
                          use unmodified files as source to find copies
    --no-renames          disable rename detection
    --[no-]rename-empty   use empty blobs as rename source
    --[no-]follow         continue listing the history of a file beyond renames
    -l <n>                prevent rename/copy detection if the number of rename/copy targets exceeds given limit

Diff algorithm options
    --minimal             produce the smallest possible diff
    -w, --ignore-all-space
                          ignore whitespace when comparing lines
    -b, --ignore-space-change
                          ignore changes in amount of whitespace
    --ignore-space-at-eol ignore changes in whitespace at EOL
    --ignore-cr-at-eol    ignore carrier-return at the end of line
    --ignore-blank-lines  ignore changes whose lines are all blank
    -I, --[no-]ignore-matching-lines <regex>
                          ignore changes whose all lines match <regex>
    --[no-]indent-heuristic
                          heuristic to shift diff hunk boundaries for easy reading
    --patience            generate diff using the "patience diff" algorithm
    --histogram           generate diff using the "histogram diff" algorithm
    --diff-algorithm <algorithm>
                          choose a diff algorithm
    --anchored <text>     generate diff using the "anchored diff" algorithm
    --word-diff[=<mode>]  show word diff, using <mode> to delimit changed words
    --word-diff-regex <regex>
                          use <regex> to decide what a word is
    --color-words[=<regex>]
                          equivalent to --word-diff=color --word-diff-regex=<regex>
    --[no-]color-moved[=<mode>]
                          moved lines of code are colored differently
    --[no-]color-moved-ws <mode>
                          how white spaces are ignored in --color-moved

Other diff options
    --[no-]relative[=<prefix>]
                          when run from subdir, exclude changes outside and show relative paths
    -a, --[no-]text       treat all files as text
    -R                    swap two inputs, reverse the diff
    --[no-]exit-code      exit with 1 if there were differences, 0 otherwise
    --[no-]quiet          disable all output of the program
    --[no-]ext-diff       allow an external diff helper to be executed
    --[no-]textconv       run external text conversion filters when comparing binary files
    --ignore-submodules[=<when>]
                          ignore changes to submodules in the diff generation
    --submodule[=<format>]
                          specify how differences in submodules are shown
    --ita-invisible-in-index
                          hide 'git add -N' entries from the index
    --ita-visible-in-index
                          treat 'git add -N' entries as real in the index
    -S <string>           look for differences that change the number of occurrences of the specified string
    -G <regex>            look for differences that change the number of occurrences of the specified regex
    --pickaxe-all         show all changes in the changeset with -S or -G
    --pickaxe-regex       treat <string> in -S as extended POSIX regular expression
    -O <file>             control the order in which files appear in the output
    --rotate-to <path>    show the change in the specified path first
    --skip-to <path>      skip the output to the specified path
    --find-object <object-id>
                          look for differences that change the number of occurrences of the specified object
    --diff-filter [(A|C|D|M|R|T|U|X|B)...[*]]
                          select files by diff type
    --max-depth <depth>   maximum tree depth to recurse
    --output <file>       output to a specific file

warning: in the working copy of '.claude/scripts/knowledge-decay-report.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/test_knowledge_decay_report.py', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/scripts/knowledge-decay-report.py b/.claude/scripts/knowledge-decay-report.py
new file mode 100644
index 0000000000000000000000000000000000000000..145c275c929084d0d84834375b0241c46b4effdc
--- /dev/null
+++ b/.claude/scripts/knowledge-decay-report.py
@@ -0,0 +1,283 @@
+#!/usr/bin/env python3
+"""Audit knowledge.md entries by verification age tier."""
+import argparse
+import json
+import logging
+import re
+import sys
+from datetime import date
+from pathlib import Path
+
+
+TIERS = ("active", "warm", "cold", "archive", "unparsed")
+DEFAULT_THRESHOLDS = (14, 30, 90)
+ENTRY_RE = re.compile(r"^###\s+(.+?)\s+\((\d{4}-\d{2}-\d{2}),\s*verified:\s*(\d{4}-\d{2}-\d{2})\)\s*$")
+HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
+
+
+class JsonFormatter(logging.Formatter):
+    def format(self, record):
+        payload = {
+            "level": record.levelname,
+            "message": record.getMessage(),
+            "logger": record.name,
+        }
+        if record.exc_info:
+            payload["exc_info"] = self.formatException(record.exc_info)
+        for key, value in getattr(record, "context", {}).items():
+            payload[key] = value
+        return json.dumps(payload, sort_keys=True)
+
+
+logger = logging.getLogger("knowledge_decay_report")
+
+
+def configure_logging(verbose):
+    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
+    handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(JsonFormatter())
+    root = logging.getLogger()
+    root.handlers.clear()
+    root.addHandler(handler)
+    root.setLevel(logging.DEBUG if verbose else logging.WARNING)
+    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})
+
+
+def parse_args(argv):
+    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
+    parser = argparse.ArgumentParser(description="Audit .claude/memory/knowledge.md verification decay tiers.")
+    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
+    parser.add_argument("--knowledge-path", default=".claude/memory/knowledge.md", help="Path to knowledge.md.")
+    parser.add_argument("--today", help="Override today's date as YYYY-MM-DD.")
+    group = parser.add_mutually_exclusive_group()
+    group.add_argument("--include-gotchas", action="store_true", help="Include Gotchas section entries (default).")
+    group.add_argument("--patterns-only", action="store_true", help="Only include Patterns section entries.")
+    parser.add_argument("--threshold-days", default="14,30,90", help="Comma-separated active,warm,cold day cutoffs.")
+    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG structured logs on stderr.")
+    args = parser.parse_args(argv)
+    logger.debug("exit", extra={"context": {"function": "parse_args", "json": args.json}})
+    return args
+
+
+def parse_thresholds(value):
+    logger.debug("entry", extra={"context": {"function": "parse_thresholds", "value": value}})
+    try:
+        parts = tuple(int(part.strip()) for part in value.split(","))
+        if len(parts) != 3 or parts[0] < 0 or not (parts[0] < parts[1] < parts[2]):
+            raise ValueError("thresholds must be three increasing non-negative integers")
+        logger.debug("exit", extra={"context": {"function": "parse_thresholds", "thresholds": parts}})
+        return parts
+    except ValueError:
+        logger.exception("invalid_thresholds", extra={"context": {"function": "parse_thresholds", "value": value}})
+        raise
+
+
+def parse_today(value):
+    logger.debug("entry", extra={"context": {"function": "parse_today", "provided": bool(value)}})
+    try:
+        result = date.fromisoformat(value) if value else date.today()
+        logger.debug("exit", extra={"context": {"function": "parse_today", "today": result.isoformat()}})
+        return result
+    except ValueError:
+        logger.exception("invalid_today", extra={"context": {"function": "parse_today", "value": value}})
+        raise
+
+
+def classify_age(age_days, thresholds):
+    logger.debug("entry", extra={"context": {"function": "classify_age", "age_days": age_days}})
+    active, warm, cold = thresholds
+    if age_days <= active:
+        tier = "active"
+    elif age_days <= warm:
+        tier = "warm"
+    elif age_days <= cold:
+        tier = "cold"
+    else:
+        tier = "archive"
+    logger.debug("exit", extra={"context": {"function": "classify_age", "tier": tier}})
+    return tier
+
+
+def blank_report(today_value):
+    logger.debug("entry", extra={"context": {"function": "blank_report", "today": today_value.isoformat()}})
+    result = {
+        "generated_at": date.today().isoformat(),
+        "today": today_value.isoformat(),
+        "tiers": {tier: [] for tier in TIERS},
+        "summary": {tier: 0 for tier in TIERS},
+        "promotion_candidates": [],
+    }
+    result["summary"]["total"] = 0
+    logger.debug("exit", extra={"context": {"function": "blank_report"}})
+    return result
+
+
+def extract_name(line):
+    logger.debug("entry", extra={"context": {"function": "extract_name"}})
+    text = line[4:].strip()
+    name = text.split(" (", 1)[0].strip() or text[:80]
+    logger.debug("exit", extra={"context": {"function": "extract_name", "name": name}})
+    return name
+
+
+def parse_entry_line(line, line_no, today_value, thresholds):
+    logger.debug("entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+    match = ENTRY_RE.match(line)
+    if not match:
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.warning("unparsed_entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+    try:
+        name, created_text, verified_text = match.groups()
+        created = date.fromisoformat(created_text)
+        verified = date.fromisoformat(verified_text)
+        age_days = (today_value - verified).days
+        tier = classify_age(age_days, thresholds)
+        entry = {
+            "name": name,
+            "verified": verified.isoformat(),
+            "created": created.isoformat(),
+            "age_days": age_days,
+            "tier": tier,
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": tier}})
+        return entry
+    except ValueError:
+        logger.exception("malformed_entry_dates", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+
+
+def iter_relevant_lines(text, include_gotchas):
+    logger.debug("entry", extra={"context": {"function": "iter_relevant_lines", "include_gotchas": include_gotchas}})
+    section = None
+    for line_no, line in enumerate(text.splitlines(), start=1):
+        heading = HEADING_RE.match(line)
+        if heading:
+            title = heading.group(1).strip().lower()
+            section = title if title in {"patterns", "gotchas"} else None
+            continue
+        if line.startswith("### ") and section == "patterns":
+            yield line_no, line
+        elif line.startswith("### ") and section == "gotchas" and include_gotchas:
+            yield line_no, line
+    logger.debug("exit", extra={"context": {"function": "iter_relevant_lines"}})
+
+
+def detect_promotion_candidates(report, knowledge_path):
+    logger.debug("entry", extra={"context": {"function": "detect_promotion_candidates", "path": str(knowledge_path)}})
+    try:
+        active_path = knowledge_path.parent / "activeContext.md"
+        if not active_path.exists():
+            logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": 0}})
+            return []
+        active_text = active_path.read_text(encoding="utf-8", errors="replace").lower()
+        candidates = []
+        for tier in ("warm", "cold", "archive"):
+            for entry in report["tiers"][tier]:
+                if entry["name"].lower() in active_text:
+                    candidates.append(entry)
+        logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": len(candidates)}})
+        return candidates
+    except OSError:
+        logger.exception("active_context_read_failed", extra={"context": {"function": "detect_promotion_candidates"}})
+        return []
+
+
+def make_report(knowledge_path, today_value, include_gotchas, thresholds):
+    logger.debug("entry", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+    report = blank_report(today_value)
+    try:
+        text = Path(knowledge_path).read_text(encoding="utf-8", errors="replace")
+    except OSError:
+        logger.exception("knowledge_read_failed", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+        raise
+    for line_no, line in iter_relevant_lines(text, include_gotchas):
+        entry = parse_entry_line(line, line_no, today_value, thresholds)
+        report["tiers"][entry["tier"]].append(entry)
+    for tier in TIERS:
+        report["summary"][tier] = len(report["tiers"][tier])
+    report["summary"]["total"] = sum(report["summary"][tier] for tier in TIERS)
+    report["promotion_candidates"] = detect_promotion_candidates(report, Path(knowledge_path))
+    logger.debug("exit", extra={"context": {"function": "make_report", "total": report["summary"]["total"]}})
+    return report
+
+
+def format_entry(entry):
+    logger.debug("entry", extra={"context": {"function": "format_entry", "tier": entry["tier"]}})
+    if entry["tier"] == "unparsed":
+        text = f"* {entry['name']} (line={entry['line_no']})"
+    else:
+        text = f"* {entry['name']} ({entry['verified']}, age={entry['age_days']}d)"
+    result = text[:80]
+    logger.debug("exit", extra={"context": {"function": "format_entry", "length": len(result)}})
+    return result
+
+
+def format_text_report(report):
+    logger.debug("entry", extra={"context": {"function": "format_text_report", "total": report["summary"]["total"]}})
+    lines = [
+        "Tier    | Count | Entries (truncated to first 80 chars)",
+        "--------+-------+-----------------------------------------",
+    ]
+    for tier in TIERS:
+        entries = report["tiers"][tier]
+        first = format_entry(entries[0]) if entries else ""
+        lines.append(f"{tier:<8}| {len(entries):^5} | {first}")
+        for entry in entries[1:]:
+            lines.append(f"{'':8}  {'':5}   {format_entry(entry)}")
+    lines.append(f"Total   | {report['summary']['total']:^5} |")
+    lines.extend(["", "## Age histogram"])
+    for tier in TIERS:
+        lines.append(f"{tier}: {report['summary'][tier]}")
+    candidates = report["promotion_candidates"]
+    lines.extend(["", f"## Promotion candidates ({len(candidates)}):"])
+    for entry in candidates:
+        lines.append(format_entry(entry))
+    result = "\n".join(lines)
+    logger.debug("exit", extra={"context": {"function": "format_text_report", "length": len(result)}})
+    return result
+
+
+def main(argv=None):
+    if argv is None:
+        argv = sys.argv[1:]
+    args = parse_args(argv)
+    configure_logging(args.verbose)
+    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
+    try:
+        today_value = parse_today(args.today)
+        thresholds = parse_thresholds(args.threshold_days)
+        data = make_report(Path(args.knowledge_path), today_value, not args.patterns_only, thresholds)
+        if args.json:
+            print(json.dumps(data, indent=2, sort_keys=True))
+        else:
+            print(format_text_report(data))
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 0}})
+        return 0
+    except (OSError, ValueError) as exc:
+        logger.exception("fatal_error", extra={"context": {"function": "main"}})
+        print(f"error: {exc}", file=sys.stderr)
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 2}})
+        return 2
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/.claude/scripts/test_knowledge_decay_report.py b/.claude/scripts/test_knowledge_decay_report.py
new file mode 100644
index 0000000000000000000000000000000000000000..f5e06729bb3a550ff345b4cf8b883c350128a62a
--- /dev/null
+++ b/.claude/scripts/test_knowledge_decay_report.py
@@ -0,0 +1,83 @@
+import importlib.util
+import json
+import tempfile
+import unittest
+from datetime import date
+from pathlib import Path
+
+
+SCRIPT_PATH = Path(__file__).with_name("knowledge-decay-report.py")
+SPEC = importlib.util.spec_from_file_location("knowledge_decay_report", SCRIPT_PATH)
+report = importlib.util.module_from_spec(SPEC)
+SPEC.loader.exec_module(report)
+
+
+def write_memory(root, knowledge_text, active_text=None):
+    memory = Path(root) / ".claude" / "memory"
+    memory.mkdir(parents=True)
+    knowledge_path = memory / "knowledge.md"
+    knowledge_path.write_text(knowledge_text, encoding="utf-8")
+    if active_text is not None:
+        (memory / "activeContext.md").write_text(active_text, encoding="utf-8")
+    return knowledge_path
+
+
+class KnowledgeDecayReportTests(unittest.TestCase):
+    def make_report(self, text, today="2026-04-25", active_text=None, include_gotchas=True):
+        with tempfile.TemporaryDirectory() as root:
+            knowledge_path = write_memory(root, text, active_text)
+            return report.make_report(
+                knowledge_path,
+                date.fromisoformat(today),
+                include_gotchas,
+                (14, 30, 90),
+            )
+
+    def test_fresh_entry_active(self):
+        data = self.make_report("## Patterns\n### Fresh (2026-04-20, verified: 2026-04-20)\n")
+        self.assertEqual(data["tiers"]["active"][0]["tier"], "active")
+
+    def test_twenty_days_warm(self):
+        data = self.make_report("## Patterns\n### Warm One (2026-04-05, verified: 2026-04-05)\n")
+        self.assertEqual(data["summary"]["warm"], 1)
+
+    def test_sixty_days_cold(self):
+        data = self.make_report("## Patterns\n### Cold One (2026-02-24, verified: 2026-02-24)\n")
+        self.assertEqual(data["tiers"]["cold"][0]["age_days"], 60)
+
+    def test_hundred_twenty_days_archive(self):
+        data = self.make_report("## Patterns\n### Old One (2025-12-26, verified: 2025-12-26)\n")
+        self.assertEqual(data["summary"]["archive"], 1)
+
+    def test_missing_verified_unparsed(self):
+        data = self.make_report("## Patterns\n### Missing Verified (2026-01-01)\n")
+        self.assertEqual(data["tiers"]["unparsed"][0]["tier"], "unparsed")
+
+    def test_today_override_applied(self):
+        data = self.make_report("## Patterns\n### Override (2026-04-01, verified: 2026-04-01)\n", today="2026-04-08")
+        self.assertEqual(data["tiers"]["active"][0]["age_days"], 7)
+
+    def test_patterns_only_excludes_gotchas(self):
+        text = "## Patterns\n### Pattern A (2026-04-20, verified: 2026-04-20)\n## Gotchas\n### Gotcha A (2026-04-20, verified: 2026-04-20)\n"
+        data = self.make_report(text, include_gotchas=False)
+        self.assertEqual(data["summary"]["total"], 1)
+        self.assertEqual(data["tiers"]["active"][0]["name"], "Pattern A")
+
+    def test_json_schema_round_trip(self):
+        data = self.make_report("## Patterns\n### Json One (2026-04-20, verified: 2026-04-20)\n")
+        loaded = json.loads(json.dumps(data))
+        self.assertEqual(set(["generated_at", "today", "tiers", "summary"]).issubset(loaded), True)
+        self.assertEqual(set(loaded["tiers"]["active"][0]), set(["name", "verified", "created", "age_days", "tier", "line_no"]))
+
+    def test_promotion_candidate_detection(self):
+        text = "## Patterns\n### Promote Me (2026-04-01, verified: 2026-04-01)\n"
+        data = self.make_report(text, active_text="We should revisit promote me today.")
+        self.assertEqual(data["promotion_candidates"][0]["name"], "Promote Me")
+
+    def test_empty_knowledge_total_zero(self):
+        data = self.make_report("")
+        self.assertEqual(data["summary"]["total"], 0)
+
+
+if __name__ == "__main__":
+    unittest.main()

codex
Git diff behaved oddly with untracked files, so I’ll check status and whitespace directly on the new files.
exec
powershell.exe -Command 'git status --short; git ls-files -- .claude/scripts/knowledge-decay-report.py .claude/scripts/test_knowledge_decay_report.py; git diff --no-index --check -- /dev/null .claude/scripts/knowledge-decay-report.py; Write-Output "SCRIPT_CHECK_EXIT=$LASTEXITCODE"; git diff --no-index --check -- /dev/null .claude/scripts/test_knowledge_decay_report.py; Write-Output "TEST_CHECK_EXIT=$LASTEXITCODE"' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\codex\task-V1-knowledge-decay-report
 succeeded in 451ms:
SCRIPT_CHECK_EXIT=1
TEST_CHECK_EXIT=1
fatal: detected dubious ownership in repository at 'C:/Bots/Migrator bots/claude-project-template-update/worktrees/validation/codex/task-V1-knowledge-decay-report'
'C:/Bots/Migrator bots/claude-project-template-update/worktrees/validation/codex/task-V1-knowledge-decay-report/.git' is owned by:
	DESKTOP-7FI6JC5/Lenovo (S-1-5-21-3639331995-3164478676-1546236719-1001)
but the current user is:
	DESKTOP-7FI6JC5/CodexSandboxOffline (S-1-5-21-3639331995-3164478676-1546236719-1004)
To add an exception for this directory, call:

	git config --global --add safe.directory 'C:/Bots/Migrator bots/claude-project-template-update/worktrees/validation/codex/task-V1-knowledge-decay-report'
fatal: detected dubious ownership in repository at 'C:/Bots/Migrator bots/claude-project-template-update/worktrees/validation/codex/task-V1-knowledge-decay-report'
'C:/Bots/Migrator bots/claude-project-template-update/worktrees/validation/codex/task-V1-knowledge-decay-report/.git' is owned by:
	DESKTOP-7FI6JC5/Lenovo (S-1-5-21-3639331995-3164478676-1546236719-1001)
but the current user is:
	DESKTOP-7FI6JC5/CodexSandboxOffline (S-1-5-21-3639331995-3164478676-1546236719-1004)
To add an exception for this directory, call:

	git config --global --add safe.directory 'C:/Bots/Migrator bots/claude-project-template-update/worktrees/validation/codex/task-V1-knowledge-decay-report'
warning: in the working copy of '.claude/scripts/knowledge-decay-report.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/test_knowledge_decay_report.py', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/scripts/knowledge-decay-report.py b/.claude/scripts/knowledge-decay-report.py
new file mode 100644
index 0000000000000000000000000000000000000000..145c275c929084d0d84834375b0241c46b4effdc
--- /dev/null
+++ b/.claude/scripts/knowledge-decay-report.py
@@ -0,0 +1,283 @@
+#!/usr/bin/env python3
+"""Audit knowledge.md entries by verification age tier."""
+import argparse
+import json
+import logging
+import re
+import sys
+from datetime import date
+from pathlib import Path
+
+
+TIERS = ("active", "warm", "cold", "archive", "unparsed")
+DEFAULT_THRESHOLDS = (14, 30, 90)
+ENTRY_RE = re.compile(r"^###\s+(.+?)\s+\((\d{4}-\d{2}-\d{2}),\s*verified:\s*(\d{4}-\d{2}-\d{2})\)\s*$")
+HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
+
+
+class JsonFormatter(logging.Formatter):
+    def format(self, record):
+        payload = {
+            "level": record.levelname,
+            "message": record.getMessage(),
+            "logger": record.name,
+        }
+        if record.exc_info:
+            payload["exc_info"] = self.formatException(record.exc_info)
+        for key, value in getattr(record, "context", {}).items():
+            payload[key] = value
+        return json.dumps(payload, sort_keys=True)
+
+
+logger = logging.getLogger("knowledge_decay_report")
+
+
+def configure_logging(verbose):
+    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
+    handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(JsonFormatter())
+    root = logging.getLogger()
+    root.handlers.clear()
+    root.addHandler(handler)
+    root.setLevel(logging.DEBUG if verbose else logging.WARNING)
+    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})
+
+
+def parse_args(argv):
+    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
+    parser = argparse.ArgumentParser(description="Audit .claude/memory/knowledge.md verification decay tiers.")
+    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
+    parser.add_argument("--knowledge-path", default=".claude/memory/knowledge.md", help="Path to knowledge.md.")
+    parser.add_argument("--today", help="Override today's date as YYYY-MM-DD.")
+    group = parser.add_mutually_exclusive_group()
+    group.add_argument("--include-gotchas", action="store_true", help="Include Gotchas section entries (default).")
+    group.add_argument("--patterns-only", action="store_true", help="Only include Patterns section entries.")
+    parser.add_argument("--threshold-days", default="14,30,90", help="Comma-separated active,warm,cold day cutoffs.")
+    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG structured logs on stderr.")
+    args = parser.parse_args(argv)
+    logger.debug("exit", extra={"context": {"function": "parse_args", "json": args.json}})
+    return args
+
+
+def parse_thresholds(value):
+    logger.debug("entry", extra={"context": {"function": "parse_thresholds", "value": value}})
+    try:
+        parts = tuple(int(part.strip()) for part in value.split(","))
+        if len(parts) != 3 or parts[0] < 0 or not (parts[0] < parts[1] < parts[2]):
+            raise ValueError("thresholds must be three increasing non-negative integers")
+        logger.debug("exit", extra={"context": {"function": "parse_thresholds", "thresholds": parts}})
+        return parts
+    except ValueError:
+        logger.exception("invalid_thresholds", extra={"context": {"function": "parse_thresholds", "value": value}})
+        raise
+
+
+def parse_today(value):
+    logger.debug("entry", extra={"context": {"function": "parse_today", "provided": bool(value)}})
+    try:
+        result = date.fromisoformat(value) if value else date.today()
+        logger.debug("exit", extra={"context": {"function": "parse_today", "today": result.isoformat()}})
+        return result
+    except ValueError:
+        logger.exception("invalid_today", extra={"context": {"function": "parse_today", "value": value}})
+        raise
+
+
+def classify_age(age_days, thresholds):
+    logger.debug("entry", extra={"context": {"function": "classify_age", "age_days": age_days}})
+    active, warm, cold = thresholds
+    if age_days <= active:
+        tier = "active"
+    elif age_days <= warm:
+        tier = "warm"
+    elif age_days <= cold:
+        tier = "cold"
+    else:
+        tier = "archive"
+    logger.debug("exit", extra={"context": {"function": "classify_age", "tier": tier}})
+    return tier
+
+
+def blank_report(today_value):
+    logger.debug("entry", extra={"context": {"function": "blank_report", "today": today_value.isoformat()}})
+    result = {
+        "generated_at": date.today().isoformat(),
+        "today": today_value.isoformat(),
+        "tiers": {tier: [] for tier in TIERS},
+        "summary": {tier: 0 for tier in TIERS},
+        "promotion_candidates": [],
+    }
+    result["summary"]["total"] = 0
+    logger.debug("exit", extra={"context": {"function": "blank_report"}})
+    return result
+
+
+def extract_name(line):
+    logger.debug("entry", extra={"context": {"function": "extract_name"}})
+    text = line[4:].strip()
+    name = text.split(" (", 1)[0].strip() or text[:80]
+    logger.debug("exit", extra={"context": {"function": "extract_name", "name": name}})
+    return name
+
+
+def parse_entry_line(line, line_no, today_value, thresholds):
+    logger.debug("entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+    match = ENTRY_RE.match(line)
+    if not match:
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.warning("unparsed_entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+    try:
+        name, created_text, verified_text = match.groups()
+        created = date.fromisoformat(created_text)
+        verified = date.fromisoformat(verified_text)
+        age_days = (today_value - verified).days
+        tier = classify_age(age_days, thresholds)
+        entry = {
+            "name": name,
+            "verified": verified.isoformat(),
+            "created": created.isoformat(),
+            "age_days": age_days,
+            "tier": tier,
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": tier}})
+        return entry
+    except ValueError:
+        logger.exception("malformed_entry_dates", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+
+
+def iter_relevant_lines(text, include_gotchas):
+    logger.debug("entry", extra={"context": {"function": "iter_relevant_lines", "include_gotchas": include_gotchas}})
+    section = None
+    for line_no, line in enumerate(text.splitlines(), start=1):
+        heading = HEADING_RE.match(line)
+        if heading:
+            title = heading.group(1).strip().lower()
+            section = title if title in {"patterns", "gotchas"} else None
+            continue
+        if line.startswith("### ") and section == "patterns":
+            yield line_no, line
+        elif line.startswith("### ") and section == "gotchas" and include_gotchas:
+            yield line_no, line
+    logger.debug("exit", extra={"context": {"function": "iter_relevant_lines"}})
+
+
+def detect_promotion_candidates(report, knowledge_path):
+    logger.debug("entry", extra={"context": {"function": "detect_promotion_candidates", "path": str(knowledge_path)}})
+    try:
+        active_path = knowledge_path.parent / "activeContext.md"
+        if not active_path.exists():
+            logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": 0}})
+            return []
+        active_text = active_path.read_text(encoding="utf-8", errors="replace").lower()
+        candidates = []
+        for tier in ("warm", "cold", "archive"):
+            for entry in report["tiers"][tier]:
+                if entry["name"].lower() in active_text:
+                    candidates.append(entry)
+        logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": len(candidates)}})
+        return candidates
+    except OSError:
+        logger.exception("active_context_read_failed", extra={"context": {"function": "detect_promotion_candidates"}})
+        return []
+
+
+def make_report(knowledge_path, today_value, include_gotchas, thresholds):
+    logger.debug("entry", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+    report = blank_report(today_value)
+    try:
+        text = Path(knowledge_path).read_text(encoding="utf-8", errors="replace")
+    except OSError:
+        logger.exception("knowledge_read_failed", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+        raise
+    for line_no, line in iter_relevant_lines(text, include_gotchas):
+        entry = parse_entry_line(line, line_no, today_value, thresholds)
+        report["tiers"][entry["tier"]].append(entry)
+    for tier in TIERS:
+        report["summary"][tier] = len(report["tiers"][tier])
+    report["summary"]["total"] = sum(report["summary"][tier] for tier in TIERS)
+    report["promotion_candidates"] = detect_promotion_candidates(report, Path(knowledge_path))
+    logger.debug("exit", extra={"context": {"function": "make_report", "total": report["summary"]["total"]}})
+    return report
+
+
+def format_entry(entry):
+    logger.debug("entry", extra={"context": {"function": "format_entry", "tier": entry["tier"]}})
+    if entry["tier"] == "unparsed":
+        text = f"* {entry['name']} (line={entry['line_no']})"
+    else:
+        text = f"* {entry['name']} ({entry['verified']}, age={entry['age_days']}d)"
+    result = text[:80]
+    logger.debug("exit", extra={"context": {"function": "format_entry", "length": len(result)}})
+    return result
+
+
+def format_text_report(report):
+    logger.debug("entry", extra={"context": {"function": "format_text_report", "total": report["summary"]["total"]}})
+    lines = [
+        "Tier    | Count | Entries (truncated to first 80 chars)",
+        "--------+-------+-----------------------------------------",
+    ]
+    for tier in TIERS:
+        entries = report["tiers"][tier]
+        first = format_entry(entries[0]) if entries else ""
+        lines.append(f"{tier:<8}| {len(entries):^5} | {first}")
+        for entry in entries[1:]:
+            lines.append(f"{'':8}  {'':5}   {format_entry(entry)}")
+    lines.append(f"Total   | {report['summary']['total']:^5} |")
+    lines.extend(["", "## Age histogram"])
+    for tier in TIERS:
+        lines.append(f"{tier}: {report['summary'][tier]}")
+    candidates = report["promotion_candidates"]
+    lines.extend(["", f"## Promotion candidates ({len(candidates)}):"])
+    for entry in candidates:
+        lines.append(format_entry(entry))
+    result = "\n".join(lines)
+    logger.debug("exit", extra={"context": {"function": "format_text_report", "length": len(result)}})
+    return result
+
+
+def main(argv=None):
+    if argv is None:
+        argv = sys.argv[1:]
+    args = parse_args(argv)
+    configure_logging(args.verbose)
+    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
+    try:
+        today_value = parse_today(args.today)
+        thresholds = parse_thresholds(args.threshold_days)
+        data = make_report(Path(args.knowledge_path), today_value, not args.patterns_only, thresholds)
+        if args.json:
+            print(json.dumps(data, indent=2, sort_keys=True))
+        else:
+            print(format_text_report(data))
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 0}})
+        return 0
+    except (OSError, ValueError) as exc:
+        logger.exception("fatal_error", extra={"context": {"function": "main"}})
+        print(f"error: {exc}", file=sys.stderr)
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 2}})
+        return 2
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/.claude/scripts/test_knowledge_decay_report.py b/.claude/scripts/test_knowledge_decay_report.py
new file mode 100644
index 0000000000000000000000000000000000000000..f5e06729bb3a550ff345b4cf8b883c350128a62a
--- /dev/null
+++ b/.claude/scripts/test_knowledge_decay_report.py
@@ -0,0 +1,83 @@
+import importlib.util
+import json
+import tempfile
+import unittest
+from datetime import date
+from pathlib import Path
+
+
+SCRIPT_PATH = Path(__file__).with_name("knowledge-decay-report.py")
+SPEC = importlib.util.spec_from_file_location("knowledge_decay_report", SCRIPT_PATH)
+report = importlib.util.module_from_spec(SPEC)
+SPEC.loader.exec_module(report)
+
+
+def write_memory(root, knowledge_text, active_text=None):
+    memory = Path(root) / ".claude" / "memory"
+    memory.mkdir(parents=True)
+    knowledge_path = memory / "knowledge.md"
+    knowledge_path.write_text(knowledge_text, encoding="utf-8")
+    if active_text is not None:
+        (memory / "activeContext.md").write_text(active_text, encoding="utf-8")
+    return knowledge_path
+
+
+class KnowledgeDecayReportTests(unittest.TestCase):
+    def make_report(self, text, today="2026-04-25", active_text=None, include_gotchas=True):
+        with tempfile.TemporaryDirectory() as root:
+            knowledge_path = write_memory(root, text, active_text)
+            return report.make_report(
+                knowledge_path,
+                date.fromisoformat(today),
+                include_gotchas,
+                (14, 30, 90),
+            )
+
+    def test_fresh_entry_active(self):
+        data = self.make_report("## Patterns\n### Fresh (2026-04-20, verified: 2026-04-20)\n")
+        self.assertEqual(data["tiers"]["active"][0]["tier"], "active")
+
+    def test_twenty_days_warm(self):
+        data = self.make_report("## Patterns\n### Warm One (2026-04-05, verified: 2026-04-05)\n")
+        self.assertEqual(data["summary"]["warm"], 1)
+
+    def test_sixty_days_cold(self):
+        data = self.make_report("## Patterns\n### Cold One (2026-02-24, verified: 2026-02-24)\n")
+        self.assertEqual(data["tiers"]["cold"][0]["age_days"], 60)
+
+    def test_hundred_twenty_days_archive(self):
+        data = self.make_report("## Patterns\n### Old One (2025-12-26, verified: 2025-12-26)\n")
+        self.assertEqual(data["summary"]["archive"], 1)
+
+    def test_missing_verified_unparsed(self):
+        data = self.make_report("## Patterns\n### Missing Verified (2026-01-01)\n")
+        self.assertEqual(data["tiers"]["unparsed"][0]["tier"], "unparsed")
+
+    def test_today_override_applied(self):
+        data = self.make_report("## Patterns\n### Override (2026-04-01, verified: 2026-04-01)\n", today="2026-04-08")
+        self.assertEqual(data["tiers"]["active"][0]["age_days"], 7)
+
+    def test_patterns_only_excludes_gotchas(self):
+        text = "## Patterns\n### Pattern A (2026-04-20, verified: 2026-04-20)\n## Gotchas\n### Gotcha A (2026-04-20, verified: 2026-04-20)\n"
+        data = self.make_report(text, include_gotchas=False)
+        self.assertEqual(data["summary"]["total"], 1)
+        self.assertEqual(data["tiers"]["active"][0]["name"], "Pattern A")
+
+    def test_json_schema_round_trip(self):
+        data = self.make_report("## Patterns\n### Json One (2026-04-20, verified: 2026-04-20)\n")
+        loaded = json.loads(json.dumps(data))
+        self.assertEqual(set(["generated_at", "today", "tiers", "summary"]).issubset(loaded), True)
+        self.assertEqual(set(loaded["tiers"]["active"][0]), set(["name", "verified", "created", "age_days", "tier", "line_no"]))
+
+    def test_promotion_candidate_detection(self):
+        text = "## Patterns\n### Promote Me (2026-04-01, verified: 2026-04-01)\n"
+        data = self.make_report(text, active_text="We should revisit promote me today.")
+        self.assertEqual(data["promotion_candidates"][0]["name"], "Promote Me")
+
+    def test_empty_knowledge_total_zero(self):
+        data = self.make_report("")
+        self.assertEqual(data["summary"]["total"], 0)
+
+
+if __name__ == "__main__":
+    unittest.main()

**Reflecting on git issues**

I’m feeling a bit dubious about my git setup since the previous git diff didn’t seem to work. It’s strange that I can’t edit the global configuration outside of certain writable roots. I'm guessing I might need to inspect exact files using PowerShell's Get-Content. There might also be an issue with Python. I’m considering adding type hints even if they bloat the lines a bit. Additionally, I need to be cautious about parsing potential malformed entries, which might lead to unparsed records.
**Examining potential issues**

I'm noticing some potential issues with the "Default output" where the age histogram counts are by tier instead of age buckets. It might be better to have labeled ranges, like active (0-14), but there isn't a strict requirement for the histogram. Also, there’s a flag for including gotchas that defaults to include, which seems okay. I should check if `activeContext.md` exists as well. Lastly, there's concern about marking candidates for promotion without specified keys in the JSON schema, which could lead to breaks if extras aren't allowed.
**Deciding on JSON output**

I’m realizing that AC7 requires rendering candidates, which makes me think that the JSON format might need to explicitly include candidate markers. However, AC5 omits candidates in its exact JSON fields, even though the task intro suggests a default output for a candidates list. Should I stick strictly to AC5's requirements to avoid any potential violations? It's a tricky decision, so I need to weigh the importance of adhering to the exact format versus including the candidates.
**Optimizing Functionality**

I’m working on ensuring the function remains under 300 lines; currently, it’s at 283. I’m thinking about optimizing my approach, maybe using a line that counts instances over 300. An alternative is to keep the existing code with a simpler JSON dump for certain keys. I’m considering potential issues with the test cases, wondering if I need to enforce stricter checks, and thinking about any necessary patches to ensure everything runs smoothly.
codex
I’ll tighten JSON output to the exact public schema while keeping candidates for text output.
apply patch
patch: completed
C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\codex\task-V1-knowledge-decay-report\.claude/scripts/knowledge-decay-report.py
diff --git a/.claude/scripts/knowledge-decay-report.py b/.claude/scripts/knowledge-decay-report.py
new file mode 100644
index 0000000000000000000000000000000000000000..edcf049bfb31e2415301b3d4c6b5fa871b5d814f
--- /dev/null
+++ b/.claude/scripts/knowledge-decay-report.py
@@ -0,0 +1,284 @@
+#!/usr/bin/env python3
+"""Audit knowledge.md entries by verification age tier."""
+import argparse
+import json
+import logging
+import re
+import sys
+from datetime import date
+from pathlib import Path
+
+
+TIERS = ("active", "warm", "cold", "archive", "unparsed")
+DEFAULT_THRESHOLDS = (14, 30, 90)
+ENTRY_RE = re.compile(r"^###\s+(.+?)\s+\((\d{4}-\d{2}-\d{2}),\s*verified:\s*(\d{4}-\d{2}-\d{2})\)\s*$")
+HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
+
+
+class JsonFormatter(logging.Formatter):
+    def format(self, record):
+        payload = {
+            "level": record.levelname,
+            "message": record.getMessage(),
+            "logger": record.name,
+        }
+        if record.exc_info:
+            payload["exc_info"] = self.formatException(record.exc_info)
+        for key, value in getattr(record, "context", {}).items():
+            payload[key] = value
+        return json.dumps(payload, sort_keys=True)
+
+
+logger = logging.getLogger("knowledge_decay_report")
+
+
+def configure_logging(verbose):
+    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
+    handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(JsonFormatter())
+    root = logging.getLogger()
+    root.handlers.clear()
+    root.addHandler(handler)
+    root.setLevel(logging.DEBUG if verbose else logging.WARNING)
+    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})
+
+
+def parse_args(argv):
+    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
+    parser = argparse.ArgumentParser(description="Audit .claude/memory/knowledge.md verification decay tiers.")
+    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
+    parser.add_argument("--knowledge-path", default=".claude/memory/knowledge.md", help="Path to knowledge.md.")
+    parser.add_argument("--today", help="Override today's date as YYYY-MM-DD.")
+    group = parser.add_mutually_exclusive_group()
+    group.add_argument("--include-gotchas", action="store_true", help="Include Gotchas section entries (default).")
+    group.add_argument("--patterns-only", action="store_true", help="Only include Patterns section entries.")
+    parser.add_argument("--threshold-days", default="14,30,90", help="Comma-separated active,warm,cold day cutoffs.")
+    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG structured logs on stderr.")
+    args = parser.parse_args(argv)
+    logger.debug("exit", extra={"context": {"function": "parse_args", "json": args.json}})
+    return args
+
+
+def parse_thresholds(value):
+    logger.debug("entry", extra={"context": {"function": "parse_thresholds", "value": value}})
+    try:
+        parts = tuple(int(part.strip()) for part in value.split(","))
+        if len(parts) != 3 or parts[0] < 0 or not (parts[0] < parts[1] < parts[2]):
+            raise ValueError("thresholds must be three increasing non-negative integers")
+        logger.debug("exit", extra={"context": {"function": "parse_thresholds", "thresholds": parts}})
+        return parts
+    except ValueError:
+        logger.exception("invalid_thresholds", extra={"context": {"function": "parse_thresholds", "value": value}})
+        raise
+
+
+def parse_today(value):
+    logger.debug("entry", extra={"context": {"function": "parse_today", "provided": bool(value)}})
+    try:
+        result = date.fromisoformat(value) if value else date.today()
+        logger.debug("exit", extra={"context": {"function": "parse_today", "today": result.isoformat()}})
+        return result
+    except ValueError:
+        logger.exception("invalid_today", extra={"context": {"function": "parse_today", "value": value}})
+        raise
+
+
+def classify_age(age_days, thresholds):
+    logger.debug("entry", extra={"context": {"function": "classify_age", "age_days": age_days}})
+    active, warm, cold = thresholds
+    if age_days <= active:
+        tier = "active"
+    elif age_days <= warm:
+        tier = "warm"
+    elif age_days <= cold:
+        tier = "cold"
+    else:
+        tier = "archive"
+    logger.debug("exit", extra={"context": {"function": "classify_age", "tier": tier}})
+    return tier
+
+
+def blank_report(today_value):
+    logger.debug("entry", extra={"context": {"function": "blank_report", "today": today_value.isoformat()}})
+    result = {
+        "generated_at": date.today().isoformat(),
+        "today": today_value.isoformat(),
+        "tiers": {tier: [] for tier in TIERS},
+        "summary": {tier: 0 for tier in TIERS},
+        "promotion_candidates": [],
+    }
+    result["summary"]["total"] = 0
+    logger.debug("exit", extra={"context": {"function": "blank_report"}})
+    return result
+
+
+def extract_name(line):
+    logger.debug("entry", extra={"context": {"function": "extract_name"}})
+    text = line[4:].strip()
+    name = text.split(" (", 1)[0].strip() or text[:80]
+    logger.debug("exit", extra={"context": {"function": "extract_name", "name": name}})
+    return name
+
+
+def parse_entry_line(line, line_no, today_value, thresholds):
+    logger.debug("entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+    match = ENTRY_RE.match(line)
+    if not match:
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.warning("unparsed_entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+    try:
+        name, created_text, verified_text = match.groups()
+        created = date.fromisoformat(created_text)
+        verified = date.fromisoformat(verified_text)
+        age_days = (today_value - verified).days
+        tier = classify_age(age_days, thresholds)
+        entry = {
+            "name": name,
+            "verified": verified.isoformat(),
+            "created": created.isoformat(),
+            "age_days": age_days,
+            "tier": tier,
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": tier}})
+        return entry
+    except ValueError:
+        logger.exception("malformed_entry_dates", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+
+
+def iter_relevant_lines(text, include_gotchas):
+    logger.debug("entry", extra={"context": {"function": "iter_relevant_lines", "include_gotchas": include_gotchas}})
+    section = None
+    for line_no, line in enumerate(text.splitlines(), start=1):
+        heading = HEADING_RE.match(line)
+        if heading:
+            title = heading.group(1).strip().lower()
+            section = title if title in {"patterns", "gotchas"} else None
+            continue
+        if line.startswith("### ") and section == "patterns":
+            yield line_no, line
+        elif line.startswith("### ") and section == "gotchas" and include_gotchas:
+            yield line_no, line
+    logger.debug("exit", extra={"context": {"function": "iter_relevant_lines"}})
+
+
+def detect_promotion_candidates(report, knowledge_path):
+    logger.debug("entry", extra={"context": {"function": "detect_promotion_candidates", "path": str(knowledge_path)}})
+    try:
+        active_path = knowledge_path.parent / "activeContext.md"
+        if not active_path.exists():
+            logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": 0}})
+            return []
+        active_text = active_path.read_text(encoding="utf-8", errors="replace").lower()
+        candidates = []
+        for tier in ("warm", "cold", "archive"):
+            for entry in report["tiers"][tier]:
+                if entry["name"].lower() in active_text:
+                    candidates.append(entry)
+        logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": len(candidates)}})
+        return candidates
+    except OSError:
+        logger.exception("active_context_read_failed", extra={"context": {"function": "detect_promotion_candidates"}})
+        return []
+
+
+def make_report(knowledge_path, today_value, include_gotchas, thresholds):
+    logger.debug("entry", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+    report = blank_report(today_value)
+    try:
+        text = Path(knowledge_path).read_text(encoding="utf-8", errors="replace")
+    except OSError:
+        logger.exception("knowledge_read_failed", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+        raise
+    for line_no, line in iter_relevant_lines(text, include_gotchas):
+        entry = parse_entry_line(line, line_no, today_value, thresholds)
+        report["tiers"][entry["tier"]].append(entry)
+    for tier in TIERS:
+        report["summary"][tier] = len(report["tiers"][tier])
+    report["summary"]["total"] = sum(report["summary"][tier] for tier in TIERS)
+    report["promotion_candidates"] = detect_promotion_candidates(report, Path(knowledge_path))
+    logger.debug("exit", extra={"context": {"function": "make_report", "total": report["summary"]["total"]}})
+    return report
+
+
+def format_entry(entry):
+    logger.debug("entry", extra={"context": {"function": "format_entry", "tier": entry["tier"]}})
+    if entry["tier"] == "unparsed":
+        text = f"* {entry['name']} (line={entry['line_no']})"
+    else:
+        text = f"* {entry['name']} ({entry['verified']}, age={entry['age_days']}d)"
+    result = text[:80]
+    logger.debug("exit", extra={"context": {"function": "format_entry", "length": len(result)}})
+    return result
+
+
+def format_text_report(report):
+    logger.debug("entry", extra={"context": {"function": "format_text_report", "total": report["summary"]["total"]}})
+    lines = [
+        "Tier    | Count | Entries (truncated to first 80 chars)",
+        "--------+-------+-----------------------------------------",
+    ]
+    for tier in TIERS:
+        entries = report["tiers"][tier]
+        first = format_entry(entries[0]) if entries else ""
+        lines.append(f"{tier:<8}| {len(entries):^5} | {first}")
+        for entry in entries[1:]:
+            lines.append(f"{'':8}  {'':5}   {format_entry(entry)}")
+    lines.append(f"Total   | {report['summary']['total']:^5} |")
+    lines.extend(["", "## Age histogram"])
+    for tier in TIERS:
+        lines.append(f"{tier}: {report['summary'][tier]}")
+    candidates = report["promotion_candidates"]
+    lines.extend(["", f"## Promotion candidates ({len(candidates)}):"])
+    for entry in candidates:
+        lines.append(format_entry(entry))
+    result = "\n".join(lines)
+    logger.debug("exit", extra={"context": {"function": "format_text_report", "length": len(result)}})
+    return result
+
+
+def main(argv=None):
+    if argv is None:
+        argv = sys.argv[1:]
+    args = parse_args(argv)
+    configure_logging(args.verbose)
+    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
+    try:
+        today_value = parse_today(args.today)
+        thresholds = parse_thresholds(args.threshold_days)
+        data = make_report(Path(args.knowledge_path), today_value, not args.patterns_only, thresholds)
+        if args.json:
+            json_data = {key: data[key] for key in ("generated_at", "today", "tiers", "summary")}
+            print(json.dumps(json_data, indent=2, sort_keys=True))
+        else:
+            print(format_text_report(data))
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 0}})
+        return 0
+    except (OSError, ValueError) as exc:
+        logger.exception("fatal_error", extra={"context": {"function": "main"}})
+        print(f"error: {exc}", file=sys.stderr)
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 2}})
+        return 2
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/.claude/scripts/test_knowledge_decay_report.py b/.claude/scripts/test_knowledge_decay_report.py
new file mode 100644
index 0000000000000000000000000000000000000000..f5e06729bb3a550ff345b4cf8b883c350128a62a
--- /dev/null
+++ b/.claude/scripts/test_knowledge_decay_report.py
@@ -0,0 +1,83 @@
+import importlib.util
+import json
+import tempfile
+import unittest
+from datetime import date
+from pathlib import Path
+
+
+SCRIPT_PATH = Path(__file__).with_name("knowledge-decay-report.py")
+SPEC = importlib.util.spec_from_file_location("knowledge_decay_report", SCRIPT_PATH)
+report = importlib.util.module_from_spec(SPEC)
+SPEC.loader.exec_module(report)
+
+
+def write_memory(root, knowledge_text, active_text=None):
+    memory = Path(root) / ".claude" / "memory"
+    memory.mkdir(parents=True)
+    knowledge_path = memory / "knowledge.md"
+    knowledge_path.write_text(knowledge_text, encoding="utf-8")
+    if active_text is not None:
+        (memory / "activeContext.md").write_text(active_text, encoding="utf-8")
+    return knowledge_path
+
+
+class KnowledgeDecayReportTests(unittest.TestCase):
+    def make_report(self, text, today="2026-04-25", active_text=None, include_gotchas=True):
+        with tempfile.TemporaryDirectory() as root:
+            knowledge_path = write_memory(root, text, active_text)
+            return report.make_report(
+                knowledge_path,
+                date.fromisoformat(today),
+                include_gotchas,
+                (14, 30, 90),
+            )
+
+    def test_fresh_entry_active(self):
+        data = self.make_report("## Patterns\n### Fresh (2026-04-20, verified: 2026-04-20)\n")
+        self.assertEqual(data["tiers"]["active"][0]["tier"], "active")
+
+    def test_twenty_days_warm(self):
+        data = self.make_report("## Patterns\n### Warm One (2026-04-05, verified: 2026-04-05)\n")
+        self.assertEqual(data["summary"]["warm"], 1)
+
+    def test_sixty_days_cold(self):
+        data = self.make_report("## Patterns\n### Cold One (2026-02-24, verified: 2026-02-24)\n")
+        self.assertEqual(data["tiers"]["cold"][0]["age_days"], 60)
+
+    def test_hundred_twenty_days_archive(self):
+        data = self.make_report("## Patterns\n### Old One (2025-12-26, verified: 2025-12-26)\n")
+        self.assertEqual(data["summary"]["archive"], 1)
+
+    def test_missing_verified_unparsed(self):
+        data = self.make_report("## Patterns\n### Missing Verified (2026-01-01)\n")
+        self.assertEqual(data["tiers"]["unparsed"][0]["tier"], "unparsed")
+
+    def test_today_override_applied(self):
+        data = self.make_report("## Patterns\n### Override (2026-04-01, verified: 2026-04-01)\n", today="2026-04-08")
+        self.assertEqual(data["tiers"]["active"][0]["age_days"], 7)
+
+    def test_patterns_only_excludes_gotchas(self):
+        text = "## Patterns\n### Pattern A (2026-04-20, verified: 2026-04-20)\n## Gotchas\n### Gotcha A (2026-04-20, verified: 2026-04-20)\n"
+        data = self.make_report(text, include_gotchas=False)
+        self.assertEqual(data["summary"]["total"], 1)
+        self.assertEqual(data["tiers"]["active"][0]["name"], "Pattern A")
+
+    def test_json_schema_round_trip(self):
+        data = self.make_report("## Patterns\n### Json One (2026-04-20, verified: 2026-04-20)\n")
+        loaded = json.loads(json.dumps(data))
+        self.assertEqual(set(["generated_at", "today", "tiers", "summary"]).issubset(loaded), True)
+        self.assertEqual(set(loaded["tiers"]["active"][0]), set(["name", "verified", "created", "age_days", "tier", "line_no"]))
+
+    def test_promotion_candidate_detection(self):
+        text = "## Patterns\n### Promote Me (2026-04-01, verified: 2026-04-01)\n"
+        data = self.make_report(text, active_text="We should revisit promote me today.")
+        self.assertEqual(data["promotion_candidates"][0]["name"], "Promote Me")
+
+    def test_empty_knowledge_total_zero(self):
+        data = self.make_report("")
+        self.assertEqual(data["summary"]["total"], 0)
+
+
+if __name__ == "__main__":
+    unittest.main()

diff --git a/.claude/scripts/knowledge-decay-report.py b/.claude/scripts/knowledge-decay-report.py
new file mode 100644
index 0000000000000000000000000000000000000000..edcf049bfb31e2415301b3d4c6b5fa871b5d814f
--- /dev/null
+++ b/.claude/scripts/knowledge-decay-report.py
@@ -0,0 +1,284 @@
+#!/usr/bin/env python3
+"""Audit knowledge.md entries by verification age tier."""
+import argparse
+import json
+import logging
+import re
+import sys
+from datetime import date
+from pathlib import Path
+
+
+TIERS = ("active", "warm", "cold", "archive", "unparsed")
+DEFAULT_THRESHOLDS = (14, 30, 90)
+ENTRY_RE = re.compile(r"^###\s+(.+?)\s+\((\d{4}-\d{2}-\d{2}),\s*verified:\s*(\d{4}-\d{2}-\d{2})\)\s*$")
+HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
+
+
+class JsonFormatter(logging.Formatter):
+    def format(self, record):
+        payload = {
+            "level": record.levelname,
+            "message": record.getMessage(),
+            "logger": record.name,
+        }
+        if record.exc_info:
+            payload["exc_info"] = self.formatException(record.exc_info)
+        for key, value in getattr(record, "context", {}).items():
+            payload[key] = value
+        return json.dumps(payload, sort_keys=True)
+
+
+logger = logging.getLogger("knowledge_decay_report")
+
+
+def configure_logging(verbose):
+    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
+    handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(JsonFormatter())
+    root = logging.getLogger()
+    root.handlers.clear()
+    root.addHandler(handler)
+    root.setLevel(logging.DEBUG if verbose else logging.WARNING)
+    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})
+
+
+def parse_args(argv):
+    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
+    parser = argparse.ArgumentParser(description="Audit .claude/memory/knowledge.md verification decay tiers.")
+    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
+    parser.add_argument("--knowledge-path", default=".claude/memory/knowledge.md", help="Path to knowledge.md.")
+    parser.add_argument("--today", help="Override today's date as YYYY-MM-DD.")
+    group = parser.add_mutually_exclusive_group()
+    group.add_argument("--include-gotchas", action="store_true", help="Include Gotchas section entries (default).")
+    group.add_argument("--patterns-only", action="store_true", help="Only include Patterns section entries.")
+    parser.add_argument("--threshold-days", default="14,30,90", help="Comma-separated active,warm,cold day cutoffs.")
+    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG structured logs on stderr.")
+    args = parser.parse_args(argv)
+    logger.debug("exit", extra={"context": {"function": "parse_args", "json": args.json}})
+    return args
+
+
+def parse_thresholds(value):
+    logger.debug("entry", extra={"context": {"function": "parse_thresholds", "value": value}})
+    try:
+        parts = tuple(int(part.strip()) for part in value.split(","))
+        if len(parts) != 3 or parts[0] < 0 or not (parts[0] < parts[1] < parts[2]):
+            raise ValueError("thresholds must be three increasing non-negative integers")
+        logger.debug("exit", extra={"context": {"function": "parse_thresholds", "thresholds": parts}})
+        return parts
+    except ValueError:
+        logger.exception("invalid_thresholds", extra={"context": {"function": "parse_thresholds", "value": value}})
+        raise
+
+
+def parse_today(value):
+    logger.debug("entry", extra={"context": {"function": "parse_today", "provided": bool(value)}})
+    try:
+        result = date.fromisoformat(value) if value else date.today()
+        logger.debug("exit", extra={"context": {"function": "parse_today", "today": result.isoformat()}})
+        return result
+    except ValueError:
+        logger.exception("invalid_today", extra={"context": {"function": "parse_today", "value": value}})
+        raise
+
+
+def classify_age(age_days, thresholds):
+    logger.debug("entry", extra={"context": {"function": "classify_age", "age_days": age_days}})
+    active, warm, cold = thresholds
+    if age_days <= active:
+        tier = "active"
+    elif age_days <= warm:
+        tier = "warm"
+    elif age_days <= cold:
+        tier = "cold"
+    else:
+        tier = "archive"
+    logger.debug("exit", extra={"context": {"function": "classify_age", "tier": tier}})
+    return tier
+
+
+def blank_report(today_value):
+    logger.debug("entry", extra={"context": {"function": "blank_report", "today": today_value.isoformat()}})
+    result = {
+        "generated_at": date.today().isoformat(),
+        "today": today_value.isoformat(),
+        "tiers": {tier: [] for tier in TIERS},
+        "summary": {tier: 0 for tier in TIERS},
+        "promotion_candidates": [],
+    }
+    result["summary"]["total"] = 0
+    logger.debug("exit", extra={"context": {"function": "blank_report"}})
+    return result
+
+
+def extract_name(line):
+    logger.debug("entry", extra={"context": {"function": "extract_name"}})
+    text = line[4:].strip()
+    name = text.split(" (", 1)[0].strip() or text[:80]
+    logger.debug("exit", extra={"context": {"function": "extract_name", "name": name}})
+    return name
+
+
+def parse_entry_line(line, line_no, today_value, thresholds):
+    logger.debug("entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+    match = ENTRY_RE.match(line)
+    if not match:
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.warning("unparsed_entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+    try:
+        name, created_text, verified_text = match.groups()
+        created = date.fromisoformat(created_text)
+        verified = date.fromisoformat(verified_text)
+        age_days = (today_value - verified).days
+        tier = classify_age(age_days, thresholds)
+        entry = {
+            "name": name,
+            "verified": verified.isoformat(),
+            "created": created.isoformat(),
+            "age_days": age_days,
+            "tier": tier,
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": tier}})
+        return entry
+    except ValueError:
+        logger.exception("malformed_entry_dates", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+
+
+def iter_relevant_lines(text, include_gotchas):
+    logger.debug("entry", extra={"context": {"function": "iter_relevant_lines", "include_gotchas": include_gotchas}})
+    section = None
+    for line_no, line in enumerate(text.splitlines(), start=1):
+        heading = HEADING_RE.match(line)
+        if heading:
+            title = heading.group(1).strip().lower()
+            section = title if title in {"patterns", "gotchas"} else None
+            continue
+        if line.startswith("### ") and section == "patterns":
+            yield line_no, line
+        elif line.startswith("### ") and section == "gotchas" and include_gotchas:
+            yield line_no, line
+    logger.debug("exit", extra={"context": {"function": "iter_relevant_lines"}})
+
+
+def detect_promotion_candidates(report, knowledge_path):
+    logger.debug("entry", extra={"context": {"function": "detect_promotion_candidates", "path": str(knowledge_path)}})
+    try:
+        active_path = knowledge_path.parent / "activeContext.md"
+        if not active_path.exists():
+            logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": 0}})
+            return []
+        active_text = active_path.read_text(encoding="utf-8", errors="replace").lower()
+        candidates = []
+        for tier in ("warm", "cold", "archive"):
+            for entry in report["tiers"][tier]:
+                if entry["name"].lower() in active_text:
+                    candidates.append(entry)
+        logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": len(candidates)}})
+        return candidates
+    except OSError:
+        logger.exception("active_context_read_failed", extra={"context": {"function": "detect_promotion_candidates"}})
+        return []
+
+
+def make_report(knowledge_path, today_value, include_gotchas, thresholds):
+    logger.debug("entry", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+    report = blank_report(today_value)
+    try:
+        text = Path(knowledge_path).read_text(encoding="utf-8", errors="replace")
+    except OSError:
+        logger.exception("knowledge_read_failed", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+        raise
+    for line_no, line in iter_relevant_lines(text, include_gotchas):
+        entry = parse_entry_line(line, line_no, today_value, thresholds)
+        report["tiers"][entry["tier"]].append(entry)
+    for tier in TIERS:
+        report["summary"][tier] = len(report["tiers"][tier])
+    report["summary"]["total"] = sum(report["summary"][tier] for tier in TIERS)
+    report["promotion_candidates"] = detect_promotion_candidates(report, Path(knowledge_path))
+    logger.debug("exit", extra={"context": {"function": "make_report", "total": report["summary"]["total"]}})
+    return report
+
+
+def format_entry(entry):
+    logger.debug("entry", extra={"context": {"function": "format_entry", "tier": entry["tier"]}})
+    if entry["tier"] == "unparsed":
+        text = f"* {entry['name']} (line={entry['line_no']})"
+    else:
+        text = f"* {entry['name']} ({entry['verified']}, age={entry['age_days']}d)"
+    result = text[:80]
+    logger.debug("exit", extra={"context": {"function": "format_entry", "length": len(result)}})
+    return result
+
+
+def format_text_report(report):
+    logger.debug("entry", extra={"context": {"function": "format_text_report", "total": report["summary"]["total"]}})
+    lines = [
+        "Tier    | Count | Entries (truncated to first 80 chars)",
+        "--------+-------+-----------------------------------------",
+    ]
+    for tier in TIERS:
+        entries = report["tiers"][tier]
+        first = format_entry(entries[0]) if entries else ""
+        lines.append(f"{tier:<8}| {len(entries):^5} | {first}")
+        for entry in entries[1:]:
+            lines.append(f"{'':8}  {'':5}   {format_entry(entry)}")
+    lines.append(f"Total   | {report['summary']['total']:^5} |")
+    lines.extend(["", "## Age histogram"])
+    for tier in TIERS:
+        lines.append(f"{tier}: {report['summary'][tier]}")
+    candidates = report["promotion_candidates"]
+    lines.extend(["", f"## Promotion candidates ({len(candidates)}):"])
+    for entry in candidates:
+        lines.append(format_entry(entry))
+    result = "\n".join(lines)
+    logger.debug("exit", extra={"context": {"function": "format_text_report", "length": len(result)}})
+    return result
+
+
+def main(argv=None):
+    if argv is None:
+        argv = sys.argv[1:]
+    args = parse_args(argv)
+    configure_logging(args.verbose)
+    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
+    try:
+        today_value = parse_today(args.today)
+        thresholds = parse_thresholds(args.threshold_days)
+        data = make_report(Path(args.knowledge_path), today_value, not args.patterns_only, thresholds)
+        if args.json:
+            json_data = {key: data[key] for key in ("generated_at", "today", "tiers", "summary")}
+            print(json.dumps(json_data, indent=2, sort_keys=True))
+        else:
+            print(format_text_report(data))
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 0}})
+        return 0
+    except (OSError, ValueError) as exc:
+        logger.exception("fatal_error", extra={"context": {"function": "main"}})
+        print(f"error: {exc}", file=sys.stderr)
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 2}})
+        return 2
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/.claude/scripts/test_knowledge_decay_report.py b/.claude/scripts/test_knowledge_decay_report.py
new file mode 100644
index 0000000000000000000000000000000000000000..f5e06729bb3a550ff345b4cf8b883c350128a62a
--- /dev/null
+++ b/.claude/scripts/test_knowledge_decay_report.py
@@ -0,0 +1,83 @@
+import importlib.util
+import json
+import tempfile
+import unittest
+from datetime import date
+from pathlib import Path
+
+
+SCRIPT_PATH = Path(__file__).with_name("knowledge-decay-report.py")
+SPEC = importlib.util.spec_from_file_location("knowledge_decay_report", SCRIPT_PATH)
+report = importlib.util.module_from_spec(SPEC)
+SPEC.loader.exec_module(report)
+
+
+def write_memory(root, knowledge_text, active_text=None):
+    memory = Path(root) / ".claude" / "memory"
+    memory.mkdir(parents=True)
+    knowledge_path = memory / "knowledge.md"
+    knowledge_path.write_text(knowledge_text, encoding="utf-8")
+    if active_text is not None:
+        (memory / "activeContext.md").write_text(active_text, encoding="utf-8")
+    return knowledge_path
+
+
+class KnowledgeDecayReportTests(unittest.TestCase):
+    def make_report(self, text, today="2026-04-25", active_text=None, include_gotchas=True):
+        with tempfile.TemporaryDirectory() as root:
+            knowledge_path = write_memory(root, text, active_text)
+            return report.make_report(
+                knowledge_path,
+                date.fromisoformat(today),
+                include_gotchas,
+                (14, 30, 90),
+            )
+
+    def test_fresh_entry_active(self):
+        data = self.make_report("## Patterns\n### Fresh (2026-04-20, verified: 2026-04-20)\n")
+        self.assertEqual(data["tiers"]["active"][0]["tier"], "active")
+
+    def test_twenty_days_warm(self):
+        data = self.make_report("## Patterns\n### Warm One (2026-04-05, verified: 2026-04-05)\n")
+        self.assertEqual(data["summary"]["warm"], 1)
+
+    def test_sixty_days_cold(self):
+        data = self.make_report("## Patterns\n### Cold One (2026-02-24, verified: 2026-02-24)\n")
+        self.assertEqual(data["tiers"]["cold"][0]["age_days"], 60)
+
+    def test_hundred_twenty_days_archive(self):
+        data = self.make_report("## Patterns\n### Old One (2025-12-26, verified: 2025-12-26)\n")
+        self.assertEqual(data["summary"]["archive"], 1)
+
+    def test_missing_verified_unparsed(self):
+        data = self.make_report("## Patterns\n### Missing Verified (2026-01-01)\n")
+        self.assertEqual(data["tiers"]["unparsed"][0]["tier"], "unparsed")
+
+    def test_today_override_applied(self):
+        data = self.make_report("## Patterns\n### Override (2026-04-01, verified: 2026-04-01)\n", today="2026-04-08")
+        self.assertEqual(data["tiers"]["active"][0]["age_days"], 7)
+
+    def test_patterns_only_excludes_gotchas(self):
+        text = "## Patterns\n### Pattern A (2026-04-20, verified: 2026-04-20)\n## Gotchas\n### Gotcha A (2026-04-20, verified: 2026-04-20)\n"
+        data = self.make_report(text, include_gotchas=False)
+        self.assertEqual(data["summary"]["total"], 1)
+        self.assertEqual(data["tiers"]["active"][0]["name"], "Pattern A")
+
+    def test_json_schema_round_trip(self):
+        data = self.make_report("## Patterns\n### Json One (2026-04-20, verified: 2026-04-20)\n")
+        loaded = json.loads(json.dumps(data))
+        self.assertEqual(set(["generated_at", "today", "tiers", "summary"]).issubset(loaded), True)
+        self.assertEqual(set(loaded["tiers"]["active"][0]), set(["name", "verified", "created", "age_days", "tier", "line_no"]))
+
+    def test_promotion_candidate_detection(self):
+        text = "## Patterns\n### Promote Me (2026-04-01, verified: 2026-04-01)\n"
+        data = self.make_report(text, active_text="We should revisit promote me today.")
+        self.assertEqual(data["promotion_candidates"][0]["name"], "Promote Me")
+
+    def test_empty_knowledge_total_zero(self):
+        data = self.make_report("")
+        self.assertEqual(data["summary"]["total"], 0)
+
+
+if __name__ == "__main__":
+    unittest.main()

**Considering code validation methods**

I've got counts by tier, and I’m thinking about whether I should want bins. There’s a potential issue with running `git diff --check` due to a safe directory, not a code problem. I might want to avoid using git altogether. I could run a custom whitespace check with PowerShell, but maybe it’s not necessary. If there's no Python available, I’ll need to consider validating through static analysis and check for syntax manually instead.
codex
I’ll inspect active context and file lengths to prepare an honest handoff sample.
exec
powershell.exe -Command "if (Test-Path '.claude/memory/activeContext.md') { Get-Content '.claude/memory/activeContext.md' -TotalCount 120 } else { Write-Output 'NO_ACTIVE_CONTEXT' }; ''; (Select-String -Path '.claude/memory/knowledge.md' -Pattern '"'^###'"' | Measure-Object).Count; (Select-String -Path '.claude/memory/knowledge.md' -Pattern '"'^###'"' | ForEach-Object { "'$_.Line })' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\validation\codex\task-V1-knowledge-decay-report
 succeeded in 455ms:
# Active Context

> Session bridge. Agent reads at start, updates at end. Max ~150 lines.
> Old sessions в†’ `.claude/memory/archive/`

**Last updated:** 2026-04-24

---

## Current Focus

### Codex Primary Implementer Pipeline вЂ” PIPELINE_COMPLETE 2026-04-24
**Goal:** GPT-5.5 via Codex CLI as primary code implementer; Opus as planner + reviewer + memory keeper. Level 2 + Level 3 together. Local-to-this-project only until PoC validates on other boats.

**Status:** End-to-end validated. Two live dual-implement rounds completed. 9 bugs found and fixed surgically. Speed layer added. All 98 unit tests green.

**Key artifacts (local scope, NOT synced to new-project template yet):**
- `.claude/scripts/codex-implement.py` (1120 lines) + 38 tests вЂ” single-task Codex executor
- `.claude/scripts/codex-wave.py` (582 lines) + 23 tests вЂ” parallel launcher (architectural-ready, not yet live-exercised)
- `.claude/scripts/codex-scope-check.py` (274 lines) + 23 tests вЂ” diff в†” fence validator with `@path` file-mode prefix
- `.claude/hooks/codex-gate.py` extended + 14 tests вЂ” recognizes task-result.md as valid opinion
- `.claude/skills/dual-implement/SKILL.md` вЂ” Level 3 orchestration
- `.claude/adr/adr-012-codex-primary-implementer.md` вЂ” decision record
- `.claude/shared/work-templates/phases/{IMPLEMENT-CODEX,IMPLEMENT-HYBRID,DUAL-IMPLEMENT}.md` вЂ” phase-mode docs
- `.claude/shared/work-templates/task-codex-template.md` вЂ” extended task-N.md format
- `AGENTS.md` at repo root вЂ” shared Codex project_doc context (auto-loaded, ~40% prompt shrink)
- Project `CLAUDE.md` вЂ” new opt-in section "Codex Primary Implementer (Experimental, Local)"

**Live validations performed:**
- PoC on gpt-5.5: status=pass, all tests passing
- PoC on gpt-5.5 via chatgpt backend-api route: status=pass
- Dual-1 (task-dual-1, add --json): bugs #7/#8/#9/#11 surfaced, Claude won by default
- Dual-2 (task-dual-2, add --sort-by): both sides PASS with valid diffs, Claude won on merit (logging-standards + style consistency + docstring quality)

**Speed layer:**
- `speed_profile: fast | balanced | thorough` frontmatter + `--speed` CLI flag
- Default `balanced` (reasoning=medium) вЂ” halves runtime vs old `high` default
- Precedence: `--reasoning` > `--speed` > FM `reasoning` > FM `speed_profile` > default
- AGENTS.md shared context cuts prompt size ~40%

**Critical gotchas surfaced (see knowledge.md):**
- GPT-5.5 via CLI blocked for ChatGPT accounts on default `openai` provider в†’ use `chatgpt` provider route
- Codex prompts via stdin not argv on Windows (cmd.exe quoting kills markdown)
- Codex sandbox lacks `py -3` в†’ use `python` in Test Commands
- `codex-scope-check.py --fence` needs explicit `@` prefix for file mode
- `codex-implement.py` preflight refuses dirty tree (rollback would destroy user work)

**Git tags (checkpoint trail):**
pipeline-checkpoint-PLAN в†’ IMPLEMENT_WAVE_1 в†’ IMPLEMENT_WAVE_2 в†’ POC_FAIL в†’ POC_FIX_v1 в†’ POC_SUCCESS_GPT55 в†’ POST_DUAL1_FIXES в†’ DUAL2_COMPLETE в†’ PIPELINE_COMPLETE

**What's next (future sessions):**
- `codex-wave.py` smoke test with 2 parallel tasks (architectural-ready)
- Propagation to new-project template + other bot projects via fleet-sync
- Iteration memory mechanism (`## Iteration History` section) automated when Opus re-runs same task

---

### Watchdog Р”nushnost Fix вЂ” COMPLETE (branch: `fix/watchdog-dushnost`)
**Problem:** Codex Watchdog РґР°РІР°Р» 10+ РёС‚РµСЂР°С†РёРѕРЅРЅС‹Рµ С†РёРєР»С‹ Р»РѕР¶РЅС‹С… РїСЂРѕР±СѓР¶РґРµРЅРёР№. Р”РІР° live FP РїРѕР№РјР°РЅС‹ Р·Р° РѕРґРЅСѓ СЃРµСЃСЃРёСЋ: (1) В«Linear MCP works with caveatВ» С‚СЂРёРіРіРµСЂРЅСѓР» РїРѕ СЃР»РѕРІР°Рј works+fails; (2) codex-gate Р·Р°Р±Р»РѕРєРёСЂРѕРІР°Р» write РЅР° 5 edits (by-design, РЅРµ С‡Р°СЃС‚СЊ РїСЂРѕР±Р»РµРјС‹).

**Root cause (confirmed via evidence in session):**
1. `codex-watchdog.py` РЅРµ РёРјРµР» state-С„Р°Р№Р»Р° РјРµР¶РґСѓ РІС‹Р·РѕРІР°РјРё вЂ” РєР°Р¶РґРѕРµ Stop Р·Р°РЅРѕРІРѕ РІРёРґРµР»Рѕ С‚Рµ Р¶Рµ С‚СЂРёРіРіРµСЂС‹.
2. Pre-filter keywords Р±С‹Р»Рё СЃР»РёС€РєРѕРј С€РёСЂРѕРєРёРµ (`bug/error/РѕС€РёР±Рє/fail` + Р»СЋР±РѕРµ action word = trigger).
3. Р•РґРёРЅСЃС‚РІРµРЅРЅС‹Р№ РєР°РЅР°Р» СЂРµР°РєС†РёРё = Р±Р»РѕРєРёСЂРѕРІРєР° Claude (exit 2 + asyncRewake). РќСЋР°РЅСЃРёСЂРѕРІР°РЅРЅС‹Рµ РІРµСЂРґРёРєС‚С‹ С„РѕСЂСЃРёР»РёСЃСЊ РІ HALT.
4. Codex СЃР°Рј РІ `.codex/reviews/latest.json` РїРѕРјРµС‚РёР» over-blocking РєР°Рє BLOCKER РІ СЃС‚Р°СЂРѕР№ СЂРµР°Р»РёР·Р°С†РёРё `codex-review.py` (СѓР¶Рµ РЅРµ wired).

**Solution (4 СЃР»РѕСЏ):**
- **L1 Severity triage**: HALT (exit 2, ~3-5%) / WARN (stdout systemMessage, ~15%) / OBSERVE (file log, ~80%). HALT С‚СЂРµР±СѓРµС‚ confidence в‰Ґ 0.85.
- **L2 State memory**: `.codex/watchdog-state.json` вЂ” sig dedup (3 last wakes), topic dedup (downgrade after 2 HALTs РЅР° С‚Сѓ Р¶Рµ С‚РµРјСѓ), post-HALT cooldown (СЃР»РµРґСѓСЋС‰РёРµ 3 Stops cap'СЏС‚СЃСЏ РґРѕ WARN).
- **L3 Task-class detector**: РЅРѕРІС‹Р№ `session-task-class.py` С…СѓРє РЅР° UserPromptSubmit вЂ” regex-РєР»Р°СЃСЃРёС„РёС†РёСЂСѓРµС‚ prompt РІ chat/typo/bugfix/feature/refactor/deploy. `chat` в†’ watchdog skip entirely. `bugfix` в†’ С‚РѕР»СЊРєРѕ HALT.
- **L5 Slash command**: `/watchdog status|strict|normal|off|class X` С‡РµСЂРµР· `.codex/task-class-override` JSON.

**NOT changed (scope discipline):** `codex-gate.py`, `codex-broker.py`, `task-completed-gate.py` вЂ” user РїРѕРґС‚РІРµСЂРґРёР» С‡С‚Рѕ СЌС‚Рѕ by-design parallel Codex review, РЅРµ С‡Р°СЃС‚СЊ РїСЂРѕР±Р»РµРјС‹.

**Files:** `.claude/hooks/codex-watchdog.py` (rewrite 255в†’456), `.claude/hooks/session-task-class.py` (new 195), `.claude/hooks/test_watchdog_fix.py` (new 277, 30/30 pass), `.claude/commands/watchdog.md` (new), `.claude/hooks/hook_base.py` (+session-task-class РІ profile), `.claude/settings.json` (wire UserPromptSubmit). Р’СЃС‘ СЃРёРЅС…СЂРѕРЅРёР·РёСЂРѕРІР°РЅРѕ РІ new-project template.

**Not done (follow-up):** fleet-sync РЅР° 13 bot РїСЂРѕРµРєС‚РѕРІ С‚СЂРµР±СѓРµС‚ РѕС‚РґРµР»СЊРЅРѕРіРѕ user approval. Layer 4 (gate consolidation С‡РµСЂРµР· broker cache) РѕС‚Р»РѕР¶РµРЅ вЂ” СЌС‚Рѕ РїРµСЂС„-РѕРїС‚РёРјРёР·Р°С†РёСЏ, РЅРµ РґСѓС€РЅРѕС‚Р°.

---

### Autoresearch Integration (Bayram Annakov в†’ experiment-loop) вЂ” PARTIALLY VERIFIED (not deployment-ready)
**Task:** Evaluate Bayram Annakov's MIT-licensed autoresearch skill (github.com/BayramAnnakov/ai-native-product-skills) and integrate useful pieces into our existing `experiment-loop` skill.

**Status clarification (per Codex watchdog 2026-04-19):** All 8 files written + unit-level behavioral tests pass (28/28). End-to-end `claude -p` smoke test, canary validation on a real bot, and Windows SIGINT verification are NOT done. Work is reproducible from tests but NOT certified for rollout.

**What was done (session 2026-04-19):**
- Cloned + security-audited Bayram's 8-file autoresearch skill (MIT)
- Codex 4-way consultation (Option C confirmed: evolve experiment-loop + add references/)
- Fixed false-positive merge-conflict detection in `task-completed-gate.py` hook (now requires exact 7-char marker or marker+space, not `=======+` prefix)
- Ported 5 reference files: `triage-checklist.md`, `fitness-design.md` (7 reqs incl. compliance audit), `modes.md` (5 modes), `plateau-ideation.md` (revert mining + taxonomy coverage), `anti-patterns.md` (16 failure modes)
- Wrote 3 templates: `goal.md`, `iteration-prompt.md`, `loop-driver.py` (Python cross-platform, 315 lines, structured logging, direction-aware plateau, SIGINT handler, resume mode)
- Upgraded `experiment-loop/SKILL.md` (219в†’302 lines) with 5-stage flow (intake/triage/fitness/mode/loop+postmortem)
- Synced global + new-project template (8 files, ~75KB)
- Auto-fixed Codex-found bug: `best_metric` initialization on `--resume` now scans entire journal for best kept metric + baseline fallback

**Decisions (user-delegated autonomy):**
- Loop driver **Python** (not bash) вЂ” cross-platform, structured logging
- Permission mode **acceptEdits** default (not bypassPermissions) вЂ” auditable
- Triage **BLOCKING** with explicit `override: force + mandatory reason`
- Single **EXPERIMENT** phase with internal checklist (not 5 sub-phases) вЂ” avoids bureaucracy

**Files:** `.claude/shared/templates/new-project/.claude/skills/experiment-loop/**` + `~/.claude/skills/experiment-loop/**` + hook fix in `.claude/hooks/task-completed-gate.py` + pipeline tracker in `work/autoresearch-integration/PIPELINE.md` + daily log `.claude/memory/daily/2026-04-19.md`

**Not done (follow-up for user approval):** fleet sync to 13 bot projects. Global + new-project template is primary source per "single source of truth" convention.

### Karpathy Behavioral Rules Integration вЂ” COMPLETE
**Task:** Evaluate andrej-karpathy-skills repo (40K stars) and selectively adopt useful principles.

**What was done (session 2026-04-16):**
- Cloned and analyzed forrestchang/andrej-karpathy-skills (4 principles, ~60 lines)
- Full comparison with our 597-line CLAUDE.md + 22 skills system
- Codex second opinion obtained (agrees: "adopt principles, not repo")
- Adopted 2 of 4 principles into global ~/.claude/CLAUDE.md:
  1. **Think Before Coding** (new ### 1) вЂ” surface assumptions, ask if unclear
  2. **Surgical Changes** (new ### 2) вЂ” every changed line traces to request
- Renumbered existing rules (Loggingв†’3, Auto-Fixв†’4, Codexв†’5)
- Added to Summary instructions (THINK FIRST, SURGICAL)
- Added to FORBIDDEN list (silent interpretation, drive-by refactoring)
- NOT adopted: Simplicity First (already in system prompt), Goal-Driven (our gates are deeper)


36
### Triage-Before-Loop (Autoresearch) (2026-04-19, verified: 2026-04-19)
### Compliance Audit for LLM-Prompt Loops (2026-04-19, verified: 2026-04-19)
### Best-Kept Metric Scan on Loop Resume (2026-04-19, verified: 2026-04-19)
### Agent Teams Scale Well (2026-02-27, verified: 2026-02-27)
### CLAUDE.md Rule Placement Matters (2026-02-16, verified: 2026-02-16)
### Skill Descriptions > Skill Bodies (2026-02-17, verified: 2026-02-17)
### Pipeline `<- CURRENT` Marker (2026-02-16, verified: 2026-02-16)
### Test After Change (2026-02-17, verified: 2026-02-17)
### Fewer Rules = Higher Compliance (2026-02-22, verified: 2026-02-22)
### Stale References Compound Across Template Mirrors (2026-02-22, verified: 2026-02-22)
### PreCompact Hook for Automatic Memory Save (2026-02-22, verified: 2026-02-22)
### TaskCompleted Hook as Quality Gate (2026-02-23, verified: 2026-02-23)
### Ebbinghaus Decay Prevents Knowledge Junk Drawer (2026-02-27, verified: 2026-02-27)
### Three Memory Layers Complement Each Other (2026-02-27, verified: 2026-02-27)
### PostToolUseFailure Hook as Error Logger (2026-02-23, verified: 2026-02-23)
### KAIROS Proactive Agent Pattern (2026-04-08, verified: 2026-04-08)
### Docker Desktop on Windows (2026-02-18, verified: 2026-02-18)
### Windows PATH trap in Docker Compose (2026-02-19, verified: 2026-02-19)
### Git Clone of Large Repos (2026-02-22, verified: 2026-02-22)
### Windows Hooks Work via Python (2026-02-13, updated 2026-03-19, verified: 2026-03-19)
### Hook Scripts Must Not Contain Their Own Detection Targets (2026-02-23, verified: 2026-02-23)
### Claude Code Has 17 Hook Events (2026-02-23, verified: 2026-02-23)
### Memory Compliance is ~30-40% (2026-02-22, verified: 2026-02-22)
### Hook Enforcement > Instruction Enforcement (2026-02-24, verified: 2026-02-24)
### Session-Orient Hook as Context Injection (2026-02-24, verified: 2026-02-24)
### Warn-Don't-Block Validation (2026-02-24, verified: 2026-02-24)
### Structured Handoff Protocol (2026-02-24, verified: 2026-02-24)
### memory-engine.py CLI Accepts Both File and Directory (2026-02-27, verified: 2026-02-27)
### GPT-5.5 via Codex CLI for ChatGPT Accounts (2026-04-24, verified: 2026-04-24)
### Codex Prompts Must Go Via stdin on Windows (2026-04-24, verified: 2026-04-24)
### Opus as Memory Keeper for Stateless Codex (2026-04-24, verified: 2026-04-24)
### Clean Tree Required Before codex-implement.py Runs (2026-04-24, verified: 2026-04-24)
### Codex Scope-Fence File Mode Needs Explicit @ Prefix (2026-04-24, verified: 2026-04-24)
### Codex Sandbox Lacks py -3 on Windows (2026-04-24, verified: 2026-04-24)
### Speed Profile as Single Knob for Codex Latency (2026-04-24, verified: 2026-04-24)
### AGENTS.md as Shared Codex Project Context (2026-04-24, verified: 2026-04-24)

diff --git a/.claude/scripts/knowledge-decay-report.py b/.claude/scripts/knowledge-decay-report.py
new file mode 100644
index 0000000000000000000000000000000000000000..edcf049bfb31e2415301b3d4c6b5fa871b5d814f
--- /dev/null
+++ b/.claude/scripts/knowledge-decay-report.py
@@ -0,0 +1,284 @@
+#!/usr/bin/env python3
+"""Audit knowledge.md entries by verification age tier."""
+import argparse
+import json
+import logging
+import re
+import sys
+from datetime import date
+from pathlib import Path
+
+
+TIERS = ("active", "warm", "cold", "archive", "unparsed")
+DEFAULT_THRESHOLDS = (14, 30, 90)
+ENTRY_RE = re.compile(r"^###\s+(.+?)\s+\((\d{4}-\d{2}-\d{2}),\s*verified:\s*(\d{4}-\d{2}-\d{2})\)\s*$")
+HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
+
+
+class JsonFormatter(logging.Formatter):
+    def format(self, record):
+        payload = {
+            "level": record.levelname,
+            "message": record.getMessage(),
+            "logger": record.name,
+        }
+        if record.exc_info:
+            payload["exc_info"] = self.formatException(record.exc_info)
+        for key, value in getattr(record, "context", {}).items():
+            payload[key] = value
+        return json.dumps(payload, sort_keys=True)
+
+
+logger = logging.getLogger("knowledge_decay_report")
+
+
+def configure_logging(verbose):
+    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
+    handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(JsonFormatter())
+    root = logging.getLogger()
+    root.handlers.clear()
+    root.addHandler(handler)
+    root.setLevel(logging.DEBUG if verbose else logging.WARNING)
+    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})
+
+
+def parse_args(argv):
+    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
+    parser = argparse.ArgumentParser(description="Audit .claude/memory/knowledge.md verification decay tiers.")
+    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
+    parser.add_argument("--knowledge-path", default=".claude/memory/knowledge.md", help="Path to knowledge.md.")
+    parser.add_argument("--today", help="Override today's date as YYYY-MM-DD.")
+    group = parser.add_mutually_exclusive_group()
+    group.add_argument("--include-gotchas", action="store_true", help="Include Gotchas section entries (default).")
+    group.add_argument("--patterns-only", action="store_true", help="Only include Patterns section entries.")
+    parser.add_argument("--threshold-days", default="14,30,90", help="Comma-separated active,warm,cold day cutoffs.")
+    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG structured logs on stderr.")
+    args = parser.parse_args(argv)
+    logger.debug("exit", extra={"context": {"function": "parse_args", "json": args.json}})
+    return args
+
+
+def parse_thresholds(value):
+    logger.debug("entry", extra={"context": {"function": "parse_thresholds", "value": value}})
+    try:
+        parts = tuple(int(part.strip()) for part in value.split(","))
+        if len(parts) != 3 or parts[0] < 0 or not (parts[0] < parts[1] < parts[2]):
+            raise ValueError("thresholds must be three increasing non-negative integers")
+        logger.debug("exit", extra={"context": {"function": "parse_thresholds", "thresholds": parts}})
+        return parts
+    except ValueError:
+        logger.exception("invalid_thresholds", extra={"context": {"function": "parse_thresholds", "value": value}})
+        raise
+
+
+def parse_today(value):
+    logger.debug("entry", extra={"context": {"function": "parse_today", "provided": bool(value)}})
+    try:
+        result = date.fromisoformat(value) if value else date.today()
+        logger.debug("exit", extra={"context": {"function": "parse_today", "today": result.isoformat()}})
+        return result
+    except ValueError:
+        logger.exception("invalid_today", extra={"context": {"function": "parse_today", "value": value}})
+        raise
+
+
+def classify_age(age_days, thresholds):
+    logger.debug("entry", extra={"context": {"function": "classify_age", "age_days": age_days}})
+    active, warm, cold = thresholds
+    if age_days <= active:
+        tier = "active"
+    elif age_days <= warm:
+        tier = "warm"
+    elif age_days <= cold:
+        tier = "cold"
+    else:
+        tier = "archive"
+    logger.debug("exit", extra={"context": {"function": "classify_age", "tier": tier}})
+    return tier
+
+
+def blank_report(today_value):
+    logger.debug("entry", extra={"context": {"function": "blank_report", "today": today_value.isoformat()}})
+    result = {
+        "generated_at": date.today().isoformat(),
+        "today": today_value.isoformat(),
+        "tiers": {tier: [] for tier in TIERS},
+        "summary": {tier: 0 for tier in TIERS},
+        "promotion_candidates": [],
+    }
+    result["summary"]["total"] = 0
+    logger.debug("exit", extra={"context": {"function": "blank_report"}})
+    return result
+
+
+def extract_name(line):
+    logger.debug("entry", extra={"context": {"function": "extract_name"}})
+    text = line[4:].strip()
+    name = text.split(" (", 1)[0].strip() or text[:80]
+    logger.debug("exit", extra={"context": {"function": "extract_name", "name": name}})
+    return name
+
+
+def parse_entry_line(line, line_no, today_value, thresholds):
+    logger.debug("entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+    match = ENTRY_RE.match(line)
+    if not match:
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.warning("unparsed_entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+    try:
+        name, created_text, verified_text = match.groups()
+        created = date.fromisoformat(created_text)
+        verified = date.fromisoformat(verified_text)
+        age_days = (today_value - verified).days
+        tier = classify_age(age_days, thresholds)
+        entry = {
+            "name": name,
+            "verified": verified.isoformat(),
+            "created": created.isoformat(),
+            "age_days": age_days,
+            "tier": tier,
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": tier}})
+        return entry
+    except ValueError:
+        logger.exception("malformed_entry_dates", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+
+
+def iter_relevant_lines(text, include_gotchas):
+    logger.debug("entry", extra={"context": {"function": "iter_relevant_lines", "include_gotchas": include_gotchas}})
+    section = None
+    for line_no, line in enumerate(text.splitlines(), start=1):
+        heading = HEADING_RE.match(line)
+        if heading:
+            title = heading.group(1).strip().lower()
+            section = title if title in {"patterns", "gotchas"} else None
+            continue
+        if line.startswith("### ") and section == "patterns":
+            yield line_no, line
+        elif line.startswith("### ") and section == "gotchas" and include_gotchas:
+            yield line_no, line
+    logger.debug("exit", extra={"context": {"function": "iter_relevant_lines"}})
+
+
+def detect_promotion_candidates(report, knowledge_path):
+    logger.debug("entry", extra={"context": {"function": "detect_promotion_candidates", "path": str(knowledge_path)}})
+    try:
+        active_path = knowledge_path.parent / "activeContext.md"
+        if not active_path.exists():
+            logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": 0}})
+            return []
+        active_text = active_path.read_text(encoding="utf-8", errors="replace").lower()
+        candidates = []
+        for tier in ("warm", "cold", "archive"):
+            for entry in report["tiers"][tier]:
+                if entry["name"].lower() in active_text:
+                    candidates.append(entry)
+        logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": len(candidates)}})
+        return candidates
+    except OSError:
+        logger.exception("active_context_read_failed", extra={"context": {"function": "detect_promotion_candidates"}})
+        return []
+
+
+def make_report(knowledge_path, today_value, include_gotchas, thresholds):
+    logger.debug("entry", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+    report = blank_report(today_value)
+    try:
+        text = Path(knowledge_path).read_text(encoding="utf-8", errors="replace")
+    except OSError:
+        logger.exception("knowledge_read_failed", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+        raise
+    for line_no, line in iter_relevant_lines(text, include_gotchas):
+        entry = parse_entry_line(line, line_no, today_value, thresholds)
+        report["tiers"][entry["tier"]].append(entry)
+    for tier in TIERS:
+        report["summary"][tier] = len(report["tiers"][tier])
+    report["summary"]["total"] = sum(report["summary"][tier] for tier in TIERS)
+    report["promotion_candidates"] = detect_promotion_candidates(report, Path(knowledge_path))
+    logger.debug("exit", extra={"context": {"function": "make_report", "total": report["summary"]["total"]}})
+    return report
+
+
+def format_entry(entry):
+    logger.debug("entry", extra={"context": {"function": "format_entry", "tier": entry["tier"]}})
+    if entry["tier"] == "unparsed":
+        text = f"* {entry['name']} (line={entry['line_no']})"
+    else:
+        text = f"* {entry['name']} ({entry['verified']}, age={entry['age_days']}d)"
+    result = text[:80]
+    logger.debug("exit", extra={"context": {"function": "format_entry", "length": len(result)}})
+    return result
+
+
+def format_text_report(report):
+    logger.debug("entry", extra={"context": {"function": "format_text_report", "total": report["summary"]["total"]}})
+    lines = [
+        "Tier    | Count | Entries (truncated to first 80 chars)",
+        "--------+-------+-----------------------------------------",
+    ]
+    for tier in TIERS:
+        entries = report["tiers"][tier]
+        first = format_entry(entries[0]) if entries else ""
+        lines.append(f"{tier:<8}| {len(entries):^5} | {first}")
+        for entry in entries[1:]:
+            lines.append(f"{'':8}  {'':5}   {format_entry(entry)}")
+    lines.append(f"Total   | {report['summary']['total']:^5} |")
+    lines.extend(["", "## Age histogram"])
+    for tier in TIERS:
+        lines.append(f"{tier}: {report['summary'][tier]}")
+    candidates = report["promotion_candidates"]
+    lines.extend(["", f"## Promotion candidates ({len(candidates)}):"])
+    for entry in candidates:
+        lines.append(format_entry(entry))
+    result = "\n".join(lines)
+    logger.debug("exit", extra={"context": {"function": "format_text_report", "length": len(result)}})
+    return result
+
+
+def main(argv=None):
+    if argv is None:
+        argv = sys.argv[1:]
+    args = parse_args(argv)
+    configure_logging(args.verbose)
+    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
+    try:
+        today_value = parse_today(args.today)
+        thresholds = parse_thresholds(args.threshold_days)
+        data = make_report(Path(args.knowledge_path), today_value, not args.patterns_only, thresholds)
+        if args.json:
+            json_data = {key: data[key] for key in ("generated_at", "today", "tiers", "summary")}
+            print(json.dumps(json_data, indent=2, sort_keys=True))
+        else:
+            print(format_text_report(data))
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 0}})
+        return 0
+    except (OSError, ValueError) as exc:
+        logger.exception("fatal_error", extra={"context": {"function": "main"}})
+        print(f"error: {exc}", file=sys.stderr)
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 2}})
+        return 2
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/.claude/scripts/test_knowledge_decay_report.py b/.claude/scripts/test_knowledge_decay_report.py
new file mode 100644
index 0000000000000000000000000000000000000000..f5e06729bb3a550ff345b4cf8b883c350128a62a
--- /dev/null
+++ b/.claude/scripts/test_knowledge_decay_report.py
@@ -0,0 +1,83 @@
+import importlib.util
+import json
+import tempfile
+import unittest
+from datetime import date
+from pathlib import Path
+
+
+SCRIPT_PATH = Path(__file__).with_name("knowledge-decay-report.py")
+SPEC = importlib.util.spec_from_file_location("knowledge_decay_report", SCRIPT_PATH)
+report = importlib.util.module_from_spec(SPEC)
+SPEC.loader.exec_module(report)
+
+
+def write_memory(root, knowledge_text, active_text=None):
+    memory = Path(root) / ".claude" / "memory"
+    memory.mkdir(parents=True)
+    knowledge_path = memory / "knowledge.md"
+    knowledge_path.write_text(knowledge_text, encoding="utf-8")
+    if active_text is not None:
+        (memory / "activeContext.md").write_text(active_text, encoding="utf-8")
+    return knowledge_path
+
+
+class KnowledgeDecayReportTests(unittest.TestCase):
+    def make_report(self, text, today="2026-04-25", active_text=None, include_gotchas=True):
+        with tempfile.TemporaryDirectory() as root:
+            knowledge_path = write_memory(root, text, active_text)
+            return report.make_report(
+                knowledge_path,
+                date.fromisoformat(today),
+                include_gotchas,
+                (14, 30, 90),
+            )
+
+    def test_fresh_entry_active(self):
+        data = self.make_report("## Patterns\n### Fresh (2026-04-20, verified: 2026-04-20)\n")
+        self.assertEqual(data["tiers"]["active"][0]["tier"], "active")
+
+    def test_twenty_days_warm(self):
+        data = self.make_report("## Patterns\n### Warm One (2026-04-05, verified: 2026-04-05)\n")
+        self.assertEqual(data["summary"]["warm"], 1)
+
+    def test_sixty_days_cold(self):
+        data = self.make_report("## Patterns\n### Cold One (2026-02-24, verified: 2026-02-24)\n")
+        self.assertEqual(data["tiers"]["cold"][0]["age_days"], 60)
+
+    def test_hundred_twenty_days_archive(self):
+        data = self.make_report("## Patterns\n### Old One (2025-12-26, verified: 2025-12-26)\n")
+        self.assertEqual(data["summary"]["archive"], 1)
+
+    def test_missing_verified_unparsed(self):
+        data = self.make_report("## Patterns\n### Missing Verified (2026-01-01)\n")
+        self.assertEqual(data["tiers"]["unparsed"][0]["tier"], "unparsed")
+
+    def test_today_override_applied(self):
+        data = self.make_report("## Patterns\n### Override (2026-04-01, verified: 2026-04-01)\n", today="2026-04-08")
+        self.assertEqual(data["tiers"]["active"][0]["age_days"], 7)
+
+    def test_patterns_only_excludes_gotchas(self):
+        text = "## Patterns\n### Pattern A (2026-04-20, verified: 2026-04-20)\n## Gotchas\n### Gotcha A (2026-04-20, verified: 2026-04-20)\n"
+        data = self.make_report(text, include_gotchas=False)
+        self.assertEqual(data["summary"]["total"], 1)
+        self.assertEqual(data["tiers"]["active"][0]["name"], "Pattern A")
+
+    def test_json_schema_round_trip(self):
+        data = self.make_report("## Patterns\n### Json One (2026-04-20, verified: 2026-04-20)\n")
+        loaded = json.loads(json.dumps(data))
+        self.assertEqual(set(["generated_at", "today", "tiers", "summary"]).issubset(loaded), True)
+        self.assertEqual(set(loaded["tiers"]["active"][0]), set(["name", "verified", "created", "age_days", "tier", "line_no"]))
+
+    def test_promotion_candidate_detection(self):
+        text = "## Patterns\n### Promote Me (2026-04-01, verified: 2026-04-01)\n"
+        data = self.make_report(text, active_text="We should revisit promote me today.")
+        self.assertEqual(data["promotion_candidates"][0]["name"], "Promote Me")
+
+    def test_empty_knowledge_total_zero(self):
+        data = self.make_report("")
+        self.assertEqual(data["summary"]["total"], 0)
+
+
+if __name__ == "__main__":
+    unittest.main()

**Considering logging setup**

I see that the generator function doesn't log anything until the iteration starts, which is fine. However, there's a potential issue with `configure_logging` because it does debug before the handler or root is set, which might mean the first entry doesn't show up. If I want an entry logged with verbose details, I need to configure it beforehand, but that's tricky. Maybe I could call it after the config, but that doesn't seem right either. It's complicated!
  ✓ Read applicable implementation guidance
  ✓ Inspect existing script patterns
  ✓ Implement CLI and tests
  ✓ Run required commands
  ✓ Prepare handoff report
diff --git a/.claude/scripts/knowledge-decay-report.py b/.claude/scripts/knowledge-decay-report.py
new file mode 100644
index 0000000000000000000000000000000000000000..edcf049bfb31e2415301b3d4c6b5fa871b5d814f
--- /dev/null
+++ b/.claude/scripts/knowledge-decay-report.py
@@ -0,0 +1,284 @@
+#!/usr/bin/env python3
+"""Audit knowledge.md entries by verification age tier."""
+import argparse
+import json
+import logging
+import re
+import sys
+from datetime import date
+from pathlib import Path
+
+
+TIERS = ("active", "warm", "cold", "archive", "unparsed")
+DEFAULT_THRESHOLDS = (14, 30, 90)
+ENTRY_RE = re.compile(r"^###\s+(.+?)\s+\((\d{4}-\d{2}-\d{2}),\s*verified:\s*(\d{4}-\d{2}-\d{2})\)\s*$")
+HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
+
+
+class JsonFormatter(logging.Formatter):
+    def format(self, record):
+        payload = {
+            "level": record.levelname,
+            "message": record.getMessage(),
+            "logger": record.name,
+        }
+        if record.exc_info:
+            payload["exc_info"] = self.formatException(record.exc_info)
+        for key, value in getattr(record, "context", {}).items():
+            payload[key] = value
+        return json.dumps(payload, sort_keys=True)
+
+
+logger = logging.getLogger("knowledge_decay_report")
+
+
+def configure_logging(verbose):
+    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
+    handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(JsonFormatter())
+    root = logging.getLogger()
+    root.handlers.clear()
+    root.addHandler(handler)
+    root.setLevel(logging.DEBUG if verbose else logging.WARNING)
+    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})
+
+
+def parse_args(argv):
+    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
+    parser = argparse.ArgumentParser(description="Audit .claude/memory/knowledge.md verification decay tiers.")
+    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
+    parser.add_argument("--knowledge-path", default=".claude/memory/knowledge.md", help="Path to knowledge.md.")
+    parser.add_argument("--today", help="Override today's date as YYYY-MM-DD.")
+    group = parser.add_mutually_exclusive_group()
+    group.add_argument("--include-gotchas", action="store_true", help="Include Gotchas section entries (default).")
+    group.add_argument("--patterns-only", action="store_true", help="Only include Patterns section entries.")
+    parser.add_argument("--threshold-days", default="14,30,90", help="Comma-separated active,warm,cold day cutoffs.")
+    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG structured logs on stderr.")
+    args = parser.parse_args(argv)
+    logger.debug("exit", extra={"context": {"function": "parse_args", "json": args.json}})
+    return args
+
+
+def parse_thresholds(value):
+    logger.debug("entry", extra={"context": {"function": "parse_thresholds", "value": value}})
+    try:
+        parts = tuple(int(part.strip()) for part in value.split(","))
+        if len(parts) != 3 or parts[0] < 0 or not (parts[0] < parts[1] < parts[2]):
+            raise ValueError("thresholds must be three increasing non-negative integers")
+        logger.debug("exit", extra={"context": {"function": "parse_thresholds", "thresholds": parts}})
+        return parts
+    except ValueError:
+        logger.exception("invalid_thresholds", extra={"context": {"function": "parse_thresholds", "value": value}})
+        raise
+
+
+def parse_today(value):
+    logger.debug("entry", extra={"context": {"function": "parse_today", "provided": bool(value)}})
+    try:
+        result = date.fromisoformat(value) if value else date.today()
+        logger.debug("exit", extra={"context": {"function": "parse_today", "today": result.isoformat()}})
+        return result
+    except ValueError:
+        logger.exception("invalid_today", extra={"context": {"function": "parse_today", "value": value}})
+        raise
+
+
+def classify_age(age_days, thresholds):
+    logger.debug("entry", extra={"context": {"function": "classify_age", "age_days": age_days}})
+    active, warm, cold = thresholds
+    if age_days <= active:
+        tier = "active"
+    elif age_days <= warm:
+        tier = "warm"
+    elif age_days <= cold:
+        tier = "cold"
+    else:
+        tier = "archive"
+    logger.debug("exit", extra={"context": {"function": "classify_age", "tier": tier}})
+    return tier
+
+
+def blank_report(today_value):
+    logger.debug("entry", extra={"context": {"function": "blank_report", "today": today_value.isoformat()}})
+    result = {
+        "generated_at": date.today().isoformat(),
+        "today": today_value.isoformat(),
+        "tiers": {tier: [] for tier in TIERS},
+        "summary": {tier: 0 for tier in TIERS},
+        "promotion_candidates": [],
+    }
+    result["summary"]["total"] = 0
+    logger.debug("exit", extra={"context": {"function": "blank_report"}})
+    return result
+
+
+def extract_name(line):
+    logger.debug("entry", extra={"context": {"function": "extract_name"}})
+    text = line[4:].strip()
+    name = text.split(" (", 1)[0].strip() or text[:80]
+    logger.debug("exit", extra={"context": {"function": "extract_name", "name": name}})
+    return name
+
+
+def parse_entry_line(line, line_no, today_value, thresholds):
+    logger.debug("entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+    match = ENTRY_RE.match(line)
+    if not match:
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.warning("unparsed_entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+    try:
+        name, created_text, verified_text = match.groups()
+        created = date.fromisoformat(created_text)
+        verified = date.fromisoformat(verified_text)
+        age_days = (today_value - verified).days
+        tier = classify_age(age_days, thresholds)
+        entry = {
+            "name": name,
+            "verified": verified.isoformat(),
+            "created": created.isoformat(),
+            "age_days": age_days,
+            "tier": tier,
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": tier}})
+        return entry
+    except ValueError:
+        logger.exception("malformed_entry_dates", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+
+
+def iter_relevant_lines(text, include_gotchas):
+    logger.debug("entry", extra={"context": {"function": "iter_relevant_lines", "include_gotchas": include_gotchas}})
+    section = None
+    for line_no, line in enumerate(text.splitlines(), start=1):
+        heading = HEADING_RE.match(line)
+        if heading:
+            title = heading.group(1).strip().lower()
+            section = title if title in {"patterns", "gotchas"} else None
+            continue
+        if line.startswith("### ") and section == "patterns":
+            yield line_no, line
+        elif line.startswith("### ") and section == "gotchas" and include_gotchas:
+            yield line_no, line
+    logger.debug("exit", extra={"context": {"function": "iter_relevant_lines"}})
+
+
+def detect_promotion_candidates(report, knowledge_path):
+    logger.debug("entry", extra={"context": {"function": "detect_promotion_candidates", "path": str(knowledge_path)}})
+    try:
+        active_path = knowledge_path.parent / "activeContext.md"
+        if not active_path.exists():
+            logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": 0}})
+            return []
+        active_text = active_path.read_text(encoding="utf-8", errors="replace").lower()
+        candidates = []
+        for tier in ("warm", "cold", "archive"):
+            for entry in report["tiers"][tier]:
+                if entry["name"].lower() in active_text:
+                    candidates.append(entry)
+        logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": len(candidates)}})
+        return candidates
+    except OSError:
+        logger.exception("active_context_read_failed", extra={"context": {"function": "detect_promotion_candidates"}})
+        return []
+
+
+def make_report(knowledge_path, today_value, include_gotchas, thresholds):
+    logger.debug("entry", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+    report = blank_report(today_value)
+    try:
+        text = Path(knowledge_path).read_text(encoding="utf-8", errors="replace")
+    except OSError:
+        logger.exception("knowledge_read_failed", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+        raise
+    for line_no, line in iter_relevant_lines(text, include_gotchas):
+        entry = parse_entry_line(line, line_no, today_value, thresholds)
+        report["tiers"][entry["tier"]].append(entry)
+    for tier in TIERS:
+        report["summary"][tier] = len(report["tiers"][tier])
+    report["summary"]["total"] = sum(report["summary"][tier] for tier in TIERS)
+    report["promotion_candidates"] = detect_promotion_candidates(report, Path(knowledge_path))
+    logger.debug("exit", extra={"context": {"function": "make_report", "total": report["summary"]["total"]}})
+    return report
+
+
+def format_entry(entry):
+    logger.debug("entry", extra={"context": {"function": "format_entry", "tier": entry["tier"]}})
+    if entry["tier"] == "unparsed":
+        text = f"* {entry['name']} (line={entry['line_no']})"
+    else:
+        text = f"* {entry['name']} ({entry['verified']}, age={entry['age_days']}d)"
+    result = text[:80]
+    logger.debug("exit", extra={"context": {"function": "format_entry", "length": len(result)}})
+    return result
+
+
+def format_text_report(report):
+    logger.debug("entry", extra={"context": {"function": "format_text_report", "total": report["summary"]["total"]}})
+    lines = [
+        "Tier    | Count | Entries (truncated to first 80 chars)",
+        "--------+-------+-----------------------------------------",
+    ]
+    for tier in TIERS:
+        entries = report["tiers"][tier]
+        first = format_entry(entries[0]) if entries else ""
+        lines.append(f"{tier:<8}| {len(entries):^5} | {first}")
+        for entry in entries[1:]:
+            lines.append(f"{'':8}  {'':5}   {format_entry(entry)}")
+    lines.append(f"Total   | {report['summary']['total']:^5} |")
+    lines.extend(["", "## Age histogram"])
+    for tier in TIERS:
+        lines.append(f"{tier}: {report['summary'][tier]}")
+    candidates = report["promotion_candidates"]
+    lines.extend(["", f"## Promotion candidates ({len(candidates)}):"])
+    for entry in candidates:
+        lines.append(format_entry(entry))
+    result = "\n".join(lines)
+    logger.debug("exit", extra={"context": {"function": "format_text_report", "length": len(result)}})
+    return result
+
+
+def main(argv=None):
+    if argv is None:
+        argv = sys.argv[1:]
+    args = parse_args(argv)
+    configure_logging(args.verbose)
+    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
+    try:
+        today_value = parse_today(args.today)
+        thresholds = parse_thresholds(args.threshold_days)
+        data = make_report(Path(args.knowledge_path), today_value, not args.patterns_only, thresholds)
+        if args.json:
+            json_data = {key: data[key] for key in ("generated_at", "today", "tiers", "summary")}
+            print(json.dumps(json_data, indent=2, sort_keys=True))
+        else:
+            print(format_text_report(data))
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 0}})
+        return 0
+    except (OSError, ValueError) as exc:
+        logger.exception("fatal_error", extra={"context": {"function": "main"}})
+        print(f"error: {exc}", file=sys.stderr)
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 2}})
+        return 2
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/.claude/scripts/test_knowledge_decay_report.py b/.claude/scripts/test_knowledge_decay_report.py
new file mode 100644
index 0000000000000000000000000000000000000000..f5e06729bb3a550ff345b4cf8b883c350128a62a
--- /dev/null
+++ b/.claude/scripts/test_knowledge_decay_report.py
@@ -0,0 +1,83 @@
+import importlib.util
+import json
+import tempfile
+import unittest
+from datetime import date
+from pathlib import Path
+
+
+SCRIPT_PATH = Path(__file__).with_name("knowledge-decay-report.py")
+SPEC = importlib.util.spec_from_file_location("knowledge_decay_report", SCRIPT_PATH)
+report = importlib.util.module_from_spec(SPEC)
+SPEC.loader.exec_module(report)
+
+
+def write_memory(root, knowledge_text, active_text=None):
+    memory = Path(root) / ".claude" / "memory"
+    memory.mkdir(parents=True)
+    knowledge_path = memory / "knowledge.md"
+    knowledge_path.write_text(knowledge_text, encoding="utf-8")
+    if active_text is not None:
+        (memory / "activeContext.md").write_text(active_text, encoding="utf-8")
+    return knowledge_path
+
+
+class KnowledgeDecayReportTests(unittest.TestCase):
+    def make_report(self, text, today="2026-04-25", active_text=None, include_gotchas=True):
+        with tempfile.TemporaryDirectory() as root:
+            knowledge_path = write_memory(root, text, active_text)
+            return report.make_report(
+                knowledge_path,
+                date.fromisoformat(today),
+                include_gotchas,
+                (14, 30, 90),
+            )
+
+    def test_fresh_entry_active(self):
+        data = self.make_report("## Patterns\n### Fresh (2026-04-20, verified: 2026-04-20)\n")
+        self.assertEqual(data["tiers"]["active"][0]["tier"], "active")
+
+    def test_twenty_days_warm(self):
+        data = self.make_report("## Patterns\n### Warm One (2026-04-05, verified: 2026-04-05)\n")
+        self.assertEqual(data["summary"]["warm"], 1)
+
+    def test_sixty_days_cold(self):
+        data = self.make_report("## Patterns\n### Cold One (2026-02-24, verified: 2026-02-24)\n")
+        self.assertEqual(data["tiers"]["cold"][0]["age_days"], 60)
+
+    def test_hundred_twenty_days_archive(self):
+        data = self.make_report("## Patterns\n### Old One (2025-12-26, verified: 2025-12-26)\n")
+        self.assertEqual(data["summary"]["archive"], 1)
+
+    def test_missing_verified_unparsed(self):
+        data = self.make_report("## Patterns\n### Missing Verified (2026-01-01)\n")
+        self.assertEqual(data["tiers"]["unparsed"][0]["tier"], "unparsed")
+
+    def test_today_override_applied(self):
+        data = self.make_report("## Patterns\n### Override (2026-04-01, verified: 2026-04-01)\n", today="2026-04-08")
+        self.assertEqual(data["tiers"]["active"][0]["age_days"], 7)
+
+    def test_patterns_only_excludes_gotchas(self):
+        text = "## Patterns\n### Pattern A (2026-04-20, verified: 2026-04-20)\n## Gotchas\n### Gotcha A (2026-04-20, verified: 2026-04-20)\n"
+        data = self.make_report(text, include_gotchas=False)
+        self.assertEqual(data["summary"]["total"], 1)
+        self.assertEqual(data["tiers"]["active"][0]["name"], "Pattern A")
+
+    def test_json_schema_round_trip(self):
+        data = self.make_report("## Patterns\n### Json One (2026-04-20, verified: 2026-04-20)\n")
+        loaded = json.loads(json.dumps(data))
+        self.assertEqual(set(["generated_at", "today", "tiers", "summary"]).issubset(loaded), True)
+        self.assertEqual(set(loaded["tiers"]["active"][0]), set(["name", "verified", "created", "age_days", "tier", "line_no"]))
+
+    def test_promotion_candidate_detection(self):
+        text = "## Patterns\n### Promote Me (2026-04-01, verified: 2026-04-01)\n"
+        data = self.make_report(text, active_text="We should revisit promote me today.")
+        self.assertEqual(data["promotion_candidates"][0]["name"], "Promote Me")
+
+    def test_empty_knowledge_total_zero(self):
+        data = self.make_report("")
+        self.assertEqual(data["summary"]["total"], 0)
+
+
+if __name__ == "__main__":
+    unittest.main()

codex
=== PHASE HANDOFF: V-1-knowledge-decay-report ===

NOTE: Added stdlib CLI at `.claude/scripts/knowledge-decay-report.py:1` with tier parsing, text/JSON output, thresholds, gotcha filtering, promotion candidates, and JSON structured logging.
NOTE: Added 10 unittest cases at `.claude/scripts/test_knowledge_decay_report.py:1` covering all required AC10 scenarios.
NOTE: Expected sample on this repo’s `knowledge.md` with `--today 2026-04-25`: `active=8`, `warm=1`, `cold=23`, `archive=0`, `unparsed=1`, `total=33`, `Promotion candidates (0)`.
NOTE: Sample table:
`Tier    | Count | Entries (truncated to first 80 chars)`
`active  |   8   | * GPT-5.5 via Codex CLI for ChatGPT Accounts (2026-04-24, age=1d)`
`warm    |   1   | * KAIROS Proactive Agent Pattern (2026-04-08, age=17d)`
`cold    |  23   | * Agent Teams Scale Well (2026-02-27, age=57d)`
`archive |   0   |`
`unparsed|   1   | * Windows Hooks Work via Python (line=141)`
`Total   |  33   |`
NOTE: JSON snippet shape: `{"generated_at":"2026-04-25","today":"2026-04-25","summary":{"active":8,"warm":1,"cold":23,"archive":0,"unparsed":1,"total":33},"tiers":{"active":[...]}}`.
BLOCKER: Required command `py -3 .claude/scripts/test_knowledge_decay_report.py` failed before running tests with `No installed Python found!` exit `1`.
BLOCKER: Required commands `py -3 .claude/scripts/knowledge-decay-report.py --help` and `py -3 .claude/scripts/knowledge-decay-report.py` also failed with `No installed Python found!` exit `112`; `python` and the PATH Python312 executable were unavailable in this sandbox.
diff --git a/.claude/scripts/knowledge-decay-report.py b/.claude/scripts/knowledge-decay-report.py
new file mode 100644
index 0000000000000000000000000000000000000000..edcf049bfb31e2415301b3d4c6b5fa871b5d814f
--- /dev/null
+++ b/.claude/scripts/knowledge-decay-report.py
@@ -0,0 +1,284 @@
+#!/usr/bin/env python3
+"""Audit knowledge.md entries by verification age tier."""
+import argparse
+import json
+import logging
+import re
+import sys
+from datetime import date
+from pathlib import Path
+
+
+TIERS = ("active", "warm", "cold", "archive", "unparsed")
+DEFAULT_THRESHOLDS = (14, 30, 90)
+ENTRY_RE = re.compile(r"^###\s+(.+?)\s+\((\d{4}-\d{2}-\d{2}),\s*verified:\s*(\d{4}-\d{2}-\d{2})\)\s*$")
+HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
+
+
+class JsonFormatter(logging.Formatter):
+    def format(self, record):
+        payload = {
+            "level": record.levelname,
+            "message": record.getMessage(),
+            "logger": record.name,
+        }
+        if record.exc_info:
+            payload["exc_info"] = self.formatException(record.exc_info)
+        for key, value in getattr(record, "context", {}).items():
+            payload[key] = value
+        return json.dumps(payload, sort_keys=True)
+
+
+logger = logging.getLogger("knowledge_decay_report")
+
+
+def configure_logging(verbose):
+    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
+    handler = logging.StreamHandler(sys.stderr)
+    handler.setFormatter(JsonFormatter())
+    root = logging.getLogger()
+    root.handlers.clear()
+    root.addHandler(handler)
+    root.setLevel(logging.DEBUG if verbose else logging.WARNING)
+    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})
+
+
+def parse_args(argv):
+    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
+    parser = argparse.ArgumentParser(description="Audit .claude/memory/knowledge.md verification decay tiers.")
+    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
+    parser.add_argument("--knowledge-path", default=".claude/memory/knowledge.md", help="Path to knowledge.md.")
+    parser.add_argument("--today", help="Override today's date as YYYY-MM-DD.")
+    group = parser.add_mutually_exclusive_group()
+    group.add_argument("--include-gotchas", action="store_true", help="Include Gotchas section entries (default).")
+    group.add_argument("--patterns-only", action="store_true", help="Only include Patterns section entries.")
+    parser.add_argument("--threshold-days", default="14,30,90", help="Comma-separated active,warm,cold day cutoffs.")
+    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG structured logs on stderr.")
+    args = parser.parse_args(argv)
+    logger.debug("exit", extra={"context": {"function": "parse_args", "json": args.json}})
+    return args
+
+
+def parse_thresholds(value):
+    logger.debug("entry", extra={"context": {"function": "parse_thresholds", "value": value}})
+    try:
+        parts = tuple(int(part.strip()) for part in value.split(","))
+        if len(parts) != 3 or parts[0] < 0 or not (parts[0] < parts[1] < parts[2]):
+            raise ValueError("thresholds must be three increasing non-negative integers")
+        logger.debug("exit", extra={"context": {"function": "parse_thresholds", "thresholds": parts}})
+        return parts
+    except ValueError:
+        logger.exception("invalid_thresholds", extra={"context": {"function": "parse_thresholds", "value": value}})
+        raise
+
+
+def parse_today(value):
+    logger.debug("entry", extra={"context": {"function": "parse_today", "provided": bool(value)}})
+    try:
+        result = date.fromisoformat(value) if value else date.today()
+        logger.debug("exit", extra={"context": {"function": "parse_today", "today": result.isoformat()}})
+        return result
+    except ValueError:
+        logger.exception("invalid_today", extra={"context": {"function": "parse_today", "value": value}})
+        raise
+
+
+def classify_age(age_days, thresholds):
+    logger.debug("entry", extra={"context": {"function": "classify_age", "age_days": age_days}})
+    active, warm, cold = thresholds
+    if age_days <= active:
+        tier = "active"
+    elif age_days <= warm:
+        tier = "warm"
+    elif age_days <= cold:
+        tier = "cold"
+    else:
+        tier = "archive"
+    logger.debug("exit", extra={"context": {"function": "classify_age", "tier": tier}})
+    return tier
+
+
+def blank_report(today_value):
+    logger.debug("entry", extra={"context": {"function": "blank_report", "today": today_value.isoformat()}})
+    result = {
+        "generated_at": date.today().isoformat(),
+        "today": today_value.isoformat(),
+        "tiers": {tier: [] for tier in TIERS},
+        "summary": {tier: 0 for tier in TIERS},
+        "promotion_candidates": [],
+    }
+    result["summary"]["total"] = 0
+    logger.debug("exit", extra={"context": {"function": "blank_report"}})
+    return result
+
+
+def extract_name(line):
+    logger.debug("entry", extra={"context": {"function": "extract_name"}})
+    text = line[4:].strip()
+    name = text.split(" (", 1)[0].strip() or text[:80]
+    logger.debug("exit", extra={"context": {"function": "extract_name", "name": name}})
+    return name
+
+
+def parse_entry_line(line, line_no, today_value, thresholds):
+    logger.debug("entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+    match = ENTRY_RE.match(line)
+    if not match:
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.warning("unparsed_entry", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+    try:
+        name, created_text, verified_text = match.groups()
+        created = date.fromisoformat(created_text)
+        verified = date.fromisoformat(verified_text)
+        age_days = (today_value - verified).days
+        tier = classify_age(age_days, thresholds)
+        entry = {
+            "name": name,
+            "verified": verified.isoformat(),
+            "created": created.isoformat(),
+            "age_days": age_days,
+            "tier": tier,
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": tier}})
+        return entry
+    except ValueError:
+        logger.exception("malformed_entry_dates", extra={"context": {"function": "parse_entry_line", "line_no": line_no}})
+        entry = {
+            "name": extract_name(line),
+            "verified": None,
+            "created": None,
+            "age_days": None,
+            "tier": "unparsed",
+            "line_no": line_no,
+        }
+        logger.debug("exit", extra={"context": {"function": "parse_entry_line", "tier": "unparsed"}})
+        return entry
+
+
+def iter_relevant_lines(text, include_gotchas):
+    logger.debug("entry", extra={"context": {"function": "iter_relevant_lines", "include_gotchas": include_gotchas}})
+    section = None
+    for line_no, line in enumerate(text.splitlines(), start=1):
+        heading = HEADING_RE.match(line)
+        if heading:
+            title = heading.group(1).strip().lower()
+            section = title if title in {"patterns", "gotchas"} else None
+            continue
+        if line.startswith("### ") and section == "patterns":
+            yield line_no, line
+        elif line.startswith("### ") and section == "gotchas" and include_gotchas:
+            yield line_no, line
+    logger.debug("exit", extra={"context": {"function": "iter_relevant_lines"}})
+
+
+def detect_promotion_candidates(report, knowledge_path):
+    logger.debug("entry", extra={"context": {"function": "detect_promotion_candidates", "path": str(knowledge_path)}})
+    try:
+        active_path = knowledge_path.parent / "activeContext.md"
+        if not active_path.exists():
+            logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": 0}})
+            return []
+        active_text = active_path.read_text(encoding="utf-8", errors="replace").lower()
+        candidates = []
+        for tier in ("warm", "cold", "archive"):
+            for entry in report["tiers"][tier]:
+                if entry["name"].lower() in active_text:
+                    candidates.append(entry)
+        logger.debug("exit", extra={"context": {"function": "detect_promotion_candidates", "count": len(candidates)}})
+        return candidates
+    except OSError:
+        logger.exception("active_context_read_failed", extra={"context": {"function": "detect_promotion_candidates"}})
+        return []
+
+
+def make_report(knowledge_path, today_value, include_gotchas, thresholds):
+    logger.debug("entry", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+    report = blank_report(today_value)
+    try:
+        text = Path(knowledge_path).read_text(encoding="utf-8", errors="replace")
+    except OSError:
+        logger.exception("knowledge_read_failed", extra={"context": {"function": "make_report", "path": str(knowledge_path)}})
+        raise
+    for line_no, line in iter_relevant_lines(text, include_gotchas):
+        entry = parse_entry_line(line, line_no, today_value, thresholds)
+        report["tiers"][entry["tier"]].append(entry)
+    for tier in TIERS:
+        report["summary"][tier] = len(report["tiers"][tier])
+    report["summary"]["total"] = sum(report["summary"][tier] for tier in TIERS)
+    report["promotion_candidates"] = detect_promotion_candidates(report, Path(knowledge_path))
+    logger.debug("exit", extra={"context": {"function": "make_report", "total": report["summary"]["total"]}})
+    return report
+
+
+def format_entry(entry):
+    logger.debug("entry", extra={"context": {"function": "format_entry", "tier": entry["tier"]}})
+    if entry["tier"] == "unparsed":
+        text = f"* {entry['name']} (line={entry['line_no']})"
+    else:
+        text = f"* {entry['name']} ({entry['verified']}, age={entry['age_days']}d)"
+    result = text[:80]
+    logger.debug("exit", extra={"context": {"function": "format_entry", "length": len(result)}})
+    return result
+
+
+def format_text_report(report):
+    logger.debug("entry", extra={"context": {"function": "format_text_report", "total": report["summary"]["total"]}})
+    lines = [
+        "Tier    | Count | Entries (truncated to first 80 chars)",
+        "--------+-------+-----------------------------------------",
+    ]
+    for tier in TIERS:
+        entries = report["tiers"][tier]
+        first = format_entry(entries[0]) if entries else ""
+        lines.append(f"{tier:<8}| {len(entries):^5} | {first}")
+        for entry in entries[1:]:
+            lines.append(f"{'':8}  {'':5}   {format_entry(entry)}")
+    lines.append(f"Total   | {report['summary']['total']:^5} |")
+    lines.extend(["", "## Age histogram"])
+    for tier in TIERS:
+        lines.append(f"{tier}: {report['summary'][tier]}")
+    candidates = report["promotion_candidates"]
+    lines.extend(["", f"## Promotion candidates ({len(candidates)}):"])
+    for entry in candidates:
+        lines.append(format_entry(entry))
+    result = "\n".join(lines)
+    logger.debug("exit", extra={"context": {"function": "format_text_report", "length": len(result)}})
+    return result
+
+
+def main(argv=None):
+    if argv is None:
+        argv = sys.argv[1:]
+    args = parse_args(argv)
+    configure_logging(args.verbose)
+    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
+    try:
+        today_value = parse_today(args.today)
+        thresholds = parse_thresholds(args.threshold_days)
+        data = make_report(Path(args.knowledge_path), today_value, not args.patterns_only, thresholds)
+        if args.json:
+            json_data = {key: data[key] for key in ("generated_at", "today", "tiers", "summary")}
+            print(json.dumps(json_data, indent=2, sort_keys=True))
+        else:
+            print(format_text_report(data))
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 0}})
+        return 0
+    except (OSError, ValueError) as exc:
+        logger.exception("fatal_error", extra={"context": {"function": "main"}})
+        print(f"error: {exc}", file=sys.stderr)
+        logger.debug("exit", extra={"context": {"function": "main", "returncode": 2}})
+        return 2
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/.claude/scripts/test_knowledge_decay_report.py b/.claude/scripts/test_knowledge_decay_report.py
new file mode 100644
index 0000000000000000000000000000000000000000..f5e06729bb3a550ff345b4cf8b883c350128a62a
--- /dev/null
+++ b/.claude/scripts/test_knowledge_decay_report.py
@@ -0,0 +1,83 @@
+import importlib.util
+import json
+import tempfile
+import unittest
+from datetime import date
+from pathlib import Path
+
+
+SCRIPT_PATH = Path(__file__).with_name("knowledge-decay-report.py")
+SPEC = importlib.util.spec_from_file_location("knowledge_decay_report", SCRIPT_PATH)
+report = importlib.util.module_from_spec(SPEC)
+SPEC.loader.exec_module(report)
+
+
+def write_memory(root, knowledge_text, active_text=None):
+    memory = Path(root) / ".claude" / "memory"
+    memory.mkdir(parents=True)
+    knowledge_path = memory / "knowledge.md"
+    knowledge_path.write_text(knowledge_text, encoding="utf-8")
+    if active_text is not None:
+        (memory / "activeContext.md").write_text(active_text, encoding="utf-8")
+    return knowledge_path
+
+
+class KnowledgeDecayReportTests(unittest.TestCase):
+    def make_report(self, text, today="2026-04-25", active_text=None, include_gotchas=True):
+        with tempfile.TemporaryDirectory() as root:
+            knowledge_path = write_memory(root, text, active_text)
+            return report.make_report(
+                knowledge_path,
+                date.fromisoformat(today),
+                include_gotchas,
+                (14, 30, 90),
+            )
+
+    def test_fresh_entry_active(self):
+        data = self.make_report("## Patterns\n### Fresh (2026-04-20, verified: 2026-04-20)\n")
+        self.assertEqual(data["tiers"]["active"][0]["tier"], "active")
+
+    def test_twenty_days_warm(self):
+        data = self.make_report("## Patterns\n### Warm One (2026-04-05, verified: 2026-04-05)\n")
+        self.assertEqual(data["summary"]["warm"], 1)
+
+    def test_sixty_days_cold(self):
+        data = self.make_report("## Patterns\n### Cold One (2026-02-24, verified: 2026-02-24)\n")
+        self.assertEqual(data["tiers"]["cold"][0]["age_days"], 60)
+
+    def test_hundred_twenty_days_archive(self):
+        data = self.make_report("## Patterns\n### Old One (2025-12-26, verified: 2025-12-26)\n")
+        self.assertEqual(data["summary"]["archive"], 1)
+
+    def test_missing_verified_unparsed(self):
+        data = self.make_report("## Patterns\n### Missing Verified (2026-01-01)\n")
+        self.assertEqual(data["tiers"]["unparsed"][0]["tier"], "unparsed")
+
+    def test_today_override_applied(self):
+        data = self.make_report("## Patterns\n### Override (2026-04-01, verified: 2026-04-01)\n", today="2026-04-08")
+        self.assertEqual(data["tiers"]["active"][0]["age_days"], 7)
+
+    def test_patterns_only_excludes_gotchas(self):
+        text = "## Patterns\n### Pattern A (2026-04-20, verified: 2026-04-20)\n## Gotchas\n### Gotcha A (2026-04-20, verified: 2026-04-20)\n"
+        data = self.make_report(text, include_gotchas=False)
+        self.assertEqual(data["summary"]["total"], 1)
+        self.assertEqual(data["tiers"]["active"][0]["name"], "Pattern A")
+
+    def test_json_schema_round_trip(self):
+        data = self.make_report("## Patterns\n### Json One (2026-04-20, verified: 2026-04-20)\n")
+        loaded = json.loads(json.dumps(data))
+        self.assertEqual(set(["generated_at", "today", "tiers", "summary"]).issubset(loaded), True)
+        self.assertEqual(set(loaded["tiers"]["active"][0]), set(["name", "verified", "created", "age_days", "tier", "line_no"]))
+
+    def test_promotion_candidate_detection(self):
+        text = "## Patterns\n### Promote Me (2026-04-01, verified: 2026-04-01)\n"
+        data = self.make_report(text, active_text="We should revisit promote me today.")
+        self.assertEqual(data["promotion_candidates"][0]["name"], "Promote Me")
+
+    def test_empty_knowledge_total_zero(self):
+        data = self.make_report("")
+        self.assertEqual(data["summary"]["total"], 0)
+
+
+if __name__ == "__main__":
+    unittest.main()

tokens used
134 281
```
