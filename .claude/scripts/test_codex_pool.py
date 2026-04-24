"""Unit tests for codex-pool.py.

Never launches real codex processes; mocks subprocess.Popen and websocket.
Uses a temporary directory for state file.

Run: py -3 .claude/scripts/test_codex_pool.py
"""
from __future__ import annotations
import importlib.util, json, logging, os, sys, tempfile, time, unittest
from pathlib import Path
from unittest import mock

SCRIPT_PATH = Path(__file__).parent / "codex-pool.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("codex_pool", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["codex_pool"] = mod
    spec.loader.exec_module(mod)
    return mod


pool = _load_module()
logging.getLogger("codex_pool").setLevel(logging.CRITICAL)


def _make_args(**kw):
    import argparse
    ns = argparse.Namespace()
    for k, v in kw.items():
        setattr(ns, k, v)
    return ns


class StateRoundTripTest(unittest.TestCase):
    def test_pool_state_roundtrip(self):
        inst1 = pool.Instance(pool_id=0, port=4510, pid=11111, start_time=1_700_000_000.0)
        inst2 = pool.Instance(pool_id=1, port=4511, pid=22222, start_time=1_700_000_000.5)
        state = pool.PoolState(schema_version=1, created_at=1_700_000_000.0, instances=[inst1, inst2])
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / ".codex" / "pool-state.json"
            pool.save_state(p, state)
            self.assertTrue(p.exists())
            raw = json.loads(p.read_text(encoding="utf-8"))
            self.assertEqual(raw["schema_version"], 1)
            self.assertEqual(len(raw["instances"]), 2)
            self.assertEqual(raw["instances"][0]["port"], 4510)
            reloaded = pool.load_state(p)
            self.assertEqual(len(reloaded.instances), 2)
            self.assertEqual(reloaded.instances[1].pid, 22222)
            self.assertEqual(reloaded.schema_version, 1)

    def test_load_state_missing_returns_empty(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "does-not-exist.json"
            state = pool.load_state(p)
            self.assertEqual(state.instances, [])
            self.assertEqual(state.schema_version, pool.SCHEMA_VERSION)

    def test_load_state_corrupt_returns_empty(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "bad.json"
            p.write_text("{not json", encoding="utf-8")
            state = pool.load_state(p)
            self.assertEqual(state.instances, [])


class StartTest(unittest.TestCase):
    def test_start_default_size_is_2(self):
        parser = pool.build_parser()
        args = parser.parse_args(["start"])
        self.assertEqual(args.size, 2)
        self.assertEqual(args.base_port, 4510)

    def test_start_creates_n_instances_and_state(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fake_pids = [50000, 50001, 50002]
            popen_mock = mock.MagicMock()
            popen_mock.side_effect = [mock.MagicMock(pid=p) for p in fake_pids]
            with mock.patch.object(pool, "resolve_codex_bin", return_value="/fake/codex"), \
                 mock.patch.object(pool, "allocate_ports", return_value=[4510, 4511, 4512]), \
                 mock.patch.object(pool.subprocess, "Popen", popen_mock):
                rc = pool.cmd_start(_make_args(size=3, base_port=4510), root)
            self.assertEqual(rc, 0)
            state = pool.load_state(root / pool.STATE_REL)
            self.assertEqual(len(state.instances), 3)
            ports = sorted(i.port for i in state.instances)
            self.assertEqual(ports, [4510, 4511, 4512])
            pids = sorted(i.pid for i in state.instances)
            self.assertEqual(pids, sorted(fake_pids))

    def test_start_refuses_when_live_instances_recorded(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".codex").mkdir()
            existing = pool.PoolState(instances=[pool.Instance(0, 4510, 99999, time.time())])
            pool.save_state(root / pool.STATE_REL, existing)
            with mock.patch.object(pool, "pid_alive", return_value=True):
                rc = pool.cmd_start(_make_args(size=1, base_port=4510), root)
            self.assertEqual(rc, 1)

    def test_start_cleans_stale_entries_before_launch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".codex").mkdir()
            stale = pool.PoolState(instances=[pool.Instance(0, 4510, 1, time.time() - 3600)])
            pool.save_state(root / pool.STATE_REL, stale)
            popen_mock = mock.MagicMock(return_value=mock.MagicMock(pid=70000))
            with mock.patch.object(pool, "pid_alive", return_value=False), \
                 mock.patch.object(pool, "resolve_codex_bin", return_value="/fake/codex"), \
                 mock.patch.object(pool, "allocate_ports", return_value=[4510]), \
                 mock.patch.object(pool.subprocess, "Popen", popen_mock):
                rc = pool.cmd_start(_make_args(size=1, base_port=4510), root)
            self.assertEqual(rc, 0)
            state = pool.load_state(root / pool.STATE_REL)
            self.assertEqual(len(state.instances), 1)
            self.assertEqual(state.instances[0].pid, 70000)


class StopTest(unittest.TestCase):
    def test_stop_terminates_all_and_removes_state(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state = pool.PoolState(instances=[
                pool.Instance(0, 4510, 50000, time.time()),
                pool.Instance(1, 4511, 50001, time.time()),
            ])
            pool.save_state(root / pool.STATE_REL, state)
            killed = []
            def fake_kill(pid, grace_seconds=pool.POSIX_GRACE_SECONDS):
                killed.append(pid); return True
            with mock.patch.object(pool, "terminate_pid", side_effect=fake_kill):
                rc = pool.cmd_stop(_make_args(), root)
            self.assertEqual(rc, 0)
            self.assertEqual(sorted(killed), [50000, 50001])
            self.assertFalse((root / pool.STATE_REL).exists())

    def test_stop_noop_when_no_state(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rc = pool.cmd_stop(_make_args(), root)
            self.assertEqual(rc, 0)


class StatusTest(unittest.TestCase):
    def test_status_table_has_header_and_rows(self):
        state = pool.PoolState(instances=[
            pool.Instance(0, 4510, 100, 0.0),
            pool.Instance(1, 4511, 200, 0.0),
        ])
        alive = {100: True, 200: False}
        table = pool.render_status_table(state, now=5.0, alive_map=alive)
        self.assertIn("pool_id", table)
        self.assertIn("4510", table)
        self.assertIn("4511", table)
        self.assertIn("yes", table)
        self.assertIn("no", table)
        self.assertIn("summary: 1/2 alive", table)
        self.assertIn("schema_version=1", table)

    def test_status_empty_state_message(self):
        state = pool.PoolState()
        table = pool.render_status_table(state, now=0.0, alive_map={})
        self.assertIn("empty", table)


class HealthTest(unittest.TestCase):
    def test_health_check_tcp_fail(self):
        with mock.patch.object(pool.socket, "create_connection",
                               side_effect=OSError("refused")):
            ok, msg = pool.health_check_port(44444, timeout=0.1)
        self.assertFalse(ok)
        self.assertIn("tcp", msg)

    def test_health_check_ws_ok(self):
        fake_ws = mock.MagicMock(); fake_ws.close = mock.MagicMock()
        fake_create = mock.MagicMock(return_value=fake_ws)
        fake_client = mock.MagicMock()
        fake_client.create_connection = fake_create
        fake_tcp = mock.MagicMock()
        fake_tcp.__enter__ = mock.MagicMock(return_value=fake_tcp)
        fake_tcp.__exit__ = mock.MagicMock(return_value=False)
        with mock.patch.object(pool.socket, "create_connection", return_value=fake_tcp), \
             mock.patch.dict("sys.modules", {"websocket": fake_client}):
            ok, msg = pool.health_check_port(4510, timeout=0.2)
        self.assertTrue(ok)
        self.assertIn("ws-ok", msg)
        fake_create.assert_called_once()

    def test_health_check_ws_missing_graceful(self):
        fake_tcp = mock.MagicMock()
        fake_tcp.__enter__ = mock.MagicMock(return_value=fake_tcp)
        fake_tcp.__exit__ = mock.MagicMock(return_value=False)
        # Simulate ImportError for websocket by pre-inserting a sentinel then
        # replacing import lookup via builtins.__import__.
        import builtins
        real_import = builtins.__import__
        def fake_import(name, *a, **kw):
            if name == "websocket":
                raise ImportError("no websocket-client")
            return real_import(name, *a, **kw)
        with mock.patch.object(pool.socket, "create_connection", return_value=fake_tcp), \
             mock.patch.object(builtins, "__import__", side_effect=fake_import):
            ok, msg = pool.health_check_port(4510, timeout=0.2)
        self.assertTrue(ok)
        self.assertIn("tcp-ok", msg)


class TerminationBranchTest(unittest.TestCase):
    def test_terminate_pid_windows_branch_calls_taskkill(self):
        fake_run = mock.MagicMock(return_value=mock.MagicMock(returncode=0, stdout=""))
        with mock.patch.object(pool.sys, "platform", "win32"), \
             mock.patch.object(pool.subprocess, "run", fake_run):
            ok = pool.terminate_pid(12345)
        self.assertTrue(ok)
        argv = fake_run.call_args[0][0]
        self.assertEqual(argv[:4], ["taskkill", "/T", "/F", "/PID"])
        self.assertEqual(argv[4], "12345")

    def test_terminate_pid_posix_sigterm_then_sigkill(self):
        # Force the POSIX branch regardless of host.
        kill_calls = []
        def fake_kill(pid, sig):
            kill_calls.append((pid, sig))
        alive_answers = [True, True, False]
        def fake_alive(pid):
            return alive_answers.pop(0) if alive_answers else False
        with mock.patch.object(pool.sys, "platform", "linux"), \
             mock.patch.object(pool.os, "kill", side_effect=fake_kill), \
             mock.patch.object(pool, "pid_alive", side_effect=fake_alive), \
             mock.patch.object(pool.time, "monotonic", side_effect=[0.0, 0.1, 0.2, 0.3, 10.0]):
            ok = pool.terminate_pid(9999, grace_seconds=1.0)
        self.assertTrue(ok)
        # SIGTERM sent first; if pid_alive returned True past deadline, SIGKILL sent.
        self.assertTrue(any(call[1] == pool.signal.SIGTERM for call in kill_calls))


class PortAllocTest(unittest.TestCase):
    def test_allocate_ports_skips_busy(self):
        # Pretend 4510 busy, 4511 free, 4512 free
        responses = {4510: False, 4511: True, 4512: True, 4513: True}
        def fake_port_free(port, host="127.0.0.1"):
            return responses.get(port, True)
        with mock.patch.object(pool, "port_free", side_effect=fake_port_free):
            ports = pool.allocate_ports(2, 4510)
        self.assertEqual(ports, [4511, 4512])

    def test_allocate_ports_raises_when_none_free(self):
        with mock.patch.object(pool, "port_free", return_value=False):
            with self.assertRaises(RuntimeError):
                pool.allocate_ports(1, 5000)


class CliParserTest(unittest.TestCase):
    def test_parser_required_subcommand(self):
        parser = pool.build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args([])

    def test_parser_health_has_timeout(self):
        parser = pool.build_parser()
        args = parser.parse_args(["health", "--timeout", "0.5"])
        self.assertEqual(args.cmd, "health")
        self.assertAlmostEqual(args.timeout, 0.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)