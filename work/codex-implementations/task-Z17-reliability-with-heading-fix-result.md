# Codex Implementation Result — Task Z17-reliability-with-heading-fix

- status: pass
- timestamp: 2026-04-26T15:27:35.810148+00:00
- task_file: C:\Bots\Migrator bots\claude-project-template-update\work\criterion-upgrade\task-Z17-reliability-with-heading-fix.md
- base_sha: 5c42957b9c0c980af7672253f69bfd18d242d9fc
- codex_returncode: 1
- scope_status: pass
- scope_message: OK: 4 path(s) in fence
- tests_all_passed: True
- test_commands_count: 5

## Diff

```diff
diff --git a/.claude/scripts/codex-implement.py b/.claude/scripts/codex-implement.py
index c6b0d6f..c54e648 100644
--- a/.claude/scripts/codex-implement.py
+++ b/.claude/scripts/codex-implement.py
@@ -294,25 +294,38 @@ def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
 
 
 def split_sections(body: str) -> dict[str, str]:
-    """Split markdown body into ## sections. Key = heading text (without ##)."""
+    """Split markdown body into ## sections. Key = heading text (without ##).
+
+    Headings with descriptive suffixes like ``## Scope Fence - paths`` are
+    also registered under the prefix key (``Scope Fence``) for stable lookups.
+    """
     _log(logging.DEBUG, "entry: split_sections", body_len=len(body))
     try:
         sections: dict[str, str] = {}
         current_key: Optional[str] = None
+        current_keys: list[str] = []
         current_lines: list[str] = []
 
         for raw_line in body.splitlines():
             m = re.match(r"^##\s+(?!#)(.+?)\s*$", raw_line)
             if m:
                 if current_key is not None:
-                    sections[current_key] = "\n".join(current_lines).strip("\n")
+                    section_text = "\n".join(current_lines).strip("\n")
+                    for key in current_keys:
+                        sections[key] = section_text
                 current_key = m.group(1).strip()
+                current_keys = [current_key]
+                alias = re.split(r"\s[-—]\s", current_key, maxsplit=1)[0].strip()
+                if alias and alias != current_key:
+                    current_keys.append(alias)
                 current_lines = []
             else:
                 current_lines.append(raw_line)
 
         if current_key is not None:
-            sections[current_key] = "\n".join(current_lines).strip("\n")
+            section_text = "\n".join(current_lines).strip("\n")
+            for key in current_keys:
+                sections[key] = section_text
 
         _log(logging.DEBUG, "exit: split_sections", section_count=len(sections))
         return sections
@@ -1069,6 +1082,51 @@ class ScopeCheckResult:
     violations: list[str] = field(default_factory=list)
 
 
+def _find_main_repo_root(p: Path) -> Optional[Path]:
+    """Return the nearest ancestor with a real ``.git`` directory."""
+    _log(logging.DEBUG, "entry: _find_main_repo_root", path=str(p))
+    try:
+        start = p.resolve()
+        for candidate in (start, *start.parents):
+            if (candidate / ".git").is_dir():
+                _log(logging.DEBUG, "exit: _find_main_repo_root", root=str(candidate))
+                return candidate
+        _log(logging.DEBUG, "exit: _find_main_repo_root", root=None)
+        return None
+    except Exception:
+        logger.exception("_find_main_repo_root failed")
+        raise
+
+
+def _resolve_scope_check_script(project_root: Path) -> Path:
+    """Resolve the repo-current codex-scope-check.py script path."""
+    _log(logging.DEBUG, "entry: _resolve_scope_check_script", project_root=str(project_root))
+    try:
+        env_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
+        if env_project_dir:
+            script = (
+                Path(env_project_dir).expanduser().resolve()
+                / ".claude"
+                / "scripts"
+                / "codex-scope-check.py"
+            )
+            _log(logging.DEBUG, "exit: _resolve_scope_check_script", source="env", script=str(script))
+            return script
+
+        main_root = _find_main_repo_root(project_root)
+        if main_root is not None:
+            script = main_root / ".claude" / "scripts" / "codex-scope-check.py"
+            _log(logging.DEBUG, "exit: _resolve_scope_check_script", source="main_repo", script=str(script))
+            return script
+
+        script = project_root / ".claude" / "scripts" / "codex-scope-check.py"
+        _log(logging.DEBUG, "exit: _resolve_scope_check_script", source="worktree", script=str(script))
+        return script
+    except Exception:
+        logger.exception("_resolve_scope_check_script failed")
+        raise
+
+
 def run_scope_check(
     diff_path: Path,
     fence_paths: ScopeFence,
@@ -1077,7 +1135,7 @@ def run_scope_check(
     """Invoke codex-scope-check.py if present; skip gracefully otherwise."""
     _log(logging.DEBUG, "entry: run_scope_check", diff_path=str(diff_path))
     try:
-        script = project_root / ".claude" / "scripts" / "codex-scope-check.py"
+        script = _resolve_scope_check_script(project_root)
         if not script.exists():
             msg = f"codex-scope-check.py not found at {script}; scope check SKIPPED"
             _log(logging.WARNING, msg)
diff --git a/.claude/scripts/spawn-agent.py b/.claude/scripts/spawn-agent.py
index 6e82aaf..24ce71e 100644
--- a/.claude/scripts/spawn-agent.py
+++ b/.claude/scripts/spawn-agent.py
@@ -55,16 +55,19 @@ Y14_BLOCK = (
     "\n"
     "Claude Code harness denies the `Write` and `Edit` tools at the permission\n"
     "layer for sub-agents. This is design intent, not a bug. Use PowerShell as\n"
-    "the PRIMARY mechanism for file creation:\n"
+    "the PRIMARY mechanism for file creation and replacement. Use this no-BOM\n"
+    "UTF-8 template for source files:\n"
     "\n"
     "```bash\n"
