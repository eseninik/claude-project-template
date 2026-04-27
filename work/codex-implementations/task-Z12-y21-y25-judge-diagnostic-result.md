# Codex Implementation Result — Task Z12-y21-y25-judge-diagnostic

- status: scope-violation
- timestamp: 2026-04-26T13:07:52.818557+00:00
- task_file: C:\Bots\Migrator bots\claude-project-template-update\work\codify-enforcement\task-Z12-y21-y25-judge-diagnostic.md
- base_sha: 03ec7a7676b4c32f9da88aba6d18a145aabe8644
- codex_returncode: 0
- scope_status: fail
- scope_message: 2026-04-26 16:16:21,788 INFO codex_scope_check main_started diff=C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations\task-Z12-y21-y25-judge-diagnostic.diff fence= root=.
2026-04-26 16:16:21,789 INFO codex_scope_check read_diff_started source=C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations\task-Z12-y21-y25-judge-diagnostic.diff
2026-04-26 16:16:21,797 INFO codex_scope_check read_diff_completed bytes=10642
2026-04-26 16:16:21,797 INFO codex_scope_check parse_diff_paths_started diff_bytes=10642
2026-04-26 16:16:21,797 INFO codex_scope_check parse_diff_paths_completed count=5
2026-04-26 16:16:21,797 INFO codex_scope_check parse_fence_started fence_spec='' root=C:\Bots\Migrator bots\claude-project-template-update
2026-04-26 16:16:21,797 INFO codex_scope_check parse_fence_completed allowed=0 forbidden=0
2026-04-26 16:16:21,797 INFO codex_scope_check check_paths_started allowed=0 forbidden=0
2026-04-26 16:16:21,797 WARNING codex_scope_check check_paths_no_allowed path=.claude/hooks/codex-delegate-enforcer.py
2026-04-26 16:16:21,797 WARNING codex_scope_check check_paths_no_allowed path=.claude/hooks/test_codex_delegate_enforcer_invariants.py
2026-04-26 16:16:21,797 WARNING codex_scope_check check_paths_no_allowed path=.claude/scripts/judge_axes.py
2026-04-26 16:16:21,797 WARNING codex_scope_check check_paths_no_allowed path=.claude/scripts/test_judge.py
2026-04-26 16:16:21,797 WARNING codex_scope_check check_paths_no_allowed path=work/errors.md
2026-04-26 16:16:21,797 INFO codex_scope_check check_paths_completed violations=5
2026-04-26 16:16:21,798 ERROR codex_scope_check main_completed status=violation count=5
- scope_violations:
  - VIOLATION: 5 path(s) outside fence
  - .claude/hooks/codex-delegate-enforcer.py	no allowed fence entries configured
  - .claude/hooks/test_codex_delegate_enforcer_invariants.py	no allowed fence entries configured
  - .claude/scripts/judge_axes.py	no allowed fence entries configured
  - .claude/scripts/test_judge.py	no allowed fence entries configured
  - work/errors.md	no allowed fence entries configured
  - 2026-04-26 16:16:21,788 INFO codex_scope_check main_started diff=C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations\task-Z12-y21-y25-judge-diagnostic.diff fence= root=.
  - 2026-04-26 16:16:21,789 INFO codex_scope_check read_diff_started source=C:\Bots\Migrator bots\claude-project-template-update\work\codex-implementations\task-Z12-y21-y25-judge-diagnostic.diff
  - 2026-04-26 16:16:21,797 INFO codex_scope_check read_diff_completed bytes=10642
  - 2026-04-26 16:16:21,797 INFO codex_scope_check parse_diff_paths_started diff_bytes=10642
  - 2026-04-26 16:16:21,797 INFO codex_scope_check parse_diff_paths_completed count=5
  - 2026-04-26 16:16:21,797 INFO codex_scope_check parse_fence_started fence_spec='' root=C:\Bots\Migrator bots\claude-project-template-update
  - 2026-04-26 16:16:21,797 INFO codex_scope_check parse_fence_completed allowed=0 forbidden=0
  - 2026-04-26 16:16:21,797 INFO codex_scope_check check_paths_started allowed=0 forbidden=0
  - 2026-04-26 16:16:21,797 WARNING codex_scope_check check_paths_no_allowed path=.claude/hooks/codex-delegate-enforcer.py
  - 2026-04-26 16:16:21,797 WARNING codex_scope_check check_paths_no_allowed path=.claude/hooks/test_codex_delegate_enforcer_invariants.py
  - 2026-04-26 16:16:21,797 WARNING codex_scope_check check_paths_no_allowed path=.claude/scripts/judge_axes.py
  - 2026-04-26 16:16:21,797 WARNING codex_scope_check check_paths_no_allowed path=.claude/scripts/test_judge.py
  - 2026-04-26 16:16:21,797 WARNING codex_scope_check check_paths_no_allowed path=work/errors.md
  - 2026-04-26 16:16:21,797 INFO codex_scope_check check_paths_completed violations=5
  - 2026-04-26 16:16:21,798 ERROR codex_scope_check main_completed status=violation count=5

## Diff

```diff
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f..ab289f1 100644
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -899,8 +899,38 @@ def _now_iso() -> str:
         microsecond=0).isoformat()
 
 
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
 def _build_block_message(blocked_path: str, reason_code: str) -> str:
     """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
     reason_text = {
         "no-results": "no codex-implement result found",
         "no-results-dir": "work/codex-implementations/ does not exist",
@@ -910,7 +940,17 @@ def _build_block_message(blocked_path: str, reason_code: str) -> str:
         "parse-error": "could not parse codex-implement result",
         "bash-no-cover": "Bash command would mutate code without cover",
     }.get(reason_code, reason_code)
-    msg = (
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
         "Code Delegation Protocol: " + blocked_path + " blocked ("
         + reason_text + ").\n\n"
         "To start the dual-implement track for this path, run:\n\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7..bbf8b1b 100644
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -393,6 +393,70 @@ class TestI4Ledger(_Base):
         self.assertIn("--describe", reason)
         self.assertIn(target, reason)
 
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
 
 
 # ======================================================================
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e9..9cdc7db 100644
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -180,11 +180,12 @@ def _git_diff_numstat(worktree: Path, base: str = "HEAD") -> tuple[int, int]:
 
 def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
                     cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
     _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
     try:
         added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
         _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
         return AxisResult(name="diff_size", score=score, weight=weight,
                           raw={"added": added, "removed": removed,
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd..c57e8d2 100644
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -99,7 +99,7 @@ class TestDiffSize(unittest.TestCase):
             # Add 50 lines uncommitted
             _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
             res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
             self.assertGreater(res.score, 0.85)
             self.assertLess(res.score, 0.95)
             self.assertEqual(res.raw["added"], 50)
@@ -112,6 +112,29 @@ class TestDiffSize(unittest.TestCase):
             self.assertAlmostEqual(res.score, 1.0)
             self.assertEqual(res.raw["added"], 0)
 
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
 
 # ------------------------ logging_coverage ------------------------ #
 
diff --git a/work/errors.md b/work/errors.md
index 7a8c0e3..dc96c30 100644
--- a/work/errors.md
+++ b/work/errors.md
@@ -2048,3 +2048,11 @@ txt = p.read_text(encoding='utf-8`
 """Codex Pool вЂ” warm pool of `codex app-server` in`
 **Error:** Exit code 2 /usr/bin/bash: -c: line 3: unexpected EOF while looking for matching `''
 
+### 2026-04-26 16:16:01 — Bash
+**Context:** `rtk git status -s echo "---" git diff --cached --name-only`
+**Error:** Exit code 129 [rtk] /!\ No hook installed вЂ” run `rtk init -g` for automatic token savings error: unknown option `-' usage: git status [<options>] [--] [<pathspec>...]      -v, --[no-]verbose    be verbose     -s, --[no-]short      show status concisely     -b, --[no-]branch     show branch informa
+
+### 2026-04-26 16:16:05 — Bash
+**Context:** `rtk git status --porcelain echo "---staged:---" git diff --cached --name-only`
+**Error:** Exit code 129 [rtk] /!\ No hook installed вЂ” run `rtk init -g` for automatic token savings error: unknown option `-staged:---' usage: git status [<options>] [--] [<pathspec>...]      -v, --[no-]verbose    be verbose     -s, --[no-]short      show status concisely     -b, --[no-]branch     show bran
+
```

## Test Output

(no test commands executed)
## Self-Report (Codex NOTE/BLOCKER lines)

(no NOTE/BLOCKER lines)

## Codex stderr

```
OpenAI Codex v0.125.0 (research preview)
--------
workdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
model: gpt-5.5
provider: chatgpt
approval: never
sandbox: danger-full-access
reasoning effort: xhigh
reasoning summaries: none
session id: 019dc9e7-4fea-7602-b07a-8213f9975550
--------
user
You are the single-task implementer. The task specification below is IMMUTABLE.
Write code to satisfy all Acceptance Criteria. Do NOT modify files listed in
Forbidden Paths or Read-Only Files. After writing code, run every Test Command
listed in the task and report the result in your self-report.
Any AGENTS.md or CLAUDE.md in the worktree is authoritative background context.

---- TASK SPECIFICATION ----

---
task_id: Z12-y21-y25-judge-diagnostic
title: Y21 (judge diff_size logarithmic) + Y25 (enforcer unavailability diagnostic)
executor: dual
risk_class: routine
speed_profile: balanced
---

# Task Z12 — Y21 + Y25 final UX/quality polish

## Goal

Two final improvements that close all open follow-ups:

**Y21:** `score_diff_size` in `judge_axes.py:181-188` uses `score =
max(0, 1 - added/cap_lines)` with hardcoded `cap_lines=500`. Diffs > 500
LOC score 0.0 — Z1 was +1102 LOC → forced TIE artifact. Fix:
asymptotic `score = scale / (scale + added)` — large diffs still score
lower, but never 0; judge can differentiate.

**Y25:** When enforcer denies a code-extension write, message says
"no Codex cover for X / run codex-inline-dual". But if Codex itself is
DOWN (auth expired, network out), running the suggestion ALSO fails.
Y25 detects unavailability and prepends an explicit hint:
```
*** Codex appears unavailable (<reason>).
*** Run `codex login` or wait, then retry.
```
Rule unchanged (still fail-closed). Wording improves only.

## Scope Fence — files you MAY modify

```
.claude/scripts/judge_axes.py
.claude/scripts/test_judge.py
.claude/hooks/codex-delegate-enforcer.py
.claude/hooks/test_codex_delegate_enforcer_invariants.py
```

DO NOT modify any other file.

## Read-Only Files / Evaluation Firewall

- `work/codify-enforcement/task-Z12-y21-y25-judge-diagnostic.md`
- `.claude/scripts/judge.py`, `codex-implement.py`, `codex-wave.py`,
  `codex-inline-dual.py` (downstream consumers)

## Acceptance Criteria

### AC-1 (Y21): asymptotic scaling

Modify `score_diff_size(...)`:
```python
score = scale_factor / (scale_factor + max(0, added))
```
where `scale_factor` = parameter previously named `cap_lines`. Keep
the kwarg name backward-compatible (`cap_lines: int = 500`) — internally
treat it as the asymptotic scale.

Add tests in `test_judge.py` (create file if absent — hermetic, no
real codex needed):

- `test_diff_size_zero_added_scores_one()` — added=0, cap=500 → score == 1.0
- `test_diff_size_at_scale_scores_half()` — added=500, cap=500 → score in [0.49, 0.51]
- `test_diff_size_far_above_scale_still_nonzero()` — added=2000, cap=500 → 0.0 < score < 0.3
- `test_diff_size_huge_diff_asymptotic()` — added=10000, cap=500 → score in (0.0, 0.1]

If existing test_judge tests assert hard-zero at cap, RELAX them per
this design change. Document any updated tests in self-report.

### AC-2 (Y25): unavailability helper

Add to `codex-delegate-enforcer.py`:

```python
def _codex_appears_unavailable(
    auth_path: Optional[Path] = None,
    now: Optional[datetime] = None,
    max_auth_age_hours: int = 24,
) -> tuple[bool, str]:
    """Return (True, reason) if Codex appears unusable, else (False, '')."""
    auth = auth_path or (Path.home() / ".codex" / "auth.json")
    if not auth.exists():
        return True, f"~/.codex/auth.json missing"
    age_hours = ((now or datetime.now()).timestamp() - auth.stat().st_mtime) / 3600
    if age_hours > max_auth_age_hours:
        return True, f"~/.codex/auth.json older than {max_auth_age_hours}h ({int(age_hours)}h)"
    return False, ""
```

Tests:

- `test_codex_unavailable_when_auth_missing(tmp_path)` — pass
  `auth_path=tmp_path/nonexistent.json` → True + "missing" in reason
- `test_codex_available_when_auth_recent(tmp_path)` — write tmp file
  with mtime=now → False, ""
- `test_codex_unavailable_when_auth_stale(tmp_path)` — write tmp file
  + os.utime to set mtime 48h ago → True + "older" in reason

### AC-3 (Y25): block message includes unavailability hint

In the existing block-message construction (likely in `decide()` or
`_format_deny_message()`), when the unavailability helper returns True,
prepend lines:
```
*** Codex appears unavailable: {reason}.
*** Run `codex login` or check ~/.codex/auth.json, then retry.
```
Then continue with the existing "no cover" message.

Test:
- `test_block_message_mentions_unavailability_when_codex_down(monkeypatch)` —
  monkeypatch `_codex_appears_unavailable` to return `(True, "test reason")`,
  build a no-cover deny scenario, capture stderr → assert it contains
  "appears unavailable" AND "test reason" AND existing "codex-inline-dual"
- `test_block_message_unchanged_when_codex_available(monkeypatch)` —
  monkeypatch to return `(False, "")` → assert stderr does NOT contain
  "appears unavailable"

### AC-4: Existing 220 tests still pass

```bash
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line
```

Some judge tests may need adjusting (AC-1) — that's by design.

### AC-5: Selftest still passes
`python .claude/scripts/dual-teams-selftest.py` → 6/6 PASS

## Test Commands

```bash
# 1. Judge axis tests
python -m pytest .claude/scripts/test_judge.py -v --tb=line

# 2. Enforcer invariants (with Y25 helper)
python -m pytest .claude/hooks/test_codex_delegate_enforcer_invariants.py -v --tb=line

# 3. Other suites
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line

# 4. Selftest
python .claude/scripts/dual-teams-selftest.py
```

## Implementation hints

- For Y21: the formula `scale / (scale + x)` is a Hill function /
  Michaelis-Menten — smooth, monotonic, asymptotic to 0 as x → ∞.
  Score@x=0 = 1.0, score@x=scale = 0.5, score@x=2*scale = 0.333,
  score@x=10*scale ≈ 0.091.
- For Y25 helper: pure function with optional kwargs for `auth_path`
  and `now` makes testing trivial. Default to real `~/.codex/auth.json`
  and `datetime.now()`.
- For Y25 message: find the existing deny-message construction —
  `grep -n "codex-inline-dual\|no cover\|blocked" .claude/hooks/codex-delegate-enforcer.py`.
  Wrap the message string with conditional prefix.
- Logging: add `logger.debug` entry/exit for Y25 helper. Y21 — keep
  existing logs.

## Self-report format

```
=== TASK Z12 SELF-REPORT ===
- status: pass | fail | blocker
- files modified: [list]
- new tests added: <count>
- net lines: <approx>
- Y21 approach: <1 line>
- Y25 approach: <1 line>
- existing 220 tests still pass: yes / no
- selftest: PASS / FAIL
- diff_size new behavior verified (added=2000, cap=500, 0 < score < 0.3): yes / no
- block message unavailability hint added: yes / no
- NOTE: <surprising>
- BLOCKER: <only if>
- Final commit SHA: <SHA>
=== END SELF-REPORT ===
```


---- END TASK SPECIFICATION ----
Return a short self-report at the end of your run using lines starting with
`NOTE:` for observations and `BLOCKER:` for unresolved problems.

codex
I’ll inspect the current worktree and the four allowed files first, then make the smallest scoped changes for the two acceptance areas.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "codex-inline-dual|no cover|blocked|def decide|format_deny|logger|from datetime|import datetime" .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer_invariants.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "def score_diff_size|score_diff_size|cap_lines" .claude/scripts/judge_axes.py .claude/scripts/test_judge.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 142ms:
.claude/scripts/judge_axes.py:181:def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
.claude/scripts/judge_axes.py:182:                    cap_lines: int = 500) -> AxisResult:
.claude/scripts/judge_axes.py:183:    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
.claude/scripts/judge_axes.py:184:    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
.claude/scripts/judge_axes.py:187:        score = max(0.0, 1.0 - (added / cap_lines))
.claude/scripts/judge_axes.py:188:        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
.claude/scripts/judge_axes.py:191:                               "cap_lines": cap_lines, "base": base})
.claude/scripts/judge_axes.py:193:        logger.exception("score_diff_size failed")
.claude/scripts/test_judge.py:30:    score_diff_size, score_lint_clean, score_logging_coverage,
.claude/scripts/test_judge.py:101:            res = score_diff_size(repo, cap_lines=500)
.claude/scripts/test_judge.py:111:            res = score_diff_size(repo, cap_lines=500)

 succeeded in 142ms:
.claude/hooks/test_codex_delegate_enforcer_invariants.py:385:        """DENY error message contains codex-inline-dual.py --describe + path."""
.claude/hooks/test_codex_delegate_enforcer_invariants.py:392:        self.assertIn("codex-inline-dual.py", reason)
.claude/hooks/codex-delegate-enforcer.py:23:    codex-inline-dual.py command for the blocked path.
.claude/hooks/codex-delegate-enforcer.py:31:import datetime
.claude/hooks/codex-delegate-enforcer.py:105:    ".claude/scripts/codex-inline-dual.py",
.claude/hooks/codex-delegate-enforcer.py:143:def _build_logger(project_dir: Path) -> logging.Logger:
.claude/hooks/codex-delegate-enforcer.py:144:    """Create enforcer logger: file if writable else stderr-only."""
.claude/hooks/codex-delegate-enforcer.py:145:    logger = logging.getLogger(HOOK_NAME)
.claude/hooks/codex-delegate-enforcer.py:146:    if logger.handlers:
.claude/hooks/codex-delegate-enforcer.py:147:        return logger
.claude/hooks/codex-delegate-enforcer.py:148:    logger.setLevel(logging.INFO)
.claude/hooks/codex-delegate-enforcer.py:156:        logger.addHandler(fh)
.claude/hooks/codex-delegate-enforcer.py:163:    logger.addHandler(sh)
.claude/hooks/codex-delegate-enforcer.py:164:    logger.propagate = False
.claude/hooks/codex-delegate-enforcer.py:165:    return logger
.claude/hooks/codex-delegate-enforcer.py:175:    logger = logging.getLogger(HOOK_NAME)
.claude/hooks/codex-delegate-enforcer.py:176:    logger.info("is_dual_teams_worktree.enter project=%s", project_dir)
.claude/hooks/codex-delegate-enforcer.py:183:            logger.debug("is_dual_teams_worktree.resolve-error path=%s exc=%s", current, exc)
.claude/hooks/codex-delegate-enforcer.py:186:            logger.info(
.claude/hooks/codex-delegate-enforcer.py:195:                logger.info(
.claude/hooks/codex-delegate-enforcer.py:201:            logger.debug("is_dual_teams_worktree.probe-error sentinel=%s exc=%s", sentinel, exc)
.claude/hooks/codex-delegate-enforcer.py:204:            logger.info("is_dual_teams_worktree.exit project=%s result=False", project_dir)
.claude/hooks/codex-delegate-enforcer.py:211:    logger = logging.getLogger(HOOK_NAME)
.claude/hooks/codex-delegate-enforcer.py:220:        logger.info("resolve_target.err raw=%r exc=%s", target_raw, exc)
.claude/hooks/codex-delegate-enforcer.py:225:        logger.info("resolve_target.escape resolved=%s", resolved)
.claude/hooks/codex-delegate-enforcer.py:245:    logger = logging.getLogger(HOOK_NAME)
.claude/hooks/codex-delegate-enforcer.py:250:                logger.debug("is_exempt.match pattern=%s", pattern)
.claude/hooks/codex-delegate-enforcer.py:260:                logger.debug("is_exempt.match pattern=%s (double-glob)", pattern)
.claude/hooks/codex-delegate-enforcer.py:264:            logger.debug("is_exempt.match pattern=%s", pattern)
.claude/hooks/codex-delegate-enforcer.py:275:    logger = logging.getLogger(HOOK_NAME)
.claude/hooks/codex-delegate-enforcer.py:276:    logger.info("requires_cover.enter rel=%s", rel_path)
.claude/hooks/codex-delegate-enforcer.py:278:        logger.info("requires_cover.exit rel=%s result=True reason=code-ext-wins", rel_path)
.claude/hooks/codex-delegate-enforcer.py:281:        logger.info("requires_cover.exit rel=%s result=False reason=non-code-exempt", rel_path)
.claude/hooks/codex-delegate-enforcer.py:283:    logger.info("requires_cover.exit rel=%s result=False reason=non-code-default", rel_path)
.claude/hooks/codex-delegate-enforcer.py:295:    logger = logging.getLogger(HOOK_NAME)
.claude/hooks/codex-delegate-enforcer.py:300:        logger.info("parse_result_fields.read_err path=%s exc=%s", result_path.name, exc)
.claude/hooks/codex-delegate-enforcer.py:319:    logger = logging.getLogger(HOOK_NAME)
.claude/hooks/codex-delegate-enforcer.py:323:        logger.info("parse_scope_fence.read_err path=%s exc=%s", task_path.name, exc)
.claude/hooks/codex-delegate-enforcer.py:385:    logger = logging.getLogger(HOOK_NAME)
.claude/hooks/codex-delegate-enforcer.py:394:        logger.info("resolve_task_file.err raw=%r exc=%s", raw, exc)
.claude/hooks/codex-delegate-enforcer.py:401:    logger = logging.getLogger(HOOK_NAME)
.claude/hooks/codex-delegate-enforcer.py:402:    logger.info("find_cover.enter target=%s", target_rel_posix)
.claude/hooks/codex-delegate-enforcer.py:406:            logger.info("find_cover.no-dir dir=%s", results_dir)
.claude/hooks/codex-delegate-enforcer.py:424:            logger.info("find_cover.no-results")
.claude/hooks/codex-delegate-enforcer.py:439:                logger.info("find_cover.symlink-escape path=%s", rpath.name)
.claude/hooks/codex-delegate-enforcer.py:446:                logger.info("find_cover.skip path=%s status=%s age=%.1fs",
.claude/hooks/codex-delegate-enforcer.py:471:                logger.info("find_cover.no-task-file result=%s", rpath.name)
.claude/hooks/codex-delegate-enforcer.py:477:                    logger.info("find_cover.empty-fence task=%s", tpath.name)
.claude/hooks/codex-delegate-enforcer.py:480:                    logger.info("find_cover.MATCH target=%s result=%s task=%s age=%.1fs",
.claude/hooks/codex-delegate-enforcer.py:483:                logger.info("find_cover.scope-miss target=%s task=%s entries=%d",
.claude/hooks/codex-delegate-enforcer.py:492:        logger.info("find_cover.exit target=%s covered=False reason=%s",
.claude/hooks/codex-delegate-enforcer.py:496:        logger.exception("find_cover.unexpected target=%s exc=%s", target_rel_posix, exc)
.claude/hooks/codex-delegate-enforcer.py:636:    logger = logging.getLogger(HOOK_NAME)
.claude/hooks/codex-delegate-enforcer.py:637:    logger.info("parse_bash_command.enter cmd=%r", command[:200])
.claude/hooks/codex-delegate-enforcer.py:660:        logger.info("parse_bash_command.exit decision=require_cover targets=%s", unique_targets)
.claude/hooks/codex-delegate-enforcer.py:662:    logger.info("parse_bash_command.exit decision=allow")
.claude/hooks/codex-delegate-enforcer.py:668:    logger = logging.getLogger(HOOK_NAME)
.claude/hooks/codex-delegate-enforcer.py:677:        logger.info("classify.dual-tooling cmd=%r", command[:120])
.claude/hooks/codex-delegate-enforcer.py:800:    logger = logging.getLogger(HOOK_NAME)
.claude/hooks/codex-delegate-enforcer.py:883:    logger = logging.getLogger(HOOK_NAME)
.claude/hooks/codex-delegate-enforcer.py:891:        logger.exception("skip_ledger.write_err exc=%s", exc)
.claude/hooks/codex-delegate-enforcer.py:893:        logger.exception("skip_ledger.unexpected exc=%s", exc)
.claude/hooks/codex-delegate-enforcer.py:902:def _build_block_message(blocked_path: str, reason_code: str) -> str:
.claude/hooks/codex-delegate-enforcer.py:914:        "Code Delegation Protocol: " + blocked_path + " blocked ("
.claude/hooks/codex-delegate-enforcer.py:917:        "  py -3 .claude/scripts/codex-inline-dual.py \\n"
.claude/hooks/codex-delegate-enforcer.py:918:        "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
.claude/hooks/codex-delegate-enforcer.py:919:        "    --scope " + blocked_path + " \\n"
.claude/hooks/codex-delegate-enforcer.py:927:def emit_deny(blocked: str, reason_code: str, project_dir: Path,
.claude/hooks/codex-delegate-enforcer.py:930:    logger = logging.getLogger(HOOK_NAME)
.claude/hooks/codex-delegate-enforcer.py:931:    message = _build_block_message(blocked, reason_code)
.claude/hooks/codex-delegate-enforcer.py:939:    logger.warning("emit_deny target=%s reason=%s", blocked, reason_code)
.claude/hooks/codex-delegate-enforcer.py:943:        "path": blocked,
.claude/hooks/codex-delegate-enforcer.py:988:def decide(payload: dict, project_dir: Path) -> bool:
.claude/hooks/codex-delegate-enforcer.py:990:    logger = logging.getLogger(HOOK_NAME)
.claude/hooks/codex-delegate-enforcer.py:993:    logger.info("decide.enter event=%s tool=%s", event, tool_name)
.claude/hooks/codex-delegate-enforcer.py:995:        logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
.claude/hooks/codex-delegate-enforcer.py:998:        logger.info("decide.passthrough reason=unknown-tool tool=%s", tool_name)
.claude/hooks/codex-delegate-enforcer.py:1001:        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
.claude/hooks/codex-delegate-enforcer.py:1011:    logger = logging.getLogger(HOOK_NAME)
.claude/hooks/codex-delegate-enforcer.py:1014:        logger.info("decide.passthrough reason=no-targets tool=%s", tool_name)
.claude/hooks/codex-delegate-enforcer.py:1019:            logger.info("decide.skip reason=unresolvable raw=%r", raw)
.claude/hooks/codex-delegate-enforcer.py:1023:            logger.info("decide.skip reason=outside-project path=%s", abs_path)
.claude/hooks/codex-delegate-enforcer.py:1026:            logger.info("decide.allow-target rel=%s reason=non-code-or-exempt", rel)
.claude/hooks/codex-delegate-enforcer.py:1033:            logger.info("decide.allow-target rel=%s reason=dual-teams-target abs=%s",
.claude/hooks/codex-delegate-enforcer.py:1043:            logger.info("decide.exit target=%s allowed=False reason=%s", rel, reason)
.claude/hooks/codex-delegate-enforcer.py:1045:        logger.info("decide.allow-target rel=%s reason=covered", rel)
.claude/hooks/codex-delegate-enforcer.py:1050:    logger.info("decide.exit allowed=True")
.claude/hooks/codex-delegate-enforcer.py:1056:    logger = logging.getLogger(HOOK_NAME)
.claude/hooks/codex-delegate-enforcer.py:1059:        logger.info("decide_bash.no-input")
.claude/hooks/codex-delegate-enforcer.py:1063:        logger.info("decide_bash.empty-command")
.claude/hooks/codex-delegate-enforcer.py:1067:        logger.info("decide_bash.allow reason=%s", parsed["reason"])
.claude/hooks/codex-delegate-enforcer.py:1075:        logger.info("decide_bash.require_cover-no-targets reason=%s", parsed["reason"])
.claude/hooks/codex-delegate-enforcer.py:1081:            logger.info("decide_bash.exit allowed=False reason=opaque-target target=%s", target)
.claude/hooks/codex-delegate-enforcer.py:1090:            logger.info("decide_bash.allow-target rel=%s reason=dual-teams-target", rel)
.claude/hooks/codex-delegate-enforcer.py:1099:            logger.info("decide_bash.exit target=%s allowed=False reason=%s", rel, reason)
.claude/hooks/codex-delegate-enforcer.py:1105:    logger.info("decide_bash.exit allowed=True")
.claude/hooks/codex-delegate-enforcer.py:1112:    logger = _build_logger(project_dir)
.claude/hooks/codex-delegate-enforcer.py:1113:    logger.info("main.enter pid=%d", os.getpid())
.claude/hooks/codex-delegate-enforcer.py:1117:            logger.info("main.empty-stdin passthrough")
.claude/hooks/codex-delegate-enforcer.py:1122:            logger.info("main.malformed-json exc=%s", exc)
.claude/hooks/codex-delegate-enforcer.py:1125:            logger.info("main.non-dict-payload type=%s", type(payload).__name__)
.claude/hooks/codex-delegate-enforcer.py:1129:        logger.exception("main.unexpected exc=%s", exc)
.claude/hooks/codex-delegate-enforcer.py:1131:        logger.info("main.exit")

 succeeded in 266ms:
codex
The worktree is clean. I found the linear diff-size formula and the existing deny-message builder; next I’m reading the surrounding code and tests so the edits match local style.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/scripts/judge_axes.py | Select-Object -Skip 160 -First 50' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/scripts/test_judge.py | Select-Object -First 170' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/hooks/codex-delegate-enforcer.py | Select-Object -First 130' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/hooks/codex-delegate-enforcer.py | Select-Object -Skip 880 -First 85' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/hooks/test_codex_delegate_enforcer_invariants.py | Select-Object -First 460' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 189ms:
        _ensure_untracked_visible(worktree)
        proc = subprocess.run(["git", "diff", "--numstat", base],
                              cwd=str(worktree), check=False, capture_output=True,
                              text=True, timeout=30)
        added = removed = 0
        for line in proc.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                added += int(parts[0])
                removed += int(parts[1])
        _log(logging.DEBUG, "exit: _git_diff_numstat", added=added, removed=removed)
        return added, removed
    except subprocess.TimeoutExpired:
        _log(logging.WARNING, "_git_diff_numstat timeout", worktree=str(worktree))
        return 0, 0
    except Exception:
        logger.exception("_git_diff_numstat failed")
        return 0, 0


def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
                    cap_lines: int = 500) -> AxisResult:
    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
    try:
        added, removed = _git_diff_numstat(worktree, base)
        score = max(0.0, 1.0 - (added / cap_lines))
        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
        return AxisResult(name="diff_size", score=score, weight=weight,
                          raw={"added": added, "removed": removed,
                               "cap_lines": cap_lines, "base": base})
    except Exception:
        logger.exception("score_diff_size failed")
        raise


_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")


def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
    """Return unified diff text for working-tree-vs-base (``git diff <base>``).

    Captures committed + staged + unstaged + intent-to-add diffs; calls
    ``_ensure_untracked_visible`` first so untracked .py files are included.
    """
    _log(logging.DEBUG, "entry: _git_diff_text", worktree=str(worktree), base=base)
    try:
        _ensure_untracked_visible(worktree)
        proc = subprocess.run(["git", "diff", base, "--", "*.py"],

 succeeded in 193ms:
#!/usr/bin/env python3
"""Unit tests for judge.py / judge_axes.py (AC9 >=10 tests).

