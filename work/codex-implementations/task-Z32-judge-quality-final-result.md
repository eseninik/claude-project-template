# Codex Implementation Result — Task Z32-judge-quality-final

- status: pass
- timestamp: 2026-04-26T18:46:44.498379+00:00
- task_file: C:\Bots\Migrator bots\claude-project-template-update\work\criterion-upgrade\task-Z32-judge-quality-final.md
- base_sha: c74ae20e7d87ab47353458cb8a76a62e2f6d3923
- codex_returncode: 0
- scope_status: pass
- scope_message: OK: 6 path(s) in fence
- tests_all_passed: True
- test_commands_count: 4

## Diff

```diff
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719..f64816f 100644
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -31,6 +31,8 @@ if sys.platform == "win32":
 BROKER_URL = "ws://127.0.0.1:4500"
 INACTIVITY_TIMEOUT = 30
 MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
 
 logger = logging.getLogger(__name__)
 
@@ -151,13 +153,15 @@ def ask_via_broker(prompt):
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
     """Fallback: ask via codex exec (cold start).
 
     Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
     both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
     """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
     codex = shutil.which("codex")
     if not codex:
         logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
@@ -167,7 +171,7 @@ def ask_via_exec(prompt):
             [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
              "--sandbox", "read-only", "--full-auto", "--ephemeral"],
             capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
+            timeout=timeout,
         )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
@@ -185,11 +189,16 @@ def ask_via_exec(prompt):
 
 
 def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
         sys.exit(1)
 
-    prompt = " ".join(sys.argv[1:])
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -200,7 +209,7 @@ def main():
 
     # Fallback to codex exec
     if not result:
-        result = ask_via_exec(prompt)
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3..946aa74 100644
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@ def build_arg_parser() -> argparse.ArgumentParser:
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc..519d269 100644
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -213,7 +213,9 @@ def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
 
 
 _FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,8 +389,17 @@ def score_type_check(worktree: Path, weight: int = 2, base: str = "HEAD",
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
         if not has_config:
             return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165..63ac9a7 100644
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -119,6 +119,22 @@ class TestAskViaExecIntegration:
                                                        stderr="[ts] header\n")):
             assert codex_ask.ask_via_exec("ping say OK") == "OK"
 
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
     def test_ask_via_exec_v117_returns_response(self):
         v117_stdout = (
             "[ts] header\n"
@@ -147,7 +163,7 @@ class TestAskViaExecIntegration:
     def test_ask_via_exec_timeout_returns_none(self):
         with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
              mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
             assert codex_ask.ask_via_exec("anything") is None
 
 
@@ -187,7 +203,8 @@ class TestMainFlowUnchanged:
         monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
         monkeypatch.setattr(codex_ask, "ask_via_broker",
                             lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
         monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd..b9e7ec9 100644
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -182,6 +182,18 @@ class TestLoggingCoverage(unittest.TestCase):
         self.assertAlmostEqual(res.score, 1.0)
         self.assertEqual(res.raw["covered"], 1)
 
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
     def test_function_without_logger(self) -> None:
         diff = textwrap.dedent("""\
             diff --git a/x.py b/x.py
@@ -261,6 +273,24 @@ class TestOptionalToolSkip(unittest.TestCase):
             self.assertTrue(res.skipped)
             self.assertIn("mypy", res.skip_reason or "")
 
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
+
 
 # ------------------------ weighted aggregate + winner ------------------------ #
 
@@ -363,6 +393,14 @@ class TestCLI(unittest.TestCase):
         self.assertIn("--base", proc.stdout)
         self.assertIn("auto", proc.stdout)
 
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
     def test_malformed_task_exit_1(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             missing = Path(td) / "nope.md"
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000..34f1230
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False
```

## Test Output

### `python -m pytest .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py -v --tb=line`

- returncode: 0  - passed: True  - timed_out: False

```
--- stdout ---
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.2, pluggy-1.6.0 -- C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
plugins: anyio-4.12.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 64 items

.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_simple_ok PASSED [  1%]
.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_with_tokens_trailer PASSED [  3%]
.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_multiline_response PASSED [  4%]
.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_empty_returns_none PASSED [  6%]
.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_only_whitespace_returns_none PASSED [  7%]
.claude/scripts/test_codex_ask.py::TestParseV117Legacy::test_parse_v117_legacy_with_sentinel PASSED [  9%]
.claude/scripts/test_codex_ask.py::TestParseV117Legacy::test_parse_v117_with_repeated_response PASSED [ 10%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_v125_returns_response PASSED [ 12%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_default_timeout_180 PASSED [ 14%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_strategic_timeout_900 PASSED [ 15%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_v117_returns_response PASSED [ 17%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_returncode_nonzero_returns_none PASSED [ 18%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_codex_not_in_path_returns_none PASSED [ 20%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_timeout_returns_none PASSED [ 21%]
.claude/scripts/test_codex_ask.py::TestRefactorContract::test_parse_function_exists PASSED [ 23%]
.claude/scripts/test_codex_ask.py::TestRefactorContract::test_parse_function_has_docstring_mentioning_both_versions PASSED [ 25%]
.claude/scripts/test_codex_ask.py::TestRefactorContract::test_ask_via_exec_delegates_to_parser PASSED [ 26%]
.claude/scripts/test_codex_ask.py::TestMainFlowUnchanged::test_main_flow_unchanged PASSED [ 28%]
.claude/scripts/test_judge.py::TestTestsPassed::test_all_pass PASSED     [ 29%]
.claude/scripts/test_judge.py::TestTestsPassed::test_empty_skipped PASSED [ 31%]
.claude/scripts/test_judge.py::TestTestsPassed::test_none_pass PASSED    [ 32%]
.claude/scripts/test_judge.py::TestTestsPassed::test_some_pass PASSED    [ 34%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_at_scale_scores_half PASSED [ 35%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_far_above_scale_still_nonzero PASSED [ 37%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_huge_diff_asymptotic PASSED [ 39%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_zero_added_scores_one PASSED [ 40%]
.claude/scripts/test_judge.py::TestDiffSize::test_empty_diff_max_score PASSED [ 42%]
.claude/scripts/test_judge.py::TestDiffSize::test_inverse_normalization PASSED [ 43%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_edge_no_new_functions PASSED [ 45%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_function_with_logger PASSED [ 46%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_function_without_logger PASSED [ 48%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_logging_coverage_counts_delegated_log_calls PASSED [ 50%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_mixed_functions PASSED [ 51%]
.claude/scripts/test_judge.py::TestLintClean::test_clean_file PASSED     [ 53%]
.claude/scripts/test_judge.py::TestLintClean::test_no_files_skipped PASSED [ 54%]
.claude/scripts/test_judge.py::TestLintClean::test_syntax_error PASSED   [ 56%]
.claude/scripts/test_judge.py::TestOptionalToolSkip::test_complexity_skipped_when_radon_absent PASSED [ 57%]
.claude/scripts/test_judge.py::TestOptionalToolSkip::test_score_type_check_active_when_mypy_ini_present PASSED [ 59%]
.claude/scripts/test_judge.py::TestOptionalToolSkip::test_type_check_skipped_when_mypy_absent PASSED [ 60%]
.claude/scripts/test_judge.py::TestWeightedAggregate::test_all_skipped_zero PASSED [ 62%]
.claude/scripts/test_judge.py::TestWeightedAggregate::test_skipped_ignored PASSED [ 64%]
.claude/scripts/test_judge.py::TestWeightedAggregate::test_weighted_correctness PASSED [ 65%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_claude_wins PASSED [ 67%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_codex_wins PASSED [ 68%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_tie_custom_delta PASSED [ 70%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_tie_within_delta PASSED [ 71%]
.claude/scripts/test_judge.py::TestVerdictSchema::test_rationale_cites_biggest_delta PASSED [ 73%]
.claude/scripts/test_judge.py::TestVerdictSchema::test_verdict_is_valid_json PASSED [ 75%]
.claude/scripts/test_judge.py::TestCLI::test_dry_run PASSED              [ 76%]
.claude/scripts/test_judge.py::TestCLI::test_help_exits_zero PASSED      [ 78%]
.claude/scripts/test_judge.py::TestCLI::test_help_mentions_auto_base PASSED [ 79%]
.claude/scripts/test_judge.py::TestCLI::test_malformed_task_exit_1 PASSED [ 81%]
.claude/scripts/test_judge.py::TestCLI::test_tie_threshold_default_is_0_03 PASSED [ 82%]
.claude/scripts/test_judge.py::TestStructuredLogging::test_json_formatter_shape PASSED [ 84%]
.claude/scripts/test_judge.py::TestEnsureUntrackedVisible::test_idempotent_no_untracked PASSED [ 85%]
.claude/scripts/test_judge.py::TestEnsureUntrackedVisible::test_never_raises_on_missing_git PASSED [ 87%]
.claude/scripts/test_judge.py::TestEnsureUntrackedVisible::test_registers_untracked_py PASSED [ 89%]
.claude/scripts/test_judge.py::TestDiffBaselineCommitted::test_committed_diff_visible_with_merge_base PASSED [ 90%]
.claude/scripts/test_judge.py::TestDiffBaselineUntracked::test_untracked_numstat_after_ensure PASSED [ 92%]
.claude/scripts/test_judge.py::TestResolveBase::test_cli_explicit_wins_over_sidecar PASSED [ 93%]
.claude/scripts/test_judge.py::TestResolveBase::test_head_fallback_in_non_git PASSED [ 95%]
.claude/scripts/test_judge.py::TestResolveBase::test_head_literal_passes_through_to_fallback PASSED [ 96%]
.claude/scripts/test_judge.py::TestResolveBase::test_merge_base_when_no_sidecar_and_auto PASSED [ 98%]
.claude/scripts/test_judge.py::TestResolveBase::test_sidecar_wins_over_auto_fallback PASSED [100%]

============================== warnings summary ===============================
.claude\scripts\judge_axes.py:46
  C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final\.claude\scripts\judge_axes.py:46: PytestCollectionWarning: cannot collect test class 'TestRun' because it has a __init__ constructor (from: .claude/scripts/test_judge.py)
    @dataclass

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 64 passed, 1 warning in 2.42s ========================
```

### `python -c "import configparser; c=configparser.ConfigParser(); c.read('mypy.ini'); assert 'mypy' in c"`

- returncode: 0  - passed: True  - timed_out: False

```
```

### `python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_spawn_agent.py .claude/scripts/test_determinism_chaos.py .claude/scripts/test_archive_active_context.py .claude/scripts/test_generate_changelog.py .claude/scripts/test_sync_template_to_target.py .claude/scripts/test_verify_codex_auth.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line`

- returncode: 0  - passed: True  - timed_out: False

```
--- stdout ---
........................................................................ [ 28%]
........................................................................ [ 56%]
........................................................................ [ 84%]
........................................                                 [100%]
256 passed in 7.11s
```

### `python .claude/scripts/dual-teams-selftest.py`

- returncode: 0  - passed: True  - timed_out: False

```
--- stdout ---
[PASS] preflight-clean-with-sentinel-V1                     (61 ms)
[PASS] preflight-clean-with-sentinel-V2                     (60 ms)
[PASS] is_dual_teams_worktree-true-on-V1                    ( 1 ms)
[PASS] is_dual_teams_worktree-true-on-V2                    ( 1 ms)
[PASS] judge-axes-sees-claude-committed-py                  (28 ms)
[PASS] judge-axes-sees-codex-untracked-py                   (46 ms)
selftest: 6 checks, 6 passed, 0 failed (613 ms)
--- stderr ---
{"json_output": false, "keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: main", "ts": "2026-04-26T18:57:04.564137+00:00"}
{"keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: run_selftest", "ts": "2026-04-26T18:57:04.564137+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: setup_transient_repo", "tmpdir": "C:\\Users\\Lenovo\\AppData\\Local\\Temp\\dual-teams-selftest-6adzq8ir", "ts": "2026-04-26T18:57:04.565146+00:00"}
{"base_sha": "d17eafa40ebd97d1233e9d978ac857f2bafdaf9d", "duration_ms": 311, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: setup_transient_repo", "ts": "2026-04-26T18:57:04.876844+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: load_integrations", "project_root": "C:\\Bots\\Migrator bots\\claude-project-template-update\\worktrees\\criterion-upgrade-z32\\codex\\task-Z32-judge-quality-final", "ts": "2026-04-26T18:57:04.876844+00:00"}
{"duration_ms": 5, "failures": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: load_integrations", "ts": "2026-04-26T18:57:04.881843+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: build_results", "ts": "2026-04-26T18:57:04.881843+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T18:57:04.881843+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "detail": "git status --porcelain empty", "duration_ms": 61, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T18:57:04.943035+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T18:57:04.943035+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "detail": "git status --porcelain empty", "duration_ms": 60, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T18:57:05.002859+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T18:57:05.003843+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T18:57:05.003843+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T18:57:05.003843+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T18:57:05.003843+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T18:57:05.069492+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "detail": "saw claude_probe.py", "duration_ms": 28, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T18:57:05.097558+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T18:57:05.097558+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "detail": "saw codex_probe.py", "duration_ms": 46, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T18:57:05.143214+00:00"}
{"checks": 6, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: build_results", "ts": "2026-04-26T18:57:05.143214+00:00"}
{"checks": 6, "duration_ms": 613, "failed": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: run_selftest", "passed": 6, "ts": "2026-04-26T18:57:05.176234+00:00"}
{"exit_code": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: main", "ts": "2026-04-26T18:57:05.176234+00:00"}
```

## Self-Report (Codex NOTE/BLOCKER lines)

- NOTE: Focused suite stdout: `64 passed, 1 warning in 2.32s`.
- NOTE: Listed regression stdout: `256 passed in 7.63s`; full AC-5 combined suite stdout: `320 passed, 1 warning in 9.23s`.
- NOTE: Selftest stdout: `selftest: 6 checks, 6 passed, 0 failed`; attack matrix stdout: `25 passed in 1.48s`.
- NOTE: `mypy.ini` parse command exited 0 with no stdout.

## Codex stderr

