# Project: Claude Project Template Update

> Template upgrade automation with AI-First methodology integration

**Memory:** `.claude/memory/activeContext.md` | **ADR:** `.claude/adr/` | **Branch:** `dev`

## Project-Specific Notes
- Main template: `.claude/` in project root
- New-project template: `.claude/shared/templates/new-project/.claude/`
- BOTH must be updated when making template changes
- Template CLAUDE.md (in shared/templates) should match global ~/.claude/CLAUDE.md structure
- Codex CLI integration: `.claude/guides/codex-integration.md` | Skill: `cross-model-review`

## Bridge-stubs for staging sessions
When a Claude Code session's CWD is inside a staging subdir (e.g. `work/dp-notifier/files/v2/`), hook commands like `py -3 .claude/hooks/X.py` resolve relative to that CWD and fail unless a bridge-stub exists at `<staging>/.claude/hooks/X.py`. Stubs re-exec the real hook from the repo root.

**After ANY change to `.claude/settings.json` hook wiring, or after creating a new staging dir, run:**
```
py -3 .claude/scripts/sync-bridge-stubs.py
```
The sync script reads `settings.json`, finds every `.claude/hooks/` dir under `work/`, `deploy/`, `staging/` and ensures each has an up-to-date canonical stub for every hook. Safe idempotent — run any time. Canonical stub: `.claude/scripts/bridge-stub-template.py` (filename-derived, uses `subprocess.run` for Windows path-with-spaces safety).

## Codex Primary Implementer (Experimental, Local)

**SCOPE — READ FIRST.** This section is **LOCAL to this project only**. It is **NOT propagated** to other bot projects or to `.claude/shared/templates/new-project/CLAUDE.md` until the PoC validates. Do not copy this section elsewhere; do not sync via template scripts until promotion is explicitly approved. The default phase modes remain `AGENT_TEAMS`, `AO_HYBRID`, and `AO_FLEET` as documented in global `~/.claude/CLAUDE.md`. The modes below are **specialized, opt-in tools**, not replacements.

### What it is
Opus plans, decomposes, and reviews; **Codex (GPT-5.5) executes** well-defined, scope-fenced implementation tasks. The pattern keeps Opus as the judge/architect and lets a second model do logic-heavy, well-specified work where a fresh perspective or higher throughput helps.

### New phase modes (choose per task — not always-on)

- **`CODEX_IMPLEMENT`** — every implementation task in the phase is delegated to Codex. Use when tasks are logic-heavy, well-specified, and unambiguous (algorithms, protocol code, data transforms) and where an independent executor reduces confirmation-bias risk. Avoid for tasks requiring deep repo conventions or heavy cross-file refactors.
- **`HYBRID_TEAMS`** — per-task `executor:` dispatch (`claude` | `codex` | `dual`). Most flexible mode. Use when a wave mixes task shapes: some tasks suit Claude (conventions, wide context), others suit Codex (self-contained logic), and a few warrant both (high-stakes).
- **`DUAL_IMPLEMENT`** — high-stakes code: Claude and Codex implement the task **in parallel**, Opus acts as judge and picks or merges. Use for auth, crypto, payments, migrations, or any change where two independent attempts catch more bugs than one. Expect ~2× token cost — reserve for genuinely risky diffs.

### Pointers (canonical docs — do not duplicate here)
- Tech-spec: `work/codex-primary/tech-spec.md`
- ADR: `.claude/adr/adr-012-codex-primary-implementer.md`
- Phase-mode docs: `.claude/shared/work-templates/phases/IMPLEMENT-CODEX.md`, `.claude/shared/work-templates/phases/IMPLEMENT-HYBRID.md`, `.claude/shared/work-templates/phases/DUAL-IMPLEMENT.md`
- Scripts: `.claude/scripts/codex-implement.py`, `.claude/scripts/codex-wave.py`, `.claude/scripts/codex-scope-check.py`
- Skill: `.claude/skills/dual-implement/SKILL.md`

### Compatibility (unchanged — fully supported)
Agent Teams (TeamCreate), skills injection, memory (activeContext / knowledge / daily), `codex-ask` second opinion, existing codex-advisor hooks (`codex-parallel`, `codex-watchdog`, `codex-broker`, `codex-review`, `codex-stop-opinion`, `codex-gate`) — **all unchanged and fully supported**. The new modes compose with existing infrastructure; they do not replace or disable any of it.

