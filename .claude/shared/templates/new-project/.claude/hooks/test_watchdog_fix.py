#!/usr/bin/env python3
"""Unit tests for watchdog-dushnost fix.

Covers (per spec.md AC1-AC7):
  AC1: Severity triage — HALT/WARN/OBSERVE act correctly.
  AC2: HALT confidence gating (>=0.85).
  AC3: Signature dedup prevents re-analysis.
  AC4: Post-HALT cooldown caps subsequent stops at WARN.
  AC5: Task-class classifier maps prompts correctly.
  AC6: FP replay — Linear MCP case does NOT trigger HALT.
  AC7: Override file honored.

Run:
  py -3 .claude/hooks/test_watchdog_fix.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

HOOKS_DIR = Path(__file__).resolve().parent


def _load_module(name: str, filename: str):
    """Load a hook module by file path (needed because filenames have dashes)."""
    spec = importlib.util.spec_from_file_location(name, HOOKS_DIR / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


watchdog = _load_module("cwd_watchdog", "codex-watchdog.py")
classifier = _load_module("cwd_classifier", "session-task-class.py")


# ---------------------------------------------------------------------------
# AC5 — Classifier
# ---------------------------------------------------------------------------

class TestClassifier(unittest.TestCase):
    """AC5: Task-class detector works across all 6 classes."""

    CASES = [
        ("а что там по задаче?", "chat"),
        ("привет, что думаешь?", "chat"),
        ("спасибо, ок", "chat"),
        ("переименуй переменную foo в bar", "typo"),
        ("rename the variable userID", "typo"),
        ("почини баг с логином, не работает", "bugfix"),
        ("fix the failing test in auth.py", "bugfix"),
        ("добавь новый endpoint для api", "feature"),
        ("implement a new caching layer", "feature"),
        ("отрефактори модуль auth полностью", "refactor"),
        ("migrate this module to async", "refactor"),
        ("задеплой на прод через ssh", "deploy"),
        ("deploy to production now", "deploy"),
    ]

    def test_all_cases(self):
        for prompt, expected in self.CASES:
            with self.subTest(prompt=prompt):
                got = classifier.classify(prompt)
                self.assertEqual(got, expected,
                                 f"'{prompt}' → {got}, expected {expected}")

    def test_empty_prompt_is_chat(self):
        self.assertEqual(classifier.classify(""), "chat")
        self.assertEqual(classifier.classify("   "), "chat")

    def test_unknown_prompt_falls_back_to_feature(self):
        got = classifier.classify(
            "не могу вспомнить что мы обсуждали вчера по этой теме "
            "дайте контекст пожалуйста и давайте продолжим"
        )
        self.assertEqual(got, "feature")


# ---------------------------------------------------------------------------
# AC3 — Signature dedup
# ---------------------------------------------------------------------------

class TestSignatureDedup(unittest.TestCase):

    def test_sig_hash_stable(self):
        r = "some response " * 100
        self.assertEqual(watchdog.sig_hash(r), watchdog.sig_hash(r))

    def test_sig_hash_differs_on_tail_change(self):
        a = "x" * 100 + " response A"
        b = "x" * 100 + " response B"
        self.assertNotEqual(watchdog.sig_hash(a), watchdog.sig_hash(b))


# ---------------------------------------------------------------------------
# AC2 — HALT confidence gating
# ---------------------------------------------------------------------------

class TestConfidenceGating(unittest.TestCase):

    def test_parse_valid_halt_verdict(self):
        raw = '{"severity":"HALT","confidence":0.92,"reason":"lied","evidence":"x"}'
        v = watchdog._parse_codex_verdict(raw)
        self.assertEqual(v["severity"], "HALT")
        self.assertAlmostEqual(v["confidence"], 0.92, places=2)

    def test_parse_low_confidence_halt_still_parses(self):
        raw = '{"severity":"HALT","confidence":0.6,"reason":"maybe","evidence":"x"}'
        v = watchdog._parse_codex_verdict(raw)
        self.assertEqual(v["severity"], "HALT")
        self.assertLess(v["confidence"], watchdog.HALT_CONFIDENCE_THRESHOLD)

    def test_parse_invalid_severity_returns_none(self):
        raw = '{"severity":"BLOCKER","confidence":0.9}'
        self.assertIsNone(watchdog._parse_codex_verdict(raw))

    def test_parse_non_json_returns_none(self):
        self.assertIsNone(watchdog._parse_codex_verdict("OK"))
        self.assertIsNone(watchdog._parse_codex_verdict(""))

    def test_parse_json_in_markdown_fences(self):
        raw = ('Verdict:\n```json\n'
               '{"severity":"WARN","confidence":0.7,"reason":"x","evidence":"y"}'
               '\n```')
        v = watchdog._parse_codex_verdict(raw)
        self.assertIsNotNone(v)
        self.assertEqual(v["severity"], "WARN")


# ---------------------------------------------------------------------------
# AC1 — Severity cap
# ---------------------------------------------------------------------------

class TestSeverityCap(unittest.TestCase):

    def test_cap_halt_to_warn(self):
        self.assertEqual(watchdog.cap_severity("HALT", "WARN"), "WARN")

    def test_cap_warn_to_observe(self):
        self.assertEqual(watchdog.cap_severity("WARN", "OBSERVE"), "OBSERVE")

    def test_no_cap_when_equal(self):
        self.assertEqual(watchdog.cap_severity("HALT", "HALT"), "HALT")

    def test_no_cap_when_below(self):
        self.assertEqual(watchdog.cap_severity("OBSERVE", "HALT"), "OBSERVE")


# ---------------------------------------------------------------------------
# AC1 — Pre-filter
# ---------------------------------------------------------------------------

class TestPreFilter(unittest.TestCase):

    def test_too_short_skips(self):
        self.assertFalse(watchdog.should_analyze("hi", "feature"))

    def test_chat_class_disabled(self):
        long_text = "x" * 500 + " готово commit"
        self.assertFalse(watchdog.should_analyze(long_text, "chat"))

    def test_no_hard_signals_skips(self):
        long_text = (
            "Linear MCP работает — отдаёт реальные данные. list_issues "
            "вернул 5 issues. search_issues выполнил поиск. Старый "
            "list_projects падает из-за схемы сервера, обход через "
            "list_issues с фильтром."
        ) * 2
        self.assertFalse(watchdog.should_analyze(long_text, "feature"))

    def test_hard_signal_plus_length_triggers(self):
        text = (
            "Я завершил работу. Часть тестов не запускал — они не критично. "
            "Можно commit. " * 10
        )
        self.assertTrue(watchdog.should_analyze(text, "feature"))


# ---------------------------------------------------------------------------
# TRUE POSITIVES — watchdog MUST analyze these (symmetric to FP tests)
# ---------------------------------------------------------------------------

class TestTruePositives(unittest.TestCase):
    """Responses that genuinely warrant Codex analysis must pass pre-filter.

    These are the anti-test to AC6 — verify watchdog is NOT too passive.
    Without this coverage, narrowing pre-filter could silently break
    the watchdog's ability to catch real quality shortcuts.
    """

    def test_tp_skip_test_before_commit(self):
        r = ("Реализовал фичу. Тесты пока без запуска — не критично, "
             "закоммичу и задеплой на прод сразу. " * 6)
        self.assertTrue(watchdog.should_analyze(r, "feature"),
                        "skip_test + commit + deploy MUST trigger analysis")

    def test_tp_partial_work_with_deploy(self):
        r = ("Готово. Можно закоммитить. Осталось пару edge cases, но пока "
             "не критично — оставим на потом. Push в production. " * 4)
        self.assertTrue(watchdog.should_analyze(r, "feature"),
                        "partial + deploy MUST trigger")

    def test_tp_acknowledged_failure_proceeding(self):
        r = ("Тесты не запускал на этом модуле, но commit делаю всё равно — "
             "задеплой завершён, работает. " * 5)
        self.assertTrue(watchdog.should_analyze(r, "feature"),
                        "no_tests + commit + deploy MUST trigger")

    def test_tp_triggers_in_deploy_class(self):
        r = ("Закоммитил релиз. Часть проверок не запускал — не критично. " * 4)
        self.assertTrue(watchdog.should_analyze(r, "deploy"),
                        "In deploy class, any quality shortcut MUST trigger")

    def test_tp_chat_still_skipped_even_with_signals(self):
        """Exception: even TP signals are skipped under `chat` class.

        This is by design — user asking about a PAST commit is not grounds
        for watchdog wake. User is the one making statements, not Claude.
        """
        r = ("Да, помню — мы в тот commit не запускали тесты, было не критично, "
             "и задеплоил сразу. " * 5)
        self.assertFalse(watchdog.should_analyze(r, "chat"),
                         "chat class disables watchdog by design")


# ---------------------------------------------------------------------------
# AC6 — FP replay (Linear MCP case)
# ---------------------------------------------------------------------------

class TestFPReplay(unittest.TestCase):
    """AC6: Today's live FP must not trigger analysis under any realistic class."""

    LINEAR_MCP_RESPONSE = """Да, Linear MCP полностью живой — отдаёт реальные данные, не заглушку.

Доказательства из только что выполненного запроса:
list_issues вернул 5 реальных issues (MIG-83, MIG-82, MIG-67, MIG-65, MIG-8, MIG-7).
search_issues вернул MIG-65 «Технический апдейт до уровня Knowledge Bot Legal».

Эти UUID не могли бы быть сгенерированы из кэша — значит поиск реально идёт на сервер.

Старый баг list_projects — это проблема сервера линейского MCP, обходится через
list_issues с фильтром project без отдельного list_projects."""

    def test_fp_chat_class_skips_entirely(self):
        self.assertFalse(watchdog.should_analyze(self.LINEAR_MCP_RESPONSE, "chat"))

    def test_fp_feature_class_no_hard_signals(self):
        self.assertFalse(watchdog.should_analyze(self.LINEAR_MCP_RESPONSE, "feature"))

    def test_fp_deploy_class_no_hard_signals(self):
        self.assertFalse(watchdog.should_analyze(self.LINEAR_MCP_RESPONSE, "deploy"))


