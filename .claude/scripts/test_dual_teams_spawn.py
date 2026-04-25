"""Unit tests for dual-teams-spawn.py.

Mocks spawn-agent.py + codex-wave.py Popen so nothing is actually executed.
Uses a real temporary git repo for worktree creation tests on Windows.

Run: py -3 .claude/scripts/test_dual_teams_spawn.py
"""
from __future__ import annotations

import importlib.util
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).parent / "dual-teams-spawn.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("dual_teams_spawn",
                                                   SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["dual_teams_spawn"] = mod
    spec.loader.exec_module(mod)
    return mod


dts = _load_module()

logging.getLogger("dual_teams_spawn").setLevel(logging.CRITICAL)


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.setdefault("GIT_AUTHOR_NAME", "test")
    env.setdefault("GIT_AUTHOR_EMAIL", "test@example.com")
    env.setdefault("GIT_COMMITTER_NAME", "test")
    env.setdefault("GIT_COMMITTER_EMAIL", "test@example.com")
    return subprocess.run(["git", *args], cwd=str(cwd), check=True,
                          capture_output=True, text=True, env=env)


def _init_repo(path: Path) -> None:
    _git(["init", "-b", "main"], cwd=path)
    _git(["config", "user.email", "test@example.com"], cwd=path)
    _git(["config", "user.name", "test"], cwd=path)
    (path / "README.md").write_text("hello\n", encoding="utf-8")
    _git(["add", "README.md"], cwd=path)
    _git(["commit", "-m", "init"], cwd=path)


def _cleanup_worktrees(path: Path) -> None:
    try:
        subprocess.run(["git", "worktree", "prune"], cwd=str(path),
                       capture_output=True, check=False)
    except Exception:
        pass


def _fake_launch_factory(pid: int = 99999):
    """Return a launch_codex_wave stand-in that writes a log file."""
    def _launch(codex_wave_script, task_files, parallel,
                worktree_base, log_file, project_root, base_branch,
                result_dir=None):
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.touch()
        cmd = ["py", str(codex_wave_script)]
        if result_dir is not None:
            cmd += ["--result-dir", str(result_dir.resolve())]
        return dts.WavePlan(pid=pid,
                            cmd=cmd,
                            log_file=str(log_file), started=True,
                            result_dir=(str(result_dir.resolve())
                                        if result_dir is not None else None))
    return _launch


def _fake_prompt(spawn_agent_script, task_file, prompt_output,
                 team_name, agent_name, project_root):
    """Stand-in for spawn-agent.py that writes a simple prompt file."""
    prompt_output.parent.mkdir(parents=True, exist_ok=True)
    prompt_output.write_text(f"# prompt for {task_file}\n", encoding="utf-8")
    return True, None


# ---------------------------------------------------------------------------
# Pure-function tests
# ---------------------------------------------------------------------------


class DeriveTaskIdTests(unittest.TestCase):
    def test_numeric_id(self):
        self.assertEqual(dts.derive_task_id(Path("tasks/T1.md")), "T1")
        self.assertEqual(dts.derive_task_id(Path("tasks/T42-foo.md")), "T42")

    def test_lowercase_t(self):
        self.assertEqual(dts.derive_task_id(Path("t7-thing.md")), "T7")

    def test_fallback_to_stem(self):
        self.assertEqual(
            dts.derive_task_id(Path("tasks/misc-task.md")), "misc-task")


class ExpandTasksTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "tasks").mkdir()
        for n in (1, 2):
            (self.root / "tasks" / f"T{n}.md").write_text("x", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_csv(self):
        arg = f"{self.root}/tasks/T1.md,{self.root}/tasks/T2.md"
        self.assertEqual(len(dts.expand_tasks(arg)), 2)

    def test_dedup(self):
        p = f"{self.root}/tasks/T1.md"
        self.assertEqual(len(dts.expand_tasks(f"{p},{p}")), 1)

    def test_empty_returns_empty(self):
        self.assertEqual(dts.expand_tasks(""), [])


class BuildPlanTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self):
        self._tmp.cleanup()

    def test_branch_names_follow_convention(self):
        """AC6: worktree branch names follow claude/dual-teams/Ti convention."""
        pairs = dts.build_plan([Path("tasks/T1.md"), Path("tasks/T2.md")],
                               self.root, Path("worktrees/dual-teams"), "demo")
        self.assertEqual(len(pairs), 2)
        self.assertEqual(pairs[0].claude_branch, "claude/dual-teams/T1")
        self.assertEqual(pairs[0].codex_branch, "codex/dual-teams/T1")
        self.assertEqual(pairs[1].claude_branch, "claude/dual-teams/T2")
        self.assertEqual(pairs[1].codex_branch, "codex/dual-teams/T2")

    def test_prompt_file_paths(self):
        """AC5: prompt files live in work/<feature>/prompts/Ti-claude.md."""
        pairs = dts.build_plan([Path("tasks/T1.md")], self.root,
                               Path("worktrees/dual-teams"), "feat-x")
        self.assertTrue(pairs[0].claude_prompt_file.endswith(
            os.path.join("work", "feat-x", "prompts", "T1-claude.md")))


# ---------------------------------------------------------------------------
# Worktree tests (real git)
# ---------------------------------------------------------------------------


class CreateWorktreeTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        _init_repo(self.root)

    def tearDown(self):
        _cleanup_worktrees(self.root)
        try:
            self._tmp.cleanup()
        except PermissionError:
            import gc, time as _t
            gc.collect(); _t.sleep(0.2)
            shutil.rmtree(self._tmp.name, ignore_errors=True)

    def test_creates_on_new_branch(self):
        wt = self.root / "worktrees" / "T1"
        dts.create_worktree(self.root, wt, "claude/dual-teams/T1", base="HEAD")
        self.assertTrue(wt.is_dir())
        self.assertTrue((wt / "README.md").is_file())

    def test_failure_raises(self):
        wt = self.root / "worktrees" / "Tbad"
        with self.assertRaises(RuntimeError):
            dts.create_worktree(self.root, wt, "claude/dual-teams/Tbad",
                                base="nonexistent-ref-xyz")


# ---------------------------------------------------------------------------
# orchestrate (end-to-end with mocks)
# ---------------------------------------------------------------------------


class OrchestrateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        _init_repo(self.root)
        self.tasks_dir = self.root / "tasks"
        self.tasks_dir.mkdir()
        self.task_files = []
        for n in (1, 2):
            p = self.tasks_dir / f"T{n}.md"
            p.write_text(f"# T{n}\n", encoding="utf-8")
            self.task_files.append(p)
        self.log_dir = self.root / ".claude" / "logs"
        self.log_dir.mkdir(parents=True)

    def tearDown(self):
        _cleanup_worktrees(self.root)
        try:
            self._tmp.cleanup()
        except PermissionError:
            import gc, time as _t
            gc.collect(); _t.sleep(0.2)
            shutil.rmtree(self._tmp.name, ignore_errors=True)

    def _run_orchestrate(self, dry_run: bool = False, pid: int = 99999):
        with mock.patch.object(dts, "generate_claude_prompt",
                               side_effect=_fake_prompt), \
             mock.patch.object(dts, "launch_codex_wave",
                               side_effect=_fake_launch_factory(pid)):
            return dts.orchestrate(
                task_files=self.task_files, feature="demo",
                project_root=self.root,
                worktree_base=Path("worktrees/dual-teams"),
                parallel=2,
                codex_wave_script=Path(".claude/scripts/codex-wave.py"),
                spawn_agent_script=Path(".claude/scripts/spawn-agent.py"),
                log_dir=self.log_dir, base_branch="HEAD", dry_run=dry_run)

    def test_orchestrate_omits_result_dir_by_default(self):
        """Y9: no --result-dir flag is forwarded unless requested."""
        plan = self._run_orchestrate()
        self.assertIsNotNone(plan.wave)
        self.assertNotIn("--result-dir", plan.wave.cmd)
        self.assertIsNone(plan.wave.result_dir)

    def test_orchestrate_forwards_absolute_result_dir(self):
        """Y9: explicit result_dir is forwarded as an absolute path."""
        result_dir = self.root / "work" / "codex-implementations"
        with mock.patch.object(dts, "generate_claude_prompt",
                               side_effect=_fake_prompt), \
             mock.patch.object(dts, "launch_codex_wave",
                               side_effect=_fake_launch_factory()):
            plan = dts.orchestrate(
                task_files=self.task_files, feature="demo",
                project_root=self.root,
                worktree_base=Path("worktrees/dual-teams"),
                parallel=2,
                codex_wave_script=Path(".claude/scripts/codex-wave.py"),
                spawn_agent_script=Path(".claude/scripts/spawn-agent.py"),
                log_dir=self.log_dir, base_branch="HEAD", dry_run=False,
                result_dir=result_dir)
        expected = str(result_dir.resolve())
        self.assertIsNotNone(plan.wave)
        self.assertIn("--result-dir", plan.wave.cmd)
        self.assertEqual(plan.wave.cmd[plan.wave.cmd.index("--result-dir") + 1],
                         expected)
        self.assertEqual(plan.wave.result_dir, expected)

    def test_launch_codex_wave_resolves_relative_result_dir(self):
        """Y9: relative result_dir is resolved before entering argv."""
        popen = mock.Mock()
        popen.pid = 1234
        relative_result_dir = Path("work/codex-implementations")
        with mock.patch.object(dts.subprocess, "Popen", return_value=popen):
            wave = dts.launch_codex_wave(
                codex_wave_script=Path(".claude/scripts/codex-wave.py"),
                task_files=self.task_files,
                parallel=2,
                worktree_base=Path("worktrees/dual-teams/codex"),
                log_file=self.log_dir / "codex-wave.log",
                project_root=self.root,
                base_branch="HEAD",
                result_dir=relative_result_dir)
        expected = str(relative_result_dir.resolve())
        self.assertIn("--result-dir", wave.cmd)
        self.assertEqual(wave.cmd[wave.cmd.index("--result-dir") + 1],
                         expected)
        self.assertEqual(wave.result_dir, expected)

    def test_happy_path_two_tasks_four_worktrees(self):
        """AC1/AC2: 2 tasks => 4 worktrees, 2 prompts, 1 codex-wave pid."""
        plan = self._run_orchestrate()
        self.assertEqual(len(plan.pairs), 2)
        for pair in plan.pairs:
            self.assertTrue(Path(pair.claude_worktree).is_dir())
            self.assertTrue(Path(pair.codex_worktree).is_dir())
            self.assertTrue(Path(pair.claude_prompt_file).is_file())
            self.assertEqual(pair.claude_prompt_status, "ok")
        self.assertIsNotNone(plan.wave)
        self.assertTrue(plan.wave.started)
        self.assertEqual(plan.wave.pid, 99999)

    def test_dry_run_creates_nothing(self):
        """AC8: --dry-run prints plan but creates no worktrees/prompts."""
        plan = self._run_orchestrate(dry_run=True)
        self.assertEqual(len(plan.pairs), 2)
        self.assertTrue(plan.dry_run)
        for pair in plan.pairs:
            self.assertFalse(Path(pair.claude_worktree).exists())
            self.assertFalse(Path(pair.codex_worktree).exists())
            self.assertFalse(Path(pair.claude_prompt_file).exists())
        self.assertIsNone(plan.wave)

    def test_duplicate_worktree_rolled_back(self):
        """AC3: if a worktree fails, prior ones in this run are rolled back."""
        real_create = dts.create_worktree
        calls: list[Path] = []

        def flaky(project_root, worktree_path, branch, base="HEAD"):
            calls.append(worktree_path)
            if len(calls) == 4:  # fail on 2nd pair's codex worktree.
                raise RuntimeError("simulated worktree failure")
            return real_create(project_root, worktree_path, branch, base)

        with mock.patch.object(dts, "create_worktree", side_effect=flaky), \
             mock.patch.object(dts, "launch_codex_wave",
                               side_effect=_fake_launch_factory()):
            with self.assertRaises(RuntimeError):
                dts.orchestrate(
                    task_files=self.task_files, feature="demo",
                    project_root=self.root,
                    worktree_base=Path("worktrees/dual-teams"),
                    parallel=2,
                    codex_wave_script=Path(".claude/scripts/codex-wave.py"),
                    spawn_agent_script=Path(".claude/scripts/spawn-agent.py"),
                    log_dir=self.log_dir, base_branch="HEAD", dry_run=False)
        base = self.root / "worktrees" / "dual-teams"
        self.assertFalse((base / "claude" / "T1").is_dir())
        self.assertFalse((base / "codex" / "T1").is_dir())
        self.assertFalse((base / "claude" / "T2").is_dir())