---

## Code Delegation Protocol — Always Dual (MANDATORY, blocking)

> **Every code-writing task runs on TWO parallel tracks by default: Claude
> and Codex both implement the same plan independently; Claude judges the
> results and picks the winner.** This is "Level 3" applied universally,
> not opt-in. Claude's role stays "writer + planner + judge", but every
> diff Claude commits has a Codex counterpart that was weighed against it.

### Why

- **Per-task quality.** GPT-5.5 benchmarks higher than Opus 4.7 on coding
  (Terminal-Bench 82.7 %, SWE-Bench Pro 58.6 % vs 53.4 %). Running both
  gives us Claude's contextual strength plus Codex's raw coding edge.
- **Convergent-design signal.** When both independent implementations
  converge on the same architecture, the spec was good. When they diverge,
  that is the richest reviewable moment.
- **No default bypass.** Discipline alone gave us ~30-40 % compliance on
  "remember to also run Codex". A harness-level enforcer closes that gap
  so the dual track is the default, not an afterthought.

### Rule

For any `Edit`, `Write`, or `MultiEdit` operation that targets a **code
file**, Claude MUST have a matching Codex run (from `codex-implement.py`,
`codex-inline.py`, `codex-wave.py`, or the `dual-implement` skill) covering
the same path, with `status: pass`, produced in the last 15 minutes.

The `codex-delegate-enforcer.py` hook validates this at `PreToolUse` and
blocks the edit (exit 2) if no matching Codex artifact exists. Claude is
still free to write — but only **in parallel with or after** a Codex run
on the same scope. The hand-edit without Codex is what gets blocked.

### The Four Invariants (Z1 — codified enforcement)

The enforcer applies one rule expressed as four invariants. Together they
close 12 documented bypass vectors:

1. **Extension wins.** A path with a code extension (`.py`, `.ts`, `.sh`,
   ...) ALWAYS requires a Codex cover, regardless of where it lives.
   Path-based exemptions (`work/**`, `worktrees/**`, `.claude/scripts/**`)
   only apply to non-code extensions. A `.py` file in `work/` is still code.
2. **Bash counts.** `PreToolUse(Bash)` parses the command. Mutating verbs
   (`cp`, `mv`, `sed -i`, redirects `>`/`>>`, `git apply`, `python script.py`,
   `powershell Set-Content`, etc.) on code paths require cover. A whitelist
   exempts read-only verbs (`ls`, `cat`, `git status`, `pytest`, ...) and
   the project's own dual-implement tooling (`codex-ask`, `codex-implement`,
   `dual-teams-spawn`, ...).
3. **Path-exact coverage.** A Codex artifact's Scope Fence must explicitly
   list the target file (with glob support). "Any fresh pass within 15 min"
   is NOT enough — multi-stage tasks must run their own Codex per stage.
4. **Skip-token audit + actionable block messages.** Every allow/deny
   decision is appended to `work/codex-implementations/skip-ledger.jsonl`
   for offline audit. DENY error messages include a ready-to-run
   `codex-inline-dual.py --describe ... --scope <path>` command for the
   blocked path so the recovery is obvious.


### Task size → execution mode

| Task scope | Mode | How it runs |
|------------|------|-------------|
| 1-2 files, small diff (feature flag, typo, local bug) | **`codex-inline` + Claude hand-edit** | Claude writes own version, `codex-inline.py --describe "…"` produces Codex version in parallel, Claude picks winner |
| One focused task, non-trivial | **`dual-implement` skill (Level 3)** | Two git worktrees; Claude teammate in A, `codex-implement.py` in B; Opus judges |
| Big feature / refactor / N subtasks | **`DUAL_TEAMS` mode** (below) | N Claude teammates via `TeamCreate` **AND** N Codex sessions via `codex-wave.py`, both consuming the same `tasks/T*.md` specs in parallel; Opus judges N pairs |

### DUAL_TEAMS mode (Agent Teams + codex-wave running as twins)