# ---------------------------------------------------------------------------
# AC7 — Override file honored
# ---------------------------------------------------------------------------

class TestOverride(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.tmpdir.name)
        (self.project_dir / ".codex").mkdir()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_active_override_returns_class(self):
        override_path = self.project_dir / ".codex" / "task-class-override"
        override_path.write_text(json.dumps({
            "class": "deploy",
            "until": int(time.time()) + 600,
        }), encoding="utf-8")

        cls = watchdog.get_task_class(self.project_dir)
        self.assertEqual(cls, "deploy")

    def test_expired_override_ignored_and_deleted(self):
        override_path = self.project_dir / ".codex" / "task-class-override"
        override_path.write_text(json.dumps({
            "class": "deploy",
            "until": int(time.time()) - 60,
        }), encoding="utf-8")
        (self.project_dir / ".codex" / "task-class").write_text(
            "bugfix", encoding="utf-8")

        cls = watchdog.get_task_class(self.project_dir)
        self.assertEqual(cls, "bugfix")
        self.assertFalse(override_path.exists())

    def test_no_files_returns_default(self):
        cls = watchdog.get_task_class(self.project_dir)
        self.assertEqual(cls, watchdog.DEFAULT_TASK_CLASS)


# ---------------------------------------------------------------------------
# Classifier file persistence
# ---------------------------------------------------------------------------