```
OpenAI Codex v0.125.0 (research preview)
--------
workdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
model: gpt-5.5
provider: chatgpt
approval: never
sandbox: danger-full-access
reasoning effort: xhigh
reasoning summaries: none
session id: 019dcb1d-8c85-7e92-b8ad-33d17a2bae0d
--------
user
You are the single-task implementer. The task specification below is IMMUTABLE.
Write code to satisfy all Acceptance Criteria. Do NOT modify files listed in
Forbidden Paths or Read-Only Files. After writing code, run every Test Command
listed in the task and report the result in your self-report.
Any AGENTS.md or CLAUDE.md in the worktree is authoritative background context.

---- TASK SPECIFICATION ----

---
task_id: Z32-judge-quality-final
title: Criterion 7 Judge Quality — codex-ask timeout Y27 + mypy.ini for type_check axis + tie threshold tuning + logging_coverage refinement
executor: dual
risk_class: routine
speed_profile: balanced
---

# Task Z32

## Goal

Criterion 7 (Judge Quality) currently 5/10 because:
- 2 of 6 axes always skip (radon now INSTALLED via pip, mypy already INSTALLED but no `mypy.ini` config → still skips)
- `codex-ask.py` has hardcoded 120s timeout → strategic deep consults silently fail (Y27)
- Tie threshold 0.02 may not match observed verdict variance
- `logging_coverage` heuristic (window=5) misses functions delegating to logged helpers

## Four coordinated improvements

### Improvement 1 (Y27) — codex-ask.py timeout extension

In `.claude/scripts/codex-ask.py` `ask_via_exec()`, current `timeout=120`
silently fails for deep analyses (production-readiness review timed out
in our last verification round). Two-mode fix:
- Default `timeout=180` (up from 120 — covers normal advisor consults)
- Add `--strategic` CLI flag → `timeout=900` (15 min, for deep reviews)

Add tests:
- `test_ask_via_exec_default_timeout_180`
- `test_ask_via_exec_strategic_timeout_900`

### Improvement 2 — mypy.ini for type_check axis

NEW file `mypy.ini` at repo root with reasonable defaults:
```ini
[mypy]
python_version = 3.12
ignore_missing_imports = True
warn_unused_ignores = True
strict_optional = False
```

Update `.claude/scripts/judge_axes.py:score_type_check` to look for
`mypy.ini` OR `pyproject.toml` `[tool.mypy]` section and activate the
axis when present.

Add test:
- `test_score_type_check_active_when_mypy_ini_present`

### Improvement 3 — Tie threshold tuning

Observed verdicts in this session:
- Z10: TIE 0.000
- Z11: TIE -0.0099
- Z12: Codex -0.0245
- Z17: Codex -0.1741
- Z23: Codex -0.0277
- Z26: Codex -0.0856
- Z29: Codex -0.0533

Mean |delta| ≈ 0.052, std ≈ 0.057. Current tie threshold 0.02 catches
2 of 7 verdicts as TIE — too tight. Recommend threshold 0.030 (2σ-ish
of the bottom cluster). Configurable via judge.py `--tie-delta` already.

Update default in `judge.py` `--tie-delta` from 0.02 to 0.03 with NOTE
in argparse help: "Threshold tuned from observed dual-implement deltas".

Add test:
- `test_tie_threshold_default_is_0_03` (assert default in argparse)

### Improvement 4 — logging_coverage delegated-call recognition

In `judge_axes.py:score_logging_coverage`, current heuristic counts
functions whose body has `logger.` within `window=5` lines. Functions
that delegate to a helper (e.g. `_log(level, msg)`) are missed.

Refine: also count functions where body contains call to local helpers
matching pattern `_log\(` OR `logger.` within window. Helper names
recognized: `_log`, `log_info`, `log_warn`, `log_error`, `log_debug`.

Add test:
- `test_logging_coverage_counts_delegated_log_calls`

## Scope Fence

```
.claude/scripts/codex-ask.py
.claude/scripts/test_codex_ask.py
.claude/scripts/judge.py
.claude/scripts/judge_axes.py
.claude/scripts/test_judge.py
mypy.ini   (NEW at repo root)
```

DO NOT modify any other file.

## Read-Only Files / Evaluation Firewall

- `work/criterion-upgrade/task-Z32-judge-quality-final.md`
- `.claude/hooks/codex-delegate-enforcer.py`
- `.claude/scripts/codex-implement.py`, `spawn-agent.py`, etc.

## Acceptance Criteria

### AC-1 (Y27): timeout tests pass
- `test_ask_via_exec_default_timeout_180` PASSES
- `test_ask_via_exec_strategic_timeout_900` PASSES

### AC-2: mypy.ini exists + type_check active
- `mypy.ini` at repo root, valid INI parseable
- `test_score_type_check_active_when_mypy_ini_present` PASSES (no longer skipped)

### AC-3: tie threshold default 0.03
- `test_tie_threshold_default_is_0_03` PASSES

### AC-4: logging_coverage counts delegated calls
- `test_logging_coverage_counts_delegated_log_calls` PASSES

### AC-5: Existing 138 tests still pass

```bash
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/scripts/test_spawn_agent.py .claude/scripts/test_determinism_chaos.py .claude/scripts/test_archive_active_context.py .claude/scripts/test_generate_changelog.py .claude/scripts/test_sync_template_to_target.py .claude/scripts/test_verify_codex_auth.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line
```

### AC-6: Selftest + matrix
`python .claude/scripts/dual-teams-selftest.py` 6/6
`pytest .claude/hooks/test_enforcer_live_attacks.py` 25/25

## Test Commands

```bash
# 1. New + existing test_judge / test_codex_ask
python -m pytest .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py -v --tb=line

# 2. mypy.ini parseable
python -c "import configparser; c=configparser.ConfigParser(); c.read('mypy.ini'); assert 'mypy' in c"

# 3. Existing 138 (regression)
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_spawn_agent.py .claude/scripts/test_determinism_chaos.py .claude/scripts/test_archive_active_context.py .claude/scripts/test_generate_changelog.py .claude/scripts/test_sync_template_to_target.py .claude/scripts/test_verify_codex_auth.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line

# 4. Selftest
python .claude/scripts/dual-teams-selftest.py
```

## Implementation hints

- For Y27: locate `subprocess.run(..., timeout=120)` in `ask_via_exec`. Replace with `timeout=180` default, accept `strategic: bool` kwarg → 900s.
- mypy.ini: simple INI format. See implementation hint in task spec body.
- judge_axes.score_type_check: check `Path("mypy.ini").exists() or "[tool.mypy]" in pyproject.toml`. If yes, run `mypy --no-error-summary <files>` capture rc, score = 1.0 if rc==0 else 0.5.
- Tie threshold: simple constant change in argparse. Keep `tie_delta` param signatures.
- logging_coverage: extend regex to recognize `_log\(` AND `logger\.` within window.

## Self-report format

```
=== TASK Z32 SELF-REPORT ===
- status: pass | fail | blocker
- Improvement 1 (Y27 timeout) approach: <1 line>
- Improvement 2 (mypy.ini + type_check) approach: <1 line>
- Improvement 3 (tie threshold) approach: <1 line>
- Improvement 4 (logging delegated) approach: <1 line>
- new tests: <count> (expected 4)
- existing 138 pass: yes / no
- attack matrix 25/25: yes / no
- selftest 6/6: PASS / FAIL
- mypy.ini valid INI: yes / no
- net lines: <approx>
- files modified: [list]
- NOTE: <surprising>
- BLOCKER: <only if>
- Final commit SHA: <SHA>
=== END SELF-REPORT ===
```


---- END TASK SPECIFICATION ----
Return a short self-report at the end of your run using lines starting with
`NOTE:` for observations and `BLOCKER:` for unresolved problems.

codex
I’ll inspect the scoped scripts and tests first, then make only the fenced edits and run the required commands. After changes I’ll report the exact pass/fail evidence in the requested self-report shape.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg --files -g AGENTS.md -g CLAUDE.md -g .claude/scripts/codex-ask.py -g .claude/scripts/test_codex_ask.py -g .claude/scripts/judge.py -g .claude/scripts/judge_axes.py -g .claude/scripts/test_judge.py -g mypy.ini' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 147ms:
AGENTS.md
CLAUDE.md

 succeeded in 231ms:
codex
The worktree is clean. The first file scan only saw top-level docs because hidden `.claude` paths are not listed by default, so I’m reading the scoped files with hidden-file search enabled next.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg --files -uu .claude/scripts .claude/hooks | rg "(codex-ask.py|test_codex_ask.py|judge.py|judge_axes.py|test_judge.py)$"' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Raw -LiteralPath AGENTS.md' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Raw -LiteralPath CLAUDE.md' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 142ms:
# AGENTS.md вЂ” Shared Agent Context

> Auto-loaded by Codex CLI via `~/.codex/config.toml` `project_doc` fallback
> (`AGENTS.md` takes precedence over `CLAUDE.md`). Keep this file focused:
> shared invariants that every task delegated to Codex should follow, so
> individual `task-N.md` specs don't have to re-inline them on every run.
>
> Claude Code reads `CLAUDE.md`, not this file. Project-wide rules specific
> to Claude's behavior (hook wiring, Agent Teams policy, memory protocol)
> stay in `CLAUDE.md`. Only put things here that apply when **any** agent вЂ”
> Codex, Copilot, Gemini CLI вЂ” writes code in this repo.

## Repo shape (one-liner)

`claude-project-template-update` is the **source template** for all AI-First
bot projects. Edits to `.claude/` here propagate downstream via fleet-sync
to real bot projects. The code you touch here shapes many downstream
codebases. Think twice before refactoring widely.

## You are one of two parallel tracks (Always-Dual protocol)

This project runs under the **Always-Dual Code Delegation Protocol**
(see `CLAUDE.md` в†’ "Code Delegation Protocol"). Every code-writing
task is implemented on **two parallel tracks**:

- **Claude teammate** вЂ” one fresh Claude Code subagent, in a dedicated
  git worktree, implements the same task spec you received.
- **You (Codex)** вЂ” in your own worktree, implement the same spec.

Both diffs finish; then Opus (the orchestrator) judges on **merit**
(objective test scores via `.claude/scripts/judge.py`, plus subjective
tie-break) and picks a winner per subtask. The loser's diff is archived
under `work/<feature>/dual-history/`; only the winner merges into main.

**What this means for your output:**

- Don't assume your diff will be taken as-is. Write it to win on merit:
  correctness, style-consistency, minimal diff, full logging coverage,
  AC-grounded tests.
- Convergent design is a positive signal вЂ” if you and the Claude
  teammate independently arrive at the same architecture, the spec was
  well-formed. Divergence is where Opus's judge focuses.
- You do NOT coordinate with the Claude teammate. Work from the spec
  alone. The two of you are intentionally independent so the judge step
  actually has two opinions to weigh.
- `task-N.md` Acceptance Criteria are **IMMUTABLE**. Changing tests or
  ACs to make your implementation pass is disqualifying (Evaluation
  Firewall).
- When you fail, be explicit: use `BLOCKER:` self-report lines. A clean
  "I can't do this because Y" beats a plausible-looking wrong diff.

## Universal skill contracts (apply to ALL code changes)

These are the extracts that every task-N.md used to repeat. Now they live
here once and are implicit for every Codex invocation.

### Verification (before claiming done)

- Run every Test Command listed in your task file. Quote the stdout in
  your self-report (`NOTE: ...` lines).
- Verify each Acceptance Criterion with concrete evidence вЂ” a passing
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
  work. Platform-portable paths matter вЂ” this repo runs on Windows.
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
  `No installed Python found!`, that is the reason вЂ” it is NOT a
  Python installation problem.
- Paths with spaces: this repo lives under `C:\Bots\Migrator bots\...`.
  Quote paths in subprocess calls. Prefer forward slashes for git вЂ”
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
  file Y even if that seems necessary вЂ” report `BLOCKER` instead.

## Speed profile (optional guidance)

If the task frontmatter carries `speed_profile`, treat it as guidance
about how much thoroughness is expected:

- `fast` вЂ” routine, well-specified, tight deadline. Do the simplest
  correct thing. Fewer helper functions, less docstring prose. Skip
  speculative hardening.
- `balanced` (default) вЂ” normal coding standards apply; structured logs,
  helpful docstrings, safe defaults.
- `thorough` вЂ” high-stakes or novel problem. Add explicit edge-case
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
the full-project context to unblock you вЂ” you just need to ask.

## References for deeper context

- `.claude/adr/adr-012-codex-primary-implementer.md` вЂ” architectural
  decision record: why Opus plans + Codex implements.
- `work/codex-primary/tech-spec.md` вЂ” full tech-spec for the
  codex-primary pipeline (section 4 = task-N.md format).
- `.claude/shared/work-templates/phases/IMPLEMENT-CODEX.md`,
  `IMPLEMENT-HYBRID.md`, `DUAL-IMPLEMENT.md` вЂ” phase-mode docs.
- `work/codex-primary/dual-1-postmortem.md` +
  `dual-2-judgment.md` вЂ” real-run learnings (what breaks in practice).


 succeeded in 167ms:
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
The sync script reads `settings.json`, finds every `.claude/hooks/` dir under `work/`, `deploy/`, `staging/` and ensures each has an up-to-date canonical stub for every hook. Safe idempotent вЂ” run any time. Canonical stub: `.claude/scripts/bridge-stub-template.py` (filename-derived, uses `subprocess.run` for Windows path-with-spaces safety).

## Codex Primary Implementer (Experimental, Local)

**SCOPE вЂ” READ FIRST.** This section is **LOCAL to this project only**. It is **NOT propagated** to other bot projects or to `.claude/shared/templates/new-project/CLAUDE.md` until the PoC validates. Do not copy this section elsewhere; do not sync via template scripts until promotion is explicitly approved. The default phase modes remain `AGENT_TEAMS`, `AO_HYBRID`, and `AO_FLEET` as documented in global `~/.claude/CLAUDE.md`. The modes below are **specialized, opt-in tools**, not replacements.

### What it is
Opus plans, decomposes, and reviews; **Codex (GPT-5.5) executes** well-defined, scope-fenced implementation tasks. The pattern keeps Opus as the judge/architect and lets a second model do logic-heavy, well-specified work where a fresh perspective or higher throughput helps.

### New phase modes (choose per task вЂ” not always-on)

- **`CODEX_IMPLEMENT`** вЂ” every implementation task in the phase is delegated to Codex. Use when tasks are logic-heavy, well-specified, and unambiguous (algorithms, protocol code, data transforms) and where an independent executor reduces confirmation-bias risk. Avoid for tasks requiring deep repo conventions or heavy cross-file refactors.
- **`HYBRID_TEAMS`** вЂ” per-task `executor:` dispatch (`claude` | `codex` | `dual`). Most flexible mode. Use when a wave mixes task shapes: some tasks suit Claude (conventions, wide context), others suit Codex (self-contained logic), and a few warrant both (high-stakes).
- **`DUAL_IMPLEMENT`** вЂ” high-stakes code: Claude and Codex implement the task **in parallel**, Opus acts as judge and picks or merges. Use for auth, crypto, payments, migrations, or any change where two independent attempts catch more bugs than one. Expect ~2Г— token cost вЂ” reserve for genuinely risky diffs.

### Pointers (canonical docs вЂ” do not duplicate here)
- Tech-spec: `work/codex-primary/tech-spec.md`
- ADR: `.claude/adr/adr-012-codex-primary-implementer.md`
- Phase-mode docs: `.claude/shared/work-templates/phases/IMPLEMENT-CODEX.md`, `.claude/shared/work-templates/phases/IMPLEMENT-HYBRID.md`, `.claude/shared/work-templates/phases/DUAL-IMPLEMENT.md`
- Scripts: `.claude/scripts/codex-implement.py`, `.claude/scripts/codex-wave.py`, `.claude/scripts/codex-scope-check.py`
- Skill: `.claude/skills/dual-implement/SKILL.md`

### Compatibility (unchanged вЂ” fully supported)
Agent Teams (TeamCreate), skills injection, memory (activeContext / knowledge / daily), `codex-ask` second opinion, existing codex-advisor hooks (`codex-parallel`, `codex-watchdog`, `codex-broker`, `codex-review`, `codex-stop-opinion`, `codex-gate`) вЂ” **all unchanged and fully supported**. The new modes compose with existing infrastructure; they do not replace or disable any of it.

---

## Code Delegation Protocol вЂ” Always Dual (MANDATORY, blocking)

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
still free to write вЂ” but only **in parallel with or after** a Codex run
on the same scope. The hand-edit without Codex is what gets blocked.

### The Four Invariants (Z1 вЂ” codified enforcement)

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
   is NOT enough вЂ” multi-stage tasks must run their own Codex per stage.
4. **Skip-token audit + actionable block messages.** Every allow/deny
   decision is appended to `work/codex-implementations/skip-ledger.jsonl`
   for offline audit. DENY error messages include a ready-to-run
   `codex-inline-dual.py --describe ... --scope <path>` command for the
   blocked path so the recovery is obvious.


### Task size в†’ execution mode

| Task scope | Mode | How it runs |
|------------|------|-------------|
| 1-2 files, small diff (feature flag, typo, local bug) | **`codex-inline` + Claude hand-edit** | Claude writes own version, `codex-inline.py --describe "вЂ¦"` produces Codex version in parallel, Claude picks winner |
| One focused task, non-trivial | **`dual-implement` skill (Level 3)** | Two git worktrees; Claude teammate in A, `codex-implement.py` in B; Opus judges |
| Big feature / refactor / N subtasks | **`DUAL_TEAMS` mode** (below) | N Claude teammates via `TeamCreate` **AND** N Codex sessions via `codex-wave.py`, both consuming the same `tasks/T*.md` specs in parallel; Opus judges N pairs |

### DUAL_TEAMS mode (Agent Teams + codex-wave running as twins)

For big work (`IMPLEMENT` phase with 3+ independent subtasks), instead of
either `AGENT_TEAMS` alone or `CODEX_IMPLEMENT` alone, Claude runs **both
in parallel** against the same task specs:

1. Claude (planner) writes `tasks/T1.md вЂ¦ TN.md` with Scope Fence + tests
   + Skill Contracts, as usual.
2. Claude spawns N Claude teammates via `TeamCreate` + `spawn-agent.py`
   (existing Agent Teams flow). Each lives in its own git worktree or
   agreed file scope, produces a diff + handoff.
3. **In parallel**, Claude runs `codex-wave.py --tasks T1.md,...,TN.md
   --parallel N`. Each Codex session lives in its own worktree, consumes
   its assigned `T{i}.md`, produces its own `task-T{i}-result.md`.
4. All 2N agents finish in wall-time в‰€ `max(task_i)`.
5. Claude (as judge, using `cross-model-review` skill) compares each
   Claude-diff vs Codex-diff pair against the `T{i}.md` spec, picks the
   winner or cherry-picks hybrid. Repeats for all N subtasks.
6. Winners merged, losers archived under `work/codex-primary/dual-history/`
   for reference.

When to use:
- Any `IMPLEMENT` phase with 3+ independent subtasks вЂ” default to this
- Any high-stakes subtask within any phase вЂ” always include it in dual

When not to use:
- Pure documentation / spec writing вЂ” Claude solo
- Research / exploration / reading вЂ” no code, no Codex
- Truly trivial (< ~5 lines, single location, obvious) вЂ” inline-dual is
  still expected; only skip if the enforcer explicitly allows (see below)

### Code file extensions (delegated / enforced)

`.py .pyi .js .jsx .mjs .cjs .ts .tsx .sh .bash .zsh .go .rs .rb .java
.kt .swift .c .cpp .cc .h .hpp .cs .php .sql .lua .r`

### Exempt paths (Claude may edit freely вЂ” no Codex counterpart required)

- Any file whose extension is NOT in the list above
- `.claude/memory/**` вЂ” session memory (activeContext, knowledge, daily logs)
- `work/**` вЂ” planning artifacts (task specs, post-mortems, judgments, PIPELINE.md) (non-code only вЂ” `.py` under `work/` still requires cover, see Invariant 1)
- `CLAUDE.md`, `AGENTS.md`, `README.md`, `CHANGELOG.md`, `LICENSE`, `.gitignore`
- `.claude/settings.json`, `.claude/ops/*.yaml`, `.mcp.json` вЂ” config
- `.claude/adr/**/*.md` вЂ” architecture decisions
- `.claude/guides/**/*.md`, `.claude/skills/**/*.md` вЂ” documentation

### Workflow summary

1. Claude writes the plan (task-N.md or inline description).
2. Claude starts **both** tracks in parallel:
   - Claude-side implementation (via `TeamCreate`, direct hand-write after
     the Codex run starts, or a second worktree).
   - Codex-side implementation (via `codex-implement.py`, `codex-wave.py`,
     or `codex-inline.py`).
3. Both tracks finish вЂ” Claude reviews both diffs against the spec.
4. Claude picks winner (or merges hybrid), commits, archives loser.

### Enforcement artefact

`.claude/hooks/codex-delegate-enforcer.py` runs on `PreToolUse(Edit|Write|MultiEdit|Bash|NotebookEdit)`:
- If target has a code extension AND is NOT in exempt paths
- в†’ Looks for a recent (< 15 min) `work/codex-implementations/task-*-result.md`
  with `status: pass` whose Scope Fence covers this path
- в†’ Allows the edit when found; blocks with a clear recovery hint otherwise

The hook only guarantees Codex-side participation. The Claude-side half
of the dual pair is Claude's own discipline вЂ” it is expected by this
protocol, and reviewed in handoff blocks.

### Sub-agent file writes (Y14)

Sub-agents spawned via the `Agent` / `Task` tool have `Write` / `Edit` / `MultiEdit`
denied at the harness Permission UI layer (Y14, commit `1c5490b`, 4 escalating tests).
Teammate-spawners must instruct teammates to use **PowerShell `Set-Content` as the canonical
file-write mechanism** (with Bash heredoc + `git apply` as fallback). See
`.claude/guides/teammate-prompt-template.md` В§ "File creation in sub-agent context (Y14 finding)".


2026-04-26T18:47:08.011036Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 0.2 seconds
Output:

 exited 1 in 179ms:
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-ChildItem -Force' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git ls-files .claude/scripts/codex-ask.py .claude/scripts/test_codex_ask.py .claude/scripts/judge.py .claude/scripts/judge_axes.py .claude/scripts/test_judge.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-ChildItem -Force -LiteralPath .claude' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 174ms:


    Каталог: C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-
    quality-final


Mode                 LastWriteTime         Length Name                                                                 
----                 -------------         ------ ----                                                                 
d-----        26.04.2026     21:46                .claude                                                              
d-----        26.04.2026     21:46                .codex                                                               
d-----        26.04.2026     21:46                .github                                                              
d-----        26.04.2026     21:46                docs                                                                 
d-----        26.04.2026     21:46                scripts                                                              
d-----        26.04.2026     21:46                work                                                                 
-a----        26.04.2026     21:46             41 .dual-base-ref                                                       
-a-h--        26.04.2026     21:46            106 .git                                                                 
-a----        26.04.2026     21:46            946 .gitignore                                                           
-a----        26.04.2026     21:46            243 .mcp.json                                                            
-a----        26.04.2026     21:46           8625 AGENTS.md                                                            
-a----        26.04.2026     21:46          14065 CHANGELOG.md                                                         
-a----        26.04.2026     21:46          12134 CLAUDE.md                                                            
-a----        26.04.2026     21:46           3947 README.md                                                            
-a----        26.04.2026     21:46           2265 SSH_CONTABO_CONNECTION.md                                            



 succeeded in 129ms:
.claude/scripts/codex-ask.py
.claude/scripts/judge.py
.claude/scripts/judge_axes.py
.claude/scripts/test_codex_ask.py
.claude/scripts/test_judge.py

 succeeded in 176ms:


    Каталог: C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-
    quality-final\.claude


Mode                 LastWriteTime         Length Name                                                                 
----                 -------------         ------ ----                                                                 
d-----        26.04.2026     21:46                adr                                                                  
d-----        26.04.2026     21:46                agent-memory                                                         
d-----        26.04.2026     21:46                agents                                                               
d-----        26.04.2026     21:46                commands                                                             
d-----        26.04.2026     21:46                guides                                                               
d-----        26.04.2026     21:46                hooks                                                                
d-----        26.04.2026     21:46                knowledge                                                            
d-----        26.04.2026     21:46                memory                                                               
d-----        26.04.2026     21:46                ops                                                                  
d-----        26.04.2026     21:46                prompts                                                              
d-----        26.04.2026     21:46                schemas                                                              
d-----        26.04.2026     21:46                scripts                                                              
d-----        26.04.2026     21:46                shared                                                               
d-----        26.04.2026     21:46                skills                                                               
-a----        26.04.2026     21:46           3792 settings.json                                                        



codex
The local project instructions add the usual dual-track context, but this worktree is already the Codex implementation track. I’m now reading the five scoped Python files to mirror their current style and keep the diff narrow.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Raw -LiteralPath .claude/scripts/codex-ask.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Raw -LiteralPath .claude/scripts/test_codex_ask.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Raw -LiteralPath .claude/scripts/judge.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Raw -LiteralPath .claude/scripts/judge_axes.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 148ms:
#!/usr/bin/env python3
"""Codex Ask - CLI tool for Claude to get Codex opinion on any task.

Usage:
    py -3 .claude/scripts/codex-ask.py "Your question or task description"

Connects to warm Codex broker (ws://127.0.0.1:4500), sends question,
waits for response, prints to stdout. Claude reads the output.

Works everywhere: main session, subtasks, Agent Teams, pipeline phases.
If broker is not running, falls back to codex exec.
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Also update last-consulted for codex-broker sync
BROKER_URL = "ws://127.0.0.1:4500"

if sys.platform == "win32":
    for s in [sys.stdin, sys.stdout, sys.stderr]:
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")

BROKER_URL = "ws://127.0.0.1:4500"
INACTIVITY_TIMEOUT = 30
MAX_TIMEOUT = 300

logger = logging.getLogger(__name__)


def parse_codex_exec_stdout(stdout: str) -> str | None:
    """Parse Codex CLI exec stdout. Handles both:

      - v0.117 (legacy): header lines + sentinel ``codex`` line + response
        + ``tokens used N`` trailer, all in stdout. Extract body between
        the ``codex`` sentinel and the ``tokens used`` trailer.
      - v0.125 (modern): header is sent to stderr, only the response (and
        an optional ``tokens used`` trailer) appears in stdout. No
        sentinel - return everything until the trailer (or all of it if
        no trailer is present).

    Returns the response text, or ``None`` when stdout is empty / blank /
    yields no parseable body.
    """
    logger.info("parse_codex_exec_stdout.enter stdout_len=%d", len(stdout or ""))
    if not stdout or not stdout.strip():
        logger.info("parse_codex_exec_stdout.exit result_truthy=False reason=empty")
        return None
    lines = stdout.splitlines()
    # Try v0.117 sentinel-based extraction first (more specific contract).
    if any(line.strip() == "codex" for line in lines):
        in_resp = False
        out: list[str] = []
        for line in lines:
            if not in_resp:
                if line.strip() == "codex":
                    in_resp = True
                continue
            if "tokens used" in line:
                break
            out.append(line)
        result = "\n".join(out).strip()
        if result:
            logger.info("parse_codex_exec_stdout.exit result_truthy=True format=v0.117")
            return result
    # v0.125 fallback: take everything up to (optional) "tokens used" trailer.
    out2: list[str] = []
    for line in lines:
        if line.strip() == "tokens used":
            break
        out2.append(line)
    result2 = "\n".join(out2).strip()
    truthy = bool(result2)
    logger.info("parse_codex_exec_stdout.exit result_truthy=%s format=v0.125", truthy)
    return result2 or None


def ask_via_broker(prompt):
    """Ask Codex via warm WebSocket broker."""
    from websockets.sync.client import connect

    t0 = time.time()
    ws = connect(BROKER_URL, close_timeout=5, open_timeout=5)

    # Initialize
    ws.send(json.dumps({"id": 1, "method": "initialize", "params": {
        "clientInfo": {"title": "Codex Ask", "name": "codex-ask", "version": "1.0.0"},
        "capabilities": {
            "experimentalApi": False,
            "optOutNotificationMethods": [
                "item/agentMessage/delta",
                "item/reasoning/summaryTextDelta",
                "item/reasoning/summaryPartAdded",
                "item/reasoning/textDelta",
            ],
        },
    }}))
    ws.recv()
    ws.send(json.dumps({"method": "initialized", "params": {}}))

    # Get project dir
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", str(Path.cwd()))

    # Start thread
    ws.send(json.dumps({"id": 2, "method": "thread/start", "params": {
        "cwd": project_dir,
        "ephemeral": True,
        "sandbox": "read-only",
    }}))
    tr = json.loads(ws.recv())
    tid = tr.get("result", {}).get("thread", {}).get("id", "")
    if not tid:
        return None

    # Start turn
    ws.send(json.dumps({"id": 3, "method": "turn/start", "params": {
        "threadId": tid,
        "input": [{"type": "text", "text": prompt, "text_elements": []}],
    }}))

    # Wait for response - as long as Codex is active
    text = ""
    for _ in range(1000):
        if time.time() - t0 > MAX_TIMEOUT:
            break
        try:
            raw = ws.recv(timeout=INACTIVITY_TIMEOUT)
        except Exception:
            break
        msg = json.loads(raw)
        m = msg.get("method", "")
        if m == "turn/completed":
            break
        if m == "error":
            break
        if m == "item/completed":
            item = msg.get("params", {}).get("item", {})
            if item.get("type") == "agentMessage":
                t = item.get("text", "")
                if t:
                    text += t

    ws.close()
    return text.strip() if text.strip() else None


def ask_via_exec(prompt):
    """Fallback: ask via codex exec (cold start).

    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
    """
    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
    codex = shutil.which("codex")
    if not codex:
        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
        return None
    try:
        r = subprocess.run(
            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=120,
        )
        if r.returncode != 0:
            logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                        r.returncode)
            return None
        result = parse_codex_exec_stdout(r.stdout)
        logger.info("ask_via_exec.exit result_truthy=%s reason=ok", bool(result))
        return result
    except subprocess.TimeoutExpired:
        logger.exception("ask_via_exec.exit result_truthy=False reason=timeout")
        return None
    except Exception:
        logger.exception("ask_via_exec.exit result_truthy=False reason=exception")
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])

    # Try broker first (fast, warm)
    result = None
    try:
        result = ask_via_broker(prompt)
    except Exception:
        pass

    # Fallback to codex exec
    if not result:
        result = ask_via_exec(prompt)

    if result:
        print(f"--- Codex gpt-5.5 opinion ---")
        print(result)
        print(f"---")
        # Mark as consulted for codex-gate.py
        _proj = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
        _ts = _proj / ".codex" / "last-consulted"
        _ts.parent.mkdir(parents=True, exist_ok=True)
        _ts.write_text(str(time.time()), encoding="utf-8")
        # Reset edit counter for codex-gate
        _ec = _proj / ".codex" / "edit-count"
        _ec.write_text("0", encoding="utf-8")
    else:
        print("Codex unavailable - proceed without second opinion.", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()


exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Raw -LiteralPath .claude/scripts/test_judge.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 143ms:
#!/usr/bin/env python3
"""Judge вЂ” objective judge for dual-implement runs.

Runs Test Commands in claude & codex worktrees, scores on 6 axes (see
judge_axes.py), emits verdict JSON. Exit 0 valid run, 1 infra failure.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if sys.platform == "win32":
    for _s in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import judge_axes  # noqa: E402
from judge_axes import (  # noqa: E402
    AxisResult, TestRun, biggest_delta_rationale, decide_winner,
    score_complexity, score_diff_size, score_lint_clean,
    score_logging_coverage, score_tests_passed, score_type_check,
    weighted_aggregate,
)

logger = logging.getLogger("judge")
EXIT_OK, EXIT_INFRA = 0, 1

_MAIN_BRANCHES = ("main", "master", "dev")


def _log(level: int, msg: str, **fields: object) -> None:
    logger.log(level, msg, extra={"extra_fields": fields})


def setup_logging() -> None:
    """Init JSON logger on stderr."""
    _log(logging.DEBUG, "entry: setup_logging")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    h = logging.StreamHandler(sys.stderr)
    h.setFormatter(judge_axes.JsonFormatter())
    h.setLevel(logging.INFO)
    logger.addHandler(h)
    _log(logging.DEBUG, "exit: setup_logging")


def _load_task_parser() -> Any:
    """Try reusing codex-implement.parse_task_file via importlib."""
    _log(logging.DEBUG, "entry: _load_task_parser")
    try:
        ci = _THIS_DIR / "codex-implement.py"
        if not ci.exists():
            return None
        spec = importlib.util.spec_from_file_location("codex_implement", ci)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _log(logging.DEBUG, "exit: _load_task_parser", reused=True)
        return mod
    except Exception:
        logger.exception("_load_task_parser failed")
        return None


@dataclass
class ParsedTask:
    task_id: str
    test_commands: list[str]
    acceptance_criteria: list[str]


def _local_parse(text: str, stem: str) -> ParsedTask:
    """Fallback parser for Test Commands + acceptance criteria."""
    _log(logging.DEBUG, "entry: _local_parse", stem=stem)
    tid_m = re.match(r"^T(\d+[\w\-]*)", stem, re.IGNORECASE)
    tid = tid_m.group(1) if tid_m else (
        re.match(r"^task-(.+)$", stem, re.IGNORECASE) or re.match(r"(.+)", stem)).group(1)
    try:
        m = re.search(r"^##\s+Test Commands.*?$(.*?)(?=^##\s+|\Z)",
                      text, flags=re.MULTILINE | re.DOTALL)
        cmds: list[str] = []
        if m:
            in_block = False
            for line in m.group(1).splitlines():
                s = line.strip()
                if s.startswith("```"):
                    in_block = not in_block
                    continue
                if in_block and s and not s.startswith("#"):
                    cmds.append(s)
        m2 = re.search(r"^##\s+Acceptance Criteria.*?$(.*?)(?=^##\s+|\Z)",
                       text, flags=re.MULTILINE | re.DOTALL)
        acs = [mm.group(1).strip()
               for line in (m2.group(1).splitlines() if m2 else [])
               for mm in [re.match(r"^\s*-\s*\[.\]\s*(.+)$", line)] if mm]
        pt = ParsedTask(task_id=tid, test_commands=cmds, acceptance_criteria=acs)
        _log(logging.DEBUG, "exit: _local_parse", task_id=pt.task_id, n_cmds=len(cmds))
        return pt
    except Exception:
        logger.exception("_local_parse failed")
        raise


def parse_task(task_path: Path) -> ParsedTask:
    """Parse task-N.md for Test Commands + acceptance criteria."""
    _log(logging.DEBUG, "entry: parse_task", task_path=str(task_path))
    try:
        if not task_path.exists():
            raise FileNotFoundError(f"Task file not found: {task_path}")
        mod = _load_task_parser()
        if mod is not None:
            try:
                t = mod.parse_task_file(task_path)
                pt = ParsedTask(task_id=t.task_id,
                                test_commands=list(t.test_commands),
                                acceptance_criteria=list(t.acceptance_criteria))
                _log(logging.INFO, "parsed_task_via_shared",
                     task_id=pt.task_id, n_cmds=len(pt.test_commands))
                return pt
            except Exception:
                logger.exception("shared parser failed; fallback local")
        pt = _local_parse(task_path.read_text(encoding="utf-8"), task_path.stem)
        _log(logging.INFO, "parsed_task_locally", task_id=pt.task_id,
             n_cmds=len(pt.test_commands))
        return pt
    except Exception:
        logger.exception("parse_task failed")
        raise


def _tail(text: str, n: int = 20) -> str:
    return "\n".join(text.splitlines()[-n:])


def run_test_commands(commands: list[str], worktree: Path,
                      per_timeout: int = 600) -> list[TestRun]:
    """Run each shell command in worktree; capture exit/tail/duration."""
    _log(logging.DEBUG, "entry: run_test_commands", n=len(commands),
         worktree=str(worktree))
    try:
        results: list[TestRun] = []
        for cmd in commands:
            _log(logging.INFO, "running_test", cmd=cmd, worktree=str(worktree))
            t0 = time.monotonic()
            try:
                proc = subprocess.run(cmd, shell=True, cwd=str(worktree),
                                      check=False, capture_output=True,
                                      text=True, timeout=per_timeout)
                run = TestRun(command=cmd, exit_code=proc.returncode,
                              duration_s=round(time.monotonic() - t0, 3),
                              stdout_tail=_tail(proc.stdout, 20),
                              stderr_tail=_tail(proc.stderr, 20))
            except subprocess.TimeoutExpired:
                _log(logging.WARNING, "test_timeout", cmd=cmd)
                run = TestRun(command=cmd, exit_code=124,
                              duration_s=round(time.monotonic() - t0, 3),
                              stdout_tail="", stderr_tail="TIMEOUT")
            results.append(run)
            _log(logging.INFO, "test_done", cmd=cmd, rc=run.exit_code,
                 dur=run.duration_s)
        _log(logging.DEBUG, "exit: run_test_commands", n=len(results))
        return results
    except Exception:
        logger.exception("run_test_commands failed")
        raise


def _resolve_base(worktree: Path, cli_base: str) -> str:
    """Resolve the diff base for one side's worktree.

    Priority (first match wins):
      1. Explicit CLI arg (not ``"HEAD"`` or ``"auto"``) - pass-through verbatim.
      2. Sidecar file ``<worktree>/.dual-base-ref`` (first non-empty line).
      3. ``git merge-base HEAD <branch>`` for branch in (main, master, dev).
      4. Literal ``"HEAD"`` fallback.

    Logs which level hit at INFO. Swallows per-step errors so a broken sidecar
    or missing git CLI cannot break scoring - always returns a usable string.
    """
    _log(logging.DEBUG, "entry: _resolve_base", worktree=str(worktree),
         cli_base=cli_base)
    try:
        if cli_base and cli_base not in ("HEAD", "auto"):
            _log(logging.INFO, "resolve_base hit=cli", base=cli_base,
                 worktree=str(worktree))
            return cli_base
        sidecar = worktree / ".dual-base-ref"
        if sidecar.exists():
            try:
                for ln in sidecar.read_text(encoding="utf-8").splitlines():
                    s = ln.strip()
                    if s and not s.startswith("#"):
                        _log(logging.INFO, "resolve_base hit=sidecar",
                             base=s, worktree=str(worktree))
                        return s
            except Exception:
                logger.exception("_resolve_base sidecar read failed")
        for branch in _MAIN_BRANCHES:
            try:
                proc = subprocess.run(
                    ["git", "merge-base", "HEAD", branch],
                    cwd=str(worktree), check=False, capture_output=True,
                    text=True, timeout=15,
                )
                if proc.returncode == 0:
                    sha = proc.stdout.strip()
                    if sha:
                        _log(logging.INFO, "resolve_base hit=merge-base",
                             branch=branch, base=sha[:12],
                             worktree=str(worktree))
                        return sha
            except subprocess.TimeoutExpired:
                _log(logging.WARNING, "_resolve_base merge-base timeout",
                     branch=branch)
                continue
            except Exception:
                logger.exception("_resolve_base merge-base error branch=%s", branch)
                continue
        _log(logging.INFO, "resolve_base hit=fallback", base="HEAD",
             worktree=str(worktree))
        return "HEAD"
    except Exception:
        logger.exception("_resolve_base unexpected error")
        return "HEAD"


def score_side(worktree: Path, test_runs: list[TestRun],
               base: str = "HEAD") -> list[AxisResult]:
    """Compute all six axes for one side."""
    _log(logging.DEBUG, "entry: score_side", worktree=str(worktree), base=base)
    try:
        axes = [score_tests_passed(test_runs, weight=10),
                score_diff_size(worktree, weight=2, base=base),
                score_logging_coverage(worktree, weight=3, base=base),
                score_lint_clean(worktree, weight=2, base=base),
                score_complexity(worktree, weight=1, base=base),
                score_type_check(worktree, weight=2, base=base)]
        _log(logging.DEBUG, "exit: score_side",
             active=sum(1 for a in axes if not a.skipped))
        return axes
    except Exception:
        logger.exception("score_side failed")
        raise


def build_verdict(task_id: str, claude_axes: list[AxisResult],
                  codex_axes: list[AxisResult],
                  tie_delta: float = 0.02) -> dict[str, Any]:
    """Assemble verdict JSON per AC7 schema."""
    _log(logging.DEBUG, "entry: build_verdict", task_id=task_id, tie_delta=tie_delta)
    try:
        c_agg = weighted_aggregate(claude_axes)
        k_agg = weighted_aggregate(codex_axes)
        winner, delta = decide_winner(c_agg, k_agg, tie_delta)
        verdict = {
            "task_id": task_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "winner": winner, "delta": round(delta, 4), "tie_delta": tie_delta,
            "scores": {
                "claude": {"aggregate": round(c_agg, 4),
                           "axes": {a.name: a.to_dict() for a in claude_axes}},
                "codex": {"aggregate": round(k_agg, 4),
                          "axes": {a.name: a.to_dict() for a in codex_axes}},
            },
            "rationale_auto": biggest_delta_rationale(claude_axes, codex_axes, winner),
            "rationale_manual": None,
        }
        _log(logging.INFO, "verdict_built", task_id=task_id, winner=winner,
             delta=round(delta, 4))
        return verdict
    except Exception:
        logger.exception("build_verdict failed")
        raise


def _default_output(task_id: str) -> Path:
    return Path("work/codex-primary/dual-history") / task_id / "judge-verdict.json"


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="judge.py",
        description="Objective judge for Claude vs Codex dual-implement runs.")
    p.add_argument("--task", required=True, type=Path, help="Path to task-N.md")
    p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
    p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
    p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
    p.add_argument("--base", default="auto",
                   help="Git diff base. 'auto' = auto-resolve per side via "
                        "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
                        "then HEAD fallback. 'HEAD' = literal HEAD pass-through. "
                        "Any other value = explicit base (commit sha / ref).")
    p.add_argument("--per-timeout", type=int, default=600, help="Per-cmd timeout (s)")
    p.add_argument("--dry-run", action="store_true", help="Print plan, skip tests")
    return p


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    args = build_arg_parser().parse_args(argv)
    _log(logging.INFO, "judge_start", task=str(args.task),
         claude=str(args.claude_worktree), codex=str(args.codex_worktree),
         tie_delta=args.tie_delta, dry_run=args.dry_run, base_arg=args.base)
    try:
        try:
            task = parse_task(args.task)
        except (FileNotFoundError, Exception) as e:  # noqa: B014
            _log(logging.ERROR, "task_parse_failed", err=str(e))
            print(f"ERROR: {e}", file=sys.stderr)
            return EXIT_INFRA
        for label, wt in (("claude", args.claude_worktree), ("codex", args.codex_worktree)):
            if not wt.exists():
                _log(logging.ERROR, "worktree_missing", side=label, path=str(wt))
                print(f"ERROR: {label} worktree not found: {wt}", file=sys.stderr)
                return EXIT_INFRA
        output = args.output or _default_output(task.task_id)
        if args.dry_run:
            plan = {"task_id": task.task_id, "test_commands": task.test_commands,
                    "claude_worktree": str(args.claude_worktree),
                    "codex_worktree": str(args.codex_worktree),
                    "output": str(output), "tie_delta": args.tie_delta,
                    "base_arg": args.base}
            print(json.dumps(plan, indent=2))
            _log(logging.INFO, "dry_run_complete", task_id=task.task_id)
            return EXIT_OK
        claude_base = _resolve_base(args.claude_worktree, args.base)
        codex_base = _resolve_base(args.codex_worktree, args.base)
        _log(logging.INFO, "running_claude_side", n_cmds=len(task.test_commands),
             base=claude_base)
        c_runs = run_test_commands(task.test_commands, args.claude_worktree, args.per_timeout)
        c_axes = score_side(args.claude_worktree, c_runs, base=claude_base)
        _log(logging.INFO, "running_codex_side", n_cmds=len(task.test_commands),
             base=codex_base)
        k_runs = run_test_commands(task.test_commands, args.codex_worktree, args.per_timeout)
        k_axes = score_side(args.codex_worktree, k_runs, base=codex_base)
        verdict = build_verdict(task.task_id, c_axes, k_axes, tie_delta=args.tie_delta)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(verdict, indent=2, ensure_ascii=False), encoding="utf-8")
        _log(logging.INFO, "verdict_written", path=str(output),
             winner=verdict["winner"], delta=verdict["delta"])
        print(json.dumps({"task_id": verdict["task_id"], "winner": verdict["winner"],
                          "delta": verdict["delta"], "output": str(output)}, indent=2))
        return EXIT_OK
    except Exception:
        logger.exception("judge main failed")
        return EXIT_INFRA