# ---------------------------------------------------------------------------
# CLI-level tests: help, missing tasks, missing files, parallel default
# ---------------------------------------------------------------------------


class CliSmokeTests(unittest.TestCase):
    def test_help_exits_zero(self):
        """AC1: --help is available."""
        with self.assertRaises(SystemExit) as cm:
            dts.main(["--help"])
        self.assertEqual(cm.exception.code, 0)

    def test_missing_tasks_arg_exits_nonzero(self):
        with self.assertRaises(SystemExit) as cm:
            dts.main([])
        self.assertNotEqual(cm.exception.code, 0)

    def test_missing_task_file_exits_nonzero(self):
        """AC4: missing task file => clean error, exit non-zero."""
        with tempfile.TemporaryDirectory() as tmp:
            rc = dts.main([
                "--tasks", f"{tmp}/does-not-exist.md",
                "--feature", "demo",
                "--project-root", tmp,
            ])
            self.assertEqual(rc, 2)


class ParallelDefaultTests(unittest.TestCase):
    """AC1: --parallel defaults to number of tasks when 0/unset."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        _init_repo(self.root)
        self.tasks_dir = self.root / "tasks"
        self.tasks_dir.mkdir()
        self.task_files = []
        for n in (1, 2, 3):
            p = self.tasks_dir / f"T{n}.md"
            p.write_text(f"# T{n}\n", encoding="utf-8")
            self.task_files.append(p)

    def tearDown(self):
        _cleanup_worktrees(self.root)
        try:
            self._tmp.cleanup()
        except PermissionError:
            import gc, time as _t
            gc.collect(); _t.sleep(0.2)
            shutil.rmtree(self._tmp.name, ignore_errors=True)

    def test_dry_run_parallel_defaults_to_task_count(self):
        tasks_csv = ",".join(str(t) for t in self.task_files)
        rc = dts.main([
            "--tasks", tasks_csv,
            "--feature", "demo",
            "--project-root", str(self.root),
            "--dry-run",
        ])
        self.assertEqual(rc, 0)
        report = self.root / "work" / "demo" / "dual-teams-plan.md"
        self.assertTrue(report.is_file())
        text = report.read_text(encoding="utf-8")
        self.assertIn("parallel: 3", text)
        self.assertIn("DRY RUN", text)


# ---------------------------------------------------------------------------
# Report schema tests
# ---------------------------------------------------------------------------


class ReportSchemaTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_report_includes_required_sections(self):
        """AC5: report has feature, pairs, wave, Opus instructions."""
        plan = dts.PlanResult(
            feature="demo",
            timestamp="2026-04-24T00:00:00Z",
            worktree_base="worktrees/dual-teams",
            parallel=2,
            pairs=[
                dts.TaskPair(
                    task_id="T1", task_file="tasks/T1.md",
                    claude_worktree="/tmp/claude/T1",
                    claude_branch="claude/dual-teams/T1",
                    codex_worktree="/tmp/codex/T1",
                    codex_branch="codex/dual-teams/T1",
                    claude_prompt_file="work/demo/prompts/T1-claude.md",
                    claude_prompt_status="ok"),
            ],
            wave=dts.WavePlan(pid=12345,
                              cmd=["py", "codex-wave.py"],
                              log_file="/tmp/log",
                              started=True),
        )
        report = self.root / "plan.md"
        dts._write_report(report, plan)
        text = report.read_text(encoding="utf-8")
        self.assertIn("# dual-teams plan -- feature: demo", text)
        self.assertIn("## Task pairs", text)
        self.assertIn("### T1", text)
        self.assertIn("claude/dual-teams/T1", text)
        self.assertIn("codex/dual-teams/T1", text)
        self.assertIn("## Codex wave (background)", text)
        self.assertIn("pid: `12345`", text)
        self.assertIn("## Instructions for Opus", text)
        self.assertIn("cross-model-review", text)

    def test_report_wave_failure_included(self):
        plan = dts.PlanResult(
            feature="demo",
            timestamp="2026-04-24T00:00:00Z",
            worktree_base="worktrees/dual-teams",
            parallel=1, pairs=[],
            wave=dts.WavePlan(pid=None, cmd=["py", "codex-wave.py"],
                              log_file="/tmp/log", started=False,
                              error="not found"),
        )
        report = self.root / "plan.md"
        dts._write_report(report, plan)
        text = report.read_text(encoding="utf-8")
        self.assertIn("failed to start", text)
        self.assertIn("not found", text)

    def test_report_result_dir_included_when_set(self):
        result_dir = str((self.root / "work" / "codex-implementations").resolve())
        plan = dts.PlanResult(
            feature="demo",
            timestamp="2026-04-24T00:00:00Z",
            worktree_base="worktrees/dual-teams",
            parallel=1, pairs=[],
            wave=dts.WavePlan(pid=12345, cmd=["py", "codex-wave.py"],
                              log_file="/tmp/log", started=True,
                              result_dir=result_dir),
        )
        report = self.root / "plan.md"
        dts._write_report(report, plan)
        text = report.read_text(encoding="utf-8")
        self.assertIn(f"- result_dir: {result_dir}", text)

    def test_report_result_dir_omitted_when_unset(self):
        plan = dts.PlanResult(
            feature="demo",
            timestamp="2026-04-24T00:00:00Z",
            worktree_base="worktrees/dual-teams",
            parallel=1, pairs=[],
            wave=dts.WavePlan(pid=12345, cmd=["py", "codex-wave.py"],
                              log_file="/tmp/log", started=True),
        )
        report = self.root / "plan.md"
        dts._write_report(report, plan)
        text = report.read_text(encoding="utf-8")
        self.assertNotIn("- result_dir:", text)



class WriteBaseRefSidecarTests(unittest.TestCase):
    """AC6: create_worktree writes <wt>/.dual-base-ref with base SHA."""
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        _init_repo(self.root)
    def tearDown(self):
        subprocess.run(['git', 'worktree', 'prune'], cwd=str(self.root),
                       capture_output=True, check=False)
        try: self._tmp.cleanup()
        except PermissionError:
            shutil.rmtree(self._tmp.name, ignore_errors=True)
    def test_create_worktree_writes_sidecar(self):
        """AC1/AC5: .dual-base-ref = 40-char hex SHA + trailing \n."""
        wt = self.root / 'worktrees' / 'Tsc'
        dts.create_worktree(self.root, wt, 'claude/dual-teams/Tsc', base='HEAD')
        sidecar = wt / '.dual-base-ref'
        self.assertTrue(sidecar.is_file())
        content = sidecar.read_text(encoding='utf-8')
        self.assertTrue(content.endswith('\n'))
        sha = content.rstrip('\n')
        self.assertEqual(len(sha), 40)
        self.assertTrue(all(c in '0123456789abcdef' for c in sha))
        self.assertEqual(content.count('\n'), 1)
    def test_create_worktree_sidecar_failure_soft(self):
        """AC3: rev-parse fail => worktree ok, no sidecar, WARNING."""
        wt = self.root / 'worktrees' / 'Tsoft'
        real = dts._run
        def fake(cmd, cwd=None, timeout=None):
            if len(cmd) >= 2 and cmd[0] == 'git' and cmd[1] == 'rev-parse':
                return (128, '', 'fatal: not a valid object')
            return real(cmd, cwd=cwd, timeout=timeout)
        with mock.patch.object(dts, '_run', side_effect=fake), \
             self.assertLogs(dts.logger, level='WARNING') as cm:
            dts.create_worktree(self.root, wt, 'claude/dual-teams/Tsoft', base='HEAD')
        self.assertTrue(wt.is_dir())
        self.assertFalse((wt / '.dual-base-ref').exists())
        self.assertIn('write_base_ref_sidecar_revparse_failed', '\n'.join(cm.output))


if __name__ == "__main__":
    unittest.main(verbosity=2)