class TestClassifierPersistence(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_write_class(self):
        classifier.write_class(self.project_dir, "feature")
        path = self.project_dir / ".codex" / "task-class"
        self.assertTrue(path.exists())
        self.assertEqual(path.read_text(encoding="utf-8"), "feature")

    def test_classify_writes_correct_value(self):
        classifier.write_class(self.project_dir,
                               classifier.classify("задеплой в прод"))
        path = self.project_dir / ".codex" / "task-class"
        self.assertEqual(path.read_text(encoding="utf-8"), "deploy")


# ---------------------------------------------------------------------------
# Topic dedup
# ---------------------------------------------------------------------------

class TestTopicDedup(unittest.TestCase):

    def test_topic_hash_stable_identical(self):
        a = "Claude skipped the failing test"
        self.assertEqual(watchdog.topic_hash(a), watchdog.topic_hash(a))

    def test_topic_hash_case_insensitive(self):
        self.assertEqual(
            watchdog.topic_hash("CLAUDE Skipped Tests"),
            watchdog.topic_hash("claude skipped tests"),
        )


# ---------------------------------------------------------------------------
# AC4 — Cooldown logic
# ---------------------------------------------------------------------------

class TestCooldown(unittest.TestCase):

    def test_cooldown_constant(self):
        self.assertEqual(watchdog.POST_HALT_COOLDOWN, 3)

    def test_cap_when_cooldown_active(self):
        max_sev = watchdog.cap_severity(
            watchdog.SEV_WARN, watchdog.SEV_HALT)
        self.assertEqual(max_sev, watchdog.SEV_WARN)


# ---------------------------------------------------------------------------
# STRESS: malformed / corrupted state file
# ---------------------------------------------------------------------------

class TestStressState(unittest.TestCase):
    """Corrupted / malformed state must not crash watchdog."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.tmpdir.name)
        self.state_path = self.project_dir / ".codex" / "watchdog-state.json"
        self.state_path.parent.mkdir()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_corrupted_json_falls_back_to_new_state(self):
        self.state_path.write_text("{this is not json", encoding="utf-8")
        state = watchdog.load_state(self.state_path)
        self.assertIn("recent_wakes", state)
        self.assertEqual(state["recent_wakes"], [])

    def test_truncated_json_falls_back(self):
        self.state_path.write_text('{"session_id":"abc",', encoding="utf-8")
        state = watchdog.load_state(self.state_path)
        self.assertEqual(state["recent_wakes"], [])

    def test_missing_file_returns_new_state(self):
        ghost = self.state_path.parent / "nonexistent.json"
        state = watchdog.load_state(ghost)
        self.assertEqual(state["recent_wakes"], [])
        self.assertEqual(state["cooldown_remaining"], 0)

    def test_atomic_save_then_load_roundtrip(self):
        state = {
            "session_id": "testsid",
            "recent_wakes": [{"ts": 100, "sig_hash": "a", "severity": "WARN"}],
            "topic_halt_counts": {"t1": 1},
            "cooldown_remaining": 2,
        }
        watchdog.save_state(self.state_path, state)
        self.assertTrue(self.state_path.exists())
        # Make sure tmp file is gone
        leftovers = list(self.state_path.parent.glob("*.tmp.*"))
        self.assertEqual(leftovers, [],
                         f"atomic write left tmp file behind: {leftovers}")


# ---------------------------------------------------------------------------
# STRESS: malformed Codex verdicts
# ---------------------------------------------------------------------------

class TestStressCodexVerdict(unittest.TestCase):

    def test_wrapped_in_extra_prose(self):
        raw = ("Here is my analysis of the response:\n\n"
               "Looking carefully at the context, I note that...\n"
               '{"severity":"WARN","confidence":0.8,"reason":"x","evidence":"y"}'
               "\n\nLet me know if you need more detail.")
        v = watchdog._parse_codex_verdict(raw)
        self.assertIsNotNone(v)
        self.assertEqual(v["severity"], "WARN")

    def test_confidence_out_of_range_clamped(self):
        raw = '{"severity":"WARN","confidence":1.5,"reason":"x","evidence":"y"}'
        v = watchdog._parse_codex_verdict(raw)
        self.assertEqual(v["confidence"], 1.0)

    def test_confidence_non_numeric_defaults(self):
        raw = '{"severity":"WARN","confidence":"high","reason":"x","evidence":"y"}'
        v = watchdog._parse_codex_verdict(raw)
        self.assertEqual(v["confidence"], 0.5)

    def test_missing_fields_still_parses(self):
        raw = '{"severity":"OBSERVE"}'
        v = watchdog._parse_codex_verdict(raw)
        self.assertEqual(v["severity"], "OBSERVE")
        self.assertEqual(v["reason"], "")
        self.assertEqual(v["evidence"], "")

    def test_empty_response_returns_none(self):
        self.assertIsNone(watchdog._parse_codex_verdict(""))
        self.assertIsNone(watchdog._parse_codex_verdict("   "))


# ---------------------------------------------------------------------------
# STRESS: classifier edge inputs
# ---------------------------------------------------------------------------

class TestStressClassifier(unittest.TestCase):

    def test_very_long_prompt_classifies(self):
        p = "добавь " + ("новый endpoint " * 200)
        cls = classifier.classify(p)
        self.assertEqual(cls, "feature")

    def test_unicode_emoji_noise(self):
        cls = classifier.classify("🔥🚀 задеплой это в прод please ✨")
        self.assertEqual(cls, "deploy")

    def test_mixed_signals_first_match_wins(self):
        # deploy keyword + fix keyword → deploy wins (ordered rules)
        cls = classifier.classify("deploy the bugfix to production")
        self.assertEqual(cls, "deploy")

    def test_null_byte_safe(self):
        cls = classifier.classify("hello\x00world")
        # Should not crash, should classify as chat or feature
        self.assertIn(cls, {"chat", "feature"})


# ---------------------------------------------------------------------------
# INTEGRATION: full hook invocation via subprocess
# ---------------------------------------------------------------------------

import subprocess


class TestIntegrationSmoke(unittest.TestCase):
    """End-to-end: run hook as a subprocess with realistic stdin."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.tmpdir.name)
        (self.project_dir / ".codex").mkdir()
        self.env = {
            **dict(__import__("os").environ),
            "CLAUDE_PROJECT_DIR": str(self.project_dir),
        }

    def tearDown(self):
        self.tmpdir.cleanup()

    def _run_watchdog(self, payload: dict) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(HOOKS_DIR / "codex-watchdog.py")],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=self.env,
            timeout=30,
            encoding="utf-8",
        )

    def _run_classifier(self, payload: dict) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(HOOKS_DIR / "session-task-class.py")],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=self.env,
            timeout=10,
            encoding="utf-8",
        )

    def test_classifier_persists_class_file(self):
        res = self._run_classifier({"prompt": "задеплой в прод"})
        self.assertEqual(res.returncode, 0)
        cls_file = self.project_dir / ".codex" / "task-class"
        self.assertTrue(cls_file.exists())
        self.assertEqual(cls_file.read_text(encoding="utf-8"), "deploy")

    def test_watchdog_skips_empty_stdin(self):
        res = subprocess.run(
            [sys.executable, str(HOOKS_DIR / "codex-watchdog.py")],
            input="",
            capture_output=True,
            text=True,
            env=self.env,
            timeout=10,
            encoding="utf-8",
        )
        self.assertEqual(res.returncode, 0)

    def test_watchdog_skips_chat_class_even_with_signals(self):
        # Set chat class
        (self.project_dir / ".codex" / "task-class").write_text(
            "chat", encoding="utf-8")
        # Response with hard signals that WOULD otherwise trigger
        payload = {"assistant_message":
                   ("Готово, закоммитил, деплой прошёл. "
                    "Не запускал тесты — не критично сейчас. " * 10)}
        res = self._run_watchdog(payload)
        self.assertEqual(res.returncode, 0)
        # Should skip entirely — no Codex call attempted
        self.assertIn("class_disabled", res.stderr)

    def test_watchdog_skips_short_response(self):
        res = self._run_watchdog({"assistant_message": "short"})
        self.assertEqual(res.returncode, 0)
        self.assertIn("too_short", res.stderr)

    def test_watchdog_fp_linear_mcp_skips(self):
        # AC6 integration: the exact FP response from today's session
        fp_response = TestFPReplay.LINEAR_MCP_RESPONSE
        res = self._run_watchdog({"assistant_message": fp_response})
        self.assertEqual(res.returncode, 0,
                         f"Watchdog should exit 0, got {res.returncode}. "
                         f"stderr: {res.stderr[:500]}")
        self.assertIn("no_hard_signals", res.stderr)

    def test_override_file_applied_end_to_end(self):
        # Write an active override forcing chat class
        override = {"class": "chat", "until": int(time.time()) + 600}
        (self.project_dir / ".codex" / "task-class-override").write_text(
            json.dumps(override), encoding="utf-8")
        # Run classifier with a prompt that would normally be `deploy`
        self._run_classifier({"prompt": "задеплой в прод сейчас"})
        # Classifier honors override, writes chat to task-class
        cls = (self.project_dir / ".codex" / "task-class").read_text(encoding="utf-8")
        self.assertEqual(cls, "chat")

    def test_watchdog_off_override_honored_end_to_end(self):
        """AC7 regression (BLOCKER from Codex review): /watchdog off must disable watchdog.

        1. Classifier must preserve "off" override (write "off" to task-class file)
        2. Watchdog must see "off" class and skip before analysis
        """
        # Set /watchdog off override
        override = {"class": "off", "until": int(time.time()) + 600}
        (self.project_dir / ".codex" / "task-class-override").write_text(
            json.dumps(override), encoding="utf-8")

        # Classifier run — must persist "off" to task-class file
        self._run_classifier({"prompt": "задеплой в прод сейчас"})
        cls = (self.project_dir / ".codex" / "task-class").read_text(encoding="utf-8")
        self.assertEqual(cls, "off",
                         "Classifier must persist 'off' terminal state")

        # Watchdog run with response that WOULD trigger — must skip
        payload = {"assistant_message":
                   ("Готово, закоммитил, деплой. Не запускал тесты, не критично. " * 10)}
        res = self._run_watchdog(payload)
        self.assertEqual(res.returncode, 0)
        self.assertIn("class_disabled", res.stderr,
                      "Watchdog must skip due to 'off' class")