if __name__ == "__main__":
    sys.exit(main())


 succeeded in 151ms:
#!/usr/bin/env python3
"""Unit tests for codex-ask.py - Y23 (v0.125 stdout format support).

Covers:
  - parse_codex_exec_stdout for v0.125 (header in stderr, response in stdout)
  - parse_codex_exec_stdout for v0.117 legacy (sentinel "codex" in stdout)
  - ask_via_exec integration with mocked subprocess (both formats + edge cases)
  - main() end-to-end flow: last-consulted touch + edit-count reset

Run:
    python -m pytest .claude/scripts/test_codex_ask.py -v --tb=short
"""

from __future__ import annotations

import importlib.util
import logging
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest


# --------------------------------------------------------------------------- #
# Load codex-ask.py as a module (filename has a hyphen, so importlib needed). #
# --------------------------------------------------------------------------- #

_THIS = Path(__file__).resolve()
_SCRIPT = _THIS.parent / "codex-ask.py"

_spec = importlib.util.spec_from_file_location("codex_ask", _SCRIPT)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load {_SCRIPT}")
codex_ask = importlib.util.module_from_spec(_spec)
sys.modules["codex_ask"] = codex_ask
_spec.loader.exec_module(codex_ask)

logging.getLogger("codex_ask").setLevel(logging.CRITICAL)


# --------------------------------------------------------------------------- #
# AC-1: Parser handles v0.125 format (response only in stdout)                #
# --------------------------------------------------------------------------- #


class TestParseV125Format:
    """v0.125: header is in stderr, stdout has only the response (+ optional
    'tokens used' trailer). Old sentinel-based parser returned None."""

    def test_parse_v125_simple_ok(self):
        assert codex_ask.parse_codex_exec_stdout("OK\n") == "OK"

    def test_parse_v125_with_tokens_trailer(self):
        result = codex_ask.parse_codex_exec_stdout("OK\ntokens used\n3 901\nOK\n")
        assert result is not None
        assert result in ("OK", "OK\nOK")

    def test_parse_v125_multiline_response(self):
        stdout = "line 1\nline 2\nline 3\ntokens used\n100\n"
        assert codex_ask.parse_codex_exec_stdout(stdout) == "line 1\nline 2\nline 3"

    def test_parse_v125_empty_returns_none(self):
        assert codex_ask.parse_codex_exec_stdout("") is None

    def test_parse_v125_only_whitespace_returns_none(self):
        assert codex_ask.parse_codex_exec_stdout("   \n\n") is None


# --------------------------------------------------------------------------- #
# AC-2: Parser still handles v0.117 legacy format                             #
# --------------------------------------------------------------------------- #


class TestParseV117Legacy:
    def test_parse_v117_legacy_with_sentinel(self):
        stdout = (
            "[2026-04-26T12:00:00] OpenAI Codex v0.117\n"
            "model: gpt-5.4\n"
            "workdir: /tmp/work\n"
            "codex\n"
            "Hello world\n"
            "second line\n"
            "tokens used: 42\n"
        )
        assert codex_ask.parse_codex_exec_stdout(stdout) == "Hello world\nsecond line"

    def test_parse_v117_with_repeated_response(self):
        stdout = (
            "[ts] header\n"
            "model: gpt-5.4\n"
            "codex\n"
            "Answer: 42\n"
            "tokens used: 10\n"
            "Answer: 42\n"
        )
        result = codex_ask.parse_codex_exec_stdout(stdout)
        assert result is not None
        assert "Answer: 42" in result


# --------------------------------------------------------------------------- #
# AC-3: ask_via_exec integration (mocked subprocess)                          #
# --------------------------------------------------------------------------- #


def _completed(returncode, stdout="", stderr=""):
    return subprocess.CompletedProcess(
        args=["codex"], returncode=returncode, stdout=stdout, stderr=stderr,
    )


class TestAskViaExecIntegration:
    def test_ask_via_exec_v125_returns_response(self):
        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
             mock.patch.object(codex_ask.subprocess, "run",
                               return_value=_completed(0, stdout="OK\n",
                                                       stderr="[ts] header\n")):
            assert codex_ask.ask_via_exec("ping say OK") == "OK"

    def test_ask_via_exec_v117_returns_response(self):
        v117_stdout = (
            "[ts] header\n"
            "model: gpt-5.4\n"
            "codex\n"
            "Hello\n"
            "tokens used: 5\n"
        )
        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
             mock.patch.object(codex_ask.subprocess, "run",
                               return_value=_completed(0, stdout=v117_stdout, stderr="")):
            assert codex_ask.ask_via_exec("hello") == "Hello"

    def test_ask_via_exec_returncode_nonzero_returns_none(self):
        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
             mock.patch.object(codex_ask.subprocess, "run",
                               return_value=_completed(1, stdout="OK\n", stderr="boom")):
            assert codex_ask.ask_via_exec("anything") is None

    def test_ask_via_exec_codex_not_in_path_returns_none(self):
        with mock.patch.object(codex_ask.shutil, "which", return_value=None), \
             mock.patch.object(codex_ask.subprocess, "run") as run_mock:
            assert codex_ask.ask_via_exec("anything") is None
        run_mock.assert_not_called()

    def test_ask_via_exec_timeout_returns_none(self):
        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
             mock.patch.object(codex_ask.subprocess, "run",
                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
            assert codex_ask.ask_via_exec("anything") is None


# --------------------------------------------------------------------------- #
# AC-4: parse_codex_exec_stdout exists, has docstring, ask_via_exec uses it   #
# --------------------------------------------------------------------------- #


class TestRefactorContract:
    def test_parse_function_exists(self):
        assert hasattr(codex_ask, "parse_codex_exec_stdout")
        assert callable(codex_ask.parse_codex_exec_stdout)

    def test_parse_function_has_docstring_mentioning_both_versions(self):
        doc = (codex_ask.parse_codex_exec_stdout.__doc__ or "").lower()
        assert "v0.117" in doc
        assert "v0.125" in doc

    def test_ask_via_exec_delegates_to_parser(self):
        sentinel_response = "PATCHED-RESULT"
        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
             mock.patch.object(codex_ask.subprocess, "run",
                               return_value=_completed(0, stdout="anything\n", stderr="")), \
             mock.patch.object(codex_ask, "parse_codex_exec_stdout",
                               return_value=sentinel_response) as parse_mock:
            assert codex_ask.ask_via_exec("anything") == sentinel_response
        parse_mock.assert_called_once()


# --------------------------------------------------------------------------- #
# AC-5: Regression - main() flow still touches last-consulted + resets count  #
# --------------------------------------------------------------------------- #


class TestMainFlowUnchanged:
    def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
        monkeypatch.setattr(codex_ask, "ask_via_broker",
                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])

        with pytest.raises(SystemExit) as exc:
            codex_ask.main()
        assert exc.value.code == 0

        captured = capsys.readouterr()
        assert "FAKE-RESPONSE" in captured.out
        assert "Codex gpt-5.5 opinion" in captured.out

        last_consulted = tmp_path / ".codex" / "last-consulted"
        edit_count = tmp_path / ".codex" / "edit-count"
        assert last_consulted.exists()
        assert edit_count.exists()
        assert edit_count.read_text(encoding="utf-8") == "0"
        float(last_consulted.read_text(encoding="utf-8"))


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))


 succeeded in 148ms:
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
    _log(logging.DEBUG, "entry: score_tests_passed", n=len(runs))
    try:
        if not runs:
            return _skip("tests_passed", weight, "no test commands")
        passed = sum(1 for r in runs if r.passed)
        score = passed / len(runs)
        _log(logging.DEBUG, "exit: score_tests_passed", score=score,
             passed=passed, total=len(runs))
        return AxisResult(name="tests_passed", score=score, weight=weight,
                          raw={"passed": passed, "total": len(runs)})
    except Exception:
        logger.exception("score_tests_passed failed")
        raise