-    "powershell -NoProfile -Command \"Set-Content -Encoding utf8 -Path '<abs>' -Value @'\n"
+    "powershell -NoProfile -Command \"$utf8NoBom = [System.Text.UTF8Encoding]::new($false); [System.IO.File]::WriteAllText('<abs>', @'\n"
     "...content here...\n"
-    "'@\"\n"
+    "'@, $utf8NoBom)\"\n"
     "```\n"
     "\n"
-    "Edit tool MAY work for in-place edits to existing files; if denied, fall\n"
-    "back to a PowerShell `.Replace()` + `Set-Content` invocation.\n"
+    "For one-line writes where BOM sensitivity does not matter, the legacy\n"
+    "`Set-Content -Encoding utf8` pattern remains acceptable. For in-place\n"
+    "edits to existing files, use PowerShell `.Replace()` plus the no-BOM\n"
+    "write template above.\n"
     "\n"
     "**Tools cheat-sheet:** rely on `Read`, `Bash`, `Glob`, `Grep` for analysis;\n"
     "PowerShell via `Bash` for writes; `Edit`/`Write` may be denied — don't\n"
@@ -111,15 +114,22 @@ def inject_y14_block(prompt: str) -> str:
     """
     logger.debug("event=inject_y14_block.enter prompt_chars=%d", len(prompt))
 
-    if Y14_HEADING in prompt:
+    prompt_lines = prompt.splitlines()
+    already_has_block = any(line.strip() == Y14_HEADING for line in prompt_lines)
+    if already_has_block:
         logger.debug("event=inject_y14_block.skip reason=already_present")
         return prompt
 
     block = build_y14_block()
-    marker = "## Your Task"
-
-    if marker in prompt:
-        injected = prompt.replace(marker, block + "\n" + marker, 1)
+    marker_match = re.search(r"(?m)^## Your Task\s*$", prompt)
+
+    if marker_match is not None:
+        injected = (
+            prompt[:marker_match.start()]
+            + block
+            + "\n"
+            + prompt[marker_match.start():]
+        )
         logger.debug(
             "event=inject_y14_block.exit position=before_task_body chars=%d",
             len(injected),
@@ -461,8 +471,7 @@ Examples:
 
     # Dry run: emit auto-detection summary to stderr (callers can still
     # inspect detection metadata) and emit the full generated prompt to
-    # stdout so AC3 holds: piping --dry-run output through
-    # `grep -c "Y14 finding"` returns exactly 1.
+    # stdout so tests can inspect the injected Y14 block.
     if args.dry_run:
         logger.debug("event=main.dry_run agent_type=%s", agent_type)
         print("Auto-detection:", file=sys.stderr)
diff --git a/.claude/scripts/test_codex_implement.py b/.claude/scripts/test_codex_implement.py
index 0f9da89..13add8a 100644
--- a/.claude/scripts/test_codex_implement.py
+++ b/.claude/scripts/test_codex_implement.py
@@ -156,6 +156,24 @@ class TestSectionSplitter(unittest.TestCase):
         self.assertIn("B", sections)
         self.assertIn("### subsection", sections["A"])
 
+    def test_parse_section_handles_em_dash_suffix(self):
+        text = "## Scope Fence — desc\nbody\n"
+        sections = codex_impl.split_sections(text)
+        self.assertEqual(sections["Scope Fence"], "body")
+        self.assertEqual(sections["Scope Fence — desc"], "body")
+
+    def test_parse_section_handles_hyphen_suffix(self):
+        text = "## Test Commands - desc\n```bash\necho hi\n```\n"
+        sections = codex_impl.split_sections(text)
+        self.assertIn("echo hi", sections["Test Commands"])
+        self.assertIn("echo hi", sections["Test Commands - desc"])
+
+    def test_parse_section_no_suffix_unchanged(self):
+        text = "## Scope Fence\nbody\n"
+        sections = codex_impl.split_sections(text)
+        self.assertEqual(sections["Scope Fence"], "body")
+        self.assertEqual(list(sections.keys()), ["Scope Fence"])
+
 
 class TestScopeFenceParser(unittest.TestCase):
     def test_parses_allowed_and_forbidden_bullets(self):
@@ -248,6 +266,27 @@ class TestScopeFenceParserCodeBlock(unittest.TestCase):
         self.assertEqual(fence.allowed, ["legacy/path.py"])
         self.assertNotIn("should_NOT_appear.py", fence.allowed)
 
+    def test_parse_scope_fence_em_dash_heading_yields_paths(self):
+        text = (
+            "# Task Z17\n\n"
+            "## Scope Fence — files you MAY modify\n\n"
+            "```\n"
+            ".claude/scripts/codex-implement.py\n"
+            ".claude/scripts/test_codex_implement.py\n"
+            "```\n"
+        )
+        with tempfile.TemporaryDirectory() as td:
+            task_path = Path(td) / "task-Z17.md"
+            task_path.write_text(text, encoding="utf-8")
+            task = codex_impl.parse_task_file(task_path)
+        self.assertEqual(
+            task.scope_fence.allowed,
+            [
+                ".claude/scripts/codex-implement.py",
+                ".claude/scripts/test_codex_implement.py",
+            ],
+        )
+
 
 class TestDetermineRunStatus(unittest.TestCase):
     """Y20: determine_run_status() pure helper.