Run: python .claude/scripts/test_judge.py

Uses unittest + pytest-style direct invocation. Zero deps beyond stdlib
so it runs in the judge's own CI sandbox without tool installs.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import judge  # noqa: E402
import judge_axes  # noqa: E402
from judge_axes import (  # noqa: E402
    AxisResult, TestRun, biggest_delta_rationale, decide_winner,
    score_diff_size, score_lint_clean, score_logging_coverage,
    score_tests_passed, weighted_aggregate,
)


# ------------------------ helpers ------------------------ #


def _init_git_repo(repo: Path) -> None:
    """Bare-minimum git repo with one empty initial commit."""
    for args in (
        ["git", "init", "-q", "-b", "main"],
        ["git", "config", "user.email", "t@example.com"],
        ["git", "config", "user.name", "t"],
        ["git", "commit", "-q", "--allow-empty", "-m", "init"],
    ):
        subprocess.run(args, cwd=str(repo), check=True, capture_output=True)


def _add_file(repo: Path, rel: str, content: str, commit: bool = False) -> Path:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    if commit:
        subprocess.run(["git", "add", rel], cwd=str(repo), check=True,
                       capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", f"add {rel}"],
                       cwd=str(repo), check=True, capture_output=True)
    return p


# ------------------------ tests_passed ------------------------ #


class TestTestsPassed(unittest.TestCase):
    def test_all_pass(self) -> None:
        runs = [TestRun(command="t1", exit_code=0, duration_s=0.1),
                TestRun(command="t2", exit_code=0, duration_s=0.1)]
        res = score_tests_passed(runs)
        self.assertAlmostEqual(res.score, 1.0)
        self.assertFalse(res.skipped)

    def test_some_pass(self) -> None:
        runs = [TestRun(command="t1", exit_code=0, duration_s=0.1),
                TestRun(command="t2", exit_code=1, duration_s=0.1),
                TestRun(command="t3", exit_code=0, duration_s=0.1)]
        res = score_tests_passed(runs)
        self.assertAlmostEqual(res.score, 2 / 3)

    def test_none_pass(self) -> None:
        runs = [TestRun(command="t1", exit_code=1, duration_s=0.1)]
        res = score_tests_passed(runs)
        self.assertEqual(res.score, 0.0)

    def test_empty_skipped(self) -> None:
        res = score_tests_passed([])
        self.assertTrue(res.skipped)
        self.assertEqual(res.skip_reason, "no test commands")


# ------------------------ diff_size ------------------------ #


class TestDiffSize(unittest.TestCase):
    def test_inverse_normalization(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)
            _add_file(repo, "a.py", "# pre\n", commit=True)
            # Add 50 lines uncommitted
            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
            res = score_diff_size(repo, cap_lines=500)
            # ~50 added, cap 500 => 1 - 50/500 = 0.9
            self.assertGreater(res.score, 0.85)
            self.assertLess(res.score, 0.95)
            self.assertEqual(res.raw["added"], 50)

    def test_empty_diff_max_score(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)
            res = score_diff_size(repo, cap_lines=500)
            self.assertAlmostEqual(res.score, 1.0)
            self.assertEqual(res.raw["added"], 0)


# ------------------------ logging_coverage ------------------------ #


class TestLoggingCoverage(unittest.TestCase):
    def test_function_with_logger(self) -> None:
        diff = textwrap.dedent("""\
            diff --git a/x.py b/x.py
            @@ -0,0 +1,3 @@
            +def foo():
            +    logger.info("hi")
            +    return 1
            """)
        res = score_logging_coverage(Path("."), diff_text=diff)
        self.assertAlmostEqual(res.score, 1.0)
        self.assertEqual(res.raw["covered"], 1)

    def test_function_without_logger(self) -> None:
        diff = textwrap.dedent("""\
            diff --git a/x.py b/x.py
            @@ -0,0 +1,3 @@
            +def foo():
            +    x = 1
            +    return x
            """)
        res = score_logging_coverage(Path("."), diff_text=diff)
        self.assertAlmostEqual(res.score, 0.0)
        self.assertEqual(res.raw["covered"], 0)

    def test_edge_no_new_functions(self) -> None:
        diff = "diff --git a/x.py b/x.py\n+x = 1\n"
        res = score_logging_coverage(Path("."), diff_text=diff)
        self.assertTrue(res.skipped)
        self.assertEqual(res.skip_reason, "no new python functions")

    def test_mixed_functions(self) -> None:
        diff = textwrap.dedent("""\
            diff --git a/x.py b/x.py
            @@ -0,0 +1,6 @@
            +def foo():
            +    logger.info("ok")
            +    return 1
            +def bar():
            +    return 2
            +
            """)
        res = score_logging_coverage(Path("."), diff_text=diff)
        self.assertAlmostEqual(res.score, 0.5)
        self.assertEqual(res.raw["covered"], 1)
        self.assertEqual(res.raw["total"], 2)


# ------------------------ lint_clean ------------------------ #


class TestLintClean(unittest.TestCase):

 succeeded in 196ms:
#!/usr/bin/env python3
"""Codex Delegate Enforcer - Always-Dual PreToolUse hook (CLAUDE.md).

Z1 - Four Invariants closing 12 bypass vectors:

I1. Extension wins. is_code_extension() is checked BEFORE is_exempt().
    Path exemptions (work/**, worktrees/**, .claude/scripts/**) only
    protect non-code extensions. A .py file in work/ requires cover.

I2. Bash counts. PreToolUse(Bash) tokenizes the command; mutating verbs
    (cp/mv/sed -i/redirect/python script.py/PowerShell Set-Content/...)
    against code paths require cover. A whitelist exempts read-only verbs
    (ls/cat/git status/pytest/...) and the project's own dual tooling
    (codex-ask, codex-implement, dual-teams-spawn, ...).

I3. Path-exact coverage. find_cover(target) returns True only if some
    artifact's Scope Fence explicitly lists the target (with glob support
    via fnmatch). No temporal carryover from unrelated stages.

I4. Skip-token audit + actionable block messages. Every allow/deny
    decision is appended to work/codex-implementations/skip-ledger.jsonl
    (best-effort, never blocks). DENY messages include a ready-to-run
    codex-inline-dual.py command for the blocked path.

Edit/Write/MultiEdit on a code file that is NOT exempt -> require a fresh
(<15 min) work/codex-implementations/task-*-result.md with status=pass
whose Scope Fence covers the target. Missing cover -> deny via PreToolUse
JSON. Fail-open on any unexpected exception.
"""
from __future__ import annotations
import datetime
import fnmatch
import json
import logging
import os
import re
import shlex
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Optional

if sys.platform == "win32":
    for _stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")