def _ensure_untracked_visible(worktree: Path) -> int:
    """Register untracked .py files with ``git add -N`` so they appear in diffs.

    Intent-to-add stages only the filename (not content), which makes
    ``git diff <base>`` include the file as a new-file diff. Idempotent:
    ``git add -N`` on an already-registered file is a no-op. Swallows every
    exception and returns 0 - this helper MUST NOT break axis scoring.
    """
    _log(logging.DEBUG, "entry: _ensure_untracked_visible", worktree=str(worktree))
    try:
        proc = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=str(worktree), check=False, capture_output=True,
            text=True, timeout=30,
        )
        if proc.returncode != 0:
            _log(logging.WARNING, "_ensure_untracked_visible ls-files failed",
                 rc=proc.returncode, stderr=proc.stderr[:200])
            return 0
        py_files = [ln.strip() for ln in proc.stdout.splitlines()
                    if ln.strip().endswith(".py")]
        if not py_files:
            _log(logging.DEBUG, "exit: _ensure_untracked_visible", count=0)
            return 0
        add_proc = subprocess.run(
            ["git", "add", "-N", "--", *py_files],
            cwd=str(worktree), check=False, capture_output=True,
            text=True, timeout=30,
        )
        if add_proc.returncode != 0:
            _log(logging.WARNING, "_ensure_untracked_visible add -N failed",
                 rc=add_proc.returncode, stderr=add_proc.stderr[:200])
            return 0
        count = len(py_files)
        _log(logging.INFO, "exit: _ensure_untracked_visible", count=count,
             sample=py_files[:5])
        return count
    except subprocess.TimeoutExpired:
        _log(logging.WARNING, "_ensure_untracked_visible timeout",
             worktree=str(worktree))
        return 0
    except Exception:
        logger.exception("_ensure_untracked_visible failed")
        return 0


def _git_diff_numstat(worktree: Path, base: str = "HEAD") -> tuple[int, int]:
    """Return (added, removed) for working-tree-vs-base.

    Uses ``git diff <base>`` form (NOT ``<base>..HEAD``) so committed +
    staged + unstaged + intent-to-add changes are all captured. Calls
    ``_ensure_untracked_visible`` first to register untracked .py files.
    """
    _log(logging.DEBUG, "entry: _git_diff_numstat", worktree=str(worktree), base=base)
    try:
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
    """Smaller diff = higher score. Asymptotic Hill function.

    score = scale / (scale + max(0, added))

    where ``scale`` is the legacy ``cap_lines`` parameter (kept for kwarg
    backward compat). The function is smooth, monotonic, and asymptotic
    to 0 as ``added`` -> infinity. Sample anchor points:
      added=0      -> 1.0
      added=scale  -> 0.5
      added=2*scale-> 0.333
      added=10*scale->~0.091

    Y21 (Z12): replaces hard-zero clamp ``max(0, 1 - added/cap)`` so
    diffs above the scale stay differentiable. Z1's +1102 LOC artifact
    was forced to a TIE; under this curve it would yield a real verdict.
    """
    _log(logging.DEBUG, "entry: score_diff_size", worktree=str(worktree), cap=cap_lines)
    try:
        added, removed = _git_diff_numstat(worktree, base)
        scale_factor = max(1, int(cap_lines))
        added_clamped = max(0, int(added))
        score = scale_factor / (scale_factor + added_clamped)
        _log(logging.DEBUG, "exit: score_diff_size", score=score, added=added,
             scale=scale_factor)
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
                              cwd=str(worktree), check=False, capture_output=True,
                              text=True, timeout=30)
        _log(logging.DEBUG, "exit: _git_diff_text", chars=len(proc.stdout))
        return proc.stdout
    except subprocess.TimeoutExpired:
        _log(logging.WARNING, "_git_diff_text timeout", worktree=str(worktree))
        return ""
    except Exception:
        logger.exception("_git_diff_text failed")
        return ""


def score_logging_coverage(worktree: Path, weight: int = 3, base: str = "HEAD",
                           window: int = 5, diff_text: str | None = None) -> AxisResult:
    """Fraction of NEW Python functions that log within `window` following lines."""
    _log(logging.DEBUG, "entry: score_logging_coverage", worktree=str(worktree),
         window=window)
    try:
        diff = diff_text if diff_text is not None else _git_diff_text(worktree, base)
        if not diff.strip():
            return _skip("logging_coverage", weight, "empty diff")
        lines = diff.splitlines()
        total = covered = 0
        for i, line in enumerate(lines):
            if not _FUNC_RE.match(line):
                continue
            total += 1
            found = False
            j = i + 1
            seen = 0
            while j < len(lines) and seen < window:
                nxt = lines[j]
                if nxt.startswith("@@"):
                    break
                if nxt.startswith("+") or (nxt and not nxt.startswith("-")):
                    seen += 1
                    if _LOGGER_RE.search(nxt):
                        found = True
                        break
                j += 1
            if found:
                covered += 1
        if total == 0:
            return _skip("logging_coverage", weight, "no new python functions")
        score = covered / total
        _log(logging.DEBUG, "exit: score_logging_coverage", score=score,
             covered=covered, total=total)
        return AxisResult(name="logging_coverage", score=score, weight=weight,
                          raw={"covered": covered, "total": total, "window": window})
    except Exception:
        logger.exception("score_logging_coverage failed")
        raise


def _list_modified_py(worktree: Path, base: str = "HEAD") -> list[Path]:
    """List modified .py files for working-tree-vs-base (``git diff --name-only <base>``).

    Calls ``_ensure_untracked_visible`` first so untracked .py files are listed.
    """
    _log(logging.DEBUG, "entry: _list_modified_py", worktree=str(worktree))
    try:
        _ensure_untracked_visible(worktree)
        proc = subprocess.run(["git", "diff", "--name-only", base],
                              cwd=str(worktree), check=False, capture_output=True,
                              text=True, timeout=30)
        files: list[Path] = []
        for line in proc.stdout.splitlines():
            s = line.strip()
            if s.endswith(".py"):
                p = worktree / s
                if p.exists():
                    files.append(p)
        _log(logging.DEBUG, "exit: _list_modified_py", count=len(files))
        return files
    except subprocess.TimeoutExpired:
        _log(logging.WARNING, "_list_modified_py timeout")
        return []
    except Exception:
        logger.exception("_list_modified_py failed")
        return []


def score_lint_clean(worktree: Path, weight: int = 2, base: str = "HEAD",
                     files_override: list[Path] | None = None) -> AxisResult:
    """py_compile + optional pyflakes. score = max(0, 1 - (errs+0.2*warns)/files)."""
    _log(logging.DEBUG, "entry: score_lint_clean", worktree=str(worktree))
    try:
        files = files_override if files_override is not None else _list_modified_py(worktree, base)
        if not files:
            return _skip("lint_clean", weight, "no modified .py files")
        compile_errors = 0
        for f in files:
            proc = subprocess.run([sys.executable, "-m", "py_compile", str(f)],
                                  check=False, capture_output=True, text=True, timeout=30)
            if proc.returncode != 0:
                compile_errors += 1
        pyflakes_warnings = 0
        pyflakes_used = _module_available("pyflakes")
        if pyflakes_used:
            proc = subprocess.run([sys.executable, "-m", "pyflakes",
                                   *[str(f) for f in files]],
                                  check=False, capture_output=True, text=True, timeout=60)
            pyflakes_warnings = sum(1 for ln in proc.stdout.splitlines() if ln.strip())
        else:
            _log(logging.INFO, "optional_tool_missing", tool="pyflakes")
        n = max(len(files), 1)
        score = max(0.0, 1.0 - (compile_errors + 0.2 * pyflakes_warnings) / n)
        _log(logging.DEBUG, "exit: score_lint_clean", score=score,
             compile_errors=compile_errors, pyflakes_warnings=pyflakes_warnings)
        return AxisResult(name="lint_clean", score=score, weight=weight,
                          raw={"files": len(files), "compile_errors": compile_errors,
                               "pyflakes_warnings": pyflakes_warnings,
                               "pyflakes_used": pyflakes_used})
    except Exception:
        logger.exception("score_lint_clean failed")
        raise


def score_complexity(worktree: Path, weight: int = 1, base: str = "HEAD",
                     files_override: list[Path] | None = None) -> AxisResult:
    """Radon CC (optional). score = max(0, 1 - avg_cc/20)."""
    _log(logging.DEBUG, "entry: score_complexity", worktree=str(worktree))
    try:
        if not _module_available("radon"):
            return _skip("complexity", weight, "radon not installed")
        files = files_override if files_override is not None else _list_modified_py(worktree, base)
        if not files:
            return _skip("complexity", weight, "no modified .py files")
        try:
            from radon.complexity import cc_visit  # type: ignore
        except ImportError:
            return _skip("complexity", weight, "radon import failed")
        cc_values: list[int] = []
        for f in files:
            try:
                src = f.read_text(encoding="utf-8", errors="replace")
                for block in cc_visit(src):
                    cc_values.append(int(block.complexity))
            except Exception:
                logger.exception("radon parse failed on %s", f)
                continue
        if not cc_values:
            return _skip("complexity", weight, "no functions in modified files")
        avg_cc = sum(cc_values) / len(cc_values)
        score = max(0.0, 1.0 - avg_cc / 20.0)
        _log(logging.DEBUG, "exit: score_complexity", score=score, avg_cc=avg_cc)
        return AxisResult(name="complexity", score=score, weight=weight,
                          raw={"avg_cc": round(avg_cc, 2), "max_cc": max(cc_values),
                               "n_functions": len(cc_values)})
    except Exception:
        logger.exception("score_complexity failed")
        raise


def score_type_check(worktree: Path, weight: int = 2, base: str = "HEAD",
                     files_override: list[Path] | None = None) -> AxisResult:
    """Mypy (optional, needs config). score = max(0, 1 - errors/files)."""
    _log(logging.DEBUG, "entry: score_type_check", worktree=str(worktree))
    try:
        if not _module_available("mypy"):
            return _skip("type_check", weight, "mypy not installed")
        has_config = any((worktree / p).exists()
                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
        if not has_config:
            return _skip("type_check", weight, "no mypy config")
        files = files_override if files_override is not None else _list_modified_py(worktree, base)
        if not files:
            return _skip("type_check", weight, "no modified .py files")
        proc = subprocess.run([sys.executable, "-m", "mypy", "--no-error-summary",
                               *[str(f) for f in files]],
                              cwd=str(worktree), check=False, capture_output=True,
                              text=True, timeout=180)
        errors = sum(1 for ln in proc.stdout.splitlines() if ": error:" in ln)
        n = max(len(files), 1)
        score = max(0.0, 1.0 - errors / n)
        _log(logging.DEBUG, "exit: score_type_check", score=score, errors=errors)
        return AxisResult(name="type_check", score=score, weight=weight,
                          raw={"errors": errors, "files": len(files)})
    except subprocess.TimeoutExpired:
        _log(logging.WARNING, "score_type_check timeout")
        return _skip("type_check", weight, "mypy timeout")
    except Exception:
        logger.exception("score_type_check failed")
        raise


def weighted_aggregate(axes: list[AxisResult]) -> float:
    """sum(weight*score) / sum(weight_used), ignoring skipped axes."""
    _log(logging.DEBUG, "entry: weighted_aggregate", n=len(axes))
    try:
        used = [a for a in axes if not a.skipped]
        if not used:
            _log(logging.WARNING, "weighted_aggregate: no active axes")
            return 0.0
        total_w = sum(a.weight for a in used)
        if total_w <= 0:
            _log(logging.WARNING, "weighted_aggregate: zero total weight")
            return 0.0
        agg = sum(a.weight * a.score for a in used) / total_w
        _log(logging.DEBUG, "exit: weighted_aggregate", agg=agg, total_w=total_w)
        return agg
    except Exception:
        logger.exception("weighted_aggregate failed")
        raise


def decide_winner(claude_agg: float, codex_agg: float,
                  tie_delta: float = 0.02) -> tuple[str, float]:
    """Return (winner, delta). winner in {'claude','codex','tie'}."""
    _log(logging.DEBUG, "entry: decide_winner", claude=claude_agg,
         codex=codex_agg, tie_delta=tie_delta)
    try:
        delta = claude_agg - codex_agg
        if delta >= tie_delta:
            winner = "claude"
        elif -delta >= tie_delta:
            winner = "codex"
        else:
            winner = "tie"
        _log(logging.DEBUG, "exit: decide_winner", winner=winner, delta=delta)
        return winner, delta
    except Exception:
        logger.exception("decide_winner failed")
        raise


def biggest_delta_rationale(claude_axes: list[AxisResult],
                            codex_axes: list[AxisResult], winner: str) -> str:
    """Cite the axis with the largest |claude - codex| delta."""
    _log(logging.DEBUG, "entry: biggest_delta_rationale", winner=winner)
    try:
        c = {a.name: a for a in claude_axes if not a.skipped}
        k = {a.name: a for a in codex_axes if not a.skipped}
        common = set(c) & set(k)
        if not common:
            return f"winner={winner}: no common active axes"
        best = max(common, key=lambda n: abs(c[n].score - k[n].score))
        out = (f"winner={winner} вЂ” biggest axis delta on '{best}' "
               f"(claude={c[best].score:.3f}, codex={k[best].score:.3f})")
        _log(logging.DEBUG, "exit: biggest_delta_rationale", rationale=out)
        return out
    except Exception:
        logger.exception("biggest_delta_rationale failed")
        raise


 succeeded in 141ms:
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
            # Y21 (Z12): score = 500 / (500 + 50) = 0.909... still in [0.85, 0.95]
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

    # ----- Y21 (Z12): asymptotic Hill function tests -----

    def test_diff_size_zero_added_scores_one(self) -> None:
        """Y21 AC: added=0, cap=500 => score == 1.0 (boundary)."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)
            res = score_diff_size(repo, cap_lines=500)
            self.assertAlmostEqual(res.score, 1.0, places=6)

    def test_diff_size_at_scale_scores_half(self) -> None:
        """Y21 AC: added=cap=500 => score in [0.49, 0.51] (Hill midpoint)."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)
            _add_file(repo, "a.py", "# pre\n", commit=True)
            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 500))
            res = score_diff_size(repo, cap_lines=500)
            # 500 / (500 + 500) = 0.5 exactly
            self.assertGreaterEqual(res.score, 0.49)
            self.assertLessEqual(res.score, 0.51)
            self.assertEqual(res.raw["added"], 500)

    def test_diff_size_far_above_scale_still_nonzero(self) -> None:
        """Y21 AC: added=2000, cap=500 => 0.0 < score < 0.3 (4*scale region).

        Under the OLD formula this would clamp to 0.0 (forcing a TIE).
        Under Hill: 500/(500+2000) = 0.2.
        """
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)
            _add_file(repo, "a.py", "# pre\n", commit=True)
            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 2000))
            res = score_diff_size(repo, cap_lines=500)
            self.assertGreater(res.score, 0.0,
                               "asymptotic вЂ” must NOT clamp to zero")
            self.assertLess(res.score, 0.3)
            self.assertEqual(res.raw["added"], 2000)

    def test_diff_size_huge_diff_asymptotic(self) -> None:
        """Y21 AC: added=10000, cap=500 => score in (0.0, 0.1] (~0.0476)."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)
            _add_file(repo, "a.py", "# pre\n", commit=True)
            _add_file(repo, "a.py", "# pre\n" + ("x = 1\n" * 10000))
            res = score_diff_size(repo, cap_lines=500)
            # 500/(500+10000) = 0.0476..
            self.assertGreater(res.score, 0.0)
            self.assertLessEqual(res.score, 0.1)
            self.assertEqual(res.raw["added"], 10000)


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
    def test_clean_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            clean = _add_file(repo, "clean.py", "x = 1\n")
            res = score_lint_clean(repo, files_override=[clean])
            self.assertAlmostEqual(res.score, 1.0)
            self.assertEqual(res.raw["compile_errors"], 0)

    def test_syntax_error(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            bad = _add_file(repo, "bad.py", "def :\n")
            res = score_lint_clean(repo, files_override=[bad])
            self.assertLess(res.score, 1.0)
            self.assertEqual(res.raw["compile_errors"], 1)

    def test_no_files_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            res = score_lint_clean(repo, files_override=[])
            self.assertTrue(res.skipped)
            self.assertEqual(res.skip_reason, "no modified .py files")


# ------------------------ optional tool skip ------------------------ #


class TestOptionalToolSkip(unittest.TestCase):
    def test_complexity_skipped_when_radon_absent(self) -> None:
        with patch.object(judge_axes, "_module_available", return_value=False):
            res = judge_axes.score_complexity(Path("."))
            self.assertTrue(res.skipped)
            self.assertIn("radon", res.skip_reason or "")

    def test_type_check_skipped_when_mypy_absent(self) -> None:
        with patch.object(judge_axes, "_module_available", return_value=False):
            res = judge_axes.score_type_check(Path("."))
            self.assertTrue(res.skipped)
            self.assertIn("mypy", res.skip_reason or "")


# ------------------------ weighted aggregate + winner ------------------------ #


class TestWeightedAggregate(unittest.TestCase):
    def test_weighted_correctness(self) -> None:
        axes = [
            AxisResult(name="a", score=1.0, weight=10),
            AxisResult(name="b", score=0.5, weight=2),
            AxisResult(name="c", score=0.0, weight=2),
        ]
        # (10*1 + 2*0.5 + 2*0) / 14 = 11/14 ~ 0.786
        agg = weighted_aggregate(axes)
        self.assertAlmostEqual(agg, 11 / 14, places=4)

    def test_skipped_ignored(self) -> None:
        axes = [
            AxisResult(name="a", score=1.0, weight=10),
            AxisResult(name="b", score=0.0, weight=100, skipped=True),
        ]
        self.assertAlmostEqual(weighted_aggregate(axes), 1.0)

    def test_all_skipped_zero(self) -> None:
        axes = [AxisResult(name="a", score=1.0, weight=10, skipped=True)]
        self.assertEqual(weighted_aggregate(axes), 0.0)


class TestWinnerDecision(unittest.TestCase):
    def test_claude_wins(self) -> None:
        w, d = decide_winner(0.80, 0.70)
        self.assertEqual(w, "claude")
        self.assertAlmostEqual(d, 0.10)

    def test_codex_wins(self) -> None:
        w, d = decide_winner(0.70, 0.90)
        self.assertEqual(w, "codex")

    def test_tie_within_delta(self) -> None:
        w, d = decide_winner(0.81, 0.80)  # delta 0.01 < 0.02
        self.assertEqual(w, "tie")

    def test_tie_custom_delta(self) -> None:
        w, _ = decide_winner(0.90, 0.70, tie_delta=0.25)
        self.assertEqual(w, "tie")


# ------------------------ verdict JSON schema ------------------------ #


class TestVerdictSchema(unittest.TestCase):
    def test_verdict_is_valid_json(self) -> None:
        c_axes = [AxisResult(name="tests_passed", score=1.0, weight=10)]
        k_axes = [AxisResult(name="tests_passed", score=0.5, weight=10)]
        verdict = judge.build_verdict("demo", c_axes, k_axes, tie_delta=0.02)
        blob = json.dumps(verdict)
        parsed = json.loads(blob)
        self.assertEqual(parsed["task_id"], "demo")
        self.assertEqual(parsed["winner"], "claude")
        self.assertIn("scores", parsed)
        self.assertIn("claude", parsed["scores"])
        self.assertIn("codex", parsed["scores"])
        self.assertIn("aggregate", parsed["scores"]["claude"])
        self.assertIn("axes", parsed["scores"]["claude"])
        self.assertIn("rationale_auto", parsed)
        self.assertIsNone(parsed["rationale_manual"])

    def test_rationale_cites_biggest_delta(self) -> None:
        c_axes = [
            AxisResult(name="tests_passed", score=1.0, weight=10),
            AxisResult(name="diff_size", score=0.5, weight=2),
        ]
        k_axes = [
            AxisResult(name="tests_passed", score=0.9, weight=10),
            AxisResult(name="diff_size", score=0.9, weight=2),
        ]
        rat = biggest_delta_rationale(c_axes, k_axes, "tie")
        # diff_size delta = 0.4, tests_passed delta = 0.1 => diff_size cited
        self.assertIn("diff_size", rat)


# ------------------------ CLI behavior ------------------------ #


class TestCLI(unittest.TestCase):
    def test_help_exits_zero(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
            check=False, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Objective judge", proc.stdout)

    def test_help_mentions_auto_base(self) -> None:
        """AC6: --help text must mention auto-resolve for --base."""
        proc = subprocess.run(
            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
            check=False, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("--base", proc.stdout)
        self.assertIn("auto", proc.stdout)

    def test_malformed_task_exit_1(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "nope.md"
            wt = Path(td) / "wt"
            wt.mkdir()
            rc = judge.main([
                "--task", str(missing),
                "--claude-worktree", str(wt),
                "--codex-worktree", str(wt),
            ])
            self.assertEqual(rc, 1)

    def test_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            task = tdp / "T1.md"
            task.write_text(textwrap.dedent("""\
                ---
                executor: dual
                ---
                # T1
                ## Test Commands
                ```bash
                echo hi
                ```
                ## Acceptance Criteria
                - [ ] AC1: ok
                """), encoding="utf-8")
            c_wt = tdp / "c"
            c_wt.mkdir()
            k_wt = tdp / "k"
            k_wt.mkdir()
            rc = judge.main([
                "--task", str(task),
                "--claude-worktree", str(c_wt),
                "--codex-worktree", str(k_wt),
                "--dry-run",
            ])
            self.assertEqual(rc, 0)


# ------------------------ logging sanity ------------------------ #


class TestStructuredLogging(unittest.TestCase):
    """AC10: each module emits structured JSON logs on entry/exit."""

    def test_json_formatter_shape(self) -> None:
        fmt = judge_axes.JsonFormatter()
        rec = logging.LogRecord(
            name="t", level=logging.INFO, pathname="x", lineno=1,
            msg="hello", args=(), exc_info=None,
        )
        out = fmt.format(rec)
        parsed = json.loads(out)
        self.assertEqual(parsed["msg"], "hello")
        self.assertEqual(parsed["level"], "INFO")
        self.assertIn("ts", parsed)


# ------------------------ FIX-A: diff-baseline AC7 coverage ------------------------ #


class TestEnsureUntrackedVisible(unittest.TestCase):
    """AC1/AC7b: _ensure_untracked_visible registers untracked .py files.

    Ensures the helper makes `git diff` see files that were previously
    invisible because they were never tracked.
    """

    def test_idempotent_no_untracked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)
            # No untracked files - should return 0 both times.
            self.assertEqual(judge_axes._ensure_untracked_visible(repo), 0)
            self.assertEqual(judge_axes._ensure_untracked_visible(repo), 0)

    def test_registers_untracked_py(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)
            _add_file(repo, "newfile.py", "x = 1\n")
            _add_file(repo, "skip.txt", "not python\n")
            n = judge_axes._ensure_untracked_visible(repo)
            self.assertEqual(n, 1)
            # Second call is idempotent (safe - git add -N already registered;
            # git ls-files --others now returns empty, so return 0 not 1).
            n2 = judge_axes._ensure_untracked_visible(repo)
            self.assertEqual(n2, 0)
            # File is still visible in diff after both calls.
            added, _ = judge_axes._git_diff_numstat(repo, base="HEAD")
            self.assertGreater(added, 0)

    def test_never_raises_on_missing_git(self) -> None:
        # Non-git directory: git ls-files fails; helper must return 0.
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self.assertEqual(judge_axes._ensure_untracked_visible(repo), 0)


class TestDiffBaselineCommitted(unittest.TestCase):
    """AC7a: committed-only worktree produces non-empty numstat.

    After a commit, `git diff HEAD` is empty. Using merge-base against
    the parent commit makes changes visible again.
    """

    def test_committed_diff_visible_with_merge_base(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)
            # Capture initial commit sha as the base.
            proc = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(repo), check=True, capture_output=True, text=True,
            )
            base = proc.stdout.strip()
            # Now commit a change on top of base.
            _add_file(repo, "committed.py", "x = 1\ny = 2\ny = 3\n", commit=True)
            # Against HEAD diff is empty; against base (parent) it should NOT be empty.
            added_head, _ = judge_axes._git_diff_numstat(repo, base="HEAD")
            added_base, _ = judge_axes._git_diff_numstat(repo, base=base)
            self.assertEqual(added_head, 0)
            self.assertGreater(added_base, 0)


class TestDiffBaselineUntracked(unittest.TestCase):
    """AC7b: untracked-only worktree produces non-empty numstat after helper."""

    def test_untracked_numstat_after_ensure(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)
            _add_file(repo, "newfile.py", "x = 1\ny = 2\nz = 3\n")
            # _git_diff_numstat internally calls _ensure_untracked_visible first,
            # so the untracked file should show up in the numstat.
            added, _ = judge_axes._git_diff_numstat(repo, base="HEAD")
            self.assertGreater(added, 0)
            # Modified file list should include the new file too.
            files = judge_axes._list_modified_py(repo, base="HEAD")
            self.assertTrue(any(f.name == "newfile.py" for f in files))


class TestResolveBase(unittest.TestCase):
    """AC7c/AC7d: _resolve_base priority order."""

    def test_sidecar_wins_over_auto_fallback(self) -> None:
        """AC7c: sidecar beats CLI='auto' and merge-base fallback."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)
            (repo / ".dual-base-ref").write_text("abc123def456\n", encoding="utf-8")
            resolved = judge._resolve_base(repo, "auto")
            self.assertEqual(resolved, "abc123def456")

    def test_cli_explicit_wins_over_sidecar(self) -> None:
        """Explicit CLI arg other than HEAD/auto is pass-through verbatim."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)
            (repo / ".dual-base-ref").write_text("sidecar-sha\n", encoding="utf-8")
            resolved = judge._resolve_base(repo, "explicit-ref")
            self.assertEqual(resolved, "explicit-ref")

    def test_merge_base_when_no_sidecar_and_auto(self) -> None:
        """AC7d: without sidecar + CLI=auto, picks merge-base HEAD <branch>."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)  # main branch already exists
            # Extra commit on main so HEAD != merge-base(HEAD, main) is well-defined.
            _add_file(repo, "seed.py", "x = 1\n", commit=True)
            resolved = judge._resolve_base(repo, "auto")
            # Should be a 40-char sha (merge-base output), not the literal string.
            self.assertNotIn(resolved, ("HEAD", "auto"))
            self.assertTrue(len(resolved) >= 7 and all(c in "0123456789abcdef" for c in resolved))

    def test_head_fallback_in_non_git(self) -> None:
        """Non-git directory + CLI=auto falls back to literal 'HEAD'."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            # No git init.
            resolved = judge._resolve_base(repo, "auto")
            self.assertEqual(resolved, "HEAD")

    def test_head_literal_passes_through_to_fallback(self) -> None:
        """CLI='HEAD' triggers resolution logic; if no sidecar and no merge-base,
        the result is literal 'HEAD'."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            # Non-git: skip sidecar + merge-base -> literal HEAD.
            resolved = judge._resolve_base(repo, "HEAD")
            self.assertEqual(resolved, "HEAD")


