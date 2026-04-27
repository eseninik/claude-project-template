# Codex Implementation Result — Task Z33-full-parity-sync

- status: pass
- timestamp: 2026-04-26T19:04:30.419436+00:00
- task_file: C:\Bots\Migrator bots\claude-project-template-update\work\criterion-upgrade\task-Z33-full-parity-sync.md
- base_sha: 11ef9496fbbae42ae513a928bc8263ccc3a6c7f9
- codex_returncode: 0
- scope_status: pass
- scope_message: OK: 2 path(s) in fence
- tests_all_passed: True
- test_commands_count: 4

## Diff

```diff
diff --git a/.claude/scripts/sync-template-to-target.py b/.claude/scripts/sync-template-to-target.py
index 1565d06..91ef974 100644
--- a/.claude/scripts/sync-template-to-target.py
+++ b/.claude/scripts/sync-template-to-target.py
@@ -44,6 +44,12 @@ MIRROR_DIRS: list[str] = [
     ".claude/shared/work-templates",
 ]
 
+MIRROR_TOP_FILES: list[str] = [
+    ".github/workflows/dual-implement-ci.yml",
+    "CHANGELOG.md",
+    "mypy.ini",
+]
+
 # Files inside MIRROR_DIRS that must NEVER be copied (secrets, caches, etc.)
 EXCLUDE_NAMES: set[str] = {
     "__pycache__",
@@ -270,6 +276,48 @@ def collect_dir(root: Path) -> list[Path]:
     return out
 
 
+def mirror_file(
+    src_file: Path,
+    tgt_file: Path,
+    rel_display: str,
+    tgt_root: Path,
+    plan: Plan,
+    apply: bool,
+    force: bool = False,
+    snapshot: RollbackSnapshot | None = None,
+) -> None:
+    logger.info(
+        "mirror_file.enter rel_display=%s apply=%s force=%s",
+        rel_display,
+        apply,
+        force,
+    )
+    if not src_file.is_file():
+        logger.info("mirror_file.exit action=missing-source rel_display=%s", rel_display)
+        return
+    if tgt_file.exists():
+        if filecmp.cmp(src_file, tgt_file, shallow=False):
+            plan.same_files += 1
+            logger.info("mirror_file.exit action=same rel_display=%s", rel_display)
+            return
+        if _should_skip_locally_modified(tgt_root, tgt_file, rel_display, plan, force):
+            logger.info("mirror_file.exit action=skipped rel_display=%s", rel_display)
+            return
+        plan.changed_files.append((str(src_file), str(tgt_file)))
+        if apply:
+            tgt_file.parent.mkdir(parents=True, exist_ok=True)
+            if snapshot is not None:
+                snapshot.capture(tgt_file, rel_display)
+            shutil.copy2(src_file, tgt_file)
+        logger.info("mirror_file.exit action=changed rel_display=%s", rel_display)
+        return
+    plan.new_files.append((str(src_file), str(tgt_file)))
+    if apply:
+        tgt_file.parent.mkdir(parents=True, exist_ok=True)
+        shutil.copy2(src_file, tgt_file)
+    logger.info("mirror_file.exit action=new rel_display=%s", rel_display)
+
+
 def mirror_category(
     src_root: Path,
     tgt_root: Path,
@@ -291,23 +339,7 @@ def mirror_category(
         if s.name in EXCLUDE_NAMES:
             plan.skipped_files.append((rel_display, "secret-name"))
             continue
-        if t.exists():
-            if filecmp.cmp(s, t, shallow=False):
-                plan.same_files += 1
-                continue
-            if _should_skip_locally_modified(tgt_root, t, rel_display, plan, force):
-                continue
-            plan.changed_files.append((str(s), str(t)))
-            if apply:
-                t.parent.mkdir(parents=True, exist_ok=True)
-                if snapshot is not None:
-                    snapshot.capture(t, rel_display)
-                shutil.copy2(s, t)
-        else:
-            plan.new_files.append((str(s), str(t)))
-            if apply:
-                t.parent.mkdir(parents=True, exist_ok=True)
-                shutil.copy2(s, t)
+        mirror_file(s, t, rel_display, tgt_root, plan, apply, force, snapshot)
 
 
 def merge_settings(
@@ -442,6 +474,8 @@ def main() -> int:
     snapshot = RollbackSnapshot(tgt_root) if args.apply else None
     for rel in MIRROR_DIRS:
         mirror_category(src_root, tgt_root, rel, plan, args.apply, args.force, snapshot)
+    for rel in MIRROR_TOP_FILES:
+        mirror_file(src_root / rel, tgt_root / rel, rel, tgt_root, plan, args.apply, args.force, snapshot)
     merge_settings(src_root, tgt_root, plan, args.apply, args.force, snapshot)
     merge_gitignore(tgt_root, plan, args.apply, args.force, snapshot)
     if snapshot is not None and snapshot.snapshot_dir is not None:
diff --git a/.claude/scripts/test_sync_template_to_target.py b/.claude/scripts/test_sync_template_to_target.py
index 402e856..a62fddc 100644
--- a/.claude/scripts/test_sync_template_to_target.py
+++ b/.claude/scripts/test_sync_template_to_target.py
@@ -16,6 +16,9 @@ sys.modules["sync_template_to_target"] = sync
 SPEC.loader.exec_module(sync)
 
 REL_FILE = ".claude/scripts/example.py"
+TOP_DUAL_CI = ".github/workflows/dual-implement-ci.yml"
+TOP_CHANGELOG = "CHANGELOG.md"
+TOP_MYPY = "mypy.ini"
 
 
 def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
@@ -48,6 +51,32 @@ def _make_sync_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
     return src, tgt, tgt / REL_FILE
 
 
+def _commit_target_files(tgt: Path, *rel_files: str) -> None:
+    _git(tgt, "init", "-q")
+    _git(tgt, "config", "user.email", "test@example.invalid")
+    _git(tgt, "config", "user.name", "Test User")
+    _git(tgt, "add", *rel_files)
+    _git(tgt, "commit", "-q", "-m", "initial")
+
+
+def _run_template_sync(src: Path, tgt: Path, force: bool = False) -> int:
+    old_argv = sys.argv
+    sys.argv = [
+        "sync-template-to-target.py",
+        "--src",
+        str(src),
+        "--tgt",
+        str(tgt),
+        "--apply",
+    ]
+    if force:
+        sys.argv.append("--force")
+    try:
+        return sync.main()
+    finally:
+        sys.argv = old_argv
+
+
 def _apply_scripts_sync(src: Path, tgt: Path, force: bool) -> tuple[object, object]:
     plan = sync.Plan()
     snapshot = sync.RollbackSnapshot(tgt)
@@ -63,6 +92,57 @@ def _apply_scripts_sync(src: Path, tgt: Path, force: bool) -> tuple[object, obje
     return plan, snapshot
 
 
+def test_mirror_top_files_constant_lists_three_files() -> None:
+    assert sync.MIRROR_TOP_FILES == [TOP_DUAL_CI, TOP_CHANGELOG, TOP_MYPY]
+
+
+def test_sync_mirrors_top_level_dual_implement_ci_yml(tmp_path: Path) -> None:
+    src = tmp_path / "src"
+    tgt = tmp_path / "tgt"
+    (src / ".claude").mkdir(parents=True)
+    _write(src / TOP_DUAL_CI, "template ci\n")
+    _write(tgt / TOP_DUAL_CI, "target ci\n")
+    _commit_target_files(tgt, TOP_DUAL_CI)
+
+    assert _run_template_sync(src, tgt) == 0
+
+    assert (tgt / TOP_DUAL_CI).read_text(encoding="utf-8") == "template ci\n"
+    snapshots = list((tgt / sync.ROLLBACK_SNAPSHOT_DIR).glob(f"*/{TOP_DUAL_CI}"))
+    assert len(snapshots) == 1
+    assert snapshots[0].read_text(encoding="utf-8") == "target ci\n"
+
+
+def test_sync_mirrors_top_level_changelog_and_mypy_ini(tmp_path: Path) -> None:
+    src = tmp_path / "src"
+    tgt = tmp_path / "tgt"
+    (src / ".claude").mkdir(parents=True)
+    _write(src / TOP_CHANGELOG, "template changelog\n")
+    _write(src / TOP_MYPY, "[mypy]\ntemplate = true\n")
+    _write(tgt / TOP_CHANGELOG, "target changelog\n")
+    _write(tgt / TOP_MYPY, "[mypy]\ntarget = true\n")
+    _commit_target_files(tgt, TOP_CHANGELOG, TOP_MYPY)
+
+    assert _run_template_sync(src, tgt) == 0
+
+    assert (tgt / TOP_CHANGELOG).read_text(encoding="utf-8") == "template changelog\n"
+    assert (tgt / TOP_MYPY).read_text(encoding="utf-8") == "[mypy]\ntemplate = true\n"
+
+
+def test_top_files_skipped_when_locally_modified_without_force(tmp_path: Path) -> None:
+    src = tmp_path / "src"
+    tgt = tmp_path / "tgt"
+    (src / ".claude").mkdir(parents=True)
+    _write(src / TOP_CHANGELOG, "template changelog\n")
+    _write(tgt / TOP_CHANGELOG, "target changelog\n")
+    _commit_target_files(tgt, TOP_CHANGELOG)
+    (tgt / TOP_CHANGELOG).write_text("local changelog\n", encoding="utf-8")
+
+    assert _run_template_sync(src, tgt) == 0
+
+    assert (tgt / TOP_CHANGELOG).read_text(encoding="utf-8") == "local changelog\n"
+    assert not (tgt / sync.ROLLBACK_SNAPSHOT_DIR).exists()
+
+
 def test_sync_skips_locally_modified_without_force(tmp_path: Path) -> None:
     src, tgt, target_file = _make_sync_fixture(tmp_path)
     target_file.write_text("local change\n", encoding="utf-8")
```

