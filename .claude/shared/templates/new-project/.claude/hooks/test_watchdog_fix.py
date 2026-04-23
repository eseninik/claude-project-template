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


if __name__ == "__main__":
    unittest.main(verbosity=2)
