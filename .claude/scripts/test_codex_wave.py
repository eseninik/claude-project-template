"""Unit tests for codex-wave.py.

Mocks codex-implement.py subprocess invocations; never actually calls Codex.
Uses a real temporary git repo to exercise worktree creation on Windows.

Run: py -3 .claude/scripts/test_codex_wave.py
"""

from __future__ import annotations

import importlib.util
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).parent / "codex-wave.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("codex_wave", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    # Must register before exec_module so dataclass can resolve the module.
    sys.modules["codex_wave"] = mod
    spec.loader.exec_module(mod)
    return mod


wave = _load_module()


logging.getLogger("codex_wave").setLevel(logging.CRITICAL)


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.setdefault("GIT_AUTHOR_NAME", "test")
    env.setdefault("GIT_AUTHOR_EMAIL", "test@example.com")
    env.setdefault("GIT_COMMITTER_NAME", "test")
    env.setdefault("GIT_COMMITTER_EMAIL", "test@example.com")
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


def _init_repo(path: Path) -> None:
    _git(["init", "-b", "main"], cwd=path)
    _git(["config", "user.email", "test@example.com"], cwd=path)
    _git(["config", "user.name", "test"], cwd=path)
    (path / "README.md").write_text("hello\n", encoding="utf-8")
    _git(["add", "README.md"], cwd=path)
    _git(["commit", "-m", "init"], cwd=path)


# -----------------------------------------------------------------------------
# Pure-function tests (no filesystem)
# -----------------------------------------------------------------------------


class DeriveTaskIdTests(unittest.TestCase):
    def test_numeric_id(self):
        self.assertEqual(wave.derive_task_id(Path("tasks/T1.md")), "T1")
        self.assertEqual(wave.derive_task_id(Path("tasks/T42-foo.md")), "T42")

    def test_lowercase_t(self):
        self.assertEqual(wave.derive_task_id(Path("t7-thing.md")), "T7")

    def test_fallback_to_stem(self):
        self.assertEqual(
            wave.derive_task_id(Path("tasks/misc-task.md")), "misc-task"
        )


class ExpandTasksTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "tasks").mkdir()
        for n in (1, 2, 3):
            (self.root / "tasks" / f"T{n}.md").write_text("x", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_literal_csv(self):
        arg = f"{self.root}/tasks/T1.md,{self.root}/tasks/T2.md"
        result = wave.expand_tasks(arg)
        self.assertEqual(len(result), 2)
        self.assertTrue(all(p.name.startswith("T") for p in result))

    def test_glob_expansion(self):
        arg = str(self.root / "tasks" / "T*.md")
        result = wave.expand_tasks(arg)
        self.assertEqual(len(result), 3)

    def test_csv_of_globs_dedupes(self):
        arg = (
            f"{self.root / 'tasks' / 'T*.md'},"
            f"{self.root / 'tasks' / 'T1.md'}"
        )
        result = wave.expand_tasks(arg)
        self.assertEqual(len(result), 3)  # T1 dedup'd

    def test_empty_returns_empty(self):
        self.assertEqual(wave.expand_tasks(""), [])


class StatusFromExitTests(unittest.TestCase):
    def test_map(self):
        self.assertEqual(wave._status_from_exit(0), "pass")
        self.assertEqual(wave._status_from_exit(1), "fail")
        self.assertEqual(wave._status_from_exit(2), "scope-violation")
        self.assertEqual(wave._status_from_exit(99), "error")


class ExcerptTests(unittest.TestCase):
    def test_short_passthrough(self):
        self.assertEqual(wave._excerpt("hi"), "hi")

    def test_long_truncated(self):
        text = "x" * 3000
        out = wave._excerpt(text, limit=1000)
        self.assertTrue(out.startswith("x" * 1000))
        self.assertIn("truncated", out)


# -----------------------------------------------------------------------------
# Worktree creation (real git, real filesystem)
# -----------------------------------------------------------------------------


class CreateWorktreeTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        _init_repo(self.root)

    def tearDown(self):
        # Best-effort: clean worktree registrations before removing dir.
        try:
            subprocess.run(
                ["git", "worktree", "prune"],
                cwd=str(self.root),
                capture_output=True,
                check=False,
            )
        except Exception:
            pass
        try:
            self._tmp.cleanup()
        except PermissionError:
            # Windows can hold file handles briefly; retry once after gc.
            import gc, time as _t
            gc.collect()
            _t.sleep(0.2)
            try:
                shutil.rmtree(self._tmp.name, ignore_errors=True)
            except Exception:
                pass

    def test_creates_worktree_on_new_branch(self):
        wt = self.root / "worktrees" / "T1"
        wave.create_worktree(self.root, wt, "codex-wave/T1", base="HEAD")
        self.assertTrue(wt.is_dir())
        self.assertTrue((wt / "README.md").is_file())

    def test_failure_raises(self):
        # Use a bogus base ref to force git to fail.
        wt = self.root / "worktrees" / "Tbad"
        with self.assertRaises(RuntimeError):
            wave.create_worktree(
                self.root, wt, "codex-wave/Tbad", base="nonexistent-ref-xyz"
            )


# -----------------------------------------------------------------------------
# process_task with mocked codex-implement
# -----------------------------------------------------------------------------


class ProcessTaskTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        _init_repo(self.root)
        self.task_file = self.root / "tasks" / "T1.md"
        self.task_file.parent.mkdir()
        self.task_file.write_text("# T1\nfake task", encoding="utf-8")
        self.result_dir = self.root / "work" / "codex-implementations"
        self.result_dir.mkdir(parents=True)

    def tearDown(self):
        try:
            subprocess.run(
                ["git", "worktree", "prune"],
                cwd=str(self.root),
                capture_output=True,
                check=False,
            )
        except Exception:
            pass
        try:
            self._tmp.cleanup()
        except PermissionError:
            import gc, time as _t
            gc.collect()
            _t.sleep(0.2)
            shutil.rmtree(self._tmp.name, ignore_errors=True)

    def test_pass_captures_result_md(self):
        # Write a fake result.md ahead of time; mock the subprocess to "pass".
        (self.result_dir / "task-T1-result.md").write_text(
            "status: pass\ntests: 3/3", encoding="utf-8"
        )
        with mock.patch.object(
            wave, "run_codex_implement",
            return_value=(0, "implement stdout", ""),
        ):
            r = wave.process_task(
                task_file=self.task_file,
                project_root=self.root,
                worktree_base=Path("worktrees/codex-wave"),
                implement_script=Path("/fake/codex-implement.py"),
                timeout=10,
                result_dir=self.result_dir,
                base_branch="HEAD",
            )
        self.assertEqual(r.status, "pass")
        self.assertEqual(r.exit_code, 0)
        self.assertIn("status: pass", r.result_md_excerpt)
        self.assertTrue(r.worktree_path.endswith("T1"))

    def test_fail_exit_1(self):
        with mock.patch.object(
            wave, "run_codex_implement",
            return_value=(1, "", "tests failed"),
        ):
            r = wave.process_task(
                task_file=self.task_file,
                project_root=self.root,
                worktree_base=Path("worktrees/codex-wave"),
                implement_script=Path("/fake/codex-implement.py"),
                timeout=10,
                result_dir=self.result_dir,
                base_branch="HEAD",
            )
        self.assertEqual(r.status, "fail")

    def test_scope_violation_exit_2(self):
        with mock.patch.object(
            wave, "run_codex_implement",
            return_value=(2, "", "scope breach"),
        ):
            r = wave.process_task(
                task_file=self.task_file,
                project_root=self.root,
                worktree_base=Path("worktrees/codex-wave"),
                implement_script=Path("/fake/codex-implement.py"),
                timeout=10,
                result_dir=self.result_dir,
                base_branch="HEAD",
            )
        self.assertEqual(r.status, "scope-violation")

    def test_timeout_recorded(self):
        def _raise_timeout(*a, **kw):
            raise subprocess.TimeoutExpired(cmd=["fake"], timeout=10)
        with mock.patch.object(wave, "run_codex_implement", side_effect=_raise_timeout):
            r = wave.process_task(
                task_file=self.task_file,
                project_root=self.root,
                worktree_base=Path("worktrees/codex-wave"),
                implement_script=Path("/fake/codex-implement.py"),
                timeout=10,
                result_dir=self.result_dir,
                base_branch="HEAD",
            )
        self.assertEqual(r.status, "timeout")
        self.assertIn("timed out", (r.error or ""))

    def test_implement_crash_isolated(self):
        def _boom(*a, **kw):
            raise RuntimeError("ugly crash")
        with mock.patch.object(wave, "run_codex_implement", side_effect=_boom):
            r = wave.process_task(
                task_file=self.task_file,
                project_root=self.root,
                worktree_base=Path("worktrees/codex-wave"),
                implement_script=Path("/fake/codex-implement.py"),
                timeout=10,
                result_dir=self.result_dir,
                base_branch="HEAD",
            )
        self.assertEqual(r.status, "error")
        self.assertIn("ugly crash", (r.error or ""))


# -----------------------------------------------------------------------------
# run_wave parallel + failure isolation
# -----------------------------------------------------------------------------


class RunWaveTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        _init_repo(self.root)
        self.tasks_dir = self.root / "tasks"
        self.tasks_dir.mkdir()
        self.task_files = []
        for n in (1, 2, 3):
            p = self.tasks_dir / f"T{n}.md"
            p.write_text(f"task {n}", encoding="utf-8")
            self.task_files.append(p)
        self.result_dir = self.root / "results"
        self.result_dir.mkdir()

    def tearDown(self):
        try:
            subprocess.run(
                ["git", "worktree", "prune"],
                cwd=str(self.root),
                capture_output=True,
                check=False,
            )
        except Exception:
            pass
        try:
            self._tmp.cleanup()
        except PermissionError:
            import gc, time as _t
            gc.collect()
            _t.sleep(0.2)
            shutil.rmtree(self._tmp.name, ignore_errors=True)

    def test_parallel_launcher_one_failure_isolated(self):
        # Task T2 "fails" (rc=1). Others pass. Wave must complete all 3.
        call_log: list[str] = []
        lock = threading.Lock()

        def fake_impl(implement_script, task_file, worktree_path, timeout, result_dir=None):
            with lock:
                call_log.append(task_file.name)
            # T2 → fail, others → pass
            if "T2" in task_file.name:
                return (1, "", "test failure")
            return (0, "ok", "")

        with mock.patch.object(wave, "run_codex_implement", side_effect=fake_impl):
            results = wave.run_wave(
                task_files=self.task_files,
                project_root=self.root,
                worktree_base=Path("worktrees/codex-wave"),
                implement_script=Path("/fake/codex-implement.py"),
                parallel=2,
                timeout=10,
                result_dir=self.result_dir,
                base_branch="HEAD",
            )

        self.assertEqual(len(results), 3)
        statuses = {r.task_id: r.status for r in results}
        self.assertEqual(statuses["T1"], "pass")
        self.assertEqual(statuses["T2"], "fail")
        self.assertEqual(statuses["T3"], "pass")
        self.assertEqual(sorted(call_log), ["T1.md", "T2.md", "T3.md"])

    def test_parallel_respects_semaphore(self):
        # Confirm no more than --parallel workers hold the fake call at once.
        in_flight = 0
        peak = 0
        lock = threading.Lock()

        def fake_impl(implement_script, task_file, worktree_path, timeout, result_dir=None):
            nonlocal in_flight, peak
            with lock:
                in_flight += 1
                peak = max(peak, in_flight)
            time.sleep(0.05)  # small window
            with lock:
                in_flight -= 1
            return (0, "ok", "")

        with mock.patch.object(wave, "run_codex_implement", side_effect=fake_impl):
            results = wave.run_wave(
                task_files=self.task_files,
                project_root=self.root,
                worktree_base=Path("worktrees/codex-wave"),
                implement_script=Path("/fake/codex-implement.py"),
                parallel=2,
                timeout=10,
                result_dir=self.result_dir,
                base_branch="HEAD",
            )
        self.assertEqual(len(results), 3)
        self.assertLessEqual(peak, 2, f"peak concurrency {peak} exceeds --parallel=2")

    def test_empty_tasks_returns_empty(self):
        r = wave.run_wave(
            task_files=[],
            project_root=self.root,
            worktree_base=Path("worktrees/codex-wave"),
            implement_script=Path("/fake/codex-implement.py"),
            parallel=2,
            timeout=10,
            result_dir=self.result_dir,
            base_branch="HEAD",
        )
        self.assertEqual(r, [])


# -----------------------------------------------------------------------------
# write_report
# -----------------------------------------------------------------------------


class WriteReportTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_report_contains_worktree_paths_and_statuses(self):
        results = [
            wave.TaskResult(
                task_id="T1",
                task_file="tasks/T1.md",
                worktree_path="worktrees/codex-wave/T1",
                branch="codex-wave/T1",
                status="pass",
                exit_code=0,
                duration_s=12.3,
                result_md_path="results/task-T1-result.md",
                result_md_excerpt="status: pass",
            ),
            wave.TaskResult(
                task_id="T2",
                task_file="tasks/T2.md",
                worktree_path="worktrees/codex-wave/T2",
                branch="codex-wave/T2",
                status="fail",
                exit_code=1,
                duration_s=5.0,
                stderr="boom",
            ),
        ]
        report = self.root / "wave-report.md"
        wave._write_report(report, results)
        text = report.read_text(encoding="utf-8")
        # AC12: worktree paths logged prominently
        self.assertIn("worktrees/codex-wave/T1", text)
        self.assertIn("worktrees/codex-wave/T2", text)
        self.assertIn("NOT auto-merged", text)
        self.assertIn("pass", text)
        self.assertIn("fail", text)
        self.assertIn("boom", text)


# -----------------------------------------------------------------------------
# CLI smoke (argparse --help)
# -----------------------------------------------------------------------------


class CliSmokeTests(unittest.TestCase):
    def test_help_exits_zero(self):
        with self.assertRaises(SystemExit) as cm:
            wave.main(["--help"])
        self.assertEqual(cm.exception.code, 0)

    def test_missing_tasks_arg_exits_nonzero(self):
        with self.assertRaises(SystemExit) as cm:
            wave.main([])
        self.assertNotEqual(cm.exception.code, 0)



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
        wave.create_worktree(self.root, wt, 'codex-wave/Tsc', base='HEAD')
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
        real = wave._run
        def fake(cmd, cwd=None, timeout=None):
            if len(cmd) >= 2 and cmd[0] == 'git' and cmd[1] == 'rev-parse':
                return (128, '', 'fatal: not a valid object')
            return real(cmd, cwd=cwd, timeout=timeout)
        with mock.patch.object(wave, '_run', side_effect=fake), \
             self.assertLogs(wave.logger, level='WARNING') as cm:
            wave.create_worktree(self.root, wt, 'codex-wave/Tsoft', base='HEAD')
        self.assertTrue(wt.is_dir())
        self.assertFalse((wt / '.dual-base-ref').exists())
        self.assertIn('write_base_ref_sidecar_revparse_failed', '\n'.join(cm.output))


if __name__ == "__main__":
    unittest.main(verbosity=2)