## Test Output

### `python -m pytest .claude/scripts/test_sync_template_to_target.py -v --tb=line`

- returncode: 0  - passed: True  - timed_out: False

```
--- stdout ---
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.2, pluggy-1.6.0 -- C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z33\codex\task-Z33-full-parity-sync
plugins: anyio-4.12.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 9 items

.claude/scripts/test_sync_template_to_target.py::test_mirror_top_files_constant_lists_three_files PASSED [ 11%]
.claude/scripts/test_sync_template_to_target.py::test_sync_mirrors_top_level_dual_implement_ci_yml PASSED [ 22%]
.claude/scripts/test_sync_template_to_target.py::test_sync_mirrors_top_level_changelog_and_mypy_ini PASSED [ 33%]
.claude/scripts/test_sync_template_to_target.py::test_top_files_skipped_when_locally_modified_without_force PASSED [ 44%]
.claude/scripts/test_sync_template_to_target.py::test_sync_skips_locally_modified_without_force PASSED [ 55%]
.claude/scripts/test_sync_template_to_target.py::test_sync_overwrites_locally_modified_with_force PASSED [ 66%]
.claude/scripts/test_sync_template_to_target.py::test_sync_normal_overwrite_when_target_clean PASSED [ 77%]
.claude/scripts/test_sync_template_to_target.py::test_sync_creates_rollback_snapshot PASSED [ 88%]
.claude/scripts/test_sync_template_to_target.py::test_rollback_restores_pre_sync_state PASSED [100%]

============================== 9 passed in 1.15s ==============================
```

### `python -m pytest .claude/hooks/test_enforcer_live_attacks.py -q --tb=line`

- returncode: 0  - passed: True  - timed_out: False

```
--- stdout ---
.........................                                                [100%]
25 passed in 1.50s
```

### `python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/scripts/test_spawn_agent.py .claude/scripts/test_determinism_chaos.py .claude/scripts/test_archive_active_context.py .claude/scripts/test_generate_changelog.py .claude/scripts/test_verify_codex_auth.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line`

- returncode: 0  - passed: True  - timed_out: False

```
--- stdout ---
........................................................................ [ 24%]
........................................................................ [ 48%]
........................................................................ [ 73%]
........................................................................ [ 97%]
.......                                                                  [100%]
============================== warnings summary ===============================
.claude\scripts\judge_axes.py:46
  C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z33\codex\task-Z33-full-parity-sync\.claude\scripts\judge_axes.py:46: PytestCollectionWarning: cannot collect test class 'TestRun' because it has a __init__ constructor (from: .claude/scripts/test_judge.py)
    @dataclass

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
295 passed, 1 warning in 7.28s
```

### `python .claude/scripts/dual-teams-selftest.py`

- returncode: 0  - passed: True  - timed_out: False

```
--- stdout ---
[PASS] preflight-clean-with-sentinel-V1                     (56 ms)
[PASS] preflight-clean-with-sentinel-V2                     (53 ms)
[PASS] is_dual_teams_worktree-true-on-V1                    ( 1 ms)
[PASS] is_dual_teams_worktree-true-on-V2                    ( 1 ms)
[PASS] judge-axes-sees-claude-committed-py                  (28 ms)
[PASS] judge-axes-sees-codex-untracked-py                   (46 ms)
selftest: 6 checks, 6 passed, 0 failed (547 ms)
--- stderr ---
{"json_output": false, "keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: main", "ts": "2026-04-26T19:12:18.531325+00:00"}
{"keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: run_selftest", "ts": "2026-04-26T19:12:18.531325+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: setup_transient_repo", "tmpdir": "C:\\Users\\Lenovo\\AppData\\Local\\Temp\\dual-teams-selftest-uziybglo", "ts": "2026-04-26T19:12:18.532324+00:00"}
{"base_sha": "b75187ed245b98fd55a534342b3ea7c0518fde03", "duration_ms": 262, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: setup_transient_repo", "ts": "2026-04-26T19:12:18.794524+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: load_integrations", "project_root": "C:\\Bots\\Migrator bots\\claude-project-template-update\\worktrees\\criterion-upgrade-z33\\codex\\task-Z33-full-parity-sync", "ts": "2026-04-26T19:12:18.794524+00:00"}
{"duration_ms": 5, "failures": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: load_integrations", "ts": "2026-04-26T19:12:18.799530+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: build_results", "ts": "2026-04-26T19:12:18.799530+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T19:12:18.799530+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "detail": "git status --porcelain empty", "duration_ms": 56, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T19:12:18.855817+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T19:12:18.855817+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "detail": "git status --porcelain empty", "duration_ms": 53, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T19:12:18.908815+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T19:12:18.908815+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T19:12:18.908815+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T19:12:18.908815+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T19:12:18.908815+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T19:12:18.974354+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "detail": "saw claude_probe.py", "duration_ms": 28, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T19:12:19.002360+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T19:12:19.002360+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "detail": "saw codex_probe.py", "duration_ms": 46, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T19:12:19.047671+00:00"}
{"checks": 6, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: build_results", "ts": "2026-04-26T19:12:19.047671+00:00"}
{"checks": 6, "duration_ms": 547, "failed": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: run_selftest", "passed": 6, "ts": "2026-04-26T19:12:19.079135+00:00"}
{"exit_code": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: main", "ts": "2026-04-26T19:12:19.079135+00:00"}
```

## Self-Report (Codex NOTE/BLOCKER lines)

(no NOTE/BLOCKER lines)

## Codex stderr

