#!/usr/bin/env python3
"""Chaos tests for Codex helper determinism."""

from __future__ import annotations

import importlib.util
import os
import re
import sys
from pathlib import Path


_THIS = Path(__file__).resolve()
_SCRIPT = _THIS.parent / "codex-implement.py"

spec = importlib.util.spec_from_file_location("codex_implement", _SCRIPT)
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load {_SCRIPT}")
codex_impl = importlib.util.module_from_spec(spec)
sys.modules["codex_implement"] = codex_impl
spec.loader.exec_module(codex_impl)


def test_argv_chaos_30_runs_identical():
    """30 invocations of _build_codex_argv produce identical argv."""
    results = [
        codex_impl._build_codex_argv("codex", "gpt-5.5", Path("/wt"), "<provider>")
        for _ in range(30)
    ]
    prefixes = [tuple(r[:8]) for r in results]
    assert all(p == prefixes[0] for p in prefixes), "argv prefix non-deterministic"
    assert all(r == results[0] for r in results), "argv non-deterministic"

    joined = "\n".join(results[0])
    assert str(os.getpid()) not in joined, "argv contains current PID"
    timestamp_like = re.compile(r"\d{4}-\d{2}-\d{2}|T\d{2}:\d{2}:\d{2}|\d{10,}")
    assert not timestamp_like.search(joined), "argv contains timestamp-like value"


def test_env_chaos_30_runs_identical():
    """30 invocations of _build_codex_env produce identical env (after sorting)."""
    results = [codex_impl._build_codex_env(Path("/wt"), Path("/proj")) for _ in range(30)]
    keys_sets = [frozenset(r.keys()) for r in results]
    assert all(k == keys_sets[0] for k in keys_sets), "env keys non-deterministic"
    allowlists = [r.get("CODEX_FS_READ_ALLOWLIST", "") for r in results]
    assert all(a == allowlists[0] for a in allowlists), "FS allowlist non-deterministic"