if __name__ == "__main__":
    unittest.main(verbosity=2)


codex
The key changes are small: one new boolean path through `codex-ask`, one root config file, a narrower mypy config detector, the judge default threshold, and one logging regex expansion. I’m checking the current tests’ import style so the new assertions fit without changing the test harness.
codex
I’m applying the scoped edits now. The only behavioral addition in `codex-ask` is a `strategic` flag that changes the exec fallback timeout; broker behavior stays unchanged.
apply patch
patch: completed
C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final\.claude\scripts\codex-ask.py
C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final\.claude\scripts\judge.py
C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final\.claude\scripts\judge_axes.py
C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final\mypy.ini
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..e84e344671eef1888c3c236ba5a1cde649dd454f
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -213,7 +213,9 @@
 
 
 _FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?:_log|log_info|log_warn|log_error|log_debug)\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..e84e344671eef1888c3c236ba5a1cde649dd454f
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -213,7 +213,9 @@
 
 
 _FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?:_log|log_info|log_warn|log_error|log_debug)\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

apply patch
patch: completed
C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final\.claude\scripts\test_codex_ask.py
C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final\.claude\scripts\test_judge.py
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..e84e344671eef1888c3c236ba5a1cde649dd454f
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -213,7 +213,9 @@
 
 
 _FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?:_log|log_info|log_warn|log_error|log_debug)\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..a6d847de451eee2112f9de7df079578471b3bca4
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..e84e344671eef1888c3c236ba5a1cde649dd454f
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -213,7 +213,9 @@
 
 
 _FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?:_log|log_info|log_warn|log_error|log_debug)\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..a6d847de451eee2112f9de7df079578471b3bca4
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

codex
The implementation and tests are in place. I’m doing a quick diff review before running pytest so I can catch mechanical issues like an import/test mismatch first.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff -- .claude/scripts/codex-ask.py .claude/scripts/test_codex_ask.py .claude/scripts/judge.py .claude/scripts/judge_axes.py .claude/scripts/test_judge.py mypy.ini' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 143ms:
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719..f64816f 100644
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -31,6 +31,8 @@ if sys.platform == "win32":
 BROKER_URL = "ws://127.0.0.1:4500"
 INACTIVITY_TIMEOUT = 30
 MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
 
 logger = logging.getLogger(__name__)
 
@@ -151,13 +153,15 @@ def ask_via_broker(prompt):
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
     """Fallback: ask via codex exec (cold start).
 
     Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
     both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
     """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
     codex = shutil.which("codex")
     if not codex:
         logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
@@ -167,7 +171,7 @@ def ask_via_exec(prompt):
             [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
              "--sandbox", "read-only", "--full-auto", "--ephemeral"],
             capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
+            timeout=timeout,
         )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
@@ -185,11 +189,16 @@ def ask_via_exec(prompt):
 
 
 def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
         sys.exit(1)
 
-    prompt = " ".join(sys.argv[1:])
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -200,7 +209,7 @@ def main():
 
     # Fallback to codex exec
     if not result:
-        result = ask_via_exec(prompt)
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3..946aa74 100644
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@ def build_arg_parser() -> argparse.ArgumentParser:
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc..e84e344 100644
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -213,7 +213,9 @@ def score_diff_size(worktree: Path, weight: int = 2, base: str = "HEAD",
 
 
 _FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?:_log|log_info|log_warn|log_error|log_debug)\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,8 +389,17 @@ def score_type_check(worktree: Path, weight: int = 2, base: str = "HEAD",
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
         if not has_config:
             return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165..a6d847d 100644
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -119,6 +119,22 @@ class TestAskViaExecIntegration:
                                                        stderr="[ts] header\n")):
             assert codex_ask.ask_via_exec("ping say OK") == "OK"
 
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
     def test_ask_via_exec_v117_returns_response(self):
         v117_stdout = (
             "[ts] header\n"
@@ -147,7 +163,7 @@ class TestAskViaExecIntegration:
     def test_ask_via_exec_timeout_returns_none(self):
         with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
              mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
             assert codex_ask.ask_via_exec("anything") is None
 
 
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd..b9e7ec9 100644
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -182,6 +182,18 @@ class TestLoggingCoverage(unittest.TestCase):
         self.assertAlmostEqual(res.score, 1.0)
         self.assertEqual(res.raw["covered"], 1)
 
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
     def test_function_without_logger(self) -> None:
         diff = textwrap.dedent("""\
             diff --git a/x.py b/x.py
@@ -261,6 +273,24 @@ class TestOptionalToolSkip(unittest.TestCase):
             self.assertTrue(res.skipped)
             self.assertIn("mypy", res.skip_reason or "")
 
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
+
 
 # ------------------------ weighted aggregate + winner ------------------------ #
 
@@ -363,6 +393,14 @@ class TestCLI(unittest.TestCase):
         self.assertIn("--base", proc.stdout)
         self.assertIn("auto", proc.stdout)
 
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
     def test_malformed_task_exit_1(self) -> None:
         with tempfile.TemporaryDirectory() as td:
             missing = Path(td) / "nope.md"
warning: in the working copy of '.claude/scripts/codex-ask.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/judge.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/judge_axes.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/test_codex_ask.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/test_judge.py', LF will be replaced by CRLF the next time Git touches it

 succeeded in 127ms:
 M .claude/scripts/codex-ask.py
 M .claude/scripts/judge.py
 M .claude/scripts/judge_axes.py
 M .claude/scripts/test_codex_ask.py
 M .claude/scripts/test_judge.py
?? mypy.ini

diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..e84e344671eef1888c3c236ba5a1cde649dd454f
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -213,7 +213,9 @@
 
 
 _FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?:_log|log_info|log_warn|log_error|log_debug)\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..a6d847de451eee2112f9de7df079578471b3bca4
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

codex
The diff is within the scope fence and adds five named tests, matching the individual AC bullets. I’m running the new/changed judge and codex-ask suites first.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py -v --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
2026-04-26T18:49:36.104513Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 3 seconds
Output:
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.2, pluggy-1.6.0 -- C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
plugins: anyio-4.12.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 64 items

.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_simple_ok PASSED [  1%]
.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_with_tokens_trailer PASSED [  3%]
.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_multiline_response PASSED [  4%]
.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_empty_returns_none PASSED [  6%]
.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_only_whitespace_returns_none PASSED [  7%]
.claude/scripts/test_codex_ask.py::TestParseV117Legacy::test_parse_v117_legacy_with_sentinel PASSED [  9%]
.claude/scripts/test_codex_ask.py::TestParseV117Legacy::test_parse_v117_with_repeated_response PASSED [ 10%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_v125_returns_response PASSED [ 12%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_default_timeout_180 PASSED [ 14%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_strategic_timeout_900 PASSED [ 15%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_v117_returns_response PASSED [ 17%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_returncode_nonzero_returns_none PASSED [ 18%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_codex_not_in_path_returns_none PASSED [ 20%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_timeout_returns_none PASSED [ 21%]
.claude/scripts/test_codex_ask.py::TestRefactorContract::test_parse_function_exists PASSED [ 23%]
.claude/scripts/test_codex_ask.py::TestRefactorContract::test_parse_function_has_docstring_mentioning_both_versions PASSED [ 25%]
.claude/scripts/test_codex_ask.py::TestRefactorContract::test_ask_via_exec_delegates_to_parser PASSED [ 26%]
.claude/scripts/test_codex_ask.py::TestMainFlowUnchanged::test_main_flow_unchanged FAILED [ 28%]
.claude/scripts/test_judge.py::TestTestsPassed::test_all_pass PASSED     [ 29%]
.claude/scripts/test_judge.py::TestTestsPassed::test_empty_skipped PASSED [ 31%]
.claude/scripts/test_judge.py::TestTestsPassed::test_none_pass PASSED    [ 32%]
.claude/scripts/test_judge.py::TestTestsPassed::test_some_pass PASSED    [ 34%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_at_scale_scores_half PASSED [ 35%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_far_above_scale_still_nonzero PASSED [ 37%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_huge_diff_asymptotic PASSED [ 39%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_zero_added_scores_one PASSED [ 40%]
.claude/scripts/test_judge.py::TestDiffSize::test_empty_diff_max_score PASSED [ 42%]
.claude/scripts/test_judge.py::TestDiffSize::test_inverse_normalization PASSED [ 43%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_edge_no_new_functions PASSED [ 45%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_function_with_logger PASSED [ 46%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_function_without_logger PASSED [ 48%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_logging_coverage_counts_delegated_log_calls PASSED [ 50%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_mixed_functions PASSED [ 51%]
.claude/scripts/test_judge.py::TestLintClean::test_clean_file PASSED     [ 53%]
.claude/scripts/test_judge.py::TestLintClean::test_no_files_skipped PASSED [ 54%]
.claude/scripts/test_judge.py::TestLintClean::test_syntax_error PASSED   [ 56%]
.claude/scripts/test_judge.py::TestOptionalToolSkip::test_complexity_skipped_when_radon_absent PASSED [ 57%]
.claude/scripts/test_judge.py::TestOptionalToolSkip::test_score_type_check_active_when_mypy_ini_present PASSED [ 59%]
.claude/scripts/test_judge.py::TestOptionalToolSkip::test_type_check_skipped_when_mypy_absent PASSED [ 60%]
.claude/scripts/test_judge.py::TestWeightedAggregate::test_all_skipped_zero PASSED [ 62%]
.claude/scripts/test_judge.py::TestWeightedAggregate::test_skipped_ignored PASSED [ 64%]
.claude/scripts/test_judge.py::TestWeightedAggregate::test_weighted_correctness PASSED [ 65%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_claude_wins PASSED [ 67%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_codex_wins PASSED [ 68%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_tie_custom_delta PASSED [ 70%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_tie_within_delta PASSED [ 71%]
.claude/scripts/test_judge.py::TestVerdictSchema::test_rationale_cites_biggest_delta PASSED [ 73%]
.claude/scripts/test_judge.py::TestVerdictSchema::test_verdict_is_valid_json PASSED [ 75%]
.claude/scripts/test_judge.py::TestCLI::test_dry_run PASSED              [ 76%]
.claude/scripts/test_judge.py::TestCLI::test_help_exits_zero PASSED      [ 78%]
.claude/scripts/test_judge.py::TestCLI::test_help_mentions_auto_base PASSED [ 79%]
.claude/scripts/test_judge.py::TestCLI::test_malformed_task_exit_1 PASSED [ 81%]
.claude/scripts/test_judge.py::TestCLI::test_tie_threshold_default_is_0_03 PASSED [ 82%]
.claude/scripts/test_judge.py::TestStructuredLogging::test_json_formatter_shape PASSED [ 84%]
.claude/scripts/test_judge.py::TestEnsureUntrackedVisible::test_idempotent_no_untracked PASSED [ 85%]
.claude/scripts/test_judge.py::TestEnsureUntrackedVisible::test_never_raises_on_missing_git PASSED [ 87%]
.claude/scripts/test_judge.py::TestEnsureUntrackedVisible::test_registers_untracked_py PASSED [ 89%]
.claude/scripts/test_judge.py::TestDiffBaselineCommitted::test_committed_diff_visible_with_merge_base PASSED [ 90%]
.claude/scripts/test_judge.py::TestDiffBaselineUntracked::test_untracked_numstat_after_ensure PASSED [ 92%]
.claude/scripts/test_judge.py::TestResolveBase::test_cli_explicit_wins_over_sidecar PASSED [ 93%]
.claude/scripts/test_judge.py::TestResolveBase::test_head_fallback_in_non_git PASSED [ 95%]
.claude/scripts/test_judge.py::TestResolveBase::test_head_literal_passes_through_to_fallback PASSED [ 96%]
.claude/scripts/test_judge.py::TestResolveBase::test_merge_base_when_no_sidecar_and_auto PASSED [ 98%]
.claude/scripts/test_judge.py::TestResolveBase::test_sidecar_wins_over_auto_fallback PASSED [100%]

================================== FAILURES ===================================
E   TypeError: TestMainFlowUnchanged.test_main_flow_unchanged.<locals>.<lambda>() got an unexpected keyword argument 'strategic'
C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final\.claude\scripts\codex-ask.py:212: TypeError: TestMainFlowUnchanged.test_main_flow_unchanged.<locals>.<lambda>() got an unexpected keyword argument 'strategic'
============================== warnings summary ===============================
.claude\scripts\judge_axes.py:46
  C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final\.claude\scripts\judge_axes.py:46: PytestCollectionWarning: cannot collect test class 'TestRun' because it has a __init__ constructor (from: .claude/scripts/test_judge.py)
    @dataclass

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ===========================
FAILED .claude/scripts/test_codex_ask.py::TestMainFlowUnchanged::test_main_flow_unchanged
=================== 1 failed, 63 passed, 1 warning in 2.43s ===================

 exited 1 in 2969ms:
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.2, pluggy-1.6.0 -- C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
plugins: anyio-4.12.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 64 items

.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_simple_ok PASSED [  1%]
.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_with_tokens_trailer PASSED [  3%]
.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_multiline_response PASSED [  4%]
.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_empty_returns_none PASSED [  6%]
.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_only_whitespace_returns_none PASSED [  7%]
.claude/scripts/test_codex_ask.py::TestParseV117Legacy::test_parse_v117_legacy_with_sentinel PASSED [  9%]
.claude/scripts/test_codex_ask.py::TestParseV117Legacy::test_parse_v117_with_repeated_response PASSED [ 10%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_v125_returns_response PASSED [ 12%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_default_timeout_180 PASSED [ 14%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_strategic_timeout_900 PASSED [ 15%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_v117_returns_response PASSED [ 17%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_returncode_nonzero_returns_none PASSED [ 18%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_codex_not_in_path_returns_none PASSED [ 20%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_timeout_returns_none PASSED [ 21%]
.claude/scripts/test_codex_ask.py::TestRefactorContract::test_parse_function_exists PASSED [ 23%]
.claude/scripts/test_codex_ask.py::TestRefactorContract::test_parse_function_has_docstring_mentioning_both_versions PASSED [ 25%]
.claude/scripts/test_codex_ask.py::TestRefactorContract::test_ask_via_exec_delegates_to_parser PASSED [ 26%]
.claude/scripts/test_codex_ask.py::TestMainFlowUnchanged::test_main_flow_unchanged FAILED [ 28%]
.claude/scripts/test_judge.py::TestTestsPassed::test_all_pass PASSED     [ 29%]
.claude/scripts/test_judge.py::TestTestsPassed::test_empty_skipped PASSED [ 31%]
.claude/scripts/test_judge.py::TestTestsPassed::test_none_pass PASSED    [ 32%]
.claude/scripts/test_judge.py::TestTestsPassed::test_some_pass PASSED    [ 34%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_at_scale_scores_half PASSED [ 35%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_far_above_scale_still_nonzero PASSED [ 37%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_huge_diff_asymptotic PASSED [ 39%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_zero_added_scores_one PASSED [ 40%]
.claude/scripts/test_judge.py::TestDiffSize::test_empty_diff_max_score PASSED [ 42%]
.claude/scripts/test_judge.py::TestDiffSize::test_inverse_normalization PASSED [ 43%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_edge_no_new_functions PASSED [ 45%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_function_with_logger PASSED [ 46%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_function_without_logger PASSED [ 48%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_logging_coverage_counts_delegated_log_calls PASSED [ 50%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_mixed_functions PASSED [ 51%]
.claude/scripts/test_judge.py::TestLintClean::test_clean_file PASSED     [ 53%]
.claude/scripts/test_judge.py::TestLintClean::test_no_files_skipped PASSED [ 54%]
.claude/scripts/test_judge.py::TestLintClean::test_syntax_error PASSED   [ 56%]
.claude/scripts/test_judge.py::TestOptionalToolSkip::test_complexity_skipped_when_radon_absent PASSED [ 57%]
.claude/scripts/test_judge.py::TestOptionalToolSkip::test_score_type_check_active_when_mypy_ini_present PASSED [ 59%]
.claude/scripts/test_judge.py::TestOptionalToolSkip::test_type_check_skipped_when_mypy_absent PASSED [ 60%]
.claude/scripts/test_judge.py::TestWeightedAggregate::test_all_skipped_zero PASSED [ 62%]
.claude/scripts/test_judge.py::TestWeightedAggregate::test_skipped_ignored PASSED [ 64%]
.claude/scripts/test_judge.py::TestWeightedAggregate::test_weighted_correctness PASSED [ 65%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_claude_wins PASSED [ 67%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_codex_wins PASSED [ 68%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_tie_custom_delta PASSED [ 70%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_tie_within_delta PASSED [ 71%]
.claude/scripts/test_judge.py::TestVerdictSchema::test_rationale_cites_biggest_delta PASSED [ 73%]
.claude/scripts/test_judge.py::TestVerdictSchema::test_verdict_is_valid_json PASSED [ 75%]
.claude/scripts/test_judge.py::TestCLI::test_dry_run PASSED              [ 76%]
.claude/scripts/test_judge.py::TestCLI::test_help_exits_zero PASSED      [ 78%]
.claude/scripts/test_judge.py::TestCLI::test_help_mentions_auto_base PASSED [ 79%]
.claude/scripts/test_judge.py::TestCLI::test_malformed_task_exit_1 PASSED [ 81%]
.claude/scripts/test_judge.py::TestCLI::test_tie_threshold_default_is_0_03 PASSED [ 82%]
.claude/scripts/test_judge.py::TestStructuredLogging::test_json_formatter_shape PASSED [ 84%]
.claude/scripts/test_judge.py::TestEnsureUntrackedVisible::test_idempotent_no_untracked PASSED [ 85%]
.claude/scripts/test_judge.py::TestEnsureUntrackedVisible::test_never_raises_on_missing_git PASSED [ 87%]
.claude/scripts/test_judge.py::TestEnsureUntrackedVisible::test_registers_untracked_py PASSED [ 89%]
.claude/scripts/test_judge.py::TestDiffBaselineCommitted::test_committed_diff_visible_with_merge_base PASSED [ 90%]
.claude/scripts/test_judge.py::TestDiffBaselineUntracked::test_untracked_numstat_after_ensure PASSED [ 92%]
.claude/scripts/test_judge.py::TestResolveBase::test_cli_explicit_wins_over_sidecar PASSED [ 93%]
.claude/scripts/test_judge.py::TestResolveBase::test_head_fallback_in_non_git PASSED [ 95%]
.claude/scripts/test_judge.py::TestResolveBase::test_head_literal_passes_through_to_fallback PASSED [ 96%]
.claude/scripts/test_judge.py::TestResolveBase::test_merge_base_when_no_sidecar_and_auto PASSED [ 98%]
.claude/scripts/test_judge.py::TestResolveBase::test_sidecar_wins_over_auto_fallback PASSED [100%]

================================== FAILURES ===================================
E   TypeError: TestMainFlowUnchanged.test_main_flow_unchanged.<locals>.<lambda>() got an unexpected keyword argument 'strategic'
C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final\.claude\scripts\codex-ask.py:212: TypeError: TestMainFlowUnchanged.test_main_flow_unchanged.<locals>.<lambda>() got an unexpected keyword argument 'strategic'
============================== warnings summary ===============================
.claude\scripts\judge_axes.py:46
  C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final\.claude\scripts\judge_axes.py:46: PytestCollectionWarning: cannot collect test class 'TestRun' because it has a __init__ constructor (from: .claude/scripts/test_judge.py)
    @dataclass

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ===========================
FAILED .claude/scripts/test_codex_ask.py::TestMainFlowUnchanged::test_main_flow_unchanged
=================== 1 failed, 63 passed, 1 warning in 2.43s ===================

diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..e84e344671eef1888c3c236ba5a1cde649dd454f
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -213,7 +213,9 @@
 
 
 _FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?:_log|log_info|log_warn|log_error|log_debug)\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..a6d847de451eee2112f9de7df079578471b3bca4
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

codex
One existing `codex-ask` test failed because its monkeypatched fallback lambda did not accept the new keyword argument. The production path is behaving as expected; I’m updating that test double to match the new signature.
apply patch
patch: completed
C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final\.claude\scripts\test_codex_ask.py
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..e84e344671eef1888c3c236ba5a1cde649dd454f
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -213,7 +213,9 @@
 
 
 _FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?:_log|log_info|log_warn|log_error|log_debug)\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..e84e344671eef1888c3c236ba5a1cde649dd454f
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -213,7 +213,9 @@
 
 
 _FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?:_log|log_info|log_warn|log_error|log_debug)\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

codex
The test double is aligned now, so I’m rerunning the focused suites before moving on to the required parse and regression commands.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py -v --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 3300ms:
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.2, pluggy-1.6.0 -- C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
plugins: anyio-4.12.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 64 items

.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_simple_ok PASSED [  1%]
.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_with_tokens_trailer PASSED [  3%]
.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_multiline_response PASSED [  4%]
.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_empty_returns_none PASSED [  6%]
.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_only_whitespace_returns_none PASSED [  7%]
.claude/scripts/test_codex_ask.py::TestParseV117Legacy::test_parse_v117_legacy_with_sentinel PASSED [  9%]
.claude/scripts/test_codex_ask.py::TestParseV117Legacy::test_parse_v117_with_repeated_response PASSED [ 10%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_v125_returns_response PASSED [ 12%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_default_timeout_180 PASSED [ 14%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_strategic_timeout_900 PASSED [ 15%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_v117_returns_response PASSED [ 17%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_returncode_nonzero_returns_none PASSED [ 18%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_codex_not_in_path_returns_none PASSED [ 20%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_timeout_returns_none PASSED [ 21%]
.claude/scripts/test_codex_ask.py::TestRefactorContract::test_parse_function_exists PASSED [ 23%]
.claude/scripts/test_codex_ask.py::TestRefactorContract::test_parse_function_has_docstring_mentioning_both_versions PASSED [ 25%]
.claude/scripts/test_codex_ask.py::TestRefactorContract::test_ask_via_exec_delegates_to_parser PASSED [ 26%]
.claude/scripts/test_codex_ask.py::TestMainFlowUnchanged::test_main_flow_unchanged PASSED [ 28%]
.claude/scripts/test_judge.py::TestTestsPassed::test_all_pass PASSED     [ 29%]
.claude/scripts/test_judge.py::TestTestsPassed::test_empty_skipped PASSED [ 31%]
.claude/scripts/test_judge.py::TestTestsPassed::test_none_pass PASSED    [ 32%]
.claude/scripts/test_judge.py::TestTestsPassed::test_some_pass PASSED    [ 34%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_at_scale_scores_half PASSED [ 35%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_far_above_scale_still_nonzero PASSED [ 37%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_huge_diff_asymptotic PASSED [ 39%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_zero_added_scores_one PASSED [ 40%]
.claude/scripts/test_judge.py::TestDiffSize::test_empty_diff_max_score PASSED [ 42%]
.claude/scripts/test_judge.py::TestDiffSize::test_inverse_normalization PASSED [ 43%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_edge_no_new_functions PASSED [ 45%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_function_with_logger PASSED [ 46%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_function_without_logger PASSED [ 48%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_logging_coverage_counts_delegated_log_calls PASSED [ 50%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_mixed_functions PASSED [ 51%]
.claude/scripts/test_judge.py::TestLintClean::test_clean_file PASSED     [ 53%]
.claude/scripts/test_judge.py::TestLintClean::test_no_files_skipped PASSED [ 54%]
.claude/scripts/test_judge.py::TestLintClean::test_syntax_error PASSED   [ 56%]
.claude/scripts/test_judge.py::TestOptionalToolSkip::test_complexity_skipped_when_radon_absent PASSED [ 57%]
.claude/scripts/test_judge.py::TestOptionalToolSkip::test_score_type_check_active_when_mypy_ini_present PASSED [ 59%]
.claude/scripts/test_judge.py::TestOptionalToolSkip::test_type_check_skipped_when_mypy_absent PASSED [ 60%]
.claude/scripts/test_judge.py::TestWeightedAggregate::test_all_skipped_zero PASSED [ 62%]
.claude/scripts/test_judge.py::TestWeightedAggregate::test_skipped_ignored PASSED [ 64%]
.claude/scripts/test_judge.py::TestWeightedAggregate::test_weighted_correctness PASSED [ 65%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_claude_wins PASSED [ 67%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_codex_wins PASSED [ 68%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_tie_custom_delta PASSED [ 70%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_tie_within_delta PASSED [ 71%]
.claude/scripts/test_judge.py::TestVerdictSchema::test_rationale_cites_biggest_delta PASSED [ 73%]
.claude/scripts/test_judge.py::TestVerdictSchema::test_verdict_is_valid_json PASSED [ 75%]
.claude/scripts/test_judge.py::TestCLI::test_dry_run PASSED              [ 76%]
.claude/scripts/test_judge.py::TestCLI::test_help_exits_zero PASSED      [ 78%]
.claude/scripts/test_judge.py::TestCLI::test_help_mentions_auto_base PASSED [ 79%]
.claude/scripts/test_judge.py::TestCLI::test_malformed_task_exit_1 PASSED [ 81%]
.claude/scripts/test_judge.py::TestCLI::test_tie_threshold_default_is_0_03 PASSED [ 82%]
.claude/scripts/test_judge.py::TestStructuredLogging::test_json_formatter_shape PASSED [ 84%]
.claude/scripts/test_judge.py::TestEnsureUntrackedVisible::test_idempotent_no_untracked PASSED [ 85%]
.claude/scripts/test_judge.py::TestEnsureUntrackedVisible::test_never_raises_on_missing_git PASSED [ 87%]
.claude/scripts/test_judge.py::TestEnsureUntrackedVisible::test_registers_untracked_py PASSED [ 89%]
.claude/scripts/test_judge.py::TestDiffBaselineCommitted::test_committed_diff_visible_with_merge_base PASSED [ 90%]
.claude/scripts/test_judge.py::TestDiffBaselineUntracked::test_untracked_numstat_after_ensure PASSED [ 92%]
.claude/scripts/test_judge.py::TestResolveBase::test_cli_explicit_wins_over_sidecar PASSED [ 93%]
.claude/scripts/test_judge.py::TestResolveBase::test_head_fallback_in_non_git PASSED [ 95%]
.claude/scripts/test_judge.py::TestResolveBase::test_head_literal_passes_through_to_fallback PASSED [ 96%]
.claude/scripts/test_judge.py::TestResolveBase::test_merge_base_when_no_sidecar_and_auto PASSED [ 98%]
.claude/scripts/test_judge.py::TestResolveBase::test_sidecar_wins_over_auto_fallback PASSED [100%]

============================== warnings summary ===============================
.claude\scripts\judge_axes.py:46
  C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final\.claude\scripts\judge_axes.py:46: PytestCollectionWarning: cannot collect test class 'TestRun' because it has a __init__ constructor (from: .claude/scripts/test_judge.py)
    @dataclass

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 64 passed, 1 warning in 2.65s ========================

diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..e84e344671eef1888c3c236ba5a1cde649dd454f
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -213,7 +213,9 @@
 
 
 _FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?:_log|log_info|log_warn|log_error|log_debug)\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

codex
The focused suites pass: 64 tests. Next I’m verifying the new root `mypy.ini` parses exactly as required.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "python -c \"import configparser; c=configparser.ConfigParser(); c.read('mypy.ini'); assert 'mypy' in c\"" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 159ms:
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..e84e344671eef1888c3c236ba5a1cde649dd454f
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -213,7 +213,9 @@
 
 
 _FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?:_log|log_info|log_warn|log_error|log_debug)\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

codex
The INI parse check passed with no output, which is expected for the assertion command. I’m running the broader regression set now.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_spawn_agent.py .claude/scripts/test_determinism_chaos.py .claude/scripts/test_archive_active_context.py .claude/scripts/test_generate_changelog.py .claude/scripts/test_sync_template_to_target.py .claude/scripts/test_verify_codex_auth.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 8223ms:
........................................................................ [ 28%]
........................................................................ [ 56%]
........................................................................ [ 84%]
........................................                                 [100%]
256 passed in 7.62s

diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..e84e344671eef1888c3c236ba5a1cde649dd454f
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -213,7 +213,9 @@
 
 
 _FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?:_log|log_info|log_warn|log_error|log_debug)\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

codex
The broad regression command passed, currently 256 tests in this checkout. I’m running the selftest next; after that I’ll run the live attack matrix separately because AC-6 calls it out even though it was included in the regression command.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python .claude/scripts/dual-teams-selftest.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 727ms:
[PASS] preflight-clean-with-sentinel-V1                     (59 ms)
[PASS] preflight-clean-with-sentinel-V2                     (58 ms)
[PASS] is_dual_teams_worktree-true-on-V1                    ( 1 ms)
[PASS] is_dual_teams_worktree-true-on-V2                    ( 1 ms)
[PASS] judge-axes-sees-claude-committed-py                  (27 ms)
[PASS] judge-axes-sees-codex-untracked-py                   (46 ms)
selftest: 6 checks, 6 passed, 0 failed (543 ms)
{"json_output": false, "keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: main", "ts": "2026-04-26T18:50:30.684512+00:00"}
{"keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: run_selftest", "ts": "2026-04-26T18:50:30.684512+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: setup_transient_repo", "tmpdir": "C:\\Users\\Lenovo\\AppData\\Local\\Temp\\dual-teams-selftest-g5atgcyr", "ts": "2026-04-26T18:50:30.685517+00:00"}
{"base_sha": "f67dfa54af48b24235212e46f5f06d1dd2353277", "duration_ms": 249, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: setup_transient_repo", "ts": "2026-04-26T18:50:30.934640+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: load_integrations", "project_root": "C:\\Bots\\Migrator bots\\claude-project-template-update\\worktrees\\criterion-upgrade-z32\\codex\\task-Z32-judge-quality-final", "ts": "2026-04-26T18:50:30.934640+00:00"}
{"duration_ms": 5, "failures": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: load_integrations", "ts": "2026-04-26T18:50:30.940638+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: build_results", "ts": "2026-04-26T18:50:30.940638+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T18:50:30.940638+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "detail": "git status --porcelain empty", "duration_ms": 59, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T18:50:30.999814+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T18:50:30.999814+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "detail": "git status --porcelain empty", "duration_ms": 58, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T18:50:31.057130+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T18:50:31.057130+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T18:50:31.058130+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T18:50:31.058130+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T18:50:31.058130+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T18:50:31.119607+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "detail": "saw claude_probe.py", "duration_ms": 27, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T18:50:31.147453+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T18:50:31.147453+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "detail": "saw codex_probe.py", "duration_ms": 46, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T18:50:31.193328+00:00"}
{"checks": 6, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: build_results", "ts": "2026-04-26T18:50:31.193328+00:00"}
{"checks": 6, "duration_ms": 543, "failed": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: run_selftest", "passed": 6, "ts": "2026-04-26T18:50:31.228189+00:00"}
{"exit_code": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: main", "ts": "2026-04-26T18:50:31.228189+00:00"}

diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..e84e344671eef1888c3c236ba5a1cde649dd454f
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -213,7 +213,9 @@
 
 
 _FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?:_log|log_info|log_warn|log_error|log_debug)\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

codex
The selftest passed 6/6. I’m running the live attack matrix on its own now to capture the 25/25 evidence separately.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'pytest .claude/hooks/test_enforcer_live_attacks.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 2211ms:
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.2, pluggy-1.6.0
rootdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
plugins: anyio-4.12.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 25 items

.claude\hooks\test_enforcer_live_attacks.py .........................    [100%]

============================= 25 passed in 1.56s ==============================

diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..e84e344671eef1888c3c236ba5a1cde649dd454f
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -213,7 +213,9 @@
 
 
 _FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?:_log|log_info|log_warn|log_error|log_debug)\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

codex
The live attack matrix passed 25/25. The task also includes a fuller AC-5 regression command in the acceptance criteria, so I’m running that exact combined suite once before committing.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/scripts/test_spawn_agent.py .claude/scripts/test_determinism_chaos.py .claude/scripts/test_archive_active_context.py .claude/scripts/test_generate_changelog.py .claude/scripts/test_sync_template_to_target.py .claude/scripts/test_verify_codex_auth.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 9706ms:
........................................................................ [ 22%]
........................................................................ [ 45%]
........................................................................ [ 67%]
........................................................................ [ 90%]
................................                                         [100%]
============================== warnings summary ===============================
.claude\scripts\judge_axes.py:46
  C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final\.claude\scripts\judge_axes.py:46: PytestCollectionWarning: cannot collect test class 'TestRun' because it has a __init__ constructor (from: .claude/scripts/test_judge.py)
    @dataclass

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
320 passed, 1 warning in 9.18s

diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..e84e344671eef1888c3c236ba5a1cde649dd454f
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -213,7 +213,9 @@
 
 
 _FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?:_log|log_info|log_warn|log_error|log_debug)\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

codex
The required suites are green, including the exact combined AC-5 command at 320 tests. I’m making one small regex tightening so delegated logging matches the named helper calls as helpers, not arbitrary substrings.
apply patch
patch: completed
C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final\.claude\scripts\judge_axes.py
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

codex
Because that regex tightening touched production code, I’m rerunning the required commands on the final diff rather than relying on the previous run.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py -v --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 2798ms:
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.2, pluggy-1.6.0 -- C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
plugins: anyio-4.12.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 64 items

.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_simple_ok PASSED [  1%]
.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_with_tokens_trailer PASSED [  3%]
.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_multiline_response PASSED [  4%]
.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_empty_returns_none PASSED [  6%]
.claude/scripts/test_codex_ask.py::TestParseV125Format::test_parse_v125_only_whitespace_returns_none PASSED [  7%]
.claude/scripts/test_codex_ask.py::TestParseV117Legacy::test_parse_v117_legacy_with_sentinel PASSED [  9%]
.claude/scripts/test_codex_ask.py::TestParseV117Legacy::test_parse_v117_with_repeated_response PASSED [ 10%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_v125_returns_response PASSED [ 12%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_default_timeout_180 PASSED [ 14%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_strategic_timeout_900 PASSED [ 15%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_v117_returns_response PASSED [ 17%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_returncode_nonzero_returns_none PASSED [ 18%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_codex_not_in_path_returns_none PASSED [ 20%]
.claude/scripts/test_codex_ask.py::TestAskViaExecIntegration::test_ask_via_exec_timeout_returns_none PASSED [ 21%]
.claude/scripts/test_codex_ask.py::TestRefactorContract::test_parse_function_exists PASSED [ 23%]
.claude/scripts/test_codex_ask.py::TestRefactorContract::test_parse_function_has_docstring_mentioning_both_versions PASSED [ 25%]
.claude/scripts/test_codex_ask.py::TestRefactorContract::test_ask_via_exec_delegates_to_parser PASSED [ 26%]
.claude/scripts/test_codex_ask.py::TestMainFlowUnchanged::test_main_flow_unchanged PASSED [ 28%]
.claude/scripts/test_judge.py::TestTestsPassed::test_all_pass PASSED     [ 29%]
.claude/scripts/test_judge.py::TestTestsPassed::test_empty_skipped PASSED [ 31%]
.claude/scripts/test_judge.py::TestTestsPassed::test_none_pass PASSED    [ 32%]
.claude/scripts/test_judge.py::TestTestsPassed::test_some_pass PASSED    [ 34%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_at_scale_scores_half PASSED [ 35%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_far_above_scale_still_nonzero PASSED [ 37%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_huge_diff_asymptotic PASSED [ 39%]
.claude/scripts/test_judge.py::TestDiffSize::test_diff_size_zero_added_scores_one PASSED [ 40%]
.claude/scripts/test_judge.py::TestDiffSize::test_empty_diff_max_score PASSED [ 42%]
.claude/scripts/test_judge.py::TestDiffSize::test_inverse_normalization PASSED [ 43%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_edge_no_new_functions PASSED [ 45%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_function_with_logger PASSED [ 46%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_function_without_logger PASSED [ 48%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_logging_coverage_counts_delegated_log_calls PASSED [ 50%]
.claude/scripts/test_judge.py::TestLoggingCoverage::test_mixed_functions PASSED [ 51%]
.claude/scripts/test_judge.py::TestLintClean::test_clean_file PASSED     [ 53%]
.claude/scripts/test_judge.py::TestLintClean::test_no_files_skipped PASSED [ 54%]
.claude/scripts/test_judge.py::TestLintClean::test_syntax_error PASSED   [ 56%]
.claude/scripts/test_judge.py::TestOptionalToolSkip::test_complexity_skipped_when_radon_absent PASSED [ 57%]
.claude/scripts/test_judge.py::TestOptionalToolSkip::test_score_type_check_active_when_mypy_ini_present PASSED [ 59%]
.claude/scripts/test_judge.py::TestOptionalToolSkip::test_type_check_skipped_when_mypy_absent PASSED [ 60%]
.claude/scripts/test_judge.py::TestWeightedAggregate::test_all_skipped_zero PASSED [ 62%]
.claude/scripts/test_judge.py::TestWeightedAggregate::test_skipped_ignored PASSED [ 64%]
.claude/scripts/test_judge.py::TestWeightedAggregate::test_weighted_correctness PASSED [ 65%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_claude_wins PASSED [ 67%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_codex_wins PASSED [ 68%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_tie_custom_delta PASSED [ 70%]
.claude/scripts/test_judge.py::TestWinnerDecision::test_tie_within_delta PASSED [ 71%]
.claude/scripts/test_judge.py::TestVerdictSchema::test_rationale_cites_biggest_delta PASSED [ 73%]
.claude/scripts/test_judge.py::TestVerdictSchema::test_verdict_is_valid_json PASSED [ 75%]
.claude/scripts/test_judge.py::TestCLI::test_dry_run PASSED              [ 76%]
.claude/scripts/test_judge.py::TestCLI::test_help_exits_zero PASSED      [ 78%]
.claude/scripts/test_judge.py::TestCLI::test_help_mentions_auto_base PASSED [ 79%]
.claude/scripts/test_judge.py::TestCLI::test_malformed_task_exit_1 PASSED [ 81%]
.claude/scripts/test_judge.py::TestCLI::test_tie_threshold_default_is_0_03 PASSED [ 82%]
.claude/scripts/test_judge.py::TestStructuredLogging::test_json_formatter_shape PASSED [ 84%]
.claude/scripts/test_judge.py::TestEnsureUntrackedVisible::test_idempotent_no_untracked PASSED [ 85%]
.claude/scripts/test_judge.py::TestEnsureUntrackedVisible::test_never_raises_on_missing_git PASSED [ 87%]
.claude/scripts/test_judge.py::TestEnsureUntrackedVisible::test_registers_untracked_py PASSED [ 89%]
.claude/scripts/test_judge.py::TestDiffBaselineCommitted::test_committed_diff_visible_with_merge_base PASSED [ 90%]
.claude/scripts/test_judge.py::TestDiffBaselineUntracked::test_untracked_numstat_after_ensure PASSED [ 92%]
.claude/scripts/test_judge.py::TestResolveBase::test_cli_explicit_wins_over_sidecar PASSED [ 93%]
.claude/scripts/test_judge.py::TestResolveBase::test_head_fallback_in_non_git PASSED [ 95%]
.claude/scripts/test_judge.py::TestResolveBase::test_head_literal_passes_through_to_fallback PASSED [ 96%]
.claude/scripts/test_judge.py::TestResolveBase::test_merge_base_when_no_sidecar_and_auto PASSED [ 98%]
.claude/scripts/test_judge.py::TestResolveBase::test_sidecar_wins_over_auto_fallback PASSED [100%]

============================== warnings summary ===============================
.claude\scripts\judge_axes.py:46
  C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final\.claude\scripts\judge_axes.py:46: PytestCollectionWarning: cannot collect test class 'TestRun' because it has a __init__ constructor (from: .claude/scripts/test_judge.py)
    @dataclass

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 64 passed, 1 warning in 2.32s ========================

diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "python -c \"import configparser; c=configparser.ConfigParser(); c.read('mypy.ini'); assert 'mypy' in c\"" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python .claude/scripts/dual-teams-selftest.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 138ms:
 succeeded in 749ms:
[PASS] preflight-clean-with-sentinel-V1                     (57 ms)
[PASS] preflight-clean-with-sentinel-V2                     (55 ms)
[PASS] is_dual_teams_worktree-true-on-V1                    ( 1 ms)
[PASS] is_dual_teams_worktree-true-on-V2                    ( 1 ms)
[PASS] judge-axes-sees-claude-committed-py                  (35 ms)
[PASS] judge-axes-sees-codex-untracked-py                   (50 ms)
selftest: 6 checks, 6 passed, 0 failed (568 ms)
{"json_output": false, "keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: main", "ts": "2026-04-26T18:51:50.603462+00:00"}
{"keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: run_selftest", "ts": "2026-04-26T18:51:50.603462+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: setup_transient_repo", "tmpdir": "C:\\Users\\Lenovo\\AppData\\Local\\Temp\\dual-teams-selftest-7tjbz2ro", "ts": "2026-04-26T18:51:50.604477+00:00"}
{"base_sha": "941ae1e2c402be5a0482544d1c95b70f6120f475", "duration_ms": 258, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: setup_transient_repo", "ts": "2026-04-26T18:51:50.861797+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: load_integrations", "project_root": "C:\\Bots\\Migrator bots\\claude-project-template-update\\worktrees\\criterion-upgrade-z32\\codex\\task-Z32-judge-quality-final", "ts": "2026-04-26T18:51:50.861797+00:00"}
{"duration_ms": 5, "failures": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: load_integrations", "ts": "2026-04-26T18:51:50.866801+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: build_results", "ts": "2026-04-26T18:51:50.867803+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T18:51:50.867803+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "detail": "git status --porcelain empty", "duration_ms": 57, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T18:51:50.924789+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T18:51:50.924789+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "detail": "git status --porcelain empty", "duration_ms": 55, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T18:51:50.979442+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T18:51:50.979442+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T18:51:50.979442+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T18:51:50.979442+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T18:51:50.979442+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T18:51:51.040201+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "detail": "saw claude_probe.py", "duration_ms": 35, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T18:51:51.074718+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T18:51:51.074718+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "detail": "saw codex_probe.py", "duration_ms": 50, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T18:51:51.125196+00:00"}
{"checks": 6, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: build_results", "ts": "2026-04-26T18:51:51.125196+00:00"}
{"checks": 6, "duration_ms": 568, "failed": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: run_selftest", "passed": 6, "ts": "2026-04-26T18:51:51.171220+00:00"}
{"exit_code": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: main", "ts": "2026-04-26T18:51:51.171220+00:00"}

diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

codex
The INI assertion is still clean and selftest is 6/6 on the final diff. I’m rerunning the regression command now.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_spawn_agent.py .claude/scripts/test_determinism_chaos.py .claude/scripts/test_archive_active_context.py .claude/scripts/test_generate_changelog.py .claude/scripts/test_sync_template_to_target.py .claude/scripts/test_verify_codex_auth.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 8178ms:
........................................................................ [ 28%]
........................................................................ [ 56%]
........................................................................ [ 84%]
........................................                                 [100%]
256 passed in 7.63s

diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

codex
The listed regression command passed again: 256 tests. I’m running the explicit live attack matrix and then the combined AC-5 suite one final time.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'pytest .claude/hooks/test_enforcer_live_attacks.py' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 1933ms:
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.2, pluggy-1.6.0
rootdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
plugins: anyio-4.12.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 25 items

.claude\hooks\test_enforcer_live_attacks.py .........................    [100%]

============================= 25 passed in 1.48s ==============================

diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/scripts/test_spawn_agent.py .claude/scripts/test_determinism_chaos.py .claude/scripts/test_archive_active_context.py .claude/scripts/test_generate_changelog.py .claude/scripts/test_sync_template_to_target.py .claude/scripts/test_verify_codex_auth.py .claude/hooks/test_enforcer_live_attacks.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 9727ms:
........................................................................ [ 22%]
........................................................................ [ 45%]
........................................................................ [ 67%]
........................................................................ [ 90%]
................................                                         [100%]
============================== warnings summary ===============================
.claude\scripts\judge_axes.py:46
  C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final\.claude\scripts\judge_axes.py:46: PytestCollectionWarning: cannot collect test class 'TestRun' because it has a __init__ constructor (from: .claude/scripts/test_judge.py)
    @dataclass

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
320 passed, 1 warning in 9.23s

diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

codex
All required checks are green on the final diff. I’m doing a last working-tree review and whitespace check, then I’ll commit the scoped changes for the requested final SHA.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff --check' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff --numstat -- .claude/scripts/codex-ask.py .claude/scripts/test_codex_ask.py .claude/scripts/judge.py .claude/scripts/judge_axes.py .claude/scripts/test_judge.py mypy.ini' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 143ms:
warning: in the working copy of '.claude/scripts/codex-ask.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/judge.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/judge_axes.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/test_codex_ask.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/test_judge.py', LF will be replaced by CRLF the next time Git touches it

 succeeded in 140ms:
16	7	.claude/scripts/codex-ask.py
3	1	.claude/scripts/judge.py
14	3	.claude/scripts/judge_axes.py
19	2	.claude/scripts/test_codex_ask.py
38	0	.claude/scripts/test_judge.py
warning: in the working copy of '.claude/scripts/codex-ask.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/judge.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/judge_axes.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/test_codex_ask.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/test_judge.py', LF will be replaced by CRLF the next time Git touches it

 succeeded in 131ms:
 M .claude/scripts/codex-ask.py
 M .claude/scripts/judge.py
 M .claude/scripts/judge_axes.py
 M .claude/scripts/test_codex_ask.py
 M .claude/scripts/test_judge.py
?? mypy.ini

diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

codex
`git diff --check` is clean aside from the repository’s normal LF/CRLF warning. I’m staging only the six scoped files and committing them now.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git add -- .claude/scripts/codex-ask.py .claude/scripts/test_codex_ask.py .claude/scripts/judge.py .claude/scripts/judge_axes.py .claude/scripts/test_judge.py mypy.ini; git commit -m "Improve judge quality axes"' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 756ms:
[codex-wave/task-Z32-judge-quality-final 6b10ed1] Improve judge quality axes
 6 files changed, 95 insertions(+), 13 deletions(-)
 create mode 100644 mypy.ini
warning: in the working copy of '.claude/scripts/codex-ask.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/judge.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/judge_axes.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/test_codex_ask.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/scripts/test_judge.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'mypy.ini', LF will be replaced by CRLF the next time Git touches it
Memory NOT updated. Adding auto-generated entry...
Auto-entry added to memory

diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

codex
The commit succeeded at `6b10ed1`. The commit hook reported that it auto-updated memory after the commit, so I’m checking the tree now to ensure no out-of-scope uncommitted file is left behind.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git show --stat --oneline --name-only HEAD' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 127ms:
6b10ed1 Improve judge quality axes
.claude/scripts/codex-ask.py
.claude/scripts/judge.py
.claude/scripts/judge_axes.py
.claude/scripts/test_codex_ask.py
.claude/scripts/test_judge.py
mypy.ini

 succeeded in 132ms:
 M .claude/memory/activeContext.md

diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff -- .claude/memory/activeContext.md' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 128ms:
diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index df1de9d..c690399 100644
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,6 +620,11 @@ pipeline-checkpoint-PLAN в†’ IMPLEMENT_WAVE_1 в†’ IMPLEMENT_WAVE_2 в
 
 ## Auto-Generated Summaries
 
+### 2026-04-26 21:52 (commit `6b10ed1`)
+**Message:** Improve judge quality axes
+**Files:** 6
+
+
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
warning: in the working copy of '.claude/memory/activeContext.md', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

codex
The only out-of-scope dirt is the post-commit auto memory entry. I’m removing that generated entry so the worktree stays scoped to the task files.
apply patch
patch: completed
C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final\.claude\memory\activeContext.md
diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index c6903997a2cb0956a3fc8c55113ab50800ce959f..f6648c0c979deed6e5839b64e92561fc290c344c
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,11 +620,6 @@
 
 ## Auto-Generated Summaries
 
-### 2026-04-26 21:52 (commit `6b10ed1`)
-**Message:** Improve judge quality axes
-**Files:** 6
-
-
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
@@ -1001,7 +996,6 @@
 
 **Architectural status:**
 Always-Dual protocol fully operational: CLAUDE.md + AGENTS.md + enforcer hook + codex-gate bypass + DUAL_TEAMS phase mode + dual-teams-spawn.py + codex-inline-dual.py + judge.py + stability layer + warm pool + streaming+cherry-pick docs.
-
 
 
 
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index c6903997a2cb0956a3fc8c55113ab50800ce959f..f6648c0c979deed6e5839b64e92561fc290c344c
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,11 +620,6 @@
 
 ## Auto-Generated Summaries
 
-### 2026-04-26 21:52 (commit `6b10ed1`)
-**Message:** Improve judge quality axes
-**Files:** 6
-
-
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
@@ -1001,7 +996,6 @@
 
 **Architectural status:**
 Always-Dual protocol fully operational: CLAUDE.md + AGENTS.md + enforcer hook + codex-gate bypass + DUAL_TEAMS phase mode + dual-teams-spawn.py + codex-inline-dual.py + judge.py + stability layer + warm pool + streaming+cherry-pick docs.
-
 
 
 
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 129ms:
 M .claude/memory/activeContext.md

diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index c6903997a2cb0956a3fc8c55113ab50800ce959f..f6648c0c979deed6e5839b64e92561fc290c344c
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,11 +620,6 @@
 
 ## Auto-Generated Summaries
 
-### 2026-04-26 21:52 (commit `6b10ed1`)
-**Message:** Improve judge quality axes
-**Files:** 6
-
-
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
@@ -1001,7 +996,6 @@
 
 **Architectural status:**
 Always-Dual protocol fully operational: CLAUDE.md + AGENTS.md + enforcer hook + codex-gate bypass + DUAL_TEAMS phase mode + dual-teams-spawn.py + codex-inline-dual.py + judge.py + stability layer + warm pool + streaming+cherry-pick docs.
-
 
 
 
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff -- .claude/memory/activeContext.md' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 117ms:
diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index df1de9d..f6648c0 100644
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -1002,4 +1002,3 @@ Always-Dual protocol fully operational: CLAUDE.md + AGENTS.md + enforcer hook +
 
 
 
-
warning: in the working copy of '.claude/memory/activeContext.md', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index c6903997a2cb0956a3fc8c55113ab50800ce959f..f6648c0c979deed6e5839b64e92561fc290c344c
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,11 +620,6 @@
 
 ## Auto-Generated Summaries
 
-### 2026-04-26 21:52 (commit `6b10ed1`)
-**Message:** Improve judge quality axes
-**Files:** 6
-
-
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
@@ -1001,7 +996,6 @@
 
 **Architectural status:**
 Always-Dual protocol fully operational: CLAUDE.md + AGENTS.md + enforcer hook + codex-gate bypass + DUAL_TEAMS phase mode + dual-teams-spawn.py + codex-inline-dual.py + judge.py + stability layer + warm pool + streaming+cherry-pick docs.
-
 
 
 
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Tail 8 -LiteralPath .claude/memory/activeContext.md | ForEach-Object { '[' + "'$_ + '"']' }" in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 140ms:
[**Architectural status:**]
[Always-Dual protocol fully operational: CLAUDE.md + AGENTS.md + enforcer hook + codex-gate bypass + DUAL_TEAMS phase mode + dual-teams-spawn.py + codex-inline-dual.py + judge.py + stability layer + warm pool + streaming+cherry-pick docs.]
[]
[]
[]
[]
[]
[]

diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index c6903997a2cb0956a3fc8c55113ab50800ce959f..f6648c0c979deed6e5839b64e92561fc290c344c
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,11 +620,6 @@
 
 ## Auto-Generated Summaries
 
-### 2026-04-26 21:52 (commit `6b10ed1`)
-**Message:** Improve judge quality axes
-**Files:** 6
-
-
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
@@ -1001,7 +996,6 @@
 
 **Architectural status:**
 Always-Dual protocol fully operational: CLAUDE.md + AGENTS.md + enforcer hook + codex-gate bypass + DUAL_TEAMS phase mode + dual-teams-spawn.py + codex-inline-dual.py + judge.py + stability layer + warm pool + streaming+cherry-pick docs.
-
 
 
 
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

apply patch
patch: completed
C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final\.claude\memory\activeContext.md
diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index c6903997a2cb0956a3fc8c55113ab50800ce959f..f6648c0c979deed6e5839b64e92561fc290c344c
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,11 +620,6 @@
 
 ## Auto-Generated Summaries
 
-### 2026-04-26 21:52 (commit `6b10ed1`)
-**Message:** Improve judge quality axes
-**Files:** 6
-
-
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
@@ -1001,7 +996,6 @@
 
 **Architectural status:**
 Always-Dual protocol fully operational: CLAUDE.md + AGENTS.md + enforcer hook + codex-gate bypass + DUAL_TEAMS phase mode + dual-teams-spawn.py + codex-inline-dual.py + judge.py + stability layer + warm pool + streaming+cherry-pick docs.
-
 
 
 
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index c6903997a2cb0956a3fc8c55113ab50800ce959f..f6648c0c979deed6e5839b64e92561fc290c344c
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,11 +620,6 @@
 
 ## Auto-Generated Summaries
 
-### 2026-04-26 21:52 (commit `6b10ed1`)
-**Message:** Improve judge quality axes
-**Files:** 6
-
-
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
@@ -1001,7 +996,6 @@
 
 **Architectural status:**
 Always-Dual protocol fully operational: CLAUDE.md + AGENTS.md + enforcer hook + codex-gate bypass + DUAL_TEAMS phase mode + dual-teams-spawn.py + codex-inline-dual.py + judge.py + stability layer + warm pool + streaming+cherry-pick docs.
-
 
 
 
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff -- .claude/memory/activeContext.md' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 137ms:
diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index df1de9d..f6648c0 100644
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -1002,4 +1002,3 @@ Always-Dual protocol fully operational: CLAUDE.md + AGENTS.md + enforcer hook +
 
 
 
-
warning: in the working copy of '.claude/memory/activeContext.md', LF will be replaced by CRLF the next time Git touches it

 succeeded in 147ms:
 M .claude/memory/activeContext.md

diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index c6903997a2cb0956a3fc8c55113ab50800ce959f..f6648c0c979deed6e5839b64e92561fc290c344c
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,11 +620,6 @@
 
 ## Auto-Generated Summaries
 
-### 2026-04-26 21:52 (commit `6b10ed1`)
-**Message:** Improve judge quality axes
-**Files:** 6
-
-
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
@@ -1001,7 +996,6 @@
 
 **Architectural status:**
 Always-Dual protocol fully operational: CLAUDE.md + AGENTS.md + enforcer hook + codex-gate bypass + DUAL_TEAMS phase mode + dual-teams-spawn.py + codex-inline-dual.py + judge.py + stability layer + warm pool + streaming+cherry-pick docs.
-
 
 
 
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

apply patch
patch: completed
C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final\.claude\memory\activeContext.md
diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index c6903997a2cb0956a3fc8c55113ab50800ce959f..df1de9de55440716df46ea1c2f0ac1aca9d3a776
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,11 +620,6 @@
 
 ## Auto-Generated Summaries
 
-### 2026-04-26 21:52 (commit `6b10ed1`)
-**Message:** Improve judge quality axes
-**Files:** 6
-
-
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index c6903997a2cb0956a3fc8c55113ab50800ce959f..df1de9de55440716df46ea1c2f0ac1aca9d3a776
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,11 +620,6 @@
 
 ## Auto-Generated Summaries
 
-### 2026-04-26 21:52 (commit `6b10ed1`)
-**Message:** Improve judge quality axes
-**Files:** 6
-
-
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff -- .claude/memory/activeContext.md' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 124ms:
warning: in the working copy of '.claude/memory/activeContext.md', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index c6903997a2cb0956a3fc8c55113ab50800ce959f..df1de9de55440716df46ea1c2f0ac1aca9d3a776
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,11 +620,6 @@
 
 ## Auto-Generated Summaries
 
-### 2026-04-26 21:52 (commit `6b10ed1`)
-**Message:** Improve judge quality axes
-**Files:** 6
-
-
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 149ms:
 M .claude/memory/activeContext.md

diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index c6903997a2cb0956a3fc8c55113ab50800ce959f..df1de9de55440716df46ea1c2f0ac1aca9d3a776
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,11 +620,6 @@
 
 ## Auto-Generated Summaries
 
-### 2026-04-26 21:52 (commit `6b10ed1`)
-**Message:** Improve judge quality axes
-**Files:** 6
-
-
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff --cached -- .claude/memory/activeContext.md' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff --raw -- .claude/memory/activeContext.md' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff --numstat -- .claude/memory/activeContext.md' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 148ms:
 succeeded in 135ms:
warning: in the working copy of '.claude/memory/activeContext.md', LF will be replaced by CRLF the next time Git touches it

 succeeded in 140ms:
warning: in the working copy of '.claude/memory/activeContext.md', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index c6903997a2cb0956a3fc8c55113ab50800ce959f..df1de9de55440716df46ea1c2f0ac1aca9d3a776
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,11 +620,6 @@
 
 ## Auto-Generated Summaries
 
-### 2026-04-26 21:52 (commit `6b10ed1`)
-**Message:** Improve judge quality axes
-**Files:** 6
-
-
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git update-index --refresh; git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 160ms:
.claude/memory/activeContext.md: needs update
 M .claude/memory/activeContext.md

diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index c6903997a2cb0956a3fc8c55113ab50800ce959f..df1de9de55440716df46ea1c2f0ac1aca9d3a776
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,11 +620,6 @@
 
 ## Auto-Generated Summaries
 
-### 2026-04-26 21:52 (commit `6b10ed1`)
-**Message:** Improve judge quality axes
-**Files:** 6
-
-
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git ls-files --eol -- .claude/memory/activeContext.md; git hash-object .claude/memory/activeContext.md; git rev-parse HEAD:.claude/memory/activeContext.md' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 164ms:
i/lf    w/lf    attr/                 	.claude/memory/activeContext.md
df1de9de55440716df46ea1c2f0ac1aca9d3a776
df1de9de55440716df46ea1c2f0ac1aca9d3a776

diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index c6903997a2cb0956a3fc8c55113ab50800ce959f..df1de9de55440716df46ea1c2f0ac1aca9d3a776
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,11 +620,6 @@
 
 ## Auto-Generated Summaries
 
-### 2026-04-26 21:52 (commit `6b10ed1`)
-**Message:** Improve judge quality axes
-**Files:** 6
-
-
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git update-index --really-refresh; git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 160ms:
.claude/memory/activeContext.md: needs update
 M .claude/memory/activeContext.md

diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index c6903997a2cb0956a3fc8c55113ab50800ce959f..df1de9de55440716df46ea1c2f0ac1aca9d3a776
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,11 +620,6 @@
 
 ## Auto-Generated Summaries
 
-### 2026-04-26 21:52 (commit `6b10ed1`)
-**Message:** Improve judge quality axes
-**Files:** 6
-
-
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff --summary -- .claude/memory/activeContext.md' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff --name-status -- .claude/memory/activeContext.md' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --porcelain=v2 -- .claude/memory/activeContext.md' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 127ms:
warning: in the working copy of '.claude/memory/activeContext.md', LF will be replaced by CRLF the next time Git touches it

 succeeded in 139ms:
warning: in the working copy of '.claude/memory/activeContext.md', LF will be replaced by CRLF the next time Git touches it

 succeeded in 137ms:
1 .M N... 100644 100644 100644 df1de9de55440716df46ea1c2f0ac1aca9d3a776 df1de9de55440716df46ea1c2f0ac1aca9d3a776 .claude/memory/activeContext.md

diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index c6903997a2cb0956a3fc8c55113ab50800ce959f..df1de9de55440716df46ea1c2f0ac1aca9d3a776
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,11 +620,6 @@
 
 ## Auto-Generated Summaries
 
-### 2026-04-26 21:52 (commit `6b10ed1`)
-**Message:** Improve judge quality axes
-**Files:** 6
-
-
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff --quiet -- .claude/memory/activeContext.md; Write-Output "diff_quiet_exit=$LASTEXITCODE"; git diff --ignore-cr-at-eol --quiet -- .claude/memory/activeContext.md; Write-Output "diff_ignore_cr_exit=$LASTEXITCODE"' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 196ms:
diff_quiet_exit=0
diff_ignore_cr_exit=0
warning: in the working copy of '.claude/memory/activeContext.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.claude/memory/activeContext.md', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index c6903997a2cb0956a3fc8c55113ab50800ce959f..df1de9de55440716df46ea1c2f0ac1aca9d3a776
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,11 +620,6 @@
 
 ## Auto-Generated Summaries
 
-### 2026-04-26 21:52 (commit `6b10ed1`)
-**Message:** Improve judge quality axes
-**Files:** 6
-
-
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git add -- .claude/memory/activeContext.md; git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 157ms:
warning: in the working copy of '.claude/memory/activeContext.md', LF will be replaced by CRLF the next time Git touches it

diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index c6903997a2cb0956a3fc8c55113ab50800ce959f..df1de9de55440716df46ea1c2f0ac1aca9d3a776
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,11 +620,6 @@
 
 ## Auto-Generated Summaries
 
-### 2026-04-26 21:52 (commit `6b10ed1`)
-**Message:** Improve judge quality axes
-**Files:** 6
-
-
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git show --stat --oneline HEAD' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git rev-parse HEAD' in C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z32\codex\task-Z32-judge-quality-final
 succeeded in 139ms:
 succeeded in 133ms:
6b10ed1 Improve judge quality axes
 .claude/scripts/codex-ask.py      | 23 ++++++++++++++++-------
 .claude/scripts/judge.py          |  4 +++-
 .claude/scripts/judge_axes.py     | 17 ++++++++++++++---
 .claude/scripts/test_codex_ask.py | 21 +++++++++++++++++++--
 .claude/scripts/test_judge.py     | 38 ++++++++++++++++++++++++++++++++++++++
 mypy.ini                          |  5 +++++
 6 files changed, 95 insertions(+), 13 deletions(-)

 succeeded in 128ms:
6b10ed1029125c40a714b628ed74e34171c92549

diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index c6903997a2cb0956a3fc8c55113ab50800ce959f..df1de9de55440716df46ea1c2f0ac1aca9d3a776
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,11 +620,6 @@
 
 ## Auto-Generated Summaries
 
-### 2026-04-26 21:52 (commit `6b10ed1`)
-**Message:** Improve judge quality axes
-**Files:** 6
-
-
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

codex
=== TASK Z32 SELF-REPORT ===
- status: pass
- Improvement 1 (Y27 timeout) approach: `ask_via_exec()` now defaults to 180s and supports `--strategic` / `strategic=True` at 900s.
- Improvement 2 (mypy.ini + type_check) approach: added root `mypy.ini`; `score_type_check` activates on `mypy.ini` or `pyproject.toml` with `[tool.mypy]`.
- Improvement 3 (tie threshold) approach: judge argparse default is now `--tie-delta 0.03` with tuned-threshold help text.
- Improvement 4 (logging delegated) approach: logging coverage recognizes `_log`, `log_info`, `log_warn`, `log_error`, and `log_debug`.
- new tests: 5
- existing 138 pass: yes
- attack matrix 25/25: yes
- selftest 6/6: PASS
- mypy.ini valid INI: yes
- net lines: +82
- files modified: `.claude/scripts/codex-ask.py`, `.claude/scripts/test_codex_ask.py`, `.claude/scripts/judge.py`, `.claude/scripts/judge_axes.py`, `.claude/scripts/test_judge.py`, `mypy.ini`
- Final commit SHA: `6b10ed1029125c40a714b628ed74e34171c92549`
NOTE: Focused suite stdout: `64 passed, 1 warning in 2.32s`.
NOTE: Listed regression stdout: `256 passed in 7.63s`; full AC-5 combined suite stdout: `320 passed, 1 warning in 9.23s`.
NOTE: Selftest stdout: `selftest: 6 checks, 6 passed, 0 failed`; attack matrix stdout: `25 passed in 1.48s`.
NOTE: `mypy.ini` parse command exited 0 with no stdout.
=== END SELF-REPORT ===
diff --git a/.claude/memory/activeContext.md b/.claude/memory/activeContext.md
index c6903997a2cb0956a3fc8c55113ab50800ce959f..df1de9de55440716df46ea1c2f0ac1aca9d3a776
--- a/.claude/memory/activeContext.md
+++ b/.claude/memory/activeContext.md
@@ -620,11 +620,6 @@
 
 ## Auto-Generated Summaries
 
-### 2026-04-26 21:52 (commit `6b10ed1`)
-**Message:** Improve judge quality axes
-**Files:** 6
-
-
 ### 2026-04-26 16:07 (commit `03ec7a7`)
 **Message:** chore(work): commit Z12 task spec (Y21 logarithmic diff_size + Y25 unavailability diagnostic)
 **Files:** 1
diff --git a/.claude/scripts/codex-ask.py b/.claude/scripts/codex-ask.py
index 7164719ca563a5d22e550bb123b0892bdba4f731..f64816f785c8cc1b99c077dba379511fd120bac2
--- a/.claude/scripts/codex-ask.py
+++ b/.claude/scripts/codex-ask.py
@@ -29,10 +29,12 @@
             s.reconfigure(encoding="utf-8", errors="replace")
 
 BROKER_URL = "ws://127.0.0.1:4500"
-INACTIVITY_TIMEOUT = 30
-MAX_TIMEOUT = 300
-
-logger = logging.getLogger(__name__)
+INACTIVITY_TIMEOUT = 30
+MAX_TIMEOUT = 300
+EXEC_TIMEOUT_DEFAULT = 180
+EXEC_TIMEOUT_STRATEGIC = 900
+
+logger = logging.getLogger(__name__)
 
 
 def parse_codex_exec_stdout(stdout: str) -> str | None:
@@ -151,24 +153,26 @@
     return text.strip() if text.strip() else None
 
 
-def ask_via_exec(prompt):
-    """Fallback: ask via codex exec (cold start).
-
-    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
-    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
-    """
-    logger.info("ask_via_exec.enter prompt_len=%d", len(prompt or ""))
-    codex = shutil.which("codex")
-    if not codex:
-        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
+def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
+    """Fallback: ask via codex exec (cold start).
+
+    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
+    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.
+    """
+    timeout = EXEC_TIMEOUT_STRATEGIC if strategic else EXEC_TIMEOUT_DEFAULT
+    logger.info("ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
+                len(prompt or ""), strategic, timeout)
+    codex = shutil.which("codex")
+    if not codex:
+        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
         return None
     try:
-        r = subprocess.run(
-            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
-             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
-            capture_output=True, text=True, encoding="utf-8", errors="replace",
-            timeout=120,
-        )
+        r = subprocess.run(
+            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
+             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
+            capture_output=True, text=True, encoding="utf-8", errors="replace",
+            timeout=timeout,
+        )
         if r.returncode != 0:
             logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                         r.returncode)
@@ -184,12 +188,17 @@
         return None
 
 
-def main():
-    if len(sys.argv) < 2:
-        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
-        sys.exit(1)
-
-    prompt = " ".join(sys.argv[1:])
+def main():
+    argv = sys.argv[1:]
+    strategic = "--strategic" in argv
+    if strategic:
+        argv = [arg for arg in argv if arg != "--strategic"]
+    if not argv:
+        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
+              file=sys.stderr)
+        sys.exit(1)
+
+    prompt = " ".join(argv)
 
     # Try broker first (fast, warm)
     result = None
@@ -198,9 +207,9 @@
     except Exception:
         pass
 
-    # Fallback to codex exec
-    if not result:
-        result = ask_via_exec(prompt)
+    # Fallback to codex exec
+    if not result:
+        result = ask_via_exec(prompt, strategic=strategic)
 
     if result:
         print(f"--- Codex gpt-5.5 opinion ---")
diff --git a/.claude/scripts/judge.py b/.claude/scripts/judge.py
index 8086ee3cdbd9d2b4f7717d3780b7b07a9a1257d8..946aa74d371460ae03ea7486f10651c0d026b9f6
--- a/.claude/scripts/judge.py
+++ b/.claude/scripts/judge.py
@@ -299,7 +299,9 @@
     p.add_argument("--claude-worktree", required=True, type=Path, help="Claude worktree")
     p.add_argument("--codex-worktree", required=True, type=Path, help="Codex worktree")
     p.add_argument("--output", type=Path, default=None, help="Verdict JSON path")
-    p.add_argument("--tie-delta", type=float, default=0.02, help="Tie threshold (0.02)")
+    p.add_argument("--tie-delta", type=float, default=0.03,
+                   help=("Tie threshold (0.03). Threshold tuned from observed "
+                         "dual-implement deltas"))
     p.add_argument("--base", default="auto",
                    help="Git diff base. 'auto' = auto-resolve per side via "
                         "sidecar .dual-base-ref then merge-base HEAD <main|master|dev> "
diff --git a/.claude/scripts/judge_axes.py b/.claude/scripts/judge_axes.py
index 0180adc20952ccd20904889355a0dcba2b90445f..519d269933e6098a9efecb43cc7ab6a51b7479fa
--- a/.claude/scripts/judge_axes.py
+++ b/.claude/scripts/judge_axes.py
@@ -212,8 +212,10 @@
         raise
 
 
-_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
-_LOGGER_RE = re.compile(r"logger\.|structlog\.|_log\(")
+_FUNC_RE = re.compile(r"^\+(\s*)def\s+\w+\s*\(")
+_LOGGER_RE = re.compile(
+    r"logger\.|structlog\.|(?<![\w.])(?:_log|log_info|log_warn|log_error|log_debug)\s*\("
+)
 
 
 def _git_diff_text(worktree: Path, base: str = "HEAD") -> str:
@@ -387,10 +389,19 @@
     try:
         if not _module_available("mypy"):
             return _skip("type_check", weight, "mypy not installed")
-        has_config = any((worktree / p).exists()
-                         for p in ("mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"))
-        if not has_config:
-            return _skip("type_check", weight, "no mypy config")
+        has_config = (worktree / "mypy.ini").exists()
+        pyproject = worktree / "pyproject.toml"
+        if not has_config and pyproject.exists():
+            try:
+                has_config = bool(re.search(
+                    r"^\s*\[tool\.mypy\]\s*$",
+                    pyproject.read_text(encoding="utf-8", errors="replace"),
+                    re.MULTILINE,
+                ))
+            except Exception:
+                logger.exception("score_type_check pyproject config read failed")
+        if not has_config:
+            return _skip("type_check", weight, "no mypy config")
         files = files_override if files_override is not None else _list_modified_py(worktree, base)
         if not files:
             return _skip("type_check", weight, "no modified .py files")
diff --git a/.claude/scripts/test_codex_ask.py b/.claude/scripts/test_codex_ask.py
index 5061165fa70060ec85d4d9db97b55f4ae763094c..63ac9a76be0885319072f430287bb3e2dc6e2072
--- a/.claude/scripts/test_codex_ask.py
+++ b/.claude/scripts/test_codex_ask.py
@@ -111,18 +111,34 @@
     )
 
 
-class TestAskViaExecIntegration:
-    def test_ask_via_exec_v125_returns_response(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               return_value=_completed(0, stdout="OK\n",
-                                                       stderr="[ts] header\n")):
-            assert codex_ask.ask_via_exec("ping say OK") == "OK"
-
-    def test_ask_via_exec_v117_returns_response(self):
-        v117_stdout = (
-            "[ts] header\n"
-            "model: gpt-5.4\n"
+class TestAskViaExecIntegration:
+    def test_ask_via_exec_v125_returns_response(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")):
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+
+    def test_ask_via_exec_default_timeout_180(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("ping say OK") == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 180
+
+    def test_ask_via_exec_strategic_timeout_900(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               return_value=_completed(0, stdout="OK\n",
+                                                       stderr="[ts] header\n")) as run_mock:
+            assert codex_ask.ask_via_exec("deep review", strategic=True) == "OK"
+        assert run_mock.call_args.kwargs["timeout"] == 900
+
+    def test_ask_via_exec_v117_returns_response(self):
+        v117_stdout = (
+            "[ts] header\n"
+            "model: gpt-5.4\n"
             "codex\n"
             "Hello\n"
             "tokens used: 5\n"
@@ -144,11 +160,11 @@
             assert codex_ask.ask_via_exec("anything") is None
         run_mock.assert_not_called()
 
-    def test_ask_via_exec_timeout_returns_none(self):
-        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
-             mock.patch.object(codex_ask.subprocess, "run",
-                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=120)):
-            assert codex_ask.ask_via_exec("anything") is None
+    def test_ask_via_exec_timeout_returns_none(self):
+        with mock.patch.object(codex_ask.shutil, "which", return_value="/usr/bin/codex"), \
+             mock.patch.object(codex_ask.subprocess, "run",
+                               side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=180)):
+            assert codex_ask.ask_via_exec("anything") is None
 
 
 # --------------------------------------------------------------------------- #
@@ -184,11 +200,12 @@
 
 class TestMainFlowUnchanged:
     def test_main_flow_unchanged(self, tmp_path, monkeypatch, capsys):
-        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
-        monkeypatch.setattr(codex_ask, "ask_via_broker",
-                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
-        monkeypatch.setattr(codex_ask, "ask_via_exec", lambda _p: "FAKE-RESPONSE")
-        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
+        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
+        monkeypatch.setattr(codex_ask, "ask_via_broker",
+                            lambda _p: (_ for _ in ()).throw(RuntimeError("no broker")))
+        monkeypatch.setattr(codex_ask, "ask_via_exec",
+                            lambda _p, strategic=False: "FAKE-RESPONSE")
+        monkeypatch.setattr(sys, "argv", ["codex-ask.py", "ping"])
 
         with pytest.raises(SystemExit) as exc:
             codex_ask.main()
diff --git a/.claude/scripts/test_judge.py b/.claude/scripts/test_judge.py
index 1e9d4cd3254a58de5795d8fa515ae47ab68d859d..b9e7ec9db85254c4c72d882f798330b66d3da6b7
--- a/.claude/scripts/test_judge.py
+++ b/.claude/scripts/test_judge.py
@@ -170,23 +170,35 @@
 
 
 class TestLoggingCoverage(unittest.TestCase):
-    def test_function_with_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+    def test_function_with_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    logger.info("hi")
             +    return 1
             """)
         res = score_logging_coverage(Path("."), diff_text=diff)
-        self.assertAlmostEqual(res.score, 1.0)
-        self.assertEqual(res.raw["covered"], 1)
-
-    def test_function_without_logger(self) -> None:
-        diff = textwrap.dedent("""\
-            diff --git a/x.py b/x.py
-            @@ -0,0 +1,3 @@
-            +def foo():
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_logging_coverage_counts_delegated_log_calls(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
+            +    log_info("hi")
+            +    return 1
+            """)
+        res = score_logging_coverage(Path("."), diff_text=diff)
+        self.assertAlmostEqual(res.score, 1.0)
+        self.assertEqual(res.raw["covered"], 1)
+
+    def test_function_without_logger(self) -> None:
+        diff = textwrap.dedent("""\
+            diff --git a/x.py b/x.py
+            @@ -0,0 +1,3 @@
+            +def foo():
             +    x = 1
             +    return x
             """)
@@ -255,11 +267,29 @@
             self.assertTrue(res.skipped)
             self.assertIn("radon", res.skip_reason or "")
 
-    def test_type_check_skipped_when_mypy_absent(self) -> None:
-        with patch.object(judge_axes, "_module_available", return_value=False):
-            res = judge_axes.score_type_check(Path("."))
-            self.assertTrue(res.skipped)
-            self.assertIn("mypy", res.skip_reason or "")
+    def test_type_check_skipped_when_mypy_absent(self) -> None:
+        with patch.object(judge_axes, "_module_available", return_value=False):
+            res = judge_axes.score_type_check(Path("."))
+            self.assertTrue(res.skipped)
+            self.assertIn("mypy", res.skip_reason or "")
+
+    def test_score_type_check_active_when_mypy_ini_present(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            repo = Path(td)
+            sample = _add_file(repo, "typed.py", "x: int = 1\n")
+            _add_file(repo, "mypy.ini", "[mypy]\npython_version = 3.12\n")
+            completed = subprocess.CompletedProcess(
+                args=[sys.executable, "-m", "mypy"], returncode=0,
+                stdout="", stderr="",
+            )
+            with patch.object(judge_axes, "_module_available", return_value=True), \
+                 patch.object(judge_axes.subprocess, "run",
+                              return_value=completed) as run_mock:
+                res = judge_axes.score_type_check(repo, files_override=[sample])
+            self.assertFalse(res.skipped)
+            self.assertAlmostEqual(res.score, 1.0)
+            self.assertEqual(res.raw["files"], 1)
+            self.assertIn("--no-error-summary", run_mock.call_args.args[0])
 
 
 # ------------------------ weighted aggregate + winner ------------------------ #
@@ -353,20 +383,28 @@
         self.assertEqual(proc.returncode, 0)
         self.assertIn("Objective judge", proc.stdout)
 
-    def test_help_mentions_auto_base(self) -> None:
-        """AC6: --help text must mention auto-resolve for --base."""
-        proc = subprocess.run(
-            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
-            check=False, capture_output=True, text=True, timeout=30,
+    def test_help_mentions_auto_base(self) -> None:
+        """AC6: --help text must mention auto-resolve for --base."""
+        proc = subprocess.run(
+            [sys.executable, str(_THIS_DIR / "judge.py"), "--help"],
+            check=False, capture_output=True, text=True, timeout=30,
         )
         self.assertEqual(proc.returncode, 0)
-        self.assertIn("--base", proc.stdout)
-        self.assertIn("auto", proc.stdout)
-
-    def test_malformed_task_exit_1(self) -> None:
-        with tempfile.TemporaryDirectory() as td:
-            missing = Path(td) / "nope.md"
-            wt = Path(td) / "wt"
+        self.assertIn("--base", proc.stdout)
+        self.assertIn("auto", proc.stdout)
+
+    def test_tie_threshold_default_is_0_03(self) -> None:
+        args = judge.build_arg_parser().parse_args([
+            "--task", "T1.md",
+            "--claude-worktree", "claude",
+            "--codex-worktree", "codex",
+        ])
+        self.assertAlmostEqual(args.tie_delta, 0.03)
+
+    def test_malformed_task_exit_1(self) -> None:
+        with tempfile.TemporaryDirectory() as td:
+            missing = Path(td) / "nope.md"
+            wt = Path(td) / "wt"
             wt.mkdir()
             rc = judge.main([
                 "--task", str(missing),
diff --git a/mypy.ini b/mypy.ini
new file mode 100644
index 0000000000000000000000000000000000000000..34f1230ed249751c8dc8c74df80b4c42c7b5e022
--- /dev/null
+++ b/mypy.ini
@@ -0,0 +1,5 @@
+[mypy]
+python_version = 3.12
+ignore_missing_imports = True
+warn_unused_ignores = True
+strict_optional = False

2026-04-26T18:56:53.608964Z ERROR codex_core::session: failed to record rollout items: thread 019dcb1d-8c85-7e92-b8ad-33d17a2bae0d not found
tokens used
153 826
```