HOOK_NAME = "codex-delegate-enforcer"
RESULT_MAX_AGE_SECONDS: int = 15 * 60
MAX_RESULT_FILES_TO_SCAN: int = 50
CODEX_IMPLEMENTATIONS_DIR = "work/codex-implementations"
CODEX_TASKS_DIR = "work/codex-primary/tasks"
SKIP_LEDGER_REL = "work/codex-implementations/skip-ledger.jsonl"

# I1 - delegated code extensions. Frozenset for O(1) lookup.
# Z7-V02: .ipynb added - Jupyter notebooks contain executable code cells.
CODE_EXTENSIONS: frozenset = frozenset({
    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
    ".sh", ".bash", ".zsh", ".go", ".rs", ".rb", ".java", ".kt",
    ".swift", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php",
    ".sql", ".lua", ".r", ".ipynb",
})

# I1 - exempt path globs. ONLY apply to non-code extensions.
EXEMPT_PATTERNS: tuple = (
    ".claude/memory/**", "work/**", "CLAUDE.md", "AGENTS.md",
    "README.md", "CHANGELOG.md", "LICENSE", ".gitignore",
    ".claude/settings.json", ".claude/ops/*.yaml", ".mcp.json",
    ".claude/adr/**/*.md", ".claude/guides/**/*.md",
    ".claude/skills/**/*.md",
    "worktrees/**",
)

# Regexes - compiled at module scope.
_STATUS_RE = re.compile(r"(?i)status\s*[:=]\s*([A-Za-z0-9_-]+)")
_TASK_FILE_RE = re.compile(r"(?i)task[_\s-]*file\s*[:=]\s*(.+)")
_SCOPE_FENCE_HEADING_RE = re.compile(r"(?im)^##\s+Scope\s+Fence\s*$")
_NEXT_HEADING_RE = re.compile(r"(?m)^##\s+")
_ALLOWED_SECTION_RE = re.compile(
    r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\Z)"
)
_TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
_RESULT_NAME_RE = re.compile(r"task-(.+?)-result\.md$")

# I2 - Bash classification tables.
_BASH_READONLY_VERBS: frozenset = frozenset({
    "ls", "cat", "head", "tail", "less", "more", "wc", "file", "stat",
    "find", "grep", "rg", "ag", "sort", "uniq", "cut", "tr", "diff",
    "cmp", "tree", "echo", "printf", "true", "false", "pwd", "which",
    "whoami", "date", "env", "type", "command", "id", "hostname",
})

_BASH_TEST_RUNNERS: frozenset = frozenset({
    "pytest", "unittest", "mypy", "ruff", "tsc", "eslint", "prettier",
    "cargo", "go",
})

_BASH_PACKAGE_MANAGERS: frozenset = frozenset({
    "uv", "pip", "npm", "yarn", "pnpm",
})

_BASH_DUAL_TOOLING: frozenset = frozenset({
    ".claude/scripts/codex-implement.py",
    ".claude/scripts/codex-wave.py",
    ".claude/scripts/codex-inline-dual.py",
    ".claude/scripts/dual-teams-spawn.py",
    ".claude/scripts/dual-teams-selftest.py",
    ".claude/scripts/judge.py",
    ".claude/scripts/judge_axes.py",
    ".claude/scripts/codex-ask.py",
    ".claude/scripts/codex-scope-check.py",
    ".claude/scripts/codex-pool.py",
    ".claude/scripts/dual-history-archive.py",
    ".claude/scripts/verdict-summarizer.py",
    ".claude/scripts/worktree-cleaner.py",
    ".claude/scripts/codex-cost-report.py",
    ".claude/scripts/sync-template-to-target.py",
})

_BASH_MUTATING_VERBS: frozenset = frozenset({
    "cp", "mv", "install", "rsync", "rm", "tee", "touch", "ln", "chmod",
    "chown", "dd",
})

_BASH_INPLACE_VERBS: frozenset = frozenset({"sed", "awk", "perl"})

_BASH_INTERPRETERS: frozenset = frozenset({
    "python", "python3", "py", "bash", "sh", "zsh", "node", "deno",
    "ruby", "perl", "lua",
})

 succeeded in 189ms:
def _append_skip_ledger(project_dir: Path, entry: dict) -> None:
    """Append one JSON line to skip-ledger.jsonl. Best-effort."""
    logger = logging.getLogger(HOOK_NAME)
    try:
        ledger = project_dir / SKIP_LEDGER_REL
        ledger.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(entry, ensure_ascii=False)
        with ledger.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError as exc:
        logger.exception("skip_ledger.write_err exc=%s", exc)
    except Exception as exc:
        logger.exception("skip_ledger.unexpected exc=%s", exc)


def _now_iso() -> str:
    """Return UTC timestamp in ISO-8601 format."""
    return datetime.datetime.now(datetime.timezone.utc).replace(
        microsecond=0).isoformat()


def _build_block_message(blocked_path: str, reason_code: str) -> str:
    """Build the actionable DENY message for emit_deny."""
    reason_text = {
        "no-results": "no codex-implement result found",
        "no-results-dir": "work/codex-implementations/ does not exist",
        "stale": "all codex-implement results older than 15 min",
        "fail-status": "most recent matching result has status != pass",
        "scope-miss": "no recent pass result covers this exact path",
        "parse-error": "could not parse codex-implement result",
        "bash-no-cover": "Bash command would mutate code without cover",
    }.get(reason_code, reason_code)
    msg = (
        "Code Delegation Protocol: " + blocked_path + " blocked ("
        + reason_text + ").\n\n"
        "To start the dual-implement track for this path, run:\n\n"
        "  py -3 .claude/scripts/codex-inline-dual.py \\n"
        "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
        "    --scope " + blocked_path + " \\n"
        "    --test \"py -3 -m pytest -q\"\n\n"
        "Then retry your edit. For multi-file tasks, use:\n"
        "  py -3 .claude/scripts/dual-teams-spawn.py --tasks <task.md> ...\n"
    )
    return msg


def emit_deny(blocked: str, reason_code: str, project_dir: Path,
              tool_name: str = "Edit") -> None:
    """Print the PreToolUse deny JSON to stdout and append ledger entry."""
    logger = logging.getLogger(HOOK_NAME)
    message = _build_block_message(blocked, reason_code)
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }
    logger.warning("emit_deny target=%s reason=%s", blocked, reason_code)
    _append_skip_ledger(project_dir, {
        "ts": _now_iso(),
        "tool": tool_name,
        "path": blocked,
        "decision": "deny",
        "reason": reason_code,
    })
    print(json.dumps(payload, ensure_ascii=False))


# ----------------------------------------------------------------------
# Tool dispatch
# ----------------------------------------------------------------------

def extract_targets(payload: dict) -> list:
    """Collect every file path this Edit/Write/MultiEdit/NotebookEdit call edits."""
    if not isinstance(payload, dict):
        return []
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return []
    paths: list = []
    if tool_name in {"Edit", "Write", "NotebookEdit"}:
        p = tool_input.get("file_path") or tool_input.get("notebook_path")
        if isinstance(p, str) and p:

 succeeded in 187ms:
#!/usr/bin/env python3
"""Tests for Z1 four-invariant enforcer (codex-delegate-enforcer.py).

Covers all 4 invariants:
- AC-1: I1 вЂ” extension wins (path exemption is non-code only)
- AC-2: I2 вЂ” Bash counts (effect-based interception)
- AC-3: I3 вЂ” path-exact coverage (no temporal carryover)
- AC-4: I4 вЂ” skip-token ledger + actionable block messages
- AC-5: regression вЂ” existing 36 tests still pass + selftest
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENFORCER_PATH = HERE / "codex-delegate-enforcer.py"


def _load_module():
    """Import codex-delegate-enforcer.py as a module (hyphen in filename)."""
    spec = importlib.util.spec_from_file_location(
        "codex_delegate_enforcer_z1", ENFORCER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Base(unittest.TestCase):
    """Shared fixture: isolated project root with results + tasks dirs."""

    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module()

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="z1-enforcer-")
        self.root = Path(self.tmpdir).resolve()
        (self.root / ".claude" / "hooks").mkdir(parents=True)
        (self.root / "work" / "codex-primary" / "tasks").mkdir(parents=True)
        (self.root / "work" / "codex-implementations").mkdir(parents=True)
        (self.root / ".claude" / "scripts").mkdir(parents=True)
        (self.root / "src").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ----- fixture helpers -----

    def _write_task(self, task_id: str, fence_paths: list) -> Path:
        """Write a task-N.md with given Scope Fence allowed paths."""
        tf = self.root / "work" / "codex-primary" / "tasks" / (
            "T" + task_id + "-test.md"
        )
        fence_block = "\n".join("- `" + p + "`" for p in fence_paths)
        tf.write_text(
            "---\nexecutor: codex\n---\n\n# Task T" + task_id + "\n\n"
            "## Your Task\ntest\n\n"
            "## Scope Fence\n"
            "**Allowed paths (may be written):**\n"
            + fence_block + "\n\n"
            "**Forbidden paths:**\n- other/\n\n"
            "## Acceptance Criteria\n- [ ] AC1\n",
            encoding="utf-8",
        )
        return tf

    def _write_result(self, task_id: str, status: str, age_seconds: float = 0) -> Path:
        rf = self.root / "work" / "codex-implementations" / (
            "task-" + task_id + "-result.md"
        )
        task_file_rel = "work/codex-primary/tasks/T" + task_id + "-test.md"
        rf.write_text(
            "# Result T" + task_id + "\n\n"
            "- status: " + status + "\n"
            "- task_file: " + task_file_rel + "\n\n"
            "## Diff\n(none)\n",
            encoding="utf-8",
        )
        if age_seconds > 0:
            old = time.time() - age_seconds
            os.utime(rf, (old, old))
        return rf

    def _edit_payload(self, file_path: str) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": file_path,
                           "old_string": "a", "new_string": "b"},
        }

    def _bash_payload(self, command: str) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command},
        }

    def _decide(self, payload: dict):
        """Run decide() in-process; return (allowed, stdout)."""
        with contextlib.redirect_stdout(io.StringIO()) as out:
            allowed = self.mod.decide(payload, self.root)
        return allowed, out.getvalue()

    def _assert_deny(self, allowed: bool, stdout: str):
        self.assertFalse(allowed, "expected DENY but got allow. stdout=" + stdout)
        self.assertTrue(stdout.strip(), "expected deny JSON on stdout")
        parsed = json.loads(stdout)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")

    def _assert_allow(self, allowed: bool, stdout: str):
        self.assertTrue(allowed, "expected ALLOW but got deny. stdout=" + stdout)



# ======================================================================
# AC-1 вЂ” Invariant 1: Extension wins
# ======================================================================
class TestI1ExtensionWins(_Base):
    """Code extensions ALWAYS require cover, regardless of path glob."""

    def test_work_py_requires_cover(self):
        """work/sync-template-to-target.py -> DENY (was previously ALLOW)."""
        target = "work/sync-template-to-target.py"
        (self.root / "work" / "sync-template-to-target.py").write_text("# x\n",
                                                                      encoding="utf-8")
        allowed, out = self._decide(self._edit_payload(target))
        self._assert_deny(allowed, out)

    def test_work_md_still_exempt(self):
        """work/notes.md -> ALLOW (non-code, exempt)."""
        target = "work/notes.md"
        (self.root / "work" / "notes.md").write_text("notes\n", encoding="utf-8")
        allowed, out = self._decide(self._edit_payload(target))
        self._assert_allow(allowed, out)

    def test_claude_scripts_py_requires_cover(self):
        """.claude/scripts/foo.py -> DENY."""
        target = ".claude/scripts/foo.py"
        (self.root / target).write_text("# foo\n", encoding="utf-8")
        allowed, out = self._decide(self._edit_payload(target))
        self._assert_deny(allowed, out)

    def test_worktrees_py_outside_dual_requires_cover(self):
        """worktrees/random/foo.py (no .dual-base-ref) -> DENY."""
        target = "worktrees/random/foo.py"
        (self.root / "worktrees" / "random").mkdir(parents=True)
        (self.root / target).write_text("# foo\n", encoding="utf-8")
        allowed, out = self._decide(self._edit_payload(target))
        self._assert_deny(allowed, out)

    def test_worktrees_dual_teams_py_allow(self):
        """worktrees/feature/.dual-base-ref present -> ALLOW (Y6/Y11 preserved)."""
        wt = self.root / "worktrees" / "feature" / "claude" / "task-A"
        wt.mkdir(parents=True)
        (wt / ".dual-base-ref").write_text("main\n", encoding="utf-8")
        target_abs = wt / "foo.py"
        target_abs.write_text("# foo\n", encoding="utf-8")
        target_rel = target_abs.relative_to(self.root).as_posix()
        allowed, out = self._decide(self._edit_payload(target_rel))
        self._assert_allow(allowed, out)



# ======================================================================
# AC-2 вЂ” Invariant 2: Bash counts
# ======================================================================
class TestI2BashCounts(_Base):
    """Bash command effects on code paths require cover."""

    def test_bash_python_script_in_work_requires_cover(self):
        cmd = "py -3 work/sync-template-to-target.py"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_pytest_allow(self):
        cmd = "pytest tests/"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_cp_code_to_code_requires_cover(self):
        cmd = "cp src/a.py src/b.py"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_cp_md_to_md_allow(self):
        cmd = "cp README.md /tmp/"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_sed_i_on_code_requires_cover(self):
        cmd = "sed -i 's/x/y/' src/auth.py"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_sed_i_on_md_allow(self):
        cmd = "sed -i 's/x/y/' work/notes.md"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_redirect_to_code_requires_cover(self):
        cmd = "echo \"x\" > src/foo.py"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_heredoc_to_code_requires_cover(self):
        cmd = "cat > src/foo.py << EOF\nbody\nEOF"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_powershell_set_content_code_requires_cover(self):
        cmd = "powershell -Command \"Set-Content -Path src/foo.py -Value '...'\""
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_powershell_set_content_md_allow(self):
        cmd = "powershell -Command \"Set-Content -Path notes.md -Value '...'\""
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_git_apply_requires_cover(self):
        cmd = "git apply patch.diff"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_git_checkout_code_file_requires_cover(self):
        cmd = "git checkout main src/auth.py"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_codex_ask_allow(self):
        cmd = "py -3 .claude/scripts/codex-ask.py \"hello\""
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_dual_teams_spawn_allow(self):
        cmd = "py -3 .claude/scripts/dual-teams-spawn.py --tasks T1.md"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_python_dash_c_open_write_requires_cover(self):
        cmd = "python -c \"open('src/x.py','w').write('...')\""
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)

    def test_bash_python_dash_c_print_allow(self):
        cmd = "python -c \"print(2+2)\""
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_ls_allow(self):
        cmd = "ls -la work/"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_git_status_allow(self):
        cmd = "git status"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_allow(allowed, out)

    def test_bash_python_dash_alone_requires_cover(self):
        """python - (stdin) is opaque -> always require cover."""
        cmd = "python - < script.py"
        allowed, out = self._decide(self._bash_payload(cmd))
        self._assert_deny(allowed, out)



# ======================================================================
# AC-3 вЂ” Invariant 3: Path-exact coverage (no temporal carryover)
# ======================================================================
class TestI3PathExactCoverage(_Base):
    """Codex artifact must EXPLICITLY list the target path."""

    def test_artifact_covers_path_a_blocks_path_b(self):
        """Artifact lists src/a.py; Edit on src/b.py -> DENY."""
        self._write_task("aa", ["src/a.py"])
        self._write_result("aa", "pass")
        (self.root / "src" / "b.py").write_text("# b\n", encoding="utf-8")
        allowed, out = self._decide(self._edit_payload("src/b.py"))
        self._assert_deny(allowed, out)

    def test_artifact_covers_path_a_allows_path_a(self):
        """Same artifact; Edit on src/a.py -> ALLOW."""
        self._write_task("ab", ["src/a.py"])
        self._write_result("ab", "pass")
        (self.root / "src" / "a.py").write_text("# a\n", encoding="utf-8")
        allowed, out = self._decide(self._edit_payload("src/a.py"))
        self._assert_allow(allowed, out)

    def test_glob_in_scope_fence_matches(self):
        """Artifact lists src/auth/*.py; Edit on src/auth/login.py -> ALLOW."""
        (self.root / "src" / "auth").mkdir(parents=True)
        (self.root / "src" / "auth" / "login.py").write_text("# login\n",
                                                             encoding="utf-8")
        self._write_task("gl", ["src/auth/*.py"])
        self._write_result("gl", "pass")
        allowed, out = self._decide(self._edit_payload("src/auth/login.py"))
        self._assert_allow(allowed, out)

    def test_stale_artifact_outside_15min_blocks(self):
        """Artifact older than 15 min covering exact path -> DENY."""
        self._write_task("st", ["src/a.py"])
        self._write_result("st", "pass", age_seconds=20 * 60)
        (self.root / "src" / "a.py").write_text("# a\n", encoding="utf-8")
        allowed, out = self._decide(self._edit_payload("src/a.py"))
        self._assert_deny(allowed, out)

    def test_failed_artifact_blocks_even_if_covers_path(self):
        """status: fail covering path -> DENY."""
        self._write_task("fa", ["src/a.py"])
        self._write_result("fa", "fail")
        (self.root / "src" / "a.py").write_text("# a\n", encoding="utf-8")
        allowed, out = self._decide(self._edit_payload("src/a.py"))
        self._assert_deny(allowed, out)



# ======================================================================
# AC-4 вЂ” Invariant 4: Skip-token ledger + actionable block messages
# ======================================================================
class TestI4Ledger(_Base):
    """Skip-ledger.jsonl audit + actionable DENY messages."""

    def _read_ledger(self):
        ledger = self.root / "work" / "codex-implementations" / "skip-ledger.jsonl"
        if not ledger.exists():
            return []
        text = ledger.read_text(encoding="utf-8").strip()
        return [json.loads(ln) for ln in text.splitlines() if ln.strip()]

    def test_skip_ledger_appends_on_allow(self):
        """Allowed Edit appends one JSONL line with decision=allow + reason."""
        self._write_task("la", ["src/a.py"])
        self._write_result("la", "pass")
        (self.root / "src" / "a.py").write_text("# a\n", encoding="utf-8")
        before = len(self._read_ledger())
        allowed, _ = self._decide(self._edit_payload("src/a.py"))
        self.assertTrue(allowed)
        after = self._read_ledger()
        self.assertEqual(len(after) - before, 1, "expected exactly 1 new ledger line")
        last = after[-1]
        self.assertEqual(last["decision"], "allow")
        self.assertIn("reason", last)
        self.assertEqual(last["path"], "src/a.py")

    def test_skip_ledger_appends_on_deny(self):
        """Denied Edit appends one JSONL line with decision=deny + reason."""
        (self.root / "src" / "a.py").write_text("# a\n", encoding="utf-8")
        before = len(self._read_ledger())
        allowed, _ = self._decide(self._edit_payload("src/a.py"))
        self.assertFalse(allowed)
        after = self._read_ledger()
        self.assertEqual(len(after) - before, 1)
        last = after[-1]
        self.assertEqual(last["decision"], "deny")
        self.assertIn("reason", last)

    def test_skip_ledger_jsonl_parseable(self):
        """All ledger lines parse as valid JSON with required keys."""
        # Trigger a few decisions.
        (self.root / "src" / "a.py").write_text("# a\n", encoding="utf-8")
        self._decide(self._edit_payload("src/a.py"))  # deny
        self._decide(self._edit_payload("CLAUDE.md"))  # allow
        ledger = self._read_ledger()
        self.assertGreaterEqual(len(ledger), 2)
        required = {"ts", "tool", "decision", "reason"}
        for entry in ledger:
            self.assertTrue(required.issubset(entry.keys()),
                            "missing keys in entry: " + str(entry))

    def test_block_message_includes_inline_dual_command(self):
        """DENY error message contains codex-inline-dual.py --describe + path."""
        target = "src/auth.py"
        (self.root / "src" / "auth.py").write_text("# a\n", encoding="utf-8")
        allowed, stdout = self._decide(self._edit_payload(target))
        self.assertFalse(allowed)
        parsed = json.loads(stdout)
        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("codex-inline-dual.py", reason)
        self.assertIn("--describe", reason)
        self.assertIn(target, reason)



# ======================================================================
# AC-5 вЂ” Regression: existing tests + selftest still pass
# ======================================================================
class TestRegression(unittest.TestCase):
    """Regression suite вЂ” runs the existing 36-test suite and selftest."""

    def test_existing_tests_still_pass(self):
        """Run pytest on test_codex_delegate_enforcer.py вЂ” exit 0."""
        existing = HERE / "test_codex_delegate_enforcer.py"
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(existing), "-q",
             "--tb=line", "--no-header"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=120,
        )
        self.assertEqual(
            result.returncode, 0,
            "existing tests failed: stdout=" + result.stdout
            + " stderr=" + result.stderr,
        )

    def test_dual_teams_selftest_still_passes(self):
        """Run dual-teams-selftest.py вЂ” exit 0."""
        # Walk up to project root (the worktree itself).
        project_root = HERE.parent.parent
        selftest = project_root / ".claude" / "scripts" / "dual-teams-selftest.py"
        if not selftest.is_file():
            self.skipTest("dual-teams-selftest.py not found at " + str(selftest))
        result = subprocess.run(
            [sys.executable, str(selftest)],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=180, cwd=str(project_root),
        )
        self.assertEqual(
            result.returncode, 0,
            "dual-teams-selftest failed: stdout=" + result.stdout[-1000:]
            + " stderr=" + result.stderr[-500:],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "permissionDecisionReason|stderr|emit_deny|codex-inline-dual|appears unavailable|block_message" .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_gate.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/hooks/codex-delegate-enforcer.py | Select-Object -Skip 980 -First 135' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"datetime\\.\" .claude/hooks/codex-delegate-enforcer.py" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"diff_size|score_diff_size|cap_lines|0\\.0|0\\.9\" .claude/scripts/test_judge.py" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 136ms:
.claude/hooks/test_codex_delegate_enforcer_invariants.py:384:    def test_block_message_includes_inline_dual_command(self):
.claude/hooks/test_codex_delegate_enforcer_invariants.py:385:        """DENY error message contains codex-inline-dual.py --describe + path."""
.claude/hooks/test_codex_delegate_enforcer_invariants.py:391:        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
.claude/hooks/test_codex_delegate_enforcer_invariants.py:392:        self.assertIn("codex-inline-dual.py", reason)
.claude/hooks/test_codex_delegate_enforcer_invariants.py:416:            + " stderr=" + result.stderr,
.claude/hooks/test_codex_delegate_enforcer_invariants.py:434:            + " stderr=" + result.stderr[-500:],
.claude/hooks/test_codex_delegate_enforcer.py:72:        """Invoke enforcer as subprocess; return (exit_code, stdout, stderr)."""
.claude/hooks/test_codex_delegate_enforcer.py:81:        return result.returncode, result.stdout, result.stderr
.claude/hooks/test_codex_delegate_enforcer.py:154:    def _assert_allow(self, code: int, stdout: str, stderr: str) -> None:
.claude/hooks/test_codex_delegate_enforcer.py:155:        self.assertEqual(code, 0, msg="expected exit 0. stderr=" + stderr)
.claude/hooks/test_codex_delegate_enforcer.py:170:    def _assert_deny(self, code: int, stdout: str, stderr: str) -> None:
.claude/hooks/test_codex_delegate_enforcer.py:171:        self.assertEqual(code, 0, msg="expected exit 0 (deny via JSON). stderr=" + stderr)
.claude/hooks/test_codex_delegate_enforcer.py:176:        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
.claude/hooks/test_codex_delegate_enforcer.py:261:        # the point is the script didn't blow up (no traceback in stderr).
.claude/hooks/test_codex_delegate_enforcer.py:277:        self.assertNotIn("Traceback", result.stderr)
.claude/hooks/test_enforcer_live_attacks.py:13:             (in stdout reason or stderr log).
.claude/hooks/test_enforcer_live_attacks.py:94:        f"stderr={result.stderr[-500:]!r}"
.claude/hooks/test_enforcer_live_attacks.py:97:        reason = deny["hookSpecificOutput"].get("permissionDecisionReason", "")
.claude/hooks/test_enforcer_live_attacks.py:99:                or must_contain_in_reason in result.stderr), (
.claude/hooks/test_enforcer_live_attacks.py:101:            f"or stderr log; reason={reason!r} stderr={result.stderr[-500:]!r}"
.claude/hooks/test_enforcer_live_attacks.py:109:        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
.claude/hooks/test_codex_gate.py:59:        """Invoke gate as subprocess; return (exit_code, stderr)."""
.claude/hooks/test_codex_gate.py:67:        return result.returncode, result.stderr
.claude/hooks/test_codex_gate.py:132:        code, stderr = self._run_gate(self._payload(self.target_rel))
.claude/hooks/test_codex_gate.py:133:        self.assertEqual(code, 2, msg=f"expected block, got stderr:\n{stderr}")
.claude/hooks/test_codex_gate.py:134:        self.assertIn("stale", stderr.lower())
.claude/hooks/test_codex_gate.py:139:        code, stderr = self._run_gate(self._payload(self.target_rel))
.claude/hooks/test_codex_gate.py:140:        self.assertEqual(code, 0, msg=f"expected allow, got stderr:\n{stderr}")
.claude/hooks/test_codex_gate.py:141:        self.assertIn("codex-ask", stderr)
.claude/hooks/test_codex_gate.py:147:        code, stderr = self._run_gate(self._payload(self.target_rel))
.claude/hooks/test_codex_gate.py:148:        self.assertEqual(code, 0, msg=f"expected allow, got stderr:\n{stderr}")
.claude/hooks/test_codex_gate.py:149:        self.assertIn("codex-implement", stderr)
.claude/hooks/test_codex_gate.py:155:        code, stderr = self._run_gate(self._payload(self.target_rel))
.claude/hooks/test_codex_gate.py:156:        self.assertEqual(code, 2, msg=f"expected block, got stderr:\n{stderr}")
.claude/hooks/test_codex_gate.py:157:        self.assertIn("NOT in fence", stderr)
.claude/hooks/test_codex_gate.py:163:        code, stderr = self._run_gate(self._payload(self.target_rel))
.claude/hooks/test_codex_gate.py:164:        self.assertEqual(code, 2, msg=f"expected block, got stderr:\n{stderr}")
.claude/hooks/test_codex_gate.py:165:        self.assertIn("status=fail", stderr)
.claude/hooks/test_codex_gate.py:174:        code, stderr = self._run_gate(self._payload(self.target_rel))
.claude/hooks/test_codex_gate.py:176:        self.assertEqual(code, 2, msg=f"expected block, got stderr:\n{stderr}")
.claude/hooks/test_codex_gate.py:183:        code, stderr = self._run_gate(self._payload(self.target_rel))
.claude/hooks/test_codex_gate.py:184:        self.assertEqual(code, 0, msg=f"expected allow, got stderr:\n{stderr}")
.claude/hooks/test_codex_gate.py:185:        self.assertIn("dual-teams-worktree", stderr)

 succeeded in 127ms:
898:    return datetime.datetime.now(datetime.timezone.utc).replace(

 succeeded in 180ms:
    for p in paths:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def decide(payload: dict, project_dir: Path) -> bool:
    """Core gate. True to allow; False after emitting deny."""
    logger = logging.getLogger(HOOK_NAME)
    event = payload.get("hook_event_name", "") if isinstance(payload, dict) else ""
    tool_name = payload.get("tool_name", "") if isinstance(payload, dict) else ""
    logger.info("decide.enter event=%s tool=%s", event, tool_name)
    if event and event != "PreToolUse":
        logger.info("decide.passthrough reason=non-PreToolUse event=%s", event)
        return True
    if tool_name not in {"Edit", "Write", "MultiEdit", "Bash", "NotebookEdit"}:
        logger.info("decide.passthrough reason=unknown-tool tool=%s", tool_name)
        return True
    if is_dual_teams_worktree(project_dir):
        logger.info("decide.passthrough reason=dual-teams-worktree project=%s", project_dir)
        return True

    if tool_name == "Bash":
        return _decide_bash(payload, project_dir)
    return _decide_edit(payload, project_dir, tool_name)


def _decide_edit(payload: dict, project_dir: Path, tool_name: str) -> bool:
    """Edit/Write/MultiEdit/NotebookEdit branch."""
    logger = logging.getLogger(HOOK_NAME)
    raw_targets = extract_targets(payload)
    if not raw_targets:
        logger.info("decide.passthrough reason=no-targets tool=%s", tool_name)
        return True
    for raw in raw_targets:
        abs_path = resolve_target(project_dir, raw)
        if abs_path is None:
            logger.info("decide.skip reason=unresolvable raw=%r", raw)
            continue
        rel = rel_posix(project_dir, abs_path)
        if rel is None:
            logger.info("decide.skip reason=outside-project path=%s", abs_path)
            continue
        if not requires_cover(rel):
            logger.info("decide.allow-target rel=%s reason=non-code-or-exempt", rel)
            _append_skip_ledger(project_dir, {
                "ts": _now_iso(), "tool": tool_name, "path": rel,
                "decision": "allow", "reason": "non-code-or-exempt",
            })
            continue
        if is_dual_teams_worktree(abs_path):
            logger.info("decide.allow-target rel=%s reason=dual-teams-target abs=%s",
                        rel, abs_path)
            _append_skip_ledger(project_dir, {
                "ts": _now_iso(), "tool": tool_name, "path": rel,
                "decision": "allow", "reason": "dual-teams-target",
            })
            continue
        covered, reason = find_cover(project_dir, rel)
        if not covered:
            emit_deny(rel, reason, project_dir, tool_name=tool_name)
            logger.info("decide.exit target=%s allowed=False reason=%s", rel, reason)
            return False
        logger.info("decide.allow-target rel=%s reason=covered", rel)
        _append_skip_ledger(project_dir, {
            "ts": _now_iso(), "tool": tool_name, "path": rel,
            "decision": "allow", "reason": reason,
        })
    logger.info("decide.exit allowed=True")
    return True


def _decide_bash(payload: dict, project_dir: Path) -> bool:
    """Bash branch (I2). Parse command, classify, check cover for each target."""
    logger = logging.getLogger(HOOK_NAME)
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        logger.info("decide_bash.no-input")
        return True
    command = tool_input.get("command", "")
    if not isinstance(command, str) or not command.strip():
        logger.info("decide_bash.empty-command")
        return True
    parsed = parse_bash_command(command)
    if parsed["decision"] == "allow":
        logger.info("decide_bash.allow reason=%s", parsed["reason"])
        _append_skip_ledger(project_dir, {
            "ts": _now_iso(), "tool": "Bash", "cmd": command[:200],
            "decision": "allow", "reason": parsed["reason"],
        })
        return True
    targets = parsed["targets"]
    if not targets:
        logger.info("decide_bash.require_cover-no-targets reason=%s", parsed["reason"])
        emit_deny("<bash-command>", "bash-no-cover", project_dir, tool_name="Bash")
        return False
    for target in targets:
        if target.startswith("<") and target.endswith(">"):
            emit_deny(target, "bash-no-cover", project_dir, tool_name="Bash")
            logger.info("decide_bash.exit allowed=False reason=opaque-target target=%s", target)
            return False
        norm = _normalize_path_token(target)
        abs_path = resolve_target(project_dir, norm)
        if abs_path is not None:
            rel = rel_posix(project_dir, abs_path) or norm
        else:
            rel = norm
        if abs_path is not None and is_dual_teams_worktree(abs_path):
            logger.info("decide_bash.allow-target rel=%s reason=dual-teams-target", rel)
            _append_skip_ledger(project_dir, {
                "ts": _now_iso(), "tool": "Bash", "path": rel,
                "decision": "allow", "reason": "dual-teams-target",
            })
            continue
        covered, reason = find_cover(project_dir, rel)
        if not covered:
            emit_deny(rel, reason, project_dir, tool_name="Bash")
            logger.info("decide_bash.exit target=%s allowed=False reason=%s", rel, reason)
            return False
        _append_skip_ledger(project_dir, {
            "ts": _now_iso(), "tool": "Bash", "path": rel,
            "decision": "allow", "reason": reason,
        })
    logger.info("decide_bash.exit allowed=True")
    return True


def main() -> int:
    """Read JSON payload from stdin, run decide(), exit 0 always."""
    project_dir = get_project_dir()
    logger = _build_logger(project_dir)
    logger.info("main.enter pid=%d", os.getpid())
    try:
        raw = sys.stdin.read()

 succeeded in 125ms:
30:    score_diff_size, score_lint_clean, score_logging_coverage,
82:        self.assertEqual(res.score, 0.0)
90:# ------------------------ diff_size ------------------------ #
101:            res = score_diff_size(repo, cap_lines=500)
102:            # ~50 added, cap 500 => 1 - 50/500 = 0.9
104:            self.assertLess(res.score, 0.95)
111:            res = score_diff_size(repo, cap_lines=500)
141:        self.assertAlmostEqual(res.score, 0.0)
220:            AxisResult(name="c", score=0.0, weight=2),
229:            AxisResult(name="b", score=0.0, weight=100, skipped=True),
235:        self.assertEqual(weighted_aggregate(axes), 0.0)
245:        w, d = decide_winner(0.70, 0.90)
249:        w, d = decide_winner(0.81, 0.80)  # delta 0.01 < 0.02
253:        w, _ = decide_winner(0.90, 0.70, tie_delta=0.25)
264:        verdict = judge.build_verdict("demo", c_axes, k_axes, tie_delta=0.02)
280:            AxisResult(name="diff_size", score=0.5, weight=2),
283:            AxisResult(name="tests_passed", score=0.9, weight=10),
284:            AxisResult(name="diff_size", score=0.9, weight=2),
287:        # diff_size delta = 0.4, tests_passed delta = 0.1 => diff_size cited
288:        self.assertIn("diff_size", rat)

ERROR: Reconnecting... 1/5
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/hooks/test_codex_delegate_enforcer.py | Select-Object -First 205' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/hooks/test_enforcer_live_attacks.py | Select-Object -First 130' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 192ms:
#!/usr/bin/env python3
"""Z5 - Live attack matrix for codex-delegate-enforcer.py.

Subprocess-level live integration harness exercising all 12 documented
bypass vectors (must DENY) plus 6 positive controls (must ALLOW). Each
test crafts a PreToolUse JSON payload, pipes it via stdin into a fresh
``python codex-delegate-enforcer.py`` subprocess and asserts on the
binary contract Claude Code's harness uses:

  - DENY  -> stdout contains valid JSON with
             hookSpecificOutput.permissionDecision == "deny"
             AND the offending path / reason substring is present
             (in stdout reason or stderr log).
  - ALLOW -> stdout has no ``"permissionDecision": "deny"`` JSON.

Note on exit codes: the task spec mentions "exit code (2=deny, 0=allow)".
The current enforcer ALWAYS exits 0 and signals deny via JSON on stdout
(the actual PreToolUse contract). This file therefore checks the JSON
contract rather than the exit code. If the harness later switches to
exit-code semantics, the deny-side checks below must be tightened.

Each test uses an isolated ``tmp_path``-based project root with NO
``.dual-base-ref`` sentinel, so the enforcer fully engages (the
dual-teams shortcut would otherwise allow everything). For tests that
legitimately need a sentinel (A5), we create one in a dedicated tmp tree.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------

HERE = Path(__file__).resolve().parent
HOOK_PATH = HERE / "codex-delegate-enforcer.py"
SUBPROC_TIMEOUT_SECONDS = 10


# ----------------------------------------------------------------------
# Subprocess invocation helpers
# ----------------------------------------------------------------------

def _run_enforcer(payload: dict, project_root: Path) -> subprocess.CompletedProcess:
    """Spawn codex-delegate-enforcer.py with payload JSON on stdin.

    Uses a hermetic CLAUDE_PROJECT_DIR so the enforcer never sees the
    real repo's .dual-base-ref sentinel (which would short-circuit it).
    """
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project_root)}
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=SUBPROC_TIMEOUT_SECONDS,
    )


def _parse_deny(stdout: str) -> Optional[dict]:
    """Return the parsed deny payload if stdout contains one, else None."""
    s = stdout.strip()
    if not s:
        return None
    try:
        obj = json.loads(s)
    except json.JSONDecodeError:
        return None
    hs = obj.get("hookSpecificOutput") if isinstance(obj, dict) else None
    if not isinstance(hs, dict):
        return None
    if hs.get("permissionDecision") == "deny":
        return obj
    return None


def _assert_deny(result: subprocess.CompletedProcess,
                 must_contain_in_reason: str = "") -> None:
    """Assert the subprocess produced a PreToolUse deny JSON on stdout."""
    deny = _parse_deny(result.stdout)
    assert deny is not None, (
        "expected DENY JSON on stdout. "
        f"returncode={result.returncode} stdout={result.stdout!r} "
        f"stderr={result.stderr[-500:]!r}"
    )
    if must_contain_in_reason:
        reason = deny["hookSpecificOutput"].get("permissionDecisionReason", "")
        assert (must_contain_in_reason in reason
                or must_contain_in_reason in result.stderr), (
            f"expected substring {must_contain_in_reason!r} in deny reason "
            f"or stderr log; reason={reason!r} stderr={result.stderr[-500:]!r}"
        )


def _assert_allow(result: subprocess.CompletedProcess) -> None:
    """Assert the subprocess produced no deny JSON (allow / passthrough)."""
    assert result.returncode == 0, (
        f"unexpected non-zero exit on allow: {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
    )
    deny = _parse_deny(result.stdout)
    assert deny is None, (
        f"expected ALLOW but enforcer emitted DENY JSON: {result.stdout!r}"
    )


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------

@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Hermetic project root with the dirs the enforcer expects.

    Critically does NOT include a .dual-base-ref sentinel anywhere up
    the tree, so the dual-teams short-circuit does NOT engage.
    """
    root = tmp_path / "repo"
    (root / ".claude" / "hooks").mkdir(parents=True)
    (root / ".claude" / "scripts").mkdir(parents=True)

 succeeded in 196ms:
#!/usr/bin/env python3
"""Unit tests for codex-delegate-enforcer.py (task T1).

Covers all 11 required cases from spec AC12:

  1. exempt path (e.g., CLAUDE.md) -> allow
  2. code file + NO recent result.md -> deny with JSON
  3. code file + stale (> 15 min) result.md -> deny
  4. code file + fresh status=pass result.md with covering fence -> allow
  5. code file + fresh pass result.md but fence does NOT cover target -> deny
  6. code file + fresh status=fail result.md -> deny
  7. non-code file (.txt, .md) -> allow
  8. MultiEdit with multiple files, all covered -> allow
  9. MultiEdit with one file uncovered -> deny
 10. malformed result.md / corrupt JSON payload -> pass-through (no crash)
 11. hook called on non-Edit event (e.g., Bash) -> pass-through

Each test isolates state under a temporary CLAUDE_PROJECT_DIR so
production .codex/ and work/ directories are never touched.
"""

from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENFORCER_PATH = HERE / "codex-delegate-enforcer.py"


def _load_module():
    """Import codex-delegate-enforcer.py as a module (hyphen in filename)."""
    spec = importlib.util.spec_from_file_location(
        "codex_delegate_enforcer", ENFORCER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BaseEnforcerTest(unittest.TestCase):
    """Shared fixture: isolated project root with results + tasks dirs."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp(prefix="codex-enforcer-test-")
        self.root = Path(self.tmpdir).resolve()
        (self.root / ".claude" / "hooks").mkdir(parents=True)
        (self.root / "work" / "codex-primary" / "tasks").mkdir(parents=True)
        (self.root / "work" / "codex-implementations").mkdir(parents=True)
        # Target file the tool call "would edit"
        self.target_rel = ".claude/hooks/my_hook.py"
        (self.root / ".claude" / "hooks" / "my_hook.py").write_text(
            "# placeholder\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ----- subprocess invocation helpers -----

    def _run_enforcer(self, payload):
        """Invoke enforcer as subprocess; return (exit_code, stdout, stderr)."""
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)}
        result = subprocess.run(
            [sys.executable, str(ENFORCER_PATH)],
            input=json.dumps(payload),
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            env=env, timeout=30,
        )
        return result.returncode, result.stdout, result.stderr

    # ----- fixture helpers -----

    def _write_task(self, task_id: str, fence_paths: list) -> Path:
        """Write a task-N.md with given Scope Fence allowed paths."""
        task_file = self.root / "work" / "codex-primary" / "tasks" / (
            "T" + task_id + "-test.md"
        )
        fence_block = "\n".join("- `" + p + "`" for p in fence_paths)
        task_file.write_text(
            "---\nexecutor: codex\n---\n\n"
            "# Task T" + task_id + "\n\n"
            "## Your Task\ntest\n\n"
            "## Scope Fence\n"
            "**Allowed paths (may be written):**\n"
            + fence_block + "\n\n"
            "**Forbidden paths:**\n- other/\n\n"
            "## Acceptance Criteria\n- [ ] AC1\n",
            encoding="utf-8",
        )
        return task_file

    def _write_result(self, task_id: str, status: str, age_seconds: float = 0) -> Path:
        """Write a task-N-result.md with given status and optional mtime offset."""
        result_file = self.root / "work" / "codex-implementations" / (
            "task-" + task_id + "-result.md"
        )
        task_file_rel = "work/codex-primary/tasks/T" + task_id + "-test.md"
        result_file.write_text(
            "# Result T" + task_id + "\n\n"
            "- status: " + status + "\n"
            "- task_file: " + task_file_rel + "\n\n"
            "## Diff\n(none)\n",
            encoding="utf-8",
        )
        if age_seconds > 0:
            old = time.time() - age_seconds
            os.utime(result_file, (old, old))
        return result_file

    def _edit_payload(self, file_path: str) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": file_path,
                "old_string": "a",
                "new_string": "b",
            },
        }

    def _write_payload(self, file_path: str) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": file_path, "content": "x"},
        }

    def _multiedit_payload(self, paths: list) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "MultiEdit",
            "tool_input": {
                "edits": [
                    {"file_path": p, "old_string": "a", "new_string": "b"}
                    for p in paths
                ],
            },
        }

    # ----- response assertions -----

    def _assert_allow(self, code: int, stdout: str, stderr: str) -> None:
        self.assertEqual(code, 0, msg="expected exit 0. stderr=" + stderr)
        # No deny JSON in stdout.
        if stdout.strip():
            try:
                parsed = json.loads(stdout)
                decision = (
                    parsed.get("hookSpecificOutput", {})
                    .get("permissionDecision")
                )
                self.assertNotEqual(
                    decision, "deny", msg="unexpected deny JSON: " + stdout
                )
            except json.JSONDecodeError:
                pass  # non-JSON stdout is fine

    def _assert_deny(self, code: int, stdout: str, stderr: str) -> None:
        self.assertEqual(code, 0, msg="expected exit 0 (deny via JSON). stderr=" + stderr)
        self.assertTrue(stdout.strip(), msg="expected deny JSON on stdout")
        parsed = json.loads(stdout)
        decision = parsed["hookSpecificOutput"]["permissionDecision"]
        self.assertEqual(decision, "deny")
        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("Code Delegation Protocol", reason)


class TestAC12Cases(BaseEnforcerTest):
    """The 10 scenarios enumerated in AC12 plus the non-Edit pass-through."""

    def test_01_exempt_path_allow(self) -> None:
        """AC12.1: exempt path (CLAUDE.md) -> allow."""
        code, out, err = self._run_enforcer(self._write_payload("CLAUDE.md"))
        self._assert_allow(code, out, err)

    def test_02_code_no_result_deny(self) -> None:
        """AC12.2: code file + NO recent result.md -> deny with JSON."""
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_03_stale_result_deny(self) -> None:
        """AC12.3: code file + stale (> 15 min) result.md -> deny."""
        self._write_task("3", [self.target_rel])
        self._write_result("3", "pass", age_seconds=20 * 60)  # 20 min old
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_deny(code, out, err)

    def test_04_covered_pass_allow(self) -> None:
        """AC12.4: code file + fresh pass result.md with covering fence -> allow."""
        self._write_task("4", [self.target_rel])
        self._write_result("4", "pass")
        code, out, err = self._run_enforcer(self._edit_payload(self.target_rel))
        self._assert_allow(code, out, err)

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/scripts/judge_axes.py | Select-Object -First 90' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 170ms:
#!/usr/bin/env python3
"""Judge axes вЂ” pure scoring for dual-implement judging.

Each axis returns AxisResult{score in [0,1], weight, skipped, raw}.
Skipped axes are excluded from the weighted aggregate.
"""
from __future__ import annotations

import importlib.util
import json
import logging
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if sys.platform == "win32":
    for _s in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")

logger = logging.getLogger("judge_axes")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {"ts": datetime.now(timezone.utc).isoformat(),
                   "level": record.levelname, "logger": record.name,
                   "msg": record.getMessage()}
        extra = getattr(record, "extra_fields", None)
        if extra:
            payload.update(extra)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _log(level: int, msg: str, **fields: object) -> None:
    logger.log(level, msg, extra={"extra_fields": fields})


@dataclass
class TestRun:
    command: str
    exit_code: int
    duration_s: float
    stdout_tail: str = ""
    stderr_tail: str = ""

    @property
    def passed(self) -> bool:
        return self.exit_code == 0


@dataclass
class AxisResult:
    name: str
    score: float = 0.0
    weight: int = 0
    skipped: bool = False
    skip_reason: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "score": round(self.score, 4),
                "weight": self.weight, "skipped": self.skipped,
                "skip_reason": self.skip_reason, "raw": self.raw}


def _module_available(name: str) -> bool:
    _log(logging.DEBUG, "entry: _module_available", name=name)
    try:
        found = importlib.util.find_spec(name) is not None
        _log(logging.DEBUG, "exit: _module_available", name=name, found=found)
        return found
    except (ValueError, ModuleNotFoundError):
        return False


def _skip(name: str, weight: int, reason: str) -> AxisResult:
    _log(logging.INFO, "axis_skipped", axis=name, reason=reason)
    return AxisResult(name=name, weight=weight, skipped=True, skip_reason=reason)


def score_tests_passed(runs: list[TestRun], weight: int = 10) -> AxisResult:
    """Fraction of Test Commands that exited 0. Empty => skipped."""

  → Update judge diff-size formula and tests
  • Add Codex availability helper and deny-message prefix
  • Add enforcer invariant tests
  • Run required test commands
  • Commit and self-report
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/hooks/codex-delegate-enforcer.py | Select-Object -Skip 1110 -First 40' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/hooks/test_codex_delegate_enforcer_invariants.py | Select-Object -Skip 360 -First 75' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 168ms:
    project_dir = get_project_dir()
    logger = _build_logger(project_dir)
    logger.info("main.enter pid=%d", os.getpid())
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            logger.info("main.empty-stdin passthrough")
            return 0
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.info("main.malformed-json exc=%s", exc)
            return 0
        if not isinstance(payload, dict):
            logger.info("main.non-dict-payload type=%s", type(payload).__name__)
            return 0
        decide(payload, project_dir)
    except Exception as exc:
        logger.exception("main.unexpected exc=%s", exc)
    finally:
        logger.info("main.exit")
    return 0


if __name__ == "__main__":
    sys.exit(main())

 succeeded in 166ms:
        (self.root / "src" / "a.py").write_text("# a\n", encoding="utf-8")
        before = len(self._read_ledger())
        allowed, _ = self._decide(self._edit_payload("src/a.py"))
        self.assertFalse(allowed)
        after = self._read_ledger()
        self.assertEqual(len(after) - before, 1)
        last = after[-1]
        self.assertEqual(last["decision"], "deny")
        self.assertIn("reason", last)

    def test_skip_ledger_jsonl_parseable(self):
        """All ledger lines parse as valid JSON with required keys."""
        # Trigger a few decisions.
        (self.root / "src" / "a.py").write_text("# a\n", encoding="utf-8")
        self._decide(self._edit_payload("src/a.py"))  # deny
        self._decide(self._edit_payload("CLAUDE.md"))  # allow
        ledger = self._read_ledger()
        self.assertGreaterEqual(len(ledger), 2)
        required = {"ts", "tool", "decision", "reason"}
        for entry in ledger:
            self.assertTrue(required.issubset(entry.keys()),
                            "missing keys in entry: " + str(entry))

    def test_block_message_includes_inline_dual_command(self):
        """DENY error message contains codex-inline-dual.py --describe + path."""
        target = "src/auth.py"
        (self.root / "src" / "auth.py").write_text("# a\n", encoding="utf-8")
        allowed, stdout = self._decide(self._edit_payload(target))
        self.assertFalse(allowed)
        parsed = json.loads(stdout)
        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("codex-inline-dual.py", reason)
        self.assertIn("--describe", reason)
        self.assertIn(target, reason)



# ======================================================================
# AC-5 вЂ” Regression: existing tests + selftest still pass
# ======================================================================
class TestRegression(unittest.TestCase):
    """Regression suite вЂ” runs the existing 36-test suite and selftest."""

    def test_existing_tests_still_pass(self):
        """Run pytest on test_codex_delegate_enforcer.py вЂ” exit 0."""
        existing = HERE / "test_codex_delegate_enforcer.py"
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(existing), "-q",
             "--tb=line", "--no-header"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=120,
        )
        self.assertEqual(
            result.returncode, 0,
            "existing tests failed: stdout=" + result.stdout
            + " stderr=" + result.stderr,
        )

    def test_dual_teams_selftest_still_passes(self):
        """Run dual-teams-selftest.py вЂ” exit 0."""
        # Walk up to project root (the worktree itself).
        project_root = HERE.parent.parent
        selftest = project_root / ".claude" / "scripts" / "dual-teams-selftest.py"
        if not selftest.is_file():
            self.skipTest("dual-teams-selftest.py not found at " + str(selftest))
        result = subprocess.run(
            [sys.executable, str(selftest)],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=180, cwd=str(project_root),
        )
        self.assertEqual(
            result.returncode, 0,
            "dual-teams-selftest failed: stdout=" + result.stdout[-1000:]
            + " stderr=" + result.stderr[-500:],
        )

codex
I’m going to change the scoring formula and add unit tests that patch the numstat helper directly. For the enforcer, I’ll keep the deny JSON contract intact and only prefix the existing permission reason when the availability check says Codex is unusable.
2026-04-26T13:10:26.023530Z ERROR codex_core::tools::router: error=apply_patch verification failed: Failed to find expected lines in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic\.claude\hooks\test_codex_delegate_enforcer_invariants.py:
        self.assertIn("codex-inline-dual.py", reason)
        self.assertIn("--describe", reason)
        self.assertIn(target, reason)



# ======================================================================
# AC-5 вЂ” Regression: existing tests + selftest still pass
# ======================================================================
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff -- .claude/scripts/judge_axes.py .claude/scripts/test_judge.py .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer_invariants.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/hooks/test_codex_delegate_enforcer_invariants.py | Select-Object -Skip 380 -First 25' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 131ms:
 succeeded in 165ms:
            self.assertTrue(required.issubset(entry.keys()),
                            "missing keys in entry: " + str(entry))

    def test_block_message_includes_inline_dual_command(self):
        """DENY error message contains codex-inline-dual.py --describe + path."""
        target = "src/auth.py"
        (self.root / "src" / "auth.py").write_text("# a\n", encoding="utf-8")
        allowed, stdout = self._decide(self._edit_payload(target))
        self.assertFalse(allowed)
        parsed = json.loads(stdout)
        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("codex-inline-dual.py", reason)
        self.assertIn("--describe", reason)
        self.assertIn(target, reason)



# ======================================================================
# AC-5 вЂ” Regression: existing tests + selftest still pass
# ======================================================================
class TestRegression(unittest.TestCase):
    """Regression suite вЂ” runs the existing 36-test suite and selftest."""

    def test_existing_tests_still_pass(self):
        """Run pytest on test_codex_delegate_enforcer.py вЂ” exit 0."""

codex
The first patch missed a context boundary in the invariant test file, so no files changed. I’m applying the same edits in smaller chunks against the exact current context.
apply patch
patch: completed
C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic\.claude\scripts\judge_axes.py
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")

diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")

apply patch
patch: completed
C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic\.claude\scripts\test_judge.py
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

apply patch
patch: completed
C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic\.claude\hooks\codex-delegate-enforcer.py
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

2026-04-26T13:11:34.842348Z ERROR codex_core::tools::router: error=apply_patch verification failed: Failed to find expected lines in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic\.claude\hooks\test_codex_delegate_enforcer_invariants.py:
        self.assertIn("codex-inline-dual.py", reason)
        self.assertIn("--describe", reason)
        self.assertIn(target, reason)



# ======================================================================
# AC-5 вЂ” Regression: existing tests + selftest still pass
# ======================================================================
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

apply patch
patch: completed
C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic\.claude\hooks\test_codex_delegate_enforcer_invariants.py
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..68d77951a26f73e574b3df7fd70b96f89e6497f1
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -398,7 +398,73 @@
 # ======================================================================
 # AC-5 — Regression: existing tests + selftest still pass
 # ======================================================================
-class TestRegression(unittest.TestCase):
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..68d77951a26f73e574b3df7fd70b96f89e6497f1
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -398,7 +398,73 @@
 # ======================================================================
 # AC-5 — Regression: existing tests + selftest still pass
 # ======================================================================
-class TestRegression(unittest.TestCase):
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/hooks/test_codex_delegate_enforcer_invariants.py | Select-Object -Skip 380 -First 110' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/hooks/codex-delegate-enforcer.py | Select-Object -Skip 890 -First 80' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content .claude/scripts/test_judge.py | Select-Object -Skip 90 -First 75' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff --stat' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 192ms:
            self.assertTrue(required.issubset(entry.keys()),
                            "missing keys in entry: " + str(entry))

    def test_block_message_includes_inline_dual_command(self):
        """DENY error message contains codex-inline-dual.py --describe + path."""
        target = "src/auth.py"
        (self.root / "src" / "auth.py").write_text("# a\n", encoding="utf-8")
        allowed, stdout = self._decide(self._edit_payload(target))
        self.assertFalse(allowed)
        parsed = json.loads(stdout)
        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("codex-inline-dual.py", reason)
        self.assertIn("--describe", reason)
        self.assertIn(target, reason)



# ======================================================================
# AC-5 вЂ” Regression: existing tests + selftest still pass
# ======================================================================
    def test_codex_unavailable_when_auth_missing(self):
        """Missing auth file reports Codex unavailable."""
        missing = self.root / "missing-auth.json"
        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
        self.assertTrue(unavailable)
        self.assertIn("missing", reason)

    def test_codex_available_when_auth_recent(self):
        """Fresh auth file reports Codex available."""
        auth = self.root / "auth.json"
        auth.write_text("{}", encoding="utf-8")
        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
        unavailable, reason = self.mod._codex_appears_unavailable(
            auth_path=auth, now=now,
        )
        self.assertFalse(unavailable)
        self.assertEqual(reason, "")

    def test_codex_unavailable_when_auth_stale(self):
        """Stale auth file reports Codex unavailable."""
        auth = self.root / "auth.json"
        auth.write_text("{}", encoding="utf-8")
        old = time.time() - (48 * 3600)
        os.utime(auth, (old, old))
        now = self.mod.datetime.datetime.fromtimestamp(time.time())
        unavailable, reason = self.mod._codex_appears_unavailable(
            auth_path=auth, now=now,
        )
        self.assertTrue(unavailable)
        self.assertIn("older", reason)

    def test_block_message_mentions_unavailability_when_codex_down(self):
        """DENY message prepends Codex availability hint when unavailable."""
        target = "src/codex_down.py"
        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
        original = self.mod._codex_appears_unavailable
        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
        try:
            allowed, stdout = self._decide(self._edit_payload(target))
        finally:
            self.mod._codex_appears_unavailable = original
        self.assertFalse(allowed)
        parsed = json.loads(stdout)
        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("appears unavailable", reason)
        self.assertIn("test reason", reason)
        self.assertIn("codex-inline-dual", reason)

    def test_block_message_unchanged_when_codex_available(self):
        """DENY message omits Codex availability hint when available."""
        target = "src/codex_available.py"
        (self.root / "src" / "codex_available.py").write_text("# a\n",
                                                              encoding="utf-8")
        original = self.mod._codex_appears_unavailable
        self.mod._codex_appears_unavailable = lambda: (False, "")
        try:
            allowed, stdout = self._decide(self._edit_payload(target))
        finally:
            self.mod._codex_appears_unavailable = original
        self.assertFalse(allowed)
        parsed = json.loads(stdout)
        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertNotIn("appears unavailable", reason)
        self.assertIn("codex-inline-dual", reason)


class TestRegression(unittest.TestCase):
    """Regression suite вЂ” runs the existing 36-test suite and selftest."""

    def test_existing_tests_still_pass(self):
        """Run pytest on test_codex_delegate_enforcer.py вЂ” exit 0."""
        existing = HERE / "test_codex_delegate_enforcer.py"
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(existing), "-q",
             "--tb=line", "--no-header"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=120,
        )
        self.assertEqual(
            result.returncode, 0,
            "existing tests failed: stdout=" + result.stdout
            + " stderr=" + result.stderr,
        )

    def test_dual_teams_selftest_still_passes(self):
        """Run dual-teams-selftest.py вЂ” exit 0."""
        # Walk up to project root (the worktree itself).
        project_root = HERE.parent.parent
        selftest = project_root / ".claude" / "scripts" / "dual-teams-selftest.py"
        if not selftest.is_file():

 succeeded in 188ms:
        logger.exception("skip_ledger.write_err exc=%s", exc)
    except Exception as exc:
        logger.exception("skip_ledger.unexpected exc=%s", exc)


def _now_iso() -> str:
    """Return UTC timestamp in ISO-8601 format."""
    return datetime.datetime.now(datetime.timezone.utc).replace(
        microsecond=0).isoformat()


def _codex_appears_unavailable(
    auth_path: Optional[Path] = None,
    now: Optional[datetime.datetime] = None,
    max_auth_age_hours: int = 24,
) -> tuple[bool, str]:
    """Return (True, reason) if Codex appears unusable, else (False, '')."""
    logger = logging.getLogger(HOOK_NAME)
    auth = auth_path or (Path.home() / ".codex" / "auth.json")
    logger.debug(
        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
        auth, max_auth_age_hours,
    )
    if not auth.exists():
        reason = "~/.codex/auth.json missing"
        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
        return True, reason
    age_hours = ((now or datetime.datetime.now()).timestamp()
                 - auth.stat().st_mtime) / 3600
    if age_hours > max_auth_age_hours:
        reason = (
            f"~/.codex/auth.json older than {max_auth_age_hours}h "
            f"({int(age_hours)}h)"
        )
        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
        return True, reason
    logger.debug("codex_appears_unavailable.exit result=False reason=")
    return False, ""


def _build_block_message(blocked_path: str, reason_code: str) -> str:
    """Build the actionable DENY message for emit_deny."""
    logger = logging.getLogger(HOOK_NAME)
    reason_text = {
        "no-results": "no codex-implement result found",
        "no-results-dir": "work/codex-implementations/ does not exist",
        "stale": "all codex-implement results older than 15 min",
        "fail-status": "most recent matching result has status != pass",
        "scope-miss": "no recent pass result covers this exact path",
        "parse-error": "could not parse codex-implement result",
        "bash-no-cover": "Bash command would mutate code without cover",
    }.get(reason_code, reason_code)
    prefix = ""
    try:
        unavailable, unavailable_reason = _codex_appears_unavailable()
        if unavailable:
            prefix = (
                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
            )
    except Exception as exc:
        logger.exception("codex_unavailable_check.failed exc=%s", exc)
    msg = prefix + (
        "Code Delegation Protocol: " + blocked_path + " blocked ("
        + reason_text + ").\n\n"
        "To start the dual-implement track for this path, run:\n\n"
        "  py -3 .claude/scripts/codex-inline-dual.py \\n"
        "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
        "    --scope " + blocked_path + " \\n"
        "    --test \"py -3 -m pytest -q\"\n\n"
        "Then retry your edit. For multi-file tasks, use:\n"
        "  py -3 .claude/scripts/dual-teams-spawn.py --tasks <task.md> ...\n"
    )
    return msg


def emit_deny(blocked: str, reason_code: str, project_dir: Path,
              tool_name: str = "Edit") -> None:
    """Print the PreToolUse deny JSON to stdout and append ledger entry."""
    logger = logging.getLogger(HOOK_NAME)

 succeeded in 180ms:


class TestDiffSize(unittest.TestCase):
    def test_inverse_normalization(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)
            _add_file(repo, "a.py", "# pre\n", commit=True)
            # Add 50 lines uncommitted
            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
            res = score_diff_size(repo, cap_lines=500)
            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
            self.assertGreater(res.score, 0.85)
            self.assertLess(res.score, 0.95)
            self.assertEqual(res.raw["added"], 50)

    def test_empty_diff_max_score(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)
            res = score_diff_size(repo, cap_lines=500)
            self.assertAlmostEqual(res.score, 1.0)
            self.assertEqual(res.raw["added"], 0)

    def test_diff_size_zero_added_scores_one(self) -> None:
        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
            res = score_diff_size(Path("."), cap_lines=500)
        self.assertEqual(res.score, 1.0)

    def test_diff_size_at_scale_scores_half(self) -> None:
        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
            res = score_diff_size(Path("."), cap_lines=500)
        self.assertGreaterEqual(res.score, 0.49)
        self.assertLessEqual(res.score, 0.51)

    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
            res = score_diff_size(Path("."), cap_lines=500)
        self.assertGreater(res.score, 0.0)
        self.assertLess(res.score, 0.3)

    def test_diff_size_huge_diff_asymptotic(self) -> None:
        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
            res = score_diff_size(Path("."), cap_lines=500)
        self.assertGreater(res.score, 0.0)
        self.assertLessEqual(res.score, 0.1)


# ------------------------ logging_coverage ------------------------ #


class TestLoggingCoverage(unittest.TestCase):
    def test_function_with_logger(self) -> None:
        diff = textwrap.dedent("""\
            diff --git a/x.py b/x.py
            @@ -0,0 +1,3 @@
            +def foo():
            +    logger.info("hi")
            +    return 1
            """)
        res = score_logging_coverage(Path("."), diff_text=diff)
        self.assertAlmostEqual(res.score, 1.0)
        self.assertEqual(res.raw["covered"], 1)

    def test_function_without_logger(self) -> None:
        diff = textwrap.dedent("""\
            diff --git a/x.py b/x.py
            @@ -0,0 +1,3 @@
            +def foo():
            +    x = 1
            +    return x
            """)
        res = score_logging_coverage(Path("."), diff_text=diff)
        self.assertAlmostEqual(res.score, 0.0)
        self.assertEqual(res.raw["covered"], 0)

 succeeded in 143ms:
 .claude/hooks/codex-delegate-enforcer.py           | 42 +++++++++++++-
 .../test_codex_delegate_enforcer_invariants.py     | 66 ++++++++++++++++++++++
 .claude/scripts/judge_axes.py                      |  5 +-
 .claude/scripts/test_judge.py                      | 25 +++++++-
 4 files changed, 134 insertions(+), 4 deletions(-)
warning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/hooks/test_codex_delegate_enforcer_invariants.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/judge_axes.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/test_judge.py', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..68d77951a26f73e574b3df7fd70b96f89e6497f1
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -398,7 +398,73 @@
 # ======================================================================
 # AC-5 — Regression: existing tests + selftest still pass
 # ======================================================================
-class TestRegression(unittest.TestCase):
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

2026-04-26T13:12:18.269002Z ERROR codex_core::tools::router: error=apply_patch verification failed: Failed to find expected lines in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic\.claude\hooks\test_codex_delegate_enforcer_invariants.py:

# ======================================================================
# AC-5 вЂ” Regression: existing tests + selftest still pass
# ======================================================================
    def test_codex_unavailable_when_auth_missing(self):
        """Missing auth file reports Codex unavailable."""
        missing = self.root / "missing-auth.json"
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..68d77951a26f73e574b3df7fd70b96f89e6497f1
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -398,7 +398,73 @@
 # ======================================================================
 # AC-5 — Regression: existing tests + selftest still pass
 # ======================================================================
-class TestRegression(unittest.TestCase):
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Select-String -Path .claude/hooks/test_codex_delegate_enforcer_invariants.py -Pattern "AC-5" -Context 2,2' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 185ms:

  .claude\hooks\test_codex_delegate_enforcer_invariants.py:7:- AC-3: I3 — path-exact coverage (no temporal carryover)
  .claude\hooks\test_codex_delegate_enforcer_invariants.py:8:- AC-4: I4 — skip-token ledger + actionable block messages
> .claude\hooks\test_codex_delegate_enforcer_invariants.py:9:- AC-5: regression — existing 36 tests still pass + selfte
st
  .claude\hooks\test_codex_delegate_enforcer_invariants.py:10:"""
  .claude\hooks\test_codex_delegate_enforcer_invariants.py:11:from __future__ import annotations
  .claude\hooks\test_codex_delegate_enforcer_invariants.py:397:
  .claude\hooks\test_codex_delegate_enforcer_invariants.py:398:# ======================================================
================
> .claude\hooks\test_codex_delegate_enforcer_invariants.py:399:# AC-5 — Regression: existing tests + selftest still pas
s
  .claude\hooks\test_codex_delegate_enforcer_invariants.py:400:# ======================================================
================
  .claude\hooks\test_codex_delegate_enforcer_invariants.py:401:    def test_codex_unavailable_when_auth_missing(self):



diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..68d77951a26f73e574b3df7fd70b96f89e6497f1
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -398,7 +398,73 @@
 # ======================================================================
 # AC-5 — Regression: existing tests + selftest still pass
 # ======================================================================
-class TestRegression(unittest.TestCase):
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

apply patch
patch: completed
C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic\.claude\hooks\test_codex_delegate_enforcer_invariants.py
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..010648824c4a741fd10756adac0a664c87c6f9ca
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -395,10 +395,73 @@
 
 
 
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..010648824c4a741fd10756adac0a664c87c6f9ca
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -395,10 +395,73 @@
 
 
 
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

apply patch
patch: completed
C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic\.claude\hooks\test_codex_delegate_enforcer_invariants.py
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..9ce50418ac74e67f1627aad567750f8063130976
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -395,10 +395,76 @@
 
 
 
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..9ce50418ac74e67f1627aad567750f8063130976
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -395,10 +395,76 @@
 
 
 
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

  ✓ Update judge diff-size formula and tests
  ✓ Add Codex availability helper and deny-message prefix
  ✓ Add enforcer invariant tests
  → Run required test commands
  • Commit and self-report
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..9ce50418ac74e67f1627aad567750f8063130976
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -395,10 +395,76 @@
 
 
 
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

codex
The code changes are in place across the four allowed files. I’m starting with the targeted judge and enforcer invariant suites, then I’ll run the broader regression command and selftest.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/scripts/test_judge.py -v --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 2161ms:
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.2, pluggy-1.6.0 -- C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
plugins: anyio-4.12.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 43 items

.claude/scripts/test_judge.py::TestTestsPassed::test_all_pass PASSED     [  2%]
.claude/scripts/test_judge.py::TestTestsPassed::test_empty_skipped PASSED [  4%]
.claude/scripts/test_judge.py::TestTestsPassed::test_none_pass PASSED    [  6%]
.claude/scripts/test_judge.py::TestTestsPassed::test_some_pass PASSED    [  9%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_at_scale_scores_half PASSED [ 11%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_far_above_scale_still_nonzero PASSED [ 13%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_huge_diff_asymptotic PASSED [ 16%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_zero_added_scores_one PASSED [ 18%]
.claude/scripts/test_judge.py::TestDiffSize::test_empty_diff_max_score PASSED [ 20%]
.claude/scripts/test_judge.py::TestDiffSize::test_inverse_normalization PASSED [ 23%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_edge_no_new_functions PASSED [ 25%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_function_with_logger PASSED [ 27%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_function_without_logger PASSED [ 30%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_mixed_functions PASSED [ 32%]
.claude/scripts/test_judge.py::TestLintClean::test_clean_file PASSED     [ 34%]
.claude/scripts/test_judge.py::TestLintClean::test_no_files_skipped PASSED [ 37%]
.claude/scripts/test_judge.py::TestLintClean::test_syntax_error PASSED   [ 39%]
.claude/scripts/test_judge.py::TestOptionalToolSkip::test_complexity_skipped_when_radon_absent PASSED [ 41%]
.claude/scripts/test_judge.py::TestOptionalToolSkip::test_type_check_skipped_when_mypy_absent PASSED [ 44%]
.claude/scripts/test_judge.py::TestWeightedAggregate::test_all_skipped_zero PASSED [ 46%]
.claude/scripts/test_judge.py::TestWeightedAggregate::test_skipped_ignored PASSED [ 48%]
.claude/scripts/test_judge.py::TestWeightedAggregate::test_weighted_correctness PASSED [ 51%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_claude_wins PASSED [ 53%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_codex_wins PASSED [ 55%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_tie_custom_delta PASSED [ 58%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_tie_within_delta PASSED [ 60%]
.claude/scripts/test_judge.py::TestVerdictSchema::test_rationale_cites_biggest_delta PASSED [ 62%]
.claude/scripts/test_judge.py::TestVerdictSchema::test_verdict_is_valid_json PASSED [ 65%]
.claude/scripts/test_judge.py::TestCLI::test_dry_run PASSED              [ 67%]
.claude/scripts/test_judge.py::TestCLI::test_help_exits_zero PASSED      [ 69%]
.claude/scripts/test_judge.py::TestCLI::test_help_mentions_auto_base PASSED [ 72%]
.claude/scripts/test_judge.py::TestCLI::test_malformed_task_exit_1 PASSED [ 74%]
.claude/scripts/test_judge.py::TestStructuredLogging::test_json_formatter_shape PASSED [ 76%]
.claude/scripts/test_judge.py::TestEnsureUntrackedVisible::test_idempotent_no_untracked PASSED [ 79%]
.claude/scripts/test_judge.py::TestEnsureUntrackedVisible::test_never_raises_on_missing_git PASSED [ 81%]
.claude/scripts/test_judge.py::TestEnsureUntrackedVisible::test_registers_untracked_py PASSED [ 83%]
.claude/scripts/test_judge.py::TestDiffBaselineCommitted::test_committed_diff_visible_with_merge_base PASSED [ 86%]
.claude/scripts/test_judge.py::TestDiffBaselineUntracked::test_untracked_numstat_after_ensure PASSED [ 88%]
.claude/scripts/test_judge.py::TestResolveBase::test_cli_explicit_wins_over_sidecar PASSED [ 90%]
.claude/scripts/test_judge.py::TestResolveBase::test_head_fallback_in_non_git PASSED [ 93%]
.claude/scripts/test_judge.py::TestResolveBase::test_head_literal_passes_through_to_fallback PASSED [ 95%]
.claude/scripts/test_judge.py::TestResolveBase::test_merge_base_when_no_sidecar_and_auto PASSED [ 97%]
.claude/scripts/test_judge.py::TestResolveBase::test_sidecar_wins_over_auto_fallback PASSED [100%]

============================== warnings summary ===============================
.claude\scripts\judge_axes.py:46
  C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic\.claude\scripts\judge_axes.py:46: PytestCollectionWarning: cannot collect test class 'TestRun' because it has a __init__ constructor (from: .claude/scripts/test_judge.py)
    @dataclass

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 43 passed, 1 warning in 1.71s ========================

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..9ce50418ac74e67f1627aad567750f8063130976
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -395,10 +395,76 @@
 
 
 
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/hooks/test_codex_delegate_enforcer_invariants.py -v --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 2444ms:
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.2, pluggy-1.6.0 -- C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
plugins: anyio-4.12.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 40 items

.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI1ExtensionWins::test_claude_scripts_py_requires_cover PASSED [  2%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI1ExtensionWins::test_work_md_still_exempt PASSED [  5%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI1ExtensionWins::test_work_py_requires_cover PASSED [  7%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI1ExtensionWins::test_worktrees_dual_teams_py_allow PASSED [ 10%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI1ExtensionWins::test_worktrees_py_outside_dual_requires_cover PASSED [ 12%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_codex_ask_allow PASSED [ 15%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_cp_code_to_code_requires_cover PASSED [ 17%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_cp_md_to_md_allow PASSED [ 20%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_dual_teams_spawn_allow PASSED [ 22%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_git_apply_requires_cover PASSED [ 25%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_git_checkout_code_file_requires_cover PASSED [ 27%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_git_status_allow PASSED [ 30%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_heredoc_to_code_requires_cover PASSED [ 32%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_ls_allow PASSED [ 35%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_powershell_set_content_code_requires_cover PASSED [ 37%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_powershell_set_content_md_allow PASSED [ 40%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_pytest_allow PASSED [ 42%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_python_dash_alone_requires_cover PASSED [ 45%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_python_dash_c_open_write_requires_cover PASSED [ 47%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_python_dash_c_print_allow PASSED [ 50%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_python_script_in_work_requires_cover PASSED [ 52%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_redirect_to_code_requires_cover PASSED [ 55%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_sed_i_on_code_requires_cover PASSED [ 57%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_sed_i_on_md_allow PASSED [ 60%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI3PathExactCoverage::test_artifact_covers_path_a_allows_path_a PASSED [ 62%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI3PathExactCoverage::test_artifact_covers_path_a_blocks_path_b PASSED [ 65%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI3PathExactCoverage::test_failed_artifact_blocks_even_if_covers_path PASSED [ 67%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI3PathExactCoverage::test_glob_in_scope_fence_matches PASSED [ 70%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI3PathExactCoverage::test_stale_artifact_outside_15min_blocks PASSED [ 72%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI4Ledger::test_block_message_includes_inline_dual_command PASSED [ 75%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI4Ledger::test_block_message_mentions_unavailability_when_codex_down PASSED [ 77%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI4Ledger::test_block_message_unchanged_when_codex_available PASSED [ 80%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI4Ledger::test_codex_available_when_auth_recent PASSED [ 82%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI4Ledger::test_codex_unavailable_when_auth_missing PASSED [ 85%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI4Ledger::test_codex_unavailable_when_auth_stale PASSED [ 87%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI4Ledger::test_skip_ledger_appends_on_allow PASSED [ 90%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI4Ledger::test_skip_ledger_appends_on_deny PASSED [ 92%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI4Ledger::test_skip_ledger_jsonl_parseable PASSED [ 95%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestRegression::test_dual_teams_selftest_still_passes PASSED [ 97%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestRegression::test_existing_tests_still_pass PASSED [100%]

============================= 40 passed in 1.99s ==============================

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..9ce50418ac74e67f1627aad567750f8063130976
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -395,10 +395,76 @@
 
 
 
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

codex
The two targeted suites are passing: judge has 43 passed, enforcer invariants has 40 passed. I’m running the broader suite now to catch interactions with the existing hook and script tests.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 3909ms:
........................................................................ [ 38%]
........................................................................ [ 77%]
.........................................                                [100%]
185 passed in 3.39s

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..9ce50418ac74e67f1627aad567750f8063130976
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -395,10 +395,76 @@
 
 
 
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

codex
The broader regression command passed with 185 tests. I’m running the dual-teams selftest next.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python .claude/scripts/dual-teams-selftest.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 719ms:
[PASS] preflight-clean-with-sentinel-V1                     (57 ms)
[PASS] preflight-clean-with-sentinel-V2                     (57 ms)
[PASS] is_dual_teams_worktree-true-on-V1                    ( 1 ms)
[PASS] is_dual_teams_worktree-true-on-V2                    ( 1 ms)
[PASS] judge-axes-sees-claude-committed-py                  (28 ms)
[PASS] judge-axes-sees-codex-untracked-py                   (47 ms)
selftest: 6 checks, 6 passed, 0 failed (543 ms)
{"json_output": false, "keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: main", "ts": "2026-04-26T13:13:16.736545+00:00"}
{"keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: run_selftest", "ts": "2026-04-26T13:13:16.736545+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: setup_transient_repo", "tmpdir": "C:\\Users\\Lenovo\\AppData\\Local\\Temp\\dual-teams-selftest-8_jsoy9o", "ts": "2026-04-26T13:13:16.737647+00:00"}
{"base_sha": "d2abbf2fa6b876b1f872b833315eb6b421063b02", "duration_ms": 250, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: setup_transient_repo", "ts": "2026-04-26T13:13:16.987586+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: load_integrations", "project_root": "C:\\Bots\\Migrator bots\\claude-project-template-update\\worktrees\\codify-enforcement-z12\\codex\\task-Z12-y21-y25-judge-diagnostic", "ts": "2026-04-26T13:13:16.987586+00:00"}
{"duration_ms": 6, "failures": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: load_integrations", "ts": "2026-04-26T13:13:16.994597+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: build_results", "ts": "2026-04-26T13:13:16.994597+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T13:13:16.994597+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "detail": "git status --porcelain empty", "duration_ms": 57, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T13:13:17.050739+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T13:13:17.050739+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "detail": "git status --porcelain empty", "duration_ms": 57, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T13:13:17.108137+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T13:13:17.108137+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T13:13:17.108137+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T13:13:17.108137+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T13:13:17.108137+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T13:13:17.169766+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "detail": "saw claude_probe.py", "duration_ms": 28, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T13:13:17.198871+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T13:13:17.198871+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "detail": "saw codex_probe.py", "duration_ms": 47, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T13:13:17.245786+00:00"}
{"checks": 6, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: build_results", "ts": "2026-04-26T13:13:17.245786+00:00"}
{"checks": 6, "duration_ms": 543, "failed": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: run_selftest", "passed": 6, "ts": "2026-04-26T13:13:17.278788+00:00"}
{"exit_code": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: main", "ts": "2026-04-26T13:13:17.278788+00:00"}

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..9ce50418ac74e67f1627aad567750f8063130976
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -395,10 +395,76 @@
 
 
 
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

codex
The selftest passed 6/6. The AC text also lists the combined “existing tests” command, so I’m running that exact aggregate once as a final cross-check even though its parts already passed.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 5895ms:
........................................................................ [ 32%]
........................................................................ [ 64%]
........................................................................ [ 96%]
.........                                                                [100%]
225 passed in 5.37s

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..9ce50418ac74e67f1627aad567750f8063130976
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -395,10 +395,76 @@
 
 
 
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff -- .claude/scripts/judge_axes.py .claude/scripts/test_judge.py .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer_invariants.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff --numstat' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 131ms:
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f..ab289f1 100644
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -899,8 +899,38 @@ def _now_iso() -> str:
         microsecond=0).isoformat()
 
 
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
 def _build_block_message(blocked_path: str, reason_code: str) -> str:
     """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
     reason_text = {
         "no-results": "no codex-implement result found",
         "no-results-dir": "work/codex-implementations/ does not exist",
@@ -910,7 +940,17 @@ def _build_block_message(blocked_path: str, reason_code: str) -> str:
         "parse-error": "could not parse codex-implement result",
         "bash-no-cover": "Bash command would mutate code without cover",
     }.get(reason_code, reason_code)
-    msg = (
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
         "Code Delegation Protocol: " + blocked_path + " blocked ("
         + reason_text + ").\n\n"
         "To start the dual-implement track for this path, run:\n\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7..9ce5041 100644
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -395,6 +395,72 @@ class TestI4Ledger(_Base):
 
 
 
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
 # ======================================================================
 # AC-5 — Regression: existing tests + selftest still pass
 # ======================================================================
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e9..9cdc7db 100644
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -180,11 +180,12 @@ def _git_diff_numstat(worktree: Path, base: str = "HEAD") -> tuple[int, int]:
 
 def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
                     cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
     _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
     try:
         added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
         _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
         return AxisResult(name="diff_size", score=score, weight=weight,
                           raw={"added": added, "removed": removed,
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd..c57e8d2 100644
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -99,7 +99,7 @@ class TestDiffSize(unittest.TestCase):
             # Add 50 lines uncommitted
             _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
             res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
             self.assertGreater(res.score, 0.85)
             self.assertLess(res.score, 0.95)
             self.assertEqual(res.raw["added"], 50)
@@ -112,6 +112,29 @@ class TestDiffSize(unittest.TestCase):
             self.assertAlmostEqual(res.score, 1.0)
             self.assertEqual(res.raw["added"], 0)
 
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
 
 # ------------------------ logging_coverage ------------------------ #
 
warning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/hooks/test_codex_delegate_enforcer_invariants.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/judge_axes.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/test_judge.py', LF will be replaced by CRLF the next time Git touches it

 succeeded in 129ms:
 M .claude/hooks/codex-delegate-enforcer.py
 M .claude/hooks/test_codex_delegate_enforcer_invariants.py
 M .claude/scripts/judge_axes.py
 M .claude/scripts/test_judge.py

 succeeded in 159ms:
41	1	.claude/hooks/codex-delegate-enforcer.py
66	0	.claude/hooks/test_codex_delegate_enforcer_invariants.py
3	2	.claude/scripts/judge_axes.py
24	1	.claude/scripts/test_judge.py
warning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/hooks/test_codex_delegate_enforcer_invariants.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/judge_axes.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/test_judge.py', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..9ce50418ac74e67f1627aad567750f8063130976
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -395,10 +395,76 @@
 
 
 
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

apply patch
patch: completed
C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic\.claude\hooks\test_codex_delegate_enforcer_invariants.py
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..bbf8b1bbb4e6e0b350bff5faa16c01d77cab747e
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -389,16 +389,80 @@
         self.assertFalse(allowed)
         parsed = json.loads(stdout)
         reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
-        self.assertIn("codex-inline-dual.py", reason)
-        self.assertIn("--describe", reason)
-        self.assertIn(target, reason)
-
-
-
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+        self.assertIn("codex-inline-dual.py", reason)
+        self.assertIn("--describe", reason)
+        self.assertIn(target, reason)
+
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..bbf8b1bbb4e6e0b350bff5faa16c01d77cab747e
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -389,16 +389,80 @@
         self.assertFalse(allowed)
         parsed = json.loads(stdout)
         reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
-        self.assertIn("codex-inline-dual.py", reason)
-        self.assertIn("--describe", reason)
-        self.assertIn(target, reason)
-
-
-
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+        self.assertIn("codex-inline-dual.py", reason)
+        self.assertIn("--describe", reason)
+        self.assertIn(target, reason)
+
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

codex
I cleaned up one spacing artifact in the invariant test file. I’m rerunning the required commands after that final edit so the report reflects the final tree.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/scripts/test_judge.py -v --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 2158ms:
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.2, pluggy-1.6.0 -- C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
plugins: anyio-4.12.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 43 items

.claude/scripts/test_judge.py::TestTestsPassed::test_all_pass PASSED     [  2%]
.claude/scripts/test_judge.py::TestTestsPassed::test_empty_skipped PASSED [  4%]
.claude/scripts/test_judge.py::TestTestsPassed::test_none_pass PASSED    [  6%]
.claude/scripts/test_judge.py::TestTestsPassed::test_some_pass PASSED    [  9%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_at_scale_scores_half PASSED [ 11%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_far_above_scale_still_nonzero PASSED [ 13%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_huge_diff_asymptotic PASSED [ 16%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_zero_added_scores_one PASSED [ 18%]
.claude/scripts/test_judge.py::TestDiffSize::test_empty_diff_max_score PASSED [ 20%]
.claude/scripts/test_judge.py::TestDiffSize::test_inverse_normalization PASSED [ 23%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_edge_no_new_functions PASSED [ 25%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_function_with_logger PASSED [ 27%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_function_without_logger PASSED [ 30%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_mixed_functions PASSED [ 32%]
.claude/scripts/test_judge.py::TestLintClean::test_clean_file PASSED     [ 34%]
.claude/scripts/test_judge.py::TestLintClean::test_no_files_skipped PASSED [ 37%]
.claude/scripts/test_judge.py::TestLintClean::test_syntax_error PASSED   [ 39%]
.claude/scripts/test_judge.py::TestOptionalToolSkip::test_complexity_skipped_when_radon_absent PASSED [ 41%]
.claude/scripts/test_judge.py::TestOptionalToolSkip::test_type_check_skipped_when_mypy_absent PASSED [ 44%]
.claude/scripts/test_judge.py::TestWeightedAggregate::test_all_skipped_zero PASSED [ 46%]
.claude/scripts/test_judge.py::TestWeightedAggregate::test_skipped_ignored PASSED [ 48%]
.claude/scripts/test_judge.py::TestWeightedAggregate::test_weighted_correctness PASSED [ 51%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_claude_wins PASSED [ 53%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_codex_wins PASSED [ 55%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_tie_custom_delta PASSED [ 58%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_tie_within_delta PASSED [ 60%]
.claude/scripts/test_judge.py::TestVerdictSchema::test_rationale_cites_biggest_delta PASSED [ 62%]
.claude/scripts/test_judge.py::TestVerdictSchema::test_verdict_is_valid_json PASSED [ 65%]
.claude/scripts/test_judge.py::TestCLI::test_dry_run PASSED              [ 67%]
.claude/scripts/test_judge.py::TestCLI::test_help_exits_zero PASSED      [ 69%]
.claude/scripts/test_judge.py::TestCLI::test_help_mentions_auto_base PASSED [ 72%]
.claude/scripts/test_judge.py::TestCLI::test_malformed_task_exit_1 PASSED [ 74%]
.claude/scripts/test_judge.py::TestStructuredLogging::test_json_formatter_shape PASSED [ 76%]
.claude/scripts/test_judge.py::TestEnsureUntrackedVisible::test_idempotent_no_untracked PASSED [ 79%]
.claude/scripts/test_judge.py::TestEnsureUntrackedVisible::test_never_raises_on_missing_git PASSED [ 81%]
.claude/scripts/test_judge.py::TestEnsureUntrackedVisible::test_registers_untracked_py PASSED [ 83%]
.claude/scripts/test_judge.py::TestDiffBaselineCommitted::test_committed_diff_visible_with_merge_base PASSED [ 86%]
.claude/scripts/test_judge.py::TestDiffBaselineUntracked::test_untracked_numstat_after_ensure PASSED [ 88%]
.claude/scripts/test_judge.py::TestResolveBase::test_cli_explicit_wins_over_sidecar PASSED [ 90%]
.claude/scripts/test_judge.py::TestResolveBase::test_head_fallback_in_non_git PASSED [ 93%]
.claude/scripts/test_judge.py::TestResolveBase::test_head_literal_passes_through_to_fallback PASSED [ 95%]
.claude/scripts/test_judge.py::TestResolveBase::test_merge_base_when_no_sidecar_and_auto PASSED [ 97%]
.claude/scripts/test_judge.py::TestResolveBase::test_sidecar_wins_over_auto_fallback PASSED [100%]

============================== warnings summary ===============================
.claude\scripts\judge_axes.py:46
  C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic\.claude\scripts\judge_axes.py:46: PytestCollectionWarning: cannot collect test class 'TestRun' because it has a __init__ constructor (from: .claude/scripts/test_judge.py)
    @dataclass

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 43 passed, 1 warning in 1.68s ========================

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..bbf8b1bbb4e6e0b350bff5faa16c01d77cab747e
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -389,16 +389,80 @@
         self.assertFalse(allowed)
         parsed = json.loads(stdout)
         reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
-        self.assertIn("codex-inline-dual.py", reason)
-        self.assertIn("--describe", reason)
-        self.assertIn(target, reason)
-
-
-
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+        self.assertIn("codex-inline-dual.py", reason)
+        self.assertIn("--describe", reason)
+        self.assertIn(target, reason)
+
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/hooks/test_codex_delegate_enforcer_invariants.py -v --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 2503ms:
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.2, pluggy-1.6.0 -- C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
plugins: anyio-4.12.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 40 items

.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI1ExtensionWins::test_claude_scripts_py_requires_cover PASSED [  2%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI1ExtensionWins::test_work_md_still_exempt PASSED [  5%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI1ExtensionWins::test_work_py_requires_cover PASSED [  7%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI1ExtensionWins::test_worktrees_dual_teams_py_allow PASSED [ 10%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI1ExtensionWins::test_worktrees_py_outside_dual_requires_cover PASSED [ 12%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_codex_ask_allow PASSED [ 15%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_cp_code_to_code_requires_cover PASSED [ 17%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_cp_md_to_md_allow PASSED [ 20%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_dual_teams_spawn_allow PASSED [ 22%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_git_apply_requires_cover PASSED [ 25%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_git_checkout_code_file_requires_cover PASSED [ 27%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_git_status_allow PASSED [ 30%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_heredoc_to_code_requires_cover PASSED [ 32%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_ls_allow PASSED [ 35%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_powershell_set_content_code_requires_cover PASSED [ 37%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_powershell_set_content_md_allow PASSED [ 40%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_pytest_allow PASSED [ 42%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_python_dash_alone_requires_cover PASSED [ 45%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_python_dash_c_open_write_requires_cover PASSED [ 47%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_python_dash_c_print_allow PASSED [ 50%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_python_script_in_work_requires_cover PASSED [ 52%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_redirect_to_code_requires_cover PASSED [ 55%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_sed_i_on_code_requires_cover PASSED [ 57%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI2BashCounts::test_bash_sed_i_on_md_allow PASSED [ 60%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI3PathExactCoverage::test_artifact_covers_path_a_allows_path_a PASSED [ 62%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI3PathExactCoverage::test_artifact_covers_path_a_blocks_path_b PASSED [ 65%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI3PathExactCoverage::test_failed_artifact_blocks_even_if_covers_path PASSED [ 67%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI3PathExactCoverage::test_glob_in_scope_fence_matches PASSED [ 70%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI3PathExactCoverage::test_stale_artifact_outside_15min_blocks PASSED [ 72%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI4Ledger::test_block_message_includes_inline_dual_command PASSED [ 75%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI4Ledger::test_block_message_mentions_unavailability_when_codex_down PASSED [ 77%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI4Ledger::test_block_message_unchanged_when_codex_available PASSED [ 80%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI4Ledger::test_codex_available_when_auth_recent PASSED [ 82%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI4Ledger::test_codex_unavailable_when_auth_missing PASSED [ 85%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI4Ledger::test_codex_unavailable_when_auth_stale PASSED [ 87%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI4Ledger::test_skip_ledger_appends_on_allow PASSED [ 90%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI4Ledger::test_skip_ledger_appends_on_deny PASSED [ 92%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestI4Ledger::test_skip_ledger_jsonl_parseable PASSED [ 95%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestRegression::test_dual_teams_selftest_still_passes PASSED [ 97%]
.claude/hooks/test_codex_delegate_enforcer_invariants.py::TestRegression::test_existing_tests_still_pass PASSED [100%]

============================= 40 passed in 2.03s ==============================

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..bbf8b1bbb4e6e0b350bff5faa16c01d77cab747e
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -389,16 +389,80 @@
         self.assertFalse(allowed)
         parsed = json.loads(stdout)
         reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
-        self.assertIn("codex-inline-dual.py", reason)
-        self.assertIn("--describe", reason)
-        self.assertIn(target, reason)
-
-
-
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+        self.assertIn("codex-inline-dual.py", reason)
+        self.assertIn("--describe", reason)
+        self.assertIn(target, reason)
+
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 3885ms:
........................................................................ [ 38%]
........................................................................ [ 77%]
.........................................                                [100%]
185 passed in 3.35s

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..bbf8b1bbb4e6e0b350bff5faa16c01d77cab747e
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -389,16 +389,80 @@
         self.assertFalse(allowed)
         parsed = json.loads(stdout)
         reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
-        self.assertIn("codex-inline-dual.py", reason)
-        self.assertIn("--describe", reason)
-        self.assertIn(target, reason)
-
-
-
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+        self.assertIn("codex-inline-dual.py", reason)
+        self.assertIn("--describe", reason)
+        self.assertIn(target, reason)
+
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python .claude/scripts/dual-teams-selftest.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 722ms:
[PASS] preflight-clean-with-sentinel-V1                     (60 ms)
[PASS] preflight-clean-with-sentinel-V2                     (55 ms)
[PASS] is_dual_teams_worktree-true-on-V1                    ( 1 ms)
[PASS] is_dual_teams_worktree-true-on-V2                    ( 1 ms)
[PASS] judge-axes-sees-claude-committed-py                  (28 ms)
[PASS] judge-axes-sees-codex-untracked-py                   (45 ms)
selftest: 6 checks, 6 passed, 0 failed (553 ms)
{"json_output": false, "keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: main", "ts": "2026-04-26T13:14:35.106595+00:00"}
{"keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: run_selftest", "ts": "2026-04-26T13:14:35.106595+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: setup_transient_repo", "tmpdir": "C:\\Users\\Lenovo\\AppData\\Local\\Temp\\dual-teams-selftest-tffmduhw", "ts": "2026-04-26T13:14:35.107602+00:00"}
{"base_sha": "7648554c581215beee772b23f2a5f06db8c063af", "duration_ms": 262, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: setup_transient_repo", "ts": "2026-04-26T13:14:35.369565+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: load_integrations", "project_root": "C:\\Bots\\Migrator bots\\claude-project-template-update\\worktrees\\codify-enforcement-z12\\codex\\task-Z12-y21-y25-judge-diagnostic", "ts": "2026-04-26T13:14:35.369565+00:00"}
{"duration_ms": 5, "failures": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: load_integrations", "ts": "2026-04-26T13:14:35.374578+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: build_results", "ts": "2026-04-26T13:14:35.375580+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T13:14:35.375580+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "detail": "git status --porcelain empty", "duration_ms": 60, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T13:14:35.435799+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T13:14:35.435799+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "detail": "git status --porcelain empty", "duration_ms": 55, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T13:14:35.489972+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T13:14:35.489972+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T13:14:35.489972+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T13:14:35.489972+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T13:14:35.490969+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T13:14:35.552833+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "detail": "saw claude_probe.py", "duration_ms": 28, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T13:14:35.581100+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T13:14:35.581100+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "detail": "saw codex_probe.py", "duration_ms": 45, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T13:14:35.626124+00:00"}
{"checks": 6, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: build_results", "ts": "2026-04-26T13:14:35.626658+00:00"}
{"checks": 6, "duration_ms": 553, "failed": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: run_selftest", "passed": 6, "ts": "2026-04-26T13:14:35.658614+00:00"}
{"exit_code": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: main", "ts": "2026-04-26T13:14:35.658614+00:00"}

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..bbf8b1bbb4e6e0b350bff5faa16c01d77cab747e
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -389,16 +389,80 @@
         self.assertFalse(allowed)
         parsed = json.loads(stdout)
         reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
-        self.assertIn("codex-inline-dual.py", reason)
-        self.assertIn("--describe", reason)
-        self.assertIn(target, reason)
-
-
-
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+        self.assertIn("codex-inline-dual.py", reason)
+        self.assertIn("--describe", reason)
+        self.assertIn(target, reason)
+
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 5883ms:
........................................................................ [ 32%]
........................................................................ [ 64%]
........................................................................ [ 96%]
.........                                                                [100%]
225 passed in 5.38s

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..bbf8b1bbb4e6e0b350bff5faa16c01d77cab747e
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -389,16 +389,80 @@
         self.assertFalse(allowed)
         parsed = json.loads(stdout)
         reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
-        self.assertIn("codex-inline-dual.py", reason)
-        self.assertIn("--describe", reason)
-        self.assertIn(target, reason)
-
-
-
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+        self.assertIn("codex-inline-dual.py", reason)
+        self.assertIn("--describe", reason)
+        self.assertIn(target, reason)
+
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

  ✓ Update judge diff-size formula and tests
  ✓ Add Codex availability helper and deny-message prefix
  ✓ Add enforcer invariant tests
  ✓ Run required test commands
  → Commit and self-report
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..bbf8b1bbb4e6e0b350bff5faa16c01d77cab747e
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -389,16 +389,80 @@
         self.assertFalse(allowed)
         parsed = json.loads(stdout)
         reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
-        self.assertIn("codex-inline-dual.py", reason)
-        self.assertIn("--describe", reason)
-        self.assertIn(target, reason)
-
-
-
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+        self.assertIn("codex-inline-dual.py", reason)
+        self.assertIn("--describe", reason)
+        self.assertIn(target, reason)
+
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff --stat' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff --numstat' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 140ms:
 .claude/hooks/codex-delegate-enforcer.py           | 42 +++++++++++++-
 .../test_codex_delegate_enforcer_invariants.py     | 64 ++++++++++++++++++++++
 .claude/scripts/judge_axes.py                      |  5 +-
 .claude/scripts/test_judge.py                      | 25 ++++++++-
 4 files changed, 132 insertions(+), 4 deletions(-)
warning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/hooks/test_codex_delegate_enforcer_invariants.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/judge_axes.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/test_judge.py', LF will be replaced by CRLF the next time Git touches it

 succeeded in 126ms:
 M .claude/hooks/codex-delegate-enforcer.py
 M .claude/hooks/test_codex_delegate_enforcer_invariants.py
 M .claude/scripts/judge_axes.py
 M .claude/scripts/test_judge.py

 succeeded in 139ms:
41	1	.claude/hooks/codex-delegate-enforcer.py
64	0	.claude/hooks/test_codex_delegate_enforcer_invariants.py
3	2	.claude/scripts/judge_axes.py
24	1	.claude/scripts/test_judge.py
warning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/hooks/test_codex_delegate_enforcer_invariants.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/judge_axes.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/test_judge.py', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..bbf8b1bbb4e6e0b350bff5faa16c01d77cab747e
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -389,16 +389,80 @@
         self.assertFalse(allowed)
         parsed = json.loads(stdout)
         reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
-        self.assertIn("codex-inline-dual.py", reason)
-        self.assertIn("--describe", reason)
-        self.assertIn(target, reason)
-
-
-
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+        self.assertIn("codex-inline-dual.py", reason)
+        self.assertIn("--describe", reason)
+        self.assertIn(target, reason)
+
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff --check' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 133ms:
warning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/hooks/test_codex_delegate_enforcer_invariants.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/judge_axes.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/test_judge.py', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..bbf8b1bbb4e6e0b350bff5faa16c01d77cab747e
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -389,16 +389,80 @@
         self.assertFalse(allowed)
         parsed = json.loads(stdout)
         reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
-        self.assertIn("codex-inline-dual.py", reason)
-        self.assertIn("--describe", reason)
-        self.assertIn(target, reason)
-
-
-
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+        self.assertIn("codex-inline-dual.py", reason)
+        self.assertIn("--describe", reason)
+        self.assertIn(target, reason)
+
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

codex
All required tests are passing and `git diff --check` only reported the repo’s normal CRLF conversion warnings. I’m staging just the four allowed files and creating the task commit now.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git add .claude/scripts/judge_axes.py .claude/scripts/test_judge.py .claude/hooks/codex-delegate-enforcer.py .claude/hooks/test_codex_delegate_enforcer_invariants.py; git commit -m "Fix judge diff size and codex availability hint"' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 591ms:
[codex-wave/task-Z12-y21-y25-judge-diagnostic 814ff4c] Fix judge diff size and codex availability hint
 4 files changed, 132 insertions(+), 4 deletions(-)
warning: in the working copy of '.claude/hooks/codex-delegate-enforcer.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/hooks/test_codex_delegate_enforcer_invariants.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/judge_axes.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/test_judge.py', LF will be replaced by CRLF the next time Git touches it
Memory NOT updated. Adding auto-generated entry...
Auto-entry added to memory

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..bbf8b1bbb4e6e0b350bff5faa16c01d77cab747e
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -389,16 +389,80 @@
         self.assertFalse(allowed)
         parsed = json.loads(stdout)
         reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
-        self.assertIn("codex-inline-dual.py", reason)
-        self.assertIn("--describe", reason)
-        self.assertIn(target, reason)
-
-
-
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+        self.assertIn("codex-inline-dual.py", reason)
+        self.assertIn("--describe", reason)
+        self.assertIn(target, reason)
+
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git rev-parse HEAD' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git show --stat --oneline --name-only HEAD' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 130ms:
 M .claude/memory/activeContext.md

 succeeded in 134ms:
814ff4c55db9a6622fdfd62763372de0ad70ea3f

 succeeded in 125ms:
814ff4c Fix judge diff size and codex availability hint
.claude/hooks/codex-delegate-enforcer.py
.claude/hooks/test_codex_delegate_enforcer_invariants.py
.claude/scripts/judge_axes.py
.claude/scripts/test_judge.py

diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..bbf8b1bbb4e6e0b350bff5faa16c01d77cab747e
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -389,16 +389,80 @@
         self.assertFalse(allowed)
         parsed = json.loads(stdout)
         reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
-        self.assertIn("codex-inline-dual.py", reason)
-        self.assertIn("--describe", reason)
-        self.assertIn(target, reason)
-
-
-
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+        self.assertIn("codex-inline-dual.py", reason)
+        self.assertIn("--describe", reason)
+        self.assertIn(target, reason)
+
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

codex
The commit hook wrote an unstaged `.claude/memory/activeContext.md` entry after the commit. That file is outside the task fence and was a hook side effect, so I’m restoring it to keep the final worktree scoped to the committed four-file change.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git restore -- .claude/memory/activeContext.md; git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\codify-enforcement-z12\codex\task-Z12-y21-y25-judge-diagnostic
 succeeded in 150ms:
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..bbf8b1bbb4e6e0b350bff5faa16c01d77cab747e
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -389,16 +389,80 @@
         self.assertFalse(allowed)
         parsed = json.loads(stdout)
         reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
-        self.assertIn("codex-inline-dual.py", reason)
-        self.assertIn("--describe", reason)
-        self.assertIn(target, reason)
-
-
-
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+        self.assertIn("codex-inline-dual.py", reason)
+        self.assertIn("--describe", reason)
+        self.assertIn(target, reason)
+
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

  ✓ Update judge diff-size formula and tests
  ✓ Add Codex availability helper and deny-message prefix
  ✓ Add enforcer invariant tests
  ✓ Run required test commands
  ✓ Commit and self-report
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..bbf8b1bbb4e6e0b350bff5faa16c01d77cab747e
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -389,16 +389,80 @@
         self.assertFalse(allowed)
         parsed = json.loads(stdout)
         reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
-        self.assertIn("codex-inline-dual.py", reason)
-        self.assertIn("--describe", reason)
-        self.assertIn(target, reason)
-
-
-
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+        self.assertIn("codex-inline-dual.py", reason)
+        self.assertIn("--describe", reason)
+        self.assertIn(target, reason)
+
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

codex
=== TASK Z12 SELF-REPORT ===
- status: pass
- files modified: [.claude/scripts/judge_axes.py, .claude/scripts/test_judge.py, .claude/hooks/codex-delegate-enforcer.py, .claude/hooks/test_codex_delegate_enforcer_invariants.py]
- new tests added: 9
- net lines: +128 approx
- Y21 approach: replaced linear cap-to-zero with `scale_factor / (scale_factor + max(0, added))`.
- Y25 approach: added auth-file freshness helper and prepended unavailable-Codex hint to deny reasons.
- existing 220 tests still pass: yes
- selftest: PASS
- diff_size new behavior verified (added=2000, cap=500, 0 < score < 0.3): yes
- block message unavailability hint added: yes
- NOTE: Judge tests: `43 passed, 1 warning in 1.68s`.
- NOTE: Enforcer invariants: `40 passed in 2.03s`.
- NOTE: Other suites: `185 passed in 3.35s`; combined AC-4 command: `225 passed in 5.38s`.
- NOTE: Selftest stdout included `selftest: 6 checks, 6 passed, 0 failed`.
- NOTE: Updated the existing diff-size normalization comment; no hard-zero-at-cap assertion existed.
- Final commit SHA: 814ff4c55db9a6622fdfd62763372de0ad70ea3f
=== END SELF-REPORT ===
diff --git a/.claude/hooks/codex-delegate-enforcer.py b/.claude/hooks/codex-delegate-enforcer.py
index 43c523f023ce0fe718a2d7c5b43a6dc1cbd44688..ab289f1e3a1370314a314fd47473efc953a16c36
--- a/.claude/hooks/codex-delegate-enforcer.py
+++ b/.claude/hooks/codex-delegate-enforcer.py
@@ -893,27 +893,67 @@
         logger.exception("skip_ledger.unexpected exc=%s", exc)
 
 
-def _now_iso() -> str:
-    """Return UTC timestamp in ISO-8601 format."""
-    return datetime.datetime.now(datetime.timezone.utc).replace(
-        microsecond=0).isoformat()
-
-
-def _build_block_message(blocked_path: str, reason_code: str) -> str:
-    """Build the actionable DENY message for emit_deny."""
-    reason_text = {
-        "no-results": "no codex-implement result found",
-        "no-results-dir": "work/codex-implementations/ does not exist",
-        "stale": "all codex-implement results older than 15 min",
-        "fail-status": "most recent matching result has status != pass",
+def _now_iso() -> str:
+    """Return UTC timestamp in ISO-8601 format."""
+    return datetime.datetime.now(datetime.timezone.utc).replace(
+        microsecond=0).isoformat()
+
+
+def _codex_appears_unavailable(
+    auth_path: Optional[Path] = None,
+    now: Optional[datetime.datetime] = None,
+    max_auth_age_hours: int = 24,
+) -> tuple[bool, str]:
+    """Return (True, reason) if Codex appears unusable, else (False, '')."""
+    logger = logging.getLogger(HOOK_NAME)
+    auth = auth_path or (Path.home() / ".codex" / "auth.json")
+    logger.debug(
+        "codex_appears_unavailable.enter auth_path=%s max_auth_age_hours=%s",
+        auth, max_auth_age_hours,
+    )
+    if not auth.exists():
+        reason = "~/.codex/auth.json missing"
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    age_hours = ((now or datetime.datetime.now()).timestamp()
+                 - auth.stat().st_mtime) / 3600
+    if age_hours > max_auth_age_hours:
+        reason = (
+            f"~/.codex/auth.json older than {max_auth_age_hours}h "
+            f"({int(age_hours)}h)"
+        )
+        logger.debug("codex_appears_unavailable.exit result=True reason=%s", reason)
+        return True, reason
+    logger.debug("codex_appears_unavailable.exit result=False reason=")
+    return False, ""
+
+
+def _build_block_message(blocked_path: str, reason_code: str) -> str:
+    """Build the actionable DENY message for emit_deny."""
+    logger = logging.getLogger(HOOK_NAME)
+    reason_text = {
+        "no-results": "no codex-implement result found",
+        "no-results-dir": "work/codex-implementations/ does not exist",
+        "stale": "all codex-implement results older than 15 min",
+        "fail-status": "most recent matching result has status != pass",
         "scope-miss": "no recent pass result covers this exact path",
-        "parse-error": "could not parse codex-implement result",
-        "bash-no-cover": "Bash command would mutate code without cover",
-    }.get(reason_code, reason_code)
-    msg = (
-        "Code Delegation Protocol: " + blocked_path + " blocked ("
-        + reason_text + ").\n\n"
-        "To start the dual-implement track for this path, run:\n\n"
+        "parse-error": "could not parse codex-implement result",
+        "bash-no-cover": "Bash command would mutate code without cover",
+    }.get(reason_code, reason_code)
+    prefix = ""
+    try:
+        unavailable, unavailable_reason = _codex_appears_unavailable()
+        if unavailable:
+            prefix = (
+                "*** Codex appears unavailable: " + unavailable_reason + ".\n"
+                "*** Run `codex login` or check ~/.codex/auth.json, then retry.\n\n"
+            )
+    except Exception as exc:
+        logger.exception("codex_unavailable_check.failed exc=%s", exc)
+    msg = prefix + (
+        "Code Delegation Protocol: " + blocked_path + " blocked ("
+        + reason_text + ").\n\n"
+        "To start the dual-implement track for this path, run:\n\n"
         "  py -3 .claude/scripts/codex-inline-dual.py \\n"
         "    --describe \"Edit/Write to " + blocked_path + "\" \\n"
         "    --scope " + blocked_path + " \\n"
diff --git a/.claude/hooks/test_codex_delegate_enforcer_invariants.py b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
index 8830fc7a04aad0e1de44b12878ef3b08b95675d1..bbf8b1bbb4e6e0b350bff5faa16c01d77cab747e
--- a/.claude/hooks/test_codex_delegate_enforcer_invariants.py
+++ b/.claude/hooks/test_codex_delegate_enforcer_invariants.py
@@ -389,16 +389,80 @@
         self.assertFalse(allowed)
         parsed = json.loads(stdout)
         reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
-        self.assertIn("codex-inline-dual.py", reason)
-        self.assertIn("--describe", reason)
-        self.assertIn(target, reason)
-
-
-
-# ======================================================================
-# AC-5 — Regression: existing tests + selftest still pass
-# ======================================================================
-class TestRegression(unittest.TestCase):
+        self.assertIn("codex-inline-dual.py", reason)
+        self.assertIn("--describe", reason)
+        self.assertIn(target, reason)
+
+    def test_codex_unavailable_when_auth_missing(self):
+        """Missing auth file reports Codex unavailable."""
+        missing = self.root / "missing-auth.json"
+        unavailable, reason = self.mod._codex_appears_unavailable(auth_path=missing)
+        self.assertTrue(unavailable)
+        self.assertIn("missing", reason)
+
+    def test_codex_available_when_auth_recent(self):
+        """Fresh auth file reports Codex available."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        now = self.mod.datetime.datetime.fromtimestamp(auth.stat().st_mtime)
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertFalse(unavailable)
+        self.assertEqual(reason, "")
+
+    def test_codex_unavailable_when_auth_stale(self):
+        """Stale auth file reports Codex unavailable."""
+        auth = self.root / "auth.json"
+        auth.write_text("{}", encoding="utf-8")
+        old = time.time() - (48 * 3600)
+        os.utime(auth, (old, old))
+        now = self.mod.datetime.datetime.fromtimestamp(time.time())
+        unavailable, reason = self.mod._codex_appears_unavailable(
+            auth_path=auth, now=now,
+        )
+        self.assertTrue(unavailable)
+        self.assertIn("older", reason)
+
+    def test_block_message_mentions_unavailability_when_codex_down(self):
+        """DENY message prepends Codex availability hint when unavailable."""
+        target = "src/codex_down.py"
+        (self.root / "src" / "codex_down.py").write_text("# a\n", encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (True, "test reason")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertIn("appears unavailable", reason)
+        self.assertIn("test reason", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+    def test_block_message_unchanged_when_codex_available(self):
+        """DENY message omits Codex availability hint when available."""
+        target = "src/codex_available.py"
+        (self.root / "src" / "codex_available.py").write_text("# a\n",
+                                                              encoding="utf-8")
+        original = self.mod._codex_appears_unavailable
+        self.mod._codex_appears_unavailable = lambda: (False, "")
+        try:
+            allowed, stdout = self._decide(self._edit_payload(target))
+        finally:
+            self.mod._codex_appears_unavailable = original
+        self.assertFalse(allowed)
+        parsed = json.loads(stdout)
+        reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
+        self.assertNotIn("appears unavailable", reason)
+        self.assertIn("codex-inline-dual", reason)
+
+
+# ======================================================================
+# AC-5 — Regression: existing tests + selftest still pass
+# ======================================================================
+class TestRegression(unittest.TestCase):
     """Regression suite — runs the existing 36-test suite and selftest."""
 
     def test_existing_tests_still_pass(self):
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index ac9f2e948799c36c35b3647f0bfe177ea328d31c..9cdc7db954a61d5fe6afe5678901d7e460be8d94
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -178,16 +178,17 @@
         return 0, 0
 
 
-def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
-                    cap_lines: int = 500) -> AxisResult:
-    """Smaller diff = higher score. score = max(0, 1 - added/cap_lines)."""
-    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
-    try:
-        added, removed = _git_diff_numstat(worktree, base)
-        score = max(0.0, 1.0 - (added / cap_lines))
-        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
-        return AxisResult(name="diff_size", score=score, weight=weight,
-                          raw={"added": added, "removed": removed,
+def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
+                    cap_lines: int = 500) -> AxisResult:
+    """Smaller diff = higher score. cap_lines is the asymptotic scale."""
+    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
+    try:
+        added, removed = _git_diff_numstat(worktree, base)
+        scale_factor = cap_lines
+        score = scale_factor / (scale_factor + max(0, added))
+        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added)
+        return AxisResult(name="diff_size", score=score, weight=weight,
+                          raw={"added": added, "removed": removed,
                                "cap_lines": cap_lines, "base": base})
     except Exception:
         logger.exception("score_diff_size failed")
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 013e7dd5bfb78647b6cd54255b5e7b918c299867..c57e8d217ce660bbae34c247f94800796c70adc2
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -97,23 +97,46 @@
             _init_git_repo(repo)
             _add_file(repo, "a.py", "# pre\n", commit=True)
             # Add 50 lines uncommitted
-            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
-            res = score_diff_size(repo, cap_lines=500)
-            # ~50 added, cap 500 => 1 - 50/500 = 0.9
-            self.assertGreater(res.score, 0.85)
-            self.assertLess(res.score, 0.95)
-            self.assertEqual(res.raw["added"], 50)
+            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 50))
+            res = score_diff_size(repo, cap_lines=500)
+            # ~50 added, cap 500 => 500 / (500 + 50) ~= 0.91
+            self.assertGreater(res.score, 0.85)
+            self.assertLess(res.score, 0.95)
+            self.assertEqual(res.raw["added"], 50)
 
     def test_empty_diff_max_score(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             repo = Path(td)
             _init_git_repo(repo)
-            res = score_diff_size(repo, cap_lines=500)
-            self.assertAlmostEqual(res.score, 1.0)
-            self.assertEqual(res.raw["added"], 0)
-
-
-# ------------------------ logging_coverage ------------------------ #
+            res = score_diff_size(repo, cap_lines=500)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["added"], 0)
+
+    def test_diff_size_zero_added_scores_one(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(0, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertEqual(res.score, 1.0)
+
+    def test_diff_size_at_scale_scores_half(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(500, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreaterEqual(res.score, 0.49)
+        self.assertLessEqual(res.score, 0.51)
+
+    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(2000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLess(res.score, 0.3)
+
+    def test_diff_size_huge_diff_asymptotic(self) -> None:
+        with patch("judge_axes._git_diff_numstat", return_value=(10000, 0)):
+            res = score_diff_size(Path("."), cap_lines=500)
+        self.assertGreater(res.score, 0.0)
+        self.assertLessEqual(res.score, 0.1)
+
+
+# ------------------------ logging_coverage ------------------------ #
 
 
 class TestLoggingCoverage(unittest.TestCase):

2026-04-26T13:16:21.480702Z ERROR codex_core::session: failed to record rollout items: thread 019dc9e7-4fea-7602-b07a-8213f9975550 not found
tokens used
126 995
```
