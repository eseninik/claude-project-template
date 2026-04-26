"""Tests for verify-codex-auth.py."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).with_name("verify-codex-auth.py")
SPEC = importlib.util.spec_from_file_location("verify_codex_auth", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Cannot load {SCRIPT_PATH}")
verify = importlib.util.module_from_spec(SPEC)
sys.modules["verify_codex_auth"] = verify
SPEC.loader.exec_module(verify)


def _completed(returncode: int, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["codex.cmd", "exec", "-"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def test_verify_codex_auth_subprocess_called(tmp_path: Path) -> None:
    with mock.patch.object(
        verify.subprocess,
        "run",
        return_value=_completed(0, stdout="OK\n"),
    ) as run_mock:
        assert verify.verify_codex_auth(tmp_path) is True

    run_mock.assert_called_once()
    args, kwargs = run_mock.call_args
    assert args[0] == ["codex.cmd", "exec", "-"]
    assert kwargs["cwd"] == str(tmp_path)
    assert kwargs["input"] == verify.AUTH_PROMPT
    assert kwargs["check"] is False
    assert kwargs["timeout"] == verify.AUTH_TIMEOUT_SECONDS


def test_verify_codex_auth_returns_zero_on_success(tmp_path: Path) -> None:
    with mock.patch.object(
        verify.subprocess,
        "run",
        return_value=_completed(0, stdout="OK\n"),
    ):
        assert verify.main(["--tgt", str(tmp_path)]) == 0


def test_verify_codex_auth_returns_one_on_failure(tmp_path: Path) -> None:
    with mock.patch.object(
        verify.subprocess,
        "run",
        return_value=_completed(1, stderr="not authenticated\n"),
    ):
        assert verify.main(["--tgt", str(tmp_path)]) == 1