```
OpenAI Codex v0.125.0 (research preview)
--------
workdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z33\codex\task-Z33-full-parity-sync
model: gpt-5.5
provider: chatgpt
approval: never
sandbox: danger-full-access
reasoning effort: xhigh
reasoning summaries: none
session id: 019dcb33-4578-76b2-a243-788b7314b181
--------
user
You are the single-task implementer. The task specification below is IMMUTABLE.
Write code to satisfy all Acceptance Criteria. Do NOT modify files listed in
Forbidden Paths or Read-Only Files. After writing code, run every Test Command
listed in the task and report the result in your self-report.
Any AGENTS.md or CLAUDE.md in the worktree is authoritative background context.

---- TASK SPECIFICATION ----

---
task_id: Z33-full-parity-sync
title: Full QA-Legal parity sync — top-level CI/CHANGELOG/mypy.ini mirroring
executor: dual
risk_class: routine
speed_profile: balanced
---

# Task Z33

## Goal

User wants QA Legal byte-identical infrastructure to template (except
project-specific files). Current `sync-template-to-target.py` mirrors
`.claude/...` categories but SKIPS three top-level files created in
Round 8: `.github/workflows/dual-implement-ci.yml` (Z26),
`CHANGELOG.md` (Z26), `mypy.ini` (Z32). They must land in target for
full parity.

## The fix

In `.claude/scripts/sync-template-to-target.py` add new constant
`MIRROR_TOP_FILES` listing the three relative paths above. After the
per-category mirror loop, iterate this list and use the same per-file
helper (with `--force` and rollback semantics).

Add 4 tests in `test_sync_template_to_target.py`:
- `test_mirror_top_files_constant_lists_three_files`
- `test_sync_mirrors_top_level_dual_implement_ci_yml`
- `test_sync_mirrors_top_level_changelog_and_mypy_ini`
- `test_top_files_skipped_when_locally_modified_without_force`

## Scope Fence

```
.claude/scripts/sync-template-to-target.py
.claude/scripts/test_sync_template_to_target.py
```

DO NOT modify any other file.

## Read-Only Files / Evaluation Firewall

- `work/criterion-upgrade/task-Z33-full-parity-sync.md`
- `.github/workflows/dual-implement-ci.yml`, `CHANGELOG.md`, `mypy.ini`
  (source files; do not modify)

## Acceptance Criteria

### AC-1
`test_mirror_top_files_constant_lists_three_files` PASSES.

### AC-2
`test_sync_mirrors_top_level_dual_implement_ci_yml` PASSES.

### AC-3
`test_sync_mirrors_top_level_changelog_and_mypy_ini` PASSES.

### AC-4
`test_top_files_skipped_when_locally_modified_without_force` PASSES.

### AC-5: Existing tests still pass
```bash
python -m pytest .claude/scripts/test_sync_template_to_target.py -q --tb=line
```

### AC-6: Live attack matrix 25/25
```bash
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -q --tb=line
```

### AC-7: Selftest 6/6
`python .claude/scripts/dual-teams-selftest.py`

## Test Commands

```bash
python -m pytest .claude/scripts/test_sync_template_to_target.py -v --tb=line
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -q --tb=line
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/scripts/test_spawn_agent.py .claude/scripts/test_determinism_chaos.py .claude/scripts/test_archive_active_context.py .claude/scripts/test_generate_changelog.py .claude/scripts/test_verify_codex_auth.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line
python .claude/scripts/dual-teams-selftest.py
```

## Implementation hints

- `MIRROR_TOP_FILES` near `MIRROR_DIRS`.
- After category loop add `for top in MIRROR_TOP_FILES: <call same per-file helper>`.
- Honor `--force` (refuse overwrite of locally-modified target without it)
  AND `--rollback` (snapshot pre-state) — same as existing mirror behavior.
- Tests use `tmp_path` fixture for synthetic source/target trees.

## Self-report format

```
=== TASK Z33 SELF-REPORT ===
- status: pass | fail | blocker
- approach: <1 line>
- new tests: <count>
- existing tests pass: yes / no
- attack matrix 25/25: yes / no
- selftest 6/6: PASS / FAIL
- net lines: <approx>
- files modified: [list]
- conflict guard works for top files: yes / no
- NOTE: <surprising>
- BLOCKER: <only if>
- Final commit SHA: <SHA>
=== END SELF-REPORT ===
```


---- END TASK SPECIFICATION ----
Return a short self-report at the end of your run using lines starting with
`NOTE:` for observations and `BLOCKER:` for unresolved problems.

codex
I’ll inspect the sync script and its existing tests first, then make the smallest scoped change in the two allowed files and run the required commands.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z33\codex\task-Z33-full-parity-sync
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "MIRROR_DIRS|mirror|force|rollback|copy" .claude/scripts/sync-template-to-target.py .claude/scripts/test_sync_template_to_target.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z33\codex\task-Z33-full-parity-sync
 succeeded in 135ms:
 succeeded in 134ms:
.claude/scripts/test_sync_template_to_target.py:1:"""Tests for sync-template-to-target.py conflict guard and rollback."""
.claude/scripts/test_sync_template_to_target.py:62:def _run_template_sync(src: Path, tgt: Path, force: bool = False) -> int:
.claude/scripts/test_sync_template_to_target.py:72:    if force:
.claude/scripts/test_sync_template_to_target.py:73:        sys.argv.append("--force")
.claude/scripts/test_sync_template_to_target.py:80:def _apply_scripts_sync(src: Path, tgt: Path, force: bool) -> tuple[object, object]:
.claude/scripts/test_sync_template_to_target.py:83:    sync.mirror_category(
.claude/scripts/test_sync_template_to_target.py:89:        force=force,
.claude/scripts/test_sync_template_to_target.py:95:def test_mirror_top_files_constant_lists_three_files() -> None:
.claude/scripts/test_sync_template_to_target.py:99:def test_sync_mirrors_top_level_dual_implement_ci_yml(tmp_path: Path) -> None:
.claude/scripts/test_sync_template_to_target.py:115:def test_sync_mirrors_top_level_changelog_and_mypy_ini(tmp_path: Path) -> None:
.claude/scripts/test_sync_template_to_target.py:131:def test_top_files_skipped_when_locally_modified_without_force(tmp_path: Path) -> None:
.claude/scripts/test_sync_template_to_target.py:146:def test_sync_skips_locally_modified_without_force(tmp_path: Path) -> None:
.claude/scripts/test_sync_template_to_target.py:150:    plan, snapshot = _apply_scripts_sync(src, tgt, force=False)
.claude/scripts/test_sync_template_to_target.py:158:def test_sync_overwrites_locally_modified_with_force(tmp_path: Path) -> None:
.claude/scripts/test_sync_template_to_target.py:162:    plan, snapshot = _apply_scripts_sync(src, tgt, force=True)
.claude/scripts/test_sync_template_to_target.py:174:    plan, snapshot = _apply_scripts_sync(src, tgt, force=False)
.claude/scripts/test_sync_template_to_target.py:182:def test_sync_creates_rollback_snapshot(tmp_path: Path) -> None:
.claude/scripts/test_sync_template_to_target.py:185:    _plan, snapshot = _apply_scripts_sync(src, tgt, force=False)
.claude/scripts/test_sync_template_to_target.py:193:def test_rollback_restores_pre_sync_state(tmp_path: Path) -> None:
.claude/scripts/test_sync_template_to_target.py:195:    _plan, snapshot = _apply_scripts_sync(src, tgt, force=False)
.claude/scripts/test_sync_template_to_target.py:198:    restored_from = sync.rollback_latest_snapshot(tgt)
.claude/scripts/sync-template-to-target.py:5:  * MIRROR  — full per-category copy (overwrite differing files, add missing).
.claude/scripts/sync-template-to-target.py:34:MIRROR_DIRS: list[str] = [
.claude/scripts/sync-template-to-target.py:53:# Files inside MIRROR_DIRS that must NEVER be copied (secrets, caches, etc.)
.claude/scripts/sync-template-to-target.py:62:# Special-handled files (NOT copied as part of MIRROR_DIRS)
.claude/scripts/sync-template-to-target.py:78:ROLLBACK_SNAPSHOT_DIR = ".claude/sync-rollback-snapshot"
.claude/scripts/sync-template-to-target.py:92:    rollback_snapshot: str | None = None
.claude/scripts/sync-template-to-target.py:126:        shutil.copy2(target_file, snapshot_file)
.claude/scripts/sync-template-to-target.py:189:    force: bool,
.claude/scripts/sync-template-to-target.py:192:        "_should_skip_locally_modified.enter rel_display=%s force=%s",
.claude/scripts/sync-template-to-target.py:194:        force,
.claude/scripts/sync-template-to-target.py:196:    if force:
.claude/scripts/sync-template-to-target.py:197:        logger.info("_should_skip_locally_modified.exit skipped=False reason=force")
.claude/scripts/sync-template-to-target.py:214:def _latest_rollback_snapshot(tgt_root: Path) -> Path | None:
.claude/scripts/sync-template-to-target.py:215:    logger.info("_latest_rollback_snapshot.enter tgt_root=%s", tgt_root)
.claude/scripts/sync-template-to-target.py:218:        logger.info("_latest_rollback_snapshot.exit found=False reason=no-root")
.claude/scripts/sync-template-to-target.py:222:        logger.info("_latest_rollback_snapshot.exit found=False reason=empty")
.claude/scripts/sync-template-to-target.py:225:    logger.info("_latest_rollback_snapshot.exit found=True latest=%s", latest)
.claude/scripts/sync-template-to-target.py:229:def rollback_latest_snapshot(tgt_root: Path) -> Path | None:
.claude/scripts/sync-template-to-target.py:230:    logger.info("rollback_latest_snapshot.enter tgt_root=%s", tgt_root)
.claude/scripts/sync-template-to-target.py:231:    latest = _latest_rollback_snapshot(tgt_root)
.claude/scripts/sync-template-to-target.py:233:        logger.info("rollback_latest_snapshot.exit restored=False reason=no-snapshot")
.claude/scripts/sync-template-to-target.py:243:            shutil.copy2(snapshot_file, target_file)
.claude/scripts/sync-template-to-target.py:246:        logger.exception("rollback_latest_snapshot.exit restored=False latest=%s", latest)
.claude/scripts/sync-template-to-target.py:249:        "rollback_latest_snapshot.exit restored=True latest=%s files=%d",
.claude/scripts/sync-template-to-target.py:279:def mirror_file(
.claude/scripts/sync-template-to-target.py:286:    force: bool = False,
.claude/scripts/sync-template-to-target.py:290:        "mirror_file.enter rel_display=%s apply=%s force=%s",
.claude/scripts/sync-template-to-target.py:293:        force,
.claude/scripts/sync-template-to-target.py:296:        logger.info("mirror_file.exit action=missing-source rel_display=%s", rel_display)
.claude/scripts/sync-template-to-target.py:301:            logger.info("mirror_file.exit action=same rel_display=%s", rel_display)
.claude/scripts/sync-template-to-target.py:303:        if _should_skip_locally_modified(tgt_root, tgt_file, rel_display, plan, force):
.claude/scripts/sync-template-to-target.py:304:            logger.info("mirror_file.exit action=skipped rel_display=%s", rel_display)
.claude/scripts/sync-template-to-target.py:311:            shutil.copy2(src_file, tgt_file)
.claude/scripts/sync-template-to-target.py:312:        logger.info("mirror_file.exit action=changed rel_display=%s", rel_display)
.claude/scripts/sync-template-to-target.py:317:        shutil.copy2(src_file, tgt_file)
.claude/scripts/sync-template-to-target.py:318:    logger.info("mirror_file.exit action=new rel_display=%s", rel_display)
.claude/scripts/sync-template-to-target.py:321:def mirror_category(
.claude/scripts/sync-template-to-target.py:327:    force: bool = False,
.claude/scripts/sync-template-to-target.py:342:        mirror_file(s, t, rel_display, tgt_root, plan, apply, force, snapshot)
.claude/scripts/sync-template-to-target.py:350:    force: bool = False,
.claude/scripts/sync-template-to-target.py:360:    if t.exists() and _should_skip_locally_modified(tgt_root, t, SETTINGS_JSON, plan, force):
.claude/scripts/sync-template-to-target.py:369:        shutil.copy2(s, t)
.claude/scripts/sync-template-to-target.py:376:    force: bool = False,
.claude/scripts/sync-template-to-target.py:390:    if t.exists() and _should_skip_locally_modified(tgt_root, t, GITIGNORE, plan, force):
.claude/scripts/sync-template-to-target.py:413:    if plan.rollback_snapshot:
.claude/scripts/sync-template-to-target.py:414:        print(f"rollback snap   : {plan.rollback_snapshot}")
.claude/scripts/sync-template-to-target.py:445:    ap.add_argument("--force", action="store_true", help="overwrite locally modified target files")
.claude/scripts/sync-template-to-target.py:446:    ap.add_argument("--rollback", action="store_true", help="restore the latest pre-sync snapshot")
.claude/scripts/sync-template-to-target.py:455:    if args.rollback:
.claude/scripts/sync-template-to-target.py:457:            restored_from = rollback_latest_snapshot(tgt_root)
.claude/scripts/sync-template-to-target.py:459:            print(f"ERROR: rollback failed: {exc}", file=sys.stderr)
.claude/scripts/sync-template-to-target.py:462:            print(f"ERROR: no rollback snapshot found under {tgt_root / ROLLBACK_SNAPSHOT_DIR}", file=sys.stderr)
.claude/scripts/sync-template-to-target.py:475:    for rel in MIRROR_DIRS:
.claude/scripts/sync-template-to-target.py:476:        mirror_category(src_root, tgt_root, rel, plan, args.apply, args.force, snapshot)
.claude/scripts/sync-template-to-target.py:478:        mirror_file(src_root / rel, tgt_root / rel, rel, tgt_root, plan, args.apply, args.force, snapshot)
.claude/scripts/sync-template-to-target.py:479:    merge_settings(src_root, tgt_root, plan, args.apply, args.force, snapshot)
.claude/scripts/sync-template-to-target.py:480:    merge_gitignore(tgt_root, plan, args.apply, args.force, snapshot)
.claude/scripts/sync-template-to-target.py:482:        plan.rollback_snapshot = str(snapshot.snapshot_dir)

codex
The worktree is currently clean. I’m seeing the requested test names already present, so I’ll verify whether they are stubs/expected failures and inspect the exact implementation gap before editing.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path .claude/scripts/sync-template-to-target.py | Select-Object -First 540' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z33\codex\task-Z33-full-parity-sync
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path .claude/scripts/test_sync_template_to_target.py | Select-Object -First 260' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z33\codex\task-Z33-full-parity-sync
 succeeded in 186ms:
"""Mirror this project's .claude/ infrastructure into a target project.

Decisions encoded here (see SESSION-RESUME-CONTEXT-v2.md for the why):

  * MIRROR  вЂ” full per-category copy (overwrite differing files, add missing).
  * MERGE   вЂ” smart structural merge (settings.json deep-merge, .gitignore line-add).
  * PROTECT вЂ” never read, never write. Includes secrets, project-specific session
              data, project source code, and the entire new-project sub-template.

Run order:
  1) python sync-template-to-target.py --tgt "C:/path/to/target"        # dry-run plan
  2) python sync-template-to-target.py --tgt "C:/path/to/target" --apply # do it

Idempotent. Safe to re-run. Never deletes files outside __pycache__.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import filecmp
import json
import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------

MIRROR_DIRS: list[str] = [
    ".claude/scripts",
    ".claude/hooks",
    ".claude/guides",
    ".claude/agents",
    ".claude/commands",
    ".claude/prompts",
    ".claude/schemas",
    ".claude/skills/dual-implement",
    ".claude/ops",
    ".claude/shared/work-templates",
]

MIRROR_TOP_FILES: list[str] = [
    ".github/workflows/dual-implement-ci.yml",
    "CHANGELOG.md",
    "mypy.ini",
]

# Files inside MIRROR_DIRS that must NEVER be copied (secrets, caches, etc.)
EXCLUDE_NAMES: set[str] = {
    "__pycache__",
    ".env",
    ".env.local",
    ".env.production",
}
EXCLUDE_SUFFIXES: tuple[str, ...] = (".pyc", ".pyo")

# Special-handled files (NOT copied as part of MIRROR_DIRS)
SETTINGS_JSON = ".claude/settings.json"
GITIGNORE = ".gitignore"

# Lines that MUST be present in target .gitignore (added if missing)
GITIGNORE_REQUIRED_LINES: list[str] = [
    ".dual-base-ref",
    ".claude/scheduled_tasks.lock",
    ".claude/tmp/",
    ".claude/logs/",
    ".claude/hooks/.env",
    ".claude/settings.local.json",
    "worktrees/",
]

LOCAL_MODIFIED_SKIP_REASON = "LocallyModifiedSkipped"
ROLLBACK_SNAPSHOT_DIR = ".claude/sync-rollback-snapshot"
GIT_TIMEOUT_SECONDS = 30

logger = logging.getLogger(__name__)


@dataclass
class Plan:
    new_files: list[tuple[str, str]] = field(default_factory=list)      # (src, tgt)
    changed_files: list[tuple[str, str]] = field(default_factory=list)
    same_files: int = 0
    skipped_files: list[tuple[str, str]] = field(default_factory=list)  # (path, reason)
    settings_action: str = "no-op"
    gitignore_added: list[str] = field(default_factory=list)
    rollback_snapshot: str | None = None


@dataclass
class RollbackSnapshot:
    tgt_root: Path
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    )
    snapshot_dir: Path | None = None
    captured_files: list[str] = field(default_factory=list)

    def capture(self, target_file: Path, rel_file: str) -> None:
        logger.info(
            "RollbackSnapshot.capture.enter tgt_root=%s rel_file=%s",
            self.tgt_root,
            rel_file,
        )
        if not target_file.exists():
            logger.info(
                "RollbackSnapshot.capture.exit captured=False reason=missing rel_file=%s",
                rel_file,
            )
            return
        if self.snapshot_dir is None:
            self.snapshot_dir = self.tgt_root / ROLLBACK_SNAPSHOT_DIR / self.timestamp
        snapshot_file = self.snapshot_dir / Path(rel_file)
        if snapshot_file.exists():
            logger.info(
                "RollbackSnapshot.capture.exit captured=False reason=already-captured rel_file=%s",
                rel_file,
            )
            return
        snapshot_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target_file, snapshot_file)
        self.captured_files.append(rel_file)
        logger.info(
            "RollbackSnapshot.capture.exit captured=True snapshot_file=%s",
            snapshot_file,
        )


def _target_has_local_changes(tgt_repo: Path, file: Path | str) -> bool:
    logger.info(
        "_target_has_local_changes.enter tgt_repo=%s file=%s",
        tgt_repo,
        file,
    )
    rel_file = Path(file)
    if rel_file.is_absolute():
        try:
            rel_file = rel_file.resolve().relative_to(tgt_repo.resolve())
        except ValueError:
            logger.warning(
                "_target_has_local_changes.exit dirty=False reason=outside-repo file=%s",
                file,
            )
            return False
    try:
        proc = subprocess.run(
            [
                "git",
                "-C",
                str(tgt_repo),
                "diff",
                "--quiet",
                "--",
                rel_file.as_posix(),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        logger.exception(
            "_target_has_local_changes.exit dirty=False reason=git-exception file=%s",
            rel_file,
        )
        return False
    dirty = proc.returncode == 1
    if proc.returncode not in (0, 1):
        logger.warning(
            "_target_has_local_changes.exit dirty=False reason=git-returncode returncode=%d stderr=%s",
            proc.returncode,
            proc.stderr.strip(),
        )
        return False
    logger.info("_target_has_local_changes.exit dirty=%s file=%s", dirty, rel_file)
    return dirty


def _should_skip_locally_modified(
    tgt_root: Path,
    target_file: Path,
    rel_display: str,
    plan: Plan,
    force: bool,
) -> bool:
    logger.info(
        "_should_skip_locally_modified.enter rel_display=%s force=%s",
        rel_display,
        force,
    )
    if force:
        logger.info("_should_skip_locally_modified.exit skipped=False reason=force")
        return False
    if _target_has_local_changes(tgt_root, Path(rel_display)):
        plan.skipped_files.append((rel_display, LOCAL_MODIFIED_SKIP_REASON))
        print(
            f"WARNING: skipping locally modified target file: {rel_display}",
            file=sys.stderr,
        )
        logger.warning(
            "_should_skip_locally_modified.exit skipped=True rel_display=%s",
            rel_display,
        )
        return True
    logger.info("_should_skip_locally_modified.exit skipped=False reason=clean")
    return False


def _latest_rollback_snapshot(tgt_root: Path) -> Path | None:
    logger.info("_latest_rollback_snapshot.enter tgt_root=%s", tgt_root)
    snapshot_root = tgt_root / ROLLBACK_SNAPSHOT_DIR
    if not snapshot_root.is_dir():
        logger.info("_latest_rollback_snapshot.exit found=False reason=no-root")
        return None
    snapshots = [path for path in snapshot_root.iterdir() if path.is_dir()]
    if not snapshots:
        logger.info("_latest_rollback_snapshot.exit found=False reason=empty")
        return None
    latest = sorted(snapshots, key=lambda path: path.name)[-1]
    logger.info("_latest_rollback_snapshot.exit found=True latest=%s", latest)
    return latest


def rollback_latest_snapshot(tgt_root: Path) -> Path | None:
    logger.info("rollback_latest_snapshot.enter tgt_root=%s", tgt_root)
    latest = _latest_rollback_snapshot(tgt_root)
    if latest is None:
        logger.info("rollback_latest_snapshot.exit restored=False reason=no-snapshot")
        return None
    restored = 0
    try:
        for snapshot_file in latest.rglob("*"):
            if not snapshot_file.is_file():
                continue
            rel_file = snapshot_file.relative_to(latest)
            target_file = tgt_root / rel_file
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(snapshot_file, target_file)
            restored += 1
    except OSError:
        logger.exception("rollback_latest_snapshot.exit restored=False latest=%s", latest)
        raise
    logger.info(
        "rollback_latest_snapshot.exit restored=True latest=%s files=%d",
        latest,
        restored,
    )
    return latest


def is_excluded(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDE_NAMES:
        return True
    if path.name in EXCLUDE_NAMES:
        return True
    return path.suffix in EXCLUDE_SUFFIXES


def collect_dir(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    out: list[Path] = []
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        rel = p.relative_to(root)
        if is_excluded(rel):
            continue
        out.append(rel)
    return out


def mirror_file(
    src_file: Path,
    tgt_file: Path,
    rel_display: str,
    tgt_root: Path,
    plan: Plan,
    apply: bool,
    force: bool = False,
    snapshot: RollbackSnapshot | None = None,
) -> None:
    logger.info(
        "mirror_file.enter rel_display=%s apply=%s force=%s",
        rel_display,
        apply,
        force,
    )
    if not src_file.is_file():
        logger.info("mirror_file.exit action=missing-source rel_display=%s", rel_display)
        return
    if tgt_file.exists():
        if filecmp.cmp(src_file, tgt_file, shallow=False):
            plan.same_files += 1
            logger.info("mirror_file.exit action=same rel_display=%s", rel_display)
            return
        if _should_skip_locally_modified(tgt_root, tgt_file, rel_display, plan, force):
            logger.info("mirror_file.exit action=skipped rel_display=%s", rel_display)
            return
        plan.changed_files.append((str(src_file), str(tgt_file)))
        if apply:
            tgt_file.parent.mkdir(parents=True, exist_ok=True)
            if snapshot is not None:
                snapshot.capture(tgt_file, rel_display)
            shutil.copy2(src_file, tgt_file)
        logger.info("mirror_file.exit action=changed rel_display=%s", rel_display)
        return
    plan.new_files.append((str(src_file), str(tgt_file)))
    if apply:
        tgt_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, tgt_file)
    logger.info("mirror_file.exit action=new rel_display=%s", rel_display)


def mirror_category(
    src_root: Path,
    tgt_root: Path,
    rel_dir: str,
    plan: Plan,
    apply: bool,
    force: bool = False,
    snapshot: RollbackSnapshot | None = None,
) -> None:
    src_dir = src_root / rel_dir
    tgt_dir = tgt_root / rel_dir
    if not src_dir.is_dir():
        return
    rels = collect_dir(src_dir)
    for rel in rels:
        s = src_dir / rel
        t = tgt_dir / rel
        rel_display = f"{rel_dir}/{rel.as_posix()}"
        if s.name in EXCLUDE_NAMES:
            plan.skipped_files.append((rel_display, "secret-name"))
            continue
        mirror_file(s, t, rel_display, tgt_root, plan, apply, force, snapshot)


def merge_settings(
    src_root: Path,
    tgt_root: Path,
    plan: Plan,
    apply: bool,
    force: bool = False,
    snapshot: RollbackSnapshot | None = None,
) -> None:
    s = src_root / SETTINGS_JSON
    t = tgt_root / SETTINGS_JSON
    if not s.is_file():
        return
    if t.is_file() and filecmp.cmp(s, t, shallow=False):
        plan.settings_action = "identical"
        return
    if t.exists() and _should_skip_locally_modified(tgt_root, t, SETTINGS_JSON, plan, force):
        plan.settings_action = "skipped-local-modified"
        return
    plan.settings_action = "overwrite" if t.exists() else "create"
    if apply:
        json.loads(s.read_text(encoding="utf-8"))
        t.parent.mkdir(parents=True, exist_ok=True)
        if t.exists() and snapshot is not None:
            snapshot.capture(t, SETTINGS_JSON)
        shutil.copy2(s, t)


def merge_gitignore(
    tgt_root: Path,
    plan: Plan,
    apply: bool,
    force: bool = False,
    snapshot: RollbackSnapshot | None = None,
) -> None:
    t = tgt_root / GITIGNORE
    existing: list[str] = []
    if t.is_file():
        existing = t.read_text(encoding="utf-8").splitlines()
    existing_set = {line.strip() for line in existing}
    additions: list[str] = []
    for line in GITIGNORE_REQUIRED_LINES:
        if line not in existing_set:
            additions.append(line)
    if not additions:
        return
    if t.exists() and _should_skip_locally_modified(tgt_root, t, GITIGNORE, plan, force):
        return
    plan.gitignore_added = additions
    if apply:
        if t.exists() and snapshot is not None:
            snapshot.capture(t, GITIGNORE)
        block = ["", "# Added by template sync 2026-04-26 (Y6-Y17 dual-implement infrastructure)"]
        block.extend(additions)
        new_content = ("\n".join(existing).rstrip() + "\n" + "\n".join(block) + "\n")
        t.write_text(new_content, encoding="utf-8")


def report(plan: Plan, apply: bool) -> None:
    bar = "=" * 70
    print(bar)
    print(f"SYNC {'APPLIED' if apply else 'DRY-RUN PLAN'}")
    print(bar)
    print(f"NEW files       : {len(plan.new_files)}")
    print(f"CHANGED files   : {len(plan.changed_files)}")
    print(f"SAME (unchanged): {plan.same_files}")
    print(f"SKIPPED         : {len(plan.skipped_files)}")
    print(f"settings.json   : {plan.settings_action}")
    print(f".gitignore add  : {len(plan.gitignore_added)} lines")
    if plan.rollback_snapshot:
        print(f"rollback snap   : {plan.rollback_snapshot}")
    if plan.skipped_files:
        print("\nSKIPPED items (not copied):")
        for path, reason in plan.skipped_files:
            print(f"  - {path}  ({reason})")
    if plan.gitignore_added:
        print("\n.gitignore additions:")
        for line in plan.gitignore_added:
            print(f"  + {line}")
    if plan.new_files and not apply:
        print("\nFirst 15 NEW files:")
        for s, t in plan.new_files[:15]:
            rel = os.path.relpath(t, str(Path(t).parents[2]))
            print(f"  + {rel}")
        if len(plan.new_files) > 15:
            print(f"  ... and {len(plan.new_files) - 15} more")
    if plan.changed_files and not apply:
        print("\nFirst 15 CHANGED files:")
        for s, t in plan.changed_files[:15]:
            rel = os.path.relpath(t, str(Path(t).parents[2]))
            print(f"  ~ {rel}")
        if len(plan.changed_files) > 15:
            print(f"  ... and {len(plan.changed_files) - 15} more")
    print(bar)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=".", help="source template project root")
    ap.add_argument("--tgt", required=True, help="target project root")
    ap.add_argument("--apply", action="store_true", help="actually write changes")
    ap.add_argument("--force", action="store_true", help="overwrite locally modified target files")
    ap.add_argument("--rollback", action="store_true", help="restore the latest pre-sync snapshot")
    args = ap.parse_args()

    src_root = Path(args.src).resolve()
    tgt_root = Path(args.tgt).resolve()

    if not tgt_root.is_dir():
        print(f"ERROR: tgt does not exist: {tgt_root}", file=sys.stderr)
        return 2
    if args.rollback:
        try:
            restored_from = rollback_latest_snapshot(tgt_root)
        except OSError as exc:
            print(f"ERROR: rollback failed: {exc}", file=sys.stderr)
            return 2
        if restored_from is None:
            print(f"ERROR: no rollback snapshot found under {tgt_root / ROLLBACK_SNAPSHOT_DIR}", file=sys.stderr)
            return 1
        print(f"ROLLBACK restored from {restored_from}")
        return 0
    if src_root == tgt_root:
        print("ERROR: src and tgt point at the same directory", file=sys.stderr)
        return 2
    if not (src_root / ".claude").is_dir():
        print(f"ERROR: src has no .claude/: {src_root}", file=sys.stderr)
        return 2

    plan = Plan()
    snapshot = RollbackSnapshot(tgt_root) if args.apply else None
    for rel in MIRROR_DIRS:
        mirror_category(src_root, tgt_root, rel, plan, args.apply, args.force, snapshot)
    for rel in MIRROR_TOP_FILES:
        mirror_file(src_root / rel, tgt_root / rel, rel, tgt_root, plan, args.apply, args.force, snapshot)
    merge_settings(src_root, tgt_root, plan, args.apply, args.force, snapshot)
    merge_gitignore(tgt_root, plan, args.apply, args.force, snapshot)
    if snapshot is not None and snapshot.snapshot_dir is not None:
        plan.rollback_snapshot = str(snapshot.snapshot_dir)
    report(plan, args.apply)
    return 0


if __name__ == "__main__":
    sys.exit(main())

 succeeded in 170ms:
"""Tests for sync-template-to-target.py conflict guard and rollback."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("sync-template-to-target.py")
SPEC = importlib.util.spec_from_file_location("sync_template_to_target", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Cannot load {SCRIPT_PATH}")
sync = importlib.util.module_from_spec(SPEC)
sys.modules["sync_template_to_target"] = sync
SPEC.loader.exec_module(sync)

REL_FILE = ".claude/scripts/example.py"
TOP_DUAL_CI = ".github/workflows/dual-implement-ci.yml"
TOP_CHANGELOG = "CHANGELOG.md"
TOP_MYPY = "mypy.ini"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    return proc


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_sync_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    src = tmp_path / "src"
    tgt = tmp_path / "tgt"
    _write(src / REL_FILE, "template\n")
    _write(tgt / REL_FILE, "target\n")
    _git(tgt, "init", "-q")
    _git(tgt, "config", "user.email", "test@example.invalid")
    _git(tgt, "config", "user.name", "Test User")
    _git(tgt, "add", REL_FILE)
    _git(tgt, "commit", "-q", "-m", "initial")
    return src, tgt, tgt / REL_FILE


def _commit_target_files(tgt: Path, *rel_files: str) -> None:
    _git(tgt, "init", "-q")
    _git(tgt, "config", "user.email", "test@example.invalid")
    _git(tgt, "config", "user.name", "Test User")
    _git(tgt, "add", *rel_files)
    _git(tgt, "commit", "-q", "-m", "initial")


def _run_template_sync(src: Path, tgt: Path, force: bool = False) -> int:
    old_argv = sys.argv
    sys.argv = [
        "sync-template-to-target.py",
        "--src",
        str(src),
        "--tgt",
        str(tgt),
        "--apply",
    ]
    if force:
        sys.argv.append("--force")
    try:
        return sync.main()
    finally:
        sys.argv = old_argv


def _apply_scripts_sync(src: Path, tgt: Path, force: bool) -> tuple[object, object]:
    plan = sync.Plan()
    snapshot = sync.RollbackSnapshot(tgt)
    sync.mirror_category(
        src,
        tgt,
        ".claude/scripts",
        plan,
        apply=True,
        force=force,
        snapshot=snapshot,
    )
    return plan, snapshot


def test_mirror_top_files_constant_lists_three_files() -> None:
    assert sync.MIRROR_TOP_FILES == [TOP_DUAL_CI, TOP_CHANGELOG, TOP_MYPY]


def test_sync_mirrors_top_level_dual_implement_ci_yml(tmp_path: Path) -> None:
    src = tmp_path / "src"
    tgt = tmp_path / "tgt"
    (src / ".claude").mkdir(parents=True)
    _write(src / TOP_DUAL_CI, "template ci\n")
    _write(tgt / TOP_DUAL_CI, "target ci\n")
    _commit_target_files(tgt, TOP_DUAL_CI)

    assert _run_template_sync(src, tgt) == 0

    assert (tgt / TOP_DUAL_CI).read_text(encoding="utf-8") == "template ci\n"
    snapshots = list((tgt / sync.ROLLBACK_SNAPSHOT_DIR).glob(f"*/{TOP_DUAL_CI}"))
    assert len(snapshots) == 1
    assert snapshots[0].read_text(encoding="utf-8") == "target ci\n"


def test_sync_mirrors_top_level_changelog_and_mypy_ini(tmp_path: Path) -> None:
    src = tmp_path / "src"
    tgt = tmp_path / "tgt"
    (src / ".claude").mkdir(parents=True)
    _write(src / TOP_CHANGELOG, "template changelog\n")
    _write(src / TOP_MYPY, "[mypy]\ntemplate = true\n")
    _write(tgt / TOP_CHANGELOG, "target changelog\n")
    _write(tgt / TOP_MYPY, "[mypy]\ntarget = true\n")
    _commit_target_files(tgt, TOP_CHANGELOG, TOP_MYPY)

    assert _run_template_sync(src, tgt) == 0

    assert (tgt / TOP_CHANGELOG).read_text(encoding="utf-8") == "template changelog\n"
    assert (tgt / TOP_MYPY).read_text(encoding="utf-8") == "[mypy]\ntemplate = true\n"


def test_top_files_skipped_when_locally_modified_without_force(tmp_path: Path) -> None:
    src = tmp_path / "src"
    tgt = tmp_path / "tgt"
    (src / ".claude").mkdir(parents=True)
    _write(src / TOP_CHANGELOG, "template changelog\n")
    _write(tgt / TOP_CHANGELOG, "target changelog\n")
    _commit_target_files(tgt, TOP_CHANGELOG)
    (tgt / TOP_CHANGELOG).write_text("local changelog\n", encoding="utf-8")

    assert _run_template_sync(src, tgt) == 0

    assert (tgt / TOP_CHANGELOG).read_text(encoding="utf-8") == "local changelog\n"
    assert not (tgt / sync.ROLLBACK_SNAPSHOT_DIR).exists()


def test_sync_skips_locally_modified_without_force(tmp_path: Path) -> None:
    src, tgt, target_file = _make_sync_fixture(tmp_path)
    target_file.write_text("local change\n", encoding="utf-8")

    plan, snapshot = _apply_scripts_sync(src, tgt, force=False)

    assert target_file.read_text(encoding="utf-8") == "local change\n"
    assert (REL_FILE, sync.LOCAL_MODIFIED_SKIP_REASON) in plan.skipped_files
    assert plan.changed_files == []
    assert snapshot.snapshot_dir is None


def test_sync_overwrites_locally_modified_with_force(tmp_path: Path) -> None:
    src, tgt, target_file = _make_sync_fixture(tmp_path)
    target_file.write_text("local change\n", encoding="utf-8")

    plan, snapshot = _apply_scripts_sync(src, tgt, force=True)

    assert target_file.read_text(encoding="utf-8") == "template\n"
    assert plan.skipped_files == []
    assert len(plan.changed_files) == 1
    assert snapshot.snapshot_dir is not None
    assert (snapshot.snapshot_dir / REL_FILE).read_text(encoding="utf-8") == "local change\n"


def test_sync_normal_overwrite_when_target_clean(tmp_path: Path) -> None:
    src, tgt, target_file = _make_sync_fixture(tmp_path)

    plan, snapshot = _apply_scripts_sync(src, tgt, force=False)

    assert target_file.read_text(encoding="utf-8") == "template\n"
    assert plan.skipped_files == []
    assert len(plan.changed_files) == 1
    assert snapshot.snapshot_dir is not None


def test_sync_creates_rollback_snapshot(tmp_path: Path) -> None:
    src, tgt, _target_file = _make_sync_fixture(tmp_path)

    _plan, snapshot = _apply_scripts_sync(src, tgt, force=False)

    assert snapshot.snapshot_dir is not None
    snapshot_file = snapshot.snapshot_dir / REL_FILE
    assert snapshot_file.is_file()
    assert snapshot_file.read_text(encoding="utf-8") == "target\n"


def test_rollback_restores_pre_sync_state(tmp_path: Path) -> None:
    src, tgt, target_file = _make_sync_fixture(tmp_path)
    _plan, snapshot = _apply_scripts_sync(src, tgt, force=False)
    assert target_file.read_text(encoding="utf-8") == "template\n"

    restored_from = sync.rollback_latest_snapshot(tgt)

    assert restored_from == snapshot.snapshot_dir
    assert target_file.read_text(encoding="utf-8") == "target\n"

codex
The requested constant and mirror loop are already in the script, and the four named tests are already present in the allowed test file. I’ll run the required suites now to confirm the worktree satisfies the immutable spec as-is.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/scripts/test_sync_template_to_target.py -v --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z33\codex\task-Z33-full-parity-sync
 succeeded in 1664ms:
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.2, pluggy-1.6.0 -- C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z33\codex\task-Z33-full-parity-sync
plugins: anyio-4.12.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 9 items

.claude/scripts/test_sync_template_to_target.py::test_mirror_top_files_constant_lists_three_files PASSED [ 11%]
.claude/scripts/test_sync_template_to_target.py::test_sync_mirrors_top_level_dual_implement_ci_yml PASSED [ 22%]
.claude/scripts/test_sync_template_to_target.py::test_sync_mirrors_top_level_changelog_and_mypy_ini PASSED [ 33%]
.claude/scripts/test_sync_template_to_target.py::test_top_files_skipped_when_locally_modified_without_force PASSED [ 44%]
.claude/scripts/test_sync_template_to_target.py::test_sync_skips_locally_modified_without_force PASSED [ 55%]
.claude/scripts/test_sync_template_to_target.py::test_sync_overwrites_locally_modified_with_force PASSED [ 66%]
.claude/scripts/test_sync_template_to_target.py::test_sync_normal_overwrite_when_target_clean PASSED [ 77%]
.claude/scripts/test_sync_template_to_target.py::test_sync_creates_rollback_snapshot PASSED [ 88%]
.claude/scripts/test_sync_template_to_target.py::test_rollback_restores_pre_sync_state PASSED [100%]

============================== 9 passed in 1.14s ==============================

codex
The sync-template test file passed all 9 tests, including the four Z33 cases. Next I’m running the live attack matrix exactly as specified.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/hooks/test_enforcer_live_attacks.py -q --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z33\codex\task-Z33-full-parity-sync
 succeeded in 1974ms:
.........................                                                [100%]
25 passed in 1.52s

codex
The attack matrix is green at 25/25. I’m starting the broader Codex/delegation regression suite now; this is the longest required pytest command.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/scripts/test_spawn_agent.py .claude/scripts/test_determinism_chaos.py .claude/scripts/test_archive_active_context.py .claude/scripts/test_generate_changelog.py .claude/scripts/test_verify_codex_auth.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z33\codex\task-Z33-full-parity-sync
 succeeded in 7479ms:
........................................................................ [ 24%]
........................................................................ [ 48%]
........................................................................ [ 73%]
........................................................................ [ 97%]
.......                                                                  [100%]
============================== warnings summary ===============================
.claude\scripts\judge_axes.py:46
  C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z33\codex\task-Z33-full-parity-sync\.claude\scripts\judge_axes.py:46: PytestCollectionWarning: cannot collect test class 'TestRun' because it has a __init__ constructor (from: .claude/scripts/test_judge.py)
    @dataclass

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
295 passed, 1 warning in 6.98s

codex
The broader regression suite passed: 295 tests, with one existing pytest collection warning from `judge_axes.py`. I’m running the dual teams selftest last.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python .claude/scripts/dual-teams-selftest.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z33\codex\task-Z33-full-parity-sync
 succeeded in 730ms:
[PASS] preflight-clean-with-sentinel-V1                     (61 ms)
[PASS] preflight-clean-with-sentinel-V2                     (57 ms)
[PASS] is_dual_teams_worktree-true-on-V1                    ( 1 ms)
[PASS] is_dual_teams_worktree-true-on-V2                    ( 1 ms)
[PASS] judge-axes-sees-claude-committed-py                  (29 ms)
[PASS] judge-axes-sees-codex-untracked-py                   (48 ms)
selftest: 6 checks, 6 passed, 0 failed (558 ms)
{"json_output": false, "keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: main", "ts": "2026-04-26T19:11:30.641747+00:00"}
{"keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: run_selftest", "ts": "2026-04-26T19:11:30.641747+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: setup_transient_repo", "tmpdir": "C:\\Users\\Lenovo\\AppData\\Local\\Temp\\dual-teams-selftest-sfd6o7yu", "ts": "2026-04-26T19:11:30.644102+00:00"}
{"base_sha": "9966d666cb401de97dc4ec56ec4c21b6f5c30c08", "duration_ms": 258, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: setup_transient_repo", "ts": "2026-04-26T19:11:30.901885+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: load_integrations", "project_root": "C:\\Bots\\Migrator bots\\claude-project-template-update\\worktrees\\criterion-upgrade-z33\\codex\\task-Z33-full-parity-sync", "ts": "2026-04-26T19:11:30.901885+00:00"}
{"duration_ms": 5, "failures": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: load_integrations", "ts": "2026-04-26T19:11:30.906888+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: build_results", "ts": "2026-04-26T19:11:30.906888+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T19:11:30.906888+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "detail": "git status --porcelain empty", "duration_ms": 61, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T19:11:30.968081+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T19:11:30.968081+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "detail": "git status --porcelain empty", "duration_ms": 57, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T19:11:31.024890+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T19:11:31.024890+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T19:11:31.024890+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T19:11:31.024890+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T19:11:31.025897+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T19:11:31.088563+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "detail": "saw claude_probe.py", "duration_ms": 29, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T19:11:31.117567+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T19:11:31.117567+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "detail": "saw codex_probe.py", "duration_ms": 48, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T19:11:31.166483+00:00"}
{"checks": 6, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: build_results", "ts": "2026-04-26T19:11:31.166483+00:00"}
{"checks": 6, "duration_ms": 558, "failed": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: run_selftest", "passed": 6, "ts": "2026-04-26T19:11:31.199516+00:00"}
{"exit_code": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: main", "ts": "2026-04-26T19:11:31.199516+00:00"}

codex
The required selftest passed 6/6. I’m also running the AC-5 `-q` variant of the sync test command because the acceptance criteria list it separately from the verbose test command.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/scripts/test_sync_template_to_target.py -q --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z33\codex\task-Z33-full-parity-sync
 succeeded in 1626ms:
.........                                                                [100%]
9 passed in 1.12s

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z33\codex\task-Z33-full-parity-sync
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git rev-parse HEAD' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z33\codex\task-Z33-full-parity-sync
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff --stat' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z33\codex\task-Z33-full-parity-sync
 succeeded in 128ms:
0b6889eea56f7a2f19ecb67bcd934158c4f5a02e

 succeeded in 132ms:
 succeeded in 138ms:
codex
=== TASK Z33 SELF-REPORT ===
- status: pass
- approach: verified existing scoped implementation mirrors `MIRROR_TOP_FILES` after category sync using `mirror_file`
- new tests: 4
- existing tests pass: yes
- attack matrix 25/25: yes
- selftest 6/6: PASS
- net lines: 0
- files modified: []
- conflict guard works for top files: yes
- NOTE: Worktree already contained the requested script change and four Z33 tests; no edits were needed.
- NOTE: `python -m pytest .claude/scripts/test_sync_template_to_target.py -v --tb=line` -> 9 passed
- NOTE: `python -m pytest .claude/hooks/test_enforcer_live_attacks.py -q --tb=line` -> 25 passed
- NOTE: Broad Codex/delegation suite -> 295 passed, 1 existing pytest collection warning
- NOTE: `python .claude/scripts/dual-teams-selftest.py` -> 6 passed, 0 failed
- Final commit SHA: 0b6889eea56f7a2f19ecb67bcd934158c4f5a02e
=== END SELF-REPORT ===
2026-04-26T19:12:06.983227Z ERROR codex_core::session: failed to record rollout items: thread 019dcb33-4578-76b2-a243-788b7314b181 not found
tokens used
38 852
```