For big work (`IMPLEMENT` phase with 3+ independent subtasks), instead of
either `AGENT_TEAMS` alone or `CODEX_IMPLEMENT` alone, Claude runs **both
in parallel** against the same task specs:

1. Claude (planner) writes `tasks/T1.md … TN.md` with Scope Fence + tests
   + Skill Contracts, as usual.
2. Claude spawns N Claude teammates via `TeamCreate` + `spawn-agent.py`
   (existing Agent Teams flow). Each lives in its own git worktree or
   agreed file scope, produces a diff + handoff.
3. **In parallel**, Claude runs `codex-wave.py --tasks T1.md,...,TN.md
   --parallel N`. Each Codex session lives in its own worktree, consumes
   its assigned `T{i}.md`, produces its own `task-T{i}-result.md`.
4. All 2N agents finish in wall-time ≈ `max(task_i)`.
5. Claude (as judge, using `cross-model-review` skill) compares each
   Claude-diff vs Codex-diff pair against the `T{i}.md` spec, picks the
   winner or cherry-picks hybrid. Repeats for all N subtasks.
6. Winners merged, losers archived under `work/codex-primary/dual-history/`
   for reference.

When to use:
- Any `IMPLEMENT` phase with 3+ independent subtasks — default to this
- Any high-stakes subtask within any phase — always include it in dual

When not to use:
- Pure documentation / spec writing — Claude solo
- Research / exploration / reading — no code, no Codex
- Truly trivial (< ~5 lines, single location, obvious) — inline-dual is
  still expected; only skip if the enforcer explicitly allows (see below)

### Code file extensions (delegated / enforced)

`.py .pyi .js .jsx .mjs .cjs .ts .tsx .sh .bash .zsh .go .rs .rb .java
.kt .swift .c .cpp .cc .h .hpp .cs .php .sql .lua .r`

### Exempt paths (Claude may edit freely — no Codex counterpart required)

- Any file whose extension is NOT in the list above
- `.claude/memory/**` — session memory (activeContext, knowledge, daily logs)
- `work/**` — planning artifacts (task specs, post-mortems, judgments, PIPELINE.md) (non-code only — `.py` under `work/` still requires cover, see Invariant 1)
- `CLAUDE.md`, `AGENTS.md`, `README.md`, `CHANGELOG.md`, `LICENSE`, `.gitignore`
- `.claude/settings.json`, `.claude/ops/*.yaml`, `.mcp.json` — config
- `.claude/adr/**/*.md` — architecture decisions
- `.claude/guides/**/*.md`, `.claude/skills/**/*.md` — documentation

### Workflow summary

1. Claude writes the plan (task-N.md or inline description).
2. Claude starts **both** tracks in parallel:
   - Claude-side implementation (via `TeamCreate`, direct hand-write after
     the Codex run starts, or a second worktree).
   - Codex-side implementation (via `codex-implement.py`, `codex-wave.py`,
     or `codex-inline.py`).
3. Both tracks finish — Claude reviews both diffs against the spec.
4. Claude picks winner (or merges hybrid), commits, archives loser.

### Enforcement artefact

`.claude/hooks/codex-delegate-enforcer.py` runs on `PreToolUse(Edit|Write|MultiEdit|Bash|NotebookEdit)`:
- If target has a code extension AND is NOT in exempt paths
- → Looks for a recent (< 15 min) `work/codex-implementations/task-*-result.md`
  with `status: pass` whose Scope Fence covers this path
- → Allows the edit when found; blocks with a clear recovery hint otherwise

The hook only guarantees Codex-side participation. The Claude-side half
of the dual pair is Claude's own discipline — it is expected by this
protocol, and reviewed in handoff blocks.

### Sub-agent file writes (Y14)

Sub-agents spawned via the `Agent` / `Task` tool have `Write` / `Edit` / `MultiEdit`
denied at the harness Permission UI layer (Y14, commit `1c5490b`, 4 escalating tests).
Teammate-spawners must instruct teammates to use **PowerShell `Set-Content` as the canonical
file-write mechanism** (with Bash heredoc + `git apply` as fallback). See
`.claude/guides/teammate-prompt-template.md` § "File creation in sub-agent context (Y14 finding)".