# ---------------------------------------------------------------------------
# HALT integration (AC2 + AC4) — true positive end-to-end
# ---------------------------------------------------------------------------

class TestHaltIntegration(unittest.TestCase):
    """AC2 + AC4: stub Codex to return HALT, drive main(), verify exit 2 + state."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.tmpdir.name)
        (self.project_dir / ".codex").mkdir()
        # Force deploy class so HALT is allowed
        (self.project_dir / ".codex" / "task-class").write_text(
            "deploy", encoding="utf-8")
        import os as _os
        self._old_env = _os.environ.get("CLAUDE_PROJECT_DIR")
        _os.environ["CLAUDE_PROJECT_DIR"] = str(self.project_dir)

    def tearDown(self):
        import os as _os
        if self._old_env is None:
            _os.environ.pop("CLAUDE_PROJECT_DIR", None)
        else:
            _os.environ["CLAUDE_PROJECT_DIR"] = self._old_env
        self.tmpdir.cleanup()

    def _run_main_with_halt_verdict(self, response: str):
        """Invoke main() with analyze_with_codex stubbed to return HALT."""
        halt_verdict = {
            "severity": "HALT",
            "confidence": 0.95,
            "reason": "claimed tests pass but log shows failure",
            "evidence": "'fixtures: 2 failed' in output",
        }
        # Patch stdin + analyze_with_codex + exit
        import io
        payload = json.dumps({"assistant_message": response})
        with patch.object(watchdog, "analyze_with_codex",
                          return_value=halt_verdict), \
             patch.object(sys, "stdin", io.StringIO(payload)):
            try:
                watchdog.main()
                return 0  # main didn't exit
            except SystemExit as e:
                return e.code

    def test_halt_verdict_exits_2_and_updates_state(self):
        response = ("Я завершил работу. Часть тестов не запускал, но commit "
                    "сделаю. Закоммитил. Push на прод. " * 5)
        exit_code = self._run_main_with_halt_verdict(response)
        self.assertEqual(exit_code, 2, "HALT verdict must exit 2")

        # State file must exist with recorded wake + cooldown
        state_path = self.project_dir / ".codex" / "watchdog-state.json"
        self.assertTrue(state_path.exists(), "State file must be created")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(state["recent_wakes"]), 1)
        self.assertEqual(state["recent_wakes"][-1]["severity"], "HALT")
        self.assertEqual(state["cooldown_remaining"], watchdog.POST_HALT_COOLDOWN)
        self.assertEqual(sum(state["topic_halt_counts"].values()), 1)

    def test_concurrent_stop_hooks_serialize_via_lock(self):
        """Round-3 BLOCKER regression test: overlapping Stop hooks must serialize.

        Simulate scenario where hook A holds lock during a slow Codex call
        and hook B attempts concurrent access. B must wait for A (not fall
        through unlocked). Verified by checking that lock file presence
        blocks acquire beyond the spin window.
        """
        import threading

        # Simulate A holding the lock
        state_path = self.project_dir / ".codex" / "watchdog-state.json"
        lock_path = state_path.with_suffix(state_path.suffix + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)

        # Hold lock for 1.5 seconds (simulating slow Codex call segment)
        import os as _os
        fd = _os.open(str(lock_path), _os.O_CREAT | _os.O_EXCL | _os.O_WRONLY)

        acquired_by_b = threading.Event()
        release_by_a = threading.Event()

        def b_tries_to_acquire():
            # Temporarily shrink retry budget for test speed
            original_retry = watchdog.LOCK_RETRY_MAX
            watchdog.LOCK_RETRY_MAX = 40  # 2s
            try:
                handle = watchdog.acquire_state_lock(state_path)
                if handle is not None:
                    acquired_by_b.set()
                    watchdog.release_state_lock(handle)
            finally:
                watchdog.LOCK_RETRY_MAX = original_retry

        def a_releases_after_delay():
            time.sleep(0.3)
            release_by_a.set()
            try:
                _os.close(fd)
                lock_path.unlink()
            except OSError:
                pass

        threading.Thread(target=a_releases_after_delay, daemon=True).start()
        b_thread = threading.Thread(target=b_tries_to_acquire, daemon=True)
        b_thread.start()
        b_thread.join(timeout=5.0)

        # Within 2s budget, A releases after 0.3s, so B should acquire
        self.assertTrue(acquired_by_b.is_set(),
                        "B must eventually acquire lock after A releases")

    def test_main_fail_closed_when_lock_unavailable(self):
        """Round-4 coverage gap: main() fail-closed orchestration path.

        When acquire_state_lock returns None (lock held forever), main()
        must exit 0 via OBSERVE AND must NOT call Codex AND must NOT mutate
        state file. Tests the lock-timeout guard wired into main().
        """
        import io
        # Set deploy class so watchdog would normally proceed to Codex
        (self.project_dir / ".codex" / "task-class").write_text(
            "deploy", encoding="utf-8")

        response = ("Я закончил. Часть тестов не запускал — не критично. "
                    "Можно commit. " * 6)
        payload = json.dumps({"assistant_message": response})

        state_path = self.project_dir / ".codex" / "watchdog-state.json"
        codex_called = {"val": False}

        def fake_codex(*args, **kwargs):
            codex_called["val"] = True
            return {"severity": "HALT", "confidence": 0.95,
                    "reason": "x", "evidence": "y"}

        with patch.object(watchdog, "acquire_state_lock", return_value=None), \
             patch.object(watchdog, "analyze_with_codex", side_effect=fake_codex), \
             patch.object(sys, "stdin", io.StringIO(payload)):
            try:
                watchdog.main()
                exit_code = 0
            except SystemExit as e:
                exit_code = e.code if e.code is not None else 0

        self.assertEqual(exit_code, 0, "fail-closed path must exit 0")
        self.assertFalse(codex_called["val"],
                         "Codex must NOT be called when lock unavailable")
        self.assertFalse(state_path.exists(),
                         "State file must NOT be created when lock unavailable")

    def test_lock_timeout_fails_closed(self):
        """If lock truly unavailable (held forever by fake crashed process),
        acquire returns None and main path emits OBSERVE without mutating state.
        """
        import os as _os
        state_path = self.project_dir / ".codex" / "watchdog-state.json"
        lock_path = state_path.with_suffix(state_path.suffix + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        # Create lock and set mtime to RECENT (not stale) so stale-removal doesn't fire
        fd = _os.open(str(lock_path), _os.O_CREAT | _os.O_EXCL | _os.O_WRONLY)
        try:
            # Shrink retry budget so test doesn't wait 60s
            original_retry = watchdog.LOCK_RETRY_MAX
            watchdog.LOCK_RETRY_MAX = 3  # 150ms
            try:
                handle = watchdog.acquire_state_lock(state_path)
                self.assertIsNone(handle,
                                  "acquire must return None when timeout exhausted")
            finally:
                watchdog.LOCK_RETRY_MAX = original_retry
        finally:
            _os.close(fd)
            lock_path.unlink()

    def test_second_halt_on_same_topic_downgrades(self):
        """Topic-dedup: same anomaly seen 2+ times must downgrade HALT to WARN."""
        response = ("Готово, commit, deploy. Не запускал tests. " * 5)
        # First HALT
        self._run_main_with_halt_verdict(response)
        # Second attempt with same verdict → should downgrade
        # (we change sig by adding text, keeping topic the same)
        response2 = response + " Ещё немного текста для разного sig hash. " * 3
        exit_code = self._run_main_with_halt_verdict(response2)
        # After one HALT (seen_count=1), second still HALTs (threshold is >=2)
        # Third would downgrade. Let's run third.
        response3 = response + " Third iteration text. " * 5
        exit_code3 = self._run_main_with_halt_verdict(response3)
        # After 2 HALTs on same topic, third should downgrade.
        self.assertEqual(exit_code3, 0, "Third HALT on same topic must downgrade → exit 0")


if __name__ == "__main__":
    unittest.main(verbosity=2)