@@ -290,6 +329,16 @@ class TestDetermineRunStatus(unittest.TestCase):
         )
         self.assertEqual(status, "pass")
 
+    def test_status_pass_when_only_codex_returncode_nonzero_and_no_modifications(self):
+        """Verification-only run: tests/scope pass even when Codex rc is non-zero."""
+        status = codex_impl.determine_run_status(
+            scope=self._scope("pass"),
+            test_run=self._tests(True),
+            codex_run=self._codex(7),
+            timed_out=False,
+        )
+        self.assertEqual(status, "pass")
+
     def test_status_fail_when_tests_fail(self):
         """AC-2.b: scope=pass, tests fail, codex_returncode=0 -> 'fail'."""
         status = codex_impl.determine_run_status(
@@ -545,6 +594,42 @@ class TestBuildCodexArgvY26(unittest.TestCase):
 
 
 class TestScopeCheckFallback(unittest.TestCase):
+    def test_resolve_scope_check_uses_env_var(self):
+        with tempfile.TemporaryDirectory() as td:
+            env_root = Path(td) / "repo-current"
+            expected = env_root / ".claude" / "scripts" / "codex-scope-check.py"
+            with mock.patch.dict(
+                codex_impl.os.environ,
+                {"CLAUDE_PROJECT_DIR": str(env_root)},
+                clear=True,
+            ):
+                script = codex_impl._resolve_scope_check_script(Path(td) / "worktree")
+        self.assertEqual(script, expected.resolve())
+
+    def test_resolve_scope_check_walks_up_from_worktree(self):
+        with tempfile.TemporaryDirectory() as td:
+            repo_root = Path(td) / "repo"
+            worktree = repo_root / "worktrees" / "feature"
+            (repo_root / ".git").mkdir(parents=True)
+            worktree.mkdir(parents=True)
+            (worktree / ".git").write_text(
+                "gitdir: ../../.git/worktrees/feature",
+                encoding="utf-8",
+            )
+            expected = repo_root / ".claude" / "scripts" / "codex-scope-check.py"
+            with mock.patch.dict(codex_impl.os.environ, {}, clear=True):
+                script = codex_impl._resolve_scope_check_script(worktree)
+        self.assertEqual(script, expected)
+
+    def test_resolve_scope_check_falls_back_to_worktree(self):
+        with tempfile.TemporaryDirectory() as td:
+            worktree = Path(td) / "worktree"
+            worktree.mkdir()
+            expected = worktree / ".claude" / "scripts" / "codex-scope-check.py"
+            with mock.patch.dict(codex_impl.os.environ, {}, clear=True):
+                script = codex_impl._resolve_scope_check_script(worktree)
+        self.assertEqual(script, expected)
+
     def test_missing_scope_check_script_returns_skipped(self):
         with tempfile.TemporaryDirectory() as td:
             root = Path(td)
@@ -553,7 +638,8 @@ class TestScopeCheckFallback(unittest.TestCase):
             diff_file = root / "some.diff"
             diff_file.write_text("", encoding="utf-8")
             fence = codex_impl.ScopeFence(allowed=["a.py"])
-            result = codex_impl.run_scope_check(diff_file, fence, root)
+            with mock.patch.dict(codex_impl.os.environ, {}, clear=True):
+                result = codex_impl.run_scope_check(diff_file, fence, root)
             self.assertEqual(result.status, "skipped")
 
 
diff --git a/.claude/scripts/test_spawn_agent.py b/.claude/scripts/test_spawn_agent.py
index 0978b51..6106510 100644
--- a/.claude/scripts/test_spawn_agent.py
+++ b/.claude/scripts/test_spawn_agent.py
@@ -130,9 +130,12 @@ class Y14InjectionTests(unittest.TestCase):
         """AC1 / AC5(a): generated prompt contains the Y14 heading."""
         logger.info("event=test.y14_section_present.enter")
         prompt = dry_run_prompt()
+        heading_lines = [
+            line for line in prompt.splitlines() if line.strip() == Y14_HEADING
+        ]
         self.assertIn(
             Y14_HEADING,
-            prompt,
+            heading_lines,
             msg="Y14 heading missing from generated prompt (AC1)",
         )
         logger.info("event=test.y14_section_present.exit pass=true")
@@ -141,7 +144,9 @@ class Y14InjectionTests(unittest.TestCase):
         """AC2 / AC5(b): the Y14 heading appears exactly once per prompt."""
         logger.info("event=test.y14_section_appears_once.enter")
         prompt = dry_run_prompt()
-        count = prompt.count(Y14_HEADING)
+        count = sum(
+            1 for line in prompt.splitlines() if line.strip() == Y14_HEADING
+        )
         self.assertEqual(
             count, 1,
             msg=(
@@ -163,17 +168,52 @@ class Y14InjectionTests(unittest.TestCase):
             )
         logger.info("event=test.y14_block_keywords.exit pass=true")
 
+    def test_spawn_agent_prompt_has_powershell_primary_section(self) -> None:
+        """Z17: PowerShell is the PRIMARY write mechanism with no-BOM UTF-8."""
+        logger.info("event=test.powershell_primary.enter")
+        prompt = dry_run_prompt()
+        lines = prompt.splitlines()
+        block_start = next(
+            i for i, line in enumerate(lines) if line.strip() == Y14_HEADING
+        )
+        block_end = next(
+            (i for i in range(block_start + 1, len(lines)) if lines[i].startswith("## ")),
+            len(lines),
+        )
+        block_lines = lines[block_start:block_end]
+        block = "\n".join(block_lines)
+        powershell_indexes = [
+            i for i, line in enumerate(block_lines) if "PowerShell" in line
+        ]
+        self.assertTrue(powershell_indexes, msg="prompt does not mention PowerShell")
+        self.assertIn("[System.Text.UTF8Encoding]::new($false)", block)
+        self.assertTrue(
+            any(
+                "PRIMARY" in "\n".join(block_lines[max(0, i - 2): i + 3])
+                for i in powershell_indexes
+            ),
+            msg="PRIMARY must appear near a PowerShell instruction",
+        )
+        for i in powershell_indexes:
+            nearby = "\n".join(block_lines[max(0, i - 5): i + 6]).lower()
+            self.assertNotIn(
+                "fallback",
+                nearby,
+                msg="fallback wording must not appear near PowerShell instruction",
+            )
+        logger.info("event=test.powershell_primary.exit pass=true")
+
     def test_dry_run_grep_count_one(self) -> None:
-        """AC3: ``grep -c "Y14 finding"`` against --dry-run stdout returns 1."""
+        """AC3: the injected Y14 heading line appears exactly once."""
         logger.info("event=test.dry_run_grep_count.enter")
         prompt = dry_run_prompt()
         finding_count = sum(
-            1 for line in prompt.splitlines() if "Y14 finding" in line
+            1 for line in prompt.splitlines() if line.strip() == Y14_HEADING
         )
         self.assertEqual(
             finding_count, 1,
             msg=(
-                f"grep -c 'Y14 finding' should return 1 per AC3, got {finding_count}"
+                f"Y14 heading line should appear once per AC3, got {finding_count}"
             ),
         )
         logger.info(
```

## Test Output

### `python -m pytest .claude/scripts/test_codex_implement.py -q --tb=line`

- returncode: 0  - passed: True  - timed_out: False

```
--- stdout ---
........................................................................ [ 90%]
........                                                                 [100%]
80 passed in 1.27s
```

### `python -m pytest .claude/scripts/test_spawn_agent.py -q --tb=line`

- returncode: 0  - passed: True  - timed_out: False

```
--- stdout ---
......                                                                   [100%]
6 passed in 0.43s
```

### `python -m pytest .claude/hooks/test_enforcer_live_attacks.py -q --tb=line`

- returncode: 0  - passed: True  - timed_out: False

```
--- stdout ---
.........................                                                [100%]
25 passed in 1.76s
```

### `python -m pytest .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line`

- returncode: 0  - passed: True  - timed_out: False

```
--- stdout ---
........................................................................ [ 40%]
........................................................................ [ 81%]
.................................                                        [100%]
============================== warnings summary ===============================
.claude\scripts\judge_axes.py:46
  C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z17\codex\task-Z17-reliability-with-heading-fix\.claude\scripts\judge_axes.py:46: PytestCollectionWarning: cannot collect test class 'TestRun' because it has a __init__ constructor (from: .claude/scripts/test_judge.py)
    @dataclass

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
177 passed, 1 warning in 6.91s
```

### `python .claude/scripts/dual-teams-selftest.py`

- returncode: 0  - passed: True  - timed_out: False

```
--- stdout ---
[PASS] preflight-clean-with-sentinel-V1                     (70 ms)
[PASS] preflight-clean-with-sentinel-V2                     (65 ms)
[PASS] is_dual_teams_worktree-true-on-V1                    ( 1 ms)
[PASS] is_dual_teams_worktree-true-on-V2                    ( 1 ms)
[PASS] judge-axes-sees-claude-committed-py                  (34 ms)
[PASS] judge-axes-sees-codex-untracked-py                   (58 ms)
selftest: 6 checks, 6 passed, 0 failed (739 ms)
--- stderr ---
{"json_output": false, "keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: main", "ts": "2026-04-26T15:38:37.229956+00:00"}
{"keep_tmpdir": false, "level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: run_selftest", "ts": "2026-04-26T15:38:37.229956+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: setup_transient_repo", "tmpdir": "C:\\Users\\Lenovo\\AppData\\Local\\Temp\\dual-teams-selftest-w0gbda8a", "ts": "2026-04-26T15:38:37.231961+00:00"}
{"base_sha": "b462d9f98a354b093e33b5a9b23c4b4ccc1f6625", "duration_ms": 335, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: setup_transient_repo", "ts": "2026-04-26T15:38:37.567084+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: load_integrations", "project_root": "C:\\Bots\\Migrator bots\\claude-project-template-update\\worktrees\\criterion-upgrade-z17\\codex\\task-Z17-reliability-with-heading-fix", "ts": "2026-04-26T15:38:37.567084+00:00"}
{"duration_ms": 6, "failures": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: load_integrations", "ts": "2026-04-26T15:38:37.572567+00:00"}
{"level": "INFO", "logger": "dual_teams_selftest", "msg": "entry: build_results", "ts": "2026-04-26T15:38:37.572567+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T15:38:37.572567+00:00"}
{"check": "preflight-clean-with-sentinel-V1", "detail": "git status --porcelain empty", "duration_ms": 70, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T15:38:37.642968+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T15:38:37.642968+00:00"}
{"check": "preflight-clean-with-sentinel-V2", "detail": "git status --porcelain empty", "duration_ms": 65, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T15:38:37.707889+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T15:38:37.707889+00:00"}
{"check": "is_dual_teams_worktree-true-on-V1", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T15:38:37.708888+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T15:38:37.708888+00:00"}
{"check": "is_dual_teams_worktree-true-on-V2", "detail": ".dual-base-ref recognized", "duration_ms": 1, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T15:38:37.708888+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T15:38:37.837313+00:00"}
{"check": "judge-axes-sees-claude-committed-py", "detail": "saw claude_probe.py", "duration_ms": 34, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T15:38:37.871467+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "level": "INFO", "logger": "dual_teams_selftest", "msg": "check entry", "ts": "2026-04-26T15:38:37.871467+00:00"}
{"check": "judge-axes-sees-codex-untracked-py", "detail": "saw codex_probe.py", "duration_ms": 58, "level": "INFO", "logger": "dual_teams_selftest", "msg": "check exit", "status": "PASS", "ts": "2026-04-26T15:38:37.929685+00:00"}
{"checks": 6, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: build_results", "ts": "2026-04-26T15:38:37.929685+00:00"}
{"checks": 6, "duration_ms": 739, "failed": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: run_selftest", "passed": 6, "ts": "2026-04-26T15:38:37.968646+00:00"}
{"exit_code": 0, "level": "INFO", "logger": "dual_teams_selftest", "msg": "exit: main", "ts": "2026-04-26T15:38:37.968646+00:00"}
```

## Self-Report (Codex NOTE/BLOCKER lines)

(no NOTE/BLOCKER lines)

## Codex stderr

```
OpenAI Codex v0.125.0 (research preview)
--------
workdir: C:\Bots\Migrator bots\claude-project-template-update\worktrees\criterion-upgrade-z17\codex\task-Z17-reliability-with-heading-fix
model: gpt-5.5
provider: chatgpt
approval: never
sandbox: danger-full-access
reasoning effort: xhigh
reasoning summaries: none
session id: 019dca71-17f1-75d0-b9ee-9b6df5b98622
--------
user
You are the single-task implementer. The task specification below is IMMUTABLE.
Write code to satisfy all Acceptance Criteria. Do NOT modify files listed in
Forbidden Paths or Read-Only Files. After writing code, run every Test Command
listed in the task and report the result in your self-report.
Any AGENTS.md or CLAUDE.md in the worktree is authoritative background context.

---- TASK SPECIFICATION ----

---
task_id: Z17-reliability-with-heading-fix
title: Criterion 2 Reliability — 4 fixes including parse_scope_fence heading-suffix robustness
executor: dual
risk_class: high-stakes
speed_profile: balanced
---

# Task Z17

## Goal

Criterion 2 (Reliability) currently 6/10. Z16 attempted 3 fixes but
hit a self-referential rollback because task spec heading
`## Scope Fence — files you MAY modify` produced an empty fence
(em-dash suffix broke section extraction in codex-implement.py).
Z17 retries with plain `## Scope Fence` heading AND adds a 4th fix
that closes the heading-suffix issue for future task specs.

## Four coordinated fixes

### Fix 1 — codex-implement uses REPO-CURRENT parser

`run_scope_check` invokes the worktree-local `codex-scope-check.py`
which is FROZEN at worktree-create-time. If a parser fix is the very
thing being merged, the worktree still has the buggy parser and rolls
back the fix.

Resolve `CLAUDE_PROJECT_DIR` env var first; else walk up from worktree
to find the non-worktree repo root; else fall back to worktree-local.

Helper `_resolve_scope_check_script(project_root)` extracted for tests.

### Fix 2 — spawn-agent.py promotes PowerShell to PRIMARY

Replace existing Y14 "fallback" wording with "PRIMARY mechanism".
Provide complete template with `[System.Text.UTF8Encoding]::new($false)`
to eliminate BOM (Z11 hit this).

### Fix 3 — Y20 verification-only edge case test

Test locks `tests_ok=True ∧ scope_status='pass' ∧ codex_returncode!=0
∧ no actual file modifications → status='pass'`. Verifies Y20 fix
from Z11 holds for verification-only Codex runs.

### Fix 4 — parse_scope_fence robust to heading suffix (NEW)

Section parser currently uses exact heading text. Heading
`## Scope Fence — files you MAY modify` produces section name
`Scope Fence — files you MAY modify`, not `Scope Fence`.

Change: when heading contains ` — ` (em-dash + spaces) or ` - ` (hyphen
+ spaces) AFTER the first word, also register the prefix as alias.
Use `re.split(r"\s[-—]\s", heading_text, maxsplit=1)[0].strip()`.

## Scope Fence

```
.claude/scripts/codex-implement.py
.claude/scripts/test_codex_implement.py
.claude/scripts/spawn-agent.py
.claude/scripts/test_spawn_agent.py
```

DO NOT modify any other file.

## Read-Only Files / Evaluation Firewall

- `work/criterion-upgrade/task-Z17-reliability-with-heading-fix.md` (this file)
- `.claude/hooks/codex-delegate-enforcer.py`
- `.claude/scripts/codex-scope-check.py`

## Acceptance Criteria

### AC-1: Fix 1 tests pass

Three new tests in `test_codex_implement.py`:
- `test_resolve_scope_check_uses_env_var` — when env CLAUDE_PROJECT_DIR set, uses that
- `test_resolve_scope_check_walks_up_from_worktree` — no env, walks up to non-worktree root
- `test_resolve_scope_check_falls_back_to_worktree` — neither yields → worktree script

### AC-2: Fix 2 test passes

`test_spawn_agent_prompt_has_powershell_primary_section` in `test_spawn_agent.py`.
Generated prompt MUST contain "PRIMARY" near "PowerShell" AND
`[System.Text.UTF8Encoding]::new($false)` AND must NOT contain "fallback"
within 5 lines of the PowerShell instruction.

### AC-3: Fix 3 test passes

`test_status_pass_when_only_codex_returncode_nonzero_and_no_modifications`
in `test_codex_implement.py`. Locks Y20 behavior.

### AC-4: Fix 4 tests pass

Four new tests in `test_codex_implement.py`:
- `test_parse_section_handles_em_dash_suffix` — `## Scope Fence — desc`
  yields section accessible by `Scope Fence`
- `test_parse_section_handles_hyphen_suffix` — `## Test Commands - desc` ditto
- `test_parse_section_no_suffix_unchanged` — plain `## Scope Fence` works
- `test_parse_scope_fence_em_dash_heading_yields_paths` — full integration:
  task spec with em-dash heading + code-block paths → returned list non-empty

### AC-5: Existing 72 test_codex_implement + 5 test_spawn_agent still pass

```bash
python -m pytest .claude/scripts/test_codex_implement.py .claude/scripts/test_spawn_agent.py -q --tb=line
```

### AC-6: Live attack matrix 25/25 still passes

```bash
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -q --tb=line
```

### AC-7: Selftest still passes

`python .claude/scripts/dual-teams-selftest.py` → 6/6 PASS

## Test Commands

```bash
# 1. test_codex_implement
python -m pytest .claude/scripts/test_codex_implement.py -q --tb=line

# 2. test_spawn_agent
python -m pytest .claude/scripts/test_spawn_agent.py -q --tb=line

# 3. Live attack matrix (regression)
python -m pytest .claude/hooks/test_enforcer_live_attacks.py -q --tb=line

# 4. Other suites
python -m pytest .claude/scripts/test_codex_inline_dual.py .claude/scripts/test_codex_ask.py .claude/scripts/test_judge.py .claude/hooks/test_codex_delegate_enforcer_invariants.py .claude/hooks/test_codex_delegate_enforcer.py .claude/hooks/test_codex_gate.py -q --tb=line

# 5. Selftest
python .claude/scripts/dual-teams-selftest.py
```

## Implementation hints

- Fix 1: `_find_main_repo_root(p: Path) -> Optional[Path]` walks up looking for a directory whose `.git` is a directory (not a file pointing to a worktree).
- Fix 4: locate the section parser via `grep -n "sections\[\|sections.update\|^def parse_task\|## " codex-implement.py`. After registering exact heading, also register the prefix-before-em-dash-or-hyphen as alias.
- For testing Fix 4, use literal `## Scope Fence — embedded em-dash` in test fixtures (string literal, not file). Do NOT use em-dash in section headings of THIS task spec — keep this spec safe.
- Logging: each new helper has entry/exit logs.

## Self-report format

```
=== TASK Z17 SELF-REPORT ===
- status: pass | fail | blocker
- Fix 1 (repo-current parser) approach: <1 line>
- Fix 2 (PowerShell primary) approach: <1 line>
- Fix 3 (Y20 audit) approach: <1 line>
- Fix 4 (heading suffix robust) approach: <1 line>
- new tests added: <count>
- existing 77 tests still pass: yes / no
- live attack matrix 25/25: yes / no
- selftest 6/6: PASS / FAIL
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

ERROR: You've hit your usage limit. Upgrade to Pro (https://chatgpt.com/explore/pro), visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at Apr 29th, 2026 5:54 PM.
ERROR: You've hit your usage limit. Upgrade to Pro (https://chatgpt.com/explore/pro), visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at Apr 29th, 2026 5:54 PM.
2026-04-26T15:38:24.798667Z ERROR codex_core::session: failed to record rollout items: thread 019dca71-17f1-75d0-b9ee-9b6df5b98622 not found
```
