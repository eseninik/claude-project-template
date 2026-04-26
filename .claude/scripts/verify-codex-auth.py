#!/usr/bin/env python3
"""Verify that Codex CLI authentication works from a target project."""
from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path
from typing import Sequence


AUTH_PROMPT = "ping say OK"
AUTH_TIMEOUT_SECONDS = 10

logger = logging.getLogger(__name__)


def verify_codex_auth(target: Path, timeout: int = AUTH_TIMEOUT_SECONDS) -> bool:
    """Return True when Codex CLI exec succeeds from the target project."""
    logger.info(
        "verify_codex_auth.enter target=%s timeout=%d",
        target,
        timeout,
    )
    try:
        proc = subprocess.run(
            ["codex.cmd", "exec", "-"],
            input=AUTH_PROMPT,
            cwd=str(target),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError):
        logger.exception("verify_codex_auth.exit ok=False reason=subprocess-exception")
        return False
    output = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    ok = proc.returncode == 0 and bool(output)
    logger.info(
        "verify_codex_auth.exit ok=%s returncode=%d output_chars=%d",
        ok,
        proc.returncode,
        len(output),
    )
    return ok


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse CLI arguments."""
    logger.info("parse_args.enter argc=%d", len(argv))
    parser = argparse.ArgumentParser(description="Verify Codex authentication in a target project.")
    parser.add_argument("--tgt", default=".", help="target project root")
    parser.add_argument("--timeout", type=int, default=AUTH_TIMEOUT_SECONDS, help="subprocess timeout in seconds")
    args = parser.parse_args(list(argv))
    logger.info("parse_args.exit tgt=%s timeout=%d", args.tgt, args.timeout)
    return args


def main(argv: Sequence[str] | None = None) -> int:
    """Run the auth verification CLI."""
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)
    target = Path(args.tgt).resolve()
    logger.info("main.enter target=%s", target)
    if not target.is_dir():
        print(f"Codex auth check failed: target does not exist: {target}", file=sys.stderr)
        logger.info("main.exit returncode=1 reason=missing-target")
        return 1
    if verify_codex_auth(target, args.timeout):
        print(f"Codex auth OK in {target}")
        logger.info("main.exit returncode=0")
        return 0
    print(f"Codex auth check failed in {target}", file=sys.stderr)
    logger.info("main.exit returncode=1 reason=auth-failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
