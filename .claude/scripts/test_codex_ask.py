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
